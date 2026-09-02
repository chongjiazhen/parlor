"""The random-active turn arm: who holds the floor, and the idle action.

Off by default. Every test here is written against the arm's two promises:

  - **The DEAL does not move.** The turn schedule draws from its own stream, so
    the same seed deals the same night under either mode. A pair whose deals
    differ is not a pair, and this is the test that says so.
  - **The only referee bytes that change are the ones the mode is about** - the
    discussion-opening event and the DISCUSS ask. Everything else a seat is shown
    is byte-identical, asserted rather than argued.
"""

from __future__ import annotations

import random
import unittest

from core.replies import ParseError
from games.changeling.audit import assert_no_leak, leak_audit
from games.changeling.player import RandomPolicy, parse_action, play_game
from games.changeling.referee import (TURNS_FIXED, TURNS_RANDOM_ACTIVE,
                                      ChangelingReferee, IllegalAction, Phase)


def ref_for(seed: int, mode: str = TURNS_FIXED,
            rounds: int = 2) -> ChangelingReferee:
    return ChangelingReferee.new(5, seed=seed, discussion_rounds=rounds,
                                 turn_mode=mode)


class TestTheModeIsValidated(unittest.TestCase):
    def test_default_is_fixed(self):
        self.assertEqual(ref_for(1).turn_mode, TURNS_FIXED)

    def test_an_unknown_mode_is_refused_at_construction(self):
        with self.assertRaises(ValueError):
            ref_for(1, "round-robin-ish")


class TestTheSchedule(unittest.TestCase):
    def test_fixed_order_is_unchanged(self):
        self.assertEqual(ref_for(7).speaking_order(), [0, 1, 2, 3, 4])

    def test_a_random_active_round_is_a_budget_of_n_turns(self):
        ref = ref_for(7, TURNS_RANDOM_ACTIVE)
        self.assertEqual(len(ref.speaking_order()), ref.n)

    def test_the_schedule_is_stable_within_a_round(self):
        """``acting_seats`` re-reads it on every audit, so a re-draw would make
        the audited seat and the asked seat different seats."""
        ref = ref_for(7, TURNS_RANDOM_ACTIVE)
        self.assertEqual(ref.speaking_order(), ref.speaking_order())

    def test_the_schedule_is_seeded_from_the_game_seed(self):
        a = ref_for(11, TURNS_RANDOM_ACTIVE).speaking_order()
        b = ref_for(11, TURNS_RANDOM_ACTIVE).speaking_order()
        self.assertEqual(a, b)

    def test_different_seeds_give_different_schedules(self):
        seen = {tuple(ref_for(s, TURNS_RANDOM_ACTIVE).speaking_order())
                for s in range(40)}
        self.assertGreater(len(seen), 1)

    def test_it_is_not_merely_the_fixed_order(self):
        seen = {tuple(ref_for(s, TURNS_RANDOM_ACTIVE).speaking_order())
                for s in range(40)}
        self.assertTrue(any(o != (0, 1, 2, 3, 4) for o in seen))

    def test_later_rounds_draw_again(self):
        ref = ref_for(11, TURNS_RANDOM_ACTIVE, rounds=6)
        orders = []
        for _ in range(6):
            orders.append(tuple(ref.speaking_order()))
            for seat in ref.speaking_order():
                ref.listen(seat)
            ref.close_round()
        self.assertGreater(len(set(orders)), 1)


class TestTheDealDoesNotMove(unittest.TestCase):
    def test_same_seed_deals_the_same_night_under_either_mode(self):
        for seed in range(30):
            a = ref_for(seed, TURNS_FIXED)
            b = ref_for(seed, TURNS_RANDOM_ACTIVE)
            self.assertEqual(a.night.dealt, b.night.dealt, seed)
            self.assertEqual(a.night.truth, b.night.truth, seed)
            self.assertEqual(a.night.belief, b.night.belief, seed)
            self.assertEqual(a.night.knowledge, b.night.knowledge, seed)


