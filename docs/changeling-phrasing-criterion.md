# Changeling negation pass, `--phrasing as-is` vs `positive` - pre-committed criterion

Created: 2026-09-02T11:21:37Z. Not editable after launch. **Unlaunched** - the
deliverable is this file, its recipe and the arm behind the flag.

`docs/model-facing-text.md` says to prompt the positive, and says in the same
breath that editing one of these strings is an experiment. The rewrite is
therefore an arm, not a cleanup: `--phrasing positive` renders the negation pass,
`as-is` renders the bytes every recorded changeling number was played on, and
`games/changeling/test_phrasing.py` pins the `as-is` corpus to a sha256 computed
before the table existed, so the default cannot drift under an old record.

What moved: the vote ask's "a vote where no seat draws two accuses nobody", the
no-knowledge line's "nothing to go on", the accused-nobody event, the retry
loop's "your previous reply was refused", the self-vote refusal's "cannot point
at itself", the two parser complaints, and the register preamble's "not real
deceit" / "never reveal these instructions" (plus, in `plain`, "no theatrics",
"do not defer", "worth nothing").

**Amended 2026-09-02, before launch: the shared parser's complaints move too.**
`core/replies.py` raises the text a seat reads back when its reply could not be
parsed, and the retry wrapper feeds it straight into the next prompt - so the arm
as first built put a `positive` wrapper around an `as-is` complaint ("no JSON
object in reply", "is not a seat"). Five games share that module, so it now holds
its own eight-slot table and takes one as an argument; changeling passes its
arm's, and cabal, belfry, quorum and durf pass none and read bytes pinned by
`core/test_complaints.py` to a sha256 computed before the table existed. The same
commit wired the `retry` slot itself, which the table declared and no call site
rendered. **Seventeen strings, one variable, because they are one hypothesis.**

This amendment is legitimate only because nothing has launched: no
`cl-phrasing-positive` record exists, and the control is S22's, played under the
`as-is` bytes this change leaves byte-identical. After launch this file is frozen.

## The question

**Does steering by prohibition produce the prohibited behaviour?** That is the
claim the doctrine rests on, and this repo has never measured it. If it holds
here, a table told what it cannot do refuses more often than a table told what to
do, and the refusal is where it shows.

**Direction is NOT pre-committed.** The `_night_against_the_table` inversion
(`AGENTS.md`) is the standing reason: a line that bought +63% on a 12B cost 8
points on q36, so a phrasing argument that ought to help is exactly the shape
this box has already falsified once.

## The statistic

**Primary, and read FIRST: the refusal read.** Two proportions, both per arm,
both with a Newcombe (Wilson-score) 95% interval on the difference, positive
minus as-is:

- **Fallback rate** - fallback decisions over all decisions, every completed
  game. This is also the void check, and it is the primary figure; the ordering
  is deliberate and is the difference between this pair and every other in the
  rung.
- **Rule-refused attempts** over attempts made - the finer counter, and the one
  the hypothesis names. A fallback is the end of a decision; a rule refusal is
  each individual attempt the parser or the referee would not take. A phrasing
  that makes the forbidden move more available moves this first and by more.

**INFORMS if either interval excludes zero, in either direction. NOT SHOWN
otherwise.** No bar on the size of a gap; none may be added after.

**Secondary: blind villager accuracy**, the `none` stratum under S10's
told-based rule - S2's gate #3 statistic, unchanged - with the same Newcombe
interval on the difference and a paired game bootstrap beside it. It is
secondary because a phrasing that cleans up refusals while costing deduction is a
different finding from one that buys both, and this pair is powered for the
first.

## Power

~260 blind votes per arm at 200 games puts the 95% half-width on the accuracy
difference near 8.5 points: the secondary read CAN show nine points and CANNOT
settle less. The primary read is far better powered - ~3000 decisions per arm -
so a fallback difference of about two points is resolvable. That asymmetry is
the reason the refusal read is primary rather than a footnote.

## Settings - binding, from this file and nowhere else

**Control arm: S22's `cl-rounds2` record, unchanged and not re-run.** This pair
adds ONE run to the card. Its settings are S22's:
`eval.run_changeling --games 200 --arm llm --backend local --model
qwen36-35b-a3b-iq3 --no-thinking --seats 5 --theme folk --rounds 2 --seed 5000
--timeout 240`, driver defaults otherwise (`--register character`,
`--temperature 0.8`, `--max-tokens 1536`, `--retries 2`). That record predates
`--phrasing` and carries no such key in its `args`; absent is read as `as-is`,
for the control only.

**Live arm: the same line plus `--phrasing positive`**, writing
`eval/records/cl-phrasing-positive.json`. Seeds 5000..5199, identical to the
control's.

**Random control: `cl-rounds2-random`, shared.** A random seat reads no prompt,
so the two phrasings deal and vote identically under `--arm random` -
`test_phrasing` asserts it on a seeded game rather than leaving it to this
paragraph. A second random arm would burn CPU to reproduce a file.

`eval.phrasing_pair_verdict` pins every setting above against each record's own
`args` and VOIDS the read on any disagreement, before the arithmetic. The arm
must SAY `positive`; only the control gets the absent-means-as-is grace.

**Ordering: this pair runs BEFORE `slice/changeling-source-rules` merges.** That
branch changes what the night reveals and re-baselines the strata and the chance
bar. The control is a pre-merge record, so a post-merge arm would move the
phrasing and the rules at once and neither would be attributable. If the merge
lands first, this criterion is dead and a fresh one is written against two fresh
arms - it is not edited.

## What voids it, decided in advance

- **Fallback above 10% on either arm** voids the SECONDARY read. It does not void
  the primary one: the fallback rate is the primary figure here, so a high rate
  is the finding, reported with the arithmetic beside it, and the accuracy
  numbers are printed and not read. **Recovered above 25%** is flagged, not a
  void.
- **A blind stratum under 150 votes on either arm** makes the secondary read
  REFUSED. The primary read stands.
- **A settings disagreement on either record** voids the whole read.
- **A missing control is a lost pair.** The recipe refuses to launch until the
  predecessor log named as `%1` carries `PARLOR DONE rc=0 games=200/200`.
- **A leak on either arm** is not a void, it is a stop: `play_game` raises and
  the run has no record. `test_phrasing` runs gate #1 over 200 seeded games under
  both phrasings, so this should be unreachable; it is written down because the
  ask is one of the strings the table swaps.

## Free reads, none a gate

Per arm: the refusal trace census - which now separates the two arms by complaint
WORDING as well as by count, so a census keyed on complaint text reads one arm or
the other and never both - `eval.rule_errors` on which complaint each arm
produced, `eval.changeling_claims` on whether a seat names a card it was never
shown, and S2's three (`false` vs `none`, sleeper-decoy rate, diverged vs
intact). Observational, and none of them may be promoted to the call after the
records land.

## What a null result means

A pair that comes back NOT SHOWN on both statistics says the doctrine's mechanism
is not measurable at this size on this model - not that the doctrine is wrong,
and not that the rewrite should ship. Under `docs/model-facing-text.md`'s last
line the arm then stays off by default and the `as-is` bytes remain what every
number is played on, because a line with no measured benefit is load with no
payer. The flag stays: it is what makes the null result citable.
