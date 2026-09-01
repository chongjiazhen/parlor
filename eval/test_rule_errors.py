"""The rule-error instrument, pinned on the properties that would silently rot it.

Cheap on purpose - it scores records already on disk, so the whole file runs
without a model. The definitions it guards are in `eval/rule_errors.py`'s
docstring; a test here that contradicts one of them is the test to change.
"""

import unittest

from eval import records_gate
from eval import rule_errors as re_


def utterance(text: str, *, seat: int = 0, dealt: str = "bystander",
              game: int = 0) -> dict:
    """One synthetic record holding one utterance.

    Synthetic on purpose: a case whose subject is read out of a live record goes
    vacuous the moment that record is re-run or renamed, and these cases are about
    the PREDICATE, not about any run.
    """
    return {
        "game": game,
        "dealt": {str(seat): dealt},
        "utterances": [text],
        "decisions": 1,
        "fallbacks": 0,
        "decision_log": [{"seat": seat, "phase": "discuss"},
                         {"seat": seat, "phase": "vote"}],
    }


def score_one(text: str, dealt: str = "bystander") -> dict:
    return re_.score_arm([utterance(text, dealt=dealt)])


class TestSpeakerAttribution(unittest.TestCase):

    def test_the_speaker_comes_from_the_discuss_rows_in_order(self):
        rec = {
            "game": 0,
            "dealt": {"0": "bystander", "1": "switcher"},
            "utterances": ["first", "second"],
            "decision_log": [{"seat": 1, "phase": "discuss"},
                             {"seat": 0, "phase": "vote"},
                             {"seat": 0, "phase": "discuss"}],
        }
        self.assertEqual(re_.speaking_seats(rec), [1, 0])

    def test_a_pairing_that_does_not_line_up_RAISES_rather_than_shifting_by_one(self):
        """An off-by-one here mis-attributes every hit in the game to the wrong
        seat, and error B is conditioned on the speaker's deal - so a silent
        mismatch would move the count without moving anything visible."""
        rec = {"game": 3, "dealt": {}, "utterances": ["a", "b"],
               "decision_log": [{"seat": 0, "phase": "discuss"}]}
        with self.assertRaises(ValueError) as caught:
            re_.speaking_seats(rec)
        self.assertIn("game 3", str(caught.exception))


class TestErrorA(unittest.TestCase):
    """A: the speaker asserts its own dawn card is the card it was dealt."""

    def test_an_explicit_denial_that_the_card_moved_scores(self):
        self.assertEqual(len(score_one("My card didn't move.")["A"]), 1)

    def test_a_claim_to_still_hold_it_scores(self):
        self.assertEqual(len(score_one("I still hold the Seer card now.")["A"]), 1)

    def test_it_does_not_score_the_same_claim_about_ANOTHER_seat(self):
        """The error is an unentitled assertion about ONESELF. A read of another
        seat is ordinary play."""
        s = score_one("Seat 2 still holds her card, so she is clean.")
        self.assertEqual(len(s["A"]), 0)

    def test_a_predicate_cannot_span_a_sentence_boundary(self):
        """Two halves in two different clauses are not one assertion. The gap
        classes are ``[^.!?]`` for exactly this, and widening them to ``.`` scores
        the pair below - which is a seat reporting a robbery and a seat reading
        somebody else, neither of them the error."""
        s = score_one("Someone took my card. Seat 3 remains unchanged.")
        self.assertEqual(len(s["A"]), 0)

    def test_knowing_what_you_WERE_DEALT_is_not_an_error(self):
        """Every seat is entitled to that, and only the dawn card is unknowable.
        A looser form of the predicate scored this sentence and it was hand-read
        out of the count 2026-08-28."""
        s = score_one("The night swapped my card, but I still know what I was.")
        self.assertEqual(len(s["A"]), 0)

    def test_it_scores_regardless_of_whether_the_seat_turns_out_to_be_right(self):
        """The count is about what the speaker thinks the rules let it know, so
        the deal must not enter it. Divergence is silent by construction."""
        for dealt in ("bystander", "spotter", "pack"):
            self.assertEqual(len(score_one("My card didn't move.", dealt)["A"]), 1,
                             dealt)


