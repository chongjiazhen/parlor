"""Small-sample statistics, shared by every game in the arena.

Promoted from ``eval/run_games.py`` when the second game needed it, which is the
bar this repo sets for anything entering ``core/``: a primitive earns its place on
evidence that game #2 uses it, never on a guess that one might.

Nothing here knows about roles, seats, or hidden information. That is the test for
whether a thing belongs in the spine.
"""

from __future__ import annotations

import math
import random


def wilson(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval. Small-N proportions need their error bars visible, or a
    3-of-5 run reads as a result."""
    if total == 0:
        return (0.0, 0.0)
    p = hits / total
    d = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / d
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def bootstrap_ci(units: list, statistic, resamples: int = 4000, seed: int = 7,
                 lo: float = 2.5, hi: float = 97.5) -> tuple[float, float] | None:
    """Percentile CI, resampling whole UNITS rather than observations.

    The unit is a game, not a vote. Votes inside one game share a deal, a night and
    a table, so treating them as independent draws reports an interval far tighter
    than the data supports - which is how a run comes to claim a result it has not
    got. ``statistic`` takes a resampled list of units and returns a float, or
    ``None`` when that resample cannot support one.
    """
    if not units:
        return None
    rng = random.Random(seed)
    n = len(units)
    out: list[float] = []
    for _ in range(resamples):
        sample = [units[rng.randrange(n)] for _ in range(n)]
        value = statistic(sample)
        if value is not None:
            out.append(value)
    if not out:
        return None
    out.sort()
    return (out[int(len(out) * lo / 100)],
            out[min(len(out) - 1, int(len(out) * hi / 100))])
