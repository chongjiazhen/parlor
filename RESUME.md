# RESUME - open work

Queue only. Done work leaves to git log. What's next:

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
