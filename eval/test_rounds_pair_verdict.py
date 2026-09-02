"""The discussion-length pair scorer - the settings pin and the arm binding.

The arithmetic is `eval.skin_pair_verdict`'s, already tested there. What is new
here is the binding: a record scored as the three-round arm must SAY it was
played at three rounds, or the scorer refuses. Every other paired read in this
repo got that pin after a launcher default and a criterion disagreed once.
"""

from __future__ import annotations

import unittest

from eval.rounds_pair_verdict import ARMS, EXPECTED, settings_voids


def args(**over) -> dict:
    base = {"arm": "llm", "rounds": 2, "theme": "folk", "seats": 5, "seed": 5000,
            "no_thinking": True, "temperature": 0.8, "model": "qwen36-35b-a3b-iq3"}
    base.update(over)
    return base


class TestSettingsPin(unittest.TestCase):
    def test_the_two_arms_differ_in_rounds_and_nothing_else(self):
        (a, b) = (EXPECTED[n] for n in ARMS)
        moved = {k for k in a if a[k] != b[k]}
        self.assertEqual(moved, {"rounds"})

    def test_a_matching_record_raises_no_void(self):
        self.assertEqual(settings_voids(ARMS[0], args()), [])
        self.assertEqual(settings_voids(ARMS[1], args(rounds=3)), [])

    def test_the_three_round_arm_played_at_two_rounds_is_voided(self):
        voids = settings_voids(ARMS[1], args(rounds=2))
        self.assertTrue(any("rounds" in v for v in voids))

    def test_a_theme_drift_is_voided(self):
        voids = settings_voids(ARMS[0], args(theme="greek"))
        self.assertTrue(any("theme" in v for v in voids))

    def test_a_seed_drift_is_voided(self):
        voids = settings_voids(ARMS[0], args(seed=4000))
        self.assertTrue(any("seed" in v for v in voids))


if __name__ == "__main__":
    unittest.main()
