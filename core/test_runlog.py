"""The marker has to survive the ways a twelve-hour run actually ends.

Every test here is about the same reader: someone opening a log the next morning
with no session, no process and no chain log, who has to decide whether the run
finished or was killed. `hunt20b` gave that reader a clean log with no marker.
"""

from __future__ import annotations

import io
import os
import pathlib
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from core.runlog import (MARKER, RunState, claim_record, record_paths,
                         run_with_marker)


#: one landed game, as `land()` writes it - a line, terminated.
LANDED_GAME = '{"game": 0}\n'


def run(main, state: RunState | None = None) -> tuple[int, str, str]:
    state = state if state is not None else RunState()
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = run_with_marker(main, state)
    return rc, out.getvalue(), err.getvalue()


def marker_line(stdout: str) -> str:
    lines = [ln for ln in stdout.splitlines() if ln.startswith(MARKER)]
    assert len(lines) == 1, f"expected exactly one marker, got {lines}"
    return lines[0]


class TestTheMarkerIsAlwaysWritten(unittest.TestCase):

    def test_a_clean_run_ends_in_a_marker_naming_its_yield(self):
        state = RunState()

        def main():
            state.requested = 3
            state.landed = 3

        rc, out, _ = run(main, state)
        self.assertEqual(rc, 0)
        self.assertIn("games=3/3", marker_line(out))

    def test_the_marker_is_the_LAST_line(self):
        """A reader tails the log. Anything after the marker invites the question
        of whether the run kept going."""
        def main():
            print("the report")
            print("wrote out.json")

        _, out, _ = run(main)
        self.assertTrue(out.strip().splitlines()[-1].startswith(MARKER))

    def test_a_crash_still_writes_one_and_reports_the_partial_yield(self):
        """The case the wrapper echo was supposed to cover and did not: a run that
        died at hour four still landed games, and the reader needs the count."""
        state = RunState()

        def main():
            state.requested = 20
            state.landed = 17
            raise RuntimeError("the GPU went away")

        rc, out, err = run(main, state)
        self.assertEqual(rc, 1)
        self.assertIn("games=17/20", marker_line(out))
        self.assertIn("the GPU went away", err)

    def test_a_ctrl_c_is_130_and_not_mistaken_for_a_clean_exit(self):
        def main():
            raise KeyboardInterrupt

        rc, out, _ = run(main)
        self.assertEqual(rc, 130)
        self.assertIn(f"{MARKER}130", marker_line(out))

    def test_an_int_exit_code_is_carried_through(self):
        def main():
            raise SystemExit(3)

        rc, out, _ = run(main)
        self.assertEqual(rc, 3)
        self.assertIn(f"{MARKER}3", marker_line(out))

    def test_sys_exit_with_a_MESSAGE_still_prints_the_message(self):
        """``sys.exit("...")`` is how the driver refuses a bad argument, and the
        interpreter prints it only because nobody caught it. We catch it."""
        def main():
            raise SystemExit("--arm llm needs --backend")

        rc, out, err = run(main)
        self.assertEqual(rc, 1)
        self.assertIn("--arm llm needs --backend", err)
        self.assertIn(f"{MARKER}1", marker_line(out))

    def test_an_argparse_exit_0_is_not_reported_as_a_failure(self):
        def main():
            raise SystemExit(None)

        rc, out, _ = run(main)
        self.assertEqual(rc, 0)
        self.assertIn(f"{MARKER}0", marker_line(out))


