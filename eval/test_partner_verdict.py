"""The partner-protection arm's scorer - the guards, and the pin to the criterion.

The arithmetic is `eval.changeling_audit`'s `partner_votes` and
`eval.skin_pair_verdict`'s Newcombe, both tested where they live. What is new
here is the binding, and every test below is a guard the criterion names:
settings that must match the frozen file, a fallback bar, a votes floor, and the
census check that catches a control dealt something other than the arm's deal.

The settings test reads `docs/changeling-partner-criterion.md` itself rather than
a copy of its numbers, because the failure this repo has already paid for is a
launcher and a criterion disagreeing while both looked right.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from eval.partner_verdict import (
    CRITERION,
    EXPECTED,
    VOTES_FLOOR,
    Arm,
    census_void,
    partner,
    settings_voids,
    verdict,
)

TRUTH = {"0": "spotter", "1": "pack", "2": "bystander", "3": "swapper",
         "4": "pack"}


def game(index, log, votes):
    return {"game": index, "log": log, "votes": votes, "truth": TRUTH,
            "dealt": dict(TRUTH), "accused": [], "winner": "pack"}


def met(index, voted):
    """Seat 1 is told seat 4 is its fellow, and votes ``voted``."""
    return game(index, ["meet: seat 1 (pack) sees [4]"],
                [{"seat": 1, "target": voted, "target_holds_pack": False}])


def arm(hits, misses, first=0, fallback=0.0):
    games = [met(first + i, 4) for i in range(hits)]
    games += [met(first + hits + i, 2) for i in range(misses)]
    return Arm(name="cl-partner", games=games, fallback_rate=fallback)


def args(**over) -> dict:
    base = dict(EXPECTED)
    base.update(over)
    return base


class TestSettingsPin(unittest.TestCase):
    def test_a_matching_record_raises_no_void(self):
        self.assertEqual(settings_voids(args()), [])

    def test_a_seed_drift_is_voided(self):
        self.assertTrue(any("seed" in v for v in settings_voids(args(seed=5000))))

    def test_a_rounds_drift_is_voided(self):
        self.assertTrue(any("rounds" in v for v in settings_voids(args(rounds=3))))

    def test_a_theme_drift_is_voided(self):
        self.assertTrue(any("theme" in v
                            for v in settings_voids(args(theme="greek"))))

    def test_the_expected_block_agrees_with_the_frozen_criterion(self):
        """The module's settings are the criterion's, read from the file."""
        text = Path(CRITERION).read_text(encoding="utf-8")
        for flag, value in (("--seed", EXPECTED["seed"]),
                            ("--rounds", EXPECTED["rounds"]),
                            ("--seats", EXPECTED["seats"]),
                            ("--arm", EXPECTED["arm"]),
                            ("--theme", EXPECTED["theme"])):
            self.assertIn(f"{flag} {value}", text, f"{flag} disagrees with {CRITERION}")


class TestPartnerCount(unittest.TestCase):
    def test_the_count_is_the_audit_s_own(self):
        from eval.changeling_audit import partner_votes
        games = arm(3, 7).games
        self.assertEqual(partner(games), partner_votes(games)[:2])

    def test_a_seat_told_nobody_is_outside_the_denominator(self):
        games = [game(0, ["meet: seat 1 (pack) sees no one"],
                      [{"seat": 1, "target": 4, "target_holds_pack": False}])]
        self.assertEqual(partner(games), (0, 0))


class TestVerdict(unittest.TestCase):
    def control(self, hits, misses):
        return Arm(name="cl-partner-random", games=arm(hits, misses).games,
                   fallback_rate=0.0)

    def test_a_gap_that_excludes_zero_informs(self):
        v = verdict(arm(30, 170), self.control(260, 740))
        self.assertEqual(v.call, "INFORMS")
        self.assertLess(v.diff, 0)

    def test_a_gap_that_spans_zero_is_not_shown(self):
        v = verdict(arm(50, 150), self.control(260, 740))
        self.assertEqual(v.call, "NOT SHOWN")

    def test_fallback_above_the_bar_voids_and_still_reports_the_figure(self):
        v = verdict(arm(30, 170, fallback=0.11), self.control(260, 740))
        self.assertEqual(v.call, "VOID")
        self.assertIsNotNone(v.diff)
        self.assertIsNotNone(v.newcombe)

    def test_too_few_eligible_votes_is_refused(self):
        v = verdict(arm(10, VOTES_FLOOR - 11), self.control(260, 740))
        self.assertEqual(v.call, "REFUSED")

    def test_the_floor_counts_the_arm_not_the_control(self):
        v = verdict(arm(10, VOTES_FLOOR - 11), self.control(2600, 7400))
        self.assertEqual(v.call, "REFUSED")


class TestCensus(unittest.TestCase):
    def test_a_control_sharing_the_arm_s_deals_agrees(self):
        a = arm(30, 170)
        ctrl = Arm(name="c", games=arm(60, 940).games, fallback_rate=0.0)
        self.assertIsNone(census_void(a.games, ctrl.games))

    def test_a_control_dealt_something_else_is_voided(self):
        a = arm(30, 170)
        other = [met(i, 4) for i in range(150)]
        other += [game(150 + i, ["meet: seat 1 (pack) sees no one"], [])
                  for i in range(850)]
        self.assertIsNotNone(census_void(a.games, other))

    def test_a_control_dealt_something_else_voids_the_VERDICT(self):
        """The guard has to fire through `verdict`, not only when called directly -
        a census test that never reaches the caller leaves the void unwired."""
        other = [met(i, 4) for i in range(150)]
        other += [game(150 + i, ["meet: seat 1 (pack) sees no one"], [])
                  for i in range(850)]
        v = verdict(arm(30, 170), Arm(name="c", games=other, fallback_rate=0.0))
        self.assertEqual(v.call, "VOID")
        self.assertTrue(any("census" in r for r in v.reasons))

    def test_the_check_reads_only_the_shared_indices(self):
        """The control is five times the arm; its extra games are not compared."""
        a = arm(30, 170)
        ctrl = arm(30, 170).games + [
            game(1000 + i, ["meet: seat 1 (pack) sees no one"], [])
            for i in range(800)]
        self.assertIsNone(census_void(a.games, ctrl))


if __name__ == "__main__":
    unittest.main()
