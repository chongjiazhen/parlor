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
from core.runlog import RunState, run_with_marker
from core.stats import wilson
from games.cabal import transcript
from games.cabal.player import (GameRecord, LLMPolicy, RandomPolicy, VoteRecord,
                                play_game)
from games.cabal.referee import CabalReferee
from games.cabal.roles import DEFAULT_THEME, THEMES, Team


def _ci_text(ci, joiner: str = "-") -> str:
    """A CI, or a refusal. ``wilson`` returns None on an empty sample rather than a
    zero-width interval, so every render site has to say "no interval" instead of
    printing one that reads as a precise measurement of nothing."""
    return "no interval, n=0" if not ci else f"{ci[0]:.2%}{joiner}{ci[1]:.2%}"


def _ci_floor(ci) -> float | None:
    """The floor a verdict tests, or None when there is no interval. A caller must
    treat None as "not shown" - never as a floor of zero, which would let a gate
    pass or fail on an empty sample."""
    return None if not ci else ci[0]


def _blind_line(g3: dict) -> str:
    """The gate's own line. A missing stratum is REFUSED, never rendered as 0."""
    d, ci = g3["discrimination_blind"], g3.get("discrimination_blind_ci95")
    if d is None:
        return ("  DISCRIMINATION (blind)     REFUSED - no votes from seats the "
                "night told nothing (clean "
                f"n={g3.get('votes_clean_blind', 0)}, tainted "
                f"n={g3.get('votes_tainted_blind', 0)})")
    band = f"  95% CI [{ci[0]:+.2%}, {ci[1]:+.2%}]" if ci else "  (CI unavailable)"
    return (f"  discrimination, binary     {d:+.2%} "
            f"(n={g3['votes_clean_blind']} clean / {g3['votes_tainted_blind']} "
            f"tainted, same blind seats - superseded by the graded slope above, "
            f"which uses every taint level){band}")


def _graded_lines(g3: dict) -> str:
    """The graded gate, plus the dose-response table it is fitted to."""
    b = g3["strata"].get("none") or {}
    s, ci = b.get("taint_sensitivity"), b.get("taint_sensitivity_ci95")
    if s is None:
        return ("  TAINT SENSITIVITY (blind)  REFUSED - blind votes span fewer "
                "than two taint levels, so no slope is defined")
    band = f"  95% CI [{ci[0]:+.2%}, {ci[1]:+.2%}]" if ci else "  (CI unavailable)"
    rows = "  ".join(f"{k}:{h}/{n} ({h / n:.0%})"
                     for k, (h, n) in sorted(b.get("by_taint", {}).items()))
    return (f"  TAINT SENSITIVITY (blind)  {s:+.2%} per extra saboteur - THE GATE"
            f"{band}\n    approval by taint level  {rows}")


def _strata_lines(g3: dict) -> str:
    """Every stratum beside the gate, so the reader sees where the signal lives."""
    names = {"none": "none     (blind)", "aura": "aura     (pair only)",
             "identity": "identity (named)"}
    out = []
    for cls in ("none", "aura", "identity"):
        s = g3["strata"].get(cls) or {}
        d = s.get("discrimination")
        shown = f"{d:+.2%}" if d is not None else "n/a"
        out.append(f"    by knowledge: {names[cls]:<18}{shown:>9} "
                   f"(n={s.get('n_clean', 0)}/{s.get('n_tainted', 0)})")
    return "\n".join(out)


def taint_sensitivity(votes) -> tuple[float | None, dict[int, tuple[int, int]]]:
    """How much approval each ADDITIONAL saboteur on the team costs, plus the
    per-level table it is fitted to.

    The binary metric thresholds taint at 1, which throws away the 1-vs-2 contrast
    and caps precision on the thinnest cell - at 5 seats a clean team has P~0.18,
    so `p_clean` is always the scarce term. Grading fits the whole dose-response
    instead: ordinary least squares of approval on the evil count, sign-flipped so
    POSITIVE means the seat approves less as the team gets dirtier, matching the
    direction of the binary figure.

    It degenerates correctly: with only levels 0 and 1 present the slope IS the
    binary discrimination, so this generalises the old number rather than
    replacing it with something incomparable.

    The per-level table is returned because the slope alone hides
    non-monotonicity, and non-monotonicity is the interesting failure - a table
    that rises from 1 to 2 evils is not a weak deducer, it is a seat responding to
    something other than taint.
    """
    by_level: dict[int, tuple[int, int]] = {}
    for v in votes:
        hits, n = by_level.get(v.team_evil_count, (0, 0))
        by_level[v.team_evil_count] = (hits + bool(v.approved), n + 1)
    if len({v.team_evil_count for v in votes}) < 2:
        return None, by_level        # one level only: no slope is defined
    mean_t = sum(v.team_evil_count for v in votes) / len(votes)
    mean_y = sum(bool(v.approved) for v in votes) / len(votes)
    var = sum((v.team_evil_count - mean_t) ** 2 for v in votes)
    if var == 0:
        return None, by_level
    cov = sum((v.team_evil_count - mean_t) * (bool(v.approved) - mean_y)
              for v in votes)
    return -(cov / var), by_level


