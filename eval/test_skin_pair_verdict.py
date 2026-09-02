"""The name-form pair scorer, on synthetic records.

The unit it grades is a DIFFERENCE between two arms played on the same seeds, and
the calls it can make were fixed in docs/changeling-skin-pair-criterion.md before
either arm existed. Each void is a guard here because the scorer that forgot one
would still print a number.
"""

from __future__ import annotations

import unittest

from eval.skin_pair_verdict import (
    BLIND_FLOOR_VOTES,
    REFERENCE_CHANCE,
    Arm,
    newcombe,
    own_bar,
    paired_bootstrap,
    verdict,
)


def game(idx: int, blind_hits: int, blind_misses: int, wolves: int = 1) -> dict:
    """A five-seat game whose villager votes are all in the `none` stratum."""
    truth = {str(s): "pack" if s < wolves else "bystander" for s in range(5)}
    votes = []
    for k in range(blind_hits + blind_misses):
        seat = wolves + (k % (5 - wolves))
        votes.append({"seat": seat, "target": 0 if k < blind_hits else 4,
                      "voter_holds_pack": False, "voter_believes_pack": False,
                      "voter_diverged": False,
                      "target_holds_pack": k < blind_hits,
                      "knowledge_class": "none"})
    return {"game": idx, "winner": "village", "truth": truth, "votes": votes,
            "decisions": 15, "fallbacks": 0, "recovered": 0}


def arm(name: str, games: list[dict], fallback_rate: float = 0.0) -> Arm:
    return Arm(name=name, games=games, fallback_rate=fallback_rate)


class TestNewcombe(unittest.TestCase):
    def test_identical_proportions_straddle_zero(self):
        lo, hi = newcombe(40, 100, 40, 100)
        self.assertLess(lo, 0.0)
        self.assertGreater(hi, 0.0)

    def test_a_large_gap_excludes_zero_and_is_signed_b_minus_a(self):
        lo, hi = newcombe(30, 100, 60, 100)
        self.assertGreater(lo, 0.0)
        self.assertAlmostEqual((lo + hi) / 2, 0.30, delta=0.03)

    def test_refuses_an_empty_arm(self):
        self.assertIsNone(newcombe(0, 0, 5, 10))


class TestPairedBootstrap(unittest.TestCase):
    def test_identical_arms_give_a_zero_width_interval_at_zero(self):
        games = [game(i, 1, 1) for i in range(30)]
        lo, hi = paired_bootstrap(games, games)
        self.assertEqual((lo, hi), (0.0, 0.0))

    def test_pairs_by_game_index_not_by_position(self):
        a = [game(i, 1, 1) for i in range(30)]
        b = list(reversed([game(i, 2, 0) for i in range(30)]))
        lo, hi = paired_bootstrap(a, b)
        self.assertGreater(lo, 0.0)


class TestOwnBar(unittest.TestCase):
    def test_a_control_within_a_point_leaves_the_reference_as_the_bar(self):
        bar, note = own_bar(REFERENCE_CHANCE + 0.005)
        self.assertEqual(bar, REFERENCE_CHANCE)

    def test_a_control_more_than_a_point_off_becomes_the_bar(self):
        bar, note = own_bar(REFERENCE_CHANCE + 0.02)
        self.assertAlmostEqual(bar, REFERENCE_CHANCE + 0.02)


class TestVerdict(unittest.TestCase):
    def test_a_clear_gap_informs(self):
        a = arm("greek", [game(i, 1, 2) for i in range(120)])
        b = arm("greek-named", [game(i, 2, 1) for i in range(120)])
        self.assertEqual(verdict(a, b).call, "INFORMS")

    def test_no_gap_is_not_shown(self):
        a = arm("greek", [game(i, 1, 1) for i in range(120)])
        b = arm("greek-named", [game(i, 1, 1) for i in range(120)])
        self.assertEqual(verdict(a, b).call, "NOT SHOWN")

    def test_fallback_over_the_bar_on_either_arm_voids(self):
        a = arm("greek", [game(i, 1, 2) for i in range(120)], fallback_rate=0.11)
        b = arm("greek-named", [game(i, 2, 1) for i in range(120)])
        self.assertEqual(verdict(a, b).call, "VOID")

    def test_a_thin_blind_stratum_on_either_arm_refuses(self):
        a = arm("greek", [game(i, 1, 2) for i in range(120)])
        thin = [game(i, 1, 0) for i in range(BLIND_FLOOR_VOTES - 1)]
        b = arm("greek-named", thin)
        self.assertEqual(verdict(a, b).call, "REFUSED")


if __name__ == "__main__":
    unittest.main()
