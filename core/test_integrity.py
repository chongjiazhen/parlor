"""The integrity block: three outcomes, and a rate that says whose it is.

Every case here is a claim the S9 semantics change makes, written so that removing
the change breaks the case by name. The records are hand-built stand-ins rather
than played games - what is under test is the arithmetic over decision counts, and
a real game would only make the numbers harder to read.
"""

import unittest
from dataclasses import dataclass, field

from core import integrity


@dataclass
class FakeDecision:
    seat: int
    fell_back: bool = False


@dataclass
class FakeRecord:
    """Only the fields ``core.integrity`` is documented to read."""

    decisions: int = 0
    fallbacks: int = 0
    recovered: int = 0
    refused_attempts: int = 0
    rule_refused_attempts: int = 0
    decision_log: list = field(default_factory=list)
    upstreams: dict = field(default_factory=dict)
    trace_sample: list = field(default_factory=list)
    error: str | None = None


def game(decisions, fallbacks=0, recovered=0, attempts=0, rule_attempts=0,
         seats=(0, 1, 2, 3, 4), error=None):
    """One game whose decision log is round-robin over ``seats``, with the
    fallbacks landing on the first seat unless a caller says otherwise."""
    log = [FakeDecision(seat=seats[i % len(seats)]) for i in range(decisions)]
    placed = 0
    for d in log:
        if placed < fallbacks and d.seat == seats[0]:
            d.fell_back = True
            placed += 1
    return FakeRecord(decisions=decisions, fallbacks=fallbacks,
                      recovered=recovered, refused_attempts=attempts,
                      rule_refused_attempts=rule_attempts, decision_log=log,
                      error=error)


class TestThreeOutcomes(unittest.TestCase):
    """A decision is clean, recovered or a fallback, and the three partition the
    total. Before S9 there were two and the middle one was counted as clean."""

    def test_the_three_outcomes_partition_the_decisions(self):
        s = integrity.summarise([game(20, fallbacks=2, recovered=5)])
        self.assertEqual(s["fallbacks"] + s["recovered"] + s["clean_decisions"],
                         s["decisions"])
        self.assertEqual(s["clean_decisions"], 13)

    def test_recovered_is_reported_separately_from_the_fallback_rate(self):
        """The whole point of item 4. A run at 1% fallback and 25% recovered must
        not read as a run at 1%."""
        s = integrity.summarise([game(20, fallbacks=0, recovered=5)])
        self.assertEqual(s["fallback_rate"], 0.0)
        self.assertEqual(s["recovered_rate"], 0.25)

    def test_the_attempt_counts_are_diagnostic_and_not_the_headline(self):
        """Attempts are bounded only by the retry budget, so a rate over them means
        nothing - they are carried, never divided by decisions."""
        s = integrity.summarise([game(10, recovered=2, attempts=7, rule_attempts=3)])
        self.assertEqual(s["refused_attempts"], 7)
        self.assertEqual(s["rule_refused_attempts"], 3)
        self.assertNotIn("refusal_rate", s)


class TestCleanGames(unittest.TestCase):
    """Item 2. A clean game is one no seat had to be corrected in."""

    def test_a_game_with_no_fallback_and_no_recovery_is_clean(self):
        s = integrity.summarise([game(10), game(10)])
        self.assertEqual((s["clean_games"], s["games_finished"]), (2, 2))

    def test_a_recovered_decision_costs_the_game_its_clean_count(self):
        """A game the model had to be sent back in is not a clean game, even though
        every decision in it was legal by the time it landed."""
        s = integrity.summarise([game(10), game(10, recovered=1)])
        self.assertEqual(s["clean_games"], 1)

    def test_a_transport_failure_alone_leaves_the_game_clean(self):
        """A 429 is not a seat failing to follow the rules. ``recovered`` counts
        only what the parser or the rules sent back, so a game that flaked in
        transport and answered correctly every time is still clean."""
        s = integrity.summarise([game(10, attempts=4, rule_attempts=0)])
        self.assertEqual((s["clean_games"], s["recovered"]), (1, 0))

    def test_an_errored_game_is_in_neither_half_of_the_clean_count(self):
        """It never finished, so calling it clean or dirty makes the denominator a
        statement about crashes."""
        s = integrity.summarise([game(10), game(3, error="referee failed")])
        self.assertEqual((s["clean_games"], s["games_finished"]), (1, 1))


