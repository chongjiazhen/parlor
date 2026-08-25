"""Run N games and score gates #2 and #3.

    python -m eval.run_games --games 20 --backend clean --model gpt-oss-120b
    python -m eval.run_games --games 200 --arm random          # the chance baseline
    python -m eval.run_games --games 20 --arm llm-good --backend clean --model gpt-oss-120b
    python -m eval.run_games --games 6 --backend local --model rocinante-x-12b-heretic-q4

Four arms, because ``llm`` on both sides measures deduction and deception
entangled - good failing to deduce and evil deceiving well look identical in the
numbers. ``llm-good`` and ``llm-evil`` seat one side live against the random
control, so the live side's contribution is the only thing moving. Note which
seats each half of gate #3 belongs to: the vote half is the GOOD seats, but the
hunt half is the hunter, who is EVIL. Only the full ``llm`` arm can carry gate #3
whole; a mixed arm carries one half and the report says which.

Route discipline follows the endpoint, not the flag: ``clean``/``gray`` are
parallel (freellmapi fans out), ``local`` is one model on one GPU and is forced
serial no matter what ``--workers`` says.

Two gates, and what would falsify each:

  #2 deception - evil's win rate is non-trivial. Evil wins by failing three
     missions, by stalling five proposals, or by naming the informant at the end.
     A rate at or near zero means the evil seats never lied convincingly (or
     refused to lie at all - check ``--arm random`` first, which shows what the
     rate looks like with no reasoning in the loop).

  #3 deduction - good play beats chance on two counts: good seats approve
     evil-carrying teams LESS than clean ones (delta > 0), and the hunter finds
     the informant more than 1 time in 3. Either at chance means the deduction is
     decorative.

Every number is reported next to the fallback rate that produced it. A fallback is
a decision no model could make legally within its retries, played at random
instead - so a run with a high fallback rate is measuring the random policy
wearing a model's name, and the summary says so out loud.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

from core.backends import ENDPOINTS, REGISTERS, Backend
from games.cabal import transcript
from games.cabal.player import GameRecord, LLMPolicy, RandomPolicy, play_game
from games.cabal.referee import CabalReferee
from games.cabal.roles import DEFAULT_THEME, THEMES, Team


def wilson(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval. Small-N proportions need their error bars visible or
    a 3-of-5 run reads as a result."""
    if total == 0:
        return (0.0, 0.0)
    p = hits / total
    d = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / d
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


#: which side runs on a model, per arm. The mixed arms exist because ``llm`` on
#: both sides measures deduction and deception entangled: good failing to deduce
#: and evil deceiving well produce the same numbers. Seat one side on the random
#: policy and the other side's contribution is the only thing left moving.
LIVE_TEAMS: dict[str, set] = {
    "random": set(),
    "llm": {Team.GOOD, Team.EVIL},
    "llm-good": {Team.GOOD},
    "llm-evil": {Team.EVIL},
}


def build_policies(ref: CabalReferee, args, rng: random.Random) -> dict:
    """Seat -> policy. Seats on the arm's live side get their own ``LLMPolicy``
    (each seat needs its own retry trace; a shared object would interleave
    ``last_fell_back``); everyone else plays the random control."""
    fallback = RandomPolicy(rng=rng)
    live = LIVE_TEAMS[args.arm] if args.backend else set()
    if not live:
        return {s: fallback for s in ref.assignment}
    backend = Backend.named(
        args.backend, args.model,
        api_key=os.environ.get("PARLOR_API_KEY") or os.environ.get("FREELLMAPI_KEY"),
        system_prompt=REGISTERS[getattr(args, "register", "character")],
        temperature=args.temperature,
        timeout=args.timeout,
        max_tokens=args.max_tokens,
    )
    return {
        s: (LLMPolicy(backend=backend, retries=args.retries, fallback=fallback)
            if ref.assignment[s].team in live else fallback)
        for s in ref.assignment
    }


def one_game(index: int, args) -> GameRecord:
    theme = THEMES[args.theme] if args.theme else DEFAULT_THEME
    seed = None if args.seed is None else args.seed + index
    rng = random.Random(seed)
    ref = CabalReferee.new(5, seed=seed, theme=theme, discussion_rounds=args.rounds)
    policies = build_policies(ref, args, rng)
    try:
        return play_game(ref, policies, max_turns=args.max_turns)
    except Exception as exc:                     # one bad game must not kill the run
        rec = GameRecord(assignment={s: r.key for s, r in ref.assignment.items()})
        rec.error = f"{type(exc).__name__}: {exc}"
        return rec


