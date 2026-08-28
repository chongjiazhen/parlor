"""Player policies and the game driver.

A policy answers one question: given a seat's own context and the referee's ask,
what does that seat do? Two implementations, the same pair both sibling rungs
ship:

  - ``RandomPolicy`` - legal noise. Runs the state machine with no model, and is
    the fallback when a model will not produce a legal move.
  - ``LLMPolicy`` - one ``core.backends.Backend`` call per decision, with a
    bounded refuse-and-retell loop. An unparseable or illegal reply is fed back to
    the SAME seat with the referee's own error text, then the seat falls back to
    random and the driver counts it.

Silently coercing a bad move would hide a real agent bug and silently dropping one
would poison the numbers, so the referee refuses, the policy is told why, and
every fallback is counted.

**What this driver records that the sibling rungs cannot.** The referee knows
every card that was drawn, passed and dropped, so ``DrawRecord`` writes the whole
cascade down beside the public enactment: what the proposer held, what it passed
on, what it discarded, and what came out. That is the ground truth a claim is
scored against, and it is also what separates a lie from a forced move - a seat
that drew three writs had no legal way to enact a charter, and a scorer that
counted the enactment against it would be measuring the deck. It is referee-side
and never enters ``render_context``; gate #1 is about the bytes a seat receives.
"""

from __future__ import annotations

import random
import time
from collections import Counter
from dataclasses import dataclass, field

from core.backends import Backend
from core.replies import ParseError, parse_bool, parse_index, read_reply
from games.quorum.audit import assert_no_leak
from games.quorum.referee import IllegalAction, Phase, QuorumReferee
from games.quorum.roles import ADVANCES, Card, Side


# ---- reply parsing --------------------------------------------------------
#
# The generic half - JSON out of prose, salvage of a truncated reply, word-to-value
# coercion - lives in ``core.replies``. What stays here is the part that IS about
# this game: which key each phase asks for, and what a legal value means.

#: every key the referee ever asks for, for the salvage path
ACTION_KEYS = ("nominate", "say", "vote", "discard", "target", "think")


def parse_action(reply: str, ref: QuorumReferee, seat: int) -> dict:
    """Reply text -> a normalised action dict for the referee's current phase.

    Keys out: ``nominate`` | ``say`` | ``vote`` | ``discard`` | ``target``, plus the
    private ``think``, kept for the referee-side log and never for the table.

    ``discard`` is an INDEX into the hand rather than a card name, and that is a
    decision rather than a convenience. A hand can hold two of the same kind, so a
    name does not identify which card is meant; and asking for an index keeps the
    reply from having to spell a card at all, which is one less way for a seat's
    own reply to carry a term the audit would have to reason about.
    """
    obj = read_reply(reply, ACTION_KEYS)
    out = {"think": str(obj.get("think", ""))[:400]}
    p = ref.phase
    if p is Phase.NOMINATE:
        if "nominate" not in obj:
            raise ParseError('missing "nominate"')
        out["nominate"] = parse_index(obj["nominate"], ref.n, noun="seat")
    elif p is Phase.DISCUSS:
        said = " ".join(str(obj.get("say", "")).split())
        if not said:
            raise ParseError('missing "say" (an empty utterance is not a move)')
        out["say"] = said
    elif p is Phase.VOTE:
        if "vote" not in obj:
            raise ParseError('missing "vote"')
        out["vote"] = parse_bool(obj["vote"])
    elif p in (Phase.PROPOSER_DISCARD, Phase.ENACTOR_DISCARD):
        if "discard" not in obj:
            raise ParseError('missing "discard"')
        held = len(ref.entitled_hand(seat) or ())
        if not held:
            raise ParseError(f"seat {seat} holds no cards at this step")
        out["discard"] = parse_index(obj["discard"], held, noun="card")
    elif p is Phase.POWER:
        if "target" not in obj:
            raise ParseError('missing "target"')
        out["target"] = parse_index(obj["target"], ref.n, noun="seat")
    else:
        raise ParseError(f"nothing to parse in phase {p.value}")
    return out


