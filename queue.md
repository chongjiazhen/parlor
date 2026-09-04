# The queue - open work

Queue only. Done work leaves - **delete the row.** What stays is the ask, its
entry condition and what done looks like. What leaves goes by lifetime, and
**nothing is rewritten on the way out** - a moved paragraph goes verbatim under a
dated heading in `docs/open-arms.md` (the argument behind a row),
`docs/measurements.md` (a dated reading), `docs/decisions.md` (a settled call) or
`docs/slices.md` (a struck slice). The budget is bytes and the pre-commit gate
ratchets it - read it before writing a row, not by failing it:
`sh scripts/hygiene-check.sh --budget`.

**One exception: a finished slice is struck and annotated, never deleted**,
because live rows cite slices by name.

## Cold start

**First command of any session that thinks a run is live:**

```
grep -L 'PARLOR DONE' eval/records/*.log   # names every run still in flight
```

Narrow it to a campaign's own arms when you know them, and exclude the files that
never carry the marker - `hunt6[ab]`, not `hunt6*`, which also matches
`hunt6b-chain.log` and so reads "in flight" forever. **Never judge a run by a
process probe.** Most of what it names is a fossil: the marker landed in S4
(`core/runlog.py`), so every earlier log lacks it permanently. Read the answer
against `queue.local.md`'s launch record and treat a name it does not list as a
fossil rather than a run.

**No progress figure, ETA or log-tail path is recorded here** - a count about a
running job is stale the hour it is written, and an ETA in this block was wrong
twice on 2026-08-27. That class lives in `queue.local.md`, along with whether a
freeze binds right now; this file keeps terminal states and route decisions.

## What each rung owes

One debt per rung, and **this table is the only place that state lives** - a
second copy is the one that goes stale. `GLOSSARY.md` defines rung, arm and void.
**No reading is restated here**: they are `docs/measurements.md`, the calls are
`docs/decisions.md`.

| rung | engine | model in a seat | what it owes |
|---|---|---|---|
| **cabal** | done | yes | nothing runnable. Its GPU program stopped at gate #3b and its live arms re-homed to changeling, so what it holds is parked, not work: **over-sabotage (b), naming the partner, is measured to HURT** and is an arm of its own if ever tried (`docs/open-arms.md`); **6/7p is dealt and baselined**, and what is left is a model (`docs/measurements.md`) |
| **changeling** | done | yes - gate #3 HOLDS on BOTH decks (S5 five-seat, S19 six-seat waker) | the `waker` deck is read and its question ANSWERED: the waker seat's advantage does not clear zero. **Not shown, not no** - the deck hit the one-vote-per-game ceiling its criterion named, so settling it needs a NEW criterion, a longer arm or a deck seating two waker-class cards, never a re-read of these records. `kindred` deck B is FROZEN and unlaunched - its row below |
| **quorum** | done, and the live4 arm READ 2026-09-01 | **never** | nothing runnable. Both clauses INFORM over one fallback decision in 2582; read `docs/measurements.md` before citing either. Seeds 11200..11219 are spent alongside 5200..5599 / 7000..7399, so a fifth arm needs fresh ones and a criterion of its own. The repeat-claim void has still never fired |
| **belfry** | done, scoring lane, control instrument, sampled-player arm, S8 referee read, live2 READ | **never** | nothing runnable. The session-memory night arm RAN and is READ 2026-09-03 - COHERENT, NO RECALL, BELOW SUPPLIED - and what it left is an observation row below, not a run. S8b is DISTINGUISHABLE and live2's Clause A INFORMS; Clause B spans chance and no second arm chases it. **S29's central prediction is FALSIFIED**: that arm carries `recovered 27` over 2454 calls at 0.00% fallback, so the retry now has the live record S29 said no arm would produce - its refusal to buy one stands, its stated mechanism does not (`docs/decisions.md`) |
| **DURF** | done | yes, and gate #1 held under the topology edits | a term decision and two questions that are not code, all three in §The three DURF questions. The adjacency question is DECIDED, its edits APPLIED, its campaign LANDED |
| **adjudicator** | S8b read | referee only | held-out source accuracy clears its Wilson chance ceiling; bounded trace difference only |

**Do not mix cabal and changeling in one session.** Separate `RULES.md` files,
scorers and baselines - every number confusion in this file so far came from
carrying one game's intuition into the other's denominator.

