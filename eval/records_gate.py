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

So absence is a skip, and the line between an excused absence and rot is drawn
**per record, on the run it names**. It was drawn on the DIRECTORY until
2026-09-03, and that premise - a populated directory means the cited records
should be here - is false in the tree this module exists for: a fresh worktree
that runs one arm populates the directory with runs of its OWN, and measured
2026-09-02, three new control JSONs turned 8 skips into 6 failures and 3 errors.
Nothing about `some-control` is evidence about `s2`.

What IS evidence about `s2` is `s2` - the run writes `s2.json`, `s2.json.jsonl`
and `s2.log` together, so a surviving sibling says the run happened HERE and the
demanded artifact has since been renamed or deleted. So:

- a surviving sibling of the demanded record's own run, or another record present
  in the same citation -> the run was here and the artifact is not. That is the
  failure this repo actually fears, so it FAILS, loudly, naming the file;
- no trace of the run at all -> a slot or a clone, nothing was ever there, skip
  and say which file was wanted.

**The one case this downgrades, named rather than discovered:** a run removed or
renamed WHOLE - every sibling gone - reads as a slot and skips. The directory
rule caught that and this one cannot, because the two are indistinguishable from
inside a tree that never held the run. The skip still names the file in the suite
output, where the pre-2026-08 behaviour was a control that never collected at all.

A skip is visible in the suite output and keeps the node in `--collect-only`, so
the count floor in `scripts/testfloor.py` still measures what it measured before.
"""

from __future__ import annotations

import os
import unittest

#: Every extension the run machinery writes for one run, longest first so that
#: `s2.json.jsonl` stems to `s2` rather than to `s2.json`. The 2026-08-27 pair
#: predates the `.json.jsonl` naming and writes a bare `.jsonl`, which is why
#: that suffix is here in its own right.
_SUFFIXES = (".json.jsonl", ".jsonl", ".json", ".log")


def _stem(path: str) -> str:
    """The run a record belongs to, which is its path minus the artifact suffix."""
    for suffix in _SUFFIXES:
        if path.endswith(suffix):
            return path[:-len(suffix)]
    return path


def _siblings_here(path: str) -> list[str]:
    """The artifacts of `path`'s own run that this tree still holds - `path`
    itself excluded, since it is the thing that is missing."""
    stem = _stem(path)
    return [candidate for candidate in (stem + suffix for suffix in _SUFFIXES)
            if candidate != path and os.path.exists(candidate)]


def demand(*paths: str) -> None:
    """Raise `SkipTest` if these records were never here, `AssertionError` if they
    were. Call it from `setUpClass`, or from the one test that reads a record."""
    missing = [p for p in paths if not os.path.exists(p)]
    if not missing:
        return
    witnesses = sorted({w for p in missing for w in _siblings_here(p)}
                       | {p for p in paths if os.path.exists(p)})
    if witnesses:
        raise AssertionError(
            f"{', '.join(witnesses)} is here but not {', '.join(missing)} - an "
            "instrument is citing a record that has been renamed or deleted, and "
            "its control is reading nothing. Fix the citation or restore the run.")
    raise unittest.SkipTest(
        f"no run output in this tree, so {', '.join(missing)} cannot be read. This "
        "control is NOT part of a grade taken here - run it in the tree that holds "
        "eval/records/.")
