# Belfry Model Adjudicator Design

Created: 2026-08-31T06:49:34Z

## Goal

Run S8's first model-referee arm: model chooses only belfry's existing setup
discretion, while seeded deal, player asks, gate #1 audit, and player policy stay
unchanged. Pre-commit an arm that cannot return a discretion verdict when either
model route falls back above the repo's 10% bar.

## Scope

`BelfryReferee.new()` still deals seats and creates the grimoire. The model is
called only after the legal menu for one setup choice exists. It may select one
legal menu item. It cannot name a seat or role outside that menu, alter the deal,
author public text, or access any player payload.

Four setup seams are in scope, only when their associated role is dealt:

1. SOT's false townsfolk belief from spare townsfolk roles.
2. Diviner's herring target from good seats.
3. Hermit's registration: good-as-self or evil-as one legal evil role.
4. Mimic's registration: evil-as-self or good-as one legal townsfolk role.

All later discretion remains seeded random. Per-query discretion is an explicitly
separate variant and is not introduced by this slice.

## Contract

A `ModelAdjudicator` implements `state.Adjudicator` and has one private adapter
for all four seams.

Input is a typed choice request: stable choice key, game seed, a concise
referee-only reason, and legal JSON values. It contains neither the grimoire nor
unbounded role/seat lists. Its system instruction requires exactly one JSON object
whose `choice` is one offered legal value. The model's sampler seed is game seed,
the same rule `one_game()` applies to player backends.

Output is accepted only if JSON parses and exactly selects one legal value. Parse,
schema, route, timeout, and illegal-choice failures use the existing seeded RNG
fallback for that single choice. Each call appends one referee-side provenance
event: choice key, offered legal values, response class, selected value, and
whether fallback happened. No response text enters player context, public channel,
or a model prompt after it is received.

The random arm remains `adjudicator=random` and continues to make no model calls.
`--adjudicator model` requires a distinct adjudicator backend configuration. It
does not reuse player `--temperature`, and fixes its own temperature at 0.0.

## Driver and records

`eval.run_belfry` constructs one adjudicator backend per game with that game's
seed, then passes it into `BelfryReferee.new()`. Player arm and adjudicator arm are
orthogonal. A model referee can run with random player seats, which isolates
referee discretion from player capability.

Each game record adds an optional `adjudicator` block with total calls, fallbacks,
recovered responses, and referee-side choice events. Existing records without it
remain readable. Summary scoring publishes adjudicator fallback rate separately
from player fallback rate; neither may be merged into the other denominator.

Gate #1 remains at `play_game()` and is not option-controlled. It audits each
player render exactly as before. Referee provenance is transcript-only and never
joins the audit view or a seat ask.

## Arm and criterion

Criterion and verdict script land before any model-referee run. Arm uses 60 games,
5 seats, compact script, one talk round, seed 6100, local
`qwen36-35b-a3b-iq3`, `--no-thinking`, player arm random, and model adjudicator
at temperature 0.0. Control is same recipe with random adjudicator. Same game
seeds establish identical deals; only discretion source moves.

Primary endpoint is source discriminability: a held-out classifier receives only
canonicalized referee-side choice traces, balanced random/model labels, and must
identify source above its pre-committed chance interval. This tests whether model
discretion produces a trace distinguishable from seeded random, not whether it is
better. Classifier training and test game seeds are disjoint. Label and model ID
stay outside classifier input.

Arm is VOID, and verdict script returns no source result, if any condition holds:

- fewer than 60 played games in either side;
- player fallback rate above 10% in either side;
- model-adjudicator fallback rate above 10% in model side;
- any gate #1 assertion, run error, missing provenance row, duplicate game seed,
  launch setting mismatch, or failure of control reconstruction;
- classifier sees label, backend/model identity, free-form response text, or a
  trace from a training seed.

Report both fallback rates and each call count beside outcome. At or below 10% is
not VOID. Random control's adjudicator fallback denominator is zero and is shown
as `n/a`, never 0%.

## Tests

Tests first, in this order:

1. Adapter accepts only offered choice, rejects malformed and illegal responses,
   and falls back from seeded RNG reproducibly.
2. Every seam receives a bounded menu and logs exactly one private provenance
   event when present.
3. Player prompts and audit inputs stay byte-identical between random and model
   adjudicator under a fixed mocked legal choice.
4. Driver records separate player/adjudicator integrity strata and preserves old
   records with no adjudicator block.
5. Verdict controller voids each stated condition, rejects classifier leakage,
   and reads exact-bar fallback as non-VOID.

Targeted tests run before full suite. Arm launch remains manual after criterion
commit and a local burst probe; no GPU run is authorized by this design document.

## Non-goals

No model-authored rules, narration, game resolution, player prompts, broader
role roster, per-query discretion, classifier optimization, or claim that model
discretion is good. A non-VOID discrimination result only establishes measurable
difference from random under this exact arm.
