# RESUME - open work

Queue only. Done work leaves to git log. What's next:

- [ ] **Live players (gate #2/#3).** Wire `core.backends.Backend` into a player policy
      that reads `render_context(seat)` and returns a legal action (propose/vote/card/
      hunt). Parse the model reply into an action; refuse + re-ask on illegal.
- [ ] **eval/run_games.py** - run N games in parallel on `clean:3001`, score:
      evil-win-rate (gate #2) and good-vote-vs-truth + hunter-accuracy (gate #3).
- [ ] **Deception spot-check** - one game on `local:8090` with an uncensored model;
      confirm the mimic/hunter actually lie. If refused, escalate the player system
      prompt (borrow a CoomKit jailbreak, per backend).
- [ ] **Discussion phase** - none yet; add a bounded round-robin (<=1-2 utterances/
      seat) before each VOTE. That is where independent context earns its keep (the
      seer must talk without leaking). Cap it: serial local = N calls/round.
- [ ] Larger setups (6/7p): add to `roles.SETUPS`, watch role-name vs faction-name
      substring collisions in the leak audit (see the plain-skin "Loyalist" case).
- [ ] Spike #2: off-map faction heartbeat (this is where hexis earns its seat).

## Decisions already locked

- Independent context = one model + per-seat private context slice, not N brains.
- Referee is deterministic code; LLM only for players (and, later, judgment-GMs).
- Canonical layer is branding-free functional keys; fiction is a swappable Theme.
  Default face = 1984-en; no branded skin shipped.
- Cloud is fine for game-fiction secrets (not credentials); local for deception checks.
