"""The night-coherence scorer, on synthetic tellings.

The unit it grades is a PAIR: a false gauge telling whose previous telling to the
same seat was also false and made over the same living neighbours. Everything
else is out of the denominator, and each exclusion is a guard here because the
scorer that forgot one would still print a number.
"""

from __future__ import annotations

import unittest

from eval.belfry_night_verdict import (
    WITHHELD_COHERENT, WITHHELD_PAIRS, recall_call, supplied_call,
    ARMS,
    CHANCE,
    SUPPLIED_COHERENT,
    SUPPLIED_PAIRS,
    _recipe_voids,
    coherence_pairs,
    coherence_read,
    unaided_call,
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


class TestCriterionBinding(unittest.TestCase):
    """Two criteria, one instrument. The supplied-memory record was taken before
    the withholding flag existed, so its summary has no such key at all; a
    binding that read the absent key as a mismatch would void a published read
    for a setting that could not have been on."""

    def _summary(self, **args):
        base = dict(games=1000, arm="random", seats=9, script="compact",
                    backend=None, rounds=1, seed=12000, adjudicator="model",
                    adjudicator_model="qwen36-35b-a3b-iq3",
                    adjudicator_night=True, adjudicator_steer=False)
        base.update(args)
        return {"args": base}

    def _flag_voids(self, arm, summary):
        voids = _recipe_voids(summary, [], arm["model_args"], "model", arm)
        return [v for v in voids if "adjudicator_night_no_prior" in v]

    def test_the_supplied_arm_reads_a_record_without_the_flag_key(self):
        self.assertEqual(self._flag_voids(ARMS["supplied"], self._summary()), [])

    def test_the_supplied_arm_refuses_a_record_that_withheld_prior(self):
        voids = self._flag_voids(ARMS["supplied"],
                                 self._summary(adjudicator_night_no_prior=True))
        self.assertEqual(len(voids), 1)

    def test_the_withheld_arm_refuses_prior_supplied_or_unstated(self):
        arm = ARMS["withheld"]
        for summary in (self._summary(seed=13000),
                        self._summary(seed=13000, adjudicator_night_no_prior=False)):
            self.assertEqual(len(self._flag_voids(arm, summary)), 1)
        self.assertEqual(self._flag_voids(
            arm, self._summary(seed=13000, adjudicator_night_no_prior=True)), [])

    def test_the_withheld_arm_binds_its_own_seeds_and_paths(self):
        arm = ARMS["withheld"]
        self.assertEqual((arm["first_seed"], arm["last_seed"]), (13000, 13999))
        self.assertEqual(arm["model_args"]["seed"], 13000)
        self.assertEqual(arm["control_args"]["seed"], 13000)
        for path in (arm["control"], arm["model"]):
            self.assertIn("noprior", path)
        self.assertNotEqual(arm["doc"], ARMS["supplied"]["doc"])

    def test_the_supplied_arm_is_the_published_one(self):
        arm = ARMS["supplied"]
        self.assertEqual((arm["first_seed"], arm["last_seed"]), (12000, 12999))
        self.assertEqual(arm["doc"], "docs/belfry-night-coherence-criterion.md")


class TestUnaidedCall(unittest.TestCase):
    """The withheld arm's second, pre-committed line: is it below the read that
    had `prior` in view? Graded on interval separation against the published
    152/163, never on a point estimate."""

    def _read(self, coherent, total):
        return coherence_read([game([told(3, 1, (2, 4), 1, False),
                                     told(3, 2, (2, 4), 1 if i < coherent else 0,
                                          False)], i) for i in range(total)])

    def test_the_comparison_is_the_published_read(self):
        self.assertEqual((SUPPLIED_COHERENT, SUPPLIED_PAIRS), (152, 163))

    def test_well_below_the_supplied_interval_needs_memory(self):
        self.assertEqual(unaided_call(self._read(100, 160)), "NEEDS MEMORY")

    def test_overlapping_the_supplied_interval_holds_unaided(self):
        self.assertEqual(unaided_call(self._read(150, 160)), "HOLDS UNAIDED")

    def test_no_pairs_is_no_call(self):
        self.assertIsNone(unaided_call(coherence_read(
            [game([told(3, 1, (2, 4), 2, True)])])))


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


class TestTranscriptArm(unittest.TestCase):
    """The session-memory arm: prior withheld, the referee's own transcript
    supplied. Bound to its own seeds, paths and flags; read against both
    published arms on intervals."""

    def _summary(self, **args):
        base = dict(games=1000, arm="random", seats=9, script="compact",
                    backend=None, rounds=1, seed=15000, adjudicator="model",
                    adjudicator_model="qwen36-35b-a3b-iq3",
                    adjudicator_night=True, adjudicator_steer=False,
                    adjudicator_night_no_prior=True)
        base.update(args)
        return {"args": base}

    def _flag_voids(self, arm, summary):
        voids = _recipe_voids(summary, [], arm["model_args"], "model", arm)
        return [v for v in voids if "adjudicator_night_transcript" in v]

    def test_binds_its_own_seeds_paths_and_flags(self):
        arm = ARMS["transcript"]
        self.assertEqual((arm["first_seed"], arm["last_seed"]), (15000, 15999))
        for path in (arm["control"], arm["model"]):
            self.assertIn("transcript", path)
        self.assertNotIn(arm["doc"], (ARMS["supplied"]["doc"],
                                      ARMS["withheld"]["doc"]))
        self.assertTrue(arm["model_args"]["adjudicator_night_no_prior"])
        self.assertTrue(arm["model_args"]["adjudicator_night_transcript"])

    def test_refuses_a_record_without_the_transcript(self):
        arm = ARMS["transcript"]
        for summary in (self._summary(),
                        self._summary(adjudicator_night_transcript=False)):
            self.assertEqual(len(self._flag_voids(arm, summary)), 1)
        self.assertEqual(self._flag_voids(
            arm, self._summary(adjudicator_night_transcript=True)), [])

    def test_the_earlier_arms_refuse_a_transcript_record(self):
        for name, seed in (("withheld", 13000), ("supplied", 12000)):
            summary = self._summary(seed=seed, adjudicator_night_transcript=True,
                                    adjudicator_night_no_prior=name == "withheld")
            self.assertEqual(len(self._flag_voids(ARMS[name], summary)), 1)

    def _read(self, coherent, total):
        return coherence_read([game([told(3, 1, (2, 4), 1, False),
                                     told(3, 2, (2, 4), 1 if i < coherent else 0,
                                          False)], i) for i in range(total)])

    def test_the_withheld_comparison_is_the_published_read(self):
        self.assertEqual((WITHHELD_COHERENT, WITHHELD_PAIRS), (94, 122))

    def test_wholly_above_the_withheld_interval_recalls(self):
        self.assertEqual(recall_call(self._read(150, 160)), "RECALLS")

    def test_touching_the_withheld_interval_is_no_recall(self):
        self.assertEqual(recall_call(self._read(125, 160)), "NO RECALL")

    def test_no_pairs_is_no_recall_call(self):
        self.assertIsNone(recall_call(coherence_read(
            [game([told(3, 1, (2, 4), 2, True)])])))

    def test_the_supplied_comparison_wears_the_arm_labels(self):
        arm = ARMS["transcript"]
        self.assertEqual(supplied_call(self._read(100, 160), arm),
                         "BELOW SUPPLIED")
        self.assertEqual(supplied_call(self._read(150, 160), arm),
                         "AS GOOD AS SUPPLIED")
        self.assertEqual(supplied_call(self._read(100, 160), ARMS["withheld"]),
                         "NEEDS MEMORY")
