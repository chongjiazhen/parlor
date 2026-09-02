# Belfry night coherence, prior WITHHELD - pre-committed memory criterion

Created: 2026-09-02T03:44:10Z. Not editable after launch.

The 2026-09-02 read (`docs/belfry-night-coherence-criterion.md`, COHERENT at
152/163) had the referee hand the model its own earlier tellings in every ask.
Its last section names this arm: the same ask with `prior` withheld. That read
measured whether a stated policy governs a play-time choice when the memory is
supplied; this one measures what the supplied memory was worth.

## The question

Over a pair of consecutive false tellings to the same switched-off gauge, over
the same living neighbours, does the second repeat the first when the ask does
NOT say what the first was?

**Read what that can and cannot mean before reading the number.** Every
adjudicator call is a fresh completion. Nothing carries between calls but the
bytes of the ask, so with `prior` withheld the model has no channel to the
earlier telling at all. Coherence here cannot come from memory; it can only
come from the choice being a stable function of what the ask still carries -
the seat, the night, the living neighbours, the true count, and the menu order.
Two things make that non-trivial. The offered order is seeded from `(seed,
seat, night)` and so differs between the two nights of a pair at chance, and
the `night` field differs by construction. So a referee that picks by position
lands at one half, one that picks by content (always the lower count, always
the count nearest the truth) lands at one, and one that reads the night number
into its choice lands anywhere. The arm therefore answers: **is the model's
false count a function of the board's content, or of the ask's incidentals?**
That is a fact about whether `prior` is load-bearing in the instrument, and it
is the honest version of "would it hold a lie unaided" - the unaided referee
cannot remember, it can only be consistent.

What it is NOT: a claim about referee quality, about the setup choices (the
model's on this side, as in every model-adjudicator arm), or about the players,
who are random on both sides.

## The ask, and what changes

One flag, `--adjudicator-night-no-prior`, off by default and refused without
`--adjudicator-night`. Without it every existing arm is byte-identical,
including the supplied-memory arm, and a test holds that the default still sends
`prior`. With it, `ModelAdjudicator.gauge_false_count` drops the `prior` key
from the board at the door and changes nothing else: same `choice_key`, same
two options in the same seeded order, same `board` fields otherwise, same
frozen `GAUGE_COHERENCE_RULE`. The referee still builds the prior list and
still records every telling in `GameRecord.gauge_told` on both arms, so the
scorer reads the same field it read on 2026-09-02.

**The rule text is unchanged on purpose.** It says "if it was told a false
count before over these same living neighbours, tell it that count again", and
the ask no longer says whether it was. One variable moves. A rule rewritten to
fit the withheld ask would be a second variable, and the smoke on the first arm
showed that a rule steering toward an unavailable answer measures the rule.

## Paired arm

Both sides run **1000 games at seeds 13000 through 13999 inclusive**: nine
seats, compact script, one talk round, random player policy. Control has the
seeded random adjudicator throughout. The model side changes the adjudicator to
local `qwen36-35b-a3b-iq3` with `--adjudicator-night --adjudicator-night-no-prior`,
sampler seed equal to the game seed, temperature fixed at 0.0, visible thinking
off; its summary records `adjudicator_night: true`,
`adjudicator_night_no_prior: true` and `adjudicator_temperature: 0.0`, the
control `false`, `false` and `null`.

Seeds move because the deals must not be the 2026-09-02 deals: a pair of runs
over the same seeds would let a reader net the two arms game for game and call
the residual "memory", when it is a difference between two model runs on the
same boards. The published read is the comparison, not the partner. 1000 games
because the first control produced 158 pairs at this shape and the model side
163; this side's own count is its own.

Smoke before this was written: 3 games at seeds 13000..13002 with the flag,
`adjudicator integrity 0/9`, three gauge asks out and answered legally, the
flag in the recorded args. Written to a scratch path, not to the bound ones.

Bound evidence paths:

~~~text
eval/records/belfry-night-noprior-control.json
eval/records/belfry-night-noprior-control.json.jsonl
eval/records/belfry-night-noprior-model.json
eval/records/belfry-night-noprior-model.json.jsonl
~~~

`py -3 -m eval.belfry_night_verdict --criterion withheld` is the controller and
`eval/runs/belfry-night-noprior.cmd` the frozen recipe. Summary arguments and
JSONL rows must establish that recipe. The instrument is the 2026-09-02 one
with two additions: a `--criterion` switch binding these paths, seeds and
flags, and one comparison line described below. Its pairing, floors and voids
are unchanged and their tests still pass.

## Integrity and voids

Raw JSONL is evidence. The arm is VOID, and the arithmetic still prints below
the refusal, when either side has fewer or more than 1000 rows, an errored game,
or a seed set that is not exactly 13000..13999; a launch setting that is not the
recipe, `adjudicator_night_no_prior` absent or false on the model side
included; player fallback strictly above 10% on either side; model-adjudicator
fallback strictly above 10%; a non-fallback gauge choice served by any upstream
other than `qwen36-35b-a3b-iq3`; a fallback event carrying provenance; or a game
whose gauge-choice event count disagrees with its false-telling count.

**The instrument control.** The seeded-random arm on these seeds must sit at
one half: its Wilson 95% interval over its own pairs must contain one half, or
the verdict is **INSTRUMENT SUSPECT** and nothing is published above it.

## Endpoint

Unit: a pair, defined exactly as on 2026-09-02 - a false telling whose
immediately previous telling to the same seat was also false, over the same
living neighbours, and whose own source is not a fallback. Coherent when the
second count equals the first. Chance per pair is exactly one half.

Two lines are read, both pre-committed here:

1. **Against chance** - the verdict, with the first criterion's words.
   **COHERENT** only if the model arm's coherence clears one half on BOTH
   floors: the two-sided Wilson 95% lower endpoint over pairs, and the 2.5th
   percentile of a 4000-resample bootstrap over GAMES. One floor short is
   **NOT SHOWN**. No pair at all is **NO VERDICT**.
2. **Against the supplied-memory read** - the call this arm exists for.
   Held against the published 152/163 by interval, never by point:
   **NEEDS MEMORY** when the model arm's whole Wilson 95% interval sits below
   the supplied read's Wilson lower endpoint (88.32%); **HOLDS UNAIDED** when
   the intervals touch or this arm sits above. No pair is no call.

Both are quoted beside both player fallback rates, the adjudicator fallback
rate and the `source` split. A void prints both lines below the refusal.

## What a result would and would not say

COHERENT + HOLDS UNAIDED says the model's false count is a content function of
the board, and `prior` bought little: the referee is consistent without being
reminded, which is the stronger property for a referee that oversees. COHERENT
+ NEEDS MEMORY says consistency survives but degrades without the reminder, and
the supplied field is doing measurable work. NOT SHOWN + NEEDS MEMORY says the
2026-09-02 result was the supplied memory, not the model: the referee follows a
reminder and has no stable policy of its own, which bounds "oversight" for this
model at "does what the ask says this call". None of the three says anything
about a referee that keeps its own memory across calls, because no arm here
gives it one; that is a different mechanism, and a different criterion.
