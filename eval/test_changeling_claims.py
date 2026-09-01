"""The controls come first, as they do for every instrument in this directory.

Two things could make `changeling_claims` publish a confident wrong number with
nothing in the output to say so: a claim scored against the wrong seat's deal, and
a skin whose language has no claim rule reading as a table that never claimed
anything. Both are refusals in `control`, and both are pinned here against a
record built to trip them.

The third is a re-baseline the other way. `_ADORN` widened the claim shape that
S13 and S16 published cabal counts with, so those counts are pinned too: a
widening that moves a published number is a re-baseline and needs a criterion, not
a test.
"""
from __future__ import annotations

import functools
import unittest

from eval import records_gate
from eval.audit_decisions import (_claim_en_dealt, claimed_a_role_it_was_not_dealt,
                                  claims_dealt_role, claims_own_role,
                                  load as load_jsonl, outed_own_role_in_public)
from eval.changeling_claims import (Claim, chance, claims_of, control,
                                    deck_names, integrity_control, load,
                                    report, speeches)

HUNT20C = "eval/records/hunt20c.json.jsonl"
S2 = "eval/records/s2.json"


@functools.cache
def hunt20c() -> list[dict]:
    """cabal's records, or a skip where they were never run. Read lazily, so the
    synthetic cases above stay in the suite in a tree with no run output."""
    records_gate.demand(HUNT20C)
    return load_jsonl(HUNT20C)


def game(**over) -> dict:
    """One five-seat folk game, minimal but shaped exactly like a record.

    Seat 1 is the interesting one: dealt `pack`, robbed at night, so it believes
    `pack`, holds `swapper` at dawn and is a villager who does not know it.
    """
    said = over.pop("said", ["I went to sleep as the Seer.",
                             "I am the Sleepwalker.",
                             "Seat 0 went to sleep as the Seer, so seat 3 is lying.",
                             "Nothing from me tonight.",
                             "I am still the Villager."])
    seats = list(range(5))
    base = {
        "game": 0,
        "theme": "folk",
        "dealt": {"0": "spotter", "1": "pack", "2": "bystander",
                  "3": "switcher", "4": "swapper"},
        "belief": {"0": "spotter", "1": "pack", "2": "bystander",
                   "3": "switcher", "4": "bystander"},
        "truth": {"0": "spotter", "1": "swapper", "2": "bystander",
                  "3": "switcher", "4": "pack"},
        "utterances": list(said),
        "public_events": [["speech", f"Seat {s}: {t}"]
                          for s, t in zip(seats, said)],
        "decision_log": [{"phase": "discuss", "seat": s, "fell_back": False}
                         for s in seats],
        "decisions": 5,
        "fallbacks": 0,
    }
    base.update(over)
    return base


def summary_for(games: list[dict]) -> dict:
    return {"score": {"integrity": {
        "decisions": sum(g["decisions"] for g in games),
        "fallbacks": sum(g["fallbacks"] for g in games),
        "fallback_rate": 0.0}}}


class TestTheSeatAttributionControl(unittest.TestCase):
    """The claim is scored against a seat's deal, so the seat has to be right."""

    def test_a_clean_record_holds(self):
        self.assertEqual(control([game()]), [])

    def test_the_two_sources_disagreeing_about_who_spoke_refuses(self):
        """Published speech says one order, the decision log says another. Every
        claim would land on the wrong seat's deal, which is worse than no claim -
        so nothing is printed and the tool exits non-zero."""
        g = game()
        g["decision_log"] = [{"phase": "discuss", "seat": s, "fell_back": False}
                             for s in [1, 0, 2, 3, 4]]
        self.assertTrue(any("disagree about who spoke" in line
                            for line in control([g])))

    def test_a_missing_decision_refuses(self):
        g = game()
        g["decision_log"] = g["decision_log"][:-1]
        self.assertTrue(control([g]))


