# The queue - open work

Queue only. Done work leaves - **delete the row.** What stays is the ask, its
entry condition and what done looks like; the argument behind a row lives in
`docs/open-arms.md`. The budget is bytes and the pre-commit gate ratchets it -
read it before writing a row, not by failing it:
`sh scripts/hygiene-check.sh --budget`.

**One exception, the slice table: a finished slice is struck through and
annotated, never deleted**, because live rows cite slices by name. The struck
rows live in `docs/slices.md`, out of the read a cold session pays for.

## Cold start

**First command of any session that thinks a run is live:**

```
grep -L 'PARLOR DONE' eval/records/*.log   # names every run still in flight
```

Narrow it to a campaign's own arms when you know them, and exclude the files
that never carry the marker - `hunt6[ab]`, not `hunt6*`, which also matches
`hunt6b-chain.log` and so reads "in flight" forever. **Never judge a run by a
process probe.** Most of what it names is a fossil and no count of them is worth
writing down: the marker landed in S4 (2026-08-27, `core/runlog.py`), so every
log written before it lacks it permanently - the `hunt20*`, `huntcloud*` and
unsuffixed `cl-powers-*` logs are all finished and all report as in flight. Read
the answer against `queue.local.md`'s launch record, and treat a name it does
not list as a pre-S4 fossil rather than a run.

**No progress figure, ETA or log-tail path is recorded here** - a count written
into a queue file about a running job is stale the hour it is written, and an ETA
in this block was wrong twice on 2026-08-27. That class lives in
`queue.local.md` (gitignored, box-local); this file keeps terminal states and
route decisions. Whether a freeze binds right now is its business too.

## What each rung owes

One debt per rung, and **this table is the only place that state lives** - a
second copy is the one that goes stale. The verdict table below is what has been
CALLED; this is what is left. `GLOSSARY.md` defines rung, arm and void.

| rung | engine | model in a seat | what it owes |
|---|---|---|---|
| **cabal** | done | yes | nothing runnable. Its GPU program stopped at gate #3b and its live arms re-homed to changeling, so the rows it still holds (evil over-sabotage, the 6/7p package) are parked on that, not on work |
| **changeling** | done | yes - gate #3 HOLDS (S5) | seat the expansion deck. `waker` is the run worth having: it is TOLD what every other seat must infer, and its deck seats it in 62% of games, so one run carries its own control |
| **quorum** | done | **never** | the live4 arm, and it is pure GPU. `docs/quorum-live4-criterion.md` §The arm, then `eval/quorum_live1_verdict.py`; live1-3 are superseded in writing, unrun. Seeds 11200..11219, and 5200..5599 / 7000..7399 are spent. **`--no-thinking` or the arm voids** - 12.90% fallback without it, 0.00% with |
| **belfry** | done, scoring lane, control instrument, and first sampled-player arm read | **never** | referee-seat spike remains. `docs/measurements.md` §belfry and `transcripts/belfry-live1.md` carry live1; it is not the 60-game/0.0 criterion arm |
| **DURF** | done | yes - gate #1 91/100, then 99/100 under the topology edits | a term decision and two questions that are not code, all three in §The three DURF questions. The adjacency question is DECIDED, its edits APPLIED, its campaign LANDED |
| **adjudicator** | not built | n/a | the spike itself (S8) - a model in the referee's seat for the discretionary choices only, which belfry has already isolated and logged |

## Gates already called

**Every called gate has left this file, and DURF now has one of its own.**

| verdict | where it lives | recompute |
|---|---|---|
| DURF gate #1 **HOLDS** - 2026-08-28, 91/100 sessions [83.77%, 95.19%]. Read under the PRE-TOPOLOGY fixture; two model-facing edits landed the same day | `docs/durf-rung.md` §The campaign | `py -3 -m eval.durf_camp1_verdict` |
| the same gate under those edits - 2026-08-28, `durf-camp2` 99/100 [94.55%, 99.82%], iron-door leaks 8 -> 0. An AUDIT: the criterion binds camp1 by name | `docs/durf-rung.md` §The paired arm | `py -3 -m eval.durf_camp1_verdict --record eval/records/durf-camp2.json` |
| its pre-committed criterion, unedited | `docs/durf-gate1-criterion.md` | - |
| changeling gate #3 **HOLDS** - 2026-08-28 (S5), 200 games | `games/changeling/RULES.md` §S2 read | `py -3 -m eval.s5_verdict` |
| its pre-committed criterion, as promised | `docs/changeling-gate3-criterion.md` | - |
| cabal gate #3b **NOT SHOWN** - 2026-08-27 (S6). cabal's GPU program stops | `docs/gate3b-verdict.md` | `py -3 -m eval.s6_verdict` |
| cabal gate #3a **RETIRED** - 2026-08-27 (S1), on arithmetic not budget | `docs/gate3a-retired.md` | `py -3 -m eval.gate3_arithmetic` |

