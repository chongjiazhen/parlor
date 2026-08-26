"""The arm wiring, and the report's refusal to read a gate off a random side.

A mixed arm is only worth anything if the seats it claims to seat live really are
live, and if the verdict lines refuse to speak for a side that played at random.
Both are cheap to get subtly wrong and expensive to notice later: the numbers look
identical either way.
"""

from __future__ import annotations

import argparse
import random
import unittest

from eval.run_games import LIVE_TEAMS, build_policies, report, score
from games.cabal.player import LLMPolicy, RandomPolicy, play_game
from games.cabal.referee import CabalReferee
from games.cabal.roles import Team


def make_args(**kw):
    base = dict(arm="llm", backend="clean", model="m", rounds=1, retries=0,
                temperature=0.8, timeout=5.0, max_tokens=1536, seed=1, games=1)
    base.update(kw)
    return argparse.Namespace(**base)


def live_seats(ref, policies) -> set:
    return {s for s, p in policies.items() if isinstance(p, LLMPolicy)}


class TestArms(unittest.TestCase):
    def setUp(self):
        self.ref = CabalReferee.new(5, seed=4)
        self.rng = random.Random(0)

    def seats_of(self, team: Team) -> set:
        return {s for s, r in self.ref.assignment.items() if r.team is team}

    def test_llm_seats_everyone(self):
        p = build_policies(self.ref, make_args(arm="llm"), self.rng)
        self.assertEqual(live_seats(self.ref, p), set(self.ref.assignment))

    def test_random_seats_nobody(self):
        p = build_policies(self.ref, make_args(arm="random"), self.rng)
        self.assertEqual(live_seats(self.ref, p), set())

    def test_llm_good_seats_only_good(self):
        p = build_policies(self.ref, make_args(arm="llm-good"), self.rng)
        self.assertEqual(live_seats(self.ref, p), self.seats_of(Team.GOOD))

    def test_llm_evil_seats_only_evil(self):
        p = build_policies(self.ref, make_args(arm="llm-evil"), self.rng)
        self.assertEqual(live_seats(self.ref, p), self.seats_of(Team.EVIL))

    def test_no_backend_means_no_live_seat_whatever_the_arm(self):
        p = build_policies(self.ref, make_args(arm="llm", backend=None), self.rng)
        self.assertEqual(live_seats(self.ref, p), set())

    def test_every_arm_is_wired(self):
        self.assertEqual(set(LIVE_TEAMS), {"random", "llm", "llm-good", "llm-evil"})


class TestReportRefusals(unittest.TestCase):
    """The report must not read a gate off a side that played at random - the
    numbers are there either way, and they are the baseline, not a result."""

    def setUp(self):
        rng = random.Random(2)
        records = []
        for i in range(6):
            ref = CabalReferee.new(5, seed=i)
            records.append(play_game(ref, {s: RandomPolicy(rng=rng)
                                           for s in ref.assignment}))
        self.s = score(records)

    def text(self, arm: str, backend: str | None = "clean") -> str:
        return report(self.s, make_args(arm=arm, backend=backend), 1.0)

    def test_random_arm_disclaims_both_halves_and_gate_2(self):
        t = self.text("random", backend=None)
        self.assertIn("good played at random", t)
        self.assertIn("hunter is an EVIL seat and played at random", t)
        self.assertIn("gate #2 not shown", t)

    def test_llm_good_arm_disclaims_the_hunt_half_and_gate_2(self):
        t = self.text("llm-good")
        self.assertNotIn("good played at random", t)
        self.assertIn("hunter is an EVIL seat and played at random", t)
        self.assertIn("evil played at random in this arm", t)

    def test_llm_evil_arm_disclaims_the_vote_half(self):
        t = self.text("llm-evil")
        self.assertIn("good played at random", t)
        self.assertNotIn("hunter is an EVIL seat and played at random", t)

    def test_one_upstream_is_named_without_a_mix_warning(self):
        s = dict(self.s)
        s["integrity"] = dict(s["integrity"], upstreams={"deepseek-v3.2": 400})
        t = report(s, make_args(arm="llm"), 1.0)
        self.assertIn("served by  deepseek-v3.2 100%", t)
        self.assertNotIn("MIX of models", t)

    def test_several_upstreams_are_flagged_as_a_mix(self):
        """``auto`` hands each request to whichever key is usable, so a run under it
        is several models' play averaged together. Reporting that as one model's
        result is the failure; the mix has to be visible next to the number."""
        s = dict(self.s)
        s["integrity"] = dict(s["integrity"],
                              upstreams={"minimax-m3": 300, "nemotron-nano": 100})
        t = report(s, make_args(arm="llm"), 1.0)
        self.assertIn("minimax-m3 75%", t)
        self.assertIn("nemotron-nano 25%", t)
        self.assertIn("MIX of models", t)

    def test_a_mixed_arm_cannot_pass_gate_3_on_passing_numbers(self):
        """Fed numbers that clear both halves outright, a mixed arm must STILL
        refuse - half of them came from the random side. Scored against a real
        random run this would pass for the wrong reason, so the numbers are
        synthetic and deliberately good."""
        s = dict(self.s)
        # The gate reads the blind stratum's CI FLOOR, so the fixture has to set
        # that - twice now this test has been left pinned to a field the verdict
        # stopped reading, which makes it fail for the wrong reason and stop
        # exercising the arm refusal it exists for.
        s["gate3_deduction"] = dict(s["gate3_deduction"],
                                    discrimination=0.4, discrimination_blind=0.4,
                                    discrimination_blind_ci95=(0.2, 0.6),
                                    taint_sensitivity_blind=0.4,
                                    taint_sensitivity_blind_ci95=(0.2, 0.6),
                                    hunter_ci95=(0.5, 0.9))
        s["gate2_deception"] = dict(s["gate2_deception"],
                                    ci95=(0.2, 0.6), evil_win_rate=0.4)
        self.assertIn("gate #3 PASS", report(s, make_args(arm="llm"), 1.0))
        for arm in ("random", "llm-good", "llm-evil"):
            with self.subTest(arm=arm):
                self.assertNotIn("gate #3 PASS", report(s, make_args(arm=arm), 1.0))




