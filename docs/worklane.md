# The worklane - what may be handed to a worker, and what may not

The 2026-08-29 hand-played session added eight rows to `queue.md` at once, most
of them small and mechanical. This note is how they get done in parallel by
delegated workers instead of one at a time by a session, and - the half that
actually needs writing down - which of them must not be delegated at all.

Nothing here is box configuration. Routes are named by what they promise about
the data, never by address; the launcher, its endpoints and its keys live in the
operator's harness, and a public tree has no business restating them.

## The containment is the worktree, not the route

**A worker's working directory is its entire exposure.** It runs with the
operator's privileges and reads whatever is under it, and this repo's root holds
an untracked working-notes directory that the tracked tree deliberately does not
describe. Dispatching from the repo root puts that directory inside a worker's
reach, and on a logged route inside a third party's.

So every slot gets its own `git worktree`, and that is the whole mechanism: a
worktree materialises **tracked files only**, so the untracked notes and both
box-local files are simply absent from it. Verified 2026-08-29 rather than
assumed - a probe worktree was checked for the notes directory (absent) and then
mutated to confirm that its tests import ITS tree and not the editable install
pointing at the primary checkout (they do: the mutated constant was the one the
test read). One worktree per slot also means two workers cannot collide in one
index, which is the second reason to prefer it over a bare clone.

That control turned up one small finding worth its own line: the mutant SURVIVED
`core/test_console.py`, because three of that file's assertions compare a value
against the very constant that produced it. They cannot fail on its value. Not a
queue row on its own - noted here so the next person to read those assertions
knows they are decorative.

## The route is chosen on data residency, not on job size

The tempting split is small jobs to the local model, larger ones to the hosted
tier. It is the wrong axis, and it costs on both ends.

- **The tracked tree is already public.** Every byte a worker sees in a worktree
  is on `origin/main`. A hosted tier that logs and trains on its prompts is
  therefore taking nothing it could not clone, which is what makes the wide
  free-model tier usable here at all - and that argument is void the moment a
  slot's cwd is the repo root instead of a worktree. The containment above is
  what buys the route, so the two decisions are one decision.
- **The local route is the GPU**, the same card every eval run needs, and it
  serves one model serially. So a local-route worker does not merely queue behind
  a run in flight - it competes with it, and the run is the thing with a
  measurement attached. **No local-route worker while an arm is running.** When
  the card is free the local route is the right home for anything that must not
  leave the box, which for this repo is a short list: nothing in the tracked tree
  qualifies, and everything that does is off-repo and undelegatable anyway.

## What must not be delegated

The rule is not difficulty. It is whether acceptance can be a command.

- **Anything model-facing.** A string a seat reads is a measured variable here;
  editing one re-baselines every number recorded under it. A worker graded by
  `pytest` will happily make a test pass with wording nobody would have chosen,
  and the cost lands on the next campaign rather than in the diff. The wording is
  authored in-session, and only its application is delegable.
- **Anything that decides what a number means** - a scorer's definition, a
  criterion, a denominator, a re-score of existing records. These have no
  mechanical accept: the tests pass either way and the error is in the claim.
- **Anything touching the off-repo notes**, which by construction a worker cannot
  see anyway. That is the design working, not an obstacle to route around.

Everything else in the 2026-08-29 block is delegable: an additive record field, a
console line, a flag that parses one more value, a test-collection gap. Each
carries a real acceptance command, which is what makes review cheap enough that
delegating is worth the round trip.

## The batch

Plans are written in the launcher's own sprint-plan format - one `### Slot`
block per unit, an acceptance command per slot, a worktree per slot - rather than
in a shape invented here. Every slot states the constraint that would make a
plausible-looking diff wrong: the payload must not change, or the seed invariant
must hold, or an added field must be optional so the records already on disk stay
readable.

Three slots first, not eight. A batch that lands is worth more than a batch that
needs rework, and the loop itself - dispatch, launcher-run acceptance, verdict -
is unproven in this repo until one batch has been through it.
