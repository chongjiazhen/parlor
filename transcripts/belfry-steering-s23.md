# Belfry S23 steered discretion - rule-application record

Recorded: 2026-09-01T16:21:13Z

Recipe: `eval/runs/belfry-steering.cmd`.
Criterion: `docs/belfry-discretion-quality-criterion.md`.
Raw evidence: untracked `eval/records/belfry-steering-{control,model}.json` and
sibling JSONL files.

Rule stated in every steered ask: place the false demon read on the good seat
sitting nearest the demon's seat around the circle; if two are equally near, take
the lower seat number.

~~~text
control player fallback: 0/16568 = 0.00%
control adjudicator fallback: n/a (random control makes no calls)
steered player fallback: 0/16568 = 0.00%
steered adjudicator fallback: 0/152 = 0.00%
steered adjudicator recovered: 0/152 = 0.00%

152 scored steered calls after dropping fallback pairs
menu of 3, offered in a seeded order: chance is 1/3 for any fixed seat-index
  or list-position prior
control compliance: 49/152 = 32.24% (instrument control, inside its chance interval)
chance interval: [25.93%, 40.71%] (Wilson 95% at 50/152)
steered compliance: 70/152 = 46.05%
VERDICT: STEERED
~~~

Meaning: bounded setup discretion follows a stated placement rule above chance
when the board is in the ask. It is not a quality, referee-quality, deduction,
deception or win claim, and the rule's content is a probe rather than a claim
about good refereeing.

**Read the size, not only the verdict.** The referee ignores the rule on 82 of
152 calls. What clears the bar is a tendency, not compliance; anything that needs
the rule OBEYED - a policy the referee must not break - is not evidenced here.
