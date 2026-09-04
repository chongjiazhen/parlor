"""Is this branch safe to merge while that run is in flight?

`queue.md` says a branch is free and a merge is not. What actually makes a merge
unsafe mid-arm is touching what the LIVE RUN IMPORTS - the checkout the running
process reads from changes under it. That was a hand check, done once on
2026-09-03 and skipped by a merge on the same day; nothing in the tree would
have stopped a merge that skipped it. This is the check as a command.

    py -3 scripts/merge-safety.py <entry-module> <branch> [<branch> ...]
    py -3 scripts/merge-safety.py eval.run_changeling slice/changeling-notebook

`<entry-module>` is what the live recipe runs - `eval.run_changeling` for a
changeling arm, `eval.run_belfry` for belfry. Exit 0 when every branch named is
disjoint from that closure, 1 when any branch touches it, 2 on a usage or
resolution failure.

**A short closure reads SAFE**, which is the one way this tool can lie, so the
walk covers every import shape the tree actually uses - absolute, relative
(`games/durf/`), and function-level (`eval/run_changeling.py:136`) - and an
entry it cannot resolve RAISES rather than returning an empty set.

What it deliberately does not do: it reads the closure at the WORKING TREE's
current state, not the running process's loaded modules, which are not
observable from outside. The two differ only if the tree changed under the run,
which is the thing being prevented. Non-`.py` files a package reads at runtime
(a `RULES.md`) are reported separately rather than silently ignored.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


class EntryNotFound(Exception):
    """The entry module does not resolve to a file - never answer SAFE."""


def module_file(root: Path, dotted: str) -> Path | None:
    """`a.b.c` -> `a/b/c.py`, or `a/b/c/__init__.py`, or None."""
    parts = dotted.split(".")
    direct = root.joinpath(*parts).with_suffix(".py")
    if direct.is_file():
        return direct
    pkg = root.joinpath(*parts, "__init__.py")
    return pkg if pkg.is_file() else None


def _targets(node: ast.AST, pkg: str) -> list[str]:
    """Dotted module names one import statement could name.

    `from .kernel import load` names `pkg.kernel`; `from . import rules` names
    `pkg.rules` through its alias, not through the module field. Both shapes are
    live in `games/durf/`, and a walker that reads only `node.module` finds the
    first and silently drops the second.
    """
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    if node.level:                                   # relative
        base = pkg.rsplit(".", node.level - 1)[0] if node.level > 1 else pkg
        head = f"{base}.{node.module}" if node.module else base
    else:
        head = node.module or ""
    # `from X import Y` - Y may be a submodule or just a name; try both and let
    # module_file() decide which exists.
    return [head] + [f"{head}.{a.name}" for a in node.names]


def import_closure(root: Path, entry: str) -> set[str]:
    """Repo-relative paths of every local module reachable from `entry`."""
    start = module_file(root, entry)
    if start is None:
        raise EntryNotFound(f"{entry} does not resolve to a file under {root}")
    seen: set[str] = set()
    queue = [(entry, start)]
    while queue:
        dotted, path = queue.pop()
        rel = path.relative_to(root).as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        pkg = dotted if path.name == "__init__.py" else dotted.rsplit(".", 1)[0]
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):          # walk, not iter: line 136 is in a def
            for name in _targets(node, pkg):
                nxt = module_file(root, name)
                if nxt is not None:
                    queue.append((name, nxt))
    return seen


def unsafe_files(closure: set[str], changed: list[str]) -> list[str]:
    return sorted(set(changed) & closure)


def companions(closure: set[str], changed: list[str]) -> list[str]:
    """Changed non-.py files sitting inside a package the run imports.

    Not an import edge, so not a merge block - but `games/<rung>/RULES.md` is
    read at runtime and a reader deserves to be told, rather than have the tool
    quietly scope it out.
    """
    dirs = {p.rsplit("/", 1)[0] for p in closure if "/" in p}
    return sorted(f for f in changed
                  if not f.endswith(".py") and "/" in f
                  and f.rsplit("/", 1)[0] in dirs)


def changed_files(branch: str, base: str = "main") -> list[str]:
    out = subprocess.run(["git", "diff", "--name-only", f"{base}...{branch}"],
                         capture_output=True, text=True)
    if out.returncode:
        raise EntryNotFound(f"git diff failed for {branch}: {out.stderr.strip()}")
    return [l for l in out.stdout.splitlines() if l]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    entry, branches = argv[0], argv[1:]
    root = Path(__file__).resolve().parent.parent
    try:
        closure = import_closure(root, entry)
    except EntryNotFound as exc:
        print(f"REFUSING: {exc}")
        return 2
    print(f"{entry} imports {len(closure)} local files\n")
    blocked = False
    for branch in branches:
        try:
            changed = changed_files(branch)
        except EntryNotFound as exc:
            print(f"  {branch}: REFUSING - {exc}")
            blocked = True
            continue
        hits = unsafe_files(closure, changed)
        also = companions(closure, changed)
        if hits:
            blocked = True
            print(f"  UNSAFE  {branch} - touches {len(hits)} imported file(s):")
            for h in hits:
                print(f"            {h}")
        else:
            print(f"  safe    {branch} ({len(changed)} file(s) changed)")
        for a in also:
            print(f"            note: {a} is read at runtime, not imported")
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
