"""The arithmetic behind belfry's first live arm, written BEFORE the record exists.

    py -3 -m eval.belfry_live1_verdict

``docs/belfry-live1-criterion.md`` is the promise. This file is that promise made
mechanical, and it was written before any model had played a belfry seat - which is
the only time it can be written honestly. A verdict script authored after the
numbers land has had its statistic chosen with the numbers in view, which is the
``hunt20b`` error ``docs/evidence-discipline.md`` refuses by name. Nothing here may
be edited to agree with what the arm returns; the outcome goes in
``games/belfry/RULES.md``, clause by clause.

Five things it does, in the order the criterion uses them:

1. **Instrument control first.** The per-game JSONL is the raw evidence and the
   summary ``.json`` is what the driver published. This re-derives the vote and
   execution counts straight off the rows and refuses to report a verdict if they
   disagree with the summary. A number this file derives is worth nothing until it
   agrees with what the scorer already wrote down.

2. **The void conditions, checked before either clause.** Fallback above the repo's
   ``core.integrity.VOID_BAR``, or fewer played games than promised. A partial run
   is reported as partial, never as a short arm. An entitlement leak cannot reach
   here at all - ``play_game`` raises and ``one_game`` re-raises, so a leaked run
   writes no summary.

3. **Clause A, the primary.** Good-seat vote discrimination: the yes-rate on evil
   nominees minus the yes-rate on good ones. Its floor is exactly zero and no
   degenerate policy can clear it - always-no scores 0, always-yes scores 0, and so
   does any vote independent of what the nominee is. The interval is a bootstrap
   over GAMES, not a Wilson over votes, on the argument ``core/stats.py`` makes in
   its own docstring: votes inside one game share a deal, a night and a table.

4. **Clause B, the pre-registered secondary.** Day-1 execution accuracy against the
   chance rate on its own boards, which at 5 seats is exactly 40.00%. Underpowered
   at the promised N and labelled so in every line it prints.

5. **The descriptive block**, every item of which was pre-registered in the
   criterion so that printing it here is not a statistic chosen after the fact.

Exit codes, so a caller can gate on it: **0** the criterion was applied, **1** the
instrument control disagreed or the record is missing, **2** the run is void by its
own pre-committed conditions.

It infers no deduction or deception figure from the win rate. A win on this rung is
a four-day chain and attributing it to one decision is not something the record
supports, which ``eval/run_belfry.py`` says in its own report.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core import integrity
from core.stats import bootstrap_ci, wilson

#: The arm the criterion binds. A different record still scores, loudly marked,
#: because the arithmetic is worth auditing against any run - but only this one is
#: the pre-committed arm.
CAMPAIGN = "eval/records/belfry-live1.json"

#: Pre-committed in ``docs/belfry-live1-criterion.md``, every one before any data.
GAMES_PROMISED = 60
#: Below this many good-seat votes on EITHER conditional arm, clause A is not read.
ARM_FLOOR = 100
#: Below this many misled good-seat votes, no misled/clear gap is reported. The
#: control's rate puts 60 games at ~49, so this is expected to fire.
MISLED_FLOOR = 200
#: Day 1 at 5 seats opens with five alive and two evil, every game. The control
#: landed on this exactly over 134 executions.
DAY1_CHANCE = 0.40
#: A run whose own day-1 chance figure misses that by more than this killed a seat
#: before the first execution, and clause B is unreadable rather than failed.
CHANCE_TOLERANCE = 0.02

#: The control's own reading, written down rather than only cited, so the
#: instrument's floor travels with the arithmetic that uses it.
#: 551/1113 yes on evil nominees against 777/1650 on good, over 200 games.
CONTROL_DISCRIMINATION = 0.0241
CONTROL_BOOTSTRAP = (-0.0149, 0.0615)


def load(path: Path) -> tuple[dict, list[dict]]:
    """The summary the driver published, and the per-game rows behind it."""
    summary = json.loads(path.read_text(encoding="utf-8"))
    rows_path = path.with_suffix(path.suffix + ".jsonl")
    rows = [json.loads(line) for line in
            rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return summary, rows


def tally(row: dict) -> dict:
    """One game's votes and executions, counted the way both clauses need them.

    A per-game unit, because the bootstrap resamples games. Every field is a count,
    so a resample is a sum and the statistic functions below stay arithmetic.
    """
    t = {k: 0 for k in (
        "yes_evil", "n_evil", "yes_good", "n_good",
        "correct", "always_no", "votes",
        "evil_yes_evil", "evil_n_evil", "evil_yes_good", "evil_n_good",
        "misled_yes_evil", "misled_n_evil", "misled_yes_good", "misled_n_good",
        "misled_votes", "misled_correct",
        "alive_votes", "alive_correct", "dead_votes", "dead_correct",
        "day1_live", "day1_hits", "day1_chance_num",
        "live", "hits", "chance_num", "dead_seat", "executions",
        "vote_decisions", "vote_fallbacks", "provenance_missing")}
    for v in row.get("votes", []):
        # A vote the random fallback cast is not a model vote. Old records carry
        # no field; tally counts them apart rather than assuming clean, and the
        # verdict refuses to read a vote-specific void off them.
        if "fell_back" not in v:
            t["provenance_missing"] += 1
        t["vote_decisions"] += 1
        t["vote_fallbacks"] += int(bool(v.get("fell_back", False)))
        if v.get("fell_back", False):
            continue
        evil_nominee = bool(v["nominee_evil"])
        yes = bool(v["yes"])
        if v["voter_evil"]:
            if evil_nominee:
                t["evil_n_evil"] += 1
                t["evil_yes_evil"] += yes
            else:
                t["evil_n_good"] += 1
                t["evil_yes_good"] += yes
            continue
        t["votes"] += 1
        # The scorer's own definition, restated rather than imported: a good seat is
        # right to vote for executing an evil nominee and against executing a good
        # one, and always-no is right exactly when the nominee is good.
        correct = int(yes == evil_nominee)
        t["correct"] += correct
        t["always_no"] += int(not evil_nominee)
        if evil_nominee:
            t["n_evil"] += 1
            t["yes_evil"] += yes
        else:
            t["n_good"] += 1
            t["yes_good"] += yes
        if v.get("voter_misled"):
            t["misled_votes"] += 1
            t["misled_correct"] += correct
            if evil_nominee:
                t["misled_n_evil"] += 1
                t["misled_yes_evil"] += yes
            else:
                t["misled_n_good"] += 1
                t["misled_yes_good"] += yes
        if v.get("voter_alive", True):
            t["alive_votes"] += 1
            t["alive_correct"] += correct
        else:
            t["dead_votes"] += 1
            t["dead_correct"] += correct
    for e in row.get("executions", []):
        t["executions"] += 1
        if not e["was_alive"]:
            t["dead_seat"] += 1
            continue
        share = e["evil_before"] / e["alive_before"] if e["alive_before"] else 0.0
        t["live"] += 1
        t["hits"] += int(bool(e["evil"]))
        t["chance_num"] += share
        if e["day"] == 1:
            t["day1_live"] += 1
            t["day1_hits"] += int(bool(e["evil"]))
            t["day1_chance_num"] += share
    return t


def total(units: list[dict], key: str) -> int | float:
    return sum(u[key] for u in units)


def discrimination(units: list[dict], prefix: str = "") -> float | None:
    """P(yes | nominee evil) - P(yes | nominee good), for one side's votes.

    ``None`` when either conditional arm is empty, so a bootstrap resample that
    happens to draw no evil nominee is dropped rather than counted as zero -
    the same refusal ``wilson`` makes for the same reason.
    """
    n_e = total(units, prefix + "n_evil")
    n_g = total(units, prefix + "n_good")
    if not n_e or not n_g:
        return None
    return (total(units, prefix + "yes_evil") / n_e
            - total(units, prefix + "yes_good") / n_g)


def degenerate_gap(units: list[dict]) -> float | None:
    """Good-seat accuracy minus the always-no policy's score on the SAME votes."""
    n = total(units, "votes")
    if not n:
        return None
    return (total(units, "correct") - total(units, "always_no")) / n


