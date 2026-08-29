"""Player policies and the game driver.

Same contract as the other rungs: a policy answers one question per decision, the
referee refuses an illegal move rather than coercing it, the seat is told why, and
every fallback to random is counted. Silently coercing a bad move hides an agent
bug; silently dropping one poisons the gate numbers.

One thing differs, and it is the reason this file is not a copy of
``games/changeling/player.py`` with the nouns changed. There, the driver knows the
shape of the game: a discussion loop, then a vote loop. Here it does not and must
not - the referee's ``pending()`` says who is on the clock and what they are being
asked, and the driver's whole job is to hand that to a policy and hand the answer
back. A day can end early, a seat can wake because it just died, a nomination can
end the day on the spot; a driver that encoded the sequence would have to be
edited every time a role was added, and would silently disagree with the referee
about the rules the first time somebody forgot.

**Night targets ARE chosen by the seat here.** `changeling` picks its night
targets at random on purpose, because there the night only has to create
divergence. This game's night is a decision: who the demon kills, who the
protector covers, who the poisoner switches off. A random kill would make the
whole evil side a control policy wearing a model's name.
"""

from __future__ import annotations

import random
import time
from collections import Counter
from dataclasses import dataclass, field

from core.backends import Backend
from core.replies import (ParseError, parse_bool, parse_index, parse_index_set,
                          read_reply)
from games.belfry.audit import assert_no_leak
from games.belfry.referee import BelfryReferee, IllegalAction, Turn
from games.belfry.roles import Align


#: Every key the referee ever asks for, for the salvage path.
ACTION_KEYS = ("say", "slay", "nominate", "vote", "target", "targets", "think")

#: The driver's structural bound, distinct from the referee's day bound. Two
#: counters because they catch different bugs: ``max_days`` catches a win condition
#: that never fires, this catches a phase that never advances. Neither is reachable
#: in a legal game - the largest table plays a few hundred decisions.
MAX_DECISIONS = 4000

#: A pass, in the words a model is likely to reach for.
PASS_WORDS = frozenset({"", "none", "null", "pass", "nobody", "no one", "skip"})


def parse_action(reply: str, ref: BelfryReferee, turn: Turn) -> dict:
    """Reply text -> a normalised action for whatever this seat is being asked.

    ``think`` is kept for the referee-side log and reaches no channel a seat can
    read. Only ``say`` is published.
    """
    obj = read_reply(reply, ACTION_KEYS)
    out = {"think": str(obj.get("think", ""))[:400]}
    kind = turn.kind
    if kind == "speak":
        said = " ".join(str(obj.get("say", "")).split())
        if not said:
            raise ParseError('missing "say" (an empty utterance is not a move)')
        out["say"] = said
        if obj.get("slay") is not None:
            word = str(obj["slay"]).strip().lower()
            if word not in PASS_WORDS:
                out["slay"] = parse_index(obj["slay"], ref.n, noun="seat")
    elif kind == "nominate":
        if "nominate" not in obj:
            raise ParseError('missing "nominate" (a seat number, or null to pass)')
        value = obj["nominate"]
        word = str(value).strip().strip(".!\"'").lower()
        out["nominate"] = (None if value is None or word in PASS_WORDS
                           else parse_index(value, ref.n, noun="seat"))
    elif kind == "vote":
        if "vote" not in obj:
            raise ParseError('missing "vote"')
        out["vote"] = parse_bool(obj["vote"])
    elif kind == "divine":
        if "targets" not in obj:
            raise ParseError('missing "targets" (two seat numbers)')
        out["targets"] = parse_index_set(obj["targets"], ref.n, 2, noun="seat")
    else:
        if "target" not in obj:
            raise ParseError('missing "target" (one seat number)')
        out["target"] = parse_index(obj["target"], ref.n, noun="seat")
    return out


def illegal_reason(ref: BelfryReferee, turn: Turn, action: dict) -> str:
    """Why the referee would refuse this action, or "".

    Asked BEFORE the move is applied, and answered out of ``ref.legal_targets`` -
    the same list the ask printed. A second copy of the rules here is how a seat
    comes to be refused for the move its own prompt told it to make.
    """
    seat, kind = turn.seat, turn.kind
    legal = ref.legal_targets(seat, kind)
    if kind == "speak":
        if "slay" in action:
            if not ref.grim.seat(seat).alive:
                return f"seat {seat} is dead and cannot use a day power"
            allowed = ref.legal_targets(seat, "slay")
            if ref.grim.seat(seat).used_power:
                return f"seat {seat} has already spent its public day power"
            if action["slay"] not in allowed:
                return (f"seat {action['slay']} cannot be named out loud; choose "
                        f"from {allowed}")
        return ""
    if kind == "nominate":
        target = action["nominate"]
        if target is not None and target not in legal:
            return (f"seat {target} has already been nominated today; choose "
                    f"from {legal} or pass")
        return ""
    if kind == "vote":
        return ""
    if kind == "divine":
        picks = action["targets"]
        bad = [p for p in picks if p not in legal]
        return f"seat(s) {bad} are not legal choices; choose from {legal}" if bad \
            else ""
    target = action["target"]
    if target not in legal:
        return f"seat {target} is not a legal choice; choose from {legal}"
    return ""


