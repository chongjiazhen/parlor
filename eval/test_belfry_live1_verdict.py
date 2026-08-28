"""The pre-commitment, pinned so it cannot drift after the arm lands.

``docs/belfry-live1-criterion.md`` is a promise in prose; ``eval/belfry_live1_verdict``
is that promise as arithmetic. This file is what stops the arithmetic from being
edited to agree with the result - every case below is built from a SYNTHETIC record,
never a live one, so a run landing on disk cannot change what any of them assert.

The cases that matter are the three clause A outcomes, and all three are asserted
rather than only the happy one: a table that discriminates (floor above zero), a
table that does not (interval spanning zero), and a table that votes against its own
side (ceiling below zero). A verdict script that only knew how to say yes would pass
a test suite that only asked it to.
"""
from __future__ import annotations

import random
import unittest

from core.stats import wilson
from eval import belfry_live1_verdict as verdict


def vote(nominee_evil: bool, yes: bool, voter_evil: bool = False,
         misled: bool = False, alive: bool = True) -> dict:
    """One ``VoteRecord`` as ``asdict`` lands it in the JSONL."""
    return {"day": 1, "seat": 0, "nominee": 1, "yes": yes,
            "voter_evil": voter_evil, "nominee_evil": nominee_evil,
            "voter_alive": alive, "voter_misled": misled}


def execution(day: int, evil: bool, was_alive: bool = True,
              alive_before: int = 5, evil_before: int = 2) -> dict:
    """One ``ExecutionRecord``, on a board that defaults to the day-1 board."""
    return {"day": day, "seat": 2, "evil": evil, "was_alive": was_alive,
            "alive_before": alive_before, "evil_before": evil_before}


def game(votes: list, executions: list, decisions: int = 48,
         fallbacks: int = 0, recovered: int = 0, days: int = 3,
         error: str | None = None) -> dict:
    """One per-game JSONL row of the shape ``eval.run_belfry`` lands."""
    row = {"index": 0, "winner": "good", "reason": "", "cause": "demon-dead",
           "days": days, "seats": 5, "script": "compact", "dealt": {},
           "final": {}, "alive": [], "executions": executions, "votes": votes,
           "decisions": decisions, "fallbacks": fallbacks,
           "recovered": recovered, "refused_attempts": 0,
           "rule_refused_attempts": 0, "utterances": [], "decision_log": [],
           "public_events": [], "log": [], "upstreams": {}, "trace_sample": [],
           "misled": {}, "error": error}
    return row


def arm(games: int, p_evil: float, p_good: float, seed: int,
        day1_evil: float = 0.4, n_evil: int = 6, n_good: int = 8) -> list[dict]:
    """``games`` rows whose good seats vote yes at ``p_evil`` on an evil nominee
    and ``p_good`` on a good one, plus one day-1 execution each.

    Drawn rather than fixed per game, because a bootstrap over games with zero
    between-game variance is not exercising the thing under test.
    """
    rng = random.Random(seed)
    rows = []
    for _ in range(games):
        votes = [vote(True, rng.random() < p_evil) for _ in range(n_evil)]
        votes += [vote(False, rng.random() < p_good) for _ in range(n_good)]
        # One evil seat votes on each side, so ``vote_evil`` has a sample.
        votes += [vote(True, False, voter_evil=True),
                  vote(False, True, voter_evil=True)]
        rows.append(game(votes, [execution(1, rng.random() < day1_evil)]))
    return rows


