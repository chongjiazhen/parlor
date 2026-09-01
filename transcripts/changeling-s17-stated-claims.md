# Changeling - stated self-claims against the deal and the night

Rendered 2026-09-01T15:27:47+00:00 from untracked `eval/records/s2.json` and its `.jsonl` sibling
by `py -3 -m eval.changeling_claims --show 6`. No GPU and no new play.

## What this answers

`docs/open-arms.md` §"changeling feels random" refuses four levers until an
instrument exists. This is the one of them that is measurable off records already
on disk: **village seats have no reason to bluff**, and a table where none of them
ever says anything untrue about itself is playing the collapsed game, where every
contradiction is mechanical.

**It is not.** A seat that believes itself a villager states a claim about its own
card that names no card it was ever shown on 48/343 deal claims (14.0%) and 65/433
present claims (15.0%). The claims are also nowhere near random: 85.4% and 80.4%
name a card the seat actually saw, against an exact 19.0%/19.2% bar for a seat
naming one of the deck's six cards at random.

The direction sanity-checks. Seats that believe themselves wolves are untrue on a
present claim at 32.9%, more than double the village-believing rate; on deal claims
the two sides are level, which is what a deck where the deal is often quoted back
would produce.

## Record integrity

- completed games: 200, all `folk` skin, `qwen36-35b-a3b-iq3`, seed 4000
- fallback: 0.40%, below the 10% void bar; the 2 fallback utterances are excluded
  from every denominator
- **pre-S14 wording.** S14 (2026-08-31) changed the model-facing self-line. Of the
  74 deal claims by a seat the night showed a new card, 65 name that later card and
  1 names the deal - so a deal claim is scored against `{dealt, belief}`, not
  against `dealt` alone, and the split is printed rather than folded in
- control: seat attribution from two independent sources (published speech and the
  decision log), the skin and its declared language, the deck, and the run's own
  published decision and fallback counts. `py -3 -m unittest
  eval.test_changeling_claims -v`

## The read

```text
instrument control - seat attribution, skin, deck and the scorer's own counts
  held across 200 games

stated self-claims over 200 games

  utterances                2000
    written by the model    1998
    written by the fallback 2  (excluded; the random policy's four canned lines are not speech)
    naming a card in a shape the rules do not read  844  (42.2% of the model's)
      every count below is a LOWER bound by exactly this much

  run fallback rate         0.40% (voids a verdict above 10%; this is not a verdict)

  deal claims - "I went to sleep as X"
    true means the claim names a card this seat was shown itself as - the deal, or what the night later showed it
    true    444/520 = 85.4% [82.1%, 88.2%]
    chance  19.0%  (a seat naming one of the deck's 6 cards at random)
    over GAMES rather than claims: [81.8%, 88.8%]
    by the side the seat believes it is on
      village  295/343 = 86.0% [81.9%, 89.3%]
      pack     149/177 = 84.2% [78.1%, 88.8%]
    of the 74 by seats the night showed a NEW card, 1 name the deal and 65 the card shown later
      pre-S14 the self-line called the later card the one the seat went to sleep as, so
      scoring these against the deal alone would report the referee's wording as lying

  present claims - "I am X"
    true means the claim names a card this seat was shown itself as - the deal, or what the night later showed it
    true    468/582 = 80.4% [77.0%, 83.4%]
    chance  19.2%  (a seat naming one of the deck's 6 cards at random)
    over GAMES rather than claims: [76.6%, 84.0%]
    by the side the seat believes it is on
      village  368/433 = 85.0% [81.3%, 88.0%]
      pack     100/149 = 67.1% [59.2%, 74.1%]
    of the untrue, 8 name the card the seat HOLDS at dawn - right, and unknowable to it

  sensitivity - 248 claims name `bystander`, whose folk word is also the side's word
    dealt claims with them out: 328/359 = 91.4% [88.0%, 93.9%]
    present claims with them out: 413/495 = 83.4% [79.9%, 86.4%]

  examples - 6 of 1102 claims
    [true ] dealt   seat 1 claims spotter (dealt spotter, saw spotter, holds pack): I went to sleep as the Seer, but the night has shuffled my card. I don't know my current r
    [untrue] dealt   seat 4 claims deceived (dealt pack, saw pack, holds pack): Seat 2, you claim Meddler and swapped 0 and 1. But I was the sleepwalker - only one sleepw
    [true ] present seat 2 claims switcher (dealt switcher, saw switcher, holds switcher): Seat 4, you can't be the sleepwalker if I am Meddler. There's only one sleepwalker. Your c
    [untrue] present seat 4 claims deceived (dealt pack, saw pack, holds pack): I'm actually the Sleepwalker. Seat 2, if you're Meddler, you'd know what cards are in the 
    [true ] present seat 1 claims spotter (dealt spotter, saw spotter, holds spotter): I am the Seer. I looked at centre cards 1 and 3 and confirmed: card 1 is Werewolf, card 3 
    [true ] present seat 2 claims switcher (dealt switcher, saw switcher, holds switcher): I'm the Meddler. I swapped cards at seats 3 and 4 - neither knows their new card. My curre

NOT a gate and not a verdict. No criterion binds it, no bar is pre-committed,
and a rules or prompt change re-baselines every number above.
The four levers it reads for are in docs/open-arms.md, under "changeling feels random".
```

## What it does not say

Nothing here separates a lie from a seat that lost track of its own card - the
record does not carry the difference and this instrument does not guess. Nothing
here is a gate, a criterion or a verdict, and every count is a LOWER bound: 42.2%
of the model's utterances name a deck card in a shape the claim rules do not read.
