"""Per-GAME deduction, off records that already exist. No GPU, no new games.

    py -3 -m eval.deduction                        # the S5 records
    py -3 -m eval.deduction --record <path>.json   # any changeling run

**Why this exists.** Gate #3 holds: villager accuracy over 200 games beats the
chance baseline, and that is a claim about the AGGREGATE. A person playing by hand
reported the game feeling arbitrary anyway, and nothing here could answer them,
because "the table deduces above chance on average" and "this game was decided by
deduction" are different sentences. The second one is per-game and nobody had
computed it.

**It re-uses the gate's own definitions rather than inventing a rival.** A hit is
a villager vote landing on a seat that HELD a pack card at dawn, villager means
holds-village-at-dawn, and games with no wolf seated are out of the denominator -
all three are `eval.run_changeling`'s, imported here, not restated. A second
almost-identical definition of accuracy is how two numbers in one repo stop being
comparable, and this file must never become that.

**What it adds is decisiveness.** Accuracy alone cannot separate a table that
reasoned from one that guessed and got lucky, because the winner is decided BY the
votes - so "village won when villagers voted well" is close to tautological and is
deliberately not reported as a finding. What is not tautological is how much slack
the result had: `min_flips` is the smallest number of votes that, redirected to
another legal target, would hand the game to the other side. A game that turns on
one vote was a coin flip whatever its accuracy looked like, and a table that wins
with two votes to spare converged on something.

The execution rule is re-derived here (plurality; a tie accuses everyone tied;
village wins if any accused seat held a pack card) because the referee resolves it
against live state and a record has no referee. `test_deduction.py` pins that
re-derivation against the recorded winner on every game in the file - if the rule
here ever drifts from the referee's, the control fails rather than the number
quietly changing.
"""
from __future__ import annotations

import argparse
import json

from core.stats import bootstrap_ci, wilson
from eval.s5_verdict import S2 as _DEFAULT
from eval.s5_verdict import dawn_wolves, load, villager_votes, winnable

PACK = "pack"


def winner_from(votes: dict[int, int], truth: dict[int, str],
                rule: str = "plurality") -> str:
    """The referee's rule, applied to a vote map, under the rule the RECORD names.

    ``plurality`` (every record before 2026-09-02, and the default because those
    records carry no ``vote_rule`` key): the top count accuses, a tie accuses every
    seat tied, the village wins if any accused seat held a pack card.
    ``plurality-min2`` (the referee since 2026-09-02): the same, except a top
    count of one accuses nobody, and then the village wins only if no seat holds a
    pack card at dawn.
    """
    tally: dict[int, int] = {}
    for target in votes.values():
        tally[target] = tally.get(target, 0) + 1
    top = max(tally.values())
    if rule == "plurality-min2" and top <= 1:
        return "pack" if any(c == PACK for c in truth.values()) else "village"
    accused = [s for s, c in tally.items() if c == top]
    return "village" if any(truth[str(s)] == PACK for s in accused) else "pack"


def min_flips(game: dict, cap: int = 2) -> int | None:
    """Fewest votes that, redirected to another legal target, flip the winner.

    ``None`` means more than ``cap`` - the result had real slack. A seat may not
    vote for itself, which is the only legality this has to honour.
    """
    truth = game["truth"]
    seats = sorted(int(s) for s in truth)
    votes = {v["seat"]: v["target"] for v in game["votes"]}
    if len(votes) != len(seats):
        return None                      # an incomplete vote map decides nothing
    rule = game.get("vote_rule", "plurality")
    now = winner_from(votes, truth, rule)

    def flipped(changes) -> bool:
        trial = dict(votes)
        for seat, target in changes:
            trial[seat] = target
        return winner_from(trial, truth, rule) != now

    for seat in votes:
        for target in seats:
            if target != seat and target != votes[seat] and flipped([(seat, target)]):
                return 1
    if cap < 2:
        return None
    voters = sorted(votes)
    for i, a in enumerate(voters):
        for b in voters[i + 1:]:
            for ta in seats:
                if ta == a or ta == votes[a]:
                    continue
                for tb in seats:
                    if tb == b or tb == votes[b]:
                        continue
                    if flipped([(a, ta), (b, tb)]):
                        return 2
    return None


