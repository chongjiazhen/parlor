# changeling's waker-deck criterion - written 2026-09-02, BEFORE any waker record

**This file is the PROMISE, not the result.** It is written before the run, and
**nothing in it may be edited once a record is launched against it** - that is the
whole value of a pre-commitment, and a promise rewritten with the numbers in view
is not evidence of anything. The outcome goes in a writeup that cites this file
clause by clause, the way `games/changeling/RULES.md` §S2 read cites
`docs/changeling-gate3-criterion.md`.

Same discipline as the gate #3 criterion, which held, and the S6 one before it.
`AGENTS.md` makes this file - not `queue.md`, not the launcher's defaults - the
only binding statement of N, temperature and flags. Cost when that was skipped:
belfry live1 ran 100 games at temperature 0.8 with `--no-thinking` against a
criterion promising 60 at 0.0 without it, 11.5 h of GPU that can be read but never
called.

## The deck, and the second variable it spends

**`SETUP_6_WAKER`: 6 seats, 3 centre, 9 cards** - `pack` x2, `spotter`, `swapper`,
`switcher`, `deceived`, `bystander` x2, `waker`. Registered in
`games/changeling/roles.py`, candidate W-c of `RULES.md` §The decks that would seat
them.

**This is a new baseline, not a variant, and it spends two variables by
construction.** `Setup.__post_init__` requires `len(deck) == n + centre`, so a card
cannot be added without also growing the table or the centre. Growing the table was
measured better than either alternative. **Nothing measured on `SETUP_5` transfers**
- wolf density moves from 2/5 to 2/6, so the chance bar is not derivable from the
old one and was re-measured rather than asserted.

Priced with the repo's own instrument, `py -3 -m eval.strata --deck SETUP_6_WAKER`,
4000 nights, seed 11, against the shipped deck on the same command:

| | `SETUP_5` | `SETUP_6_WAKER` |
|---|---|---|
| blind villager seat-nights / game | 1.340 | **1.416** |
| unwinnable (no pack seated at dawn) | 2.80% | **1.82%** |
| villager `identity` seats told nothing | 18.7% | **10.3%** |
| `waker` seated | - | **63.1%** |

**These are the S10 told-based figures, and they are not the design table's.**
`RULES.md` §The decks quotes 1.02 -> 1.18 blind/game from the 2026-08-27 paper
design, computed on a different definition of blind. The direction agrees and the
magnitude does not (+5.7% here, +16% there). **The numbers in this table are the
binding ones**, because they come from the instrument the gate is actually cut
with; the design table is left as written rather than retrofitted.

## The bar, measured before the run

`py -3 -m eval.run_changeling --arm random --seats 6 --games 4000 --seed 900000
--model none --rounds 1`, record `eval/records/waker-chance.json`:

- **derived per-vote chance: 30.14%** - computed from the arm's own dawn-wolf mix
  by `_chance`, which now reads the table size off the record instead of a
  hardcoded 5.
- directly measured blind accuracy of that arm: **28.82%** [27.58%, 30.11%] over
  **5445** blind votes on 3936 scored games.
- random-arm village win rate **37.07%**, the gate #2 reference for this deck.
  `SETUP_5`'s 39.51% does not apply and may not be printed beside a six-seat run.

**THE BAR IS 30.14%, the derived figure, chosen because it is the HIGHER of the
two.** They disagree by 1.3 points, past the one-point tolerance the gate #3
criterion set, so this file names one rather than leaving a reader to pick after
the fact. Taking the higher makes the gate harder by 1.3 points, which is the
direction a pre-commitment should err in.

**The run must still report its own random arm.** If it disagrees with 30.14% by
more than a point, that arm is the bar and this number is the thing that was wrong.

## Gate #3, deduction - the gate is blind villager accuracy

- **The statistic: accuracy of votes cast by villager seats the night told
  NOTHING**, on the `none` stratum keyed by S10's told-based rule. Unchanged from
  the gate #3 criterion, and unchanged deliberately - a new deck is enough
  variables.
- **It holds only if the 95% floor clears 30.14%.** Point estimates do not decide
  gates here. The scorer publishes a game bootstrap and `wilson` is available;
  **both are computed and both must clear**, which is the clause S5 had to record as
  not applying cleanly. Stated in advance this time.
- **Power, computed before the run.** 1.383 blind votes per scored game x 200 games
  x 98.4% winnable = **~272 blind votes**. At that N the floor clears 30.14% from a
  true rate of **36% upward**; 35% does not clear. So **200 games CAN show a
  moderately good blind villager on this deck and CANNOT settle a marginal one.**
  That is better headroom than S2 bought at five seats (~260 votes needing 42%
  against a 35.95% bar), and the reason is the deck, not the sample: a bigger table
  lowers the chance bar faster than it thins the stratum.
- **If it lands marginal the answer is "not shown".** No second campaign to chase
  it, and no re-cut of the statistic.

## Gate #2, deception - conditional, and the condition is stated here

Unchanged in substance from the gate #3 criterion. Gate #2 is **unreadable until
gate #3 holds** - villagers at chance hand the pack a win rate with no deception in
it, and on this deck the random arm already gives the pack 62.93%. If #3 holds, #2
is the pack win rate with its interval against **this run's own random arm**, never
against 37.07%, which is a different day and a reference point rather than a
control. No bar for #2 is declared here, so #2 is reported as a rate with an
interval and **no verdict**.

## The waker split - an OBSERVATION, and it is not a gate

The `waker` is seated in 63.1% of deals and sits in the centre otherwise,
randomised within the run on one deck - so waker-present against waker-absent is
one run, not a paired pair. **That is what makes it affordable and also what limits
it**: different deals, not the same ones.

**It gets no bar and may not be promoted to one after the fact.** At 200 games the
split is ~126 present / ~74 absent, so roughly 172 and 100 blind votes - intervals
wide enough that only a large difference would read. It is reported as two rates
with intervals and a statement of which way it points, or as "not readable".

## Free off the same records, and none of them a gate

- the `false` stratum against the `none` stratum, this rung's own question;
- diverged-vs-intact accuracy;
- **whether the `waker` seat itself votes better than the table** - the one seat
  TOLD what every other seat must infer. This is the instrument the deck exists
  for, and it is still an observation, because the seat is one vote per game.

## What voids the whole thing, decided in advance

- **Fallback rate above 10% voids every verdict**, as always (`AGENTS.md`).
- **Recovered rate above 25% does NOT void** - flagged beside the verdict
  (`core/integrity.py` §RECOVERED_WARN_BAR).
- **A blind stratum under 150 votes makes the gate REFUSED rather than failed.**
- **Any leak raises.** Gate #1 audits every turn by default and a leak is never
  scored; this deck seats a card `SETUP_5` never dealt, which is exactly when a
  render path first meets a card name it has not printed before.

## The run, exactly

```
eval\runs\changeling-waker.cmd waker1 200 12000 qwen36-35b-a3b-iq3
```

- **200 games**, `--arm llm`, `--seats 6`, **`--seed 12000`** (games take
  12000..12199 - fresh; 4000..4199 are S2's and 900000..903999 are the bar above).
- **model `qwen36-35b-a3b-iq3`, temperature 0.8, `--no-thinking`, `--rounds 2`,
  `--retries 2`, `--max-tokens 1536`, `--timeout 240`** - S2's settings exactly, so
  the deck is the variable and the lane is not.
- local route, served serially. S2 cost 18250 s at five seats; six seats is ~20%
  more model calls, so **budget ~6.1 h** and judge progress by the run's own log.
- **The paired random arm on the same seeds runs too**, and it is what the
  own-arm clause above reads.
