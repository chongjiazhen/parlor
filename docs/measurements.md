# Measured, dated - the numbers and the backends

Moved out of `queue.md` 2026-08-28: these are readings, not queue. Verbatim.
**Read before trusting any number in this repo.** Each verdict's own doc
(`docs/gate3a-retired.md`, `docs/gate3b-verdict.md`, `docs/durf-rung.md`,
`games/changeling/RULES.md` §S2 read) is canonical for that gate; this file is the
dated ladder underneath them.

**Rules re-baseline, 2026-09-02.** An audit against the published rulebooks
changed four rungs' rules that day: changeling's vote (a flat tally accuses
nobody; records carry `vote_rule`), quorum's slot-3 power (peek, not inspect) and
veto, belfry's evil briefings (seven seats and up only) and mimic cover, and the
durf adjudicator digest. **Every number below dated before 2026-09-02 on those
rungs was played under the earlier rules** and is comparable only to a run that
pins them; each rung's `RULES.md` carries the dated note and, since the same
day, the random control re-measured under the corrected rule beside the old figure
(changeling §The chance baseline, quorum §What the deck does, belfry §Cost).

## Measured, dated - numbers before opinions

All local `rocinante-x-12b-heretic-q4`, seed 400, 8 games, 2 rounds, <1% fallback
unless said otherwise. Fallback rate is quoted because a number without it is the
random policy wearing a model's name.

| what | result | 2026-08-25 |
|---|---|---|
| good vote discrimination, baseline | -0.2% (n=138 votes) | at chance |
| seer approving a team carrying a KNOWN evil | 42% baseline -> 43% with the salience line | the line does nothing in a live game |
| same seer decision, isolated bench, no discussion | 83% -> 37% (n=30/cell, p<0.001) | the line works when nothing buries it |
| `--rounds 2` vs 1 round | 1 of 8 games deadlocked vs 2 of 2 | two rounds is the floor |
| vote unanimity | 11% of 46 votes (spread 1/5..4/5) | votes are ALREADY independent, just uninformed |
| record length vs the 60-line cap | 10 of 16 games over, speech:facts ~4:1 | the trim was deleting missions 1-2 (fixed, `e3249ec`) |
| cap at 512 vs 1536 max_tokens, `nemotron-3-super` | 0/4 -> 2/4 parsed, failures truncated at BOTH caps | no cap fixes a model that thinks out loud; pin one that does not |
| **cloud `auto` (mixed 120B-class), character register, 12 games** | **discrimination +66.0%** (clean 94.4%, tainted 28.4%, n=192; 2.5% fallback) | **gate #3a HOLDS - it was model capability, not the prompt** |
| same run, hunter | 33.3% (3/9, CI floor 12.1%) | exactly chance - gate #3b is now the blocker |
| local 12B, `--register plain`, same seeds as the salient run | discrimination +16.7% (blind seats +11.4%, n=76) | first positive on the 12B, but 7 of 8 games died at five_rejects |
| **local `qwen36-35b-a3b-iq3` (MoE 35B-A3B APEX), 12 games, 0.69% fallback** | **discrimination +30.7%** (blind seats +13.7%, n=222); evil 66.7% with 6 wins by SINKING missions and 32 fail cards | gate #3a holds on ONE pinned local model - reproducible, unlike the cloud's 30-upstream `auto` mix |
| cloud upstream cells, `huntcloud-auto-lottery.jsonl` | 24 served-upstream cells, all 0.00% fallback; one un-attributed source-unknown cell, 2/2 fallbacks; only `nvidia/nemotron-3-nano-30b-a3b` has a hunt, 0/1 (Wilson 0.00%-79.35%) | **2026-08-31T11:53:18.4082507Z**: `py -3 -m eval.cloud_strata <records...>` never pools cells; old vote rows lack turns, so its vote metric REFUSES |
| same model, seer bench | +80% as-is vs +72% with the salience line | the salience line is now HARMFUL - it competes with reasoning a capable model already does |
| hunts across ALL live runs | 8/26 = 31%, and **5 of 26 named the hunter's own ally** | fixed in `hunt()`: a seat the night named as yours cannot be the seer, so the referee refuses it |
| cost, `q36` local | ~14.6 min/game (reasoning distill, long generations) | a 50-game hunter run is ~12h overnight; cloud is ~3 min/game when quota allows |

Added 2026-08-26, all `qwen36-35b-a3b-iq3`, seed 1000, 20 games, 2 rounds. **NONE of
these three columns is a controlled comparison of another.** `hunt20` vs `hunt20b`
differ by three things (see the `hunt20b` item); `hunt20b` vs `hunt20c` differ by the
sampler pin `2cfe9d5`, which landed between them. They are three draws, which is all
they are. `hunt20d` is not a fourth column - it reproduced `hunt20c` exactly
(`docs/reproducibility.md`), so a controlled pair still needs a different seed.

| what | `hunt20` (08-25 19:54) | `hunt20b` (08-26 08:56) | `hunt20c` (08-26 14:52) |
|---|---|---|---|
| blind taint sensitivity - THE GATE | +1.20% [-8.44%, +9.63%] | +8.82% [+0.94%, +16.82%] | +9.00% [**-0.25%**, +18.18%] |
| blind, binary (superseded - see below) | +2.53% [-13.45%, +18.04%] | +19.94% [+6.27%, +32.02%] | +18.11% [+3.52%, +33.53%] |
| approval by taint level, blind | - | 93% / 70% / 77% (41/44, 28/40, 24/31) | 82% / 64% / 64% (41/50, 37/58, 32/50) |
| hunter | 3/9 = 33.33%, floor 12.06% | 6/11 = 54.55%, floor 28.01% | 5/9 = 55.56%, floor 26.66% |
| evil win rate | 70%, 5 of 14 by `five_rejects` | 75%, **0** by `five_rejects` | 80%, **6 of 16** by `five_rejects` |
| evil win paths | 6 missions / 5 rejects / 3 hunts | 9 missions / 0 rejects / 6 hunts | 5 missions / 6 rejects / 5 hunts |
| missions, fail-card distribution | 63, `{0:34, 1:17, 2:12}` | 74, `{0:37, 1:22, 2:15}` | 62, `{0:35, 1:15, 2:12}` (derived) |
| over-sabotage, share of sunk, UNCONDITIONED (superseded 2026-08-27) | 12/29 = 41% | 15/37 = 41% | 12/27 = 44% |
| over-sabotage, **conditioned on the game continuing** - the honest figure | - | **11/28 = 39%** | **10/22 = 45%** |
| fallback rate | 0.49% (11/2231) | 0.54% (11/2033) | 1.78% (48/2691) |
| wall clock | - | 4h42m | 6h37m |

Two things this table now shows that no single column does:

- **The GATE row's point estimate is stable (+8.82 -> +9.00) while its floor verdict
  INVERTS** (+0.94 -> -0.25). At n=20 the floor's position relative to 0 is noise.
  Do not report "the floor cleared 0" as a finding at this N.
- **The taint-level row read as a STEP rather than a slope** - a 0->1 drop and
  little further response at 2 - which would make the linear "per extra saboteur"
  statistic mis-specified for this shape.
  **SUPERSEDED 2026-08-27, and the scorer was right.** Read across all four legs on
  the S6 records they run +7.4, +0.2, -1.6, -6.8: noise around a small negative, not
  a step, so the trigger for a non-monotone caveat did not fire and
  `run_cabal.py`'s "superseded by the graded slope" note stands as written.
  `docs/gate3b-verdict.md` §The three draw-dependent items, resolved carries the
  table. **Do not act on the
  sentence above** - it is kept because it is what two runs looked like on
  2026-08-26, and deleting a superseded reading hides that the correction happened.
- `hunt20c`'s fail-card distribution is DERIVED (62 missions, 27 sunk, 39 cards, max 2
  fails at 5 seats => `{0:35, 1:15, 2:12}`), not read from a scorer field. The JSONL
  carries `fails_played` per GAME only.

| what | result | 2026-08-26 |
|---|---|---|
| **the sampler was never seeded** | same 20 games, seed 1000, twice: 63 missions / 9 hunts vs 74 / 11 | **`--seed` fixed the deal and the fallback RNG and NOTHING about the model.** Every "same seeds, one variable" number in this file was read against an unmeasured run-to-run spread |
| sampler pinned (`2cfe9d5`), verified on the instrument | two calls at seed 1000 to local `q36` byte-identical; seed 7 differs | llama.cpp honours `seed`; on cloud it is a best-effort hint and unproven until a repeat run shows it |
| `need` disclosure vs over-sabotage | 41% of sunk missions in both runs | disclosing the threshold did NOT reduce redundant sabotage - the problem is the missing focal point, not missing rules |

**2026-08-27 (S1)** - `docs/gate3a-retired.md`, `py -3 -m eval.gate3_arithmetic`.
Arithmetic only, no new games. The unconfounded gate-#3a cell splits in OPPOSITE
directions across the two runs and accrues at 0.30-0.40 votes/game; no cabal table
size reopens it.

Added 2026-08-27 (S3). No new games - the four scorer/audit numbers re-derived and
re-run over `hunt20b`/`hunt20c`. Each fix is mutation-checked: the pre-fix
derivation restored as a compiling mutant, killed by its own named test, restored.

| what | result | what it decides |
|---|---|---|
| **hunter baseline, derived** `1/len(legal_targets)` per hunt, meaned over hunts | **1/3 on `SETUP_5`** - unchanged, because the legal set is 3 in every game of it | **S6's pre-committed bar and power table stand as written.** The bar was RIGHT; what was wrong was that it was a constant. A 7p or blind-evil deal makes it 1/4 and the scorer now follows |
| a run whose hunts record no legal-target count | **REFUSED**, not defaulted | fails closed, same shape as the empty blind stratum - a default grades a record against whichever chance the reader assumed |
| **over-sabotage, conditioned on the game continuing** | `hunt20b` 15/37 -> **11/28 = 39%**; `hunt20c` 12/27 -> **10/22 = 45%** | the correction is real and it does NOT rescue the finding - 4 and 2 of the redundant cards were free, and the rate barely moves. Evil still over-sabotages ~2 of every 5 payable sinkings |
| **`outed_own_role_in_public`, claim-shaped re-score (S13)** | `hunt20b` **0/1150** (0.54% fallback); `hunt20c` **7/1580 = 0.44%** (1.78% fallback). **`hunt20b`'s zero is REFUSED by S16's control (2026-09-01): 0 both as recorded and with the deals rotated, so the matcher is not shown to fire on that record at all and its 0 cannot be read as a table that never outed itself.** `hunt20c`'s 7 stands and carries the control | **theme-name match over-counted ordinary role talk.** Explicit first-person present-tense claims remain: `hunt20c` has 7, including repeated claims in game 9. The earlier 0/1290 was matcher-blind, not evidence of no claims |
| `hunt_named_impossible`, allies from `known_allies` | 0/11 and 0/9, unchanged on these runs | no regression on the shipping deal, and it stops flagging a legal hunt on a `stray` - which is a wrong PROOF-class finding, the worst kind this file can emit |

**2026-09-01 (S16), the false-claim instrument.** No new games - the three stored
cabal runs re-scored by `py -3 -m eval.audit_decisions <jsonl>`, which now also
counts a seat claiming a role it does NOT hold. That is not an error: a mimic
saying "I am the Seer" is the game working, and it is counted because gate #2 is
conditional on gate #3 - with good voting at chance, evil wins ~65% with no
deception at all, so a run's deception has to be read rather than inferred from
the win column.

Same claim shape as S13 (first person, present tense), so the same narrowness: an
oblique claim is invisible to it, and no number here says whether a claim was
strategic. Fallback rates are quoted per the invariant; all three are far under the
10% void bar.