@dataclass
class RandomPolicy:
    """Legal noise. The control arm, and the only honest source of this game's
    chance baseline."""

    rng: random.Random = field(default_factory=random.Random)

    def act(self, ref: BelfryReferee, seat: int) -> dict:
        turn = ref.pending()
        if turn is None or turn.seat != seat:
            raise IllegalAction(f"seat {seat} is not on the clock")
        kind = turn.kind
        legal = ref.legal_targets(seat, kind)
        if kind == "speak":
            return {"say": self.rng.choice([
                "I have nothing worth saying yet.",
                f"Seat {self.rng.choice([s for s in ref.grim.alive_seats() if s != seat] or [seat])} has been very quiet.",
                "I am good, and I would rather we executed somebody today.",
                "Say what you were told last night, or say why you will not.",
            ])}
        if kind == "nominate":
            # Passing has to be reachable by the control policy, or the baseline
            # this rung is measured against is a table that always executes.
            if not legal or self.rng.random() < 0.5:
                return {"nominate": None}
            return {"nominate": self.rng.choice(legal)}
        if kind == "vote":
            return {"vote": self.rng.random() < 0.5}
        if kind == "divine":
            return {"targets": sorted(self.rng.sample(legal, 2))}
        return {"target": self.rng.choice(legal)}


@dataclass
class LLMPolicy:
    """One model call per decision, with a bounded refuse-and-retell loop."""

    backend: Backend
    retries: int = 2
    #: Seconds after a TRANSPORT failure, doubling. Retrying instantly just burns
    #: the budget and lands the seat on random, which then reads as "the model
    #: played badly" in the eval.
    backoff: float = 2.0
    fallback: RandomPolicy = field(default_factory=RandomPolicy)
    trace: list[str] = field(default_factory=list)
    upstreams: Counter = field(default_factory=Counter)
    last_fell_back: bool = False
    last_upstream: str = ""
    last_refusal: str = ""
    last_refusals: int = 0
    last_rule_refusals: int = 0

    def act(self, ref: BelfryReferee, seat: int) -> dict:
        self.last_fell_back = False
        self.last_refusal = ""
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_prompt_size = 0
        self.last_reply_size = 0
        self.last_usage = None
        turn = ref.pending()
        base = ref.prompt_for(seat)
        complaint = ""
        for attempt in range(self.retries + 1):
            prompt = base if not complaint else (
                f"{base}\n\nYour previous reply was refused: {complaint}\n"
                "Answer again, correctly, as one JSON object.")
            try:
                reply, served_by = self.backend.complete_meta(prompt)
                self.upstreams[served_by] += 1
                self.last_upstream = served_by
                self.last_prompt_size = len(prompt)
                self.last_reply_size = len(reply)
                self.last_usage = getattr(self.backend, "last_usage", None)
            except Exception as exc:                      # transport, not rules
                complaint = f"the call failed ({type(exc).__name__}: {exc})"
                self._refused(seat, attempt, "transport", complaint)
                if self.backoff and attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt))
                continue
            try:
                action = parse_action(reply, ref, turn)
            except ParseError as exc:
                complaint = str(exc)
                self._refused(seat, attempt, "unparsed", str(exc))
                continue
            bad = illegal_reason(ref, turn, action)
            if bad:
                complaint = bad
                self._refused(seat, attempt, "illegal", bad)
                continue
            return action
        self.trace.append(
            f"seat {seat}: {self.retries + 1} attempts failed, playing random")
        self.last_fell_back = True
        self.last_upstream = ""          # nothing served it; the random policy did
        return self.fallback.act(ref, seat)

    def _refused(self, seat: int, attempt: int, kind: str, detail: str) -> None:
        """One place writes a refusal, so the trace, the per-decision census and the
        integrity block can never disagree about what happened."""
        self.last_refusals += 1
        if kind != "transport":
            self.last_rule_refusals += 1
        text = detail if kind == "transport" else f"{kind} - {detail}"
        self.last_refusal = f"seat {seat} attempt {attempt}: {text}"
        self.trace.append(self.last_refusal)


# ---- driver ---------------------------------------------------------------