class TestThePayloadDelta(unittest.TestCase):
    """The whole measured change, named line by line."""

    def test_the_render_differs_by_exactly_the_opening_line(self):
        for seed in range(20):
            a = ref_for(seed, TURNS_FIXED)
            b = ref_for(seed, TURNS_RANDOM_ACTIVE)
            for seat in range(a.n):
                left = a.render_context(seat).splitlines()
                right = b.render_context(seat).splitlines()
                self.assertEqual(len(left), len(right))
                differ = [i for i, (x, y) in enumerate(zip(left, right))
                          if x != y]
                self.assertEqual(len(differ), 1, (seed, seat, differ))
                self.assertIn("Discussion opens", left[differ[0]])

    def test_the_preamble_and_the_seat_line_are_byte_identical(self):
        for seed in range(20):
            a = ref_for(seed, TURNS_FIXED)
            b = ref_for(seed, TURNS_RANDOM_ACTIVE)
            self.assertEqual(a.preamble(), b.preamble())
            for seat in range(a.n):
                self.assertEqual(a.self_line(seat), b.self_line(seat))

    def test_the_vote_ask_is_byte_identical(self):
        a, b = ref_for(3, TURNS_FIXED), ref_for(3, TURNS_RANDOM_ACTIVE)
        for ref in (a, b):
            ref.phase = Phase.VOTE
        for seat in range(a.n):
            self.assertEqual(a.ask(seat), b.ask(seat))

    def test_only_the_random_active_ask_offers_the_idle_action(self):
        self.assertNotIn("listen", ref_for(3).ask(0).lower())
        self.assertIn("listen", ref_for(3, TURNS_RANDOM_ACTIVE).ask(0).lower())


class TestOnlyTheActiveSeatIsAsked(unittest.TestCase):
    def test_fixed_asks_every_seat(self):
        ref = ref_for(5)
        self.assertEqual(ref.acting_seats(), (0, 1, 2, 3, 4))

    def test_random_active_asks_exactly_the_seat_on_the_clock(self):
        ref = ref_for(5, TURNS_RANDOM_ACTIVE)
        order = ref.speaking_order()
        for expected in order:
            self.assertEqual(ref.acting_seats(), (expected,))
            ref.listen(expected)
        self.assertEqual(ref.acting_seats(), ())


class TestTheIdleAction(unittest.TestCase):
    def test_listening_publishes_nothing(self):
        ref = ref_for(5, TURNS_RANDOM_ACTIVE)
        before = list(ref.public_events)
        ref.listen(ref.speaking_order()[0])
        self.assertEqual(ref.public_events, before)

    def test_listening_spends_the_turn(self):
        ref = ref_for(5, TURNS_RANDOM_ACTIVE)
        ref.listen(ref.speaking_order()[0])
        self.assertEqual(ref.turn_index, 1)

    def test_listening_is_refused_under_fixed_order(self):
        with self.assertRaises(IllegalAction):
            ref_for(5).listen(0)

    def test_listening_is_refused_outside_discussion(self):
        ref = ref_for(5, TURNS_RANDOM_ACTIVE)
        ref.phase = Phase.VOTE
        with self.assertRaises(IllegalAction):
            ref.listen(0)

    def test_speaking_is_refused_from_a_seat_not_on_the_clock(self):
        ref = ref_for(5, TURNS_RANDOM_ACTIVE)
        wrong = [s for s in range(ref.n) if s != ref.speaking_order()[0]][0]
        with self.assertRaises(IllegalAction):
            ref.speak(wrong, "out of turn")

    def test_speaking_out_of_turn_is_still_legal_under_fixed_order(self):
        """The floor is a rule of the new mode only; `fixed` keeps its own
        contract, where the driver's loop is the order."""
        ref = ref_for(5)
        self.assertEqual(ref.speak(3, "hello"), "hello")

    def test_listening_is_refused_from_a_seat_not_on_the_clock(self):
        ref = ref_for(5, TURNS_RANDOM_ACTIVE)
        wrong = [s for s in range(ref.n) if s != ref.speaking_order()[0]][0]
        with self.assertRaises(IllegalAction):
            ref.listen(wrong)


