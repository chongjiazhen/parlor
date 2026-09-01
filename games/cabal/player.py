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
A reply's ``note`` goes to ``referee.note()``, which files it under that seat and
shows it back to that seat alone - a private channel, and still not a public one.
"""

from __future__ import annotations

import random
import time
from collections import Counter
from dataclasses import dataclass, field

from core import callcost
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
ACTION_KEYS = ("team", "say", "vote", "card", "target", "think", "note")

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
    private ``think`` (kept for the transcript-side log, never for the table) and
    the optional ``note`` (filed in this seat's own notebook, read back only by
    this seat).

    ``note`` is optional in every phase and its absence is never an error: the
    referee asks for a move, and the notebook is the seat's own business. Nothing
    here refuses a long one either - the referee truncates - because burning a
    retry on a seat's private bookkeeping would turn housekeeping into a fallback,
    and a fallback is a decision no model made.
    """
    obj = read_reply(reply, ACTION_KEYS)
    out = {"think": str(obj.get("think", ""))[:400],
           "note": str(obj.get("note", ""))[:400]}
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
            # evil the night named. `1/len` of this set is the chance baseline gate
            # #3b beats, and it comes from the referee so the control and the bar
            # cannot disagree - at 5p with a hunter that sees its ally it is 1/3,
            # and under any variant that changes what the night says it is not.
            return {"target": self.rng.choice(ref.legal_hunt_targets(seat))}
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
    #: Every upstream that answered an attempt on current decision. A fallback
    #: through more than one route cannot honestly belong to its final retry.
    last_attempted_upstreams: list[str] = field(default_factory=list)
    #: the complaint that refused the most recent ATTEMPT - a transport failure, an
    #: unparsed reply, an illegal move. Deliberately not the trace's last line: that
    #: is the "N attempts failed, playing random" summary, which says a fallback
    #: happened and nothing about why, and a census of those is no diagnosis at all.
    last_refusal: str = ""
    #: how many attempts on the most recent decision were refused, and how many of
    #: those the PARSER or the RULES refused rather than the network. Both, because
    #: they answer different questions: a 429 says nothing about how the model
    #: plays, an unparsed or illegal reply says everything. A decision with
    #: ``last_refusals`` above zero and ``last_fell_back`` False is the third
    #: outcome this record used to have no room for - the model got there, but only
    #: after the referee sent it back.
    last_refusals: int = 0
    last_rule_refusals: int = 0

    def act(self, ref: CabalReferee, seat: int) -> dict:
        self.last_fell_back = False
        self.last_upstream = ""
        self.last_attempted_upstreams = []
        self.last_refusal = ""
        self.last_refusals = 0
        self.last_rule_refusals = 0
        callcost.forget(self)
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
                self.last_attempted_upstreams.append(served_by)
                callcost.note(self, prompt, reply, self.backend)
            except Exception as exc:                      # transport, not rules
                complaint = f"the call failed ({type(exc).__name__}: {exc})"
                self._refused(seat, attempt, "transport", complaint)
                if self.backoff and attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt))
                continue
            try:
                action = parse_action(reply, ref)
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
        self.trace.append(f"seat {seat}: {self.retries + 1} attempts failed, playing random")
        self.last_fell_back = True
        return self.fallback.act(ref, seat)

    def _refused(self, seat: int, attempt: int, kind: str, detail: str) -> None:
        """One place writes a refusal, so the trace, the per-decision census and the
        integrity block can never disagree about what happened.

        ``kind`` is ``transport`` | ``unparsed`` | ``illegal``, and it is an argument
        rather than a prefix parsed back off the text: the clean-game count turns on
        whether the model or the network was at fault, and recovering that by string
        match against a message written for a human is how the answer drifts the next
        time somebody rewords one. The rendered line is unchanged - a transport
        complaint already reads as its own sentence.
        """
        self.last_refusals += 1
        if kind != "transport":
            self.last_rule_refusals += 1
        text = detail if kind == "transport" else f"{kind} - {detail}"
        self.last_refusal = f"seat {seat} attempt {attempt}: {text}"
        self.trace.append(self.last_refusal)

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
    #: did this seat KNOW, from the night, that one of THESE seats is evil? Kept
    #: for the decision audit. It is team-conditional, so it is the wrong field to
    #: stratify a gate on: a seat can be "blind" about this team while still
    #: holding night knowledge that shapes how it votes on every other one.
    knew_evil_on_team: bool = False
    #: what the night told this SEAT, regardless of team - the field the gate
    #: stratifies on.
    #:
    #: Deliberately NOT the good/evil vocabulary. Those are orthogonal axes: which
    #: side a seat wins with (``seat_is_evil``) versus what it was told. A GOOD
    #: seat can hold identity knowledge - the seer does - so labelling its class
    #: "evil" put two opposite meanings of the word on one seat in the scorer, and
    #: `find_leaks` is naive substring matching by design.
    #:
    #:   ``"identity"`` - the night NAMED specific seats' allegiance: the seer, and
    #:      each evil seat, which is named its partner.
    #:   ``"aura"`` - an ambiguous pair only. The watcher learns two seats of which
    #:      exactly one is evil; at 5 seats that certifies taint outright on some
    #:      team shapes and bounds it on the rest, so it is NOT blind.
    #:   ``"none"`` - the night said nothing. The only population whose votes are
    #:      deduction, and the only one gate #3a is scored on.
    #:
    #: A CLASS, not a bool, so the strata, the watcher question, and every future
    #: knowledge variant fall out of one field without a schema change - the same
    #: trap as a hardcoded baseline, avoided once.
    knowledge_class: str = "none"
    #: HOW MANY evil seats the proposed team carried. ``team_has_evil`` is this
    #: thresholded at 1, which throws away the 1-vs-2 contrast - and at 5 seats a
    #: clean team is rare (P~0.18), so the binary estimator's precision is capped
    #: by its thinnest cell while a well-populated comparison sits unused. Graded
    #: taint uses every vote against every level.
    team_evil_count: int = 0
    #: Driver turn for joining this vote to its per-decision upstream provenance.
    #: A seat votes repeatedly, so seat alone cannot identify which model answered.
    turn: int = 0


