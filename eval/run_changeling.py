"""Run N changeling games and score deduction and deception.

    python -m eval.run_changeling --games 200 --arm random     # the chance baseline
    python -m eval.run_changeling --games 40 --backend local --model qwen36-35b-a3b-iq3

Two gates, and what would falsify each. They are the same two questions `cabal`
asks, put to a game where a seat can be wrong about itself:

  #2 deception - the pack's win rate beats what it gets from villagers voting at
     random. As in `cabal`, this is only READABLE once #3 holds: villagers at chance
     hand the pack a high win rate with no deception in it at all.

  #3 deduction - villagers point at a seat holding `pack` more often than the
     measured baseline. Stratified by what the night told each seat, because a
     villager handed an identity is not deducing.

And one question `cabal` cannot ask at all, reported beside them: **do seats whose
belief diverged from their truth vote differently from seats whose did not?** A seat
playing the day as a wolf it no longer is has every incentive of a wolf and none of
the facts. Nothing here scores that as a gate; it is the observation the rung was
built to make possible.

Every number ships beside its fallback rate. A fallback is a decision no model made
legally within its retries, played at random - so a run with a high fallback rate is
measuring the random policy wearing a model's name, and the report says so.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import Counter
from dataclasses import asdict

from core import integrity
from core.backends import Backend, ENDPOINTS, REGISTERS, api_key_from_env, require_key
from core.runlog import RunState, record_paths, run_with_marker
from core.stats import bootstrap_ci, wilson
from eval.gate3_bar import REFERENCE_CHANCE
from games.changeling.player import (GameRecord, LLMPolicy, RandomPolicy,
                                     VoteRecord, play_game)
from games.changeling.referee import ChangelingReferee
from games.changeling.roles import DEFAULT_THEME, SETUPS, THEMES

#: Measured on this game at 5 seats with uniform random votes, n=4000, and on the
#: SAME denominator the report prints beside it: games that seated a wolf at dawn.
#:
#: The first value here was 0.385, which is the rate over ALL games including the
#: 2.7% that seat no wolf and cannot be won. Printing it next to a run figure scored
#: on winnable games only put a ~1.1 point bias in the pack's favour - quietly
#: averaging in the excluded games, in exactly the comparison RULES.md warns about.
#: Found by review 2026-08-27; on the scored denominator it is 39.51%.
#:
#: A REFERENCE POINT, never the thing a run is scored against - a run reports its
#: own random arm or it reports nothing.
MEASURED_RANDOM_VILLAGE_WINS = 0.3951
MEASURED_RANDOM_VILLAGE_WINS_ALL_GAMES = 0.3845

ARMS = ("random", "llm", "llm-village", "llm-pack")


def build_backend(args, seed: int | None) -> Backend:
    """``seed`` is the GAME's seed, never the run's base.

    `2cfe9d5` landed this invariant for cabal and AGENTS.md records it: "Backend.seed
    rides in the payload and one_game hands each game the number it deals with."
    This lane shipped `seed=args.seed`, which pinned the sampler to one value for
    every game in a run while the deal advanced - so cross-game variation came only
    from the prompt, and the spread the invariant exists to make measurable was
    collapsed silently. Found by review 2026-08-27.
    """
    return Backend(
        endpoint=ENDPOINTS[args.backend],
        model=args.model,
        api_key=api_key_from_env(),
        system_prompt=REGISTERS[args.register],
        temperature=args.temperature,
        timeout=args.timeout,
        max_tokens=args.max_tokens,
        seed=seed,
        enable_thinking=(False if args.no_thinking else None),
    )


def build_policies(ref: ChangelingReferee, args, rng: random.Random,
                   seed: int | None = None) -> dict:
    """Which seats are live. A mixed arm seats one side live against the random
    control, so the live side's contribution is the only thing moving.

    Seated by DAWN TRUTH, which is the only defensible reading: a seat wins with the
    card in front of it, so that is the side it is playing for whether or not it
    knows. Seating by belief would put a seat in the `llm-pack` arm on the strength
    of a card it no longer holds.
    """
    if args.arm == "random":
        return {s: RandomPolicy(rng) for s in range(ref.n)}
    backend = build_backend(args, seed)

    # One LLMPolicy PER SEAT. Sharing one object across seats makes `upstreams` a
    # single Counter that the record then sums once per seat, multiplying the
    # census by the live-seat count - and in a mixed arm that count varies with the
    # deal, so the reported model mix gets weighted by seats rather than by calls.
    def live() -> LLMPolicy:
        return LLMPolicy(backend=backend, retries=args.retries,
                         fallback=RandomPolicy(rng))

    if args.arm == "llm":
        return {s: live() for s in range(ref.n)}
    from games.changeling.roles import Side
    want = Side.PACK if args.arm == "llm-pack" else Side.VILLAGE
    return {s: (live() if ref.holds(s).side is want else RandomPolicy(rng))
            for s in range(ref.n)}


def one_game(index: int, args) -> GameRecord:
    theme = THEMES[args.theme] if args.theme else DEFAULT_THEME
    seed = None if args.seed is None else args.seed + index
    rng = random.Random(seed)
    ref = ChangelingReferee.new(args.seats, seed=seed, theme=theme,
                                discussion_rounds=args.rounds)
    try:
        return play_game(ref, build_policies(ref, args, rng, seed))
    except AssertionError:
        raise                                    # a leak is never scoreable
    except Exception as exc:                     # one bad game must not kill a run
        rec = GameRecord(theme=theme.name)
        rec.error = f"{type(exc).__name__}: {exc}"
        return rec


# ---- scoring --------------------------------------------------------------

def dawn_wolves(rec: GameRecord) -> int:
    return sum(1 for k in rec.truth.values() if k == "pack")


def villager_votes(rec: GameRecord) -> list[VoteRecord]:
    """Votes cast by seats that HOLD a village card at dawn. Those are the seats
    trying to find a wolf; a wolf's vote is a different act entirely."""
    return [v for v in rec.votes if not v.voter_holds_pack]


