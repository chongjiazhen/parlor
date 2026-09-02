"""The gate #2 pair scorer, on synthetic records.

The unit is a GAME: did the pack win? The pair is the same seeds played with the
pack live against the pack played at random, both against the same live village.
Each void and the pairing check are guards here because the scorer that forgot
one would still print a number.
"""

from __future__ import annotations

import unittest

from eval.gate2_pair_verdict import (
    ARMS,
    EXPECTED,
    Arm,
    dawn_agreement,
    pack_wins,
    settings_voids,
    verdict,
)


def game(idx: int, pack_won: bool, wolves: int = 1, truth: dict | None = None) -> dict:
    truth = truth or {str(s): "pack" if s < wolves else "bystander" for s in range(5)}
    return {"game": idx, "winner": "pack" if pack_won else "village", "truth": truth,
            "votes": [], "decisions": 15, "fallbacks": 0, "recovered": 0}


def arm(name, games, fallback_rate=0.0):
    return Arm(name=name, games=games, fallback_rate=fallback_rate)


class TestPackWins(unittest.TestCase):
    def test_counts_over_winnable_games_only(self):
        games = [game(0, True), game(1, False), game(2, True, wolves=0)]
        self.assertEqual(pack_wins(games), (1, 2))


class TestDawnAgreement(unittest.TestCase):
    def test_pairs_by_index_and_counts_identical_truths(self):
        a = [game(0, True), game(1, False)]
        b = [game(1, True), game(0, False, truth={"0": "bystander", "1": "pack",
                                                   "2": "bystander", "3": "bystander",
                                                   "4": "bystander"})]
        self.assertEqual(dawn_agreement(a, b), (1, 2))


class TestSettingsPin(unittest.TestCase):
    def test_the_arms_differ_in_arm_and_nothing_else(self):
        a, b = (EXPECTED[n] for n in ARMS)
        self.assertEqual({k for k in a if a[k] != b[k]}, {"arm"})

    def test_a_drift_is_named(self):
        args = {**EXPECTED[ARMS[1]], "rounds": 3}
        self.assertTrue(any("rounds" in v for v in settings_voids(ARMS[1], args)))


class TestVerdict(unittest.TestCase):
    def test_a_clear_gap_informs_signed_live_minus_control(self):
        live = arm("llm", [game(i, i % 10 < 8) for i in range(200)])
        ctrl = arm("village", [game(i, i % 10 < 4) for i in range(200)])
        v = verdict(live, ctrl)
        self.assertEqual(v.call, "INFORMS")
        self.assertGreater(v.newcombe[0], 0.0)

    def test_no_gap_is_not_shown(self):
        live = arm("llm", [game(i, i % 2 == 0) for i in range(200)])
        ctrl = arm("village", [game(i, i % 2 == 1) for i in range(200)])
        self.assertEqual(verdict(live, ctrl).call, "NOT SHOWN")

    def test_fallback_over_the_bar_voids(self):
        live = arm("llm", [game(i, i % 10 < 8) for i in range(200)], fallback_rate=0.2)
        ctrl = arm("village", [game(i, i % 10 < 4) for i in range(200)])
        self.assertEqual(verdict(live, ctrl).call, "VOID")

    def test_a_short_arm_refuses(self):
        live = arm("llm", [game(i, i % 10 < 8) for i in range(200)])
        ctrl = arm("village", [game(i, i % 10 < 4) for i in range(120)])
        self.assertEqual(verdict(live, ctrl).call, "REFUSED")


if __name__ == "__main__":
    unittest.main()
