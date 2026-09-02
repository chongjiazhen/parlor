# Changeling gate #2 as a pair - the pack's own contribution, pre-committed

Created: 2026-09-02T06:47:03Z. Not editable after launch. **Unlaunched**; needs
one new arm.

S2 read gate #2 as a rate with no verdict (`games/changeling/RULES.md` §Gate #2):
59.49% pack wins, with the no-deception reference sitting inside the interval and
no control on the same seeds. `docs/open-arms.md` §Gate #2 has a cheaper
falsifiable design names the fix: hold the opponent population fixed and move only
the side under test. This is that design on the rung where gate #3 already holds,
so the conditionality is met and the number is readable as deception.

## The question

Against the SAME live village, does a live pack win more often than a pack
played at random? The two arms share seeds, deck, skin, rounds and model; the
only thing that moves is who is behind the pack seats. What the difference
measures is what the pack's speech and votes are worth against a table that is
actually deducing - and nothing about the village, which is identical by
construction.

**Direction is pre-committed for the READING, not for the call.** The interval
excluding zero in either direction INFORMS. Above zero reads "the pack's play
contributes"; below zero reads "the pack's play costs it against this village",
which is a finding about the model, not a failure of the instrument.

## The statistic

- **Pack win rate on the scored denominator** (games with a wolf at dawn), per
  arm. The gate #2 statistic the scorer already publishes.
- **The pair's figure is the difference, live pack minus random pack**, Newcombe
  (Wilson-score) 95% interval over games, a paired game bootstrap beside it.
  **INFORMS if the Newcombe interval excludes zero. NOT SHOWN otherwise.** No bar
  on the size of the gap; `rate_ok`'s 5% CI-floor bar is not adopted.
- **Read the fallback rate FIRST, per arm.**
- **The all-random control is a REFERENCE beside it, never deciding**: the first
  200 games of `cl-rounds2-random` (seeds 5000..5199, the same seeds). It is the
  comparison S2's writeup said a paired random arm would make, so it is printed.
  It differs from the live arm in BOTH populations, which is why it cannot be
  the control here.
- **Pairing is COUNTED, not assumed.** Same seed means same deal, and the night
  is chosen by village seats on both arms, so dawn truth should agree game by
  game. The scorer prints how many pairs share their dawn truth; a shortfall is
  reported as a weakening of the pair, not smoothed.

## Power

~194 scored games per arm at 200 played. For two win rates near 60%, the standard
error of the difference is ~5 points and the 95% half-width near **10 points**.
The pair CAN show a ten-point contribution and CANNOT settle a smaller one. A
marginal result is "not shown" and no second pair chases it.

## Settings - binding, from this file and nowhere else

**The live-pack arm IS S22's two-round record**, `eval/records/cl-rounds2.json`:
`--games 200 --arm llm --backend local --model qwen36-35b-a3b-iq3 --no-thinking
--seats 5 --theme folk --rounds 2 --seed 5000 --timeout 240`
(`docs/changeling-rounds-pair-criterion.md`). This file is written before that
record exists; it is cited, not chosen.

**The one new arm**: identical, `--arm llm-village`, record
`eval/records/cl-gate2-village.json`. Village seats by DAWN TRUTH are live, pack
seats are `RandomPolicy` - a random pack says one of the stock lines and votes a
random legal seat. Cheaper than a full arm: fewer live seats per game.

`eval.gate2_pair_verdict` pins every setting on both records against their own
`args` and VOIDS the read on any disagreement, before the arithmetic. Recipe
`eval/runs/changeling-gate2-arm.cmd`; it refuses while `cl-rounds2.log` lacks
`PARLOR DONE rc=0 games=200/200` or `cl-rounds-pair.log` lacks
`PARLOR PAIR DONE` - the record it pairs against must exist and the card must be
free.

## What voids it, decided in advance

- **Fallback above 10% on either arm** voids the difference; rates still print.
  **Recovered above 25%** is flagged, not a void.
- **Fewer than 190 scored games on either arm** makes the pair REFUSED.
- **A settings disagreement on either record** voids the read.

## Free reads, none a gate

Blind villager accuracy per arm - the village is the same population, so a gap
here says the pack's play changed what the village had to work with. And
`eval.changeling_audit` on the village arm: how a live village votes when the
pack's speech carries no intent at all.
