"""The gate decides which of two very different things a missing record is, so
both branches are pinned, and so is the pass-through that must stay silent.

Every case builds its own directory. A case whose subject is `eval/records/` on
this box would say the opposite thing in the slot this module exists for.
"""

import os
import shutil
import tempfile
import unittest

from eval import records_gate


class TestDemand(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)

    def assertRotDetected(self, *paths: str) -> None:
        """A missing record beside real runs must FAIL. Spelled out rather than
        `assertRaises(AssertionError)`, because a gate that skipped here would
        raise `SkipTest` THROUGH that helper and the case would report a skip -
        green, and testing nothing. Verified by mutation: with the rot branch
        disabled these cases report a failure, not a skip."""
        try:
            records_gate.demand(*paths)
        except unittest.SkipTest as skipped:
            self.fail(f"skipped a rotted citation instead of failing it: {skipped}")
        except AssertionError as caught:
            for path in paths:
                if not os.path.exists(path):
                    self.assertIn(os.path.basename(path), str(caught))
        else:
            self.fail("a missing record beside real runs passed silently")

    def _record(self, name: str) -> str:
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{}\n")
        return path

    def test_a_record_that_is_there_returns_and_says_nothing(self):
        self.assertIsNone(records_gate.demand(self._record("s2.json")))

    def test_an_empty_directory_is_a_slot_and_SKIPS(self):
        with self.assertRaises(unittest.SkipTest) as caught:
            records_gate.demand(os.path.join(self.dir, "s2.json"))
        self.assertIn("s2.json", str(caught.exception))

    def test_a_directory_that_never_existed_is_also_a_slot(self):
        with self.assertRaises(unittest.SkipTest):
            records_gate.demand(os.path.join(self.dir, "gone", "s2.json"))

    def test_a_populated_directory_missing_THIS_record_FAILS_it_does_not_skip(self):
        """The rot case, and the reason the line is drawn on the directory: the
        runs are here, so an instrument is citing a record that is not. A skip
        would retire that control silently, which is the failure this whole
        module exists to stop."""
        self._record("something-else.jsonl")
        self.assertRotDetected(os.path.join(self.dir, "s2.json"))

    def test_one_missing_record_among_present_ones_is_still_a_verdict(self):
        present = self._record("before.jsonl")
        self.assertRotDetected(present, os.path.join(self.dir, "after.jsonl"))
