# Group-sequential criterion - the template, and one worked instance (2026-09-02)

**This is a DESIGN, not a promise.** It is S25's answer to the open row in
`docs/open-arms.md` §Group-sequential design: how the next campaign can look at
its record before the end and stop early without the look being a peek. The
arithmetic is `eval/sequential.py`, pinned by `eval/test_sequential.py`. Nothing
in this file binds a run. **The binding document for a campaign is its own
`docs/<rung>-<arm>-criterion.md`**, which copies the worked instance below with
its numbers filled in, is committed before launch, and is never edited after.

Every number in this file was printed by `py -3 -m eval.sequential` on the date
above and is pasted, not typed.

## The pattern, named

**Group-sequential design with a Lan-DeMets alpha-spending function.** A fixed-N
test spends its whole alpha at one look. A sequential design declares K looks at
information fractions t_1 < ... < t_K = 1 and a spending function a(t) that says
how much of alpha may have been used by information t; the boundary at each look
is solved so that the chance of a false positive across ALL the looks is still
alpha. Stopping when a floor happens to cross spends alpha it never declared;
stopping at a declared look on a declared boundary spends exactly what was priced.

- **O'Brien-Fleming-type spending is the default** (`--spend obf`). It spends
  almost nothing early - 0.0015 of 0.025 at half information - so an early stop
  needs overwhelming evidence, and the final boundary sits within 0.01 of the
  single-look 1.960. On a campaign whose interim look is a cheap check for a
  runaway result, this is the right shape: an early stop is a windfall, and a
  run that goes the distance pays almost nothing for having looked.
- **Pocock-type spending is the named alternative** (`--spend pocock`). It
  spends nearly evenly, so early stops are easier and the final boundary is
  materially higher (2.201 against 1.960 at two looks). Pick it only when an
  early stop is the POINT of the design, and pay for it at the end.

The test is one-sided on a binomial proportion against a pre-committed chance
bar: exactly the changeling gate #3 shape, blind villager accuracy against a
derived chance bar. Its single-look form is the repo's existing gate - the count
whose Wilson 95% floor clears the bar is the count whose score statistic reaches
1.960, and `min_hits` at z=1.960 reproduces it (tested).

## The template - what a sequential criterion must declare

A criterion adopting this design adds one section, and every item in it is
written before launch:

1. **The unit.** The thing the criterion COUNTS, never the game. For gate #3 it
   is a blind villager vote; a look happens when the record holds a declared
   number of them, whatever game that falls in. The planned N is the criterion's
   power figure in that unit.
2. **The bar** p0, the chance rate the unit is tested against, measured the way
   the criterion already measures it.
3. **Alpha**, one-sided. 0.025 matches the 95% Wilson floor the repo has used
   throughout, so a one-look design is the existing gate and a K-look design is
   a strict superset of it.
4. **The looks**, as information fractions, and the spending function. The
   command that prints the table, and the table itself, pasted.
5. **What fixes the information fraction: the record's unit count at the look.**
   The interim look is taken when the record's blind-vote count REACHES the
   declared total (136 below), read off the JSONL - not at game 100, which is
   the same count only in expectation. `look` refuses any other total.
6. **The final look is at the run's planned end, at whatever total the record
   holds.** A campaign is priced in votes and run in games, so it will not land
   on the planned N. `refit_final` keeps every interim boundary exactly as
   declared and re-solves only the final z at the actual total, spending the
   alpha that remains; the criterion says this is how the final look is read.
   A run that stops short of its planned games has NO final look and is a
   short run, as before.
7. **The stopping rule.** CROSSED at an interim look ends the campaign with the
   gate HOLDING; CONTINUE means the run goes on with no verdict and no
   figure quoted. The interim hit count is printed by the verdict module and by
   nothing else.
8. **What is NOT sequential.** Every other reading on the record - the paired
   control, the observations, gate #2 - is read at the end as it always was. The
   design covers the gate statistic and only that.

**A look at any other point is a peek, and it voids the sequential read.** Not
"weakens": the boundary was solved for the declared looks, and a look at 100
votes is alpha the table did not price. If an undeclared look happens, the
campaign is read as a fixed-N test at its final total, the look is disclosed the
way S19's was, and the sequential machinery is not used on that record. The
guard is executable: `look` raises `UndeclaredLook` on any undeclared total,
and that refusal was written test-first.

**The S19 record is never re-read as sequential.** `eval/records/waker1.json`
was run under `docs/changeling-waker-criterion.md`, a fixed-N criterion that
spends no alpha at an interim, and one interim look at game 50 is disclosed in
`docs/measurements.md`. Computing a boundary now and asking whether that look
would have crossed it is exactly the retrofit `docs/open-arms.md` forbids - the
boundary would be chosen with the numbers in view, whatever its shape. The
fixed-N read stands as the only read of that record.

## What the design costs, from the table

At full information the sequential boundary is higher than the single-look one,
because some alpha was reserved for the interim. From the tables below, at the
worked instance's N and bar:

| design | final z | final min hits (of 272) | cost vs the Wilson gate |
|---|---|---|---|
| single look (the existing gate) | 1.960 | 97 (35.66%) | - |
| OBF, looks at 0.5 / 1.0 | 1.969 | 97 (35.66%) | 0 hits; z +0.009 |
| OBF, looks at 0.5 / 0.75 / 1.0 | 2.014 | 98 (36.03%) | 1 hit (+0.37%) |
| Pocock, looks at 0.5 / 1.0 | 2.201 | 99 (36.40%) | 2 hits (+0.74%) |

So the two-look OBF design costs NOTHING at this N once the z is rounded to a
hit count - the reserved 0.0015 of alpha is smaller than one vote's worth of
boundary. That is the whole argument for it as the default: a free option on an
early stop. The three-look and Pocock shapes cost one and two votes at the end,
which is the price of looking more often or stopping more easily.

