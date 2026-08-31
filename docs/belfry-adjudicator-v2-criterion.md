# Belfry model adjudicator S8b - pre-committed paired-arm criterion

Created: 2026-08-31T12:51:51.7954079Z

S8's 2026-08-31 pair is VOID: model adjudicator fallback was 12/20 (60.00%).
The route served the committed upstream but returned a whole fenced `json` block,
while the old parser accepted only a bare object. Those records remain evidence
for S8 and are not re-scored here.

This is a new arm. It binds parser grammar before new records exist: a legal model
reply is one JSON object with exactly `choice`, either bare or enclosed by a whole
` ```json ` fence. Prose outside the fence, another fence label, extra keys,
non-string choices, and choices outside the offered menu all fall back. The parser
normalizes response formatting only; no model-facing byte changes.

## Paired arm

Both sides run 60 games at seeds 6100 through 6159 inclusive: five seats, compact
script, one talk round, random player policy, and `--no-thinking`. Control has a
seeded random adjudicator. Model side changes only adjudicator to local
`qwen36-35b-a3b-iq3`, sampler seed equals game seed, and temperature is fixed at
0.0. Its summary records `adjudicator_temperature: 0.0`; control records null.

Bound evidence paths:

~~~text
eval/records/belfry-adjudicator-v2-control.json
eval/records/belfry-adjudicator-v2-control.json.jsonl
eval/records/belfry-adjudicator-v2-model.json
eval/records/belfry-adjudicator-v2-model.json.jsonl
~~~

`py -3 -m eval.belfry_adjudicator_verdict --v2` is controller. Summary arguments
and JSONL rows must establish this recipe. It reconstructs control from every seed
and requires paired deals to match seat-for-seat. Compact five-seat setup reaches
only diviner herring registration: exactly 20 choice events, 40 no-event rows.

## Integrity and voids

Raw JSONL is evidence. Controller first reconciles summary against rows. Missing,
malformed, or disagreeing evidence is corrupt and gets no read.

Arm is VOID when either side has fewer than 60 games, error, duplicate/missing/
out-of-range seed; reconstruction or paired deal mismatch; player fallback above
10%; model-adjudicator fallback above 10%; missing/extra/mismatched setup event;
fallback event with upstream provenance; successful event from another upstream;
event field outside `key, options, selected, fallback, recovered, upstream`; or
unbalanced classifier labels/training contamination. Exactly 10.00% is not void.
Control adjudicator rate is n/a, never 0%.

## Endpoint

One legal setup call yields `(choice key, offered-option count, zero-based selected
position)`. Feature excludes seed, source, backend, model identity, provenance,
response text, role names, and seat names. Model fallbacks and paired controls are
removed. Even seeds train empirical per-feature source frequencies; odd seeds are
held out. Larger frequency predicts source, ties score half. Verdict is
DISTINGUISHABLE only if held-out accuracy is strictly above two-sided Wilson 95%
upper endpoint from `core.stats.wilson(N / 2, N)`. Else NOT SHOWN. Both are
non-VOID reads.

This tests whether bounded setup choices differ from seeded random, not quality,
wins, deduction, or general referee performance.
