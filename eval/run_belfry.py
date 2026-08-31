"""Run N games of belfry and score what can honestly be scored today.

    py -3 -m eval.run_belfry --games 200 --arm random --seats 5 --script compact
    py -3 -m eval.run_belfry --games 20 --arm llm --seats 5 --script compact \\
        --backend local --model qwen36-35b-a3b-iq3 --temperature 0.0 \\
        --seed 6100 --out eval/records/belfry-live1.json

**The headline is the execution, not the win.** A win on this rung is a long
chain - four or five days, a night kill each, a demon that can change hands - and
attributing it to any one decision is not something the record supports. What the
record does support is the day's one irreversible act: the table executed a seat,
and that seat was evil or it was not. Every execution carries the board it
happened on (``alive_before``, ``evil_before``), so the chance rate is computed
per execution rather than assumed, and the comparison is against what a table
picking uniformly at random from the living would have hit.

**Two denominators, and the second one is the honest primary.** The pooled
execution figure is subject to a stopping rule: executing the demon ENDS the game,
so a table that guesses well generates fewer executions than a table that guesses
badly, and the pool is enriched in the mistakes by construction. The first-day
figure has exactly one execution per game and no stopping rule behind it, so it is
the comparison that means what it looks like. Both ship, and the caveat ships with
them.

**The stratum this rung exists for** is the vote split by whether the voter had
been told something false at the time it voted. That is the question no earlier
rung could ask: `cabal`'s reveals are true, `changeling`'s go stale but were true
when given, and here the referee states a falsehood on purpose. A model that plays
the same misled as clear either is not using its information or is not being
fooled by it, and the two look different in the accuracy gap.

**Serial by construction**, like `eval.run_quorum`: the first arms are local, one
model on one GPU, where a worker pool only queues. Add one when a cloud campaign
needs it, and not before - a knob no run has used is a knob no run has tested.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from dataclasses import asdict

from core import integrity
from core.backends import (Backend, ENDPOINTS, REGISTERS, api_key_from_env,
                           require_key)
from core.runlog import RunState, record_paths, run_with_marker
from core.stats import wilson
from games.belfry.adjudicator import ModelAdjudicator
from games.belfry.player import GameRecord, LLMPolicy, RandomPolicy, play_game
from games.belfry.referee import BelfryReferee
from games.belfry.roles import DEFAULT_SCRIPT, DISTRIBUTION, SCRIPTS, Align

ARMS = ("random", "llm", "llm-good", "llm-evil")

ADJUDICATOR_ARMS = ("random", "model")

ADJUDICATOR_SYSTEM_PROMPT = (
    "You are the referee for a hidden-role game. Choose exactly one option from "
    "the offered list. Reply as one JSON object with only the key `choice`.")


def build_adjudicator_backend(args, seed: int | None) -> Backend:
    """Build the setup referee independently of the players at the table."""
    return Backend(
        endpoint=ENDPOINTS[args.adjudicator_backend],
        model=args.adjudicator_model,
        api_key=api_key_from_env(),
        system_prompt=ADJUDICATOR_SYSTEM_PROMPT,
        temperature=0.0,
        timeout=args.timeout,
        max_tokens=args.max_tokens,
        seed=seed,
        enable_thinking=False,
    )


def build_adjudicator(args, seed: int | None) -> ModelAdjudicator | None:
    """Keep random discretion on the referee's deal RNG, or model it separately."""
    if args.adjudicator == "random":
        return None
    return ModelAdjudicator(build_adjudicator_backend(args, seed), random.Random(seed))

STATE = RunState()


