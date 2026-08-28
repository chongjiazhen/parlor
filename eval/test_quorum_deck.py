"""The deck arithmetic, and the control that keeps the sweep honest."""

from __future__ import annotations

import unittest
from math import comb

from eval.quorum_deck import DRIFT_TOLERANCE, ExactRates, Sweep, exact_rates, report, sweep
from games.quorum.roles import SETUP_5, Setup


class TestExactRates(unittest.TestCase):
    def test_it_agrees_with_the_closed_form_it_declines_to_use(self):
        """The module enumerates so a third card kind would not need it rewritten.
        This is the hypergeometric it is enumerating, written out once, here - two
        derivations of one number, which is the only way to know either is right."""
        e = exact_rates()
        total = comb(17, 3)
        self.assertEqual(e.draws, total)
        self.assertAlmostEqual(e.p_forced_writ, comb(11, 3) / total, places=12)
        self.assertAlmostEqual(e.p_forced_charter, comb(6, 3) / total, places=12)
        self.assertAlmostEqual(e.p_forced, (comb(11, 3) + comb(6, 3)) / total,
                               places=12)

    def test_the_enactor_pair_rate_is_the_proposers_uniform_discard(self):
        """A proposer discarding uniformly leaves a matching pair always when it
        drew three of a kind, and one time in three otherwise."""
        e = exact_rates()
        mixed = 1.0 - e.p_forced
        self.assertAlmostEqual(e.p_pair_same, e.p_forced + mixed / 3.0, places=12)

    def test_the_asymmetry_is_what_makes_a_defence_available(self):
        """'I had no choice' is 8.25x more available toward the minority than
        toward the majority, and that ratio is the deck's, not a model's."""
        e = exact_rates()
        self.assertAlmostEqual(e.asymmetry, comb(11, 3) / comb(6, 3), places=12)
        self.assertGreater(e.p_forced_writ, e.p_forced_charter)

    def test_it_is_derived_from_the_setup_and_not_written_down(self):
        balanced = Setup(n=5, roles=SETUP_5.roles, deck_charter=8, deck_writ=9)
        e = exact_rates(balanced)
        self.assertNotAlmostEqual(e.p_forced, exact_rates().p_forced, places=4)
        self.assertLess(e.asymmetry, exact_rates().asymmetry)

    def test_a_deck_of_one_kind_forces_every_draw(self):
        one = Setup(n=5, roles=SETUP_5.roles, deck_charter=0, deck_writ=17)
        e = exact_rates(one)
        self.assertAlmostEqual(e.p_forced, 1.0, places=12)
        self.assertEqual(e.p_forced_charter, 0.0)


class TestSweep(unittest.TestCase):
    def test_the_same_seed_is_the_same_sweep(self):
        a, b = sweep(12, seed=5), sweep(12, seed=5)
        self.assertEqual((a.events, a.forced, a.pair_same),
                         (b.events, b.forced, b.pair_same))
        self.assertEqual(a.seeds, b.seeds)

    def test_a_different_seed_moves_it(self):
        a, b = sweep(12, seed=5), sweep(12, seed=500)
        self.assertNotEqual(a.seeds, b.seeds)

    def test_every_game_is_replayable_on_its_own(self):
        s = sweep(6, seed=77)
        self.assertEqual(s.seeds, list(range(77, 83)))

    def test_the_realized_rate_lands_near_the_arithmetic(self):
        """The instrument control, run small. Reshuffle drift is real - cards leave
        play when enacted - so this asserts the ORDER, not equality."""
        e = exact_rates()
        s = sweep(120, seed=0)
        self.assertGreater(s.events, 400)
        self.assertLess(abs(s.rate - e.p_forced), DRIFT_TOLERANCE)


class TestReport(unittest.TestCase):
    def _obs(self, forced: int, events: int) -> Sweep:
        return Sweep(games=100, events=events, forced=forced,
                     forced_writ=forced, pair_same=events // 2, majority_wins=20)

    def test_drift_inside_tolerance_says_the_arithmetic_may_be_quoted(self):
        e = exact_rates()
        lines = "\n".join(report(e, self._obs(int(1000 * e.p_forced), 1000)))
        self.assertIn("within tolerance", lines)
        self.assertNotIn("NOT a fair denominator", lines)

    def test_drift_outside_tolerance_refuses_the_arithmetic(self):
        """Mutation-shaped: a sweep that disagrees with the deck must be SAID to
        disagree. Without this the tolerance is a constant nothing reads."""
        e = exact_rates()
        lines = "\n".join(report(e, self._obs(700, 1000)))
        self.assertIn("NOT a fair denominator", lines)
        self.assertIn("EXCLUDES the fresh-deck figure", lines)

    def test_the_control_win_split_is_labelled_as_a_baseline(self):
        lines = "\n".join(report(exact_rates(), self._obs(272, 1000)))
        self.assertIn("chance baseline", lines)
        self.assertIn("NOT a claim about either side", lines)


if __name__ == "__main__":
    unittest.main()