def summary_for(rows: list[dict]) -> dict:
    """A summary that AGREES with the rows - the instrument control's happy path.

    Built from ``recompute`` on purpose, so the control's happy path is the one
    thing this helper cannot get wrong, and every disagreement test has to
    perturb it deliberately.
    """
    d = verdict.recompute(rows)
    u = d["units"]
    t = verdict.total
    votes = t(u, "votes")
    live, hits = t(u, "day1_live"), t(u, "day1_hits")
    all_live, all_hits = t(u, "live"), t(u, "hits")
    return {"score": {
        "games_completed": d["played"],
        "games_requested": len(rows),
        "errors": [r["error"] for r in rows if r.get("error")],
        "days_mean": d["days_mean"],
        "good_win_rate": 0.5, "good_win_ci95": [0.4, 0.6],
        "causes": {"demon-dead": d["played"]},
        "seat_games_misled": 0,
        "execution_day1": {
            "executions": live, "on_a_living_seat": live, "on_a_dead_seat": 0,
            "hits": hits, "rate": hits / live if live else None,
            "chance": (t(u, "day1_chance_num") / live) if live else None,
            "ci95": wilson(hits, live) if live else None},
        "execution": {
            "executions": t(u, "executions"), "on_a_living_seat": all_live,
            "on_a_dead_seat": t(u, "dead_seat"), "hits": all_hits,
            "rate": all_hits / all_live if all_live else None,
            "chance": (t(u, "chance_num") / all_live) if all_live else None,
            "ci95": wilson(all_hits, all_live) if all_live else None},
        "vote_good": {
            "votes": votes,
            "accuracy": t(u, "correct") / votes if votes else None,
            "always_no": t(u, "always_no") / votes if votes else None,
            "always_yes": 1 - t(u, "always_no") / votes if votes else None,
            "ci95": wilson(t(u, "correct"), votes) if votes else None},
        "vote_good_misled": {"votes": t(u, "misled_votes")},
        "vote_good_clear": {"votes": votes - t(u, "misled_votes")},
        "vote_evil": {"votes": t(u, "evil_n_evil") + t(u, "evil_n_good")},
        "integrity": {"decisions": d["decisions"], "fallbacks": d["fallbacks"],
                      "recovered": d["recovered"]},
    }}


def run(rows: list[dict], summary: dict | None = None,
        promised: int = verdict.GAMES_PROMISED, path: str = verdict.CAMPAIGN):
    from pathlib import Path
    summary = summary_for(rows) if summary is None else summary
    lines, code = verdict.report(summary, verdict.recompute(rows), Path(path),
                                 promised)
    return "\n".join(lines), code


class ClauseA(unittest.TestCase):
    """The primary endpoint, all three of its pre-committed outcomes."""

    def test_a_discriminating_table_clears_the_bar(self):
        text, code = run(arm(60, 0.70, 0.30, seed=11))
        self.assertEqual(code, 0)
        self.assertIn("VERDICT: INFORMS", text)
        self.assertIn("CLAUSE A", text)

    def test_a_table_at_chance_is_not_shown_rather_than_failed(self):
        text, code = run(arm(60, 0.50, 0.50, seed=12))
        self.assertEqual(code, 0)
        self.assertIn("VERDICT: NOT SHOWN", text)
        self.assertIn("No second arm", text)

    def test_a_table_voting_against_its_own_side_is_a_result(self):
        text, code = run(arm(60, 0.20, 0.70, seed=13))
        self.assertEqual(code, 0)
        self.assertIn("VERDICT: VOTES AGAINST ITS OWN SIDE", text)

    def test_the_bar_is_zero_and_a_degenerate_policy_cannot_clear_it(self):
        """Always-no and always-yes both score exactly 0, whatever the mix."""
        for p in (0.0, 1.0):
            rows = arm(60, p, p, seed=14)
            self.assertEqual(verdict.discrimination(verdict.recompute(rows)
                                                    ["units"]), 0.0)
            text, code = run(rows)
            self.assertIn("VERDICT: NOT SHOWN", text)
            self.assertEqual(code, 0)

    def test_thin_conditional_arms_are_not_read(self):
        rows = arm(60, 0.9, 0.1, seed=15, n_evil=1, n_good=8)
        text, code = run(rows)
        self.assertEqual(code, 0)
        self.assertIn("VERDICT: NOT READ", text)
        self.assertIn(f"floor of {verdict.ARM_FLOOR}", text)

    def test_the_control_reading_ships_beside_the_verdict(self):
        text, _ = run(arm(60, 0.70, 0.30, seed=11))
        self.assertIn("the random control read 2.41%", text)