| run | false claims | self-outings (S13) | control: deals rotated one seat | fallback |
|---|---|---|---|---|
| `hunt20-q36` (08-25) | **1/1290** - game 9 seat 2, dealt `hunter`, said "I'm Outer Party" (`loyalist`) | 3/1290 | **fires** - 1 -> 4 | 11/2231 = 0.49% |
| `hunt20b` (08-26) | 0/1150 | 0/1150 | **REFUSED** - 0 both ways, exit 3 | 11/2033 = 0.54% |
| `hunt20c` (08-26) | **0/1580** | 7/1580 | **fires** - 0 -> 7, and the 7 self-outings become 7 false claims | 48/2691 = 1.78% |

**The control is the finding.** `--control` re-scores with every seat's deal moved
one seat along, speech untouched: a claim about the speaker's own role becomes a
claim about a role it does not hold, so the two counts must trade places. A 0 from
a string matcher is worth nothing until the matcher has been shown to fire on the
record that produced it - this file already published a 0/1290 for weeks while
looking for vocabulary the players could not produce. `hunt20c`'s 0 false claims is
therefore a reading; `hunt20b`'s two zeros are not, and the tool exits 3 rather
than reporting them.

So the deception number these runs support is **1 explicit false claim in 4020
utterances across three runs**, one of which cannot be read at all. Explicit
role-claiming is not how this model deceives, and gate #2's ~65% is not being
bought with it. A wider instrument (oblique claims, implied roles) is a different
slice; this one measured what it said it would measure and the answer is a floor.

**2026-08-27, the mechanical denominator and the control ladder** -
`docs/reference-policies.md` §Results and §The control ladder,
`python -m eval.derivable`. 60 games of existing records, no GPU. Three findings:
derivable bits at the hunt are **0.000 and that is a theorem** (192,000
combinations), so a hunter above 1/3 reads BEHAVIOUR necessarily; the un-entitled
good seats read **flat** against what the record proved (+3.0%, gap crosses zero),
and the seer's +82.4% is entitlement rather than reading; a 60-line rule out-hunts
the model **94.3% to 48.3%**, so `captured` = 24.5%.

**This does NOT re-specify gate #3a or #3b**, and the S1 verdict stands in its own
words. The blind rows above score response to DERIVABLE taint; §Measured's
`+8.82%/+9.00%` rows score response to ACTUAL taint. Read together they say
something sharper than either: whatever the blind seats respond to, it is not the
mechanically derivable part.

**2026-09-02 (S26), the solver-seat control read** -
`transcripts/cabal-solver-control.md`, `eval/runs/solver-control.cmd`,
`py -3 -m eval.solver_control`. Backend `none`, no model, no GPU. `--arm solver`
against `--arm random` on the same 400 seeds (20000..20399, unspent; N sized from a
20-game pilot at 19000). **A control read of an instrument, not a gate result.**
The gap it closes: `SolverPolicy` deferred most decisions to its random fallback and
those draws routed around the fallback counter, so the arm read `0.00%` random when
most of it was. The split is a record field now (`solver_mechanical` /
`solver_deferred`, per decision `Decision.solver`), never folded into `fallbacks`.

| what | result | what it decides |
|---|---|---|
| **the split**, solver arm | **10085/32586 = 30.95% proved**, 22501 deferred; seer, hunter, mimic proved all 2843 votes each, watcher 1032, loyalist 524 - all from the night and the seat's own role, none from mission arithmetic | the arm was 69% the random policy; "0.00% fell back" was true and said nothing |
| fallback, both arms | solver 0/32586, random 0/26211 | expected: neither arm calls a model, so nothing can be refused. A deferred draw is not a fallback |
| good wins, same seeds | solver **69/400 = 17.25% [13.86%, 21.26%]** vs random 136/400 = 34.00% [29.53%, 38.77%] | intervals disjoint, and NOT a good side vs a control - the solver sat on the evil seats too |
| how evil won | solver: 295 `five_rejects`, 36 hunt hits, **0 missions failed, 0 fail cards** over 544 missions; random: 189 missions, 75 hunts, 0 rejects | seer + both evils reject every tainted team, so none passes and no mission fails; evil wins on the clock or at the random hunt (34.3%, chance 1/3) |
| paired stratum, proved votes before divergence | 1274 paired / 8811 after; random on the same votes: clean 173/240 = 72.08% [66.09%, 77.38%], tainted 697/1034 = 67.41% [64.49%, 70.20%]; solver 240/240 and 0/1034 by definition | both random intervals hold `approve_rate = 0.7`: the pairing selects nothing, and the paired stratum is the first vote round of each game |
| the tell warning | does NOT reach the hunt (deferred to random, at chance); DOES reach the outcome column (entitlement voting against itself, evil seats included) and the share itself (a table that never plays a fail card starves the mission constraint) | a solver-good / random-evil arm is where both artifacts stop; READ below, 2026-09-02 |

**2026-09-02, the solver on GOOD seats only - the control S26 pointed at** -
`transcripts/cabal-solver-good-control.md`, `eval/runs/solver-control.cmd
solver-good-control 400 21000 solver-good`, `py -3 -m eval.solver_control`.
Backend `none`, no model, no GPU. `--arm solver-good` (solver on the three good
seats, evil on the random policy) against `--arm random` on the same 400 seeds
(21000..21399, unspent). Fallback 0/39468 and 0/25778. **Still a control read of
an instrument, not a gate result.**

| what | result | what it decides |
|---|---|---|
| **the S26 artefact** | proved roles are seer 3266, watcher 1788, loyalist 1306 and no evil role; fail cards 524 over 1360 missions (S26: 0 over 544); 43 evil wins by failed missions | the entitlement-against-itself artefact stops with the seating, as the S26 row said it would |
| good wins, same seeds | solver-good **155/400 = 38.75% [34.10%, 43.61%]** vs random 143/400 = 35.75% [31.21%, 40.56%] | intervals overlap: a good side that votes its entitled proof perfectly gains about three points over voting at 0.7 approve, at five seats and one round |
| how evil won | solver-good: **144 `five_rejects`**, 58 hunt hits, 43 missions; random: 0, 77, 180 | the second artefact is the RULE's: three proving good seats reject every tainted proposal, two evils approve, 2/5 fails, and a run of tainted proposers hands evil the clock. Perfect good voting converts certainty into five-reject losses; this caps what "good votes well" is worth on this rung before any model is seated |
| paired stratum | 473 paired / 5887 after; random on the same votes: clean 68/88 = 77.27% [67.49%, 84.78%], tainted 283/385 = 73.51% [68.88%, 77.67%] | both hold 0.7 approve; the pairing selects nothing, as in S26 |


## belfry's control arm, RE-RUN 2026-08-29 - and the instrument check it now PASSES

**Every row in this section is the RANDOM policy:** what the rules alone do, and
what a live arm has to be read against. The first sampled-player reading is below.

**These replace the 2026-08-28 columns, which were measured on a different game.**
Two commits moved random play underneath them: `1b926f9` (a role search prefers the
seat that can still act - before it, 74 of 400 five-seat compact games ran with an
inherited demon that could never kill again) and `5a71004` (the referee and the
policies stopped sharing one random stream). The old numbers are in git history and
are not comparable; nothing should be read against them.

| run, `--arm random --rounds 1` | 5 seats, compact, seed 6100, 200 games | 9 seats, full, seed 7000, 300 games | 10 seats, full, seed 9400, 200 games |
|---|---|---|---|
| good win rate, decided games | 44.00% [37.30%, 50.93%] | 54.33% [48.68%, 59.88%] | 62.00% [55.11%, 68.44%] |
| was, pre-fix | 48.24% | 60.55% | 59.00% |
| how they ended | attrition 112, demon-dead 88 | demon-dead 160, attrition 85, bad-execution 52, speaker 3 | demon-dead 115, attrition 59, bad-execution 17, speaker 9 |
| days per game | 2.8 | 4.5 | 5.5 |
| **day-1 execution accuracy** | 40.00% [31.33%, 49.34%], 44/110 | 22.40% [16.97%, 28.98%], 41/183 | 25.81% [18.91%, 34.15%], 32/124 |
| chance on those day-1 boards | **40.00%** | **22.22%** | **30.00%** |
| day-1 executions a TRIGGER fired, scored apart | 0 | 24 | 30 |
| good-seat vote accuracy | 50.44% [48.52%, 52.36%], n=2601 | 49.79% [49.14%, 50.45%], n=22206 | 49.84% [49.13%, 50.56%], n=18642 |
| fallback rate | 0.00% (0/9330) | 0.00% (0/49762) | 0.00% (0/45401) |

### The day-1 deficit was a METRIC summing two different quantities, and the metric is fixed

**Found 2026-08-29.** The reported failure was real - 514 evil day-1 executions
against 586.4 expected over 1963, Poisson-binomial z = -3.60, seven of eight
samples low. It was not the random policy missing chance. **A day-1 execution is
not always a pick.** The `martyr` executes the seat that NOMINATED it, and the
referee fires that only when the nominator is a townsfolk
(`referee.py`, the guard is `role.team is Team.TOWNSFOLK`) - so a trigger
execution is good with probability **1**, while the scorer priced it against the
board rate like any other. The role is on the full script and not on compact,
which is why the deficit tracked the script rather than the table size.

Measured at 3-8x the sample that raised the alarm, splitting day-1 executions on a
living seat by how they happened:

| run, `--arm random` | executions the table VOTED up | executions a TRIGGER fired |
|---|---|---|
| 5 seats compact, 12000 games | 2811/7007 = 40.12% vs 40.00%, z = **+0.20** | none on this script |
| 10 seats compact, 8000 games | 1623/5561 = 29.19% vs 30.00%, z = **-1.33** | none on this script |
| 9 seats full, 1500 games | 212/893 = 23.74% vs 22.22%, z = **+1.09** | 138, **0 evil**, z = -6.28 |
| 10 seats full, 1500 games | 274/889 = 30.82% vs 30.00%, z = **+0.53** | 216, **0 evil**, z = -9.62 |

**Pooled trigger executions: 354, none of them evil, 95.5 expected, z = -11.48.**
The voted half lands on chance in every configuration, on both scripts, at both
table sizes. The instrument is sound; the pooling was not. Two earlier readings
were noise and should not be carried forward: the 5-seat compact 33.61% (81/241,
one 400-game seed) and the nomination-stage 38.95%, which is a 0.67-sigma miss and
was read as a signal.

**What changed in the code.** `Execution.by_vote` rides in the record beside
`was_alive`, `_executions` scores the two apart, and `eval/belfry_live1_verdict.py`
skips trigger executions in clause B - the same treatment, for the same reason, as
the executions that carried against a seat already dead. Old records carry no field
and default to `by_vote=True`, which is honest: they predate every script with such
a role. The 9- and 10-seat full columns above MOVED when this landed (they were
19.81% and 20.78% pooled); the compact column did not move by a byte, and cannot.

**What it costs the criterion: nothing, and it settles the open question.**
`docs/belfry-live1-criterion.md` reads clause B against `DAY1_CHANCE = 0.40` on 5
seats compact, a script with no such role, and the control lands on 40.00% exactly
(44/110 at seed 6100, 40.12% over 7007 executions pooled). The bar is exact
arithmetic AND the empirical random floor, so clause B may be read as "beats
random" as written. The arm is otherwise unaffected: 0% fallback, 200/200 games.

**The ~14% figure in the previous slice-6 note was wrong.** The `venom` and `mimic`
are both dealt in **17.23%** of 10-seat full deals, measured over 4,000 deals,
against the theoretical `C(2,2)/C(4,2)` = 16.67%.

Two properties of the RULES worth carrying into any live read, both visible above:
the good side wins more often on a bigger table under identical play, and 49 of
the 5-seat run's 274 executions carried against a seat that was **already dead**
(the day ends, nobody dies). Those are counted apart, because a table that spent
its days on corpses is not a table that executed badly.

Recipe, and none of it needs a GPU - all three columns re-run in under 20 seconds
total, which is why there is no excuse for reading a stale control:

```
py -3 -m eval.run_belfry --games 200 --arm random --seats 5  --script compact   --rounds 1 --seed 6100 --out eval/records/belfry-control-5compact.json
py -3 -m eval.run_belfry --games 300 --arm random --seats 9  --script full   --rounds 1 --seed 7000 --out eval/records/belfry-control-9full.json
py -3 -m eval.run_belfry --games 200 --arm random --seats 10 --script full   --rounds 1 --seed 9400 --out eval/records/belfry-control-10full.json
```

## Changeling per-game deduction - S5 record re-read, 2026-08-30 (pre-S14 wording)

Rendered evidence: [`transcripts/changeling-s5-per-game-deduction.md`](../transcripts/changeling-s5-per-game-deduction.md).
`py -3 -m eval.deduction` re-read S5's 200 completed games with no GPU or new
play. This is historical evidence, not a post-S14 verdict: S14 changed a
model-facing self-line. The S5 record's fallback rate was **0.40%**, below the 10% void bar. The
instrument first replays each recorded winner from its votes, including the
tie-accuses-all rule; `py -3 -m unittest eval.test_deduction -v` is its control.

Of 195 winnable games, mean per-game lift over each game's own chance baseline
was **+0.169 [+0.085, +0.255]**. 89/195 (45.6%) voted above that baseline,
29/195 (14.9%) met it, and 77/195 (39.5%) fell below it. Decisiveness was thin:
88/195 (45.1%) outcomes could reverse with one redirected legal vote, and
35/79 village wins (44.3%, Wilson [33.9%, 55.3%]) did so.

Gate #3 and the hand-played "feels random" complaint do not conflict. The gate
is aggregate discrimination; this reading shows many individual outcomes remain
available to chance. `docs/open-arms.md` §"changeling feels random" owns the four
open levers. Changing rules or model-facing text re-baselines this reading.

## Changeling stated self-claims - S2 record re-read, 2026-09-01 (S17)

Rendered evidence: [`transcripts/changeling-s17-stated-claims.md`](../transcripts/changeling-s17-stated-claims.md).
`py -3 -m eval.changeling_claims` re-read S2's 200 games with no GPU and no new
play; its control is `py -3 -m unittest eval.test_changeling_claims -v`. The S2
record's fallback rate was **0.40%**, below the 10% void bar, and its 2 fallback
utterances are out of every denominator. **Pre-S14 wording**, like the per-game
deduction read above.

A claim is scored true when it names a card the seat was actually shown itself as,
`{dealt, belief}`. Deal claims ("I went to sleep as X") came in at **444/520 =
85.4%** [82.1%, 88.2%] and present claims ("I am X") at **468/582 = 80.4%**
[77.0%, 83.4%], against exact chance bars of 19.0% and 19.2% - a seat naming one of
the deck's six cards at random. Scoring a deal claim against `dealt` ALONE was the
first draft and the record refused it: of the 74 deal claims by a seat the night
showed a new card, 65 name that later card and 1 names the deal, because the
pre-S14 self-line called the later card the one the seat went to sleep as.

**The finding is a negative one and it stands on its own.** `docs/open-arms.md`
§"changeling feels random" holds that village seats have no reason to bluff, and
that an all-honest table collapses the game. This table is not all-honest: a seat
that believes itself a villager names no card it was ever shown on 48/343 deal
claims (14.0%) and 65/433 present claims (15.0%). Wolf-believing seats are untrue
on 49/149 present claims (32.9%), twice the village rate, which is the direction a
working deception axis produces.

Both counts are LOWER bounds: 844 of 1998 model-written utterances (42.2%) name a
deck card in a shape the claim rules do not read. The rules are cabal's, widened
2026-09-01 with an adornment gap that leaves S13's 7/1580 and S16's 0/1580 on
`hunt20c` exactly where they were - pinned by a test, because a widening that moves
a published number is a re-baseline.

## belfry live1 - sampled-player measurement, 2026-08-31

Rendered record: [`transcripts/belfry-live1.md`](../transcripts/belfry-live1.md).
100/100 local `qwen36-35b-a3b-iq3` games: 5 seats, compact script, one talk
round, seed 6100, `--no-thinking`, temperature 0.8. It shares the 5-seat compact
control's table, script, rounds and seed. Fallback was **1.49% (82/5515)**, below
the 10% void bar; 12.84% (708/5515) were recovered legal answers.

Good-seat vote discrimination was **+16.09pp [11.44pp, 20.82pp]**: 591/801 yes on
evil nominees against 634/1099 yes on good nominees. Random control is +2.41pp
[-1.49pp, +6.15pp] over 200 games. This record's game-bootstrap interval clears
zero; it is a dated reading of this sampled-player arm, not a claim about models.
Day-1 voted execution accuracy was 29/60 = 48.33% [36.17%, 60.69%] against 40.00%
chance, so its interval spans chance. Good won 42/100 = 42.00% [32.80%, 51.79%];
no deduction or deception result is inferred from that outcome.

**Not an execution of `docs/belfry-live1-criterion.md`.** That promise fixed 60
games, temperature 0.0 and no `--no-thinking`; this arm ran 100, 0.8 and
`--no-thinking`. The criterion remains unedited. `eval.belfry_live1_verdict` now
checks its full launch binding and rejects this record with exit 3 rather than
printing a criterion verdict.

## changeling waker deck - gate #3 HOLDS on six seats, READ 2026-09-02

The first arm on `SETUP_6_WAKER`, and the first changeling evidence after S14
changed the model-facing self-line. Scored with `py -3 -m eval.waker_verdict`,
exit 0; rendered evidence `transcripts/changeling-waker1.md`, written by that same
command with `--transcript` so the artifact cannot disagree with the tool.

**The run.** 200/200 local `qwen36-35b-a3b-iq3` games in 20183 s (5.61 h),
`--arm llm --seats 6 --seed 12000 --rounds 2 --temperature 0.8 --no-thinking`,
exactly as `docs/changeling-waker-criterion.md` promised - the verdict's own
instrument control checks every one of those against the criterion and prints a
DISAGREES line for any that miss. Recipe `eval/runs/changeling-waker.cmd`, records
`eval/records/waker1.json(.jsonl)` plus its paired control `waker1-random`. Five
games seated no pack at dawn and are excluded and reported; **195 scored**.
Fallback **11/3600 = 0.31%**, worst seat-game 6.67%, none over the 10% bar;
recovered 246/3600 = 6.83%, under the 25% warn bar. No void fired.

**Gate #3 HOLDS.** Blind villager accuracy - votes by villager seats the night told
NOTHING, `none` stratum on S10's told-based rule - **120/262 = 45.80%**, Wilson
floor **39.87%** and game-bootstrap floor **38.87%**, both clearing the
pre-committed **30.14%**. The criterion required BOTH floors in advance, which is
the clause S5 could only record after the fact; here it was settled before the
data and both cleared, so the call turns on neither choice.

**The own-arm clause nearly fired.** The paired random control on the same seeds
read **31.12%** derived against the criterion's 30.14% - a gap of 0.98% against a
1.00% tolerance, two hundredths of a point from the control becoming the bar. It
would not have moved the call: both floors sit ~8 points above either candidate.
Recorded because a reader should not have to notice it.

**Power reproduced.** 262 blind votes against a predicted ~272; the floor clears
from a true 36% upward and not from 35%, exactly as written before the run.

**Gate #2 is read and given NO VERDICT**, per the criterion, which declared no bar
for it: pack win rate 54.36% [47.35%, 61.20%] over 195 scored games.

**The waker split reads as nothing, and that is not a failure of the card.** Waker
seated 125 games / 162 blind votes / 45.68% [38.20%, 53.36%]; in the centre 70
games / 100 votes / 46.00% [36.56%, 55.74%]. The stratum is BLIND villagers and the
waker is not blind - it is told what it holds - so its own vote leaves this
denominator by construction. The split was pre-registered as an observation with no
bar and stays one.

**The waker seat's own read, 2026-09-02 - and the like-for-like comparison does
NOT clear zero.** Pre-registered in the criterion as an observation with no bar,
and it stays one. `py -3 -m eval.waker_verdict` prints it; the differences carry a
game bootstrap, because two overlapping Wilson bands answer "could each rate equal
some third value", which is not the question asked.

| | rate | votes |
|---|---|---|
| waker seat | 54.10% [45.27%, 62.68%] | 122 |
| every other villager | 45.73% [41.09%, 50.44%] | 433 |
| ...of those, `identity` only | 47.14% [39.06%, 55.38%] | 140 |
| **difference vs the whole table** | **+8.37% [1.46%, 14.87%]** - clears zero | |
| **difference vs `identity` only** | **+6.96% [-2.11%, 15.98%]** - SPANS zero | |

**Read the second difference, not the first.** The whole table includes blind
villagers the night told nothing, so a seat that knows anything beats them; that
comparison is close to tautological on this deck. The honest set is the `identity`
stratum - seats that also know a card - and against those the waker's advantage
does not clear zero. **So this run carries no evidence that knowing your OWN card
helps beyond knowing a card at all**, which is the claim the deck was built to
test. The point estimate leans the right way and the interval will not support it
at this N: 122 waker votes, one per game, exactly the limit the criterion named in
advance.

Two more, neither of them a gate. Splitting the waker on whether the night moved
its card gives 57.69% [38.95%, 74.46%] over 26 votes against 53.12% [43.22%,
62.79%] over 96 - the moved cell is 26 votes and settles nothing. And an instrument
control worth keeping: **0 waker votes are marked diverged**, which is the card
working as specified, since `WAKE` is last in `NIGHT_ORDER` and nothing moves after
it. Anything but zero there means the night order changed under this read.

**One interim look is disclosed.** At game 50 the blind stratum was inspected to
check the criterion's power assumption (1.354 blind votes/game against the priced
1.383); the gate statistic was printed in the same pass. Nothing was acted on, no
arm stopped early, the statistic was pre-specified and the run went its full 200,
so the fixed-N analysis stands. But this criterion spends no alpha, so **the
interim figure has no standing and is not cited anywhere.** Recorded rather than
omitted: an undisclosed look is the thing group-sequential design exists to
prevent.

**A dated snapshot of one model on one deck, never a claim about models.** Nothing
here transfers from `SETUP_5`: wolf density moves 2/5 to 2/6, so the bar was
re-measured rather than inherited.

## changeling dominated votes - S2 and waker records re-read, 2026-09-02

`py -3 -m eval.changeling_audit <run>.jsonl --reference <random>.jsonl`, no GPU,
records already on disk. The cabal decision auditor's class for this rung: a vote
dominated GIVEN WHAT THE SEAT WAS SHOWN, read off the referee's night log, priced
rather than blamed because the cards move after a seat looks. Two counts, never
pooled, each beside the same count on a random control where every vote is
uniform over the other seats. **Not a gate**; a reading of what the model does
with its own reveal. `--control` refused nothing: both parsers fire on every
record below.

| record | shown-village: a village seat voted a seat it was shown as village | partner: a pack seat voted its told fellow |
|---|---|---|
| S2, q36, 5 seats (`plurality`) | **59/164 = 35.98% [29.03%, 43.56%]**, 2/59 held pack at dawn anyway | 40/150 = 26.67% [20.24%, 34.26%], 31/40 held pack |
| random, 5 seats, 4000 games (`plurality-min2`) | 834/3327 = 25.07% [23.62%, 26.57%] | 823/3224 = 25.53% [24.05%, 27.06%] |
| waker1, q36, 6 seats | 32/175 = 18.29% [13.26%, 24.67%] | 40/220 = 18.18% [13.65%, 23.81%], 33/40 held pack |
| waker1-random, same seeds | 39/175 = 22.29% [16.75%, 29.01%] | 38/220 = 17.27% [12.85%, 22.82%] |

