"""The changeling briefing pair, scored as its criterion promised.

``py -3 -m eval.briefing_pair_verdict [records-dir]`` reads S22's two-round
``folk`` record (``cl-rounds2.json``, the control arm - cited, not chosen) and the
one new arm ``eval/runs/changeling-briefing-arm.cmd`` writes (``cl-briefing.json``,
identical settings plus ``--briefing``), and prints the read
``docs/changeling-briefing-criterion.md`` pre-committed. The arithmetic is
``eval.skin_pair_verdict``'s, unchanged: S2's blind villager accuracy per arm, the
difference (briefing minus without) under a Newcombe interval, a paired game
bootstrap beside it, voids first. The random control is the same record for both
arms: random play reads no prompt, so there is nothing for a second control to
differ in.

Same shape as ``eval.notebook_pair_verdict`` - one flag arm against S22's record
- including its wrinkle: the control was written before ``--briefing`` existed,
so its ``args`` carries no ``briefing`` key. An absent key reads as ``False`` for
the control; the arm must say ``True`` or it is voided.
"""

from __future__ import annotations

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

ARMS = ("rounds2", "briefing")
CONTROL = "rounds2-random"
_COMMON = {"arm": "llm", "theme": "folk", "seats": 5, "seed": 5000, "rounds": 2,
           "no_thinking": True, "temperature": 0.8, "model": "qwen36-35b-a3b-iq3"}
#: The two rows differ in `briefing` and in nothing else - a test holds that.
EXPECTED = {
    "rounds2": {**_COMMON, "briefing": False},
    "briefing": {**_COMMON, "briefing": True},
}
#: Keys whose ABSENCE from a record's args means this value - flags added to the
#: driver after the record was written. Only `briefing` today.
ABSENT_MEANS = {"briefing": False}


def settings_voids(arm_name: str, args: dict) -> list[str]:
    """Every criterion setting the record's own `args` contradicts."""
    want = EXPECTED[arm_name]
    out = []
    for k, v in want.items():
        got = args.get(k, ABSENT_MEANS.get(k))
        if got != v:
            out.append(f"{arm_name}: {k} is {got!r}, criterion says {v!r}")
    return out


def _load(records: Path, stem: str) -> tuple[Arm, dict]:
    import json
    path = records / f"{stem}.json"
    with open(path, encoding="utf-8") as fh:
        args = json.load(fh)["args"]
    arm = load(path)
    return Arm(name=stem, games=arm.games, fallback_rate=arm.fallback_rate,
               recovered_rate=arm.recovered_rate), args


def village_wins(arm: Arm) -> tuple[int, int]:
    """The free read the criterion names beside the primary: how often the
    village won on the scored denominator."""
    scored = arm.scored
    return sum(1 for g in scored if g.get("winner") == "village"), len(scored)


def report(records: Path) -> int:
    live, args = {}, {}
    for n in ARMS:
        live[n], args[n] = _load(records, f"cl-{n}")
    ctrl = _load(records, f"cl-{CONTROL}")[0]

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

    print("\n== gate #3 per arm - blind villager accuracy against the shared "
          "random control")
    for n in ARMS:
        arm = live[n]
        hits, k = arm.blind
        bar, note = own_bar(ctrl.blind_rate)
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

    print("\n== free read - village win rate per arm, decides nothing")
    for n in ARMS:
        w, k = village_wins(live[n])
        print(f"   {n:8s} {w}/{k} = {w / k:.2%}  Wilson {_ci(wilson(w, k))}"
              if k else f"   {n:8s} refused")

    call = v.call if pinned else f"VOID (settings) - the arithmetic read {v.call}"
    print(f"\n   -> {call}")
    return 0 if pinned and v.call in ("INFORMS", "NOT SHOWN") else 3


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return report(Path(args[0]) if args else Path("eval/records"))


if __name__ == "__main__":
    sys.exit(main())