@dataclass
class Decision(callcost.CallCost):
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
    #: what this seat filed in its own notebook on this decision, as stored (the
    #: referee's stamp and truncation applied), or "" if it wrote nothing. Kept for
    #: the same reason ``think`` is: a post-game read wants the reasoning a seat
    #: chose to CARRY, which is a different and usually sharper thing than the
    #: reasoning it happened to have.
    note: str = ""
    #: why the last refused ATTEMPT on this decision was refused - the trace line
    #: the policy wrote. Empty on a decision the model got right first time.
    #:
    #: A field of its own rather than a second meaning for ``note``: the notebook
    #: is off on most runs and on for some, so one field over two meanings would
    #: make "how many refusals did this run have" unanswerable from the JSONL
    #: without knowing which. Before this the reason existed only in
    #: ``trace_sample`` (8 per game) and the end-of-run report (deduped, capped,
    #: and absent until the run ends) - neither a census, and the second unreadable
    #: while a six-hour run is still going.
    #:
    #: **Widened 2026-08-27 (S9): it is now written on a RECOVERED decision too**,
    #: not only on one that fell back. A refused-then-corrected decision is the
    #: third outcome, and it used to be recorded as indistinguishable from a clean
    #: one. Read it with ``fell_back``: set and False is recovered, set and True is
    #: a fallback, empty is clean.
    refused: str = ""
    #: how many attempts were refused before this decision landed, and how many of
    #: those the parser or the rules refused rather than the network. Only the
    #: second kind is evidence about the model, and only the second kind costs a
    #: game its clean-game count.
    refusals: int = 0
    rule_refusals: int = 0
    fell_back: bool = False
    #: which upstream actually answered THIS decision. Under a routing alias the
    #: gateway picks per request, so a per-run mix cannot tell you whether the model
    #: that misread the hunt is the one that voted well.
    served_by: str = ""
    #: Served upstreams for every attempt. ``served_by`` is empty on a fallback
    #: that crossed upstreams, because no one upstream owns random's final move.
    attempted_upstreams: list[str] = field(default_factory=list)


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
    #: decisions the parser or the rules sent back at least once and the model then
    #: got RIGHT - the third outcome, invisible until S9 because it was counted with
    #: the decisions nothing was wrong with. ``fallbacks``, ``recovered`` and the
    #: remainder partition ``decisions``; a decision that only ever failed in
    #: TRANSPORT is not recovered, because a 429 is not the model getting it wrong.
    recovered: int = 0
    #: attempts, not decisions - the diagnostic behind the two counts above, and
    #: either may exceed ``decisions`` on a bad network.
    refused_attempts: int = 0
    rule_refused_attempts: int = 0
    decisions: int = 0
    utterances: list[str] = field(default_factory=list)
    #: every decision in order, with the private reasoning behind it. Referee-side
    #: only - this is what a post-game read needs and no seat ever sees.
    decision_log: list[Decision] = field(default_factory=list)
    #: Both public channels verbatim, in the order the referee wrote them:
    #: ("event", ...) referee-authored | ("speech:<seat>", ...) player-authored.
    #: Kept so a transcript renders from what was actually said rather than from a
    #: second implementation of the rules run backwards over end state. Private
    #: ``think`` is discarded by the driver and is in neither channel, and a seat's
    #: notebook is in neither either - it goes back only to the seat that wrote it.
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
        refusals = int(getattr(policies[seat], "last_refusals", 0) or 0)
        rule_refusals = int(getattr(policies[seat], "last_rule_refusals", 0) or 0)
        if fell_back:
            rec.fallbacks += 1
        elif rule_refusals:
            rec.recovered += 1
        rec.refused_attempts += refusals
        rec.rule_refused_attempts += rule_refusals
        # filed before the move is applied, so a note written about THIS board is
        # dated to this board. It is a no-op when the notebook is off.
        stored = ref.note(seat, action.get("note", ""))
        attempted_upstreams = list(
            getattr(policies[seat], "last_attempted_upstreams", []) or [])
        served_by = str(getattr(policies[seat], "last_upstream", "") or "")
        if fell_back and len(set(attempted_upstreams)) != 1:
            served_by = ""
        rec.decision_log.append(Decision(
            turn=rec.turns, seat=seat, phase=phase.value,
            played=played_summary(phase, action),
            think=str(action.get("think", "")), note=stored or "",
            refused=(str(getattr(policies[seat], "last_refusal", "") or "")
                     if refusals else ""),
            refusals=refusals, rule_refusals=rule_refusals,
            fell_back=fell_back,
            # A fallback remains random play (`fell_back` says that), but an
            # upstream that returned an illegal answer still owns the refusal.
            # Dropping it makes that upstream's fallback rate unmeasurable.
            served_by=served_by,
            attempted_upstreams=attempted_upstreams,
            **callcost.spent(policies[seat]),
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
            team_evil_count = sum(1 for s in team
                                  if ref.assignment[s].team is Team.EVIL)
            team_has_evil = team_evil_count > 0
            votes = {}
            for seat in sorted(ref.assignment):
                labels = {k.label for k in ref.entitled_knowledge(seat)}
                known_evil = {k.seat for k in ref.entitled_knowledge(seat)
                              if k.label in ("evil", "fellow-evil")}
                # derived from entitled_knowledge, never from the role key, so a
                # variant that changes what a role learns changes the class too
                if labels & {"evil", "fellow-evil"}:
                    knowledge_class = "identity"
                elif "magic" in labels:
                    knowledge_class = "aura"
                else:
                    knowledge_class = "none"
                votes[seat] = decide(seat)["vote"]
                rec.votes.append(VoteRecord(
                    seat=seat,
                    approved=votes[seat],
                    seat_is_evil=ref.assignment[seat].team is Team.EVIL,
                    team_has_evil=team_has_evil,
                    knew_evil_on_team=bool(known_evil & set(team)),
                    knowledge_class=knowledge_class,
                    team_evil_count=team_evil_count,
                    turn=rec.turns,
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
            # `legal_targets` is the hunt's own denominator, recorded per game
            # rather than assumed by the scorer: it is 3 at 5 seats with a hunter
            # that sees its ally, 4 at 7p/3-evil, and 4 at 5 seats under the
            # blind-evil variant. A scorer that reconstructs it from the seat
            # count is one variant away from grading against the wrong chance.
            rec.hunt = {"hunter": hunter, "target": target, "seer": seer,
                        "hit": target == seer,
                        "legal_targets": len(ref.legal_hunt_targets(hunter))}
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