def build_backend(args, seed: int | None) -> Backend:
    """``seed`` is the GAME's seed, never the run's base.

    The repo invariant: ``--seed`` seeds the SAMPLER as well as the deal, or it is
    not a seed. Passing ``args.seed`` here would pin the sampler to one value for
    every game in a run while the deal advanced, so cross-game variation would come
    from the prompt alone.
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


def build_policies(ref: BelfryReferee, args, rng: random.Random,
                   seed: int | None = None) -> dict:
    """Which seats are live. A mixed arm seats one side live against the random
    control, so the live side's contribution is the only thing moving.

    The sides are read off the grimoire, which is referee-side - and that is fine
    for the same reason the deal is: this is the harness deciding who is played by
    what, not a seat being told anything. Nothing here reaches a payload.
    """
    if args.arm == "random":
        return {s: RandomPolicy(rng=rng) for s in range(ref.n)}
    backend = build_backend(args, seed)

    # One LLMPolicy PER SEAT. Sharing one across seats makes ``upstreams`` a single
    # Counter the record then sums once per seat, multiplying the census by the
    # live-seat count.
    def live() -> LLMPolicy:
        return LLMPolicy(backend=backend, retries=args.retries,
                         fallback=RandomPolicy(rng=rng))

    if args.arm == "llm":
        return {s: live() for s in range(ref.n)}
    want = Align.EVIL if args.arm == "llm-evil" else Align.GOOD
    return {s: (live() if ref.grim.seat(s).align is want else RandomPolicy(rng=rng))
            for s in range(ref.n)}


def one_game(index: int, args) -> GameRecord:
    seed = None if args.seed is None else args.seed + index
    rng = integrity.policy_rng(seed)
    script = SCRIPTS[args.script] if args.script else DEFAULT_SCRIPT
    adjudicator = build_adjudicator(args, seed)
    ref = BelfryReferee.new(args.seats, seed=seed, script=script,
                            discussion_rounds=args.rounds,
                            max_days=args.max_days, adjudicator=adjudicator)
    try:
        return play_game(ref, build_policies(ref, args, rng, seed))
    except AssertionError:
        raise                                # a leak is never scoreable
    except Exception as exc:                 # one bad game must not kill a run
        rec = GameRecord(script=script.name, seats=args.seats)
        rec.error = f"{type(exc).__name__}: {exc}"
        return rec


# ---- scoring --------------------------------------------------------------

def _executions(records: list[GameRecord], day: int | None = None) -> dict:
    """Executions that killed somebody, against the chance rate on their own
    boards. A nomination can carry against a seat that is already dead - the day
    ends and nobody dies - and those are counted separately rather than folded in:
    a table that spent three days executing corpses is not a table that executed
    badly, it is a table that did not execute at all.

    An execution a TRIGGER fired is counted apart for the same reason, and it is
    the harder of the two to see. The trigger executes the nominator and only
    fires on a townsfolk one, so it is good with probability 1 - while the chance
    rate here prices it as a draw from the board. Pooled, they cost the day-1
    control 5.2 points on a 10-seat full script (measured 2026-08-29: 216 of 1105
    day-1 executions, 0 of them evil, z = -9.62 on their own baseline), which read
    as the random policy failing to hit chance and is instead a metric summing two
    different quantities. The vote-selected half lands on chance (§belfry, and
    ``docs/measurements.md``). The compact script has no such role, so no number
    measured on it moves."""
    every = [e for r in records for e in r.executions
             if day is None or e.day == day]
    live = [e for e in every if e.was_alive]
    voted = [e for e in live if e.by_vote]
    hits = sum(1 for e in voted if e.evil)
    chance = (sum(e.evil_before / e.alive_before for e in voted) / len(voted)
              if voted else None)
    return {
        "executions": len(every),
        "on_a_living_seat": len(live),
        "on_a_dead_seat": len(every) - len(live),
        # The accuracy denominator, and it is the voted half of the living half.
        "voted_up": len(voted),
        "by_trigger": len(live) - len(voted),
        "trigger_hits": sum(1 for e in live if not e.by_vote and e.evil),
        "hits": hits,
        "rate": hits / len(voted) if voted else None,
        "chance": chance,
        "ci95": wilson(hits, len(voted)) if voted else None,
    }


def _votes(votes: list, evil_voter: bool, misled=None) -> dict:
    """Vote accuracy for one side, on one stratum.

    "Correct" is side-relative and stated rather than assumed: a good seat is right
    to vote for executing an evil seat and against executing a good one, and an
    evil seat is right to do the opposite. The two degenerate policies ship beside
    it on the SAME denominator, because an accuracy figure with no floor under it
    is unreadable - a table that voted no to everything scores whatever share of
    nominees happened to be good.
    """
    rows = [v for v in votes if v.voter_evil is evil_voter
            and (misled is None or v.voter_misled is misled)]
    if not rows:
        return {"votes": 0, "accuracy": None, "ci95": None,
                "always_no": None, "always_yes": None}
    correct = sum(1 for v in rows
                  if (v.yes == v.nominee_evil) is not evil_voter)
    always_no = sum(1 for v in rows if (not v.nominee_evil) is not evil_voter)
    return {
        "votes": len(rows),
        "accuracy": correct / len(rows),
        "ci95": wilson(correct, len(rows)),
        "always_no": always_no / len(rows),
        "always_yes": 1 - always_no / len(rows),
    }


def score(records: list[GameRecord]) -> dict:
    played = [r for r in records if r.error is None]
    all_votes = [v for r in played for v in r.votes]
    # A fallback vote is the random policy wearing the model's name, so nothing
    # below the vote metrics is allowed to score it. The run-wide fallback rate
    # stays the integrity metric; votes get their OWN rate, because a low
    # overall rate can sit on top of votes that are half noise.
    votes = [v for v in all_votes if not v.fell_back]
    wins = Counter(r.winner for r in played)
    decided = wins["good"] + wins["evil"]
    misled_seats = sum(1 for r in played for v in r.misled.values() if v)
    return {
        "games_requested": len(records),
        "games_completed": len(played),
        "errors": [r.error for r in records if r.error],
        "days_mean": (sum(r.days for r in played) / len(played)
                      if played else 0.0),
        "wins": {"good": wins["good"], "evil": wins["evil"],
                 "no_winner": wins[None]},
        # Over DECIDED games. A game that reached the day bound had no winner, and
        # putting it in the denominator of a win rate makes the bound look like a
        # result for the other side.
        "good_win_rate": wins["good"] / decided if decided else None,
        "good_win_ci95": wilson(wins["good"], decided) if decided else None,
        "causes": dict(Counter(r.cause for r in played if r.cause).most_common()),
        "execution": _executions(played),
        "execution_day1": _executions(played, day=1),
        "seat_games_misled": misled_seats,
        "vote_good": _votes(votes, False),
        "vote_good_misled": _votes(votes, False, misled=True),
        "vote_good_clear": _votes(votes, False, misled=False),
        "vote_evil": _votes(votes, True),
        "vote_decisions": len(all_votes),
        "vote_fallbacks": sum(1 for v in all_votes if v.fell_back),
        "vote_fallback_rate": (sum(1 for v in all_votes if v.fell_back)
                               / len(all_votes) if all_votes else None),
        "model_votes": len(votes),
        "integrity": integrity.summarise(played),
        "adjudicator_integrity": _adjudicator_integrity(played),
    }


def _adjudicator_integrity(records: list[GameRecord]) -> dict | None:
    """Aggregate referee provenance without treating it as player behavior."""
    rows = [row for r in records
            if (row := getattr(r, "adjudicator", None)) is not None]
    if not rows:
        return None
    calls = sum(row["calls"] for row in rows)
    fallbacks = sum(row["fallbacks"] for row in rows)
    recovered = sum(row["recovered"] for row in rows)
    upstreams: Counter = Counter()
    for row in rows:
        upstreams.update(row["upstreams"])
    return {
        "calls": calls,
        "fallbacks": fallbacks,
        "fallback_rate": fallbacks / calls if calls else 0.0,
        "recovered": recovered,
        "upstreams": dict(upstreams.most_common()),
    }


def _pct(value) -> str:
    return "n/a" if value is None else f"{value:.2%}"


def _band(ci) -> str:
    return "" if not ci else f" [{ci[0]:.2%}, {ci[1]:.2%}]"


def _vote_line(label: str, v: dict) -> str:
    if not v["votes"]:
        return f"  {label:<22} no votes in this stratum"
    return (f"  {label:<22} {_pct(v['accuracy'])}{_band(v['ci95'])} over "
            f"{v['votes']} votes (always-no would score "
            f"{_pct(v['always_no'])})")


def report(s: dict, args, elapsed: float) -> str:
    out = [f"=== belfry: {s['games_completed']}/{s['games_requested']} games, "
           f"{args.seats} seats, script={args.script or DEFAULT_SCRIPT.name}, "
           f"arm={args.arm}, "
           f"model={args.model if args.backend else 'none (random control)'}, "
           f"{elapsed:.0f}s ==="]
    if s["errors"]:
        out.append(f"errored games: {len(s['errors'])} (excluded from every "
                   f"figure): {s['errors'][0]}")

    out += integrity.report_lines(s["integrity"])
    rate = s["integrity"]["fallback_rate"]
    if rate > integrity.VOID_BAR:
        out.append(f"  VOID: above {integrity.VOID_BAR:.0%}, so every figure below "
                   f"is the random policy wearing a model's name. Report the rate, "
                   f"not the results.")
    adjudicator_integrity = s["adjudicator_integrity"]
    if adjudicator_integrity is not None:
        out.append(
            "adjudicator integrity  "
            f"{adjudicator_integrity['fallbacks']}/{adjudicator_integrity['calls']} "
            "setup choices fell back to random "
            f"({adjudicator_integrity['fallback_rate']:.2%} caused)")
    vote_rate = s["vote_fallback_rate"]
    if vote_rate is not None:
        out.append(f"  vote fallback {s['vote_fallbacks']}/{s['vote_decisions']} "
                   f"= {vote_rate:.2%}; vote figures below are over "
                   f"{s['model_votes']} model-cast votes only")
        if vote_rate > integrity.VOID_BAR:
            out.append(f"  VOID: vote fallback rate {vote_rate:.2%} is above the "
                       f"{integrity.VOID_BAR:.0%} ceiling within votes alone, even "
                       f"though the run-wide rate is under it - enough of the "
                       f"vote record is noise that no vote figure below is the "
                       f"model's.")

    w = s["wins"]
    out.append(f"outcome: good {w['good']}, evil {w['evil']}, no winner "
               f"{w['no_winner']} (the day bound, which is a fact about the table "
               f"and not a win)")
    out.append(f"  good win rate {_pct(s['good_win_rate'])}"
               f"{_band(s['good_win_ci95'])} over decided games; "
               f"{s['days_mean']:.1f} days per game")
    if s["causes"]:
        out.append("  how they ended: " + ", ".join(
            f"{k} {v}" for k, v in s["causes"].items()))

    e = s["execution"]
    d1 = s["execution_day1"]
    out.append(f"executions the table voted up: {e['hits']}/{e['voted_up']} "
               f"were evil, {_pct(e['rate'])}{_band(e['ci95'])} against a chance "
               f"rate of {_pct(e['chance'])} on the same boards")
    out.append(f"  first day only: {d1['hits']}/{d1['voted_up']}, "
               f"{_pct(d1['rate'])}{_band(d1['ci95'])} against "
               f"{_pct(d1['chance'])} - READ THIS ONE. The pooled figure above is "
               f"subject to a stopping rule: executing the demon ends the game, so "
               f"a table that guesses well produces fewer executions and the pool "
               f"is enriched in mistakes by construction")
    if e["on_a_dead_seat"]:
        out.append(f"  {e['on_a_dead_seat']} execution(s) carried against a seat "
                   f"that was already dead - the day ended and nobody died")
    if e["by_trigger"]:
        out.append(f"  {e['by_trigger']} execution(s) ({d1['by_trigger']} on day 1) "
                   f"were fired by a trigger rather than voted up, and are counted "
                   f"apart: the trigger names the nominator and fires only on a "
                   f"townsfolk one, so it is good with probability 1 and is not a "
                   f"draw from the board the chance rate above is computed off "
                   f"({e['trigger_hits']} of them evil)")

    out.append("votes, scored against what the referee dealt:")
    out.append(_vote_line("good seats", s["vote_good"]))
    out.append(_vote_line("  after a lie", s["vote_good_misled"]))
    out.append(_vote_line("  never lied to", s["vote_good_clear"]))
    out.append(_vote_line("evil seats", s["vote_evil"]))
    if not s["vote_good_misled"]["votes"]:
        out.append("  nothing on this table switched an ability off, so the "
                   "misled/clear split has no sample. That is a property of the "
                   "SCRIPT, not a result.")
    out.append("no deception figure is inferred from the win rate: the vote rows "
               "above are the only per-decision evidence this run carries, and a "
               "figure derived from who won would be inventing one")
    return "\n".join(out)


def land(index: int, rec: GameRecord, args) -> None:
    STATE.landed += 1
    if args.out:
        with open(record_paths(args.out)[1], "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"index": index, **asdict(rec)},
                                default=str) + "\n")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="run N games of belfry")
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--arm", choices=ARMS, default="random")
    ap.add_argument("--seats", type=int, default=5, choices=sorted(DISTRIBUTION),
                    help="table size. Cost is roughly quadratic in it: measured "
                         "at ~49 decisions per 5-seat game and ~183 per 9-seat "
                         "one, one model call each")
    ap.add_argument("--script", choices=list(SCRIPTS),
                    help="which roles could be in play (default: full). A number "
                         "recorded on one script says nothing about the other")
    ap.add_argument("--backend", choices=list(ENDPOINTS))
    ap.add_argument("--model", default="auto")
    ap.add_argument("--rounds", type=int, default=1,
                    help="rounds of talk per day - the largest single lever on "
                         "the cost of a run")
    ap.add_argument("--max-days", type=int, default=12)
    ap.add_argument("--register", choices=list(REGISTERS), default="character")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=1536)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--no-thinking", action="store_true",
                    help="ask the backend to skip visible reasoning")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed; game i uses seed+i for the deal AND the "
                         "sampler. Unset sends no seed at all, so a run that is "
                         "not pinned does not look reproducible in the records")
    ap.add_argument("--adjudicator", choices=ADJUDICATOR_ARMS, default="random",
                    help="discretion source (random uses referee deal RNG)")
    ap.add_argument("--adjudicator-backend", choices=list(ENDPOINTS))
    ap.add_argument("--adjudicator-model")
    ap.add_argument("--out", help="write the full per-game records here as JSON")
    args = ap.parse_args()

    if args.arm != "random" and not args.backend:
        raise SystemExit(f"--arm {args.arm} needs --backend")
    if args.adjudicator == "model":
        if not args.adjudicator_backend:
            raise SystemExit("--adjudicator model needs --adjudicator-backend")
        if not args.adjudicator_model:
            raise SystemExit("--adjudicator model needs --adjudicator-model")
    # Refuse at the DOOR, never at game 200. An off-box route with no key does not
    # crash - it 401s every attempt, falls back on every decision, and reports a
    # number the scorer then voids after the GPU is spent.
    if args.backend:
        require_key(ENDPOINTS[args.backend], api_key_from_env())
    if args.adjudicator == "model":
        require_key(ENDPOINTS[args.adjudicator_backend], api_key_from_env())

    STATE.requested = args.games
    started = time.time()
    records: list[GameRecord] = []
    for i in range(args.games):
        rec = one_game(i, args)
        records.append(rec)
        land(i, rec, args)
        print(f"[{i + 1}/{args.games}] {rec.winner or 'no winner'} "
              f"({rec.cause or rec.error or '?'}), {rec.days} days, "
              f"{rec.decisions} decisions, {rec.fallbacks} fell back",
              flush=True)

    s = score(records)
    print()
    print(report(s, args, time.time() - started))
    if args.out:
        with open(record_paths(args.out)[0], "w", encoding="utf-8") as fh:
            json.dump({"score": s, "args": vars(args)}, fh, indent=2)
        print(f"\nwrote {record_paths(args.out)[0]}")


if __name__ == "__main__":
    sys.exit(run_with_marker(main, STATE))
