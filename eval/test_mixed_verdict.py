"""The mixed-cell scorer - the guards, and the pin to the criterion.

The arithmetic is borrowed and tested where it lives: `eval.s5_verdict`'s
`winnable` and blind stratum, `eval.skin_pair_verdict`'s Newcombe and `Arm`.
What is new here is the binding, and every test is a guard the criterion names:
settings that must match the frozen file, a control rescored on its FIRST 200
games rather than quoted at 1000, a fallback bar read off the LIVE SIDE's own
rate rather than the diluted run-level one, a scored-games floor, and a blind
floor that refuses the secondary without touching the primary.

The settings test reads `docs/changeling-mixed-criterion.md` itself rather than a
copy of its numbers, because the failure this repo has already paid for is a
launcher and a criterion disagreeing while both looked right on their own.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from eval.mixed_verdict import (
    ARMS,
    CONTROL_GAMES,
    CRITERION,
    EXPECTED,
    SCORED_FLOOR,
    Arm,
    control_slice,
    dedupe_last,
    live_fallback,
    live_seats,
    rung_wins,
    settings_voids,
    summary_voids,
    verdict,
)

#: Seats 1 and 4 hold pack at dawn, 0/2/3 village. Dawn TRUTH is the seating
#: rule, so this map alone decides which seats were live in either arm.
TRUTH = {"0": "spotter", "1": "pack", "2": "bystander", "3": "swapper",
         "4": "pack"}


def game(index, winner, log=(), decisions=()):
    return {"game": index, "winner": winner, "truth": TRUTH,
            "dealt": dict(TRUTH), "log": list(log), "votes": [],
            "accused": [], "decision_log": list(decisions)}


def decision(seat, fell_back):
    return {"seat": seat, "fell_back": fell_back, "phase": "discuss"}


def arm(village_wins, pack_wins, first=0, fallback=0.0, decisions=()):
    games = [game(first + i, "village", decisions=decisions)
             for i in range(village_wins)]
    games += [game(first + village_wins + i, "pack", decisions=decisions)
              for i in range(pack_wins)]
    return Arm(name="cl-mixed-pack", games=games, fallback_rate=fallback)


def args(**over) -> dict:
    base = dict(EXPECTED)
    base["arm"] = "mixed-pack"
    base.update(over)
    return base


class TestSettingsPin(unittest.TestCase):
    def test_a_matching_record_raises_no_void(self):
        self.assertEqual(settings_voids(args(), "mixed-pack"), [])

    def test_a_changed_setting_is_named_with_both_values(self):
        [void] = settings_voids(args(temperature=0.0), "mixed-pack")
        self.assertIn("temperature", void)
        self.assertIn("0.0", void)
        self.assertIn("0.8", void)

    def test_the_arm_name_is_itself_a_setting(self):
        self.assertTrue(settings_voids(args(), "mixed-village"))

    def test_the_criterion_file_still_says_what_this_module_copied(self):
        text = Path(CRITERION).read_text(encoding="utf-8")
        for token in ("--games 200", "--seats 5", "--theme folk", "--rounds 2",
                      "--seed 5000", "--no-thinking", "--timeout 240",
                      "qwen36-35b-a3b-iq3", "--temperature 0.8"):
            self.assertIn(token, text, f"{token} is no longer in {CRITERION}")

    def test_the_criterion_still_names_both_arms_and_their_published_controls(self):
        text = Path(CRITERION).read_text(encoding="utf-8")
        for name in ARMS:
            self.assertIn(name, text)
        self.assertIn("56.09%", text)
        self.assertIn("43.91%", text)


class TestControlSlice(unittest.TestCase):
    """The control is 1000 games over a SUPERSET of the arm's seeds. Pairing
    against the published figure would compare two different populations."""

    def test_only_the_first_200_game_indices_survive(self):
        games = [game(i, "village") for i in range(1000)]
        self.assertEqual(len(control_slice(games)), CONTROL_GAMES)

    def test_it_selects_by_game_INDEX_not_by_file_position(self):
        """A positional head of this input would keep 900 and 400; selecting on
        the index keeps 1, 3 and 5, in game order."""
        games = [game(i, "village") for i in (900, 5, 3, 400, 1)]
        self.assertEqual([g["game"] for g in control_slice(games)], [1, 3, 5])

    def test_a_short_control_is_returned_whole_rather_than_padded(self):
        games = [game(i, "pack") for i in range(20)]
        self.assertEqual(len(control_slice(games)), 20)


class TestDedupe(unittest.TestCase):
    """`cl-heuristic.json.jsonl` holds 3000 lines for a 1000-game run: the
    per-game JSONL is opened in APPEND mode while the summary is truncated, so
    re-running an arm onto an existing path stacks blocks. Measured 2026-09-03 -
    block 1 of that file is a stale run of the same seeds at 71.55% pack wins
    against the published 56.09%, and reading the file naively blends them into
    a plausible wrong number with nothing raising."""

    def test_the_last_write_of_each_game_index_wins(self):
        games = [game(0, "village"), game(1, "pack"), game(0, "pack")]
        self.assertEqual([g["winner"] for g in dedupe_last(games)],
                         ["pack", "pack"])

    def test_it_keeps_ascending_game_order_not_file_order(self):
        games = [game(2, "pack"), game(0, "village"), game(2, "village")]
        self.assertEqual([g["game"] for g in dedupe_last(games)], [0, 2])

    def test_a_clean_record_is_returned_unchanged(self):
        games = [game(i, "village") for i in range(5)]
        self.assertEqual(len(dedupe_last(games)), 5)

    def test_control_slice_dedupes_before_it_slices(self):
        games = [game(i, "village") for i in range(300)] * 3
        self.assertEqual(len(control_slice(games)), CONTROL_GAMES)


class TestSummaryCrossCheck(unittest.TestCase):
    """Deduping RECOVERS a run rather than proving it - so the recovered whole
    is checked against the figures the summary published from it, and a
    disagreement refuses the control instead of pairing against a guess."""

    def test_a_control_matching_its_summary_raises_no_void(self):
        games = arm(3, 2).games
        summary = {"games_scored": 5, "gate2_deception": {"village_wins": 3}}
        self.assertEqual(summary_voids(games, summary), [])

    def test_a_wrong_scored_count_is_named(self):
        games = arm(3, 2).games
        summary = {"games_scored": 977, "gate2_deception": {"village_wins": 3}}
        [void] = summary_voids(games, summary)
        self.assertIn("977", void)

    def test_a_wrong_win_count_is_named(self):
        games = arm(3, 2).games
        summary = {"games_scored": 5, "gate2_deception": {"village_wins": 429}}
        [void] = summary_voids(games, summary)
        self.assertIn("429", void)


class TestRungWins(unittest.TestCase):
    def test_the_rungs_side_decides_which_winner_counts(self):
        games = arm(3, 2).games
        self.assertEqual(rung_wins(games, "village"), (3, 5))
        self.assertEqual(rung_wins(games, "pack"), (2, 5))

    def test_an_unwinnable_game_leaves_the_denominator(self):
        no_wolf = game(9, "village")
        no_wolf["truth"] = {"0": "bystander", "1": "bystander", "2": "spotter"}
        self.assertEqual(rung_wins([no_wolf], "village"), (0, 0))


class TestLiveSeats(unittest.TestCase):
    """Seated by DAWN TRUTH - the driver's rule, not belief."""

    def test_mixed_pack_seats_the_pack_live(self):
        self.assertEqual(live_seats(game(0, "pack"), "mixed-pack"), {1, 4})

    def test_mixed_village_seats_the_village_live(self):
        self.assertEqual(live_seats(game(0, "pack"), "mixed-village"), {0, 2, 3})


