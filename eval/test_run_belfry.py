"""The belfry run driver: seeding, arms, scoring, and what it refuses to report."""

from __future__ import annotations

import argparse
import json
import os
import random
import tempfile
import unittest
from unittest import mock

from core.runlog import record_paths
from eval.run_belfry import (build_backend, build_policies, one_game, report,
                             score)
from games.belfry.player import (ExecutionRecord, GameRecord, LLMPolicy,
                                 RandomPolicy, VoteRecord)
from games.belfry.referee import BelfryReferee
from games.belfry.roles import Align
from games.belfry.state import BadSetup


def args(**over) -> argparse.Namespace:
    base = dict(games=2, arm="random", seats=5, script="compact", backend=None,
                model="auto", rounds=1, max_days=12, register="character",
                retries=2, temperature=0.8, max_tokens=1536, timeout=120.0,
                no_thinking=False, seed=None, out=None)
    base.update(over)
    return argparse.Namespace(**base)


def execution(evil: bool, alive: int = 5, evil_alive: int = 2, day: int = 1,
              was_alive: bool = True, by_vote: bool = True) -> ExecutionRecord:
    return ExecutionRecord(day=day, seat=0, evil=evil, was_alive=was_alive,
                           alive_before=alive, evil_before=evil_alive,
                           by_vote=by_vote)


def vote(yes: bool, nominee_evil: bool, voter_evil: bool = False,
         misled: bool = False, fell_back: bool = False) -> VoteRecord:
    return VoteRecord(day=1, seat=0, nominee=1, yes=yes, voter_evil=voter_evil,
                      nominee_evil=nominee_evil, voter_alive=True,
                      voter_misled=misled, fell_back=fell_back)


class TestSeeding(unittest.TestCase):
    def test_the_backend_gets_the_GAMES_seed_and_not_the_runs_base(self):
        """The repo invariant: --seed seeds the sampler as well as the deal, or it
        is not a seed. Passing the run's base here would pin the sampler for every
        game while the deal advanced, so cross-game variation would come only from
        the prompt."""
        a = args(arm="llm", backend="local", seed=6100)
        self.assertEqual(build_backend(a, 6107).seed, 6107)
        self.assertNotEqual(build_backend(a, 6107).seed, a.seed)

    def test_the_same_seed_replays_a_game_exactly(self):
        a = args(seed=31)
        one, two = one_game(3, a), one_game(3, a)
        self.assertEqual((one.winner, one.cause, one.days),
                         (two.winner, two.cause, two.days))
        self.assertEqual(one.dealt, two.dealt)

    def test_an_unpinned_run_sends_no_seed_at_all(self):
        """A default would make every run look reproducible while the records say
        nothing about it."""
        self.assertIsNone(args().seed)
        self.assertGreater(one_game(0, args()).decisions, 0)

    def test_a_broken_game_is_recorded_rather_than_killing_the_run(self):
        """One bad game must not take the other 199 with it - and it must not pass
        for a played one either, which is why the record carries the error and
        every figure excludes it."""
        with mock.patch("eval.run_belfry.play_game",
                        side_effect=RuntimeError("boom")):
            rec = one_game(0, args(seed=1))
        self.assertEqual(rec.error, "RuntimeError: boom")
        self.assertEqual(score([rec])["games_completed"], 0)

    def test_a_leak_is_never_scoreable_and_stops_the_run(self):
        """Every other exception is caught and recorded. This one is re-raised: a
        run that scored a leaked game would be reporting numbers off a table that
        broke the property the arena exists to prove."""
        with mock.patch("eval.run_belfry.play_game",
                        side_effect=AssertionError("gate #1 violated")):
            with self.assertRaises(AssertionError):
                one_game(0, args(seed=1))

    def test_a_table_with_no_published_proportions_is_refused_at_the_door(self):
        with self.assertRaises(BadSetup):
            one_game(0, args(seats=4))


