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
from unittest import mock

from eval.audit_decisions import (_rotate_deals, claimed_a_role_it_was_not_dealt,
                                  control, hunt_named_impossible,
                                  outed_own_role_in_public, over_sabotage)
from games.cabal.roles import THEMES, Team, Theme


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
    """Count explicit self-identifications, not ordinary role vocabulary."""

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

    def test_own_role_used_as_an_outward_tell_is_not_a_self_outing(self):
        """S13: role vocabulary is common table talk, not a claim by itself."""
        bad, total, _ = outed_own_role_in_public(
            [self.game("1984-en", "Seat 3 repeats a Thought Police tell.")])
        self.assertEqual((bad, total), (0, 1))

    def test_as_role_then_first_person_is_a_self_outing(self):
        """S13 keeps an explicit present-tense claim in either common order."""
        bad, total, _ = outed_own_role_in_public(
            [self.game("1984-en", "As Thought Police, I urge approval.")])
        self.assertEqual((bad, total), (1, 1))

    def test_identity_descriptor_before_own_role_is_a_self_outing(self):
        """Natural identity wording must not bypass the claim-shaped check."""
        bad, total, _ = outed_own_role_in_public(
            [self.game("1984-en", "I am a member of the Thought Police.")])
        self.assertEqual((bad, total), (1, 1))

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

    def test_a_CJK_role_adjacent_description_is_not_a_self_outing(self):
        """Possessive continuation says relation to role, not identity as role."""
        bad, total, _ = outed_own_role_in_public(
            [self.game("1984-cn", "我是思想警察的同事。")])
        self.assertEqual((bad, total), (0, 1))

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


class TestASkinWhoseLanguageHasNoRule(unittest.TestCase):
    """The floor. `CLAIM_RULES` holds `en` and `zh`; every other skin is counted by
    plain mention and the count says so.

    Written against skins that do not ship, which is the point - the bug this pins
    is not visible on any record in the tree, and would surface as a clean 0/N the
    first time somebody reskinned the game into a third language. Both fakes name
    their roles in kanji, because that is the shape that defeats a matcher keyed on
    the role name or on the script of the text: a Japanese skin looks Chinese to
    both, and says none of the Chinese claim words.
    """

    JA = Theme("1984-ja", {Team.GOOD: "\u30a4\u30f3\u30b0\u30bd\u30c3\u30af", Team.EVIL: "\u5144\u5f1f\u56e3"},
               {"seer": "\u601d\u60f3\u8b66\u5bdf", "mimic": "\u4e8c\u91cd\u4eba\u683c\u8005"}, lang="ja")
    #: The same skin with its language MISDECLARED as Chinese - the landmine, held
    #: as a fixture so the test below can show what it costs.
    AS_ZH = Theme("1984-ja-mislabelled", JA.faction_names, JA.role_names, lang="zh")

    def game(self, said: str, seat: int = 0) -> dict:
        return {"game": 0, "theme": "1984-ja",
                "assignment": {"0": "seer", "1": "mimic"},
                "utterances": [f"seat {seat}: {said}"]}

    def audit(self, said: str, theme: Theme | None = None):
        with mock.patch.dict(THEMES, {"1984-ja": theme or self.JA}):
            return outed_own_role_in_public([self.game(said)])

    def test_a_self_outing_in_an_unruled_language_SCORES(self):
        """\u79c1\u306f\u601d\u60f3\u8b66\u5bdf\u3067\u3059 - "I am the Thought Police". No rule reads it, so the
        floor does, and the run is not reported as clean."""
        bad, total, _ = self.audit("\u79c1\u306f\u601d\u60f3\u8b66\u5bdf\u3067\u3059\u3002\u4e09\u756a\u306f\u601d\u60f3\u72af\u3060\u3002")
        self.assertEqual((bad, total), (1, 1))

    def test_the_count_says_on_its_FIRST_line_that_these_are_mentions(self):
        """The floor is only honest if the reader is told - the number means
        something different here, and `--show` truncates the tail, not the head."""
        _, _, notes = self.audit("\u79c1\u306f\u601d\u60f3\u8b66\u5bdf\u3067\u3059\u3002")
        self.assertIn("MENTIONS, not claims", notes[0])
        self.assertIn("ja", notes[0])
        self.assertIn("UPPER BOUND", notes[0])

    def test_the_floor_OVER_counts_and_that_is_the_accepted_trade(self):
        """"Seat 3 is the Thought Police" is not a self-outing, and under a ruled
        skin it is not counted. Here it is, because the floor cannot tell. Pinned
        rather than hidden: wrong-high and loud beats wrong-low and silent, and a
        reader who sees this line knows to read the hits."""
        bad, _, notes = self.audit("\u4e09\u756a\u306f\u601d\u60f3\u8b66\u5bdf\u3060\u3002")
        self.assertEqual(bad, 1)
        self.assertIn("MENTIONED its own role", notes[1])

    def test_declaring_the_wrong_language_is_the_SILENT_zero_this_replaces(self):
        """The landmine, priced. Reach for the nearest regex set - the same kanji,
        so surely the Chinese rule - and the skin scores 0 while every seat outs
        itself. That is the 0/1290 again, and it is why `Theme.lang` is declared by
        the skin instead of guessed from the names it carries."""
        bad, total, _ = self.audit("\u79c1\u306f\u601d\u60f3\u8b66\u5bdf\u3067\u3059\u3002", theme=self.AS_ZH)
        self.assertEqual((bad, total), (0, 1))

    def test_a_ruled_skin_is_unaffected_by_the_floor_existing(self):
        """No mention line, and ordinary role talk still scores zero."""
        bad, _, notes = outed_own_role_in_public(
            [{"game": 0, "theme": "1984-en", "assignment": {"0": "seer"},
              "utterances": ["seat 0: Seat 3 repeats a Thought Police tell."]}])
        self.assertEqual(bad, 0)
        self.assertEqual(notes, [])


