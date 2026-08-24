# RESUME - open work

Queue only. Done work leaves to git log. What's next:

- [ ] **No readable transcript exists.** `demo.py` prints to stdout, `run_games.py`
      writes JSON; neither leaves a game log a human can read. Add `--transcript`
      to both, rendering from `public_events` (speech as speech, `think` never).
      Sample records to render against: `eval/records/*.json` (gitignored - raw run
      output stays out of history; a rendered transcript that evidences a claim is
      what gets committed).
- [ ] **Gates #2/#3 are wired but not shown.** `eval/run_games.py` runs and scores;
      no run yet has cleared gate #3, so gate #2 stays unreadable by design. Two
      things to try before widening N: more discussion rounds (`--rounds 2`) so
      votes have evidence behind them, and a stronger cloud model than the ones
      benched below.
- [ ] **Rejection deadlock on the local 12B.** Both spot-check games ended
      `five_rejects` - suspicious models reject nearly everything and nobody ever
      runs a mission. Options: raise the reject penalty's visibility in the VOTE
      prompt (it already warns), or seat a mixed table (LLM good vs random evil) to
      isolate which side is stalling.
- [ ] **A mixed arm.** `--arm llm|random` is all-or-nothing today. LLM-good vs
      random-evil (and the inverse) would separate "good can deduce" from "evil can
      deceive" instead of measuring them entangled.
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
- **`minimax-m3` reasons out loud and needs headroom.** A 10-game run scored nothing
  at 85% fallback: at `max_tokens=512` it spent the whole budget on visible
  reasoning and never reached the JSON. Default raised to 1536 and exposed as
  `--max-tokens`; **not yet re-verified** (the box was 429'd immediately after).
  Either confirm 1536 clears it or pin a model that answers without thinking aloud
  (`nemotron-3-super`, `qwen3-30b-a3b-fp8`). A too-tight cap and a refusing model
  are indistinguishable in the scores - only the refusal trace separates them.