## The three DURF questions that are still open

Named here, argued in `docs/open-arms.md`. None is code and none obliges a run.
**`hidden catch`** collides with ordinary searching prose and is deliberately
unfixed, because the edit voids its own read. **Movement is still unconstrained
by the exit graph** - adjacency is a RULES change and therefore a separate arm.
**The tell question is a separate instrument**, `py -3 -m eval.durf_reveal_order
<record>.json`, no GPU; reveal-ahead is a COUNT and must never be promoted into a
gate or into the quality rubric the rung still lacks.

## Session slices - what one `/new` should take

A slice is one session's worth, with an entry condition, ending in a thing that
exists. **Take exactly one.** Slice numbers are IDs, not positions, and are never
renumbered. **The live table is empty 2026-09-02** - every slice S1-S36 is struck and
annotated in `docs/slices.md`. The next slice is cut from the rows below when one
earns a session. The split that matters is GPU-bound versus attention-bound: a run
needs a launch and a log tail, not a session watching it, so a slice with a run in
it launches first and spends the wait on a CPU slice. **While a run is in
flight**, the standing menu is `docs/open-arms.md` §While the card is busy - an
instrument scored against records that already exist costs nothing and can
outrank the run it waits on.

**Direction, 2026-09-04: this queue is the INSTRUMENT, and the tables left it.**
The 09-03 re-call ranked table rows ahead of arms; that contest is over, because
the play lane, cross-session memory and machina moved to a private repo with its
own queue. **This is not tables being demoted** - the priority went with them,
and a reader finding only arm rows here should not read a change of mind. What
stays first is what the tables DEPEND on: the seam (`core/seam.py`, landed) and
the browser seat. Behind those, the frozen changeling arms, whose criteria and
card are unchanged. Argument: `docs/decisions.md` §Tables ahead of arms, with
its 2026-09-04 supersession note.

**Gate #3a is RETIRED and gate #3b is NOT SHOWN, and nothing below reopens
either.** Read `docs/gate3a-retired.md` before restarting any cabal run.

## The merge list

**One list, and rows do not carry branch names.** A branch cannot touch the
checkout the chain imports from, so "no changeling arm in flight" is met on a
branch and the freeze binds only the MERGE. Every row below is merge-ready on
its conflicts alone.

**The freeze is no longer prose - ask the command**, which intersects a branch's
diff with the entry module's import closure:
`py -3 scripts/merge-safety.py eval.run_changeling <branch>...`. **UNSAFE means
"would collide with a changeling arm", not "is frozen now", which is
`queue.local.md`** - no liveness argument; re-run 2026-09-04 with nothing in
flight, byte-identical answer. Nine of the ten branches collide; only belfry's
`fanout-heartbeat` was disjoint, since MERGED on that reading - an arm freezes
nearly everything, so "wait for the card" is normal, not cautious. A
changed `RULES.md` inside an imported package is reported as a runtime read.

No head sha: a copied sha is what goes stale, and a merge takes a name.

| branch | what it carries |
|---|---|
| `slice/changeling-source-rules` | the night rules - merge condition MET on the branch |
| `slice/changeling-notebook` | `--notebook` |
| `slice/fanout-simul` | `--turns simultaneous` - waits on source-rules by the order below, not on card |

**MERGED 2026-09-04, freeze lifted:** `fanout-print`, `fanout-wolf`,
`fanout-s27` + `-demo`, `fanout-replies` (carrying `fanout-neg`). Suite 1970.
Nearly every conflict was additive - `briefing=`, `turn_mode=`, `phrasing=`
reaching one constructor - and `docs/README.md` collided on all three until each
took HEAD, which is the criteria class block doing what it was built for.

**Order is forced by the controls:** every prompt arm pairs against S22's
`cl-rounds2.json`, so it must merge AND RUN before the source-rules merge
re-baselines the rung, or its pair is void. Which arm earns its ~7 h of card
first is the operator's ranking; the criteria are frozen and wait.

**GPU order and its 09-03 re-rank are `docs/decisions.md` §GPU order.** The
2026-09-04 card cleared that set: partner, briefing and both mixed arms are RUN
and READ (`docs/measurements.md`); briefing owes only its card. What is left
unrun is the ranking question, not a queue of merges.

