"""The deck's arithmetic, and the control sweep that checks it against play.

**What this measures, and why it comes before any model.** quorum's claim is that
a seat's public statement about a draw can be scored as true, false or
unfalsifiable, because the referee holds the draw. That claim needs a denominator:
how often the office had no legal alternative. A seat that enacts a writ because
it drew three of them has done nothing wrong, and a scorer that counted it as a
minority act would be measuring the deck.

So the forced rate is a property of the COMPOSITION and the control policy, not of
any model, and it is settled here on CPU before a token is spent.

**Two numbers, and they answer different questions.**

- The **exact** rate is combinatorial: draw three from a fresh 17-card deck and
  ask how often they are all one kind. It is derived from the ``Setup`` rather
  than written down, so a variant deck moves it.
- The **realized** rate comes from playing games. It need not equal the exact one:
  cards leave play when they are enacted and the pile is rebuilt from the
  discards, so the composition drifts as a game runs. Whether it drifts ENOUGH to
  matter is the question, and it cannot be answered by arithmetic alone.

The exact figure is therefore the instrument control for the sweep. If the two
agree, the fresh-deck number is a fair denominator for a whole game; if they
diverge, quoting it would misstate every later claim, and the realized one has to
be carried per-run instead.

Nothing here reports a model's behaviour, and nothing here is a gate.

    py -3 -m eval.quorum_deck                 # arithmetic + a 400-game sweep
    py -3 -m eval.quorum_deck --games 2000    # tighter interval
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from itertools import combinations

from core.stats import wilson
from games.quorum.player import RandomPolicy, play_game
from games.quorum.referee import QuorumReferee
from games.quorum.roles import ADVANCES, SETUP_5, Card, Setup, Side


# ---- the arithmetic --------------------------------------------------------

@dataclass(frozen=True)
class ExactRates:
    """Every figure derived from the composition, none of it written down."""

    charters: int
    writs: int
    draws: int                      # C(deck, 3)
    p_forced: float                 # the proposer's three are all one kind
    p_forced_writ: float            # ... all writs, so a charter is impossible
    p_forced_charter: float
    asymmetry: float                # p_forced_writ / p_forced_charter
    p_pair_same: float              # the enactor's two are one kind, under a
                                    # uniformly-discarding proposer

    def line(self) -> str:
        return (f"exact, fresh {self.charters + self.writs}-card deck "
                f"({self.charters} charter / {self.writs} writ): "
                f"proposer forced {self.p_forced:.4%} "
                f"({self.p_forced_writ:.4%} toward the minority, "
                f"{self.p_forced_charter:.4%} toward the majority, "
                f"{self.asymmetry:.2f}x), enactor handed a matching pair "
                f"{self.p_pair_same:.4%}")


def exact_rates(setup: Setup = SETUP_5) -> ExactRates:
    """Enumerate every distinguishable draw of three from a fresh deck.

    Enumerated rather than solved in closed form on purpose: the closed form is a
    hypergeometric identity that has to be rewritten if a third card kind is ever
    added, and this loop does not. The deck is small enough that the cost is
    nothing.

    ``p_pair_same`` is the enactor's side of the cascade, and it needs the
    proposer's policy: a proposer discarding UNIFORMLY leaves a matching pair
    whenever it drew three of a kind, and one time in three when it drew two and
    one. That is the control's number, not a model's - a proposer playing to win
    moves it, which is exactly what makes it worth measuring against this.
    """
    deck = ([Card.CHARTER] * setup.deck_charter + [Card.WRIT] * setup.deck_writ)
    total = forced = forced_writ = forced_charter = 0
    pair_same = 0.0
    for hand in combinations(range(len(deck)), 3):
        cards = [deck[i] for i in hand]
        total += 1
        sides = {ADVANCES[c] for c in cards}
        if len(sides) == 1:
            forced += 1
            if sides == {Side.MINORITY}:
                forced_writ += 1
            else:
                forced_charter += 1
            pair_same += 1.0
        else:
            # two of one kind and one of the other: dropping the singleton is the
            # one discard in three that leaves the enactor no choice
            pair_same += 1.0 / 3.0
    return ExactRates(
        charters=setup.deck_charter,
        writs=setup.deck_writ,
        draws=total,
        p_forced=forced / total,
        p_forced_writ=forced_writ / total,
        p_forced_charter=forced_charter / total,
        asymmetry=(forced_writ / forced_charter) if forced_charter else float("inf"),
        p_pair_same=pair_same / total,
    )


# ---- the sweep -------------------------------------------------------------

@dataclass
class Sweep:
    games: int = 0
    events: int = 0
    forced: int = 0
    forced_writ: int = 0
    forced_charter: int = 0
    pair_same: int = 0
    majority_wins: int = 0
    seeds: list[int] = field(default_factory=list)

    @property
    def rate(self) -> float:
        return self.forced / self.events if self.events else 0.0

    @property
    def pair_rate(self) -> float:
        return self.pair_same / self.events if self.events else 0.0


def sweep(games: int = 400, seed: int = 0, rounds: int = 0) -> Sweep:
    """Play ``games`` random-control games and count what the deck actually did.

    ``rounds=0`` skips discussion: speech costs turns and cannot move a draw, so
    the sweep runs the cascade and nothing else. The seed is per game and recorded,
    so any single game in here can be replayed on its own.
    """
    out = Sweep()
    for i in range(games):
        game_seed = seed + i
        ref = QuorumReferee.new(5, seed=game_seed, discussion_rounds=rounds)
        rng = random.Random(game_seed)
        rec = play_game(ref, {s: RandomPolicy(rng=rng) for s in ref.assignment})
        if rec.error:
            raise SystemExit(f"seed {game_seed}: {rec.error}")
        out.games += 1
        out.seeds.append(game_seed)
        out.majority_wins += rec.winner == Side.MAJORITY.value
        for d in rec.draws:
            out.events += 1
            if d.forced:
                out.forced += 1
                if d.enacted == Card.WRIT.value:
                    out.forced_writ += 1
                else:
                    out.forced_charter += 1
            if len(set(d.passed)) == 1:
                out.pair_same += 1
    return out


# ---- the report ------------------------------------------------------------

#: How far the realized rate may sit from the exact one before the fresh-deck
#: figure stops being a fair denominator for a whole game. Stated here, before the
#: sweep runs, so the threshold cannot be chosen with the answer in view. It is
#: deliberately loose: the question is whether reshuffle drift is a FIRST-ORDER
#: effect, not whether it is exactly zero.
DRIFT_TOLERANCE = 0.03


def report(exact: ExactRates, obs: Sweep) -> list[str]:
    lines = [exact.line()]
    ci = wilson(obs.forced, obs.events)
    pci = wilson(obs.pair_same, obs.events)
    lines.append(
        f"realized, {obs.games} control games, {obs.events} events: "
        f"proposer forced {obs.rate:.4%}"
        + (f" [{ci[0]:.2%}, {ci[1]:.2%}]" if ci else "")
        + f" ({obs.forced_writ} toward the minority, {obs.forced_charter} toward "
          f"the majority), enactor handed a matching pair {obs.pair_rate:.4%}"
        + (f" [{pci[0]:.2%}, {pci[1]:.2%}]" if pci else ""))
    drift = obs.rate - exact.p_forced
    lines.append(f"drift, realized minus exact: {drift:+.4%} "
                 f"(tolerance {DRIFT_TOLERANCE:.0%}, declared before the sweep)")
    if ci and not (ci[0] <= exact.p_forced <= ci[1]):
        lines.append("  the interval EXCLUDES the fresh-deck figure: the reshuffle "
                     "moves the composition measurably, so a run quotes its own "
                     "realized rate and not this arithmetic")
    if abs(drift) > DRIFT_TOLERANCE:
        lines.append("  and the gap is above tolerance, so the fresh-deck figure "
                     "is NOT a fair denominator for a whole game")
    else:
        lines.append("  within tolerance: the fresh-deck figure is a fair "
                     "denominator for a whole game, and the interval above is the "
                     "honest width on it")
    lines.append(
        f"control win split: majority {obs.majority_wins}/{obs.games} "
        f"({obs.majority_wins / obs.games:.2%}) - the chance baseline any later "
        f"win rate is read against, and NOT a claim about either side")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser(
        description="quorum's deck arithmetic and its random-control sweep")
    ap.add_argument("--games", type=int, default=400)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rounds", type=int, default=0,
                    help="discussion rounds per game (speech cannot move a draw)")
    args = ap.parse_args()

    exact = exact_rates()
    obs = sweep(args.games, seed=args.seed, rounds=args.rounds)
    print("=== quorum: what the deck does, before any model plays ===")
    for line in report(exact, obs):
        print(line)


if __name__ == "__main__":
    main()
