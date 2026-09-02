"""The changeling negation pass, scored as its criterion promised.

``py -3 -m eval.phrasing_pair_verdict [records-dir]`` reads the two live records
of the phrasing pair - S22's ``cl-rounds2`` as the ``as-is`` control and
``cl-phrasing-positive`` as the arm - and prints the pre-committed read from
``docs/changeling-phrasing-criterion.md``, clause by clause.

**The primary statistic is the FALLBACK RATE, and it is read before anything
else.** Every other pair in this rung reads fallbacks as a health check and blind
accuracy as the figure. Here the hypothesis is about prohibitions producing the
behaviour they forbid, so the rate at which a seat fails to answer legally IS the
hypothesis: a prohibition that makes the refused move more available shows up as
refused attempts, and the rule-refusal share separates that from a network. Blind
villager accuracy is read second, on the same seeds, with the same Newcombe
interval, because a phrasing that costs deduction while cleaning up refusals is a
different finding from one that buys both.

The settings pin has one difference from ``eval.rounds_pair_verdict``'s, and it
is the reason this module exists rather than a fourth arm name in that one: the
control was recorded BEFORE ``--phrasing`` existed, so its ``args`` carries no
such key. Absent is read as ``as-is`` for the control and only for the control -
the arm must SAY ``positive``, or the read is voided.

A voided or refused pair is still AUDITED, exit 3 with every figure printed, per
``AGENTS.md``: this repo publishes numbers from records, and a scorer that
returns early leaves a published number with no instrument in the tree.
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
    newcombe,
    own_bar,
    paired_bootstrap,
    verdict,
)

#: (record stem, the phrasing its args must name). The control's stem is S22's,
#: unchanged - this pair adds ONE run to the card, not two.
ARMS = (("cl-rounds2", "as-is"), ("cl-phrasing-positive", "positive"))

#: Everything the two arms must agree on. `phrasing` is the one variable and is
#: checked separately, against the pair above.
COMMON = {"arm": "llm", "theme": "folk", "seats": 5, "seed": 5000, "rounds": 2,
          "no_thinking": True, "temperature": 0.8, "register": "character",
          "model": "qwen36-35b-a3b-iq3", "games": 200}


def settings_voids(stem: str, want_phrasing: str, args: dict) -> list[str]:
    """Every criterion setting this record's own ``args`` contradicts."""
    out = [f"{stem}: {k} is {args.get(k)!r}, criterion says {v!r}"
           for k, v in COMMON.items() if args.get(k) != v]
    # Absent means `as-is`, and only for the arm the criterion names as-is: the
    # control predates the flag. A positive arm whose record forgot to record the
    # flag is indistinguishable from a control, so it is voided rather than
    # assumed.
    got = args.get("phrasing", "as-is" if want_phrasing == "as-is" else None)
    if got != want_phrasing:
        out.append(f"{stem}: phrasing is {got!r}, criterion says "
                   f"{want_phrasing!r}")
    return out


def fallback_counts(arm: Arm) -> tuple[int, int]:
    """(fallback decisions, decisions) over every game in the record.

    Counted off the per-game records rather than taken from the summary's rate,
    because the pair's figure is a difference of two proportions and Newcombe
    needs the denominators. Over ALL completed games, not the scored subset: a
    decision the model could not make legally happened whether or not the game it
    sat in was winnable.
    """
    fell = sum(int(g.get("fallbacks", 0)) for g in arm.games)
    total = sum(int(g.get("decisions", 0)) for g in arm.games)
    return fell, total


def rule_refusal_counts(arm: Arm) -> tuple[int, int]:
    """(attempts the parser or the rules sent back, attempts made).

    The finer read the hypothesis actually names. A fallback is the end of a
    decision; a rule refusal is each individual attempt the referee or the parser
    would not take, and a prohibition that makes the forbidden move more
    available should move this one first and by more.
    """
    refused = sum(int(g.get("rule_refused_attempts", 0)) for g in arm.games)
    decisions = sum(int(g.get("decisions", 0)) for g in arm.games)
    attempts = decisions + sum(int(g.get("refused_attempts", 0))
                               for g in arm.games)
    return refused, attempts


