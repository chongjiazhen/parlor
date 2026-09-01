"""What a MISSING record means, which is not the same thing in every tree.

`eval/records/` is gitignored, so a control that reads a run off disk is a test
whose subject exists in exactly one checkout. In the tree that produced the runs
the records are there and the control runs. In a lane slot - a worktree, or any
fresh clone - the directory is empty, and before this module that absence errored
at COLLECTION: `eval/test_deduction.py` never entered the suite at all, and five
`eval/test_rule_errors.py` controls errored at setUp. A worker graded in a slot
was graded against a suite with a hole in it, and the `--accept` chain reported
the green.

Tracking the records instead was the other candidate and is refused: 4.5 MB of
run OUTPUT, against the invariant that output stays untracked and only the recipe
is versioned. Junctioning the main tree's records into a slot was refused for the
reason `queue.md` recorded - it hands an untrusted worker a write path into the
only copy.

So absence is a skip, and the line between an excused absence and rot is drawn on
the DIRECTORY, not on the file:

- the records directory holds no runs at all -> a slot or a clone, nothing was
  ever there, skip and say which file was wanted;
- the directory holds runs and the demanded one is not among them -> an
  instrument still cites a record that has been renamed or deleted. That is the
  failure this repo actually fears, so it FAILS, loudly, naming the file.

A skip is visible in the suite output and keeps the node in `--collect-only`, so
the count floor in `scripts/testfloor.py` still measures what it measured before.
"""

from __future__ import annotations

import os
import unittest


def _holds_runs(directory: str) -> bool:
    return os.path.isdir(directory) and any(os.scandir(directory))


def demand(*paths: str) -> None:
    """Raise `SkipTest` if these records were never here, `AssertionError` if they
    were. Call it from `setUpClass`, or from the one test that reads a record."""
    missing = [p for p in paths if not os.path.exists(p)]
    if not missing:
        return
    populated = sorted(d for d in {os.path.dirname(p) for p in paths}
                       if _holds_runs(d))
    if populated:
        raise AssertionError(
            f"{', '.join(populated)} holds runs but not {', '.join(missing)} - an "
            "instrument is citing a record that has been renamed or deleted, and "
            "its control is reading nothing. Fix the citation or restore the run.")
    raise unittest.SkipTest(
        f"no run output in this tree, so {', '.join(missing)} cannot be read. This "
        "control is NOT part of a grade taken here - run it in the tree that holds "
        "eval/records/.")
