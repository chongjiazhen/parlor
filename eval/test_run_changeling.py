"""The changeling eval lane: the arms, the exclusions, and the refusal to read a
gate off a random side.

The load-bearing test here is the instrument control - the random arm MUST score at
chance. If it does not, either the chance formula or the scorer is wrong, and every
number the lane produces is wrong with it. A scorer is not validated by producing
plausible output.
"""

from __future__ import annotations

import argparse
import inspect
import os
import random
import tempfile
import unittest

import eval.run_changeling
import eval.run_games
from core.runlog import record_paths
from eval.run_changeling import (_chance, land, one_game, report, score,
                                 villager_votes)


def make_args(**kw):
    base = dict(arm="random", backend=None, model="none", rounds=1, retries=0,
                register="character", temperature=0.8, timeout=5.0,
                max_tokens=512, theme=None, seed=1000, games=1, out=None)
    base.update(kw)
    return argparse.Namespace(**base)


def random_records(n: int, seed: int = 1000):
    args = make_args(seed=seed)
    return [one_game(i, args) for i in range(n)]


class TestRandomArmScoresAtChance(unittest.TestCase):
    """The instrument control. Everything else the lane reports is read against
    this, so if the random arm does not land on chance the lane is broken."""

    @classmethod
    def setUpClass(cls):
        cls.records = random_records(300)
        cls.s = score(cls.records)

    def test_blind_accuracy_brackets_the_computed_chance(self):
        g3 = self.s["gate3_deduction"]
        lo, hi = g3["blind_accuracy_ci95"]
        chance = _chance(self.s)
        self.assertLessEqual(lo, chance, "random arm scored ABOVE chance")
        self.assertGreaterEqual(hi, chance, "random arm scored BELOW chance")

    def test_the_random_arm_never_falls_back(self):
        """A fallback IS the random policy, so a nonzero rate here means the arm
        wiring is calling something it should not."""
        self.assertEqual(self.s["integrity"]["fallback_rate"], 0.0)

    def test_the_verdict_refuses_to_read_a_gate_off_the_random_arm(self):
        text = report(self.s, make_args(arm="random"), 1.0)
        self.assertIn("this IS the chance baseline", text)
        self.assertNotIn("gate #3 HOLDS", text)


class TestUnwinnableGamesAreExcludedAndReported(unittest.TestCase):
    """RULES.md measures 2.8% of games seating no wolf at dawn. The village cannot
    win them however it plays, so they leave the denominator and are named."""

    @classmethod
    def setUpClass(cls):
        cls.records = random_records(300)
        cls.s = score(cls.records)

    def test_the_run_actually_contains_some(self):
        self.assertGreater(self.s["games_unwinnable"], 0,
                           "no unwinnable game in range - test proves nothing")

    def test_they_are_out_of_the_scored_denominator(self):
        self.assertEqual(self.s["games_scored"] + self.s["games_unwinnable"],
                         self.s["games_completed"])

    def test_they_are_named_in_the_report_rather_than_averaged_in(self):
        text = report(self.s, make_args(), 1.0)
        self.assertIn("seated no pack at dawn", text)

    def test_scoring_them_in_would_move_the_number(self):
        """Confirms the exclusion is load-bearing, not decoration."""
        g3 = self.s["gate3_deduction"]
        with_all = sum(1 for r in self.records
                       if r.winner == "village") / self.s["games_completed"]
        self.assertNotEqual(round(with_all, 6),
                            round(g3["village_win_rate"], 6))


class TestChanceIsComputedFromTheRunsOwnMix(unittest.TestCase):
    def test_a_two_wolf_dawn_carries_twice_the_chance_of_a_one_wolf_dawn(self):
        one = {"gate3_deduction": {"by_dawn_wolves": {1: (0, 100)}}}
        two = {"gate3_deduction": {"by_dawn_wolves": {2: (0, 100)}}}
        self.assertAlmostEqual(_chance(one), 0.25)
        self.assertAlmostEqual(_chance(two), 0.50)

    def test_unwinnable_games_do_not_drag_chance_down(self):
        mixed = {"gate3_deduction": {"by_dawn_wolves": {0: (0, 50), 1: (0, 100)}}}
        self.assertAlmostEqual(_chance(mixed), 0.25)


class TestVerdicts(unittest.TestCase):
    def setUp(self):
        self.s = score(random_records(60))

    def test_a_high_fallback_rate_VOIDS_the_run(self):
        void = dict(self.s, integrity=dict(self.s["integrity"],
                                           fallback_rate=0.42))
        text = report(void, make_args(arm="llm"), 1.0)
        self.assertIn("VOID", text)
        self.assertNotIn("gate #3 HOLDS", text)

    def test_gate2_stays_unreadable_while_gate3_is_at_chance(self):
        text = report(self.s, make_args(arm="llm"), 1.0)
        self.assertIn("gate #3 not shown", text)
        self.assertIn("Gate #2 is only readable once gate #3 holds", text)

    def test_gate3_holding_makes_gate2_readable(self):
        g3 = dict(self.s["gate3_deduction"], blind_accuracy=0.9,
                  blind_accuracy_ci95=(0.85, 0.95))
        text = report(dict(self.s, gate3_deduction=g3), make_args(arm="llm"), 1.0)
        self.assertIn("gate #3 HOLDS", text)
        self.assertIn("gate #2 readable", text)

    def test_an_empty_blind_stratum_is_REFUSED_not_rendered_as_zero(self):
        g3 = dict(self.s["gate3_deduction"], blind_accuracy=None,
                  blind_accuracy_ci95=None)
        text = report(dict(self.s, gate3_deduction=g3), make_args(arm="llm"), 1.0)
        self.assertIn("BLIND ACCURACY     REFUSED", text)
        self.assertNotIn("BLIND ACCURACY     0.00%", text)


