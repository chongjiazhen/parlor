"""The control ladder: what a hand-written policy gets, so a gate can say more
than "better than noise".

Two halves, and the second is the one that matters.

**Seated arms** play CPU-only games and answer "does the rule help?". One side is
swapped at a time against the random control, because swapping both changes good
and evil at once and the win rate then measures neither - the all-heuristic arm is
reported anyway, flagged, because it is what a careless reading of "heuristic vs
random" would produce.

**Offline arms** apply the hunt rules to the LLM corpus that already exists. That
is the AvalonBench question asked properly: not "can a bot beat a bot", but *how
much of the signal the models left in their own record does a sixty-line rule
extract, and how much did the model itself get*. It costs no games and no GPU.

Usage::

    python -m eval.ladder --games 300
    python -m eval.ladder --records eval/records/hunt20{-q36,b,c}.json.jsonl
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass

from core.stats import wilson
from eval.derivable import fingerprint, load
from games.cabal.heuristic import (HeuristicPolicy, hunt_by_rejections,
                                   hunt_by_votes)
from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee
from games.cabal.roles import ROLES_BY_KEY, Team, known_allies, legal_hunt_targets
from games.cabal.solver import parse_votes

HUNT_RULES = {
    "votes (taint-conditioned)": hunt_by_votes,
    "rejections only (control)": hunt_by_rejections,
}


# ---- seated arms -----------------------------------------------------------

@dataclass
class ArmResult:
    name: str
    games: int
    good_wins: int
    hunts: int
    hunt_hits: int


def play_arm(name: str, heuristic_good: bool, heuristic_evil: bool,
             games: int, seed0: int = 0) -> ArmResult:
    """One arm of the ladder. Seating is decided by the EXPERIMENTER from the deal,
    which no policy may do - a policy reads only its own role and what the referee
    rendered to it."""
    good = hunts = hits = 0
    for i in range(games):
        seed = seed0 + i
        ref = CabalReferee.new(5, seed=seed)
        policies = {}
        for s in range(5):
            use = heuristic_good if ref.assignment[s].team is Team.GOOD else heuristic_evil
            rng = random.Random(seed * 10 + s)
            policies[s] = HeuristicPolicy(rng=rng) if use else RandomPolicy(rng=rng)
        rec = play_game(ref, policies)
        good += int(rec.winner == "good")
        if rec.hunt:
            hunts += 1
            hits += int(rec.hunt["hit"])
    return ArmResult(name, games, good, hunts, hits)


def report_arms(arms: list[ArmResult]) -> None:
    print("\n== seated arms (CPU games, one side swapped at a time)")
    print("   arm                              good wins            hunter")
    for a in arms:
        ci = wilson(a.good_wins, a.games)
        gw = (f"{a.good_wins / a.games:6.1%} [{ci[0]:.0%}, {ci[1]:.0%}]"
              if ci else "-")
        hunt = (f"{a.hunt_hits}/{a.hunts} = {a.hunt_hits / a.hunts:5.1%}"
                if a.hunts else "no hunts reached")
        print(f"   {a.name:<32} {gw}   {hunt}")


# ---- offline arms ----------------------------------------------------------

def score_rules(paths: list[str]) -> dict:
    """Apply each hunt rule to every recorded hunt, tie-averaged.

    Tie-averaged rather than tie-broken: an argmax set of size k scores `1/k` when
    the seer is in it. A corpus number should not carry the luck of a tie-break
    convention, and the seated policy's `rng.choice` is that convention.
    """
    seen: set[str] = set()
    out = {name: [0.0, 0] for name in HUNT_RULES}
    out["the model itself"] = [0.0, 0]
    out["chance"] = [0.0, 0]
    for path in paths:
        for game in load(path):
            key = fingerprint(game)
            if key in seen or not game.get("hunt"):
                seen.add(key)
                continue
            seen.add(key)
            assignment = {int(s): ROLES_BY_KEY[k]
                          for s, k in game["assignment"].items()}
            hunter = int(game["hunt"]["hunter"])
            seer = int(game["hunt"]["seer"])
            known_evil = known_allies(assignment, hunter) | {hunter}
            legal = legal_hunt_targets(assignment, hunter)
            votes = parse_votes([tuple(e) for e in game["public_events"]])
            for name, rule in HUNT_RULES.items():
                arg = rule(legal, known_evil, votes)
                out[name][0] += (1 / len(arg)) if seer in arg else 0.0
                out[name][1] += 1
            out["the model itself"][0] += int(bool(game["hunt"]["hit"]))
            out["the model itself"][1] += 1
            out["chance"][0] += 1 / len(legal)
            out["chance"][1] += 1
    return out


def report_rules(scored: dict) -> None:
    n = scored["chance"][1]
    chance = scored["chance"][0] / n if n else 0.0
    model = scored["the model itself"][0] / n if n else 0.0
    print(f"\n== the hunt, on the LLM corpus ({n} hunts, no new games)")
    print("   who                          accuracy          95% Wilson")
    for name in ("chance", "the model itself", *HUNT_RULES):
        hit, total = scored[name]
        rate = hit / total if total else 0.0
        ci = wilson(round(hit), total)
        band = f"[{ci[0]:.0%}, {ci[1]:.0%}]" if ci and name != "chance" else ""
        print(f"   {name:<28} {rate:6.1%} ({hit:5.2f}/{total})  {band}")

    print("\n   captured - the model's share of what a rule extracts from the same")
    print("   record. The MECHANICAL denominator is zero (proved in test_solver.py),")
    print("   so every one of these points is behavioural.")
    for name in HUNT_RULES:
        ceiling = scored[name][0] / scored[name][1]
        if ceiling - chance <= 1e-9:
            print(f"   vs {name:<28} undefined - the rule is at chance")
            continue
        print(f"   vs {name:<28} {(model - chance) / (ceiling - chance):5.1%}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--games", type=int, default=0,
                    help="games per seated arm (0 skips the seated half)")
    ap.add_argument("--records", nargs="*", default=[],
                    help="per-game JSONL to score the hunt rules against")
    args = ap.parse_args(argv)
    if not args.games and not args.records:
        ap.error("give --games, --records, or both")

    if args.games:
        report_arms([
            play_arm("random / random (the floor)", False, False, args.games),
            play_arm("HEURISTIC good / random evil", True, False, args.games),
            play_arm("random good / HEURISTIC evil", False, True, args.games),
            play_arm("heuristic / heuristic", True, True, args.games),
        ])
        print("   The last row swaps BOTH sides, so its win rate measures neither.")
        print("   Its hunter figure is an artifact and not a result: a deterministic")
        print("   seer's votes track taint exactly, so the rule is reading its own")
        print("   twin's tell. Only the two middle rows are controlled comparisons.")

    if args.records:
        report_rules(score_rules(args.records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