class TestArms(unittest.TestCase):
    def ref(self):
        return BelfryReferee.new(7, seed=11)

    def test_the_random_arm_seats_nobody_live(self):
        ref = self.ref()
        policies = build_policies(ref, args(), random.Random(0))
        self.assertTrue(all(isinstance(p, RandomPolicy)
                            for p in policies.values()))

    def test_a_side_arm_seats_only_that_side_live(self):
        ref = self.ref()
        for arm, want in (("llm-good", Align.GOOD), ("llm-evil", Align.EVIL)):
            policies = build_policies(
                ref, args(arm=arm, backend="local"), random.Random(0))
            for seat, policy in policies.items():
                live = isinstance(policy, LLMPolicy)
                self.assertEqual(live, ref.grim.seat(seat).align is want,
                                 (arm, seat))

    def test_each_live_seat_gets_its_own_policy_object(self):
        """A shared policy makes `upstreams` one Counter the record then sums once
        per seat, multiplying the census by the live-seat count."""
        ref = self.ref()
        policies = build_policies(ref, args(arm="llm", backend="local"),
                                  random.Random(0))
        self.assertEqual(len({id(p) for p in policies.values()}), ref.n)


class TestExecutionScoring(unittest.TestCase):
    def rec(self, executions) -> GameRecord:
        r = GameRecord(winner="good", cause="demon-dead", days=2, seats=5)
        r.executions = executions
        return r

    def test_the_chance_rate_is_read_off_each_execution_s_own_board(self):
        """Hitting an evil seat with two of four alive is not the same event as
        hitting one with two of nine, so the denominator travels with the row."""
        s = score([self.rec([execution(True, alive=4, evil_alive=2),
                             execution(False, alive=9, evil_alive=2)])])
        self.assertAlmostEqual(s["execution"]["chance"], (0.5 + 2 / 9) / 2)
        self.assertAlmostEqual(s["execution"]["rate"], 0.5)

    def test_an_execution_on_a_dead_seat_is_counted_apart(self):
        """The day ended and nobody died. Folding it in would read a table that
        spent its days on corpses as a table that executed badly."""
        s = score([self.rec([execution(True), execution(False, was_alive=False)])])
        self.assertEqual(s["execution"]["executions"], 2)
        self.assertEqual(s["execution"]["on_a_living_seat"], 1)
        self.assertEqual(s["execution"]["on_a_dead_seat"], 1)
        self.assertEqual(s["execution"]["rate"], 1.0)

    def test_a_trigger_execution_is_counted_apart_from_the_accuracy(self):
        """It is not a draw from the board. The trigger executes the nominator
        and fires only on a townsfolk one, so it is good with probability 1 -
        pooled into the rate it reads as a table (or a random control) executing
        below chance, which is how the day-1 instrument check failed."""
        s = score([self.rec([execution(True), execution(False, by_vote=False)])])
        d = s["execution"]
        self.assertEqual((d["executions"], d["on_a_living_seat"]), (2, 2))
        self.assertEqual((d["voted_up"], d["by_trigger"]), (1, 1))
        self.assertEqual((d["hits"], d["rate"]), (1, 1.0))
        self.assertEqual(d["trigger_hits"], 0)

    def test_a_trigger_execution_does_not_move_the_chance_rate_either(self):
        """Excluding it from the numerator and leaving it in the denominator of
        ``chance`` would swap one bias for another."""
        s = score([self.rec([execution(True, alive=4, evil_alive=2),
                             execution(False, alive=9, evil_alive=2,
                                       by_vote=False)])])
        self.assertAlmostEqual(s["execution"]["chance"], 0.5)

    def test_the_first_day_figure_is_its_own_denominator(self):
        s = score([self.rec([execution(True, day=1), execution(False, day=2),
                             execution(False, day=3)])])
        self.assertEqual(s["execution"]["on_a_living_seat"], 3)
        self.assertEqual(s["execution_day1"]["on_a_living_seat"], 1)
        self.assertEqual(s["execution_day1"]["rate"], 1.0)

    def test_no_executions_reports_nothing_rather_than_zero(self):
        s = score([self.rec([])])
        self.assertIsNone(s["execution"]["rate"])
        self.assertIsNone(s["execution"]["chance"])