def recompute(rows: list[dict]) -> dict:
    """Everything the verdict needs, derived from the raw rows and nothing else."""
    played = [r for r in rows if not r.get("error")]
    units = [tally(r) for r in played]
    decisions = sum(r.get("decisions", 0) for r in played)
    fallbacks = sum(r.get("fallbacks", 0) for r in played)
    recovered = sum(r.get("recovered", 0) for r in played)
    return {
        "games": len(rows),
        "played": len(played),
        "errors": len(rows) - len(played),
        "decisions": decisions,
        "fallbacks": fallbacks,
        "recovered": recovered,
        "fallback_rate": fallbacks / decisions if decisions else 0.0,
        "recovered_rate": recovered / decisions if decisions else 0.0,
        "vote_decisions": total(units, "vote_decisions"),
        "vote_fallbacks": total(units, "vote_fallbacks"),
        "provenance_missing": total(units, "provenance_missing"),
        "vote_fallback_rate": (total(units, "vote_fallbacks")
                               / total(units, "vote_decisions")
                               if total(units, "vote_decisions") else None),
        "days_mean": (sum(r.get("days", 0) for r in played) / len(played)
                      if played else 0.0),
        "units": units,
    }


def control(summary: dict, derived: dict,
            rows: list[dict] | None = None) -> list[str]:
    """Disagreements between the published summary and the rows behind it."""
    score = summary.get("score", {})
    units = derived["units"]
    good = score.get("vote_good", {})
    day1 = score.get("execution_day1", {})
    pooled = score.get("execution", {})
    checks = [
        ("played games", score.get("games_completed"), derived["played"]),
        ("decisions", score.get("integrity", {}).get("decisions"),
         derived["decisions"]),
        ("fallbacks", score.get("integrity", {}).get("fallbacks"),
         derived["fallbacks"]),
        ("vote decisions", score.get("vote_decisions"),
         derived["vote_decisions"]),
        ("vote fallbacks", score.get("vote_fallbacks"),
         derived["vote_fallbacks"]),
        ("model votes", score.get("model_votes"),
         derived["vote_decisions"] - derived["vote_fallbacks"]),
        ("good-seat votes", good.get("votes"), total(units, "votes")),
        ("evil-seat votes", score.get("vote_evil", {}).get("votes"),
         total(units, "evil_n_evil") + total(units, "evil_n_good")),
        ("misled good-seat votes", score.get("vote_good_misled", {}).get("votes"),
         total(units, "misled_votes")),
        ("day-1 executions on a living seat", day1.get("on_a_living_seat"),
         total(units, "day1_live")),
        ("day-1 hits", day1.get("hits"), total(units, "day1_hits")),
        ("executions on a living seat", pooled.get("on_a_living_seat"),
         total(units, "live")),
        ("executions on a dead seat", pooled.get("on_a_dead_seat"),
         total(units, "dead_seat")),
        ("hits", pooled.get("hits"), total(units, "hits")),
    ]
    bad = []
    if rows is not None:
        # The decision log is the cross-check join source, on ``turn`` - the
        # one key that names ONE decision. (day, seat) is not a key at all: a
        # day has many nominations and a seat votes in each, so a dict keyed by
        # it silently keeps the LAST vote's provenance and lets an earlier
        # mutated one through. A mismatch is a driver bug, so the controller
        # fails on it rather than picking one record to believe.
        for i, row in enumerate(rows):
            if row.get("error"):
                continue
            log_votes = {d["turn"]: bool(d["fell_back"])
                         for d in row.get("decision_log", [])
                         if d.get("kind") == "vote"}
            if not log_votes:
                continue    # no log to join against (legacy or synthetic row)
            for j, v in enumerate(row.get("votes", [])):
                turn = v.get("turn", -1)
                if turn < 0:
                    bad.append(f"game {i} vote {j}: no turn field - a record "
                               f"written before the join key existed cannot be "
                               f"cross-checked and is not assumed to agree")
                elif turn not in log_votes:
                    bad.append(f"game {i} vote {j}: no vote decision at turn "
                               f"{turn} in the decision log")
                elif log_votes[turn] != bool(v.get("fell_back", False)):
                    bad.append(f"game {i} vote {j}: record says fell_back="
                               f"{v.get('fell_back', False)}, decision log says "
                               f"{log_votes[turn]} (turn {turn})")
    for name, published, mine in checks:
        if published is None:
            bad.append(f"the summary published no {name}")
        elif published != mine:
            bad.append(f"{name}: summary {published!r}, rows {mine!r}")
    # The two rate fields, on a tolerance rather than an equality: they are floats
    # the scorer divided, and re-deriving one is not bit-for-bit.
    votes = total(units, "votes")
    if votes and good.get("accuracy") is not None:
        mine = total(units, "correct") / votes
        if abs(good["accuracy"] - mine) > 1e-9:
            bad.append(f"good-seat accuracy: summary {good['accuracy']!r}, "
                       f"rows {mine!r}")
    if votes and good.get("always_no") is not None:
        mine = total(units, "always_no") / votes
        if abs(good["always_no"] - mine) > 1e-9:
            bad.append(f"always-no floor: summary {good['always_no']!r}, "
                       f"rows {mine!r}")
    return bad


