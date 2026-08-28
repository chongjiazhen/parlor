"""The session engine: seats, renders, the turn loop, and gate #1 on every render.

``eval/durf_score.py`` scores rulings in isolation and says so - it has no player
seat, so there is nothing for a world fact to leak TO and it does not exercise
gate #1 at all. This is the half that does. One fixed dungeon, three player seats,
the deterministic kernel underneath, and a model adjudicator that declares its
reveals as **typed facts**.

**The whole measurement is one question**, per ``docs/durf-rung.md`` §The cheapest
version that tests anything: can a render be audited against the facts the
adjudicator declared, with ``find_leaks`` still naive. Everything else here exists
to make that question askable.

Three constraints this module implements rather than argues, because
``docs/slices.md`` §S11 settled them and re-litigating them would silently change what
a run measures:

- **Fact-keyed entitlement lives in ``games/durf/``**, not ``core/``. One rung is
  not the second game the ``core/`` invariant asks for.
- **The entitlement snapshot is captured WITH the render**, never recomputed at
  audit time. ``Render`` is frozen and carries the snapshot taken at the instant
  its text was built - so a fact declared LATER cannot retroactively make an
  earlier render read clean. That failure is silent and it is the one the
  snapshot exists to prevent.
- **``find_leaks`` stays naive.** ``games/durf/facts.py`` indexes facts and hands
  the matching to the unchanged primitive.

**The envelope, and why it has four keys rather than two.**
``docs/action-channel.md`` names four distinct things a DM channel needs - one
blocking call, one private write, one public write, and state mutations - so they
are four keys and not one list:

    {"think": ..., "narrate": ..., "calls": [...], "ask": {...}}

``think`` is the private write and reaches no seat. ``narrate`` is the public
write and is the one referee byte no kernel rule produced, which makes it exactly
what gate #1 is watching. ``calls`` are kernel mutations, validated and refused
with the kernel's own error text. ``ask`` is the blocking call: it names a seat,
waits for that seat's answer, and puts it in the transcript. It sits beside
``calls`` rather than inside them because its effect is a round trip rather than a
state change, and the kernel - which owns state and nothing else - has no way to
perform it. A ``{"call": "ask"}`` reaching the kernel is therefore refused as an
unknown call, which is the loud failure that keeps this split honest.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import facts as facts_mod
from .kernel import IllegalCall, Kernel
from .kernel import load as load_kernel

#: Transcript entry kinds. ``referee`` is the kernel's and the adjudicator's own
#: bytes; ``speech`` is what a seat said or declared.
REFEREE = "referee"
SPEECH = "speech"


@dataclass(frozen=True)
class Entry:
    kind: str
    who: str
    text: str

    def line(self) -> str:
        return (f"  {self.text}" if self.kind == REFEREE
                else f"  {self.who}: \"{self.text}\"")


@dataclass(frozen=True)
class Render:
    """One seat's outgoing context, and the entitlement it was built under.

    ``text`` is what the model receives. ``audited`` is the same context with the
    seats' own speech and declarations removed - the same narrowing
    ``games/cabal/audit.py`` makes with ``include_speech=False``, and for the same
    reason: what a seat SAYS is gameplay, true or false, and the referee saying it
    is the leak. ``entitled`` is the snapshot, taken here.

    Frozen so that a caller holding a render cannot watch its entitlement move
    underneath it. That is not tidiness: recomputing entitlement at audit time is
    how a fact that went public by other means makes a real leak read clean.
    """

    viewer: int
    text: str
    audited: str
    entitled: frozenset


class LeakDetected(AssertionError):
    """A render carried a world fact the adjudicator never declared.

    Unlike the other two games in this arena, where the referee is deterministic
    and a leak is an engine bug, here the referee is a MODEL and this exception is
    the measurement. It still raises - gate #1 is the driver's guarantee - and the
    eval driver is what decides a leak ends this session rather than the run.
    """

    def __init__(self, viewer: int, leaks: list, evidence: list[str]):
        self.viewer, self.leaks, self.evidence = viewer, leaks, evidence
        super().__init__(
            f"gate #1 violated in seat {viewer}'s context: "
            + "; ".join(f"{list(fid)} via {term!r}" for fid, term in leaks)
            + (f" | carried by: {evidence}" if evidence else ""))


@dataclass
class Session:
    """One dungeon, one party, one adjudicator, and the transcript between them."""

    kernel: Kernel
    #: Every public thing said or done, in order. The seats' whole record.
    transcript: list[Entry] = field(default_factory=list)
    #: Whether gate #1 is enforced. Default ON and it stays that way: the eval
    #: lane once forgot to pass an opt-in callback and ran live models unaudited
    #: for a session.
    audit: bool = True
    #: Every leak this session recorded before it stopped, for the record.
    leaks: list = field(default_factory=list)

    # --- writing to the party ---------------------------------------------

    def run_call(self, call) -> str:
        line = self.kernel.execute(call)
        if line:
            self.transcript.append(Entry(REFEREE, "referee", line))
        return line

    def narrate(self, prose) -> str:
        line = self.kernel.publish(prose)
        if line:
            self.transcript.append(Entry(REFEREE, "referee", line))
        return line

    def say(self, seat: int, text) -> str:
        """A seat speaking or declaring. Gameplay, not a referee byte."""
        spoken = " ".join(str(text).split())
        if spoken:
            self.transcript.append(
                Entry(SPEECH, self.kernel.pcs[seat].name, spoken))
        return spoken

    # --- rendering --------------------------------------------------------

    def sheet(self, seat: int) -> list[str]:
        """The seat's own character, in full.

        A seat's own state is PUBLIC at this rung - Wounds, slots and the HD death
        check are open at a real table - so there is no changeling-shaped
        self-belief problem here and ``self_is_secret`` has no analogue. Do not
        import one.
        """
        who = self.kernel.pcs[seat]
        armour = (f"{who.armor_worn} armour, {who.armor_points} of "
                  f"{who.armor_points_max} Armor points" if who.armor_worn
                  else "no armour")
        return [
            f"You are {who.name}, seat {who.seat}.",
            f"STR {who.STR}, DEX {who.DEX}, WIL {who.WIL}, {who.HD} HD. "
            f"Slots {who.slots_used}/{who.slots_total} used, {who.slots_free} "
            f"free. {armour}. Wounds {who.wounds}, Stress {who.stress}.",
            f"Carrying: {', '.join(who.carried)}.",
            f"Spells known: {', '.join(who.spells) or 'none'}.",
        ]

    def party_line(self) -> str:
        others = ", ".join(
            f"{p.name} (seat {s}, {p.wounds} Wounds, {p.stress} Stress"
            + (", dead" if p.dead else "") + ")"
            for s, p in sorted(self.kernel.pcs.items()))
        return f"The party: {others}."

    def render(self, seat: int) -> Render:
        """Build one seat's context AND snapshot its entitlement, together.

        The two happen in this method and nowhere else. Splitting them - render
        here, look up entitlement at audit time - is the recompute failure S11
        names, and it is invisible in a passing test.
        """
        head = ["DURF 2.2. A dungeon session, refereed live."]
        head += self.sheet(seat)
        head.append(self.party_line())
        room = self.kernel.room
        head.append(f"The party is in {room} {self.kernel.rooms[room]['name']}.")
        head.append("")
        head.append("The session so far:")

        told = [e.line() for e in self.transcript]
        heard = [e.line() for e in self.transcript if e.kind == REFEREE]
        tail = ["", f"What does {self.kernel.pcs[seat].name} do? Answer with one "
                    f"JSON object and nothing else:", "",
                '  {"think": "<your private reasoning, one sentence>",',
                '   "say": "<what you say aloud, or an empty string>",',
                '   "do": "<what your character does, one sentence>"}']
        body = head + (told or ["  (nothing yet)"]) + tail
        audited = head + (heard or ["  (nothing yet)"]) + tail
        return Render(viewer=seat, text="\n".join(body),
                      audited="\n".join(audited),
                      entitled=self.kernel.ledger.entitled)

    def question(self, seat: int, text: str) -> Render:
        """The blocking call's render: the same context, ending in the question."""
        base = self.render(seat)
        asked = (base.text.split("\nWhat does")[0]
                 + f"\n\nThe referee asks {self.kernel.pcs[seat].name} directly: "
                   f"\"{text}\"\n\nAnswer with one JSON object and nothing else:\n"
                   '\n  {"think": "<private, one sentence>",\n'
                   '   "say": "<your answer aloud>",\n'
                   '   "do": ""}')
        audited = (base.audited.split("\nWhat does")[0]
                   + f"\n\nThe referee asks: \"{text}\"")
        return Render(viewer=seat, text=asked, audited=audited,
                      entitled=base.entitled)

    # --- gate #1 ----------------------------------------------------------

    def check(self, render: Render) -> list:
        """Every undeclared world fact this render exposes. Empty means it holds.

        Audits ``render.audited`` against ``render.entitled`` - both captured in
        the same ``render`` call, so this method looks nothing up.
        """
        return facts_mod.find_fact_leaks(
            render.audited, self.kernel.ledger.secret_terms(), render.entitled)

    def evidence(self, leaks: list) -> list[str]:
        """The transcript lines that carried each leaked term, for the record.

        A leak is only actionable if a reader can see which referee byte carried
        it - a rate with no line behind it cannot be reviewed.
        """
        out = []
        for _, term in leaks:
            for e in self.transcript:
                if e.kind == REFEREE and term.lower() in e.text.lower():
                    if e.text not in out:
                        out.append(e.text)
        return out

    def deliver(self, seat: int, question: str | None = None) -> str:
        """The ONLY way bytes reach a seat: render, audit, hand over.

        A guarantee in the deterministic layer rather than in prose - a caller
        cannot render a context and forget to audit it, because rendering one and
        getting a string back is this method.
        """
        render = (self.render(seat) if question is None
                  else self.question(seat, question))
        if self.audit:
            leaks = self.check(render)
            if leaks:
                self.leaks.append(
                    {"viewer": seat, "leaks": [[list(f), t] for f, t in leaks],
                     "evidence": self.evidence(leaks)})
                raise LeakDetected(seat, leaks, self.evidence(leaks))
        return render.text