class TestCausedVersusWitnessed(unittest.TestCase):
    """Item 1. The rate parlor reported was only the caused half."""

    def test_the_caused_rate_is_unchanged_and_keeps_its_name(self):
        """``fallback_rate`` is quoted by every record in eval/records and every
        published summary. It had to keep meaning exactly what it meant."""
        s = integrity.summarise([game(20, fallbacks=2)])
        self.assertEqual(s["fallback_rate"], 0.1)

    def test_a_seat_that_caused_nothing_still_witnessed_the_table(self):
        """Seat 0 fell back on all four of its decisions; the other four seats
        caused nothing and each played a table that was one-fifth random. The
        caused rate cannot tell those two positions apart."""
        s = integrity.summarise([game(20, fallbacks=4)])
        self.assertEqual(s["fallback_rate"], 0.2)
        self.assertAlmostEqual(s["witnessed_worst"], 4 / 16)
        self.assertEqual(s["seat_games"], 5)

    def test_the_seat_that_caused_them_witnessed_none(self):
        """The witnessed rate excludes a seat's own decisions, or it would just be
        the caused rate with extra steps."""
        rates = integrity._witnessed([game(20, fallbacks=4)])
        self.assertIsNotNone(rates["witnessed_rate"])
        # four seats at 4/16, and the culprit at 0/16
        self.assertAlmostEqual(rates["witnessed_rate"], (4 * 0.25) / 5)

    def test_seat_games_over_the_void_bar_are_counted(self):
        """The run-level mean is dull by construction; the number worth reading is
        how many seat-games were individually above the bar the scorer voids at."""
        s = integrity.summarise([game(20, fallbacks=4)])
        self.assertEqual(s["witnessed_over_bar"], 4)

    def test_the_two_witnessed_counts_answer_different_questions(self):
        """One fallback in a 20-decision game puts four seats at 1/16 = 6.25% - a
        random opponent every one of them faced, and none of them over the bar."""
        s = integrity.summarise([game(20, fallbacks=1)])
        self.assertEqual(s["witnessed_any"], 4)
        self.assertEqual(s["witnessed_over_bar"], 0)

    def test_an_unmeasured_table_reports_None_not_zero(self):
        """Same refusal ``wilson`` makes: 0.00% reads as a clean table when what
        happened is that nothing was measured."""
        s = integrity.summarise([])
        self.assertIsNone(s["witnessed_rate"])
        self.assertIsNone(s["witnessed_worst"])

    def test_a_single_seat_game_contributes_no_witnessed_rate(self):
        """With one seat there is no ``other``, so a zero would be an invention."""
        s = integrity.summarise([game(4, seats=(0,))])
        self.assertIsNone(s["witnessed_rate"])

    def test_a_recorded_jsonl_re_scores_without_being_rehydrated(self):
        """A decision log is dataclasses on a live run and plain dicts on a
        re-score. Both are real callers."""
        rec = game(20, fallbacks=4)
        rec.decision_log = [{"seat": d.seat, "fell_back": d.fell_back}
                            for d in rec.decision_log]
        self.assertAlmostEqual(integrity.summarise([rec])["witnessed_worst"], 0.25)


class TestReportLines(unittest.TestCase):

    def test_every_outcome_reaches_the_report(self):
        lines = "\n".join(integrity.report_lines(
            integrity.summarise([game(20, fallbacks=2, recovered=3,
                                      attempts=9, rule_attempts=5)])))
        self.assertIn("caused", lines)
        self.assertIn("witnessed", lines)
        self.assertIn("recovered", lines)
        self.assertIn("clean", lines)
        self.assertIn("transport", lines)

    def test_transport_is_left_unsaid_when_there_was_none(self):
        lines = "\n".join(integrity.report_lines(
            integrity.summarise([game(20, recovered=1, attempts=2,
                                      rule_attempts=2)])))
        self.assertNotIn("transport", lines)

    def test_the_void_bar_is_one_constant(self):
        """Both games warn off this threshold. Two literals drift."""
        self.assertEqual(integrity.VOID_BAR, 0.10)


class TestTheRecoveredBar(unittest.TestCase):
    """Set 2026-08-28, BEFORE any run produced the number. S9 added `recovered` and
    gave it no bar, so a run at 1% fallback and 40% recovered passed every check and
    read as clean. Picking the bar after seeing changeling's 200 games would be the
    peeking this repo refuses by name."""

    def summary(self, recovered):
        return integrity.summarise([game(100, fallbacks=1, recovered=recovered)])

    def test_a_high_recovered_rate_is_flagged(self):
        lines = chr(10).join(integrity.report_lines(self.summary(40)))
        self.assertIn("NOTE:", lines)
        self.assertIn("25%", lines)

    def test_a_low_recovered_rate_is_not(self):
        lines = chr(10).join(integrity.report_lines(self.summary(5)))
        self.assertNotIn("NOTE:", lines)

    def test_exactly_at_the_bar_does_not_fire(self):
        """Strictly above, matching how the void bar is applied."""
        lines = chr(10).join(integrity.report_lines(self.summary(25)))
        self.assertNotIn("NOTE:", lines)

    def test_it_WARNS_and_never_voids(self):
        """The asymmetry is the decision. A fallback is a decision no model made, so
        a verdict resting on it is void. A recovered decision IS the model's - it was
        refused, told why, and got it right - so it belongs beside the verdict."""
        lines = chr(10).join(integrity.report_lines(self.summary(90)))
        self.assertIn("NOT a void", lines)
        self.assertNotIn("VOID", lines.replace("NOT a void", ""))

    def test_the_two_bars_are_separate_constants(self):
        """A single threshold would either void a legal run or excuse a random one."""
        self.assertEqual(integrity.RECOVERED_WARN_BAR, 0.25)
        self.assertGreater(integrity.RECOVERED_WARN_BAR, integrity.VOID_BAR)

    def test_a_run_can_be_clean_on_fallback_and_flagged_on_recovery(self):
        """The exact hole S9 left: nothing else in the block reports this run as
        anything other than healthy."""
        s = self.summary(40)
        self.assertLess(s["fallback_rate"], integrity.VOID_BAR)
        self.assertGreater(s["recovered_rate"], integrity.RECOVERED_WARN_BAR)


if __name__ == "__main__":
    unittest.main()