**What it says.** On five seats the model votes a seat it was itself shown as
village MORE often than a random voter would - the intervals do not overlap - and
57 of those 59 votes were wasted on a seat that did hold a village card at dawn.
The examples are mostly the swapper voting its own victim, the seat it KNOWS now
holds the swapper card; that is the rules-error family RULES.md §The public rules
text already names, seen from the vote rather than the speech. The pack votes its
partner at exactly chance on both decks, so the evil side plays no protection
either. On six seats both counts sit inside their control's interval: 175 and
220 votes cannot separate them. The vote rule differs between S2 and the 5-seat
control, and it does not matter to a per-vote count: the chance of naming one
shown seat is k over n-1 whatever the tally does with it afterwards.

## belfry live2 - the criterion-bound arm, READ 2026-09-01

The first belfry live arm to execute its own criterion. Scored with
`py -3 -m eval.belfry_live1_verdict --criterion live2`, exit 0.
Rendered evidence `transcripts/belfry-live2.md`, written by that same
command with `--transcript` so the artifact cannot disagree with the tool.
60/60 local `qwen36-35b-a3b-iq3` games in 23104 s: 5 seats, compact script, one
talk round, seed 6100, temperature 0.0, `--no-thinking`, exactly as
`docs/belfry-live2-criterion.md` promised. Fallback **1.28% of 3353 decisions**,
far below the 10% void bar; vote fallback **0/1972 = 0.00%**; 243/3353 (7.25%)
were recovered legal answers.

**Clause A INFORMS.** Good seats voted yes on an evil nominee 351/471 = 74.52%
[70.40%, 78.25%] against 369/681 = 54.19% [50.43%, 57.89%] on a good one -
discrimination **20.34% [13.77%, 27.01%]**, game-bootstrap floor clearing zero
over 60 games. The random control reads 2.41% [-1.49%, 6.15%] over 200 games and
does not clear that bar, which is what earns this figure the right to be read. A
dated snapshot of one model on one script at one talk round, never a claim about
models.

**Clause B does not decide.** Day-1 executions 16/38 = 42.11% [27.85%, 57.81%]
against a 40.00% chance rate on the same boards; the interval spans chance. At 60
games that is ~21% power against a true 50%, so it is not evidence of absence -
said in advance, in the criterion.

Descriptive, gating nothing: good-seat accuracy 57.55% against an always-no floor
of 59.11% on the same 1152 votes, gap -1.56% [-7.18%, 4.19%]; pooled executions
35/77 = 45.45% [34.81%, 56.53%]; good won 48.33% [36.17%, 60.69%] over decided
games; 2.4 days per game; attrition 31, demon-dead 29. Misled good-seat votes
came to 98, under the pre-committed floor of 200, so no misled/clear gap is
reported - the criterion expected about 49.

**Why this arm exists, and what it cost to find out.** `docs/belfry-live1-criterion.md`
promised temperature 0.0 WITHOUT `--no-thinking`. Measured 2026-09-01, those exact
settings run **58.33% fallback** (63/108 over two games, 10 of 10 seat-games above
the bar) at 1805 s/game: the arm as promised fires its own void condition at any N,
because a reasoning distill spends the token cap inside `reasoning_content` and
returns empty content. live2 changes that one launch setting and nothing else -
every bar, floor, endpoint and void condition carried across unedited, and live1's
criterion left unedited beside its own record. The flag is worth 58.33% -> 1.28%.

## belfry setup-only adjudicator - S8 void, 2026-08-31

Rendered record: [`transcripts/belfry-adjudicator-s8-void.md`](../transcripts/belfry-adjudicator-s8-void.md).
The frozen S8 pair ran 60 five-seat compact random-player games on seeds
6100..6159. Player fallback was 0/2809 (0.00%) in both arms. The model
adjudicator reached its 20 setup opportunities, but 12 fell back (60.00%), above
the pre-committed 10% ceiling. S8 is VOID: no source-discrimination result.

Route probe served `qwen36-35b-a3b-iq3` three times. Successful choice calls
served that same upstream. Failed calls returned a complete fenced `json` object,
which S8's bare-object parser rejected. This is response formatting, not a read of
referee discretion. Records remain untracked in `eval/records/` and are not
re-scored. `docs/belfry-adjudicator-v2-criterion.md` binds fresh records and a
narrow whole-fence normalization before S8b starts.

## belfry setup-only adjudicator - S8b read, 2026-08-31

Rendered record: [`transcripts/belfry-adjudicator-s8b.md`](../transcripts/belfry-adjudicator-s8b.md).
S8b repeated the frozen 60-game pair under its new criterion, over seeds
6100..6159. Both player fallback rates were 0/2809 (0.00%). Model adjudicator
fallback was 0/20 (0.00%); control adjudicator fallback is n/a.

**S29 did not move this read, 2026-09-01.** The adjudicator gained the seats'
retry that day, which re-baselines the instrument in general - but not this
record. Its 20 calls fell back 0/20, so every first ask was already answered
legally; the first ask is byte-identical to the pre-retry one by design and by
test, and the seeded menu rng is drawn only on a fallback, so the retry has no
call here to change. Re-read after the change: recovered `0/20 = 0.00%`,
everything else identical, exit 0. **Nor does the v1 arm carry one**, though it
fell back 12/20: `recovered` is set at PLAY time inside `ModelAdjudicator.choose`
from `rule_refusals > 0`, so a record written before the retry existed holds the
event and not the attempt history, and re-scoring cannot recover a fumble that had
no second ask to make. v1 re-reads at recovered `0/20 = 0.00%`, exit 2 (void at
60%). S29 closed on that: `docs/decisions.md` §No arm will produce `recovered > 0`.

All 20 paired legal traces remained. Nine odd-seed trace pairs were held out;
source accuracy was **88.89%**, above Wilson 95% chance upper endpoint **70.97%**
(18 labelled held-out traces). Verdict: **DISTINGUISHABLE**. This establishes a
trace difference from seeded random in bounded setup choices only. It does not
establish choice quality, referee quality, deduction, deception, or wins.

## belfry steered discretion - S23 read, 2026-09-01

Rendered record: [`transcripts/belfry-steering-s23.md`](../transcripts/belfry-steering-s23.md).
The frozen S23 pair ran 360 five-seat compact random-player games on seeds
6100..6459, model arm 201 s on local `qwen36-35b-a3b-iq3` at temperature 0.0.
Both player fallback rates were 0/16568 (0.00%). Steered adjudicator fallback was
0/152 (0.00%), recovered 0/152; control adjudicator rate is n/a. **A richer ask
cost nothing at the parser**: the board and the rule went out beside the menu and
every first ask still came back legal, as in S8b's blind 0/20.

152 of the 360 games seated a diviner and so asked the question. Against the
stated placement rule, steered compliance was **46.05%** (70/152), above the
Wilson 95% chance upper endpoint **40.71%**: **STEERED**. The seeded-random
control complied 49/152 = 32.24% on the same boards against the same rule, inside
its own chance interval - which is the instrument control that says the rule is
chance-neutral here and the steered number is not reading a skewed bar.

**The size is the finding, not the verdict.** The rule was ignored on 82 of 152
calls. What is evidenced is a tendency toward a stated policy, not obedience to
one, and nothing here supports a referee that may be RELIED on to keep a rule. It
establishes no choice quality, no referee quality, deduction, deception or wins,
and the rule's content is a probe rather than a claim about good refereeing
(`docs/decisions.md` §Belfry's setup discretion has no quality axis).

## belfry night coherence - the first play-time discretion arm, READ 2026-09-02

Rendered record: [`transcripts/belfry-night-coherence.md`](../transcripts/belfry-night-coherence.md).
The frozen pair ran 1000 nine-seat compact random-player games on seeds
12000..12999, model arm 3058 s on local `qwen36-35b-a3b-iq3` at temperature 0.0
with `--adjudicator-night`; the seeded-random control ran the same recipe in
35 s. Player fallback was 0/168234 (0.00%) on the control and 0/168786 (0.00%)
on the model arm. Model-adjudicator fallback was 0/2403 (0.00%), recovered
35/2403. Every non-fallback gauge choice was served by `qwen36-35b-a3b-iq3`.

The unit is a pair: two consecutive false tellings to the same switched-off
gauge over the same living neighbours. Chance per pair is exactly one half. The
control produced 158 pairs and held the lie on 84 (**53.16%**, Wilson
[45.40%, 60.78%]), an interval that contains one half, so the instrument control
passes. The model arm produced 163 pairs and held the lie on 152 (**93.25%**,
Wilson [88.32%, 96.19%], bootstrap-by-game 2.5th percentile 86.90%). Both floors
clear one half: **COHERENT**. The counts were re-derived from the JSONL by a
separate pass and matched the verdict tool exactly.

**What it says, and the ceiling on it.** A bounded play-time choice can be held
to a stated policy across calls when the referee hands the model its own prior
tellings in the ask. It broke the lie on 11 of 163 pairs, so "oversees without
micromanaging" is evidenced as a strong tendency, not as a rule the referee can
be relied on never to break. The memory was supplied, not kept: nothing here
says the model would hold a lie it had to remember unaided, and the arm that
withholds `prior` is the one that would measure that. It is not a claim about
referee quality, deduction, deception or wins; players were random on both sides,
and the win split (control good 55.76%, model 54.05%) is the deal plus the
model's setup choices, which this arm did not grade.

## belfry night coherence, prior WITHHELD - launched 2026-09-02, VOID at 400/1000

Recipe `eval/runs/belfry-night-noprior.cmd`, criterion
`docs/belfry-night-noprior-criterion.md`, seeds 13000..13999. Control 1000/1000
in 34 s. The model arm played 399 games at 0 fallback and raised gate #1 on the
400th: `LeakDetected: [(3, 2, 'seat 2 is the Fiend')]`, seed 13400. Reproduced
deterministically: a night-3 lie to the sot named the heir as the Fiend, the
heir succeeded on night 5, and the audit found the lie true against the
current grimoire. No summary was written, so the verdict tool cannot print its
arithmetic; the arm is VOID by row count and the finding is a queue row. The
gate did what it is for: it raised, and nothing under it was published.
Stamped 2026-09-02T04:14:14Z.

## belfry night coherence, prior WITHHELD - READ 2026-09-02, COHERENT and NEEDS MEMORY

Rendered record: [`transcripts/belfry-night-noprior.md`](../transcripts/belfry-night-noprior.md).
The relaunch under the succession fix (`819963d`) ran the frozen pair on seeds
13000..13999, model arm 2969 s on local `qwen36-35b-a3b-iq3` at temperature 0.0
with `--adjudicator-night --adjudicator-night-no-prior`, control 30 s. Player
fallback 0/166782 (0.00%) control and 0/167780 (0.00%) model; adjudicator
fallback 0/2335 (0.00%), recovered 23. Every non-fallback gauge choice was
served by `qwen36-35b-a3b-iq3`. All 1000 control rows and the 399 completed
model rows are byte-identical to the void run; game 400 is the leak board with
the lie now naming the Witness.

The control produced 159 pairs and held the lie on 81 (**50.94%**, Wilson
[43.24%, 58.60%]), containing one half: instrument passes. The model arm
produced 122 pairs and held the lie on 94 (**77.05%**, Wilson [68.83%, 83.62%],
bootstrap-by-game 2.5th percentile 68.75%). Both floors clear one half:
**COHERENT**. Against the supplied-prior read's 152/163 (Wilson lower endpoint
88.32%) the withheld arm's upper endpoint is 83.62%: **NEEDS MEMORY**. Counts
re-derived from the JSONL matched the verdict tool.

**What it says.** With no channel to its earlier telling, the model's false
count is mostly a content function of the board: three in four pairs hold
without a reminder, well above the one half a position-picker would score.
And the reminder is load-bearing: supplied `prior` moved coherence from 77% to
93% on non-overlapping intervals, so the referee's consistency is partly the
harness's memory and partly the model's own policy. This bounds "oversees
without micromanaging" for this model at "consistent when reminded, mostly
consistent unaided", and says nothing about a referee that keeps its own memory
across calls, because no arm gives it one. The model side also produced fewer
false tellings (384 against 460) and fewer pairs (122 against 159): its setup
choices move which seats are switched off, and the pair count is its own, as
the criterion said it would be.

