"""The arithmetic behind the S6 verdict (2026-08-27): cabal's gate #3b, called.

Every number the verdict quotes is recomputed here from records already on disk.
No new games. Run it to audit the call:

    py -3 -m eval.s6_verdict

Four things it establishes, in the order the verdict uses them:

1. **Instrument control first.** It reproduces each arm's recorded hunter count,
   derived baseline, Wilson interval, blind taint table and fallback rate from the
   per-game records, and checks them against the summary the scorer published at
   run time. A number this file derives is worth nothing until the pipeline that
   derives it agrees with the scorer on what the scorer already wrote down, so
   that check runs first and exits non-zero on any disagreement.

2. **The pre-committed criterion, applied in its own words.** 40 games at two seed
   bases, frozen code, and 3b holds only if the hunter's Wilson 95% floor clears
   the S3-derived bar - ``1/len(legal_targets)`` averaged over the hunts actually
   faced, never a hardcoded ``1/3``. The bar is read off the records, so a variant
   that changes what the night says would move it here too.

3. **The denominator the campaign actually got.** After arm 1, ``queue.md``
   projected ~8 hunts for the whole campaign and warned the verdict would read
   "not shown" for reasons of denominator. It is recomputed here because that
   projection was wrong, and a verdict that inherits a superseded projection
   misreports why a gate failed.

4. **The three draw-dependent items**, each against the trigger written down
   before this draw existed: step-not-slope, the ``five_rejects`` shift, and
   run-length degradation. All three asked for a different seed base and this is
   it, so they are scored here and nowhere else.

It does NOT re-specify a gate. The criterion is applied as pre-committed and the
solver/heuristic denominators in ``docs/reference-policies.md`` sit beside it,
never in place of it - the discipline constraint that file states.
"""
from __future__ import annotations

import json
import sys

from core.stats import wilson
from eval.gate3_arithmetic import hunts_for_floor

#: The campaign, in the order the criterion names them.
S6_ARMS = ("eval/records/hunt6a.json", "eval/records/hunt6b.json")

#: The post-fix runs that carry a blind taint table, oldest first. The two S6 arms
#: are appended so the step-not-slope item reads four tables, none of them quoted
#: from a note.
TAINT_HISTORY = ("eval/records/hunt20b.json", "eval/records/hunt20c.json") + S6_ARMS

#: Where a long run was bucketed when the degradation was first seen on hunt20c.
SPLIT_AT = 7


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def blind_votes(game: dict) -> list[dict]:
    """Votes from good seats the night told nothing - the gate's own stratum."""
    return [v for v in game["votes"]
            if not v["seat_is_evil"] and v["knowledge_class"] == "none"]


def by_taint(record: dict) -> dict[int, tuple[int, int]]:
    """Blind approvals over blind votes, keyed on the team's actual evil count."""
    table: dict[int, list[int]] = {}
    for game in record["games"]:
        for vote in blind_votes(game):
            cell = table.setdefault(vote["team_evil_count"], [0, 0])
            cell[0] += bool(vote["approved"])
            cell[1] += 1
    return {k: (v[0], v[1]) for k, v in sorted(table.items())}


def hunts(record: dict) -> list[dict]:
    return [g["hunt"] for g in record["games"] if g.get("hunt")]


def derived_bar(hunt_list: list[dict]) -> float | None:
    """``1/len(legal_targets)`` averaged over the hunts that recorded the field.

    Averaged rather than assumed constant: nothing stops a setup from varying the
    legal set game to game, and the criterion's bar is the set each hunt faced.
    """
    legal = [h["legal_targets"] for h in hunt_list if h.get("legal_targets")]
    return sum(1 / k for k in legal) / len(legal) if legal else None


def fallbacks(games: list[dict]) -> tuple[int, int]:
    return (sum(g["fallbacks"] for g in games), sum(g["decisions"] for g in games))


def _pct(hits: int, total: int) -> str:
    return f"{hits}/{total} = {hits / total:.2%}" if total else f"{hits}/0 = -"


def _ci(interval: tuple[float, float] | None) -> str:
    return "-" if interval is None else f"[{interval[0]:.2%}, {interval[1]:.2%}]"


def control(paths: tuple[str, ...]) -> bool:
    """Reproduce each arm's published summary from its own per-game records."""
    print("== instrument control - derived from games[] vs the scorer's summary")
    agreed = True
    for path in paths:
        record = load(path)
        summary = record["summary"]["gate3_deduction"]
        hunt_list = hunts(record)
        hits = sum(1 for h in hunt_list if h["hit"])
        checks = [
            ("hunts", len(hunt_list), summary["hunts"]),
            ("hunter hits", hits, summary["hunter_hits"]),
            ("hunter baseline", derived_bar(hunt_list), summary["hunter_baseline"]),
            ("hunter CI", wilson(hits, len(hunt_list)), tuple(summary["hunter_ci95"])),
            ("blind taint table", by_taint(record),
             {int(k): tuple(v) for k, v in summary["strata"]["none"]["by_taint"].items()}),
            ("fallbacks", fallbacks(record["games"]),
             (record["summary"]["integrity"]["fallbacks"],
              record["summary"]["integrity"]["decisions"])),
        ]
        for label, derived, published in checks:
            if isinstance(derived, tuple) and derived and isinstance(derived[0], float):
                ok = all(abs(a - b) < 1e-9 for a, b in zip(derived, published))
            elif isinstance(derived, float):
                ok = abs(derived - published) < 1e-9
            else:
                ok = derived == published
            agreed &= ok
            print(f"   {path.split('/')[-1]:14s} {label:18s} "
                  f"{'agrees' if ok else 'DISAGREES'}")
    print("   -> the pipeline below reads the same records the scorer did"
          if agreed else "   -> STOP. Derived figures disagree with the scorer.")
    return agreed


