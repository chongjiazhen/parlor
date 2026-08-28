"""What a seat is told, and what it is told when its ability is off.

These test the content functions directly, on a rigged board, because the property
they carry is a property of the SENTENCE and not of the game around it: a true
reveal has to be true, a false one has to be false, and the false one has to miss
both what the seat holds and what it registers as. The last of those is a gate #1
requirement - a lie that landed on the truth is a fact a seat never earned - and it
is unreachable from a test that only reads the audit's verdict.
"""

from __future__ import annotations

import random
import unittest

from games.belfry import night as nightinfo
from games.belfry.roles import FULL, ROLES, Team
from games.belfry.state import Grimoire, Seat


def board(keys: list[str], poisoned: tuple[int, ...] = ()) -> Grimoire:
    seats = [Seat(index=i, role=ROLES[k], dealt=ROLES[k], believes=ROLES[k])
             for i, k in enumerate(keys)]
    grim = Grimoire(seats=seats, script=FULL)
    for seat in poisoned:
        grim.seat(seat).poisoned = True
    return grim


KEYS = ["fiend", "venom", "gauge", "warder", "bulwark", "witness", "tally"]


class TestPointingReveals(unittest.TestCase):
    def test_a_healthy_reveal_names_two_seats_one_of_which_holds_the_role(self):
        grim = board(KEYS)
        for seed in range(20):
            r = nightinfo.witness(grim, random.Random(seed), 5, 1)
            self.assertTrue(r.truthful)
            self.assertEqual(len(r.seats), 2)
            held = [s for s in r.seats if grim.registers_as(s).key == r.role]
            self.assertEqual(len(held), 1, r.text)

    def test_it_never_points_at_the_seat_reading_it(self):
        grim = board(KEYS)
        for seed in range(30):
            r = nightinfo.witness(grim, random.Random(seed), 5, 1)
            self.assertNotIn(5, r.seats)

    def test_the_minion_finder_names_a_minion(self):
        grim = board(KEYS)
        r = nightinfo.tracker(grim, random.Random(0), 5, 1)
        self.assertIs(ROLES[r.role].team, Team.MINION)

    def test_a_question_with_no_answer_says_so(self):
        grim = board(KEYS)
        r = nightinfo.archivist(grim, random.Random(0), 5, 1)
        self.assertTrue(r.truthful)
        self.assertIn("No seat", r.text)

    def test_a_poisoned_reveal_names_a_role_neither_seat_holds(self):
        grim = board(KEYS, poisoned=(5,))
        for seed in range(30):
            r = nightinfo.witness(grim, random.Random(seed), 5, 1)
            self.assertFalse(r.truthful)
            for seat in r.seats:
                self.assertNotEqual(grim.role_of(seat).key, r.role)
                self.assertNotEqual(grim.registers_as(seat).key, r.role)


class TestCountingReveals(unittest.TestCase):
    def test_the_neighbour_count_is_the_evil_neighbours(self):
        grim = board(["fiend", "gauge", "venom", "warder", "bulwark"])
        r = nightinfo.gauge(grim, random.Random(0), 1, 1)
        self.assertTrue(r.truthful)
        self.assertTrue(r.text.startswith("2 "), r.text)

    def test_a_poisoned_neighbour_count_is_a_different_number(self):
        grim = board(["fiend", "gauge", "venom", "warder", "bulwark"],
                     poisoned=(1,))
        for seed in range(20):
            r = nightinfo.gauge(grim, random.Random(seed), 1, 1)
            self.assertFalse(r.truthful)
            self.assertFalse(r.text.startswith("2 "), r.text)

    def test_the_pair_count_matches_the_board(self):
        grim = board(KEYS)
        r = nightinfo.tally(grim, random.Random(0), 6, 1)
        self.assertTrue(r.text.startswith(f"{grim.evil_pairs()} "))

    def test_a_poisoned_pair_count_is_a_different_number(self):
        grim = board(KEYS, poisoned=(6,))
        for seed in range(20):
            r = nightinfo.tally(grim, random.Random(seed), 6, 1)
            self.assertFalse(r.text.startswith(f"{grim.evil_pairs()} "))