def per_game(game: dict) -> dict:
    """One game's deduction reading. ``chance`` is this game's own, not the run's:
    a villager pointing at random hits a wolf at (dawn wolves)/(other seats), and
    that nearly doubles between a one- and a two-wolf dawn."""
    votes = villager_votes(game)
    seats = len(game["truth"])
    hits = sum(1 for v in votes if v["target_holds_pack"])
    chance = dawn_wolves(game) / (seats - 1)
    acc = hits / len(votes) if votes else None
    return {
        "winner": game["winner"],
        "villager_votes": len(votes),
        "hits": hits,
        "accuracy": acc,
        "chance": chance,
        # Share of the headroom above chance that this table actually took. 0.0 is
        # a table voting at random; 1.0 is every villager on a wolf.
        "lift": None if acc is None or chance >= 1 else (acc - chance) / (1 - chance),
        "min_flips": min_flips(game),
    }


def report(games: list[dict]) -> list[str]:
    rows = [per_game(g) for g in winnable(games)]
    scored = [r for r in rows if r["accuracy"] is not None]
    out = [f"per-game deduction over {len(scored)} winnable games "
           f"({len(games) - len(scored)} excluded: no wolf at dawn, or no votes)",
           ""]

    above = [r for r in scored if r["accuracy"] > r["chance"]]
    at = [r for r in scored if r["accuracy"] == r["chance"]]
    below = [r for r in scored if r["accuracy"] < r["chance"]]
    out += ["  votes vs this game's own chance baseline",
            f"    above    {len(above):4d}  ({len(above) / len(scored):.1%})",
            f"    at       {len(at):4d}  ({len(at) / len(scored):.1%})",
            f"    below    {len(below):4d}  ({len(below) / len(scored):.1%})"]

    lifts = [r["lift"] for r in scored if r["lift"] is not None]
    mean = sum(lifts) / len(lifts)
    ci = bootstrap_ci(lifts, lambda xs: sum(xs) / len(xs))
    band = f" [{ci[0]:+.3f}, {ci[1]:+.3f}]" if ci else ""
    out += ["", f"  mean per-game lift  {mean:+.3f}{band}",
            "    0.000 is a table voting at random; 1.000 is every villager on a wolf"]

    # The headline. A win that one redirected vote would have erased is not
    # evidence of deduction, however the accuracy column reads.
    knife = [r for r in scored if r["min_flips"] == 1]
    two = [r for r in scored if r["min_flips"] == 2]
    slack = [r for r in scored if r["min_flips"] is None]
    out += ["", "  decisiveness - fewest vote changes that flip the winner",
            f"    1 vote   {len(knife):4d}  ({len(knife) / len(scored):.1%})",
            f"    2 votes  {len(two):4d}  ({len(two) / len(scored):.1%})",
            f"    3+       {len(slack):4d}  ({len(slack) / len(scored):.1%})"]

    wins = [r for r in scored if r["winner"] == "village"]
    if wins:
        won_knife = sum(1 for r in wins if r["min_flips"] == 1)
        lo, hi = wilson(won_knife, len(wins))
        out += ["", f"  village wins decided by ONE vote  {won_knife}/{len(wins)} "
                    f"({won_knife / len(wins):.1%}) [{lo:.1%}, {hi:.1%}]",
                "    the measurable half of \"it feels random\": a win this thin was",
                "    available to a table that had deduced nothing"]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", default=_DEFAULT,
                    help="summary path; its .jsonl sibling holds the games")
    ap.add_argument("--json", action="store_true", help="per-game rows, one per line")
    args = ap.parse_args(argv)

    _, games = load(args.record)
    if args.json:
        for g in winnable(games):
            print(json.dumps(per_game(g)))
        return 0
    print("\n".join(report(games)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