def played_summary(phase: Phase, action: dict) -> str:
    """One line for the decision log. Never names a card: the log is referee-side,
    but it is also quoted into transcripts, and a summary that spelled the discard
    would put the cascade's secret one copy-paste from a seat's view."""
    if phase is Phase.NOMINATE:
        return f"nominate seat {action['nominate']}"
    if phase is Phase.DISCUSS:
        return f'say "{action["say"]}"'
    if phase is Phase.VOTE:
        return "vote yes" if action["vote"] else "vote no"
    if phase in (Phase.PROPOSER_DISCARD, Phase.ENACTOR_DISCARD):
        return f"discard card {action['discard']} of the hand"
    if phase is Phase.POWER:
        return f"target seat {action['target']}"
    return "-"


# ---- policies -------------------------------------------------------------

@dataclass
class RandomPolicy:
    """Legal noise. Never illegal, never interesting - the control arm."""

    rng: random.Random = field(default_factory=random.Random)
    #: biased up so governments actually seat and the deck gets drawn
    approve_rate: float = 0.65

    def act(self, ref: QuorumReferee, seat: int) -> dict:
        p = ref.phase
        if p is Phase.NOMINATE:
            return {"nominate": self.rng.choice(ref.eligible_nominees())}
        if p is Phase.DISCUSS:
            return {"say": self.rng.choice([
                "I have nothing to go on yet.",
                f"Seat {self.rng.choice(ref.living())} worries me.",
                "This pairing looks fine to me.",
                "I would rather wait for the next round.",
            ])}
        if p is Phase.VOTE:
            return {"vote": self.rng.random() < self.approve_rate}
        if p in (Phase.PROPOSER_DISCARD, Phase.ENACTOR_DISCARD):
            hand = ref.entitled_hand(seat) or []
            if not hand:
                raise IllegalAction(f"seat {seat} holds no cards at this step")
            # A random seat plays the deck, not a side: it drops a uniformly
            # chosen card. Anything smarter here would be a heuristic arm wearing
            # the control's name, and the control is what every number is read
            # against.
            return {"discard": self.rng.randrange(len(hand))}
        if p is Phase.POWER:
            return {"target": self.rng.choice(ref.legal_power_targets(seat))}
        raise IllegalAction(f"no action in phase {p.value}")


@dataclass
class LLMPolicy:
    """One model call per decision, with a bounded refuse-and-retell loop."""

    backend: Backend
    retries: int = 2
    #: Seconds to wait after a TRANSPORT failure, doubling each time. A free cloud
    #: tier answers a burst with 429s, and retrying instantly just burns the retry
    #: budget and lands the seat on the random fallback - which then reads as "the
    #: model played badly" in the eval.
    backoff: float = 2.0
    fallback: RandomPolicy = field(default_factory=RandomPolicy)
    trace: list[str] = field(default_factory=list)
    upstreams: Counter = field(default_factory=Counter)
    last_fell_back: bool = False
    last_upstream: str = ""
    last_refusal: str = ""
    last_refusals: int = 0
    last_rule_refusals: int = 0

    def act(self, ref: QuorumReferee, seat: int) -> dict:
        self.last_fell_back = False
        self.last_refusal = ""
        self.last_refusals = 0
        self.last_rule_refusals = 0
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
            try:
                self._precheck(ref, seat, action)
            except IllegalAction as exc:
                complaint = str(exc)
                self._refused(seat, attempt, "illegal", str(exc))
                continue
            return action
        self.trace.append(
            f"seat {seat}: {self.retries + 1} attempts failed, playing random")
        self.last_fell_back = True
        self.last_upstream = ""          # nothing served it; the random policy did
        return self.fallback.act(ref, seat)

    def _refused(self, seat: int, attempt: int, kind: str, detail: str) -> None:
        """One place writes a refusal, so the trace and the integrity counts can
        never disagree about what happened. ``kind`` is an argument rather than a
        prefix parsed back off the text: the clean-game count turns on whether the
        model or the network was at fault, and recovering that by string match
        against a message written for a human is how the answer drifts."""
        self.last_refusals += 1
        if kind != "transport":
            self.last_rule_refusals += 1
        text = detail if kind == "transport" else f"{kind} - {detail}"
        self.last_refusal = f"seat {seat} attempt {attempt}: {text}"
        self.trace.append(self.last_refusal)

    def _precheck(self, ref: QuorumReferee, seat: int, action: dict) -> None:
        """Catch the illegalities the seat can still fix, using the referee's own
        validators so the complaint the seat is told is the complaint the referee
        would raise."""
        if ref.phase is Phase.NOMINATE:
            ref.validate_nomination(seat, action["nominate"])
        elif ref.phase in (Phase.PROPOSER_DISCARD, Phase.ENACTOR_DISCARD):
            ref.validate_discard(seat, action["discard"])
        elif ref.phase is Phase.POWER:
            ref.validate_power_target(seat, action["target"])