def _accuracy(games: list[GameRecord], keep=lambda v: True) -> float | None:
    hits = total = 0
    for rec in games:
        for v in villager_votes(rec):
            if keep(v):
                total += 1
                hits += v.target_holds_pack
    return hits / total if total else None


def score(records: list[GameRecord], seats: int = 5) -> dict:
    """``seats`` rides in the score because ``_chance`` needs it and gets only this
    dict. It DEFAULTS TO 5 rather than being required: every record written before
    2026-09-02 was a five-seat game and carries no such key, and `eval.s5_verdict`
    still reads S2's. A default that matched the new deck would silently rescore
    every old record against the wrong table."""
    played = [r for r in records if r.error is None and r.winner]

    # Games with no wolf seated at dawn are unwinnable by the village however well
    # it plays - RULES.md measures the residual at 2.8%. They are excluded from the
    # deduction denominator and REPORTED, the way a fallback is.
    winnable = [r for r in played if dawn_wolves(r) > 0]
    unwinnable = len(played) - len(winnable)

    village_wins = sum(1 for r in winnable if r.winner == "village")
    by_wolves: dict[int, tuple[int, int]] = {}
    for rec in played:
        w = dawn_wolves(rec)
        hits, n = by_wolves.get(w, (0, 0))
        by_wolves[w] = (hits + (rec.winner == "village"), n + 1)

    strata = {}
    for cls in ("identity", "positional", "false", "none"):
        acc = _accuracy(winnable, lambda v, c=cls: v.knowledge_class == c)
        n = sum(1 for r in winnable for v in villager_votes(r)
                if v.knowledge_class == cls)
        strata[cls] = {
            "accuracy": acc,
            "votes": n,
            "ci95": bootstrap_ci(
                winnable,
                lambda s, c=cls: _accuracy(s, lambda v: v.knowledge_class == c),
            ) if n else None,
        }

    # The question `cabal` cannot ask. Not a gate - an observation.
    diverged = {
        "accuracy_diverged": _accuracy(winnable, lambda v: v.voter_diverged),
        "accuracy_intact": _accuracy(winnable, lambda v: not v.voter_diverged),
        "votes_diverged": sum(1 for r in winnable for v in villager_votes(r)
                              if v.voter_diverged),
        "votes_intact": sum(1 for r in winnable for v in villager_votes(r)
                            if not v.voter_diverged),
    }
    # Seats that believe they are pack while holding village. They play the day for
    # the wrong side and win with the right one.
    sleepers = [v for r in winnable for v in r.votes
                if v.voter_believes_pack and not v.voter_holds_pack]
    diverged["sleeper_votes"] = len(sleepers)
    diverged["sleeper_accuracy"] = (
        sum(v.target_holds_pack for v in sleepers) / len(sleepers)
        if sleepers else None)

    blind = strata["none"]
    return {
        "seats": seats,
        "games_requested": len(records),
        "games_completed": len(played),
        "games_scored": len(winnable),
        "games_unwinnable": unwinnable,
        "errors": [r.error for r in records if r.error],
        "gate2_deception": {
            "pack_win_rate": (1 - village_wins / len(winnable)) if winnable else 0.0,
            "village_wins": village_wins,
            "ci95": wilson(len(winnable) - village_wins, len(winnable)),
            "reference_random_village_wins": MEASURED_RANDOM_VILLAGE_WINS,
        },
        "gate3_deduction": {
            "village_win_rate": village_wins / len(winnable) if winnable else 0.0,
            "village_win_ci95": wilson(village_wins, len(winnable)),
            "by_dawn_wolves": {k: v for k, v in sorted(by_wolves.items())},
            "villager_accuracy": _accuracy(winnable),
            "villager_accuracy_ci95": bootstrap_ci(winnable, _accuracy),
            "blind_accuracy": blind["accuracy"],
            "blind_accuracy_ci95": blind["ci95"],
            "blind_votes": blind["votes"],
            "strata": strata,
        },
        "belief": diverged,
        # Shared with cabal since S9. The trace-line list moved from the key
        # ``refusals`` to ``trace_sample``, cabal's name for it: S9 gives
        # "refusals" a numeric meaning, and one key over a count and a list of
        # strings is how a JSONL reader ends up summing sentences.
        "integrity": integrity.summarise(records),
    }


