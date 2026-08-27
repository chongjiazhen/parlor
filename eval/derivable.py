"""Score a finished run against the mechanical reference - the denominator.

Every gate in this repo is scored against chance, which is a floor. This reads the
same records back and asks what a seat could have derived from the public record
WITHOUT listening to anyone, so a rate can finally be reported as a fraction of
something. The instrument and its spec: `games/cabal/solver.py`,
`docs/reference-policies.md`.

Runs on CPU over records that already exist. No new games.

Two sections, and they answer different questions.

**The hunt** is the instrument's own control. `games/cabal/test_solver.py` proves
by exhaustion that the hunter can derive zero bits mechanically in `SETUP_5`, so
this section must read exactly zero on every hunt in every corpus. It is printed
not because it is interesting but because a non-zero here means the offline path
has drifted from the theorem, and every other number below would be wrong the same
way.

**The votes** are where the record actually speaks. For each vote, from each good
seat, over the missions completed BEFORE that vote: what share of the surviving
assignments put an evil seat on the proposed team? A team at taint 1.0 was provably
tainted from the public record alone, and a good seat approving it is failing to
read something the referee had already told it. That is gate #3a's question with a
denominator under it instead of chance.

Two things this file refuses to do quietly, because both failures read as better
numbers rather than as errors: it excludes byte-identical repeat games from a pool
(a same-seed re-run is reproducible by construction - `docs/reproducibility.md`),
and it stratifies good seats by what the NIGHT gave them, because a seer holds both
evils from the deal and would carry a pooled discrimination on its own.

Usage::

    python -m eval.derivable eval/records/hunt20b.json.jsonl
    python -m eval.derivable eval/records/hunt20{-q36,b,c}.json.jsonl --pooled
"""

from __future__ import annotations

import argparse
import json
import sys

from core.stats import bootstrap_ci, wilson
from games.cabal.referee import CabalReferee
from games.cabal.roles import ROLES_BY_KEY, SETUP_5, Role, Team
from games.cabal.solver import (Evidence, RecordMismatch, derivable_bits,
                                parse_missions, parse_timeline,
                                reading_from_record, team_taint)

#: The good roles, in order of how much the night gave them. Reported as separate
#: strata and never pooled - see the module docstring.
GOOD_ROLES = ("loyalist", "watcher", "seer")


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def assignment_of(game: dict) -> dict[int, Role]:
    """Recorded `seat -> role key`, back as roles. An unknown key is a hard stop: a
    reader that silently drops a seat reports a WIDER surviving set, which reads as
    "less was derivable" - wrong in the direction that looks conservative."""
    raw = game.get("assignment") or {}
    unknown = sorted({k for k in raw.values() if k not in ROLES_BY_KEY})
    if unknown:
        raise RecordMismatch(f"record names unknown role(s): {unknown}")
    return {int(s): ROLES_BY_KEY[k] for s, k in raw.items()}


def completed_missions(game: dict) -> list[tuple[tuple[int, ...], int]]:
    return list(parse_missions(game.get("public_events", [])))


def votes_with_history(game: dict):
    """Walk the public record in order, yielding `(team, approvers, missions_before)`.

    Everything comes off `public_events`, the channel every seat holds - so the
    evidence handed to the solver is evidence that seat had, at the moment it had
    it. The record's own `votes` field carries neither the team nor the ordering,
    which is why this replays the timeline instead of reading it.
    """
    done: list[tuple[tuple[int, ...], int]] = []
    for kind, team, n in parse_timeline(game.get("public_events", [])):
        if kind == "vote":
            yield team, set(n), tuple(done)
        else:
            done.append((team, n))


def unit(game: dict) -> dict:
    """One game, reduced to what the statistics need.

    A game is the resampling unit: votes inside one share a deal, a night and a
    table, so treating them as independent draws reports an interval far tighter
    than the evidence supports.
    """
    assignment = assignment_of(game)
    ref = CabalReferee(setup=SETUP_5, assignment=assignment)
    night = {s: ref.entitled_knowledge(s) for s in assignment}

    reading = reading_from_record(game, assignment)
    hunt = None
    if reading is not None:
        hunt = {"bits": reading.bits_gained, "solver": reading.solver_accuracy,
                "chance": reading.chance, "hit": bool(game["hunt"]["hit"])}

    votes: dict[str, list[tuple[float, bool]]] = {r: [] for r in GOOD_ROLES}
    good = [s for s, r in assignment.items() if r.team is Team.GOOD]
    for team, approvers, history in votes_with_history(game):
        for seat in good:
            ev = Evidence(seat=seat, own_role_key=assignment[seat].key,
                          knowledge=night[seat], missions=history)
            votes[assignment[seat].key].append(
                (team_taint(ev, team), seat in approvers))

    end = tuple(completed_missions(game))
    end_bits = [derivable_bits(Evidence(seat=s, own_role_key=assignment[s].key,
                                        knowledge=night[s], missions=end))
                for s in good]

    return {
        "hunt": hunt,
        "votes": votes,
        "end_bits": end_bits,
        "fallbacks": int(game.get("fallbacks") or 0),
        "decisions": int(game.get("decisions") or 0),
    }