def voids(derived: dict, promised: int) -> list[str]:
    """The pre-committed void conditions, in the criterion's own words."""
    out = []
    if derived["provenance_missing"]:
        out.append(
            f"{derived['provenance_missing']} vote record(s) carry no provenance "
            f"field - a legacy pre-fix record cannot say which votes were the "
            f"model's, so the vote-specific void cannot be checked and no vote "
            f"figure from it is a new-criterion observation")
    elif (derived["vote_fallback_rate"] is not None
          and derived["vote_fallback_rate"] > integrity.VOID_BAR):
        out.append(
            f"vote fallback rate {derived['vote_fallback_rate']:.2%} "
            f"({derived['vote_fallbacks']}/{derived['vote_decisions']} votes) is "
            f"above the {integrity.VOID_BAR:.0%} ceiling within votes alone, "
            f"even with the run-wide rate under it - enough of the vote record "
            f"is noise that no vote figure is the model's")
    if derived["fallback_rate"] > integrity.VOID_BAR:
        out.append(
            f"fallback rate {derived['fallback_rate']:.2%} is above the "
            f"{integrity.VOID_BAR:.0%} ceiling - a decision no model could make "
            f"legally is played at random and counted")
    if derived["played"] < promised:
        out.append(
            f"{derived['played']} played games against {promised} promised - a "
            f"partial run is reported as partial or rerun whole, never scored as "
            f"a short arm")
    return out