def criterion(paths: tuple[str, ...]) -> None:
    """Gate #3b, against the bar pre-committed before either arm ran."""
    print("\n== gate #3b - the pre-committed criterion, applied")
    pooled_hunts: list[dict] = []
    games = 0
    for path in paths:
        record = load(path)
        arm = hunts(record)
        hits = sum(1 for h in arm if h["hit"])
        games += len(record["games"])
        print(f"   seed {record['args']['seed']:<5} {_pct(hits, len(arm))}  "
              f"Wilson {_ci(wilson(hits, len(arm)))}")
        pooled_hunts += arm

    hits = sum(1 for h in pooled_hunts if h["hit"])
    interval = wilson(hits, len(pooled_hunts))
    bar = derived_bar(pooled_hunts)
    print(f"   POOLED ({games} games) {_pct(hits, len(pooled_hunts))}  "
          f"Wilson {_ci(interval)}")
    print(f"   derived bar 1/len(legal_targets) = {bar:.2%} "
          f"over {len(pooled_hunts)} hunts")
    holds = interval is not None and interval[0] > bar
    print(f"   floor {interval[0]:.2%} vs bar {bar:.2%} -> gate #3b "
          f"{'HOLDS' if holds else 'NOT SHOWN'}")
    print("   The criterion's own answer to a marginal landing: not shown, no "
          "third campaign, cabal stops." if not holds else
          "   Reported as pre-committed.")

    print("\n   power, as computed BEFORE the run, against what landed:")
    for rate in (0.55, 0.50, 0.45):
        needed, _ = hunts_for_floor(rate, bar)
        print(f"      at a true {rate:.0%}: {needed:3d} hunts to clear the bar "
              f"-> {'reached' if needed <= len(pooled_hunts) else 'NOT reached'} "
              f"at {len(pooled_hunts)}")


def denominator(paths: tuple[str, ...]) -> None:
    """Why the campaign's hunt count is the story queue.md got wrong after arm 1."""
    print("\n== the denominator - hunts per game, which arm 1 alone mis-projected")
    total_hunts = total_games = 0
    for path in paths:
        record = load(path)
        arm, games = hunts(record), record["games"]
        evil = sum(1 for g in games if g["winner"] == "evil")
        print(f"   seed {record['args']['seed']:<5} {len(arm):2d} hunts in "
              f"{len(games)} games ({len(arm) / len(games):.2f}/game), "
              f"evil won {_pct(evil, len(games))}")
        total_hunts += len(arm)
        total_games += len(games)
    print(f"   campaign {total_hunts} hunts in {total_games} games = "
          f"{total_hunts / total_games:.2f}/game, against the 0.50/game the "
          f"criterion assumed")
    print("   A hunt needs good to complete its missions, so the count is bounded "
          "by good's mission record - which is why one arm cannot project it.")


def draw_items(paths: tuple[str, ...]) -> None:
    """The three questions that asked for a second seed base. This is it."""
    print("\n== item 1: step, not slope? Trigger: a third flat or RISING 1->2 leg")
    legs = []
    for path in TAINT_HISTORY:
        table = by_taint(load(path))
        cells = " ".join(f"{k}:{_pct(*table[k])}" for k in sorted(table))
        rates = {k: table[k][0] / table[k][1] for k in table}
        leg = rates.get(2, 0) - rates.get(1, 0) if {1, 2} <= set(rates) else None
        legs.append((path.split("/")[-1], leg))
        print(f"   {path.split('/')[-1]:14s} {cells}"
              + (f"   1->2 leg {leg:+.1%}" if leg is not None else ""))
    latest = legs[-1][1]
    print(f"   the S6 arm's 1->2 leg is {latest:+.1%} -> the trigger "
          f"{'FIRED' if latest is not None and latest >= 0 else 'did NOT fire'}; "
          "the scorer note stands as written."
          if latest is not None and latest < 0 else "   trigger FIRED.")

    print("\n== item 2: is the five_rejects shift real? Trigger: a second draw")
    for path in TAINT_HISTORY:
        record = load(path)
        paths_seen = record["summary"]["gate2_deception"]["by_path"]
        games = len(record["games"])
        print(f"   {path.split('/')[-1]:14s} five_rejects "
              f"{paths_seen.get('five_rejects', 0):2d}/{games}   "
              f"missions_failed {paths_seen.get('missions_failed', 0):2d}  "
              f"hunt_hit {paths_seen.get('hunt_hit', 0):2d}")
    print("   Four runs of 20 at the same setup. Read the spread before calling "
          "any one of them the shift.")

    print(f"\n== item 3: does a long run degrade? Trigger: same length, new seeds")
    for path in ("eval/records/hunt20c.json",) + paths:
        record = load(path)
        games = record["games"]
        early, late = fallbacks(games[:SPLIT_AT]), fallbacks(games[SPLIT_AT:])
        print(f"   {path.split('/')[-1]:14s} games 0-{SPLIT_AT - 1} "
              f"{_pct(*early)}   games {SPLIT_AT}-{len(games) - 1} {_pct(*late)}   "
              f"last 5 {_pct(*fallbacks(games[-5:]))}")
    print("   hunt20c is the run the claim was made on; the S6 arms are the "
          "different seed base it asked for.")


def report(paths: tuple[str, ...]) -> None:
    agreed = control(paths)
    criterion(paths)
    denominator(paths)
    draw_items(paths)
    if not agreed:
        sys.exit(1)


if __name__ == "__main__":
    report(tuple(sys.argv[1:]) or S6_ARMS)
