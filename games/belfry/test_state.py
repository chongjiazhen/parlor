"""The deal, and the two discretionary choices taken at setup.

The properties here are the ones a reader of a run's numbers has to be able to
assume: the published proportions were honoured, the seat that is wrong about
itself believes something nobody can check it against, and the demon's claimable
roles are roles nobody holds.
"""

from __future__ import annotations

import random
import unittest

from games.belfry.roles import (COMPACT, DISTRIBUTION, FULL, ROLES, SCRIPTS,
                                Align, Team)
from games.belfry.state import BadSetup, deal


def dealt(n: int, seed: int, script=FULL):
    return deal(n, script, random.Random(seed))


class TestProportions(unittest.TestCase):
    def test_every_table_size_deals_its_published_counts(self):
        for n, (town, out, minion, demon) in DISTRIBUTION.items():
            for seed in range(5):
                grim = dealt(n, seed)
                counts = {team: sum(1 for s in grim.seats
                                    if s.role.team is team) for team in Team}
                if grim.find("warp") is None:
                    self.assertEqual(counts[Team.TOWNSFOLK], town, (n, seed))
                    self.assertEqual(counts[Team.OUTSIDER], out, (n, seed))
                else:
                    # The setup-modifying minion trades townsfolk for outsiders,
                    # and the total is what has to hold.
                    self.assertEqual(counts[Team.TOWNSFOLK]
                                     + counts[Team.OUTSIDER], town + out)
                    self.assertGreater(counts[Team.OUTSIDER], out)
                self.assertEqual(counts[Team.MINION], minion, (n, seed))
                self.assertEqual(counts[Team.DEMON], demon, (n, seed))
                self.assertEqual(len(grim.seats), n)

    def test_no_role_is_dealt_twice(self):
        for seed in range(30):
            grim = dealt(9, seed)
            keys = [s.role.key for s in grim.seats]
            self.assertEqual(len(keys), len(set(keys)))

    def test_a_table_with_no_published_proportions_is_refused(self):
        with self.assertRaises(BadSetup):
            dealt(4, 0)
        with self.assertRaises(BadSetup):
            dealt(13, 0)

    def test_a_script_too_thin_for_the_table_is_refused_at_the_door(self):
        with self.assertRaises(BadSetup):
            deal(12, COMPACT, random.Random(0))

    def test_every_published_table_size_is_dealable_by_some_script(self):
        """A size this rung publishes proportions for must have a script.

        This is what stops the full script being reclassified out of `games/`
        on the argument that the compact one already reaches every mechanic.
        It does, up to ten seats; above that the deluded seat has no spare
        townsfolk role left and `deal` refuses, so eleven and twelve are FULL
        or they are nothing - and gate #1's own every-size sweep covers those
        two sizes on the full script alone. Delete `FULL` and this goes red
        naming the sizes that lost their script, which an argument in a queue
        row cannot do.
        """
        for n in DISTRIBUTION:
            dealt_by = []
            for script in SCRIPTS.values():
                try:
                    deal(n, script, random.Random(0))
                except BadSetup:
                    continue
                dealt_by.append(script.name)
            self.assertTrue(dealt_by, f"{n} seats has no script that deals it")


class TestTheDeludedSeat(unittest.TestCase):
    def test_it_believes_a_role_nobody_holds(self):
        found = 0
        for seed in range(120):
            grim = dealt(9, seed)
            sot = grim.find("sot")
            if sot is None:
                continue
            found += 1
            believed = grim.seat(sot).believes
            self.assertIs(believed.team, Team.TOWNSFOLK)
            self.assertIsNone(grim.find(believed.key))
        self.assertGreater(found, 0, "no deal in range put it in play")

    def test_its_ability_is_off_and_nobody_else_s_is(self):
        for seed in range(60):
            grim = dealt(9, seed)
            sot = grim.find("sot")
            for s in grim.seats:
                self.assertEqual(grim.droisoned(s.index), s.index == sot)


class TestTheDemonsClaims(unittest.TestCase):
    def test_the_bluffs_are_good_roles_that_are_not_in_play(self):
        for seed in range(40):
            grim = dealt(9, seed)
            for key in grim.bluffs:
                self.assertIs(ROLES[key].align, Align.GOOD, key)
                self.assertIsNone(grim.find(key), key)

    def test_there_are_three_of_them_on_a_script_with_room(self):
        for seed in range(20):
            self.assertEqual(len(dealt(9, seed).bluffs), 3)


