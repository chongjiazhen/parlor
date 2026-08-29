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
    #: the complaint that refused the most recent ATTEMPT. Not the trace's last
    #: line - that is the "N attempts failed, playing random" summary, which says a
    #: fallback happened and nothing about why.
    last_refusal: str = ""
    #: how many attempts on the most recent decision were refused, and how many of
    #: those the PARSER or the RULES refused rather than the network. Same fields
    #: and the same meaning as cabal's, because the integrity block that reads them
    #: is shared (``core/integrity.py``).
    last_refusals: int = 0
    last_rule_refusals: int = 0

    def act(self, ref: ChangelingReferee, seat: int) -> dict:
        self.last_fell_back = False
        self.last_refusal = ""
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_prompt_size = 0
        self.last_reply_size = 0
        self.last_usage = None
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
                action = parse_action(reply, ref, seat)
            except ParseError as exc:
                complaint = str(exc)
                self._refused(seat, attempt, "unparsed", str(exc))
                continue
            if ref.phase is Phase.VOTE and action["vote"] == seat:
                complaint = (f"seat {seat} cannot point at itself; choose from "
                             f"{ref.legal_votes(seat)}")
                self._refused(seat, attempt, "illegal", complaint)
                continue
            return action
        self.trace.append(
            f"seat {seat}: {self.retries + 1} attempts failed, playing random")
        self.last_fell_back = True
        self.last_upstream = ""          # nothing served it; the random policy did
        return self.fallback.act(ref, seat)

    def _refused(self, seat: int, attempt: int, kind: str, detail: str) -> None:
        """One place writes a refusal, so the trace, the per-decision census and the
        integrity block can never disagree about what happened.

        ``kind`` is ``transport`` | ``unparsed`` | ``illegal``, carried as an
        argument rather than parsed back off the rendered text: the clean-game count
        turns on whether the model or the network was at fault, and recovering that
        by string match against a human-facing message drifts the next time somebody
        rewords one. The rendered line is unchanged.
        """
        self.last_refusals += 1
        if kind != "transport":
            self.last_rule_refusals += 1
        text = detail if kind == "transport" else f"{kind} - {detail}"
        self.last_refusal = f"seat {seat} attempt {attempt}: {text}"
        self.trace.append(self.last_refusal)


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
    #: What the NIGHT actually TOLD this seat. Keyed on the DEALT card - the reveal
    #: is a historical fact and the deal is what produced it - but conditional on a
    #: reveal having happened, so a MEET card that met nobody is ``none`` rather
    #: than ``identity``. One of ``identity`` / ``positional`` / ``false`` /
    #: ``none``; derived by ``NightResult.knowledge_class``, argued in RULES.md.
    knowledge_class: str = "none"


@dataclass
class Decision:
    turn: int
    seat: int
    phase: str
    played: str
    think: str = ""
    #: why the last refused ATTEMPT on this decision was refused. Empty on a
    #: decision the model got right first time.
    #:
    #: Named ``refused`` rather than ``note`` so it means the same thing in both
    #: games: cabal's ``note`` is a seat's NOTEBOOK entry, a different field with a
    #: different life, and one name over two meanings is how a JSONL reader ends up
    #: counting notebook lines as refusals.
    #:
    #: **Widened 2026-08-27 (S9)** to a RECOVERED decision too, in step with cabal.
    #: Read it with ``fell_back``: set and False is recovered, set and True is a
    #: fallback, empty is clean.
    refused: str = ""
    #: attempts refused before this decision landed, and the subset the parser or
    #: the rules refused rather than the network.
    refusals: int = 0
    rule_refusals: int = 0
    fell_back: bool = False
    served_by: str = ""
    prompt_size: int = 0
    reply_size: int = 0
    usage: dict | None = None


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
    #: decisions the parser or the rules sent back at least once and the model then
    #: got RIGHT - the third outcome. Same three-way partition as cabal's, read by
    #: the shared ``core/integrity.py``.
    recovered: int = 0
    refused_attempts: int = 0
    rule_refused_attempts: int = 0
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
        turn=turn, seat=seat, phase=phase, played=played,
        think=action.get("think", ""),
        # The refusal string that produced a fallback, carried on the DECISION, so
        # the reason is a CENSUS in the JSONL rather than a sampled trace and an
        # end-of-run report - neither of which is readable mid-run. cabal does the
        # same on the same field name since 2026-08-27 (S4).
        refused=(str(getattr(policy, "last_refusal", "") or "") if refusals
                 else ""),
        refusals=refusals, rule_refusals=rule_refusals,
        fell_back=fell_back,
        served_by=getattr(policy, "last_upstream", ""),
        prompt_size=prompt_size,
        reply_size=reply_size,
        usage=usage,
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
                # What `speak` PUBLISHED, not what the policy proposed. speak()
                # normalises whitespace and truncates to MAX_UTTERANCE_CHARS, so
                # storing the raw string left the record holding text no seat ever
                # saw - anything reading `utterances` would then be analysing a
                # different corpus from the one the models were shown.
                rec.utterances.append(ref.speak(seat, action["say"]))
                _record_decision(rec, policies[seat], turn, seat, "discuss",
                                 "speaks", action)
                turn += 1
            ref.close_round()

        for seat in range(ref.n):
            if audit:
                assert_no_leak(ref)
            action = policies[seat].act(ref, seat)
            target = action["vote"]
            # NOT coerced. This used to rewrite a self-vote to the first legal seat
            # and record the rewritten target, which contradicted this module's own
            # contract one screen up and escaped the fallback count: a policy other
            # than the two here - a model-driven night policy, a test double - got
            # its illegal move laundered into the scored data with no trace.
            # `ref.cast` refuses it below; let it.
            # Cast FIRST, so the referee's refusal happens before anything is
            # written down. Recording the vote and then casting meant an illegal
            # move was already in `rec.votes` when cast raised - laundered into the
            # scored data by ordering alone, which is the same defect the removed
            # coercion had.
            ref.cast(seat, target)
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
                knowledge_class=ref.night.knowledge_class(seat),
            ))
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