**One conflict pair is still foreseen.** In `games/changeling/referee.py` simul
rewrites the turn machinery source-rules also moves: merge source-rules FIRST,
then rebase simul onto it and re-run its 20-seed byte-identity pins, which are
what would catch a silent drift. The `parse_action` pair is SPENT - replies
merged over s27 2026-09-04 and the golden sha256 passed by name; re-run it again
after any later merge touching that function.

## The queue

Open rows, unordered - the slice section above is what ranks them. **The reasoning
behind each is `docs/open-arms.md`; read the entry before taking the row**, and
the reference each names is indexed in `docs/README.md`. A second index here is
the one that goes stale.

- [ ] **The next criterion written must take its power from `eval.deal_census`.**
      The instrument landed 2026-09-04 and the gap it answers is real: the partner
      criterion took ~198 partner-eligible votes from seeds 5000..5199 and ran on
      17000..17199, which deals 168 - half-width 6.82 against a promised 5.9,
      learned after 5.2 h of card. The census deals nights only, no model, and is
      validated against play rather than itself: it reproduces 168 and 198 on the
      two blocks with records, and `cl-partner-random`'s recorded 1252 blind votes
      over 1000 deals, which pins all three blind filters at once. **Checked on
      unspent card:** `kindred` assumed ~269 blind votes from seeds 11/910000 and
      its own 14000 block deals 262, -2.6%, so its call stands and it needs no
      edit. Frozen criteria are not rewritten for this. Done when a criterion's
      Power section quotes a census of its OWN block, and a third statistic goes
      in `RULES` rather than a fork.
- [ ] **The folk-vs-greek vocabulary read needs a criterion and fresh seeds,
      ~10 h.** Decide first whether it is worth 10 h at all, given the skin pair
      showed NOT SHOWN on the name-form axis. Done when decided no (row deleted)
      or a criterion exists. Argument and the general lesson: `docs/open-arms.md`
      2026-09-03.
- [ ] **`slice/transport-retry` is not on the merge list, and its keying
      question is now DECIDED.** Four commits, 971 insertions, named nowhere in
      this file until the 2026-09-03 triage. The `core/` collision is settled:
      the branch's keying is KEPT over main's `ed6bf11`, argued in
      `docs/decisions.md` - it admits DURF's non-seat key where main's halfway
      widening does not, its sentinel cannot collide, and main's two extra rules
      are both silent skips where the branch's are loud. **Applying it is a
      REVERSAL of a landed mutation-checked guard**: `SecretKey` and `subject`
      go, and main's bare-seat-covers-every-axis tests are deleted rather than
      adapted. What is still open is the rest of the branch, each its own call:
      the shared transport rate budget, the `games/durf/facts.py` simplification
      that falls out of the keying, and a whole unlisted `games/bureau/` rung
      that no row has ever named and that must not ride in on a `core/` fix.
- [ ] **No criterion states the effect it EXPECTS, only the one it could see.**
      Every measured changeling pair is NOT SHOWN and each predicted it would be:
      resolution ~9-10 points at 200 games, observed prompt effects 1-3. The only
      arm that INFORMED swapped a whole policy. Argument, the real counter and
      the one cheap fix: `docs/open-arms.md` §Is the changeling arm program
      powered. Done when a criterion must name its expected effect before launch.
- [ ] **Five recipes DELETE a stale JSONL where the others refuse.**
      `belfry-live1`, `belfry-live2`, `durf-fixture`, `durf-session` and
      `quorum-live4` carry `if exist ... del` against the append hazard the
      writer now holds (`core/runlog.py claim_record`, 2026-09-03), so the
      line is both redundant and the only launcher line in the tree that
      destroys a record - and it deletes the JSONL while leaving the summary,
      which is the half-state the claim then refuses anyway. The other nine
      recipes `exit /b 1` instead. Done when the five refuse rather than
      delete. Not measured: whether any of the five was ever re-run onto its
      own path, which is what the `del` was written for.
- [ ] **`check-recipe-settings.py` is honest now; the pytest fixture is what is
      left.** Three vacuous passes and one false alarm came out on 2026-09-04, all
      the same disease - reading text that is not the arm. A valueless flag ate
      the next one, so `--seed` went unchecked. The multi-invocation shape
      compared a control arm against a criterion stating the model arm, printing
      a scope limit as a settings mismatch. Only `eval.run_*` lines are read now,
      so a `probe_tier` gate contributes nothing. And `rem` lines are prose:
      `belfry-live2.cmd`'s only `py -3 -m eval.` text is a commented scoring
      hint, off which the checker had reported AGREES - a recipe pinned to its
      criterion on the strength of a comment. **Re-swept all 13 pairable
      recipes: five agree, eight NOT CHECKED, zero false mismatches.** Done when
      it is a pytest fixture over them, which needs the `for %%T` loop shape read
      and a rule for which invocation of a multi-arm recipe a criterion means.
