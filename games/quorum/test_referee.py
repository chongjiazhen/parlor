"""Referee tests. The cascade ones are the point: everything else this rung does,
the two rungs before it already did.
"""

from __future__ import annotations

import random
import unittest

from games.quorum.referee import IllegalAction, Phase, QuorumReferee
from games.quorum.roles import (ADVANCES, SETUP_5, THEMES, Card, Side)


def carried(ref: QuorumReferee) -> dict[int, bool]:
    return {s: True for s in ref.living()}


def rejected(ref: QuorumReferee) -> dict[int, bool]:
    return {s: False for s in ref.living()}


def drive_to_hand(seed: int = 3) -> QuorumReferee:
    """A referee parked at PROPOSER_DISCARD, which is where the cascade starts."""
    ref = QuorumReferee.new(5, seed=seed, discussion_rounds=0)
    ref.nominate(ref.proposer, ref.eligible_nominees()[0])
    ref.vote(carried(ref))
    return ref


class TestDeal(unittest.TestCase):
    def test_sides_are_three_against_two(self):
        ref = QuorumReferee.new(5, seed=1)
        sides = [r.side for r in ref.assignment.values()]
        self.assertEqual(sides.count(Side.MAJORITY), 3)
        self.assertEqual(sides.count(Side.MINORITY), 2)

    def test_minority_seats_know_each_other_and_majority_knows_nothing(self):
        ref = QuorumReferee.new(5, seed=1)
        for seat, role in ref.assignment.items():
            known = ref.entitled_knowledge(seat)
            if role.side is Side.MAJORITY:
                self.assertEqual(known, ())
            else:
                self.assertEqual(len(known), 1)
                self.assertEqual(known[0].label, "fellow-minority")
                self.assertIs(ref.assignment[known[0].seat].side, Side.MINORITY)

    def test_deck_composition_is_the_setup(self):
        ref = QuorumReferee.new(5, seed=1)
        self.assertEqual(len(ref.deck), SETUP_5.deck_size)
        self.assertEqual(ref.deck.count(Card.CHARTER), SETUP_5.deck_charter)
        self.assertEqual(ref.deck.count(Card.WRIT), SETUP_5.deck_writ)

    def test_same_seed_is_the_same_deal_and_the_same_deck(self):
        a, b = QuorumReferee.new(5, seed=99), QuorumReferee.new(5, seed=99)
        self.assertEqual({s: r.key for s, r in a.assignment.items()},
                         {s: r.key for s, r in b.assignment.items()})
        self.assertEqual(a.deck, b.deck)


class TestCascade(unittest.TestCase):
    """Entitlement keyed on (office, phase), which is what makes this rung new."""

    def test_only_the_proposer_sees_three_and_only_at_its_step(self):
        ref = drive_to_hand()
        self.assertIs(ref.phase, Phase.PROPOSER_DISCARD)
        self.assertEqual(len(ref.entitled_hand(ref.proposer)), 3)
        for seat in ref.living():
            if seat != ref.proposer:
                self.assertIsNone(ref.entitled_hand(seat), f"seat {seat} saw the draw")

    def test_the_enactor_sees_two_and_the_proposer_stops_seeing_anything(self):
        ref = drive_to_hand()
        ref.proposer_discard(ref.proposer, 0)
        self.assertIs(ref.phase, Phase.ENACTOR_DISCARD)
        self.assertEqual(len(ref.entitled_hand(ref.enactor)), 2)
        self.assertIsNone(ref.entitled_hand(ref.proposer))

    def test_the_discarded_card_is_held_in_no_field_afterwards(self):
        """The sharp case. The proposer's third card is entitled to exactly one
        seat for the length of one decision and to nobody afterwards, so the
        entitlement has to expire with the VALUE and not behind a flag."""
        ref = drive_to_hand()
        before = list(ref.proposer_hand)
        ref.proposer_discard(ref.proposer, 0)
        self.assertEqual(ref.proposer_hand, [])
        self.assertEqual(len(ref.enactor_hand), 2)
        # The pair that was passed on is a subset of what was drawn, and the card
        # that was dropped is not reachable from the hand fields at all.
        self.assertTrue(set(ref.enactor_hand) <= set(before))

    def test_a_seat_out_of_office_may_not_discard(self):
        ref = drive_to_hand()
        other = next(s for s in ref.living() if s != ref.proposer)
        with self.assertRaises(IllegalAction):
            ref.proposer_discard(other, 0)

    def test_the_hand_is_rendered_to_its_holder_and_to_nobody_else(self):
        ref = drive_to_hand()
        held = ref.render_context(ref.proposer)
        self.assertIn("In your hand", held)
        for seat in ref.living():
            if seat != ref.proposer:
                self.assertNotIn("In your hand", ref.render_context(seat))

    def test_the_enacted_card_advances_the_side_the_data_says(self):
        ref = drive_to_hand()
        ref.proposer_discard(ref.proposer, 0)
        final = ref.enactor_hand[1]
        ref.enactor_discard(ref.enactor, 0)
        if ADVANCES[final] is Side.MAJORITY:
            self.assertEqual((ref.charters, ref.writs), (1, 0))
        else:
            self.assertEqual((ref.charters, ref.writs), (0, 1))


