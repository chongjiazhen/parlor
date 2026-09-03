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
  (the belfry family) - both need their own reading, not a shared regex;
- it checks presence, not absence - a criterion naming a flag the recipe omits
  is not caught here, only a value that disagrees.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SET_RE = re.compile(r'^\s*set\s+"([A-Za-z_][A-Za-z0-9_]*)=([^"]*)"', re.M)
FLAG_RE = re.compile(r'--([A-Za-z][A-Za-z0-9-]*)\s+(\S+)')
#: Flags whose value is a run-scoped path or a literal outfile, never a setting
#: a criterion states in prose - checking these would only ever produce noise.
SKIP_FLAGS = {"out", "backend", "require-served", "timeout"}


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


def recipe_pairs(text: str) -> list[tuple[str, str]]:
    """Every `--flag value` pair on a `py -3 -m eval.` invocation, substituted.

    A recipe quotes a value that can carry a space (`--model "%MODEL%"`); the
    criterion prose never does, so a quoted value would never match and the
    quotes are stripped here rather than compared.
    """
    env = {name: val for name, val in SET_RE.findall(text)}
    pairs = []
    for line in logical_lines(text):
        if "py -3 -m eval." not in line:
            continue
        for flag, raw in FLAG_RE.findall(line):
            if flag in SKIP_FLAGS:
                continue
            value = substitute(raw, env).strip('"')
            pairs.append((flag, value))
    return pairs


def check(recipe: Path, criterion: Path) -> list[str]:
    rtext = recipe.read_text(encoding="utf-8")
    # Criterion prose is hand-wrapped Markdown: "--model\nqwen..." is one
    # flag/value pair split by the wrap, not a disagreement. Collapsing every
    # whitespace run to one space is what a reader's eye already does.
    ctext = re.sub(r'\s+', ' ', criterion.read_text(encoding="utf-8"))
    pairs = recipe_pairs(rtext)
    if not pairs:
        # A recipe this parser cannot read (a loop variable, a two-invocation
        # control/model pair, a recipe that names its criterion but carries no
        # inline settings) must not report the vacuous "agrees" a 0-pair loop
        # produces for free - that is the exact green-with-nothing-behind-it
        # this repo already has a name for.
        return [f"{recipe.name}: 0 flag/value pairs extracted - unsupported "
                f"recipe shape (a loop variable or multi-invocation pair), "
                f"NOT CHECKED against {criterion.name}"]
    disagreements = []
    for flag, value in pairs:
        if f"--{flag} {value}" not in ctext:
            disagreements.append(
                f"{recipe.name}: --{flag} {value} not found as literal text "
                f"in {criterion.name}")
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
