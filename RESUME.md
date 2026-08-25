# RESUME - open work

Queue only. Done work leaves to git log. What's next:

- [ ] **Gate #3 is blocked on the table talk drowning the evidence**, not on the
      model. See §Measured: the same salience line that moved the seer 46 points in
      isolation moved ONE point in a live game, and the difference between the two
      setups is twenty lines of chatter between the fact and the decision. Levers,
      in the order they became worth trying: `--register plain` (running), the trim
      fix (facts now outrank chatter - every run before 3d0d07d was scored on games
      whose early missions had been deleted from the record, so re-baseline before
      trusting any older number), `--simultaneous` (built, unmeasured).
- [ ] **A per-seat private notebook.** The one real gap in "play like a human":
      `think` is dropped every turn, so a seat re-derives its read from scratch and
      cannot remember that it caught seat 2 lying in round 1. Its own words shown
      only back to itself - gate #1-safe by construction, like `think`. Needs its
      own line cap; it rides on every call.
- [ ] **Mini-personas** (credulous / suspicious / contrarian / by-the-numbers) as
      per-seat judgment biases, assigned from the game seed and recorded so the
      scorer can split by persona. Trigger: only if a table that argues from
      evidence still votes identically. NOT for flavour - votes are already
      independent (§Measured), so this buys nothing until the talk carries evidence.
- [ ] **Gate #3 needs N far past 8 games.** Hunter accuracy is 1-in-5 to 3-in-6 at
      n<=6 hunts; the CI floor cannot clear 1/3 at that size whatever the truth is.
      And `good approve clean team` runs on ~12 votes a run, because most teams in a
      5-seat game carry an evil - that denominator is too thin to gate on. This is a
      cloud-scale job, so it waits on quota, not on the GPU.
- [ ] Larger setups (6/7p): add to `roles.SETUPS`, watch role-name vs faction-name
      substring collisions in the leak audit (see the plain-skin "Loyalist" case).
- [ ] Spike #2: off-map faction heartbeat (this is where hexis earns its seat).

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
| record length vs the 60-line cap | 10 of 16 games over, speech:facts ~4:1 | the trim was deleting missions 1-2 (fixed, `3d0d07d`) |
| cap at 512 vs 1536 max_tokens, `nemotron-3-super` | 0/4 -> 2/4 parsed, failures truncated at BOTH caps | no cap fixes a model that thinks out loud; pin one that does not |
| **cloud `auto` (mixed 120B-class), character register, 12 games** | **discrimination +66.0%** (clean 94.4%, tainted 28.4%, n=192; 2.5% fallback) | **gate #3a HOLDS - it was model capability, not the prompt** |
| same run, hunter | 33.3% (3/9, CI floor 12.1%) | exactly chance - gate #3b is now the blocker |
| local 12B, `--register plain`, same seeds as the salient run | discrimination +16.7% (blind seats +11.4%, n=76) | first positive on the 12B, but 7 of 8 games died at five_rejects |
| **local `qwen36-35b-a3b-iq3` (MoE 35B-A3B APEX), 12 games, 0.69% fallback** | **discrimination +30.7%** (blind seats +13.7%, n=222); evil 66.7% with 6 wins by SINKING missions and 32 fail cards | gate #3a holds on ONE pinned local model - reproducible, unlike the cloud's 30-upstream `auto` mix |
| same model, seer bench | +80% as-is vs +72% with the salience line | the salience line is now HARMFUL - it competes with reasoning a capable model already does |
| hunts across ALL live runs | 8/26 = 31%, and **5 of 26 named the hunter's own ally** | fixed in `hunt()`: a seat the night named as yours cannot be the seer, so the referee refuses it |
| cost, `q36` local | ~14.6 min/game (reasoning distill, long generations) | a 50-game hunter run is ~12h overnight; cloud is ~3 min/game when quota allows |

## Decisions already locked

- Independent context = one model + per-seat private context slice, not N brains.
- Referee is deterministic code; LLM only for players (and, later, judgment-GMs).
- Canonical layer is branding-free functional keys; fiction is a swappable Theme.
  Default face = 1984-en; no branded skin shipped.
- Cloud is fine for game-fiction secrets (not credentials); local for deception checks.
- **What a player says is gameplay, not a leak.** Gate #1 audits the referee's own
  bytes only (`render_context(seat, include_speech=False)`); an agent naming a role
  out loud is a claim, and it may be false. Private reasoning (`think`) reaches
  neither channel.
- **Gate #2 is conditional on gate #3.** Measured: with good voting at chance, evil
  wins ~65% with no deception at all. An unconditioned evil win rate measures the
  random baseline, so the scorer will not call gate #2 until gate #3 holds.
- **A number ships next to its fallback rate.** A decision no model could make
  legally is played at random and counted; the scorer voids its verdicts above 10%.
- **Gate #1 is enforced by the driver, not by callers.** `play_game` audits every
  turn and raises; it is not an opt-in callback, because the eval lane forgot to
  pass one and ran live models unaudited for a full session.
- **`core/` = what game #2 inherits, `games/<name>/` = what is about that game.**
  Reply-reading is generic and lives in `core/replies.py`; the phase-to-key mapping
  is not and stays in the game. Resist promoting anything else until a second game
  actually needs it.
- **`--rounds 2` cleared the rejection deadlock.** 1 of 8 games ended `five_rejects`
  at two discussion rounds, against 2 of 2 at one round. One round gives a vote
  nothing to reason from; treat 2 as the floor for any live run.
- **Pin a model for attribution, use `auto` for capacity - and record the served
  upstream either way.** freellmapi fails over across its keys, but a pinned id can
  only hop between keys for providers serving that exact id, so a cooled provider
  returns an instant 429 with no hop available. `auto` has the whole catalog and
  keeps answering. The response body's top-level `model` is the ONLY thing that
  says who answered; `Backend.complete_meta` returns it and the report prints the
  mix, so an `auto` run is honest about being several models averaged.
- **`find_leaks` stays naive substring matching.** A false positive is a loud test
  failure; a false negative is a shipped leak. Do not "fix" it with word boundaries
  to quiet a collision - rename the colliding term instead.

## Route: local is for spot-checks, not for gates

Local needs no wiring - `Backend` passes `--model` straight through and the router
is exact-match, so any armed model is one flag away. The question is whether it is
worth running there at all, and for the GATES it is not: local is serial, ~9 min a
game, so the N-game statistics gate #3 needs are unaffordable there. Local's job is
the thing cloud cannot do - an uncensored model, privately, to answer "will it
deceive at all" - and that answer is already in hand.

Reach for a better local model (a qwen3.8-27b, or a half-resident quant sized so an
image-diffusion model stays co-resident on the 16 GB card) only when one of these
lands: a cloud model turns out to REFUSE to deceive (untested - the one cloud run
was void), or you want games running alongside image gen. Neither is on the gate
path today.

## Backend notes (measured 2026-08-25)

- `local:8090` armed: `hexis-active`, `rocinante-x-12b-heretic-q4`. The heretic 12B
  deceives without any prompt escalation - the mimic fabricated a prior private
  conversation to build credibility, the hunter played concerned-loyalist and then
  correctly named the seer. `PLAYER_SYSTEM_PROMPT` needed no jailbreak. Cost: ~3s
  per decision, ~9 min per game, serial.
- `clean:3001` needs `PARLOR_API_KEY`. Pin a model - `glm-4.7` is in `/v1/models`
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
