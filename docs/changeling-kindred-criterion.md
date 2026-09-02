# changeling's kindred-deck criterion - written 2026-09-02, BEFORE any live record

**This file is the PROMISE, not the result.** Written before the run, and
**nothing in it may be edited once a record is launched against it.** The outcome
goes in a writeup that cites this file clause by clause, the way the waker deck's
read cites `docs/changeling-waker-criterion.md`.

`AGENTS.md` makes this file - not `queue.md`, not the launcher's defaults - the
only binding statement of N, temperature and flags.

## The deck, and the constraint it deals under

**`SETUP_7_KIN`: 7 seats, 3 centre, 10 cards** - `pack` x2, `kindred` x2,
`spotter`, `swapper`, `switcher`, `deceived`, `bystander` x2, dealt with
`require_seated_kin`: both `kindred` seated or both in the centre, a deal retried
otherwise (pair 87.6%, 1.07 retries a game, measured on the code). Registered in
`games/changeling/roles.py`; the design is `RULES.md` §Deck B.

**A new baseline, not a variant.** Wolf density moves from 2/5 to 2/7, so the
chance bar is not derivable from either shipped deck and was measured rather than
asserted, below. **Nothing measured on `SETUP_5` or `SETUP_6_WAKER` transfers.**

Priced with `py -3 -m eval.strata --deck SETUP_7_KIN --nights 4000 --seed 11`,
against both other decks on the same command (`RULES.md` §Deck B's census):

| | `SETUP_5` | `SETUP_6_WAKER` | `SETUP_7_KIN` |
|---|---|---|---|
| blind villager seat-nights / game | 1.339 | 1.416 | **1.371** |
| unwinnable (no pack seated at dawn) | 2.85% | 2.05% | **1.27%** |
| villager `identity` seats told nothing | 18.7% | 10.3% | **5.3%** |

## What the deck asks

`kindred` is the pack's mirror on the village side: two seats who wake together
and see each other, so each holds one certainly-village identity at MEET that no
other village card is told. The rung's question, restated for this deck: **does a
village that can KNOW more deduce more?** The blind stratum is the same statistic
as every changeling read; what changes is the table around it.

**Direction is NOT pre-committed** - a pair that vouches for each other narrows
the wolves' cover, and a swapped `kindred` (the card moves after MEET, and the
seat is not told) is a stale certainty that can mislead two seats at once.

## The bar, measured before the run

`py -3 -m eval.run_changeling --arm random --seats 7 --games 4000 --seed 910000
--model none --rounds 1`, record `eval/records/kin-chance.json`, 2026-09-02, under
`plurality-min2`, fallback 0/56000 by construction:

- **directly measured blind accuracy: 25.39%** [24.22%, 26.57%] over **5376**
  blind votes on 3955 scored games (45 unwinnable, 1.13%).
- derived per-vote chance: **25.18%**, from the arm's own dawn-wolf mix by
  `_chance` (0 / 1 / 2 wolves seated: 45 / 1756 / 2199 games).
- random-arm village win rate **32.69%** [31.25%, 34.17%], pack **67.31%** - the
  gate #2 reference for this deck. `SETUP_5`'s figures do not apply. **The runner
  prints `random reference ... 60.49%` beside every deck** - that line is
  `SETUP_5`'s pre-`plurality-min2` figure and is not to be read against a
  seven-seat record.

**THE BAR IS 25.39%, the measured figure, chosen because it is the HIGHER of the
two.** They agree within the one-point tolerance (0.2 points apart), so either
would do; naming the higher makes the gate harder, which is the direction a
pre-commitment should err in, and it is the same rule the waker criterion applied.

**The run must still report its own random arm.** If it disagrees with 25.39% by
more than a point, that arm is the bar and this number is the thing that was wrong.

## Gate #3, deduction - the gate is blind villager accuracy