class TestTheParserFollowsTheMode(unittest.TestCase):
    def test_an_empty_say_is_refused_under_fixed_order(self):
        ref = ref_for(5)
        with self.assertRaises(ParseError):
            parse_action('{"think": "x", "say": ""}', ref, 0)

    def test_an_empty_say_is_the_idle_action_under_random_active(self):
        ref = ref_for(5, TURNS_RANDOM_ACTIVE)
        out = parse_action('{"think": "x", "say": ""}', ref, 0)
        self.assertEqual(out["say"], "")

    def test_a_missing_say_is_still_refused_under_random_active(self):
        """Silence must be CHOSEN. A reply with no ``say`` field at all is a
        malformed reply, and reading it as an idle action would launder a parse
        failure into a legal move and out of the fallback count."""
        ref = ref_for(5, TURNS_RANDOM_ACTIVE)
        with self.assertRaises(ParseError):
            parse_action('{"think": "x"}', ref, 0)


class LeaksInTheAsk(ChangelingReferee):
    """A referee that puts a seat-card association in the new ask."""

    def ask(self, seat: int) -> str:
        base = super().ask(seat)
        if self.phase is Phase.DISCUSS:
            return base + " " + self.reveal_forms(0, self.holds(0).key)[0]
        return base


class TestGateOneCoversTheNewAsk(unittest.TestCase):
    def test_the_honest_random_active_ask_is_clean(self):
        for seed in range(30):
            assert_no_leak(ref_for(seed, TURNS_RANDOM_ACTIVE))

    def test_a_leaky_random_active_ask_is_caught(self):
        ref = LeaksInTheAsk.new(5, seed=5, discussion_rounds=2,
                                turn_mode=TURNS_RANDOM_ACTIVE)
        leaks = leak_audit(ref)
        self.assertTrue(leaks)
        self.assertEqual({seat for _, seat, _ in leaks}, {0})
        self.assertEqual({viewer for viewer, _, _ in leaks},
                         {ref.speaking_order()[ref.turn_index]})


class TestTheControlPolicy(unittest.TestCase):
    def test_the_random_policy_can_both_speak_and_listen(self):
        ref = ref_for(5, TURNS_RANDOM_ACTIVE)
        policy = RandomPolicy(random.Random(0))
        said = {policy.act(ref, 0)["say"] for _ in range(200)}
        self.assertIn("", said)
        self.assertTrue(any(s for s in said))

    def test_the_random_policy_never_listens_under_fixed_order(self):
        ref = ref_for(5)
        policy = RandomPolicy(random.Random(0))
        said = {policy.act(ref, 0)["say"] for _ in range(200)}
        self.assertNotIn("", said)


class TestTheDriver(unittest.TestCase):
    def test_a_random_active_game_plays_to_a_winner_under_audit(self):
        for seed in range(12):
            ref = ref_for(seed, TURNS_RANDOM_ACTIVE)
            rng = random.Random(seed)
            rec = play_game(ref, {s: RandomPolicy(rng) for s in range(ref.n)})
            self.assertIsNone(rec.error)
            self.assertIn(rec.winner, ("village", "pack"))
            self.assertEqual(rec.fallbacks, 0)

    def test_the_record_carries_the_mode(self):
        rng = random.Random(0)
        fixed = play_game(ref_for(5), {s: RandomPolicy(rng) for s in range(5)})
        rand = play_game(ref_for(5, TURNS_RANDOM_ACTIVE),
                         {s: RandomPolicy(rng) for s in range(5)})
        self.assertEqual(fixed.turns, TURNS_FIXED)
        self.assertEqual(rand.turns, TURNS_RANDOM_ACTIVE)

    def test_a_listened_turn_is_recorded_as_a_decision(self):
        """The budget is decisions, and that is what makes the arm pair against
        the fixed one: a listened turn is a model call like any other."""
        rng = random.Random(3)
        rec = play_game(ref_for(3, TURNS_RANDOM_ACTIVE),
                        {s: RandomPolicy(rng) for s in range(5)})
        discuss = [d for d in rec.decision_log if d.phase == "discuss"]
        self.assertEqual(len(discuss), 5 * 2)
        self.assertLessEqual(len(rec.utterances), len(discuss))


if __name__ == "__main__":
    unittest.main()