class TestTheDemonHunt(unittest.TestCase):
    def test_it_finds_the_demon(self):
        grim = board(KEYS)
        r = nightinfo.divine(grim, random.Random(0), 2, 1, (0, 3))
        self.assertIn("yes", r.text)
        self.assertTrue(r.truthful)

    def test_it_reports_nothing_when_neither_seat_is_the_demon(self):
        grim = board(KEYS)
        r = nightinfo.divine(grim, random.Random(0), 2, 1, (3, 4))
        self.assertIn("neither", r.text)

    def test_the_false_positive_reads_as_the_demon_to_its_own_hunter(self):
        grim = board(KEYS)
        grim.herring = 4
        r = nightinfo.divine(grim, random.Random(0), 2, 1, (3, 4))
        self.assertIn("yes", r.text)
        self.assertTrue(r.truthful, "it is a true answer to the question asked")

    def test_a_poisoned_hunt_is_inverted(self):
        grim = board(KEYS, poisoned=(2,))
        r = nightinfo.divine(grim, random.Random(0), 2, 1, (0, 3))
        self.assertIn("neither", r.text)
        self.assertFalse(r.truthful)


class TestNamingOneSeat(unittest.TestCase):
    FRAME = "Seat {seat} is the {role}."

    def test_a_healthy_naming_is_the_seat_s_own_role(self):
        grim = board(KEYS)
        r = nightinfo.name_role(grim, random.Random(0), 2, 1, 0, self.FRAME)
        self.assertEqual(r.role, "fiend")
        self.assertTrue(r.truthful)
        self.assertEqual(r.seats, (0,))

    def test_a_poisoned_naming_misses_the_role_and_the_registration(self):
        grim = board(["fiend", "hermit", "gauge", "warder", "bulwark"],
                     poisoned=(2,))
        grim.hermit_evil, grim.hermit_as = True, "venom"
        for seed in range(30):
            r = nightinfo.name_role(grim, random.Random(seed), 2, 1, 1,
                                    self.FRAME)
            self.assertNotIn(r.role, {"hermit", "venom"})
            self.assertFalse(r.truthful)

    def test_it_names_what_a_seat_registers_as(self):
        grim = board(["fiend", "hermit", "gauge", "warder", "bulwark"])
        grim.hermit_evil, grim.hermit_as = True, "venom"
        r = nightinfo.name_role(grim, random.Random(0), 2, 1, 1, self.FRAME)
        self.assertEqual(r.role, "venom")

    def test_registering_as_something_else_confers_no_entitlement(self):
        """A reveal can be a true answer to the question asked while naming a role
        the seat does not hold. Entitlement follows what a seat IS, so the
        ambiguous seat keeps its secret from the very seat it fooled."""
        grim = board(["fiend", "hermit", "gauge", "warder", "bulwark"])
        grim.hermit_evil, grim.hermit_as = True, "venom"
        r = nightinfo.name_role(grim, random.Random(0), 2, 1, 1, self.FRAME)
        self.assertIsNone(r.entitles(grim))


class TestTheBoardWatcher(unittest.TestCase):
    def test_it_reads_what_every_seat_is(self):
        grim = board(["fiend", "hermit", "gauge", "warder", "bulwark"])
        grim.hermit_evil, grim.hermit_as = True, "venom"
        reveals = nightinfo.watch_the_board(grim, random.Random(0), 2, 1)
        self.assertEqual([r.role for r in reveals],
                         [s.role.key for s in grim.seats])
        for r in reveals:
            self.assertEqual(r.entitles(grim), r.seats[0])

    def test_poisoned_it_reads_a_derangement(self):
        grim = board(KEYS, poisoned=(2,))
        for seed in range(20):
            reveals = nightinfo.watch_the_board(grim, random.Random(seed), 2, 1)
            self.assertEqual(len(reveals), grim.n)
            for r in reveals:
                seat = r.seats[0]
                self.assertNotEqual(r.role, grim.role_of(seat).key)
                self.assertIsNone(r.entitles(grim))


if __name__ == "__main__":
    unittest.main()
