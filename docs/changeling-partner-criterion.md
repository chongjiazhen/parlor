# Changeling partner protection - the pack statistic as PRIMARY, pre-committed criterion

Created: 2026-09-03T05:25:31Z. Not editable after launch. **Unlaunched.**
Arithmetic `eval.partner_verdict`, recipe `eval/runs/changeling-partner-arm.cmd`,
both written 2026-09-03 and both bound by this file - the verdict pins the
record's own `args` back against §Settings and a test reads THIS file to hold the
two equal, so a launcher default cannot quietly outvote the criterion again.

Two pairs have now moved the same pack statistic as a FREE READ, on two unrelated
axes, and neither could promote it: the skin pair's primary and the rounds pair's
primary are both blind villager accuracy, a VILLAGE statistic, and both criteria
declare the audit free and forbid a bar after the fact. This file exists to make
that statistic primary ONCE, on seeds nothing has played, so the next time it
moves the number is quotable.

## The question

**Does a live pack seat protect the fellow it was told, relative to random play
on the same deal?** `eval.changeling_audit`'s `partner` check: a pack seat that
was shown a `fellow-pack` at the meet, and voted that seat. Voting the partner is
dominated whatever the cards did - if the fellow still holds pack the vote helps
the village, and if the switcher moved the card it is a wasted draw at a seat the
wolf KNOWS went to sleep as pack - so the rate is a behaviour, never a skill.

**Direction is NOT pre-committed**, and the two-sided interval below is the
criterion's word. The prior leans one way and is deliberately not spent: all four
live changeling arms to date sit at or BELOW their control and none above.

## What this does NOT ask

**Which axis causes it.** Four arms on seeds 5000..5199 split 2-2 and no single
variable separates them (`docs/measurements.md`, 2026-09-03):

| arm | partner | own control | arm - control |
|---|---|---|---|
| `folk` rounds 2 | 15.66% | 25.69% | **-10.03%** [-15.44%, -3.62%] |
| `greek-named` rounds 2 | 13.64% | 25.69% | **-12.05%** [-17.21%, -5.85%] |
| `greek` rounds 2 | 24.75% | 25.69% | -0.94% [-7.27%, +6.14%] |
| `folk` rounds 3 | 24.75% | 26.82% | -2.07% [-8.42%, +5.03%] |

Name form is causal in one comparison and inert in the other; round count the
same. **An arm that chased the axis would be a pair, would cost twice, and would
rest its control on an effect that has never been pre-registered even once.**
This criterion establishes the effect exists on a fixed configuration. The axis is
a later pair against THIS record, and it is out of scope here.

## The statistic

- **Primary: the partner-vote rate, arm minus its own random control**, Newcombe
  (Wilson-score) 95% over the two proportions. **INFORMS if the interval excludes
  zero, in either direction. NOT SHOWN otherwise.** No bar on the size of the gap;
  none may be added after.
- **Read the fallback rate FIRST.** Above 10% voids the difference; the rate is
  still reported.
- **Blind villager accuracy is a free read here**, the exact reversal of the two
  pair criteria. Reported per arm against the same 35.84% reference, carrying no
  verdict in this file: a gate #3 call belongs to a criterion that made it primary.

## Power - and why the control is not the term to spend on

~198 partner-eligible votes at 200 games (measured: 198/200 on all four arms
above), against ~798 in a 1000-game control. Half-width on the difference
**5.9 points**, minimum detectable effect at 80% power **8.7 points**. That
arithmetic reproduces the observed instrument exactly - the folk rounds-2 free
read returned [-15.44%, -3.62%], a half-width of 5.91 - so the power section is
checked against the tool rather than asserted.

Both effects seen so far (-10.0, -12.1) clear it; **a 5-point gap cannot be
settled by this arm and a marginal result is NOT SHOWN.** No second arm chases it.

The control carries only ~26% of the variance, so raising it is nearly free and
nearly pointless: 2000 games buys 0.4 points of half-width and 4000 buys 0.6.
**It stays at 1000 games**, which is what every other changeling control on this
rung runs, and comparability is worth more than the fourth decimal.

## Settings - binding, from this file and nowhere else

Arm: `eval.run_changeling --games 200 --arm llm --backend local --model
qwen36-35b-a3b-iq3 --no-thinking --seats 5 --theme folk --rounds 2 --seed 17000
--timeout 240`, driver defaults otherwise (`--register character`,
`--temperature 0.8`, `--max-tokens 1536`, `--retries 2`). Record
`eval/records/cl-partner.json`.

Control, CPU: the same line with `--arm random --games 1000 --seed 17000`, record
`cl-partner-random.json`. **The seed is the arm's**, so the first 200 deals are
the arm's deals and the eligibility census is a property of the deal, not of play.

**Seeds 17000..17999 are fresh** - the arm takes 17000..17199 and the control the
full thousand, and no record in `eval/records/` occupies any of it (checked
2026-09-03 by enumerating every record's own `seed` and `games`; the highest
changeling block ends at 5999, the highest belfry block at 16399). The four arms
this file reasons from are all on 5000..5199 and are SPENT: re-reading them is the
thing this criterion exists to replace, and a 1000-game control at base 5000
already runs to 5999, so the neighbouring block was never as free as it looked.

`--seed` seeds the sampler as well as the deal, per `AGENTS.md`; a record whose
`args` disagree with the block above is VOID before the arithmetic, and
`eval.partner_verdict` pins every field the way `eval.rounds_pair_verdict` does.

**This configuration is `cl-rounds2`'s, on new seeds, on purpose.** The primary is
therefore a pre-registered REPLICATION of an unadjusted free read - which is the
only honest thing to do with a finding of that provenance, and is why no new axis
is introduced in the same file.

## Entry condition - before the source-rules merge

**This arm must run while the rung plays the rules `cl-rounds2` played.** The
primary is a replication of that configuration, and the changeling source-rules
merge adds an `identity`-class reveal that moves the strata. The control is this
arm's OWN, so the merge would not VOID the difference - which is the trap. It
would leave every number readable and quietly change what is being replicated.
The card is otherwise free of it: the recipe refuses while
`eval/records/cl-chain-tail.log` lacks `PARLOR TAIL DONE`.

## What voids it, decided in advance

- **Fallback above 10%** voids the difference. **Recovered above 25%** is flagged,
  not a void.
- **Fewer than 150 partner-eligible votes** makes the read REFUSED.
- **A settings disagreement on either record** voids the read.
- **A census disagreement between arm and control** on the eligible count over
  the shared 200 deals voids the read: random play does not speak, so the two must
  agree exactly there, and a disagreement means the deal moved under the arm.

## Free reads, none a gate

The audit's `shown-village` check beside the primary; blind villager accuracy and
its strata; `eval.changeling_claims`; and the PRICE column the audit already
prints - how often the dominated vote landed on a seat holding pack at dawn
anyway. All observational, all unadjusted, and **the criterion forbids promoting
any of them after the fact** - which is the rule that sent the partner vote here
in the first place.