class TestVillagerVotesAreKeyedOnTruth(unittest.TestCase):
    def test_a_seat_holding_pack_is_never_counted_as_a_villager(self):
        """Keying on belief would put a sleeping wolf's vote in the deduction
        denominator, which is the whole error this game makes easy to commit."""
        for rec in random_records(80):
            for v in villager_votes(rec):
                self.assertFalse(v.voter_holds_pack)

    def test_seats_that_believe_pack_but_hold_village_ARE_counted(self):
        found = False
        for rec in random_records(200):
            for v in villager_votes(rec):
                if v.voter_believes_pack:
                    found = True
        self.assertTrue(found, "no sleeper villager in range - the night is inert")


class TestReviewFixes(unittest.TestCase):
    """Regressions for defects found by review 2026-08-27."""

    def test_the_sampler_seed_is_the_GAMES_seed_not_the_runs(self):
        """`2cfe9d5`'s invariant: Backend.seed rides in the payload and one_game
        hands each game the number it deals with. This lane shipped seed=args.seed,
        pinning the sampler to one value for every game in a run."""
        from eval.run_changeling import build_backend
        args = make_args(backend="local", model="m", seed=1000)
        args.no_thinking = True
        self.assertEqual(build_backend(args, 1007).seed, 1007)
        self.assertEqual(build_backend(args, 1000).seed, 1000)

    def test_chance_is_weighted_by_villager_VOTES_not_by_games(self):
        """A 2-wolf dawn yields 3 villager votes against a 1-wolf dawn's 4, so the
        two weightings disagree - 0.357 against 0.375 on an even mix. The rate
        _chance gates is per-vote, so game-weighting set the bar ~1.8 points too
        high and made gate #3 harder than chance."""
        mixed = {"gate3_deduction": {"by_dawn_wolves": {1: (0, 100), 2: (0, 100)}}}
        self.assertAlmostEqual(_chance(mixed), 250 / 700, places=6)
        self.assertNotAlmostEqual(_chance(mixed), 0.375, places=3)

    def test_the_random_reference_is_on_the_scored_denominator(self):
        """It is printed beside a run figure computed over winnable games only."""
        from eval.run_changeling import (MEASURED_RANDOM_VILLAGE_WINS,
                                         MEASURED_RANDOM_VILLAGE_WINS_ALL_GAMES)
        self.assertGreater(MEASURED_RANDOM_VILLAGE_WINS,
                           MEASURED_RANDOM_VILLAGE_WINS_ALL_GAMES)
        self.assertAlmostEqual(MEASURED_RANDOM_VILLAGE_WINS, 0.3951, places=4)

    def test_an_empty_sample_yields_no_interval_rather_than_a_zero_width_one(self):
        from core.stats import wilson
        self.assertIsNone(wilson(0, 0))
        self.assertIsNotNone(wilson(0, 5))

    def test_each_live_seat_gets_its_own_policy_object(self):
        """One shared LLMPolicy makes `upstreams` a single Counter that the record
        sums once per seat, multiplying the census by the live-seat count."""
        from eval.run_changeling import build_policies
        from games.changeling.referee import ChangelingReferee
        args = make_args(arm="llm", backend="local", model="m")
        args.no_thinking = True
        ref = ChangelingReferee.new(5, seed=3, discussion_rounds=1)
        policies = build_policies(ref, args, random.Random(0), seed=3)
        live = [p for p in policies.values() if hasattr(p, "upstreams")]
        self.assertEqual(len(live), 5)
        self.assertEqual(len({id(p) for p in live}), 5, "seats share one policy")


class TestBothDriversAgreeOnWhatOutMeans(unittest.TestCase):
    """``--out`` is the summary path verbatim; the JSONL is ``out.jsonl``.

    The two drivers had one convention each until 2026-08-28, and the disagreement
    cost S2's records their names: a launcher written from cabal's twin passed
    ``--out eval/records/s2.json`` and ``run_changeling`` composed ``s2.json.json``.
    Pinned here rather than in one driver's file because the defect was that the two
    disagreed - a test living beside either one cannot see that.
    """

    def test_the_summary_path_is_verbatim_and_the_jsonl_is_its_sibling(self):
        self.assertEqual(record_paths("eval/records/s2.json"),
                         ("eval/records/s2.json", "eval/records/s2.json.jsonl"))

    def test_neither_driver_composes_its_own_suffix(self):
        for module in (eval.run_changeling, eval.run_games):
            source = inspect.getsource(module)
            self.assertNotIn('f"{args.out}.json"', source, module.__name__)
            self.assertNotIn('f"{args.out}.jsonl"', source, module.__name__)

    def test_a_landed_record_goes_to_the_sibling_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "run.json")
            args = make_args(out=out)
            land(0, one_game(0, args), args)
            self.assertTrue(os.path.exists(out + ".jsonl"))
            self.assertFalse(os.path.exists(out + ".json.jsonl"))


if __name__ == "__main__":
    unittest.main()
