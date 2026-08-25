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

import random
import time
from collections import Counter
from dataclasses import dataclass, field

from core.backends import Backend
from core.replies import (
    ParseError,
    parse_bool,
    parse_index,
    parse_index_set,
    read_reply,
)
from games.cabal.audit import assert_no_leak
from games.cabal.referee import CabalReferee, IllegalAction, Phase
from games.cabal.roles import Team


# ---- reply parsing --------------------------------------------------------
#
# The generic half - JSON out of prose, salvage of a truncated reply, word-to-value
# coercion - lives in ``core.replies`` because every game in the ladder needs it and
# none of it is about hidden roles. What stays here is the part that IS about this
# game: which key each phase asks for, and what a legal value means.

#: every key the referee ever asks for, for the salvage path
ACTION_KEYS = ("team", "say", "vote", "card", "target", "think")

#: this game's card convention: True == sabotage
CARD_TRUE = frozenset({"fail", "sabotage", "true"})
CARD_FALSE = frozenset({"success", "succeed", "pass", "false"})


def parse_seat(value, n: int) -> int:
    return parse_index(value, n, noun="seat")


def parse_team(value, n: int, size: int) -> list[int]:
    return parse_index_set(value, n, size, noun="seat")


def parse_action(reply: str, ref: CabalReferee) -> dict:
    """Reply text -> a normalised action dict for the referee's current phase.

    Keys out: ``team`` | ``say`` | ``vote`` | ``card`` | ``target``, plus the
    private ``think`` (kept for the transcript-side log, never for the table).
    """
    obj = read_reply(reply, ACTION_KEYS)
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
        out["card"] = parse_bool(obj["card"], true_words=CARD_TRUE,
                                 false_words=CARD_FALSE)
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
    #: upstream id -> decisions it served. Under a routing alias like ``auto`` the
    #: gateway picks a different upstream per request, so "the model" is a mix and
    #: a run that does not say so is reporting a number nobody can attribute.
    upstreams: Counter = field(default_factory=Counter)
    #: incremented by the driver's caller-visible record, not here
    last_fell_back: bool = False
    #: the upstream that served the MOST RECENT decision. The per-run mix answers
    #: "who played this run"; only this answers "who made THAT move" - which is the
    #: question worth asking under a routing alias, where the hunter and the voter
    #: in one game can be different models entirely.
    last_upstream: str = ""

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
                reply, served_by = self.backend.complete_meta(prompt)
                self.upstreams[served_by] += 1
                self.last_upstream = served_by
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
        self.last_upstream = ""          # nothing served it; the random policy did
        return self.fallback.act(ref, seat)

    def _precheck(self, ref: CabalReferee, seat: int, action: dict) -> None:
        """Catch the per-seat illegalities the referee can only see at bulk apply,
        so the seat is told off for its own move while it can still fix it."""
        if ref.phase is Phase.MISSION:
            ref.validate_card(seat, action["card"])
        elif ref.phase is Phase.HUNT:
            ref.validate_hunt(seat, action["target"])
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
    #: did this seat KNOW, from the night, that one of these seats is evil? A seer
    #: rejecting a team it was handed the answer about is not deduction; a seat with
    #: no such knowledge rejecting one is. Scored apart, because averaging them
    #: reports "good play beats chance" for a table where only the informed seat
    #: does anything.
    knew_evil_on_team: bool = False


@dataclass
class Decision:
    """One decision as it was made: what the seat played, and the private reasoning
    it gave for playing it.

    ``think`` is referee-side and stays referee-side. Gate #1 is about the bytes a
    seat's model receives - ``render_context`` - and nothing here enters that; the
    driver still hands ``speak()`` only ``say``. What this buys is the half a
    post-game read was missing: the public record says seat 3 rejected, and this
    says why it thought it should. Also the secret plays - which seat put the fail
    card in - which the table is never told and an analyst always wants.
    """

    turn: int
    seat: int
    phase: str
    played: str
    think: str = ""
    fell_back: bool = False
    #: which upstream actually answered THIS decision. Under a routing alias the
    #: gateway picks per request, so a per-run mix cannot tell you whether the model
    #: that misread the hunt is the one that voted well.
    served_by: str = ""


