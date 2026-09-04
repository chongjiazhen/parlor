"""The turn-taking pair scorer - the settings pin, and the one absent key.

The arithmetic is `eval.skin_pair_verdict`'s, already tested there. What is new
here is the binding: a record scored as the random-active arm must SAY it was
played that way, or the scorer refuses - and a record with no `turns` key at all
is read as the shipped order, because the flag postdates the driver and S22's
control may have been played before it landed.
"""

from __future__ import annotations

import unittest

from eval.turns_pair_verdict import ARMS, EXPECTED, STEMS, settings_voids
from games.changeling.referee import TURNS_FIXED, TURNS_RANDOM_ACTIVE


def args(**over) -> dict:
    base = {"arm": "llm", "rounds": 2, "theme": "folk", "seats": 5, "seed": 5000,
            "no_thinking": True, "temperature": 0.8,
            "model": "qwen36-35b-a3b-iq3", "turns": TURNS_FIXED}
    base.update(over)
    return base


class TestSettingsPin(unittest.TestCase):
    def test_the_two_arms_differ_in_turns_and_nothing_else(self):
        (a, b) = (EXPECTED[n] for n in ARMS)
        moved = {k for k in a if a[k] != b[k]}
        self.assertEqual(moved, {"turns"})

    def test_arm_one_is_s22s_record_reused_not_a_new_one(self):
        self.assertEqual(STEMS["fixed"], "cl-rounds2")

    def test_a_matching_record_raises_no_void(self):
        self.assertEqual(settings_voids("fixed", args()), [])
        self.assertEqual(
            settings_voids("random-active", args(turns=TURNS_RANDOM_ACTIVE)), [])

    def test_the_random_active_arm_played_under_fixed_order_is_voided(self):
        voids = settings_voids("random-active", args())
        self.assertTrue(any("turns" in v for v in voids))

    def test_a_rounds_drift_is_voided(self):
        self.assertTrue(any("rounds" in v
                            for v in settings_voids("fixed", args(rounds=3))))

    def test_a_seed_drift_is_voided(self):
        self.assertTrue(any("seed" in v
                            for v in settings_voids("fixed", args(seed=4000))))


class TestTheAbsentTurnsKey(unittest.TestCase):
    """The one back-compatible default, and the half of it that must still bite."""

    def test_a_record_predating_the_flag_reads_as_fixed(self):
        pre = args()
        pre.pop("turns")
        self.assertEqual(settings_voids("fixed", pre), [])

    def test_the_random_active_arm_with_no_turns_key_is_still_voided(self):
        pre = args()
        pre.pop("turns")
        voids = settings_voids("random-active", pre)
        self.assertTrue(any("turns" in v for v in voids))


if __name__ == "__main__":
    unittest.main()