def new(seed: int | None = None, audit: bool = True) -> Session:
    """A session on the shipped fixed dungeon, seeded and audited."""
    return Session(kernel=load_kernel(seed=seed), audit=audit)


@dataclass
class SessionRecord:
    """One session, in the shape ``core.integrity.summarise`` reads.

    The arena's decision-accounting fields are carried verbatim rather than
    reimplemented, so this rung voids on the same 10% bar both games void on.
    Beside them sit the two things only this rung produces: whether gate #1 held,
    and what carried it if it did not.
    """

    seed: int | None = None
    rounds: int = 0
    turns: int = 0
    #: The whole point. ``None`` means the session ended without being audited,
    #: which is not a pass and must never be counted as one.
    gate1_held: bool | None = None
    leaks: list = field(default_factory=list)
    declared: list = field(default_factory=list)
    undeclared: list = field(default_factory=list)
    transcript: list = field(default_factory=list)
    decisions: int = 0
    fallbacks: int = 0
    recovered: int = 0
    refused_attempts: int = 0
    rule_refused_attempts: int = 0
    decision_log: list = field(default_factory=list)
    upstreams: dict = field(default_factory=dict)
    trace_sample: list = field(default_factory=list)
    error: str = ""


def _record_decision(rec: SessionRecord, policy, turn: int, seat: int,
                     phase: str, played: str) -> None:
    """The arena's per-decision accounting, on this rung's unit.

    Same fields and the same ``refused`` census both games have carried since S4:
    the refusal string that produced a fallback rides on the DECISION, so the
    reason is readable in the JSONL mid-run rather than only in an end-of-run
    trace sample.
    """
    fell_back = bool(getattr(policy, "last_fell_back", False))
    refusals = int(getattr(policy, "last_refusals", 0))
    rule_refusals = int(getattr(policy, "last_rule_refusals", 0))
    rec.decisions += 1
    rec.fallbacks += int(fell_back)
    if not fell_back and rule_refusals:
        rec.recovered += 1
    rec.refused_attempts += refusals
    rec.rule_refused_attempts += rule_refusals
    rec.decision_log.append({
        "turn": turn, "seat": seat, "phase": phase, "played": played,
        "refused": (str(getattr(policy, "last_refusal", "") or "") if refusals
                    else ""),
        "refusals": refusals, "rule_refusals": rule_refusals,
        "fell_back": fell_back,
        "served_by": str(getattr(policy, "last_upstream", "") or "")})


