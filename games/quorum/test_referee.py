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


def complete_event(ref: QuorumReferee) -> None:
    """Finish the draw in flight; the referee ends at the next NOMINATE."""
    ref.proposer_discard(ref.proposer, 0)
    ref.enactor_discard(ref.enactor, 0)
    if ref.phase is Phase.POWER:
        ref.use_power(ref.proposer, ref.legal_power_targets(ref.proposer)[0])
    assert ref.phase is Phase.NOMINATE


def vote_through(ref: QuorumReferee, votes: dict[int, bool]) -> None:
    """Speak out the discussion, then cast the roll."""
    while ref.phase is Phase.DISCUSS:
        ref.speak(ref.next_speaker(), "holding.")
    ref.vote(votes)


def parked_after_first_event(seed: int = 3) -> QuorumReferee:
    """One completed draw behind it, parked at the next round's DISCUSS."""
    ref = QuorumReferee.new(5, seed=seed, discussion_rounds=1)
    ref.nominate(ref.proposer, ref.eligible_nominees()[0])
    vote_through(ref, carried(ref))
    complete_event(ref)
    ref.nominate(ref.proposer, ref.eligible_nominees()[0])
    assert ref.phase is Phase.DISCUSS
    return ref


class TestOneClaimPerEvent(unittest.TestCase):
    """A seat files at most one claim about one completed draw: no duplicate
    public assertion, and no draw scored twice for the same seat."""

    def test_a_second_claim_about_the_same_event_is_refused(self):
        ref = parked_after_first_event()
        seat = ref.last_proposer
        cards = list(ref.recall[seat])
        filed = ref.record_claim(seat, cards)
        self.assertEqual(filed.event, 0)
        with self.assertRaises(IllegalAction) as caught:
            ref.record_claim(seat, cards)
        self.assertIn("already claimed", str(caught.exception))

    def test_standing_and_the_offer_disappear_once_claimed(self):
        ref = parked_after_first_event()
        seat = ref.last_proposer
        self.assertEqual(ref.claimable_event(seat), ("proposer", 0))
        self.assertIn('"claim"', ref.action_prompt(seat))
        ref.record_claim(seat, list(ref.recall[seat]))
        self.assertIsNone(ref.claimable_event(seat))
        self.assertIsNone(ref.claimable(seat))
        self.assertNotIn('"claim"', ref.action_prompt(seat))

    def test_the_other_office_claims_the_same_event_independently(self):
        ref = parked_after_first_event()
        proposer, enactor = ref.last_proposer, ref.last_enactor
        ref.record_claim(proposer, list(ref.recall[proposer]))
        filed = ref.record_claim(enactor, list(ref.recall[enactor]))
        self.assertEqual((filed.office, filed.event), ("enactor", 0))

    def test_the_next_completed_event_reopens_the_former_seat(self):
        ref = parked_after_first_event()
        seat = ref.last_proposer
        ref.record_claim(seat, list(ref.recall[seat]))
        # finish this round: the vote fails, then the next government seats the
        # SAME seat as enactor and completes another draw
        vote_through(ref, rejected(ref))
        ref.nominate(ref.proposer, seat)
        vote_through(ref, carried(ref))
        complete_event(ref)
        self.assertEqual(ref.claimable_event(seat), ("enactor", 1))
        filed = ref.record_claim(seat, list(ref.recall[seat]))
        self.assertEqual(filed.event, 1)


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


def parked_with_writs(writs: int, seed: int = 3,
                      hand: list[Card] | None = None) -> QuorumReferee:
    """A referee at PROPOSER_DISCARD with ``writs`` already on the board and, if
    given, the drawn hand replaced so the test controls what gets enacted. The
    nominee is never `principal`, so the install win cannot end the game first."""
    ref = QuorumReferee.new(5, seed=seed, discussion_rounds=0)
    ref.writs = writs
    nominee = next(s for s in ref.eligible_nominees()
                   if not ref.assignment[s].is_principal)
    ref.nominate(ref.proposer, nominee)
    ref.vote(carried(ref))
    assert ref.phase is Phase.PROPOSER_DISCARD
    if hand is not None:
        ref.proposer_hand = list(hand)
        ref.proposer_saw = list(hand)
    return ref


def record_of(ref: QuorumReferee) -> list[str]:
    return [t for k, t in ref.public_events if k == "event"]


class TestPeek(unittest.TestCase):
    """The third writ at five seats grants a look at the deck, never an
    inspection - the published 5-6 board has no investigation on it."""

    def test_the_third_writ_grants_a_peek_not_an_inspection(self):
        self.assertEqual(SETUP_5.power_at(3), "peek")
        ref = parked_with_writs(2, hand=[Card.WRIT] * 3)
        peeker = ref.proposer
        ref.proposer_discard(peeker, 0)
        ref.enactor_discard(ref.enactor, 0)
        self.assertEqual(ref.writs, 3)
        # resolved inline: no target is asked for and no POWER phase is entered
        self.assertIs(ref.phase, Phase.NOMINATE)
        self.assertIsNone(ref.pending_power)
        self.assertEqual(ref.inspections, {})
        self.assertEqual(len(ref.peeks[peeker]), 3)
        line = next(t for t in record_of(ref) if "top of the deck" in t)
        self.assertEqual(line, f"Seat {peeker} looked at the top of the deck. "
                               "What it saw is private.")
        for theme in THEMES.values():
            for name in theme.card_names.values():
                self.assertNotIn(name, line)

    def test_a_peek_shows_the_next_three_draws_to_the_proposer_only(self):
        ref = parked_with_writs(2, hand=[Card.WRIT] * 3)
        peeker = ref.proposer
        ref.proposer_discard(peeker, 0)
        ref.enactor_discard(ref.enactor, 0)
        seen = ref.peeks[peeker]
        shown = ", ".join(ref.theme.card_names[c] for c in seen)
        self.assertIn(f"you looked at the top of the deck: {shown}",
                      ref.render_context(peeker, include_speech=False))
        for seat in ref.living():
            if seat != peeker:
                self.assertNotIn("top of the deck: ",
                                 ref.render_context(seat, include_speech=False))
        # the cards stay where they are, in order: the knowledge is real
        self.assertEqual(ref._draw(3), list(seen))

    def test_a_peek_refills_a_short_deck_before_looking(self):
        ref = parked_with_writs(2, hand=[Card.WRIT] * 3)
        ref.discards += ref.deck[2:]
        ref.deck = ref.deck[:2]
        ref.proposer_discard(ref.proposer, 0)
        peeker = ref.proposer
        ref.enactor_discard(ref.enactor, 0)
        self.assertEqual(len(ref.peeks[peeker]), 3)
        self.assertEqual(ref.discards, [])
        self.assertEqual(tuple(ref.deck[:3]), ref.peeks[peeker])


