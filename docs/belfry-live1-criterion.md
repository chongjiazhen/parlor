# belfry's first live arm - the pre-committed criterion, written 2026-08-28 BEFORE the arm

**This file is the PROMISE, not the result.** It is written before any model has
played a belfry seat, and **nothing in it is edited after the arm launches** - not
the endpoint, not the bar, not N, not the void conditions. That is the whole value
of it. Same discipline as `docs/quorum-live1-criterion.md`,
`docs/changeling-gate3-criterion.md` and `docs/durf-gate1-criterion.md`, for the
same reason: a statistic chosen with the numbers in view is not a measurement, and
this repo has refused that by name twice already.

The outcome goes in `games/belfry/RULES.md`, clause by clause. The arithmetic is
`eval/belfry_live1_verdict.py`, written the same hour and pinned by its own tests,
so seeing a partial count cannot move the bar.

## The arm

**60 games, 5 seats, compact script, 1 talk round, `--arm llm`, local
`qwen36-35b-a3b-iq3`, temperature 0.0, seed 6100.** Same seeds, same table, same
script and same round count as the 200-game random control in
`docs/measurements.md` §belfry's control arm, so the policy is the one variable.

```
py -3 -m eval.run_belfry --games 60 --arm llm --seats 5 --script compact \
    --rounds 1 --backend local --model qwen36-35b-a3b-iq3 --temperature 0.0 \
    --seed 6100 --out eval/records/belfry-live1.json
```

Temperature 0.0, the same call `docs/durf-rung.md` measured and
`docs/quorum-live1-criterion.md` carried by argument: a vote is an adjudicable
decision rather than table speech, and a sampled one adds variance to the figure
this arm exists to read.

`--out` is required, not optional. The primary endpoint's interval is a bootstrap
over GAMES, and the per-game rows live only in the `.jsonl` sibling - a run
launched without `--out` cannot be scored against this criterion at all.

**N is fixed at 60 in advance and there is no stopping rule.** Reading a partial
run and stopping when it looks good is the same error as choosing the statistic
afterwards, one step earlier in the pipeline.

### What 60 games costs

The control measured **48.6 decisions per game** at this table and script
(9719 decisions over 200 games), one model call each, so the arm is **~2900
calls, serial**. Two dated per-decision figures exist for `qwen36-35b-a3b-iq3`
locally, and belfry has neither of them, so both are carried: changeling S2 ran
3000 decisions in 18250s (**6.1 s/decision**) and cabal `hunt20c` ran 2691 in
23818s (**8.9 s/decision**). At those rates 2916 decisions is **4.9h to 7.2h** -
an overnight run. Plan 6.5h and judge it by its own log's `PARLOR DONE rc=` line.

Belfry's payload carries the whole 12-role compact script on every call, so the
upper figure is the one to budget against. The decisions-per-game figure is also
the random control's: a model that ends games in fewer days makes fewer decisions
and one that drags them out makes more, so treat 48.6 as an estimate rather than
a count.

## The power arithmetic, and why it chose the endpoint

