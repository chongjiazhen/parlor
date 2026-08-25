# RESUME - open work

Queue only. Done work leaves to git log. What's next:

- [ ] **NEXT: score the two runs in flight against the pre-committed criterion
      below.** `eval/records/hunt20.log` (local q36, 20 games, seed 1000) and
      `eval/records/huntcloud.log` (gray `auto`, 25 games, seed 2000) - both
      detached via WMI, both landing per-game JSONL + transcripts as they go, so an
      interrupted run is still a dataset. Gate #3a already holds (+30.7% local pinned,
      +66% cloud); #3b is the only open number. Do NOT soften the 1/3 Wilson floor.
- [ ] **Gate #3 was never blocked on the table talk - that read was wrong.** It was
      model capability: identical prompts scored -0.2% on the 12B and +66% on
      120B-class. `--register plain` helped the 12B (+16.7%) but bought suspicion,
      not judgement (7 of 8 games died at five_rejects). `--simultaneous` is built
      and unmeasured; the salience line has no measured benefit anywhere and is a
      removal candidate, on its own measurement.
- [ ] **Judge a detached run only by its own log/JSONL - never by a proxy.** Three
      times in one session CPU seconds, Win32 IO counters, and an exit code each
      read as liveness for network-bound work; the IO-counter one killed a healthy
      cloud run (those counters track FILE io, not sockets). And probe a cloud tier
      with a BURST (12 back-to-back), never a single call: a key under cooldown
      serves the occasional request while failing a stream, so a single-call probe
      says "healthy" about a tier that cannot carry a run.
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
- [ ] **Larger setups (6/7p) + the two information-degrading evils.** Package them
      together, because both only make sense at 3 evil seats.
      - The engine already supports both, and has since the first commit: `Role`
        carries `seen_by_seer` (False = the evil the seer cannot see) and
        `sees_fellow_evil` / `seen_by_fellow_evil` (False = the evil who neither
        knows nor is known by its own side). `entitled_knowledge` honours all
        three, so each role is ~2 lines of DATA. The cost is measurement, not code.
      - **Why they are worth more than variety: they degrade information in a
        principled way.** The unseen-evil variant halves the seer's knowledge, so
        the current +30.7% local / +66% cloud stops being partly "the seer acting on
        a handed answer" (already isolated at +13.7% by the blind-seat split) and
        becomes a claim about deduction. The blind-evil variant makes evil deceive
        WITHOUT knowing its partner, which is the honest version of gate #2 - the
        current claim is really "two agents told about each other cooperated".
      - **Not before gate #3 is called.** Changing what the seer knows mid-run means
        neither the old nor the new number means anything. Sequence them as the
        hardening pass you would actually publish from.
      - At 5 seats there are only 2 evil, so the unseen variant leaves the seer
        seeing exactly one and the blind variant leaves two evils who know nothing
        of each other - swingy to the point of noise. These are 7+ roles.
      - Watch role-name vs faction-name substring collisions in the leak audit (see
        the plain-skin "Loyalist" case).
- [ ] **Naming discipline, for when ONUW gets built.** Prose may NAME the games a
      rung is modelled on - README has done that since commit #1 and that is
      nominative reference, not passing off. What must never enter the canonical
      layer is a game's expression: its role names, art, or text. So ONUW's roles
      arrive as functional keys (`swapper`, `switcher`, `deceived`), never as the
      published character names, exactly as this game uses seer/watcher/mimic.
- [ ] **Spike #1.5: One Night Ultimate Werewolf** - ahead of Secret Hitler, and not
      for freshness. Two reasons, both structural:
      - **Belief != truth.** Robber/troublemaker/drunk swap roles during the night,
        so a seat's knowledge of ITS OWN role can be stale and false. `SeatView`
        renders truth today; ONUW forces the split between what is true and what
        this seat believes, and makes gate #1 strictly harder - the referee must
        maintain a false belief without correcting it and without leaking the swap.
        Sharper test of independent context than cabal can pose, where every seat's
        knowledge is both true and static.
      - **It fixes the N bottleneck.** One night, one discussion, one vote: ~10-15
        model calls against cabal's 80-220, so 10-20x the games per hour. Every hard
        question this session was gated on games-per-hour (14 min/game local, 5
        hunts per 12 games, a gate needing 30+). ONUW turns "cannot afford the N"
        into "run 200 overnight".
      Also no elimination, which is the point of preferring this family. Secret
      Hitler stays the better LADDER step (forced reveals, a deck the referee
      controls) but ONUW is the better ENGINE step. Do it only once gate #3 is
      called - it is also the pressure test for what really belongs in `core/`, and
      that question wants evidence, not a guess.
- [ ] Spike #2: off-map faction heartbeat (this is where hexis earns its seat).

## Pre-committed criterion for the hunt run (written 2026-08-25 19:54, BEFORE the numbers)

Run in flight: 20 games, `qwen36-35b-a3b-iq3`, seed 1000, 2 rounds, hunt fix in,
detached (`eval/records/run-hunt20.cmd`, log `eval/records/hunt20.log`).

- **Gate #3b holds only if the hunter's Wilson 95% floor clears 1/3.** That is the
  bar the scorer already applies; it is written here so it cannot be softened after
  seeing the result.
- **If it lands near chance, the answer is "not shown at this N" - NOT "run more
  games until it clears".** Stopping when a floor happens to cross is peeking, and
  it manufactures the significance it claims to find. A repo that voids runs over
  10% fallback and refuses to read gate #2 off a random baseline cannot ship that.
- **Power, computed before the run:** at a true 60% the gate needs ~16 hunts
  (~21-38 games); at 50%, ~32 hunts (~43-76 games); at 45%, ~62 hunts (83-148
  games). This run yields ~8-15 hunts. So it can SHOW a strong hunter and cannot
  settle a marginal one - that asymmetry is the reason for the bullet above.
- **If the hunter lands marginal, respecify the metric rather than buying games.**
  Gate #3 is bottlenecked on its lowest-power half: the vote metric collects
  100-222 samples per 12 games, the hunt collects 5. A ranked or confidence-graded
  hunt would yield graded signal per hunt instead of one bit, which is the same
  reason the blind-seat split beats the raw discrimination number.

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

**Code invariants moved to `CLAUDE.md`** - it is always loaded, these are not,
and two copies of one rule is how the stale copy wins an argument. What stays
here is project state: the route calls and what a run measured.

- Independent context = one model + per-seat private context slice, not N brains.
- Referee is deterministic code; LLM only for players (and, later, judgment-GMs).
- Cloud is fine for game-fiction secrets (not credentials); local for deception checks.
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
