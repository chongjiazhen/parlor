# Belfry S8b setup-only adjudicator - source-discrimination record

Recorded: 2026-08-31T12:56:05.2915812Z

Recipe: `eval/runs/belfry-adjudicator-v2.cmd`.
Criterion: `docs/belfry-adjudicator-v2-criterion.md`.
Raw evidence: untracked `eval/records/belfry-adjudicator-v2-{control,model}.json`
and sibling JSONL files.

~~~text
control player fallback: 0/2809 = 0.00%
control adjudicator fallback: n/a (random control makes no calls)
model player fallback: 0/2809 = 0.00%
model adjudicator fallback: 0/20 = 0.00%

20 paired legal traces after dropping model fallback pairs
train: even game seeds; test: odd game seeds (18 balanced labelled traces)
chance interval: [29.03%, 70.97%] (Wilson 95% at 9/18)
source accuracy: 88.89%
VERDICT: DISTINGUISHABLE
~~~

Meaning: bounded setup-choice traces differ from seeded random under this recipe.
No choice-quality, referee-quality, deduction, deception, or win claim follows.