class TestVeto(unittest.TestCase):
    """Five writs unlock the veto: the enactor may propose it, the proposer
    decides, and an agreed veto discards both cards and counts as a failure."""

    def test_veto_is_unavailable_below_five_writs(self):
        self.assertEqual(SETUP_5.veto_threshold, 5)
        ref = parked_with_writs(4)
        ref.proposer_discard(ref.proposer, 0)
        self.assertIs(ref.phase, Phase.ENACTOR_DISCARD)
        with self.assertRaises(IllegalAction):
            ref.propose_veto(ref.enactor, True)
        ref = parked_with_writs(5)
        ref.proposer_discard(ref.proposer, 0)
        self.assertIs(ref.phase, Phase.VETO_PROPOSE)
        self.assertEqual(ref.on_clock(), [ref.enactor])
        self.assertIn('"veto"', ref.action_prompt(ref.enactor))
        # the enactor still holds its pair while it decides
        self.assertEqual(len(ref.entitled_hand(ref.enactor)), 2)

    def test_an_agreed_veto_discards_both_and_advances_the_failure_track(self):
        ref = parked_with_writs(5)
        proposer, enactor = ref.proposer, ref.enactor
        ref.proposer_discard(proposer, 0)
        ref.propose_veto(enactor, True)
        self.assertIs(ref.phase, Phase.VETO_DECIDE)
        self.assertEqual(ref.on_clock(), [proposer])
        self.assertIn('"veto"', ref.action_prompt(proposer))
        ref.decide_veto(proposer, True)
        self.assertEqual(len(ref.discards), 3)
        self.assertEqual(ref.enactor_hand, [])
        self.assertEqual((ref.charters, ref.writs), (0, 5))
        self.assertEqual(ref.failure_track, 1)
        self.assertIn("The agenda was vetoed. Nothing is enacted.", record_of(ref))
        self.assertIs(ref.phase, Phase.NOMINATE)
        self.assertNotEqual(ref.proposer, proposer)
        # the enactor was seated, so the term limit still bars it
        self.assertNotIn(enactor, ref.eligible_nominees())
        # both remember what they saw; neither has a completed draw to claim about
        self.assertEqual(len(ref.recall[proposer]), 3)
        self.assertEqual(len(ref.recall[enactor]), 2)
        self.assertIsNone(ref.claimable_event(proposer))
        self.assertIsNone(ref.claimable_event(enactor))

    def test_a_refused_veto_falls_through_to_the_enactor_discard(self):
        ref = parked_with_writs(5)
        proposer, enactor = ref.proposer, ref.enactor
        ref.proposer_discard(proposer, 0)
        ref.propose_veto(enactor, True)
        ref.decide_veto(proposer, False)
        self.assertIs(ref.phase, Phase.ENACTOR_DISCARD)
        self.assertIn(f"Seat {proposer} refuses the veto.", record_of(ref))
        self.assertEqual(len(ref.entitled_hand(enactor)), 2)
        self.assertEqual(ref.failure_track, 0)
        ref.enactor_discard(enactor, 0)
        self.assertEqual(ref.charters + ref.writs, 6)

    def test_declining_to_propose_a_veto_is_the_ordinary_discard(self):
        ref = parked_with_writs(5)
        ref.proposer_discard(ref.proposer, 0)
        ref.propose_veto(ref.enactor, False)
        self.assertIs(ref.phase, Phase.ENACTOR_DISCARD)
        self.assertEqual(ref.failure_track, 0)

    def test_a_vetoed_agenda_can_trigger_the_chaos_enactment(self):
        ref = parked_with_writs(5)
        ref.failure_track = SETUP_5.failure_limit - 1
        proposer, enactor = ref.proposer, ref.enactor
        ref.proposer_discard(proposer, 0)
        ref.propose_veto(enactor, True)
        ref.decide_veto(proposer, True)
        self.assertEqual(ref.charters + ref.writs, 6)
        self.assertEqual(ref.failure_track, 0)
        self.assertIsNone(ref.pending_power)
        self.assertIsNone(ref.last_proposer)
        self.assertTrue(any("enacted unseen" in t for t in record_of(ref)))
        # nobody held the unseen card, so nobody may claim about it
        for seat in ref.living():
            self.assertIsNone(ref.claimable_event(seat))


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
                elif ref.phase is Phase.VETO_PROPOSE:
                    ref.propose_veto(clock[0], rng.random() < 0.3)
                elif ref.phase is Phase.VETO_DECIDE:
                    ref.decide_veto(clock[0], rng.random() < 0.3)
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