class TestClaimedARoleItWasNotDealt(unittest.TestCase):
    """The other half of the claim shape: a role the seat does NOT hold.

    Deliberately not an error - a mimic saying "I am the Seer" is the game working
    - so every case here is about the COUNT being readable, not about blame.
    """

    def game(self, said: str, seat: int = 0, theme: str = "1984-en",
             assignment: dict | None = None) -> dict:
        return {"game": 0, "theme": theme,
                "assignment": assignment or {"0": "mimic", "1": "seer"},
                "utterances": [f"seat {seat}: {said}"]}

    def test_an_evil_seat_claiming_the_seers_skin_name_is_counted(self):
        bad, total, notes = claimed_a_role_it_was_not_dealt(
            [self.game("I am the Thought Police - seat 1 is lying.")])
        self.assertEqual((bad, total), (1, 1))
        self.assertIn("holds 'mimic' and claimed seer", notes[-1])

    def test_the_seat_that_ACTUALLY_holds_it_is_not_counted_here(self):
        """The separation from S13. The same sentence from the seer is a
        self-outing, which `outed_own_role_in_public` counts and this does not -
        one utterance must never land in both columns."""
        g = self.game("I am the Thought Police - seat 0 is lying.", seat=1)
        self.assertEqual(claimed_a_role_it_was_not_dealt([g])[0], 0)
        self.assertEqual(outed_own_role_in_public([g])[0], 1)

    def test_naming_another_seats_role_is_not_claiming_it(self):
        """The floor's absence, in one case: this is the most ordinary sentence at
        the table, and a containment match would count it."""
        bad, total, _ = claimed_a_role_it_was_not_dealt(
            [self.game("Seat 1 is the Thought Police.")])
        self.assertEqual((bad, total), (0, 1))

    def test_the_functional_key_is_claimable_with_no_theme(self):
        bad, _, _ = claimed_a_role_it_was_not_dealt(
            [self.game("I am the seer, and I have seen seat 1.", theme="")])
        self.assertEqual(bad, 1)

    def test_the_claimants_own_team_is_reported(self):
        bad, _, notes = claimed_a_role_it_was_not_dealt(
            [self.game("I am the Thought Police - seat 1 is lying.")])
        self.assertEqual(bad, 1)
        self.assertIn("EVIL 1", notes[0])

    def test_a_language_with_no_claim_rule_is_REFUSED_not_scored(self):
        """Where `outed_own_role_in_public` takes the mention floor, this check
        cannot: naming a role you do not hold is ordinary table talk, so a
        containment match would flag most of the record. Those games leave the
        denominator and the refusal is on the first line."""
        ja = Theme("1984-ja", {Team.GOOD: "\u30a4\u30f3\u30b0\u30bd\u30c3\u30af", Team.EVIL: "\u5144\u5f1f\u56e3"},
                   {"seer": "\u601d\u60f3\u8b66\u5bdf", "mimic": "\u4e8c\u91cd\u4eba\u683c\u8005"}, lang="ja")
        with mock.patch.dict(THEMES, {"1984-ja": ja}):
            bad, total, notes = claimed_a_role_it_was_not_dealt(
                [self.game("\u79c1\u306f\u601d\u60f3\u8b66\u5bdf\u3067\u3059\u3002", theme="1984-ja")])
        self.assertEqual((bad, total), (0, 0))
        self.assertIn("REFUSED", notes[0])
        self.assertIn("'ja'", notes[0])


class TestTheClaimControl(unittest.TestCase):
    """A 0 from a string matcher is only evidence once the matcher has been shown
    to fire on the record that produced it. Rotating the deal leaves the speech
    alone, so the two claim counts must trade places."""

    def games(self, said: str) -> list[dict]:
        return [{"game": 0, "theme": "1984-en",
                 "assignment": {"0": "seer", "1": "mimic"},
                 "utterances": [f"seat 0: {said}"]}]

    def test_rotating_the_deal_moves_a_self_outing_into_the_other_column(self):
        g = self.games("I am the Thought Police.")
        rot = _rotate_deals(g)
        self.assertEqual(outed_own_role_in_public(g)[0], 1)
        self.assertEqual(claimed_a_role_it_was_not_dealt(g)[0], 0)
        self.assertEqual(outed_own_role_in_public(rot)[0], 0)
        self.assertEqual(claimed_a_role_it_was_not_dealt(rot)[0], 1)

    def test_the_speech_is_untouched_by_the_rotation(self):
        g = self.games("I am the Thought Police.")
        self.assertEqual(_rotate_deals(g)[0]["utterances"], g[0]["utterances"])
        self.assertEqual(g[0]["assignment"], {"0": "seer", "1": "mimic"})

    def test_a_record_that_fires_passes(self):
        self.assertEqual(control(self.games("I am the Thought Police.")), 0)

    def test_a_record_that_fires_in_NEITHER_reading_is_REFUSED(self):
        """Exit 3, the same refusal the verdict tools use. `hunt20b` is a live
        example: 0/1150 both ways, so its zero cannot be published as evidence of
        a table that never claimed a role."""
        self.assertEqual(control(self.games("Seat 1 has been quiet all round.")), 3)


if __name__ == "__main__":
    unittest.main()