class TestClaimingTheRecordPaths(unittest.TestCase):
    """A run's claim on the two files it is about to write.

    `land()` appends the JSONL and the summary is written `"w"`, so a second run
    onto an occupied path stacked a block into one file and replaced the other:
    the pair then described different populations with nothing raising. Three
    records reached that state (`cl-heuristic`, `-pack`, `-village`: 3000 lines
    for 1000 games), and the first block of `cl-heuristic.json.jsonl` is a stale
    play of the same seeds at 71.55% pack wins against the published 56.09%, which
    a naive read blends to about 61% - plausible, and five points wrong.

    The claim is made once, before the first game, and it REFUSES rather than
    truncating. Deleting the older run's records to make room is the operator's
    call, not the launcher's.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.out = os.path.join(self.dir, "arm", "run.json")

    def test_a_fresh_path_is_claimed_and_reads_as_the_convention(self):
        self.assertEqual(claim_record(self.out), record_paths(self.out))

    def test_an_occupied_SUMMARY_path_is_refused(self):
        os.makedirs(os.path.dirname(self.out))
        open(self.out, "w").close()

        with self.assertRaises(SystemExit) as caught:
            claim_record(self.out)
        self.assertIn(self.out, str(caught.exception))

    def test_an_occupied_JSONL_path_is_refused_with_NO_summary_beside_it(self):
        """The shape a killed run leaves: games on disk, no summary written. It is
        also the dangerous one - the next run appends to those games and the
        summary it finally writes counts only its own."""
        jsonl = record_paths(self.out)[1]
        open(jsonl, "w").close()

        with self.assertRaises(SystemExit) as caught:
            claim_record(self.out)
        self.assertIn(jsonl, str(caught.exception))

    def test_the_refusal_destroys_nothing(self):
        jsonl = record_paths(self.out)[1]
        with open(jsonl, "w", encoding="utf-8") as fh:
            fh.write(LANDED_GAME)

        with self.assertRaises(SystemExit):
            claim_record(self.out)
        with open(jsonl, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), LANDED_GAME,
                             "the claim truncated the run it refused to stack "
                             "onto, which is the one outcome worse than stacking")

    def test_the_refusal_names_what_a_reader_would_have_to_do(self):
        open(record_paths(self.out)[1], "w").close()

        with self.assertRaises(SystemExit) as caught:
            claim_record(self.out)
        message = str(caught.exception)
        self.assertIn("--out", message)
        self.assertIn("stack", message)

    def test_a_claim_creates_the_directory_the_run_will_write_into(self):
        claim_record(self.out)
        self.assertTrue(os.path.isdir(os.path.dirname(self.out)))


class TestEveryDriverThatAPPENDSAlsoClaims(unittest.TestCase):
    """The ratchet, derived from the tree rather than from a list.

    Six drivers append a per-game JSONL today and a seventh is one copied `main()`
    away. A list of module names here would go stale silently, so the drivers are
    FOUND by the append itself: a module that opens the JSONL in ``"a"`` has to
    make the claim, or it is the next writer that can stack onto another run.
    """

    APPEND = 'record_paths(args.out)[1], "a"'
    CLAIM = "claim_record(args.out)"

    def drivers(self) -> dict[str, str]:
        root = pathlib.Path(__file__).resolve().parents[1] / "eval"
        sources = {path.name: path.read_text(encoding="utf-8")
                   for path in sorted(root.glob("*.py"))
                   if not path.name.startswith("test_")}
        return {name: text for name, text in sources.items()
                if self.APPEND in text}

    def test_the_drivers_are_findable_at_all(self):
        # a rename of the append idiom would empty the set above and pass every
        # case below vacuously, which is the way this guard dies quietly.
        self.assertGreaterEqual(len(self.drivers()), 6)

    def test_each_one_claims_its_record_path_before_it_plays(self):
        for name, text in self.drivers().items():
            with self.subTest(driver=name):
                self.assertIn(
                    self.CLAIM, text,
                    f"{name} appends its JSONL without claiming the path first, "
                    "so a re-run onto an occupied --out stacks its games onto "
                    "another run's")
                self.assertLess(
                    text.index(self.CLAIM), text.index("started = time.time()")
                    if "started = time.time()" in text else len(text),
                    f"{name} claims its record path after the run has started")


class TestTheMarkerReadsTheWayTheOldOnesDo(unittest.TestCase):

    def test_it_contains_the_string_the_wrapper_echoed(self):
        """`eval/runs/*.cmd` echo `DONE rc=N`, and every grep and eye trained on
        those logs looks for that. The new line has to be findable the same way."""
        self.assertIn("DONE rc=", MARKER)

    def test_a_run_that_never_reached_its_arguments_says_so(self):
        """Nothing parsed, so the denominator is unknown - and an unknown
        denominator is written as one, not as a plausible zero."""
        def main():
            raise SystemExit(2)

        _, out, _ = run(main)
        self.assertIn("games=0/?", marker_line(out))

    def test_state_from_a_previous_run_in_this_process_is_not_inherited(self):
        state = RunState(requested=20, landed=20)

        def main():
            state.requested = 5

        _, out, _ = run(main, state)
        self.assertIn("games=0/5", marker_line(out))


if __name__ == "__main__":
    unittest.main()