- [ ] **Find what writes a stale `.git/index.lock` in this repo.** 2026-08-28: a
      0-byte lock at 08:44, no `git.exe` running, blocked a commit 40 minutes
      later with the index intact. An unattended run that commits its own records
      would have died on it silently. Cheap probe: log the lock's ctime against
      the tool-call transcript next time. Done when the writer is named.
- [ ] **Gate #2 has a cheaper falsifiable design than waiting on gate #3** -
      `--arm llm` vs `--arm llm-good` on the same seeds, using arms that exist, and
      `rate_ok`'s 5% CI-floor bar is pre-declared nowhere. **The changeling twin is
      READ 2026-09-03 and INFORMS** (`docs/measurements.md`, criterion
      `docs/changeling-gate2-pair-criterion.md`): the live pack costs itself 17.9
      points against the same live village, and its named free read says the
      village deduces WORSE against an unreadable pack. **The mechanism is
      untested and is what survives as a row**: the arm moves the whole pack
      policy at once, so "speech is evidence" is a reading, not a finding, and
      separating speech from votes is a new pair with a criterion of its own. The
      cabal half is parked with cabal's GPU program.
- [ ] **Merge the changeling source rules.** Every blocker has CLEARED; what
      remains is the ranked arms first, then the merge, then re-measure the bar.
      Kindred re-bars after (`docs/decisions.md` 2026-09-02). Its one conflict is
      textual and resolved in advance - the resolution, verbatim, is
      `docs/open-arms.md` 2026-09-03.

Measured prompt arms - same seeds, one variable, reported beside both fallback
rates, landed between campaigns rather than into one. Every one is FROZEN and
unlaunched, and waits on the merge list above:

- [ ] **Negation pass over the model-facing strings.** Seventeen strings in two
      tables behind `--phrasing positive`, each default pinned to a hash computed
      before its table; one run against `cl-rounds2`, PRIMARY statistic the refusal
      rate. `docs/changeling-phrasing-criterion.md`, `eval.phrasing_pair_verdict`.
      **The replies branch supersedes the negation branch** - it adds the parser's
      complaints and pins the other four games through their own parse paths. Found
      in wiring it: `Phrasing.retry` had a golden hash and no consumer, so the
      positive arm was shipping the as-is retry sentence.
- [ ] **Does the standing frame belong in the PAYLOAD? `--briefing` (S21).**
      MERGED 2026-09-04; owes only the card. 553 bytes on a 1620-byte render, off
      by default and byte-identical off. **It renders inside `seat_lines`, never
      `preamble`**: measured, a leaky frame in the preamble escapes gate #1's
      per-seat scan and is caught from `seat_lines` - the rule for every
      standing-context arm. `docs/changeling-briefing-criterion.md`,
      `eval.briefing_pair_verdict`, one arm against `cl-rounds2`; recipe pinned to
      its criterion 2026-09-04.
- [ ] **A per-seat private notebook.** Promoted to `core/notebook.py` (two games
      needed it); `--notebook` on the changeling runner, notes stamped by round,
      off by default and byte-identical off. Criterion
      `docs/changeling-notebook-criterion.md`, one arm against `cl-rounds2.json`,
      recipe `eval/runs/changeling-notebook-arm.cmd <log>`, read
      `py -3 -m eval.notebook_pair_verdict`. Must RUN before the source-rules
      merge. Nothing quotable until it has.
- [ ] **Turn-taking is two arms, not one.** `--turns random-active` (S27) makes a
      round a budget of n turns, the floor drawn with replacement from the seed's
      own stream and the active seat offered an idle `listen`. `--turns
      simultaneous` withholds a round until it closes, then publishes it in seat
      order, so an agreement is one the seats reached apart - a different axis, not
      a stronger random-active. `docs/changeling-turns-criterion.md`,
      `eval.turns_pair_verdict`, TWO pairwise differences against `cl-rounds2`, no
      arm-vs-arm and no multiplicity correction, stated before the runs; the shared
      control means a void on `cl-rounds2` takes both. Round-1 agreement is a
      required free read, because the effect can only live there. Both are playable
      at the console on their demo branches. Cabal's own `--simultaneous`
      stays built and unmeasured - two rungs, two criteria, never one. Free with
      this row: **the salience line has no measured benefit anywhere and is a
      removal candidate**, on cabal, its own arm.
