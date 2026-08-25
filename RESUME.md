# RESUME - open work

Queue only. Done work leaves to git log. What's next:

- [ ] **The seer ignores what the night told it, and that is what blocks gate #3.**
      Measured 2026-08-25, local 12B, 8 games, 2 rounds, 0.37% fallback - so this is
      a clean measurement, not a degraded one. Good seats approve tainted teams
      51.5% vs clean 51.3% (discrimination -0.2%, n=138). Split by role, the seer -
      which is *told* both evil seats by name - approves a team carrying a known
      evil **42%** of the time against 31% for a clean team. It is not deducing
      badly; it is not using ground truth it already has. Watcher +27% (n=13, noise).
      Two levers, and they are distinguishable: restate the seat's entitled
      knowledge inside the VOTE ask and name the overlap with the proposed team (a
      prompt fix - measure it, do not assume it), or a stronger model. The cloud
      `auto` run answers the second before you spend effort on the first.
- [ ] **Gate #3 still not shown, and now for a known reason** (above). Hunter 3/6 =
      50%, CI floor 18.8%, so the hunt half needs far more games than 8 even if it
      is real. Gate #2 stays unreadable by design.
- [ ] Larger setups (6/7p): add to `roles.SETUPS`, watch role-name vs faction-name
      substring collisions in the leak audit (see the plain-skin "Loyalist" case).
- [ ] Larger setups (6/7p): add to `roles.SETUPS`, watch role-name vs faction-name
      substring collisions in the leak audit (see the plain-skin "Loyalist" case).
- [ ] Spike #2: off-map faction heartbeat (this is where hexis earns its seat).

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
