"""Read the solver arm against the random arm on the same seeds - S26.

    python -m eval.solver_control eval/records/solver-control-solver.json \
                                  eval/records/solver-control-random.json

An INSTRUMENT: it reads two finished records and runs no game. What it reads is
scoped by how ``SolverPolicy`` is built. The policy acts only on a VOTE it can
prove from the seat's entitled evidence, and hands every other decision to the same
random fallback the control arm plays, so the two arms differ on exactly the
decisions the solver proved and on nothing else - until the first such vote, after
which the shared random stream is read at an offset and the two games part ways.

So the read has three layers, and each is printed under its own denominator:

  1. the split - how many decisions the solver PROVED versus DEFERRED, beside the
     fallback rate the integrity block already carries. A deferred draw is not a
     fallback: nothing failed. Without the split the arm read as 0.00% random when
     most of it was.
  2. the outcome - good's win rate per arm with a Wilson interval, over the same
     seeds. Not a gate: the solver sits on EVERY seat, evil included, so this is
     not a good side against a control, it is a whole table of one policy.
  3. the paired stratum - the proved votes that fall BEFORE the two games diverge,
     where the random arm's vote on the same seat, same turn, same proposal is in
     the record. That is the only place "what the solver did versus what random
     did" is a like-for-like comparison. Everything after the divergence is a
     different game and is counted, not paired.

Refuses (exit 3) rather than reading a pair that is not one: different seeds,
different game counts, or an arm that is not the one its filename claims.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

from core.stats import wilson

REFUSED = 3


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _ci(hits: int, n: int) -> str:
    band = wilson(hits, n)
    if band is None:
        return "no interval, n=0"
    return f"{hits}/{n} = {hits / n:.2%} [{band[0]:.2%}, {band[1]:.2%}]"


def vote_line_positions(events: list) -> list[int]:
    """Indexes of the referee's vote-result lines, in order - one per vote round."""
    return [i for i, (kind, text) in enumerate(tuple(e) for e in events)
            if kind == "event" and text.startswith("vote on ")]


def pairable_rounds(solver_events: list, random_events: list) -> int:
    """How many leading vote rounds the two games share a board for.

    Round k is pairable when every public byte written BEFORE its result line is
    identical in both records: same proposals, same speech, same missions. The
    result line itself is allowed to differ - that is where a proved vote shows.
    Once a prefix differs the games are different games and nothing later pairs.
    """
    s_pos, r_pos = vote_line_positions(solver_events), vote_line_positions(random_events)
    s_ev = [tuple(e) for e in solver_events]
    r_ev = [tuple(e) for e in random_events]
    k = 0
    for sp, rp in zip(s_pos, r_pos):
        if sp != rp or s_ev[:sp] != r_ev[:rp]:
            break
        k += 1
    return k


def rounds_of(votes: list) -> list[list[dict]]:
    """Vote rows grouped by round, in the order the rounds happened."""
    by_turn: dict[int, list[dict]] = {}
    for v in votes:
        by_turn.setdefault(int(v["turn"]), []).append(v)
    return [by_turn[t] for t in sorted(by_turn)]


