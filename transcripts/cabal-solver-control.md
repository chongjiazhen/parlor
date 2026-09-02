# Cabal - the solver seat against the random control, S26

Rendered 2026-09-02T02:19:43+00:00 from untracked `eval/records/solver-control-solver.json`
and `eval/records/solver-control-random.json` by
`py -3 -m eval.solver_control <solver.json> <random.json>`. Recipe:
`eval/runs/solver-control.cmd solver-control 400 20000`. CPU only: no model, no
backend, no GPU. **A control read of an instrument, not a gate result** - no cabal
gate is reopened by anything here.

## What this answers

`SolverPolicy` acts only on a VOTE it can prove from the seat's entitled evidence
and hands every other decision to the same random fallback the control arm plays.
Those deferred draws routed around `LLMPolicy`'s counter, so `--arm solver`
reported `0.00%` fell back over decisions most of which the random policy played,
while the report called the arm "played at random". Both were true of different
parts of the arm and neither was counted. The split is counted now, per decision
(`Decision.solver`) and per game (`solver_mechanical` / `solver_deferred`), and this
is the first read taken with it.

## Arm identity

400 games per arm | seeds 20000..20399, both arms | 1 discussion round | backend
`none` | `--arm solver` on every seat vs `--arm random` on every seat. The seed
range was unspent anywhere in the tree; the pilot that sized N ran at 19000 so the
read's own seeds stayed unseen until the launch.

**N was sized from a count, not asserted.** The pilot (20 games) paired 61 proved
votes, ~3 per game and ~1.5 per clean/tainted cell, so 400 games was chosen to put
several hundred votes in each cell. It landed 240 clean / 1034 tainted: the clean
cell is the thin one, at ±5.6% Wilson half-width, and every interval below is
printed at its own n.

## Record rendering

~~~text
split (solver arm)
  10085/32586 decisions proved mechanically (30.95%), 22501 deferred to random
  proved votes by role   seer 2843, hunter 2843, mimic 2843, watcher 1032, loyalist 524
                         (of 14215 votes in the arm)
  fallback, solver arm   0/32586 = 0.00%
  fallback, random arm   0/26211 = 0.00%

outcome on the same seeds (NOT a gate: the solver sits on every seat)
  good wins, solver arm  69/400 = 17.25% [13.86%, 21.26%]
  good wins, random arm  136/400 = 34.00% [29.53%, 38.77%]
  evil by path, solver   five_rejects 295, hunt_hit 36, missions_failed 0
  evil by path, random   missions_failed 189, hunt_hit 75, five_rejects 0
  missions / fail cards  solver 544 / 0, random 1666 / 895
  games byte-identical across arms  0/400

paired stratum - proved votes BEFORE the games diverge
  paired 1274, unpaired (after divergence) 8811
  clean    n=240   solver approved 240/240, random approved 173/240 = 72.08% [66.09%, 77.38%]
  tainted  n=1034  solver approved 0/1034,  random approved 697/1034 = 67.41% [64.49%, 70.20%]
  agreement solver==random  510/1274 = 40.03% [37.37%, 42.75%]
  paired votes by role      seer 400, hunter 400, mimic 400, watcher 74
~~~

## What it reads

**(a) The split.** 30.95% of the solver arm's decisions were proved; 69.05% were
the random policy's. Of the arm's 14,215 votes, 10,085 (70.9%) were proved, and
the three seats the night names in full - the seer and both evils - proved every
vote they cast (2843 each, one per vote round). The watcher proved 1032 and the
loyalist 524, both from the night and the seat's own role alone: a three-seat team
that excludes a good seat carries at least one evil at 5 seats with 2, so it is
provably tainted to that seat with no mission read. **No proved vote in this arm
came from mission arithmetic**, because the arm played 0 fail cards over 544
missions - see (c).

**(b) Fallback.** 0/32586 and 0/26211, and both zeros are expected: neither arm
calls a model, so no decision can be refused and nothing can fall back. A deferred
draw is not a fallback - nothing failed - which is why it has its own pair of
fields rather than a second meaning for `fallbacks`. The old `0.00%` was correct
and said nothing; it is now printed beside the 69.05% it was hiding.

**(c) The outcome, same seeds.** Good wins FEWER games with the solver on every
seat - 17.25% [13.86%, 21.26%] against random's 34.00% [29.53%, 38.77%], intervals
disjoint - and the path column says why. The seer and both evil seats reject every
tainted team and approve every clean one, so a tainted team can never reach 3/5
and a clean team can never miss it: no mission ever fails (0 fail cards, 0
`missions_failed`), and evil wins only on the clock (295 `five_rejects`, 73.75% of
games - at 5 seats a random three-seat proposal is clean with probability 1/10) or
at the random hunt (36 hits over 105 hunts = 34.3%, at its 1/3 chance). This is not
a good side against a control. It is one policy on every seat, evil included, and
the evil seats' proved votes are anti-evil play: the arm as built measures what the
deal's entitlement structure does when it is played against itself.

**(d) The paired stratum.** On the 1274 proved votes cast before the two games
diverged - the same deal, the same proposal, the same public record - the solver
approved 240/240 clean and 0/1034 tainted, which is the policy's definition and is
printed as a check rather than a finding. What random did on those same votes is
the instrument control: 72.08% [66.09%, 77.38%] on clean and 67.41% [64.49%, 70.20%]
on tainted, both intervals holding `RandomPolicy.approve_rate = 0.7`, so the pairing
selects nothing and the paired random votes are the control's known rate. Agreement
is 40.03%, which is what a 0.7-approve coin agrees with a deterministic voter at
when 81% of its votes are rejections. The stratum is the first vote round of each
game (seer, hunter, mimic once each, the watcher in 74 games); the other 8811
proved votes fall after the shared random stream is read at an offset and are
counted, not paired.

## The tell warning, and whether it applies

`docs/open-arms.md` warns that a deterministic policy reading the referee's own
facts can be reading its own tell - the all-heuristic hunter at 99.5% was a
deterministic hunter reading a deterministic seer's votes. **That artifact does not
reach this read's hunt figure**: the solver defers the hunt to random, and the
hunter landed 34.3% against a 1/3 chance. **It does reach everything else, in two
forms.** First, the proved votes are a deterministic function of the deal and are
cast by the evil seats too, so the outcome column is the entitlement structure
voting against itself, not deduction - and any vote-reading rule run over these
records (the heuristic, `eval.ladder`) would read a perfect tell, the same trap as
the 99.5%. Second, the instrument starves its own second input: seated on every
seat it suppresses every fail card, so the mission-arithmetic constraint never
fires and the 30.95% mechanical share is the share under a table that never
produced the evidence that constraint reads. A solver-good / random-evil arm, which
does not exist, is where both artifacts stop and the share becomes a property of
the deal plus ordinary evil play.

Gate #1 is unaffected in either direction: `evidence_from_referee` reads
`entitled_knowledge(seat)` and `public_events`, the two channels the audit covers,
and every game of both arms ran audited with no leak raised.

Recompute every figure above with `py -3 -m eval.solver_control
eval/records/solver-control-solver.json eval/records/solver-control-random.json`.
