"""``eval/sequential.py`` pinned: the published constants, the null error rate,
the undeclared-look guard, and determinism.

The guard test was written BEFORE the guard and run red against a ``look`` that
returned CONTINUE for an undeclared total - the red run is the mutation check
(`CLAUDE.md`). The reference constants are the classic O'Brien-Fleming and
Pocock values from the published tables, recomputed here by the module's own
recursion rather than copied in as the answer.
"""
from __future__ import annotations

import math
import random
import unittest

from core.stats import wilson
from eval import sequential as seq


class UndeclaredLookGuard(unittest.TestCase):
    def setUp(self):
        self.b = seq.design(272, [0.5, 1.0], 0.025, 0.3014, "obf")

    def test_a_look_at_an_undeclared_total_is_refused(self):
        # 100 blind votes is neither look; 136 and 272 are.
        with self.assertRaises(seq.UndeclaredLook):
            seq.look(self.b, 40, 100)

    def test_the_refusal_names_the_declared_totals(self):
        with self.assertRaises(seq.UndeclaredLook) as cm:
            seq.look(self.b, 40, 137)
        self.assertIn("(136, 272)", str(cm.exception))

    def test_declared_totals_are_read(self):
        self.assertEqual(seq.look(self.b, self.b.looks[0].min_hits, 136), seq.CROSSED)
        self.assertEqual(seq.look(self.b, self.b.looks[0].min_hits - 1, 136), seq.CONTINUE)
        self.assertEqual(seq.look(self.b, self.b.looks[1].min_hits, 272), seq.CROSSED)


class ReferenceBoundaries(unittest.TestCase):
    """Classic O'Brien-Fleming c_k = C sqrt(K/k) and Pocock c_k = C constants at
    one-sided alpha 0.025 (two-sided 0.05 in the tables): C_B(2)=2.797,
    C_B(3)=3.471, C_B(4)=4.049, C_B(5)=4.562; C_P(2)=2.178, C_P(3)=2.289,
    C_P(4)=2.361, C_P(5)=2.413. Tolerance 0.005 in z - the tables carry three
    decimals and halving the grid step moves the fourth."""

    TOL = 0.002

    def test_obf_k2(self):
        c = seq.classic_boundaries(2, 0.025, "obf")
        self.assertAlmostEqual(c[0], 2.797, delta=self.TOL)
        self.assertAlmostEqual(c[1], 1.977, delta=self.TOL)

    def test_obf_k3(self):
        c = seq.classic_boundaries(3, 0.025, "obf")
        for got, want in zip(c, [3.471, 2.454, 2.004]):
            self.assertAlmostEqual(got, want, delta=self.TOL)

    def test_obf_k4_k5_constants(self):
        self.assertAlmostEqual(seq.classic_boundaries(4, 0.025, "obf")[0], 4.049, delta=self.TOL)
        self.assertAlmostEqual(seq.classic_boundaries(5, 0.025, "obf")[0], 4.562, delta=self.TOL)

    def test_pocock_constants(self):
        for k, want in ((2, 2.178), (3, 2.289), (4, 2.361), (5, 2.413)):
            self.assertAlmostEqual(seq.classic_boundaries(k, 0.025, "pocock")[0], want,
                                   delta=self.TOL, msg=f"K={k}")

    def test_one_look_is_the_single_test(self):
        z = seq.z_boundaries([1.0], 0.025, "obf")[0]
        self.assertAlmostEqual(z, seq.norm_ppf(0.975), delta=1e-6)
        self.assertAlmostEqual(z, 1.95996, delta=1e-4)

    def test_spending_boundaries_are_conservative_early(self):
        # OBF-type spending: the first boundary is far above the last, and the
        # last sits just above the single-look 1.96. Pocock-type: flatter.
        obf = seq.z_boundaries([0.5, 1.0], 0.025, "obf")
        poc = seq.z_boundaries([0.5, 1.0], 0.025, "pocock")
        self.assertGreater(obf[0], 2.9)
        self.assertLess(obf[1], 1.99)
        self.assertGreater(obf[1], 1.96)
        self.assertLess(poc[0], obf[0])
        self.assertGreater(poc[1], obf[1])

    def test_total_alpha_of_a_boundary_is_alpha(self):
        fr = [1 / 3, 2 / 3, 1.0]
        for spend in seq.SPENDING:
            zs = seq.z_boundaries(fr, 0.025, spend)
            self.assertAlmostEqual(seq._total_alpha(fr, zs), 0.025, delta=2e-5, msg=spend)


