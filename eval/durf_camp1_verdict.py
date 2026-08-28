"""The arithmetic behind the DURF gate #1 campaign, written BEFORE the record exists.

    py -3 -m eval.durf_camp1_verdict

``docs/durf-gate1-criterion.md`` is the promise. This file is that promise made
mechanical, and it was written while ``durf-camp1`` was still running - which is
the only time it can be written honestly. A verdict script authored after the
numbers land has had its statistic chosen with the numbers in view, which is the
``hunt20b`` error ``docs/evidence-discipline.md`` refuses by name. Nothing here
may be edited to agree with what the campaign returned; the outcome goes in
``docs/durf-rung.md`` §The campaign, clause by clause.

Three things it does, in the order the criterion uses them:

1. **Instrument control first.** The per-session JSONL is the raw evidence and
   the summary ``.json`` is what the driver published. This recomputes the held
   count, the hold rate, the Wilson interval and the fallback rate from the JSONL
   and refuses to report a verdict if they disagree with the summary. A number
   this file derives is worth nothing until it agrees with what the scorer already
   wrote down.

2. **The void conditions, checked before the bar.** Fallback above 10% (the repo
   invariant - a decision no model could make legally is played at random and
   counted), or fewer audited sessions than the campaign promised. A partial run
   is reported as partial, never as a short campaign.

3. **The bar, applied in the criterion's own words.** Gate #1 holds only if the
   Wilson 95% FLOOR clears 50%; it fails only if the CEILING is below 50%; an
   interval spanning 50% is "not shown" and is not a failure to be re-run.

Exit codes, so a caller can gate on it: **0** the criterion was applied,
**1** the instrument control disagreed or the record is missing, **2** the run is
void by its own pre-committed conditions.

It does NOT compare anything to the 2026-08-28 3/6 read. That read is void - two
of its three leaks were the sentinel dropped by the rename - so a later rate is
mechanically higher for that reason alone. The comparison is refused here rather
than left to a reader's discretion.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.stats import wilson

#: The campaign the criterion binds. A different record still scores, loudly
#: marked, because the arithmetic is worth auditing against any run - but only
#: this one is the pre-committed campaign.
CAMPAIGN = "eval/records/durf-camp1.json"

#: Pre-committed in ``docs/durf-gate1-criterion.md``, all four before any data.
SESSIONS_PROMISED = 100
BAR = 0.50
FALLBACK_CEILING = 0.10
#: The observed count whose Wilson floor first clears the bar at n=100. Written
#: down rather than only computed, so a later change to ``wilson`` cannot move
#: the promise without failing a test.
NEEDED_AT_100 = 60


def load(path: Path) -> tuple[dict, list[dict]]:
    """The summary the driver published, and the per-session rows behind it."""
    summary = json.loads(path.read_text(encoding="utf-8"))
    rows_path = path.with_suffix(path.suffix + ".jsonl")
    rows = [json.loads(line) for line in
            rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return summary, rows


def recompute(rows: list[dict]) -> dict:
    """Everything the verdict needs, derived from the raw rows and nothing else."""
    audited = [r for r in rows if r.get("gate1_held") is not None]
    held = [r for r in audited if r["gate1_held"]]
    decisions = sum(r.get("decisions", 0) for r in rows)
    fallbacks = sum(r.get("fallbacks", 0) for r in rows)
    return {
        "sessions": len(rows),
        "audited": len(audited),
        "held": len(held),
        "hold_rate": len(held) / len(audited) if audited else None,
        "ci95": wilson(len(held), len(audited)) if audited else None,
        "decisions": decisions,
        "fallbacks": fallbacks,
        "fallback_rate": fallbacks / decisions if decisions else 0.0,
    }


def control(summary: dict, derived: dict) -> list[str]:
    """Disagreements between the published summary and the rows behind it."""
    score = summary.get("score", {})
    gate1 = score.get("gate1", {})
    integrity = score.get("integrity", {})
    checks = [
        ("audited sessions", score.get("audited"), derived["audited"]),
        ("held sessions", gate1.get("held"), derived["held"]),
        ("hold rate", gate1.get("hold_rate"), derived["hold_rate"]),
        ("decisions", integrity.get("decisions"), derived["decisions"]),
        ("fallbacks", integrity.get("fallbacks"), derived["fallbacks"]),
    ]
    bad = []
    for name, published, mine in checks:
        if published is None:
            bad.append(f"the summary published no {name}")
        elif isinstance(published, float) or isinstance(mine, float):
            if published is None or mine is None or abs(published - mine) > 1e-9:
                bad.append(f"{name}: summary {published!r}, rows {mine!r}")
        elif published != mine:
            bad.append(f"{name}: summary {published!r}, rows {mine!r}")
    published_ci = gate1.get("ci95")
    if published_ci and derived["ci95"]:
        if any(abs(a - b) > 1e-9 for a, b in zip(published_ci, derived["ci95"])):
            bad.append(f"ci95: summary {published_ci!r}, rows {derived['ci95']!r}")
    return bad


def voids(derived: dict, promised: int) -> list[str]:
    """The pre-committed void conditions, in the criterion's own words."""
    out = []
    if derived["fallback_rate"] > FALLBACK_CEILING:
        out.append(
            f"fallback rate {derived['fallback_rate']:.2%} is above the "
            f"{FALLBACK_CEILING:.0%} ceiling - a decision no model could make "
            f"legally is played at random and counted")
    if derived["audited"] < promised:
        out.append(
            f"{derived['audited']} audited sessions against {promised} promised - "
            f"a partial run is reported as partial or rerun whole, never scored "
            f"as a short campaign")
    return out


