"""No launcher in `eval/runs/` may destroy a record.

Written against the defect, first. Five recipes - `belfry-live1`, `belfry-live2`,
`durf-fixture`, `durf-session`, `quorum-live4` - carried
`if exist ...json.jsonl del ...json.jsonl` against the append hazard, while the
other nine refuse with `exit /b 1`. Two things make the `del` wrong rather than
merely inconsistent:

* The hazard it was written for now lives in the writer. `core.runlog
  .claim_record` refuses when EITHER output path exists, made once before the
  first game, and its own docstring says the recipes' line is no longer what
  holds.
* It leaves a half-state. The `del` removes the per-game JSONL and leaves the
  summary, so `claim_record` refuses on the summary anyway - the record is
  destroyed and the run does not even start. A recipe cannot know whether the
  occupant cost GPU-hours, which is why clearing it is the operator's call.

Not measured, and it is what the `del` was written for: whether any of the five
was ever re-run onto its own path. The guarantee here is about what a launcher
may do, not about what one did.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RUNS = Path(__file__).resolve().parent.parent / "eval" / "runs"

#: `del` naming a record path, on a line that is not batch prose.
_DEL_RECORD = re.compile(r"\bdel\b[^\n]*\.json", re.IGNORECASE)

#: An existence test on a record path - the guard shape, whatever it then does.
_IF_EXIST_RECORD = re.compile(r"\bif\s+exist\b[^\n]*\.json", re.IGNORECASE)


def _recipes() -> list[Path]:
    found = sorted(RUNS.glob("*.cmd"))
    assert found, f"no recipes under {RUNS} - the scan would pass vacuously"
    return found


def _code_lines(recipe: Path) -> list[tuple[int, str]]:
    """Numbered lines that are batch CODE - `rem` prose is not a guarantee."""
    out = []
    for n, line in enumerate(recipe.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().lower().startswith("rem"):
            continue
        out.append((n, line))
    return out


def _refuses(lines: list[tuple[int, str]], start: int) -> bool:
    """Does the guard opening at line `start` end the run?

    Batch writes this two ways and both are in the tree: `if exist X exit /b 1`
    on one line, and a parenthesised block that echoes before it exits. A check
    that read only the opening line would call the block shape unguarded, which
    is a false alarm on nine recipes that are already correct.
    """
    rest = [line for n, line in lines if n >= start]
    opening = rest[0]
    if "exit /b" in opening.lower():
        return True
    if not opening.rstrip().endswith("("):
        return False
    for line in rest[1:]:
        if line.strip() == ")":
            return False
        if "exit /b" in line.lower():
            return True
    return False


@pytest.mark.parametrize("recipe", _recipes(), ids=lambda p: p.name)
def test_no_recipe_deletes_a_record(recipe: Path) -> None:
    offenders = [
        f"{recipe.name}:{n}: {line.strip()}"
        for n, line in _code_lines(recipe)
        if _DEL_RECORD.search(line)
    ]
    assert not offenders, (
        "a launcher may not destroy a record - refuse with `exit /b 1` and let "
        "clearing it be the operator's call:\n" + "\n".join(offenders)
    )


@pytest.mark.parametrize("recipe", _recipes(), ids=lambda p: p.name)
def test_an_occupied_record_path_is_refused_not_handled(recipe: Path) -> None:
    """Finding a record already there ends the run; it does not clear it.

    Scoped to `if exist` on a record path, which is the guard shape. A recipe
    that READS or copies a record is doing something else and is not covered -
    `changeling-powers-pair.cmd` lifts a JSONL out of a worktree, and a rule
    written wide enough to catch that would forbid reading a record at all.
    """
    lines = _code_lines(recipe)
    guards = [(n, line) for n, line in lines if _IF_EXIST_RECORD.search(line)]
    if not guards:
        pytest.skip("guards no record path")
    handled = [
        f"{recipe.name}:{n}: {line.strip()}"
        for n, line in guards
        if not _refuses(lines, n)
    ]
    assert not handled, (
        "an occupied record path is refused, never cleared:\n" + "\n".join(handled)
    )
