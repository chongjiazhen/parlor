"""Player policies and the game driver.

Same shape as ``games/cabal/player.py`` and the same contract: a policy answers one
question per decision, the referee refuses an illegal move rather than coercing it,
the seat is told why, and every fallback to random is counted. Silently coercing a
bad move hides an agent bug; silently dropping one poisons the gate numbers.

**Night targets are chosen at random, not by a model.** A spotter that looks at a
random seat still gets real information and a swapper that robs at random still
creates divergence, so the day is unaffected in kind - and this keeps the night
reproducible from the seed alone, which is what makes two runs of one seed
comparable. It also holds the game at ~15 model calls, which is the throughput this
rung was queued for. Whether a model chooses its own night target is a variant axis
to MEASURE later, not a default to assume; see RULES.md.
"""

from __future__ import annotations

import random
import time
from collections import Counter
from dataclasses import dataclass, field

from core.backends import Backend
from core.replies import ParseError, parse_index, read_reply
from games.changeling.audit import assert_no_leak
from games.changeling.referee import ChangelingReferee, IllegalAction, Phase
from games.changeling.roles import Side


#: Every key the referee ever asks for, for the salvage path.
ACTION_KEYS = ("say", "vote", "think")


def parse_action(reply: str, ref: ChangelingReferee, seat: int) -> dict:
    """Reply text -> a normalised action for the referee's current phase.

    ``think`` is kept for the referee-side log and reaches no channel a seat can
    read. Only ``say`` is published.
    """
    obj = read_reply(reply, ACTION_KEYS)
    out = {"think": str(obj.get("think", ""))[:400]}
    if ref.phase is Phase.DISCUSS:
        said = " ".join(str(obj.get("say", "")).split())
        if not said:
            raise ParseError('missing "say" (an empty utterance is not a move)')
        out["say"] = said
    elif ref.phase is Phase.VOTE:
        if "vote" not in obj:
            raise ParseError('missing "vote"')
        out["vote"] = parse_index(obj["vote"], ref.n, noun="seat")
    else:
        raise ParseError(f"nothing to parse in phase {ref.phase.value}")
    return out


@dataclass
class RandomPolicy:
    """Legal noise. The control arm, and the only honest source of this game's
    chance baseline - RULES.md refuses to assert one by arithmetic."""

    rng: random.Random = field(default_factory=random.Random)

    def act(self, ref: ChangelingReferee, seat: int) -> dict:
        if ref.phase is Phase.DISCUSS:
            return {"say": self.rng.choice([
                "I slept badly and I have nothing yet.",
                f"Seat {self.rng.choice(ref.legal_votes(seat))} is quiet.",
                "I am what I went to sleep as, for whatever that is worth.",
                "Someone here woke up and moved. Say who.",
            ])}
        if ref.phase is Phase.VOTE:
            return {"vote": self.rng.choice(ref.legal_votes(seat))}
        raise IllegalAction(f"no action in phase {ref.phase.value}")


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

    def act(self, ref: ChangelingReferee, seat: int) -> dict:
        self.last_fell_back = False
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
            except Exception as exc:                      # transport, not rules
                complaint = f"the call failed ({type(exc).__name__}: {exc})"
                self.trace.append(f"seat {seat} attempt {attempt}: {complaint}")
                if self.backoff and attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt))
                continue
            try:
                action = parse_action(reply, ref, seat)
            except ParseError as exc:
                complaint = str(exc)
                self.trace.append(f"seat {seat} attempt {attempt}: unparsed - {exc}")
                continue
            if ref.phase is Phase.VOTE and action["vote"] == seat:
                complaint = (f"seat {seat} cannot point at itself; choose from "
                             f"{ref.legal_votes(seat)}")
                self.trace.append(f"seat {seat} attempt {attempt}: illegal - "
                                  f"{complaint}")
                continue
            return action
        self.trace.append(
            f"seat {seat}: {self.retries + 1} attempts failed, playing random")
        self.last_fell_back = True
        self.last_upstream = ""          # nothing served it; the random policy did
        return self.fallback.act(ref, seat)


# ---- driver ---------------------------------------------------------------

@dataclass
class VoteRecord:
    """One accusation, with everything a deduction gate would stratify on.

    Three separate booleans about the voter, because in this game they come apart
    and collapsing them is how a number stops meaning anything: which side it WINS
    with (``voter_holds_pack``), which side it THINKS it is on
    (``voter_believes_pack``), and whether those agree (``voter_diverged``).
    """

    seat: int
    target: int
    voter_holds_pack: bool
    voter_believes_pack: bool
    voter_diverged: bool
    target_holds_pack: bool
    #: What the NIGHT told this seat, keyed on its DEALT card - the reveal is a
    #: historical fact and the deal is what produced it. One of
    #: ``identity`` / ``positional`` / ``false`` / ``none``; see RULES.md.
    knowledge_class: str = "none"


