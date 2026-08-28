# Measured, dated - the numbers and the backends

Moved out of `RESUME.md` 2026-08-28: these are readings, not queue. Verbatim.
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
- **The taint-level row is a STEP, not a slope, in both runs that have it** - a real
  0->1 drop and no further response at 2 (`hunt20c`'s 1->2 leg is exactly flat). The
  linear "per extra saboteur" statistic is mis-specified for this shape, and the
  binary row is the better-behaved one. The scorer's "superseded by the graded slope"
  note has it backwards.
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
fallback. **9/20 = 45.00%**, Wilson [25.82%, 65.79%] vs the derived bar 33.33% - NOT
SHOWN, at exactly the 0.50 hunts/game the power table assumed. All three
draw-dependent items came back negative there; **carry no run-length caveat
forward.**
