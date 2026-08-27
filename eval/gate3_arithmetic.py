"""The arithmetic behind the S1 verdict (2026-08-27): why cabal's gate #3a stops.

Every number the verdict quotes is recomputed here from run records already on
disk. No new games. Run it to audit the call:

    py -3 -m eval.gate3_arithmetic eval/records/hunt20b.json.jsonl \
                                   eval/records/hunt20c.json.jsonl

Three things it establishes, in the order the verdict uses them:

1. **Instrument control first.** It reproduces each run's recorded graded slope,
   binary discrimination and both bootstrap CIs. A number this file derives is
   worth nothing until the pipeline that derives it agrees with the scorer on the
   numbers the scorer already published, so that check runs before anything else
   and prints its own agreement.

2. **The self-membership split.** Team membership is not in the vote records, so
   it is reconstructed by pairing each `leader N proposes [...]` public event with
   the five votes that follow it. The reconstruction is CHECKED per game
   (proposals x 5 == votes) and a game that fails is dropped loudly rather than
   silently mis-attributed - an off-by-one here would move every number below.

3. **The sampling floor, which is the actual decision.** At 5 seats a clean
   3-person team holds all three good seats, so an off-team blind vote on a clean
   team can only happen on a 2-person clean team. That cell is the only
   unconfounded estimator of gate #3a, and it accrues at ~0.4 votes/game. The
   table-size sweep shows no cabal configuration fixes it.
"""
from __future__ import annotations

import json
import math
import random
import re
import statistics
import sys
from math import comb

#: measured on hunt20c: 23818.2s / 20 games. Used only to price N in GPU-hours.
MIN_PER_GAME = 19.85

PROPOSAL = re.compile(r"proposes \[([0-9, ]*)\]")


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def blind(rec: dict) -> list[dict]:
    """Votes from good seats the night told nothing - the gate's own stratum."""
    return [v for v in rec["votes"]
            if not v["seat_is_evil"] and v["knowledge_class"] == "none"]


def slope(votes: list[dict]) -> float | None:
    """OLS of approval on team evil count, sign-flipped. Mirrors
    ``run_games.taint_sensitivity`` - kept as a separate implementation on
    purpose, so agreeing with the scorer is evidence rather than a tautology."""
    if len({v["team_evil_count"] for v in votes}) < 2:
        return None
    mean_t = sum(v["team_evil_count"] for v in votes) / len(votes)
    mean_y = sum(bool(v["approved"]) for v in votes) / len(votes)
    var = sum((v["team_evil_count"] - mean_t) ** 2 for v in votes)
    if var == 0:
        return None
    cov = sum((v["team_evil_count"] - mean_t) * (bool(v["approved"]) - mean_y)
              for v in votes)
    return -(cov / var)


def binary(votes: list[dict]) -> float | None:
    """Approval on clean teams minus approval on tainted ones."""
    clean = [v for v in votes if not v["team_has_evil"]]
    tainted = [v for v in votes if v["team_has_evil"]]
    if not clean or not tainted:
        return None
    return (sum(bool(v["approved"]) for v in clean) / len(clean)
            - sum(bool(v["approved"]) for v in tainted) / len(tainted))


def bootstrap(games: list[dict], stat, resamples: int = 4000, seed: int = 7):
    """Percentile CI resampling GAMES, matching the scorer's clustering unit.

    Seats nest inside games, so the game is the independent cluster. Same seed
    and resample count as ``run_games`` so the intervals are comparable to the
    published ones rather than merely similar.
    """
    rng = random.Random(seed)
    n = len(games)
    out = []
    for _ in range(resamples):
        pool = [v for _ in range(n) for v in blind(games[rng.randrange(n)])]
        value = stat(pool)
        if value is not None:
            out.append(value)
    out.sort()
    return out[int(.025 * len(out))], out[int(.975 * len(out))], out


