"""The S26 reader: pairs only where the boards are the same, refuses a non-pair.

The number this instrument exists for is the paired stratum, and the way it goes
wrong is silent: pair a proved vote with a random vote taken on a DIFFERENT
proposal and the comparison still prints, with a plausible number in it. So the
pairing is tested on a synthetic pair whose divergence point is known.
"""

from __future__ import annotations

import unittest

from eval.solver_control import pairable_rounds, read_pair, render


def _vote(turn, seat, approved, tainted):
    return {"turn": turn, "seat": seat, "approved": approved,
            "team_has_evil": tainted, "seat_is_evil": False,
            "knowledge_class": "none", "team_evil_count": int(tainted)}


def _game(events, votes, mech, winner="good", mechanical=0, deferred=0, decisions=None):
    return {
        "winner": winner, "assignment": {"0": "seer", "1": "watcher", "2": "loyalist",
                                         "3": "mimic", "4": "hunter"},
        "public_events": events, "votes": votes, "hunt": None, "missions": [True],
        "fails_played": 0, "fallbacks": 0,
        "decisions": mechanical + deferred if decisions is None else decisions,
        "solver_mechanical": mechanical, "solver_deferred": deferred,
        "decision_log": [{"turn": t, "seat": s, "phase": "vote", "solver": "mechanical"}
                         for t, s in mech],
        "error": None,
    }


PREFIX = [["event", "seat 0 proposes [0, 3]"], ["speech:1", "fine"]]
ROUND1_S = ["event", "vote on [0, 3]: 2/5 approve (approved by [1, 2]) -> REJECTED"]
ROUND1_R = ["event", "vote on [0, 3]: 4/5 approve (approved by [0, 1, 2, 4]) -> APPROVED"]


class TestPairing(unittest.TestCase):
    def test_a_round_pairs_only_while_the_prefix_is_identical(self):
        solver = PREFIX + [ROUND1_S, ["event", "seat 1 proposes [1, 2]"],
                           ["event", "vote on [1, 2]: 5/5 approve (approved by [0, 1, 2, 3, 4]) -> APPROVED"]]
        control = PREFIX + [ROUND1_R, ["event", "mission 1 on [0, 3]: 1 fail(s), need 1 -> FAIL"],
                            ["event", "seat 1 proposes [1, 2]"],
                            ["event", "vote on [1, 2]: 3/5 approve (approved by [0, 1, 2]) -> APPROVED"]]
        # round 1 shares its prefix; round 2 does not (the result line differed and
        # the control ran a mission the solver arm never did)
        self.assertEqual(pairable_rounds(solver, control), 1)

    def test_identical_games_pair_every_round(self):
        events = PREFIX + [ROUND1_R]
        self.assertEqual(pairable_rounds(events, events), 1)

    def test_the_stratum_pairs_the_proved_vote_with_random_s_vote_on_the_same_board(self):
        solver = {"args": {"arm": "solver", "seed": 5}, "games": [_game(
            PREFIX + [ROUND1_S, ["event", "seat 1 proposes [1, 2]"],
                      ["event", "vote on [1, 2]: 5/5 approve (approved by [0, 1, 2, 3, 4]) -> APPROVED"]],
            [_vote(3, 0, False, True), _vote(3, 1, True, True), _vote(3, 2, True, True),
             _vote(3, 3, False, True), _vote(3, 4, False, True),
             _vote(5, 0, True, False)],
            mech=[(3, 0), (3, 3), (3, 4), (5, 0)], mechanical=4, deferred=6)]}
        control = {"args": {"arm": "random", "seed": 5}, "games": [_game(
            PREFIX + [ROUND1_R, ["event", "mission 1 on [0, 3]: 1 fail(s), need 1 -> FAIL"],
                      ["event", "seat 1 proposes [1, 2]"],
                      ["event", "vote on [1, 2]: 3/5 approve (approved by [0, 1, 2]) -> APPROVED"]],
            [_vote(3, 0, True, True), _vote(3, 1, True, True), _vote(3, 2, True, True),
             _vote(3, 3, False, True), _vote(3, 4, True, True),
             _vote(6, 0, True, False)],
            mech=[], winner="evil", decisions=11)]}   # a random seat records no split
        r = read_pair(solver, control)
        st = r["stratum"]
        # three proved votes in the shared round pair; the fourth is after divergence
        self.assertEqual((st["paired"], st["unpaired"]), (3, 1))
        self.assertEqual(st["tainted"], {"n": 3, "solver_approve": 0, "random_approve": 2})
        self.assertEqual(st["clean"]["n"], 0)
        self.assertEqual(st["agree"], 1)             # seat 3 rejected in both
        self.assertEqual(st["by_role"], {"seer": 1, "mimic": 1, "hunter": 1})
        self.assertEqual(r["solver"]["mechanical_share"], 0.4)
        self.assertEqual(r["solver"]["mechanical_by_role"], {"seer": 2, "mimic": 1, "hunter": 1})
        self.assertIsNone(r["random"]["mechanical_share"])
        self.assertEqual(r["games_identical"], 0)
        text = render(r)
        self.assertIn("paired 3, unpaired (after divergence) 1", text)
        self.assertIn("clean    n=0    no interval", text)

    def test_different_seeds_are_REFUSED_not_paired(self):
        solver = {"args": {"arm": "solver", "seed": 5}, "games": []}
        control = {"args": {"arm": "random", "seed": 6}, "games": []}
        with self.assertRaises(SystemExit):
            read_pair(solver, control)

    def test_an_unpinned_seed_is_REFUSED(self):
        solver = {"args": {"arm": "solver", "seed": None}, "games": []}
        control = {"args": {"arm": "random", "seed": None}, "games": []}
        with self.assertRaises(SystemExit):
            read_pair(solver, control)

    def test_the_wrong_arm_is_REFUSED(self):
        solver = {"args": {"arm": "random", "seed": 5}, "games": []}
        control = {"args": {"arm": "random", "seed": 5}, "games": []}
        with self.assertRaises(SystemExit):
            read_pair(solver, control)

    def test_the_solver_good_arm_is_read_and_named_as_a_good_side(self):
        """solver-good seats the solver on good only, so its outcome line IS a
        good side against a control - the disclaimer S26 printed must not be
        copied onto it, and the arm name must reach the render."""
        solver = {"args": {"arm": "solver-good", "seed": 5}, "games": []}
        control = {"args": {"arm": "random", "seed": 5}, "games": []}
        r = read_pair(solver, control)
        self.assertEqual(r["arm"], "solver-good")
        text = render(r)
        self.assertIn("solver-good", text)
        self.assertNotIn("sits on every seat", text)
        self.assertIn("GOOD seats only", text)

    def test_the_all_seat_solver_keeps_its_disclaimer(self):
        solver = {"args": {"arm": "solver", "seed": 5}, "games": []}
        control = {"args": {"arm": "random", "seed": 5}, "games": []}
        r = read_pair(solver, control)
        self.assertEqual(r["arm"], "solver")
        self.assertIn("sits on every seat", render(r))


if __name__ == "__main__":
    unittest.main()
