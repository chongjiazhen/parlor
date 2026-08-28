"""Gate #1 tests, and the mutation checks that make them worth believing.

A test for a guard is vacuous by default: it passes just as happily when the guard
is absent and the scenario never arises. So every clean-state assertion below is
paired with a deliberately broken render that MUST make it fail, and the mutants
are written to compile and run - a mutant that dies at import tests the parser.
"""

from __future__ import annotations

import random
import unittest

from games.quorum.audit import (LeakDetected, assert_no_leak, dependence_leaks,
                                identity_leaks)
from games.quorum.referee import Phase, QuorumReferee
from games.quorum.roles import THEMES, Side


def drive(ref: QuorumReferee, rng: random.Random, steps: int = 400,
          check=None) -> QuorumReferee:
    """Play a random game, running ``check`` at every reachable state."""
    for _ in range(steps):
        if check is not None:
            check(ref)
        if ref.phase is Phase.DONE:
            return ref
        clock = ref.on_clock()
        if ref.phase is Phase.NOMINATE:
            ref.nominate(clock[0], rng.choice(ref.eligible_nominees()))
        elif ref.phase is Phase.DISCUSS:
            ref.speak(clock[0], "seat 4 is one of them, I think")
        elif ref.phase is Phase.VOTE:
            ref.vote({s: rng.random() < 0.6 for s in clock})
        elif ref.phase is Phase.PROPOSER_DISCARD:
            ref.proposer_discard(clock[0], rng.randrange(3))
        elif ref.phase is Phase.ENACTOR_DISCARD:
            ref.enactor_discard(clock[0], rng.randrange(2))
        elif ref.phase is Phase.POWER:
            ref.use_power(clock[0],
                          rng.choice([s for s in ref.living() if s != clock[0]]))
    raise AssertionError("game did not terminate inside the bound")


class TestCleanGames(unittest.TestCase):
    def test_the_gate_holds_at_every_state_of_random_games(self):
        for seed in range(25):
            ref = QuorumReferee.new(5, seed=seed, discussion_rounds=1)
            drive(ref, random.Random(seed), check=assert_no_leak)

    def test_it_holds_under_every_shipped_skin(self):
        for name, theme in THEMES.items():
            ref = QuorumReferee.new(5, seed=4, theme=theme, discussion_rounds=1)
            with self.subTest(theme=name):
                drive(ref, random.Random(4), check=assert_no_leak)

    def test_a_seat_speaking_a_role_name_is_gameplay_and_not_a_leak(self):
        """The line the repo draws in both sibling games: what a seat SAYS is a
        claim, true or false. Only the referee's own bytes are audited."""
        ref = QuorumReferee.new(5, seed=2, discussion_rounds=1)
        ref.nominate(ref.proposer, ref.eligible_nominees()[0])
        speaker = ref.next_speaker()
        name = ref.theme.role_names[ref.assignment[speaker].key]
        ref.speak(speaker, f"I am the {name}, believe it or not")
        assert_no_leak(ref)
        self.assertIn(name, ref.render_context(speaker, include_speech=True))


class TestIdentityMutants(unittest.TestCase):
    """Break the render so it names a role, and require the scan to catch it."""

    def test_a_referee_that_names_another_seats_role_is_caught(self):
        class Leaky(QuorumReferee):
            def render_context(self, seat, include_speech=True):
                base = super().render_context(seat, include_speech)
                other = next(s for s in self.living() if s != seat)
                return base + (f"\nSeat {other} is the "
                               f"{self.theme.role_names[self.assignment[other].key]}.")

        ref = Leaky.new(5, seed=3, discussion_rounds=0)
        found = identity_leaks(ref)
        self.assertTrue(found, "the identity scan passed a render that names a role")
        with self.assertRaises(LeakDetected):
            assert_no_leak(ref)

    def test_the_three_electors_do_not_report_a_mutual_leak(self):
        """The collision this setup creates by construction: three seats share one
        display name, so the term one legitimately reads is the term that would
        betray the other two. Stripping the self line is what makes it auditable,
        and if that strip regresses this test goes red rather than the gate going
        quiet."""
        ref = QuorumReferee.new(5, seed=3, discussion_rounds=0)
        electors = [s for s, r in ref.assignment.items() if r.key == "elector"]
        self.assertEqual(len(electors), 3)
        self.assertEqual(identity_leaks(ref), [])


