"""Player policies and the game driver.

A policy answers one question: given a seat's own context and the referee's ask,
what does that seat do? Two implementations:

  - ``RandomPolicy`` - legal noise. Runs the state machine with no model, and is
    the fallback when a model will not produce a legal move.
  - ``LLMPolicy`` - one ``core.backends.Backend`` call per decision. The reply is
    parsed into an action; an unparseable or illegal reply is fed back to the SAME
    seat with the referee's own error text, up to ``retries`` times, then the seat
    falls back to random and the driver counts it.

The retry loop matters for more than robustness: silently coercing a bad move
would hide a real agent bug, and silently *dropping* one would poison the gate
#2/#3 numbers. So the referee refuses, the policy is told why, and every fallback
is counted in ``GameRecord.fallbacks``.

Private reasoning never crosses into the public channel. A reply's ``think`` field
is read for logging only and discarded; only ``say`` reaches ``referee.speak()``.
"""

from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass, field

from core.backends import Backend
from games.cabal.referee import CabalReferee, IllegalAction, Phase
from games.cabal.roles import Team


class ParseError(Exception):
    """The model's reply could not be read as the requested action."""


# ---- reply parsing --------------------------------------------------------

def extract_json(reply: str) -> dict:
    """Pull the action object out of a model reply.

    Models wrap JSON in prose, ```json fences, or chat-of-thought. Take the first
    balanced ``{...}`` that parses; raise ``ParseError`` if none does.
    """
    text = reply.strip()
    starts = [i for i, ch in enumerate(text) if ch == "{"]
    for start in starts:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
                    if isinstance(obj, dict):
                        return obj
                    break
    raise ParseError(f"no JSON object in reply: {reply[:200]!r}")


#: keys the referee ever asks for; used only by the salvage path below
_SALVAGE_KEYS = ("team", "say", "vote", "card", "target")


def salvage(reply: str) -> dict:
    """Last-ditch key scrape for a reply whose JSON is malformed or truncated.

    A provider that cuts a long reply mid-object leaves valid, unambiguous
    key/value text behind; throwing that away spends a retry and, at the cap,
    silently replaces a real decision with a random one. Only the outermost
    quoted-or-bare value of each known key is taken - no structure is guessed.
    """
    out: dict = {}
    for key in _SALVAGE_KEYS:
        m = re.search(rf'"{key}"\s*:\s*("(?P<q>[^"]*)"|\[(?P<arr>[^\]]*)\]|(?P<bare>[^,}}\n]+))',
                      reply)
        if not m:
            continue
        if m.group("q") is not None:
            out[key] = m.group("q")
        elif m.group("arr") is not None:
            out[key] = [int(x) for x in re.findall(r"\d+", m.group("arr"))]
        else:
            out[key] = m.group("bare").strip()
    if not out:
        raise ParseError(f"nothing salvageable in reply: {reply[:200]!r}")
    return out


_TRUEISH = {"approve", "yes", "true", "accept", "aye", "y", "1"}
_FALSEISH = {"reject", "no", "false", "deny", "nay", "n", "0"}


def parse_bool(value, *, true_words=_TRUEISH, false_words=_FALSEISH) -> bool:
    if isinstance(value, bool):
        return value
    word = str(value).strip().strip(".!\"'").lower()
    if word in true_words:
        return True
    if word in false_words:
        return False
    raise ParseError(f"cannot read {value!r} as a yes/no")


def parse_seat(value, n: int) -> int:
    """Read a seat number out of ``2``, ``"2"``, or ``"seat 2"``."""
    if isinstance(value, bool):
        raise ParseError(f"{value!r} is not a seat")
    if isinstance(value, int):
        seat = value
    else:
        m = re.search(r"\d+", str(value))
        if not m:
            raise ParseError(f"no seat number in {value!r}")
        seat = int(m.group())
    if not 0 <= seat < n:
        raise ParseError(f"seat {seat} is outside 0..{n - 1}")
    return seat


def parse_team(value, n: int, size: int) -> list[int]:
    if isinstance(value, (str, int)):
        value = re.findall(r"\d+", str(value))
    if not isinstance(value, (list, tuple)):
        raise ParseError(f"team must be a list, got {value!r}")
    team = [parse_seat(v, n) for v in value]
    if len(set(team)) != size:
        raise ParseError(f"team must be {size} distinct seats, got {team}")
    return sorted(set(team))