# ---- statistics over units -------------------------------------------------

def _mean(xs) -> float | None:
    xs = list(xs)
    return (sum(xs) / len(xs)) if xs else None


def taint_gap(units: list[dict], role: str) -> float | None:
    """Mean derivable taint on teams this stratum REJECTED, minus on those it
    approved. Positive means the seat is reading the record; zero means it is not.

    This is the gate #3a quantity with a denominator: the gate asks whether good
    approves clean teams more than tainted ones, and scores it against chance. Here
    the comparison is against what the record had already PROVED, so a seat cannot
    score by luck on a team it had no way to read.
    """
    approved = [t for u in units for t, ok in u["votes"][role] if ok]
    rejected = [t for u in units for t, ok in u["votes"][role] if not ok]
    if not approved or not rejected:
        return None
    return _mean(rejected) - _mean(approved)


def proven_tainted(units: list[dict], role: str) -> tuple[int, int]:
    """(approved anyway, total) over votes where the record proved the team tainted."""
    calls = [(t, ok) for u in units for t, ok in u["votes"][role] if t >= 1.0 - 1e-9]
    return sum(1 for _, ok in calls if ok), len(calls)


def stratum(taint: float) -> str:
    """Which of the three things the record said about this team, to this seat."""
    if taint <= 1e-9:
        return "clean"
    if taint >= 1.0 - 1e-9:
        return "tainted"
    return "unsure"


def approval_by_stratum(units: list[dict], role: str) -> dict[str, tuple[int, int]]:
    """(approvals, votes) per derivable stratum.

    The headline cut, and more legible than the mean gap: a seat that reads the
    record approves PROVABLY clean teams more than provably tainted ones. A flat
    row means the seat is not reading it - whatever it may be responding to, it is
    not the mechanically derivable part.
    """
    out = {k: [0, 0] for k in ("clean", "unsure", "tainted")}
    for u in units:
        for taint, approved in u["votes"][role]:
            cell = out[stratum(taint)]
            cell[0] += int(approved)
            cell[1] += 1
    return {k: (a, n) for k, (a, n) in out.items()}


def summarise(units: list[dict]) -> dict:
    hunts = [u["hunt"] for u in units if u["hunt"]]
    decisions = sum(u["decisions"] for u in units)
    out = {
        "games": len(units),
        "fallback_rate": (sum(u["fallbacks"] for u in units) / decisions)
                         if decisions else 0.0,
        "hunts": len(hunts),
        "bits_max": max((h["bits"] for h in hunts), default=0.0),
        "bits_mean": _mean(h["bits"] for h in hunts) or 0.0,
        "solver": _mean(h["solver"] for h in hunts) or 0.0,
        "chance": _mean(h["chance"] for h in hunts) or 0.0,
        "hits": sum(1 for h in hunts if h["hit"]),
        "end_bits": [b for u in units for b in u["end_bits"]],
        "by_role": {},
    }
    for role in GOOD_ROLES:
        approved = [t for u in units for t, ok in u["votes"][role] if ok]
        rejected = [t for u in units for t, ok in u["votes"][role] if not ok]
        hit, total = proven_tainted(units, role)
        out["by_role"][role] = {
            "votes": len(approved) + len(rejected),
            "taint_approved": _mean(approved),
            "taint_rejected": _mean(rejected),
            "gap": taint_gap(units, role),
            "gap_ci": bootstrap_ci(units, lambda s, r=role: taint_gap(s, r)),
            "proven_approved": hit,
            "proven_total": total,
            "strata": approval_by_stratum(units, role),
        }
    return out


# ---- reporting -------------------------------------------------------------

