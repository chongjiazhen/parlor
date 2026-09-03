"""The larger setups, and what each one degrades about information.

`SETUP_5` is the deal every recorded cabal number was played on, so the first
class here pins it byte for byte: a larger setup that moved it would re-baseline
the whole ledger silently. The rest are properties a setup must have to be a
playable cabal at all - one hunter, and an aura pair that is a pair - checked over
every registered setup rather than over a list, so the next one is covered on
registration.
"""

import random
import unittest

from games.cabal.audit import LeakDetected, assert_no_leak, leak_audit
from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee, Phase
from games.cabal.roles import (HUNTER, LOYALIST, LURKER, SEER, SETUP_5,
                               SETUP_6, SETUP_7, SETUPS, STRAY, Team)


class TestSetupFiveIsFrozen(unittest.TestCase):
    """A deck change re-baselines every number recorded under it."""

    def test_setup_5_is_byte_identical(self):
        self.assertEqual(SETUP_5.n, 5)
        self.assertEqual([r.key for r in SETUP_5.roles],
                         ["seer", "watcher", "loyalist", "mimic", "hunter"])
        self.assertEqual(SETUP_5.team_sizes, (2, 3, 2, 3, 3))
        self.assertEqual(SETUP_5.fails_required, (1, 1, 1, 1, 1))

    def test_setup_5_is_still_what_five_seats_deals(self):
        self.assertIs(SETUPS[5], SETUP_5)


class TestTheFolkLadder(unittest.TestCase):
    """Team sizes and the two-fail mission, as data. `docs/player-counts.md` warned
    that a 7p setup left at all-ones is silently the wrong game."""

    def test_six_is_registered(self):
        self.assertIs(SETUPS[6], SETUP_6)
        self.assertEqual(SETUP_6.n, 6)
        self.assertEqual(len(SETUP_6.roles), 6)

    def test_seven_is_registered(self):
        self.assertIs(SETUPS[7], SETUP_7)
        self.assertEqual(SETUP_7.n, 7)
        self.assertEqual(len(SETUP_7.roles), 7)

    def test_six_team_sizes(self):
        self.assertEqual(SETUP_6.team_sizes, (2, 3, 4, 3, 4))
        self.assertEqual(SETUP_6.fails_required, (1, 1, 1, 1, 1))

    def test_seven_team_sizes_and_the_two_fail_mission(self):
        self.assertEqual(SETUP_7.team_sizes, (2, 3, 3, 4, 4))
        self.assertEqual(SETUP_7.fails_required, (1, 1, 1, 2, 1))

    def test_every_setup_runs_five_missions(self):
        for n, setup in sorted(SETUPS.items()):
            with self.subTest(seats=n):
                self.assertEqual(len(setup.team_sizes), 5)
                self.assertEqual(len(setup.fails_required), 5)
                self.assertTrue(all(1 <= s <= n for s in setup.team_sizes))
                self.assertTrue(all(1 <= f <= s for f, s
                                    in zip(setup.fails_required, setup.team_sizes)))

    def test_evil_counts_follow_the_ladder(self):
        counts = {n: sum(1 for r in s.roles if r.team is Team.EVIL)
                  for n, s in SETUPS.items()}
        self.assertEqual(counts, {5: 2, 6: 2, 7: 3})


class TestEverySetupIsPlayable(unittest.TestCase):
    """Two structural properties the referee depends on, over every registered
    setup. Both are silent-wrong rather than loud: a setup with no hunter reaches
    the endgame and raises `KeyError` there, and a watcher whose aura pair carries
    no evil is handed the seer outright instead of a pair."""

    def test_exactly_one_hunter(self):
        for n, setup in sorted(SETUPS.items()):
            with self.subTest(seats=n):
                self.assertEqual(sum(1 for r in setup.roles if r.key == "hunter"), 1)

    def test_a_seated_watcher_sees_a_real_pair(self):
        for n, setup in sorted(SETUPS.items()):
            if not any(r.sees_magic for r in setup.roles):
                continue
            with self.subTest(seats=n):
                shown = [r for r in setup.roles if r.shown_to_watcher]
                self.assertEqual(len(shown), 2, "the aura is a PAIR or it is a reveal")
                self.assertEqual(sum(1 for r in shown if r.team is Team.EVIL), 1)

    def test_seven_seats_seats_no_watcher(self):
        """Stated as a test because it is a decision, not an omission: seating the
        watcher at 7p would need a fourth evil to carry the aura, and both
        information-degrading evils have to be dealt."""
        self.assertFalse(any(r.sees_magic for r in SETUP_7.roles))


class TestSevenDealsBothDegradingEvils(unittest.TestCase):
    def test_both_are_seated(self):
        keys = [r.key for r in SETUP_7.roles]
        self.assertIn("lurker", keys)
        self.assertIn("stray", keys)

    def test_neither_is_seated_below_seven(self):
        for n in (5, 6):
            keys = [r.key for r in SETUPS[n].roles]
            with self.subTest(seats=n):
                self.assertNotIn("lurker", keys)
                self.assertNotIn("stray", keys)


