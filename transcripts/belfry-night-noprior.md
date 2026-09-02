# Belfry night coherence, prior WITHHELD - play-time discretion record

Recorded: 2026-09-02T05:18:35Z

Recipe: `eval/runs/belfry-night-noprior.cmd` at `819963d`.
Criterion: `docs/belfry-night-noprior-criterion.md`.
Raw evidence: untracked `eval/records/belfry-night-noprior-{control,model}.json`
and sibling JSONL files; wrapper log `eval/records/belfry-night-noprior-launch.log`.
The first launch, which died on gate #1 at game 400, is kept whole in
`eval/records/void-13400/`.

Question graded: the same pair as the 2026-09-02 supplied-prior read - two
consecutive false tellings to one switched-off gauge over the same living
neighbours - with the ask no longer carrying the seat's prior tellings. Every
call is a fresh completion, so this grades whether the model's false count is a
content function of the board, not whether it remembers.

~~~text
burst probe: 3/3 200 on local qwen36-35b-a3b-iq3, VERDICT: can carry a stream
both arms: 1000 games, seeds 13000..13999, nine seats, compact script, one round

control player fallback: 0/166782 = 0.00%
control adjudicator fallback: n/a (seeded random makes no calls)
model player fallback: 0/167780 = 0.00%
model adjudicator fallback: 0/2335 = 0.00%; recovered 23/2335
model arm wall time: 2969 s; control 30 s

gauge tellings: control 2287 (460 false, source random x460)
                model   2211 (384 false, source model x384)
chance per pair: 50.00% exactly

control pairs: 159, coherent 81 = 50.94%
  Wilson 95% [43.24%, 58.60%]  bootstrap-by-game [43.31%, 58.48%]
  contains one half: instrument control PASSES
model pairs:   122, coherent 94 = 77.05%
  Wilson 95% [68.83%, 83.62%]  bootstrap-by-game [68.75%, 85.09%]
  both floors clear one half
VERDICT: COHERENT

against the supplied-memory read 152/163 = 93.25% [88.32%, 96.19%]:
  withheld upper endpoint 83.62% < supplied lower endpoint 88.32%
CALL: NEEDS MEMORY
~~~

Both counts were re-derived from the JSONL by a separate pass over `gauge_told`
and came back identical: 159/81 and 122/94.

Outcomes for context only: control good 521, evil 479; model good 514, evil
486; no day-bound game on either side. Random players on both sides.

## The relaunch is under the fix, and the fix is minimal

The first launch raised `LeakDetected` at seed 13400: a night-3 lie told the
sot "Seat 2 is the Fiend." while seat 2 was the heir, and the heir succeeded on
night 5. Under `819963d` a minion is never lied about as the demon. Game 400 of
this record is that board, and the same line now reads:

~~~text
discretion: seat 3 is the sot and believes it is the oracle
night 3: seat 3 <- Seat 2 is the Witness.   (FALSE - its ability is off)
discretion: seat 2 (heir) becomes the demon
~~~

Every other row is byte-identical to the void run: all 1000 control games and
the 399 model games the first launch completed. The false-role draw indexes the
script's roles with the demon last, so removing it changes a draw only where the
draw would have landed on the demon, which is exactly the leak case. In the
control's 1000 games, no false Fiend-telling names a minion.

## Two seats, read off the record

Game 0 (seed 13000), seat 4, held across three nights over neighbours 3 and 5:
told 1, 1, 1. Two gradable pairs, both coherent.

Game 30 (seed 13030), seat 0, neighbours 1 and 8 all three nights: told 0, 0,
then 2. The first pair holds, the second breaks.

Meaning: without the reminder the model still holds the lie on 77% of pairs,
well above chance, so its false count is mostly a content function of the
board. It is measurably below the 93% it held with `prior` in view, on
non-overlapping intervals, so the supplied field is doing real work. Neither
number says anything about a referee that keeps its own memory across calls;
no arm here gives it one.
