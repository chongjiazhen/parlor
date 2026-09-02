# Changeling name-form pair, `greek` vs `greek-named` - pre-committed criterion

Created: 2026-09-02T06:25:42Z. Not editable after launch.

The first GPU spend on the changeling skin set (`docs/moral-framing.md` §Name
form, §The changeling skin set). The pair goes first because it is the cleanest
single-variable manipulation in the repo: the two themes differ in exactly eight
strings, the card names, with blurb, pile word, sides, polarity, corpus and length
byte-identical. Confirmed before this was written by rendering both preambles
through `games/changeling/demo.py --seed 7` and diffing - the only lines that
move are the six dealt card names and their echoes.

## The question

The preamble prints every card's power in full, so the name sits above an
identical clause. `Oracle` restates its function; `Pythia` pays off only from the
model's priors. **How far does the model lean on what a card is CALLED over what
it is TOLD the card does?** Anything the pair separates moved through priors and
salience, never through content.

**Direction is NOT pre-committed.** The expected sign is capability-dependent: a
model holding the myth may deduce better under proper names (salience), a model
without it may fall back more (an opaque token where a power word stood).

## The statistic

- **Primary: blind villager accuracy** - votes cast by villager seats the night
  told NOTHING, the `none` stratum under S10's told-based rule. Exactly S2's gate
  #3 statistic, computed per arm by `py -3 -m eval.s5_verdict <arm>.json`.
- **The pair's figure is the difference, `greek-named` minus `greek`**, with a
  Newcombe (Wilson-score) 95% interval for two independent proportions over
  pooled votes, and a game bootstrap beside it because votes in one game share a
  deal. **INFORMS if the interval excludes zero, in either direction. NOT SHOWN
  otherwise.** No bar on the size of a gap is declared; none may be added after.
- **Read the fallback rate FIRST, per arm.** A proper-name skin raising the
  fallback rate is itself a name-form finding and is reported as one.
- **Gate #3 per arm**, secondary: Wilson floor of blind accuracy against the
  run's own random arm on the same theme and seeds. The reference chance under
  `plurality-min2` is 35.84% (`games/changeling/RULES.md` §The chance baseline,
  2026-09-02); if either own arm disagrees with it by more than a point, the own
  arm is the bar and the reference was the thing that was wrong.

## Power, computed before the run

1.34 blind villager seat-nights per game, ~97% winnable, so 200 games per arm
yields **~260 blind votes per arm**. For two proportions near 40% that puts the
standard error of the difference at ~4.3 points and the 95% half-width near **8.5
points**. So the pair CAN show a gap of nine points or more and CANNOT settle a
smaller one. A marginal result is "not shown" and **no second pair chases it**;
the next rung on the axis is a second corpus (`journey` / `investiture`), which
tests whether any effect travels, and that is a new criterion.

## Settings - binding, from this file and nowhere else

Both live arms: `eval.run_changeling --games 200 --arm llm --backend local --model
qwen36-35b-a3b-iq3 --no-thinking --seats 5 --seed 5000 --timeout 240`, driver
defaults otherwise (`--rounds 2`, `--register character`, `--temperature 0.8`,
`--max-tokens 1536`, `--retries 2`). Seeds 5000..5199, unspent on this rung;
game i deals and samples with seed 5000+i on both arms, so the pair is same seeds,
one variable. `--theme greek` then `--theme greek-named`, serially on one card.

Controls, CPU, before either live arm: `--arm random --games 1000 --seed 5000`
on each theme. Random play does not read the names, so the two controls should
agree with each other exactly on the strata census; they are the own-arm clause
above and the instrument control for `s5_verdict`.

Recipe: `eval/runs/changeling-skin-pair.cmd`, gated on a burst probe that
requires the served model to BE `qwen36-35b-a3b-iq3`. Records
`eval/records/cl-skin-{greek,greek-named}{,-random}.json`.

## What voids it, decided in advance

- **Fallback above 10% on either arm** voids that arm's verdicts and therefore
  the pair's difference; the fallback rates themselves are still reported.
- **Recovered above 25%** is flagged beside the verdict, not a void.
- **A blind stratum under 150 votes on either arm** makes the pair REFUSED, not
  failed.
- **A missing arm is a lost pair.** The recipe refuses to start arm 2 without arm
  1's own `PARLOR DONE rc=0`, and a lone arm is reported as a lone arm - never as
  a skin read.

## Free reads off the same records, none a gate

Per arm, as S2 declared them: the `false` stratum against the `none` stratum,
the sleeper-decoy rate, diverged-vs-intact accuracy. Plus
`py -3 -m eval.changeling_audit <arm>.jsonl --reference <arm>-random.jsonl` -
the dominated-vote counts, where "voted a seat it was shown as village" is the
most direct measure of a seat acting on the name over the told fact. None gets a
bar; none may be promoted to one after the fact.

## What this does NOT compare

Not against S2's `folk` record. The abstain rule (`plurality-min2`, 2026-09-02)
changed what a vote can do since S2 was played, so S2 is a reference, not a
control, and a folk-vs-greek vocabulary read needs its own folk arm on these
seeds under HEAD - a separate row, a separate criterion.