## Route: local IS the gate lane - corrected 2026-08-28

This section read "local is for spot-checks, not for gates", priced when a game cost
~9 min on a 12B and cabal was the only rung. Both gates have since been called on
local: S6's 40 games and S2's 200, the latter at 91s/game on `qwen36-35b-a3b-iq3`.
**A route claim priced against a retired model stays true-sounding until someone
re-reads it** - same failure as a queue item priced by a deleted cost
(`docs/evidence-discipline.md`).

Local is serial, exact-match and 100%-attributed, which beats a time-varying `auto`
mix as evidence. Cloud is capacity, not gates - its composition is anti-correlated
with what you are measuring (§Backend notes). Reach for a bigger local model only if
a cloud model turns out to REFUSE to deceive, or you want games beside image gen.

**2026-08-31T11:53:18.4082507Z correction:** `eval.cloud_strata` now reads the
served upstream on each stored decision, so cloud results accumulate by upstream
instead of pooling an `auto` mix. This makes a cell reproducible; it does not make a
thin cell a gate. The stored cloud hunt is one nano decision, 0/1 with 0.00%
fallback; two source-unknown fallbacks are visible separately as 2/2 un-attributed.
Its 0.00%-79.35% Wilson band is no verdict.


## Backend notes (measured 2026-08-25)

- `local` armed: `rocinante-x-12b-heretic-q4`. The heretic 12B
  deceives without any prompt escalation - the mimic fabricated a prior private
  conversation to build credibility, the hunter played concerned-loyalist and then
  correctly named the seer. `PLAYER_SYSTEM_PROMPT` needed no jailbreak. Cost: ~3s
  per decision, ~9 min per game, serial.
- **Burst-probe result, gray, 2026-08-25 23:10 - the single-call trap firing
  exactly as documented.** Pinned `gpt-oss-120b`: **1/12 served, 11 instant 429s**
  (`All models exhausted: 8 routes checked, 7 rate-limited or on cooldown, 1 no
  usable key`), and the ONE success was the FASTEST call of the set at 0.4s. A
  single-call probe would have reported the tier healthy and fast. This is why the
  `huntcloud` run sat alive for 72 minutes and wrote zero games: pinned to a model
  whose whole route pool was cooled, refused in 40ms, nothing to fail over to.
  Killed rather than waited out - free-tier cooldowns clear on nobody's schedule.
- **`auto` availability is NOT `auto` capability** (same probe, same minute).
  `auto` served **12/12 at 0.3s median** - but the upstreams were
  `gpt-oss-20b`, `gpt-oss-safeguard-20b` (x5), `nemotron-3-nano-30b-a3b` (x6). Not
  one 120B-class model: the big ones are exactly what is cooled. So `auto`'s
  composition is time-varying and **anti-correlated with the thing being measured**
  - it degrades precisely when capacity is short, which is when you reach for it.
  A gate run on tonight's `auto` would most likely read "hunter at chance" while
  actually measuring which models were uncooled at 23:10. Given -0.2% on the 12B
  vs +66% on 120B-class, a 20B/30B-nano mix sits near the at-chance end. False
  negative wearing a real number; worse than no run.
- `clean` needs `PARLOR_API_KEY`. Pin a model - `glm-4.7` is in `/v1/models`
  and 404s at call time (stale catalog entry), and `auto` silently varies the
  upstream per request. Live and answering: `minimax-m3`, `nemotron-3-super`,
  `qwen3-30b-a3b-fp8`, `gpt-oss-120b`, `glm-4.7-flash`. Bursts draw 429s - hence the
  transport backoff and `--workers 3`.
- **The cap was the cause, and 1536 is not enough for a rambler** (measured
  2026-08-25, same VOTE prompt, n=4 per cell, `clean`). `nemotron-3-super`:
  `max_tokens=512` -> 0/4 parsed, every reply ~2100 chars of visible reasoning cut
  mid-sentence; at 1536 -> 2/4, and both failures were ~6000 chars, i.e. truncated
  at the new cap too. So a model that thinks out loud does it at whatever length it
  likes and no cap is a fix. `gpt-oss-120b` answers in 80-125 chars, 4/4 at both
  caps - pin it for gate runs. `minimax-m3` itself is still unverified: the
  provider has been 429ing it since the void run, and a 429 is a transport failure,
  not a refusal. `qwen3-30b-a3b-fp8` and `glm-4.7-flash` currently 502.

**2026-08-27 (S6), the gate-#3b campaign** - `docs/gate3b-verdict.md`,
`py -3 -m eval.s6_verdict`. 40 games, seeds 2000/3000, frozen at `2c0e2a3`, 1.35%
fallback. **9/20 = 45.00%**, Wilson [25.82%, 65.79%] vs the derived bar 33.33% -
NOT SHOWN, at exactly the 0.50 hunts/game the power table assumed. All three
draw-dependent items came back negative there; **carry no run-length caveat
forward.**

## Quorum slice-7 control - the once-per-event rebaseline, measured 2026-08-29

Slice 7 (`88425ad fix(quorum): allow one claim per seat and event`) changed the
claim population: a seat now files at most one claim per completed draw, where
the live1 channel let it re-file the same assertion every discussion turn. Every
quorum claim figure recorded before it is PRE-FIX and reads against a different
denominator; `docs/quorum-live1-criterion.md` and `quorum-live1.json` are left
untouched as the historical record. Seeds 5200..5599 are contaminated; this
control ran seeds 7000..7399.

`py -3 -m eval.run_quorum --games 400 --arm random --seed 7000 --rounds 1 --out
eval/records/quorum-control-slice7.json`, at `88425ad`: 400/400 games, 0.00%
fallback over 44441 decisions, no leak. **2562 claims over 400 games = 6.41
claims/game (was 7.55 pre-fix)** - the drop IS the removed duplicates, not a
policy change. The fixed instrument still lands on chance: proposer 325/1310
honest (24.81%) Wilson [22.55%, 27.22%] vs the exact 25.00%; enactor 381/1252
(30.43%) [27.95%, 33.04%] vs 33.33%. The proposer interval contains its
baseline; **the enactor interval does NOT** - 33.04% is below 33.33%, and an
earlier revision of this block asserted that both did. The miss was read as a
one-in-twenty draw and was mostly not: the referee and the policies shared one
random stream, and decoupling them (`5a71004`) moved the enactor to 398/1246
(31.94%) with both intervals containing their baselines - see the slice-9 block
below. A
control that cleared the bar would mean the bar is wrong.

These numbers price `docs/quorum-live2-criterion.md` (written the same day,
before any live game): a 20-game live2 arm offers ~66 proposer and ~63 enactor
claim opportunities, and its Clause B keeps live1's per-claim Wilson form with
the known correlated-claims caveat declared in the file - the per-game bootstrap
replacement is slice 8 and is not pre-committed here.


## Quorum slice-8 control re-read - the game bootstrap, measured 2026-08-29

Slice 8 (`feat(quorum): score claim uncertainty by game bootstrap`) changed
clause B's interval from per-claim Wilson to a per-game nonparametric bootstrap
(4000 resamples, seed 7, pinned in `eval/quorum_live1_verdict.py`). The engine
is untouched, so no new control run was needed: the slice-7 record
(`quorum-control-slice7.json.jsonl`, seeds 7000..7399) was re-read through the
new interval. Point estimates unchanged; the uncertainty is what moved:

- proposer 325/1310 (24.81%): Wilson [22.55%, 27.22%] -> game bootstrap
  **[22.63%, 27.02%]** - still contains the exact 25.00%.
- enactor 381/1252 (30.43%): Wilson [27.95%, 33.04%] -> game bootstrap
  **[27.87%, 32.90%]** - sits just BELOW the exact 33.33%. Declared, not
  smoothed: a 95% interval excludes the true value one time in twenty, the
  control is chance by construction, and this is that draw. Neither floor
  clears its baseline, so the floor control still passes.

The pinned boundary behaviour the criterion leans on: at the spread extreme
(one claim per game) 28/79 proposer clears 25% and 27/79 does not; 33/72
enactor clears 33.33% and 32/72 does not (Wilson cleared at 32 - the bootstrap
is wider). The same 40/79 packed into 8 games does NOT clear, where spread
does - the clustering sensitivity per-claim Wilson could not see.

`docs/quorum-live3-criterion.md` (written the same day, before any live game)
supersedes the never-launched live2 promise in writing: **live3 arm seeds
9600..9619, record path `eval/records/quorum-live3.json`**. Neither live1 nor
live2 criterion files were edited.

## Three changes that re-read an old record differently - moved from the queue 2026-08-28

Verbatim from `queue.md`. Each one changes what a number recorded before it
means, which is why they live beside the numbers rather than in the queue.

class) and S5 (the `--out` convention), so a reader has one sha per change rather
than a scatter. Done rows are gone; the struck 5 stays because the S6 slice cites
it. Three things a later reader has to know, because each re-reads an old record
differently:

- **`fallback_rate` is unchanged and keeps its name** - every record in
  `eval/records/` and every published summary quotes it, and both reproducers still
  agree with the recorded runs. What is NEW beside it, in `core/integrity.py` and
  shared by both games: a witnessed rate per seat-game, a `recovered` count for
  decisions the parser or the rules sent back and the model then got right, and a
  clean-game count. **Old records carry no `recovered` field and read as 0 - that
  is absence, not a measurement**, and a re-scored pre-S9 run must not be quoted
  for it.
- **changeling's knowledge class is keyed on what the seat was TOLD**, which
  re-baselines every recorded changeling number: a pre-S10 record's blind stratum
  is ~19% smaller than the night produced and its `identity` stratum is diluted by
  the same seats, so a figure quoted across the change answers two different
  questions. `py -3 -m eval.strata` prints both rules side by side and is where
  every stratum size in `games/changeling/RULES.md` comes from.
- **`--out` is the summary path VERBATIM and the JSONL is its sibling
  `{out}.jsonl`** (`core/runlog.py`, `record_paths`) - which is what every record
  already on disk is named, so settling it renamed one run's files rather than
  every run's. One test pins the two drivers TOGETHER: the defect was that they
  disagreed, and a test beside either one cannot see that.

## cabal grew a third channel - the evil conference before the hunt, 2026-09-02

`games/cabal/RULES.md` step 5, merged at `7460953`. Before it, no evil-only channel
existed and the hunt followed the third mission directly; now each evil seat the
night introduced to a partner says one thing on a channel only the pair receives,
and `audit.conference_audit` hunts every rendered line in every other seat's
payload. **Every cabal number recorded before this sha was measured on a game
where the pair could not coordinate before the strike** - gate #2's hunt figures
most directly, and gate #1's corpus, which now carries a class of secret it did
not. A pre-conference record stays quotable as what it is and is not comparable
to anything run after it. The driver also logs one more decision per conferring
seat per game, so an aggregate fallback rate over all decisions runs on a larger
denominator than before; per-phase rates are unaffected.

## cabal 6- and 7-seat setups - RANDOM BASELINES ONLY, measured 2026-09-02

`SETUP_6` and `SETUP_7` landed this day (`games/cabal/RULES.md` §The larger
setups). **No model has been seated at either size**, and cabal has no GPU program
left, so every figure below is the chance floor and nothing here is a gate claim.
Three 1000-game random controls, same seed base, 0.00% fallback in all three:

```
py -3 -m eval.run_cabal --arm random --games 1000 --seed 5000 --seats 5 --out eval/records/cabal5-random.json
py -3 -m eval.run_cabal --arm random --games 1000 --seed 5000 --seats 6 --out eval/records/cabal6-random.json
py -3 -m eval.run_cabal --arm random --games 1000 --seed 5000 --seats 7 --out eval/records/cabal7-random.json
```