class TestLiveFallback(unittest.TestCase):
    """The run-level rate is diluted by rung seats that never fall back, so the
    criterion puts the bar on the live side's OWN rate."""

    def test_it_counts_only_decisions_at_live_seats(self):
        rows = [decision(1, True), decision(4, False), decision(0, False),
                decision(2, False), decision(3, False)]
        self.assertEqual(live_fallback([game(0, "pack", decisions=rows)],
                                       "mixed-pack"), (1, 2))

    def test_the_same_record_reads_differently_for_the_other_arm(self):
        rows = [decision(1, True), decision(0, True), decision(2, False)]
        self.assertEqual(live_fallback([game(0, "pack", decisions=rows)],
                                       "mixed-village"), (1, 2))

    def test_it_is_higher_than_the_run_level_rate_it_replaces(self):
        rows = [decision(1, True)] + [decision(s, False) for s in (0, 2, 3, 4)]
        fell, total = live_fallback([game(0, "pack", decisions=rows)],
                                    "mixed-pack")
        self.assertGreater(fell / total, 1 / len(rows))

    def test_no_live_decisions_is_not_a_zero_rate(self):
        self.assertEqual(live_fallback([game(0, "pack")], "mixed-pack"), (0, 0))


class TestVerdict(unittest.TestCase):
    def test_a_clean_pair_with_no_gap_is_not_shown(self):
        v = verdict(arm(90, 90), arm(90, 90, first=500), "mixed-pack")
        self.assertEqual(v.call, "NOT SHOWN")

    def test_a_wide_gap_informs(self):
        v = verdict(arm(170, 10), arm(20, 160, first=500), "mixed-pack")
        self.assertEqual(v.call, "INFORMS")

    def test_the_live_sides_own_fallback_voids_the_difference(self):
        rows = [decision(1, True), decision(4, True)] + [
            decision(s, False) for s in (0, 2, 3)]
        a = arm(170, 10, decisions=rows)
        v = verdict(a, arm(20, 160, first=500), "mixed-pack")
        self.assertEqual(v.call, "VOID")
        self.assertTrue(any("fallback" in r for r in v.reasons))

    def test_a_voided_pair_still_carries_its_arithmetic(self):
        rows = [decision(1, True), decision(4, True)] + [
            decision(s, False) for s in (0, 2, 3)]
        v = verdict(arm(170, 10, decisions=rows), arm(20, 160, first=500),
                    "mixed-pack")
        self.assertIsNotNone(v.diff)
        self.assertIsNotNone(v.newcombe)

    def test_too_few_scored_games_is_refused_not_called(self):
        v = verdict(arm(10, 10), arm(90, 90, first=500), "mixed-pack")
        self.assertEqual(v.call, "REFUSED")
        self.assertTrue(any(str(SCORED_FLOOR) in r for r in v.reasons))

    def test_the_control_is_held_to_the_same_scored_floor(self):
        v = verdict(arm(90, 90), arm(10, 10, first=500), "mixed-pack")
        self.assertEqual(v.call, "REFUSED")

    def test_a_void_outranks_a_refusal(self):
        rows = [decision(1, True), decision(4, True)] + [
            decision(s, False) for s in (0, 2, 3)]
        v = verdict(arm(10, 10, decisions=rows), arm(10, 10, first=500),
                    "mixed-pack")
        self.assertEqual(v.call, "VOID")


if __name__ == "__main__":
    unittest.main()