def progress_line(done: int, total: int, index: int, rec: GameRecord,
                  elapsed: float) -> str:
    """One finished game, as it finishes. A run prints nothing until the end
    otherwise, and the failure worth catching early - a provider throttling the
    whole run into the random fallback - is invisible in a summary that arrives
    twenty minutes late. Every game reports its own fallback share, so a 429 storm
    shows up as it starts rather than as a void verdict afterwards."""
    share = rec.fallbacks / rec.decisions if rec.decisions else 0.0
    eta = (elapsed / done) * (total - done) if done else 0.0
    line = (f"[{done}/{total}] game {index}: {rec.winner or 'no winner'}, "
            f"{rec.fallbacks}/{rec.decisions} fell back ({share:.0%}), "
            f"{elapsed / 60:.1f}m in, ~{eta / 60:.1f}m left")
    if rec.error:
        line += f"  ERROR {rec.error}"
    elif share > 0.10:
        line += "  <- above 10%: this game is mostly the random policy"
    return line


def run_games(args, workers: int, started: float) -> list[GameRecord]:
    """All N games, reporting each as it lands. Order is preserved regardless of
    completion order - a seeded run must produce the same records either way."""
    total = args.games
    records: list[GameRecord] = [None] * total          # type: ignore[list-item]
    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            pending = {pool.submit(one_game, i, args): i for i in range(total)}
            for done, future in enumerate(as_completed(pending), start=1):
                index = pending[future]
                records[index] = future.result()
                print(progress_line(done, total, index, records[index],
                                    time.time() - started), file=sys.stderr, flush=True)
    else:
        for index in range(total):
            records[index] = one_game(index, args)
            print(progress_line(index + 1, total, index, records[index],
                                time.time() - started), file=sys.stderr, flush=True)
    return records


def score(records: list[GameRecord]) -> dict:
    played = [r for r in records if r.error is None and r.winner]
    evil_wins = sum(1 for r in played if r.winner == "evil")

    # gate #2 - how evil won, when it did
    by_path = {"missions_failed": 0, "five_rejects": 0, "hunt_hit": 0}
    for r in played:
        if r.winner != "evil":
            continue
        if r.hunt and r.hunt["hit"]:
            by_path["hunt_hit"] += 1
        elif sum(1 for m in r.missions if not m) >= 3:
            by_path["missions_failed"] += 1
        else:
            by_path["five_rejects"] += 1

    # gate #3a - do GOOD seats approve tainted teams less than clean ones?
    tainted = [v for r in played for v in r.votes if not v.seat_is_evil and v.team_has_evil]
    clean = [v for r in played for v in r.votes if not v.seat_is_evil and not v.team_has_evil]
    appr_tainted = sum(1 for v in tainted if v.approved)
    appr_clean = sum(1 for v in clean if v.approved)
    p_tainted = appr_tainted / len(tainted) if tainted else 0.0
    p_clean = appr_clean / len(clean) if clean else 0.0

    # ...and the same question for the seats that were NOT handed the answer. A
    # seer rejecting a team the night named for it is acting on knowledge; only a
    # blind seat rejecting one is deducing. Averaged together, one informed seat
    # can carry a table that is otherwise voting at chance.
    blind_tainted = [v for v in tainted if not v.knew_evil_on_team]
    p_blind = (sum(1 for v in blind_tainted if v.approved) / len(blind_tainted)
               if blind_tainted else 0.0)

    # gate #3b - does the hunter beat 1-in-3?
    hunts = [r.hunt for r in played if r.hunt]
    hits = sum(1 for h in hunts if h["hit"])

    decisions = sum(r.decisions for r in records)
    fallbacks = sum(r.fallbacks for r in records)
    served: Counter = Counter()
    for r in records:
        served.update(r.upstreams or {})
    return {
        "games_requested": len(records),
        "games_completed": len(played),
        "errors": [r.error for r in records if r.error],
        "gate2_deception": {
            "evil_win_rate": evil_wins / len(played) if played else 0.0,
            "evil_wins": evil_wins,
            "ci95": wilson(evil_wins, len(played)),
            "by_path": by_path,
            "fails_played_total": sum(r.fails_played for r in played),
        },
        "gate3_deduction": {
            "good_approve_tainted": p_tainted,
            "good_approve_clean": p_clean,
            "discrimination": p_clean - p_tainted,
            "votes_tainted": len(tainted),
            "votes_clean": len(clean),
            "good_approve_tainted_blind": p_blind,
            "discrimination_blind": p_clean - p_blind,
            "votes_tainted_blind": len(blind_tainted),
            "hunter_accuracy": hits / len(hunts) if hunts else 0.0,
            "hunter_hits": hits,
            "hunts": len(hunts),
            "hunter_ci95": wilson(hits, len(hunts)),
            "hunter_baseline": 1 / 3,
        },
        "integrity": {
            "decisions": decisions,
            "fallbacks": fallbacks,
            "fallback_rate": fallbacks / decisions if decisions else 0.0,
            "upstreams": dict(served.most_common()),
            "trace_sample": _dedupe([line for r in records for line in r.trace_sample])[:6],
        },
    }