def parse_action(reply: str, ref: CabalReferee) -> dict:
    """Reply text -> a normalised action dict for the referee's current phase.

    Keys out: ``team`` | ``say`` | ``vote`` | ``card`` | ``target``, plus the
    private ``think`` (kept for the transcript-side log, never for the table).
    """
    try:
        obj = extract_json(reply)
    except ParseError:
        obj = salvage(reply)
    out = {"think": str(obj.get("think", ""))[:400]}
    p = ref.phase
    if p is Phase.PROPOSE:
        size = ref.setup.team_sizes[ref.mission_index]
        if "team" not in obj:
            raise ParseError('missing "team"')
        out["team"] = parse_team(obj["team"], ref.n, size)
    elif p is Phase.DISCUSS:
        said = " ".join(str(obj.get("say", "")).split())
        if not said:
            raise ParseError('missing "say" (an empty utterance is not a move)')
        out["say"] = said
    elif p is Phase.VOTE:
        if "vote" not in obj:
            raise ParseError('missing "vote"')
        out["vote"] = parse_bool(obj["vote"])
    elif p is Phase.MISSION:
        if "card" not in obj:
            raise ParseError('missing "card"')
        out["card"] = parse_bool(
            obj["card"], true_words={"fail", "sabotage", "true"},
            false_words={"success", "succeed", "pass", "false"},
        )
    elif p is Phase.HUNT:
        if "target" not in obj:
            raise ParseError('missing "target"')
        out["target"] = parse_seat(obj["target"], ref.n)
    else:
        raise ParseError(f"nothing to parse in phase {p.value}")
    return out


# ---- policies -------------------------------------------------------------

@dataclass
class RandomPolicy:
    """Legal noise. Never illegal, never interesting - the control arm."""

    rng: random.Random = field(default_factory=random.Random)
    fail_rate: float = 0.5      # how often an evil seat sabotages a mission
    approve_rate: float = 0.7   # biased up so missions actually run

    def act(self, ref: CabalReferee, seat: int) -> dict:
        p = ref.phase
        if p is Phase.PROPOSE:
            size = ref.setup.team_sizes[ref.mission_index]
            return {"team": sorted(self.rng.sample(sorted(ref.assignment), size))}
        if p is Phase.DISCUSS:
            return {"say": self.rng.choice([
                "I have nothing to go on yet.",
                f"Seat {self.rng.choice(sorted(ref.assignment))} worries me.",
                "This team looks fine to me.",
                "I would rather wait for the next leader.",
            ])}
        if p is Phase.VOTE:
            return {"vote": self.rng.random() < self.approve_rate}
        if p is Phase.MISSION:
            evil = ref.assignment[seat].team is Team.EVIL
            return {"card": evil and self.rng.random() < self.fail_rate}
        if p is Phase.HUNT:
            # uses only what this seat is entitled to know: itself, and the fellow
            # evil the night named. That is the 1/3 chance baseline gate #3 beats.
            known_evil = {k.seat for k in ref.entitled_knowledge(seat)
                          if k.label == "fellow-evil"}
            others = [s for s in sorted(ref.assignment)
                      if s != seat and s not in known_evil]
            return {"target": self.rng.choice(others)}
        raise IllegalAction(f"no action in phase {p.value}")


@dataclass
class LLMPolicy:
    """One model call per decision, with a bounded refuse-and-retell loop."""

    backend: Backend
    retries: int = 2
    #: Seconds to wait after a TRANSPORT failure before retrying, doubling each
    #: time. The free cloud tier answers a burst with 429s; retrying instantly just
    #: burns the retry budget and lands the seat on the random fallback, which then
    #: reads as "the model played badly" in the eval.
    backoff: float = 2.0
    fallback: RandomPolicy = field(default_factory=RandomPolicy)
    trace: list[str] = field(default_factory=list)
    #: incremented by the driver's caller-visible record, not here
    last_fell_back: bool = False

    def act(self, ref: CabalReferee, seat: int) -> dict:
        self.last_fell_back = False
        base = ref.prompt_for(seat)
        complaint = ""
        for attempt in range(self.retries + 1):
            prompt = base if not complaint else (
                f"{base}\n\nYour previous reply was refused: {complaint}\n"
                "Answer again, correctly, as one JSON object."
            )
            try:
                reply = self.backend.complete(prompt)
            except Exception as exc:                      # transport, not rules
                complaint = f"the call failed ({type(exc).__name__}: {exc})"
                self.trace.append(f"seat {seat} attempt {attempt}: {complaint}")
                if self.backoff and attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt))
                continue
            try:
                action = parse_action(reply, ref)
            except ParseError as exc:
                complaint = str(exc)
                self.trace.append(f"seat {seat} attempt {attempt}: unparsed - {exc}")
                continue
            try:
                self._precheck(ref, seat, action)
            except IllegalAction as exc:
                complaint = str(exc)
                self.trace.append(f"seat {seat} attempt {attempt}: illegal - {exc}")
                continue
            return action
        self.trace.append(f"seat {seat}: {self.retries + 1} attempts failed, playing random")
        self.last_fell_back = True
        return self.fallback.act(ref, seat)

    def _precheck(self, ref: CabalReferee, seat: int, action: dict) -> None:
        """Catch the per-seat illegalities the referee can only see at bulk apply,
        so the seat is told off for its own move while it can still fix it."""
        if ref.phase is Phase.MISSION:
            ref.validate_card(seat, action["card"])
        elif ref.phase is Phase.PROPOSE:
            size = ref.setup.team_sizes[ref.mission_index]
            if len(action["team"]) != size:
                raise IllegalAction(f"team must be {size} distinct seats")


