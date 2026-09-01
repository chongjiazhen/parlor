"""`scripts/testfloor.py` is a grading instrument, so it is pinned like one.

It lives in `scripts/` because an `--accept` chain calls it by path, and its test
lives here because this is where the graded suite runs - a guard collected only by
a bare root-level pytest is a guard nobody's chain runs. Loaded by path for the
same reason: `scripts/` is not a package and must not become one.

`subprocess.run` is replaced rather than really spawning pytest. The cases are
about what the tool CONCLUDES from a return code and a listing, and a real
subprocess would buy a second per case to answer a question about neither.
"""

import importlib.util
import pathlib
import subprocess
import types
import unittest

_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "testfloor.py"
_spec = importlib.util.spec_from_file_location("testfloor", _PATH)
testfloor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(testfloor)


class _Fake:
    """Stands in for one `pytest --collect-only -q` run."""

    def __init__(self, stdout: str, returncode: int = 0):
        self.result = types.SimpleNamespace(stdout=stdout, stderr="",
                                            returncode=returncode)

    def __call__(self, *_args, **_kwargs):
        return self.result


class TestCollected(unittest.TestCase):

    def use(self, fake: _Fake):
        real = subprocess.run
        testfloor.subprocess.run = fake
        self.addCleanup(setattr, testfloor.subprocess, "run", real)

    def test_it_counts_the_node_ids_and_ignores_the_summary_line(self):
        self.use(_Fake("a.py::T::test_one\na.py::T::test_two\n\n2 tests collected\n"))
        self.assertEqual(testfloor.collected("a.py"), 2)

    def test_a_collection_ERROR_is_not_a_smaller_count(self):
        """The S36 failure. pytest interrupts collection on an import error and
        still prints the ids it reached, so a line count reads a module that never
        entered the suite as a merely shorter one, and the floor passes."""
        self.use(_Fake("a.py::T::test_one\nERROR b.py\n"
                       "!!! Interrupted: 1 error during collection !!!\n",
                       returncode=2))
        self.assertEqual(testfloor.collected("."), -1)

    def test_main_FAILS_on_a_collection_error_however_high_the_count(self):
        self.use(_Fake("x::a\nx::b\nx::c\n", returncode=2))
        self.assertEqual(testfloor.main([".", "1"]), 1)

    def test_main_passes_a_clean_count_at_its_floor(self):
        self.use(_Fake("x::a\nx::b\n"))
        self.assertEqual(testfloor.main([".", "2"]), 0)

    def test_main_fails_a_count_below_its_floor(self):
        self.use(_Fake("x::a\n"))
        self.assertEqual(testfloor.main([".", "2"]), 1)


if __name__ == "__main__":
    unittest.main()