def _dedupe(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if line not in out:
            out.append(line)
    return out


def report(s: dict, args, elapsed: float) -> str:
    g2, g3, integ = s["gate2_deception"], s["gate3_deduction"], s["integrity"]
    fr = integ["fallback_rate"]
    lines = [
        f"=== {s['games_completed']}/{s['games_requested']} games "
        f"({args.arm} arm, backend={args.backend or 'none'}, model={args.model}, "
        f"{args.rounds} discussion round(s)) in {elapsed:.1f}s ===",
        "",
        "gate #2  deception",
        f"  evil win rate      {g2['evil_win_rate']:.2%}  "
        f"(95% CI {g2['ci95'][0]:.2%}-{g2['ci95'][1]:.2%}, n={s['games_completed']})",
        f"  by path            {g2['by_path']}",
        f"  fail cards played  {g2['fails_played_total']}",
        "",
        "gate #3  deduction",
        f"  good approve clean team    {g3['good_approve_clean']:.2%} "
        f"(n={g3['votes_clean']})",
        f"  good approve tainted team  {g3['good_approve_tainted']:.2%} "
        f"(n={g3['votes_tainted']})",
        f"  discrimination             {g3['discrimination']:+.2%}  "
        "(>0 means good seats smell the evil team)",
        f"  ...blind seats only        {g3['discrimination_blind']:+.2%} "
        f"(n={g3['votes_tainted_blind']} tainted votes by seats the night told "
        "nothing about that team - this half is deduction, the rest is a seer "
        "acting on what it was handed)",
        f"  hunter accuracy            {g3['hunter_accuracy']:.2%} "
        f"({g3['hunter_hits']}/{g3['hunts']}, 95% CI "
        f"{g3['hunter_ci95'][0]:.2%}-{g3['hunter_ci95'][1]:.2%}, chance 33.33%)",
        "",
        f"integrity  {integ['fallbacks']}/{integ['decisions']} decisions fell back "
        f"to random ({fr:.2%})",
    ]
    if fr > 0.10:
        lines.append("  WARNING: >10% of decisions were random. These numbers are "
                     "not a measurement of the model.")
    served = integ.get("upstreams") or {}
    if served:
        total = sum(served.values())
        mix = ", ".join(f"{name} {count / total:.0%}"
                        for name, count in list(served.items())[:6])
        lines.append(f"  served by  {mix}"
                     + (f" (+{len(served) - 6} more)" if len(served) > 6 else ""))
        if len(served) > 1:
            lines.append("  NOTE: more than one upstream answered - under a routing "
                         "alias these numbers are a MIX of models, not one model's "
                         "play. Pin a model before attributing a result to one.")
    if integ["trace_sample"]:
        lines.append("  why decisions were refused or retried:")
        lines += [f"    {line}" for line in integ["trace_sample"]]
    if s["errors"]:
        lines.append(f"  {len(s['errors'])} game(s) errored: {s['errors'][:3]}")
    # Which side a verdict is allowed to speak for is an ARM question before it is a
    # numbers question. Gate #3 straddles both: the vote half is the good seats
    # deducing, but the hunt half is the HUNTER - an evil seat - deducing. So the
    # mixed arms can each carry only one half of gate #3, and only the full llm arm
    # can carry the gate.
    live = LIVE_TEAMS[args.arm] if args.backend else set()
    good_is_live, evil_is_live = Team.GOOD in live, Team.EVIL in live
    n_3a = g3["discrimination"] > 0
    n_3b = g3["hunter_ci95"][0] > 1 / 3
    verdict_3a, verdict_3b = n_3a and good_is_live, n_3b and evil_is_live
    verdict_3 = verdict_3a and verdict_3b
    rate_ok = g2["ci95"][0] > 0.05
    lines += [
        "",
        f"gate #3 {'PASS' if verdict_3 else 'not shown'} - "
        f"vote discrimination {'>0' if n_3a else 'at/below 0'}, hunter "
        f"{'beats' if n_3b else 'does not beat'} chance at the CI floor",
    ]
    if not good_is_live:
        lines.append("  (good played at random in this arm, so the vote half is the "
                     "chance baseline, not a deduction claim)")
    if not evil_is_live:
        lines.append("  (the hunter is an EVIL seat and played at random in this "
                     "arm, so the hunt half is the 1-in-3 baseline)")
    # Gate #2 is conditional on gate #3, and that is not pedantry: against good
    # seats voting at chance, evil wins ~65% of the time with no deception at all
    # (measured, --arm random). An unconditioned evil win rate measures the
    # random baseline, so it cannot be evidence that deception works.
    if not evil_is_live:
        lines.append(
            f"gate #2 not shown - evil played at random in this arm, so its "
            f"{g2['evil_win_rate']:.2%} win rate is the baseline itself."
        )
    elif not verdict_3:
        lines.append(
            f"gate #2 not shown - evil win rate is {g2['evil_win_rate']:.2%}, but "
            "good is at chance, so evil wins without deceiving anyone. Gate #2 is "
            "only readable once gate #3 holds."
        )
    else:
        lines.append(
            f"gate #2 {'PASS' if rate_ok else 'not shown'} - against a good side "
            f"that demonstrably deduces, evil still takes "
            f"{g2['evil_win_rate']:.2%} (CI floor {g2['ci95'][0]:.2%})"
        )
    if fr > 0.10:
        lines.append("  (both verdicts void at this fallback rate)")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--arm", choices=list(LIVE_TEAMS), default="llm",
                    help="which side runs on the model: 'random' is the chance "
                         "baseline (no model calls), 'llm-good'/'llm-evil' seat one "
                         "side live against the random control")
    ap.add_argument("--backend", choices=list(ENDPOINTS))
    ap.add_argument("--model", default="auto")
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--register", choices=list(REGISTERS), default="character",
                    help="how players are told to speak: 'character' roleplays the "
                         "skin, 'plain' argues from the record out of character")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=1536,
                    help="raise for a model that reasons out loud before answering")
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--max-turns", type=int, default=400)
    ap.add_argument("--theme", choices=list(THEMES))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", help="write the full per-game records here as JSON")
    ap.add_argument("--transcript",
                    help="write ONE game as a readable markdown transcript here")
    ap.add_argument("--transcript-game", type=int, default=None,
                    help="which game to transcribe (default: the first completed one)")
    args = ap.parse_args()

    if LIVE_TEAMS[args.arm] and not args.backend:
        sys.exit(f"--arm {args.arm} needs --backend "
                 "(or run --arm random for the baseline)")

    workers = args.workers
    if not LIVE_TEAMS[args.arm] or not args.backend:
        workers = 1
    elif not ENDPOINTS[args.backend].parallel:
        workers = 1
        print(f"[{args.backend}] is serial (one model on one GPU) - forcing 1 worker",
              file=sys.stderr)

    started = time.time()
    records = run_games(args, workers, started)
    elapsed = time.time() - started

    s = score(records)
    print(report(s, args, elapsed))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"args": vars(args), "summary": s,
                       "games": [asdict(r) for r in records]}, fh, indent=2)
        print(f"\nwrote {args.out}")
    if args.transcript:
        if args.transcript_game is not None:
            index = args.transcript_game
        else:
            index = next((i for i, r in enumerate(records)
                          if r.error is None and r.winner), None)
        if index is None:
            print("\nno game completed - nothing to transcribe", file=sys.stderr)
        else:
            text = transcript.render(records[index], vars(args))
            print(f"\nwrote transcript of game {index} to "
                  f"{transcript.write(args.transcript, text)}")


if __name__ == "__main__":
    main()
