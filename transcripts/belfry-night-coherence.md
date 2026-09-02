# Belfry night coherence - play-time discretion record

Recorded: 2026-09-02T03:30:21Z

Recipe: `eval/runs/belfry-night.cmd`.
Criterion: `docs/belfry-night-coherence-criterion.md`.
Raw evidence: untracked `eval/records/belfry-night-{control,model}.json` and
sibling JSONL files; wrapper log `eval/records/belfry-night-launch.log`.

Question graded: when a switched-off gauge is told a false neighbour count on
two consecutive nights over the same living neighbours, does the second telling
repeat the first? The referee's own model chooses each false count with every
prior telling to that seat in view (`--adjudicator-night`); the control draws it
from the seeded random adjudicator. Players are random on both sides.

~~~text
burst probe: 3/3 200 on local qwen36-35b-a3b-iq3, VERDICT: can carry a stream
both arms: 1000 games, seeds 12000..12999, nine seats, compact script, one round

control player fallback: 0/168234 = 0.00%
control adjudicator fallback: n/a (seeded random makes no calls)
model player fallback: 0/168786 = 0.00%
model adjudicator fallback: 0/2403 = 0.00%; recovered 35/2403 (sent back, then legal)
model arm wall time: 3058 s; control 35 s

gauge tellings: control 2282 (481 false, source random x481)
                model   2279 (457 false, source model x457)
chance per pair: 50.00% exactly (two false counts on the menu, the previous
  one always among them)

control pairs: 158, coherent 84 = 53.16%
  Wilson 95% [45.40%, 60.78%]  bootstrap-by-game [45.45%, 60.87%]
  contains one half: instrument control PASSES
model pairs:   163, coherent 152 = 93.25%
  Wilson 95% [88.32%, 96.19%]  bootstrap-by-game [86.90%, 98.62%]
  both floors clear one half
VERDICT: COHERENT
~~~

Both counts were re-derived from the JSONL by an independent pass over
`gauge_told` (same pair definition, written separately from the verdict tool)
and came back identical: 158/84 and 163/152.

Outcomes for context only, not a finding: control good 557, evil 442, one
day-bound; model good 540, evil 459, one day-bound. Random players on both
sides, so the win split is the deal's and the referee's setup choices, not play.

## Two seats, read off the record

Game 10 (seed 12010), seat 4, a held lie. True count on nights 1 and 2 was over
neighbours 3 and 5; the model told 0 both nights. Night 3 the neighbours had
changed to 0 and 5, so the third telling is not a gradable pair.

~~~text
night 1  neighbours [3, 5]  told 0  false  model
night 2  neighbours [3, 5]  told 0  false  model     <- pair, coherent
night 3  neighbours [0, 5]  told 0  false  model     (neighbours moved, no pair)
~~~

Game 148 (seed 12148), seat 0, one of the 11 breaks. Nights 2 and 3 share
neighbours 1 and 7; the model told 2, then 0.

~~~text
night 1  neighbours [1, 8]  told 2  false  model
night 2  neighbours [1, 7]  told 2  false  model
night 3  neighbours [1, 7]  told 0  false  model     <- pair, broken
~~~

Meaning: a bounded play-time choice can be governed by a stated policy across
calls when the referee supplies the memory. The model broke the lie on 11 of
163 pairs, so this is a strong tendency and not a guarantee. It says nothing
about whether the model would hold a lie it had to remember unaided; the arm
that withholds `prior` is the one that would. It is not a claim about referee
quality, deduction, deception, or wins.
