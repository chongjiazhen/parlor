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
- [ ] **Negation pass over the model-facing strings** (the rule is
      `.claude/rules/model-facing-text.md`, path-scoped so it fires when you open
      the files that hold them). Steering by prohibition makes the banned behaviour
      MORE available, and the live prompts do it in at least three places:
      `"speak in the first person, and do not answer your own earlier lines"`
      (referee DISCUSS ask), `"do not defer to whatever the table already seems to
      think"` (plain register), `"no theatrics, no slogans, no world-flavour"`
      (same). Each has a positive form - speak TO the other seats; form your own
      read first; speak plainly and cite the record. The referee's refusals
      (`cannot fail a mission`, `cannot be the informant`) are hard guardrails and
      stay, though each already pairs with a positive instruction.
      **This is a measured change, not a cleanup** - same seeds, one variable, and
      it waits until the runs in flight land or it contaminates them.
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
      - **A bigger table does NOT fix the thin denominator - it makes it worse.**
        The §Measured note blames the ~12-votes-a-run sample on the 5-seat size,
        which implies growing the table would help. The arithmetic says otherwise:
        clean teams get combinatorially RARER as seats grow, faster than the extra
        good voters compensate. P(all-good team), averaged over the official
        mission sizes, times the good-voter count:

        | Seats | Evil | Team sizes | P(clean) | Good voters | Good-votes-on-clean per vote event |
        |---|---|---|---|---|---|
        | 5 | 2 | 2,3,2,3,3 | 0.18 | 3 | **0.54** |
        | 7 | 3 | 2,3,3,4,4 | 0.114 | 4 | 0.46 |
        | 8 | 3 | 3,4,4,5,5 | 0.071 | 5 | 0.36 |

        8p yields ~two-thirds of 5p's clean-team samples per vote event while
        costing ~60% more calls, since every seat speaks every round. And gate #3b
        is untouched either way - hunts are ONE per game at any table size. So
        table size is orthogonal to the binding constraint, and reaching for 7p to
        buy samples spends GPU-hours going backwards. (Assumes random teams; real
        leaders propose deliberately, so magnitudes shift, direction does not.)
      - **The denominator fix is the metric, not the table.** Binary clean-vs-
        tainted discards ~82% of votes. Grade taint continuously - how many evil on
        the proposed team, against what that seat could know - and every vote
        becomes a sample. Same insight as the ranked/confidence-graded hunt: turn
        one bit per rare event into graded signal per common event.
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
      - **Ship a werewolf-vocabulary theme on this rung, and that is the whole
        answer to public legibility.** A public repo has a real problem that "team-
        mission hidden-role deduction game" means nothing to anyone outside the
        hobby, while "werewolf / seer / villager" means something to nearly
        everyone. That vocabulary is public-domain folk-game vocabulary (Mafia,
        Davidoff 1986) carrying no branding question, and it lands free on a rung
        already queued on engine grounds. **This is why a vanilla Werewolf rung is
        NOT worth building for legibility**: it sits on the same rung as cabal
        (deterministic referee, bounded actions, no judgment), so it buys
        recognition and no engine progress, and it has elimination - a shrinking
        table, variable agent count per game, dead seats contributing no decisions,
        i.e. the N problem from the wrong side. Legibility is a theme and a README
        paragraph, not a spike.
- [ ] Spike #2: off-map faction heartbeat - factions acting on their own clock,
      driven by a long-running agent process outside the game loop.
