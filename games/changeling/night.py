"""The night, and the split between what is true and what a seat believes.

This module is the whole reason the rung exists, so it is kept pure and separate
from the day: deal, resolve five ordered steps, return truth and belief side by
side. No model call and no I/O reaches in here, which is what makes the property
this game is built to prove a unit test rather than an opinion.

Two dictionaries leave this module and the difference between them is the point:

  - ``truth``  - the card each seat HOLDS at dawn. Decides the win. Referee-side.
  - ``belief`` - the last card each seat actually SAW itself holding. The only one
    that may ever be rendered to that seat.

They start identical and diverge in exactly three ways, all of them silent to the
seat affected: it was robbed by ``TAKE``, it was moved by ``SWITCH``, or it is the
``DRINK`` seat, which swaps itself into the centre without looking. Nothing in the
night reconciles them, and no later phase does either.

See ``RULES.md`` for the model these functions implement.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from core.observability import Knowledge
from games.changeling.roles import (NIGHT_ORDER, Act, Card, Setup, Side)

#: Centre slots addressed as negative seats, so one ``Knowledge`` type covers both
#: without teaching ``core`` about a centre that only this game has. Slot 0 is -1.
#: A third game that also needs it is the evidence to promote the idea; one is not.
def centre_ref(slot: int) -> int:
    return -1 - slot


def is_centre(ref: int) -> bool:
    return ref < 0


def centre_slot(ref: int) -> int:
    return -1 - ref


#: A deal is retried until it seats a ``pack``. The predicate is the policy; this
#: is the structural bound beside it, because a predicate that can never be
#: satisfied (a deck with no ``pack``) would otherwise spin forever unattended.
MAX_DEAL_ATTEMPTS = 200


class ImpossibleDeal(Exception):
    """The deck cannot satisfy the setup's constraints. A loud failure, because the
    alternative is a run that hangs or silently plays a different game."""


@dataclass
class NightResult:
    """Everything the night produced. ``truth`` and ``belief`` are both here on
    purpose: a caller that wants only one of them should have to say which."""

    dealt: dict[int, Card]           # what each seat was DEALT - decides who acts
    truth: dict[int, Card]           # dawn holding - decides the win
    belief: dict[int, Card]          # last card the seat SAW itself holding
    centre: list[Card]               # dawn centre, in slot order
    knowledge: dict[int, tuple[Knowledge, ...]]
    #: Referee-side narrative of what actually happened, for the transcript. Never
    #: rendered to any seat - it names cards and seats in the same breath.
    log: list[str] = field(default_factory=list)

    def diverged(self) -> set[int]:
        """Seats whose belief is no longer their truth. Referee-side; the whole
        point is that no seat can compute this about itself."""
        return {s for s in self.truth if self.truth[s].key != self.belief[s].key}

    def side_of(self, seat: int) -> Side:
        """Which side a seat WINS with - always from truth, never from belief."""
        return self.truth[seat].side


def deal(setup: Setup, rng: random.Random) -> tuple[dict[int, Card], list[Card]]:
    """Deal seats and centre, refusing a deal that seats no ``pack``.

    Both ``pack`` cards land in the centre in 6/56 of unconstrained deals at this
    size, and every one of those games is unwinnable by accusation - not hard, but
    undefined. RULES.md states the constraint publicly so seats may reason from it.
    """
    deck = list(setup.deck)
    for _ in range(MAX_DEAL_ATTEMPTS):
        rng.shuffle(deck)
        seats = {i: deck[i] for i in range(setup.n)}
        centre = deck[setup.n:]
        if not setup.require_seated_pack:
            return seats, centre
        if any(c.side is Side.PACK for c in seats.values()):
            return seats, centre
    raise ImpossibleDeal(
        f"no deal in {MAX_DEAL_ATTEMPTS} attempts seated a pack card - check the "
        f"deck ({[c.key for c in setup.deck]}) against require_seated_pack")


def legal_targets(seat: int, act: Act, n: int, centre: int) -> list:
    """What the acting seat may choose. Returned as plain values so a policy can be
    handed them verbatim and a referee can validate a reply against them."""
    others = [s for s in range(n) if s != seat]
    if act is Act.LOOK:
        pairs = [(i, j) for i in range(centre) for j in range(i + 1, centre)]
        return [("seat", s) for s in others] + [("centre", p) for p in pairs]
    if act is Act.TAKE:
        return [("seat", s) for s in others]
    if act is Act.SWITCH:
        return [("seats", (i, j))
                for a, i in enumerate(others) for j in others[a + 1:]]
    if act is Act.DRINK:
        return [("centre", s) for s in range(centre)]
    return []


def random_chooser(rng: random.Random):
    """The control policy for night choices. A night whose targets are chosen at
    random is the baseline any model-driven night has to beat, and it is the only
    honest way to get a chance figure for this game - see RULES.md."""
    def choose(seat: int, act: Act, options: list):
        return rng.choice(options)
    return choose


def resolve_night(setup: Setup, rng: random.Random, choose=None,
                  dealt: dict[int, Card] | None = None,
                  centre: list[Card] | None = None) -> NightResult:
    """Deal, then run the five steps in order, and return truth beside belief.

    ``choose(seat, act, options)`` picks each night target and must return one of
    ``options``. It defaults to the seeded random control. It is injected rather
    than imported so the same function serves the random arm, a model-driven arm,
    and a test that needs one exact night.

    ``dealt``/``centre`` pin the deal instead of drawing one. A caller that needs a
    NAMED night - a test stating the position it means, or a replay of a recorded
    game - should not have to hunt for a seed that happens to produce it.
    """
    choose = choose or random_chooser(rng)
    if (dealt is None) != (centre is None):
        raise ValueError("pin both `dealt` and `centre`, or neither")
    if dealt is None:
        dealt, centre = deal(setup, rng)
    else:
        dealt = dict(dealt)
        centre = list(centre)
        if sorted(dealt) != list(range(setup.n)) or len(centre) != setup.centre:
            raise ValueError(
                f"pinned deal must cover seats 0..{setup.n - 1} and "
                f"{setup.centre} centre slots")

    truth = dict(dealt)                      # mutated by the night
    belief = dict(dealt)                     # only a seat that LOOKS updates this
    knowledge: dict[int, list[Knowledge]] = {s: [] for s in range(setup.n)}
    log: list[str] = [
        "deal: " + ", ".join(f"seat {s}={c.key}" for s, c in sorted(dealt.items()))
        + " | centre=" + ", ".join(c.key for c in centre)]

    def pick(seat: int, act: Act):
        options = legal_targets(seat, act, setup.n, setup.centre)
        if not options:
            return None
        chosen = choose(seat, act, options)
        if chosen not in options:
            raise ValueError(
                f"seat {seat} chose {chosen!r} for {act.value}, which is not a "
                f"legal target")
        return chosen

    for step in NIGHT_ORDER:
        # Who acts is decided by the DEALT card, never by what the seat now holds.
        # A seat robbed at TAKE still acted at MEET, and a seat handed `swapper`
        # never acts at all. RULES.md: you act on the card you were dealt.
        actors = sorted(s for s in range(setup.n) if dealt[s].act is step)

        if step is Act.MEET:
            # Grouped by dealt KEY, not by the act. Until a second meeting card
            # existed the two were the same thing, and a village pair added under
            # the old code would have woken up with the wolves - a leak the audit
            # could not have caught, because the referee would have been telling
            # each seat something the rules genuinely entitled it to.
            for seat in actors:
                if not dealt[seat].meets_own_kind:
                    continue
                kind = dealt[seat].key
                fellows = [s for s in actors
                           if s != seat and dealt[s].key == kind]
                for other in fellows:
                    knowledge[seat].append(Knowledge(other, f"fellow-{kind}"))
                log.append(f"meet: seat {seat} ({kind}) sees {fellows or 'no one'}")
            continue

        for seat in actors:
            chosen = pick(seat, step)

            if step is Act.LOOK:
                kind, target = chosen
                if kind == "seat":
                    knowledge[seat].append(Knowledge(target, truth[target].key))
                    log.append(f"look: seat {seat} sees seat {target} = "
                               f"{truth[target].key}")
                else:
                    for slot in target:
                        knowledge[seat].append(
                            Knowledge(centre_ref(slot), centre[slot].key))
                    log.append(f"look: seat {seat} sees centre slots {target} = "
                               f"{[centre[s].key for s in target]}")

            elif step is Act.TAKE:
                _, victim = chosen
                truth[seat], truth[victim] = truth[victim], truth[seat]
                # It looks, so its belief follows its truth. The victim is not told
                # and its belief stays where it was - the first way the two split.
                belief[seat] = truth[seat]
                knowledge[seat].append(Knowledge(seat, truth[seat].key))
                knowledge[seat].append(Knowledge(victim, truth[victim].key))
                log.append(f"take: seat {seat} robs seat {victim}, now holds "
                           f"{truth[seat].key}; seat {victim} holds "
                           f"{truth[victim].key} and is not told")

            elif step is Act.SWITCH:
                _, (a, b) = chosen
                truth[a], truth[b] = truth[b], truth[a]
                # Neither victim looks, and the switcher never sees either card.
                # Positional knowledge: a relation, with no card attached.
                knowledge[seat].append(Knowledge(a, "switched"))
                knowledge[seat].append(Knowledge(b, "switched"))
                log.append(f"switch: seat {seat} exchanges seats {a} and {b}, "
                           f"blind; neither is told")

            elif step is Act.WAKE:
                # Last of all, so what it sees is what it keeps. This is the only
                # seat the night hands a belief that is guaranteed true at dawn -
                # and the only one that learns it was moved, since the card it is
                # shown is not the one it went to sleep as.
                belief[seat] = truth[seat]
                knowledge[seat].append(Knowledge(seat, truth[seat].key))
                log.append(f"wake: seat {seat} looks and sees {truth[seat].key}")

            elif step is Act.DRINK:
                _, slot = chosen
                truth[seat], centre[slot] = centre[slot], truth[seat]
                # It does NOT look. Its belief stays `deceived` and is now false by
                # construction - the only seat whose entitled knowledge is wrong.
                log.append(f"drink: seat {seat} swaps with centre slot {slot}, "
                           f"blind; now holds {truth[seat].key} and believes "
                           f"{belief[seat].key}")

    return NightResult(
        dealt=dealt,
        truth=truth,
        belief=belief,
        centre=centre,
        knowledge={s: tuple(k) for s, k in knowledge.items()},
        log=log,
    )