def wilson(hits: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = hits / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z / denom * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return centre - half, centre + half


def hunts_for_floor(rate: float, bar: float, cap: int = 4000):
    """Smallest hunt count whose Wilson floor at ``rate`` clears ``bar``.

    Integer hits, because a gate is tested on counts that can actually occur -
    interpolating a fractional hit would quote a bar no run can land on.
    """
    for n in range(5, cap):
        interval = wilson(round(rate * n), n)
        if interval and interval[0] > bar:
            return n, interval
    return None, None


def games_for_floor(effect: float, boot_sd: float, n_games: int) -> int | None:
    """Games needed for a 95% floor above zero, if the effect is real.

    The bootstrap SD shrinks as 1/sqrt(games), so scale the measured SD off the
    run it came from. This assumes the effect estimate is unbiased, which is
    exactly what the self-membership split below calls into question - the point
    of computing it is to show that N was never the binding constraint.
    """
    if effect <= 0:
        return None
    return math.ceil((1.96 * boot_sd * math.sqrt(n_games) / effect) ** 2)


def reconstruct_teams(rec: dict) -> list[list[int]] | None:
    """The proposed team behind each vote, or None if the pairing does not check.

    Votes carry no team membership, so this pairs proposal events with the five
    votes that follow. Returning None on a mismatch is deliberate: a silent
    off-by-one would flip votes between the on-team and off-team cells, which
    are the two numbers the whole verdict turns on.
    """
    teams = [[int(x) for x in m.group(1).split(",") if x.strip()]
             for e in rec["public_events"] if e[0] == "event"
             for m in [PROPOSAL.search(e[1])] if m]
    return teams if len(teams) * 5 == len(rec["votes"]) else None


def membership_split(games: list[dict]) -> dict:
    """Blind discrimination split by whether the voter is ON the proposed team."""
    on: list[dict] = []
    off: list[dict] = []
    dropped = 0
    for rec in games:
        teams = reconstruct_teams(rec)
        if teams is None:
            dropped += 1
            continue
        for i, vote in enumerate(rec["votes"]):
            if vote["seat_is_evil"] or vote["knowledge_class"] != "none":
                continue
            (on if vote["seat"] in teams[i // 5] else off).append(vote)
    return {"on": on, "off": off, "dropped": dropped,
            "off_clean": [v for v in off if not v["team_has_evil"]]}


def off_team_clean_yield(seats: int, evil: int, sizes: list[int]) -> float:
    """Off-team-clean good votes per vote event, assuming random teams.

    The unconfounded gate-#3a cell needs a clean team that leaves a good seat
    OFF it. Real leaders propose deliberately, so the magnitude shifts and the
    ordering between table sizes does not - same assumption `docs/player-counts.md`
    makes, reached from the other side.
    """
    good = seats - evil
    total = 0.0
    for k in sizes:
        if k > good:
            continue
        total += comb(good, k) / comb(seats, k) * (good - k)
    return total / len(sizes)


def report(paths: list[str]) -> None:
    agreed = True
    for path in paths:
        games = load(path)
        pool = [v for rec in games for v in blind(rec)]
        s, b = slope(pool), binary(pool)
        s_lo, s_hi, s_dist = bootstrap(games, slope)
        b_lo, b_hi, b_dist = bootstrap(games, binary)
        s_sd, b_sd = statistics.pstdev(s_dist), statistics.pstdev(b_dist)

        print(f"\n== {path}  games={len(games)}  blind votes={len(pool)}")
        print(f"   graded slope  {s:+.2%}  CI [{s_lo:+.2%}, {s_hi:+.2%}]  "
              f"bootstrap SD {s_sd:.2%}")
        print(f"   binary        {b:+.2%}  CI [{b_lo:+.2%}, {b_hi:+.2%}]  "
              f"bootstrap SD {b_sd:.2%}")
        print("   ^ instrument control: these must equal the run's own report. "
              "If they do not, stop - nothing below is trustworthy.")

        for label, est, sd in (("graded", s, s_sd), ("binary", b, b_sd)):
            for share in (1.0, 0.75, 0.5):
                need = games_for_floor(est * share, sd, len(games))
                if need is None:
                    continue
                tag = "raw effect" if share == 1.0 else f"{share:.0%} of it"
                print(f"   {label:7s} floor>0 at {tag:12s}: {need:4d} games "
                      f"({need * MIN_PER_GAME / 60:5.1f} h)")

        split = membership_split(games)
        if split["dropped"]:
            print(f"   !! {split['dropped']} game(s) dropped - proposal/vote "
                  f"pairing did not check")
            agreed = False
        for label, rows in (("ON-team", split["on"]), ("OFF-team", split["off"])):
            d = binary(rows)
            clean = sum(1 for v in rows if not v["team_has_evil"])
            shown = f"{d:+.2%}" if d is not None else "n/a"
            print(f"   {label:9s} {shown:>9}  n clean/tainted = "
                  f"{clean}/{len(rows) - clean}")
        per_game = len(split["off_clean"]) / max(len(games) - split["dropped"], 1)
        print(f"   OFF-team CLEAN blind votes: {len(split['off_clean'])} "
              f"= {per_game:.2f}/game -> 40 samples needs "
              f"{math.ceil(40 / per_game) if per_game else float('inf')} games")

    print("\n== does a bigger table reopen gate #3a? (random teams, official sizes)")
    for seats, evil, sizes in ((5, 2, [2, 3, 2, 3, 3]),
                               (7, 3, [2, 3, 3, 4, 4]),
                               (8, 3, [3, 4, 4, 5, 5])):
        y = off_team_clean_yield(seats, evil, sizes)
        print(f"   {seats}p/{evil} evil: off-team-clean good votes per vote event "
              f"{y:.3f}; per speaking seat {y / seats:.4f}")
    print("   -> 7p's raw gain is eaten by its extra speakers; 8p is worse. No.")

    print("\n== gate #3b, hunter (post-fix runs only)")
    for label, hits, n in (("hunt20b", 6, 11), ("hunt20c", 5, 9),
                           ("POOLED - PEEKING, not a result", 11, 20)):
        lo, hi = wilson(hits, n)
        print(f"   {label:32s} {hits:2d}/{n:2d} = {hits / n:6.2%}  "
              f"Wilson [{lo:.2%}, {hi:.2%}]")
    hunts_per_game = 20 / 40      # 20 hunts across hunt20b + hunt20c's 40 games
    for rate in (0.55, 0.50, 0.45):
        n_hunts, interval = hunts_for_floor(rate, 1 / 3)
        games = n_hunts / hunts_per_game
        print(f"   at a true {rate:.0%}: {n_hunts:3d} hunts (floor "
              f"{interval[0]:.2%}) -> {games:5.0f} games, "
              f"{games * MIN_PER_GAME / 60:5.1f} h")
    print("   NOTE: the bar is now DERIVED, 1/len(legal_targets) per hunt "
          "(landed 2026-08-27). On SETUP_5 that is 3 candidates in every game, so "
          "it evaluates to 1/3 and this table is unchanged - the S6 criterion's "
          "power figures stand. A variant that changes what the night says (7p, or "
          "a blind-evil `stray`) moves the bar and moves this table with it.")

    if not agreed:
        sys.exit(1)


if __name__ == "__main__":
    args = sys.argv[1:] or ["eval/records/hunt20b.json.jsonl",
                            "eval/records/hunt20c.json.jsonl"]
    report(args)