def read_pair(solver: dict, control: dict) -> dict:
    """Everything the report prints, as numbers. Both arguments are the ``.json``
    summaries ``run_cabal`` writes (``args`` + ``games``)."""
    s_args, r_args = solver["args"], control["args"]
    if s_args.get("arm") != "solver" or r_args.get("arm") != "random":
        raise SystemExit(f"REFUSED: arms are {s_args.get('arm')!r} and "
                         f"{r_args.get('arm')!r}; this reads solver against random")
    if s_args.get("seed") is None or s_args.get("seed") != r_args.get("seed"):
        raise SystemExit(f"REFUSED: seeds differ or are unpinned "
                         f"({s_args.get('seed')} vs {r_args.get('seed')}) - "
                         "not the same deals, so not a pair")
    s_games, r_games = solver["games"], control["games"]
    if len(s_games) != len(r_games):
        raise SystemExit(f"REFUSED: {len(s_games)} solver games against "
                         f"{len(r_games)} random games")

    out: dict = {"seed": s_args["seed"], "games": len(s_games)}

    # 1. the split, and the fallback rate beside it, per arm
    for name, games in (("solver", s_games), ("random", r_games)):
        decisions = sum(g["decisions"] for g in games)
        fallbacks = sum(g["fallbacks"] for g in games)
        mech = sum(g.get("solver_mechanical", 0) for g in games)
        deferred = sum(g.get("solver_deferred", 0) for g in games)
        out[name] = {
            "decisions": decisions, "fallbacks": fallbacks,
            "fallback_rate": fallbacks / decisions if decisions else None,
            "mechanical": mech, "deferred": deferred,
            "mechanical_share": mech / (mech + deferred) if mech + deferred else None,
            "errors": sum(1 for g in games if g.get("error")),
        }
    # who the proved votes belonged to - the tell question turns on this
    by_role: Counter = Counter()
    votes_total = 0
    for g in s_games:
        for d in g.get("decision_log", []):
            if d.get("phase") == "vote":
                votes_total += 1
                if d.get("solver") == "mechanical":
                    by_role[g["assignment"][str(d["seat"])]] += 1
    out["solver"]["mechanical_by_role"] = dict(by_role)
    out["solver"]["votes"] = votes_total

    # 2. outcomes on the same seeds
    for name, games in (("solver", s_games), ("random", r_games)):
        played = [g for g in games if not g.get("error") and g.get("winner")]
        good = sum(1 for g in played if g["winner"] == "good")
        paths: Counter = Counter()
        for g in played:
            if g["winner"] != "evil":
                continue
            if g.get("hunt") and g["hunt"].get("hit"):
                paths["hunt_hit"] += 1
            elif sum(1 for m in g.get("missions", []) if not m) >= 3:
                paths["missions_failed"] += 1
            else:
                paths["five_rejects"] += 1
        out[name].update({
            "played": len(played), "good_wins": good,
            "good_win_ci95": wilson(good, len(played)),
            "evil_by_path": dict(paths),
            "missions": sum(len(g.get("missions", [])) for g in played),
            "fails_played": sum(g.get("fails_played", 0) for g in played),
        })
    identical = sum(1 for s, r in zip(s_games, r_games)
                    if s.get("public_events") == r.get("public_events"))
    out["games_identical"] = identical

    # 3. the paired stratum
    paired: list[dict] = []
    unpaired_mechanical = 0
    for s, r in zip(s_games, r_games):
        k = pairable_rounds(s.get("public_events", []), r.get("public_events", []))
        s_rounds, r_rounds = rounds_of(s.get("votes", [])), rounds_of(r.get("votes", []))
        mech_at = {(int(d["turn"]), int(d["seat"]))
                   for d in s.get("decision_log", [])
                   if d.get("phase") == "vote" and d.get("solver") == "mechanical"}
        for i, s_round in enumerate(s_rounds):
            r_by_seat = ({int(v["seat"]): v for v in r_rounds[i]}
                         if i < k and i < len(r_rounds) else {})
            for v in s_round:
                key = (int(v["turn"]), int(v["seat"]))
                if key not in mech_at:
                    continue
                rv = r_by_seat.get(key[1])
                if rv is None or int(rv["turn"]) != key[0]:
                    unpaired_mechanical += 1
                    continue
                paired.append({
                    "role": s["assignment"][str(v["seat"])],
                    "tainted": bool(v["team_has_evil"]),
                    "solver": bool(v["approved"]),
                    "random": bool(rv["approved"]),
                })
    stratum: dict = {"paired": len(paired), "unpaired": unpaired_mechanical}
    for label, rows in (("clean", [p for p in paired if not p["tainted"]]),
                        ("tainted", [p for p in paired if p["tainted"]])):
        stratum[label] = {
            "n": len(rows),
            "solver_approve": sum(p["solver"] for p in rows),
            "random_approve": sum(p["random"] for p in rows),
        }
    stratum["agree"] = sum(1 for p in paired if p["solver"] == p["random"])
    stratum["by_role"] = dict(Counter(p["role"] for p in paired))
    out["stratum"] = stratum
    return out


def render(r: dict) -> str:
    s, c, st = r["solver"], r["random"], r["stratum"]
    lines = [
        f"solver control read - seed {r['seed']}, {r['games']} games per arm, "
        f"backend none",
        "",
        "split (solver arm)",
        f"  {s['mechanical']}/{s['decisions']} decisions proved mechanically "
        f"({s['mechanical_share']:.2%}), {s['deferred']} deferred to random"
        if s["mechanical_share"] is not None else
        "  REFUSED - no decision carries a split; this record predates S26",
        f"  proved votes by role   {s['mechanical_by_role']}  "
        f"(of {s['votes']} votes in the arm)",
        f"  fallback, solver arm   {s['fallbacks']}/{s['decisions']} "
        f"= {s['fallback_rate']:.2%}" if s["fallback_rate"] is not None else
        "  fallback, solver arm   no decisions",
        f"  fallback, random arm   {c['fallbacks']}/{c['decisions']} "
        f"= {c['fallback_rate']:.2%}" if c["fallback_rate"] is not None else
        "  fallback, random arm   no decisions",
        "",
        "outcome on the same seeds (NOT a gate: the solver sits on every seat)",
        f"  good wins, solver arm  {_ci(s['good_wins'], s['played'])}",
        f"  good wins, random arm  {_ci(c['good_wins'], c['played'])}",
        f"  evil by path, solver   {s['evil_by_path']}",
        f"  evil by path, random   {c['evil_by_path']}",
        f"  missions / fail cards  solver {s['missions']} / {s['fails_played']}, "
        f"random {c['missions']} / {c['fails_played']}",
        f"  games byte-identical across arms  {r['games_identical']}/{r['games']}",
        "",
        "paired stratum - proved votes BEFORE the games diverge",
        f"  paired {st['paired']}, unpaired (after divergence) {st['unpaired']}",
    ]
    for label in ("clean", "tainted"):
        cell = st[label]
        if cell["n"]:
            lines.append(
                f"  {label:<8} n={cell['n']:<4} solver approved "
                f"{cell['solver_approve']}/{cell['n']}, random approved "
                f"{_ci(cell['random_approve'], cell['n'])}")
        else:
            lines.append(f"  {label:<8} n=0    no interval")
    if st["paired"]:
        lines.append(f"  agreement solver==random  {_ci(st['agree'], st['paired'])}")
    lines.append(f"  paired votes by role      {st['by_role']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("solver", help="the --arm solver run's .json summary")
    ap.add_argument("random", help="the --arm random run's .json summary, same seed")
    ap.add_argument("--json", action="store_true", help="print the numbers as JSON")
    args = ap.parse_args(argv)
    try:
        r = read_pair(load(args.solver), load(args.random))
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return REFUSED
    print(json.dumps(r, indent=2) if args.json else render(r))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
