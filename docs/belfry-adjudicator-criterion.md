# Belfry model adjudicator - pre-committed paired-arm criterion

Created: 2026-08-31T07:49:45Z

This is the promise for S8's setup-only model-referee arm. It is committed before
that arm runs and is never edited after a record lands. A later correction gets a
new criterion and new records.

## The paired arm

Both sides run exactly 60 games at game seeds 6100 through 6159 inclusive: five
seats, compact script, one talk round, random player policy, and --no-thinking.
The control uses the seeded random adjudicator and no model route. The moved side
changes only the adjudicator to local qwen36-35b-a3b-iq3. Its sampler seed is the
game seed, visible thinking is disabled by the driver, and its temperature is
fixed in the driver at 0.0 rather than inherited from a player option. The model
summary records that effective setting as `adjudicator_temperature: 0.0`; the
control records it as null.

The intended files are:

~~~text
eval/records/belfry-adjudicator-control.json
eval/records/belfry-adjudicator-control.json.jsonl
eval/records/belfry-adjudicator-model.json
eval/records/belfry-adjudicator-model.json.jsonl
~~~

The summary launch arguments and the rows must establish that recipe. A launch
setting mismatch is not this arm.

The controller reconstructs the random setup from every seed and requires the
control deal and herring outcome to match that reconstruction. It then requires
the model and control deals to match seat for seat at each game seed. Under this
exact recipe, only the diviner's herring seam is reachable: five seats have no
outsider and compact has no mimic. These seeds deal the diviner in exactly 20
games, so the model side owes exactly 20 bounded choice events and the other 40
rows owe none.

## Integrity and voids

The JSONL is the evidence. Each summary is first checked against its own rows for
games, player decisions and fallbacks, and model-adjudicator calls, fallbacks and
recovered calls. A missing file, malformed value, or disagreement is corrupt
evidence and has no read.

The arm is VOID, with no source result, when any of these holds:

- either side plays fewer than 60 games, carries an errored game, repeats a game
  seed, omits a promised seed, or contains a seed outside 6100 through 6159;
- the control cannot be reconstructed, or paired deals differ at any seed;
- player fallback is strictly above 10% on either side;
- model-adjudicator fallback is strictly above 10%;
- a model choice opportunity has no event, an event exists with no opportunity,
  the event's menu or selected outcome disagrees with the reconstructed game, or
  its selected outcome disagrees with the referee log;
- a fallback event carries non-null model provenance, or a non-fallback event's
  upstream model identity is not exactly qwen36-35b-a3b-iq3;
- a choice event exposes an input field outside the committed provenance schema
  key, options, selected, fallback, recovered, upstream;
- the classifier labels are not balanced one random and one model trace for each
  retained (game seed, choice key), or a training seed enters the held-out set.

Exactly 10.00% is not void. Player and adjudicator rates use independent
denominators. The control adjudicator makes no calls, so its adjudicator fallback
rate is n/a, never 0%.

## Primary endpoint

One canonical trace is one legal setup call. Its classifier feature is exactly:

~~~text
(choice key, number of offered options, zero-based position selected)
~~~

The feature excludes game seed, source label, backend, model identity, upstream
provenance, response text, raw role names, and raw seat names. A model fallback
is a random choice wearing the model's label, so that trace and its paired control
trace are both removed. This preserves balanced labels and reports the removed
calls in the fallback rate.

Even game seeds are training games. Odd game seeds are held out. For each feature,
the classifier counts its empirical frequency separately in the random and model
training traces and predicts the source with the larger frequency. Equal
frequencies earn one half point. Held-out source accuracy is total points divided
by the number of held-out labelled traces.

The pre-committed chance interval is the two-sided Wilson 95% interval computed by
core.stats.wilson(N / 2, N), where N is the even number of retained held-out
labelled traces. The result is DISTINGUISHABLE only when held-out accuracy is
strictly above that interval's upper endpoint. Otherwise it is NOT SHOWN.
Either is a non-VOID criterion read.

This endpoint asks only whether the model's bounded setup choices leave a trace
distinguishable from seeded random under this recipe. It does not ask whether the
choices are better, and no win, deduction, deception, or general referee-quality
claim is inferred from it.

## Controller result

py -3 -m eval.belfry_adjudicator_verdict prints both player fallback rates, the
model adjudicator call count and fallback rate, control adjudicator n/a, retained
trace counts, split, chance interval, accuracy, and the source verdict.

Exit 0 means a non-VOID read (DISTINGUISHABLE or NOT SHOWN), 1 means missing or
corrupt evidence, 2 means a stated void, and 3 means the launch recipe does not
match this criterion.