def _pct(value, width: int = 0) -> str:
    return "n/a".rjust(width) if value is None else f"{value:.2%}".rjust(width)


def _band(ci) -> str:
    return f"  95% CI [{ci[0]:.2%}, {ci[1]:.2%}]" if ci else "  (CI unavailable)"


def report(s: dict, args, elapsed: float) -> str:
    g2, g3, b, i = (s["gate2_deception"], s["gate3_deduction"], s["belief"],
                    s["integrity"])
    out = [f"=== {s['games_completed']}/{s['games_requested']} games "
           f"({args.arm} arm, backend={args.backend or 'none'}, "
           f"model={args.model}, {args.rounds} round(s)) in {elapsed:.1f}s ===", ""]

    if s["games_unwinnable"]:
        out.append(f"excluded  {s['games_unwinnable']} game(s) seated no pack at "
                   f"dawn and the village cannot win them; scored on "
                   f"{s['games_scored']}")
        out.append("")

    out += ["gate #2  deception",
            f"  pack win rate      {g2['pack_win_rate']:.2%}"
            f"{_band(g2['ci95'])}",
            f"  random reference   pack takes "
            f"{1 - g2['reference_random_village_wins']:.2%} against villagers "
            f"voting at random (n=4000, RULES.md)", ""]

    out += ["gate #3  deduction",
            f"  village win rate   {g3['village_win_rate']:.2%}"
            f"{_band(g3['village_win_ci95'])}",
            "    by dawn wolves   " + "  ".join(
                f"{k}:{h}/{n} ({h / n:.0%})"
                for k, (h, n) in g3["by_dawn_wolves"].items()),
            f"  villager accuracy  {_pct(g3['villager_accuracy'])}"
            f"{_band(g3['villager_accuracy_ci95'])}"]
    if g3["blind_accuracy"] is None:
        out.append("  BLIND ACCURACY     REFUSED - no votes from seats the night "
                   "told nothing")
    else:
        out.append(f"  BLIND ACCURACY     {_pct(g3['blind_accuracy'])} - THE GATE"
                   f"{_band(g3['blind_accuracy_ci95'])}  (n={g3['blind_votes']})")
    for cls in ("identity", "positional", "false", "none"):
        st = g3["strata"][cls]
        out.append(f"    by knowledge: {cls:<11}{_pct(st['accuracy'], 8)} "
                   f"(n={st['votes']})")
    out.append("")

    out += ["belief vs truth  (observation, not a gate)",
            f"  villagers whose belief diverged  {_pct(b['accuracy_diverged'])} "
            f"(n={b['votes_diverged']})",
            f"  villagers whose belief held      {_pct(b['accuracy_intact'])} "
            f"(n={b['votes_intact']})",
            f"  seats that believed pack, held village  "
            f"{_pct(b['sleeper_accuracy'])} (n={b['sleeper_votes']})", ""]

    rate = i["fallback_rate"]
    out += integrity.report_lines(i)
    if i["upstreams"]:
        total = sum(i["upstreams"].values()) or 1
        out.append("  served by  " + ", ".join(
            f"{k} {v / total:.0%}" for k, v in i["upstreams"].items()))
    if i["trace_sample"]:
        out.append("  why decisions were refused or retried:")
        out += [f"    {line}" for line in i["trace_sample"]]
    out.append("")

    # Verdicts. Same discipline as cabal: a gate is not read off a random side, and
    # gate #2 is unreadable until gate #3 holds.
    if rate > integrity.VOID_BAR:
        out.append("VOID - more than 10% of decisions were random. These numbers "
                   "are the random policy wearing a model's name.")
        return "\n".join(out)

    ci = g3["blind_accuracy_ci95"]
    if args.arm == "random":
        out.append("gate #3 not shown - this IS the chance baseline, so its "
                   "accuracy is the number other runs are read against.")
        out.append("gate #2 not shown - the pack played at random too.")
        return "\n".join(out)
    # A RUN LOG CALLS NO GATE. It holds neither of the two things the arm-level
    # gate is cut on: the criterion's bar - `eval.gate3_bar`, the measured
    # `--arm random` reference with its own-arm clause - where this log has only
    # its own deal's derived chance, and a WILSON floor where the interval
    # published above is a bootstrap over games. Measured on the skin pair
    # 2026-09-02, the two bars were 35.84% and 36.47% on seed-identical deals and
    # a 35.90% floor landed between them, so the log's verdict and the
    # criterion's disagreed on the same records. Both bars are printed against
    # the floor and neither is selected, which is the discipline
    # `eval.s5_verdict` already applies.
    floor = ci[0] if ci else None
    out.append("gate #3 - REPORTED, NOT CALLED. The arm-level verdict belongs to "
               "the arm's own criterion, read from the record after the run.")
    if floor is None:
        out.append("  no blind interval, so there is nothing to read against a "
                   "bar - see BLIND ACCURACY above.")
    else:
        for bar, label in ((REFERENCE_CHANCE,
                            "the criterion's bar - measured --arm random n=4000, "
                            "with the own-arm clause (eval.gate3_bar)"),
                           (_chance(s),
                            "this run's OWN deal, derived from its dawn-wolf mix "
                            "- a diagnostic, never the gate's bar")):
            out.append(f"  {bar:.2%}  {label}")
            out.append(f"          bootstrap floor {floor:.2%} "
                       f"{'clears' if floor > bar else 'does NOT clear'} it")
        out.append("  and the criterion's word is WILSON - the interval above is "
                   "a bootstrap over games, so even the floor is the wrong one.")
    out.append(f"gate #2 - REPORTED, NOT CALLED, and conditional on gate #3: with "
               f"voting at chance the pack wins ~65% with no deception in it. "
               f"Pack win rate {g2['pack_win_rate']:.2%}, a rate with no verdict "
               f"in it.")
    return "\n".join(out)


