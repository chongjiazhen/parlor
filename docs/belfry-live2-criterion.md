# belfry live arm #2 - the pre-committed criterion, written 2026-09-01 BEFORE the arm

**This file is the PROMISE, not the result.** Nothing in it is edited after the
arm launches - not the endpoint, not the bar, not N, not the void conditions.
Same discipline as `docs/belfry-live1-criterion.md`, which it replaces for one
reason and one only, stated in full below.

## Why this file exists, and the one thing it changes

**live1's criterion pre-committed an arm that cannot be run on this model.** It
promised 60 games at temperature 0.0 **without** `--no-thinking`. Measured
2026-09-01, two games at exactly those settings, seeds 6100-6101:

| | live1's promised settings | the same cell with `--no-thinking` |
|---|---|---|
| fallback | **63/108 = 58.33%** | 1.49% of 5515 decisions |
| vote fallback | **37/62 = 59.68%** | 0.31% of 3260 |
| seat-games over the 10% bar | **10 of 10**, worst 65.22% | 0 |
| recovered | 22.22% over 214 parser attempts | 12.84% |
| cost | 1805 s/game -> **~30 h for 60 games** | 320 s/game |

`qwen36-35b-a3b-iq3` is a reasoning distill: without `--no-thinking` it fails to
terminate its reasoning, the parser rejects the reply, and more than half of every
decision is played at random. live1's own void condition therefore fires on
live1's own settings, at both the run-wide and the vote-only threshold,
independently. The arm as promised buys a guaranteed VOID for thirty hours of GPU.

**So this criterion changes exactly one launch setting - `no_thinking: True` - and
nothing else.** Every endpoint, bar, floor, tolerance, void condition and
descriptive item below is copied from `docs/belfry-live1-criterion.md` verbatim.
That is the whole point of writing a second file rather than editing the first:
live1 has already run, its numbers are in view, and an edit to it now would be the
peeking the discipline exists to refuse. **The settings move because they are
unrunnable; the statistic does not move at all.**

## What was and was not seen before this file was written

Stated because the honesty of a pre-commitment written second depends on it.

- **Seen:** that live1's settings void, at the fallback rates in the table above.
  That is a fact about whether the arm can be READ, not about what it would say.
- **Seen:** live1's off-criterion 100-game record (temperature 0.8,
  `--no-thinking`), which is why **its numbers bind nothing here** and why this
  file changes no bar. `eval.belfry_live1_verdict` refuses it, exit 3, and prints
  it as a descriptive audit.
- **Not seen, and not seeable:** any figure from this arm's own seeds. The
  runnability smoke for these settings deliberately runs **seeds 6900-6901**,
  outside this arm's 6100-6159, so no game this criterion will score has been
  played or looked at. The smoke reports a fallback rate and a per-game cost and
  nothing else is read from it.

## The arm

**60 games, 5 seats, compact script, 1 talk round, `--arm llm`, local
`qwen36-35b-a3b-iq3`, temperature 0.0, `--no-thinking`, seed 6100.** Same seeds,
same table, same script and same round count as the 200-game random control in
`docs/measurements.md` §belfry's control arm, so the policy is the one variable.

```
py -3 -m eval.run_belfry --games 60 --arm llm --seats 5 --script compact \
    --rounds 1 --backend local --model qwen36-35b-a3b-iq3 --temperature 0.0 \
    --no-thinking --seed 6100 --out eval/records/belfry-live2.json
```

The recipe is `eval/runs/belfry-live2.cmd` and it takes no arguments, for the
reason live1 demonstrated: the first attempt at that arm got three settings wrong
because they were parameters read off a queue row rather than off a criterion.

Temperature stays 0.0, on live1's own argument, unedited: a vote is an adjudicable
decision rather than table speech, and a sampled one adds variance to the figure
this arm exists to read.

`--out` is required, not optional. The primary endpoint's interval is a bootstrap
over GAMES, and the per-game rows live only in the `.jsonl` sibling - a run
launched without `--out` cannot be scored against this criterion at all.

**N is fixed at 60 in advance and there is no stopping rule.** Reading a partial
run and stopping when it looks good is the same error as choosing the statistic
afterwards, one step earlier in the pipeline.

### What 60 games costs

At the 320 s/game measured for this cell with `--no-thinking`, 60 games is
**~5.3 h** - an overnight run, and a sixth of what live1's settings would have
cost. Judge it by its own log's `PARLOR DONE rc=` line, never by a process probe.

That figure came from a temperature-0.8 run. Greedy decoding changes how long a
reply is, not how many calls there are, so treat 5.3 h as an estimate and let the
smoke at these exact settings refine it.

## The power arithmetic

**Unchanged from live1 §The power arithmetic, and its conclusion is unchanged.**
That section is not restated here - read it there. What it establishes, and what
this arm inherits without amendment:

- The primary is **good-seat vote discrimination**, because its floor is exactly
  zero and nothing degenerate can clear it: always-no scores 0, always-yes scores
  0, and any policy whose vote is independent of the nominee scores 0 in
  expectation whatever the nominee mix.
- **60 games is the smallest N with 80% power against a 15-point discrimination**,
  half of what this model posted on `cabal`. It has 51% power against 10 points
  and **cannot settle a marginal reader at 5 points**. Said in advance.
- Day-1 execution accuracy is a **secondary** and is powered as one: ~69% against
  a true 60%, ~21% against a true 50%.
