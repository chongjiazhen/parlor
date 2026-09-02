"""Changeling gate #2 as a PAIR - the pack's own contribution, scored as promised.

``py -3 -m eval.gate2_pair_verdict [records-dir]`` reads two live records played
on the same seeds against the same live village - ``--arm llm`` (the pack live)
and ``--arm llm-village`` (the pack at random) - and prints the read
``docs/changeling-gate2-pair-criterion.md`` pre-committed. The unit is a GAME
and the statistic is the pack win rate on the scored (winnable) denominator; the
pair's figure is the difference, live pack minus random pack, under a Newcombe
interval with a paired game bootstrap beside it. Both arms carry the same live
village, so what moves between them is what the pack's play is worth against
a table that is actually deducing - which is the reading gate #2 has needed
since S2 and had no control for.

The all-random control (``cl-rounds2-random``, first 200 games) is printed as a
REFERENCE beside it - the comparison S2's writeup said a paired random arm would
make - and never decides anything.

Voids first, a settings pin before any figure, and a pairing check: same seed
means same deal, and the night is chosen by village seats on both arms, so dawn
truth should agree game by game. It is COUNTED, not assumed.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from core import integrity
from core.stats import bootstrap_ci, wilson
from eval.s5_verdict import winnable
from eval.skin_pair_verdict import _ci, _excludes_zero, newcombe

ARMS = ("llm", "village")
_COMMON = {"theme": "folk", "rounds": 2, "seats": 5, "seed": 5000,
           "no_thinking": True, "temperature": 0.8, "model": "qwen36-35b-a3b-iq3"}
EXPECTED = {
    "llm": {**_COMMON, "arm": "llm"},
    "village": {**_COMMON, "arm": "llm-village"},
}
#: Under this many games on either arm the pair is REFUSED, not failed - a
#: 120-game interval on a win rate spans a fifth of the axis.
GAMES_FLOOR = 190
RECORD = {"llm": "cl-rounds2", "village": "cl-gate2-village", "random": "cl-rounds2-random"}


@dataclass(frozen=True)
class Arm:
    name: str
    games: list[dict]
    fallback_rate: float
    recovered_rate: float = 0.0
    args: dict | None = None

    @property
    def scored(self) -> list[dict]:
        return winnable(self.games)


@dataclass(frozen=True)
class Verdict:
    call: str
    reasons: tuple[str, ...]
    diff: float | None
    newcombe: tuple[float, float] | None
    bootstrap: tuple[float, float] | None


def pack_wins(games: list[dict]) -> tuple[int, int]:
    """(pack wins, scored games) - the gate #2 numerator and denominator."""
    scored = winnable(games)
    return sum(1 for g in scored if g["winner"] == "pack"), len(scored)


def dawn_agreement(games_a: list[dict], games_b: list[dict]) -> tuple[int, int]:
    """How many same-seed pairs ended the night with the same dawn truth."""
    by_b = {g["game"]: g for g in games_b}
    pairs = [(g, by_b[g["game"]]) for g in games_a if g["game"] in by_b]
    return sum(1 for a, b in pairs if a["truth"] == b["truth"]), len(pairs)


def _paired_bootstrap(games_a, games_b):
    by_b = {g["game"]: g for g in winnable(games_b)}
    pairs = [(g, by_b[g["game"]]) for g in winnable(games_a) if g["game"] in by_b]

    def stat(sample):
        if not sample:
            return None
        a = sum(1 for p in sample if p[0]["winner"] == "pack") / len(sample)
        b = sum(1 for p in sample if p[1]["winner"] == "pack") / len(sample)
        return a - b

    return bootstrap_ci(pairs, stat)


def settings_voids(arm_name: str, args: dict) -> list[str]:
    want = EXPECTED[arm_name]
    return [f"{arm_name}: {k} is {args.get(k)!r}, criterion says {v!r}"
            for k, v in want.items() if args.get(k) != v]


