"""The script and the proportions - the two tables everything else derives from.

These are cheap tests over data, and they are here because the failures they catch
are silent ones: a role with no night position never wakes, a duplicate display
name makes two seats' secrets the same string, and a script that cannot fill a
table only says so when somebody deals one.
"""

from __future__ import annotations

import unittest

from games.belfry.roles import (ALL_ROLES, COMPACT, DISTRIBUTION, FIRST_NIGHT,
                                FULL, OTHER_NIGHT, ROLES, SCRIPTS, Align, Team)


class TestScript(unittest.TestCase):
    def test_role_keys_are_unique(self):
        keys = [r.key for r in ALL_ROLES]
        self.assertEqual(len(keys), len(set(keys)))

    def test_display_names_are_unique(self):
        """A seat's secret is the string "seat N is the X". Two roles sharing a
        display name would make two seats' secrets indistinguishable, and the audit
        matches strings - so it would report a leak on a true statement about the
        other one. The invariant's remedy for a collision is a rename; this is what
        finds one."""
        names = [r.display for r in ALL_ROLES]
        self.assertEqual(len(names), len(set(names)))

    def test_every_role_has_ability_text(self):
        for role in ALL_ROLES:
            self.assertTrue(role.power.strip(), role.key)

    def test_ability_text_names_no_other_role(self):
        """The script is one string sent to every seat. A clause that named another
        role would be an association in a payload that is meant to carry none."""
        for role in ALL_ROLES:
            for other in ALL_ROLES:
                if other.key != role.key:
                    self.assertNotIn(other.display, role.power,
                                     f"{role.key} names {other.key}")

    def test_the_compact_script_can_fill_every_table_it_claims(self):
        for n in (5, 6, 7, 8, 9):
            town, out, minion, demon = DISTRIBUTION[n]
            self.assertGreaterEqual(len(COMPACT.by_team(Team.TOWNSFOLK)),
                                    town + 1, n)   # +1 for the spare belief
            self.assertGreaterEqual(len(COMPACT.by_team(Team.OUTSIDER)), out, n)
            self.assertGreaterEqual(len(COMPACT.by_team(Team.MINION)), minion, n)
            self.assertGreaterEqual(len(COMPACT.by_team(Team.DEMON)), demon, n)

    def test_the_full_script_can_fill_every_table(self):
        for n, (town, out, minion, demon) in DISTRIBUTION.items():
            self.assertGreaterEqual(len(FULL.by_team(Team.TOWNSFOLK)), town, n)
            self.assertGreaterEqual(len(FULL.by_team(Team.OUTSIDER)), out, n)
            self.assertGreaterEqual(len(FULL.by_team(Team.MINION)), minion, n)
            self.assertGreaterEqual(len(FULL.by_team(Team.DEMON)), demon, n)

    def test_every_script_is_a_subset_of_the_roles(self):
        for script in SCRIPTS.values():
            for role in script.roles:
                self.assertIs(ROLES[role.key], role, script.name)


class TestNightOrder(unittest.TestCase):
    def test_positions_are_unique_within_a_night(self):
        for order in (FIRST_NIGHT, OTHER_NIGHT):
            keys = [r.key for r in order]
            self.assertEqual(len(keys), len(set(keys)))

    def test_the_poisoner_acts_before_anything_it_could_switch_off(self):
        """The whole point of the role is that its victim's step reads a board it
        has already changed. If it ever moved later in the order, every information
        role would answer from the truth and the role would do nothing."""
        for order in (FIRST_NIGHT, OTHER_NIGHT):
            keys = [r.key for r in order]
            if "venom" in keys:
                self.assertEqual(keys[0], "venom")

    def test_protection_is_resolved_before_the_kill(self):
        keys = [r.key for r in OTHER_NIGHT]
        self.assertLess(keys.index("warder"), keys.index("fiend"))

    def test_the_demon_does_not_kill_on_the_first_night(self):
        self.assertNotIn("fiend", [r.key for r in FIRST_NIGHT])

    def test_the_undertaking_role_does_not_act_on_the_first_night(self):
        """There has been no execution to learn about."""
        self.assertNotIn("mortician", [r.key for r in FIRST_NIGHT])

    def test_the_triggered_role_holds_no_position(self):
        for order in (FIRST_NIGHT, OTHER_NIGHT):
            self.assertNotIn("oracle", [r.key for r in order])


class TestAlignment(unittest.TestCase):
    def test_the_two_good_teams_and_the_two_evil_ones(self):
        self.assertIs(ROLES["witness"].align, Align.GOOD)
        self.assertIs(ROLES["pilgrim"].align, Align.GOOD)
        self.assertIs(ROLES["venom"].align, Align.EVIL)
        self.assertIs(ROLES["fiend"].align, Align.EVIL)

    def test_there_is_exactly_one_demon_in_every_published_proportion(self):
        for n, (_, _, _, demon) in DISTRIBUTION.items():
            self.assertEqual(demon, 1, n)


if __name__ == "__main__":
    unittest.main()