- Pooled execution accuracy is **not eligible to be an endpoint** - executing the
  demon ends the game, so the pool is enriched in mistakes by construction.
- The misled/clear gap needs 243 games for 80% power against a 30-point gap.
  Nothing affordable touches it; 60 games yields about 49 misled votes.

## Clause A - the primary endpoint

**The statistic: good-seat vote discrimination**, D = P(vote yes | nominee is
evil) - P(vote yes | nominee is good), over every vote cast by a seat that is
good: rows with `voter_evil == False`, misled and clear pooled, dead and living
seats pooled.

**The bar: the 95% FLOOR of a bootstrap over GAMES clears 0.** The unit is the
game, not the vote - votes inside one game share a deal, a night and a table.
`core.stats.bootstrap_ci` with its default 4000 resamples and seed 7, so the
interval is reproducible.

**Read floor: fewer than 100 good-seat votes on either conditional arm and no
discrimination figure is reported.**

The control's instrument reading, carried unchanged: **+2.41%** (551/1113 yes on
evil nominees against 777/1650 on good) with a game-clustered 95% interval of
**[-1.49%, +6.15%]**, which contains zero. Random play does not clear this bar,
which is what earns the figure the right to be read.

Three outcomes, all three of which get reported:

- **Floor above 0** -> on this backend, at this prompt, this script and one talk
  round, a good seat's vote carries information about who the referee actually
  dealt as evil. A dated snapshot of one model, never a claim about models.
- **Ceiling below 0** -> good seats vote to execute good nominees MORE often than
  evil ones. At temperature 0.0 that is systematic, not noise, and it is a
  **result rather than a broken run**: the table's talk moves its own side against
  itself. It would be the sharpest thing this arm could return, and this document
  commits to reporting it in exactly those words.
- **Interval spanning 0** -> **the run does not decide it.** Report the point
  estimate with the interval and make no claim. **No second arm to chase it**, at
  a different N or a different seed. A rerun chosen because the first draw
  disappointed is the peeking this file exists to refuse.

**That last clause binds live2 to itself, not to live1.** live2 is not a second
arm chasing live1's draw: live1 was never read, because it was never runnable.

## Clause B - the pre-registered secondary, and it is a secondary

**The statistic: day-1 execution accuracy on a living seat the table voted up**
(`execution_day1.hits` over `execution_day1.voted_up`), against
`execution_day1.chance` computed off the same boards, with `execution_day1.ci95`.

**The bar: the Wilson 95% floor clears the run's own chance figure.** The run's
own, not the control's. At 5 seats it must be 40.00%: day 1 opens with five alive
and two evil. **If the live arm's figure differs from 40.00% by more than 2
points, something killed a seat before the first execution and the endpoint is
reported as unreadable rather than scored.**

**A floor that clears is worth reporting and is not on its own the arm's result;
a floor that does not clear is not evidence of absence at this N.**

## Void conditions, declared here

- **Fallback rate above 10% voids every figure**, per the repo invariant and
  `core.integrity.VOID_BAR`. The verdict script refuses to render a verdict above
  the bar. **This is the condition live1's settings fired**, and it is carried
  here unweakened: if these settings also void, this arm voids, and the criterion
  is not edited again to chase a readable one.
- **Fewer than 60 played games voids the arm as promised.** A partial run is
  reported as partial or rerun whole, never scored as a short arm. `errors` are
  excluded from every figure by the scorer, so an errored game is a missing game.
- **An entitlement leak voids the arm.** `play_game` audits every turn and raises,
  so a leak kills the run and there is no record to score. Gate #1 is not a number
  this criterion reports.
- **Recovered above 25% warns and does not void**
  (`core.integrity.RECOVERED_WARN_BAR`). A recovered decision is the model's own
  legal play after the referee sent it back. Any comparison to the control - whose
  recovered rate is 0.00% by construction, the random policy never being refused -
  must say so in the same sentence.

## Reported beside the verdict, gating nothing

Pre-registered as descriptive **here**, unchanged from live1:

- **`vote_good.accuracy` against `vote_good.always_no`**, with a game-clustered
  interval on the difference. The control is 51.54% against 59.72%. Descriptive
  because the model's own play changes the nominee mix the floor is computed on.
- **Pooled `execution`**, with the stopping-rule caveat and `days_mean` in the
  same breath, and **never compared to the control's 41.25%**.
- **`execution.on_a_dead_seat`.** A table that spends its days on corpses is not a
  table that executed badly, and the two must not be pooled.
- **The misled/clear split** as counts and point estimates only. Below 200 misled
  votes no gap is reported, and 60 games is expected to yield about 49.
- **Dead-seat against living-seat votes**, split on `voter_alive`.
- **Evil-seat discrimination.** An evil seat playing well should be NEGATIVE here.
  The arm is not powered to split it.
- **`good_win_rate` with its interval, `causes`, `days_mean`, `seat_games_misled`,
  and the whole integrity block.** No deception or deduction figure is inferred
  from the win rate.

## The arithmetic

`py -3 -m eval.belfry_live1_verdict --criterion live2` - the same module and
the same code path, selected by one flag that switches the record path and the expected launch
settings **as a single object**. They are deliberately not separate flags:
`--v2` in `eval/belfry_adjudicator_verdict.py` switched the expected args and not
the default record paths, so a bare invocation loaded the v1 records and reported
it as a criterion violation rather than as the wrong file. One binding, one
switch.
