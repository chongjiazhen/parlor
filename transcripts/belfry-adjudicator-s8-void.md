# Belfry S8 setup-only adjudicator - void record

Recorded: 2026-08-31T12:51:51.7954079Z

Recipe: `eval/runs/belfry-adjudicator.cmd`.
Criterion: `docs/belfry-adjudicator-criterion.md`.
Raw evidence: untracked `eval/records/belfry-adjudicator-{control,model}.json`
and sibling JSONL files.

~~~text
control player fallback: 0/2809 = 0.00%
control adjudicator fallback: n/a (random control makes no calls)
model player fallback: 0/2809 = 0.00%
model adjudicator fallback: 12/20 = 60.00%
adjudicator route: local qwen36-35b-a3b-iq3, temperature 0.0 fixed by the driver

VOID: model adjudicator fallback rate 60.00% is above 10%
~~~

Burst probe served `qwen36-35b-a3b-iq3` 3/3 times. One reproduced failed choice
reply was:

~~~json
{"choice": "3"}
~~~

It was enclosed by a Markdown `json` fence in transport. S8's parser required a
bare JSON object, so it substituted its seeded random fallback. This is a void
finding about response formatting; it does not establish a model discretion read.
