"""Referee state-machine tests: setup, mission flow, both win paths, rule refusals."""

import unittest

from games.cabal.referee import CabalReferee, IllegalAction, Phase
from games.cabal.roles import (
    HUNTER,
    LOYALIST,
    MIMIC,
    SEER,
    SETUP_5,
    WATCHER,
    Team,
)

# fixed assignment so tests know who is who
FIXED = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}


def fixed_ref():
    return CabalReferee(setup=SETUP_5, assignment=dict(FIXED), leader=0)


def run_success(ref):
    """Approve a legal team for the current mission and pass it with all successes."""
    size = ref.setup.team_sizes[ref.mission_index]
    team = list(range(size))
    ref.propose(ref.leader, team)
    ref.vote({s: True for s in ref.assignment})
    ref.mission({s: False for s in team})


class TestSetup(unittest.TestCase):
    def test_team_composition(self):
        ref = fixed_ref()
        good = [s for s, r in ref.assignment.items() if r.team is Team.GOOD]
        self.assertEqual(len(good), 3)
        self.assertEqual(len(ref.evil_seats()), 2)

    def test_setup_tables(self):
        self.assertEqual(SETUP_5.team_sizes, (2, 3, 2, 3, 3))
        self.assertEqual(SETUP_5.fails_required, (1, 1, 1, 1, 1))

    def test_deal_is_seeded(self):
        a = CabalReferee.new(5, seed=42).assignment
        b = CabalReferee.new(5, seed=42).assignment
        self.assertEqual({s: r.key for s, r in a.items()},
                         {s: r.key for s, r in b.items()})


class TestWinPaths(unittest.TestCase):
    def test_good_wins_then_hunter_misses(self):
        ref = fixed_ref()
        for _ in range(3):
            run_success(ref)
        self.assertIs(ref.phase, Phase.HUNT)
        ref.hunt(hunter=4, target=2)     # seat 2 is loyalist, not the seer
        self.assertIs(ref.winner, Team.GOOD)
        self.assertIs(ref.phase, Phase.DONE)

    def test_good_wins_then_hunter_hits_seer(self):
        ref = fixed_ref()
        for _ in range(3):
            run_success(ref)
        ref.hunt(hunter=4, target=0)     # seat 0 is the seer
        self.assertIs(ref.winner, Team.EVIL)

    def test_five_rejects_is_evil_win(self):
        ref = fixed_ref()
        for _ in range(5):
            self.assertIs(ref.phase, Phase.PROPOSE)
            ref.propose(ref.leader, [0, 1])
            ref.vote({s: False for s in ref.assignment})
        self.assertIs(ref.winner, Team.EVIL)
        self.assertIs(ref.phase, Phase.DONE)

    def test_three_failed_missions_is_evil_win(self):
        ref = fixed_ref()
        for _ in range(3):
            size = ref.setup.team_sizes[ref.mission_index]
            # always include evil seat 3 so the mission can be failed
            team = [3] + [s for s in range(ref.n) if s != 3][: size - 1]
            ref.propose(ref.leader, team)
            ref.vote({s: True for s in ref.assignment})
            ref.mission({s: (ref.assignment[s].team is Team.EVIL) for s in team})
        self.assertIs(ref.winner, Team.EVIL)


class TestRuleRefusals(unittest.TestCase):
    def test_good_cannot_fail(self):
        ref = fixed_ref()
        ref.propose(0, [0, 1])
        ref.vote({s: True for s in ref.assignment})
        with self.assertRaises(IllegalAction):
            ref.mission({0: True, 1: False})   # seat 0 is good, cannot fail

    def test_wrong_team_size_refused(self):
        ref = fixed_ref()
        with self.assertRaises(IllegalAction):
            ref.propose(0, [0, 1, 2])          # mission 1 needs 2

    def test_non_leader_cannot_propose(self):
        ref = fixed_ref()
        with self.assertRaises(IllegalAction):
            ref.propose(1, [0, 1])             # leader is seat 0

    def test_out_of_phase_refused(self):
        ref = fixed_ref()
        with self.assertRaises(IllegalAction):
            ref.vote({s: True for s in ref.assignment})  # still in PROPOSE


if __name__ == "__main__":
    unittest.main()