- [ ] **Evil over-sabotages, and it is the seer-salience bug wearing the other
      team's colours.** Measured on the hunt20 run in flight, 13 games, 43 mission
      resolutions: fail-count distribution `{0: 23, 1: 11, 2: 9}`, need=1
      throughout. So **9 of 20 failed missions (45%) had BOTH evils play fail when
      one sufficed.** On a 2-seat team that names both of them outright; on a
      3-seat team it cuts the good side's search to three pairs. It is the single
      largest free information gift on the board and evil hands it over on half the
      missions it wins.
      - The rules already allow the right move. `validate_card` refuses only a GOOD
        seat playing fail, so evil may play success freely, and the MISSION prompt
        already says "weigh sabotage now against the suspicion a fail here would
        put on this team". The capability is there; nothing lines it up.
      - **What the seat is never told: how many fails are REQUIRED.** `need` appears
        only in the public event AFTER resolution (`referee.py` mission()), never in
        the ask. A seat cannot weigh redundant sabotage without knowing one fail is
        enough. It also is not told, at the decision point, that its partner is on
        this same team - it can derive that from the public proposal plus night
        knowledge, but deriving is exactly what `_night_against_the_table` proved
        models do not do unprompted.
      - **Same shape as the measured seer result, and that is the reason to expect
        it to work.** The seer HELD the knowledge and did not use it: 83% vs 90%
        (+7%, nothing) until the prompt lined the fact against the table, then 37%
        vs 100% (+63%). Evil holds partner identity and team composition and does
        not line them up either. Fix is the mirror: state `need` in the MISSION ask,
        and name which other seats on this team are yours.
      - **This is a confound in gate #3a, not just an evil-side weakness.** Good's
        +30.7% discrimination is measured against an evil side that self-identifies
        on 45% of its successful sabotages. Some unknown share of that number is
        good exploiting a blunder rather than deducing from discussion. So fixing
        evil is not a fairness gesture - it is required before the good-side number
        means what it claims. Expect discrimination to DROP when this lands; that
        drop is a truer number, not a regression.
      - Sequence: measured change, same seeds, one variable, after gate #3 is
        called. Distribution above is from a PARTIAL run (13 of 20) and is an
        incidental mechanical count, not the pre-committed hunt metric - recompute
        on the full run before quoting it anywhere load-bearing.
- [ ] **Stratify cloud results by served upstream instead of pooling them.** The
      problem with an `auto` run was never that it is undocumented - `complete_meta`
      already returns the served model and the report prints the mix. It is that
      POOLING hunts across a time-varying model population computes a Wilson
      interval over an ill-defined denominator. Record the served upstream on each
      decision, report per model class, and an `auto` run stops being "several
      models averaged": cells accumulate ACROSS runs, so tonight's nano hunts and a
      future 120B-class run land in different cells instead of contaminating one.
      Retires the "reproducible, unlike the cloud's 30-upstream mix" asymmetry -
      stratified, a cloud run is reproducible at the cell level. Does not rescue a
      thin run: ~10 hunts over 3+ upstreams is nothing per cell.
- [ ] **Theme as an experimental variable, not a default to fix** (design:
      §Open design note - moral framing). `1984-en` stays the shipping default;
      there is no licensing reason to drop it and it is the face every committed
      transcript wears. What is open is that the blurb inverts moral polarity -
      sabotage reads as heroic, deceit as survival - and nothing measures whether
      that moves behaviour. No number in §Measured records which theme produced it,
      so a theme change is a MEASURED change on the same terms as the negation
      pass: same seeds, one variable, after gate #3 is called.
- [ ] **Two shapes not to harden further before game #2** (reasoning:
      §Open design note - the RPG rung). Don't add another game's phases to
      cabal's `Phase` enum or to the `action_prompt` if-chain; don't grow
      `ACTION_KEYS` into a shared flat tuple. Both are the RPG's on-ramp and both
      are cheap to lift while they are still one game wide.

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

## Open design note: the action channel, and what the RPG rung breaks

Written 2026-08-25, unmeasured, from a design read of `core/replies.py`,
`referee.action_prompt`, and `player.parse_action`. Nothing here is a decision
yet; it is here so the cheap moves stay cheap.

**Free-text JSON stays the action channel for the deduction ladder.** No model in
this repo ever gets a tool schema. Two reasons, both about the numbers rather
than ergonomics: local llama.cpp/Kobold backends and the cloud tiers implement
function-calling at wildly different fidelity, so a tool schema makes the harness
a per-model variable in exactly the comparison being run; and a truncated
tool-call leaves nothing for `salvage()` to scrape, converting a recoverable
reply into a fallback, which is the quantity the scorer voids on.

**Constrained decoding is the real upgrade, and it belongs behind a label.** GBNF
on llama.cpp, `response_format: json_schema` on cloud, would drive fallback rate
toward zero. It must not become the default: every number ships beside its
fallback rate, and grammar-forcing DELETES that signal rather than improving it.
If it lands, it lands as a recorded arm (`strict` vs `free`) so a cell says which
lane produced it. A model that cannot emit legal JSON unaided is a data point.