@dataclass
class Decision:
    turn: int
    day: int
    seat: int
    kind: str
    played: str
    think: str = ""
    refused: str = ""
    refusals: int = 0
    rule_refusals: int = 0
    fell_back: bool = False
    served_by: str = ""
    prompt_size: int = 0
    reply_size: int = 0
    usage: dict | None = None


@dataclass
class VoteRecord:
    """One hand, with what a scorer needs to stratify it. The hand a seat
    RAISED, which is not always the hand that counted - the counted total is in the
    public record, and a record holding only that could not tell the two apart."""

    day: int
    seat: int
    nominee: int
    yes: bool
    voter_evil: bool
    nominee_evil: bool
    voter_alive: bool
    #: Had this seat been told something FALSE by the time it voted? The stratum
    #: this rung exists to measure, and it has to be recorded per vote rather than
    #: per game: a seat poisoned on night 3 voted four times before it was misled,
    #: and folding those into the misled column would credit the poison with the
    #: seat's earlier play.
    voter_misled: bool = False
    #: The same ``turn_no`` the Decision for this vote carries. A day has many
    #: nominations and a seat votes in each, so (day, seat) is NOT a join key -
    #: turn is. -1 marks a record written before the field existed.
    turn: int = -1
    #: Was THIS vote cast by the random fallback after the retry budget ran out?
    #: Snapshotted from the same decision that landed the vote - never re-read
    #: from the policy later, by which time another turn has overwritten it. A
    #: fallback vote is the random policy wearing the model's name, so the
    #: scorer must be able to drop it without asking the policy anything.
    fell_back: bool = False


@dataclass
class ExecutionRecord:
    """One execution and the board it happened on. ``alive_before`` and
    ``evil_before`` travel with it because they are the denominator: hitting an
    evil seat with two of four alive is not the same event as hitting one with two
    of nine, and the board has moved by the time anybody scores it."""

    day: int
    seat: int
    evil: bool
    #: Was the seat alive when it was executed? A dead seat can be nominated and
    #: voted up; the day ends and nobody dies.
    was_alive: bool
    alive_before: int
    evil_before: int
    #: Voted up, or executed on the spot by a trigger. A trigger execution names
    #: the nominator and only fires on a townsfolk one, so it is good with
    #: probability 1 and is not a draw from the board the chance rate is computed
    #: off. Scored apart, for the same reason ``was_alive`` is.
    by_vote: bool = True


@dataclass
class GameRecord:
    """Everything a scorer needs, plus honesty about degradation."""

    winner: str | None = None
    reason: str = ""
    #: A short key for HOW it ended, beside the sentence. A scorer matching on the
    #: sentence would be parsing prose that is free to be reworded.
    cause: str = ""
    days: int = 0
    seats: int = 0
    script: str = ""
    #: Seat -> the role it was dealt, and seat -> the role it held at the end. Both,
    #: because the demon can change hands and a record with one column could not say
    #: that it did.
    dealt: dict[int, str] = field(default_factory=dict)
    final: dict[int, str] = field(default_factory=dict)
    alive: tuple[int, ...] = ()
    executions: list[ExecutionRecord] = field(default_factory=list)
    votes: list[VoteRecord] = field(default_factory=list)
    decisions: int = 0
    fallbacks: int = 0
    recovered: int = 0
    refused_attempts: int = 0
    rule_refused_attempts: int = 0
    utterances: list[str] = field(default_factory=list)
    decision_log: list[Decision] = field(default_factory=list)
    public_events: list[tuple[str, str]] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    upstreams: dict[str, int] = field(default_factory=dict)
    trace_sample: list[str] = field(default_factory=list)
    #: Seat -> how many of the things it was told were false. Zero for every seat
    #: on a table with nothing that switches an ability off, which is what makes it
    #: readable as a check that the stratum below has a sample at all.
    misled: dict[int, int] = field(default_factory=dict)
    error: str | None = None


def _played(turn: Turn, action: dict) -> str:
    kind = turn.kind
    if kind == "speak":
        return "speaks" + (f" and names seat {action['slay']}"
                           if "slay" in action else "")
    if kind == "nominate":
        target = action["nominate"]
        return "passes" if target is None else f"nominates seat {target}"
    if kind == "vote":
        return "votes " + ("yes" if action["vote"] else "no")
    if kind == "divine":
        return "looks at seats " + ", ".join(str(s) for s in action["targets"])
    return f"{kind} seat {action['target']}"


