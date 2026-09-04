"""Count what a seed block DEALS, before any card is spent on playing it.

A criterion's §Power needs the number of decisions its statistic will actually
have to read. That number is a property of the deal, not of play - random play
and a live arm agree on it seat for seat, which is the check
`eval.partner_verdict` already runs - so it is knowable in seconds, on CPU,
before launch.

It was not known. The partner criterion took ~198 partner-eligible votes at 200
games from seeds 5000..5199 and then ran on 17000..17199, which deals 168: a
half-width of 6.82 points where §Power promised 5.9, found after 5.2 h of GPU.
Every other power section in the tree has the same shape.

    py -3 -m eval.deal_census --games 200 --seed 17000
    py -3 -m eval.deal_census --games 200 --seed 5000 --seats 5 --theme folk

**The deal comes from `ChangelingReferee.new`, called exactly as `one_game`
calls it**, rather than from a second copy of the night. The eligibility rule
comes from `eval.changeling_audit.reveals`, the same function the verdict tools
read records with. Neither is restated here, because a census that drifts from
the audit measures nothing the audit will later agree with.

It counts the partner statistic and gate #3's blind stratum. A third goes in
`RULES`, not in a fork of this file.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from eval.changeling_audit import reveals
from games.changeling.referee import ChangelingReferee
from games.changeling.roles import DEFAULT_THEME, THEMES


def _partner_eligible(night) -> int:
    """Seats told a `fellow-pack` at the meet - `partner_votes`'s own rule,
    read off the referee's night log through the audit's own `reveals`."""
    shown = reveals({"log": night.log})
    return sum(1 for labels in shown.values()
               if any(label == "fellow-pack" for _, label in labels))


def _blind_eligible(night) -> int:
    """Village seats at dawn that were told NOTHING, in a winnable game.

    The three filters `run_changeling` applies to the gate #3 stratum, each
    taken from the same source it takes them from: a game with no dawn wolf is
    unwinnable and scores nothing, a pack holder is not a villager vote, and
    blind is `NightResult.knowledge_class` returning "none".
    """
    if not any(c.key == "pack" for c in night.truth.values()):
        return 0
    return sum(1 for seat, card in night.truth.items()
               if card.key != "pack" and night.knowledge_class(seat) == "none")


#: statistic name -> what counts as one readable decision in a single deal.
RULES = {"partner": _partner_eligible, "blind": _blind_eligible}


@dataclass(frozen=True)
class Census:
    games: int
    seed: int
    statistic: str
    per_deal: tuple[int, ...]

    @property
    def eligible(self) -> int:
        return sum(self.per_deal)

    @property
    def per_game(self) -> float:
        return self.eligible / self.games if self.games else 0.0


def census(games: int, seed: int, seats: int = 5, theme: str = "folk",
           statistic: str = "partner") -> Census:
    """Deal `games` nights from `seed` and count readable decisions in each."""
    rule = RULES[statistic]
    counts = []
    for index in range(games):
        ref = ChangelingReferee.new(seats, seed=seed + index,
                                    theme=THEMES.get(theme, DEFAULT_THEME))
        counts.append(rule(ref.night))
    return Census(games, seed, statistic, tuple(counts))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--games", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--seats", type=int, default=5)
    ap.add_argument("--theme", default="folk")
    ap.add_argument("--statistic", default="partner", choices=sorted(RULES))
    a = ap.parse_args(argv)

    c = census(a.games, a.seed, a.seats, a.theme, a.statistic)
    print(f"seeds {a.seed}..{a.seed + a.games - 1}, {a.games} deals, "
          f"{a.seats} seats, theme {a.theme}")
    print(f"  {c.statistic}-eligible decisions: {c.eligible} "
          f"({c.per_game:.2f} per deal)")
    print(f"  deals offering none: {sum(1 for n in c.per_deal if not n)}")
    print("\nQuote this in the criterion's §Power, for THIS block. An eligibility "
          "rate\nmeasured on a block the arm will not play is not that arm's "
          "power.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
