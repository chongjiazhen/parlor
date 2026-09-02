"""Mine a finished changeling run for votes that are dominated GIVEN WHAT THE SEAT
WAS SHOWN. The twin of ``audit_decisions`` for this rung. No GPU.

    py -3 -m eval.changeling_audit eval/records/s2.json.jsonl
    py -3 -m eval.changeling_audit eval/records/ctl-changeling-min2-20260902.json.jsonl --control

Not a judgement grader - the cabal auditor's docstring says why, and it holds
here twice over: this game's cards MOVE after a seat looks, so nothing a seat was
shown is proof at dawn. What is checkable is narrower and is still worth a number:
a vote that could only be right if a card the seat did not see moving DID move.
Two shapes, never pooled, each priced rather than blamed:

  - **shown-village** - a village seat was shown a seat's card and it was a
    village card (the spotter's look, the swapper's victim who now holds the
    swapper card, a kindred fellow), and it voted that seat anyway.
  - **partner** - a pack seat was told its fellow and voted the fellow. Voting the
    partner never beats voting anyone else: if the partner still holds pack the
    vote helps the village, and if the switcher moved the card the vote is a
    wasted draw at a seat the wolf KNOWS went to sleep as pack.

Each count carries a PRICE column: how often the dominated vote landed on a seat
holding pack at dawn anyway, because the cards moved. That is the cost of the
domination, not a defence of the vote - the seat did not know the card moved.

Both counts are read against a chance reference, the same count on the random
control record on the same rule, where every vote is uniform over the other
seats. ``--control`` is the instrument control: it refuses (exit 3) when a check
has an empty denominator, because the log parser found no reveal to score - a 0
from a parser that never fired is the failure the cabal auditor was rewritten
for, and nothing about the output would say so.

What a seat was shown is read from the record's referee-side ``log`` lines, which
``games/changeling/night.py`` writes in one format per act. A change to those
lines breaks ``test_changeling_audit`` before it breaks a number here.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys

from core.stats import wilson
from games.changeling.roles import CARDS, Side

REFUSED = 3

_MEET = re.compile(r"^meet: seat (\d+) \((\w+)\) sees (.+)$")
_LOOK = re.compile(r"^look: seat (\d+) sees seat (\d+) = (\w+)$")
_TAKE = re.compile(r"^take: seat (\d+) robs seat (\d+), now holds (\w+); "
                   r"seat \d+ holds (\w+) and is not told$")


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def reveals(game: dict) -> dict[int, list[tuple[int, str]]]:
    """What each seat was SHOWN about a seat, as (seat, label), in night order.

    Labels are card keys for a look or a take, and ``fellow-<kind>`` for a meet -
    the same labels the referee hands the seat. Centre looks reveal no seat and
    are dropped; a switch reveals a relation and no card, so it is dropped too;
    the waker's own-card reveal is about itself and cannot be voted.
    """
    out: dict[int, list[tuple[int, str]]] = {}
    for line in game.get("log", []):
        if m := _MEET.match(line):
            seat, kind, fellows = int(m[1]), m[2], m[3]
            seen = [] if fellows == "no one" else ast.literal_eval(fellows)
            out.setdefault(seat, []).extend((int(s), f"fellow-{kind}") for s in seen)
        elif m := _LOOK.match(line):
            out.setdefault(int(m[1]), []).append((int(m[2]), m[3]))
        elif m := _TAKE.match(line):
            seat, victim = int(m[1]), int(m[2])
            out.setdefault(seat, []).extend([(seat, m[3]), (victim, m[4])])
    return out


def _is_village(label: str) -> bool:
    key = label.removeprefix("fellow-")
    card = CARDS.get(key)
    return card is not None and card.side is Side.VILLAGE


def _count(games: list[dict], eligible, dominated) -> tuple[int, int, int, list[str]]:
    """(hits, denominator, priced, notes). ``eligible(voter, shown)`` says whether
    the vote is in the denominator; ``dominated(target, shown)`` whether it is a
    hit. ``priced`` is the hits whose target held pack at dawn regardless."""
    hits = total = priced = 0
    notes: list[str] = []
    for g in games:
        shown = reveals(g)
        for v in g.get("votes", []):
            voter, target = v["seat"], v["target"]
            mine = shown.get(voter, [])
            if not eligible(voter, mine):
                continue
            total += 1
            if dominated(target, mine):
                hits += 1
                if v.get("target_holds_pack"):
                    priced += 1
                notes.append(f"game {g.get('game', '?')}: seat {voter} was shown "
                             f"{[x for x in mine if x[0] == target]} and voted "
                             f"seat {target}"
                             + (" - which held pack at dawn anyway"
                                if v.get("target_holds_pack") else ""))
    return hits, total, priced, notes


def shown_village_votes(games: list[dict]) -> tuple[int, int, int, list[str]]:
    """A village seat voting a seat it was itself shown holding a village card."""
    def village_seats(voter, shown):
        return {s for s, label in shown if s != voter and _is_village(label)}
    return _count(games,
                  eligible=lambda voter, shown: bool(village_seats(voter, shown)),
                  dominated=lambda target, shown: any(
                      s == target and _is_village(label) for s, label in shown))


def partner_votes(games: list[dict]) -> tuple[int, int, int, list[str]]:
    """A pack seat voting the fellow it was told at the meet."""
    def fellows(shown):
        return {s for s, label in shown if label == "fellow-pack"}
    return _count(games,
                  eligible=lambda voter, shown: bool(fellows(shown)),
                  dominated=lambda target, shown: target in fellows(shown))


CHECKS = (("shown-village: a village seat voted a seat it was shown as village",
           shown_village_votes),
          ("partner: a pack seat voted the fellow it was told", partner_votes))


def _rate(hits: int, total: int) -> str:
    if not total:
        return "n/a"
    lo, hi = wilson(hits, total)
    return f"{hits / total:.2%} [{lo:.2%}, {hi:.2%}]"


def control(games: list[dict]) -> int:
    """Refuse a record on which a check found nothing to score."""
    blind = []
    for name, fn in CHECKS:
        hits, total, _, _ = fn(games)
        print(f"  {name}: {hits}/{total}")
        if not total:
            blind.append(name)
    if blind:
        print("\nREFUSED: the log parser found no reveal for: "
              + "; ".join(b.split(":")[0] for b in blind)
              + ". A 0 here is a property of the parser, not of the play.")
        return REFUSED
    print("\nBoth checks have a denominator on this record: a 0 in the hits "
          "column is a reading, not a blind spot.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("jsonl", help="per-game JSONL from a changeling run")
    ap.add_argument("--reference", help="a random-control JSONL on the same rule, "
                                        "read beside each count as its chance")
    ap.add_argument("--show", type=int, default=3, help="examples per check")
    ap.add_argument("--control", action="store_true",
                    help="instrument control: exit 3 if a check has nothing to score")
    args = ap.parse_args(argv)

    games = load(args.jsonl)
    print(f"{len(games)} games from {args.jsonl}\n")
    if args.control:
        return control(games)

    ref = load(args.reference) if args.reference else None
    print("== DOMINATED given what the seat was shown - priced, not blamed ==")
    for name, fn in CHECKS:
        hits, total, priced, notes = fn(games)
        line = f"  {name}: {hits}/{total} = {_rate(hits, total)}"
        if hits:
            line += f"; {priced}/{hits} landed on a seat holding pack at dawn anyway"
        print(line)
        if ref is not None:
            rh, rt, _, _ = fn(ref)
            print(f"      chance, the random control on the same rule: "
                  f"{rh}/{rt} = {_rate(rh, rt)}")
        for note in notes[:args.show]:
            print(f"      - {note}")
        if len(notes) > args.show:
            print(f"      ... {len(notes) - args.show} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
