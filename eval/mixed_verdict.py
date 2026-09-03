"""The changeling mixed cells, scored as the criterion promised.

``py -3 -m eval.mixed_verdict [records-dir]`` reads whichever of the two records
``eval/runs/changeling-mixed.cmd`` (or its one-arm sibling) wrote and prints the
read ``docs/changeling-mixed-criterion.md`` pre-committed: the hand-written
rung's win rate against LIVE seats, against its win rate against its own twin,
under a Newcombe interval, voids first.

Three things in that criterion are easy to get wrong by hand at the moment an arm
lands, which is most of why this file exists rather than a session's arithmetic.

**The control is rescored, never quoted.** ``cl-heuristic.json`` is 1000 games on
seeds 5000..5999 and these arms play 5000..5199, so its published 56.09% / 43.91%
are a figure over a SUPERSET of the arm's seeds. They are printed here as the
wider-interval reference and are never the number the difference is taken
against; ``control_slice`` takes the first 200 game indices and the pair is read
off those.

**The fallback bar is the LIVE SIDE's own rate.** The run-level ``fallback_rate``
counts every seat's decisions, and a rung seat never falls back, so a five-seat
game with two live seats reports about two fifths of the live side's real rate. A
10% bar applied to the diluted figure would pass an arm whose live seats fell back
a quarter of the time.

**A missing arm is a lost pair, not half a result.** Each arm is read on its own
against its own rescored control, and no cross-arm claim is made.

A voided or refused record is still AUDITED - every figure prints and the exit
code says 3 - because this repo publishes numbers from records and a scorer that
returns early leaves a published number with no instrument in the tree.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from core import integrity
from core.stats import wilson
from eval.gate3_bar import REFERENCE_CHANCE
from eval.s5_verdict import BLIND_FLOOR_VOTES, winnable
from eval.skin_pair_verdict import (
    Arm,
    Verdict,
    _ci,
    _excludes_zero,
    load,
    newcombe,
)
from games.changeling.roles import CARDS, Side

#: The frozen file this module answers to. The settings below are a COPY of its
#: §Settings block and a test reads the file to hold them equal - the failure
#: this repo has already paid for (belfry live1) is a launcher and a criterion
#: disagreeing while each looked right on its own.
CRITERION = "docs/changeling-mixed-criterion.md"

#: Per arm: the record stem, the side the RUNG plays (which is the side whose win
#: rate is the primary), and the published 1000-game control figure that is
#: reported beside the rescore and never in place of it.
ARMS: dict[str, dict] = {
    "mixed-pack": {"stem": "cl-mixed-pack", "rung_side": "village",
                   "live_side": "pack", "published": 0.4391, "secondary": True},
    "mixed-village": {"stem": "cl-mixed-village", "rung_side": "pack",
                      "live_side": "village", "published": 0.5609,
                      "secondary": False},
}

CONTROL_STEM = "cl-heuristic"
#: The control record's first N game indices - the arm's own seeds and no more.
CONTROL_GAMES = 200
#: The published blind figure of the all-heuristic control at 1000 games, and the
#: rung-village-against-a-random-pack cell the secondary exists to price.
PUBLISHED_BLIND = 0.4926
PUBLISHED_BLIND_VS_RANDOM = 0.7736

EXPECTED = {"theme": "folk", "seats": 5, "seed": 5000, "rounds": 2,
            "no_thinking": True, "temperature": 0.8, "games": 200,
            "model": "qwen36-35b-a3b-iq3", "register": "character",
            "max_tokens": 1536, "retries": 2, "timeout": 240.0}
#: Under this many scored games an arm is REFUSED, not called.
SCORED_FLOOR = 150


def settings_voids(args: dict, arm: str) -> list[str]:
    """Every criterion setting the record's own `args` contradicts.

    ``arm`` is one of them: a record written by the wrong ``--arm`` is a
    different experiment wearing this criterion's file name.
    """
    expected = {**EXPECTED, "arm": arm}
    return [f"{k} is {args.get(k)!r}, criterion says {v!r}"
            for k, v in expected.items() if args.get(k) != v]


def dedupe_last(games: list[dict]) -> list[dict]:
    """One record per game index, keeping the LAST written, in game order.

    `core.runlog.record_paths`' JSONL is opened ``"a"`` while the summary beside
    it is opened ``"w"``, so a second run onto an existing record path stacks a
    block rather than replacing one - the summary describes the last run and the
    JSONL holds every run. Measured 2026-09-03: `cl-heuristic.json.jsonl` is
    3000 lines for a 1000-game run, and its FIRST block is a stale play of the
    same seeds at 71.55% pack wins against the published 56.09%. Read naively
    the three blend to about 61%, which is a plausible number, off by five
    points, with nothing raising.

    Last wins because append order is write order and the summary was written by
    the last run - and that recovery is then CHECKED, in `summary_voids`, rather
    than trusted.

    **It stays, and is now about the PAST.** `core.runlog.claim_record` refuses an
    occupied record path from 2026-09-03, so no run lands a second block again;
    the records already carrying one are not going to rewrite themselves, and this
    is what reads them.
    """
    by_index = {int(g["game"]): g for g in games}
    return [by_index[i] for i in sorted(by_index)]


def summary_voids(games: list[dict], summary: dict) -> list[str]:
    """Where the recovered games disagree with the figures published from them.

    Deduping RECOVERS a run; it does not prove it recovered the right one. The
    summary carries two counts computed in-process from the games it scored, so
    a rescore that reproduces both has recovered that run and one that does not
    is pairing against something else.
    """
    hits, scored = rung_wins(games, "village")
    want_scored = summary.get("games_scored")
    want_wins = summary.get("gate2_deception", {}).get("village_wins")
    voids = []
    if want_scored is not None and scored != want_scored:
        voids.append(f"rescored {scored} scored games, summary published "
                     f"{want_scored}")
    if want_wins is not None and hits != want_wins:
        voids.append(f"rescored {hits} village wins, summary published "
                     f"{want_wins}")
    return voids


def control_slice(games: list[dict], n: int = CONTROL_GAMES) -> list[dict]:
    """The control's first ``n`` game INDICES, deduped, in game order.

    Selected on ``game`` rather than by position: the arm plays seeds
    5000..5199 and the control 5000..5999, and a positional head would silently
    pair a different set of deals the moment a record is written out of order -
    which, on this control, it is.
    """
    return [g for g in dedupe_last(games) if int(g["game"]) < n]


def rung_wins(games: list[dict], side: str) -> tuple[int, int]:
    """(games the rung's side won, games scored). Unwinnable deals - no pack
    seated at dawn - leave the denominator, as they do in every other read."""
    scored = winnable(games)
    return sum(1 for g in scored if g["winner"] == side), len(scored)


def live_seats(game: dict, arm: str) -> set[int]:
    """The seats a model played in this deal, by DAWN TRUTH.

    The same rule `eval.run_changeling.build_policies` seats by, read off the
    record's own truth map rather than re-derived from belief: a seat plays for
    the card in front of it at dawn whether or not it knows.
    """
    want = Side(ARMS[arm]["live_side"])
    return {int(seat) for seat, key in game["truth"].items()
            if CARDS[key].side is want}


def live_fallback(games: list[dict], arm: str) -> tuple[int, int]:
    """(fallbacks, decisions) at the LIVE seats only - the criterion's bar.

    The run-level rate is diluted by rung seats that never fall back, and the
    dilution varies with the deal because the live-seat count does.
    """
    fell = total = 0
    for game in games:
        live = live_seats(game, arm)
        for row in game.get("decision_log") or ():
            if int(row["seat"]) in live:
                total += 1
                fell += bool(row.get("fell_back"))
    return fell, total


def live_fallback_rate(games: list[dict], arm: str) -> float | None:
    fell, total = live_fallback(games, arm)
    return fell / total if total else None


def verdict(arm: Arm, ctrl: Arm, name: str) -> Verdict:
    """The call on one arm, voids first, exactly as the criterion ordered them.

    ``ctrl`` is expected to be the RESCORED control - ``report`` slices it, and
    a caller that hands the whole 1000-game record gets a wrong denominator
    rather than an error, which is what ``control_slice`` and its tests are for.
    """
    side = ARMS[name]["rung_side"]
    ha, na = rung_wins(arm.games, side)
    hc, nc = rung_wins(ctrl.games, side)
    interval = newcombe(hc, nc, ha, na) if na and nc else None
    diff = None if not na or not nc else ha / na - hc / nc

    reasons: list[str] = []
    rate = live_fallback_rate(arm.games, name)
    if rate is not None and rate > integrity.VOID_BAR:
        reasons.append(f"{arm.name}: live-side fallback {rate:.2%} above "
                       f"{integrity.VOID_BAR:.0%}")
    if reasons:
        return Verdict("VOID", tuple(reasons), diff, interval, None)

    for label, n in ((arm.name, na), (f"{CONTROL_STEM} rescored", nc)):
        if n < SCORED_FLOOR:
            reasons.append(f"{label}: {n} scored games, under {SCORED_FLOOR}")
    if reasons or interval is None:
        return Verdict("REFUSED",
                       tuple(reasons) or ("an arm scored no games",),
                       diff, interval, None)

    informs = _excludes_zero(interval)
    return Verdict("INFORMS" if informs else "NOT SHOWN",
                   (f"Newcombe interval {'excludes' if informs else 'includes'}"
                    " zero",), diff, interval, None)


def _rescored(ctrl: Arm) -> Arm:
    return Arm(name=f"{CONTROL_STEM} first {CONTROL_GAMES}",
               games=control_slice(ctrl.games),
               fallback_rate=ctrl.fallback_rate,
               recovered_rate=ctrl.recovered_rate)


def _one(records: Path, name: str, ctrl: Arm) -> int:
    spec = ARMS[name]
    path = records / f"{spec['stem']}.json"
    if not path.exists():
        print(f"\n== {name}: no record at {path} - a missing arm is a lost "
              "pair, not half a result")
        return 3
    with open(path, encoding="utf-8") as fh:
        args = json.load(fh)["args"]
    arm = load(path)
    side = spec["rung_side"]

    print(f"\n== {name} - the rung plays {side.upper()}, the model plays "
          f"{spec['live_side']}")

    print("   settings pin - the record's own args against the criterion")
    voids = settings_voids(args, name)
    print(f"      {'matches' if not voids else 'VOIDED'}")
    for v in voids:
        print(f"      {v}")

    print("   read the fallback rate FIRST, and read the LIVE side's own")
    fell, total = live_fallback(arm.games, name)
    rate = live_fallback_rate(arm.games, name)
    shown = "no live decisions" if rate is None else f"{rate:.2%}"
    flag = (" RECOVERED FLAGGED"
            if arm.recovered_rate > integrity.RECOVERED_WARN_BAR else "")
    print(f"      live side  {fell}/{total} = {shown}   <- the bar is on this")
    print(f"      run level  {arm.fallback_rate:.2%}  reported, never the bar; "
          f"recovered {arm.recovered_rate:.2%}{flag}")

    v = verdict(arm, ctrl, name)
    ha, na = rung_wins(arm.games, side)
    hc, nc = rung_wins(ctrl.games, side)
    print(f"   the primary - the rung's {side} win rate")
    print(f"      against live seats  {ha}/{na} = {ha / na:.2%}  Wilson "
          f"{_ci(wilson(ha, na))}" if na else "      against live seats refused")
    print(f"      against its twin    {hc}/{nc} = {hc / nc:.2%}  Wilson "
          f"{_ci(wilson(hc, nc))}   <- {ctrl.name}" if nc
          else "      against its twin refused")
    print(f"      published at 1000 games {spec['published']:.2%} - the "
          "wider-interval reference, never the pair")
    print(f"      difference (live minus twin) {v.diff:+.2%}"
          if v.diff is not None else "      difference refused")
    print(f"      Newcombe 95%  {_ci(v.newcombe)}   <- the interval the "
          "criterion names")

    if spec["secondary"]:
        print("   the secondary - the rung's blind villager accuracy, the "
              "artifact read")
        hits, k = arm.blind
        ch, ck = ctrl.blind
        point = f"{hits / k:.2%}" if k else "refused"
        print(f"      against live seats  {hits}/{k} = {point}  Wilson "
              f"{_ci(wilson(hits, k))}")
        print(f"      against its twin    {ch}/{ck} = "
              f"{ch / ck:.2%}  Wilson {_ci(wilson(ch, ck))}" if ck
              else "      against its twin refused")
        print(f"      published: {PUBLISHED_BLIND:.2%} all-heuristic at 1000 "
              f"games, {PUBLISHED_BLIND_VS_RANDOM:.2%} the rung's village "
              "against a RANDOM pack")
        print("      the gap between that 77.36% and this is the silence tier's "
              "contribution, priced against seats that talk")
        if k < BLIND_FLOOR_VOTES:
            print(f"      REFUSED: {k} blind votes, under {BLIND_FLOOR_VOTES}. "
                  "The primary is a win rate and is untouched.")
        print(f"      the gate #3 reference is {REFERENCE_CHANCE:.2%}; this "
              "file makes no gate #3 call, its criterion did not name one")

    print("   free read, gating nothing - the tier census: NOT PAYABLE from "
          "this record")
    print("      `HeuristicPolicy._vote` returns a seat, not the rung it fired "
          "on, and the vote row carries no tier. Re-deriving the ladder here "
          "would be a second copy of the policy - the drift this file avoids "
          "everywhere else by importing. It needs one field at the source.")

    for r in v.reasons:
        print(f"      {r}")
    call = (v.call if not voids
            else f"VOID (settings) - the arithmetic read {v.call}")
    print(f"   -> {call}")
    return 0 if not voids and v.call in ("INFORMS", "NOT SHOWN") else 3


def report(records: Path) -> int:
    path = records / f"{CONTROL_STEM}.json"
    whole = load(path)
    with open(path, encoding="utf-8") as fh:
        summary = json.load(fh)["score"]

    print("== the control, RESCORED - not the published 1000-game figure")
    recovered = dedupe_last(whole.games)
    if len(recovered) != len(whole.games):
        print(f"   {len(whole.games)} records for {len(recovered)} game "
              f"indices - the JSONL is APPENDED and this record was written "
              f"more than once. Keeping the last write of each game.")
    voids = summary_voids(recovered, summary)
    for v in voids:
        print(f"   VOID: {v}")
    if voids:
        print("   the recovered run does not reproduce the figures published "
              "from it, so there is no control to pair against")
        return 3
    print("   recovered run reproduces the summary it was published from: "
          f"{summary['games_scored']} scored, "
          f"{summary['gate2_deception']['village_wins']} village wins")

    ctrl = _rescored(whole)
    print(f"   {ctrl.name}: {len(ctrl.games)} games, "
          f"{len(ctrl.scored)} scored, fallback {ctrl.fallback_rate:.2%}")
    print("   the rung has no model in it, so its fallback rate is a property "
          "of the driver, not of a tier")

    codes = [_one(records, name, ctrl) for name in ARMS]
    return 0 if codes and all(c == 0 for c in codes) else 3


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return report(Path(args[0]) if args else Path("eval/records"))


if __name__ == "__main__":
    sys.exit(main())
