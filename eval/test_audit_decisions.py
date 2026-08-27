"""The decision audit's four derived numbers, each against the variant that breaks it.

Every check in ``audit_decisions`` reads a FINISHED record, which means it holds a
second copy of the rules - and a second copy drifts. Three of the four checks here
were wrong on their own terms before 2026-08-27, and all three were wrong in the
same way: a knowledge model or a vocabulary hardcoded from the 5-seat, 1984-skinned
run that happened to be in hand.

  - ``hunt_named_impossible`` derived allies as "every other evil", so a ``stray``
    - named to nobody - would have been flagged as an ally the hunter knew. That is
    a legal hunt reported as a REGRESSION, in the one check whose non-zero count is
    supposed to mean the referee broke.
  - ``over_sabotage`` counted the double fail on the mission that ENDED the game,
    where the redundant card costs nothing.
  - ``outed_own_role_in_public`` matched ``seer``/``mimic`` against speech rendered
    as "Thought Police" and "Doublethinker", so its 0/1290 was a property of the
    matcher, not of the play.

So each case here is written against the variant, not against the shipping deal.
A test that only ever sees ``SETUP_5`` under ``1984-en`` passes on all three bugs.
"""

from __future__ import annotations

import unittest

from eval.audit_decisions import (hunt_named_impossible, outed_own_role_in_public,
                                  over_sabotage)


def mission_event(index: int, fails: int, need: int = 1) -> list:
    return ["event", f"mission {index} on [0, 1, 2]: {fails} fail(s), need {need} "
                     f"-> {'SUCCESS' if fails < need else 'FAIL'}"]


class TestHuntNamedImpossible(unittest.TestCase):
    """Allies come from ``known_allies`` - the same function the referee validates
    against - so a variant that changes what the night says moves both at once."""

    def game(self, assignment: dict[int, str], target: int, hunter: int = 4) -> dict:
        return {"game": 0, "assignment": {str(s): k for s, k in assignment.items()},
                "hunt": {"hunter": hunter, "target": target, "hit": False}}

    FIVE = {0: "seer", 1: "watcher", 2: "loyalist", 3: "mimic", 4: "hunter"}
    #: the blind-evil variant: seat 3 is named to nobody and knows nobody
    STRAY = {0: "seer", 1: "watcher", 2: "loyalist", 3: "stray", 4: "hunter"}

    def test_naming_a_seat_the_night_named_is_impossible(self):
        bad, total, notes = hunt_named_impossible([self.game(self.FIVE, target=3)])
        self.assertEqual((bad, total), (1, 1))
        self.assertIn("named ally 3", notes[0])

    def test_naming_itself_is_impossible(self):
        bad, _, notes = hunt_named_impossible([self.game(self.FIVE, target=4)])
        self.assertEqual(bad, 1)
        self.assertIn("named ITSELF", notes[0])

    def test_naming_a_STRAY_is_legal_and_must_not_be_flagged(self):
        """The regression this file exists for. A stray is evil and is named to
        nobody, so the hunter cannot know it - naming it is a legal, and possibly
        good, read. The old "every other evil is an ally" derivation reports it as
        a referee regression, which is a confident wrong answer with a number on it.
        """
        bad, total, _ = hunt_named_impossible([self.game(self.STRAY, target=3)])
        self.assertEqual((bad, total), (0, 1))

    def test_a_clean_hunt_is_clean(self):
        bad, total, _ = hunt_named_impossible([self.game(self.FIVE, target=0)])
        self.assertEqual((bad, total), (0, 1))

    def test_an_unreadable_assignment_says_so_instead_of_guessing(self):
        g = self.game(self.FIVE, target=0)
        g["assignment"] = {}
        bad, total, notes = hunt_named_impossible([g])
        self.assertEqual(bad, 0)
        self.assertIn("not checked", notes[0])