The 5-seat row is a REFERENCE, not the other arm of a pair: seats, evil count and
the mission ladder all move together, so this is three separate chance floors and
not one variable.

| | 5 seats (2 evil) | 6 seats (2 evil) | 7 seats (3 evil) |
|---|---|---|---|
| evil win rate | 64.60% [61.59, 67.50] | 60.00% [56.93, 62.99] | 56.90% [53.81, 59.94] |
| by path: missions failed / five rejects / hunt hit | 460 / 0 / 186 | 465 / 8 / 127 | 450 / 0 / 119 |
| fail cards played | 2129 | 2178 | 2740 |
| hunt chance, derived | 33.33% | 25.00% | **20.00%** |
| hunter accuracy at random | 34.44% (186/540) | 24.10% (127/527) | 21.64% (119/550) |
| blind taint sensitivity | +0.52% [-1.46, +2.60] | +0.06% [-1.28, +1.37] | -0.36% [-1.34, +0.64] |
| blind clean / tainted votes | 837 / 3978 | 1968 / 8986 | 1599 / 12516 |
| `aura` stratum | n=837/3978 | n=984/4493 | **n=0/0, REFUSED** |
| decisions | 64795 | 85363 | 84737 |

What the numbers say, and only this:

- **The hunt bar falls with the table, and 7 seats does not fall as far as the
  evil count suggests.** 1/5, not 1/4: three evil seats, but the `stray` is named
  to nobody, so the hunter bars only itself and the `lurker`. A scorer deriving
  chance from the evil count would grade a 7-seat hunt against 25% and read 21.6%
  random play as below chance. The referee records the set each hunt faced, so
  nothing here was assumed.
- **The empty `aura` stratum prints as REFUSED, not as zero.** `SETUP_7` seats no
  watcher, so gate #3a has two strata there rather than three. This is the
  instrument check on the setup: an absent stratum rendered as 0.00% would have
  been a gate reading over nothing.
- **Evil's chance floor drops as the table grows** - 64.6% -> 60.0% -> 56.9%, with
  the drop coming out of the hunt (186 -> 127 -> 119 wins) rather than out of the
  missions, which hold near 460. Gate #2's floor is therefore setup-specific: the
  ~65% figure the gate is conditional on is a 5-seat number and does not carry.
- **The blind vote floor is flat at chance in all three**, as it must be with good
  voting at random, and all three CIs straddle zero. The sampling half is
  `docs/player-counts.md`'s point restated by measurement: clean teams are 17.4% of
  blind votes at 5 seats, 18.0% at 6, and **11.3% at 7**. Per blind seat per game
  that is 0.84 / 0.98 / **0.53** clean-team votes - 7 seats has three loyalists
  instead of one and still collects fewer clean samples each. A bigger table is not
  a sampling fix, and at three evil it is a sampling loss.
- **Five-reject losses are not a 7-seat failure mode.** 0 of 1000 at 7 seats, 8 at
  6, 0 at 5. Worth knowing before reading a live arm, since perfect good voting is
  measured to convert certainty into five-reject losses at 5 seats.

## Quorum slice-9 control - the decoupled policy stream, measured 2026-08-29

`eval/records/quorum-control-slice9.json`, 400 random games, seeds 7000..7399,
`--rounds 1`, at `5a71004`. The SAME deals as the slice-7 control above: only the
policy stream moved, so the two are directly comparable.

`5a71004` stopped the referee and the policies sharing one seed. Seeding both with
the same integer makes them one MT19937 sequence read at two offsets, so the deal
and the policy's claim draw were dependent - and the exact chance baseline the
control is read against assumes they are not. Measured coupled, across nine blocks:
enactor honesty 32.550% over 20,540 claims, z = -2.38 against the exact 33.333%,
every block negative; decoupled, 33.449% over 48,971 claims, z = +0.54, blocks
straddling zero.

| figure | slice-7 (coupled) | slice-9 (decoupled) | exact |
|---|---|---|---|
| claims scored | 2562 (6.41/game) | 2554 (6.39/game) | - |
| proposer | 325/1310 = 24.81% | 313/1308 = **23.93%** | 25.00% |
| proposer bootstrap | [22.63%, 27.02%] | **[21.75%, 26.11%]** | contains |
| enactor | 381/1252 = 30.43% | 398/1246 = **31.94%** | 33.33% |
| enactor bootstrap | [27.87%, 32.90%] - **EXCLUDES** | **[29.45%, 34.48%]** | contains |

Both intervals now contain their baseline and **neither floor clears it**, which is
the property a floor control has to have: the instrument does not clear the bar on
random play. Zero repeat (seat, event) claims, so the void condition added at
`5a71004` does not fire on legal play; zero safe enactor lies, the standing
self-check. Per-game offer 3.27 proposer / 3.12 enactor, so a 20-game arm offers
~65 and ~62 opportunities.

This is the control `docs/quorum-live4-criterion.md` is priced from. live3 was
priced from the coupled one and is superseded in writing, unrun.
## quorum live4 - the first quorum arm with a model in a seat, READ 2026-09-01

The criterion-bound arm of `docs/quorum-live4-criterion.md`, scored with
`py -3 -m eval.quorum_live1_verdict`, exit 0. Rendered evidence
`transcripts/quorum-live4.md`, written by that same command with
`--transcript`. 20/20 games in 6522 s (326 s/game)
on local `qwen36-35b-a3b-iq3`: `--arm llm`, one discussion round, temperature
0.0, `--no-thinking`, seeds 11200..11219, exactly as promised. live1, live2 and
live3 stand unrun beside their own criteria, each superseded in writing.

**No void condition fired.** Model fallback **0.04% of 2582 model-controlled
decisions** against a 10% ceiling - that is ONE decision in the whole arm. 20
played games as promised. No entitlement leak. No repeat `(seat, event)`
claim - the first time that check, added at
`5a71004`, has run against a MODEL record rather than random play. It found
nothing, so the void still has no positive case behind it and a duplicate
remains a bug report rather than a finding. 46
decisions were recovered by the parser or the rules. Zero safe ENACTOR lies, the
standing self-check that an enactor lie is exposed by construction.

**Clause A: the channel was used, and used harder than the control offered.**
104 proposer and 105 enactor claims. The criterion priced ~65 and ~62 from the
slice-9 control's 3.27 / 3.12 claims a game, and named the arm's own denominator
as the first thing it was uncertain about, since a model may simply decline a
typed channel. It did the opposite: **5.20 proposer and 5.25 enactor claims a
game, 59% and 68% above the random control** on the same offer structure. A
denominator observation, not
a rate - stated here because the criterion pre-registered the uncertainty.

**Clause B INFORMS in both offices.** The statistic is honest claims over scored
claims per office; the bar is the per-game bootstrap 95% floor clearing the exact
chance baseline, resamples pinned at 4000 with seed 7.

| office | honest / scored | rate | game bootstrap 95% | exact baseline | verdict |
|---|---|---|---|---|---|
| proposer | 77/104 | 74.04% | **[64.86%, 83.16%]** | 25.00% | INFORMS |
| enactor | 73/105 | 69.52% | **[64.29%, 75.53%]** | 33.33% | INFORMS |

Both floors clear their baselines with room, against a control whose floors
clear neither (proposer 23.93% [21.75%, 26.11%], enactor 31.94% [29.45%,
34.48%]) - which is what earns these the right to be read. On this backend, at
this prompt, a declared claim carries information about the draw. **A dated
snapshot of one model on one script at one discussion round, never a claim about
models.**

Descriptive, pre-registered, gating nothing: 59 lies of which 14 no seat could
contradict; safe lies by office proposer 14, enactor 0; honest on a forced draw
70.37% over 54 claims against 72.26% where the office had a choice; by side
majority 73.55%, minority 69.32%; 42 writs enacted by an office that could have
done otherwise. No win rate is reported and no deception figure is inferred from
one - `majority_wins` is a property of the deck at this scale.

## ensemble session 0 - the draft RAN, and its distribution is NOT a measurement, 2026-09-03

The play-lane row's done-when is met: a draft completes with no duplicate seats
and the pick distribution is recorded. Seven runs, five seats each, example pack
(8 playbooks), clean route, `auto:reliable`, `eval` none - this is a driver, not
a campaign, so the numbers below are a smoke result and **nothing here may be
cited as a diversity read.** Three reasons, and any one of them is enough.

- **`auto:reliable` is a routing strategy, not a model.** A different upstream may
  serve each seat, so the run has no single subject. Observed: two ids that are
  the same model (`nemotron-3-ultra` and `nvidia/nemotron-3-ultra-550b-a55b`), so
  even counting upstreams would have double-counted one.
- **The code changed mid-sweep.** Upstream recording landed between seeds 3 and 5,
  so the runs are not all the same program. The fault is procedural and the fix
  is a branch or a wait, not a caveat.
- **2 of 7 runs died on a socket timeout** (seeds 4 and 6), so the surviving five
  are a success-conditioned sample. Its own queue row.

What it does establish, which is what the slice was for: **the loop runs end to
end against live models at 0% fallback** in all five completed runs, 5 seats in
~80 s serial. Picks over those 25 decisions: WITNESS 5, RETURNEE 5, FIXER 4,
TRUE BELIEVER 4, PROVIDER 3, UNDERSTUDY 3, LATE BLOOMER 1, GOLDEN ONE 0, against
a uniform 3.125. **That is mild concentration and it is NOT the collapse an
interim read of the first two seeds looked like** - the early runs shared a set of
five, and three more runs spread across seven of the eight. Recorded here so the
premature reading does not survive as folklore; the real read needs a pinned
model, one program, and the timeouts fixed.


## changeling discussion length - S22's `--rounds 2` vs `--rounds 3` pair, READ 2026-09-03

**NOT SHOWN.** A third discussion round did not move blind villager deduction, and
it cost 30% more card. Read with `py -3 -m eval.rounds_pair_verdict`, exit 0,
against the pre-committed `docs/changeling-rounds-pair-criterion.md` (frozen
2026-09-02T06:38Z, before either arm ran). Records `eval/records/cl-rounds{2,3}
{,-random}.json`, recipe `eval/runs/changeling-rounds-pair.cmd`.

**The runs.** 200/200 games each, local `qwen36-35b-a3b-iq3`, `--arm llm --seats 5
--theme folk --seed 5000 --no-thinking --timeout 240`, driver defaults otherwise.
rounds2 down 2026-09-03T05:38 local in 17900 s (4.97 h); rounds3 down 12:07 in
23340 s (6.48 h) - **+30.4% GPU for a difference that spans zero**. The verdict's
settings pin read each record's own `args` against the criterion and both MATCH.
196 scored per arm, 251 blind votes per arm.

**The pair's figure.** Blind villager accuracy, three rounds minus two:
**-2.79%**, Newcombe 95% **[-11.41%, +5.89%]** - the interval the criterion names,
and it includes zero. Paired game bootstrap [-11.89%, +7.03%] beside it, deciding
nothing. The criterion priced a half-width near 8.5 points and said the pair
cannot settle a gap smaller than nine; the observed gap is under three, so this is
the "not shown" the power section wrote down in advance. **No second pair chases
it**, and no bar may be added now.

**Fallback did NOT rise on the longer arm**, which was the pre-registered payload
worry: 0.43% (rounds2) against 0.50% (rounds3), both far under the 10% void bar;
recovered 7.60% against 6.45%, both under the 25% warn. A third round at a fixed
`--max-tokens 1536` costs no measurable legality.

**Gate #3 HOLDS on both arms**, secondary per the criterion: rounds2 119/251 =
**47.41%** Wilson [41.32%, 53.58%]; rounds3 112/251 = **44.62%** Wilson [38.60%,
50.81%]. Both floors clear the 35.84% reference. Each arm's own random control
agrees with that reference within the criterion's one-point tolerance (35.44% and
36.14%), so the reference stays the bar and the own-arm clause does not fire.
**Gate #2 is reported with no verdict**, as the criterion requires: pack win 50.51%
and 52.04%.

