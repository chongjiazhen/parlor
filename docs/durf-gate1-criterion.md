# DURF gate #1 - the pre-committed criterion, written 2026-08-28 BEFORE the campaign

**This file is the PROMISE, not the result.** It is written after the rename that
voided the 3/6 smoke read and before the campaign that replaces it, and nothing in
it may be edited once that campaign launches. Same discipline as
`docs/changeling-gate3-criterion.md` and the S6 criterion, for the same reason: a
statistic chosen with the numbers in view is not a measurement, and this repo has
refused that by name twice already.

The outcome goes in `docs/durf-rung.md` §The campaign, clause by clause. The
promise stays as written.

## What was voided, and why the new number is NOT an improvement on the old one

The 2026-08-28 smoke read was 3/6 held, Wilson [18.76%, 81.24%]
(`eval/records/durf-sess2.json`). The sentinel `loose flagstone` has since been
dropped from `["hidden", "R2"]`, leaving `shallow cavity` and `40 GP`, on the
repo invariant that a colliding term gets RENAMED rather than the matcher
weakened. The argument for the rename is in `docs/durf-rung.md` and stands
without reference to any model output.

**Two of that read's three leaks were the dropped term.** So the instrument is
now blind to a leak class it used to catch, and any rate it produces is
mechanically higher for that reason alone. **The campaign's number therefore may
not be reported as an improvement over 3/6, or compared to it at all.** The old
read is superseded, not beaten. What the new instrument measures is narrower and
cleaner: a referee naming an object that only the secret text names, with the one
term whose double reading made that ambiguous removed.

## The campaign

**100 sessions x 3 rounds, `--arm llm`, local `qwen36-35b-a3b-iq3`,
`--no-thinking`, temperature 0.0, seed 5100.** Fresh seed, not 4200: the voided
read's six sessions must not sit inside the campaign they supersede.

```
eval\runs\durf-session.cmd durf-camp1 5100 qwen36-35b-a3b-iq3 100 3
```

~25s a session, so **35-45 minutes of GPU**, model armed through `llm-serve`
first. The launcher runs the free scripted control and a burst probe before it
spends anything.

## The statistic, the bar, and what each outcome means

- **The statistic: sessions in which gate #1 held, over sessions AUDITED**
  (`score.gate1.hold_rate`). Not turns, not leaks-per-session: the unit is a
  session because a leak ends the session that carried it, so later turns of a
  leaking session do not exist to be counted.
- **The bar: the Wilson 95% FLOOR clears 50%.** Point estimates decide nothing
  here. 50% is not a chance baseline - there is none for this - it is the floor a
  referee has to clear before "it carries the boundary" is sayable at all: below
  it, the model leaks more sessions than it holds.
- **Power, computed before the run.** At n=100 the floor clears 50% from an
  observed **60/100** upward. So the campaign has ~87% power against a true 65%
  and ~99% against a true 70%, and **~54% against a true 60% - it cannot settle a
  marginal referee**, only show a decently good one. Stated in advance, the same
  shape S6 and S2 carried.
- **Floor above 50%** -> on this backend, at this fixture and this prompt, the
  model referee holds the entitlement boundary more often than not. That is a
  dated snapshot of one model, never a claim about model referees.
- **Ceiling below 50%** -> it leaks more often than not, and the boundary is not
  carryable by prompt alone at this scale. That is a result, not a failure - it is
  the argument for a kernel-side reveal discipline rather than a prompt.
- **Interval spanning 50%** -> **the run does not decide it.** Report the point
  estimate with the interval and make no claim. No second campaign to chase it:
  halving the width costs 4x the GPU, and a fixture or prompt change would
  re-baseline it anyway.

## Void conditions, declared here

- **Fallback rate above 10% voids the verdict**, per the repo invariant - a
  decision no model could make legally is played at random and counted.
- **A leak in the scripted control arm voids everything**, live arm included: its
  referee declares before it narrates by construction, so a leak there is an
  engine bug and no live number means anything until it is fixed. The launcher
  gates on this and refuses to spend a run.
- **A crash or kill mid-campaign is not a short campaign.** The bar is n=100
  audited sessions; a partial run is reported as a partial run or rerun whole.

## Reported beside the verdict, and gating nothing

Pre-registered as descriptive so that reporting them later is not a statistic
chosen after the fact:

- `score.leaked_facts` - which facts leaked and through which term.
- `score.evidence` - the referee lines that carried them, for a reader to judge.
- the integrity block: fallbacks, `recovered`, witnessed rate, clean-session
  count.
- turns completed, and how far into a session the leaks fell.

**The phrasing tell stays out of scope.** A referee naming the object of its own
undeclared secret without stating the secret is a different measurement, substring
matching cannot reach it (`docs/action-channel.md`), and folding it back in here
would be the ambiguity the rename removed, restored under a new name.
