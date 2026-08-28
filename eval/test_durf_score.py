"""The scorer's denominators, its grading table, and the instrument controls.

The test that matters most here is ``test_the_two_degenerate_arms_reproduce_the_published_baselines``.
``games/durf/fixtures/README.md`` publishes 61.9% / 38.1% over the 42 declarations
that admit a roll answer, and 54.2% / 33.3% over all 48, and it publishes them as
the bar a model has to clear. A scorer that returns different numbers for those
two arms is wrong about its own denominator, and every rate it prints beside them
is wrong in the same direction - silently, since a wrong baseline flatters.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import tempfile
import unittest

from eval import durf_score as ds
from games.durf import adjudicate, fixture


def make_args(**kw):
    base = dict(arm="random", backend=None, model="none", retries=0,
                temperature=0.8, timeout=5.0, max_tokens=512, no_thinking=False,
                seed=7, limit=None, out=None)
    base.update(kw)
    return argparse.Namespace(**base)


class Denominators(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = fixture.load()

    def _score(self, arm_name):
        arm = adjudicate.build_arm(arm_name, rng=random.Random(7))
        return ds.score(ds.run_items(self.fx, arm), self.fx)

    def test_the_two_degenerate_arms_reproduce_the_published_baselines(self):
        always = self._score("always-roll")
        never = self._score("never-roll")
        self.assertAlmostEqual(always["decision1"]["rate"], 26 / 42, places=6)
        self.assertAlmostEqual(never["decision1"]["rate"], 16 / 42, places=6)
        self.assertAlmostEqual(always["decision1"]["all48"]["rate"], 26 / 48, places=6)
        self.assertAlmostEqual(never["decision1"]["all48"]["rate"], 16 / 48, places=6)
        # ...and the derived baseline block agrees with the arms that play them.
        b = always["decision1"]["baselines"]
        self.assertAlmostEqual(b["always_roll"], 26 / 42, places=6)
        self.assertAlmostEqual(b["never_roll"], 16 / 42, places=6)

    def test_the_false_pass_pool_is_the_rolls_plus_the_traps(self):
        s = self._score("never-roll")
        self.assertEqual(s["false_pass"]["n"], 26 + 6)
        # never-roll grants every trap outright and skips every required roll
        self.assertEqual(s["false_pass"]["hits"], 32)
        self.assertEqual(s["false_pass"]["trap_granted_outright"], 6)
        self.assertEqual(s["false_pass"]["trap_granted_as_roll"], 0)

    def test_the_false_check_denominator_excludes_the_traps(self):
        s = self._score("always-roll")
        self.assertEqual(s["false_check"]["n"], 16)
        self.assertEqual(s["false_check"]["hits"], 16)
        # and a trap it called for a roll on is a False Pass, not a False Check
        self.assertEqual(s["false_pass"]["trap_granted_as_roll"], 6)

    def test_the_morale_split_is_six_six_so_a_constant_answer_scores_half(self):
        for arm in ("always-roll", "never-roll"):
            self.assertAlmostEqual(self._score(arm)["morale"]["rate"], 0.5, places=6)

    def test_every_item_lands_in_exactly_one_outcome(self):
        arm = adjudicate.build_arm("random", rng=random.Random(11))
        records = ds.run_items(self.fx, arm)
        outcomes = {ds.CORRECT, ds.FALSE_PASS, ds.FALSE_CHECK, ds.OVER_REFUSAL,
                    ds.REFUSAL}
        self.assertTrue(all(r.outcome in outcomes for r in records))
        self.assertEqual(len(records), 60)


class Grading(unittest.TestCase):
    """The table in ``grade_declaration``, one cell at a time."""

    TRAP = {"roll": False, "attribute": None, "opposed": False, "refuse": True}
    ROLL = {"roll": True, "attribute": "DEX", "opposed": True, "refuse": False}
    NONE = {"roll": False, "attribute": None, "opposed": False, "refuse": False}

    def grade(self, label, **ruling):
        return ds.grade_declaration(label, adjudicate.Ruling(**ruling))[0]

    def test_a_trap_answered_illegal_is_correct(self):
        self.assertEqual(self.grade(self.TRAP, ruling="illegal"), ds.CORRECT)

    def test_a_trap_granted_either_way_is_a_false_pass(self):
        self.assertEqual(self.grade(self.TRAP, ruling="no_roll"), ds.FALSE_PASS)
        self.assertEqual(self.grade(self.TRAP, ruling="roll", attribute="STR"),
                         ds.FALSE_PASS)

    def test_skipping_a_required_roll_is_a_false_pass(self):
        self.assertEqual(self.grade(self.ROLL, ruling="no_roll"), ds.FALSE_PASS)

    def test_demanding_a_roll_where_none_is_due_is_a_false_check(self):
        self.assertEqual(self.grade(self.NONE, ruling="roll", attribute="STR"),
                         ds.FALSE_CHECK)

    def test_illegal_on_a_legal_declaration_is_an_over_refusal_not_a_false_check(self):
        # It has to be counted somewhere: an arm that ruled everything illegal
        # would otherwise post a perfect False Pass and a perfect False Check.
        self.assertEqual(self.grade(self.NONE, ruling="illegal"), ds.OVER_REFUSAL)
        self.assertEqual(self.grade(self.ROLL, ruling="illegal"), ds.OVER_REFUSAL)

    def test_decline_is_a_refusal_on_every_kind_of_declaration(self):
        for label in (self.TRAP, self.ROLL, self.NONE):
            self.assertEqual(self.grade(label, ruling="decline"), ds.REFUSAL)

    def test_the_attribute_is_only_graded_on_a_roll_it_got_right(self):
        _, attr_err, opp_err = ds.grade_declaration(
            self.ROLL, adjudicate.Ruling(ruling="roll", attribute="STR", opposed=False))
        self.assertTrue(attr_err)
        self.assertTrue(opp_err)
        _, attr_err, _ = ds.grade_declaration(
            self.ROLL, adjudicate.Ruling(ruling="roll", attribute="DEX", opposed=True))
        self.assertFalse(attr_err)

    def test_a_missed_morale_moment_and_an_over_called_one_are_different_errors(self):
        self.assertEqual(ds.grade_morale({"morale": True},
                                         adjudicate.MoraleCall(morale=False)),
                         ds.FALSE_PASS)
        self.assertEqual(ds.grade_morale({"morale": False},
                                         adjudicate.MoraleCall(morale=True)),
                         ds.FALSE_CHECK)
        self.assertEqual(ds.grade_morale({"morale": True},
                                         adjudicate.MoraleCall(morale=None)),
                         ds.REFUSAL)


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = fixture.load()
        arm = adjudicate.build_arm("always-roll")
        cls.s = ds.score(ds.run_items(cls.fx, arm), cls.fx)

    def test_a_degenerate_arm_does_not_clear_the_floor_control(self):
        # The control's whole job: a constant policy cannot pass it, by
        # construction, because the bar IS the better constant policy.
        self.assertFalse(self.s["floor_control"]["passes"])
        self.assertIn("VOID", "\n".join(
            ds.report(self.s, make_args(arm="always-roll"), 0.1)))

    def test_the_floor_bar_is_derived_from_the_floor_tier_not_a_literal(self):
        bar = self.s["floor_control"]["bar"]
        self.assertAlmostEqual(bar, max(
            v for v in self.s["tiers"]["floor"]["baselines"].values() if v is not None))

    def test_the_control_is_graded_on_the_interval_floor_not_the_point(self):
        s = dict(self.s, floor_control=ds._floor_bar(
            {"rate": 0.9, "ci95": (0.4, 0.99), "baselines": {"always_roll": 0.5,
                                                             "never_roll": 0.3}}))
        self.assertFalse(s["floor_control"]["passes"])
        s = dict(self.s, floor_control=ds._floor_bar(
            {"rate": 0.9, "ci95": (0.6, 0.99), "baselines": {"always_roll": 0.5,
                                                             "never_roll": 0.3}}))
        self.assertTrue(s["floor_control"]["passes"])

    def test_a_run_over_the_void_bar_prints_no_rates_at_all(self):
        s = dict(self.s, integrity=dict(self.s["integrity"], fallback_rate=0.42))
        text = "\n".join(ds.report(s, make_args(), 0.1))
        self.assertIn("VOID", text)
        self.assertNotIn("False Pass", text)

    def test_the_report_names_the_ruleset_and_credits_the_author(self):
        # CC BY 4.0 attribution is a licence obligation, so it rides on the output
        # a reader actually sees rather than only in a docstring.
        text = "\n".join(ds.report(self.s, make_args(), 0.1))
        self.assertIn("DURF 2.2 (2021)", text)
        self.assertIn("Emiel Boven", text)


class DriverConventions(unittest.TestCase):
    def test_the_driver_does_not_compose_its_own_record_suffixes(self):
        # Same pin both game drivers carry: `--out` is the summary path VERBATIM
        # and the JSONL is its sibling, so the paths come from `record_paths`.
        import inspect
        source = inspect.getsource(ds)
        self.assertNotIn('f"{args.out}.json"', source)
        self.assertNotIn('f"{args.out}.jsonl"', source)

    def test_a_landed_item_is_written_as_it_finishes(self):
        fx = fixture.load()
        arm = adjudicate.build_arm("never-roll")
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "durf-test.json")
            lines = []
            ds.run_items(fx, arm, limit=2,
                         on_land=lambda i, r: lines.append(ds.as_line(i, r)))
            self.assertEqual(len(lines), 4)
            row = json.loads(lines[0])
            self.assertEqual(row["kind"], "declaration")
            self.assertIn("outcome", row)
            self.assertIn("decision_log", row)
            self.assertEqual(row["decision_log"][0]["seat"], 0)
            self.assertFalse(os.path.exists(out))

    def test_the_llm_arm_refuses_to_start_with_no_endpoint(self):
        # A live arm with no backend would fall back on every item and score the
        # random adjudicator - the same door-check both game drivers make.
        import sys
        argv = sys.argv
        sys.argv = ["durf_score", "--arm", "llm"]
        try:
            with self.assertRaises(SystemExit):
                ds.main()
        finally:
            sys.argv = argv


if __name__ == "__main__":
    unittest.main()
