# Belfry steered discretion S23 - pre-committed criterion

Created: 2026-09-01T16:05:53Z. Not editable after launch.

S23 asked for a narrow, gradable quality question about belfry's referee
discretion, without any general-referee claim. The first half of the work was
finding that the obvious form of that question has no answer on this rung, and
the criterion below is what is left once that is faced.

## Why this is not a quality rubric

S8b measured the model's bounded setup choices as DISTINGUISHABLE from seeded
random (88.89% held-out source accuracy over a 70.97% chance ceiling,
`docs/measurements.md`). Different is not better, and nothing on the frozen
compact five-seat recipe can make it better, because **the choice has no quality
ordering to grade**:

- The herring is the diviner's false positive and nothing else. `Grimoire.
  registers_demon` is the only reader of `grim.herring`, it applies the herring
  only when an asker is named (`for_seat`), and `night.divine` is its only such
  caller. The duelist's day power asks without an asker, so the false read cannot
  kill anybody.
- At five seats the compact distribution deals no outsiders, so the menu is
  exactly the three townsfolk, all alive, one of them the diviner. Nothing in the
  board makes one of the three a worse or better place for a read that only the
  diviner will ever see, and whose bite depends entirely on which seats that
  diviner later picks.

So a rubric over the board would be scoring exchangeable options, and a scorer
that found a difference would be reporting the seat-index prior S8b already
reported. Grading which placement a referee *should* prefer would need a ground
truth for refereeing taste that nobody here has, and inventing one and then
scoring a model against it is the general-referee claim S23 was written to avoid.

**What survives is a narrower question with a real answer:** when the referee is
given the board and one stated placement rule, does its discretion FOLLOW the
rule? That is gradable exactly, has a chance baseline that needs no taste, and it
is the part of "a referee that oversees without micromanaging" that a run can
actually buy - a referee whose discretion cannot be governed by a stated policy
is not overseeing anything.

## The rule

Frozen as `games.belfry.adjudicator.HERRING_STEER_RULE`, sent with every steered
setup choice:

> Place the false demon read on the good seat sitting nearest the demon's seat
> around the circle. If two are equally near, take the lower seat number.

`preferred_herring` is its one implementation, and the scorer's whole ground
truth. The rule names exactly one seat on every board, so the per-call chance is
`1/3` on a three-option menu.

**The rule's CONTENT is a probe, not a claim.** This document does not assert that
the nearest good seat is a better placement than any other - by the section above,
it is not. What the rule buys is that it cannot be applied without reading the
board, so compliance separates a referee that used what it was told from one that
did not.

## The ask, and what changes

Two model-facing changes, both off by default (`--adjudicator-steer`), so every
existing arm is byte-identical without the flag:

- The ask gains `board` (`{"seats": 5, "demon_seat": <index>}`) and `rule` (the
  text above). The board is referee-side fact. It reaches the referee's own model
  and nothing else: no seat ask, neither public channel, not the audit input
  (`games/belfry/RULES.md` §Discretion), and a test holds that boundary.
- The menu is offered in an order seeded from the game seed
  (`random.Random(f"belfry-ask:{seed}:{key}")`), not sorted. This is a control,
  not a variable: S8b showed this model's blind choices carry a position or
  seat-index prior, and against a sorted menu such a prior could score against a
  rule it never read. Shuffled, any fixed position strategy sits at exactly 1/3.

**This arm is therefore NOT a one-variable delta from S8b, and it is not read
against S8b.** It is read against its own chance baseline. The blind arm's 0/20
fallback is quoted beside the steered rate as the cost-of-steering line only.

## Paired arm

Both sides run 360 games at seeds 6100 through 6459 inclusive: five seats, compact
script, one talk round, random player policy, `--no-thinking`. Control has a
seeded random adjudicator. The steered side changes only the adjudicator, to local
`qwen36-35b-a3b-iq3` with `--adjudicator-steer`, sampler seed equal to the game
seed, temperature fixed at 0.0. Its summary records `adjudicator_temperature: 0.0`
and `adjudicator_steer: true`; control records `null` and `false`.

360 games is not 60 for one reason: only a game seating a diviner asks the
question at all, roughly one in three, and the read needs a denominator that can
separate 1/3 from a rate worth naming. The GPU cost is the ask count, not the game
count - S8b's 60 games spent 20 calls in 24 s.

Bound evidence paths:

~~~text
eval/records/belfry-steering-control.json
eval/records/belfry-steering-control.json.jsonl
eval/records/belfry-steering-model.json
eval/records/belfry-steering-model.json.jsonl
~~~

`py -3 -m eval.belfry_steering_verdict --criterion s23` is controller, and
`eval/runs/belfry-steering.cmd` is the frozen recipe. Summary arguments and JSONL
rows must establish that recipe. The controller reconstructs the control arm from
every seed, requires paired deals to match seat-for-seat, and rebuilds the offered
menu order from the seed rather than trusting the record's own.

## Integrity and voids

Raw JSONL is evidence. The controller reconciles summary against rows first.
Missing, malformed or disagreeing evidence is corrupt and gets no read.

The arm is VOID when either side has fewer than 360 games, an error, or a
duplicate, missing or out-of-range seed; reconstruction or paired deal mismatch;
an offered menu that is not the seeded order; a menu that is not exactly three
options; player fallback above 10%; steered adjudicator fallback above 10%; a
missing, extra or mismatched setup event; a fallback event carrying upstream
provenance; a successful event from another upstream; an event field outside
`key, options, selected, fallback, recovered, upstream`; an event that disagrees
with the referee's own log line; or no scored steered call at all. Exactly 10.00%
is not void. Control adjudicator rate is n/a, never 0%.

**One further void, and it is the instrument control that matters here.** The
seeded-random arm plays the same boards against the same rule and has no rule to
follow, so its compliance IS the chance rate. If it falls outside its own Wilson
95% interval at `wilson(N // 3, N)`, the rule is not chance-neutral on these
deals and no steered number above that bar would mean anything - so the read stops
there rather than publishing one.

## Endpoint

Over every steered call that is not a fallback, and its paired control call:
compliance is `selected == preferred_herring(...)`. A fallback is the seeded menu
wearing the model's name, so it leaves both the numerator and the denominator, and
its paired control call goes with it.

Verdict is **STEERED** only if steered compliance is strictly above the two-sided
Wilson 95% upper endpoint from `core.stats.wilson(N // 3, N)` at the realized
scored-call count `N`. Otherwise **NOT SHOWN**. Both are non-VOID reads.

This tests whether bounded setup discretion follows a stated rule when the board
is in the ask. It does not test whether the rule is good refereeing, and it
establishes nothing about choice quality, deduction, deception, wins, or general
referee performance.