- **The statistic: accuracy of votes cast by villager seats the night told
  NOTHING**, the `none` stratum under S10's told-based rule. Unchanged from every
  changeling criterion before it, deliberately - a new deck is enough variables.
- **It holds only if the 95% floor clears 25.39%.** Point estimates do not decide
  gates here. The scorer publishes a game bootstrap and `wilson` is available;
  **both are computed and both must clear.**
- **Power, computed before the run.** 1.359 blind votes per scored game x 200
  games x 98.9% winnable = **~269 blind votes**. At that N the Wilson floor clears
  25.39% from a true rate of **31% upward**; 30% does not clear. So **200 games CAN
  show a moderately good blind villager on this deck and CANNOT settle a marginal
  one.** The headroom is the widest of the three decks - a 25.39% bar against the
  waker deck's 30.14% and `SETUP_5`'s 35.84% - and the reason is wolf density,
  not the sample.
- **If it lands marginal the answer is "not shown".** No second campaign to chase
  it, and no re-cut of the statistic.

## Gate #2, deception - conditional, and the condition is stated here

Gate #2 is **unreadable until gate #3 holds** - on this deck the random arm
already hands the pack 67.31% with no deception in it. If #3 holds, #2 is the
pack win rate with its interval against **this run's own random arm**, never
against 67.31%, which is a reference point rather than a control. No bar for #2
is declared, so it is reported as a rate with an interval and **no verdict**.

## The kindred split - an OBSERVATION, and it is not a gate

Both `kindred` are seated in ~87.6% of deals and both in the centre otherwise,
randomised within the run - so pair-present against pair-absent is one run, not
a paired pair, on different deals. At 200 games the absent side is ~25 games and
~34 blind votes, so **the split is reported as two rates with intervals, or as
"not readable"**, and it gets no bar that may not be promoted after the fact.

## Free off the same records, and none of them a gate

- the `false` stratum against the `none` stratum, this rung's own question;
- diverged-vs-intact accuracy;
- **the `kindred` seats' own accuracy against the other `identity`-told
  villagers** - the seats holding one certain village identity against the
  `spotter`, which holds one certain reveal of a different kind;
- **how often a `kindred` votes its fellow** - `py -3 -m eval.changeling_audit
  <arm>.jsonl --reference <arm>-random.jsonl`, the shown-village class. Random
  play on this deck is the reference rate; a model acting on the told fact sits
  below it, a model acting on the name sits at it.

## What voids the whole thing, decided in advance

- **Fallback rate above 10% voids every verdict** (`AGENTS.md`).
- **Recovered rate above 25% does NOT void** - flagged beside the verdict.
- **A blind stratum under 150 votes makes the gate REFUSED rather than failed.**
- **Any leak raises.** This deck seats a card no recorded run has dealt, and
  `kindred` is the card whose stale-reveal collision was caught at gate #1 the
  day it landed (`RULES.md` §Expansion cards); the audit runs on every turn by
  default and a leak is never scored.

## The run, exactly

```
eval\runs\changeling-kindred.cmd kin1 200 14000 qwen36-35b-a3b-iq3
```

- **200 games**, `--arm llm`, `--seats 7`, **`--seed 14000`** (games take
  14000..14199 - fresh; 12000..12199 are the waker deck's, 5000..5199 the skin
  pair's and S22's, 910000..913999 the bar above).
- **model `qwen36-35b-a3b-iq3`, temperature 0.8, `--no-thinking`, `--rounds 2`,
  `--retries 2`, `--max-tokens 1536`, `--timeout 240`** - S2's settings exactly,
  so the deck is the variable and the lane is not.
- local route, served serially. Seven seats is ~40% more model calls than
  `SETUP_5`'s 18250 s at five, so **budget ~7 h** and judge progress by the run's
  own log.
- **The paired random arm on the same seeds runs too**, and it is what the
  own-arm clause reads.
- **Entry condition: no changeling arm in flight.** The chained campaign in
  `queue.local.md` (skin pair, S22, gate #2) holds the card and the freeze first.
