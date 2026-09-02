# Changeling discussion-length pair, `--rounds 2` vs `--rounds 3` - pre-committed criterion

Created: 2026-09-02T06:38:02Z. Not editable after launch. **Unlaunched** - S22's deliverable is
this file and its recipe, ready for the card when the name-form pair is down.

`discussion_rounds` has been a flag since the rung was built and has never been
an arm (`docs/open-arms.md` §"changeling feels random"). If a table votes on
impressions because it has not had room to argue, one more round is the
one-variable test, and it costs GPU linearly in decisions.

## The question

Does a third discussion round move blind villager deduction? **Direction is NOT
pre-committed.** The measured pattern on this box is that more context is not
monotonically good (`AGENTS.md`, the `_night_against_the_table` inversion), so
a third round handing the table more to be wrong about is as live as a third
round handing it more evidence.

## The statistic

- **Primary: blind villager accuracy** per arm, the `none` stratum under S10's
  told-based rule - S2's gate #3 statistic, unchanged.
- **The pair's figure is the difference, three rounds minus two**, Newcombe
  (Wilson-score) 95% interval over pooled votes, a paired game bootstrap beside it.
  **INFORMS if the Newcombe interval excludes zero, in either direction. NOT SHOWN
  otherwise.** No bar on the size of a gap; none may be added after.
- **Read the fallback rate FIRST, per arm.** A longer transcript at a fixed
  `--max-tokens` and context is where a fallback rate would move, and a rise on
  the three-round arm is a finding about payload budget, reported as one.
- **Gate #3 per arm**, secondary, against the run's own random arm on the same
  seeds (reference 35.84% under `plurality-min2`; own arm is the bar if it
  disagrees by more than a point).

## Power

As the name-form pair: ~260 blind votes per arm at 200 games, 95% half-width on
the difference near 8.5 points. The pair CAN show a gap of nine points or more
and CANNOT settle a smaller one. A marginal result is "not shown"; no second pair
chases it.

## Settings - binding, from this file and nowhere else

Both live arms: `eval.run_changeling --games 200 --arm llm --backend local --model
qwen36-35b-a3b-iq3 --no-thinking --seats 5 --theme folk --seed 5000 --timeout
240`, driver defaults otherwise (`--register character`, `--temperature 0.8`,
`--max-tokens 1536`, `--retries 2`). Arm 1 `--rounds 2`, arm 2 `--rounds 3`.
**Seeds 5000..5199 on purpose** - the same seeds the name-form pair plays, so the
two-round `folk` arm is also the same-seeds `folk` record a later vocabulary
criterion (`folk` vs `greek`) may cite as its control. That criterion is not
this one and is written before that arm is read, never after.

Controls, CPU: `--arm random --games 1000 --seed 5000 --theme folk` at each
rounds setting. Random play does not speak, so the two must agree exactly on the
strata census.

`eval.rounds_pair_verdict` pins every setting above against each record's own
`args` and VOIDS the read on any disagreement, before the arithmetic.

Recipe: `eval/runs/changeling-rounds-pair.cmd`. It refuses to start while
`eval/records/cl-skin-pair.log` lacks its `PARLOR PAIR DONE` line - one card,
one lane, and a second live arm on the box would corrupt the first's timings.
Records `eval/records/cl-rounds{2,3}{,-random}.json`.

## What voids it, decided in advance

- **Fallback above 10% on either arm** voids the pair's difference; the rates
  are still reported. **Recovered above 25%** is flagged, not a void.
- **A blind stratum under 150 votes on either arm** makes the pair REFUSED.
- **A settings disagreement on either record** voids the read.
- **A missing arm is a lost pair.** The recipe refuses arm 2 without arm 1's own
  `PARLOR DONE rc=0 games=200/200`.

## Free reads, none a gate

Per arm, S2's three (`false` vs `none`, sleeper-decoy rate, diverged vs intact)
and `eval.changeling_audit` against the arm's own random control. One more that
this pair alone can make: `eval.changeling_claims` per arm - whether a third
round changes how often a seat names a card it was never shown. Observational.
