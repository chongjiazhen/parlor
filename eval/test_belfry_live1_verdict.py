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
import unittest.mock
from pathlib import Path

from core.stats import wilson
from eval import belfry_live1_verdict as verdict


def vote(nominee_evil: bool, yes: bool, voter_evil: bool = False,
         misled: bool = False, alive: bool = True) -> dict:
    """One ``VoteRecord`` as ``asdict`` lands it in the JSONL."""
    return {"day": 1, "seat": 0, "nominee": 1, "yes": yes,
            "voter_evil": voter_evil, "nominee_evil": nominee_evil,
            "voter_alive": alive, "voter_misled": misled, "fell_back": False}


def execution(day: int, evil: bool, was_alive: bool = True,
              alive_before: int = 5, evil_before: int = 2,
              by_vote: bool = True) -> dict:
    """One ``ExecutionRecord``, on a board that defaults to the day-1 board."""
    return {"day": day, "seat": 2, "evil": evil, "was_alive": was_alive,
            "alive_before": alive_before, "evil_before": evil_before,
            "by_vote": by_vote}


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
            "voted_up": live, "by_trigger": 0, "trigger_hits": 0,
            "hits": hits, "rate": hits / live if live else None,
            "chance": (t(u, "day1_chance_num") / live) if live else None,
            "ci95": wilson(hits, live) if live else None},
        "execution": {
            "executions": t(u, "executions"),
            "on_a_living_seat": all_live + t(u, "by_trigger"),
            "voted_up": all_live, "by_trigger": t(u, "by_trigger"),
            "trigger_hits": 0,
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
        "vote_decisions": d["vote_decisions"],
        "vote_fallbacks": d["vote_fallbacks"],
        "vote_fallback_rate": d["vote_fallback_rate"],
        "model_votes": d["vote_decisions"] - d["vote_fallbacks"],
        "integrity": {"decisions": d["decisions"], "fallbacks": d["fallbacks"],
                      "recovered": d["recovered"]},
    }, "args": {
        "games": verdict.GAMES_PROMISED,
        "arm": "llm",
        "seats": 5,
        "script": "compact",
        "backend": "local",
        "model": "qwen36-35b-a3b-iq3",
        "rounds": 1,
        "temperature": 0.0,
        "no_thinking": False,
        "seed": 6100,
    }}