def verdict(live: Arm, control: Arm) -> Verdict:
    """Live pack minus random pack, voids first, in the criterion's order."""
    reasons = [f"{a.name}: fallback {a.fallback_rate:.2%} above {integrity.VOID_BAR:.0%}"
               for a in (live, control) if a.fallback_rate > integrity.VOID_BAR]
    hl, nl = pack_wins(live.games)
    hc, nc_ = pack_wins(control.games)
    nc = newcombe(hc, nc_, hl, nl)              # signed live minus control
    boot = _paired_bootstrap(live.games, control.games)
    diff = None if not nl or not nc_ else hl / nl - hc / nc_
    if reasons:
        return Verdict("VOID", tuple(reasons), diff, nc, boot)
    for a in (live, control):
        if len(a.scored) < GAMES_FLOOR:
            reasons.append(f"{a.name}: {len(a.scored)} scored games, under {GAMES_FLOOR}")
    if reasons or nc is None:
        return Verdict("REFUSED", tuple(reasons) or ("an arm has no scored games",),
                       diff, nc, boot)
    informs = _excludes_zero(nc)
    return Verdict("INFORMS" if informs else "NOT SHOWN",
                   (f"Newcombe interval {'excludes' if informs else 'includes'} zero",),
                   diff, nc, boot)


def load(records: Path, stem: str, name: str, limit: int | None = None) -> Arm:
    path = records / f"{stem}.json"
    with open(path, encoding="utf-8") as fh:
        summary = json.load(fh)
    with open(f"{path}.jsonl", encoding="utf-8") as fh:
        games = [json.loads(line) for line in fh if line.strip()]
    if limit is not None:
        games = [g for g in games if g["game"] < limit]
    i = summary["score"]["integrity"]
    return Arm(name=name, games=games, fallback_rate=i["fallback_rate"],
               recovered_rate=i.get("recovered_rate", 0.0), args=summary["args"])


def report(records: Path) -> int:
    live = load(records, RECORD["llm"], "llm")
    ctrl = load(records, RECORD["village"], "village")
    rnd = load(records, RECORD["random"], "random", limit=200)

    print("== settings pin - each record's own args against the criterion")
    pinned = True
    for name, a in (("llm", live), ("village", ctrl)):
        vs = settings_voids(name, a.args or {})
        pinned &= not vs
        print(f"   {name:8s} {'matches' if not vs else 'VOIDED'}")
        for v in vs:
            print(f"      {v}")

    print("\n== read the fallback rate FIRST, per arm")
    for a in (live, ctrl):
        flag = (" RECOVERED FLAGGED"
                if a.recovered_rate > integrity.RECOVERED_WARN_BAR else "")
        print(f"   {a.name:8s} fallback {a.fallback_rate:.2%}  recovered "
              f"{a.recovered_rate:.2%}{flag}  games {len(a.games)}, scored "
              f"{len(a.scored)}")

    print("\n== pairing - dawn truth agreement, same seed, village-chosen night")
    agree, n = dawn_agreement(live.games, ctrl.games)
    print(f"   {agree}/{n} pairs share their dawn truth"
          + ("" if n and agree == n else
             "  <- the arms did not play the same night everywhere; the pair is "
             "weaker than same-seeds promises and this line says by how much"))

    print("\n== pack win rate per arm, scored denominator")
    for a in (live, ctrl, rnd):
        h, k = pack_wins(a.games)
        rate = f"{h / k:.2%}" if k else "refused"
        print(f"   {a.name:8s} {h}/{k} = {rate}  Wilson {_ci(wilson(h, k))}"
              + ("   (reference only, never deciding)" if a is rnd else ""))

    v = verdict(live, ctrl)
    print("\n== the pair - live pack minus random pack, same live village")
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
    call = v.call if pinned else f"VOID (settings) - the arithmetic read {v.call}"
    print(f"\n   -> {call}")
    return 0 if pinned and v.call in ("INFORMS", "NOT SHOWN") else 3


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return report(Path(args[0]) if args else Path("eval/records"))


if __name__ == "__main__":
    sys.exit(main())
