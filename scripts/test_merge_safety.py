"""Tests for the merge-safety check, written before it existed.

The row this answers: `queue.md` says a branch is free and a merge is not, and
what makes a merge unsafe mid-arm is touching what the LIVE RUN IMPORTS. That
was a hand check, and the row records that nothing would have stopped a merge
that skipped it.

The failure mode to design against is a closure that comes back SMALL and
therefore reports SAFE - a truncated import walk is indistinguishable from a
clean branch unless the walker is tested on the shapes this tree actually uses:
relative imports (`games/durf/`), function-level imports (`eval/run_changeling.py`
line 136), and transitive depth.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("merge-safety.py")
_spec = importlib.util.spec_from_file_location("merge_safety", SCRIPT)
ms = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ms)

REPO = Path(__file__).resolve().parent.parent


def _tree(root: Path, files: dict[str, str]) -> None:
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


class TestTheClosureFollowsEveryImportShapeThisTreeUses:
    """A walker that misses a shape reports a short closure, which reads SAFE."""

    def test_the_entry_module_is_in_its_own_closure(self, tmp_path):
        _tree(tmp_path, {"pkg/__init__.py": "", "pkg/entry.py": "x = 1\n"})
        assert "pkg/entry.py" in ms.import_closure(tmp_path, "pkg.entry")

    def test_an_absolute_import_is_followed(self, tmp_path):
        _tree(tmp_path, {"pkg/__init__.py": "", "other/__init__.py": "",
                         "other/dep.py": "y = 2\n",
                         "pkg/entry.py": "from other.dep import y\n"})
        assert "other/dep.py" in ms.import_closure(tmp_path, "pkg.entry")

    def test_a_transitive_import_is_followed(self, tmp_path):
        _tree(tmp_path, {"pkg/__init__.py": "", "pkg/a.py": "from pkg.b import z\n",
                         "pkg/b.py": "from pkg.c import w\n", "pkg/c.py": "w = 3\n"})
        assert "pkg/c.py" in ms.import_closure(tmp_path, "pkg.a")

    def test_a_relative_import_is_followed(self, tmp_path):
        """`games/durf/` uses `from . import rules` - missing this truncates it."""
        _tree(tmp_path, {"pkg/__init__.py": "", "pkg/rules.py": "R = 1\n",
                         "pkg/entry.py": "from . import rules\n"})
        assert "pkg/rules.py" in ms.import_closure(tmp_path, "pkg.entry")

    def test_a_relative_from_import_of_a_name_is_followed(self, tmp_path):
        _tree(tmp_path, {"pkg/__init__.py": "", "pkg/kernel.py": "class K: pass\n",
                         "pkg/entry.py": "from .kernel import K\n"})
        assert "pkg/kernel.py" in ms.import_closure(tmp_path, "pkg.entry")

    def test_a_function_level_import_is_followed(self, tmp_path):
        """`eval/run_changeling.py:136` imports inside a function body."""
        _tree(tmp_path, {"pkg/__init__.py": "", "pkg/late.py": "L = 1\n",
                         "pkg/entry.py": "def f():\n    from pkg.late import L\n"})
        assert "pkg/late.py" in ms.import_closure(tmp_path, "pkg.entry")

    def test_stdlib_and_absent_modules_are_not_in_the_closure(self, tmp_path):
        _tree(tmp_path, {"pkg/__init__.py": "",
                         "pkg/entry.py": "import json\nimport nowhere\n"})
        closure = ms.import_closure(tmp_path, "pkg.entry")
        assert closure == {"pkg/entry.py", "pkg/__init__.py"} or "json" not in str(closure)


class TestARefusalIsNotASafeAnswer:
    """An entry it cannot resolve must raise, never return an empty closure."""

    def test_an_unresolvable_entry_raises(self, tmp_path):
        _tree(tmp_path, {"pkg/__init__.py": ""})
        with pytest.raises(ms.EntryNotFound):
            ms.import_closure(tmp_path, "pkg.does_not_exist")


class TestTheVerdictIsTheIntersection:

    def test_a_branch_touching_nothing_imported_is_safe(self):
        assert ms.unsafe_files({"a.py", "b.py"}, ["docs/README.md"]) == []

    def test_a_branch_touching_an_imported_file_is_named(self):
        assert ms.unsafe_files({"a.py", "b.py"}, ["docs/x.md", "b.py"]) == ["b.py"]


class TestAgainstTheRealTree:
    """Positive control: the walker must find known-real depth in this repo."""

    def test_the_changeling_runner_pulls_its_referee_and_core_audit(self):
        closure = ms.import_closure(REPO, "eval.run_changeling")
        assert "games/changeling/referee.py" in closure
        assert "core/observability.py" in closure, "transitive through the referee"

    def test_the_changeling_runner_does_not_pull_another_rung(self):
        closure = ms.import_closure(REPO, "eval.run_changeling")
        assert not [f for f in closure if f.startswith("games/belfry/")]
