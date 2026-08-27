"""The stratum census, and the one claim it exists to support.

Cheap on purpose - it resolves nights, so the whole file runs without a model and
in well under a second at these counts.
"""

import unittest

from eval import strata
from games.changeling.roles import SETUP_5


class TestCensus(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = strata.census(SETUP_5, nights=600, seed=11)

    def test_every_seat_night_lands_in_exactly_one_stratum_under_each_rule(self):
        self.assertEqual(sum(self.c["told"].values()), self.c["seats"])
        self.assertEqual(sum(self.c["dealt"].values()), self.c["seats"])

    def test_the_two_rules_move_seats_only_between_identity_and_none(self):
        """The S10 change is one move and nothing else. A difference in
        ``positional`` or ``false`` would mean it touched a card it had no business
        touching."""
        for cls in ("positional", "false"):
            self.assertEqual(self.c["told"][cls], self.c["dealt"][cls], cls)
        moved = self.c["dealt"]["identity"] - self.c["told"]["identity"]
        self.assertGreater(moved, 0, "S10 relabelled nothing - the census is lying")
        self.assertEqual(self.c["told"]["none"] - self.c["dealt"]["none"], moved)

    def test_the_move_is_exactly_the_MEET_seats_that_met_nobody(self):
        """Which is the whole mechanism: a MEET card's reveal is conditional on
        another seat's deal, and no other card can be told nothing."""
        moved = self.c["dealt"]["identity"] - self.c["told"]["identity"]
        self.assertEqual(moved, self.c["meet_without_fellow"])

    def test_the_blind_stratum_grows_and_the_report_says_by_how_much(self):
        self.assertGreater(self.c["told_nothing_but_labelled"], 0)
        self.assertLessEqual(self.c["told_nothing_but_labelled"],
                             self.c["blind_villagers"])
        text = "\n".join(strata.report("SETUP_5", self.c))
        self.assertIn("MISLABELLED pre-S10", text)
        self.assertIn("TOLD (S10)", text)

    def test_the_census_is_seeded(self):
        """A number nobody can reproduce is not a measurement."""
        again = strata.census(SETUP_5, nights=600, seed=11)
        self.assertEqual(again["told"], self.c["told"])
        other = strata.census(SETUP_5, nights=600, seed=99)
        self.assertNotEqual(other["told"], self.c["told"])

    def test_main_runs(self):
        self.assertEqual(strata.main(["--nights", "50", "--deck", "SETUP_5"]), 0)


if __name__ == "__main__":
    unittest.main()
