"""Deterministic referee for the one-night swap game.

Pure code, as in ``cabal``: it deals, resolves the night, validates and applies the
day's actions, and decides the winner. It never chooses a word or a vote.

What is different here, and it is the whole rung:

  **A seat is rendered its BELIEF, never its truth.** ``seat_view`` reads
  ``night.belief``; the winner is read from ``night.truth``; and nothing in the day
  reconciles them. The referee therefore holds, for a diverged seat, a fact about
  that seat which must not reach that seat - a shape ``cabal`` never has, where a
  seat's own role is something it is always entitled to.

Two public channels leave here, same contract as ``cabal``:

  - ``"event"`` - referee-authored fact. Audited by gate #1.
  - ``"speech"`` - what a seat chose to say. A lie there is gameplay.

The night is the third thing, and it is in NEITHER. The referee publishes that the
night happened and never who woke, acted, or moved what: the card multiset is
public, so an event log naming who acted would identify roles by elimination.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from core.observability import Knowledge, SeatView, find_leaks
from games.changeling.night import (NightResult, is_centre, centre_slot,
                                    resolve_night)
from games.changeling.roles import (DEFAULT_THEME, NIGHT_ORDER, SETUPS, Card,
                                    Setup, Side, Theme)


class Phase(Enum):
    DISCUSS = "discuss"
    VOTE = "vote"
    DONE = "done"


class IllegalAction(Exception):
    """A seat tried something the rules forbid. The referee refuses; it never
    silently coerces, because a coerced illegal move hides a real agent bug."""


#: Same cap as `cabal`. A seat that rambles pays for everyone's context.
MAX_UTTERANCE_CHARS = 280

#: The public record is re-sent on every call, so an unbounded one turns a long day
#: into a quadratic context bill. A one-night game never reaches this; the bound is
#: here so a longer variant cannot silently acquire the problem.
MAX_RECORD_LINES = 60


@dataclass
class ChangelingReferee:
    setup: Setup
    night: NightResult
    theme: Theme = DEFAULT_THEME
    discussion_rounds: int = 2
    phase: Phase = Phase.DISCUSS
    round_index: int = 0
    votes: dict[int, int] = field(default_factory=dict)
    accused: tuple[int, ...] = ()
    winner: str | None = None
    reason: str = ""
    public_events: list[tuple[str, str]] = field(default_factory=list)
    #: Referee-side only. Carries the night's narrative, which names seats and cards
    #: in the same breath and reaches no model ever.
    referee_log: list[str] = field(default_factory=list)

    @property
    def n(self) -> int:
        return self.setup.n

    @classmethod
    def new(cls, n: int = 5, seed: int | None = None,
            theme: Theme = DEFAULT_THEME, discussion_rounds: int = 2,
            choose=None) -> "ChangelingReferee":
        setup = SETUPS[n]
        rng = random.Random(seed)
        night = resolve_night(setup, rng, choose)
        ref = cls(setup=setup, night=night, theme=theme,
                  discussion_rounds=discussion_rounds)
        ref.referee_log.extend(night.log)
        # The ONLY thing the night puts in the public record. It says that a night
        # happened and nothing about who moved in it.
        ref.public_events.append(
            ("event", "Night passes. At dawn everyone is at the table, and the "
                      "cards have had all night to move."))
        ref.public_events.append(
            ("event", f"Discussion opens: {discussion_rounds} round(s), seat 0 "
                      f"first."))
        return ref

    # ---- what a seat may see -------------------------------------------------

    def entitled_knowledge(self, seat: int) -> tuple[Knowledge, ...]:
        """Exactly what the night told this seat. Never recomputed from dawn state -
        the reveals are historical facts, and half their interest is that they may
        have stopped being true."""
        return self.night.knowledge[seat]

    def believes(self, seat: int) -> Card:
        """The card this seat last SAW itself holding. The only self-fact it may be
        told, and for a diverged seat it is false."""
        return self.night.belief[seat]

    def holds(self, seat: int) -> Card:
        """The card this seat HOLDS at dawn. Decides the win. Referee-side."""
        return self.night.truth[seat]

    def public_state(self) -> dict:
        return {
            "n": self.n,
            "phase": self.phase.value,
            "round": self.round_index,
            "rounds": self.discussion_rounds,
            "deck": sorted(c.key for c in self.setup.deck),
            "centre_count": self.setup.centre,
            "votes_cast": len(self.votes),
        }

    def seat_view(self, seat: int) -> SeatView:
        """Belief goes in ``own_role``. This single line is the rung's thesis, and
        putting ``self.holds(seat)`` here instead would pass every ``cabal``-era
        test while breaking the property the game exists to demonstrate."""
        card = self.believes(seat)
        return SeatView(
            seat=seat,
            own_role=self.theme.card_names[card.key],
            own_team=self.theme.side_names[card.side],
            knowledge=self.entitled_knowledge(seat),
            public=self.public_state(),
        )

    def reveal_forms(self, seat: int, key: str) -> list[str]:
        """**Every phrasing this referee can emit that ties ``seat`` to ``key``.**

        One source, read by both the renderer and the audit, and that is the whole
        point of the method existing. The audit below matches on these strings
        rather than on a bare card name, because this deck holds duplicates - two
        ``pack``, two ``bystander`` - so a bare name is not a seat's secret: telling
        a wolf that seat 4 is its partner puts "Werewolf" in the bytes while saying
        nothing whatever about the OTHER wolf.

        A richer search term buys precision and costs a false-negative risk: a
        phrasing written somewhere else would tie a seat to a card in bytes the
        audit does not search for, which is the shipped leak the naive-matching
        invariant is there to prevent. That risk is answered structurally rather
        than by care - ``_knowledge_line`` builds its output from this list, and
        ``test_referee`` asserts that every line it can produce is a member of it.
        A new phrasing is audited by construction, or it fails a test.
        """
        name = self.theme.card_names[key]
        forms = [f"Seat {seat} held the {name}."]
        if key == "pack":
            forms.append(f"Seat {seat} is one of your own.")
        return forms

    def self_reveal_forms(self, key: str) -> list[str]:
        """The phrasings that would tell a seat what it HOLDS. Separate from
        ``reveal_forms`` because the referee addresses a seat in the second person,
        and a self-leak therefore looks nothing like a third-party one."""
        return [f"went to sleep as the {self.theme.card_names[key]}"]

    def _knowledge_line(self, k: Knowledge) -> str:
        """One entitled reveal, in the theme's vocabulary."""
        if k.label == "switched":
            return f"  - Seat {k.seat} is one of the two whose cards you exchanged."
        if is_centre(k.seat):
            name = self.theme.card_names[k.label]
            return f"  - Centre card {centre_slot(k.seat) + 1} is the {name}."
        if k.label == "fellow-pack":
            return "  - " + self.reveal_forms(k.seat, "pack")[1]
        return "  - " + self.reveal_forms(k.seat, k.label)[0]

    def preamble(self) -> str:
        """The rules, in the theme's vocabulary. **Byte-identical for every seat.**

        It has to name every card in the deck, because counting claims against the
        multiset is the game's central deduction and a seat that cannot do it is
        playing blind. That puts every card name into every render, which is why
        this text is a separate method and not part of the seat's own lines: a
        string that is the same for all seats carries no information about any seat,
        so it cannot be the vehicle of a per-seat leak. ``test_referee`` asserts the
        invariance rather than trusting this docstring - the moment a seat fact is
        interpolated in here, that assertion is what catches it.
        """
        counts: dict[str, int] = {}
        for card in self.setup.deck:
            counts[card.key] = counts.get(card.key, 0) + 1
        # Listed in NIGHT ORDER, which is public rules and is doing real work: it
        # is what lets a seat reason about whether a reading could since have gone
        # stale. A seat that cannot tell whether the looking happened before or
        # after the moving cannot evaluate its own knowledge, let alone a claim.
        order = {act: i for i, act in enumerate(NIGHT_ORDER)}
        deck_lines = [
            f"  {counts[c.key]}x {self.theme.card_names[c.key]} - {c.power}."
            for c in sorted({c.key: c for c in self.setup.deck}.values(),
                            key=lambda c: (order.get(c.act, len(order)), c.key))
        ]
        lines: list[str] = []
        if self.theme.blurb:
            lines += [self.theme.blurb, ""]
        lines += [
            f"Players: {self.n} seats, numbered 0..{self.n - 1}.",
            "The deck, all of it, in hands or in the centre, and what each card "
            "does. They act in this order, each one on whatever the one before it "
            "left behind:",
            *deck_lines,
            f"{self.setup.centre} of those cards lie face down in the centre and "
            f"belong to nobody.",
            # Positive framing, per .claude/rules/model-facing-text.md: state the
            # standing rule rather than warning against trusting your own card.
            "Cards move at night. You know what you went to sleep as; what you "
            "hold now is whatever the night left you, and at dawn you win with the "
            "side of the card in front of you.",
        ]
        if self.setup.require_seated_pack:
            lines.append(f"At least one {self.theme.card_names['pack']} was dealt "
                         f"to a seat.")
        return "\n".join(lines)

    def self_line(self, seat: int) -> str:
        """What the referee asserts about this seat TO this seat. One line, so the
        self-leak has exactly one place it can live and the audit has exactly one
        place to look."""
        v = self.seat_view(seat)
        return (f"You are seat {v.seat}. You went to sleep as the {v.own_role} "
                f"({v.own_team}).")

    def seat_lines(self, seat: int, include_speech: bool = True) -> str:
        """Everything the referee put in front of THIS seat and not the others: its
        own line, its night, and the public record."""
        lines = [self.self_line(seat)]
        knowledge = self.entitled_knowledge(seat)
        if knowledge:
            lines.append("What your night gave you:")
            lines += [self._knowledge_line(k) for k in knowledge]
        else:
            lines.append("Your night gave you nothing to go on. Reason from the "
                         "table.")
        record = [text for tag, text in self.public_events
                  if include_speech or tag == "event"]
        if record:
            lines += ["", "The table so far:"]
            lines += [f"  {line}" for line in record[-MAX_RECORD_LINES:]]
        return "\n".join(lines)

    def render_context(self, seat: int, include_speech: bool = True) -> str:
        """The exact text a player agent receives for this seat. Whatever is absent
        here is invisible to that agent."""
        return self.preamble() + "\n" + self.seat_lines(seat, include_speech)

    # ---- the ask -------------------------------------------------------------

    def acting_seats(self) -> tuple[int, ...]:
        """Whose turn it is. Used by the gate #1 audit, which must see the ASK as
        well as the context - a card name added to a prompt string is bytes leaving
        for the model like any other, and exactly the regression that would
        otherwise go unseen."""
        if self.phase is Phase.DISCUSS:
            return tuple(range(self.n))
        if self.phase is Phase.VOTE:
            return tuple(s for s in range(self.n) if s not in self.votes)
        return ()

    def ask(self, seat: int) -> str:
        """The question put to one seat, phrased positively per
        ``.claude/rules/model-facing-text.md``.

        A `cabal`-style bound on the ``think`` field ("keep it under 30 words,
        because a reply long enough to be truncated is one the referee has to
        refuse") was tried here on 2026-08-26 and REMOVED: measured against the same
        seed and model it moved the fallback rate not at all, 4/15 either way. The
        reasoning that was eating the budget happens in the model's own
        ``reasoning_content`` channel BEFORE it writes a field, so no instruction
        about a field can bound it. The lever that worked is
        ``Backend.enable_thinking``; the argument is there.

        Left out rather than left in, per that rule's last line: a prompt line with
        no measured benefit is load with no payer, and carrying it would put an
        unattributed difference between this game's ask and `cabal`'s.
        """
        if self.phase is Phase.DISCUSS:
            return ("Speak to the table. Reply as one JSON object: "
                    '{"think": "your private reasoning", '
                    '"say": "what the table hears"}. '
                    f"Keep `say` under {MAX_UTTERANCE_CHARS} characters.")
        if self.phase is Phase.VOTE:
            legal = ", ".join(str(s) for s in self.legal_votes(seat))
            return ("Point at one seat. Everyone points at once, and the seat with "
                    "the most fingers is accused. Reply as one JSON object: "
                    '{"think": "your private reasoning", "vote": <seat number>}. '
                    f"Choose from: {legal}.")
        raise IllegalAction(f"nothing to ask in phase {self.phase.value}")

    def prompt_for(self, seat: int, include_speech: bool = True) -> str:
        return self.render_context(seat, include_speech) + "\n\n" + self.ask(seat)

    # ---- the day -------------------------------------------------------------

    def speaking_order(self) -> list[int]:
        return list(range(self.n))

    def speak(self, seat: int, text: str) -> str:
        """Publish one utterance and RETURN what was published.

        Returning it matters: the driver records what the table saw, and the only
        alternative is re-deriving it by splitting the rendered event string, which
        is a parser of this method's own formatting.
        """
        if self.phase is not Phase.DISCUSS:
            raise IllegalAction(f"seat {seat} spoke during {self.phase.value}")
        said = " ".join(text.split())[:MAX_UTTERANCE_CHARS]
        self.public_events.append(("speech", f"Seat {seat}: {said}"))
        return said

    def close_round(self) -> None:
        """One full pass of the table is done."""
        if self.phase is not Phase.DISCUSS:
            raise IllegalAction("closed a discussion round outside discussion")
        self.round_index += 1
        if self.round_index >= self.discussion_rounds:
            self.phase = Phase.VOTE
            self.public_events.append(
                ("event", "Discussion is over. Everyone points at once."))

    def legal_votes(self, seat: int) -> list[int]:
        """Every other seat. A seat pointing at itself is refused rather than
        coerced, so a model that does it shows up as a fallback and not as a
        silently rewritten vote."""
        return [s for s in range(self.n) if s != seat]

    def cast(self, seat: int, target: int) -> None:
        """One vote, held back until every seat has cast.

        Votes are simultaneous, so nothing is published as it arrives - a seat that
        could read the tally mid-vote would be playing a different game from the one
        the rules describe.
        """
        if self.phase is not Phase.VOTE:
            raise IllegalAction(f"seat {seat} voted during {self.phase.value}")
        if seat in self.votes:
            raise IllegalAction(f"seat {seat} voted twice")
        if target not in self.legal_votes(seat):
            raise IllegalAction(
                f"seat {seat} pointed at {target}; legal targets are "
                f"{self.legal_votes(seat)}")
        self.votes[seat] = target
        if len(self.votes) == self.n:
            self._resolve()

    def _resolve(self) -> None:
        tally: dict[int, int] = {}
        for target in self.votes.values():
            tally[target] = tally.get(target, 0) + 1
        top = max(tally.values())
        self.accused = tuple(sorted(s for s, c in tally.items() if c == top))

        self.public_events.append(
            ("event", "Votes: " + ", ".join(
                f"seat {s} -> seat {t}" for s, t in sorted(self.votes.items()))))
        self.public_events.append(
            ("event", "Accused: " + ", ".join(f"seat {s}" for s in self.accused)
                      + (" (tied, so all of them)" if len(self.accused) > 1
                         else "")))

        caught = [s for s in self.accused if self.holds(s).side is Side.PACK]
        if caught:
            self.winner = Side.VILLAGE.value
            self.reason = (
                f"WINNER: {self.theme.side_names[Side.VILLAGE]} "
                f"(seat {caught[0]} was holding the "
                f"{self.theme.card_names['pack']} at dawn)")
        else:
            self.winner = Side.PACK.value
            self.reason = (
                f"WINNER: {self.theme.side_names[Side.PACK]} "
                f"(no accused seat held the "
                f"{self.theme.card_names['pack']} at dawn)")
        self.phase = Phase.DONE
        # The reveal is referee-side. It lands in the transcript, never in a render:
        # by the time it is written the game is over, but a render is still a render.
        self.referee_log.append(self.reason)
        self.referee_log.append(
            "dawn truth: " + ", ".join(
                f"seat {s}={self.holds(s).key}" for s in range(self.n)))
        self.referee_log.append(
            "diverged seats: " + (", ".join(map(str, sorted(self.night.diverged())))
                                  or "none"))

    # ---- gate #1 -------------------------------------------------------------

    def secret_terms(self) -> dict[int, list[str]]:
        """Seat -> the strings that would betray the card it HOLDS at dawn.

        Keyed on truth, which is the difference from ``cabal``: a diverged seat's
        secret is the card it holds, and that is kept from the seat itself as well
        as from the table. Terms are ASSOCIATIONS, not bare card names - see
        ``reveal_forms`` for why a bare name cannot be a secret in a deck that
        holds duplicates.
        """
        return {s: self.reveal_forms(s, self.holds(s).key) for s in range(self.n)}

    def entitled_seats(self, viewer: int) -> set[int]:
        """Whose dawn card this viewer may legitimately see named in its render.

        Three sources, and the third is the one ``cabal`` has no analogue for:

        - seats the night named to it, where that reveal still matches dawn truth;
        - itself, **only when its belief still matches its truth**;
        - nothing else. A reveal that has since been invalidated is NOT entitlement:
          the seat may still believe it, and the referee may not restate it.
        """
        entitled = set()
        for k in self.entitled_knowledge(viewer):
            if is_centre(k.seat):
                continue
            if k.label == "fellow-pack" and self.holds(k.seat).side is Side.PACK:
                entitled.add(k.seat)
            elif k.label == self.holds(k.seat).key:
                entitled.add(k.seat)
        if self.believes(viewer).key == self.holds(viewer).key:
            entitled.add(viewer)
        return entitled

    def audit(self, viewer: int) -> list[tuple[int, str]]:
        """Gate #1 for one seat. Two naive scans at two scopes, because this game
        made one scope insufficient and the other unsound.

        **Other seats' cards, against everything written to this seat.** Same check
        ``cabal`` runs, minus the preamble, which is seat-invariant and therefore
        cannot carry a per-seat secret.

        **This seat's own card, against its own line only.** Needed because a
        diverged seat is not entitled to its own truth. Scoped to ``self_line``
        because this deck holds DUPLICATE cards - two ``pack``, two ``bystander`` -
        so a card name can legitimately appear in a true statement about one seat
        while being another seat's secret. ``cabal`` never had that: its role keys
        are unique, so a term identified a seat. Auditing a seat's own term against
        its whole context would report a leak every time a spotter was told about
        the OTHER wolf, which is a reveal it is entitled to.

        Both halves stay naive substring matching, per the repo invariant. What
        changed is where each one looks, and the narrowing is argued rather than
        convenient: ``self_line`` is the only place the referee asserts anything
        about this seat to this seat, so it is the only place a self-leak can live.
        """
        others = {s: t for s, t in self.secret_terms().items() if s != viewer}
        leaks = find_leaks(
            self.seat_lines(viewer, include_speech=False),
            others,
            self.entitled_seats(viewer),
            viewer,
        )
        if viewer not in self.entitled_seats(viewer):
            leaks += find_leaks(
                self.self_line(viewer),
                {viewer: self.self_reveal_forms(self.holds(viewer).key)},
                set(),
                viewer,
                self_is_secret=True,
            )
        return leaks

    def audit_all(self) -> dict[int, list[tuple[int, str]]]:
        found = {s: self.audit(s) for s in range(self.n)}
        return {s: leaks for s, leaks in found.items() if leaks}