def _load(records: Path, stem: str) -> tuple[Arm, dict]:
    path = records / f"{stem}.json"
    with open(path, encoding="utf-8") as fh:
        args = json.load(fh)["args"]
    arm = load(path)
    return Arm(name=stem, games=arm.games, fallback_rate=arm.fallback_rate,
               recovered_rate=arm.recovered_rate), args


def _diff_line(label: str, a: tuple[int, int], b: tuple[int, int]) -> None:
    (ha, na), (hb, nb) = a, b
    pa = f"{ha / na:.2%}" if na else "n/a"
    pb = f"{hb / nb:.2%}" if nb else "n/a"
    nc = newcombe(ha, na, hb, nb)
    diff = (hb / nb - ha / na) if na and nb else None
    print(f"   {label:22s} as-is {ha}/{na} = {pa}   positive {hb}/{nb} = {pb}")
    print(f"                          difference "
          + ("refused" if diff is None else f"{diff:+.2%}")
          + f"   Newcombe 95% {_ci(nc)}"
          + ("   EXCLUDES ZERO" if _excludes_zero(nc) else ""))


def report(records: Path) -> int:
    live: dict[str, Arm] = {}
    args: dict[str, dict] = {}
    for stem, _ in ARMS:
        live[stem], args[stem] = _load(records, stem)
    control = _load(records, "cl-rounds2-random")[0]

    print("== settings pin - each record's own args against the criterion")
    pinned = True
    for stem, want in ARMS:
        vs = settings_voids(stem, want, args[stem])
        pinned &= not vs
        print(f"   {stem:24s} {'matches' if not vs else 'VOIDED'}")
        for v in vs:
            print(f"      {v}")

    a, b = live[ARMS[0][0]], live[ARMS[1][0]]

    print("\n== PRIMARY - the refusal read, the statistic this pair names first")
    _diff_line("fallback rate", fallback_counts(a), fallback_counts(b))
    _diff_line("rule-refused attempts", rule_refusal_counts(a),
               rule_refusal_counts(b))
    for arm in (a, b):
        flag = (" RECOVERED FLAGGED"
                if arm.recovered_rate > integrity.RECOVERED_WARN_BAR else "")
        print(f"   {arm.name:24s} recovered {arm.recovered_rate:.2%}{flag}  "
              f"games {len(arm.games)}, scored {len(arm.scored)}")

    print("\n== SECONDARY - blind villager accuracy, against the shared random "
          "control")
    bar, note = own_bar(control.blind_rate)
    for arm in (a, b):
        hits, n = arm.blind
        wil = wilson(hits, n)
        boot = bootstrap_ci(arm.scored, lambda s: accuracy(s, BLIND))
        holds = wil is not None and wil[0] > bar
        point = f"{hits / n:.2%}" if n else "refused"
        print(f"   {arm.name:24s} {hits}/{n} = {point}  Wilson {_ci(wil)}  "
              f"bootstrap-by-game {_ci(boot)}")
        print(f"                            Wilson floor "
              f"{'clears' if holds else 'does NOT clear'} {bar:.2%} -> gate #3 "
              f"{'HOLDS' if holds else 'NOT SHOWN'}")
    # ONE control, shared. A random seat reads no prompt, so the two phrasings
    # deal and vote identically under `--arm random` - a property `test_phrasing`
    # asserts, and the reason this pair costs one run instead of two.
    print(f"   {note}")

    v = verdict(a, b)
    print("\n== the pair - positive minus as-is, blind villager accuracy")
    print(f"   difference {v.diff:+.2%}" if v.diff is not None
          else "   difference refused")
    print(f"   Newcombe 95%          {_ci(v.newcombe)}   <- the interval the "
          "criterion names")
    print(f"   paired game bootstrap {_ci(paired_bootstrap(a.games, b.games))}"
          "   beside it, never deciding")
    for r in v.reasons:
        print(f"   {r}")
    call = v.call if pinned else f"VOID (settings) - the arithmetic read {v.call}"
    print(f"\n   -> {call}")
    return 0 if pinned and v.call in ("INFORMS", "NOT SHOWN") else 3


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return report(Path(argv[0]) if argv else Path("eval/records"))


if __name__ == "__main__":
    sys.exit(main())
