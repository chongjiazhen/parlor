# Belfry night coherence - pre-committed play-time discretion criterion

Created: 2026-09-02T02:20:58Z. Not editable after launch.

`games/belfry/RULES.md` §Discretion names per-query discretion a variant axis to
measure, and gives the reason a referee's discretion at play time is worth
anything at all: "a seat that reads evil on Tuesday and good on Wednesday is
noise nobody can reason against, and the whole value of an ambiguous seat is
that its owner can build a consistent story on it." Every model-adjudicator arm
so far (S8b, S23) moved SETUP choices, taken once. This is the first arm on the
play-time axis, scoped to one sentence.

## The question

When a switched-off gauge must be told a false neighbour count night after
night, does the model referee HOLD the lie? Concretely: over a pair of
consecutive false tellings to the same seat, counted over the same living
neighbours, does the second repeat the first?

That is gradable without inventing a taste: the rung's own text says coherence
is the value, the true count is a function of the neighbours so it is the same
on both nights, the menu is the two other counts, and the previous false count
is always one of them. **Chance per pair is exactly one half**, whatever the
deal, whatever the seat count.

What it is NOT: a claim that the model referees well, a claim about the roles it
was not asked about (pointing lies, the mortician's, the diviner's flip all stay
on the seeded draw), or a claim about the players, who are random on both sides.
It is the smallest thing that says whether bounded play-time discretion can be
governed across calls - the part of "oversees without micromanaging" that
needs the referee to remember what it said.

## The ask, and what changes

One flag, `--adjudicator-night`, off by default; without it every existing arm
is byte-identical, including the RNG stream (`ModelAdjudicator.gauge_false_count`
without `night` is `rng.choice(options)` and nothing else, and a test holds it).
With it, each false gauge count is a model call:

- `choice_key: gauge_false_count`, `options`: the two false counts as strings,
  offered in an order seeded from `(seed, seat, night)` so a position prior sits
  at exactly one half.
- `board`: the seat, the night, its living neighbours, the true count, and
  `prior` - every count this seat's gauge was told before, each with its
  neighbours and whether it was true. Referee-side facts: they reach the
  referee's own model and nothing else - no seat ask, neither public channel -
  and a test holds that boundary.
- `rule`: `games.belfry.adjudicator.GAUGE_COHERENCE_RULE`, frozen. It restates
  the RULES sentence as an instruction and says what to do when there is no lie
  to hold. **The smoke found why that clause is there:** the first wording said
  only "tell it the same count it was told before", the seat's two prior
  tellings had been TRUE, the model answered with the true count three times
  and fell back. A rule that steers into an illegal answer measures the rule.

The referee records every gauge telling on BOTH arms in `GameRecord.gauge_told`
(seat, night, neighbours, count, truthful, source), so control and model are
read off one field by one instrument. `source` is `random`, `model` or
`fallback`.

## Paired arm

Both sides run **1000 games at seeds 12000 through 12999 inclusive**: nine
seats, compact script, one talk round, random player policy. Control has the
seeded random adjudicator throughout. The model side changes the adjudicator to
local `qwen36-35b-a3b-iq3` with `--adjudicator-night`, sampler seed equal to the
game seed, temperature fixed at 0.0, visible thinking off; its summary records
`adjudicator_temperature: 0.0` and `adjudicator_night: true`, the control
`null` and `false`. Setup discretion on the model side is the model's too,
as in every model-adjudicator arm; no steering rule is sent.

Nine seats, not the five the earlier arms froze, because the stratum lives on a
seat that is switched off two nights running over the same neighbours, and at
five seats there is no outsider slot and so no sot. Measured before this was
written, seeded random at seed 8000: **150 nine-seat compact games produced 51
false gauge tellings and 24 gradable pairs**, against 1 pair at seven seats
and 1 in S23's 360 five-seat games. So 1000 games is expected to yield on the order of 160 pairs on the control; the
model side's count is its own, because its setup choices move the sot's belief.
The GPU cost is the ask count: roughly 340 gauge asks plus one sot belief per
game and a herring where a diviner is dealt.

Bound evidence paths:

~~~text
eval/records/belfry-night-control.json
eval/records/belfry-night-control.json.jsonl
eval/records/belfry-night-model.json
eval/records/belfry-night-model.json.jsonl
~~~

`py -3 -m eval.belfry_night_verdict` is the controller and
`eval/runs/belfry-night.cmd` the frozen recipe. Summary arguments and JSONL
rows must establish that recipe.

## Integrity and voids

Raw JSONL is evidence. The arm is VOID, and the arithmetic still prints below
the refusal, when either side has fewer or more than 1000 rows, an errored game,
or a seed set that is not exactly 12000..12999; a launch setting that is not the
recipe; player fallback strictly above 10% on either side; model-adjudicator
fallback strictly above 10%; a non-fallback gauge choice served by any upstream
other than `qwen36-35b-a3b-iq3`; a fallback event carrying provenance; or a game
whose gauge-choice event count disagrees with its false-telling count. A row
without `gauge_told` predates the instrument and is refused outright.

**The instrument control.** The seeded-random arm plays the same recipe with
no rule to follow, so its coherence IS the chance rate. Its Wilson 95% interval
over its own pairs must contain one half, or the verdict is **INSTRUMENT
SUSPECT** and nothing is published above it.

## Endpoint

Unit: a pair - a false telling whose immediately previous telling to the same
seat was also false, over the same living neighbours, and whose own source is
not a fallback. Coherent when the second count equals the first.

Verdict is **COHERENT** only if the model arm's coherence clears one half on
BOTH floors: the two-sided Wilson 95% lower endpoint over pairs, and the 2.5th
percentile of a 4000-resample bootstrap over GAMES (pairs in one game share a
deal and a poisoner). One floor short is **NOT SHOWN**. No pair at all is
**NO VERDICT**. All three are non-void reads and are quoted beside both player
fallback rates, the adjudicator fallback rate and the `source` split.

## What a result would and would not say

COHERENT says a bounded play-time choice can be governed by a stated policy
across calls, with the memory supplied by the referee. It does not say the
model would hold a lie it had to REMEMBER itself, and a follow-up that withholds
`prior` is the arm that would. NOT SHOWN says this model, at this size, does not
hold it even when reminded - which bounds what "oversight" can mean for it. The
control's own rate sitting at one half is what makes either reading a reading
of the model and not of the deal.