class TestVoteScoring(unittest.TestCase):
    def rec(self, votes) -> GameRecord:
        r = GameRecord(winner="good", cause="demon-dead", days=1, seats=5)
        r.votes = votes
        return r

    def test_a_good_seat_is_right_to_execute_an_evil_one(self):
        s = score([self.rec([vote(True, True), vote(False, False)])])
        self.assertEqual(s["vote_good"]["accuracy"], 1.0)

    def test_an_evil_seat_is_right_to_do_the_opposite(self):
        """Side-relative, and stated rather than assumed - the same hand is a good
        vote for one side and a bad one for the other."""
        s = score([self.rec([vote(True, True, voter_evil=True),
                             vote(False, False, voter_evil=True)])])
        self.assertEqual(s["vote_evil"]["accuracy"], 0.0)

    def test_the_degenerate_policies_ship_on_the_same_denominator(self):
        """An accuracy figure with no floor under it is unreadable: a table voting
        no to everything scores whatever share of nominees happened to be good."""
        s = score([self.rec([vote(False, False), vote(False, False),
                             vote(False, True), vote(False, True)])])
        self.assertEqual(s["vote_good"]["accuracy"], 0.5)
        self.assertEqual(s["vote_good"]["always_no"], 0.5)
        self.assertEqual(s["vote_good"]["always_yes"], 0.5)

    def test_the_misled_stratum_is_split_at_the_vote_and_not_the_game(self):
        """A seat poisoned on night three voted before it was misled. Folding those
        in would credit the poison with the seat's earlier play."""
        s = score([self.rec([vote(True, True, misled=False),
                             vote(True, False, misled=True)])])
        self.assertEqual(s["vote_good_clear"]["votes"], 1)
        self.assertEqual(s["vote_good_clear"]["accuracy"], 1.0)
        self.assertEqual(s["vote_good_misled"]["votes"], 1)
        self.assertEqual(s["vote_good_misled"]["accuracy"], 0.0)

    def test_an_empty_stratum_reports_nothing_rather_than_zero(self):
        s = score([self.rec([vote(True, True)])])
        self.assertEqual(s["vote_good_misled"]["votes"], 0)
        self.assertIsNone(s["vote_good_misled"]["accuracy"])
        self.assertIn("no sample", report(s, args(), 1.0))

    def test_fallback_votes_are_not_model_votes(self):
        """Every vote fell back, but the non-vote decisions keep the run-wide
        rate under the void bar. The model-vote strata must have NO sample, and
        the vote fallback rate is 100%, not the run's."""
        r = self.rec([vote(True, True, fell_back=True),
                      vote(False, False, fell_back=True),
                      vote(True, False, voter_evil=True, fell_back=True)])
        r.decisions, r.fallbacks = 100, 3
        s = score([r])
        self.assertEqual(s["vote_good"]["votes"], 0)
        self.assertIsNone(s["vote_good"]["accuracy"])
        self.assertEqual(s["vote_evil"]["votes"], 0)
        self.assertEqual(s["vote_decisions"], 3)
        self.assertEqual(s["vote_fallbacks"], 3)
        self.assertEqual(s["vote_fallback_rate"], 1.0)
        self.assertLess(s["integrity"]["fallback_rate"], 0.10)

    def test_model_votes_keep_their_own_denominator(self):
        r = self.rec([vote(True, True),
                      vote(False, False, fell_back=True)])
        r.decisions, r.fallbacks = 10, 1
        s = score([r])
        self.assertEqual(s["vote_good"]["votes"], 1)
        self.assertEqual(s["vote_good"]["accuracy"], 1.0)
        self.assertEqual(s["vote_fallback_rate"], 0.5)

    def test_a_vote_fallback_rate_over_the_bar_voids_the_report(self):
        r = self.rec([vote(True, True), vote(False, False, fell_back=True)])
        r.decisions, r.fallbacks = 100, 1     # run-wide 1%, votes at 50%
        self.assertIn("VOID", report(score([r]), args(), 1.0))

    def test_no_votes_at_all_is_not_a_zero_rate(self):
        s = score([self.rec([])])
        self.assertIsNone(s["vote_fallback_rate"])
        self.assertNotIn("VOID", report(s, args(), 1.0))