def call_primary(units: list[dict]) -> tuple[str, str, tuple | None]:
    """Clause A. Floor above zero -> the vote carries information."""
    n_e, n_g = total(units, "n_evil"), total(units, "n_good")
    if min(n_e, n_g) < ARM_FLOOR:
        return ("NOT READ",
                f"only {n_e} votes on an evil nominee and {n_g} on a good one, "
                f"under the pre-committed floor of {ARM_FLOOR} on each arm: no "
                f"discrimination figure is reported", None)
    ci = bootstrap_ci(units, discrimination)
    if ci is None:
        return ("NOT READ", "the bootstrap could not support a statistic", None)
    lo, hi = ci
    if lo > 0:
        return ("INFORMS",
                "the game-clustered floor clears zero: a good seat's vote carries "
                "information about who the referee dealt as evil. A dated snapshot "
                "of one model on one script at one talk round, never a claim about "
                "models", ci)
    if hi < 0:
        return ("VOTES AGAINST ITS OWN SIDE",
                "the game-clustered ceiling is below zero: good seats voted to "
                "execute good nominees MORE often than evil ones. At temperature "
                "0.0 that is systematic rather than noise, and it is a result - "
                "the table's talk moved its own side against itself", ci)
    return ("NOT SHOWN",
            "the interval spans zero: the run does not decide it. Report the point "
            "estimate with the interval and make no claim. No second arm to chase "
            "it, at a different N or a different seed", ci)


def _pct(value) -> str:
    return "n/a" if value is None else f"{value:.2%}"


def _band(ci) -> str:
    return "" if not ci else f" [{ci[0]:.2%}, {ci[1]:.2%}]"