def run(rows: list[dict], summary: dict | None = None,
        promised: int = verdict.GAMES_PROMISED, path: str = verdict.CAMPAIGN):
    from pathlib import Path
    summary = summary_for(rows) if summary is None else summary
    lines, code = verdict.report(summary, verdict.recompute(rows), Path(path),
                                 promised, rows)
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

    def test_an_execution_a_trigger_fired_is_not_read_as_a_bad_execution(self):
        """A trigger executes the nominator and fires only on a townsfolk one, so
        it is good with probability 1. Reading it as a day-1 pick would drag the
        rate toward zero for a table that never chose it - the effect that broke
        the random control's instrument check. The compact script live1 runs has
        no such role; the field is honoured anyway, because the criterion is read
        against controls measured on scripts that do."""
        rows = arm(60, 0.7, 0.3, seed=24, day1_evil=0.9)
        for r in rows:
            r["executions"] += [execution(1, False, by_vote=False)] * 3
        text, code = run(rows)
        self.assertEqual(code, 0)
        # Pooled, the three-per-game would put the rate at ~22% on a 40% board
        # and read as a table executing WORSE than chance. The denominator is the
        # assertion: 60 voted-up executions, not 240.
        self.assertRegex(text, r"\n  \d+/60 = ")
        self.assertIn("the floor clears chance", text)

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

    def test_an_errored_row_is_not_an_instrument_control_disagreement(self):
        """One recorded error must reach the partial-run void, not read as the
        summary and the rows disagreeing about decisions. The scorer excludes
        errored games from integrity; ``recompute`` always has - this pair is
        what proves they now exclude the SAME games."""
        from games.belfry.player import (ExecutionRecord, GameRecord, VoteRecord)
        from eval.run_belfry import score
        clean = game([vote(True, True), vote(False, False)], [], decisions=48)
        errored = game([], [], decisions=48, error="RuntimeError: boom")
        rows = [clean, errored]

        def record(r: dict) -> GameRecord:
            return GameRecord(
                winner=r["winner"], reason=r["reason"], cause=r["cause"],
                days=r["days"], seats=r["seats"], script=r["script"],
                executions=[ExecutionRecord(**e) for e in r["executions"]],
                votes=[VoteRecord(**v) for v in r["votes"]],
                decisions=r["decisions"], fallbacks=r["fallbacks"],
                recovered=r["recovered"], error=r["error"])

        records = [record(r) for r in rows]
        summary = {"score": score(records)}
        derived = verdict.recompute(rows)
        self.assertEqual(verdict.control(summary, derived), [])
        self.assertTrue(any("1 played games against 2 promised" in v
                            for v in verdict.voids(derived, promised=2)))

    def test_a_vote_fallback_rate_over_the_bar_voids_before_clause_a(self):
        """Run-wide the rate is clean; within votes it is not. A vote the random
        policy cast is not evidence about the model, and enough of them voids
        the arm on its own."""
        rows = arm(60, 0.9, 0.1, seed=36)
        for r in rows:
            for v in r["votes"][:7]:        # 7 of 16 votes per game, 44%
                v["fell_back"] = True
            r["decisions"], r["fallbacks"] = 480, 7    # run-wide 1.5%
        text, code = run(rows)
        self.assertEqual(code, 2)
        self.assertIn("VOID:", text)
        self.assertIn("vote fallback", text)
        self.assertNotIn("VERDICT:", text)

    def test_an_empty_vote_sample_is_unreadable_never_zero(self):
        rows = [game([], []) for _ in range(3)]
        derived = verdict.recompute(rows)
        self.assertIsNone(derived["vote_fallback_rate"])
        self.assertFalse(any("vote fallback" in v
                             for v in verdict.voids(derived, promised=3)))

    def test_legacy_rows_fail_closed_with_a_named_reason(self):
        """A pre-fix JSONL cannot say which votes were the model's. Calling that
        'zero fallback votes' is exactly the silent assumption this slice
        exists to forbid, so the verdict refuses the vote-specific void and
        says why."""
        rows = arm(60, 0.9, 0.1, seed=37)
        for r in rows:
            for v in r["votes"]:
                del v["fell_back"]
        text, code = run(rows)
        self.assertEqual(code, 2)
        self.assertIn("VOID:", text)
        self.assertIn("legacy", text)

    def test_a_loud_recovered_rate_warns_and_does_not_void(self):
        rows = arm(60, 0.7, 0.3, seed=35)
        for r in rows:
            r["recovered"] = 30            # 30/48, over RECOVERED_WARN_BAR
        text, code = run(rows)
        self.assertEqual(code, 0)
        self.assertIn("WARN:", text)
        self.assertIn("VERDICT:", text)