class TestIntegrityAndRefusals(unittest.TestCase):
    def rec(self, **over) -> GameRecord:
        base = dict(winner="good", cause="demon-dead", days=2, seats=5,
                    decisions=10, fallbacks=0)
        base.update(over)
        return GameRecord(**base)

    def test_an_errored_game_is_excluded_from_every_figure(self):
        s = score([self.rec(), self.rec(error="RuntimeError: boom")])
        self.assertEqual(s["games_requested"], 2)
        self.assertEqual(s["games_completed"], 1)
        self.assertEqual(len(s["errors"]), 1)

    def test_an_errored_game_is_excluded_from_integrity_too(self):
        """The outcome figures already drop errored games; integrity must sum the
        SAME population, or one recorded error reads as the summary and the
        criterion controller disagreeing about the instrument."""
        clean = self.rec()
        dirty = self.rec(error="RuntimeError: boom", decisions=40, fallbacks=3,
                         decision_log=[{"seat": 0, "fell_back": True},
                                       {"seat": 1, "fell_back": False}] * 20)
        s = score([clean, dirty])
        self.assertEqual(s["integrity"]["decisions"], clean.decisions)
        self.assertEqual(s["integrity"]["fallbacks"], clean.fallbacks)
        self.assertEqual(s["integrity"]["games_finished"], 1)

    def test_the_fallback_rate_is_over_decisions_and_not_games(self):
        s = score([self.rec(decisions=100, fallbacks=5)])
        self.assertAlmostEqual(s["integrity"]["fallback_rate"], 0.05)

    def test_a_run_above_the_bar_is_VOIDED_in_its_own_report(self):
        s = score([self.rec(decisions=100, fallbacks=30)])
        self.assertIn("VOID", report(s, args(), 1.0))

    def test_a_clean_run_is_not_voided(self):
        self.assertNotIn("VOID", report(score([self.rec()]), args(), 1.0))

    def test_a_game_with_no_winner_stays_out_of_the_win_rate(self):
        """The day bound is a fact about the table. Putting it in the denominator
        makes the bound look like a result for the other side."""
        s = score([self.rec(), self.rec(winner=None, cause="day-bound")])
        self.assertEqual(s["wins"]["no_winner"], 1)
        self.assertEqual(s["good_win_rate"], 1.0)

    def test_it_refuses_to_infer_deception_from_the_win_rate(self):
        self.assertIn("no deception figure is inferred",
                      report(score([self.rec()]), args(), 1.0))

    def test_the_report_names_the_stopping_rule_beside_the_pooled_figure(self):
        """The pooled execution figure is enriched in mistakes by construction, and
        a reader who does not know that will read it as anti-deduction."""
        out = report(score([self.rec()]), args(), 1.0)
        self.assertIn("stopping rule", out)
        self.assertIn("READ THIS ONE", out)


class TestARealRun(unittest.TestCase):
    def test_a_short_random_run_scores_and_writes_a_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "belfry-smoke.json")
            a = args(games=3, seed=77, out=out)
            records = [one_game(i, a) for i in range(a.games)]
            s = score(records)
            self.assertEqual(s["games_completed"], 3)
            self.assertEqual(s["integrity"]["fallbacks"], 0)
            summary, jsonl = record_paths(out)
            with open(summary, "w", encoding="utf-8") as fh:
                json.dump({"score": s, "args": vars(a)}, fh, indent=2)
            with open(summary, encoding="utf-8") as fh:
                back = json.load(fh)
            self.assertEqual(back["score"]["games_completed"], 3)
            self.assertTrue(jsonl.endswith(".jsonl"))

    def test_every_scored_game_leaves_a_cause_a_reader_can_group_on(self):
        a = args(games=6, seed=500)
        s = score([one_game(i, a) for i in range(a.games)])
        self.assertEqual(sum(s["causes"].values()), s["games_completed"])
        for key in s["causes"]:
            self.assertIn(key, {"demon-dead", "attrition", "bad-execution",
                                "speaker", "day-bound"})


if __name__ == "__main__":
    unittest.main()