class ClauseB(unittest.TestCase):
    """The secondary. Underpowered by design, and labelled so in every branch."""

    def test_a_table_that_executes_well_clears_chance(self):
        text, code = run(arm(60, 0.7, 0.3, seed=21, day1_evil=0.9))
        self.assertEqual(code, 0)
        self.assertIn("the floor clears chance", text)
        self.assertIn("not on its own the arm's result", text)

    def test_a_table_at_chance_is_not_evidence_of_absence(self):
        text, code = run(arm(60, 0.7, 0.3, seed=22, day1_evil=0.4))
        self.assertEqual(code, 0)
        self.assertIn("the interval spans chance", text)
        self.assertIn("not evidence of absence", text)

    def test_a_board_that_is_not_five_alive_and_two_evil_is_unreadable(self):
        rows = arm(60, 0.7, 0.3, seed=23)
        for r in rows:
            r["executions"] = [execution(1, True, alive_before=4, evil_before=2)]
        text, code = run(rows)
        self.assertEqual(code, 0)
        self.assertIn("UNREADABLE", text)


class Voids(unittest.TestCase):
    """No verdict is rendered on a run the criterion pre-committed to voiding."""

    def test_fallback_above_the_repo_bar_voids_everything(self):
        rows = arm(60, 0.9, 0.1, seed=31)
        for r in rows:
            r["fallbacks"] = 20            # 20/48, well over VOID_BAR
        text, code = run(rows)
        self.assertEqual(code, 2)
        self.assertIn("VOID:", text)
        self.assertNotIn("VERDICT:", text)

    def test_a_run_at_exactly_the_bar_is_not_voided(self):
        """The bar is ``> VOID_BAR``, not ``>=`` - the same comparison
        ``eval/run_belfry.py`` makes, and a drifting pair is the bug
        ``core/integrity.py`` exists to make impossible."""
        rows = arm(60, 0.9, 0.1, seed=32)
        for r in rows:
            r["decisions"], r["fallbacks"] = 100, 10
        text, code = run(rows)
        self.assertEqual(code, 0)
        self.assertNotIn("VOID:", text)

    def test_a_short_run_is_reported_as_partial_never_scored(self):
        text, code = run(arm(59, 0.9, 0.1, seed=33))
        self.assertEqual(code, 2)
        self.assertIn("59 played games against 60 promised", text)
        self.assertNotIn("VERDICT:", text)

    def test_errored_games_do_not_count_toward_the_promise(self):
        rows = arm(60, 0.9, 0.1, seed=34)
        rows[0] = game([], [], error="RuntimeError: boom")
        text, code = run(rows)
        self.assertEqual(code, 2)
        self.assertIn("59 played games", text)

    def test_a_loud_recovered_rate_warns_and_does_not_void(self):
        rows = arm(60, 0.7, 0.3, seed=35)
        for r in rows:
            r["recovered"] = 30            # 30/48, over RECOVERED_WARN_BAR
        text, code = run(rows)
        self.assertEqual(code, 0)
        self.assertIn("WARN:", text)
        self.assertIn("VERDICT:", text)


