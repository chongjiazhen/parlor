"""Reply-reading tests. Game-agnostic, like the module they cover.

These pin the behaviours that were learned from real endpoints: fenced JSON,
prose preambles, replies truncated mid-object by a provider, and words where a
boolean was asked for. Every game in the ladder inherits them.
"""

import unittest

from core.replies import (
    ParseError,
    extract_json,
    parse_bool,
    parse_index,
    parse_index_set,
    read_reply,
    salvage,
)

KEYS = ("team", "vote", "card", "say", "target", "think")


class TestExtractJson(unittest.TestCase):
    def test_out_of_prose_and_fences(self):
        self.assertEqual(extract_json('sure thing!\n```json\n{"vote": "approve"}\n```'),
                         {"vote": "approve"})

    def test_first_balanced_object_wins_with_nesting(self):
        self.assertEqual(extract_json('{"think": {"a": 1}, "vote": "reject"}')["vote"],
                         "reject")

    def test_a_leading_non_object_brace_is_skipped(self):
        self.assertEqual(extract_json('{not json} then {"vote": "no"}')["vote"], "no")

    def test_no_json_raises(self):
        with self.assertRaises(ParseError):
            extract_json("I refuse to answer in JSON.")


class TestSalvage(unittest.TestCase):
    def test_truncated_reply_still_yields_its_decision(self):
        # the shape the clean tier produced: opening brace cut off, never closed
        truncated = ('think": "seat 0 is our partner so the best play here is to '
                     'send", "team": [0, 3], "note": "cut off mid-')
        self.assertEqual(salvage(truncated, KEYS)["team"], [0, 3])

    def test_quoted_value_wins_over_bare(self):
        self.assertEqual(salvage('"vote": "approve", "x": 1', KEYS)["vote"], "approve")

    def test_a_reply_with_no_decision_in_it_raises(self):
        with self.assertRaises(ParseError):
            salvage("I will not participate in this exercise.", KEYS)

    def test_read_reply_prefers_real_json(self):
        # a valid object must not be reinterpreted by the scrape path
        self.assertEqual(read_reply('{"team": [1, 2]}', KEYS)["team"], [1, 2])


class TestCoercion(unittest.TestCase):
    def test_bool_words_and_punctuation(self):
        self.assertTrue(parse_bool("Approve."))
        self.assertFalse(parse_bool("no"))
        self.assertTrue(parse_bool(True))

    def test_custom_word_sets(self):
        self.assertTrue(parse_bool("fail", true_words={"fail"}, false_words={"success"}))

    def test_an_unknown_word_raises_rather_than_defaulting(self):
        """A silent default here would fabricate a decision the model never made."""
        with self.assertRaises(ParseError):
            parse_bool("maybe")

    def test_index_forms(self):
        self.assertEqual(parse_index(2, 5), 2)
        self.assertEqual(parse_index("seat 3", 5), 3)

    def test_index_out_of_range_raises(self):
        with self.assertRaises(ParseError):
            parse_index(9, 5)

    def test_a_bool_is_not_an_index(self):
        # True == 1 in Python; accepting it would silently mean "seat 1"
        with self.assertRaises(ParseError):
            parse_index(True, 5)

    def test_index_set_from_list_and_from_prose(self):
        self.assertEqual(parse_index_set([2, 0], 5, 2), [0, 2])
        self.assertEqual(parse_index_set("seats 1 and 4", 5, 2), [1, 4])

    def test_duplicates_are_not_a_set_of_two(self):
        with self.assertRaises(ParseError):
            parse_index_set([1, 1], 5, 2)


if __name__ == "__main__":
    unittest.main()
