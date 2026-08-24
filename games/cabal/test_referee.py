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


def fixed_ref(discussion_rounds: int = 0):
    """Discussion off by default here: these cases exercise the mission/vote state
    machine, and the discussion phase has its own class below."""
    return CabalReferee(setup=SETUP_5, assignment=dict(FIXED), leader=0,
                        discussion_rounds=discussion_rounds)


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


class TestDiscussion(unittest.TestCase):
    def test_proposal_opens_a_discussion(self):
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        self.assertIs(ref.phase, Phase.DISCUSS)
        self.assertEqual(ref.next_speaker(), 0)          # round-robin from the leader

    def test_round_robin_order_then_vote_opens(self):
        ref = fixed_ref(discussion_rounds=1)
        ref.leader = 3
        ref.propose(3, [0, 1])
        self.assertEqual(ref.speaking_order(), [3, 4, 0, 1, 2])
        for seat in [3, 4, 0, 1, 2]:
            self.assertIs(ref.phase, Phase.DISCUSS)
            ref.speak(seat, f"seat {seat} speaking")
        self.assertIs(ref.phase, Phase.VOTE)
        self.assertIsNone(ref.next_speaker())

    def test_two_rounds_is_two_passes(self):
        ref = fixed_ref(discussion_rounds=2)
        ref.propose(0, [0, 1])
        self.assertEqual(len(ref.speaking_order()), 10)
        for seat in ref.speaking_order():
            ref.speak(seat, "words")
        self.assertIs(ref.phase, Phase.VOTE)

    def test_zero_rounds_skips_straight_to_vote(self):
        ref = fixed_ref(discussion_rounds=0)
        ref.propose(0, [0, 1])
        self.assertIs(ref.phase, Phase.VOTE)

    def test_out_of_turn_speech_refused(self):
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        with self.assertRaises(IllegalAction):
            ref.speak(2, "not my turn")

    def test_empty_utterance_refused(self):
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        with self.assertRaises(IllegalAction):
            ref.speak(0, "   \n ")

    def test_utterance_is_flattened_and_capped(self):
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        ref.speak(0, "line one\nline two   spaced" + "x" * 400)
        said = [t for kind, t in ref.public_events if kind.startswith("speech")][0]
        self.assertNotIn("\n", said)
        self.assertIn("line one line two spaced", said)
        self.assertLessEqual(len(said), 320)             # 280 cap + 'seat N says: ""'

    def test_speech_reaches_every_seat_next_turn(self):
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        ref.speak(0, "I trust seat 4.")
        for viewer in ref.assignment:
            self.assertIn("I trust seat 4.", ref.render_context(viewer))

    def test_a_seat_sees_its_own_words_marked(self):
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        ref.speak(0, "I trust seat 4.")
        self.assertIn('(you) seat 0 says: "I trust seat 4."', ref.render_context(0))
        self.assertNotIn("(you)", ref.render_context(3))

    def test_speech_is_excluded_from_the_audit_view(self):
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        ref.speak(0, "I trust seat 4.")
        self.assertNotIn("I trust seat 4.", ref.render_context(2, include_speech=False))
        # referee-authored events stay in the audit view
        self.assertIn("proposes [0, 1]", ref.render_context(2, include_speech=False))


class TestRecordIsBounded(unittest.TestCase):
    """The record is re-sent on every call, so an unbounded one is a quadratic
    context bill on the longer games further up the ladder."""

    def test_oldest_lines_are_trimmed_and_the_trim_is_declared(self):
        ref = fixed_ref(discussion_rounds=0)
        ref.max_record_lines = 5
        for i in range(20):
            ref._event(f"line {i}")
        rendered = ref.render_context(0)
        self.assertIn("[15 earlier line(s) trimmed]", rendered)
        self.assertIn("line 19", rendered)
        self.assertNotIn("line 3", rendered)

    def test_a_short_game_is_never_trimmed(self):
        ref = fixed_ref(discussion_rounds=1)
        ref.propose(0, [0, 1])
        for seat in ref.speaking_order():
            ref.speak(seat, "a word")
        self.assertNotIn("trimmed", ref.render_context(0))

    def test_trimming_cannot_hide_a_leak_that_is_still_shown(self):
        """Safe-direction check: a line that scrolls off leaves the model's payload
        too, and one still shown is still audited."""
        from games.cabal.audit import leak_audit
        ref = fixed_ref(discussion_rounds=0)
        ref.max_record_lines = 3
        ref._event("clerical note: seat 3 is the mimic")
        for i in range(10):
            ref._event(f"filler {i}")
        self.assertEqual(leak_audit(ref), [])          # scrolled off, not sent
        ref._event("clerical note: seat 3 is the mimic")
        self.assertTrue(any(term == "mimic" for _, _, term in leak_audit(ref)))


class TestPublicChannel(unittest.TestCase):
    def test_deal_is_never_public(self):
        ref = CabalReferee.new(5, seed=3)
        self.assertTrue(any("dealt" in line for line in ref.log))
        self.assertFalse(any("dealt" in t for _, t in ref.public_events))

    def test_win_reason_is_never_public(self):
        ref = fixed_ref()
        for _ in range(3):
            run_success(ref)
        ref.hunt(hunter=4, target=0)
        self.assertTrue(any("WINNER" in line for line in ref.log))
        # the reason names roles ("found the seer") - it must not reach any seat
        self.assertFalse(any("seer" in t for _, t in ref.public_events))

    def test_mission_hides_who_played_which_card(self):
        ref = fixed_ref()
        ref.propose(0, [3, 4])          # both evil
        ref.vote({s: True for s in ref.assignment})
        ref.mission({3: True, 4: False})
        event = [t for k, t in ref.public_events if k == "event"][-1]
        self.assertIn("1 fail(s)", event)
        self.assertNotIn("seat 3", event)


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
