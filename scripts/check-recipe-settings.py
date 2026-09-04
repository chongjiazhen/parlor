"""Pin a `.cmd` recipe's actual flags to its frozen criterion, by reading both.

`eval/test_partner_verdict.py::TestSettingsPin.test_the_expected_block_agrees_
with_the_frozen_criterion` pins the VERDICT TOOL's constants to the criterion
file. Nothing pins the RECIPE - the thing that actually spends the card - to
anything, and belfry live1 is what that gap costs: 11.5 h of GPU that ran at
temperature 0.8 with `--no-thinking` against a criterion promising 60 games at
0.0 without it, because the queue row named flags and nobody opened the
criterion (`AGENTS.md`). This is that check, standalone so it needs no pytest
run - the suite ban binds independently of this.

Usage:  py -3 scripts/check-recipe-settings.py <recipe.cmd> <criterion.md> [...]

Exits 1 and prints every disagreement if any flag/value pair the recipe would
actually pass to `py -3 -m eval.*` is not present as `--flag value` literal
text in the criterion. Exits 0 (and prints nothing) if every pair agrees.

**What this does NOT do**, on purpose - least code for what tonight needs:
- it does not discover a recipe's criterion from a comment; the pairing is
  given on the command line, because the comment phrasing varies ("Bound by",
  "EXACTLY as ... promised it", "THE CRITERION IS") and guessing wrong would
  silently check nothing;
- it does not follow a `for %%T in (...)` loop variable (`changeling-skin-
  pair.cmd`) or a two-invocation control/model pair with different game counts
  (the belfry family) - both need their own reading, not a shared regex. **Both
  now report NOT CHECKED** rather than a disagreement: until 2026-09-04 the
  multi-invocation shape compared every line's flags against a criterion stating
  one arm's, so a scope limit printed as a settings mismatch on four belfry
  recipes, and a guard that cries wolf gets ignored;
- it reads only `eval.run_*` invocations, so a `probe_tier` gate line and a
  verdict tool contribute nothing - the criterion describes the ARM;
- it checks presence, not absence - a criterion naming a flag the recipe omits
  is not caught here, only a value that disagrees.

A VALUELESS switch (`--briefing`, `--no-thinking`) is a presence check: the
criterion must name the flag, and there is no value to compare. Both halves are
bounded on the right, so a longer setting cannot satisfy a shorter one
(`--seed 5000` must not be answered by `--seed 50000`). Tests, and the defect
that bought them, are `scripts/test_check_recipe_settings.py`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SET_RE = re.compile(r'^\s*set\s+"([A-Za-z_][A-Za-z0-9_]*)=([^"]*)"', re.M)
#: The value group is OPTIONAL and refuses a `--`-leading token, because a
#: valueless switch (`--briefing`, `--no-thinking`) is followed by the next flag
#: rather than by a value. A `(\S+)` that ate it did two things, and the loud one
#: was the harmless one: it reported `--briefing --seed` as a disagreement, and
#: `findall` then resumed PAST `--seed`, so the seed was never checked at all.
FLAG_RE = re.compile(r'--([A-Za-z][A-Za-z0-9-]*)(?:\s+(?!--)(\S+))?')
#: Flags whose value is a run-scoped path or a literal outfile, never a setting
#: a criterion states in prose - checking these would only ever produce noise.
SKIP_FLAGS = {"out", "backend", "require-served", "timeout"}
#: A recipe launches several `eval.` modules and only one of them is the ARM the
#: criterion describes. `probe_tier` is a gate whose `--model` is not the
#: promise; a verdict tool reads the record afterwards. Matching on `run_` keeps
#: the criterion's subject and drops the scaffolding around it.
INVOCATION_RE = re.compile(r"py -3 -m eval\.([A-Za-z_][A-Za-z0-9_]*)")


def substitute(value: str, env: dict[str, str]) -> str:
    """One pass of `%NAME%` substitution. Recipes here nest one level deep."""
    return re.sub(r'%([A-Za-z_][A-Za-z0-9_]*)%',
                  lambda m: env.get(m.group(1), m.group(0)), value)


def logical_lines(text: str) -> list[str]:
    """Join a batch file's `^` line continuations into one logical line each.

    `py -3 -m eval.run_changeling --games 1000 ^` and the `--seed %SEED%` that
    actually carries the setting live on separate physical lines; a per-line
    scan for `py -3 -m eval.` sees the first and never the second.
    """
    out, buf = [], ""
    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped.endswith("^"):
            buf += stripped[:-1] + " "
        else:
            out.append(buf + line)
            buf = ""
    if buf:
        out.append(buf)
    return out


def arm_invocations(text: str) -> list[str]:
    """The logical lines that launch a RUN module, one per arm the recipe runs."""
    out = []
    for line in logical_lines(text):
        # A `rem` line is prose. `belfry-live2.cmd` carries its scoring command
        # in one, and reading it made the checker report AGREES for a recipe
        # whose arm it had never seen (2026-09-04).
        if line.lstrip().lower().startswith("rem "):
            continue
        m = INVOCATION_RE.search(line)
        if m and m.group(1).startswith("run_"):
            out.append(line)
    return out


def recipe_pairs(text: str) -> list[tuple[str, str]]:
    """Every `--flag value` pair on a `py -3 -m eval.` invocation, substituted.

    A recipe quotes a value that can carry a space (`--model "%MODEL%"`); the
    criterion prose never does, so a quoted value would never match and the
    quotes are stripped here rather than compared.
    """
    env = {name: val for name, val in SET_RE.findall(text)}
    pairs = []
    for line in arm_invocations(text):
        for flag, raw in FLAG_RE.findall(line):
            if flag in SKIP_FLAGS:
                continue
            # `raw` is "" for a switch: no value to substitute, and the pair
            # becomes a presence check rather than a value comparison.
            value = substitute(raw, env).strip('"') if raw else None
            pairs.append((flag, value))
    return pairs


def mentions(ctext: str, flag: str, value: str | None) -> bool:
    """Is this flag - with its value, or alone - literal text in the criterion?

    Bounded on the right, because an unbounded substring lets a LONGER setting
    satisfy a shorter one: `--seed 5000` sits inside `--seed 50000`, and
    `--arm llm` inside `--arm llm-good`. Both are settings this repo actually
    runs, and either false pass is the same silent card-spend the script exists
    to stop.
    """
    literal = f"--{flag}" if value is None else f"--{flag} {value}"
    return re.search(re.escape(literal) + r'(?![A-Za-z0-9-])', ctext) is not None


def check(recipe: Path, criterion: Path) -> list[str]:
    rtext = recipe.read_text(encoding="utf-8")
    # Criterion prose is hand-wrapped Markdown: "--model\nqwen..." is one
    # flag/value pair split by the wrap, not a disagreement. Collapsing every
    # whitespace run to one space is what a reader's eye already does.
    ctext = re.sub(r'\s+', ' ', criterion.read_text(encoding="utf-8"))
    arms = arm_invocations(rtext)
    pairs = recipe_pairs(rtext)
    if not pairs:
        # A recipe this parser cannot read (a loop variable, a recipe that names
        # its criterion but carries no inline settings) must not report the
        # vacuous "agrees" a 0-pair loop produces for free - that is the exact
        # green-with-nothing-behind-it this repo already has a name for.
        return [f"{recipe.name}: 0 flag/value pairs extracted - unsupported "
                f"recipe shape (a loop variable, or no arm invocation), "
                f"NOT CHECKED against {criterion.name}"]
    missing = [f"--{flag}" if value is None else f"--{flag} {value}"
               for flag, value in pairs if not mentions(ctext, flag, value)]
    disagreements = [f"{recipe.name}: {lit} not found as literal text "
                     f"in {criterion.name}" for lit in missing]
    if missing and len(arms) > 1:
        # A recipe running a control arm AND a model arm carries two settings
        # blocks on purpose. When the criterion states BOTH - as the partner
        # criterion does - every pair matches and the check is real, so that
        # case is kept. When something does not match, this file cannot tell a
        # genuine mismatch from a control the criterion never stated, and on
        # four belfry recipes it called the second the first (2026-09-04). An
        # ambiguous answer is reported as ambiguous.
        return [f"{recipe.name}: {len(arms)} arm invocations and "
                f"{len(missing)} flag(s) {criterion.name} does not state - a "
                f"control/model pair this file cannot tell apart, so NOT "
                f"CHECKED. Read these by hand: " + ", ".join(missing)]
    return disagreements


def main(argv: list[str]) -> int:
    if len(argv) < 2 or len(argv) % 2:
        print(__doc__)
        return 2
    problems = []
    for i in range(0, len(argv), 2):
        problems += check(Path(argv[i]), Path(argv[i + 1]))
    if problems:
        for p in problems:
            print(p)
        return 1
    print(f"agrees: {len(argv) // 2} recipe/criterion pair(s), "
          f"no disagreement found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
