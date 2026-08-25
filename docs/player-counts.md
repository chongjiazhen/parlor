# Player counts across the ladder

Checked against sources 2026-08-25. **Supports** is a rules fact off each game's
own materials. **Plays best** is community judgement, so it is softer evidence by
nature - review and forum consensus, not a poll with vote counts; treat the ranges
as indicative and the ordering between rungs as the durable part.

Neither column answers what size MEASURES best, which is a property of this harness
and comes out the opposite way for cabal - see below.

| Rung | Supports | Plays best (human tables) | What the size buys the harness |
|---|---|---|---|
| cabal / Avalon | 5-10 | 7-8 | 5 is the cheapest table, and per the arithmetic below the best sampler. 7+ is needed for 3 evil, which is what the information-degrading variants require. |
| ONUW | 3-10 | 5-6 | Size barely matters to the harness: one night, ~10 min, no elimination. Its win is calls-per-game (~10-15 vs cabal's 80-220), not seats. Under 5 is not recommended even for humans. |
| Secret Hitler | 5-10 | 7+, commonly 8-10 | **7+ is a different game, structurally** - see below. |
| Blood on the Clocktower | 5-20 | 7-12 | Needs a big table to be itself; at 5 it degrades toward ONUW. The Storyteller is the judgment rung, so this is where seats and judgment both peak. |

Sources for the best-play column: Avalon 7-8 and Secret Hitler 7+/8-10 from review
and BGG forum consensus; ONUW 5-6 from review consensus, with sub-5 explicitly not
recommended; BotC 7-12 stated as the sweet spot in review. None of these is a
counted poll, and no number here is load-bearing on a measurement.

**Secret Hitler at 7+ ships the blind-evil variant as an OFFICIAL rule.** At 5-6
there are two fascists including Hitler, mutually known. At **7 or more, the
fascists know Hitler but Hitler does not know the fascists.** That is precisely the
`sees_fellow_evil=False` / `seen_by_fellow_evil` asymmetry the queue wants to build
into cabal as a variant - already native, already balanced by a published game, and
it arrives free with the rung that is already next on the ladder. Strong argument
for building Secret Hitler AT 7+ rather than at its minimum, and for taking the
blind-evil measurement there rather than bolting it onto cabal.

Avalon detail worth carrying into any 7+ setup: **mission 4 requires TWO fails at 7
or more players.** `Setup.fails_required` is already a per-mission tuple, so this is
data, not code - but a 7p setup that leaves it at all-ones is silently the wrong
game.

## Why a bigger cabal table does not fix the thin denominator

Clean teams get combinatorially RARER as seats grow, faster than the extra good
voters compensate. P(all-good team), averaged over the official mission sizes,
times the good-voter count:

| Seats | Evil | Team sizes | P(clean) | Good voters | Good-votes-on-clean per vote event |
|---|---|---|---|---|---|
| 5 | 2 | 2,3,2,3,3 | 0.18 | 3 | **0.54** |
| 7 | 3 | 2,3,3,4,4 | 0.114 | 4 | 0.46 |
| 8 | 3 | 3,4,4,5,5 | 0.071 | 5 | 0.36 |

8p yields ~two-thirds of 5p's clean-team samples per vote event while costing ~60%
more calls, since every seat speaks every round. Gate #3b is untouched either way -
hunts are ONE per game at any table size. So table size is orthogonal to the
binding constraint, and reaching for 7p to buy samples spends GPU-hours going
backwards. (Assumes random teams; real leaders propose deliberately, so magnitudes
shift, direction does not.)

**The denominator fix is the metric, not the table.** Binary clean-vs-tainted
discards ~82% of votes. Grade taint continuously - how many evil on the proposed
team, against what that seat could know - and every vote becomes a sample. Same
insight as the ranked/confidence-graded hunt: turn one bit per rare event into
graded signal per common event.