@dataclass
class Decision:
    turn: int
    seat: int
    phase: str
    played: str
    think: str = ""
    note: str = ""
    fell_back: bool = False
    served_by: str = ""


@dataclass
class GameRecord:
    """Everything a scorer needs, plus honesty about degradation."""

    winner: str | None = None
    reason: str = ""
    accused: tuple[int, ...] = ()
    #: Dawn holdings and beliefs, side by side. Both, because a record that kept
    #: only one of them could not answer the question this game exists to ask.
    truth: dict[int, str] = field(default_factory=dict)
    belief: dict[int, str] = field(default_factory=dict)
    dealt: dict[int, str] = field(default_factory=dict)
    diverged: tuple[int, ...] = ()
    votes: list[VoteRecord] = field(default_factory=list)
    decisions: int = 0
    fallbacks: int = 0
    utterances: list[str] = field(default_factory=list)
    decision_log: list[Decision] = field(default_factory=list)
    public_events: list[tuple[str, str]] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    upstreams: dict[str, int] = field(default_factory=dict)
    trace_sample: list[str] = field(default_factory=list)
    error: str | None = None
    theme: str = ""


def _record_decision(rec: GameRecord, policy, turn: int, seat: int, phase: str,
                     played: str, action: dict) -> None:
    fell_back = getattr(policy, "last_fell_back", False)
    rec.decisions += 1
    rec.fallbacks += int(fell_back)
    rec.decision_log.append(Decision(
        turn=turn, seat=seat, phase=phase, played=played,
        think=action.get("think", ""),
        # The refusal string that produced a fallback, carried on the DECISION.
        # The cabal JSONL records `note: ""` here and its refusal diagnosis lives
        # only in a sampled trace and an end-of-run report, which is unreadable
        # mid-run and not a census afterwards. Same bug, not repeated.
        note=(policy.trace[-1] if fell_back and getattr(policy, "trace", None)
              else ""),
        fell_back=fell_back,
        served_by=getattr(policy, "last_upstream", ""),
    ))


def play_game(ref: ChangelingReferee, policies: dict[int, object],
              audit: bool = True) -> GameRecord:
    """Run one night-and-day to a winner.

    Gate #1 is audited before every decision point and RAISES on a leak. It is on
    by default and stays that way: the property this arena exists to prove must not
    be something a caller can forget to switch on.
    """
    rec = GameRecord(theme=ref.theme.name)
    turn = 0
    try:
        if audit:
            assert_no_leak(ref)
        while ref.phase is Phase.DISCUSS:
            for seat in ref.speaking_order():
                if audit:
                    assert_no_leak(ref)
                action = policies[seat].act(ref, seat)
                ref.speak(seat, action["say"])
                rec.utterances.append(action["say"])
                _record_decision(rec, policies[seat], turn, seat, "discuss",
                                 "speaks", action)
                turn += 1
            ref.close_round()

        for seat in range(ref.n):
            if audit:
                assert_no_leak(ref)
            action = policies[seat].act(ref, seat)
            target = action["vote"]
            if target == seat:                # a fallback can only pick legally
                target = ref.legal_votes(seat)[0]
            _record_decision(rec, policies[seat], turn, seat, "vote",
                             f"points at seat {target}", action)
            turn += 1
            rec.votes.append(VoteRecord(
                seat=seat,
                target=target,
                voter_holds_pack=ref.holds(seat).side is Side.PACK,
                voter_believes_pack=ref.believes(seat).side is Side.PACK,
                voter_diverged=seat in ref.night.diverged(),
                target_holds_pack=ref.holds(target).side is Side.PACK,
                knowledge_class=ref.night.dealt[seat].knowledge_class,
            ))
            ref.cast(seat, target)
    except Exception as exc:                  # a broken run is recorded, not hidden
        rec.error = f"{type(exc).__name__}: {exc}"
        if isinstance(exc, AssertionError):   # a leak is never scoreable
            raise

    rec.winner = ref.winner
    rec.reason = ref.reason
    rec.accused = ref.accused
    rec.truth = {s: ref.holds(s).key for s in range(ref.n)}
    rec.belief = {s: ref.believes(s).key for s in range(ref.n)}
    rec.dealt = {s: ref.night.dealt[s].key for s in range(ref.n)}
    rec.diverged = tuple(sorted(ref.night.diverged()))
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