# ---- records --------------------------------------------------------------

@dataclass
class Decision:
    """One decision as it was made, plus the private reasoning behind it.

    ``think`` is referee-side and stays referee-side. Gate #1 is about the bytes a
    seat's model receives, and nothing here enters ``render_context``; the driver
    still hands ``speak()`` only ``say``.
    """

    turn: int
    seat: int
    phase: str
    played: str
    think: str = ""
    refused: str = ""
    refusals: int = 0
    rule_refusals: int = 0
    fell_back: bool = False
    served_by: str = ""


@dataclass
class DrawRecord:
    """One legislative event, from the referee's side of the table.

    This is the rung's whole measurement surface, so it is written down whether or
    not a scorer exists yet: a claim about a draw is scored against ``drew``, and
    whether an enactment was FORCED is a fact about ``drew`` rather than about the
    seat that made it. Card kinds are stored by their canonical key, not by a
    theme's display name, so a record survives a reskin.
    """

    turn: int
    proposer: int
    enactor: int
    drew: list[str]                     # the three, in the order dealt
    passed: list[str]                   # the two handed on
    proposer_dropped: str
    enactor_dropped: str
    enacted: str
    #: True when every card the proposer drew advanced the same side, so whoever
    #: held the office had no legal way to enact the other. The single most useful
    #: column here: it is the difference between a lie and a rule.
    forced: bool = False


@dataclass
class VoteRecord:
    turn: int
    seat: int
    approved: bool
    nominee: int
    seat_side: str
    nominee_side: str
    #: what the DEAL told this seat, not which side it wins with. A majority seat
    #: and a minority seat can both be voting blind on the nominee's identity, and
    #: any stratum that conflated the two would be reading the win condition rather
    #: than the knowledge.
    knowledge_class: str = "none"


@dataclass
class GameRecord:
    assignment: dict[int, str]
    turns: int = 0
    decisions: int = 0
    fallbacks: int = 0
    #: decisions the parser or the rules sent back and the model then got right
    recovered: int = 0
    refused_attempts: int = 0
    rule_refused_attempts: int = 0
    winner: str = ""
    win_reason: str = ""
    charters: int = 0
    writs: int = 0
    error: str = ""
    decision_log: list[Decision] = field(default_factory=list)
    draws: list[DrawRecord] = field(default_factory=list)
    votes: list[VoteRecord] = field(default_factory=list)
    utterances: list[str] = field(default_factory=list)

    @property
    def fallback_rate(self) -> float:
        """Every number this rung ever reports ships beside this one, and the
        scorer voids above 10% - a decision no model could make legally is played
        at random, and a run that hides that is the random policy wearing a
        model's name."""
        return self.fallbacks / self.decisions if self.decisions else 0.0

    @property
    def forced_enactments(self) -> int:
        return sum(1 for d in self.draws if d.forced)


# ---- driver ---------------------------------------------------------------

def _knowledge_class(ref: QuorumReferee, seat: int) -> str:
    """Derived from what the seat was told, never from the role key, so a variant
    that changes what the deal reveals changes the stratum with it."""
    labels = {k.label for k in ref.entitled_knowledge(seat)}
    if any(l == "fellow-minority" for l in labels):
        return "identity"
    if any(l.startswith("inspected-") for l in labels):
        return "inspected"
    return "none"