class TestSevenSeatEntitlement(unittest.TestCase):
    """All three flags on one deal. Seats: 0 seer, 1-3 loyalist, 4 hunter,
    5 lurker, 6 stray."""

    DEAL = {0: SEER, 1: LOYALIST, 2: LOYALIST, 3: LOYALIST,
            4: HUNTER, 5: LURKER, 6: STRAY}

    def ref(self):
        return CabalReferee(setup=SETUP_7, assignment=dict(self.DEAL), leader=0)

    def know(self, seat):
        return {(k.seat, k.label) for k in self.ref().entitled_knowledge(seat)}

    def test_the_seer_does_not_see_the_lurker(self):
        # seen_by_seer=False. Hunter and stray are seen; the lurker is not.
        self.assertEqual(self.know(0), {(4, "evil"), (6, "evil")})

    def test_the_stray_is_told_nothing(self):
        self.assertEqual(self.know(6), set())

    def test_the_stray_is_named_to_nobody_on_its_own_side(self):
        for seat in (4, 5):
            with self.subTest(seat=seat):
                named = {k.seat for k in self.ref().entitled_knowledge(seat)}
                self.assertNotIn(6, named)

    def test_hunter_and_lurker_see_each_other(self):
        self.assertEqual(self.know(4), {(5, "fellow-evil")})
        self.assertEqual(self.know(5), {(4, "fellow-evil")})

    def test_loyalists_know_nothing(self):
        for seat in (1, 2, 3):
            with self.subTest(seat=seat):
                self.assertEqual(self.know(seat), set())

    def test_the_conference_excludes_the_stray(self):
        self.assertEqual(self.ref().conference_seats(), [4, 5])

    def test_the_hunt_denominator_widens(self):
        # Barred: itself and the one ally it was named. 5 of 7 left, not 3 of 5.
        self.assertEqual(self.ref().legal_hunt_targets(4), [0, 1, 2, 3, 6])


class TestSevenSeatLeakAudit(unittest.TestCase):
    def test_two_hundred_seeded_seven_seat_games_are_clean(self):
        for seed in range(200):
            r = CabalReferee.new(7, seed=seed, discussion_rounds=1)
            with self.subTest(seed=seed):
                self.assertEqual(leak_audit(r), [])

    def test_a_leaky_referee_variant_is_caught_at_seven_seats(self):
        """The audit half. A referee that names a foreign role in an EVENT must
        make the driver raise, not merely be noticed - and the term planted is a
        variant evil's, which no 5-seat sweep can reach."""
        ref = CabalReferee.new(7, seed=3, discussion_rounds=1)
        victim = next(s for s, r in ref.assignment.items() if r.key == "stray")
        ref._event(f"clerical note: seat {victim} is the stray")
        pol = RandomPolicy(rng=random.Random(3))
        with self.assertRaises(LeakDetected):
            play_game(ref, {s: pol for s in ref.assignment})

    def test_the_same_seven_seat_game_is_scored_when_the_leak_is_absent(self):
        ref = CabalReferee.new(7, seed=3, discussion_rounds=1)
        pol = RandomPolicy(rng=random.Random(3))
        rec = play_game(ref, {s: pol for s in ref.assignment})
        self.assertIn(rec.winner, ("good", "evil"))

    def test_six_seat_games_are_clean_and_playable(self):
        for seed in range(50):
            ref = CabalReferee.new(6, seed=seed, discussion_rounds=1)
            with self.subTest(seed=seed):
                assert_no_leak(ref)
                rec = play_game(ref, {s: RandomPolicy(rng=random.Random(seed))
                                      for s in ref.assignment})
                self.assertIn(rec.winner, ("good", "evil"))


class TestTheTwoFailMissionBites(unittest.TestCase):
    def test_one_fail_does_not_sink_mission_four_at_seven_seats(self):
        ref = CabalReferee(setup=SETUP_7,
                           assignment=dict(TestSevenSeatEntitlement.DEAL),
                           phase=Phase.MISSION, mission_index=3,
                           results=[True, True, True],
                           proposal=(0, 1, 2, 4))
        self.assertTrue(ref.mission({0: False, 1: False, 2: False, 4: True}))

    def test_two_fails_do(self):
        ref = CabalReferee(setup=SETUP_7,
                           assignment=dict(TestSevenSeatEntitlement.DEAL),
                           phase=Phase.MISSION, mission_index=3,
                           results=[True, True, True],
                           proposal=(0, 1, 4, 5))
        self.assertFalse(ref.mission({0: False, 1: False, 4: True, 5: True}))


if __name__ == "__main__":
    unittest.main()
