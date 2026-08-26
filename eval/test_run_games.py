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
        # discrimination_blind is what grades the gate; setting only the pooled
        # figure would leave the fixture failing for the wrong reason and this
        # test would pass without ever exercising the arm refusal.
        s["gate3_deduction"] = dict(s["gate3_deduction"],
                                    discrimination=0.4, discrimination_blind=0.4,
                                    hunter_ci95=(0.5, 0.9))
        s["gate2_deception"] = dict(s["gate2_deception"],
                                    ci95=(0.2, 0.6), evil_win_rate=0.4)
        self.assertIn("gate #3 PASS", report(s, make_args(arm="llm"), 1.0))
        for arm in ("random", "llm-good", "llm-evil"):
            with self.subTest(arm=arm):
                self.assertNotIn("gate #3 PASS", report(s, make_args(arm=arm), 1.0))




class TestBlindSplit(unittest.TestCase):
    """Vote discrimination averages two different things: a seer acting on a fact
    it was handed, and a seat with nothing reasoning from play. Only the second is
    deduction, so the report shows it separately."""

    def records(self, blind_approves: int, blind_total: int):
        from games.cabal.player import VoteRecord
        rec = play_game(CabalReferee.new(5, seed=1),
                        {s: RandomPolicy(rng=random.Random(1)) for s in range(5)})
        rec.votes = (
            # informed seats: always reject a tainted team
            [VoteRecord(0, False, False, True, True) for _ in range(10)]
            # blind seats on a tainted team: as told
            + [VoteRecord(1, i < blind_approves, False, True, False)
               for i in range(blind_total)]
            # everyone on a clean team: always approve
            + [VoteRecord(2, True, False, False, False) for _ in range(10)]
        )
        rec.winner, rec.error = "good", None
        return [rec]

    def test_a_seer_carrying_the_table_cannot_pass_the_gate(self):
        """This used to assert only that the blind figure was DISPLAYED. Showing a
        number beside a verdict that ignores it is not a guard - the pooled figure
        graded the gate, so a table voting at chance with one informed seat still
        read as deduction. The blind half now grades it.
        """
        s = score(self.records(blind_approves=10, blind_total=10))
        g3 = s["gate3_deduction"]
        self.assertGreater(g3["discrimination"], 0)        # the average looks fine
        self.assertEqual(g3["discrimination_blind"], 0.0)  # the blind half is chance
        text = report(s, make_args(arm="llm"), 1.0)
        self.assertIn("DISCRIMINATION (blind)     +0.00%", text)
        self.assertIn("gate #3 not shown", text)
        self.assertIn("blind-seat discrimination at/below 0", text)

    def test_blind_seats_that_do_discriminate_show_it(self):
        g3 = score(self.records(blind_approves=2, blind_total=10))["gate3_deduction"]
        self.assertAlmostEqual(g3["discrimination_blind"], 0.8)
        self.assertEqual(g3["votes_tainted_blind"], 10)


if __name__ == "__main__":
    unittest.main()
