"""The negation-pass scorer - the settings pin and the two refusal counters.

The blind-accuracy arithmetic is `eval.skin_pair_verdict`'s, tested there. What
is new here is the pin's asymmetry - the control predates `--phrasing` and its
records carry no such key, the arm does not get that grace - and the two
counters the criterion names as its PRIMARY statistic, which no other verdict in
this repo computes.
"""

from __future__ import annotations

import unittest

from eval.phrasing_pair_verdict import (ARMS, COMMON, fallback_counts,
                                        rule_refusal_counts, settings_voids)
from eval.skin_pair_verdict import Arm

CONTROL, ARM = ARMS[0][0], ARMS[1][0]


def args(**over) -> dict:
    base = dict(COMMON)
    base.update(over)
    return base


def arm(*games: dict) -> Arm:
    return Arm(name="x", games=list(games), fallback_rate=0.0)


class TestSettingsPin(unittest.TestCase):
    def test_a_matching_control_and_arm_raise_no_void(self):
        self.assertEqual(settings_voids(CONTROL, "as-is", args()), [])
        self.assertEqual(
            settings_voids(ARM, "positive", args(phrasing="positive")), [])

    def test_the_control_may_omit_the_key_because_it_predates_the_flag(self):
        self.assertNotIn("phrasing", args())
        self.assertEqual(settings_voids(CONTROL, "as-is", args()), [])

    def test_the_positive_arm_may_NOT_omit_the_key(self):
        voids = settings_voids(ARM, "positive", args())
        self.assertTrue(any("phrasing" in v for v in voids), voids)

    def test_an_arm_recorded_as_as_is_is_voided(self):
        voids = settings_voids(ARM, "positive", args(phrasing="as-is"))
        self.assertTrue(any("phrasing" in v for v in voids), voids)

    def test_a_control_recorded_as_positive_is_voided(self):
        voids = settings_voids(CONTROL, "as-is", args(phrasing="positive"))
        self.assertTrue(any("phrasing" in v for v in voids), voids)

    def test_a_seed_or_rounds_drift_is_voided(self):
        for key, bad in (("seed", 4000), ("rounds", 3), ("theme", "greek"),
                         ("register", "plain")):
            with self.subTest(key=key):
                voids = settings_voids(CONTROL, "as-is", args(**{key: bad}))
                self.assertTrue(any(key in v for v in voids), voids)


class TestTheRefusalCounters(unittest.TestCase):
    """The primary statistic, so it is counted rather than taken from a rate."""

    def test_fallbacks_are_summed_over_every_game_not_the_scored_subset(self):
        a = arm({"fallbacks": 2, "decisions": 15},
                {"fallbacks": 0, "decisions": 15})
        self.assertEqual(fallback_counts(a), (2, 30))

    def test_attempts_are_decisions_plus_the_refused_ones(self):
        a = arm({"decisions": 15, "refused_attempts": 4,
                 "rule_refused_attempts": 3})
        self.assertEqual(rule_refusal_counts(a), (3, 19))

    def test_a_record_missing_the_keys_counts_zero_rather_than_raising(self):
        self.assertEqual(fallback_counts(arm({})), (0, 0))
        self.assertEqual(rule_refusal_counts(arm({})), (0, 0))


if __name__ == "__main__":
    unittest.main()