## What a session must not re-derive

Each of these is settled, dated and written down somewhere else. The pointer is
the whole row; **do not restate the reasoning here** when you touch it.

- **The DURF fixture arms** - the void first read, the second arm, the
  temperature arm and what each established: `docs/durf-rung.md` §First run,
  §Second arm, §The temperature arm. Two operational facts that save a wasted
  run: the action channel was never what failed (0/60 fallbacks across all four
  runs), and **an adjudicator seat must not inherit a player seat's temperature**
  - pass `--temperature 0.0` on any later durf run. `Backend.temperature` is
  deliberately unchanged; it is shared with both games. Recipe:
  `eval/runs/durf-fixture.cmd`, an arm is under three minutes.
- **The DURF session engine, the campaign, the iron-door question and the
  adjacency question** - all four landed 2026-08-28 and all four are in
  `docs/durf-rung.md`. A term change has a price payable off records:
  `py -3 -m eval.durf_rescore <record>.json --add "..." --check`.
- **The powers re-run and both rule-error counts** - landed and closed
  2026-08-28. `games/changeling/RULES.md` §The public rules text and §The two
  rule-error counts. The fall in rule errors is NOT established; the powers text
  is still the right rules text, on its own argument.
- **Three changes that re-read an old record differently** - `fallback_rate`
  keeps its name, changeling's knowledge class is keyed on what the seat was
  TOLD, and `--out` is the summary path verbatim. `docs/measurements.md` §Three
  changes. Read it before quoting any pre-2026-08-28 number.
- **Three things recorded before they were measured** - the `--notebook` null,
  the strawman answer, and the cost of a neutral canonical key.
  `docs/decisions.md` §Three things recorded.
- **What the successors reached** - the capability tell reproduced elsewhere, the
  outside baseline that does not cover gate #3b, the fourth precedent for the
  `--notebook` null, and the one result not to quote against it.
  `docs/evidence-discipline.md` §What the successors reached.
- **The CPU lane of the wait is SPENT** - the mechanical solver, the corpus
  scorer and the heuristic rung are built, tested and measured.
  `docs/reference-policies.md` §Results and §The control ladder, including the
  supersession inside. None of it re-specifies a gate.
- **The 2026-08-27 prior-work sweep is CLOSED and its output is off-repo, on
  purpose** - it names third parties, quotes their prose and carries claims
  marked unread. `CLAUDE.local.md` has the path. Do not re-import it and do not
  re-run the search half. Reading debt blocks only PUBLISHING.
- **Ten theme arms across both games are built and NONE has been run.**

**Do not mix cabal and changeling in one session.** Separate `RULES.md` files,
separate scorers, separate baselines - every number confusion in this file so far
came from carrying one game's intuition into the other's denominator.

## The three DURF questions that are still open

- **`hidden catch`, camp1's term**, colliding with ordinary searching prose
  exactly as `loose flagstone` did - the model chose the words. Deliberately
  unfixed: scoring it as a hold gives 90/100 and moves no verdict, and the edit
  voids its own read. camp2's structural pair is CLOSED. **Deciding it does NOT
  oblige a re-run** - the 91/100 is a dated read under its own term set and stays
  quotable as that. Change the term, mark the read as scored under the old set,
  and run again only when something else is worth measuring with it.
- **Movement is deliberately still unconstrained by the exit graph.** `call_move`
  accepts any room, so the party can go R1 to R4 in one call. Making it respect
  adjacency is a RULES change - it moves what is legal and therefore what the
  fallback rate counts - and it would be a second variable in the same campaign.
  Separate arm.
