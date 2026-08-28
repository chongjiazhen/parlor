# changeling's pre-committed criterion - written 2026-08-28, BEFORE S2

**This file is the PROMISE, not the result.** It was written before the 200-game
run and is reproduced here exactly as it stood in `queue.md` when S2 launched.
The outcome, clause by clause, is `games/changeling/RULES.md` §S2 read; the
arithmetic is `py -3 -m eval.s5_verdict`. **Nothing here may be edited to agree
with what happened** - that is the whole value of a pre-commitment, and a promise
rewritten after the fact is not evidence of anything.

It moved out of the queue on 2026-08-28, once applied. `queue.md` carries the
pointer.

---

Same discipline as the S6 criterion, which held. **Written before the run because
after it the statistic would be chosen with the numbers in view** - which is the
`hunt20b` error `queue.md` has already refused twice by name, and S1's verdict
declined the better-specified binary figure on exactly that ground. Nothing below
may be edited once S2 launches; the outcome goes in the S5 writeup, clause by
clause, and the promise stays as written.

**S2 is 200 games, `--arm llm`, one model pinned, `--seed` set.** Its powers re-run
comes first and is a separate 2x20 arm - that one is a re-measure on the fixed
lane, not a gate, and nothing here applies to it.

## Gate #3, deduction - THE GATE is blind villager accuracy

- **The statistic: accuracy of votes cast by villager seats the night told
  NOTHING**, on the `none` knowledge stratum keyed by S10's told-based rule. Not
  villager accuracy pooled, and not village win rate - a villager handed an
  identity is not deducing, and the win rate mixes in the deal.
- **The bar: 35.95%**, the measured per-vote chance from `--arm random`, n=4000
  (`games/changeling/RULES.md` §The chance baseline). **The run must also report
  its own random arm**; if that arm disagrees with 35.95% by more than a point,
  the run's own arm is the bar and this number is the thing that was wrong.
- **It holds only if the Wilson 95% FLOOR clears the bar.** Point estimates do not
  decide gates here.
- **Power, computed before the run** off `eval.strata`: 1.34 blind villager
  seat-nights per game, x97.2% winnable, so 200 games yields **~260 blind votes**.
  At that N the floor clears 35.95% from a true rate of **42% upward**; a true 41%
  does not clear and a true 40% is well short. So **200 games CAN show a
  moderately good blind villager and CANNOT settle a marginal one** - the same
  shape S6 had, stated in advance.
- **If it lands marginal the answer is "not shown", and the deck work proceeds
  anyway.** No second 200-game campaign to chase it. The expansion decks are the
  next thing either way, and each changes this stratum, so a re-run belongs after
  a deck change rather than after a disappointing draw.

## Gate #2, deception - conditional, and the condition is stated here

- **Gate #2 is unreadable until gate #3 holds.** Villagers at chance hand the pack
  a high win rate with no deception in it: the measured random reference is 39.51%
  village wins on the scored denominator, so the pack takes ~60% against a table
  that is not deducing at all. Same conditionality cabal's #2 carries, for the same
  measured reason.
- **If #3 holds**, gate #2 is the pack win rate with its Wilson interval, against
  that run's own random arm - never against the 39.51% reference, which is a
  different model, a different day and a reference point rather than a control.
- **`rate_ok`'s 5% CI-floor bar is pre-declared nowhere and is not adopted here.**
  If a bar for #2 is wanted it is written in this section before a run, or #2 is
  reported as a rate with an interval and no verdict.

## What voids the whole thing, decided in advance

- **Fallback rate above 10%** voids every verdict, as always.
- **Recovered rate above 25%** does NOT void - it is flagged beside the verdict
  (`core/integrity.py` §RECOVERED_WARN_BAR, set 2026-08-28 before any run produced
  the number). A recovered decision is the model's own legal move; it is simply not
  the same measurement as a run that never missed, and the writeup says so.
- **A blind stratum smaller than 150 votes** makes the gate REFUSED rather than
  failed. `_blind_line` already refuses an empty stratum; this puts a floor under
  a thin one, because a 40-vote interval spans everything and reads as a result.

## Three things to score off the same records, free

They need no extra run and are the reason S2 is one 200-game block rather than two
of 100:
- the `false` stratum's accuracy against the `none` stratum's - the seat whose
  entitled knowledge is wrong by construction, which `cabal` has no analogue for;
- the sleeper-decoy rate - seats that believed pack while holding village;
- diverged-vs-intact accuracy, the observation this rung was built to make.
**None of the three is a gate**, none gets a bar, and none may be promoted to one
after the fact.

---

## Two clauses did not apply cleanly, and S5 recorded rather than smoothed them

Noted here so a reader of the promise sees where it met the world, without the
promise itself being touched:

- It says **Wilson** where the scorer publishes a **game bootstrap**. Both floors
  were computed and both clear (38.47% Wilson, 37.36% bootstrap).
- **S2 ran no random arm**, so the own-arm clause had nothing to fire on and the
  bar stayed the criterion's 35.95%. The 34.91% in the run log is a DERIVED
  per-vote figure from that run's own dawn-wolf mix, not a measured arm. All three
  candidate bars (35.95 / 34.91 / 33.81) are cleared by both floors, so the call
  never turned on which one applied.