**An instrument control worth keeping: the two random controls share a deal
exactly.** The criterion demanded the census agree, since random play does not
speak - it does, to the vote: blind votes 1281 on both, strata `identity` 1103 /
`positional` 582 / `false` 448 on both, dawn-wolf denominators 23/483/494 on both.
Their ACCURACIES differ (35.44% vs 36.14%) because a third round advances the seed
stream and the random seats draw different votes, which is the expected shape and
not a census disagreement.

### The free reads - unadjusted, none a gate, and one of them points somewhere

Six reads below share the arms' seeds and carry no multiplicity correction. The
criterion declares them free and forbids a bar after the fact, so **nothing here
is promotable and none of it revises the NOT SHOWN above.** Intervals are
Newcombe over independent proportions, three rounds minus two.

| free read | rounds2 | rounds3 | diff | Newcombe 95% |
|---|---|---|---|---|
| pack voted the fellow it was told | 15.66% (31/198) | 24.75% (49/198) | **+9.09%** | [+1.17%, +16.90%] |
| present claims true ("I am X") | 78.75% (467/593) | 74.12% (716/966) | **-4.63%** | [-8.85%, -0.26%] |
| ...village seats only | 87.16% | 82.31% | **-4.85%** | [-9.09%, -0.34%] |
| ...pack seats only | 60.64% | 55.85% | -4.79% | [-13.56%, +4.23%] |
| dealt claims true | 82.24% | 78.21% | -4.04% | [-9.01%, +0.95%] |
| village voted a seat shown village | 29.73% (44/148) | 26.35% (39/148) | -3.38% | [-13.49%, +6.83%] |

**The one that matters is the first, and it is the SAME statistic the skin pair's
effect landed on.** `eval.changeling_audit` against each arm's own random control:
under two rounds a pack seat voted its fellow 15.66%, well below its control's
25.69% - the pack PROTECTING its partner. Under three rounds it reads 24.75%,
sitting on its own control's 26.82%, so **the protection is gone by the third
round.** That is a pack statistic; the pair's primary is a village one, so an
effect this size is structurally outside what the criterion could see. It does not
settle anything by itself - two unadjusted reads on two different axes both
landing on the partner vote is a pattern worth ONE properly-powered arm, not a
claim - and the row that would spend it already exists: the skin pair's row asks
for a new criterion with the pack statistic PRIMARY on fresh seeds. **This read
raises that row's value; it does not add a row.**

**A third round buys more talk and slightly worse talk.** Present claims went 2.97
per game to 4.83 (+63%) while their truth rate fell 4.63 points - so the extra
round is spent making more self-claims, not better ones, and the village side
carries the whole decline. Consistent with `AGENTS.md`'s standing position that
more context is not monotonically good, and it is the second dated instance of it
on this box after `_night_against_the_table`.

## changeling gate #2 as a pair - the live pack COSTS itself 17.9 points, READ 2026-09-03

`docs/changeling-gate2-pair-criterion.md`, frozen 2026-09-02T06:47:03Z and
unedited since. `py -3 -m eval.gate2_pair_verdict`, exit 0. Records
`eval/records/cl-rounds2.json` (the live-pack arm, cited not chosen - it IS S22's
two-round record) and `eval/records/cl-gate2-village.json` (`--arm llm-village`,
village seats live by dawn truth, pack seats `RandomPolicy`), 200 games each on
seeds 5000..5199.

**Fallback first, per arm.** `llm` 0.43% fallback, 7.60% recovered; `llm-village`
0.20% fallback, 5.17% recovered. Both are far under the 10% void and the 25%
recovered flag. 196 scored games on each arm, above the 190 floor that would have
REFUSED the pair. The settings pin matched both records against their own `args`.
**Pairing is counted, not assumed: 200/200 pairs share their dawn truth.**

| arm | pack behind the pack seats | pack win rate, scored | Wilson 95% |
|---|---|---|---|
| `llm` | live | **50.51%** (99/196) | [43.57%, 57.43%] |
| `llm-village` | random | **68.37%** (134/196) | [61.56%, 74.47%] |
| all-random reference | random, and a random village too | 64.29% (126/196) | [57.36%, 70.66%] |

**The pair: -17.86%, Newcombe 95% [-27.10%, -8.15%], excludes zero -> INFORMS.**
Paired game bootstrap [-26.02%, -9.69%] beside it, never deciding. The all-random
row is a REFERENCE and never decides - it moves both populations, which is why it
cannot be the control. The criterion pre-committed the reading in both directions,
so this needs no interpretation after the fact: below zero reads **"the pack's
play costs it against this village"**, a finding about the model rather than a
failure of the instrument. The effect is larger than the pair's ~10-point
half-width, so it is inside what this design can settle.

**The named free read says what changed for the village.** Blind villager
accuracy, same village population on both arms: **47.41%** [40.16%, 54.43%] with a
live pack, **31.08%** [24.56%, 37.88%] with a random one, against a 36.47% chance
bar. So the live-pack arm clears chance and holds gate #3; the random-pack arm
does NOT clear it - its interval straddles the bar. The village deduces worse when
the pack is unreadable, which is what the criterion anticipated a gap here would
mean: the pack's play changed what the village had to work with.

**Second named free read**, `eval.changeling_audit` on the village arm - how a
live village votes when the pack's speech carries no intent at all: shown-village
52/148 = 35.14% [27.91%, 43.11%]; partner 35/198 = 17.68% [12.99%, 23.59%], which
is a RANDOM pack's partner rate and therefore a baseline, not a behaviour. **Do
not read it against the skin pair's 24.75%/13.64%** - those arms are `greek` on
different seeds and the denominators are not the same population.

**What this does NOT show.** The mechanism is untested. "Speech is evidence, so a
talking pack hands the village something to deduce from" is the obvious reading of
the two numbers together and this pair does not test it; it moves the whole pack
policy at once, not its speech. Nor does it say a live pack is worse at the game -
only that against THIS village, on this model, at these settings, its play is
worth -17.9 points against playing at random.

## changeling skin pair - the effect landed on the PACK, moved from `queue.md` 2026-09-03

Free read, `eval.changeling_audit`, both arms 2026-09-02: a pack seat voted the
fellow it was told 49/198 = 24.75% under `greek`, 27/198 = 13.64% under
`greek-named`, diff -11.11% Newcombe [-18.75%, -3.35%]. `greek` sits ON its
control's 25.69%; `greek-named` is below it, so proper names read as the pack
PROTECTING its partner. The village-side shown-village count moved +2.70%
[-7.31%, +12.65%] - nothing.

The pair's primary is blind villager accuracy, a VILLAGE statistic, so the one
thing that moved is structurally outside it. **Not promotable**: the criterion
declares the audit a free read and forbids a bar after the fact, and this is one
of ~6 such reads, so the interval is unadjusted. The rounds pair moved the same
statistic the same way (§The free reads above), which is what the partner arm
exists to spend properly.

## belfry night coherence, own TRANSCRIPT - NO RECALL, READ 2026-09-03

`docs/belfry-night-transcript-criterion.md`, frozen 2026-09-02T10:16:52Z.
`py -3 -m eval.belfry_night_verdict --criterion transcript`, exit 0, no void.
The third and last leg of the 09-02/09-03 chain; model arm 1000/1000 at
elapsed=3160s, seeds 15000..15999.

**The instrument control passes**: the seeded-random arm sits at 47.71%, Wilson
[39.95%, 55.59%], which contains one half, so nothing here is INSTRUMENT SUSPECT.
Player fallback 0/167325 and 0/169397 = 0.00% on both sides; adjudicator fallback
0/2454 = 0.00%, 27 recovered; every non-fallback gauge choice served by
`qwen36-35b-a3b-iq3`. Model side 2266 gauge tellings, 505 false, all sourced
`model`; control 2196 tellings, 462 false, all `random`.

| read | pairs | coherent | Wilson 95% |
|---|---|---|---|
| control, seeded random | 153 | 73 = 47.71% | [39.95%, 55.59%] |
| **this arm, own transcript, `prior` withheld** | 181 | **111 = 61.33%** | **[54.07%, 68.12%]** |
| published withheld read, 2026-09-02 | 122 | 94 = 77.05% | [68.83%, 83.62%] |
| published supplied read, 2026-09-02 | 163 | 152 = 93.25% | [88.32%, 96.19%] |

**The three pre-committed lines.** Against chance: **COHERENT** - 61.33% clears
one half on both floors, Wilson lower 54.07% and bootstrap-by-game 2.5th
percentile 53.77%. Against the withheld read: **NO RECALL** - RECALLS needed this
arm's Wilson lower endpoint above the withheld read's upper 83.62%, and 54.07% is
not. Against the supplied read: **BELOW SUPPLIED** - the whole interval sits under
88.32%.

**What the criterion says NO RECALL means, in its own words:** the transcript
bought nothing over the withheld ask - the model does not find its earlier telling
in its own words, and a referee built from stateless completions needs the harness
to remember for it. It is a fact about this model at this size, and it says
nothing about a model that writes itself notes, which is a different mechanism and
a different criterion.

**Not pre-committed, and therefore not a verdict: this arm sits BELOW the withheld
arm on non-overlapping intervals** - 61.33% [54.07%, 68.12%] against 77.05%
[68.83%, 83.62%], upper 68.12% under lower 68.83%. The criterion licenses the
interval comparison (fresh seeds were chosen so the published read IS the
comparison) but defines only RECALLS / NO RECALL, with no verdict for below. So
this is an observation with a row behind it, not a result: on this evidence
handing the referee its own transcript looks worse than handing it nothing, and
nothing here establishes why. Denominators differ (181 pairs against 122) and the
games are different seeds by construction.
## belfry night coherence - is the transcript arm's deficit a POPULATION effect? NO, read 2026-09-03

CPU read against records already on disk, answering the question the queue's
own-transcript row named as its cheapest next step. **Post-hoc, unadjusted, and
no criterion licenses a bar on any of it** - the transcript arm's verdict stays
COHERENT / NO RECALL / BELOW SUPPLIED, and this only asks whether the unheld
below-withheld observation survives the obvious confound. Instrument:
`eval.belfry_night_verdict.coherence_pairs`, reused rather than re-implemented, so
these are the same pairs the verdict graded.

**The extra 59 pairs ARE a different population.** The transcript arm's pairs sit
deeper in the game: 54/181 = 29.8% at night 4 or later against the withheld arm's
23/122 = 18.9%, and its false tellings run later (mean night 2.30 against 2.10)
because its play droisoned the gauge more often - 505 false tellings against 384
on a near-identical 2266 against 2211 total. Depth is not free: the withheld arm
itself falls 81.0% -> 75.0% -> 71.4% across nights 2, 3 and 4.

**It does not explain the gap.** Per-night coherence, both arms:

| night | withheld | transcript | diff |
|---|---|---|---|
| n2 | 51/63 = 81.0% | 47/72 = 65.3% | -15.7pp |
| n3 | 27/36 = 75.0% | 32/55 = 58.2% | -16.8pp |
| n4 | 10/14 = 71.4% | 20/32 = 62.5% | -8.9pp |
| n5 | 3/4 = 75.0% | 7/14 = 50.0% | -25.0pp |
| n6+ | 3/5 | 5/8 | cells too small to read |

Direct standardisation, both directions: the transcript arm's rates on the
withheld arm's night mix give **62.25%** against 77.05% crude, a **-14.8pp**
difference where the crude one is -15.7pp; the withheld arm's rates on the
transcript arm's mix give 75.63% against 61.33%, **-14.3pp**. So depth composition
accounts for about one point of the fifteen. The deficit is inside the strata, not
in the mix.

**What it does NOT establish.** Stratifying spends the power that produced the
non-overlap: at the largest matched stratum alone, night 2, the intervals OVERLAP
- withheld 80.95% Wilson [69.6%, 88.8%] against transcript 65.28% [53.8%, 75.2%].
This read removes an explanation; it does not add a result, and the row still
needs an arm to settle direction.

