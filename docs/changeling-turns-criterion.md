# Changeling turn-taking pair, `--turns fixed` vs `--turns random-active` - pre-committed criterion

Created: 2026-09-02. Not editable after launch. **Unlaunched** - S27's deliverable is
this file, its recipe and the code the arm needs, ready for the card once S22's
two-round `folk` record is down.

Turn-taking has four options and cabal's fixed order was never one of them on
evidence (`queue.md`, "Turn-taking has FOUR options, not two"). Random active-seat
selection with a non-advancing idle action is the cheapest of the four: a round
becomes a BUDGET of `n` speaking turns rather than one turn per seat, so the
decision count per round - and therefore the GPU bill - is unchanged, and the
only thing that moves is who holds the floor and whether a seat has to fill it.

## The question

Does drawing the floor at random, and letting the seat on it stay quiet, move
blind villager deduction? **Direction is NOT pre-committed.** Two mechanisms
point opposite ways and neither is measured here. A seat with nothing to say
currently has to invent something, which puts noise in the record that every
later seat reads; letting it listen should raise the signal-to-noise of the
transcript. Against that, a random floor means a seat can be asked twice in a
round and another not at all, so a seat holding a decisive night fact may never
be asked to state it. The pair says which dominates on this model, or says
nothing.

## The statistic

- **Primary: blind villager accuracy** per arm, the `none` stratum under S10's
  told-based rule - S2's gate #3 statistic, unchanged.
- **The pair's figure is the difference, random-active minus fixed**, Newcombe
  (Wilson-score) 95% interval over pooled votes, a paired game bootstrap beside
  it. **INFORMS if the Newcombe interval excludes zero, in either direction. NOT
  SHOWN otherwise.** No bar on the size of a gap; none may be added after.
- **Read the fallback rate FIRST, per arm.** The new ask is longer by one clause
  and offers a move the model has never been offered on this rung, so a rise on
  the random-active arm is a finding about the ask, reported as one and not
  smoothed into the deduction figure.
- **Gate #3 per arm**, secondary, against the run's own random arm on the same
  seeds (reference 35.84% under `plurality-min2`; own arm is the bar if it
  disagrees by more than a point).

## Power

As the discussion-length pair: ~260 blind votes per arm at 200 games, 95%
half-width on the difference near 8.5 points. The pair CAN show a gap of nine
points or more and CANNOT settle a smaller one. A marginal result is "not shown";
no second pair chases it.

## The payload delta - what actually moves, exhaustively

The arm is a prompt change, so the delta is named here rather than left to a
diff. **Two referee-written strings move and nothing else does**, and
`games/changeling/test_turns.py` asserts both halves of that rather than arguing
them.

1. **The discussion-opening event.** Under `fixed`: `Discussion opens: 2
   round(s), seat 0 first.` Under `random-active`: `Discussion opens: 2 round(s)
   of 5 turns; each turn the floor goes to one seat, drawn at random.` It has to
   move: leaving "seat 0 first" in place while the referee draws the floor would
   be a referee-written falsehood in a seat's context, which is a worse cost than
   a second changed line. `test_the_render_differs_by_exactly_the_opening_line`
   holds the render to this ONE line over 20 seeds and 5 seats.
2. **The DISCUSS ask, for the seat on the clock only.** Under `random-active` it
   reads `The table looks to you. Speak, or listen this turn and let the floor
   pass on.` before the same JSON envelope instruction, and closes `Keep 'say'
   under 280 characters; an empty 'say' means you listen, the table hears
   nothing, and the turn is spent.` The idle action is stated as a thing to DO,
   per `docs/model-facing-text.md`, and its cost is stated because a seat that
   does not know silence spends the floor cannot price it.

Everything else is byte-identical and tested as such: the preamble, the seat's
own line, its night reveals, the VOTE ask, and the deal itself. **The deal is the
load-bearing one.** The turn schedule draws from its own seeded stream,
`random.Random(f"changeling-turns:{seed}")`, never the deal's, so the same seed
deals the same night under either mode - `test_same_seed_deals_the_same_night_
under_either_mode` checks dealt, truth, belief and knowledge over 30 seeds. A
pair whose deals differ is not a pair.

**Non-active seats are not asked at all that turn**, and `acting_seats` says so,
which is what keeps the gate #1 audit reading exactly the seat about to be asked.
The audit covers the new ask like any other: `test_a_leaky_random_active_ask_is_
caught` puts a seat-card association into it and confirms `leak_audit` reports
it, attributed to the seat on the clock.

## Settings - binding, from this file and nowhere else

Both live arms: `eval.run_changeling --games 200 --arm llm --backend local --model
qwen36-35b-a3b-iq3 --no-thinking --seats 5 --theme folk --rounds 2 --seed 5000
--timeout 240`, driver defaults otherwise (`--register character`,
`--temperature 0.8`, `--max-tokens 1536`, `--retries 2`). Arm 1 `--turns fixed`,
arm 2 `--turns random-active`. **Seeds 5000..5199 on purpose** - arm 1 IS S22's
`cl-rounds2.json`, the two-round `folk` record on those seeds, reused rather than
replayed. Nothing new is spent on the control.

Controls, CPU: `--arm random --games 1000 --seed 5000 --theme folk --rounds 2` at
each turn mode. Arm 1's control is S22's `cl-rounds2-random.json`; arm 2's is
`cl-turns-random-random.json`. The two will NOT agree on the strata census the
way the rounds pair's two do - the random control speaks under `fixed` and can
listen under `random-active`, so its transcript differs even though its votes are
drawn the same way. That is the arm, not a fault.

`eval.turns_pair_verdict` pins every setting above against each record's own
`args` and VOIDS the read on any disagreement, before the arithmetic. **A record
whose `args` carries no `turns` key is read as `fixed`** - the flag postdates the
driver, absence can only mean the shipped order, and that is what lets S22's
record serve as arm 1 whether it was played before or after the flag landed. The
same rule voids arm 2 if its key is missing, because absence there means the run
never went through the flag at all.

## What voids it, decided in advance

- **This pair must run BEFORE the changeling source-rules merge, or it is VOID.**
  That merge changes what a seat is told the rules are, which re-baselines blind
  accuracy on both arms; a random-active arm played after it against S22's record
  played before it is two variables, and neither result is attributable. If the
  merge lands first, arm 1 is re-run under the merged rules and this criterion is
  superseded by one written after that, never edited into.
- **Fallback above 10% on either arm** voids the pair's difference; the rates are
  still reported. **Recovered above 25%** is flagged, not a void.
- **A blind stratum under 150 votes on either arm** makes the pair REFUSED.
- **A settings disagreement on either record** voids the read.
- **A missing arm is a lost pair.** The recipe refuses arm 2 without arm 1's own
  `PARLOR DONE rc=0 games=200/200`.

## Free reads, none a gate

Per arm, S2's three (`false` vs `none`, sleeper-decoy rate, diverged vs intact)
and `eval.changeling_audit` against the arm's own random control. Three more this
pair alone can make, all observational:

- **How often a live seat chooses to listen**, over turns and over seats. A model
  that never uses the idle action makes this arm a pure turn-order arm and the
  read should say so.
- **Whether the seats that go unasked in a round are the ones holding night
  facts.** A random floor can silence a spotter, and the record carries both the
  schedule's effect (`utterances` per seat) and each seat's `knowledge_class`.
- **Transcript length per game**, which is the mechanism the signal-to-noise
  argument above rests on. Shorter with no accuracy change is still a finding
  about the payload budget.