- **The tell question is a SEPARATE instrument and must not be folded back in.**
  Substring matching cannot see a referee that names the object of its own
  undeclared secret without naming the secret (`docs/action-channel.md`).
  Relatedly, reveal-ahead is a COUNT, not a gate, and gate #1 must not be changed
  to catch it - declaring is the referee's authority, so the audit is correctly
  silent. Instrument `py -3 -m eval.durf_reveal_order <record>.json`, no GPU.
  There is still **no rubric for whether a refereed session was any GOOD**, and
  the reveal-ahead count must not be promoted into one.

## Session slices - what one `/new` should take

These are the units: each is one session's worth, has a stated entry condition,
and ends in a thing that exists. **Take exactly one.** They are ordered by what
unblocks what, so **the numbers are IDs, not positions**; live rows cite slices
by name, so do not renumber them. **Only live rows are below** - S1-S7 and
S9-S11, struck and annotated, are `docs/slices.md`.

The split that matters is GPU-bound versus attention-bound. A GPU run needs a
launch and a log tail, not a session watching it - so an S with a run in it
should launch first and spend the wait on a CPU slice.

| # | slice | entry condition | done when |
|---|---|---|---|
| ~~**S12**~~ | ~~**The delegation lane.**~~ **CLOSED 2026-08-30** - seven graded dispatches, 3 pass / 4 fail, one landed untouched. `docs/worklane.md` is the contract and carries what the batch returned; `.scratch/lane/README.md` is the index of what is still dispatchable and to whom. | - | **met** |
| **S8** | **Next rung or publish. TAKEN 2026-08-28 and NOT closed** - Belfry has the `Adjudicator` Protocol and four setup-choice seams; random control keeps its old seeded deal stream. The repaired discretion instrument uses held-out source classification and preserves every registration outcome, but no model adjudicator exists yet. The 6/7p package and publish option remain untouched. | S5 done, S1 called - **met** | a model adjudicator and measured, non-VOID discretion arm |

**Direction, called 2026-08-27 against the literature** (argument off-repo): gate
#1 measures parlor and is durable; gates #2 and #3 measure a MODEL and decay with
the next checkpoint. Nothing built so far de-risks the product claim, "a referee
that oversees without micromanaging" - so the next spike is the **adjudicator**
against 3-4 discretion-heavy characters, not a whole roster, and not Secret
Hitler, which is cabal's rung again. **While a run is in flight**, the standing
menu of what a session can still do is `docs/open-arms.md` §While the card is
busy; its reusable half is that an instrument scored against records that already
exist costs nothing and can outrank the run it waits on.

**S1 is called, and it freed half the queue.** S6 survives in a changed and
bounded form; S7 and the cloud arm are dead. Read `docs/gate3a-retired.md` before
restarting any cabal run. **Gate #3a is RETIRED and gate #3b is NOT SHOWN, and
nothing below reopens either** - what survives of both is re-homed to changeling,
where a paired 20-game arm is ~30 min against cabal's 13.2 h.

## The queue

Open rows, unordered - the slice table above is what ranks them. **The reasoning
behind each is `docs/open-arms.md`; read the entry before taking the row.**

Reference already written down, unmeasured unless it says otherwise:

- `docs/gate3a-retired.md` - the S1 verdict: the pricing table showing N was
  never the binding constraint, the off-team cell that cannot hold a sign across
  two draws, why 7p and 8p do not reopen it, **the paragraph gate #3a IS allowed
  to be reported as**, and the self-outing read.
- `docs/gate3b-verdict.md` - the S6 campaign, its pre-committed criterion
  verbatim, and the three draw-dependent items resolved off the same records.
- `docs/gate3-modelling-review.md` - the 2026-08-26 review that started it,
  closed on all six items. **Read its header before its body**: its line
  citations are stale and the gate it sharpened is the one S1 retired.
- `docs/scripted-rungs-cabal.md` - why the ladder climbs on hand rules rather
  than a learned policy, and the three rungs that follow. §0 is game-free and
  moves to `docs/control-ladder.md` when a second game builds a rung.
- `docs/content-packs.md` - the engine/content split for the endgame rung. Read
  it before laying out `games/<rung>/`, not after.
- `docs/preset-axes.md` - is every system a preset of flags over one engine? No,
  and why a DSL is the wrong reach here. Carries the boundary of the formal prior
  art (`arXiv:2205.00451`).
