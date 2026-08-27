"""Census the changeling knowledge strata a deck actually produces.

No model, no GPU, no play - it resolves nights and counts. The deduction gate is
cut on the blind villager stratum, so how big that stratum is decides whether a
run of N games can answer anything, and until S10 the answer was being read off the
DEAL rather than off what the night TOLD each seat.

Prints both rules side by side, because the whole point of the S10 change is the
gap between them and a number without its predecessor cannot show one. Every figure
RULES.md quotes about stratum sizes comes from here::

    py -3 -m eval.strata               # the shipped deck, 4000 nights
    py -3 -m eval.strata --nights 400  # a quick look

The night is seeded from ``--seed``, so two runs of the same command agree. Votes
and models are not involved: a seat's stratum is fixed the moment the night ends.
"""

from __future__ import annotations

import argparse
import random
from collections import Counter

from games.changeling.night import resolve_night
from games.changeling.roles import KNOWLEDGE_CLASSES, SETUP_5, Setup, Side

#: The decks this reports on. ``SETUP_5`` is the shipped one and the only deck any
#: recorded number was played on; a caller adds a row here to price a new deck
#: before building it.
DECKS: dict[str, Setup] = {"SETUP_5": SETUP_5}


def dealt_class(night, seat: int) -> str:
    """The pre-S10 rule, kept so the change is showable rather than asserted."""
    return night.dealt[seat].knowledge_class


def census(setup: Setup, nights: int, seed: int) -> dict:
    """Resolve ``nights`` nights and count seats by stratum under both rules."""
    rng = random.Random(seed)
    told: Counter = Counter()
    dealt: Counter = Counter()
    #: villager BY DAWN - the gate scores the side a seat wins with, so a seat
    #: robbed into the village is a villager however it was dealt.
    blind_villagers = 0
    told_nothing_but_labelled = 0
    villager_identity_dealt = 0
    meet_seats = meet_without_fellow = 0

    for _ in range(nights):
        night = resolve_night(setup, rng, choose=None)
        for seat in range(setup.n):
            t, d = night.knowledge_class(seat), dealt_class(night, seat)
            told[t] += 1
            dealt[d] += 1
            villager = night.side_of(seat) is Side.VILLAGE
            if villager and d == "identity":
                villager_identity_dealt += 1
            if villager and not night.knowledge[seat] and d != "false":
                blind_villagers += 1
                if d != "none":
                    told_nothing_but_labelled += 1
            if night.dealt[seat].meets_own_kind:
                meet_seats += 1
                if not night.knowledge[seat]:
                    meet_without_fellow += 1

    seats = nights * setup.n
    return {
        "nights": nights, "seats": seats,
        "told": told, "dealt": dealt,
        "blind_villagers": blind_villagers,
        "told_nothing_but_labelled": told_nothing_but_labelled,
        "villager_identity_dealt": villager_identity_dealt,
        "meet_seats": meet_seats,
        "meet_without_fellow": meet_without_fellow,
    }


def report(name: str, c: dict) -> list[str]:
    out = [f"== {name}  {c['nights']} nights, {c['seats']} seat-nights", "",
           "   stratum      TOLD (S10)        DEALT (pre-S10)     move",
           "   " + "-" * 56]
    for cls in KNOWLEDGE_CLASSES:
        t, d = c["told"][cls], c["dealt"][cls]
        move = t - d
        out.append(f"   {cls:<12} {t:>5} ({t / c['seats']:>6.2%})   "
                   f"{d:>5} ({d / c['seats']:>6.2%})   {move:+6d}")
    out += [
        "",
        f"   MEET seats given no fellow reveal   {c['meet_without_fellow']}/"
        f"{c['meet_seats']} "
        f"({c['meet_without_fellow'] / c['meet_seats']:.1%})"
        if c["meet_seats"] else "   no MEET card in this deck",
        f"   blind villager seat-nights          {c['blind_villagers']}",
        f"   ...of those, MISLABELLED pre-S10    {c['told_nothing_but_labelled']} "
        f"({c['told_nothing_but_labelled'] / c['blind_villagers']:.1%} of the "
        f"stratum was hidden elsewhere)"
        if c["blind_villagers"] else "   no blind villagers in this deck",
        f"   villager `identity` seats (pre-S10) told nothing   "
        f"{c['told_nothing_but_labelled']}/{c['villager_identity_dealt']} "
        f"({c['told_nothing_but_labelled'] / c['villager_identity_dealt']:.1%} "
        f"- the dilution on the other side of the same move)"
        if c["villager_identity_dealt"] else "",
    ]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--nights", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--deck", default=None, choices=sorted(DECKS),
                    help="one deck (default: every deck in DECKS)")
    args = ap.parse_args(argv)

    names = [args.deck] if args.deck else sorted(DECKS)
    for name in names:
        for line in report(name, census(DECKS[name], args.nights, args.seed)):
            print(line)
        print()
    # The two rules must disagree, or S10 changed nothing and this tool is lying.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