class InstrumentControl(unittest.TestCase):
    """A number this file derives is worth nothing until it agrees with the scorer."""

    def test_the_happy_path_reproduces(self):
        text, code = run(arm(60, 0.7, 0.3, seed=41))
        self.assertEqual(code, 0)
        self.assertIn("reproduce from the rows", text)

    def test_a_summary_that_disagrees_on_votes_blocks_the_verdict(self):
        rows = arm(60, 0.7, 0.3, seed=42)
        summary = summary_for(rows)
        summary["score"]["vote_good"]["votes"] += 1
        text, code = run(rows, summary)
        self.assertEqual(code, 1)
        self.assertIn("good-seat votes: summary", text)
        self.assertNotIn("VERDICT:", text)

    def test_a_summary_that_disagrees_on_accuracy_blocks_the_verdict(self):
        rows = arm(60, 0.7, 0.3, seed=43)
        summary = summary_for(rows)
        summary["score"]["vote_good"]["accuracy"] += 0.01
        text, code = run(rows, summary)
        self.assertEqual(code, 1)
        self.assertIn("good-seat accuracy: summary", text)

    def test_a_summary_missing_a_field_blocks_the_verdict(self):
        rows = arm(60, 0.7, 0.3, seed=44)
        summary = summary_for(rows)
        del summary["score"]["execution_day1"]["hits"]
        text, code = run(rows, summary)
        self.assertEqual(code, 1)
        self.assertIn("published no day-1 hits", text)

    def test_an_off_campaign_record_is_marked_an_audit_not_a_verdict(self):
        text, code = run(arm(60, 0.7, 0.3, seed=45),
                         path="eval/records/somebody-elses.json")
        self.assertEqual(code, 0)
        self.assertIn("NOT the pre-committed arm", text)


class Descriptive(unittest.TestCase):
    """Pre-registered as descriptive, so printing them is not a later choice."""

    def test_a_thin_misled_stratum_reports_its_count_and_no_gap(self):
        rows = arm(60, 0.7, 0.3, seed=51)
        for r in rows[:5]:
            r["votes"].append(vote(True, True, misled=True))
        text, _ = run(rows)
        self.assertIn("misled good-seat votes 5", text)
        self.assertIn(f"floor of {verdict.MISLED_FLOOR}", text)
        self.assertNotIn("misled discrimination", text)

    def test_a_fat_misled_stratum_reports_a_point_estimate(self):
        rows = arm(60, 0.7, 0.3, seed=52)
        for r in rows:
            r["votes"] += [vote(True, True, misled=True)] * 2
            r["votes"] += [vote(False, False, misled=True)] * 2
        text, _ = run(rows)
        self.assertIn("misled discrimination", text)

    def test_the_degenerate_floor_ships_with_the_accuracy(self):
        text, _ = run(arm(60, 0.7, 0.3, seed=53))
        self.assertIn("always-no floor", text)

    def test_the_pooled_execution_never_claims_a_comparison(self):
        rows = arm(60, 0.7, 0.3, seed=54)
        for r in rows:
            r["executions"].append(execution(2, True, alive_before=4,
                                             evil_before=1))
            r["executions"].append(execution(2, False, was_alive=False))
        text, _ = run(rows)
        self.assertIn("NOT compared to the control", text)
        self.assertIn("already dead", text)

    def test_no_deception_figure_is_inferred_from_the_win_rate(self):
        text, _ = run(arm(60, 0.7, 0.3, seed=55))
        self.assertIn("no deduction or deception figure is inferred", text)


class Pinned(unittest.TestCase):
    """The constants the criterion promised, so a later edit fails here first."""

    def test_the_promised_constants(self):
        self.assertEqual(verdict.GAMES_PROMISED, 60)
        self.assertEqual(verdict.ARM_FLOOR, 100)
        self.assertEqual(verdict.MISLED_FLOOR, 200)
        self.assertEqual(verdict.DAY1_CHANCE, 0.40)
        self.assertEqual(verdict.CAMPAIGN, "eval/records/belfry-live1.json")

    def test_the_void_bar_is_the_repo_bar_and_not_a_second_literal(self):
        from core import integrity
        self.assertEqual(integrity.VOID_BAR, 0.10)
        self.assertEqual(integrity.RECOVERED_WARN_BAR, 0.25)


if __name__ == "__main__":
    unittest.main()