class TestTheSkinControl(unittest.TestCase):
    def test_an_unknown_theme_refuses(self):
        self.assertTrue(any("not a known skin" in line
                            for line in control([game(theme="lantern")])))

    def test_a_language_with_no_claim_rule_refuses_rather_than_reads_zero(self):
        """S16's call, arrived at from the other side. A skin the matcher cannot
        read must not report 0 claims - that is indistinguishable from a table
        that never claimed anything, which is the 0/1290 cabal published once."""
        from games.changeling import roles

        skin = roles.Theme("ja-test", dict(roles.THEME_FOLK.side_names),
                           dict(roles.THEME_FOLK.card_names), lang="ja")
        roles.THEMES["ja-test"] = skin
        try:
            bad = control([game(theme="ja-test")])
        finally:
            del roles.THEMES["ja-test"]
        self.assertTrue(any("no claim rule" in line for line in bad), bad)

    def test_two_skin_words_the_matcher_cannot_separate_refuse(self):
        from games.changeling import roles

        names = dict(roles.THEME_FOLK.card_names)
        names["spotter"] = "Night Werewolf"        # contains another card's word
        skin = roles.Theme("collide", dict(roles.THEME_FOLK.side_names), names)
        roles.THEMES["collide"] = skin
        try:
            bad = control([game(theme="collide")])
        finally:
            del roles.THEMES["collide"]
        self.assertTrue(any("matches the other" in line for line in bad), bad)

    def test_a_card_outside_the_deck_refuses(self):
        g = game()
        g["dealt"]["0"] = "kindred"          # a real card, not in SETUP_5
        self.assertTrue(any("not a card in this deck" in line
                            for line in control([g])))


class TestTheRunControl(unittest.TestCase):
    def test_a_summary_that_counted_a_different_run_refuses(self):
        games = [game()]
        summary = summary_for(games)
        summary["score"]["integrity"]["decisions"] = 99
        self.assertTrue(integrity_control(summary, games))


class TestTheClaimShapes(unittest.TestCase):
    def test_the_deal_shape_reads_the_sentence_this_rung_actually_produces(self):
        for text in ("I went to sleep as the Seer.",
                     "I was Meddler, so I swapped 3 and 4.",
                     "I was dealt the Thief.",
                     "I slept as a Villager.",
                     "I'm seat 0. I went to sleep as the real Seer."):
            with self.subTest(text=text):
                self.assertTrue(_claim_en_dealt(text, "Seer")
                                or _claim_en_dealt(text, "Meddler")
                                or _claim_en_dealt(text, "Thief")
                                or _claim_en_dealt(text, "Villager"))

    def test_it_does_not_read_another_seats_deal_or_a_denial(self):
        for text in ("Seat 3, you went to sleep as Thief, not Seer.",
                     "I was not the Seer.",
                     "Seat 4 was the Seer and I believe them."):
            with self.subTest(text=text):
                self.assertFalse(_claim_en_dealt(text, "Seer"))
                self.assertFalse(_claim_en_dealt(text, "Thief"))

    def test_a_present_claim_is_not_a_deal_claim(self):
        self.assertFalse(_claim_en_dealt("I am the Seer.", "Seer"))
        self.assertEqual(claims_own_role("I am the Seer.", "Seer"), "claim")

    def test_the_deal_rule_has_no_mention_floor(self):
        """`claims_own_role` floors an unruled language at a plain mention;
        `claims_dealt_role` returns nothing, because naming a card is the most
        ordinary sentence at this table and a containment floor would flag most of
        the record."""
        self.assertEqual(claims_own_role("Seat 3 is the Seer.", "Seer", "ja"),
                         "mention")
        self.assertEqual(claims_dealt_role("Seat 3 is the Seer.", "Seer", "ja"), "")


