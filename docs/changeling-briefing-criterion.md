# Changeling standing-briefing pair, `--briefing` off vs on - pre-committed criterion

Created: 2026-09-02T11:21:17Z. Not editable after launch. **Unlaunched** - S21's
deliverable is this file, the off-by-default arm behind it and its recipe, ready
for the card when S22's two-round record is down.

The ask is incremental by design: a rule reaches a seat at the phase where it is
actionable and not before (`AGENTS.md`, "the ask carries what THIS phase needs,
and the payload is a budget"). Three things follow from that and none of them has
ever been measured. A seat meets the accusation rule only at VOTE, inside `ask`.
It meets what each side wins on nowhere in the payload at all. And the day's
procedure reaches it as a one-line public event. A person cannot play that, which
is why `games/changeling/demo.py` grew a `BRIEFING` printed OUTSIDE the payload.
Whether a MODEL wants it inside is the open question this pair answers.

## The question

Does the full standing frame, carried in every render, move blind villager
deduction?

**Direction is NOT pre-committed, and the reason is measured rather than
cautious.** `_night_against_the_table` restated a fact the seat already held and
bought +7% -> +63% on a 12B, then INVERTED on q36: +80% as written against +72%
with the line. More context is not monotonically better on this box, so a frame
that hands the table more to reason with is exactly as live as a frame that hands
it more to be wrong about. A direction named now would be a direction chosen
after the fact.

The lane notes make ABSENCE the novel arm. Every build read from source states
full rules in a system prompt and none ablates that, so the off arm - the shipped
default - is the arm nobody else has run.

## The statistic

- **Primary: blind villager accuracy** per arm, the `none` stratum under S10's
  told-based rule. S2's gate #3 statistic, unchanged, and the same one the rounds
  pair reads.
- **The pair's figure is the difference, briefing minus no briefing**, Newcombe
  (Wilson-score) 95% interval over pooled votes, with a paired game bootstrap
  beside it. **INFORMS if the Newcombe interval excludes zero, in either
  direction. NOT SHOWN otherwise.** No bar on the size of a gap; none may be
  added after.
- **Read the fallback rate FIRST, per arm, and the recovered rate with it.** The
  frame is 553 bytes on every render at `--rounds 2` on `folk`, against a 1620
  byte no-briefing render at seat 0 on seed 3 - about a third again, paid on every
  call of every seat. At a fixed `--max-tokens 1536` that is where a fallback rate
  moves, and a rise on the briefing arm is a finding about payload budget, reported
  as one rather than folded into the accuracy difference.
- **Gate #3 per arm**, secondary, read against the run's own random arm on the
  same seeds (reference 35.84% under `plurality-min2`; the run's own arm is the
  bar where it disagrees by more than a point).

## Power

Same shape as the rounds pair: ~260 blind votes per arm at 200 games, 95%
half-width on the difference near 8.5 points. The pair CAN show a gap of nine
points or more and CANNOT settle a smaller one. A marginal result is "not shown",
and no second pair chases it.

## Settings - binding, from this file and nowhere else

Both live arms: `eval.run_changeling --games 200 --arm llm --backend local
--model qwen36-35b-a3b-iq3 --no-thinking --seats 5 --theme folk --rounds 2 --seed
5000 --timeout 240`, driver defaults otherwise (`--register character`,
`--temperature 0.8`, `--max-tokens 1536`, `--retries 2`).

- **Arm 1 is S22's `cl-rounds2.json`** - the same command, without `--briefing`.
  It is not re-run. Seeds 5000..5199 are chosen for that reason: the two-round
  `folk` record is the control this pair pairs against, exactly as the gate #2 arm
  does.
- **Arm 2 adds `--briefing` and changes nothing else.** Record
  `eval/records/cl-briefing.json`.

`eval.briefing_pair_verdict` pins every setting above against each record's own
`args` and VOIDS the read on any disagreement, before the arithmetic. The control
predates the flag and carries no `briefing` key; absence reads as off for the
control only, and the arm must say `True`.

Controls, CPU: `--arm random --games 1000 --seed 5000 --theme folk --rounds 2`.
The random policy does not read a render, so one control serves both arms and the
strata census must agree exactly between them.

**This pair must run BEFORE the changeling source-rules merge, or it is void.**
That merge gives a lone `pack` an `identity`-class centre peek and makes
`spotter`/`swapper`/`switcher` declinable. Both move the strata and the chance
baseline - measured on the branch, `888c163`: on `SETUP_5` every lone wolf peeks,
so the blind stratum on the new baseline is SMALLER. Arm 1 is a pre-merge record.
An arm 2 taken after the merge would pair a post-merge run against a pre-merge
control and read the merge as the briefing.

## What voids it, decided in advance

- **Fallback above 10% on either arm** voids the pair's difference; both rates are
  still reported. **Recovered above 25%** is flagged, not a void.
- **A blind stratum under 150 votes on either arm** makes the pair REFUSED.
- **A settings disagreement on either record's own `args`** voids the read,
  checked before any arithmetic. `briefing` is on the per-game record as well as
  in `args`, so a pooled file is caught rather than averaged.
- **The source-rules merge landing between the two arms** voids the pair. Read the
  arms' `vote_rule` and the strata census against each other before the
  difference.
- **A missing arm is a lost pair.** The recipe refuses to start without arm 1's
  own `PARLOR DONE rc=0 games=200/200`.

## Free reads, none a gate

Per arm, S2's three (`false` vs `none`, sleeper-decoy rate, diverged vs intact),
and `eval.changeling_audit` against the shared random control. One this pair alone
can make: `eval.changeling_claims` per arm - whether a seat told what each side
wins on names a card it was never shown more or less often. Observational, and
reported whichever way the primary lands.

Recipe: `eval/runs/changeling-briefing-arm.cmd`. Records
`eval/records/cl-briefing.json`.