- `docs/player-counts.md` - why a bigger table does not fix the thin denominator,
  and the graded-taint fix that does.

belfry - state and pointers are §What each rung owes; these are its rows.
- [ ] **A model in the referee's seat, for the discretionary choices only.** The
      spike the ladder was pointed at, and belfry makes it small: the choices are
      already isolated in one place and logged, so the arm replaces the seeded
      draw and changes nothing about the audit. The measurement is whether a seat
      can tell which referee it faced.

Instrument and integrity:

- [ ] **Count self-outings by a CLAIM-shaped match, and re-score the records with
      it.** `outed_own_role_in_public` over-counts by ~3x and a functional-key
      match sees nothing; neither is a measurement. First person and present
      tense is the fix. **RE-BASELINES the 26/1580 count**, so it lands with the
      re-score, not on its own.
- [ ] **Find what writes a stale `.git/index.lock` in this repo.** 2026-08-28: a
      0-byte lock at 08:44, no `git.exe` running, blocked a commit 40 minutes
      later with the index intact. An unattended run that commits its own records
      would have died on it silently. Cheap probe: log the lock's ctime against
      the tool-call transcript next time.
- [ ] **Two behaviours the auditor prices, neither of them bugs** - a good seat
      approving a known-tainted team (7/76) and evil over-sabotaging. The
      consequence that matters is for gate #3a's metric, not for the seats.
- [ ] **Gate #2 has a cheaper falsifiable design than waiting on gate #3.**
      `--arm llm` vs `--arm llm-good` on the same seeds, using arms that already
      exist. Also: `rate_ok`'s 5% CI-floor bar is pre-declared nowhere.
- [ ] **Group-sequential design instead of a pre-committed fixed N.** Alpha
      spending, not "don't look". **It must be designed BEFORE the next
      campaign**, never retrofitted to S6's records - that would be the peeking
      it exists to prevent.
- [ ] **Stratify cloud results by served upstream instead of pooling them.**
       Pooling computes a Wilson interval over an ill-defined denominator. Cells
       accumulate ACROSS runs, which retires the "unlike the cloud's 30-upstream
       mix" asymmetry.