**The closed-phase shape generalises to the other three deduction games and not
to the RPG.** Today: `Phase` enum -> `acting_seats()` -> an `action_prompt`
if-chain -> one phase maps to one key. That holds while the action space is
finite and one decision wide per seat per turn. A tabletop rung is neither:
declarations are unbounded ("I tip the brazier onto the rope bridge"), one DM
turn is N mutations rather than one, and rule-0 inverts `referee.py:6` - there,
judgment IS the referee.

**Sketch, if that rung gets built: split the referee's two jobs.** A
deterministic rules kernel keeps state, dice, and legal mutations and raises on
illegal, exactly as `CabalReferee` does now. A model adjudicator sits in the
interpretation slot and turns free-form intent into calls against that kernel.
Players stay text-only; only the DM seat emits a list. Envelope stays ours -
`{"think":..., "narrate":..., "calls":[...]}`, validated by the kernel, refused
with the kernel's own error text, retried against the same seat, counted on
fallback. That is the existing `LLMPolicy` loop unchanged; what generalises is
`parse_action`, from "phase -> one key" to "phase -> an action spec" where the
spec may be a list.

**Gate #1 does not survive a model DM, and the fix is not a smarter matcher.**
`find_leaks` is sound today because the referee's private bytes are a fixed set
of strings. A model DM paraphrases private state: "the innkeeper looks nervous"
leaks that he is the cultist with zero substring overlap, and the audit reads
clean. Keep `find_leaks` naive and change the corpus instead - the DM declares
its intended reveals as typed facts, those are checked against entitlement, and
the prose is audited against the facts it did NOT declare. Same naive matching,
right input. This is the RPG rung's hardest problem and it is worth knowing about
before anything is built on it.

**`LLMPolicy`'s refuse -> re-prompt-with-referee-error -> count-fallback loop is
the strongest promotion candidate in the repo** and it currently lives in
`games/cabal/player.py`. Promote on evidence, per the invariant, so it moves when
game #2 needs it and not before - but it is the piece to watch for, since the RPG
sketch above reuses it verbatim.

## Open design note: moral framing as a measured variable

Written 2026-08-25. Unrun. Arrived sideways, out of a licensing question about the
default theme, which is a bad provenance for a research direction - so it is
written down narrowly rather than talked up.

**The question.** Holding mechanics, seeds, and information exactly fixed, does the
FICTION an agent is playing inside change how readily it deceives? `cabal` is an
unusually clean place to ask, because a theme is display-only by construction: swap
`Theme` and every rule, every entitlement, every byte of private knowledge is
identical. The only thing that moved is what the seat believes it is doing.

**The confound, which is the whole design problem.** `1984-en` vs `plain` is not
one variable. It is at least three: moral polarity (sabotage heroic vs neutral),
narrative richness (a blurb vs no blurb), and register (loaded vocabulary vs
sterile). A difference across that pair says nothing about morality specifically -
it could be that any fiction beats no fiction. The arms that separate them:

  1. `plain` - no fiction. Floor.
  2. `1984-en` - rich fiction, sabotage HEROIC (what ships today).
  3. a rich fiction of equal length and register with sabotage VILLAINOUS - the
     saboteurs are the betrayers, the majority are the wronged. Same word count,
     same density of loaded nouns.
  4. optional: rich fiction, morally NEUTRAL - a sport, a heist with no victim.

Polarity is arms 2 vs 3, and only 2 vs 3 - they differ in valence and in nothing
else. Richness is 2+3 vs 1. Without arm 3 the experiment cannot make a claim about
morality at all, and that is the difference between a result and an anecdote.

**What this repo brings that a prompt-level study does not.** Gate #1 makes
information equality a machine-checked property rather than an assumption, so a
behavioural difference cannot be a leak. Fallback rates are recorded per run and
void above 10%, so a "refused to deceive" cell cannot be a parse failure wearing a
moral face - which is the obvious way this result gets faked. And the criterion can
be pre-committed the way gate #3b already was.