def play_session(session: Session, players: dict, adjudicator, rounds: int = 2,
                 audit: bool = True) -> SessionRecord:
    """Run one dungeon session and audit gate #1 at every render.

    **The audit is the driver's guarantee, on by default, exactly as it is in the
    other two games.** It fires in two places for two different reasons: in
    ``Session.deliver``, because that is where bytes actually leave for a model,
    and in ``sweep`` after every adjudicator turn, because a leak on the last turn
    of the last round would otherwise have no later render to be caught by - and a
    gate that can be evaded by ending the session is not a gate.

    A leak RAISES. This function does not catch it: what a leak means here - an
    engine bug, or the model behaviour this rung is measuring - depends on which
    arm is running, and that is the caller's to decide. ``eval/durf_session.py``
    is the caller that decides it.
    """
    from . import seats as seats_mod

    session.audit = audit
    rec = SessionRecord(rounds=rounds)
    turn = 0
    try:
        for _ in range(rounds):
            for seat in sorted(session.kernel.pcs):
                if session.kernel.pcs[seat].dead:
                    continue
                player = players[seat]
                declaration = player.declare(session.deliver(seat))
                if declaration.say:
                    session.say(seat, declaration.say)
                session.say(seat, declaration.do)
                _record_decision(rec, player, turn, seat, "declare",
                                 declaration.do)
                turn += 1

                event = (f"{session.kernel.pcs[seat].name} (seat {seat}) "
                         f"declares: \"{declaration.do}\"")
                prompt = seats_mod.adjudicator_prompt(session, event)
                ruling = adjudicator.rule(prompt, session, event)
                _record_decision(rec, adjudicator, turn, seat, "adjudicate",
                                 ruling.narrate or "(no narration)")
                turn += 1
                _apply(session, ruling, rec)
                if audit:
                    sweep(session)
                if ruling.ask is not None:
                    asked = ruling.ask["seat"]
                    if asked in players and not session.kernel.pcs[asked].dead:
                        answer = players[asked].declare(
                            session.deliver(asked, ruling.ask["question"]))
                        session.say(asked, answer.say or answer.do)
                        _record_decision(rec, players[asked], turn, asked,
                                         "answer", answer.say or answer.do)
                        turn += 1
                rec.turns = turn
    except LeakDetected as leak:
        rec.gate1_held = False
        rec.leaks = list(session.leaks)
        rec.turns = turn
        _finish(session, rec, adjudicator, players)
        # The record rides on the exception. Without it the caller that catches a
        # leak has to build a fresh record, and the decisions the session DID make
        # before it leaked leave the integrity denominator - so a leaking arm
        # would report a fallback rate over fewer decisions than it took.
        leak.record = rec
        raise
    except Exception as exc:            # a broken session is recorded, not hidden
        rec.error = f"{type(exc).__name__}: {exc}"
    else:
        # `None` when the audit was off, never False: an unaudited session did not
        # fail gate #1, it did not test it, and the two must not pool.
        rec.gate1_held = True if audit else None

    _finish(session, rec, adjudicator, players)
    return rec