class NullSimulation(unittest.TestCase):
    """Under the null the boundary is crossed at some look with probability
    alpha. 20000 seeded trials; the crossing rate must sit inside the Wilson
    interval of alpha, and it may not be found by re-seeding."""

    TRIALS = 20000

    def test_gaussian_null_crossing_rate(self):
        fr = [1 / 3, 2 / 3, 1.0]
        zs = seq.z_boundaries(fr, 0.025, "obf")
        rng = random.Random(2026)
        crossed = 0
        for _ in range(self.TRIALS):
            b, prev = 0.0, 0.0
            for t, z in zip(fr, zs):
                b += rng.gauss(0.0, math.sqrt(t - prev))
                prev = t
                if b / math.sqrt(t) >= z:
                    crossed += 1
                    break
        rate = crossed / self.TRIALS
        lo, hi = wilson(crossed, self.TRIALS)
        self.assertTrue(lo <= 0.025 <= hi, f"rate {rate:.4f} [{lo:.4f}, {hi:.4f}]")

    def test_binomial_null_matches_the_exact_type1(self):
        """The integer hit-count boundary on the actual binomial at n=272,
        p0=0.3014. A hit count is discrete, so the true error is not alpha; it
        is ``exact_type1``, and the simulation must agree with THAT. Measured
        2026-09-02: 0.0296 exact against a nominal 0.025, and the single-look
        Wilson gate at 97/272 already carries 0.0289 - the excess is the score
        test on a discrete count, not the sequential design."""
        b = seq.design(272, [0.5, 1.0], 0.025, 0.3014, "obf")
        exact = seq.exact_type1(b)
        rng = random.Random(11)
        crossed = 0
        for _ in range(self.TRIALS):
            hits = 0
            done = 0
            for lk in b.looks:
                hits += sum(1 for _ in range(lk.total - done) if rng.random() < b.p0)
                done = lk.total
                if seq.look(b, hits, lk.total) == seq.CROSSED:
                    crossed += 1
                    break
        rate = crossed / self.TRIALS
        lo, hi = wilson(crossed, self.TRIALS)
        self.assertTrue(lo <= exact <= hi, f"rate {rate:.4f} [{lo:.4f}, {hi:.4f}] vs exact {exact:.4f}")
        # and the exact figure is pinned, so a change to min_hits is deliberate
        self.assertAlmostEqual(exact, 0.0296, delta=0.0005)

    def test_exact_type1_of_one_look_is_the_binomial_tail(self):
        b = seq.design(50, [1.0], 0.025, 0.5)
        tail = sum(math.comb(50, j) * 0.5 ** 50 for j in range(b.looks[0].min_hits, 51))
        self.assertAlmostEqual(seq.exact_type1(b), tail, delta=1e-12)


class Determinism(unittest.TestCase):
    def test_same_inputs_same_table(self):
        a = seq.design(272, [0.5, 1.0], 0.025, 0.3014, "obf")
        b = seq.design(272, [0.5, 1.0], 0.025, 0.3014, "obf")
        self.assertEqual(a, b)
        self.assertEqual(seq.table(a), seq.table(b))

    def test_the_worked_instance_is_pinned(self):
        # The numbers docs/group-sequential-criterion.md quotes. A change here
        # is a change to a published table and must be deliberate.
        b = seq.design(272, [0.5, 1.0], 0.025, 0.3014, "obf")
        self.assertEqual(b.totals(), (136, 272))
        self.assertAlmostEqual(b.looks[0].z, 2.963, delta=0.005)
        self.assertAlmostEqual(b.looks[1].z, 1.969, delta=0.005)


class RefitFinal(unittest.TestCase):
    """The final look at the total the record actually holds."""

    def setUp(self):
        self.b = seq.design(272, [0.5, 1.0], 0.025, 0.3014, "obf")

    def test_refit_at_the_planned_n_is_the_plan(self):
        r = seq.refit_final(self.b, 272)
        self.assertEqual(r.looks[0], self.b.looks[0])
        self.assertAlmostEqual(r.looks[1].z, self.b.looks[1].z, delta=1e-6)
        self.assertEqual(r.looks[1].min_hits, self.b.looks[1].min_hits)

    def test_interim_is_untouched_and_total_alpha_holds(self):
        for n_final in (250, 261, 290, 310):
            r = seq.refit_final(self.b, n_final)
            self.assertEqual(r.looks[0], self.b.looks[0], n_final)
            self.assertEqual(r.looks[1].total, n_final)
            fr = [136 / n_final, 1.0]
            self.assertAlmostEqual(seq._total_alpha(fr, [lk.z for lk in r.looks]), 0.025,
                                   delta=2e-5, msg=n_final)
            self.assertEqual(seq.look(r, r.looks[1].min_hits, n_final), seq.CROSSED)
            with self.assertRaises(seq.UndeclaredLook):
                seq.look(r, 90, 272 if n_final != 272 else 271)

    def test_a_short_run_has_no_final_look(self):
        with self.assertRaises(ValueError):
            seq.refit_final(self.b, 136)
        with self.assertRaises(ValueError):
            seq.refit_final(self.b, 120)


class Inputs(unittest.TestCase):
    def test_fractions_must_end_at_one_and_increase(self):
        for bad in ([0.5], [0.5, 0.5, 1.0], [1.0, 0.5], [0.0, 1.0], []):
            with self.assertRaises(ValueError, msg=bad):
                seq.z_boundaries(bad, 0.025)

    def test_two_looks_rounding_to_one_total_are_refused(self):
        with self.assertRaises(ValueError):
            seq.design(3, [0.9, 1.0], 0.025, 0.3)

    def test_min_hits_at_1_96_is_the_wilson_gate(self):
        # The count whose Wilson floor clears p0 is exactly the score-test count.
        n, p0 = 272, 0.3014
        h = seq.min_hits(n, p0, 1.96)
        self.assertGreater(wilson(h, n)[0], p0)
        self.assertLessEqual(wilson(h - 1, n)[0], p0)


if __name__ == "__main__":
    unittest.main()
