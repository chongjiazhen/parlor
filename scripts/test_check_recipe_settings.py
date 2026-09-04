"""The recipe/criterion pin's own tests - written against the defect, first.

Found 2026-09-04 by running the checker over the newly merged
`changeling-briefing-arm.cmd`: `FLAG_RE`'s `(\\S+)` matches a following
`--flag`, so a valueless flag eats the next one. The cost is not the noisy
false report - it is that `re.findall` then resumes PAST the eaten flag, so the
value it carried is never checked at all. On that recipe the seed was what went
unchecked, which is the belfry live1 class the script exists to prevent.

`--no-thinking --seats` passed at the same time only because the criterion
happens to list those two adjacent in prose - a green bought by coincidence,
which is the vacuous pass the script's own docstring claims it refuses.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("check-recipe-settings.py")
_spec = importlib.util.spec_from_file_location("check_recipe_settings", SCRIPT)
crs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(crs)

REPO = Path(__file__).resolve().parent.parent


def _pair(tmp_path: Path, recipe_body: str, criterion_body: str):
    """One recipe/criterion pair on disk, named the way the real ones are."""
    recipe = tmp_path / "arm.cmd"
    recipe.write_text(recipe_body, encoding="utf-8")
    criterion = tmp_path / "criterion.md"
    criterion.write_text(criterion_body, encoding="utf-8")
    return recipe, criterion


CRITERION = (
    "## Settings - binding, from this file and nowhere else\n\n"
    "Arm: `eval.run_changeling --games 200 --arm llm --seats 5 --briefing\n"
    "--seed 5000`, driver defaults otherwise.\n"
)

BELFRY_PAIR = ("py -3 -m eval.run_belfry --games 1000 --arm random --seats 9\n"
               "py -3 -m eval.run_belfry --games 60 --arm llm --seats 9\n")
BELFRY_CRITERION = "Arm: `eval.run_belfry --games 60 --arm llm --seats 9`.\n"


class TestAValuelessFlagDoesNotEatTheNextOne:
    """The parse defect, stated as the pairs the recipe should yield."""

    def test_the_flag_after_a_valueless_one_keeps_its_own_value(self):
        pairs = dict(crs.recipe_pairs(
            'py -3 -m eval.run_changeling --games 200 --briefing --seed 5000\n'))
        assert pairs.get("seed") == "5000"

    def test_a_valueless_flag_is_never_paired_with_a_flag_as_its_value(self):
        pairs = crs.recipe_pairs(
            'py -3 -m eval.run_changeling --games 200 --briefing --seed 5000\n')
        assert not [f for f, v in pairs if v is not None and v.startswith("--")]
        assert ("briefing", None) in pairs, "the switch is still seen, alone"


class TestTheValueBehindAValuelessFlagIsStillPinned:
    """The one that matters: a wrong seed must not ride in behind a switch."""

    def test_a_disagreeing_seed_behind_a_valueless_flag_is_caught(self, tmp_path):
        recipe, criterion = _pair(
            tmp_path,
            'py -3 -m eval.run_changeling --games 200 --arm llm --seats 5 ^\n'
            '  --briefing --seed 9999\n',
            CRITERION)
        problems = crs.check(recipe, criterion)
        assert any("9999" in p for p in problems), (
            "a seed the criterion never promised must be reported")

    def test_an_agreeing_recipe_still_reports_nothing(self, tmp_path):
        recipe, criterion = _pair(
            tmp_path,
            'py -3 -m eval.run_changeling --games 200 --arm llm --seats 5 ^\n'
            '  --briefing --seed 5000\n',
            CRITERION)
        assert crs.check(recipe, criterion) == []


class TestALongerSettingCannotSatisfyAShorterOne:
    """The same sloppiness one layer down: an unbounded substring match.

    Found while fixing the swallow, not by running a recipe - `--seed 5000`
    sits inside `--seed 50000` and `--arm llm` inside `--arm llm-good`, and
    both of those are settings this repo actually runs.
    """

    def test_a_longer_seed_does_not_satisfy_a_shorter_one(self, tmp_path):
        recipe, criterion = _pair(
            tmp_path,
            'py -3 -m eval.run_changeling --seed 5000\n',
            "Arm: `eval.run_changeling --seed 50000`.\n")
        assert crs.check(recipe, criterion) != []

    def test_a_suffixed_arm_does_not_satisfy_the_bare_one(self, tmp_path):
        recipe, criterion = _pair(
            tmp_path,
            'py -3 -m eval.run_changeling --arm llm\n',
            "Arm: `eval.run_changeling --arm llm-good`.\n")
        assert crs.check(recipe, criterion) != []


class TestAValuelessFlagIsAPresenceCheck:
    """A switch the criterion never names is a disagreement in its own right."""

    def test_a_switch_absent_from_the_criterion_is_reported_by_its_own_name(
            self, tmp_path):
        recipe, criterion = _pair(
            tmp_path,
            'py -3 -m eval.run_changeling --games 200 --arm llm --seats 5 ^\n'
            '  --no-thinking --briefing --seed 5000\n',
            CRITERION)
        problems = crs.check(recipe, criterion)
        assert any("--no-thinking" in p and "--briefing" not in p
                   for p in problems), (
            "the absent switch must be named alone, not glued to the next flag")


class TestAMultiInvocationRecipeSaysNOTCHECKED:
    """The shape that cries wolf: a control arm plus a model arm plus a probe.

    Measured 2026-09-04 on four belfry recipes - every flag of every line was
    compared against a criterion stating one arm's settings, so a SCOPE LIMIT
    printed as a settings mismatch. The script already refuses to vacuous-pass a
    shape it cannot read; this is the same refusal for a shape it was reading
    wrongly. A guard that cries wolf gets ignored, which is the belfry live1
    lesson aimed back at the script written for it.
    """

    def test_two_run_invocations_report_not_checked(self, tmp_path):
        recipe, criterion = _pair(tmp_path, BELFRY_PAIR, BELFRY_CRITERION)
        assert any("NOT CHECKED" in p for p in crs.check(recipe, criterion))

    def test_it_does_not_report_them_as_disagreements(self, tmp_path):
        recipe, criterion = _pair(tmp_path, BELFRY_PAIR, BELFRY_CRITERION)
        problems = crs.check(recipe, criterion)
        assert not [p for p in problems if "not found as literal text" in p], (
            "a scope limit must not read as a settings mismatch")

    def test_a_probe_line_contributes_no_settings(self, tmp_path):
        """`probe_tier` is a gate, not the arm; its --model is not the promise."""
        recipe, criterion = _pair(
            tmp_path,
            'py -3 -m eval.probe_tier --model wrong-model --timeout 120\n'
            'py -3 -m eval.run_belfry --games 60 --arm llm --seats 9\n',
            BELFRY_CRITERION)
        assert crs.check(recipe, criterion) == []


class TestARefusalIsNotASilentPass:

    def test_a_commented_invocation_is_not_an_invocation(self, tmp_path):
        """`belfry-live2.cmd`'s only `py -3 -m eval.` text is a `rem` scoring
        hint, and the checker read its flags and reported AGREES - a recipe
        pinned to its criterion on the strength of a comment."""
        recipe, criterion = _pair(
            tmp_path,
            "rem Score it with:  py -3 -m eval.run_belfry --games 60 --arm llm\n",
            BELFRY_CRITERION)
        assert any("NOT CHECKED" in p for p in crs.check(recipe, criterion))

    def test_a_recipe_with_no_arm_invocation_is_not_checked(self, tmp_path):
        recipe, criterion = _pair(
            tmp_path, "echo nothing to run here\n", BELFRY_CRITERION)
        assert any("NOT CHECKED" in p for p in crs.check(recipe, criterion))


class TestAgainstTheRealRecipes:
    """Regression on the tree itself, in both directions."""

    def test_the_briefing_recipe_still_agrees(self):
        assert crs.check(REPO / "eval/runs/changeling-briefing-arm.cmd",
                         REPO / "docs/changeling-briefing-criterion.md") == []

    def test_the_partner_recipe_still_agrees(self):
        assert crs.check(REPO / "eval/runs/changeling-partner-arm.cmd",
                         REPO / "docs/changeling-partner-criterion.md") == []

    def test_a_belfry_recipe_reports_not_checked_rather_than_mismatches(self):
        problems = crs.check(REPO / "eval/runs/belfry-night.cmd",
                             REPO / "docs/belfry-night-coherence-criterion.md")
        assert any("NOT CHECKED" in p for p in problems)
        assert not [p for p in problems if "not found as literal text" in p]
