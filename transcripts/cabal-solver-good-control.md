# Cabal - the solver on GOOD seats only, against the random control

Rendered 2026-09-02T04:09:00Z from untracked `eval/records/solver-good-control-solver-good.json`
and `eval/records/solver-good-control-random.json` by
`py -3 -m eval.solver_control <solver-good.json> <random.json>`. Recipe:
`eval/runs/solver-control.cmd solver-good-control 400 21000 solver-good`. CPU
only: no model, no backend, no GPU. **A control read of an instrument, not a gate
result** - no cabal gate is reopened by anything here.

## What this answers

S26 seated `SolverPolicy` on every seat and read good wins at 17.25% against
random's 34.00%, because the solver on EVIL seats votes mechanically against its
own team: every tainted team was rejected, no mission ever failed, and evil won
on the five-reject clock. That was an artefact of the seating. This arm is the
control S26's row asked for - the solver on the three good seats, the two evil
seats on the same random policy the control plays - so the good side's proved
votes are the only thing moving.

## Arm identity

400 games per arm | seeds 21000..21399, both arms, unspent anywhere in the tree |
1 discussion round | backend `none` | `--arm solver-good` vs `--arm random`.
Wall time 48 s and 30 s.

## Record rendering

~~~text
solver control read - arm solver-good vs random, seed 21000, 400 games per arm, backend none

split (solver arm)
  6360/39468 decisions proved mechanically (26.68%), 17477 deferred to random
  proved votes by role   {'seer': 3266, 'loyalist': 1306, 'watcher': 1788}  (of 16330 votes in the arm)
  fallback, solver arm   0/39468 = 0.00%
  fallback, random arm   0/25778 = 0.00%

outcome on the same seeds (the solver on GOOD seats only, evil on random - a good side against a control, on the same deals)
  good wins, solver arm  155/400 = 38.75% [34.10%, 43.61%]
  good wins, random arm  143/400 = 35.75% [31.21%, 40.56%]
  evil by path, solver   {'five_rejects': 144, 'hunt_hit': 58, 'missions_failed': 43}
  evil by path, random   {'hunt_hit': 77, 'missions_failed': 180}
  missions / fail cards  solver 1360 / 524, random 1647 / 877
  games byte-identical across arms  0/400

paired stratum - proved votes BEFORE the games diverge
  paired 473, unpaired (after divergence) 5887
  clean    n=88   solver approved 88/88, random approved 68/88 = 77.27% [67.49%, 84.78%]
  tainted  n=385  solver approved 0/385, random approved 283/385 = 73.51% [68.88%, 77.67%]
  agreement solver==random  170/473 = 35.94% [31.75%, 40.36%]
  paired votes by role      {'seer': 411, 'watcher': 60, 'loyalist': 2}
~~~

## What it reads

**The S26 artefact stops.** No evil seat proves a vote (the proved roles are
seer, watcher, loyalist only), fail cards return (524 over 1360 missions against
0 over 544 in S26), and missions fail again (43 evil wins by that path).

**Good with perfect entitled voting gains about three points over random, and
the intervals overlap.** 38.75% [34.10%, 43.61%] against 35.75% [31.21%, 40.56%]
on the same deals. A good side that rejects every tainted team it can prove
tainted and approves every clean one it can prove clean is not, at five seats
with one discussion round, a large advantage over voting at 0.7 approve.

**A second artefact takes the first one's place, and it is the rule's, not the
seating's.** 144 of evil's 245 wins on the solver-good arm come by
`five_rejects`, a path random evil never reaches (0 in the control). Three
proving good seats reject every tainted proposal; two evil seats approve it;
2/5 fails, and a run of tainted proposals hands evil the game on the clock. So
the mechanical good side converts its own certainty into the five-reject loss
whenever the proposer sequence is unlucky. That is cabal's rule doing what it
is written to do, and it caps what "good votes perfectly" can be worth on this
rung independently of any model.

**The paired stratum again selects nothing.** Random on the same boards
approved clean 77.27% and tainted 73.51%, both intervals holding the 0.7
approve rate; the pairing is the first vote round of each game, as in S26.

It says nothing about any model, about deduction, or about deception; the
solver proves from night knowledge and own role only.