class TestBlindSplit(unittest.TestCase):
    """Vote discrimination averages three different populations: a seer acting on
    a fact it was handed, a watcher acting on an aura pair that certifies taint on
    some team shapes, and a seat the night told nothing. Only the third is
    deduction, and BOTH terms of the difference must come from it - filtering only
    the tainted side leaves the seer's clean-team certification in p_clean, which
    is how the first version of this split read +13.57% where the honest figure
    was +2.53%.
    """

    def records(self, blind_approves: int, blind_total: int, blind_clean: int = 10):
        from games.cabal.player import VoteRecord
        rec = play_game(CabalReferee.new(5, seed=1),
                        {s: RandomPolicy(rng=random.Random(1)) for s in range(5)})
        rec.votes = (
            # seer on a tainted team: always rejects, on handed knowledge
            [VoteRecord(0, False, False, True, True, "identity", 1 + i % 2)
               for i in range(10)]
            # blind seats on a tainted team: as told
            + [VoteRecord(1, i < blind_approves, False, True, False, "none",
                          1 + i % 2)
               for i in range(blind_total)]
            # blind seats on a clean team: always approve
            + [VoteRecord(2, True, False, False, False, "none", 0)
               for _ in range(blind_clean)]
            # seer on a clean team: certifies it, always approves. Belongs to
            # p_clean only in the POOLED figure - never in the gate.
            + [VoteRecord(0, True, False, False, False, "identity", 0)
               for _ in range(10)]
        )
        rec.winner, rec.error = "good", None
        return [rec]

    def test_a_seer_carrying_the_table_cannot_pass_the_gate(self):
        """Blind seats at chance, seer perfect. The pooled figure looks healthy and
        the gate must still refuse - this is the whole reason for the split."""
        s = score(self.records(blind_approves=10, blind_total=10))
        g3 = s["gate3_deduction"]
        self.assertGreater(g3["discrimination"], 0)        # the average looks fine
        self.assertEqual(g3["discrimination_blind"], 0.0)  # the blind half is chance
        self.assertAlmostEqual(g3["strata"]["identity"]["discrimination"], 1.0)
        text = report(s, make_args(arm="llm"), 1.0)
        self.assertIn("gate #3 not shown", text)
        self.assertIn("blind-seat taint-sensitivity CI floor includes 0", text)

    def test_blind_seats_that_do_discriminate_show_it(self):
        g3 = score(self.records(blind_approves=2, blind_total=10))["gate3_deduction"]
        self.assertAlmostEqual(g3["discrimination_blind"], 0.8)
        self.assertEqual(g3["votes_tainted_blind"], 10)
        self.assertEqual(g3["votes_clean_blind"], 10)

    def test_the_gate_is_the_ci_floor_not_the_point_estimate(self):
        """A point estimate >0 is a sign test. Gate #3b next door demands a Wilson
        floor above baseline; 3a used to pass on +0.5% from a handful of votes.

        Asserted on the VERDICT with a synthetic interval, not on a computed one:
        a healthy point estimate whose floor straddles zero must not pass, and
        that is a statement about the verdict logic, not about the bootstrap.
        """
        s = score(self.records(blind_approves=2, blind_total=10))
        healthy_point_straddling_floor = dict(
            s["gate3_deduction"],
            discrimination_blind=0.30, discrimination_blind_ci95=(-0.05, 0.62),
            taint_sensitivity_blind=0.30,
            taint_sensitivity_blind_ci95=(-0.05, 0.62),
            hunter_ci95=(0.5, 0.9))
        text = report(dict(s, gate3_deduction=healthy_point_straddling_floor),
                      make_args(arm="llm"), 1.0)
        self.assertIn("blind-seat taint-sensitivity CI floor includes 0", text)
        self.assertIn("gate #3 not shown", text)

        clears = dict(healthy_point_straddling_floor,
                      taint_sensitivity_blind_ci95=(0.05, 0.62))
        text = report(dict(s, gate3_deduction=clears), make_args(arm="llm"), 1.0)
        self.assertIn("blind-seat taint-sensitivity CI floor clears 0", text)

    def test_no_blind_votes_is_REFUSED_not_passed(self):
        """The fail-open this replaced: p_blind defaulted to 0.0, so a run with no
        blind votes scored p_clean - 0 > 0 and PASSED on no data. A refusal must be
        distinguishable from a failure - a fail invites tuning, a refusal invites
        more data."""
        from games.cabal.player import VoteRecord
        recs = self.records(blind_approves=2, blind_total=10)
        recs[0].votes = [v for v in recs[0].votes if v.knowledge_class != "none"]
        s = score(recs)
        g3 = s["gate3_deduction"]
        self.assertIsNone(g3["discrimination_blind"])
        self.assertEqual(g3["votes_tainted_blind"], 0)
        text = report(s, make_args(arm="llm"), 1.0)
        # Two INDEPENDENT paths must both refuse - the metric line and the verdict
        # line. A bare assertIn("REFUSED") passes when either one still fires, so
        # it survived a mutation that made the metric line render +0.00%.
        self.assertIn("TAINT SENSITIVITY (blind)  REFUSED", text)
        self.assertIn("blind-seat taint sensitivity REFUSED", text)
        self.assertNotIn("TAINT SENSITIVITY (blind)  +0.00%", text)
        self.assertIn("gate #3 not shown", text)


