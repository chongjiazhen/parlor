# parlor - Claude Code adapter

@AGENTS.md

## Claude-specific

- **`CLAUDE.local.md`** (gitignored) carries the box-local layer: absolute paths,
  the untracked working-notes contract, and the one `@import` a public tree must
  not hold. A personal path never enters this file.
- **`queue.local.md`** (gitignored) is the ephemeral half of `queue.md` - launch
  times, pids, log paths, pace. Read it when picking work back up, or when
  anything suggests a run may still be live.
- **Commit at logical batch points without asking** - standing authorization for
  this repo, 2026-08-27. Push stays ask-first.
- **Guard or defensive branch -> `tdd` skill, test before code.** The red run
  against the missing guard is the mutation check, with no restore or bytecode
  trap; a guard test green on its first run was written after the guard and is
  the vacuous tell.
