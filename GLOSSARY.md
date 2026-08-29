# parlor - the words, and what they mean here

A term earns a line here only when its parlor meaning **differs from the ordinary
reading**, so that an agent using the ordinary one writes something wrong and
nothing objects. A term whose meaning you would guess correctly is not in this
file, and adding it makes the file cost more than it saves.

The formal vocabulary for what a seat may know - information set, percept,
synchronous perfect recall, the chance move - is settled separately and cited by
identifier in `docs/information-model.md`.

## Measuring

- **arm** - one run of one configuration, existing to be held against another that
  differs in exactly one variable. Never "a feature" and never a branch. "Built,
  unrun" is the normal state of an arm.
- **paired arm** - two arms over identical seeds and identical deals with one
  variable moved. The only shape that licenses a before/after claim; the deals are
  confirmed identical game for game rather than assumed.
- **control** - an arm with no model in the loop, pricing what chance alone
  produces at those settings. A number without one is not a finding.
- **campaign** - a long arm at an N fixed before launch, against a criterion.
- **criterion** - the bar, its void conditions and its arithmetic, written and
  committed BEFORE the run and never edited afterwards, not even to add a pointer
  to its own verdict script (`docs/*-criterion.md`).
- **instrument** - a scorer that reads records already on disk. No GPU, re-runnable,
  and it can outrank the run it is waiting on.
- **void** - a verdict discarded because the fallback rate cleared 10%. A void run
  is a finding about the harness, not a failed run and not a result about a model.
- **fallback rate** - the share of decisions no model made legally, played at random
  instead. Ships beside every number.
- **freeze** - a declared code hold across a campaign. Verified by byte-identical
  renders across the SHAs with a live control proving the probe can see a change,
  never argued from a diff being small.
- **fossil** - a run log written before the `PARLOR DONE` marker landed (S4,
  2026-08-27, `core/runlog.py`). It reads as in-flight forever and is not.
  `queue.local.md` names them.
- **rung** - one game on the ladder, ordered by how much JUDGMENT the referee needs.
  Not a difficulty level and not a version: a rung that adds rules without adding
  discretion is a lateral move and does not get built.
- **slice** - one session's worth of work, `S<n>`. The numbers are IDs, not
  positions; live rows cite slices by name, so they are never renumbered.

## The gates

Historical numbering. The letters are separate verdicts, not revisions of one.

- **gate #1 - no leak.** The only gate that measures *parlor* rather than whichever
  model was armed. Executable, default-on, and it raises.
- **gate #2 - deception.** Evil wins a non-trivial share by play. Conditional on
  gate #3, which is measured: against good seats voting at chance, evil already
  wins ~65% with no deception in the loop.
- **gate #3 - deduction.** Blind seats prefer clean teams to tainted ones.
  **#3a is RETIRED** (S1, on arithmetic); **#3b is NOT SHOWN** (S6). Neither is
  reopened by anything in the queue.

## The table

- **the ask** - the payload sent to one seat for one decision. Incremental by
  design: a rule reaches a seat at the phase where it is actionable and not before.
  Distinct from **the view**, which is what that seat can see (`SeatView`).
- **channel** - the two public streams the referee keeps, and the line between them
  is load-bearing: `("event", ...)` is referee-written and audited, because a
  referee naming a role is a leak; `("speech:<seat>", ...)` is player-written and
  not audited, because a claim about a role is a move whether or not it is true.
- **think / say / note** - the fields of a player's JSON envelope. `think` is read
  for the log and dropped, `say` reaches the table, `note` returns to its own seat
  and no other (under `--notebook`). Only `say` is a move.
- **leak** - a referee byte in a seat's context that the seat is not entitled to.
  Caught by naive substring match, deliberately: a colliding term gets renamed
  rather than the matcher made clever.
- **entitlement** - whether a seat may know a fact, and in quorum also *at what
  point*, since the object can be created in play rather than dealt.
- **skin / theme** - the vocabulary layer over one engine. A blurb is a prompt:
  editing one orphans every record taken against it, so the English faces are
  frozen at their word counts.
- **grimoire (`grim`)** - belfry's referee-side book of who holds what, including
  what each seat **registers as**, which may differ from what it is. Referee-side
  only; it is never rendered to a seat.

## The record

- **record** - raw run output in `eval/records/`. Gitignored, durable in-repo, and
  never a thing git stores.
- **transcript** - a rendered game committed to `transcripts/` because it evidences
  a claim. This is the tracked half.
- **recipe** - the launcher in `eval/runs/`. Tracked, because a run recipe that is
  not versioned cannot be reviewed after it misfires.