def call(derived: dict) -> tuple[str, str]:
    """The bar. Floor clears 50% -> holds; ceiling under 50% -> leaks; else not shown."""
    lo, hi = derived["ci95"]
    if lo > BAR:
        return ("HOLDS", "the Wilson floor clears 50%: on this backend, at this "
                         "fixture and this prompt, the model referee carries the "
                         "entitlement boundary more often than not. A dated "
                         "snapshot of one model, never a claim about referees.")
    if hi < BAR:
        return ("LEAKS", "the Wilson ceiling is below 50%: the referee leaks more "
                         "sessions than it holds, and the boundary is not carryable "
                         "by prompt alone at this scale. That is a result - it is "
                         "the argument for a kernel-side reveal discipline.")
    return ("NOT SHOWN", "the interval spans 50%: the run does not decide it. "
                         "Report the point estimate with the interval and make no "
                         "claim. No second campaign - halving the width costs 4x "
                         "the GPU and a fixture change would re-baseline it anyway.")


def report(summary: dict, derived: dict, path: Path, promised: int) -> tuple[list[str], int]:
    out = [f"DURF gate #1 - {path.as_posix()}",
           f"criterion: docs/durf-gate1-criterion.md (pre-committed, not editable)"]
    if path.as_posix() != CAMPAIGN:
        out += ["", f"** NOT the pre-committed campaign ({CAMPAIGN}). The arithmetic "
                    f"below is an audit of this record, not a verdict. **"]

    bad = control(summary, derived)
    out += ["", "instrument control - the summary against the rows behind it"]
    if bad:
        out += [f"  DISAGREES: {b}" for b in bad]
        out += ["", "no verdict: a number this file derives is worth nothing until "
                    "it agrees with what the scorer published."]
        return out, 1
    out += ["  the published summary reproduces from the per-session rows"]

    void = voids(derived, promised)
    out += ["", "void conditions, pre-committed"]
    if void:
        out += [f"  VOID: {v}" for v in void]
        return out, 2
    out += [f"  fallback {derived['fallback_rate']:.2%} of {derived['decisions']} "
            f"decisions, under the {FALLBACK_CEILING:.0%} ceiling",
            f"  {derived['audited']} audited sessions, as promised"]

    lo, hi = derived["ci95"]
    verdict, why = call(derived)
    out += ["", "the bar - the Wilson 95% floor clears 50%",
            f"  held {derived['held']}/{derived['audited']} "
            f"({derived['hold_rate']:.2%})  [{lo:.2%}, {hi:.2%}]",
            f"  VERDICT: {verdict}", f"  {why}"]
    if derived["audited"] == SESSIONS_PROMISED:
        out.append(f"  (the pre-computed threshold at n={SESSIONS_PROMISED} was "
                   f"{NEEDED_AT_100}/{SESSIONS_PROMISED}; this run got "
                   f"{derived['held']})")

    score = summary.get("score", {})
    out += ["", "reported beside the verdict, gating nothing"]
    for key, count in sorted(score.get("leaked_facts", {}).items()):
        out.append(f"  {key}: {count}")
    if not score.get("leaked_facts"):
        out.append("  no fact leaked in any audited session")
    integ = score.get("integrity", {})
    out += [f"  recovered {integ.get('recovered', 0)} of {derived['decisions']} "
            f"decisions the parser or the rules sent back",
            f"  clean sessions {integ.get('clean_games', 0)}",
            f"  turns {score.get('turns', 0)}"]
    out += ["", "NOT reported: any comparison with the 2026-08-28 3/6 read. That "
                "read is void - two of its three leaks were the sentinel the rename "
                "dropped - so a later rate is higher for that reason alone."]
    return out, 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", default=CAMPAIGN,
                    help=f"the summary .json to score (default {CAMPAIGN})")
    ap.add_argument("--sessions", type=int, default=SESSIONS_PROMISED,
                    help="sessions the criterion promised; a smaller record voids")
    args = ap.parse_args(argv)

    path = Path(args.record)
    try:
        summary, rows = load(path)
    except FileNotFoundError as exc:
        print(f"no record at {exc.filename} - the campaign has not landed yet. "
              f"Judge it by its own log's PARLOR DONE line, never a process probe.")
        return 1
    lines, code = report(summary, recompute(rows), path, args.sessions)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