**This is the part worth writing the document for.** At 5 seats a game yields
**0.67 executions on a living seat on day 1** (134 over the control's 200 games),
so the figure `eval/run_belfry.py` prints "READ THIS ONE" beside accrues at
two-thirds of one observation per game. Every candidate endpoint below is priced
at the control's own per-game rates, and the primary is the one the affordable N
can actually carry.

Per-game rates, all from the 200-game control record:

| event | per game | control total |
|---|---|---|
| good-seat votes | 13.82 | 2763 |
| ... on an evil nominee | 5.57 | 1113 |
| ... on a good nominee | 8.25 | 1650 |
| good-seat votes after a lie | 0.81 | 162 |
| executions on a living seat, day 1 | 0.67 | 134 |
| executions on a living seat, all days | 1.29 | 257 |
| decisions | 48.6 | 9719 |

### Candidate 1 - day-1 execution accuracy against a 40% chance rate

n = 0.67N. The bar is that the Wilson 95% floor clears the chance rate on the same
boards. At 5 seats that rate is **exactly 40.00%**: day 1 opens with five alive
and two evil every game, and the control lands on 40.00% over 134 executions,
which is what earns the figure the right to be read at all.

Games needed for 80% power, computing the smallest hit count whose Wilson floor
clears 40% at each n and then the binomial probability of reaching it:

| true accuracy | games for 80% power | day-1 executions |
|---|---|---|
| 50% | 282 | 189 |
| 55% | 124 | 83 |
| 60% | 66 | 44 |
| 70% | 28 | 19 |

**282 games is 4 to 6 days of GPU.** So this endpoint cannot be primary at any N
the operator can afford locally: it settles only a model that hits 60% or better,
which is a 20-point improvement over chance in one irreversible act, and it is
blind to anything smaller.

### Candidate 2 - pooled execution accuracy

n = 1.29N, so it accrues twice as fast, and it is **not eligible to be an endpoint
at all**. Executing the demon ends the game, so a table that guesses well produces
fewer executions than one that guesses badly and the pool is enriched in mistakes
by construction. `eval/run_belfry.py` says so in its own report. Worse for this
arm specifically: the bias is a function of how long games run, and the live arm
will not run the control's 2.85 days, so the two pools are not the same
measurement. It ships as descriptive, beside `days_mean`, and is never compared to
the control.

### Candidate 3 - good-seat vote accuracy against the degenerate floor

n = 13.82N, the fastest-accruing figure in the game. But `vote_good.accuracy` has
a floor that beats it: the control scores **51.54% against an always-no policy's
59.72% on the same votes**, because a good seat voting yes at random executes good
seats. So "beat 50%" is not a claim, and "beat always-no" is a real bar.

It is still the wrong primary, for a reason that is about arms rather than about
power. `always_no` is the share of nominees that were good, and **the model's own
play changes that share** - it nominates differently from the control. So
accuracy-minus-always-no mixes discrimination with the nominee mix, and comparing
it across two arms compares two different denominators. It ships as a descriptive
contrast with its own game-clustered interval.

### Candidate 4 - the misled/clear gap, which is what this rung exists for

0.81 misled good-seat votes per game, split 0.31 on evil nominees and 0.51 on
good. Games needed for 80% power on the difference of two discrimination figures,
at the control's rates and a doubled variance allowance:

| true gap | games for 80% power |
|---|---|
| 30 points | 243 |
| 20 points | 547 |
| 10 points | 2186 |

**Nothing affordable touches it**, and 60 games yields about 49 misled votes.
Pre-registered as descriptive, reported with its counts and no claim attached.
That the rung's own headline question is out of reach at this table is a fact
about the script - `venom` and `sot` mislead 0.19 seats per game - and the honest
places to buy the sample are a bigger table, a script weighted toward the roles
that lie, or a run an order of magnitude longer. Not this arm.

### The primary, and its power

**Good-seat vote discrimination**, D = P(vote yes | nominee is evil) - P(vote yes
| nominee is good), over every vote cast by a seat that is good.

It is the primary because **its floor is exactly zero and nothing degenerate can
clear it**. Always-no scores 0. Always-yes scores 0. Any policy whose vote is
independent of what the nominee actually is scores 0 in expectation, whatever the
nominee mix, so it is invariant to the thing that makes candidate 3 arm-dependent.
The control lands at **+2.41%** (551/1113 yes on evil nominees, 777/1650 on good)
with a game-clustered 95% interval of **[-1.49%, +6.15%]**, which contains zero.
That is the instrument control: random play does not clear this bar.

It also has a measured effect size to be powered against. `cabal`'s discrimination
figure is the same shape, and `qwen36-35b-a3b-iq3` posted **+30.7%** on it
(`docs/measurements.md`, 12 games, 0.69% fallback).

Power, from the control's own bootstrap standard error of **0.0194 at 200 games**,
scaled as sqrt(200/N). Votes cluster inside a game and the control's design effect
measured 1.00 only because random voters are independent of each other; a live
table talks, so **the table below doubles the variance as an allowance** and the
undoubled column is shown beside it:

| games | good votes | 95% floor above 0, power at D = | | | |
|---|---|---|---|---|---|
| | | 5% | 10% | 15% | 20% |
| 20 | 276 | 0.08 | 0.21 | 0.41 | 0.64 |
| 40 | 553 | 0.13 | 0.37 | 0.69 | 0.90 |
| **60** | **829** | **0.17** | **0.51** | **0.85** | **0.98** |
| 100 | 1382 | 0.25 | 0.73 | 0.97 | 1.00 |
| 60, undoubled | 829 | 0.29 | 0.81 | 0.99 | 1.00 |

**60 games is the smallest N with 80% power against a 15-point discrimination**,
which is half of what this model posted on `cabal`. It has 51% power against 10
points and it **cannot settle a marginal reader at 5 points** - stated in advance,
the same shape S6, S2 and the DURF campaign all carried. It is also, by
coincidence rather than design, within a whisker of the 66 games the day-1
secondary would need against a true 60%, which is why that figure is worth
carrying as a secondary at all.

## Clause A - the primary endpoint

**The statistic: good-seat vote discrimination**, over votes with
`voter_evil == False`, misled and clear pooled, dead and living seats pooled.
Computed from the per-game `votes` rows in the `.jsonl`: a row carries `yes`,
`voter_evil`, `nominee_evil`, `voter_alive` and `voter_misled`.

**The bar: the 95% FLOOR of a bootstrap over GAMES clears 0.** The unit is the
game, not the vote, on the argument `core/stats.py` already makes in its own
docstring - votes inside one game share a deal, a night and a table, so a
per-vote interval reports one far tighter than the data supports.
`core.stats.bootstrap_ci` with its default 4000 resamples and seed 7, so the
interval is reproducible.

**Read floor: fewer than 100 good-seat votes on either conditional arm and no
discrimination figure is reported.** The control's rates put 60 games at ~334 and
~495, so this fires only on a run that went badly wrong in some other way.

Three outcomes, all three of which get reported:

- **Floor above 0** -> on this backend, at this prompt, this script and one talk
  round, a good seat's vote carries information about who the referee actually
  dealt as evil. A dated snapshot of one model, never a claim about models.
- **Ceiling below 0** -> good seats vote to execute good nominees MORE often than
  evil ones. At temperature 0.0 that is systematic, not noise, and it is a
  **result rather than a broken run**: the table's talk moves its own side
  against itself. It would be the sharpest thing this arm could return, and this
  document commits to reporting it in exactly those words.
- **Interval spanning 0** -> **the run does not decide it.** Report the point
  estimate with the interval and make no claim. **No second arm to chase it**, at
  a different N or a different seed. A rerun chosen because the first draw
  disappointed is the peeking this file exists to refuse.

## Clause B - the pre-registered secondary, and it is a secondary

**The statistic: day-1 execution accuracy on a living seat**
(`execution_day1.hits` over `execution_day1.on_a_living_seat`), against
`execution_day1.chance` computed off the same boards, with `execution_day1.ci95`.

**The bar: the Wilson 95% floor clears the run's own chance figure.** The run's
own, not the control's - the scorer computes it per execution off that execution's
board, and the run's own number is the one that describes the run's own boards. At
5 seats it must be 40.00%: day 1 opens with five alive and two evil. **If the live
arm's figure differs from 40.00% by more than 2 points, something killed a seat
before the first execution and the endpoint is reported as unreadable rather than
scored** - the control landed on 40.00% exactly, so a deviation is a fact about
the run and not about the model.

It is a secondary because the power table above says it is: at 60 games it has
about 69% power against a true 60% and about 21% against a true 50%. **A floor
that clears is worth reporting and is not on its own the arm's result; a floor
that does not clear is not evidence of absence at this N**, and the criterion says
so before the number exists.

## Void conditions, declared here

- **Fallback rate above 10% voids every figure**, per the repo invariant and
  `core.integrity.VOID_BAR` - a decision no model could make legally is played at
  random and counted, and a run that hides that is the random policy wearing a
  model's name. The verdict script refuses to render a verdict above the bar.
- **Fewer than 60 played games voids the arm as promised.** A partial run is
  reported as partial or rerun whole, never scored as a short arm. `errors` are
  excluded from every figure by the scorer, so an errored game is a missing game
  for this purpose. If the run dies at hour five, the integrity block and the
  counts are still reported - the verdict is not.
- **An entitlement leak voids the arm.** `play_game` audits every turn and raises,
  and `one_game` re-raises `AssertionError` rather than recording it, so a leak
  kills the run and there is no record to score. Gate #1 is not a number this
  criterion reports.
- **Recovered above 25% warns and does not void** (`core.integrity.RECOVERED_WARN_BAR`).
  A recovered decision is the model's own legal play, arrived at after the referee
  sent it back. It is not the same measurement as a run that never missed, so any
  comparison to the control - whose recovered rate is 0.00% by construction, the
  random policy never being refused - must say so in the same sentence.

## Reported beside the verdict, gating nothing

Pre-registered as descriptive **here**, so that reporting them later is not a
statistic chosen after the fact:

- **`vote_good.accuracy` against `vote_good.always_no`**, with a game-clustered
  interval on the difference. The control is 51.54% against 59.72%, so random play
  loses to always-no by 8.18 points. Descriptive for the arm-dependence reason in
  candidate 3 above.
- **Pooled `execution`**, with the stopping-rule caveat and `days_mean` in the same
  breath, and **never compared to the control's 41.25%**.
- **`execution.on_a_dead_seat`.** The control carried 58 of 315 executions against
  a seat that was already dead. A table that spends its days on corpses is not a
  table that executed badly, and the two must not be pooled.
- **The misled/clear split** (`vote_good_misled`, `vote_good_clear`) as counts and
  point estimates only. Below 200 misled votes no gap is reported, and 60 games is
  expected to yield about 49, so this will almost certainly not be reported. Said
  in advance rather than discovered afterwards.
- **Dead-seat against living-seat votes**, split on `voter_alive`. Dead seats keep
  a vote and have watched more of the game; the scorer pools them and this
  criterion follows the scorer, so the split is descriptive.
- **Evil-seat discrimination** (`vote_evil` and the same conditional rates from the
  rows). An evil seat playing well should be NEGATIVE on this statistic - it votes
  to execute good seats. Descriptive: the arm is not powered to split it.
- **`good_win_rate` with its interval, `causes`, `days_mean`, `seat_games_misled`,
  and the whole integrity block.** No deception or deduction figure is inferred
  from the win rate: a win here is a four-day chain and attributing it to any one
  decision is not something the record supports.

## What the scorer does not publish, and why nothing was added to it

Three gaps found while writing this. **`eval/run_belfry.py` was not edited** -
changing the shipped scorer to fit a criterion written the same day would make the
criterion's own instrument a thing this arm invented for itself.

1. **The conditional yes-rates are not recoverable from `score()`.** `vote_good`
   publishes `accuracy`, `always_no`, `always_yes` and `votes`. `always_yes` gives
   the share of nominees that were evil, and `accuracy` is one equation in two
   unknowns, so P(yes | evil) and P(yes | good) cannot be separated from the
   summary. The verdict script computes them from the `.jsonl` rows, which carry
   every field needed.
2. **No published interval is clustered by game.** Every `ci95` in the summary is
   Wilson over votes or over executions, and `core/stats.py` already argues in its
   own docstring that this is too tight for a vote-level figure. `bootstrap_ci`
   exists in `core/` and no belfry figure uses it. The verdict script does.
3. **The criterion therefore cannot be applied to a summary alone.** It needs the
   `.jsonl`. That is stated in the arm above as a requirement on the launch rather
   than discovered when the record lands.

Whether any of the three should become a scorer field is a question for after this
arm, decided on whether a second game needs it, which is the repo's promotion bar.