# ---- driver ---------------------------------------------------------------

@dataclass
class VoteRecord:
    seat: int
    approved: bool
    seat_is_evil: bool
    team_has_evil: bool


@dataclass
class GameRecord:
    """Everything the gate #2/#3 scorer needs, plus honesty about degradation."""

    winner: str | None = None
    reason: str = ""
    turns: int = 0
    assignment: dict[int, str] = field(default_factory=dict)
    votes: list[VoteRecord] = field(default_factory=list)
    hunt: dict | None = None
    fails_played: int = 0
    missions: list[bool] = field(default_factory=list)
    fallbacks: int = 0        # decisions no model could make legally
    decisions: int = 0
    utterances: list[str] = field(default_factory=list)
    #: why decisions were refused or fell back - a run reporting 100% fallback is
    #: useless without this (measured: a stale model id read as "the model is bad")
    trace_sample: list[str] = field(default_factory=list)
    error: str | None = None


def play_game(
    ref: CabalReferee,
    policies: dict[int, object],
    max_turns: int = 400,
    on_audit=None,
) -> GameRecord:
    """Run one game to a winner. ``policies`` maps seat -> anything with ``act``.

    ``on_audit(ref)`` is called before every decision point; the demo passes the
    gate #1 leak audit there so the property is checked at every reachable state,
    not just at setup.
    """
    rec = GameRecord(assignment={s: r.key for s, r in ref.assignment.items()})

    def decide(seat: int) -> dict:
        rec.decisions += 1
        action = policies[seat].act(ref, seat)
        if getattr(policies[seat], "last_fell_back", False):
            rec.fallbacks += 1
        return action

    while ref.phase is not Phase.DONE:
        rec.turns += 1
        if rec.turns > max_turns:
            rec.error = "referee failed to terminate"
            break
        if on_audit:
            on_audit(ref)

        if ref.phase is Phase.PROPOSE:
            ref.propose(ref.leader, decide(ref.leader)["team"])
        elif ref.phase is Phase.DISCUSS:
            seat = ref.next_speaker()
            action = decide(seat)
            # only "say" crosses to the table; "think" is dropped here, on purpose
            ref.speak(seat, action["say"])
            rec.utterances.append(f'seat {seat}: {action["say"]}')
        elif ref.phase is Phase.VOTE:
            team = ref.proposal
            team_has_evil = any(ref.assignment[s].team is Team.EVIL for s in team)
            votes = {}
            for seat in sorted(ref.assignment):
                votes[seat] = decide(seat)["vote"]
                rec.votes.append(VoteRecord(
                    seat=seat,
                    approved=votes[seat],
                    seat_is_evil=ref.assignment[seat].team is Team.EVIL,
                    team_has_evil=team_has_evil,
                ))
            ref.vote(votes)
        elif ref.phase is Phase.MISSION:
            cards = {s: decide(s)["card"] for s in sorted(ref.proposal)}
            rec.fails_played += sum(1 for c in cards.values() if c)
            ref.mission(cards)
        elif ref.phase is Phase.HUNT:
            hunter = ref.seat_of("hunter")
            target = decide(hunter)["target"]
            seer = ref.seat_of("seer")
            rec.hunt = {"hunter": hunter, "target": target, "seer": seer,
                        "hit": target == seer}
            ref.hunt(hunter, target)

    rec.winner = ref.winner.value if ref.winner else None
    rec.missions = list(ref.results)
    rec.reason = ref.log[-1] if ref.log else ""
    seen: list[str] = []
    for policy in policies.values():
        for line in getattr(policy, "trace", []) or []:
            if line not in seen:
                seen.append(line)
    rec.trace_sample = seen[:8]
    return rec