**The exact type-I error is printed beside every table and it is not 0.025.** A
hit count is an integer, so the true error of the integer boundary under the
binomial sits above or below the nominal alpha. At 272 votes and p0 = 0.3014 the
two-look boundary carries 0.0296 exact, and the single-look Wilson gate at 97/272
already carries 0.0289 - the excess is the score test on a discrete count, the
property every Wilson-floor gate in this repo has had all along, and the
sequential design adds 0.0007 to it. Read the exact figure, not the nominal.

## The worked instance - the next changeling paired campaign

The figures are the six-seat waker deck's, from `docs/changeling-waker-criterion.md`:
bar 30.14%, ~272 blind votes at 200 games, two looks at 50% and 100% information.
A criterion adopting this pastes the block below and the command that made it.

```
py -3 -m eval.sequential --n 272 --looks 0.5 1.0 --alpha 0.025 --spend obf --p0 0.3014
```

```text
group-sequential boundary - n=272 units, one-sided alpha=0.025, spending=obf, p0=0.3014
  grid: step 0.02 from -8 on the B scale, trapezoid

  look    frac   total        z  min hits  min rate  alpha spent
     1   0.500     136    2.963        57    41.91%      0.00153
     2   1.000     272    1.969        97    35.66%      0.02500

  exact binomial type-I error of this integer boundary: 0.0296 (nominal 0.025)
  single-look reference at n=272: z=1.960, min hits 97 (35.66%), exact type-I 0.0289 - the Wilson-floor gate
  cost of the design at full information: 0 more hit(s) (+0.00%); z 1.969 vs 1.960
```

Read as a criterion clause:

- **Look 1 is taken when the record holds 136 blind villager votes.** If 57 or
  more of them are correct, gate #3 HOLDS and the campaign stops; the paired
  random arm is still run to its own 136 blind votes so the own-arm clause can
  fire. Fewer than 57 is CONTINUE, and no figure from this look is quoted.
- **Look 2 is at 200 games, at the blind-vote total the record holds**, read as
  `refit_final(boundary, n_final)`. The interim look keeps z=2.963 and 57 hits
  exactly; the final z is re-solved. At three plausible landings:

  | n_final | final z | min hits | exact type-I |
  |---|---|---|---|
  | 255 | 1.967 | 92 | 0.0249 |
  | 272 | 1.969 | 97 | 0.0296 |
  | 290 | 1.970 | 103 | 0.0289 |

- **The 150-vote refusal floor still applies** to the final total; a run whose
  final blind stratum is under 150 votes is REFUSED, not failed, as before.
- **Both floors still clear at the final look.** The criterion's game bootstrap
  is unchanged and is computed at the end as it always was; the sequential
  boundary replaces the Wilson floor only, since it is the Wilson floor's
  sequential form. An interim stop is a Wilson-boundary crossing; the bootstrap
  is reported beside it at the interim, and if it does not clear the bar the
  criterion says which of the two governs. **This template's answer: both must
  clear, at the interim as at the end**, which is the clause the waker
  criterion already carries.

The three-look and Pocock tables the cost section quotes:

```text
py -3 -m eval.sequential --n 272 --looks 0.5 0.75 1.0 --alpha 0.025 --spend obf --p0 0.3014
  look    frac   total        z  min hits  min rate  alpha spent
     1   0.500     136    2.963        57    41.91%      0.00153
     2   0.750     204    2.359        77    37.75%      0.00965
     3   1.000     272    2.014        98    36.03%      0.02500
  exact binomial type-I error of this integer boundary: 0.0261 (nominal 0.025)

py -3 -m eval.sequential --n 272 --looks 0.5 1.0 --alpha 0.025 --spend pocock --p0 0.3014
  look    frac   total        z  min hits  min rate  alpha spent
     1   0.500     136    2.157        53    38.97%      0.01550
     2   1.000     272    2.201        99    36.40%      0.02500
  exact binomial type-I error of this integer boundary: 0.0278 (nominal 0.025)
```

## What the arithmetic was checked against

- **The published constants.** `classic_boundaries` solves the classic
  O'Brien-Fleming (c_k = C sqrt(K/k)) and Pocock (c_k = C) constants by the same
  recursion; at one-sided 0.025 it returns C_B = 2.797 / 3.471 / 4.049 / 4.562
  and C_P = 2.178 / 2.289 / 2.361 / 2.413 for K = 2..5, each within 0.001 of the
  standard tables (K=2 OBF: 2.797, 1.977; K=3: 3.471, 2.454, 2.004). The test
  tolerance is 0.002 in z. Halving the grid step moves every one of them by under
  1e-4, so the grid is not what limits the third decimal.
- **Total alpha under the null.** The recursion's own `_total_alpha` of each
  spending boundary returns 0.025 to 2e-5; a 20000-trial seeded simulation of the
  Gaussian sequential statistic at three OBF looks crossed 503/20000 = 2.51%
  [2.31%, 2.74%], containing 2.5%; a 20000-trial binomial simulation of the
  worked instance crossed 617/20000 = 3.08% [2.85%, 3.33%], containing the exact
  0.0296 and NOT the nominal 0.025 - which is the discreteness point above.
- **Determinism.** The same inputs produce the same table byte for byte, and the
  worked instance's totals and z values are pinned by name.

What was NOT checked: the Lan-DeMets spending boundaries against a published
table of THEIR values. They match the standard software's figures to the third
decimal from memory (two looks OBF 2.963 / 1.969; three looks 3.710 / 2.511 /
1.993), and the recursion that produces them is the one that reproduces the
classic constants, but no first-hand table was opened for them. A criterion
resting on a specific spending value should say so, or cite one.
