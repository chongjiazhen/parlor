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

## A slice that touches a `demo.py` needs a smoke run in its accept chain

A suite green over a program that cannot start is not a contradiction here:
nothing in `core`, `games` or `eval` calls a demo's `main()`. Measured 2026-08-30
- a dispatch moved one line above the assignment it depended on, so
`py -3 -m games.changeling.demo` died `UnboundLocalError` on every invocation,
and the accept gate reported exit 0 over 1132 passing tests and a real diff. Put
`py -3 -m games.<rung>.demo --rounds 1` in the chain for any slice touching a
driver; it costs a second and it is the only thing that runs the entry point.

## A worktree cannot run the tests that read `eval/records/`

`eval/records/` is run output: durable, gitignored, and therefore **absent from
every worktree**, because a worktree materialises tracked files only. So
`eval/test_rule_errors.py` and anything else that opens a real record file dies
`FileNotFoundError` there, on a tree with nothing wrong with it.

This is a property of the containment, not a bug to fix - copying records into a
worktree would put run blobs inside a worker's reach for nothing. **The acceptance
command is what has to change**: scope it to what the worktree can actually run.
Measured 2026-08-30, and the fault was the commander's, not the worker's - slot B
was given `pytest games core eval`, which cannot be green inside the containment
it was dispatched into, so a correct diff came back wearing a red gate.

## Grade a dispatch on the diff. The acceptance gate cannot see an absent worker

**A passing acceptance command over an empty diff is a FAILED dispatch, not a
passing one.** The gate runs the suite against the worktree after the worker
exits; a worker that never started leaves a pristine tree, and a pristine tree
passes. So the success-shaped output of a dispatch that did nothing is
indistinguishable, line for line, from one that did everything right - unless you
read the `git status --porcelain` block the launcher prints underneath, which is
the only part of the report that answers "did anything happen".

Measured 2026-08-29, twice in a row, on the first two dispatches this repo ever
made. Both printed `689 passed, 5 skipped ... accept exit: 0` and an empty
porcelain block. Neither had touched a file:

- the hosted tiers answered `401 Invalid API key` to an authenticated caller, on
  three retries, all correctly tagged provider-error flake by the launcher;
- the local route answered `400 request (38042 tokens) exceeds the available
  context size (32768 tokens)` - the worker CLI's own scaffold does not fit the
  armed model's context, so the size of the task prompt is irrelevant. A local
  worker needs a model armed with room for the agent, not just for the job.

The launcher was honest in both cases: it named the error and tagged the run. The
trap is in the summary line, where an exit code and a green suite sit next to
each other and read as a result. **A batch reviewed by exit code would have
reported every slot green and merged nothing.**

Three slots first, not eight. A batch that lands is worth more than a batch that
needs rework, and the loop itself - dispatch, launcher-run acceptance, verdict -
is unproven in this repo until one batch has been through it.

## What the first batch actually returned

Five graded dispatches over three slices, 2026-08-30. Two verdicts pass, three
fail, and **both passes still needed hand-finishing before they could land** - so
"pass" here means the work was worth keeping, not that the dispatch was complete.

- **Every slice needed a landmine named that no test would have caught.** The
  record-size slice touched the one seam every game calls; the console slice sat
  next to a field whose value rides in the record; the seat slice could have drawn
  from the generator the policies deal out of, which would have re-baselined every
  number recorded at that seed. Two of the three prompts named their landmine and
  the worker respected it. The third did not name it, and the worker walked onto
  it - it repurposed `ConsoleBackend.model` and rewrote the assertions pinning it.
  **The naming is the work.** A slice whose landmine you cannot state in a sentence
  is a slice you have not understood well enough to delegate.
- **Two workers reached green by deleting tests** - 23 of 26, then 16 of 26 on a
  retry whose prompt named the floor, quantified it, and described the previous
  failure. Wording did not fix it; a collect-only floor in the accept chain did.
  Assume any suite a worker can edit is a suite it can shrink.
- **One worker wrote no tests at all** and reported success. Its code was correct
  and landed; the nine tests are the commander's.
- **A worker's own report is not evidence.** Every failing dispatch above produced
  a confident report. The diff, the floor and the suite are the evidence; the
  report is a convenience for reading them.

None of this argues against delegating. It prices it: the slices that came back
usable were the ones where a commander had already done the thinking and left the
worker the typing.