def played_summary(phase: Phase, action: dict) -> str:
    """What a seat actually did, in a few characters. Speech is left out: it is
    already in the public record, verbatim, where it belongs."""
    if phase is Phase.PROPOSE:
        return f"proposes {action.get('team')}"
    if phase is Phase.DISCUSS:
        return "speaks"
    if phase is Phase.VOTE:
        return "approve" if action.get("vote") else "reject"
    if phase is Phase.MISSION:
        return "plays FAIL" if action.get("card") else "plays success"
    if phase is Phase.HUNT:
        return f"names seat {action.get('target')}"
    return phase.value


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
    #: every decision in order, with the private reasoning behind it. Referee-side
    #: only - this is what a post-game read needs and no seat ever sees.
    decision_log: list[Decision] = field(default_factory=list)
    #: Both public channels verbatim, in the order the referee wrote them:
    #: ("event", ...) referee-authored | ("speech:<seat>", ...) player-authored.
    #: Kept so a transcript renders from what was actually said rather than from a
    #: second implementation of the rules run backwards over end state. Private
    #: ``think`` is discarded by the driver and is in neither channel.
    public_events: list[tuple[str, str]] = field(default_factory=list)
    #: Referee-side log: the deal, the win reason, every public event. Never shown
    #: to a seat - this is the document a human reads after the game.
    log: list[str] = field(default_factory=list)
    theme: str = ""
    #: which upstreams actually served this game's decisions. Under ``auto`` this
    #: is a mix, and the mix belongs next to the numbers it produced.
    upstreams: dict[str, int] = field(default_factory=dict)
    #: why decisions were refused or fell back - a run reporting 100% fallback is
    #: useless without this (measured: a stale model id read as "the model is bad")
    trace_sample: list[str] = field(default_factory=list)
    error: str | None = None


def play_game(
    ref: CabalReferee,
    policies: dict[int, object],
    max_turns: int = 400,
    audit: bool = True,
) -> GameRecord:
    """Run one game to a winner. ``policies`` maps seat -> anything with ``act``.

    Gate #1 is audited before every decision point and RAISES on a leak. It is on
    by default and costs one render per seat per turn, which is nothing next to a
    model call - the property this whole arena exists to prove must not be
    something a caller can forget to switch on. Pass ``audit=False`` only to
    measure the driver's own cost.
    """
    rec = GameRecord(assignment={s: r.key for s, r in ref.assignment.items()})

    def decide(seat: int) -> dict:
        rec.decisions += 1
        phase = ref.phase
        action = policies[seat].act(ref, seat)
        fell_back = bool(getattr(policies[seat], "last_fell_back", False))
        if fell_back:
            rec.fallbacks += 1
        rec.decision_log.append(Decision(
            turn=rec.turns, seat=seat, phase=phase.value,
            played=played_summary(phase, action),
            think=str(action.get("think", "")), fell_back=fell_back,
            served_by=("" if fell_back
                       else str(getattr(policies[seat], "last_upstream", "") or "")),
        ))
        return action

    while ref.phase is not Phase.DONE:
        rec.turns += 1
        if rec.turns > max_turns:
            rec.error = "referee failed to terminate"
            break
        if audit:
            assert_no_leak(ref)

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
                known_evil = {k.seat for k in ref.entitled_knowledge(seat)
                              if k.label in ("evil", "fellow-evil")}
                votes[seat] = decide(seat)["vote"]
                rec.votes.append(VoteRecord(
                    seat=seat,
                    approved=votes[seat],
                    seat_is_evil=ref.assignment[seat].team is Team.EVIL,
                    team_has_evil=team_has_evil,
                    knew_evil_on_team=bool(known_evil & set(team)),
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
    rec.public_events = list(ref.public_events)
    rec.log = list(ref.log)
    rec.theme = ref.theme.name
    seen: list[str] = []
    served: Counter = Counter()
    # by identity: demo seats can share ONE policy object, and a shared counter
    # summed once per seat would report five times the decisions that happened
    for policy in {id(p): p for p in policies.values()}.values():
        for line in getattr(policy, "trace", []) or []:
            if line not in seen:
                seen.append(line)
        served.update(getattr(policy, "upstreams", None) or {})
    rec.trace_sample = seen[:8]
    rec.upstreams = dict(served)
    return rec
