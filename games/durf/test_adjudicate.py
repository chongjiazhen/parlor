"""The ruling parser, the three refusal kinds, and the ask loop's accounting.

The property under test throughout is the one the module docstring names: a ruling
(``illegal``), a refusal to rule (``decline``) and a reply nothing could be read
out of (fallback) are three different things, and no two of them may be pooled.
"""

from __future__ import annotations

import random
import unittest

from core.replies import ParseError
from games.durf import adjudicate


class FakeBackend:
    """Answers from a scripted list. ``Exception`` entries raise, standing in for a
    transport failure - the one refusal kind that says nothing about the ruling."""

    def __init__(self, replies, upstream="fake-model"):
        self.replies = list(replies)
        self.upstream = upstream
        self.asked: list[str] = []

    def complete_meta(self, context):
        self.asked.append(context)
        reply = self.replies.pop(0) if self.replies else "{}"
        if isinstance(reply, Exception):
            raise reply
        return reply, self.upstream


class ParseRuling(unittest.TestCase):
    def test_reads_a_fenced_reply_and_normalises_the_words(self):
        r = adjudicate.parse_ruling(
            'sure:\n```json\n{"ruling": "No-Roll", "attribute": "str"}\n```')
        self.assertEqual(r.ruling, "no_roll")
        # attribute is unreachable on a non-roll, so it is dropped, not refused
        self.assertIsNone(r.attribute)

    def test_a_roll_must_name_its_attribute(self):
        with self.assertRaises(adjudicate.IllegalReply) as ctx:
            adjudicate.parse_ruling('{"ruling": "roll"}')
        self.assertIn("governing attribute", str(ctx.exception))

    def test_a_roll_naming_a_non_attribute_is_refused(self):
        with self.assertRaises(adjudicate.IllegalReply):
            adjudicate.parse_ruling('{"ruling": "roll", "attribute": "CHA"}')

    def test_an_unknown_ruling_word_is_refused_rather_than_guessed(self):
        with self.assertRaises(adjudicate.IllegalReply) as ctx:
            adjudicate.parse_ruling('{"ruling": "maybe"}')
        self.assertIn("must be one of", str(ctx.exception))

    def test_no_json_at_all_raises_ParseError_not_IllegalReply(self):
        # The two are counted the same way but named differently in the trace, and
        # a run diagnosing a refusal needs to know which happened.
        with self.assertRaises(ParseError):
            adjudicate.parse_ruling("I would rather narrate this one.")

    def test_decline_is_a_legal_answer_and_carries_no_attribute(self):
        r = adjudicate.parse_ruling('{"ruling": "decline", "think": "unclear"}')
        self.assertEqual(r.ruling, "decline")
        self.assertIsNone(r.attribute)

    def test_illegal_is_a_ruling_and_not_a_refusal_to_rule(self):
        r = adjudicate.parse_ruling('{"ruling": "illegal"}')
        self.assertEqual(r.ruling, "illegal")
        self.assertFalse(r.rolls)


class ParseMorale(unittest.TestCase):
    def test_reads_booleans_and_the_words_for_them(self):
        self.assertTrue(adjudicate.parse_morale('{"morale": true}').morale)
        self.assertFalse(adjudicate.parse_morale('{"morale": "no"}').morale)

    def test_decline_lands_as_None_and_declared_declined(self):
        call = adjudicate.parse_morale('{"morale": "decline"}')
        self.assertIsNone(call.morale)
        self.assertTrue(call.declined)

    def test_a_value_that_is_neither_is_refused(self):
        with self.assertRaises(adjudicate.IllegalReply):
            adjudicate.parse_morale('{"morale": "perhaps"}')


class AskLoop(unittest.TestCase):
    def _arm(self, replies, retries=2):
        return adjudicate.LLMAdjudicator(
            backend=FakeBackend(replies), retries=retries, backoff=0.0,
            fallback=adjudicate.RandomAdjudicator(random.Random(1)))

    def test_a_clean_answer_counts_no_refusal_and_records_the_upstream(self):
        arm = self._arm(['{"ruling": "roll", "attribute": "DEX"}'])
        r = arm.rule("prompt", {"id": "d001"})
        self.assertEqual(r.attribute, "DEX")
        self.assertEqual((arm.last_refusals, arm.last_rule_refusals), (0, 0))
        self.assertFalse(arm.last_fell_back)
        self.assertEqual(arm.last_upstream, "fake-model")

    def test_a_refused_attempt_is_re_asked_with_the_complaint_appended(self):
        backend = FakeBackend(['{"ruling": "maybe"}',
                               '{"ruling": "no_roll"}'])
        arm = adjudicate.LLMAdjudicator(backend=backend, retries=2, backoff=0.0)
        r = arm.rule("PROMPT", {"id": "d002"})
        self.assertEqual(r.ruling, "no_roll")
        self.assertEqual(arm.last_rule_refusals, 1)
        self.assertFalse(arm.last_fell_back)
        self.assertIn("Your previous reply was refused", backend.asked[1])
        self.assertIn("d002 attempt 0", backend.asked[1])

    def test_a_transport_failure_is_not_counted_as_a_rule_refusal(self):
        # A flaky endpoint must not read as a model that will not follow the rules.
        arm = self._arm([RuntimeError("connection reset"),
                         '{"ruling": "no_roll"}'])
        arm.rule("prompt", {"id": "d003"})
        self.assertEqual(arm.last_refusals, 1)
        self.assertEqual(arm.last_rule_refusals, 0)

    def test_exhausting_the_budget_falls_back_and_says_so(self):
        arm = self._arm(['{"ruling": "maybe"}'] * 3, retries=2)
        r = arm.rule("prompt", {"id": "d004"})
        self.assertTrue(arm.last_fell_back)
        self.assertEqual(arm.last_refusals, 3)
        self.assertEqual(arm.last_upstream, "")
        self.assertIn(r.ruling, adjudicate.RandomAdjudicator.CHOICES)

    def test_counters_reset_between_items(self):
        # One adjudicator instance serves the whole run, so a stale counter would
        # attribute item N-1's refusals to item N.
        arm = self._arm(['{"ruling": "maybe"}', '{"ruling": "no_roll"}',
                         '{"ruling": "no_roll"}'])
        arm.rule("prompt", {"id": "d005"})
        arm.rule("prompt", {"id": "d006"})
        self.assertEqual(arm.last_refusals, 0)


class Arms(unittest.TestCase):
    def test_the_random_arm_never_declines(self):
        # `decline` is a refusal to answer; a random arm that produced one would
        # put a refusal rate on the board that no model wrote.
        arm = adjudicate.RandomAdjudicator(random.Random(3))
        seen = {arm.rule("p", {"id": "x"}).ruling for _ in range(200)}
        self.assertNotIn("decline", seen)
        self.assertEqual(seen, set(adjudicate.RandomAdjudicator.CHOICES))

    def test_the_llm_arm_refuses_to_build_without_a_backend(self):
        with self.assertRaises(ValueError):
            adjudicate.build_arm("llm")

    def test_every_named_arm_builds(self):
        for name in adjudicate.ARMS:
            if name == "llm":
                continue
            self.assertTrue(hasattr(adjudicate.build_arm(name), "rule"))


if __name__ == "__main__":
    unittest.main()
