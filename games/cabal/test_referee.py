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
        self.assertIn("[15 earlier line(s) trimmed", rendered)
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


class TestNightAgainstTheTable(unittest.TestCase):
    """The VOTE ask restates a seat's OWN night knowledge against the proposal.

    Measured on the local 12B (n=30 per cell, seer votes in isolation): with the
    context as-is the seer approved a team carrying a seat it had been told serves
    darkness 83% of the time against 90% for a clean team - discrimination +7%,
    i.e. nothing. With the restatement, 37% vs 100%. Holding the fact and using it
    are different things, and only one of them wins games.
    """

    def setUp(self):
        # seat 0 is the seer; seats 3 and 4 are evil
        self.ref = fixed_ref()

    def ask(self, seat: int, team: list[int]) -> str:
        ref = fixed_ref()
        ref.propose(ref.leader, team)
        self.assertIs(ref.phase, Phase.VOTE)
        return ref.action_prompt(seat)

    def test_it_names_the_overlap_when_a_known_evil_is_on_the_team(self):
        ask = self.ask(0, [0, 3])
        self.assertIn("seat(s) [3, 4] serve darkness", ask)
        self.assertIn("contains [3]", ask)

    def test_it_says_so_when_no_known_evil_is_on_the_team(self):
        ask = self.ask(0, [1, 2])
        self.assertIn("contains none of them", ask)

    def test_a_seat_the_night_told_nothing_gets_no_such_line(self):
        """The loyalist knows nothing, so there is nothing to restate - and a line
        implying otherwise would be the referee inventing knowledge."""
        self.assertNotIn("serve darkness", self.ask(2, [0, 3]))

    def test_it_never_names_a_seat_this_one_was_not_told_about(self):
        """The watcher sees 'magic', not 'evil' - restating an aura as darkness
        would hand it a fact the night withheld."""
        ask = self.ask(1, [0, 3])
        self.assertNotIn("serve darkness", ask)

    def test_it_is_absent_outside_a_live_proposal(self):
        ref = fixed_ref()
        self.assertEqual(ref._night_against_the_table(0), "")   # PROPOSE, no team yet


class TestSimultaneousDiscussion(unittest.TestCase):
    """Sequential discussion anchors: seat 2 reads seat 0 and seat 1 before it
    speaks, so a table can converge on the first read without anyone deducing.
    Simultaneous discussion makes every seat commit against the same board."""

    def talking_ref(self, simultaneous: bool, rounds: int = 1):
        ref = CabalReferee(setup=SETUP_5, assignment=dict(FIXED), leader=0,
                           discussion_rounds=rounds, simultaneous=simultaneous)
        ref.propose(0, [0, 1])
        return ref

    def test_sequential_lets_a_later_seat_read_an_earlier_one(self):
        ref = self.talking_ref(simultaneous=False)
        ref.speak(0, "seat 3 worries me")
        self.assertIn("seat 3 worries me", ref.render_context(1))

    def test_simultaneous_hides_the_round_until_everyone_has_spoken(self):
        ref = self.talking_ref(simultaneous=True)
        ref.speak(0, "seat 3 worries me")
        self.assertNotIn("seat 3 worries me", ref.render_context(1))
        for seat in (1, 2, 3):
            ref.speak(seat, f"seat {seat} reporting")
        self.assertNotIn("seat 3 worries me", ref.render_context(4))  # last to speak
        ref.speak(4, "seat 4 reporting")
        self.assertIn("seat 3 worries me", ref.render_context(4))     # now published

    def test_the_whole_round_lands_in_speaking_order(self):
        ref = self.talking_ref(simultaneous=True)
        for seat in ref.speaking_order():
            ref.speak(seat, f"line from {seat}")
        said = [t for k, t in ref.public_events if k.startswith("speech:")]
        self.assertEqual(len(said), 5)
        self.assertTrue(said[0].startswith("seat 0"))
        self.assertTrue(said[-1].startswith("seat 4"))

    def test_round_two_still_sees_round_one(self):
        """Simultaneity is within a round, not across them - the second round is
        where a seat answers what the table actually said."""
        ref = self.talking_ref(simultaneous=True, rounds=2)
        order = ref.speaking_order()
        for seat in order[:5]:
            ref.speak(seat, f"first round from {seat}")
        self.assertIn("first round from 0", ref.render_context(order[5]))

    def test_nothing_is_left_pending_when_the_vote_opens(self):
        ref = self.talking_ref(simultaneous=True, rounds=2)
        for seat in ref.speaking_order():
            ref.speak(seat, f"line from {seat}")
        self.assertIs(ref.phase, Phase.VOTE)
        self.assertEqual(ref._pending_speech, [])
        self.assertEqual(
            len([t for k, t in ref.public_events if k.startswith("speech:")]), 10)