- [ ] **The pack side is where a changeling arm has room to move.** The closed
      mixed pair measures a live model 20.92 points WORSE than the hand-written
      pack it replaced, and par on the village (`docs/measurements.md`
      §changeling mixed cells). The control exists and the hole is stated, so an
      arm aimed at pack play has its comparison already recorded. **No gate #3
      claim rides on this** - the criterion named no bar and one may not be added
      now.
- [ ] **`briefing_text()` describes FIXED turns and no longer knows it.** S21 and
      S27 merged 2026-09-04 without meeting: the frame says "one turn each, in
      seat order", which under `--turns random-active` is false, and it rides in
      the payload gate #1 audits for every seat. Nothing recorded is affected -
      no frozen criterion sets both flags, checked - so this is latent, and it
      lands the moment an arm pairs them. Done when the frame reads the mode, or
      `--briefing` refuses a mode it cannot describe.
- [ ] **The tier census is NOT PAYABLE from any record, and `mixed-pack` is where
      that first cost something.** `HeuristicPolicy._vote` returns a seat, not the
      rung it fired on, and the vote row carries no tier - so the census must
      re-derive the ladder, a second copy of the policy. One field at the source
      fixes it. The cost is specific: seated by dawn truth against a RANDOM control
      every liar is a sleeper (tier 3, 0/111), and a live pack is the first place
      tier 3 can catch a TRUE wolf. Done when a vote row carries the tier that
      fired and `eval.mixed_verdict` reads it instead of declining.
- [ ] **Theme as an experimental variable, not a default to fix**
      (`docs/moral-framing.md` owns the arm ladder). **A blurb is a prompt** - the
      four English faces are frozen at 53 words and an edit orphans what was
      recorded against them; `1984-en` stays cabal's face on every committed
      transcript. The `greek`/`greek-named` pair LAUNCHED 2026-09-02 under
      `docs/changeling-skin-pair-criterion.md`; the other four stay unrun, and a
      werewolf-vocabulary face is BUILT and unrun on the merge list. **That face is
      the WHOLE answer to public legibility**, which is why a vanilla Werewolf RUNG
      is not worth building (`docs/open-arms.md`). Read the `1984-cn` arm
      FALLBACK-FIRST: non-English play surfaces as a fallback rate, not as worse
      deduction, so a CN arm voiding on the 10% rule is a finding.

Runs that are frozen and want card - and one that is already in the chain:

- [ ] **Run `kindred` deck B - FROZEN 2026-09-02, NEVER RUN.** `SETUP_7_KIN`
      with `require_seated_kin`, `--seats 7`. Bar measured (blind 25.39% over
      5376 random votes, `eval/records/kin-chance.json`) and the criterion is
      `docs/changeling-kindred-criterion.md`; recipe
      `eval/runs/changeling-kindred.cmd kin1 200 14000 qwen36-35b-a3b-iq3`, ~7 h.
      **Entry condition MET 2026-09-03** - nothing is in flight. It still runs
      after the source-rules merge and re-bars first (`docs/decisions.md`). A new
      deck re-baselines everything under it.
- [ ] **The own-transcript arm sits BELOW the withheld arm, and no criterion has
      a verdict for that.** READ 2026-09-03 (`docs/measurements.md`): COHERENT,
      NO RECALL, BELOW SUPPLIED, all three pre-committed and clean. The unheld
      part is the direction - handing the referee its own transcript looks worse
      than handing it nothing, on non-overlapping intervals - and the criterion
      defines only RECALLS / NO RECALL, so it is an observation, not a result.
      **The population explanation is now CLOSED, 2026-09-03**: the extra 59
      pairs are genuinely deeper (29.8% at night 4+ against 18.9%) and depth
      genuinely costs coherence, but standardising either direction moves -15.7pp
      to -14.8pp / -14.3pp, so the deficit is INSIDE the strata. What that read
      also spent is the non-overlap: at the largest matched stratum the intervals
      touch, so an arm is the honest next move and the cheap CPU route is done.
      Not measured: any mechanism.