def bootstrap_taint_sensitivity(records, cls: str, resamples: int = 4000,
                                seed: int = 7) -> tuple[float, float] | None:
    """CI for the graded slope, resampling GAMES for the same clustering reason."""
    rng = random.Random(seed)
    n = len(records)
    if n == 0:
        return None
    out: list[float] = []
    for _ in range(resamples):
        pool = [v for _ in range(n)
                for v in records[rng.randrange(n)].votes
                if not v.seat_is_evil and v.knowledge_class == cls]
        if not pool:
            continue
        s, _ = taint_sensitivity(pool)
        if s is not None:
            out.append(s)
    if len(out) < resamples // 2:
        return None
    out.sort()
    return (out[int(0.025 * len(out))], out[int(0.975 * len(out))])


def bootstrap_discrimination(records, cls: str, resamples: int = 4000,
                             seed: int = 7) -> tuple[float, float] | None:
    """95% percentile CI for one stratum's discrimination, resampling GAMES.

    The clustering unit is the game: seats nest inside games (seat 3 of game 1
    shares nothing with seat 3 of game 2), so resampling game indices handles
    seat- and game-level correlation at once. Treating ~150 votes as independent
    Bernoulli overstates the evidence - at ~7.5 votes per game and modest
    within-game correlation the design effect is ~2x, which is the difference
    between an interval that clears zero and one that straddles it.

    Percentile bootstrap on 20 clusters is itself rough; its own coverage is
    approximate. It is the least-wrong option at this N, and the honest fix for
    the width is more games or a graded metric, not a narrower method.
    """
    rng = random.Random(seed)
    n = len(records)
    if n == 0:
        return None
    out: list[float] = []
    for _ in range(resamples):
        c_hits = c_n = t_hits = t_n = 0
        for _ in range(n):
            for v in records[rng.randrange(n)].votes:
                if v.seat_is_evil or v.knowledge_class != cls:
                    continue
                if v.team_has_evil:
                    t_n += 1
                    t_hits += v.approved
                else:
                    c_n += 1
                    c_hits += v.approved
        if c_n and t_n:
            out.append(c_hits / c_n - t_hits / t_n)
    if len(out) < resamples // 2:      # too many degenerate resamples to trust
        return None
    out.sort()
    return (out[int(0.025 * len(out))], out[int(0.975 * len(out))])


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


def build_policies(ref: CabalReferee, args, rng: random.Random,
                   seed: int | None = None) -> dict:
    """Seat -> policy. Seats on the arm's live side get their own ``LLMPolicy``
    (each seat needs its own retry trace; a shared object would interleave
    ``last_fell_back``); everyone else plays the random control.

    ``seed`` is this game's seed, and it is handed to the BACKEND as well as to the
    deal. That is the whole point: without it ``--seed`` fixed the roles and left
    the model sampling free, so a re-run was a different draw and every
    "same seeds, one variable" comparison was reading its variable against an
    unmeasured spread."""
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
        seed=seed,
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
    ref = CabalReferee.new(5, seed=seed, theme=theme, discussion_rounds=args.rounds,
                           simultaneous=getattr(args, "simultaneous", False),
                           notebook=getattr(args, "notebook", False))
    policies = build_policies(ref, args, rng, seed=seed)
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


#: What this run knows about itself, for the terminal marker. See `core/runlog.py`
#: for why the marker is written by the run rather than echoed by its wrapper.
RUN_STATE = RunState()