class TestOverSabotage(unittest.TestCase):
    """Conditioned on the game continuing, and scored against SUNK missions."""

    def game(self, *missions) -> dict:
        return {"game": 0, "public_events": list(missions)}

    def test_a_redundant_fail_on_a_continuing_mission_counts(self):
        bad, total, _ = over_sabotage([self.game(mission_event(1, 2))])
        self.assertEqual((bad, total), (1, 1))

    def test_the_game_ENDING_double_fail_is_free_and_excluded(self):
        """Evil's third failed mission ends the game on that resolution: the
        identification is never paid for and the extra card weakly insures against
        a miscount. Counting it inflated the rate the repo quotes.

        Both halves asserted - excluded from the numerator AND from the
        denominator. Dropping it from one only is a subtler version of the same
        wrong number.
        """
        bad, total, notes = over_sabotage([self.game(
            mission_event(1, 1), mission_event(2, 1), mission_event(3, 2))])
        self.assertEqual((bad, total), (0, 2))
        self.assertIn("EXCLUDED as costless", notes[0])

    def test_a_HELD_mission_is_not_in_the_denominator(self):
        """A redundant fail can only be played on a mission that sank, so scoring
        it against every resolution mixes in missions where the move was not
        available - and quietly halves the rate."""
        bad, total, _ = over_sabotage([self.game(
            mission_event(1, 0), mission_event(2, 0), mission_event(3, 2))])
        self.assertEqual((bad, total), (1, 1))

    def test_the_third_FAIL_is_terminal_even_after_successes(self):
        """Three fails end the game wherever they land in the sequence - the
        counter is over failed missions, not over missions."""
        bad, total, _ = over_sabotage([self.game(
            mission_event(1, 1), mission_event(2, 0), mission_event(3, 1),
            mission_event(4, 0), mission_event(5, 2))])
        self.assertEqual((bad, total), (0, 2))


class TestOutedOwnRoleInPublic(unittest.TestCase):
    """Matched against the theme's display names, because those are the only words
    a skinned run's speech contains."""

    def game(self, theme: str, said: str, seat: int = 0) -> dict:
        return {"game": 0, "theme": theme,
                "assignment": {"0": "seer", "1": "mimic"},
                "utterances": [f"seat {seat}: {said}"]}

    def test_the_shipping_skin_is_matched_by_its_display_name(self):
        """The bug this replaces: 0/1290 on two 20-game runs, because the matcher
        looked for "seer" in speech that could only ever say "Thought Police"."""
        bad, total, notes = outed_own_role_in_public(
            [self.game("1984-en", "Fine - I am the Thought Police, and seat 3 is a "
                                  "thoughtcriminal.")])
        self.assertEqual((bad, total), (1, 1))
        self.assertIn("Thought Police", notes[0])

    def test_naming_ANOTHER_seat_s_role_is_not_outing_your_own(self):
        bad, _, _ = outed_own_role_in_public(
            [self.game("1984-en", "Seat 1 is the Doublethinker.")])
        self.assertEqual(bad, 0)

    def test_a_CJK_skin_is_matched_where_a_word_boundary_would_not_be(self):
        """``\\b`` is a word/non-word transition and CJK characters are word
        characters with no spaces between them, so a boundary match never fires
        inside an ordinary Chinese sentence - the `1984-cn` skin would go silently
        unchecked, which is the same silence the English bug produced."""
        bad, _, _ = outed_own_role_in_public(
            [self.game("1984-cn", "我就是思想警察,三号是思想犯。")])
        self.assertEqual(bad, 1)

    def test_the_functional_key_is_still_matched(self):
        bad, _, _ = outed_own_role_in_public(
            [self.game("plain", "I am the Seer, and I have seen seat 3.")])
        self.assertEqual(bad, 1)

    def test_an_unknown_theme_is_checked_narrowly_and_SAYS_so(self):
        """Silently narrowing the match is how the 0/1290 happened. A run whose
        skin the audit cannot resolve gets the caveat on the first line, where
        ``--show`` cannot truncate it away."""
        g = self.game("some-future-skin", "I am the Thought Police.")
        bad, _, notes = outed_own_role_in_public([g])
        self.assertEqual(bad, 0)
        self.assertIn("no known theme", notes[0])


if __name__ == "__main__":
    unittest.main()