class TestWhatIsCounted(unittest.TestCase):
    def test_the_two_shapes_are_scored_against_different_facts(self):
        claims, scored, blind = claims_of(game())
        self.assertEqual(scored, 5)
        by = {(c.seat, c.shape): c for c in claims}
        self.assertTrue(by[(0, "dealt")].true)          # dealt spotter, said Seer
        self.assertFalse(by[(1, "present")].true)       # dealt pack, said Sleepwalker
        self.assertTrue(by[(4, "present")].true)        # saw bystander after the theft
        self.assertNotIn((2, "dealt"), by)              # spoke about seat 0, not itself

    def test_a_deal_claim_naming_the_card_the_night_showed_it_is_true_not_a_lie(self):
        """The S14 wording call, pinned. Every record on disk was played under a
        self-line that called the seat's post-night belief the card it went to
        sleep as, so a seat naming that card is quoting the referee. Scoring it
        against `dealt` alone reports the referee's own wording as a table of
        liars - measured on S2 as 65 of 74 such claims."""
        g = game(said=["x", "x", "x", "x", "I went to sleep as a Villager."])
        claim = next(c for c in claims_of(g)[0] if c.seat == 4)
        self.assertEqual((claim.shape, claim.card), ("dealt", "bystander"))
        self.assertTrue(claim.true)
        self.assertFalse(claim.names_deal)

    def test_a_claim_naming_the_dawn_card_it_could_not_know_is_marked_lucky(self):
        c = Claim(game=0, seat=4, index=0, shape="present", card="pack",
                  dealt="swapper", belief="bystander", truth="pack", said="")
        self.assertFalse(c.true)
        self.assertTrue(c.lucky)

    def test_the_side_partition_is_what_the_seat_believes_not_what_it_holds(self):
        """Seat 1 holds `swapper` at dawn and believes `pack`. Grading its speech
        by the dawn card would score a wolf's bluff as a villager's lie."""
        claims, _, _ = claims_of(game())
        seat1 = next(c for c in claims if c.seat == 1)
        self.assertTrue(seat1.believes_pack)

    def test_the_fallbacks_lines_are_not_counted_as_speech(self):
        """The random policy wrote them, so they are the control arm's vocabulary
        and not a model's - in the denominator they would move the rate."""
        g = game()
        g["decision_log"][0]["fell_back"] = True
        claims, scored, _ = claims_of(g)
        self.assertEqual(scored, 4)
        self.assertFalse(any(c.seat == 0 for c in claims))

    def test_an_utterance_naming_a_card_in_no_readable_shape_is_the_blind_spot(self):
        _, _, blind = claims_of(game(said=[
            "Whoever took the Seer card should say so.",
            "x", "x", "x", "x"]))
        self.assertEqual(blind, 1)

    def test_the_chance_bar_is_the_decks_arithmetic(self):
        deck = len(deck_names(game()))
        self.assertEqual(deck, 6)
        dealt = Claim(0, 0, 0, "dealt", "spotter", "spotter", "spotter",
                      "spotter", "")
        moved = Claim(0, 4, 0, "present", "pack", "swapper", "bystander",
                      "pack", "")
        self.assertAlmostEqual(chance([dealt], deck), 1 / 6)
        self.assertAlmostEqual(chance([moved], deck), 2 / 6)
        self.assertIsNone(chance([], deck))

    def test_the_corpus_is_what_the_table_saw(self):
        """Records written before 2026-08-27 stored the policy's raw string in
        `utterances` and published a truncated one. The published line is the one a
        model was shown, so it is the one that is read."""
        g = game()
        g["public_events"][0][1] = "Seat 0: I am the Seer"
        g["utterances"][0] = "I am the Seer and here is 400 more characters nobody saw"
        self.assertEqual(speeches(g)[0], (0, "I am the Seer"))


class TestTheRenderedRead(unittest.TestCase):
    def test_it_reports_both_denominators_and_the_fallback_rate(self):
        games = [game()]
        text = "\n".join(report(summary_for(games), games))
        for needle in ("deal claims", "present claims", "chance",
                       "run fallback rate", "LOWER bound", "pre-S14"):
            self.assertIn(needle, text)


class TestCabalsPublishedCountsDidNotMove(unittest.TestCase):
    """`_ADORN` widened the shape S13 and S16 count with. Their figures are in
    `docs/slices.md` and `docs/measurements.md`; if this fails, the widening is a
    re-baseline and the numbers have to be republished, not quietly changed."""

    def test_s13_self_outings_reproduce(self):
        self.assertEqual(outed_own_role_in_public(hunt20c())[:2], (7, 1580))

    def test_s16_false_claims_reproduce(self):
        self.assertEqual(
            claimed_a_role_it_was_not_dealt(hunt20c())[:2], (0, 1580))


class TestAgainstTheRecordItWasWrittenFor(unittest.TestCase):
    def test_the_control_holds_over_the_s2_run(self):
        records_gate.demand(S2, f"{S2}.jsonl")
        summary, games = load(S2)
        self.assertEqual(len(games), 200)
        self.assertEqual(control(games) + integrity_control(summary, games), [])


if __name__ == "__main__":
    unittest.main()
