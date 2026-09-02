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

    def test_a_SURVIVING_SIBLING_of_the_same_run_is_the_rot_signal(self):
        """The rot case, and the reason the line is drawn per record: `s2.log` is
        the run that wrote `s2.json`, so the run happened HERE and an instrument
        is citing an artifact of it that is not. A skip would retire that control
        silently, which is the failure this whole module exists to stop."""
        self._record("s2.log")
        self.assertRotDetected(os.path.join(self.dir, "s2.json"))

    def test_a_MISSING_json_jsonl_stems_past_both_suffixes_to_its_run(self):
        """The suffix order carries a real case and only this direction shows
        it. `s2.json.jsonl` must stem to `s2`, not to `s2.json`: with the short
        suffix matching first the surviving `s2.log` is not recognised as its
        run and the rot reads as a slot. The mirrored case - `s2.json` missing
        beside a surviving `s2.json.jsonl` - passes under either order, so it is
        not the test that pins this."""
        self._record("s2.log")
        self.assertRotDetected(os.path.join(self.dir, "s2.json.jsonl"))

    def test_an_UNRELATED_run_is_not_evidence_and_the_citation_SKIPS(self):
        """The premise this module dropped 2026-09-03. `something-else` says
        nothing about `s2`, and reading it as evidence is what made a fresh
        worktree fail every control it should have skipped."""
        self._record("something-else.jsonl")
        self._record("something-else.log")
        with self.assertRaises(unittest.SkipTest):
            records_gate.demand(os.path.join(self.dir, "s2.json"))

    def test_a_run_removed_WHOLE_skips_and_this_is_the_named_downgrade(self):
        """The one case the directory rule caught and this one cannot: every
        artifact of the run is gone, so from inside the tree it is
        indistinguishable from a run that was never here. Pinned so that a later
        reader finds a decision rather than a hole - the skip still names the
        file, which the pre-gate behaviour did not."""
        self._record("something-else.log")
        with self.assertRaises(unittest.SkipTest) as caught:
            records_gate.demand(os.path.join(self.dir, "s2.json"))
        self.assertIn("s2.json", str(caught.exception))

    def test_one_missing_record_among_present_ones_is_still_a_verdict(self):
        present = self._record("before.jsonl")
        self.assertRotDetected(present, os.path.join(self.dir, "after.jsonl"))

    def test_a_worktree_that_wrote_its_OWN_runs_still_skips_a_record_it_never_held(self):
        """The queue's 2026-09-02 finding, pinned. A fresh worktree runs an arm,
        three control JSONs land in a directory that was empty, and every control
        that reads a record it never had flipped from skip to failure - 8 skips
        became 6 failures and 3 errors. Nothing about `some-control` says anything
        about `s2`, so the gate must not read one as evidence for the other."""
        self._record("some-control.json")
        self._record("some-control.json.jsonl")
        self._record("some-control.log")
        with self.assertRaises(unittest.SkipTest) as caught:
            records_gate.demand(os.path.join(self.dir, "s2.json"))
        self.assertIn("s2.json", str(caught.exception))