- [ ] **Spike #2 heartbeat is MERGED 2026-09-04 and still UNMEASURED.**
      `--heartbeat` on belfry, off by default; `docs/faction-heartbeat.md` §Seated
      in belfry. Merged mid-run because it is the one branch disjoint from a
      changeling arm's import closure. What it owes is a criterion and card. The
      review's call to move `games/heartbeat/` out of `games/` names a different
      object. What seating found and the chain-slot correction are
      `docs/open-arms.md` 2026-09-03.

Human-seat play, triaged from one hand-played session 2026-08-29. Nothing here is
measured. Which of it may be handed to a worker is S12 and `docs/worklane.md`.
**Three rows left for the tables repo 2026-09-04** - the play lane, cross-session
gate #1 and machina. What remains is engine work a table depends on, not play.

- [ ] **"q36 is terse and robotic" is a claim about a model, and there is no
      bench.** RP tunes against `ablx` and q36, on ONE parlor-shaped question:
      whether fallback rate and deduction move together or apart. **Each tune is
      TWO arms** - gate #2 is unreadable without that tune's own gate #3 control.
      Candidates, the two corrections to them and the one candidate already
      measured: `docs/open-arms.md` §The RP-tune bench. **Entry condition: the
      source-rules MERGE, not an idle card** - every frozen arm pairs against a
      control recorded on q36, so a re-arm before those run voids them.
- [ ] **Changeling: respond to measured randomness.** Four levers and their order:
      `docs/open-arms.md` §"changeling feels random". Every rules or prompt change
      re-baselines this reading. The heuristic rung (`docs/scripted-rungs-cabal.md`
      §0) is MERGED 2026-09-03 and says what un-random looks like here; the mixed
      arms read it against a live seat and are the run this row now waits on.

- [ ] **Build the Paranoia-shaped rung, branding-free** - called 2026-09-03 and
      the pre-committed falsifier did NOT fire, `docs/decisions.md`. **The gate #1
      half is DONE, 2026-09-03**: `find_leaks` takes a `(seat, axis)` key, so one
      seat's several secrets are entitled separately, and seat-level entitlement
      still covers every axis (`core/test_observability.py`, both branches
      mutation-checked). The rung inherits it and owes no `core/` change; what was
      wrong is narrower than this row claimed, `docs/decisions.md`. Functional
      keys only. **What earns `games/` here is multi-axis entitlement, not the
      setting** - a rung, not a table someone sits at. Done when a seat holds four
      orthogonal secrets and the audit distinguishes them.

- [ ] **A browser front-end for a human seat.** A SECOND implementation of the
      `complete_meta` seam (`core/seam.py` §Transport), not a rewrite; v1 ships
      the gate-#1-audited string and nothing else. **The trap is rendering
      referee state into widgets** - a second channel the audit does not see.
      Per-connection channels also lift the one-seat cap a terminal forces, which
      needs a real seat-binding guard. Argument: `docs/open-arms.md` 2026-09-03.
- [ ] **Belfry's FULL script is the last reclassification, and it is UNBLOCKED
      2026-09-04.** `heartbeat` and `ensemble` left `games/` the same day, so
      `games/` and `core/registry.py` now name the same five. Belfry's own
      `RULES.md` says COMPACT already reaches every mechanic the rung exercises,
      so the extra roles buy recognition surface and prompt cost. It waited only
      on a live changeling arm touching `games/belfry/`; that arm is down. Done
      when the script is local-only or gone.
- [ ] **Obtain the paywalled theory chapter before publishing anything about gate
      #1** - the one result that could bound gate #1's shape, and two published
      hybrids are in the same debt (`docs/open-arms.md`). **No public claim about
      gate #1 until it is read**, and done when a copy is in hand.
- [ ] **The thesis moved on 2026-08-27** - `README.md` leads on the product claim,
      the off-repo positioning argument still leads on the research one. Reconcile
      them **in the off-repo file, not here**. Done when the two name the same
      leading framing; the failure to avoid is a stale copy that disagrees.
- [ ] **Code debt, item 3 only** - adopt a **termination-depth diagnostic**
      against the published threshold the off-repo ledger records, with that
      citation. Gated outside the tree; it held up nothing and still does not.
      **Entry condition: no arm in flight.**
