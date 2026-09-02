"""The night-coherence scorer, on synthetic tellings.

The unit it grades is a PAIR: a false gauge telling whose previous telling to the
same seat was also false and made over the same living neighbours. Everything
else is out of the denominator, and each exclusion is a guard here because the
scorer that forgot one would still print a number.
"""

from __future__ import annotations

import unittest

from eval.belfry_night_verdict import (
    CHANCE,
    coherence_pairs,
    coherence_read,
    verdict,
)


def told(seat, night, neighbours, count, truthful, source="random"):
    return {"seat": seat, "night": night, "neighbours": list(neighbours),
            "count": count, "truthful": truthful, "source": source}


class TestPairing(unittest.TestCase):
    def test_two_false_tellings_over_the_same_neighbours_are_one_pair(self):
        rows = [told(3, 1, (2, 4), 1, False), told(3, 2, (2, 4), 1, False)]
        pairs = coherence_pairs(rows)
        self.assertEqual(len(pairs), 1)
        self.assertTrue(pairs[0].coherent)

    def test_a_different_count_is_an_incoherent_pair(self):
        rows = [told(3, 1, (2, 4), 1, False), told(3, 2, (2, 4), 0, False)]
        self.assertFalse(coherence_pairs(rows)[0].coherent)

    def test_a_truthful_prior_is_not_a_pair(self):
        rows = [told(3, 1, (2, 4), 2, True), told(3, 2, (2, 4), 1, False)]
        self.assertEqual(coherence_pairs(rows), [])

    def test_changed_neighbours_are_not_a_pair(self):
        rows = [told(3, 1, (2, 4), 1, False), told(3, 2, (1, 4), 1, False)]
        self.assertEqual(coherence_pairs(rows), [])

    def test_a_truthful_current_telling_is_not_a_pair(self):
        rows = [told(3, 1, (2, 4), 1, False), told(3, 2, (2, 4), 2, True)]
        self.assertEqual(coherence_pairs(rows), [])

    def test_seats_do_not_pair_with_each_other(self):
        rows = [told(3, 1, (2, 4), 1, False), told(5, 2, (2, 4), 1, False)]
        self.assertEqual(coherence_pairs(rows), [])

    def test_only_consecutive_tellings_pair(self):
        rows = [told(3, 1, (2, 4), 1, False), told(3, 2, (2, 4), 2, True),
                told(3, 3, (2, 4), 1, False)]
        self.assertEqual(coherence_pairs(rows), [])

    def test_a_fallback_telling_is_the_seeded_menu_and_not_a_pair(self):
        rows = [told(3, 1, (2, 4), 1, False),
                told(3, 2, (2, 4), 1, False, source="fallback")]
        self.assertEqual(coherence_pairs(rows), [])

    def test_a_fallback_prior_still_counts_as_what_the_seat_holds(self):
        rows = [told(3, 1, (2, 4), 1, False, source="fallback"),
                told(3, 2, (2, 4), 1, False, source="model")]
        self.assertEqual(len(coherence_pairs(rows)), 1)

    def test_order_on_disk_does_not_matter(self):
        rows = [told(3, 2, (2, 4), 1, False), told(3, 1, (2, 4), 1, False)]
        self.assertEqual(len(coherence_pairs(rows)), 1)


def game(rows, index=0):
    return {"index": index, "gauge_told": rows, "decisions": 10,
            "fallbacks": 0, "error": None}


class TestRead(unittest.TestCase):
    def test_chance_is_exactly_one_half(self):
        self.assertEqual(CHANCE, 0.5)

    def test_the_read_counts_pairs_across_games_and_floors_by_game(self):
        games = [game([told(3, 1, (2, 4), 1, False),
                       told(3, 2, (2, 4), 1, False)], i) for i in range(30)]
        read = coherence_read(games)
        self.assertEqual((read.coherent, read.pairs), (30, 30))
        self.assertIsNotNone(read.wilson)
        self.assertIsNotNone(read.bootstrap)

    def test_an_empty_stratum_has_no_floors(self):
        read = coherence_read([game([told(3, 1, (2, 4), 2, True)])])
        self.assertEqual(read.pairs, 0)
        self.assertIsNone(read.wilson)
        self.assertIsNone(read.bootstrap)

    def test_a_row_without_the_field_is_refused(self):
        with self.assertRaises(ValueError):
            coherence_read([{"index": 0, "decisions": 1, "fallbacks": 0}])


class TestVerdict(unittest.TestCase):
    def _games(self, coherent: int, total: int):
        out = []
        for i in range(total):
            c = 1 if i < coherent else 0
            out.append(game([told(3, 1, (2, 4), 1, False),
                             told(3, 2, (2, 4), c, False)], i))
        return out

    def test_both_floors_over_chance_is_coherent(self):
        control = coherence_read(self._games(50, 100))
        model = coherence_read(self._games(90, 100))
        self.assertEqual(verdict(control, model), "COHERENT")

    def test_one_floor_under_chance_is_not_shown(self):
        control = coherence_read(self._games(50, 100))
        model = coherence_read(self._games(56, 100))
        self.assertEqual(verdict(control, model), "NOT SHOWN")

    def test_a_control_that_does_not_sit_at_chance_voids_the_instrument(self):
        control = coherence_read(self._games(80, 100))
        model = coherence_read(self._games(90, 100))
        self.assertEqual(verdict(control, model), "INSTRUMENT SUSPECT")

    def test_an_empty_model_stratum_is_no_verdict(self):
        control = coherence_read(self._games(50, 100))
        model = coherence_read([game([told(3, 1, (2, 4), 2, True)])])
        self.assertEqual(verdict(control, model), "NO VERDICT")


if __name__ == "__main__":
    unittest.main()
