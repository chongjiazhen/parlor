# Belfry night coherence, own TRANSCRIPT - pre-committed session-memory criterion

Created: 2026-09-02T10:16:52Z. Not editable after launch.

Two reads on this axis are published (`docs/measurements.md` §belfry night
coherence, both sections). With the referee's earlier tellings SUPPLIED in the
ask the model held the lie on 152/163 pairs; with them WITHHELD, 94/122, below
the supplied read on non-overlapping intervals. Both criteria end on the same
sentence: neither says anything about a referee that keeps its own memory
across calls, because no arm gives it one. This is that arm.

## The question

Over a pair of consecutive false tellings to the same switched-off gauge, over
the same living neighbours, does the second repeat the first when the ask does
NOT say what the first was, but the model can see everything it has already
been asked and everything it has already answered in this game?

**The mechanism, and why it is the honest one.** The referee's calls in one
game become one conversation: every accepted ask and its reply so far ride
ahead of the night ask as earlier user and assistant turns. The harness
supplies the CHANNEL and nothing of the content - no digest, no per-seat list,
no flag saying which earlier turn matters. What the model can recall is what
it wrote, in the order it wrote it, among setup choices that have nothing to do
with the seat in question. Holding the lie here means finding its own earlier
telling to this seat in its own transcript and repeating it. That is what
"keeps its own memory" can mean for a referee that is a sequence of stateless
completions; a model that writes notes for itself is a second mechanism, with a
note-writing prompt as a second variable, and is not this arm.