def report(summary: dict, derived: dict, path: Path,
           promised: int, rows: list[dict]) -> tuple[list[str], int]:
    # ``rows`` is REQUIRED, not optional. It WAS optional, every caller that
    # mattered had the rows in hand, and ``main`` did not pass them - so the
    # vote-provenance join in ``control`` sat behind ``if rows is not None`` and
    # never ran on the one path an operator executes. The suite stayed green
    # because the test helper passed them. A default here is a controller that
    # silently degrades to no controller, so the signature refuses one.
    units = derived["units"]
    score = summary.get("score", {})
    out = [f"belfry live arm #1 - {path.as_posix()}",
           "criterion: docs/belfry-live1-criterion.md (pre-committed, not editable)"]
    if path.as_posix() != CAMPAIGN:
        out += ["", f"** NOT the pre-committed arm ({CAMPAIGN}). The arithmetic "
                    f"below is an audit of this record, not a verdict. **"]

    bad = control(summary, derived, rows)
    out += ["", "instrument control - the summary against the rows behind it"]
    if bad:
        out += [f"  DISAGREES: {b}" for b in bad]
        out += ["", "no verdict: a number this file derives is worth nothing until "
                    "it agrees with what the scorer published."]
        return out, 1
    out += ["  the published vote and execution counts reproduce from the rows"]

    void = voids(derived, promised)
    out += ["", "void conditions, pre-committed"]
    if void:
        out += [f"  VOID: {v}" for v in void]
        out += [f"  reported anyway: {derived['played']} played games, "
                f"{derived['decisions']} decisions, {derived['errors']} errored"]
        return out, 2
    out += [f"  fallback {derived['fallback_rate']:.2%} of {derived['decisions']} "
            f"decisions, under the {integrity.VOID_BAR:.0%} ceiling",
            f"  {derived['played']} played games, as promised"
            + (f" ({derived['errors']} errored, excluded from every figure)"
               if derived["errors"] else "")]
    if derived["vote_fallback_rate"] is not None:
        out.append(
            f"  vote fallback {derived['vote_fallbacks']}/"
            f"{derived['vote_decisions']} = "
            f"{derived['vote_fallback_rate']:.2%} within votes; vote figures "
            f"below are over "
            f"{derived['vote_decisions'] - derived['vote_fallbacks']} "
            f"model-cast votes only")
    if derived["recovered_rate"] > integrity.RECOVERED_WARN_BAR:
        out.append(
            f"  WARN: {derived['recovered_rate']:.2%} of decisions were sent back "
            f"by the parser or the rules before the model answered legally, above "
            f"the {integrity.RECOVERED_WARN_BAR:.0%} bar. Legal play and NOT a "
            f"void - but this is not the same measurement as the control, whose "
            f"recovered rate is 0.00% because the random policy is never refused, "
            f"and any comparison must say so.")

    out += ["", "CLAUSE A (primary) - good-seat vote discrimination, floor above 0"]
    n_e, n_g = total(units, "n_evil"), total(units, "n_good")
    if n_e and n_g:
        p_e = total(units, "yes_evil") / n_e
        p_g = total(units, "yes_good") / n_g
        out += [f"  yes on an evil nominee {total(units, 'yes_evil')}/{n_e} = "
                f"{_pct(p_e)}{_band(wilson(total(units, 'yes_evil'), n_e))}",
                f"  yes on a good nominee  {total(units, 'yes_good')}/{n_g} = "
                f"{_pct(p_g)}{_band(wilson(total(units, 'yes_good'), n_g))}"]
    verdict, why, ci = call_primary(units)
    point = discrimination(units)
    out += [f"  discrimination {_pct(point)}{_band(ci)} "
            f"(bootstrap over {len(units)} games)",
            f"    VERDICT: {verdict}",
            f"    {why}",
            f"  the random control read {CONTROL_DISCRIMINATION:.2%} "
            f"[{CONTROL_BOOTSTRAP[0]:.2%}, {CONTROL_BOOTSTRAP[1]:.2%}] over 200 "
            f"games - it does not clear this bar, which is what earns the figure "
            f"the right to be read"]

    out += ["", "CLAUSE B (secondary, underpowered by design) - day-1 executions"]
    day1 = score.get("execution_day1", {})
    live, hits = total(units, "day1_live"), total(units, "day1_hits")
    chance = (total(units, "day1_chance_num") / live) if live else None
    if not live:
        out.append("  no day-1 execution landed on a living seat - nothing to read")
    elif chance is None or abs(chance - DAY1_CHANCE) > CHANCE_TOLERANCE:
        out.append(f"  UNREADABLE: the run's own chance rate is {_pct(chance)}, "
                   f"more than {CHANCE_TOLERANCE:.0%} from the {DAY1_CHANCE:.2%} "
                   f"that five alive and two evil forces. Something killed a seat "
                   f"before the first execution; that is a fact about the run")
    else:
        ci95 = day1.get("ci95") or wilson(hits, live)
        rate = hits / live
        out.append(f"  {hits}/{live} = {_pct(rate)}{_band(ci95)} against a chance "
                   f"rate of {_pct(chance)} on the same boards")
        if ci95 and ci95[0] > chance:
            out.append("    the floor clears chance. Worth reporting, and not on "
                       "its own the arm's result - this endpoint had ~69% power "
                       "against a true 60% at 60 games")
        elif ci95 and ci95[1] < chance:
            out.append("    the ceiling is below chance: the table executed evil "
                       "seats on day 1 LESS often than picking at random would")
        else:
            out.append("    the interval spans chance. At 60 games this is not "
                       "evidence of absence: ~21% power against a true 50%")

    out += ["", "reported beside the verdict, gating nothing - every item "
                "pre-registered in the criterion"]
    votes = total(units, "votes")
    if votes:
        acc = total(units, "correct") / votes
        floor = total(units, "always_no") / votes
        gap = bootstrap_ci(units, degenerate_gap)
        out.append(f"  good-seat accuracy {_pct(acc)} against an always-no floor of "
                   f"{_pct(floor)} on the same {votes} votes; gap "
                   f"{_pct(acc - floor)}{_band(gap)}. Descriptive: always-no "
                   f"depends on the nominee mix, which this arm's own play changes")
    live_all, hits_all = total(units, "live"), total(units, "hits")
    if live_all:
        out.append(f"  pooled executions {hits_all}/{live_all} = "
                   f"{_pct(hits_all / live_all)}"
                   f"{_band(wilson(hits_all, live_all))} against "
                   f"{_pct(total(units, 'chance_num') / live_all)}, over "
                   f"{derived['days_mean']:.1f} days per game. NOT compared to the "
                   f"control: executing the demon ends the game, so the pool is "
                   f"enriched in mistakes by construction and the two arms did not "
                   f"run the same number of days")
    if total(units, "dead_seat"):
        out.append(f"  {total(units, 'dead_seat')} execution(s) of "
                   f"{total(units, 'executions')} carried against a seat that was "
                   f"already dead - the day ended and nobody died")
    misled = total(units, "misled_votes")
    out.append(f"  misled good-seat votes {misled}"
               + ("" if misled >= MISLED_FLOOR else
                  f" - under the pre-committed floor of {MISLED_FLOOR}, so no "
                  f"misled/clear gap is reported. Said in advance: 60 games was "
                  f"expected to yield about 49"))
    if misled >= MISLED_FLOOR:
        m = discrimination(units, "misled_")
        out.append(f"    misled discrimination {_pct(m)}, clear "
                   f"{_pct(discrimination(units))} pooled - point estimates only")
    if total(units, "alive_votes") and total(units, "dead_votes"):
        out.append(f"  living good seats {_pct(total(units, 'alive_correct') / total(units, 'alive_votes'))} "
                   f"over {total(units, 'alive_votes')} votes; dead good seats "
                   f"{_pct(total(units, 'dead_correct') / total(units, 'dead_votes'))} "
                   f"over {total(units, 'dead_votes')}")
    evil_d = discrimination(units, "evil_")
    if evil_d is not None:
        out.append(f"  evil-seat discrimination {_pct(evil_d)} - an evil seat "
                   f"playing well is NEGATIVE here, and the arm is not powered to "
                   f"split it")
    out += [f"  good win rate {_pct(score.get('good_win_rate'))}"
            f"{_band(score.get('good_win_ci95'))} over decided games; "
            f"{derived['days_mean']:.1f} days per game; "
            f"{score.get('seat_games_misled', 0)} seat-games misled",
            f"  how they ended: " + (", ".join(
                f"{k} {v}" for k, v in (score.get("causes") or {}).items())
                or "nothing recorded"),
            f"  recovered {derived['recovered']}/{derived['decisions']} "
            f"({derived['recovered_rate']:.2%}) decisions were sent back before "
            f"the model answered legally",
            "",
            "no deduction or deception figure is inferred from the win rate: a win "
            "here is a four-day chain and the record does not attribute it to any "
            "one decision."]
    return out, 0


def main() -> None:
    ap = argparse.ArgumentParser(
        description="apply belfry's pre-committed first-arm criterion")
    ap.add_argument("record", nargs="?", default=CAMPAIGN,
                    help=f"the run summary .json (default {CAMPAIGN})")
    ap.add_argument("--games", type=int, default=GAMES_PROMISED,
                    help="games the criterion promised, for the partial-run void")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    path = Path(args.record)
    try:
        summary, rows = load(path)
    except FileNotFoundError as exc:
        print(f"no record at {exc.filename} - the arm has not been run")
        sys.exit(1)

    lines, code = report(summary, recompute(rows), path, args.games, rows)
    print("\n".join(lines))
    sys.exit(code)


if __name__ == "__main__":
    main()
