"""The marker has to survive the ways a twelve-hour run actually ends.

Every test here is about the same reader: someone opening a log the next morning
with no session, no process and no chain log, who has to decide whether the run
finished or was killed. `hunt20b` gave that reader a clean log with no marker.
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from core.runlog import MARKER, RunState, run_with_marker


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
