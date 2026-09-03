"""The changeling name-form pair, scored as the criterion promised.

``py -3 -m eval.skin_pair_verdict [records-dir]`` reads the four records
``eval/runs/changeling-skin-pair.cmd`` writes - two random controls and two live
arms, ``greek`` and ``greek-named`` - and prints the pre-committed read from
``docs/changeling-skin-pair-criterion.md``, clause by clause. The statistic is
S2's gate #3 statistic per arm (blind villager accuracy, the ``none`` stratum),
the pair's figure is the difference ``greek-named`` minus ``greek``, and the call
turns on whether the Newcombe interval on that difference excludes zero. The game
bootstrap stands beside it; the criterion names the Newcombe interval as the one
that decides, so a disagreement between them is printed, never resolved here.

A voided or refused pair is still AUDITED - every figure prints and the exit
code says 3 - because this repo publishes numbers from records and a scorer that
returns early leaves a published number with no instrument in the tree.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

from core import integrity
from core.stats import bootstrap_ci, wilson
from eval.gate3_bar import OWN_ARM_TOLERANCE, REFERENCE_CHANCE, own_bar
from eval.s5_verdict import (
    BLIND_FLOOR_VOTES,
    accuracy,
    stratum,
    villager_votes,
    votes,
    winnable,
)

#: The bar and its own-arm clause are `eval.gate3_bar` - re-exported here because
#: this module's criterion names them and `rounds_pair_verdict` imported them
#: through this file when it was their only home.
ARMS = ("greek", "greek-named")
BLIND = stratum("none")


@dataclass(frozen=True)
class Arm:
    name: str
    games: list[dict]
    fallback_rate: float
    recovered_rate: float = 0.0

    @property
    def scored(self) -> list[dict]:
        return winnable(self.games)

    @property
    def blind(self) -> tuple[int, int]:
        """(hits, votes) on the blind stratum."""
        hits = sum(1 for g in self.scored for v in villager_votes(g)
                   if BLIND(v) and v["target_holds_pack"])
        return hits, votes(self.scored, BLIND)

    @property
    def blind_rate(self) -> float | None:
        hits, n = self.blind
        return hits / n if n else None


@dataclass(frozen=True)
class Verdict:
    call: str                      # INFORMS | NOT SHOWN | VOID | REFUSED
    reasons: tuple[str, ...]
    diff: float | None
    newcombe: tuple[float, float] | None
    bootstrap: tuple[float, float] | None


def newcombe(h1: int, n1: int, h2: int, n2: int, z: float = 1.96
             ) -> tuple[float, float] | None:
    """Newcombe's method 10: a Wilson-score interval for p2 - p1 over two
    independent proportions. ``None`` when either arm is empty, never a
    zero-width interval, for the reason ``core.stats.wilson`` gives."""
    w1, w2 = wilson(h1, n1, z), wilson(h2, n2, z)
    if w1 is None or w2 is None:
        return None
    p1, p2 = h1 / n1, h2 / n2
    (l1, u1), (l2, u2) = w1, w2
    diff = p2 - p1
    lo = diff - math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)
    hi = diff + math.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
    return (max(-1.0, lo), min(1.0, hi))


def paired_bootstrap(games_a: list[dict], games_b: list[dict]
                     ) -> tuple[float, float] | None:
    """Resample GAMES, keeping each seed's two plays together. The arms share
    seeds by construction, so the unit is the pair of games dealt from one seed,
    matched on the record's ``game`` index and never on file position."""
    by_b = {g["game"]: g for g in winnable(games_b)}
    pairs = [(g, by_b[g["game"]]) for g in winnable(games_a) if g["game"] in by_b]

    def stat(sample):
        a = accuracy([p[0] for p in sample], BLIND)
        b = accuracy([p[1] for p in sample], BLIND)
        return None if a is None or b is None else b - a

    return bootstrap_ci(pairs, stat)


