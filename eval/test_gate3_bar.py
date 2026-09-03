"""One bar, and a test that keeps it one.

The defect this module was cut out of was not a wrong number - both estimators
were honest - it was TWO of them, in two files, answering differently on the same
records. So the interesting test here is not the arithmetic of the clause, which
`eval/test_skin_pair_verdict.py` already pins through the tool that applies it.
It is that a second definition cannot quietly appear.
"""

from __future__ import annotations

import pathlib
import re
import unittest

from eval.gate3_bar import OWN_ARM_TOLERANCE, REFERENCE_CHANCE, own_bar

EVAL = pathlib.Path(__file__).resolve().parent


class TestTheClauseIsAppliedAsWritten(unittest.TestCase):

    def test_no_control_read_leaves_the_reference_standing(self):
        bar, note = own_bar(None)
        self.assertEqual(bar, REFERENCE_CHANCE)
        self.assertIn("reference bar stands", note)

    def test_exactly_the_tolerance_is_AGREEMENT_not_disagreement(self):
        """The criterion says "more than a point", so a point itself is inside.
        The boundary is where a rewritten clause would land first."""
        bar, note = own_bar(REFERENCE_CHANCE + OWN_ARM_TOLERANCE)
        self.assertEqual(bar, REFERENCE_CHANCE)
        self.assertIn("agrees", note)

    def test_a_hair_past_the_tolerance_makes_the_own_arm_the_bar(self):
        control = REFERENCE_CHANCE + OWN_ARM_TOLERANCE + 1e-9
        bar, note = own_bar(control)
        self.assertEqual(bar, control)
        self.assertIn("own arm is the bar", note)

    def test_the_clause_is_symmetric_a_control_BELOW_the_reference_also_binds(self):
        """Written with `abs`, and a one-sided rewrite reads plausible: a control
        that lands LOW makes the gate easier, which is the direction a reader is
        least likely to challenge."""
        control = REFERENCE_CHANCE - 0.02
        self.assertEqual(own_bar(control)[0], control)


class TestThereIsExactlyOneOfIt(unittest.TestCase):
    """The guarantee, held by a scan rather than by prose. `eval.s5_verdict`'s
    0.3595 and `eval.waker_verdict`'s 0.3014 are different bars - S2's frozen
    criterion and the waker deck's - and are not what this looks for."""

    def test_the_reference_value_is_defined_in_exactly_one_file(self):
        literal = re.compile(r"=\s*0\.3584\b")
        defining = sorted(path.name for path in EVAL.glob("*.py")
                          if not path.name.startswith("test_")
                          and literal.search(path.read_text(encoding="utf-8")))
        self.assertEqual(defining, ["gate3_bar.py"])

    def test_no_second_own_bar_function_is_defined_anywhere_in_eval(self):
        defining = sorted(path.name for path in EVAL.glob("*.py")
                          if not path.name.startswith("test_")
                          and "def own_bar(" in path.read_text(encoding="utf-8"))
        self.assertEqual(defining, ["gate3_bar.py"])


if __name__ == "__main__":
    unittest.main()