class TestFactsOutrankChatterInTheTrim(unittest.TestCase):
    """What the record drops decides what a seat can deduce from.

    Measured on the first live runs: at two discussion rounds, speech outnumbers
    referee facts about four to one, and 10 of 16 games crossed the 60-line cap.
    Trimming oldest-first therefore deleted missions 1 and 2 - who was on the team
    that failed, and how each seat voted on it - while keeping eighty lines of
    table talk. The table was asked to deduce from evidence the referee had
    already thrown away.
    """

    def loaded_ref(self, facts: int, speech: int, cap: int):
        ref = fixed_ref(discussion_rounds=0)
        ref.max_record_lines = cap
        for i in range(facts):
            ref._event(f"mission {i} result")
        for i in range(speech):
            ref.public_events.append((f"speech:{i % 5}", f"seat {i % 5} says: chatter {i}"))
        return ref

    def test_every_mission_result_survives_a_record_full_of_talk(self):
        ref = self.loaded_ref(facts=20, speech=80, cap=60)
        rendered = ref.render_context(0)
        for i in range(20):
            self.assertIn(f"mission {i} result", rendered)

    def test_the_oldest_talk_is_what_goes(self):
        ref = self.loaded_ref(facts=20, speech=80, cap=60)
        rendered = ref.render_context(0)
        self.assertNotIn("chatter 0", rendered)
        self.assertIn("chatter 79", rendered)

    def test_the_budget_still_holds(self):
        """Priority within the cap, not exemption from it - the record is re-sent
        on every call, and the games up the ladder are longer than this one."""
        ref = self.loaded_ref(facts=20, speech=80, cap=60)
        body = ref.render_context(0).split("Public record (everyone sees this):")[1]
        shown = [ln for ln in body.splitlines() if ln.strip() and "trimmed" not in ln]
        self.assertEqual(len(shown), 60)

    def test_facts_alone_over_budget_still_trim(self):
        ref = self.loaded_ref(facts=30, speech=0, cap=10)
        rendered = ref.render_context(0)
        self.assertIn("mission 29 result", rendered)
        self.assertNotIn("mission 0 result", rendered)


class TestHuntCannotNameYourOwnSide(unittest.TestCase):
    """Naming a seat the night named as your own is not a bad read, it is an
    impossible one - the seer is good, so a seat you were told is evil cannot be
    it. Measured across every live run: 5 of 26 hunts did exactly that.

    It matters because RandomPolicy never does it (it excludes known fellow-evil,
    which is why the baseline is 1 in 3 and not 1 in 4). Leaving it legal scored
    the model against a control using knowledge the model was throwing away.
    """

    def reached_hunt(self):
        ref = fixed_ref()                       # 3 mimic, 4 hunter, 0 seer
        for _ in range(3):
            run_success(ref)
        self.assertIs(ref.phase, Phase.HUNT)
        return ref

    def test_the_referee_refuses_a_strike_on_a_known_ally(self):
        ref = self.reached_hunt()
        with self.assertRaises(IllegalAction) as caught:
            ref.hunt(4, 3)                      # 3 is the hunter's fellow evil
        self.assertIn("one of your own", str(caught.exception))
        self.assertIsNone(ref.winner)           # the game is not over, it retries

    def test_the_policy_is_told_before_the_move_is_applied(self):
        """Checked by validate_hunt too, so the retry loop can hand the seat the
        reason while it can still choose again - the same split as validate_card."""
        ref = self.reached_hunt()
        with self.assertRaises(IllegalAction):
            ref.validate_hunt(4, 3)
        ref.validate_hunt(4, 0)                 # a legal target raises nothing

    def test_a_legal_strike_still_decides_the_game(self):
        ref = self.reached_hunt()
        ref.hunt(4, 0)                          # seat 0 is the seer
        self.assertIs(ref.winner, Team.EVIL)

    def test_a_miss_on_a_legal_target_still_loses(self):
        ref = self.reached_hunt()
        ref.hunt(4, 1)                          # watcher, not the seer
        self.assertIs(ref.winner, Team.GOOD)