def report(name: str, s: dict) -> None:
    print(f"\n== {name}")
    print(f"   {s['games']} games, {s['hunts']} hunts, "
          f"fallback rate {s['fallback_rate']:.1%}")
    if s["fallback_rate"] > 0.10:
        print("   *** fallback rate above 10% - the scorer voids verdicts here ***")

    print("\n   -- the hunt (instrument control: the theorem says 0.000 bits)")
    print(f"   derivable bits           mean {s['bits_mean']:.3f}  "
          f"max {s['bits_max']:.3f}")
    if s["bits_max"] > 1e-9:
        print("   *** NON-ZERO - the offline path has drifted from the exhaustion "
              "proof in test_solver.py. Every number below is suspect. ***")
    print(f"   mechanical hunter        {s['solver']:.3f}   "
          f"(= chance {s['chance']:.3f}, as it must be)")
    ci = wilson(s["hits"], s["hunts"])
    print(f"   the model                {(s['hits'] / s['hunts']) if s['hunts'] else 0:.3f}"
          f"   ({s['hits']}/{s['hunts']})"
          + (f", 95% Wilson [{ci[0]:.3f}, {ci[1]:.3f}]" if ci else ""))
    print("   captured                 UNDEFINED - the denominator is zero, so a")
    print("                            hunter above chance is reading behaviour.")

    print("\n   -- good seats at the vote (where the record does speak)")
    print("   role         votes  taint|approve  taint|reject   gap [95% boot, "
          "by game]   proven tainted, approved")
    for role, row in s["by_role"].items():
        if not row["votes"]:
            continue
        gap = f"{row['gap']:+.3f}" if row["gap"] is not None else "   -  "
        gci = (f" [{row['gap_ci'][0]:+.3f}, {row['gap_ci'][1]:+.3f}]"
               if row["gap_ci"] else "")
        if row["proven_total"]:
            wci = wilson(row["proven_approved"], row["proven_total"])
            proven = (f"{row['proven_approved']}/{row['proven_total']} "
                      f"({row['proven_approved'] / row['proven_total']:.1%})"
                      + (f" [{wci[0]:.0%}, {wci[1]:.0%}]" if wci else ""))
        else:
            proven = "-"
        print(f"   {role:<11} {row['votes']:>6}  {row['taint_approved']:>13.3f}  "
              f"{row['taint_rejected']:>12.3f}   {gap}{gci}   {proven}")
    print("\n   approval rate by what the record PROVED about the team")
    print("   role         provably clean   record unsure   provably tainted"
          "   clean - tainted")
    for role, row in s["by_role"].items():
        if not row["votes"]:
            continue
        cells = []
        for key in ("clean", "unsure", "tainted"):
            hit, n = row["strata"][key]
            cells.append(f"{hit / n:.1%} (n={n})" if n else "- (n=0)")
        c_hit, c_n = row["strata"]["clean"]
        t_hit, t_n = row["strata"]["tainted"]
        swing = (f"{c_hit / c_n - t_hit / t_n:+.1%}" if c_n and t_n else "-")
        print(f"   {role:<11} {cells[0]:>14}  {cells[1]:>14}  {cells[2]:>17}"
              f"   {swing:>15}")

    positive = sum(1 for b in s["end_bits"] if b > 1e-9)
    print(f"   end-of-game bits         mean {_mean(s['end_bits']) or 0:.3f} over "
          f"{len(s['end_bits'])} good seats, {positive} above zero")


def fingerprint(game: dict) -> str:
    """Identity of a game as PLAYED - the deal and both public channels verbatim."""
    return json.dumps([game.get("assignment"), game.get("public_events")],
                      sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("jsonl", nargs="+", help="per-game JSONL from one or more runs")
    ap.add_argument("--pooled", action="store_true",
                    help="also report every file pooled, byte-identical repeats out")
    args = ap.parse_args(argv)

    pool: list[dict] = []
    seen: set[str] = set()
    duplicates = 0
    for path in args.jsonl:
        games = load(path)
        for game in games:
            key = fingerprint(game)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            pool.append(unit(game))
        report(path, summarise([unit(g) for g in games]))

    if args.pooled and len(args.jsonl) > 1:
        # A local run is a function of its seed, so two runs at one seed come back
        # byte-identical. Pooling them tightens every interval while adding no
        # evidence at all, and nothing in the output would say so - the numbers
        # simply look better. Excluded here rather than left to whoever assembles
        # the file list.
        if duplicates:
            print(f"\n*** {duplicates} game(s) were byte-identical repeats of an "
                  "earlier file and are EXCLUDED from the pool: a same-seed re-run "
                  "carries no new evidence (docs/reproducibility.md). ***")
        report(f"POOLED ({len(pool)} distinct games)", summarise(pool))
    return 0


if __name__ == "__main__":
    sys.exit(main())
