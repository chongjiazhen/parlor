"""Stratify stored cabal cloud records by upstream that served each decision.

Run with one or more full JSON records or landed JSONL files. Cells deliberately
accumulate across input paths: an upstream is population, not a property of one
run under a routing alias.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from core.stats import wilson


UNATTRIBUTED = "UNATTRIBUTED - fallback source unknown"


def _cell() -> dict:
    return {"decisions": 0, "fallbacks": 0, "clean": 0, "clean_votes": 0,
            "tainted": 0, "tainted_votes": 0, "hunt_hits": 0, "hunts": 0}


def _served(decision: dict, *, game: int, outcome: str) -> str:
    """Return outcome provenance, refusing records that would pool unknowns."""
    served_by = decision.get("served_by")
    if not served_by:
        raise ValueError(f"game {game} {outcome} has no served_by provenance")
    return served_by


def score_records(records: list[dict]) -> dict[str, dict]:
    """Score each served upstream from stored games without pooling cells."""
    cells = defaultdict(_cell)
    for game_index, record in enumerate(records):
        decisions = record.get("decision_log") or []
        by_turn_seat = {}
        for decision in decisions:
            served_by = decision.get("served_by")
            if served_by:
                cell = cells[served_by]
                cell["decisions"] += 1
                cell["fallbacks"] += bool(decision.get("fell_back"))
            elif decision.get("fell_back"):
                # Legacy rows erased provenance on every fallback, whatever caused
                # it. Keep this denominator visible without inventing attribution.
                cell = cells[UNATTRIBUTED]
                cell["decisions"] += 1
                cell["fallbacks"] += 1
            else:
                raise ValueError(f"game {game_index} decision has no served_by provenance")
            by_turn_seat[(decision.get("turn"), decision.get("seat"))] = decision

        for vote in record.get("votes") or []:
            if vote.get("seat_is_evil") or vote.get("knowledge_class") != "none":
                continue
            # Pre-provenance vote rows have no turn, so cannot be joined without
            # guessing. Keep any independently attributable hunt in this record.
            if vote.get("turn") is None:
                continue
            key = (vote.get("turn"), vote.get("seat"))
            decision = by_turn_seat.get(key)
            if decision is None:
                raise ValueError(f"game {game_index} vote has no decision record")
            if decision.get("fell_back"):
                continue
            cell = cells[_served(decision, game=game_index, outcome="vote")]
            if vote.get("team_has_evil"):
                cell["tainted_votes"] += 1
                cell["tainted"] += bool(vote.get("approved"))
            else:
                cell["clean_votes"] += 1
                cell["clean"] += bool(vote.get("approved"))

        hunt = record.get("hunt")
        if hunt:
            hunter = hunt.get("hunter")
            hunt_decisions = [d for d in decisions
                              if d.get("phase") == "hunt" and d.get("seat") == hunter]
            if len(hunt_decisions) != 1:
                raise ValueError(f"game {game_index} hunt has no unique decision record")
            decision = hunt_decisions[0]
            if decision.get("fell_back"):
                continue
            cell = cells[_served(decision, game=game_index, outcome="hunt")]
            cell["hunts"] += 1
            cell["hunt_hits"] += bool(hunt.get("hit"))

    scored = {}
    for upstream, cell in sorted(cells.items()):
        clean_rate = cell["clean"] / cell["clean_votes"] if cell["clean_votes"] else None
        tainted_rate = (cell["tainted"] / cell["tainted_votes"]
                        if cell["tainted_votes"] else None)
        scored[upstream] = {
            "integrity": {
                "decisions": cell["decisions"],
                "fallbacks": cell["fallbacks"],
                "fallback_rate": cell["fallbacks"] / cell["decisions"],
            },
            "votes": {
                "clean": cell["clean"],
                "tainted": cell["tainted"],
                "discrimination": (clean_rate - tainted_rate
                                   if clean_rate is not None and tainted_rate is not None
                                   else None),
            },
            "hunts": {
                "hits": cell["hunt_hits"],
                "total": cell["hunts"],
                "accuracy": (cell["hunt_hits"] / cell["hunts"]
                             if cell["hunts"] else None),
                "ci95": wilson(cell["hunt_hits"], cell["hunts"]),
            },
        }
    return scored


def load_paths(paths: list[str]) -> list[dict]:
    """Read run summary JSON and incremental JSONL records into one population."""
    records = []
    for raw_path in paths:
        path = Path(raw_path)
        with path.open(encoding="utf-8") as fh:
            if path.suffix == ".jsonl":
                records.extend(json.loads(line) for line in fh if line.strip())
            else:
                records.extend(json.load(fh).get("games") or [])
    return records


def report(score: dict[str, dict]) -> str:
    """One measurement block per upstream, never a synthetic pooled total."""
    lines = []
    for upstream, cell in score.items():
        integrity, votes, hunts = cell["integrity"], cell["votes"], cell["hunts"]
        lines += [
            upstream,
            f"  integrity  {integrity['fallbacks']}/{integrity['decisions']} fallbacks "
            f"({integrity['fallback_rate']:.2%})",
            f"  votes      discrimination "
            + (f"{votes['discrimination']:+.2%}" if votes["discrimination"] is not None
               else "REFUSED")
            + f" ({votes['clean']} clean approvals, {votes['tainted']} tainted approvals)",
            f"  hunts      "
            + (f"{hunts['hits']}/{hunts['total']} ({hunts['accuracy']:.2%}, 95% CI "
               f"{hunts['ci95'][0]:.2%}-{hunts['ci95'][1]:.2%})"
               if hunts["accuracy"] is not None else "REFUSED - no hunts"),
        ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("records", nargs="+", help="run_cabal JSON or JSONL record paths")
    args = ap.parse_args(argv)
    print(report(score_records(load_paths(args.records))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