if __name__ == "__main__":
    unittest.main()


class TestGradedTaint(unittest.TestCase):
    """The binary metric thresholds taint at 1, so it is precision-capped by the
    clean cell - the scarce one at 5 seats (P(clean team) ~ 0.18). The slope uses
    every level, and degenerates to the binary number when only two occur."""

    def votes(self, by_level):
        """by_level: {evil_count: (approvals, total)} for one blind seat."""
        from games.cabal.player import VoteRecord
        out = []
        for level, (hits, total) in by_level.items():
            for i in range(total):
                out.append(VoteRecord(1, i < hits, False, level > 0, False,
                                      "none", level))
        return out

    def test_it_degenerates_to_the_binary_number_at_two_levels(self):
        """Same quantity, better estimator - not a different claim. With only
        levels 0 and 1 the slope IS p_clean - p_tainted."""
        from eval.run_games import taint_sensitivity
        v = self.votes({0: (8, 10), 1: (3, 10)})
        slope, _ = taint_sensitivity(v)
        self.assertAlmostEqual(slope, 0.8 - 0.3)

    def test_the_third_level_carries_signal_the_binary_metric_discards(self):
        """Two runs identical under the binary split - both 80% clean, 40%
        tainted - but one keeps discriminating between 1 and 2 saboteurs and the
        other does not. The binary figure cannot tell them apart."""
        from eval.run_games import taint_sensitivity
        graded, _ = taint_sensitivity(self.votes({0: (8, 10), 1: (6, 10), 2: (2, 10)}))
        flat, _ = taint_sensitivity(self.votes({0: (8, 10), 1: (4, 10), 2: (4, 10)}))
        for v in (graded, flat):
            self.assertIsNotNone(v)
        self.assertGreater(graded, flat)

    def test_a_non_monotonic_table_is_visible_even_when_the_slope_is_positive(self):
        """A seat that rejects 1 saboteur but approves 2 is not a weak deducer, it
        is responding to something other than taint. The slope alone hides that,
        which is why the per-level table ships beside it."""
        from eval.run_games import taint_sensitivity
        slope, levels = taint_sensitivity(self.votes({0: (9, 10), 1: (2, 10),
                                                      2: (5, 10)}))
        self.assertGreater(slope, 0)                       # slope looks fine
        rates = [h / n for _, (h, n) in sorted(levels.items())]
        self.assertLess(rates[1], rates[2])                # but it goes back UP

    def test_one_taint_level_is_refused_not_scored_as_zero(self):
        from eval.run_games import taint_sensitivity
        slope, levels = taint_sensitivity(self.votes({0: (5, 10)}))
        self.assertIsNone(slope)
        self.assertEqual(levels, {0: (5, 10)})
