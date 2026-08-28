"""The fixture loader's guards, and the counts it holds the fixture to.

Every raise in ``check_balance`` exists because the failure it catches is silent:
a fixture edited without a re-count produces numbers, and a wrong degenerate
baseline flatters a model with nothing in the output to say so. So each guard is
tested by breaking the fixture in exactly the way it exists to catch.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from games.durf import fixture


def _copy_fixture(tmp: Path) -> Path:
    root = tmp / "fixtures"
    shutil.copytree(fixture.FIXTURE_DIR, root)
    return root


def _edit(root: Path, mutate) -> None:
    path = root / "declarations.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data), encoding="utf-8")


class ShippedFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = fixture.load()

    def test_every_published_count_re_derives(self):
        # The README's balance section, held against the file rather than trusted.
        self.assertEqual(fixture.check_balance(self.fx), fixture.EXPECTED_BALANCE)

    def test_scorable_excludes_the_traps_and_is_the_42(self):
        self.assertEqual(len(self.fx.scorable), 42)
        self.assertEqual(len(self.fx.traps), 6)
        self.assertTrue(all(not d["refuse"] for d in self.fx.scorable))

    def test_the_referee_view_carries_the_hidden_room_contents(self):
        # Not a leak: the adjudicator IS the referee. Pinned so a later edit that
        # trims the render cannot silently change what the model was asked from.
        text = fixture.render_scenario(self.fx)
        self.assertIn("Referee only:", text)
        self.assertIn("40 GP", text)

    def test_the_render_states_every_pc_free_slot_count(self):
        # Three of the six traps turn on slot arithmetic. A render that dropped
        # slots_free would make them unanswerable and score the model for it.
        for pc in self.fx.scenario["pcs"]:
            self.assertIn(f"{pc['slots_free']} free", fixture.render_scenario(self.fx))


class BrokenFixture(unittest.TestCase):
    """Each guard, killed by the edit it exists to catch."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = _copy_fixture(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_a_moved_count_raises_and_names_both_numbers(self):
        _edit(self.root, lambda d: d["declarations"].pop())
        fx = fixture.load(self.root)
        with self.assertRaises(fixture.FixtureError) as ctx:
            fixture.check_balance(fx)
        self.assertIn("47", str(ctx.exception))
        self.assertIn("48", str(ctx.exception))

    def test_a_trap_that_stops_being_a_refusal_raises(self):
        def mutate(d):
            for decl in d["declarations"]:
                if decl["tier"] == "trap":
                    decl["refuse"] = False
                    return
        _edit(self.root, mutate)
        fx = fixture.load(self.root)
        # Hand it the file's OWN counts, so the count guard passes and the
        # structural one is the only thing left that can fire. One mutation, one
        # guard - a count check firing first would prove nothing about this one.
        with self.assertRaises(fixture.FixtureError) as ctx:
            fixture.check_balance(fx, fixture.balance(fx))
        self.assertIn("refuse and tier:trap", str(ctx.exception))

    def test_a_roll_with_no_attribute_raises(self):
        def mutate(d):
            for decl in d["declarations"]:
                if decl["roll"]:
                    decl["attribute"] = None
                    return
        _edit(self.root, mutate)
        fx = fixture.load(self.root)
        with self.assertRaises(fixture.FixtureError) as ctx:
            fixture.check_balance(fx, fixture.balance(fx))
        self.assertIn("decision 2 has nothing to score against", str(ctx.exception))

    def test_a_no_roll_that_names_an_attribute_raises(self):
        def mutate(d):
            for decl in d["declarations"]:
                if not decl["roll"]:
                    decl["attribute"] = "STR"
                    return
        _edit(self.root, mutate)
        fx = fixture.load(self.root)
        with self.assertRaises(fixture.FixtureError):
            fixture.check_balance(fx, fixture.balance(fx))

    def test_a_fixture_not_labelled_before_a_run_is_refused_at_load(self):
        _edit(self.root, lambda d: d.update(labelled_before_any_model_run=False))
        with self.assertRaises(fixture.FixtureError) as ctx:
            fixture.load(self.root)
        self.assertIn("not ground truth", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