class TestDependenceMutants(unittest.TestCase):
    """Break the render so it DEPENDS on a card, and require the differential
    check to catch it - including when the words that come out look innocent."""

    def _at_proposer_discard(self, cls, seed=3):
        ref = cls.new(5, seed=seed, discussion_rounds=0)
        ref.nominate(ref.proposer, ref.eligible_nominees()[0])
        ref.vote({s: True for s in ref.living()})
        assert ref.phase is Phase.PROPOSER_DISCARD
        return ref

    def test_showing_the_proposers_hand_to_the_table_is_caught(self):
        class Leaky(QuorumReferee):
            def render_context(self, seat, include_speech=True):
                base = super().render_context(seat, include_speech)
                if self.proposer_hand:
                    shown = ", ".join(self.theme.card_names[c]
                                      for c in self.proposer_hand)
                    return base + f"\nThe drawn hand: {shown}."
                return base

        ref = self._at_proposer_discard(Leaky)
        found = dependence_leaks(ref)
        viewers = {v for v, _ in found}
        self.assertTrue(viewers - {ref.proposer},
                        "a hand rendered to every seat was not caught")
        self.assertTrue(all(f == "proposer_hand" for v, f in found if v != ref.proposer),
                        f"blamed the wrong field: {found}")

    def test_an_innocent_looking_dependence_is_caught(self):
        """The case substring matching cannot reach at all. Nothing here names a
        card: the render leaks one bit of the hand through a word that is in no
        skin's vocabulary, and the differential check does not care."""
        class Leaky(QuorumReferee):
            def render_context(self, seat, include_speech=True):
                base = super().render_context(seat, include_speech)
                if self.proposer_hand and seat != self.proposer:
                    mood = "tense" if self.proposer_hand[0].value == "writ" else "calm"
                    return base + f"\nThe room feels {mood}."
                return base

        ref = self._at_proposer_discard(Leaky)
        found = dependence_leaks(ref)
        self.assertTrue(found, "a render carrying one bit of the hand was not caught")
        with self.assertRaises(LeakDetected):
            assert_no_leak(ref)

    def test_leaking_another_seats_inspection_is_caught(self):
        class Leaky(QuorumReferee):
            def render_context(self, seat, include_speech=True):
                base = super().render_context(seat, include_speech)
                for who, found in sorted(self.inspections.items()):
                    for subject, side in sorted(found.items()):
                        base += (f"\nSeat {who} found seat {subject} to be "
                                 f"{self.theme.side_names[side]}.")
                return base

        ref = Leaky.new(5, seed=8, discussion_rounds=0)
        ref.phase = Phase.POWER
        ref.pending_power = "inspect"
        target = next(s for s in ref.living() if s != ref.proposer)
        ref.use_power(ref.proposer, target)
        found = dependence_leaks(ref)
        self.assertTrue([v for v, _ in found if v != ref.proposer],
                        "another seat's inspection result was not caught")

    def test_the_public_counts_survive_the_flip(self):
        """The check has to be falsifiable in the other direction too. Deck size
        and the enactment tallies are public, so flipping every card in the piles
        must leave every render byte-identical - otherwise the differential is
        firing on legal content and would have to be relaxed until it said
        nothing."""
        ref = QuorumReferee.new(5, seed=6, discussion_rounds=0)
        ref.nominate(ref.proposer, ref.eligible_nominees()[0])
        ref.vote({s: True for s in ref.living()})
        ref.proposer_discard(ref.proposer, 0)
        ref.enactor_discard(ref.enactor, 0)
        self.assertEqual(dependence_leaks(ref), [])
        self.assertGreater(len(ref.discards), 0)

    def test_the_entitled_holder_is_not_reported_against_its_own_hand(self):
        ref = QuorumReferee.new(5, seed=3, discussion_rounds=0)
        ref.nominate(ref.proposer, ref.eligible_nominees()[0])
        ref.vote({s: True for s in ref.living()})
        self.assertIn("In your hand", ref.render_context(ref.proposer))
        self.assertEqual([v for v, _ in dependence_leaks(ref) if v == ref.proposer],
                         [])


class TestInspectionEntitlement(unittest.TestCase):
    def test_a_subject_is_never_told_it_was_looked_at(self):
        ref = QuorumReferee.new(5, seed=8, discussion_rounds=0)
        ref.phase = Phase.POWER
        ref.pending_power = "inspect"
        target = next(s for s in ref.living() if s != ref.proposer)
        ref.use_power(ref.proposer, target)
        rendered = ref.render_context(target, include_speech=False)
        self.assertNotIn("you looked at", rendered)
        for side in Side:
            self.assertNotIn(f"looked at seat {target}", rendered)
        assert_no_leak(ref)


if __name__ == "__main__":
    unittest.main()