What it is NOT: a claim about referee quality, about the setup choices (the
model's on this side, as in every model-adjudicator arm), or about the players,
who are random on both sides.

## The ask, and what changes

One flag, `--adjudicator-night-transcript`, off by default and refused without
`--adjudicator-night-no-prior`. Without it every existing arm is byte-identical,
including the withheld arm, and a test holds that no history is sent unless it
is on. With it:

- `ModelAdjudicator.night_transcript` keeps a per-game list of `(ask, reply)`
  for every ACCEPTED choice - setup asks included, because they are what the
  referee has said. A fallback is not the model's telling and enters nothing.
- The night ask, and ONLY the night ask, is sent with that list as earlier
  turns (`Backend.complete_meta(context, history=...)`). Setup asks feed the
  transcript and do not receive it, so the model's setup choices are asked
  exactly as on the withheld arm and one variable moves: the channel.
- Everything else is the withheld ask: same `choice_key`, same two options in
  the same seeded order, `prior` dropped at the door, same frozen
  `GAUGE_COHERENCE_RULE`. The rule text is unchanged for the reason the
  withheld criterion gives: it says "if it was told a false count before over
  these same living neighbours, tell it that count again", and whether it was
  is now something the model can find out for itself.

The referee still builds the prior list and still records every telling in
`GameRecord.gauge_told` on both arms, so the scorer reads the field it read on
2026-09-02.

**A retried ask enters the transcript as the attempt that was accepted** - the
payload carrying the referee's `refused` complaint - with the reply that
satisfied it. A transcript that showed a clean ask over a reply that was in
fact refused would be the harness editing the model's memory.

## Paired arm

Both sides run **1000 games at seeds 15000 through 15999 inclusive**: nine
seats, compact script, one talk round, random player policy. Control has the
seeded random adjudicator throughout. The model side changes the adjudicator to
local `qwen36-35b-a3b-iq3` with `--adjudicator-night
--adjudicator-night-no-prior --adjudicator-night-transcript`, sampler seed
equal to the game seed, temperature fixed at 0.0, visible thinking off; its
summary records `adjudicator_night`, `adjudicator_night_no_prior` and
`adjudicator_night_transcript` all `true` and `adjudicator_temperature: 0.0`,
the control all `false` and `null`.

Fresh seeds, for the reason the withheld criterion gives: the same seeds as
either published arm would let a reader net two model runs game for game and
call the residual "memory". The published read is the interval comparison.
1000 games because the two controls at this shape produced 158 and 159 pairs
and the model sides 163 and 122; this side's count is its own.

Cost is the withheld arm's plus the transcript: a game's referee session is a
handful of asks, so the extra context per night ask is a few hundred tokens at
most, and the model arm should run in the withheld arm's ~50 min.

Smoke before this was written: seed 13000, one game, the model's setup choices
reproduced from the withheld record, three gauge asks out under the flag, the
second and third carrying the session, all three answered legally by
`qwen36-35b-a3b-iq3`, `adjudicator integrity 0/5`, the flag in the recorded
args. Written to a scratch path, not to the bound ones.

Bound evidence paths:

~~~text
eval/records/belfry-night-transcript-control.json
eval/records/belfry-night-transcript-control.json.jsonl
eval/records/belfry-night-transcript-model.json
eval/records/belfry-night-transcript-model.json.jsonl
~~~

`py -3 -m eval.belfry_night_verdict --criterion transcript` is the controller
and `eval/runs/belfry-night-transcript.cmd` the frozen recipe. Summary
arguments and JSONL rows must establish that recipe. The instrument is the
2026-09-02 one with a third `--criterion` binding these paths, seeds and flags,
and one more comparison line described below. Its pairing, floors and voids
are unchanged and their tests still pass.

**The card.** This arm queues behind the changeling chain in flight on the
one GPU. The recipe takes an optional first argument, a log that must carry a
`PARLOR` done marker before it launches, and refuses otherwise; launching it
early costs nothing and does nothing.

## Integrity and voids

Raw JSONL is evidence. The arm is VOID, and the arithmetic still prints below
the refusal, when either side has fewer or more than 1000 rows, an errored game,
or a seed set that is not exactly 15000..15999; a launch setting that is not the
recipe, `adjudicator_night_no_prior` or `adjudicator_night_transcript` absent
or false on the model side included; player fallback strictly above 10% on
either side; model-adjudicator fallback strictly above 10%; a non-fallback gauge
choice served by any upstream other than `qwen36-35b-a3b-iq3`; a fallback event
carrying provenance; or a game whose gauge-choice event count disagrees with
its false-telling count.

**The instrument control.** The seeded-random arm on these seeds must sit at
one half: its Wilson 95% interval over its own pairs must contain one half, or
the verdict is **INSTRUMENT SUSPECT** and nothing is published above it.

## Endpoint

Unit: a pair, defined exactly as on 2026-09-02 - a false telling whose
immediately previous telling to the same seat was also false, over the same
living neighbours, and whose own source is not a fallback. Coherent when the
second count equals the first. Chance per pair is exactly one half. A pair
whose FIRST telling was a fallback is one the model never said and cannot
recall; it stays in the denominator so the unit is the published one, and at
the 0.00% adjudicator fallback both earlier arms recorded it is nothing. The
fallback rate prints beside the number either way.

Three lines are read, all pre-committed here:

1. **Against chance** - the verdict, with the first criterion's words.
   **COHERENT** only if the model arm's coherence clears one half on BOTH
   floors: the two-sided Wilson 95% lower endpoint over pairs, and the 2.5th
   percentile of a 4000-resample bootstrap over GAMES. One floor short is
   **NOT SHOWN**. No pair at all is **NO VERDICT**.
2. **Against the withheld read** - the call this arm exists for. Held against
   the published 94/122 by interval, never by point: **RECALLS** when the model
   arm's Wilson 95% lower endpoint sits above the withheld read's upper
   endpoint (83.62%); **NO RECALL** when the intervals touch or this arm sits
   below. No pair is no call.
3. **Against the supplied read** - held against the published 152/163 the same
   way: **BELOW SUPPLIED** when the model arm's whole Wilson interval sits below
   the supplied read's lower endpoint (88.32%); **AS GOOD AS SUPPLIED** when
   the intervals touch or this arm sits above.

All are quoted beside both player fallback rates, the adjudicator fallback
rate and the `source` split. A void prints every line below the refusal.

## What a result would and would not say

RECALLS + AS GOOD AS SUPPLIED says the referee holds its own lie from its own
transcript as well as it does from a reminder: the memory can be the model's,
and the harness needs to supply nothing but the channel - the strongest of the
three properties for a referee that oversees. RECALLS + BELOW SUPPLIED says
the channel carries something the model uses and a digest still beats it:
own-memory works and costs coherence, which prices the digest. NO RECALL says
the transcript bought nothing over the withheld ask - the model does not find
its earlier telling in its own words, and a referee built from stateless
completions needs the harness to remember for it. Each of the three is a fact
about this model at this size and says nothing about a model that writes
itself notes, which is a different mechanism and a different criterion.
