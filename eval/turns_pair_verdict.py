"""The changeling turn-taking pair, scored as its criterion promised.

``py -3 -m eval.turns_pair_verdict [records-dir]`` reads S22's two-round ``folk``
record as arm 1 and ``eval/runs/changeling-turns-arm.cmd``'s record as arm 2, and
prints the read ``docs/changeling-turns-criterion.md`` pre-committed. The
arithmetic is ``eval.skin_pair_verdict``'s, unchanged: S2's blind villager
accuracy per arm, the difference (random-active minus fixed) under a Newcombe
interval, a paired game bootstrap beside it, voids first.

What this module adds is the SETTINGS PIN, and one rule the other pins do not
need. **A record whose ``args`` carries no ``turns`` key is read as ``fixed``.**
The flag postdates the driver, so absence can only mean the shipped order - which
is what lets S22's record serve as arm 1 whether it was played before or after
the flag landed. The same rule voids arm 2 when its key is missing, because
absence there means the run never went through the flag at all.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from core import integrity
from core.stats import bootstrap_ci, wilson
from eval.skin_pair_verdict import (
    BLIND,
    Arm,
    _ci,
    _excludes_zero,
    accuracy,
    load,
    own_bar,
    verdict,
)
from games.changeling.referee import TURNS_FIXED, TURNS_RANDOM_ACTIVE

#: Arm name -> the record stem it is scored off. Arm 1 is S22's, reused rather
#: than replayed: the criterion spends no new GPU on a control that already
#: exists on the same seeds.
STEMS = {"fixed": "cl-rounds2", "random-active": "cl-turns-random"}
ARMS = tuple(STEMS)

#: The criterion's settings, per arm. The two rows differ in `turns` and in
#: nothing else - a test holds that, so the pair cannot quietly grow a second
#: variable here.
_COMMON = {"arm": "llm", "theme": "folk", "seats": 5, "seed": 5000, "rounds": 2,
           "no_thinking": True, "temperature": 0.8, "model": "qwen36-35b-a3b-iq3"}
EXPECTED = {
    "fixed": {**_COMMON, "turns": TURNS_FIXED},
    "random-active": {**_COMMON, "turns": TURNS_RANDOM_ACTIVE},
}


def read_setting(args: dict, key: str):
    """One setting off a record's own ``args``, with the one back-compatible
    default this pair needs. Absence of ``turns`` means the record predates the
    flag, and the driver had exactly one order then."""
    if key == "turns":
        return args.get(key, TURNS_FIXED)
    return args.get(key)


def settings_voids(arm_name: str, args: dict) -> list[str]:
    """Every criterion setting the record's own `args` contradicts."""
    want = EXPECTED[arm_name]
    return [f"{arm_name}: {k} is {read_setting(args, k)!r}, criterion says {v!r}"
            for k, v in want.items() if read_setting(args, k) != v]


def _load(records: Path, stem: str) -> tuple[Arm, dict]:
    path = records / f"{stem}.json"
    with open(path, encoding="utf-8") as fh:
        args = json.load(fh)["args"]
    arm = load(path)
    return Arm(name=stem, games=arm.games, fallback_rate=arm.fallback_rate,
               recovered_rate=arm.recovered_rate), args


def report(records: Path) -> int:
    live, args = {}, {}
    for n in ARMS:
        live[n], args[n] = _load(records, STEMS[n])
    ctrl = {n: _load(records, f"{STEMS[n]}-random")[0] for n in ARMS}

    print("== settings pin - the record's own args against the criterion")
    pinned = True
    for n in ARMS:
        vs = settings_voids(n, args[n])
        pinned &= not vs
        print(f"   {n:14s} {'matches' if not vs else 'VOIDED'}")
        for v in vs:
            print(f"      {v}")

    print("\n== read the fallback rate FIRST, per arm")
    for arm in live.values():
        flag = (" RECOVERED FLAGGED"
                if arm.recovered_rate > integrity.RECOVERED_WARN_BAR else "")
        print(f"   {arm.name:16s} fallback {arm.fallback_rate:.2%}  recovered "
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
        print(f"   {n:14s} {hits}/{k} = {point}  Wilson {_ci(wil)}  "
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