def land(index: int, rec: GameRecord, args) -> None:
    """Persist one finished game immediately.

    A 50-game run on a local reasoning model is a twelve-hour job, and until now
    NOTHING reached disk until the last game returned: a crash, a reboot, or an OOM
    at hour eleven threw away eleven hours of GPU. Each game now lands as a JSONL
    line the moment it finishes, and its transcript with it, so an interrupted run
    is still a dataset - one short of what was asked for, not empty.
    """
    if args.out:
        with open(f"{args.out}.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"game": index, **asdict(rec)}) + "\n")
    if getattr(args, "transcript_dir", None):
        os.makedirs(args.transcript_dir, exist_ok=True)
        transcript.write(os.path.join(args.transcript_dir, f"game-{index:03d}.md"),
                         transcript.render(rec, vars(args)))
    RUN_STATE.landed += 1


#: The fields the gate #3 strata are cut on. A record missing any of them is not
#: a worse record - it is one the scorer cannot read at all.
SCORER_VOTE_FIELDS = ("seat_is_evil", "team_has_evil", "knowledge_class",
                      "team_evil_count")


def assert_scoreable(path: str) -> None:
    """Read the FIRST landed game back off disk and score it, or abort the run.

    `hunt20` spent a full run and was then unscoreable: its JSONL predates
    ``knowledge_class`` and ``team_evil_count``, so the current ``score()`` cannot
    read it at all, and the numbers it contributed came from a hand reconstruction
    rather than from the scorer every other run used. Nothing announced that. On a
    local reasoning model the discovery lands six hours after the mistake, and the
    GPU-hours are already spent.

    The round trip is the thing that has to hold, so this asserts on the BYTES ON
    DISK rather than on the in-memory record they came from: ``land()`` writes and
    nothing in the run ever reads back, which is exactly the gap a record/scorer
    drift hides in. Cost is one game; it buys the other nineteen.
    """
    with open(path, encoding="utf-8") as fh:
        first = fh.readline()
    if not first.strip():
        raise RuntimeError(f"scoreability check: {path} landed no readable game")

    raw = json.loads(first)
    raw.pop("game", None)
    raw_votes = raw.pop("votes", [])

    missing = sorted({f for v in raw_votes for f in SCORER_VOTE_FIELDS if f not in v})
    if missing:
        raise RuntimeError(
            f"scoreability check FAILED on {path}: vote rows are missing {missing}. "
            "The current score() cannot stratify this run. Fix the record now - "
            "the remaining games would land just as unreadable.")

    try:
        rec = GameRecord(**raw, votes=[VoteRecord(**v) for v in raw_votes])
    except TypeError as exc:
        raise RuntimeError(
            f"scoreability check FAILED on {path}: the landed record does not "
            f"round-trip into GameRecord/VoteRecord ({exc}). Record and scorer "
            "have drifted apart.") from None

    if rec.error is not None or not rec.votes:
        return                      # nothing to stratify; the field check stands

    blind = score([rec])["gate3_deduction"]["strata"]["none"]
    if blind["n_clean"] + blind["n_tainted"] == 0:
        raise RuntimeError(
            f"scoreability check FAILED on {path}: the blind stratum is empty on a "
            "completed game, so THE GATE would be refused for every game this run "
            "lands. Check knowledge_class assignment before spending the rest.")


def run_games(args, workers: int, started: float) -> list[GameRecord]:
    """All N games, reporting each as it lands. Order is preserved regardless of
    completion order - a seeded run must produce the same records either way."""
    total = args.games
    records: list[GameRecord] = [None] * total          # type: ignore[list-item]

    checked = False

    def landed(done: int, index: int) -> None:
        nonlocal checked
        land(index, records[index], args)
        if not checked and args.out:
            assert_scoreable(f"{args.out}.jsonl")
            checked = True
        print(progress_line(done, total, index, records[index],
                            time.time() - started), file=sys.stderr, flush=True)

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            pending = {pool.submit(one_game, i, args): i for i in range(total)}
            for done, future in enumerate(as_completed(pending), start=1):
                index = pending[future]
                records[index] = future.result()
                landed(done, index)
    else:
        for index in range(total):
            records[index] = one_game(index, args)
            landed(index + 1, index)
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

    # ...and the same question for the seats the night told NOTHING. Both terms
    # come from that population, which the first version of this split got wrong:
    # it filtered only the TAINTED side, leaving p_clean carrying the seer's
    # clean-team certification (94.3% vs the loyalist's 73.6% on seed 1000). It
    # also counted the watcher as blind, though its aura pair certifies taint
    # outright on some team shapes. Re-scored on seed 1000, correcting both took
    # the figure from +13.57% to +2.53% - the whole gate had been the seer.
    strata = {}
    for cls in ("none", "aura", "identity"):
        c = [v for v in clean if v.knowledge_class == cls]
        t = [v for v in tainted if v.knowledge_class == cls]
        slope, levels = taint_sensitivity(c + t)
        strata[cls] = {
            "n_clean": len(c),
            "n_tainted": len(t),
            "discrimination": ((sum(1 for v in c if v.approved) / len(c)
                                - sum(1 for v in t if v.approved) / len(t))
                               if c and t else None),
            "ci95": bootstrap_discrimination(played, cls) if c and t else None,
            "taint_sensitivity": slope,
            "taint_sensitivity_ci95": (bootstrap_taint_sensitivity(played, cls)
                                       if slope is not None else None),
            # level -> (approvals, votes). The dose-response the slope is fitted to.
            "by_taint": {k: v for k, v in sorted(levels.items())},
        }
    blind = strata["none"]

    # gate #3b - does the hunter beat chance? Chance is DERIVED from the legal
    # target set each hunt actually faced, never hardcoded: `1/3` is right only at
    # 5 seats with a hunter that sees its ally. At 7p/3-evil the set is 4, and under
    # the blind-evil variant it is 4 at 5 seats too - and `RandomPolicy` and
    # `validate_hunt` both read that set from the referee, so they would silently
    # agree on the new denominator while a hardcoded bar kept grading against 1/3,
    # in the flattering direction.
    #
    # Averaged over hunts rather than assumed constant: nothing stops a setup from
    # varying it game to game. `None` when no hunt carries the field, which fails
    # the gate CLOSED - a record predating it cannot be graded against a chance
    # nobody wrote down, and inventing one is exactly the error being fixed.
    hunts = [r.hunt for r in played if r.hunt]
    hits = sum(1 for h in hunts if h["hit"])
    legal = [h["legal_targets"] for h in hunts
             if h.get("legal_targets")]
    hunter_baseline = sum(1 / k for k in legal) / len(legal) if legal else None

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
            "strata": strata,
            "taint_sensitivity_blind": blind["taint_sensitivity"],
            "taint_sensitivity_blind_ci95": blind["taint_sensitivity_ci95"],
            "discrimination_blind": blind["discrimination"],
            "discrimination_blind_ci95": blind["ci95"],
            "votes_tainted_blind": blind["n_tainted"],
            "votes_clean_blind": blind["n_clean"],
            "hunter_accuracy": hits / len(hunts) if hunts else 0.0,
            "hunter_hits": hits,
            "hunts": len(hunts),
            "hunter_ci95": wilson(hits, len(hunts)),
            "hunter_baseline": hunter_baseline,
            #: how many hunts contributed a legal-target count. Below `hunts` means
            #: some rows predate the field and the average speaks for a subset.
            "hunter_baseline_n": len(legal),
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
        f"(95% CI {_ci_text(g2['ci95'])}, n={s['games_completed']})",
        f"  by path            {g2['by_path']}",
        f"  fail cards played  {g2['fails_played_total']}",
        "",
        "gate #3  deduction",
        f"  good approve clean team    {g3['good_approve_clean']:.2%} "
        f"(n={g3['votes_clean']})",
        f"  good approve tainted team  {g3['good_approve_tainted']:.2%} "
        f"(n={g3['votes_tainted']})",
        # The BLIND number is the gate. It is the only one of the three free of
        # both biases the pooled figure carries: inflated by handed knowledge (a
        # seer rejecting a seat it was TOLD about is obeying a fact, not deducing)
        # and deflated by concealment (a seer that approves a tainted team to hide
        # from the hunter is playing well and scores as a bad deducer). Blind seats
        # have nothing handed and nothing to hide. Reporting the flattering pooled
        # number as the headline was the same class of error as quoting a result
        # without its fallback rate.
        _graded_lines(g3),
        _blind_line(g3),
        _strata_lines(g3),
        f"  ...pooled, all good seats  {g3['discrimination']:+.2%} "
        "(averages all three strata, so the seer carries it; kept visible because "
        "it is what earlier runs reported, not because it means anything)",
        f"  hunter accuracy            {g3['hunter_accuracy']:.2%} "
        f"({g3['hunter_hits']}/{g3['hunts']}, 95% CI "
        f"{_ci_text(g3['hunter_ci95'])}, chance "
        + (f"{g3['hunter_baseline']:.2%}" if g3.get("hunter_baseline") is not None
           else "UNRECORDED")
        + ")",
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
    # Graded on the blind stratum's CI FLOOR, not on a point estimate, and never
    # on a missing stratum. Three ways this used to be wrong, all fixed here:
    #   - pooled figure graded it, so one informed seat carried a chance table
    #   - a point estimate `> 0` is a sign test: +0.5% on 40 votes "passed",
    #     while gate #3b next door demanded a Wilson floor. Same bar now.
    #   - an absent stratum defaulted p to 0.0, so a run with no blind votes
    #     scored `p_clean - 0 > 0` and PASSED on no data. Refused now, and the
    #     refusal is distinguishable from a failure: a fail invites tuning, a
    #     refusal invites more data.
    # Graded, not binary. The binary figure thresholds taint at 1 and so is
    # precision-capped by the clean cell, which at 5 seats is the scarce one
    # (P(clean team) ~ 0.18). The slope uses every level. It degenerates to the
    # binary number when only two levels occur, so this is a strictly better
    # estimator of the same quantity, not a different claim.
    blind_ci = g3.get("taint_sensitivity_blind_ci95")
    n_3a = bool(blind_ci) and blind_ci[0] > 0
    a_refused = g3.get("taint_sensitivity_blind") is None
    # Same shape as 3a's refusal: a missing baseline is REFUSED, not defaulted. The
    # bar is `1/len(legal_targets)` as the hunt actually faced it, so a run that did
    # not record the set cannot be graded - and a default would grade it against
    # whichever chance the reader happened to assume.
    baseline_3b = g3.get("hunter_baseline")
    b_refused = baseline_3b is None
    floor_3b = _ci_floor(g3["hunter_ci95"])
    n_3b = (not b_refused and floor_3b is not None and floor_3b > baseline_3b)
    verdict_3a, verdict_3b = n_3a and good_is_live, n_3b and evil_is_live
    verdict_3 = verdict_3a and verdict_3b
    floor_2 = _ci_floor(g2["ci95"])
    rate_ok = floor_2 is not None and floor_2 > 0.05
    lines += [
        "",
        f"gate #3 {'PASS' if verdict_3 else 'not shown'} - "
        + ("blind-seat taint sensitivity REFUSED (no blind votes)" if a_refused
           else f"blind-seat taint-sensitivity CI floor {'clears 0' if n_3a else 'includes 0'}")
        + ", hunter "
        + ("baseline REFUSED (no legal-target count recorded)" if b_refused
           else f"{'beats' if n_3b else 'does not beat'} chance "
                f"({baseline_3b:.2%}) at the CI floor"),
    ]
    if not good_is_live:
        lines.append("  (good played at random in this arm, so the vote half is the "
                     "chance baseline, not a deduction claim)")
    if not evil_is_live:
        lines.append("  (the hunter is an EVIL seat and played at random in this "
                     "arm, so the hunt half IS the baseline"
                     + (f", {baseline_3b:.2%}" if not b_refused else "") + ")")
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
            f"{g2['evil_win_rate']:.2%} (CI floor {_ci_text(g2['ci95'])})"
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
    ap.add_argument("--simultaneous", action="store_true",
                    help="collect each discussion round against one board state and "
                         "publish it together - no seat sees its neighbours first")
    ap.add_argument("--notebook", action="store_true",
                    help="give each seat a private notebook it writes for itself and "
                         "reads back on every later turn (a measured change: same "
                         "seeds, one variable)")
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
    ap.add_argument("--transcript-dir",
                    help="write EVERY game as its own markdown transcript here, as "
                         "it finishes - the readable half of a long run")
    ap.add_argument("--transcript-game", type=int, default=None,
                    help="which game to transcribe (default: the first completed one)")
    args = ap.parse_args()
    RUN_STATE.requested = args.games

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
    sys.exit(run_with_marker(main, RUN_STATE))