def verdict(a: Arm, b: Arm) -> Verdict:
    """The call on the pair, voids first, exactly as the criterion ordered them."""
    reasons: list[str] = []
    for arm in (a, b):
        if arm.fallback_rate > integrity.VOID_BAR:
            reasons.append(f"{arm.name}: fallback {arm.fallback_rate:.2%} above "
                           f"{integrity.VOID_BAR:.0%}")
    ha, na = a.blind
    hb, nb = b.blind
    nc = newcombe(ha, na, hb, nb)
    boot = paired_bootstrap(a.games, b.games)
    diff = (None if a.blind_rate is None or b.blind_rate is None
            else b.blind_rate - a.blind_rate)
    if reasons:
        return Verdict("VOID", tuple(reasons), diff, nc, boot)
    for arm in (a, b):
        if arm.blind[1] < BLIND_FLOOR_VOTES:
            reasons.append(f"{arm.name}: blind stratum {arm.blind[1]} votes, under "
                           f"{BLIND_FLOOR_VOTES}")
    if reasons or nc is None:
        return Verdict("REFUSED", tuple(reasons) or ("an arm has no blind votes",),
                       diff, nc, boot)
    informs = nc[0] > 0.0 or nc[1] < 0.0
    return Verdict("INFORMS" if informs else "NOT SHOWN",
                   (f"Newcombe interval {'excludes' if informs else 'includes'} zero",),
                   diff, nc, boot)


def load(path: Path) -> Arm:
    with open(path, encoding="utf-8") as fh:
        summary = json.load(fh)
    with open(f"{path}.jsonl", encoding="utf-8") as fh:
        games = [json.loads(line) for line in fh if line.strip()]
    i = summary["score"]["integrity"]
    return Arm(name=summary["args"].get("theme") or path.stem, games=games,
               fallback_rate=i["fallback_rate"],
               recovered_rate=i.get("recovered_rate", 0.0))


def _ci(ci) -> str:
    return "refused" if ci is None else f"[{ci[0]:+.2%}, {ci[1]:+.2%}]"


def _excludes_zero(ci) -> bool:
    return ci is not None and (ci[0] > 0.0 or ci[1] < 0.0)


def report(records: Path) -> int:
    live = {t: load(records / f"cl-skin-{t}.json") for t in ARMS}
    ctrl = {t: load(records / f"cl-skin-{t}-random.json") for t in ARMS}
    a, b = live[ARMS[0]], live[ARMS[1]]

    print("== read the fallback rate FIRST, per arm")
    for arm in live.values():
        flag = (" RECOVERED FLAGGED"
                if arm.recovered_rate > integrity.RECOVERED_WARN_BAR else "")
        print(f"   {arm.name:12s} fallback {arm.fallback_rate:.2%}  recovered "
              f"{arm.recovered_rate:.2%}{flag}  games {len(arm.games)}, scored "
              f"{len(arm.scored)}")

    print("\n== gate #3 per arm - blind villager accuracy against the run's own "
          "random arm")
    for t in ARMS:
        arm, c = live[t], ctrl[t]
        hits, n = arm.blind
        bar, note = own_bar(c.blind_rate)
        wil = wilson(hits, n)
        boot = bootstrap_ci(arm.scored, lambda s: accuracy(s, BLIND))
        holds = wil is not None and wil[0] > bar
        point = f"{hits / n:.2%}" if n else "refused"
        print(f"   {t:12s} {hits}/{n} = {point}  Wilson {_ci(wil)}  "
              f"bootstrap-by-game {_ci(boot)}")
        print(f"                {note}; Wilson floor "
              f"{'clears' if holds else 'does NOT clear'} {bar:.2%} -> gate #3 "
              f"{'HOLDS' if holds else 'NOT SHOWN'}")
    ca, cb = ctrl[ARMS[0]].blind, ctrl[ARMS[1]].blind
    agree = "yes" if ca == cb else f"NO - {ca!r} vs {cb!r}"
    print(f"   controls agree on the census: {agree} (random play reads no names)")

    v = verdict(a, b)
    print(f"\n== the pair - {ARMS[1]} minus {ARMS[0]}, blind villager accuracy")
    print(f"   difference {v.diff:+.2%}" if v.diff is not None
          else "   difference refused")
    print(f"   Newcombe 95%          {_ci(v.newcombe)}   <- the interval the "
          "criterion names")
    print(f"   paired game bootstrap {_ci(v.bootstrap)}   beside it, never deciding")
    if v.newcombe and v.bootstrap and (_excludes_zero(v.newcombe)
                                       != _excludes_zero(v.bootstrap)):
        print("   the two intervals DISAGREE on zero - printed, not resolved; the "
              "criterion named Newcombe")
    for r in v.reasons:
        print(f"   {r}")
    print(f"\n   -> {v.call}")
    return 0 if v.call in ("INFORMS", "NOT SHOWN") else 3


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return report(Path(args[0]) if args else Path("eval/records"))


if __name__ == "__main__":
    sys.exit(main())