def play_game(
    ref: QuorumReferee,
    policies: dict[int, object],
    max_turns: int = 600,
    audit: bool = True,
) -> GameRecord:
    """Run one game to a winner. ``policies`` maps seat -> anything with ``act``.

    Gate #1 is audited before every decision point and RAISES on a leak. It is on
    by default, and it stays that way for every caller: the eval lane in this repo
    once forgot to pass an opt-in callback and ran live models unaudited for a
    session. Pass ``audit=False`` only to measure the driver's own cost.
    """
    rec = GameRecord(assignment={s: r.key for s, r in ref.assignment.items()})

    def decide(seat: int) -> dict:
        rec.decisions += 1
        phase = ref.phase
        policy = policies[seat]
        action = policy.act(ref, seat)
        fell_back = bool(getattr(policy, "last_fell_back", False))
        refusals = int(getattr(policy, "last_refusals", 0) or 0)
        rule_refusals = int(getattr(policy, "last_rule_refusals", 0) or 0)
        if fell_back:
            rec.fallbacks += 1
        elif rule_refusals:
            rec.recovered += 1
        rec.refused_attempts += refusals
        rec.rule_refused_attempts += rule_refusals
        rec.decision_log.append(Decision(
            turn=rec.turns, seat=seat, phase=phase.value,
            played=played_summary(phase, action),
            think=str(action.get("think", "")),
            refused=(str(getattr(policy, "last_refusal", "") or "")
                     if refusals else ""),
            refusals=refusals, rule_refusals=rule_refusals, fell_back=fell_back,
            served_by=("" if fell_back
                       else str(getattr(policy, "last_upstream", "") or "")),
        ))
        return action

    pending: dict | None = None      # the half-built DrawRecord for this event

    while ref.phase is not Phase.DONE:
        rec.turns += 1
        if rec.turns > max_turns:
            rec.error = "referee failed to terminate"
            break
        if audit:
            assert_no_leak(ref)

        p = ref.phase
        if p is Phase.NOMINATE:
            ref.nominate(ref.proposer, decide(ref.proposer)["nominate"])
        elif p is Phase.DISCUSS:
            seat = ref.next_speaker()
            action = decide(seat)
            # only "say" crosses to the table; "think" is dropped here, on purpose
            ref.speak(seat, action["say"])
            rec.utterances.append(f'seat {seat}: {action["say"]}')
        elif p is Phase.VOTE:
            nominee = ref.nominee
            votes: dict[int, bool] = {}
            for seat in ref.living():
                klass = _knowledge_class(ref, seat)
                votes[seat] = decide(seat)["vote"]
                rec.votes.append(VoteRecord(
                    turn=rec.turns, seat=seat, approved=votes[seat],
                    nominee=nominee,
                    seat_side=ref.assignment[seat].side.value,
                    nominee_side=ref.assignment[nominee].side.value,
                    knowledge_class=klass,
                ))
            ref.vote(votes)
            if ref.phase is Phase.PROPOSER_DISCARD:
                drew = list(ref.proposer_hand)
                pending = {
                    "turn": rec.turns, "proposer": ref.proposer,
                    "enactor": ref.enactor, "drew": [c.value for c in drew],
                    "forced": len({ADVANCES[c] for c in drew}) == 1,
                }
        elif p is Phase.PROPOSER_DISCARD:
            seat = ref.proposer
            index = decide(seat)["discard"]
            dropped = ref.entitled_hand(seat)[index]
            ref.proposer_discard(seat, index)
            if pending is not None:
                pending["proposer_dropped"] = dropped.value
                pending["passed"] = [c.value for c in ref.enactor_hand]
        elif p is Phase.ENACTOR_DISCARD:
            seat = ref.enactor
            index = decide(seat)["discard"]
            hand = ref.entitled_hand(seat)
            dropped = hand[index]
            enacted = hand[1 - index]
            ref.enactor_discard(seat, index)
            if pending is not None:
                pending["enactor_dropped"] = dropped.value
                pending["enacted"] = enacted.value
                rec.draws.append(DrawRecord(**pending))
                pending = None
        elif p is Phase.POWER:
            ref.use_power(ref.proposer, decide(ref.proposer)["target"])

    rec.winner = ref.winner.value if ref.winner else ""
    rec.win_reason = ref.win_reason
    rec.charters = ref.charters
    rec.writs = ref.writs
    return rec