class TestVoting(unittest.TestCase):
    def test_a_partial_roll_is_refused(self):
        ref = QuorumReferee.new(5, seed=2, discussion_rounds=0)
        ref.nominate(ref.proposer, ref.eligible_nominees()[0])
        with self.assertRaises(IllegalAction):
            ref.vote({0: True})

    def test_a_tie_fails_and_advances_the_office(self):
        ref = QuorumReferee.new(5, seed=2, discussion_rounds=0)
        opener = ref.proposer
        ref.nominate(opener, ref.eligible_nominees()[0])
        seats = ref.living()
        ref.vote({s: (i < 2) for i, s in enumerate(seats)})
        self.assertEqual(ref.failure_track, 1)
        self.assertNotEqual(ref.proposer, opener)

    def test_three_failures_enact_the_top_card_unseen_and_reset(self):
        ref = QuorumReferee.new(5, seed=2, discussion_rounds=0)
        for _ in range(3):
            ref.nominate(ref.proposer, ref.eligible_nominees()[0])
            ref.vote(rejected(ref))
        self.assertEqual(ref.charters + ref.writs, 1)
        self.assertEqual(ref.failure_track, 0)
        # Nobody held that card, so no power fires off it.
        self.assertIsNone(ref.pending_power)

    def test_the_previous_enactor_cannot_be_renominated(self):
        ref = drive_to_hand()
        seated = ref.enactor
        ref.proposer_discard(ref.proposer, 0)
        ref.enactor_discard(seated, 0)
        if ref.phase is Phase.NOMINATE:
            self.assertNotIn(seated, ref.eligible_nominees())


class TestWinConditions(unittest.TestCase):
    def test_seating_the_principal_after_the_threshold_ends_it(self):
        ref = QuorumReferee.new(5, seed=5, discussion_rounds=0)
        ref.writs = SETUP_5.install_threshold
        principal = next(s for s, r in ref.assignment.items() if r.is_principal)
        if principal == ref.proposer:
            ref._advance_proposer()
        ref.nominate(ref.proposer, principal)
        ref.vote(carried(ref))
        self.assertIs(ref.winner, Side.MINORITY)
        self.assertIs(ref.phase, Phase.DONE)

    def test_seating_the_principal_below_the_threshold_does_not(self):
        ref = QuorumReferee.new(5, seed=5, discussion_rounds=0)
        ref.writs = SETUP_5.install_threshold - 1
        principal = next(s for s, r in ref.assignment.items() if r.is_principal)
        if principal == ref.proposer:
            ref._advance_proposer()
        ref.nominate(ref.proposer, principal)
        ref.vote(carried(ref))
        self.assertIsNone(ref.winner)

    def test_removing_the_principal_wins_for_the_majority(self):
        ref = QuorumReferee.new(5, seed=5, discussion_rounds=0)
        ref.phase = Phase.POWER
        ref.pending_power = "remove"
        principal = next(s for s, r in ref.assignment.items() if r.is_principal)
        if principal == ref.proposer:
            ref.proposer = next(s for s in ref.living() if s != principal)
        ref.use_power(ref.proposer, principal)
        self.assertIs(ref.winner, Side.MAJORITY)

    def test_a_removed_seat_keeps_its_role_out_of_the_record(self):
        ref = QuorumReferee.new(5, seed=6, discussion_rounds=0)
        ref.phase = Phase.POWER
        ref.pending_power = "remove"
        target = next(s for s in ref.living()
                      if s != ref.proposer and not ref.assignment[s].is_principal)
        ref.use_power(ref.proposer, target)
        record = " ".join(t for k, t in ref.public_events if k == "event")
        for theme in THEMES.values():
            self.assertNotIn(theme.role_names[ref.assignment[target].key], record)