def _chance(s: dict) -> float:
    """A villager pointing at random hits a wolf at (dawn wolves)/(other seats).

    Computed from the run's OWN mix of one- and two-wolf dawns rather than taken
    from a constant, because RULES.md measured that the baseline nearly doubles
    between them and a run does not control which it deals.
    """
    seats = s.get("seats", 5)
    total = weighted = 0
    for w, (_, n) in s["gate3_deduction"]["by_dawn_wolves"].items():
        # JSON has no integer keys, so a score dict READ BACK from a record hands
        # this loop "1" where the live one hands it 1. In-process the shipped path
        # never sees a string; a reader recomputing the bar off a written record -
        # which the waker criterion asks for by name - dies on the subtraction.
        w = int(w)
        if w == 0:
            continue
        # Weight by VILLAGER VOTES, not by games. The rate this gates is per-vote,
        # and a 2-wolf dawn contributes only 3 villager votes against a 1-wolf
        # dawn's 4 - so game-weighting set the bar ~1.8 points too high and made
        # gate #3 harder than chance. The instrument-control test cannot catch a
        # bias this size: at 300 games the blind CI is +/-7pp. Review, 2026-08-27.
        # Both factors are the TABLE's, not constants: a villager is one of
        # ``seats - w`` voters and may point at ``seats - 1`` others. Hardcoded 5
        # and 4 here would have returned SETUP_5's bar for a six-seat run - a
        # plausible number, wrong by ~5 points, with nothing raising.
        votes = n * (seats - w)
        weighted += votes * (w / (seats - 1))
        total += votes
    return weighted / total if total else 0.0


