# Changeling mixed cells, the rung against a LIVE opponent - pre-committed criterion

Created: 2026-09-02T11:50:46Z. Not editable after launch. **Unlaunched** - the
deliverable is this file, the two arms and their recipe, ready for the card.

`docs/control-ladder.md` names the failure this arm exists to close, and
`docs/measurements.md` §"changeling heuristic rung" measures it on this game: a
hand-written rung seated against the RANDOM control is partly reading its own
twin. The random policy never claims a deal, so the ladder's fourth tier - a seat
that claimed no deal - points at a random wolf by its silence, and the
`heuristic-village` cell's 77.36% blind accuracy falls to 31.62% with that tier
switched off. cabal's 99.5% hunter is the same artifact one game over. Both
existing changeling cells hold a policy against a control that cannot talk. This
one replaces the control with seats that can.

## The question

**Does the rung's advantage survive an opponent that speaks?** Direction is NOT
pre-committed, and the two arms can disagree with each other. A live side that
claims deals removes the silence the rung reads, which should cost the rung. A
live side that claims deals badly - inconsistently, or in a grammar the ladder
refutes - hands the rung evidence the random control never offered, which should
pay it. Both are findings, and neither is the one this file is written to expect.

## The arms

Two, each seating one side live against the rung by DAWN TRUTH, the seating rule
every mixed arm in this driver already uses (`eval.run_changeling.build_policies`):

| arm | live seats | rung seats | the rung's side |
|---|---|---|---|
| `mixed-village` | village | pack | PACK, so its figure is the pack win rate |
| `mixed-pack` | pack | village | VILLAGE, so its figure is the village win rate |

## The statistic

**Primary: the rung's win rate against live seats, against its win rate against
its own twin.** One figure per arm, and the twin control is the same number read
off the all-heuristic record.

- `mixed-village`: the rung's pack win rate, against the all-heuristic arm's
  56.09%.
- `mixed-pack`: the rung's village win rate, against the all-heuristic arm's
  43.91%.

Wilson 95% interval on each rate over the arm's own scored games; the difference
carries a Newcombe (Wilson-score) 95% interval. **INFORMS if that interval
excludes zero, in either direction. NOT SHOWN otherwise.** No bar on the size of
a gap, and none may be added after.

**The control is `eval/records/cl-heuristic.json`, RESCORED on its first 200
games.** That record is 1000 games on seeds 5000..5999 and these arms play
5000..5199, so the record as written is a 1000-game figure over a superset of
these seeds and is NOT the paired control. Rescore
`eval/records/cl-heuristic.json.jsonl` entries `game` 0..199 through
`eval.run_changeling.score` and pair against that. The published 56.09% / 43.91%
are the wider-interval reference and are reported beside the paired figures, never
in place of them.

**Secondary, `mixed-pack` only: the rung's blind villager accuracy**, against the
same 200-seed rescore of `cl-heuristic.json` (49.26% at 1000 games) and against
`cl-heuristic-village.json`'s 77.36% versus the random pack. This is the artifact
read directly: the gap between 77.36% and whatever the rung scores against seats
that talk is the size of the silence tier's contribution, priced against a live
opponent instead of against a switch.

**Free read, neither arm's gate: the tier census.** `docs/measurements.md` records
tier 3 firing 0/111 on a sleeper every time in a mixed arm, because seated by dawn
truth the only liars against a random control are sleepers. Live seats can lie
while holding the pack card, so this arm is the first place tier 3 can catch a
true wolf. Reported as a count, gating nothing.

## Read the fallback rate FIRST, and read the LIVE side's own

The run-level `fallback_rate` is diluted here and understates the live side by
roughly the ratio of table size to live-seat count: every seat's decision enters
the denominator and a rung seat never falls back, so a five-seat game with two
live seats reports about two fifths of the live side's real rate. **The bar is on
the live side's own rate**, computed from the JSONL: take each game's `truth` map,
select the seats on the live side for that arm, and divide `fell_back` decisions
at those seats by all decisions at those seats. The run-level figure is reported
beside it and is not the number that voids anything.

## Power

200 games at five seats, of which roughly 195 are scored (RULES.md measures 2.8%
seating no pack at dawn). A win rate near 50% carries a Wilson half-width near 7
points, so the Newcombe interval on the difference against a 200-game control is
near 10 points. **The pair CAN show a gap of ten points or more and CANNOT settle
a smaller one.** A marginal result is not shown, and no second pair chases it.

## Settings - binding, from this file and nowhere else

Both arms: `eval.run_changeling --games 200 --backend local --model
qwen36-35b-a3b-iq3 --no-thinking --seats 5 --theme folk --rounds 2 --seed 5000
--timeout 240`, driver defaults otherwise (`--register character`,
`--temperature 0.8`, `--max-tokens 1536`, `--retries 2`). Arm 1
`--arm mixed-pack`, arm 2 `--arm mixed-village`. Seeds 5000..5199, the same seeds
every changeling live arm on this box plays.

Records `eval/records/cl-mixed-{village,pack}.json`. Recipe
`eval/runs/changeling-mixed.cmd <predecessor-log>`, which refuses without the
argument, refuses while the named log carries no `PARLOR DONE rc=0`, refuses on an
existing record, burst-probes the tier, and gates arm 2 on arm 1's own
`PARLOR DONE rc=0 games=200/200` rather than on a wrapper exit code.

## Launch order - this arm runs BEFORE the source-rules merge

Its control is `cl-heuristic.json`, which was recorded on branch
`slice/changeling-heuristic` under the CURRENT night rules. The changeling
source-rules half (`queue.md`: a lone `pack` views one centre card at MEET,
`spotter`/`swapper`/`switcher` declinable) moves the strata and the chance
baseline, so it re-baselines the rung and every record taken against it. **The
control is pre-merge, therefore these arms must run pre-merge**, and they join the
skin pair, S22 and the gate #2 arm in the set the merge waits on. Running them
after the merge does not produce a weaker result, it produces an unpaired one: the
rung's twin figure would come from a different game.

2026-09-02T13:05:29Z: order swapped before launch, `mixed-pack` runs first.
`mixed-pack` carries the artifact read (§The statistic, "Secondary, `mixed-pack`
only"), is the cheaper arm (2 live seats vs 3), and a single landed arm is a
valid read under this criterion, so ordering decides which read exists if the
card runs out.

## What voids it, decided in advance

- **A live-side fallback rate above 10% on an arm** voids that arm's difference.
  Both rates are still reported. **Recovered above 25%** is flagged, not a void.
- **Fewer than 150 scored games on either arm** makes that arm REFUSED.
- **A settings disagreement** between either record's own `args` and the table
  above voids the read, before any arithmetic.
- **A blind stratum under 150 votes** makes the `mixed-pack` secondary REFUSED.
  It does not touch the primary, which is a win rate.
- **A missing arm is a lost pair, not half a result.** The recipe refuses arm 2
  without arm 1's marker, and a single landed arm reports its own rate against the
  rescored control with no cross-arm claim.