class TestRegistration(unittest.TestCase):
    def test_the_ambiguous_good_seat_holds_one_answer_all_game(self):
        """Per-query re-rolling is a different game: a seat that reads evil on
        Tuesday and good on Wednesday is noise nobody can reason against."""
        for seed in range(120):
            grim = dealt(9, seed, FULL)
            hermit = grim.find("hermit")
            if hermit is None:
                continue
            first = grim.registers_evil(hermit)
            for _ in range(5):
                self.assertEqual(grim.registers_evil(hermit), first)
            if grim.hermit_evil:
                self.assertIs(ROLES[grim.hermit_as].align, Align.EVIL)
                self.assertIs(grim.registers_as(hermit), ROLES[grim.hermit_as])

    def test_the_ambiguous_evil_seat_can_read_as_an_outsider(self):
        """The source lets it register as a townsfolk OR an outsider. Until
        2026-09-02 the pool held townsfolk only. Nine seats on the full script
        always seat outsiders, so the pool is never empty of them."""
        seen = set()
        for seed in range(300):
            grim = dealt(9, seed, FULL)
            if grim.find("mimic") is None or not grim.mimic_good:
                continue
            seen.add(ROLES[grim.mimic_as].team)
        self.assertIn(Team.OUTSIDER, seen)
        self.assertIn(Team.TOWNSFOLK, seen)

    def test_the_ambiguous_evil_seat_can_read_as_a_townsfolk(self):
        seen = set()
        for seed in range(200):
            grim = dealt(9, seed, FULL)
            mimic = grim.find("mimic")
            if mimic is None:
                continue
            seen.add(grim.registers_evil(mimic))
            if grim.mimic_good:
                self.assertIn(grim.registers_as(mimic).team,
                              (Team.TOWNSFOLK, Team.OUTSIDER))
        self.assertEqual(seen, {True, False},
                         "the discretionary coin never came up both ways")

    def test_the_false_positive_is_a_good_seat(self):
        for seed in range(60):
            grim = dealt(9, seed)
            if grim.herring is None:
                self.assertIsNone(grim.find_believer("diviner"))
                continue
            self.assertIs(grim.seat(grim.herring).align, Align.GOOD)
            self.assertTrue(grim.registers_demon(
                grim.herring, for_seat=grim.find_believer("diviner")))
            if grim.role_of(grim.herring).key != "hermit":
                # It reads as the demon to ONE seat. The ambiguous outsider is the
                # exception and reads that way to everybody, which is its own rule
                # rather than this one.
                self.assertFalse(grim.registers_demon(grim.herring))


class TestSeating(unittest.TestCase):
    def test_neighbours_are_read_past_the_dead(self):
        grim = dealt(7, 1)
        for seat in (1, 2, 3):
            grim.seat(seat).alive = False
        self.assertEqual(grim.living_neighbours(0), [4, 6])

    def test_the_seating_circle_is_what_the_pair_count_reads(self):
        grim = dealt(7, 1)
        pairs = sum(1 for i in range(grim.n)
                    if grim.registers_evil(i)
                    and grim.registers_evil((i + 1) % grim.n))
        self.assertEqual(grim.evil_pairs(), pairs)

    def test_the_pair_count_ignores_who_is_alive(self):
        grim = dealt(9, 2)
        before = grim.evil_pairs()
        for seat in (0, 1, 2):
            grim.seat(seat).alive = False
        self.assertEqual(grim.evil_pairs(), before)


class TestDeterminism(unittest.TestCase):
    def test_the_same_seed_deals_the_same_table(self):
        a, b = dealt(9, 77), dealt(9, 77)
        self.assertEqual([s.role.key for s in a.seats],
                         [s.role.key for s in b.seats])
        self.assertEqual(a.bluffs, b.bluffs)
        self.assertEqual(a.herring, b.herring)
        self.assertEqual(a.log, b.log)


if __name__ == "__main__":
    unittest.main()


class TestInheritedRoleLookup(unittest.TestCase):
    """Inheritance is the one thing that puts two rows on one role key.

    ``_demon_died`` writes ``fiend`` onto the successor and leaves the dead
    demon's row holding it, so ``find`` has to say which of the two ACTS. The
    living one does: a first-match search returns the corpse, the night walk
    skips the demon's step on the ``alive`` guard, and the living demon never
    kills again for the rest of the game.
    """

    def _inherited(self, dead: int):
        """Seats 0 and 1 both key ``fiend``; ``dead`` is the one that died."""
        grim = dealt(5, 4, COMPACT)
        fiend = ROLES["fiend"]
        for seat in (0, 1):
            grim.seat(seat).role = fiend
            grim.seat(seat).believes = fiend
        grim.seat(dead).alive = False
        return grim

    def test_a_living_holder_wins_over_a_dead_one_at_a_lower_seat(self):
        grim = self._inherited(dead=0)
        self.assertEqual(grim.find("fiend"), 1)
        self.assertEqual(grim.find_believer("fiend"), 1)

    def test_the_living_holder_is_found_when_it_sits_first(self):
        grim = self._inherited(dead=1)
        self.assertEqual(grim.find("fiend"), 0)

    def test_a_role_whose_only_holder_is_dead_is_still_found(self):
        grim = dealt(5, 4, COMPACT)
        seat = grim.find("fiend")
        grim.seat(seat).alive = False
        self.assertEqual(grim.find("fiend"), seat)

    def test_the_living_demon_agrees_with_the_role_search(self):
        grim = self._inherited(dead=0)
        self.assertEqual(grim.find("fiend"), grim.demon_seat())