**Not answerable from any record: whether the transcript arm's ASKS are longer.**
`ChoiceEvent` carries key, options, selection, fallback, recovered and upstream,
and no size - while player decisions have carried `prompt_size` and `reply_size`
through `core/callcost` all along. The code answers it unambiguously and the
record cannot: `Adjudicator.choose(recall=True)` sends `history=list(self.transcript)`,
and the transcript accumulates every accepted ask AND its reply for the whole game,
including the two setup asks, so the ask grows monotonically within a game and the
deepest pairs carry the longest one. That is a mechanism nothing on disk can size.

## changeling heuristic rung - the ladder's middle rung, measured 2026-09-02

`games/changeling/heuristic.py`, the changeling twin of cabal's hand-written
rung, MERGED to main 2026-09-03 after the changeling chain read (it touches
`eval/run_changeling.py`, which the chained recipes ran). Backend none, CPU, ~23 s
per 1000 games. Seeds 5000..5999, `--theme folk --seats 5`, two rounds, 977 of
1000 games scored (23 seated no pack at dawn). Records `eval/records/cl-heuristic*.json`,
untracked; the command reproduces them exactly:

```
py -3 -m eval.run_changeling --games 1000 --arm heuristic --theme folk --seats 5 --seed 5000 --out eval/records/cl-heuristic.json
```

The rules are in the module docstring. A seat plays the card it BELIEVES; a
village seat states its deal, its belief and every reveal truthfully in the
claim grammar `eval.audit_decisions` reads; a pack seat claims the bystander card
as its deal and accuses one village seat, and a fellow that reads the accusation
repeats and votes it; a village seat votes down a ladder - night-named pack,
refuted DEAL claim, a card claimed as a deal by more seats than the deck holds, a
seat that claimed no deal, random. Present-tense claims are never refuted: the
card may have moved. Gate #1 by construction and by test - the dawn-truth table is
replaced with one that raises and every decision still lands.

| arm, seeds 5000..5999 | village wins | BLIND accuracy (n=1281) | pack wins |
|---|---|---|---|
| `random` | 37.97% [34.98%, 41.06%] | 35.44% [32.77%, 37.99%] | 62.03% |
| `heuristic` (all five seats) | 43.91% [40.83%, 47.04%] | **49.26% [46.36%, 52.21%]** | 56.09% [52.96%, 59.17%] |
| `heuristic-village` vs random pack | 88.43% [86.28%, 90.29%] | 77.36% [74.35%, 80.28%] | 11.57% |
| `heuristic-pack` vs random village | 32.34% [29.48%, 35.34%] | 37.78% [35.17%, 40.60%] | 67.66% [64.66%, 70.52%] |

Chance for a blind villager on this deal is 35.85%.

**What un-random looks like here: the all-heuristic table clears the gate at
49.26% against 35.85%, and the pack still wins 56% of the games.** That is the
number the "changeling feels random" row asked for. It is a floor - sixty lines
of tallies - that a model arm on the same seeds can now be read against. Not
against S2: that read 44.53% [38.47%, 50.77%] on 247 blind votes, under the
pre-2026-09-02 vote rule and other seeds, so the intervals overlap and the
objects differ. The fair comparison is the seated arm in the queue row, and a
model losing to sixty lines of tallies would be the AvalonBench finding again
(`docs/reference-policies.md` §The control ladder).

**Two artifacts, both the kind `docs/control-ladder.md` warns about, and both
measured rather than assumed:**

- **The `heuristic-village` cell is mostly the control's vocabulary.** The random
  policy's four canned lines never make a deal claim, so the ladder's fourth tier
  (a seat that has claimed no deal) points at a random wolf by its silence. With
  that tier switched off the same cell reads 34.90% village wins and 31.62%
  [29.00%, 34.33%] blind accuracy - at or below chance. The all-heuristic cell
  does not move when the tier is switched off (49.26% either way), because every
  heuristic seat claims a deal and the tier never fires. **The 77.36% is not a
  deduction number.** It is the rung reading a twin's tell, exactly as cabal's
  99.5% hunter is.
- **In a mixed arm every liar is a sleeper, so every refutation lands on a
  villager.** Seated by dawn truth, the real wolves in `heuristic-village` are
  random and claim nothing; the only seats that lie are heuristic seats robbed
  INTO the pack card who believe they are wolves and hold village at dawn. Tier
  census over 600 games with the silence tier off: tier 1 (night-named pack) 44/57
  = 77.2%, because a seen wolf can be robbed or switched afterwards; tier 3
  (over-claimed card) 0/111 - every catch a sleeper; tier 2 fired 3 times. That
  0/111 is the belief/truth divergence the rung was built to make observable, in
  a control with no model in it. Any instrument that scores "caught a liar" on
  this game has to decide whether a sleeper counts, and the vote scorer says no.

**`heuristic-pack` is the clean cell.** Coordination alone - two fingers on one
village seat, the whole of `plurality-min2` - buys the pack +5.6 points over
random wolves against a random village (67.66% vs 62.03%, intervals touching),
with nothing read from the control's vocabulary.

What this does NOT show: anything about a model. The arm that puts this rung at a
table with LLM seats is the queue's "seat the heuristic against the MODEL" row
and is GPU work. The rung is a denominator, not a player.

## changeling mixed cells - the rung against a LIVE pack, INFORMS, READ 2026-09-03

One arm of the two `docs/changeling-mixed-criterion.md` names. `mixed-pack`
seats the model on the PACK by dawn truth and the hand-written rung on the
village, so the rung's figure is the village win rate. `mixed-village` was NOT
queued and never ran - a missing arm is a lost pair, not half a result, and no
cross-arm claim is made below.

Record `eval/records/cl-mixed-pack.json`, 200 games on seeds 5000..5199, 196
scored, 5162 s (1.43 h) on `qwen36-35b-a3b-iq3` at 100% served. Read with
`py -3 -m eval.mixed_verdict`; the record's own `args` pin against the
criterion's §Settings and match.

**Voids first, and the bar is the LIVE side's own rate.** The run-level
`fallback_rate` is diluted here - every rung seat enters the denominator and a
rung seat never falls back - so the number that governs is the pack seats' own:
**4/900 = 0.44%** against a 10% bar. Run level 0.13% is reported and gates
nothing. Recovered 1.67%, far under the 25% flag. 196 scored against a 150 floor.
Nothing voids.

**The control is RESCORED, never quoted.** `cl-heuristic.json` is 1000 games on
5000..5999 and this arm plays 5000..5199, so its published 43.91% is a figure
over a superset. `eval.mixed_verdict` rescores the first 200 game indices and
pairs against that. Two things surfaced in the rescore and both are recorded
because neither is visible from the summary: the JSONL held **3000 records for
1000 game indices** - it was written more than once and the last write of each
game is kept - and the recovered run reproduces the published summary exactly
(977 scored, 429 village wins), which is what makes the rescore trustworthy.

| the rung's VILLAGE win rate, 196 scored games | rate | Wilson 95% |
|---|---|---|
| against LIVE pack seats | **130/196 = 66.33%** | [59.45%, 72.57%] |
| against its own twin, `cl-heuristic` first 200 | 89/196 = 45.41% | [38.59%, 52.40%] |
| published at 1000 games - the wider reference, never the pair | 43.91% | - |

**Difference +20.92%, Newcombe 95% [+11.11%, +30.16%] - excludes zero, so
INFORMS.** The criterion pre-committed both directions and named this one: a live
side that claims deals badly, inconsistently or in a grammar the ladder refutes,
hands the rung evidence the random control never offered. The gap also clears the
~10-point floor §Power said was the smallest this pair could settle, so it is not
a marginal result.

**The secondary prices the artifact, and the artifact is real but not the whole
number.** Blind villager accuracy, same 251-vote stratum:

| the rung's blind accuracy | rate | Wilson 95% |
|---|---|---|
| against LIVE pack seats | 150/251 = 59.76% | [53.59%, 65.64%] |
| against its own twin | 123/251 = 49.00% | [42.88%, 55.16%] |
| against a RANDOM pack (`heuristic-village`, published) | 77.36% | [74.35%, 80.28%] |

The 77.36% was measured against a control that cannot talk, and the silence tier
was shown to carry it (§changeling heuristic rung: 31.62% with that tier off).
Priced against seats that DO talk it is 59.76%, so roughly 18 points of the
77.36% was the artifact - and the remaining 59.76% still sits clear of the 49.00%
twin, so the ladder holds signal underneath it. This is the artifact read the
criterion was written for, taken against a live opponent instead of against a
switch.

**The tier census is NOT PAYABLE from this record**, and that is a finding rather
than an omission. `HeuristicPolicy._vote` returns a seat, not the rung it fired
on, and the vote row carries no tier field, so the census would have to
re-derive the ladder - a second copy of the policy, the drift `eval.mixed_verdict`
avoids everywhere else by importing. It needs one field at the source. The cost
is specific: this is the first arm in the tree where tier 3 could catch a TRUE
wolf rather than a sleeper (§changeling heuristic rung records 0/111 sleepers
against a random control), so the read it would have bought is one no earlier
record could offer.

Gate #3's reference bar is 35.84% and this file makes no gate #3 call - the
criterion did not name one. Nothing here is a statement about `mixed-village`.

## changeling partner protection - the pre-registered replication is NOT SHOWN, READ 2026-09-04

`docs/changeling-partner-criterion.md`, frozen 2026-09-03T05:25:31Z.
`py -3 -m eval.partner_verdict`, exit 0, no void. This is the arm the two free
reads above (§changeling skin pair, §changeling discussion length) were sent here
to spend, and it spends them in the direction that says they were not an effect.

Record `eval/records/cl-partner.json`, 200 games on fresh seeds 17000..17199, 193
scored, 18830 s (5.23 h) on `qwen36-35b-a3b-iq3` at 100% served; control
`cl-partner-random.json`, 1000 games from the arm's own seed base. The record's
own `args` pin against the criterion's §Settings on both records and match.

**Voids first.** Fallback **0.70%** against the 10% bar. Recovered 8.73%, under
the 25% flag. 168 partner-eligible votes against the criterion's REFUSED floor of
150. The census check passes - arm and control agree exactly on the eligible
count over the 200 deals they share, which is the check that proves eligibility
is a property of the deal and not of play. Nothing voids.

| the partner vote - a pack seat voted the fellow it was told | rate | Wilson 95% |
|---|---|---|
| arm | **37/168 = 22.02%** | [16.42%, 28.88%] |
| its own random control | 178/840 = 21.19% | [18.56%, 24.08%] |

**Difference +0.83%, Newcombe 95% [-5.47%, +8.17%] - includes zero, so NOT
SHOWN.** Direction was deliberately not pre-committed and the point estimate sits
on the wrong side of zero for the prior anyway: the two free reads that motivated
this arm were -10.03% and -12.05%, and both lie outside this interval. The
criterion pre-committed that no second arm chases it, so the effect does not
survive its first pre-registered test and the two free reads are not quotable as
a finding.

**The instrument came in wider than its own power section.** §Power computed a
5.9-point half-width from ~198 partner-eligible votes, measured at 198/200 on all
four prior arms; this arm got 168, and the realized Newcombe half-width is 6.82
points. The arm stayed powered for the effect it was chasing - both prior effects
clear even the widened interval - so this does not soften the call. **What it
costs is a separate question the tree does not hold an answer to:** the fresh
17000-block deals partner-eligible games at 168/200 where the 5000-block dealt
198/200, the census check proves that is the deal rather than play, and no row
predicted it. It is a row now.

Free read, no verdict, and the criterion forbids promoting it: blind villager
accuracy 119/264 = 45.08% [39.19%, 51.11%] on the arm against 469/1252 = 37.46%
[34.82%, 40.18%] on its control, reference 35.84%. This file makes no gate #3
call - the criterion did not name one.
