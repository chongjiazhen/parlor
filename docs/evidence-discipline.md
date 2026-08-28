# Evidence discipline - the rules this repo learned by breaking them

Durable lessons about how parlor handles a number, a citation, a run and its own
record. They lived in `queue.md` until 2026-08-28, wrapped in the terminal
narrative of the slices that produced them; the queue keeps a pointer and the
reasoning lives here. Each one is here because it has already cost something.

The code-level invariants these serve are in `CLAUDE.md` and are not repeated here.

## Citing work nobody here has read

Three failures, found on three separate days of the same sweep, all in material
that was correctly marked unread. **The mark was right and did not help** - the
provenance has to travel with the value, not beside it.

- **An unread entry may carry a title, an identifier and one line on what the work
  is about. It may NOT carry a number.** Twice a figure rode into the notes attached
  to an entry nobody had opened, carried from a search summary, sitting next to a
  mark that correctly said "unread". A number next to a citation reads as a citation
  whatever the mark says.
- **It may not carry a DISTINCTION either**, and this is the cheaper one to miss.
  One note had the mechanism of another system right and the argument built on it
  wrong - and it tripped nothing, because there was no number attached for the rule
  above to catch. Reading the source narrowed the contrast and made it stronger.
  **Whenever the case for what parlor does rests on how somebody else's system
  works, that is a read, not an inference.**
- **A figure copied out of a source records WHOSE it is, in the same sentence.**
  Neither rule above catches the third: a headline figure had been recorded against
  the wrong subject - an agent's win rate written down as the humans'. That entry was
  honestly marked as read at abstract depth, and it had been; the error was in the
  reading, not in the depth. A bare percentage inverts silently, and this one sat
  inverted long enough to be quoted in an argument.

**Rank a reading ledger by what each item BLOCKS, not by lane.** The 2026-08-27
ledger's first ranking filed the social-deduction successors as completeness debt
gating nothing but "did you look" - while one of them carried a standing instruction
to read it in full BEFORE the S5/S6 writeups, which the ranking had quietly demoted.
Read, four of them moved something live. A ledger that ranks by lane inherits
whatever the lane was worth when it was written; re-check the ranking against the
notes' own flags before trusting it.

**Where this material lives is a separate decision** and it is in `CLAUDE.md`: the
tree describes parlor, and who else built something goes to the untracked working
notes. `CLAUDE.local.md` has the path.

## Pre-committing a statistic

**The statistic is chosen before the run or it is chosen with the numbers in
view.** This is the `hunt20b` error, and the repo has refused it three times by
name - most sharply when S1 declined to promote the better-specified binary blind
figure, which cleared zero in both runs that had it, because promoting it after
seeing that is the same error wearing a third hat.