class TestErrorB(unittest.TestCase):
    """B: a seat DEALT switcher speaks as though its own card was exchanged."""

    SELF_SWAP = "I exchanged cards with seats 1 and 3, but I have no idea what I'm holding now."

    def test_the_hand_read_sentence_scores(self):
        self.assertEqual(len(score_one(self.SELF_SWAP, "switcher")["B"]), 1)

    def test_it_is_conditioned_on_the_DEAL_not_on_what_the_seat_claims(self):
        """A seat claiming to be the switcher without holding it is lying or
        mistaken about its identity - play, not a rules error."""
        self.assertEqual(len(score_one(self.SELF_SWAP, "bystander")["B"]), 0)

    def test_the_CORRECT_reading_of_the_power_does_not_score(self):
        """Exchanging two OTHER seats' cards blind is what the card does, and the
        word-boundary guard is what keeps ``without`` from matching as ``with``."""
        s = score_one("I swapped two other seats' cards without knowing either.",
                      "switcher")
        self.assertEqual(len(s["B"]), 0)

    def test_someone_else_holding_my_card_is_the_same_claim_in_third_person(self):
        s = score_one("One of them now has my card.", "switcher")
        self.assertEqual(len(s["B"]), 1)


class TestEither(unittest.TestCase):

    def test_an_utterance_carrying_both_errors_counts_once(self):
        """``either`` is the union, because the published row is a rate of
        UTTERANCES. Summing the two columns would double-count."""
        text = ("My card didn't move. "
                "I exchanged cards with seats 1 and 3, so I don't know what I hold.")
        s = score_one(text, "switcher")
        self.assertEqual((len(s["A"]), len(s["B"]), s["either"]), (1, 1, 1))

    def test_an_utterance_matching_neither_counts_nowhere(self):
        s = score_one("Seat 3 has said nothing useful. I vote for seat 3.")
        self.assertEqual((len(s["A"]), len(s["B"]), s["either"]), (0, 0, 0))


class TestBlindFloor(unittest.TestCase):

    def test_the_switcher_is_NOT_the_seat_that_always_knows_what_it_holds(self):
        """TAKE runs before SWITCH, so the swapper can rob the switcher. RULES.md
        said otherwise, and error B is an upper bound because of it."""
        diverged, total = re_.switcher_divergence_floor(nights=400, seed=3)
        self.assertGreater(total, 0)
        self.assertGreater(diverged, 0)
        self.assertLess(diverged / total, 0.5)


class TestControl(unittest.TestCase):
    """The reproduction gate. It runs against the records on disk, because that is
    the only thing it can be a control ON - so in a tree that holds no run output
    it SKIPS rather than erroring, and says so (`eval/records_gate.py`). The two
    cases that only need synthetic input are in the class below, where a slot
    still runs them."""

    @classmethod
    def setUpClass(cls):
        records_gate.demand(*[p for pair in re_.PAIRS.values() for p in pair])
        cls.pairs = {label: {"before": re_.score_arm(re_.load(b)),
                             "after": re_.score_arm(re_.load(a))}
                     for label, (b, a) in re_.PAIRS.items()}

    def test_every_arm_carries_the_200_utterances_published_figures_divide_by(self):
        for label, arms in self.pairs.items():
            for arm, s in arms.items():
                self.assertEqual(s["utterances"], re_.UTTERANCES_PER_ARM,
                                 f"{label} {arm}")

    def test_the_2026_08_27_after_arm_returns_the_hand_reads_four_hits(self):
        self.assertEqual(len(self.pairs["2026-08-27"]["after"]["B"]),
                         re_.PRIOR_B["after"])

    def test_main_exits_zero_on_the_records_as_they_stand(self):
        self.assertEqual(re_.main([]), 0)


class TestTheControlFails(unittest.TestCase):
    """Synthetic on both sides, so it needs no records and survives a slot."""

    def test_the_control_reports_a_disagreement_by_FAILING_not_by_printing(self):
        """Mutation guard: the gate has to be the thing that fails. A control that
        only prints passes just as happily when it stops agreeing."""
        broken = {"2026-08-27": {
            "before": {"utterances": 200, "B": []},
            "after": {"utterances": 200, "B": []}}}
        self.assertTrue(re_.control(broken))

    def test_a_wrong_denominator_fails_the_control(self):
        broken = {"x": {"before": {"utterances": 199, "B": []},
                        "after": {"utterances": 200, "B": []}}}
        self.assertTrue(re_.control(broken))


if __name__ == "__main__":
    unittest.main()
