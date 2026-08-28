# Gate #3b called - 2026-08-27, the S6 campaign

**Gate #3b is NOT SHOWN, and cabal's GPU program stops here.** That is the
pre-committed answer to a marginal landing, written before either arm ran, and it
is being applied rather than revisited.

Every number below is recomputable from records already on disk, no new games:

```
py -3 -m eval.s6_verdict
```

It reproduces each arm's published summary from that arm's own per-game records
before deriving anything, and exits non-zero if the reconstruction stops checking.
A verdict that retires a gate should not rest on arithmetic nobody can re-run.

## The criterion, and what each clause returned

Pre-committed 2026-08-27 in `queue.md`, BEFORE the run, on the same discipline as
the 2026-08-25 criterion that held.

| clause as written | what landed |
|---|---|
| 40 games, `--seed 2000` then `--seed 3000`, code frozen between them | 40/40 completed, `rc=0` both arms, code frozen at `2c0e2a3` throughout |
| 3b holds only if the hunter's Wilson 95% floor clears the S3-derived bar, `1/len(legal_targets)` | floor **25.82%** against a bar of **33.33%** - does not clear |
| expect ~20 hunts at the observed 0.50 hunts/game | **20 hunts**, exactly the assumed rate |
| if it lands marginal the answer is "not shown", and cabal stops anyway | it landed marginal; that is this document |

The hunt, pooled over the campaign as the criterion specifies:

| arm | hunter | Wilson 95% |
|---|---|---|
| seed 2000 | 1/4 = 25.00% | [4.56%, 69.94%] |
| seed 3000 | 8/16 = 50.00% | [28.00%, 72.00%] |
| **pooled, 40 games** | **9/20 = 45.00%** | **[25.82%, 65.79%]** |

The bar is derived, not assumed: all 20 hunts recorded a legal target set of 3, so
`1/len(legal_targets)` evaluates to 1/3 here. A variant that changes what the night
says - 7p, or a blind-evil `stray` - moves the bar and the scorer reads it off the
records rather than off this sentence.

Campaign integrity: **62/4588 decisions fell back to random (1.35%)**, 100% served
by `qwen36-35b-a3b-iq3`, an order of magnitude under the 10% void bar. Nothing here
is voided.

## The denominator held, and that is what makes this a clean refusal

After arm 1 returned only 4 hunts in 20 games, `queue.md` projected ~8 for the
campaign and warned that S6 was "on course to return not shown for reasons of
denominator, not of hunter skill". **That projection was wrong and this verdict
does not inherit it.** Arm 2 returned 16 hunts, the campaign returned 20, and 20 is
exactly the 0.50 hunts/game the power table assumed.

| arm | hunts/game | evil win rate |
|---|---|---|
| seed 2000 | 0.20 | 85.00% |
| seed 3000 | 0.80 | 60.00% |
| campaign | **0.50** | 72.50% |

A hunt only happens when good completes its missions, so the hunt count is bounded
by good's mission record - which is why a single arm cannot project it, and why the
two arms sit four-fold apart. The lesson is narrower than "arm 1 was unlucky": **a
rate whose denominator is another gate's outcome is not projectable from one draw**,
and the file said so with one draw in hand.

So the campaign was tested at the sample it budgeted for. Against the power table
computed before the run, 20 hunts is enough to clear the bar at a true 55% (18
needed) and not at 50% (27) or 45% (57). The hunter came in at 45%. **The gate
failed on hunter skill at a sample the criterion called adequate, not on a thin
denominator** - which is a stronger negative result than the one arm 1 predicted.

## What gate #3b is allowed to be reported as

> Across 40 games on a pinned local model, the hunter identified the seer on 9 of
> 20 hunts (45.00%, Wilson 95% [25.82%, 65.79%]) against a derived chance baseline
> of 33.33%. The interval's floor does not clear the baseline, so the gate is not
> shown. The campaign's budget was pre-committed before the run and no further
> games were bought after seeing the result.

That paragraph is the whole claim. It is not "the hunter is at chance" - the point
estimate sits 11.7 points above the bar and the interval is wide enough to contain
both a strong hunter and a bad one. It is that **40 games cannot separate those two
cases**, which the power table said before the run and is the reason the budget was
fixed in advance rather than extended.

**Read it beside the denominators in `docs/reference-policies.md`, never in place of
them.** Two results there change what a reader may conclude from a hunter at 45%:
the hunter derives *zero* bits mechanically in `SETUP_5` - proved by exhaustion over
192,000 deal-and-history combinations, not measured - so whatever it is doing is
behavioural, necessarily. And a 60-line heuristic reading the same records hits
94.3% where the model hits 48.3%. The gate's own number is the pre-committed one;
those two are the denominator beside it.

