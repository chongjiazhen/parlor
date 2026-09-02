"""The briefing pair scorer - the settings pin and the arm binding.

The arithmetic is `eval.skin_pair_verdict`'s, already tested there. New here: the
control record predates the `--briefing` flag, so its args carry no such key, and
the pin must read that absence as "off" rather than voiding every pair whose
control is older than its arm.
"""

from __future__ import annotations

import unittest

from eval.briefing_pair_verdict import ARMS, EXPECTED, settings_voids


def args(**over) -> dict:
    base = {"arm": "llm", "rounds": 2, "theme": "folk", "seats": 5, "seed": 5000,
            "no_thinking": True, "temperature": 0.8, "model": "qwen36-35b-a3b-iq3"}
    base.update(over)
    return base


class TestSettingsPin(unittest.TestCase):
    def test_the_two_arms_differ_in_briefing_and_nothing_else(self):
        (a, b) = (EXPECTED[n] for n in ARMS)
        moved = {k for k in a if a[k] != b[k]}
        self.assertEqual(moved, {"briefing"})

    def test_a_control_record_that_predates_the_flag_is_not_voided(self):
        self.assertEqual(settings_voids("rounds2", args()), [])
        self.assertEqual(settings_voids("rounds2", args(briefing=False)), [])

    def test_the_briefing_arm_must_say_so(self):
        voids = settings_voids("briefing", args())
        self.assertTrue(any("briefing" in v for v in voids))
        self.assertEqual(settings_voids("briefing", args(briefing=True)), [])

    def test_a_control_played_with_the_briefing_on_is_voided(self):
        voids = settings_voids("rounds2", args(briefing=True))
        self.assertTrue(any("briefing" in v for v in voids))

    def test_a_rounds_drift_is_voided(self):
        voids = settings_voids("briefing", args(briefing=True, rounds=3))
        self.assertTrue(any("rounds" in v for v in voids))


if __name__ == "__main__":
    unittest.main()