- A pre-commitment is reproduced verbatim and never edited to agree with the
  outcome. Four on file: `docs/gate3b-verdict.md` (cabal #3b, applied),
  `docs/changeling-gate3-criterion.md` (changeling #3, applied),
  `docs/durf-gate1-criterion.md` (DURF #1, applied) and
  `docs/quorum-live1-criterion.md` (quorum's first live arm, written before any
  model played a seat and not yet applied). `docs/decisions.md` is the roll-up.
- Clause-by-clause outcomes go in the verdict, not back into the promise. Where a
  clause did not apply cleanly, record that it did not rather than smoothing it -
  both applied criteria have one such clause each.
- **Stopping when a floor happens to cross is peeking**, and pooling runs after the
  fact is the same move. `queue.md` carries the open row for the honest version:
  a group-sequential boundary computed BEFORE a campaign, which must never be
  retrofitted to records already in hand.

## Projecting a rate from one draw

**A rate whose denominator is another gate's outcome is not projectable from one
draw.** After S6's arm 1 returned 4 hunts, `queue.md` projected ~8 for the campaign
and said the gate was "on course to return not shown for reasons of denominator, not
of hunter skill". Arm 2 returned 16. The campaign returned **20 hunts, exactly the
0.50/game the power table assumed**, so the gate failed on hunter skill at a sample
the criterion called adequate - a stronger negative than the one projected. The two
arms sit four-fold apart (0.20 vs 0.80 hunts/game, evil at 85% vs 60%) for exactly
that reason. Numbers: `docs/gate3b-verdict.md`.

The same shape governs pace estimates for a run in flight, which is why
`queue.local.md` carries a band rather than a number and `queue.md` carries
neither.

## Freezing code across a campaign, and proving the freeze held

A freeze is verified, not argued. S6's freeze line named `2c0e2a3` and HEAD moved
past it during the campaign; what settled it was a **byte-identical render
comparison across the SHAs** - cabal's full render under `1984-en` at seeds 2000 and
3000, all five seats, context plus prompt, byte-identical, **with `bnw-en` as a live
control proving the comparison could see a change at all**.

Keep the method:

- A zero-line diff on `eval/` is the cheaper first check, not a substitute.
- The byte COUNT depends on how the probe concatenates seats, so compare a render
  pair against itself rather than against a remembered number.
- A comparison with no control is not evidence that nothing moved; it is evidence
  that the probe ran.

The same method answers "did this refactor touch a model-facing byte", which is the
gate on any change that claims not to be a measured one.

## Reading a run

**Judge a detached run by its own log or JSONL.** The invariant is in `CLAUDE.md`;
the two ways it has actually failed here are worth keeping:

- **A proxy reads healthy while a run sleeps.** CPU seconds, Win32 IO counters and
  exit codes each read as liveness for network-bound work three times in one
  session, and the IO-counter one killed a healthy cloud run - those counters track
  FILE io, not sockets.
- **The gate's glob has to exclude the files that never carry the marker.**
  `grep -L 'PARLOR DONE' eval/records/hunt6[ab].log` is right; `hunt6*` also matches
  `hunt6b-chain.log`, which never contains that line, so the gate would read "in
  flight" forever.
- **Probe a cloud tier with a burst, never a ping.** A key under cooldown serves the
  occasional request while failing a stream, so a single-call probe says "healthy"
  about a tier that cannot carry a run. Measured: 1/12 served on a pinned model, and
  the one success was the fastest call of the set.

## Re-reading the queue itself

**An item priced by a cost that a later decision deleted stays expensive until
someone re-reads it.** The `DEFAULT_THEME` move sat gated on "cannot land during S6"
and "re-baselines every cabal number" after S6 was called and cabal's GPU program had
stopped - at which point the re-baselining cost was zero, because there was no future
cabal run to be incomparable with. Nothing in the queue recomputes itself.

**A rule stated in two places loses to whichever copy the reader opens.** Code
invariants live in `CLAUDE.md` and nowhere else, for that reason; this file states
none of them.


## What the successors reached - moved from the queue 2026-08-28

Verbatim from `queue.md`, whose 2026-08-27 prior-work sweep produced it. The
sources are in the off-repo ledger; what is stated here is in parlor's terms.

**Three things the successors reached, and the first two are in the S6 verdict.**
Stated in parlor's own terms; the sources are in the off-repo ledger.
- **S1's capability tell has been independently reproduced elsewhere** - a
  different game, a different model family, one agent scaled down across three
  sizes, win rate falling monotonically with parameters. parlor measured identical
  prompts at -0.2% on a 12B against +66% on 120B-class and drew the conclusion
  alone. It is no longer alone, and that is the argument for reporting gates #2 and
  #3 as dated snapshots rather than as parlor's result.
- **The nearest outside baseline on this task does not cover gate #3b.** It drops
  the role the hunter hunts, on purpose, to study detecting deception rather than
  producing it - so there is no hunt in it at all. The honest version is **3a
  only**, not the wider claim the ledger first recorded.
- **A fourth precedent for the `--notebook` null, and the oldest of them** - a 2024
  game-theoretic evaluation reporting that step-by-step and tree-search scaffolds
  do not reliably help. That prediction now rests on four results across two years.
- **One thing NOT to quote against it**: a large multi-round result shows memory
  producing real effects, but its memory persists ACROSS games where `--notebook`
  is per-seat memory WITHIN one. Different lever, different timescale; it neither
  supports nor refutes the null.
