"""The deal census, tested against two blocks whose answer is already on disk.

The row this answers: every power section in the tree computes its half-width
from an eligibility rate measured on a block it is not going to play. The partner
criterion assumed ~198 partner-eligible votes at 200 games, measured on
seeds 5000..5199, and its own 17000-block dealt 168 - a real 0.9 points of
half-width, found only after the card was spent.

The census must be validated against reality rather than against itself, so the
two cases below are the counts that fall out of `cl-partner-random.json.jsonl`
and `cl-mixed-pack.json.jsonl` - records made by PLAYING those deals. A census
that reproduces them without playing is measuring the deal.
"""

from __future__ import annotations

import unittest

from eval.deal_census import census


class TestAgainstBlocksAlreadyPlayed(unittest.TestCase):
    """Positive control: no model, no votes, and the same number comes back."""

    def test_the_partner_block_deals_168_eligible_over_200(self):
        """`cl-partner-random.json.jsonl`, game indices 0..199."""
        self.assertEqual(census(200, seed=17000).eligible, 168)

    def test_the_block_the_criterion_reasoned_from_deals_198(self):
        """`cl-mixed-pack.json.jsonl`, and the 198/200 §Power quoted."""
        self.assertEqual(census(200, seed=5000).eligible, 198)


class TestTheBlindStratumAgreesWithAPlayedRecord(unittest.TestCase):
    """`cl-partner-random.json` scored 1252 blind votes over its 1000 deals.

    Three filters have to match `run_changeling`'s exactly or this misses:
    unwinnable games score nothing, pack holders are not villager votes, and
    blind is `knowledge_class == "none"`. An off-by-one in any of them shows up
    here as a wrong total rather than as a plausible one.
    """

    def test_the_blind_census_reproduces_the_recorded_1252(self):
        self.assertEqual(census(1000, seed=17000, statistic="blind").eligible,
                         1252)


class TestTheInstrumentDiscriminates(unittest.TestCase):
    """Negative control: a census that answers the same for any block is a
    constant wearing a measurement's name."""

    def test_two_blocks_do_not_agree(self):
        self.assertNotEqual(census(200, seed=17000).eligible,
                            census(200, seed=5000).eligible)

    def test_the_same_block_twice_agrees(self):
        self.assertEqual(census(60, seed=17000).eligible,
                         census(60, seed=17000).eligible)


class TestTheShapeAPowerSectionNeeds(unittest.TestCase):

    def test_games_and_per_deal_counts_are_reported(self):
        c = census(20, seed=17000)
        self.assertEqual(c.games, 20)
        self.assertEqual(len(c.per_deal), 20)
        self.assertEqual(sum(c.per_deal), c.eligible)

    def test_a_prefix_of_a_block_is_a_prefix_of_its_census(self):
        """Deals are seeded per index, so the first 20 of 200 are the same 20."""
        self.assertEqual(census(20, seed=17000).per_deal,
                         census(200, seed=17000).per_deal[:20])


if __name__ == "__main__":
    unittest.main()