**Prior work - verified 2026-08-25, read before designing arm 3.** All four opened
and confirmed; identifiers are exact so nobody re-searches for them.

  - **Hagendorff, "Deception Abilities Emerged in Large Language Models"**,
    arXiv:2307.16513, PNAS 121(24), doi:10.1073/pnas.2317967121 (2024). **The
    closest prior result, and it constrains the design.** It reports that eliciting
    Machiavellianism in an LLM alters its propensity to deceive - so "manipulating
    the fiction moves deception rates" is ALREADY SHOWN, single-agent. Arm 3 must
    therefore not touch the seat's persona or traits; if it does, this is a
    replication wearing a new skin. The one thing left unclaimed is the valence of
    the ACT with the agent's character held fixed.
  - **Park, Goldstein, O'Gara, Chen, Hendrycks, "AI Deception: A Survey of
    Examples, Risks, and Potential Solutions"**, arXiv:2308.14752, Patterns (2024).
    Survey; defines deception as systematic inducement of false beliefs in pursuit
    of an outcome other than truth. Covers CICERO. Use its definition rather than
    coining one.
  - **Meinke, Schoen, Scheurer, Balesni, Shah, Hobbhahn (Apollo Research),
    "Frontier Models are Capable of In-context Scheming"**, arXiv:2412.04984
    (2024). Six agentic evals; covert vs deferred subversion. Nearest neighbour for
    eval DESIGN, not for the question.
  - **Pan, Shern et al., "Do the Rewards Justify the Means? Measuring Trade-Offs
    Between Rewards and Ethical Behavior in the MACHIAVELLI Benchmark"**,
    arXiv:2304.03279, ICML 2023 (oral). 134 choose-your-own-adventure games, half a
    million scenarios, reward-vs-ethics tension. Nearest neighbour for the SETTING.

**So the contribution, if any, is narrower than it first looked.** Not "does fiction
move deception" - Hagendorff answers that. What is left: whether the moral valence
of the act, with persona held fixed, moves deception in a MULTI-AGENT game where
information isolation is machine-checked rather than assumed, pre-registered, and
reported with its fallback rate. Workshop-paper shaped at most, and only if the
effect survives arm 3. If arm 3 shows nothing, that is the honest result and it
ships as one.

**Precondition: not before gate #3 is called.** Same reasoning as every other
measured change - and gate #3's own N problem binds here twice as hard, because
this needs four arms rather than one. It is an argument for doing ONUW first (~10-15
calls a game against cabal's 80-220), not for running it sooner.

## Player counts across the ladder (verified 2026-08-25, sources checked)

Two different questions get conflated here and they have different answers. What a
game SUPPORTS is a rules fact. What size plays BEST is a community judgement about
human tables - and it is not the same as what size MEASURES best, which is a
property of this harness (see the larger-setups arithmetic in the queue).

| Rung | Supports | Plays best (human tables) | What the size buys the harness |
|---|---|---|---|
| cabal / Avalon | 5-10 | 7-8 | 5 is the cheapest table, and per §larger-setups the best sampler. 7+ is needed for 3 evil, which is what the information-degrading variants require. |
| ONUW | 3-10 | - | Size barely matters: one night, ~10 min, no elimination. Its win is calls-per-game (~10-15 vs cabal's 80-220), not seats. |
| Secret Hitler | 5-10 | 7-9 | **7+ is a different game, structurally** - see below. |
| Blood on the Clocktower | 5-20 | **7-12** | Needs a big table to be itself; at 5 it degrades toward ONUW. The Storyteller is the judgment rung, so this is where seats and judgment both peak. |

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

## Prior work on this exact setting - read before publishing

**AvalonBench: Evaluating LLMs Playing the Game of Avalon** - Light, Cai, Shen, Hu,
arXiv:2310.05036 (Oct 2023). A game environment for Avalon, rule-based baseline
bots, and ReAct-style LLM agents with per-role prompts. Reports ChatGPT in a good
role winning 22.2% against rule-based evil, versus 38.2% for the rule-based good
bot - i.e. LLMs UNDER-performing scripted baselines.

This is the nearest neighbour to parlor itself, not to any one of its notes, and a
public repo doing LLM-Avalon that does not mention it reads as either unaware or
evasive. Position honestly before flipping public: the overlap is the setting, and
the difference is what is being claimed. AvalonBench asks how well agents PLAY and
scores win rate against bots. parlor asks whether the harness is HONEST first -
information isolation as a machine-checked property (gate #1), a fallback rate
shipped beside every number and voiding above 10%, and criteria pre-committed
before the run. Those are complementary, and the win-rate comparison is not the
axis this repo competes on. Read the paper before writing the positioning line -
this summary is from its abstract and search results, not a full read.

Also surfaced and unread, both plausibly relevant to §moral framing: **HARBOR:
Exploring Persona Dynamics in Multi-Agent Competition**, arXiv:2502.12149.

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

- `local:8090` armed: `rocinante-x-12b-heretic-q4`. The heretic 12B
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