def _record_decision(rec: GameRecord, policy, turn_no: int, day: int, turn: Turn,
                     action: dict) -> None:
    fell_back = getattr(policy, "last_fell_back", False)
    refusals = int(getattr(policy, "last_refusals", 0) or 0)
    rule_refusals = int(getattr(policy, "last_rule_refusals", 0) or 0)
    prompt_size = getattr(policy, "last_prompt_size", 0)
    reply_size = getattr(policy, "last_reply_size", 0)
    usage = getattr(policy, "last_usage", None)
    rec.decisions += 1
    rec.fallbacks += int(fell_back)
    if not fell_back and rule_refusals:
        rec.recovered += 1
    rec.refused_attempts += refusals
    rec.rule_refused_attempts += rule_refusals
    rec.decision_log.append(Decision(
        turn=turn_no, day=day, seat=turn.seat, kind=turn.kind,
        played=_played(turn, action), think=action.get("think", ""),
        refused=(str(getattr(policy, "last_refusal", "") or "") if refusals
                 else ""),
        refusals=refusals, rule_refusals=rule_refusals, fell_back=fell_back,
        served_by=getattr(policy, "last_upstream", ""),
        prompt_size=prompt_size,
        reply_size=reply_size,
        usage=usage,
    ))


def play_game(ref: BelfryReferee, policies: dict[int, object],
              audit: bool = True) -> GameRecord:
    """Run one table to a winner.

    Gate #1 is audited before every decision point and RAISES on a leak. It is on
    by default and stays that way: the property this arena exists to prove must not
    be something a caller can forget to switch on.
    """
    rec = GameRecord(script=ref.grim.script.name, seats=ref.n)
    rec.dealt = {s.index: s.dealt.key for s in ref.grim.seats}
    turn_no = 0
    try:
        while not ref.done():
            turn = ref.pending()
            if turn is None:
                break
            if turn_no >= MAX_DECISIONS:
                raise IllegalAction(
                    f"{MAX_DECISIONS} decisions without a winner; the referee is "
                    "not advancing and this is a rules bug, not a long game")
            if audit:
                assert_no_leak(ref)
            day, kind, seat = ref.day, turn.kind, turn.seat
            nominee = ref.nominee
            action = policies[seat].act(ref, seat)
            # Submit FIRST, so a refusal happens before anything is written down.
            # Recording and then submitting would put an illegal move in the scored
            # data at the moment the referee raised on it - laundered by ordering
            # alone, which is the defect the removed coercion in `changeling` had.
            ref.submit(seat, action)
            _record_decision(rec, policies[seat], turn_no, day, turn, action)
            # Snapshot the SAME decision's provenance before anything else can
            # overwrite the policy's last_* fields (the fallback's own act()
            # resets them). The vote record below carries this value, so a
            # scorer never re-derives it from aggregate totals or policy state.
            fell_back = getattr(policies[seat], "last_fell_back", False)
            turn_no += 1
            if kind == "speak":
                # What the referee PUBLISHED, not what the policy proposed: it
                # normalises whitespace and truncates, so the raw string would
                # leave the record holding text no seat ever saw.
                rec.utterances.append(ref.last_said)
            if kind == "vote" and nominee is not None:
                rec.votes.append(VoteRecord(
                    day=day, seat=seat, nominee=nominee, yes=action["vote"],
                    turn=turn_no - 1,
                    voter_evil=ref.grim.seat(seat).align is Align.EVIL,
                    nominee_evil=ref.grim.seat(nominee).align is Align.EVIL,
                    voter_alive=ref.grim.seat(seat).alive,
                    voter_misled=any(not r.truthful
                                     for r in ref.knowledge[seat]),
                    fell_back=fell_back))
    except Exception as exc:                  # a broken run is recorded, not hidden
        rec.error = f"{type(exc).__name__}: {exc}"
        if isinstance(exc, AssertionError):   # a leak is never scoreable
            raise

    rec.winner = ref.winner
    rec.reason = ref.reason
    rec.days = ref.day
    rec.final = {s.index: s.role.key for s in ref.grim.seats}
    rec.cause = ref.cause
    rec.misled = {s: sum(1 for r in ref.knowledge[s] if not r.truthful)
                  for s in range(ref.n)}
    rec.executions = [
        ExecutionRecord(day=e.day, seat=e.seat,
                        evil=ref.grim.seat(e.seat).align is Align.EVIL,
                        was_alive=e.was_alive, alive_before=e.alive_before,
                        evil_before=e.evil_before, by_vote=e.by_vote)
        for e in ref.executions]
    rec.alive = tuple(ref.grim.alive_seats())
    rec.public_events = list(ref.public_events)
    rec.log = list(ref.referee_log)

    served: Counter = Counter()
    traces: list[str] = []
    for policy in policies.values():
        served.update(getattr(policy, "upstreams", {}))
        traces.extend(getattr(policy, "trace", []))
    rec.upstreams = dict(served)
    seen: list[str] = []
    for line in traces:
        if line not in seen:
            seen.append(line)
    rec.trace_sample = seen[:8]
    return rec
