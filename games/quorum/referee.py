"""Deterministic referee for the legislative hidden-role game.

The referee is pure code: it deals roles, computes each seat's entitled knowledge,
validates and applies the actions players choose (nominate, speak, vote, discard,
use a power), tracks state, and detects the win. It never decides a nomination or
a vote - that is the players' job. No judgment lives here.

**What is different from the two rungs before it, and why the file exists.** In
``games/cabal`` a seat's entitlement is fixed at the deal; in
``games/changeling`` it is mutable but still a fact about a role. Here the
interesting secret is created per event and passes down a chain of offices,
narrowing as it goes - three cards to the proposer, two to the enactor, one to the
table. So entitlement is computed from ``(office, phase)`` and never cached
against a seat: the same seat is tier 1 at one event and tier 3 at the next.

Two channels leave this module, and the difference is the whole point:

  - ``public_events`` tagged ``"event"`` are referee-authored facts. Everyone sees
    them, so they are audited by gate #1 - a referee that named a role or an
    unentitled card here would be leaking.
  - ``public_events`` tagged ``"speech:<seat>"`` are what a player chose to say.
    A lie there is gameplay, not a leak, so the audit skips them.

**A warning for whoever writes the audit.** Naive substring matching reaches the
identity secrets here exactly as it does in cabal, and it CANNOT reach the card
secrets: the word for a card kind appears in the public record on every enactment,
so "a writ was enacted" (public, legal) and "your discard was a writ" (private,
a leak) are the same substring. The remedy is not a cleverer matcher - the repo
invariant keeps ``find_leaks`` naive on purpose - but a poisoned re-render: replace
every unentitled field with a unique token and re-render, and any token that
survives into the payload is a leak the substring scanner can then see. The hand
accessors below exist in that shape for this reason; see ``RULES.md``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from core.observability import Knowledge, SeatView
from games.quorum.roles import (ADVANCES, DEFAULT_THEME, SETUPS, Card, Role,
                                Setup, Side, Theme, known_allies)


@dataclass(frozen=True)
class ClaimRecord:
    """One seat's formal statement about a draw it saw.

    **Typed on purpose, and this is the decision the whole measurement rests on.**
    A claim made only in free speech cannot be scored without a parser that reads
    intent, and a parser with opinions is exactly what this repo refuses - the
    referee is a unit test, not a judge. So a seat that wants its statement counted
    declares it as a multiset of card keys, the referee reads it back to the table
    verbatim, and scoring is set comparison against what was dealt.

    A seat may still lie about a draw in ``say`` and never claim; that is gameplay
    and it is unscored, exactly as it is on the two rungs before this one. What the
    typed channel buys is the population that CAN be scored, not a ban on the rest.

    ``cards`` holds canonical keys rather than themed names, so a record survives a
    reskin - and the seat is asserting it, so nothing here is referee knowledge.
    """

    turn: int
    seat: int
    office: str                  # "proposer" | "enactor"
    cards: tuple[str, ...]


class Phase(Enum):
    NOMINATE = "nominate"
    DISCUSS = "discuss"
    VOTE = "vote"
    PROPOSER_DISCARD = "proposer_discard"
    ENACTOR_DISCARD = "enactor_discard"
    POWER = "power"
    DONE = "done"


class IllegalAction(Exception):
    """A player tried something the rules forbid. The referee refuses; it never
    silently coerces. A surveyed implementation of a comparable game drops an
    unknown action with no log, which makes a broken game read as a quiet one."""


#: Hard cap on one utterance. A player that rambles pays for everyone's context.
MAX_UTTERANCE_CHARS = 280

#: How many lines of public record a seat sees. The record is re-sent on every
#: call, so an unbounded one turns a long game into a quadratic context bill.
#: Trimming is safe for gate #1: what scrolls off the render leaves the payload
#: too, so it cannot leak what it no longer contains.
MAX_RECORD_LINES = 60


@dataclass
class QuorumReferee:
    setup: Setup
    assignment: dict[int, Role]
    theme: Theme = DEFAULT_THEME
    phase: Phase = Phase.NOMINATE
    proposer: int = 0
    nominee: int | None = None
    enactor: int | None = None
    charters: int = 0
    writs: int = 0
    failure_track: int = 0
    #: The last enactor is ineligible for the next nomination, which stops two
    #: seats trading the offices between them.
    last_enactor: int | None = None
    removed: set[int] = field(default_factory=set)
    last_votes: dict[int, bool] | None = None
    winner: Side | None = None
    win_reason: str = ""
    pending_power: str | None = None

    #: Referee-side only, and the reason this rung exists. ``proposer_hand`` is the
    #: three cards dealt this event; ``enactor_hand`` the two passed on. Both are
    #: cleared the moment the event ends, because an entitlement that outlives its
    #: event is the bug the cascade was built to make visible.
    proposer_hand: list[Card] = field(default_factory=list)
    enactor_hand: list[Card] = field(default_factory=list)
    #: what each office SAW this event, kept so recall can be filed when the hand
    #: is cleared. Referee-side, and never rendered except through ``recall``.
    proposer_saw: list[Card] = field(default_factory=list)
    enactor_saw: list[Card] = field(default_factory=list)

    deck: list[Card] = field(default_factory=list)
    discards: list[Card] = field(default_factory=list)

    #: inspector seat -> {subject seat -> side}. A private fact created mid-game,
    #: held by exactly one seat, about a seat that is never told it was inspected.
    inspections: dict[int, dict[int, Side]] = field(default_factory=dict)

    #: Formal statements about the last completed draw. Seat-authored data the
    #: referee reads back verbatim; it is never derived from a hand, which is what
    #: keeps a truthful claim legal under the dependence audit.
    claims: list[ClaimRecord] = field(default_factory=list)
    #: seat -> the cards IT saw in the last completed event. A seat's own past
    #: observation, entitled to that seat alone.
    #:
    #: **This exists because the claim channel would otherwise measure memory.** A
    #: hand renders only during its own discard step and ``think`` is discarded
    #: every turn, so without this a seat had no way to retrieve what it saw and an
    #: honest claim was impossible to make on purpose. Perfect recall - an agent
    #: remembers its own moves and perceptions along the history - is the standard
    #: assumption, and this is the channel that implements it.
    recall: dict[int, tuple[Card, ...]] = field(default_factory=dict)
    #: who held each office in the last COMPLETED event, so a claim can be checked
    #: for standing without the caller restating the flow. Both are cleared when an
    #: enactment happened with nobody holding cards.
    last_proposer: int | None = None

    discussion_rounds: int = 1
    speech_ptr: int = 0
    max_record_lines: int = MAX_RECORD_LINES
    log: list[str] = field(default_factory=list)
    public_events: list[tuple[str, str]] = field(default_factory=list)
    _rng: random.Random = field(default_factory=random.Random)

    # ---- construction -----------------------------------------------------

    @classmethod
    def new(
        cls,
        n: int = 5,
        seed: int | None = None,
        theme: Theme = DEFAULT_THEME,
        discussion_rounds: int = 1,
    ) -> "QuorumReferee":
        setup = SETUPS[n]
        rng = random.Random(seed)
        roles = list(setup.roles)
        rng.shuffle(roles)
        assignment = {seat: role for seat, role in zip(range(n), roles)}
        ref = cls(
            setup=setup,
            assignment=assignment,
            theme=theme,
            proposer=rng.randrange(n),
            discussion_rounds=discussion_rounds,
            _rng=rng,
        )
        ref._refill_deck()
        # The deal is referee-side only: it never enters public_events.
        ref.log.append(f"dealt {n} roles; opening proposer = seat {ref.proposer}")
        ref._event(f"Session opens. Seat {ref.proposer} holds "
                   f"{ref.theme.office_names['proposer']}.")
        return ref

    # ---- deck -------------------------------------------------------------

    def _refill_deck(self) -> None:
        """Rebuild and shuffle the draw pile from the composition plus whatever has
        been discarded. Called at the open and whenever fewer than three remain -
        three because that is the size of one draw, and a draw that had to be
        served from two piles would make the composition unstateable."""
        if not self.deck and not self.discards:
            pool = ([Card.CHARTER] * self.setup.deck_charter
                    + [Card.WRIT] * self.setup.deck_writ)
        else:
            pool = self.deck + self.discards
        self._rng.shuffle(pool)
        self.deck = pool
        self.discards = []
        self.log.append(f"deck rebuilt: {len(self.deck)} cards")

    def _draw(self, k: int) -> list[Card]:
        if len(self.deck) < k:
            self._refill_deck()
        drawn, self.deck = self.deck[:k], self.deck[k:]
        return drawn

    # ---- derived state ----------------------------------------------------

    @property
    def n(self) -> int:
        return self.setup.n

    def living(self) -> list[int]:
        return [s for s in sorted(self.assignment) if s not in self.removed]

    def eligible_nominees(self) -> list[int]:
        """Every seat the proposer may name. Itself and the previous enactor are
        out; at five seats the previous proposer is not, because barring both
        would leave a two-seat pool and make the nomination almost forced."""
        pool = self.living()
        barred = {self.proposer}
        if self.last_enactor is not None:
            barred.add(self.last_enactor)
        out = [s for s in pool if s not in barred]
        if out:
            return out
        # Removals can shrink the table until the previous-enactor bar leaves no
        # legal nomination at all. The bar is a term limit, not a rule the game may
        # deadlock on, so it lifts rather than stalling - and it lifts HERE so that
        # every caller sees one answer. A driver picking from an empty list is the
        # shape this returned before a random-play sweep hit it at 2 living seats.
        return [s for s in pool if s != self.proposer]

    def _event(self, text: str) -> None:
        self.public_events.append(("event", text))

    # ---- entitlement ------------------------------------------------------

    def entitled_knowledge(self, seat: int) -> tuple[Knowledge, ...]:
        """Every reveal this seat is entitled to, as fiction-safe labels.

        Two sources, and they are different in kind. The deal's is static and
        symmetric; an inspection's is created mid-game, held by one seat, and
        invisible to its subject.
        """
        out = [Knowledge(seat=s, label="fellow-minority")
               for s in sorted(known_allies(self.assignment, seat))]
        for subject, side in sorted(self.inspections.get(seat, {}).items()):
            out.append(Knowledge(seat=subject, label=f"inspected-{side.value}"))
        return tuple(out)

    def entitled_hand(self, seat: int) -> list[Card] | None:
        """The cards this seat may see RIGHT NOW, or None.

        Keyed on ``(office, phase)`` and never on the seat, which is the whole
        difference between this rung and the two before it. The proposer's third
        card stops being visible to anyone the instant it is discarded, including
        to the proposer that saw it - the hand list is replaced, not filtered, so
        there is no field left holding it.
        """
        if self.phase is Phase.PROPOSER_DISCARD and seat == self.proposer:
            return list(self.proposer_hand)
        if self.phase is Phase.ENACTOR_DISCARD and seat == self.enactor:
            return list(self.enactor_hand)
        return None

    # ---- views ------------------------------------------------------------

    def public_state(self) -> dict:
        return {
            "phase": self.phase.value,
            "proposer": self.proposer,
            "nominee": self.nominee,
            "enactor": self.enactor,
            "charters": self.charters,
            "writs": self.writs,
            "charter_target": self.setup.charter_target,
            "writ_target": self.setup.writ_target,
            "failure_track": self.failure_track,
            "failure_limit": self.setup.failure_limit,
            "removed": sorted(self.removed),
            "deck_remaining": len(self.deck),
            "last_votes": dict(self.last_votes) if self.last_votes else None,
            "winner": self.winner.value if self.winner else None,
            "record": [t for kind, t in self.public_events if kind == "event"],
            "table_talk": [t for kind, t in self.public_events
                           if kind.startswith("speech")],
            "next_speaker": self.next_speaker(),
        }

    def seat_view(self, seat: int) -> SeatView:
        role = self.assignment[seat]
        return SeatView(
            seat=seat,
            own_role=self.theme.role_names[role.key],
            own_team=self.theme.side_names[role.side],
            knowledge=self.entitled_knowledge(seat),
            public=self.public_state(),
        )

    def render_context(self, seat: int, include_speech: bool = True) -> str:
        """The exact text a player agent receives for this seat. Whatever is not
        here is invisible to that agent, so this string is what gate #1 audits.

        ``include_speech=False`` drops what other players said, leaving only what
        the referee itself put in front of this seat. A player naming a role is
        playing the game; the referee doing it is the leak.
        """
        v = self.seat_view(seat)
        t = self.theme
        lines: list[str] = []
        if t.blurb:
            lines += [t.blurb, ""]
        lines += [
            f"You are seat {v.seat}. Your role: {v.own_role} ({v.own_team}).",
            f"Players: {self.n} seats, numbered 0..{self.n - 1}.",
        ]
        if v.knowledge:
            lines.append("What you know privately:")
            for k in v.knowledge:
                if k.label == "fellow-minority":
                    lines.append(f"  - seat {k.seat} is one of your own.")
                elif k.label.startswith("inspected-"):
                    side = Side(k.label.split("-", 1)[1])
                    lines.append(f"  - you looked at seat {k.seat}: "
                                 f"{t.side_names[side]}.")
        else:
            lines.append("You were told nothing. You must reason from play alone.")
        p = v.public
        lines.append(
            f"Board: {t.card_names[Card.CHARTER]}s {p['charters']}/"
            f"{p['charter_target']}, {t.card_names[Card.WRIT]}s {p['writs']}/"
            f"{p['writ_target']}, {t.office_names['proposer']} seat "
            f"{p['proposer']}, failed votes {p['failure_track']}/"
            f"{p['failure_limit']}."
        )
        if p["removed"]:
            lines.append(f"Removed from the session: {p['removed']}.")
        if p["nominee"] is not None and self.phase in (Phase.DISCUSS, Phase.VOTE):
            lines.append(f"Nominated as {t.office_names['enactor']}: "
                         f"seat {p['nominee']}.")
        hand = self.entitled_hand(seat)
        if hand is not None:
            shown = ", ".join(f"{i}: {t.card_names[c]}" for i, c in enumerate(hand))
            lines.append(f"In your hand, and seen by nobody else: {shown}.")
        remembered = self.recall.get(seat)
        if remembered:
            # The office is read off how many cards it saw, not off `claimable`:
            # recall is filed the moment a seat discards, which is BEFORE the
            # event completes and therefore before standing to claim exists.
            office = "proposer" if len(remembered) == 3 else "enactor"
            shown = ", ".join(t.card_names[c] for c in remembered)
            lines.append(
                f"You remember holding, as {t.office_names[office]} last round "
                f"and seen by nobody else: {shown}.")
        record: list[str] = []
        for kind, text in self.public_events:
            if kind == "event":
                record.append(text)
            elif include_speech:
                who = int(kind.split(":", 1)[1])
                mark = " (you)" if who == seat else ""
                record.append(f"seat {who}{mark}: \"{text}\"")
        if record:
            lines.append("")
            lines.append("The record so far:")
            lines += [f"  {r}" for r in record[-self.max_record_lines:]]
        return "\n".join(lines)

    # ---- turn order -------------------------------------------------------

    def next_speaker(self) -> int | None:
        if self.phase is not Phase.DISCUSS:
            return None
        order = self.living()
        total = self.discussion_rounds * len(order)
        if self.speech_ptr >= total:
            return None
        return order[self.speech_ptr % len(order)]

    def on_clock(self) -> list[int]:
        """Every seat the driver must ask this turn. One list, so a driver cannot
        invent its own turn order and quietly diverge from the referee's."""
        if self.phase is Phase.NOMINATE:
            return [self.proposer]
        if self.phase is Phase.DISCUSS:
            nxt = self.next_speaker()
            return [] if nxt is None else [nxt]
        if self.phase is Phase.VOTE:
            return self.living()
        if self.phase is Phase.PROPOSER_DISCARD:
            return [self.proposer]
        if self.phase is Phase.ENACTOR_DISCARD:
            return [] if self.enactor is None else [self.enactor]
        if self.phase is Phase.POWER:
            return [self.proposer]
        return []

    # ---- the ask ----------------------------------------------------------

    def action_prompt(self, seat: int) -> str:
        """The ask appended to ``render_context`` for whichever seat acts next.

        Declares the JSON envelope. ``think`` is the sanctioned place for private
        reasoning and the driver discards it - only ``say`` is ever handed to
        ``speak()``.

        Written in the positive per this repo's model-facing-text rule: every ask
        states the move to make rather than the move to avoid. The one thing
        phrased as a constraint is the envelope, which the parser enforces anyway.
        """
        t = self.theme
        head = (
            'Reply with ONE JSON object and nothing else. A "think" field is '
            "private scratch space that is discarded and never shown to anyone - "
            "keep it under 30 words, because a reply long enough to be truncated "
            "is a reply the referee has to refuse."
        )
        scratch = '"think": "..."'
        p = self.phase
        if p is Phase.NOMINATE:
            eligible = self.eligible_nominees()
            return (
                f"{head}\nYou hold {t.office_names['proposer']}. Name the seat to "
                f"serve as {t.office_names['enactor']} this round. Eligible: "
                f"{eligible}.\n"
                f'Format: {{{scratch}, "nominate": <one seat from {eligible}>}}'
            )
        if p is Phase.DISCUSS:
            office = self.claimable(seat)
            extra = ""
            if office is not None:
                size = self.CLAIM_SIZE[office]
                names = " or ".join(sorted(t.card_names.values()))
                extra = (
                    f' You held {t.office_names[office]} in the last round, so you '
                    f'may also make a formal claim: "claim" naming the {size} cards '
                    f'you held, each {names}. The table is told you claimed it and '
                    f'told that nothing confirms it. Claim what serves you.'
                )
            return (
                f"{head}{extra}\nYou are seat {seat}; speak in the first person and "
                "address the table - your own earlier lines are marked (you) in "
                f"the record.\nSay one or two short sentences before the vote, at "
                f"most {MAX_UTTERANCE_CHARS} characters. Everyone reads \"say\" "
                "and nothing else of yours. Argue, accuse, defend, or mislead as "
                "your role requires.\n"
                f'Format: {{{scratch}, "say": "<your public words>"'
                + (f', "claim": [<{self.CLAIM_SIZE[office]} card names>]'
                   if office is not None else "")
                + "}"
            )
        if p is Phase.VOTE:
            return (
                f"{head}\nVote on seating seat {self.nominee} as "
                f"{t.office_names['enactor']}. Every vote is public and permanent, "
                "and the table will remember who backed this government.\n"
                f'Format: {{{scratch}, "vote": true or false}}'
            )
        if p is Phase.PROPOSER_DISCARD:
            hand = self.entitled_hand(seat) or []
            return (
                f"{head}\nYou drew {len(hand)} cards and nobody else has seen "
                f"them. Discard one face down; the other two pass to seat "
                f"{self.enactor}, which enacts one of them. The card you drop is "
                "seen by nobody, now or later.\n"
                f'Format: {{{scratch}, "discard": <index 0..{len(hand) - 1}>}}'
            )
        if p is Phase.ENACTOR_DISCARD:
            hand = self.entitled_hand(seat) or []
            return (
                f"{head}\nSeat {self.proposer} drew three cards, kept one to "
                f"itself, and passed you these {len(hand)}. Discard one face "
                "down; the other is enacted in front of the table.\n"
                f'Format: {{{scratch}, "discard": <index 0..{len(hand) - 1}>}}'
            )
        if p is Phase.POWER:
            legal = self.legal_power_targets(seat)
            if self.pending_power == "inspect":
                what = ("Look at one seat's allegiance. You alone learn it, the "
                        "seat you look at is not told, and the record says only "
                        "that you looked.")
            else:
                what = ("Remove one seat from the session. Its role stays secret, "
                        "and the table sees only that it is gone.")
            return (
                f"{head}\n{what} Legal targets: {legal}.\n"
                f'Format: {{{scratch}, "target": <one seat from {legal}>}}'
            )
        raise IllegalAction(f"nothing to ask in phase {p.value}")

    # ---- the claim channel -------------------------------------------------

    def claimable(self, seat: int) -> str | None:
        """Which office this seat held in the last completed event, or None.

        One rule, read by the referee, the policy precheck and the ask, so a seat
        cannot be invited to make a claim the referee would refuse.
        """
        if self.last_proposer is not None and seat == self.last_proposer:
            return "proposer"
        if self.last_enactor is not None and seat == self.last_enactor:
            return "enactor"
        return None

    #: how many cards each office saw, and therefore how long its claim must be
    CLAIM_SIZE = {"proposer": 3, "enactor": 2}

    def validate_claim(self, seat: int, cards) -> None:
        office = self.claimable(seat)
        if office is None:
            raise IllegalAction(
                f"seat {seat} held no office in the last event, so it has nothing "
                "to claim about")
        want = self.CLAIM_SIZE[office]
        if len(cards) != want:
            raise IllegalAction(
                f"a {self.theme.office_names[office]} claim names {want} cards, "
                f"got {len(cards)}")
        for c in cards:
            if not isinstance(c, Card):
                raise IllegalAction(f"{c!r} is not a card")

    def record_claim(self, seat: int, cards) -> ClaimRecord:
        """File a claim and read it back to the table.

        The public line is the seat's assertion, never the referee's knowledge:
        it is rendered from ``cards`` as given. That is what the dependence audit
        checks - flipping the hand this claim is about leaves every seat's render
        byte-identical, because no render reads the hand to write this line.
        """
        self.validate_claim(seat, cards)
        office = self.claimable(seat)
        rec = ClaimRecord(turn=len(self.public_events), seat=seat, office=office,
                          cards=tuple(c.value for c in cards))
        self.claims.append(rec)
        named = ", ".join(self.theme.card_names[c] for c in cards)
        self._event(f"Seat {seat} claims that as "
                    f"{self.theme.office_names[office]} it held: {named}. "
                    f"Nothing confirms this.")
        return rec

    def prompt_for(self, seat: int, include_speech: bool = True) -> str:
        """The complete outgoing payload for one seat: its view plus its ask. This
        is the string a player policy sends, so this is the string gate #1 audits.
        """
        return (f"{self.render_context(seat, include_speech)}\n\n"
                f"{self.action_prompt(seat)}")

    # ---- validators, so one rule answers the policy and the referee ---------

    def legal_power_targets(self, seat: int) -> list[int]:
        """Every seat the current power may name.

        Derived here so that the precheck a policy runs before spending a retry
        and the refusal the referee raises cannot disagree. Two copies of one
        legality rule is how an audit ends up certifying the move it was written
        to catch.
        """
        return [s for s in self.living() if s != seat]

    def validate_nomination(self, seat: int, target: int) -> None:
        if seat != self.proposer:
            raise IllegalAction(f"seat {seat} does not hold the office")
        if target not in self.eligible_nominees():
            raise IllegalAction(
                f"seat {target} is not an eligible nominee; eligible are "
                f"{self.eligible_nominees()}")

    def validate_power_target(self, seat: int, target: int) -> None:
        if seat != self.proposer:
            raise IllegalAction(f"seat {seat} does not hold the office")
        if target not in self.legal_power_targets(seat):
            raise IllegalAction(
                f"seat {target} is not a legal target; legal are "
                f"{self.legal_power_targets(seat)}")

    def validate_discard(self, seat: int, index: int) -> None:
        """The hand's own accessor decides whether this seat may discard at all,
        so entitlement is asked once and answered in one place."""
        hand = self.entitled_hand(seat)
        if hand is None:
            raise IllegalAction(f"seat {seat} holds no cards at this step")
        if not 0 <= index < len(hand):
            raise IllegalAction(f"index {index} outside a hand of {len(hand)}")

    # ---- actions ----------------------------------------------------------

    def nominate(self, seat: int, target: int) -> None:
        if self.phase is not Phase.NOMINATE:
            raise IllegalAction(f"nominate out of phase ({self.phase.value})")
        self.validate_nomination(seat, target)
        self.nominee = target
        self._event(f"Seat {seat} nominates seat {target} as "
                    f"{self.theme.office_names['enactor']}.")
        self.phase = Phase.DISCUSS
        self.speech_ptr = 0
        if self.next_speaker() is None:
            self.phase = Phase.VOTE

    def speak(self, seat: int, text: str) -> None:
        if self.phase is not Phase.DISCUSS:
            raise IllegalAction(f"speak out of phase ({self.phase.value})")
        if seat != self.next_speaker():
            raise IllegalAction(f"seat {seat} is not the current speaker")
        said = text.strip()[:MAX_UTTERANCE_CHARS]
        self.public_events.append((f"speech:{seat}", said))
        self.speech_ptr += 1
        if self.next_speaker() is None:
            self.phase = Phase.VOTE

    def vote(self, votes: dict[int, bool]) -> None:
        """Every living seat votes at once, and every vote is public in full.

        Taken as one dict rather than seat by seat because the votes are
        simultaneous by rule: a seat that could see a neighbour's vote before
        casting its own would be playing a different game, and a per-seat API
        makes that failure available to any driver that loops in seat order.
        """
        if self.phase is not Phase.VOTE:
            raise IllegalAction(f"vote out of phase ({self.phase.value})")
        expected = set(self.living())
        if set(votes) != expected:
            raise IllegalAction(f"vote roll {sorted(votes)} != living {sorted(expected)}")
        self.last_votes = dict(votes)
        yes = sum(1 for v in votes.values() if v)
        passed = yes * 2 > len(expected)
        cast = ", ".join(f"seat {s}: {'yes' if votes[s] else 'no'}"
                         for s in sorted(votes))
        self._event(f"Vote on seat {self.nominee}: {cast}. "
                    f"{'Carried' if passed else 'Failed'} ({yes}/{len(expected)}).")
        if not passed:
            self._fail_vote()
            return
        self.enactor = self.nominee
        self.failure_track = 0
        if self._install_win():
            return
        self.proposer_hand = self._draw(3)
        self.proposer_saw = list(self.proposer_hand)
        self.recall = {}
        self.log.append(f"proposer hand: {[c.value for c in self.proposer_hand]}")
        self.phase = Phase.PROPOSER_DISCARD

    def _install_win(self) -> bool:
        """The minority's second win condition, checked on a passed vote and before
        the draw. It is what makes the identity question urgent rather than
        academic: the table must eventually seat somebody it cannot read."""
        if self.writs < self.setup.install_threshold:
            return False
        if not self.assignment[self.enactor].is_principal:
            return False
        self._finish(Side.MINORITY,
                     f"seat {self.enactor} was seated as "
                     f"{self.theme.office_names['enactor']} after "
                     f"{self.writs} {self.theme.card_names[Card.WRIT]}s")
        return True

    def _fail_vote(self) -> None:
        self.failure_track += 1
        self.enactor = None
        self.nominee = None
        if self.failure_track >= self.setup.failure_limit:
            card = self._draw(1)[0]
            self._event(f"{self.failure_track} votes failed in a row. The top card "
                        f"is enacted unseen.")
            self.failure_track = 0
            self._enact(card, seen_by_nobody=True)
            return
        self._advance_proposer()

    def proposer_discard(self, seat: int, index: int) -> None:
        if self.phase is not Phase.PROPOSER_DISCARD:
            raise IllegalAction(f"discard out of phase ({self.phase.value})")
        if seat != self.proposer:
            raise IllegalAction(f"seat {seat} does not hold the office")
        if not 0 <= index < len(self.proposer_hand):
            raise IllegalAction(f"index {index} outside a hand of "
                                f"{len(self.proposer_hand)}")
        hand = list(self.proposer_hand)
        dropped = hand.pop(index)
        self.discards.append(dropped)
        # Replaced, not filtered: no field is left holding the discarded card, so
        # the entitlement expires with the value rather than with a flag.
        self.proposer_hand = []
        self.enactor_hand = hand
        # its own observation, kept for its own recall - the discard included,
        # because the seat saw it and is entitled to remember what it dropped
        self.recall = {seat: tuple(self.proposer_saw)}
        self.enactor_saw = list(hand)
        self.log.append(f"proposer discarded {dropped.value}; passed "
                        f"{[c.value for c in hand]}")
        self._event(f"Seat {seat} passes two cards to seat {self.enactor}.")
        self.phase = Phase.ENACTOR_DISCARD

    def enactor_discard(self, seat: int, index: int) -> None:
        if self.phase is not Phase.ENACTOR_DISCARD:
            raise IllegalAction(f"discard out of phase ({self.phase.value})")
        if seat != self.enactor:
            raise IllegalAction(f"seat {seat} does not hold the office")
        if not 0 <= index < len(self.enactor_hand):
            raise IllegalAction(f"index {index} outside a hand of "
                                f"{len(self.enactor_hand)}")
        hand = list(self.enactor_hand)
        dropped = hand.pop(index)
        self.discards.append(dropped)
        self.recall[seat] = tuple(self.enactor_saw)
        self.enactor_hand = []
        self.log.append(f"enactor discarded {dropped.value}")
        self._enact(hand[0])

    def _enact(self, card: Card, seen_by_nobody: bool = False) -> None:
        self._event(f"Enacted: {self.theme.card_names[card]}.")
        if ADVANCES[card] is Side.MAJORITY:
            self.charters += 1
        else:
            self.writs += 1
        # Standing to claim comes from having SEEN cards. The failure-track
        # enactment deals to nobody, so it confers none - and clearing both here
        # rather than only setting them on the other path is what stops last
        # round's proposer claiming about a card no one drew.
        self.last_proposer = None if seen_by_nobody else self.proposer
        self.last_enactor = self.enactor
        if seen_by_nobody:
            self.recall = {}
        self.enactor = None
        self.nominee = None
        if self.charters >= self.setup.charter_target:
            self._finish(Side.MAJORITY,
                         f"{self.charters} {self.theme.card_names[Card.CHARTER]}s enacted")
            return
        if self.writs >= self.setup.writ_target:
            self._finish(Side.MINORITY,
                         f"{self.writs} {self.theme.card_names[Card.WRIT]}s enacted")
            return
        # The power fires on the WRIT that reached the threshold, never merely on
        # the count standing there. Checking `power_at(self.writs)` alone re-fires
        # every power on each later charter - measured, not argued: a 40-seed
        # random-play sweep produced two inspections and three removals in one
        # 5-seat game, which is what the structural bound in the test caught.
        advanced_minority = ADVANCES[card] is Side.MINORITY
        power = (self.setup.power_at(self.writs)
                 if advanced_minority and not seen_by_nobody else None)
        if power:
            self.pending_power = power
            self._event(f"Seat {self.proposer} may now {power}.")
            self.phase = Phase.POWER
            return
        self._advance_proposer()

    def use_power(self, seat: int, target: int) -> None:
        if self.phase is not Phase.POWER:
            raise IllegalAction(f"power out of phase ({self.phase.value})")
        self.validate_power_target(seat, target)
        if self.pending_power == "inspect":
            side = self.assignment[target].side
            self.inspections.setdefault(seat, {})[target] = side
            self.log.append(f"seat {seat} inspected seat {target}: {side.value}")
            # The record says an inspection HAPPENED and never what it found, and
            # it does not name the subject: telling the table who was looked at
            # hands it a read the inspector paid an action for.
            self._event(f"Seat {seat} inspected one seat. The result is private.")
        elif self.pending_power == "remove":
            self.removed.add(target)
            self._event(f"Seat {target} is removed from the session. "
                        f"Its role is not revealed.")
            if self.assignment[target].is_principal:
                self._finish(Side.MAJORITY, f"seat {target} was removed")
                return
        else:
            raise IllegalAction(f"unknown power {self.pending_power!r}")
        self.pending_power = None
        self._advance_proposer()

    # ---- clock ------------------------------------------------------------

    def _advance_proposer(self) -> None:
        order = self.living()
        if not order:
            self._finish(Side.MINORITY, "no seats remain")
            return
        after = [s for s in order if s > self.proposer]
        self.proposer = after[0] if after else order[0]
        self.nominee = None
        self.speech_ptr = 0
        self.phase = Phase.NOMINATE
        self._event(f"Seat {self.proposer} takes "
                    f"{self.theme.office_names['proposer']}.")

    def _finish(self, side: Side, why: str) -> None:
        self.winner = side
        self.win_reason = why
        self.phase = Phase.DONE
        self.proposer_hand = []
        self.enactor_hand = []
        self._event(f"{self.theme.side_names[side]} wins: {why}.")
        self.log.append(f"WINNER: {side.value} ({why})")