## The three draw-dependent items, resolved

All three were `hunt20c` observations that `hunt20d` reproduced byte for byte,
which said nothing - a same-seed re-run replays the same calls
(`docs/reproducibility.md`). Each asked for a different seed base. S6 is it, and
each was scored against a trigger written down before this draw existed.

**Step, not slope - the trigger did NOT fire.** It required a third flat or *rising*
1→2 leg in the blind approval-by-taint table. Four runs, recomputed from records:

| run | taint 0 | taint 1 | taint 2 | 1→2 leg |
|---|---|---|---|---|
| `hunt20b` | 93.18% | 70.00% | 77.42% | +7.4% |
| `hunt20c` | 82.00% | 63.79% | 64.00% | +0.2% |
| `hunt6a` | 77.50% | 65.85% | 64.29% | -1.6% |
| `hunt6b` | 81.25% | 68.09% | 61.29% | **-6.8%** |

The legs run +7.4, +0.2, -1.6, -6.8 - noise around a small negative, not a step. The
scorer note in `_blind_line` stands as written and `taint_sensitivity` needs no
caveat about a non-monotone table. **This closes code-debt item 5 with no code
change**, which is the outcome a pre-stated trigger is for: the item existed
precisely so the note would not be retargeted on the two draws that flattered it.

**The `five_rejects` shift is not established.** Four runs of 20 at the same setup:

| run | `five_rejects` | `missions_failed` | `hunt_hit` |
|---|---|---|---|
| `hunt20b` | 0/20 | 9 | 6 |
| `hunt20c` | 6/20 | 5 | 5 |
| `hunt6a` | 6/20 | 10 | 1 |
| `hunt6b` | 2/20 | 2 | 8 |

0, 6, 6, 2. Arm 1's match with `hunt20c` was read as the second draw confirming a
real shift; arm 2 undercuts it at 2/20. Evil's win path varies run to run at this N
and no run of 20 pins it. Deadlocking the table is a real path - 8/40 across the
campaign - but "it became evil's main path" is a statement one draw cannot carry.

**Run-length degradation did not reproduce.** `hunt20c` ran 0.83% over games 0-6
against 2.32% over games 7-19, and that 2.8x jump was the whole basis for treating
the fallback rate as partly a function of run length.

| run | games 0-6 | games 7-19 | last 5 |
|---|---|---|---|
| `hunt20c` | 0.83% | 2.32% | 2.73% |
| `hunt6a` | 0.88% | 0.99% | 1.12% |
| `hunt6b` | 1.44% | 1.81% | **1.20%** |

Both S6 arms are near-flat and arm 2's last five games run *below* its own
games-7-19 rate. So `hunt20c`'s jump was that run's own, not a property of a 20-game
run against this server. **Do not carry a run-length caveat into future runs**; the
fallback rate is still reported per run, which is what catches it if it returns.

## What this does not license

- **It does not re-specify a gate.** The criterion is reported in the words it was
  pre-committed in. The solver and heuristic denominators are additive, and the
  discipline constraint in `docs/reference-policies.md` governs.
- **It does not reopen gate #3a.** S1 abandoned 3a on sample grounds - the only
  unconfounded cell accrues at 0.3-0.4 votes per game and no table size fixes it -
  and nothing here touches that. Arm 2's blind taint sensitivity clears zero
  (+10.38% [+2.34%, +18.88%]) where arm 1's did not (+6.57% [-0.71%, +13.71%]);
  that is two draws disagreeing on a statistic 3a was retired over, and it is
  recorded rather than promoted.
- **It does not settle gate #2.** Evil won 72.50% [57.16%, 83.89%] across the
  campaign, and gate #2 remains conditional on gate #3 by measurement: with good
  voting at chance, evil wins ~65% with no deception at all. An evil win rate above
  that baseline while good is at chance says the good side lost, not that the evil
  side deceived.
- **It is a dated snapshot of one checkpoint, not parlor's result.** Gates #2 and #3
  measure a model; S1 already found identical prompts scoring -0.2% on a 12B against
  +66% on 120B-class, and that capability tell is not unique to this repo. Gate #1 -
  that a seat's un-entitled secrets are absent from the bytes sent to its model - is
  the durable one, and no run here bears on it either way.

## What stops, and what does not

cabal's GPU program is finished. No third campaign, no larger table bought to
rescue this number, and the re-homed prompt variables (negation pass, notebook,
theme polarity, mini-personas) stay on changeling where a paired arm is ~30 minutes
against cabal's 13.2 hours.

What the campaign leaves behind is usable: 40 games of frozen-code records at two
seed bases, at 1.35% fallback, on a pinned model with 100% attribution - the corpus
the solver and heuristic rungs score against, and the second draw three open items
were waiting on. All three are now closed.
