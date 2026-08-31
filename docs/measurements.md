# Measured, dated - the numbers and the backends

Moved out of `queue.md` 2026-08-28: these are readings, not queue. Verbatim.
**Read before trusting any number in this repo.** Each verdict's own doc
(`docs/gate3a-retired.md`, `docs/gate3b-verdict.md`, `docs/durf-rung.md`,
`games/changeling/RULES.md` §S2 read) is canonical for that gate; this file is the
dated ladder underneath them.

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
| **`outed_own_role_in_public`, matched against theme names** | 0/1290 (matcher-blind) -> `hunt20b` **4/1150**, `hunt20c` **26/1580 = 1.6%** | **the old zero was a property of the matcher, not of the play.** It looked for `seer`/`mimic` in speech that can only ever say "Thought Police"/"Inner Party". Seats DO name their own role in public, and `hunt20c` seat 0 does it repeatedly as cover |
| `hunt_named_impossible`, allies from `known_allies` | 0/11 and 0/9, unchanged on these runs | no regression on the shipping deal, and it stops flagging a legal hunt on a `stray` - which is a wrong PROOF-class finding, the worst kind this file can emit |

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

## Changeling per-game deduction - S5 record re-read, 2026-08-30

`py -3 -m eval.deduction` re-read S5's 200 completed games with no GPU or new
play. The S5 record's fallback rate was **0.40%**, below the 10% void bar. The
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