- [review-merge owed] **the \`unittest discover\` shortfall: a shipped doc currently claims a runner collects 850 tests when it collects 572; every later "all tests pass" claim inherits that**
- [review-merge owed] **Slot C: `--human random` allows varying human seat position** - adds `--human random` to draw seat from `--seed`, preventing always playing seat 0 and enabling full position sampling while preserving reproducibility

Measured prompt arms - each is same seeds, one variable, reported beside both
fallback rates, and landed between campaigns rather than into one:

- [ ] **Negation pass over the model-facing strings** (rule:
      `.claude/rules/model-facing-text.md`, path-scoped). Steering by prohibition
      makes the banned behaviour more available; three live prompts do it. The
      referee's hard refusals stay. **UNBLOCKED 2026-08-28.** Re-homed to
      changeling (S1).
- [ ] **Does the standing frame belong in the PAYLOAD? A `--briefing` arm.** The
      per-phase drip is deliberate and unplayable for a person, which is why the
      console got a `BRIEFING` outside the payload. Expect a
      capability-dependent sign. **ABSENCE is the novel arm** - every build read
      from source states full rules in the system prompt and none ablates that.
      **Done when** a paired arm exists.
- [ ] **A per-seat private notebook - BUILT 2026-08-26, UNMEASURED.**
      `--notebook`, off by default. Gate #1 holds by construction and the audit
      says so. Nothing about it is quotable until a paired arm exists.
- [ ] **Theme as an experimental variable, not a default to fix**
      (`docs/moral-framing.md`). Re-homed to changeling at 1/26th the GPU cost;
      `1984-en` stays cabal's face on every committed transcript. Arms built
      2026-08-27, unrun. **A blurb is a prompt** - all four English faces are
      frozen at 53 words and an edit orphans what has been recorded against them.
- [ ] **Candidate changeling skins - BUILT 2026-08-27, ALL UNRUN.** Design owns
      the arm ladder: `docs/moral-framing.md` §The changeling skin set. Open is
      which arm gets GPU first - the `greek`/`greek-named` pair is the cleanest
      single-variable manipulation in the repo.
- [ ] **The `1984-cn` language arm is less novel than it looked**, and prior work
      predicts its confound: non-English play surfaces here as a FALLBACK RATE,
      not as worse deduction. Read that arm fallback-first; a CN arm voiding on
      the 10% rule is a finding, not a failed run.
- [ ] **Mini-personas** as per-seat judgment biases, assigned from the seed and
      recorded so the scorer can split by persona. Trigger: only if a table that
      argues from evidence still votes identically. Re-homed to changeling (S1);
      its trigger was never met on cabal.

Rules and setup changes, each of which re-baselines what runs under it:

- [ ] **Evil over-sabotages** - 41% of sunk missions hand over the pair for free.
      **Two fixes, NOT one, and keeping them apart is the whole judgement:**
      (a) **disclose `need`** is a harness BUG - public rules information withheld
      from the ask - and lands unconditionally and alone; (b) **naming the partner**
      is a HINT and the one measurement on this exact move says it HURTS on q36.
      This is also a confound in gate #3a: expect discrimination to DROP, and
      that drop is a truer number.
- [ ] **Larger setups (6/7p) + the two information-degrading evils.** Package
      them - both only make sense at 3 evil seats. The roles landed 2026-08-27 as
      `LURKER` and `STRAY`; nothing deals them, so what is left is the setups and
      the measurement, which was always the cost. **Worth it for what they
      degrade about INFORMATION, never as a sampling fix** - a bigger table makes
      the thin denominator worse. Blocked only by cabal having no GPU program.
- [ ] **Seat the changeling expansion cards, which means picking a deck.**
      `kindred` and `waker` are implemented, skinned, resolved and tested;
      `SETUP_5` deals neither. Deck design is `games/changeling/RULES.md` §The
      decks that would seat them and is the source of record. **UNBLOCKED
      2026-08-28** (S10). **Route call: `waker` is the one worth a run** - it is
      told that the night moved it where every other seat must infer it, and its
      deck seats it in 62% of games, so one run carries its own control.
- [ ] **Ship a werewolf-vocabulary theme on changeling - and that is the WHOLE
      answer to public legibility.** Public-domain folk-game vocabulary (Mafia,
      Davidoff 1986), no branding question, on a rung already built. **This is
      why a vanilla Werewolf RUNG is not worth building** - same rung as cabal,
      plus elimination.

Human-seat play - triaged from one operator's hand-played session, 2026-08-29.
Nothing here is measured; the code claims are read from the files cited. Which
of them may be handed to a worker is S12 and `docs/worklane.md`.

- [ ] **"You went to sleep as the X" is rendered over the seat's POST-night
      belief, and for a thief or a waker that sentence is false.**
      `games/changeling/referee.py:239` prints `believes(seat)`, which
      `night.py` REPLACES on TAKE (:248) and WAKE (:270). Observed: a seat told it
      slept as the Werewolf and then handed "Seat 4 held the Thief" - it was the
      Thief, it robbed seat 4, and the two lines cannot be reconciled by any
      reader. **Not a leak** - every reveal was entitled, so the audit is right
      and only the English is wrong. It is still model-facing text on the rung
      whose gate #3 read is 200 games, so **it re-baselines S5** and lands alone,
      saying so. The fix separates deal from dawn rather than adding a fact.
- [ ] **An omniscient live view is a SECOND channel, not a wider first one.** It
      reads the referee (`holds`, the night log) and must never reach
      `prompt_for`, or gate #1's guarantee becomes a flag somebody can forget. The
      shape that cannot leak by construction: write the referee-side transcript
      incrementally and tail it from another terminal.
- [ ] **"q36 is terse and robotic" is a claim about a model, and there is no
      bench.** Candidates offered: RP-tuned Anubis-mini-8B, Rocinante-X-12B,
      Rocinante-XL-16B, Cydonia-24B against untuned gemma, qwen36-35b-a3b,
      qwen3.8-27B and its MTP build. **Read the direction note first** - gates #2
      and #3 measure a model and decay with the next checkpoint. It earns GPU on
      one parlor-shaped question only: whether fallback rate and deduction move
      together or apart across tunes, which is what an RP tune is supposed to buy.
      Serial local lane; `--no-thinking` is a property of the rung, not the bench.
- [ ] **Let a seat choose to speak rather than be scheduled to.** The same ask as
      the turn-taking row above - bidding, or random active-seat with an idle
      action - and it should be taken as ONE arm with it, not twice.
- [ ] **"changeling feels random" is now MEASURED, and the levers are the open
      half.** `py -3 -m eval.deduction` (2026-08-30, S5 records): mean per-game
      lift +0.169 [+0.085, +0.255], 39.5% of games vote BELOW their own chance
      baseline, and 44.3% of village wins (35/79) turn on one vote. Gate #3 and
      the complaint were never in conflict. Four levers and the order to try them:
      `docs/open-arms.md` §"changeling feels random". A changeling heuristic rung
      (`docs/scripted-rungs-cabal.md` §0) is still unbuilt and would say what
      un-random looks like here.

Spikes and unbuilt arms:

- [ ] **Spike #2: off-map faction heartbeat - SCOPED 2026-08-27,**
      `docs/faction-heartbeat.md`. **Not an alternative to the adjudicator spike;
      the small version of its hardest part.** Ticks are counted and the schedule
      derives from the game seed - a wall-clock actor voids the seed invariant.
      One new gate #1 failure and it is silent: audit a render against the
      entitlement snapshot taken when it was BUILT.
- [ ] **Seat the solver as an ARM** - `SolverPolicy.act(ref, seat)` does not
      exist. Gate #1-safe by construction. Note what it buys first: the hunt is
      mechanically flat, so a solver arm can only differ at the VOTE.
- [ ] **Seat the heuristic against the MODEL** - a table with heuristic and LLM
      seats, the arm that does not exist. Read the artifact warning in
      `docs/measurements.md` §Measured first: the all-heuristic arm's 99.5%
      hunter is a deterministic twin reading its own tell.
- [ ] **Gate #3 was never blocked on the table talk - that read was wrong.** It
      was model capability: identical prompts, -0.2% on the 12B against +66% on
      120B-class. `--simultaneous` is built and unmeasured; the salience line has
      no measured benefit anywhere and is a removal candidate.
- [ ] **Turn-taking has FOUR options, not two** - cabal's fixed order, the
      built-but-unmeasured `--simultaneous`, bidding for the right to speak, and
      random active-seat selection with a non-advancing idle action, which is the
      cheapest. Worth one paired arm if table talk ever needs to carry evidence.
- [ ] **Two shapes not to harden further before game #2** - cabal's `Phase` enum,
      the `action_prompt` if-chain, and `ACTION_KEYS`. `docs/action-channel.md`.

Publishing:

- [ ] **Obtain the paywalled theory chapter before publishing anything about gate
      #1.** The one result that could bound gate #1's shape; no free copy exists
      and the route is a request to its authors, drafted off-repo. **No public
      claim about gate #1 until it is read.** Two published hybrids are in the
      same debt, and both change what gate #3's number means to a reader.
- [ ] **The thesis moved on 2026-08-27** - `README.md` leads on the product
      claim, the off-repo positioning argument still leads on the research one.
      Reconcile them **in the off-repo file, not here**; the failure to avoid is
      a stale copy that disagrees with the README about which framing leads.
- [ ] **Code debt, item 3 only** - adopt a **termination-depth diagnostic**
      against the published threshold the off-repo ledger records, with that
      citation. Gated outside the tree; it held up nothing and still does not.
      **Entry condition: no arm in flight.**

## Where the rest of this file went

`queue.md` was 1200 lines on 2026-08-28 and 68 KB the same day, against its own
30 KB budget - most of it work that had already landed, or argument that is only
needed once a row is taken. The split is by lifetime, and **nothing was
rewritten**: every line is verbatim where it went.

- `docs/open-arms.md` - the reasoning behind the open rows above, and the
  standing menu for what a session can do while the card is busy.
- `docs/slices.md` - the closed slice ledger, S1-S7 and S9-S11.
- `docs/measurements.md` - §Measured, §Route, §Backend notes, and the three
  changes that re-read an old record differently.
- `docs/decisions.md` - settled calls, pre-committed criteria, and the three
  things recorded before they were measured.
- `docs/evidence-discipline.md` - what the successors reached.
- `docs/README.md` - the `docs/` index.