# ---- runner ---------------------------------------------------------------

#: What this run knows about itself, for the terminal marker. See `core/runlog.py`
#: for why the marker is written by the run rather than echoed by its wrapper.
RUN_STATE = RunState()


def land(index: int, rec: GameRecord, args) -> None:
    if args.out:
        with open(record_paths(args.out)[1], "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"game": index, **asdict(rec)}) + "\n")
    RUN_STATE.landed += 1


def main() -> None:
    # Same trap `games/cabal/demo.py` hit and fixed in 320e322: a CJK skin cannot be
    # printed to the Windows console, whose default codec is cp1252. The run
    # completes, every render is correct, and the process dies at the moment of
    # writing the report out - which reads as a crash in the arena rather than a
    # fact about the terminal. Landed ahead of any CJK skin here, per queue.md, since
    # after the skin it is a debugging session instead of a line.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--arm", choices=ARMS, default="llm")
    ap.add_argument("--backend", choices=list(ENDPOINTS))
    ap.add_argument("--model", default="auto")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--register", choices=list(REGISTERS), default="character")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=1536)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--theme", choices=list(THEMES))
    ap.add_argument("--no-thinking", action="store_true",
                    help="ask the chat template to skip the model's reasoning "
                         "pass. A reasoning-distill model can fail to terminate "
                         "its reasoning and no token cap fixes that; see "
                         "core/backends.py. A MEASURED change, off by default.")
    ap.add_argument("--seats", type=int, default=5, choices=sorted(SETUPS),
                    help="which registered deck to deal - 5 is the shipped "
                         "SETUP_5 every recorded number was played on, 6 is the "
                         "waker deck, 7 is the kindred deck and has never been "
                         "run. A deck change re-baselines everything.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", help="write the full per-game records here as JSON")
    args = ap.parse_args()
    RUN_STATE.requested = args.games

    if args.arm != "random" and not args.backend:
        ap.error("a live arm needs --backend")

    # Refuse at the DOOR, never at game 200. An off-box route with no key does
    # not crash - it 401s every attempt, falls back on every decision, and
    # reports a number the scorer then voids after the GPU is spent.
    if args.backend:
        require_key(ENDPOINTS[args.backend], api_key_from_env())

    started = time.time()
    records: list[GameRecord] = []
    for index in range(args.games):
        rec = one_game(index, args)
        records.append(rec)
        land(index, rec, args)
        share = rec.fallbacks / rec.decisions if rec.decisions else 0.0
        line = (f"[{index + 1}/{args.games}] game {index}: "
                f"{rec.winner or 'no winner'}, {rec.fallbacks}/{rec.decisions} "
                f"fell back ({share:.0%}), "
                f"{(time.time() - started) / 60:.1f}m in")
        if rec.error:
            line += f"  ERROR {rec.error}"
        print(line, file=sys.stderr, flush=True)

    scored = score(records, seats=args.seats)
    print(report(scored, args, time.time() - started))
    if args.out:
        with open(record_paths(args.out)[0], "w", encoding="utf-8") as fh:
            json.dump({"score": scored, "args": vars(args)}, fh, indent=2)
        print(f"\nwrote {record_paths(args.out)[0]}")


if __name__ == "__main__":
    sys.exit(run_with_marker(main, RUN_STATE))
