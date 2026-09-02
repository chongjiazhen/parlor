"""The evil-only conference before the hunt, and the gate #1 rule it adds.

Once good holds three missions the two evil seats speak once each, in seat order,
on a channel only the two of them receive; then the hunter names. The channel's
bytes are entitled to the pair by the deal - the night introduced them to each
other - and are a LEAK the moment any of them reaches a seat outside the pair.
That is a new class of secret for the audit to carry, so the audit test comes
first here and the referee follows it.
"""

import random
import unittest

from games.cabal import transcript
from games.cabal.audit import leak_audit
from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee, IllegalAction, Phase
from games.cabal.roles import (HUNTER, LOYALIST, MIMIC, SEER, SETUP_5, STRAY,
                               WATCHER, Team)

FIXED = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}
EVIL = [3, 4]
GOOD = [0, 1, 2]


def fixed_ref():
    return CabalReferee(setup=SETUP_5, assignment=dict(FIXED), leader=0,
                        discussion_rounds=0)


def run_success(ref):
    size = ref.setup.team_sizes[ref.mission_index]
    team = list(range(size))
    ref.propose(ref.leader, team)
    ref.vote({s: True for s in ref.assignment})
    ref.mission({s: False for s in team})


def at_conference():
    ref = fixed_ref()
    for _ in range(3):
        run_success(ref)
    return ref


WORDS = {3: "seat 0 approved every clean team and rejected the one we sat on",
         4: "agreed, and seat 1 hedged all game - I read seat 0 as the informant"}


def conferred():
    ref = at_conference()
    for seat in EVIL:
        ref.confer(seat, WORDS[seat])
    return ref


class TestGate1CarriesTheConference(unittest.TestCase):
    def test_conference_bytes_in_a_good_seat_payload_are_caught_as_a_leak(self):
        # The guard under test. Render the conference into a GOOD seat's context
        # by force and the audit must name the viewer, the speaker and the line.
        ref = conferred()
        line = ref.conference_lines()[0]          # (speaker, rendered line)
        speaker, rendered = line
        clean = ref.render_context

        def leaky(seat, *a, **kw):
            out = clean(seat, *a, **kw)
            return out + f"\n  {rendered}" if seat == 2 else out

        ref.render_context = leaky
        self.assertIn((2, speaker, rendered), leak_audit(ref))

    def test_the_evil_seats_receive_it_and_the_good_seats_do_not(self):
        ref = conferred()
        for seat in EVIL:
            payload = ref.prompt_for(seat) if seat in ref.acting_seats() \
                else ref.render_context(seat)
            for words in WORDS.values():
                self.assertIn(words, payload, f"seat {seat} misses the conference")
        for seat in GOOD:
            payload = ref.render_context(seat)
            for words in WORDS.values():
                self.assertNotIn(words, payload, f"seat {seat} reads the conference")
            self.assertNotIn("confer", payload.lower())

    def test_a_clean_conference_audits_clean(self):
        # The words name the informant by role in the partner's payload. That is a
        # player's claim, so the audit view drops it exactly as it drops speech,
        # and the referee-authored frame around it names no role.
        ref = at_conference()
        ref.confer(3, "seat 0 is the seer, I am sure of it")
        self.assertEqual(leak_audit(ref), [])
        ref.confer(4, "then seat 0 it is")
        self.assertEqual(leak_audit(ref), [])
        self.assertNotIn("seer", ref.render_context(4, include_speech=False))

    def test_the_conference_stays_out_of_the_public_channels(self):
        ref = conferred()
        public = " ".join(text for _, text in ref.public_events)
        for words in WORDS.values():
            self.assertNotIn(words, public)
        self.assertEqual(ref.public_state()["table_talk"], [])


class TestFlow(unittest.TestCase):
    def test_third_success_opens_the_conference_then_the_hunt(self):
        ref = at_conference()
        self.assertIs(ref.phase, Phase.CONFER)
        self.assertEqual(ref.conference_seats(), EVIL)
        self.assertEqual(ref.acting_seats(), [3])
        ref.confer(3, WORDS[3])
        self.assertIs(ref.phase, Phase.CONFER)
        self.assertEqual(ref.acting_seats(), [4])
        ref.confer(4, WORDS[4])
        self.assertIs(ref.phase, Phase.HUNT)
        self.assertEqual(ref.acting_seats(), [4])

    def test_seat_order_is_enforced_and_good_seats_are_refused(self):
        ref = at_conference()
        with self.assertRaises(IllegalAction):
            ref.confer(4, "me first")
        with self.assertRaises(IllegalAction):
            ref.confer(0, "may I join")
        with self.assertRaises(IllegalAction):
            ref.confer(3, "   ")
        self.assertEqual(ref.conference_lines(), [])

    def test_a_pair_the_night_never_introduced_skips_straight_to_the_hunt(self):
        # Under the blind-evil variant the hunter is named nobody and the stray
        # knows nobody. No channel exists between seats that were not introduced.
        ref = CabalReferee(setup=SETUP_5, leader=0, discussion_rounds=0,
                           assignment={0: SEER, 1: WATCHER, 2: LOYALIST,
                                       3: STRAY, 4: HUNTER})
        self.assertEqual(ref.conference_seats(), [])
        for _ in range(3):
            run_success(ref)
        self.assertIs(ref.phase, Phase.HUNT)

    def test_the_ask_names_no_role_and_asks_for_say(self):
        ref = at_conference()
        ask = ref.action_prompt(3)
        self.assertIn('"say"', ask)
        for role in ref.assignment.values():
            self.assertNotIn(role.key, ask.lower())


class TestDriverAndTranscript(unittest.TestCase):
    def test_a_random_game_that_reaches_the_hunt_confers_first(self):
        found = False
        for seed in range(40):
            ref = CabalReferee.new(5, seed=seed, discussion_rounds=0)
            pol = RandomPolicy(rng=random.Random(seed))
            rec = play_game(ref, {s: pol for s in ref.assignment})
            confers = [d for d in rec.decision_log if d.phase == "confer"]
            if not rec.hunt:
                self.assertEqual(confers, [])
                continue
            found = True
            evil = sorted(s for s, r in ref.assignment.items() if r.team is Team.EVIL)
            self.assertEqual([d.seat for d in confers], evil)
            self.assertEqual(len(rec.conference), 2)
        self.assertTrue(found, "no seed reached the hunt")

    def test_the_transcript_shows_the_conference_referee_side_only(self):
        ref = conferred()
        text = transcript.from_referee(ref)
        public, _, rest = text.partition("## Outcome")
        for words in WORDS.values():
            self.assertNotIn(words, public)
            self.assertIn(words, rest)


if __name__ == "__main__":
    unittest.main()
