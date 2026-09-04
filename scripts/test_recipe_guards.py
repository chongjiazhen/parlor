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

The third guarantee is a WRITE shape rather than a name, added 2026-09-04. A
`del` is not the only way to destroy a record: `changeling-powers-pair.cmd`
lifted arm 1's records out of a worktree with `copy /y` and no existence test,
which replaces a same-named occupant without a word. The two rules above could
not see it - it deletes nothing and it tests nothing - and the docstring below
`test_an_occupied_record_path_is_refused_not_handled` said so, excusing it
because a rule wide enough to catch a `copy` would forbid READING a record.
That is true only of a rule keyed on the record NAME. Keyed on the copy-family
VERBS the excuse goes away: `findstr` and `type` read a record and are untouched,
while every command that can land bytes on a record path must refuse first.

Not measured, and the row that opened this said so: whether that recipe ever
overwrote a record. Its `cl-powers-before2` records are down and a collision
needs a re-run onto the same tag.
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

#: A command that can land bytes on a path. Verbs, not names: this is what lets
#: the rule below cover a write without forbidding `findstr` on a record.
_WRITE_VERB = re.compile(r"^\s*(copy|xcopy|robocopy|move|ren|rename)\b", re.IGNORECASE)

#: A record filename as a recipe writes it - `%TAGB%.json`, `%TAGB%.json.jsonl`.
#: The trailing assertion is what makes `%TAGB%.json.jsonl` match whole - without
#: it the walk stops at `%TAGB%.json.json` and the guard is asked for a name no
#: recipe contains, which reads as an unguarded write on a recipe that is fine.
_RECORD_TOKEN = re.compile(
    r"[^\s\"\\/]+\.json(?:\.jsonl)?(?![^\s\"\\/])", re.IGNORECASE
)


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


def test_the_record_token_spans_a_jsonl_name() -> None:
    """The rule below asks a guard for these exact strings, so pin them.

    A token that stopped one character short would ask for a name no recipe
    holds, and every guarded write would read as unguarded - a loud failure,
    but on the wrong file. This is the cheaper way to find that out.
    """
    line = 'copy /y "%B%\\eval\\records\\%TAGB%.json.jsonl" "%OUTDIR%\\" >nul'
    assert _RECORD_TOKEN.findall(line) == ["%TAGB%.json.jsonl"]
    assert _RECORD_TOKEN.findall('copy "x\\cl-rounds2.json" "y\\"') == [
        "cl-rounds2.json"
    ]


@pytest.mark.parametrize("recipe", _recipes(), ids=lambda p: p.name)
def test_a_write_onto_a_record_path_refuses_first(recipe: Path) -> None:
    """A launcher that can land bytes on a record refuses before it does.

    Keyed on the copy-family VERBS, so a recipe that READS a record is not
    covered - `changeling-powers-pair.cmd` judges arm 1 with `findstr` on the
    arm's own log two lines above the copies this catches, and that stays legal.
    What must precede the write is the same refusal every other recipe already
    makes on an occupied path: `if exist <that record> ... exit /b 1`.

    The guard is matched by the record name the write itself carries, so a
    recipe cannot satisfy this by guarding some OTHER record earlier in the file.
    """
    lines = _code_lines(recipe)
    refusing = [
        line
        for n, line in lines
        if _IF_EXIST_RECORD.search(line) and _refuses(lines, n)
    ]
    unguarded = []
    for n, line in lines:
        if not _WRITE_VERB.match(line):
            continue
        for token in _RECORD_TOKEN.findall(line):
            if not any(token.lower() in guard.lower() for guard in refusing):
                unguarded.append(f"{recipe.name}:{n}: {line.strip()}")
                break
    assert not unguarded, (
        "a launcher may not write onto a record path it has not refused - a "
        "same-named occupant cost GPU-hours and clearing it is the operator's "
        "call:\n" + "\n".join(unguarded)
    )