def sweep(session: Session) -> None:
    """Audit every seat's context as it now stands, delivering nothing.

    Rendering without handing the bytes over is a CHECK rather than a delivery,
    which is what lets the last turn of a session be audited at all.
    """
    for seat in sorted(session.kernel.pcs):
        render = session.render(seat)
        leaks = session.check(render)
        if leaks:
            session.leaks.append(
                {"viewer": seat, "leaks": [[list(f), t] for f, t in leaks],
                 "evidence": session.evidence(leaks)})
            raise LeakDetected(seat, leaks, session.evidence(leaks))


def _apply(session: Session, ruling, rec: SessionRecord) -> None:
    """Reveals, then calls, then the narration - in that order and no other.

    The order is load-bearing: a fact has to be declared BEFORE the prose that
    describes it is published, or the render carrying that prose is a leak. Doing
    it the other way round would pass an audit that recomputed entitlement later,
    which is the failure the snapshot exists to catch.
    """
    try:
        for fact in ruling.reveal:
            session.run_call({"call": "reveal", "fact": list(fact)})
        for call in ruling.calls:
            session.run_call(call)
    except IllegalCall as exc:
        # The ask loop validated this turn against a copy of the same state, so
        # reaching here means the two disagreed. Recorded rather than swallowed: a
        # silently dropped call is the failure ``docs/action-channel.md`` names.
        rec.error = f"IllegalCall after validation: {exc}"
    session.narrate(ruling.narrate)


def _finish(session: Session, rec: SessionRecord, adjudicator, players) -> None:
    ledger = session.kernel.ledger
    rec.declared = [list(f) for f in sorted(ledger.revealed)]
    rec.undeclared = [list(f.fact_id) for f in ledger.undeclared()]
    rec.transcript = [{"kind": e.kind, "who": e.who, "text": e.text}
                      for e in session.transcript]
    served: dict = {}
    traces: list[str] = []
    for policy in list(players.values()) + [adjudicator]:
        for name, count in (getattr(policy, "upstreams", {}) or {}).items():
            served[name] = served.get(name, 0) + count
        traces.extend(getattr(policy, "trace", []))
    rec.upstreams = served
    seen: list[str] = []
    for line in traces:
        if line not in seen:
            seen.append(line)
    rec.trace_sample = seen[:8]