class TestInspection(unittest.TestCase):
    def test_the_result_reaches_the_inspector_only(self):
        ref = QuorumReferee.new(5, seed=8, discussion_rounds=0)
        ref.phase = Phase.POWER
        ref.pending_power = "inspect"
        inspector = ref.proposer
        target = next(s for s in ref.living() if s != inspector)
        ref.use_power(inspector, target)
        labels = [k.label for k in ref.entitled_knowledge(inspector)
                  if k.seat == target]
        self.assertEqual(labels, [f"inspected-{ref.assignment[target].side.value}"])
        for seat in ref.living():
            if seat != inspector:
                self.assertFalse([k for k in ref.entitled_knowledge(seat)
                                  if k.label.startswith("inspected-")])

    def test_the_record_names_neither_the_subject_nor_the_finding(self):
        ref = QuorumReferee.new(5, seed=8, discussion_rounds=0)
        ref.phase = Phase.POWER
        ref.pending_power = "inspect"
        target = next(s for s in ref.living() if s != ref.proposer)
        ref.use_power(ref.proposer, target)
        line = [t for k, t in ref.public_events if k == "event"][-2]
        self.assertIn("inspected one seat", line)
        self.assertNotIn(f"seat {target}", line)
        for theme in THEMES.values():
            for name in theme.side_names.values():
                self.assertNotIn(name, line)


class TestRandomPlay(unittest.TestCase):
    def test_random_games_terminate_and_never_desync_the_driver(self):
        """A structural bound, not just the win predicate. If the only thing that
        stops the loop is the thing deciding whether to go again, one bad
        predicate runs unattended - so the cap is here and a hit is a failure."""
        for seed in range(40):
            rng = random.Random(seed)
            ref = QuorumReferee.new(5, seed=seed, discussion_rounds=1)
            for _ in range(400):
                if ref.phase is Phase.DONE:
                    break
                clock = ref.on_clock()
                if ref.phase is Phase.NOMINATE:
                    ref.nominate(clock[0], rng.choice(ref.eligible_nominees()))
                elif ref.phase is Phase.DISCUSS:
                    ref.speak(clock[0], "nothing to add")
                elif ref.phase is Phase.VOTE:
                    ref.vote({s: rng.random() < 0.6 for s in clock})
                elif ref.phase is Phase.PROPOSER_DISCARD:
                    ref.proposer_discard(clock[0], rng.randrange(3))
                elif ref.phase is Phase.ENACTOR_DISCARD:
                    ref.enactor_discard(clock[0], rng.randrange(2))
                elif ref.phase is Phase.POWER:
                    ref.use_power(clock[0],
                                  rng.choice([s for s in ref.living()
                                              if s != clock[0]]))
            else:
                self.fail(f"seed {seed} did not terminate inside the bound")
            self.assertIsNotNone(ref.winner, f"seed {seed} ended with no winner")

    def test_a_short_deck_is_rebuilt_from_the_discards_before_a_draw(self):
        """Enacted cards leave play, so the pile shrinks; the discards are what
        refills it. A draw served from two piles would make the composition -
        which RULES.md states as a rule, not a knob - unstateable."""
        ref = QuorumReferee.new(5, seed=11)
        ref.discards = ref.deck[1:]
        ref.deck = ref.deck[:1]
        drawn = ref._draw(3)
        self.assertEqual(len(drawn), 3)
        self.assertEqual(ref.discards, [])


if __name__ == "__main__":
    unittest.main()
