# What a seed pins, and where a spread estimate comes from

Measured 2026-08-27 from two complete 20-game runs. This is the strongest evidence
class in the repo - a demonstration, not a design read - and it settles one claim
while invalidating a plan that three items in `RESUME.md` were waiting on.

## The measurement

`hunt20c` (2026-08-26 14:52, 23818.2s) and `hunt20d` (2026-08-27 01:01, 23788.6s)
were run off the same code, the same `--seed 1000`, the same pinned
`qwen36-35b-a3b-iq3`, on the same box.

**All 20 game records are byte-identical.** Every winner, every vote, every
utterance, every fallback. The only difference anywhere in the two runs is 29.6
seconds of wall clock.

```
byte-identical game records: 20/20
winners identical: True
utterances identical: True
```

## What that proves

`core/backends.py` said of `Backend.seed`: "llama.cpp honours it, so a LOCAL run
becomes reproducible." That was a claim about an external system, of the kind this
repo's debugging rules say to verify rather than inherit. It is now measured, at
full run scale, and it holds exactly.

So a local run is a function of its seed. Re-running one reproduces it.

## What that costs, and the plan it invalidated

**A repeat run at the same seed cannot measure run-to-run spread.** The spread is
zero by construction, and no number of repeats changes that.

`RESUME.md` had queued `hunt20d` as "the paired re-run that measures the spread",
and hung the ONUW and cloud-arm decisions on the result. That was a contradiction
nobody caught for a day: `2cfe9d5` pinned the sampler *in order to make runs
reproducible*, and re-running to estimate variance requires them not to be. Those
two goals cannot both be served by the same pair of runs.

The 6h37m was not wasted - it bought the demonstration above, which nothing else in
the repo established - but it did not buy what it was launched for.

**The tell, for next time:** before running something to measure variability, ask
what in it is free to vary. If the answer is "nothing", the run is a reproducibility
check, and it should be described and budgeted as one.

## Where a spread estimate actually comes from

**Inside one run, by resampling games.** A run of N games at seeds `base..base+N-1`
already contains N independent deals and N independent sampler draws. The bootstrap
in `core/stats.py` resamples *games* - the unit that shares a deal, a night and a
table - and the interval it returns is the sampling-variability estimate.

`hunt20c` already reported one: blind taint sensitivity **+9.00%, 95% CI [-0.25%,
+18.18%]**. That interval was the answer to "what is the run-to-run spread" the
whole time, sitting in the report while a second run was scheduled to go and find
it.

**An independent check is still worth having, and it is a different run**: same
code, a *different* seed base (`--seed 2000`), compared against `hunt20c`. That
tests whether the within-run bootstrap is honest - a real question, since the
bootstrap assumes games are exchangeable and they may not be. It is a smaller prize
than "the spread nobody has measured", and it should not be sold as that.

## Consequences for the gates

Read off `hunt20c`'s own interval rather than waiting for a pair:

- Blind taint sensitivity is **±9pp around a +9.00% effect at n=20 games**. A
  5-seat cabal run of this size cannot show gate #3a, and a repeat at seed 1000
  would have returned the identical number rather than a second draw.
- The decision that was blocked on "the spread" - whether to keep spending GPU on
  cabal's gate #3 or move to another rung - is therefore answerable now, on
  evidence already in hand.

## Scope

**Local only.** `Backend.seed` reaches llama.cpp, which honours it. On the cloud
tiers `seed` is a best-effort hint the provider may ignore, and under a routing
alias the upstream can change between runs regardless - so cloud reproducibility is
**unproven**, and the same two-run check would have to be repeated there before any
of the above is assumed to carry over.

Nothing here says two runs of *different* seeds should agree. They should not; that
difference is the sampling variability the bootstrap estimates.
