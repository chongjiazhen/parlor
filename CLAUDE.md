# parlor - Claude Code adapter

The content is not here. This file is the adapter that loads it, so that a Claude
session and a `codex`/`qwen`/`pi` worker dispatched into the same tree are working
from the same invariants rather than from two files that drift.

@AGENTS.md

@GLOSSARY.md

## What is Claude-specific, and therefore stays here

- **`CLAUDE.local.md`** (gitignored) carries the box-local layer: absolute paths,
  the untracked working-notes contract, and the one `@import` a public tree must
  not hold. A personal path never enters this file.
- **`queue.local.md`** (gitignored) is the ephemeral half of `queue.md` - launch
  times, pids, log paths, pace. It is pointed at, never `@import`ed: a queue only
  matters when picking work back up, and paying for it every turn is the failure
  it exists to prevent.
- **Commit at logical batch points without asking** - standing authorization for
  this repo, 2026-08-27. Push stays ask-first. The pre-commit gate
  (`scripts/hygiene-check.sh`) runs on every commit whoever is driving.

## Why three files

`AGENTS.md` is what must stay true, `GLOSSARY.md` is what the words mean, and this
file is the harness adapter over both. The split is by AUDIENCE, not by topic: the
first two are read by any agent in this tree and by a person, and only this one
knows what Claude Code is. If a fourth harness arrives it gets its own adapter and
the two files below it do not move.
