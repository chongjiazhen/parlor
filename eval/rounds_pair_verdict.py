"""The changeling discussion-length pair, scored as its criterion promised.

``py -3 -m eval.rounds_pair_verdict [records-dir]`` reads the records
``eval/runs/changeling-rounds-pair.cmd`` writes - two random controls and two
live arms on the ``folk`` skin, ``--rounds 2`` and ``--rounds 3`` - and prints the
read ``docs/changeling-rounds-pair-criterion.md`` pre-committed. The arithmetic
is ``eval.skin_pair_verdict``'s, unchanged: S2's blind villager accuracy per arm,
the difference (three rounds minus two) under a Newcombe interval, a paired game
bootstrap beside it, voids first.

What this module adds is the SETTINGS PIN. Every arm's record carries the
driver's ``args``; the criterion says what each arm's must be; a record that
disagrees is voided before any figure is trusted, because a launcher default and
a criterion have disagreed once already in this repo (belfry live1) and the run
could be read but never called.
"""

from __future__ import annotations

import sys
from pathlib import Path

from core import integrity
from core.stats import bootstrap_ci, wilson
from eval.gate3_bar import own_bar
from eval.skin_pair_verdict import (
    BLIND,
    Arm,
    _ci,
    _excludes_zero,
    accuracy,
    load,
    verdict,
)

ARMS = ("rounds2", "rounds3")
#: The criterion's settings, per arm. The two rows differ in `rounds` and in
#: nothing else - a test holds that, so the pair cannot quietly grow a second
#: variable here.
_COMMON = {"arm": "llm", "theme": "folk", "seats": 5, "seed": 5000,
           "no_thinking": True, "temperature": 0.8, "model": "qwen36-35b-a3b-iq3"}
EXPECTED = {
    "rounds2": {**_COMMON, "rounds": 2},
    "rounds3": {**_COMMON, "rounds": 3},
}


def settings_voids(arm_name: str, args: dict) -> list[str]:
    """Every criterion setting the record's own `args` contradicts."""
    want = EXPECTED[arm_name]
    return [f"{arm_name}: {k} is {args.get(k)!r}, criterion says {v!r}"
            for k, v in want.items() if args.get(k) != v]


def _load(records: Path, stem: str) -> tuple[Arm, dict]:
    import json
    path = records / f"{stem}.json"
    with open(path, encoding="utf-8") as fh:
        args = json.load(fh)["args"]
    arm = load(path)
    return Arm(name=stem, games=arm.games, fallback_rate=arm.fallback_rate,
               recovered_rate=arm.recovered_rate), args


def report(records: Path) -> int:
    live, args = {}, {}
    for n in ARMS:
        live[n], args[n] = _load(records, f"cl-{n}")
    ctrl = {n: _load(records, f"cl-{n}-random")[0] for n in ARMS}

    print("== settings pin - the record's own args against the criterion")
    pinned = True
    for n in ARMS:
        vs = settings_voids(n, args[n])
        pinned &= not vs
        print(f"   {n:8s} {'matches' if not vs else 'VOIDED'}")
        for v in vs:
            print(f"      {v}")

    print("\n== read the fallback rate FIRST, per arm")
    for arm in live.values():
        flag = (" RECOVERED FLAGGED"
                if arm.recovered_rate > integrity.RECOVERED_WARN_BAR else "")
        print(f"   {arm.name:8s} fallback {arm.fallback_rate:.2%}  recovered "
              f"{arm.recovered_rate:.2%}{flag}  games {len(arm.games)}, scored "
              f"{len(arm.scored)}")

    print("\n== gate #3 per arm - blind villager accuracy against the run's own "
          "random arm")
    for n in ARMS:
        arm, c = live[n], ctrl[n]
        hits, k = arm.blind
        bar, note = own_bar(c.blind_rate)
        wil = wilson(hits, k)
        boot = bootstrap_ci(arm.scored, lambda s: accuracy(s, BLIND))
        holds = wil is not None and wil[0] > bar
        point = f"{hits / k:.2%}" if k else "refused"
        print(f"   {n:8s} {hits}/{k} = {point}  Wilson {_ci(wil)}  "
              f"bootstrap-by-game {_ci(boot)}")
        print(f"            {note}; Wilson floor "
              f"{'clears' if holds else 'does NOT clear'} {bar:.2%} -> gate #3 "
              f"{'HOLDS' if holds else 'NOT SHOWN'}")

    a, b = live[ARMS[0]], live[ARMS[1]]
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
    call = v.call if pinned else f"VOID (settings) - the arithmetic read {v.call}"
    print(f"\n   -> {call}")
    return 0 if pinned and v.call in ("INFORMS", "NOT SHOWN") else 3


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return report(Path(args[0]) if args else Path("eval/records"))


if __name__ == "__main__":
    sys.exit(main())