class CriterionBinding(unittest.TestCase):
    """Criterion arithmetic cannot attach to a record with changed run settings."""

    def test_a_temperature_mismatch_is_not_given_a_criterion_verdict(self):
        """Removing config validation would call a sampled-player arm pre-committed."""
        rows = arm(60, 0.7, 0.3, seed=38)
        summary = summary_for(rows)
        summary["args"]["temperature"] = 0.8

        text, code = run(rows, summary)

        self.assertEqual(code, 3)
        self.assertIn("temperature: expected 0.0, record 0.8", text)
        self.assertIn("NOT this criterion", text)
        self.assertNotIn("VERDICT:", text)

    def test_cli_does_not_allow_the_criterion_game_count_to_be_overridden(self):
        """Adding ``--games`` back would let an operator rewrite promised N."""
        with unittest.mock.patch("sys.argv", ["x", "--games", "100"]):
            with self.assertRaises(SystemExit) as raised:
                verdict.main()

        self.assertEqual(raised.exception.code, 2)


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

    def test_an_off_campaign_record_is_rejected_before_a_verdict(self):
        text, code = run(arm(60, 0.7, 0.3, seed=45),
                         path="eval/records/somebody-elses.json")
        self.assertEqual(code, 3)
        self.assertIn("record path: expected", text)
        self.assertNotIn("VERDICT:", text)

    def test_vote_provenance_reproduces_from_the_rows(self):
        rows = arm(60, 0.9, 0.1, seed=46)
        for r in rows:
            r["votes"][0]["fell_back"] = True
            r["decisions"], r["fallbacks"] = 480, 1
        summary = summary_for(rows)
        self.assertEqual(verdict.control(summary, verdict.recompute(rows)), [])
        self.assertEqual(summary["score"]["vote_fallbacks"], 60)

    def test_a_summary_that_disagrees_on_vote_fallbacks_blocks_the_verdict(self):
        rows = arm(60, 0.7, 0.3, seed=47)
        summary = summary_for(rows)
        summary["score"]["vote_fallbacks"] += 1
        text, code = run(rows, summary)
        self.assertEqual(code, 1)
        self.assertIn("vote fallbacks: summary", text)

    def test_a_vote_record_disagreeing_with_its_decision_log_blocks_the_verdict(self):
        """The decision log is the cross-check join source. A VoteRecord and its
        Decision saying different things about the SAME vote is a driver bug,
        and the controller fails on it rather than picking one to believe."""
        rows = arm(60, 0.7, 0.3, seed=48)
        for i, v in enumerate(rows[0]["votes"]):
            v["turn"] = 100 + i
        rows[0]["votes"][0]["fell_back"] = True
        rows[0]["decision_log"] = [
            {"turn": 100 + i, "day": 1, "seat": 0, "kind": "vote",
             "fell_back": False} for i in range(len(rows[0]["votes"]))]
        text, code = run(rows)
        self.assertEqual(code, 1)
        self.assertIn("decision log", text)

    def test_an_early_mutated_vote_cannot_hide_behind_a_later_duplicate_key(self):
        """Regression: the join used to be keyed (day, seat), which repeats the
        moment one seat votes twice in a day - the dict kept the LAST entry and
        a mutation to an earlier vote escaped the controller whole."""
        rows = arm(60, 0.9, 0.1, seed=49)
        for i, v in enumerate(rows[0]["votes"]):
            v["turn"] = 100 + i
        rows[0]["decision_log"] = [
            {"turn": 100 + i, "day": 1, "seat": 0, "kind": "vote",
             "fell_back": False} for i in range(len(rows[0]["votes"]))]
        rows[0]["votes"][0]["fell_back"] = True     # the EARLY one
        text, code = run(rows)
        self.assertEqual(code, 1)
        self.assertIn("turn 100", text)


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


class TheCliRunsTheControllerItShips(unittest.TestCase):
    """The join is only worth having if the path an operator runs reaches it.

    ``report`` took ``rows`` as an OPTIONAL argument and ``main`` did not pass
    them, so the whole vote-provenance join sat behind ``if rows is not None``
    and never ran outside the tests. The two regression tests above passed
    because the helper supplies rows by hand. This one goes through ``main``.
    """

    def _write(self, rows) -> str:
        import json
        import tempfile
        from pathlib import Path
        d = Path(tempfile.mkdtemp())
        p = d / "probe.json"
        p.write_text(json.dumps(summary_for(rows)), encoding="utf-8")
        (d / "probe.json.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        return str(p)

    def _main(self, path: str) -> tuple[str, int]:
        import contextlib
        import io
        buf = io.StringIO()
        code = 0
        with contextlib.redirect_stdout(buf):
            with (unittest.mock.patch("sys.argv", ["x", path]),
                  unittest.mock.patch.object(
                      verdict, "CAMPAIGN", Path(path).as_posix())):
                try:
                    verdict.main()
                except SystemExit as exc:
                    code = int(exc.code or 0)
        return buf.getvalue(), code

    @staticmethod
    def _joinable(rows: list[dict]) -> list[dict]:
        """Give game 0 the turn keys and decision log the join needs."""
        for i, v in enumerate(rows[0]["votes"]):
            v["turn"] = 100 + i
        rows[0]["decision_log"] = [
            {"turn": 100 + i, "day": 1, "seat": 0, "kind": "vote",
             "fell_back": False} for i in range(len(rows[0]["votes"]))]
        return rows

    def test_a_desynchronised_vote_is_caught_through_main_not_only_the_helper(self):
        rows = self._joinable(arm(60, 0.70, 0.30, seed=11))
        rows[0]["votes"][0]["fell_back"] = True      # the log says False
        text, code = self._main(self._write(rows))
        self.assertEqual(code, 1, "main must run the provenance join")
        self.assertIn("decision log", text)

    def test_a_clean_record_still_passes_through_main(self):
        text, code = self._main(self._write(
            self._joinable(arm(60, 0.70, 0.30, seed=11))))
        self.assertEqual(code, 0)
        self.assertIn("VERDICT", text)

    def test_report_refuses_to_be_called_without_rows(self):
        with self.assertRaises(TypeError):
            verdict.report({}, {}, Path("x"), 60)
