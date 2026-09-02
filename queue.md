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
writing down: the marker landed in S4 (2026-08-27, `core/runlog.py`), so every log
written before it lacks it permanently. Read the answer against
`queue.local.md`'s launch record, which names each one, and treat a name it does
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
| **changeling** | done | yes - gate #3 HOLDS on BOTH decks (S5 five-seat, S19 six-seat waker) | the `waker` deck is seated, read, and its own question is ANSWERED - against the like-for-like `identity` set the waker seat's advantage does not clear zero (`+6.96% [-2.11%, 15.98%]`), so the deck shows no evidence that knowing your OWN card beats knowing a card. **Not shown, not no**: 122 waker votes is the one-vote-per-game ceiling the criterion named. Settling it needs a NEW criterion - a longer arm or a deck seating two waker-class cards - never a re-read of these records. `kindred` deck B is FROZEN and unlaunched - its row below |
| **quorum** | done, and the live4 arm READ 2026-09-01 | **never** | nothing runnable. Both clauses INFORM - proposer 74.04% [64.86%, 83.16%] vs an exact 25.00%, enactor 69.52% [64.29%, 75.53%] vs 33.33%, over one fallback decision in 2582; `docs/measurements.md`, read that before citing either. Seeds 11200..11219 now spent alongside 5200..5599 / 7000..7399, so a fifth arm needs fresh ones and a criterion of its own. The repeat-claim void has still never fired |
| **belfry** | done, scoring lane, control instrument, sampled-player arm, S8 referee read, and the live2 arm READ | **never** | **One arm frozen 2026-09-02, unlaunched: the session-memory night arm** (`docs/belfry-night-transcript-criterion.md`, recipe `eval/runs/belfry-night-transcript.cmd [after-log]`, seeds 15000..15999, ~1 h of card) - the referee's own transcript as its memory, the arm both night reads end by naming. Queues behind the changeling chain. S8b is DISTINGUISHABLE and live2's Clause A INFORMS at 20.34% [13.77%, 27.01%] over 1.28% fallback - both in `docs/measurements.md`, read that before citing either. Clause B spans chance and no second arm chases it. S29's adjudicator retry LANDED 2026-09-01 and did NOT re-baseline S8b - that record fell back 0/20, so it holds no call the retry could have changed, and S29 CLOSED the same day on the finding that no arm will carry `recovered > 0` (`docs/decisions.md`). The retry is verified by test, and the rung owes no run for it |
| **DURF** | done | yes - gate #1 91/100, then 99/100 under the topology edits | a term decision and two questions that are not code, all three in §The three DURF questions. The adjacency question is DECIDED, its edits APPLIED, its campaign LANDED |
| **adjudicator** | S8b read | referee only | 88.89% held-out source accuracy clears 70.97% Wilson chance ceiling; bounded trace difference only |

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
by name, so do not renumber them. **Only live rows are below**; every struck
and annotated slice is `docs/slices.md` - S1-S23, S29-S36 today - every slice is struck.

The split that matters is GPU-bound versus attention-bound. A GPU run needs a
launch and a log tail, not a session watching it - so an S with a run in it
should launch first and spend the wait on a CPU slice.

| # | slice | judgment | worker | entry condition | done when |
|---|---|---|---|---|---|
| - | **The table is empty 2026-09-02.** The next slice is cut from the rows below when one earns a session; the merge queue and the four frozen prompt arms are what a cold session picks up first. | | | | |

**Direction, called 2026-08-27 against the literature** (argument off-repo): gate
#1 measures parlor and is durable; gates #2 and #3 measure a MODEL and decay with
the next checkpoint. Nothing built so far de-risks the product claim, "a referee
that oversees without micromanaging" - so the next spike is the **adjudicator**
against 3-4 discretion-heavy characters, not a whole roster, and not Secret
Hitler, which is cabal's rung again. **Taken 2026-09-02 as belfry's first
PLAY-TIME discretion arm** - the false count a switched-off gauge is told, held
across nights - `docs/belfry-night-coherence-criterion.md`, recipe
`eval/runs/belfry-night.cmd`, READ 2026-09-02 **COHERENT**: the model held the
lie on 152/163 pairs (93.25%, Wilson floor 88.32%) against a control at 84/158
(53.16%, containing one half), 0.00% fallback on every side. Its follow-up with
`prior` withheld READ the same day **COHERENT and NEEDS MEMORY**: 94/122
(77.05%, Wilson [68.83%, 83.62%]) against a control at 81/159, below the
supplied read on non-overlapping intervals - `docs/measurements.md` §belfry
night coherence, both sections. **The third arm both end by naming is FROZEN**
- the belfry row above. Nothing on this axis is in flight.
**While a run is in flight**, the standing
menu of what a session can still do is `docs/open-arms.md` §While the card is
busy; its reusable half is that an instrument scored against records that already
exist costs nothing and can outrank the run it waits on.

**Gate #3a is RETIRED and gate #3b is NOT SHOWN, and nothing below reopens
either.** Read `docs/gate3a-retired.md` before restarting any cabal run.

## The queue

Open rows, unordered - the slice table above is what ranks them. **The reasoning
behind each is `docs/open-arms.md`; read the entry before taking the row.**

**Reference lives in `docs/README.md`**, which indexes every one of these and
is maintained as an index. A second list here is the one that goes stale.

Instrument and integrity: the 2026-09-01 review of `2d28e60..HEAD` is CLOSED -
all seven findings landed. Its rows are gone; git holds the record.

**Merge queue behind the chain read, 2026-09-02.** Worktrees unfreeze the code
half of this file: a branch cannot touch the checkout the chain imports from,
so the entry condition "no changeling arm in flight" is met on a branch and the
freeze binds only the MERGE. **One branch is free of the ordering below and can
merge first:** `slice/fanout-skip` (`bf88a1d`), one line, test-only - the S2
five-seat test called `load(S2)` past the `records_gate.demand` guard the rest
of its own file already used, so every fresh worktree failed on a record
`eval/records/` cannot carry. Nothing else in `eval/` or `games/` reads a record
unguarded. Branches waiting: `slice/changeling-source-rules`,
`slice/changeling-heuristic`, and the off-by-default arm branches below
(`slice/changeling-notebook`, `slice/fanout-*`). **Order is forced by the
controls:** every prompt arm pairs against S22's `cl-rounds2.json`, so it must
merge AND RUN before the source-rules merge re-baselines the rung, or its pair is
void. Which of those arms earns its ~7 h of card first is the operator's ranking;
the criteria are frozen and wait.


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
      **The changeling twin is FROZEN 2026-09-02**,
      `docs/changeling-gate2-pair-criterion.md` - `llm` vs `llm-village` on S22's
      seeds, one new arm (`eval/runs/changeling-gate2-arm.cmd`), unlaunched. The
      cabal half stays parked with cabal's GPU program.
- [ ] **Merge the changeling source rules when the campaign chain has read.**
      The cabal half (evil conference before the hunt) LANDED 2026-09-02,
      `7460953`, and re-baselines cabal (`docs/measurements.md`). The changeling
      half - a lone `pack` views one centre card at MEET, an `identity`-class
      reveal that moves the strata and the chance baseline; `spotter`/`swapper`/
      `switcher` declinable with `pass`, refused for `deceived` - is built on
      branch `slice/changeling-source-rules` and MUST NOT merge while the skin
      pair, S22 and the gate #2 arm are unread: their criteria froze under the
      current rules. Merging re-baselines the rung; the RULES.md notes flip then.
      **Merge condition MET on the branch, `888c163` 2026-09-02:** the control
      never declines - `random_chooser` skips `PASS`, the peek's slot stays
      random, the guard mutation-checked, `eval.strata` takes a chooser. Found
      in doing it: on `SETUP_5` a random arm now has NO S10 gap - every lone wolf
      peeks - so the blind stratum on the new baseline is smaller, not larger.
      What remains is the chain reading; then merge and re-measure the bar.
Measured prompt arms - each is same seeds, one variable, reported beside both
fallback rates, and landed between campaigns rather than into one:

- [ ] **Negation pass - FROZEN 2026-09-02 as a changeling arm, unlaunched, on
      `slice/fanout-neg` (`8abd79e`).** Nine strings in one table
      (`games/changeling/phrasing.py`) behind `--phrasing positive`; the `as-is`
      default is pinned to a hash computed before the table and mutation-checked.
      One new run against `cl-rounds2`, PRIMARY statistic the refusal rate;
      `docs/changeling-phrasing-criterion.md`, `eval.phrasing_pair_verdict`.
      Merge queue above. **The parser's complaints were left out and are now
      IN, `99bdc68` on `slice/fanout-replies`**: `core/replies.py` holds a
      `Complaints` table of eight, default pinned to a sha256 computed before
      the table, and the other four games are pinned through their own parse
      paths rather than by a default nobody exercises. Found in wiring it -
      `Phrasing.retry` had a golden hash and no consumer, so the positive arm
      was shipping the as-is retry sentence. Criterion amended before launch:
      seventeen strings, one variable, and it freezes at launch.
- [ ] **Does the standing frame belong in the PAYLOAD? `--briefing` - FROZEN
      2026-09-02 (S21), unlaunched, on `slice/fanout-s21` (`c298173`).** The
      frame is 553 bytes on a 1620-byte render, off by default and byte-identical
      off. **It renders inside `seat_lines`, never `preamble`**: measured, a
      leaky frame placed in the preamble escapes gate #1's per-seat scan 40/40
      (that scope is excluded on the invariance argument) and is caught 40/40
      from `seat_lines`. The rule for every standing-context arm from here.
      `docs/changeling-briefing-criterion.md`, `eval.briefing_pair_verdict`, one
      arm against `cl-rounds2`. Merge queue above. **Playable at the console on
      `slice/fanout-s21-demo` (`ffa90b2`)**, which branches from the arm: the
      same flag on `games/changeling/demo.py`, and the console's own furniture
      briefing drops when it is on, because `briefing_text()` already reaches a
      human seat inside its printed payload. Console-only - no model-facing
      byte moves, so the criterion is untouched and still binds the arm.
- [ ] **A per-seat private notebook - FROZEN 2026-09-02 as a changeling arm,
      unlaunched, on `slice/changeling-notebook` (`bb1e7c5`).** Promoted to
      `core/notebook.py` (two games needed it); `--notebook` on the changeling
      runner, notes stamped by round, off by default and byte-identical off.
      Criterion `docs/changeling-notebook-criterion.md`, one arm against
      `cl-rounds2.json`, recipe `eval/runs/changeling-notebook-arm.cmd <log>`,
      read `py -3 -m eval.notebook_pair_verdict`. Must RUN before the
      source-rules merge (merge queue above). Nothing quotable until it has.
- [ ] **Theme as an experimental variable, not a default to fix**
      (`docs/moral-framing.md`). Re-homed to changeling at 1/26th the GPU cost;
      `1984-en` stays cabal's face on every committed transcript. Arms built
      2026-08-27, unrun. **A blurb is a prompt** - all four English faces are
      frozen at 53 words and an edit orphans what has been recorded against them.
- [ ] **Candidate changeling skins - BUILT 2026-08-27, ALL UNRUN.** Design owns
      the arm ladder: `docs/moral-framing.md` §The changeling skin set. Open is
      which arm gets GPU first - the `greek`/`greek-named` pair is the cleanest
      single-variable manipulation in the repo. **That pair LAUNCHED 2026-09-02**
      under `docs/changeling-skin-pair-criterion.md`, recipe
      `eval/runs/changeling-skin-pair.cmd`, 200 games/arm at seeds 5000..5199;
      the other four faces stay unrun.
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
      (a) **disclose `need`** was a harness BUG and LANDED in `c43274e` - the
      MISSION ask states the threshold; this row kept saying it was open. What
      remains is (b) only: **naming the partner**
      is a HINT and the one measurement on this exact move says it HURTS on q36.
      This is also a confound in gate #3a: expect discrimination to DROP, and
      that drop is a truer number.
- [ ] **Larger setups (6/7p) + the two information-degrading evils.** Package
      them - both only make sense at 3 evil seats. The roles landed 2026-08-27 as
      `LURKER` and `STRAY`; nothing deals them, so what is left is the setups and
      the measurement, which was always the cost. **Worth it for what they
      degrade about INFORMATION, never as a sampling fix** - a bigger table makes
      the thin denominator worse. Blocked only by cabal having no GPU program.
- [ ] **Run `kindred` deck B - FROZEN 2026-09-02, NEVER RUN.** `SETUP_7_KIN`
      with `require_seated_kin`, `--seats 7`. Bar measured (blind 25.39% over
      5376 random votes, `eval/records/kin-chance.json`) and the criterion is
      `docs/changeling-kindred-criterion.md`; recipe
      `eval/runs/changeling-kindred.cmd kin1 200 14000 qwen36-35b-a3b-iq3`, ~7 h.
      Entry condition: no changeling arm in flight - it queues behind the chain
      in `queue.local.md`. A new deck re-baselines everything under it.
- [ ] **Run the belfry session-memory night arm - FROZEN 2026-09-02, NEVER RUN.**
      The withheld night ask carrying the referee's own transcript of the game,
      `prior` still dropped; criterion `docs/belfry-night-transcript-criterion.md`,
      recipe `eval/runs/belfry-night-transcript.cmd <last-chain-log>`, seeds
      15000..15999, ~1 h. Read `py -3 -m eval.belfry_night_verdict --criterion
      transcript`: RECALLS or NO RECALL against the withheld 94/122, and BELOW or
      AS GOOD AS the supplied 152/163, on intervals. Entry condition: the card -
      it refuses until the log it is handed carries a PARLOR done marker, so
      hand it the chain's last log via `eval/runs/chain-tail.cmd`.
- [ ] **The runner prints `SETUP_5`'s pre-`plurality-min2` pack reference
      (60.49%) beside every deck.** Seen on the 7-seat bar run. A print, not a
      score; both deck criteria already say not to read it. **FIXED on
      `slice/fanout-print` (`1d62b3c`)**: the figure prints only for the deck
      AND vote rule it was measured under, which no current run matches, so
      every report now prints a labelled absence. Merge after the chain reads.
- [ ] **Ship a werewolf-vocabulary theme on changeling - and that is the WHOLE
      answer to public legibility.** Public-domain folk-game vocabulary (Mafia,
      Davidoff 1986), no branding question, on a rung already built. **This is
      why a vanilla Werewolf RUNG is not worth building** - same rung as cabal,
      plus elimination. **BUILT on `slice/fanout-wolf` (`1d12c74`), unrun**:
      `--theme werewolf`, a second folk-family face with descriptive card names
      - one published game's coined role names were asked for and declined
      under the branding invariant. Merge after the chain reads.

Human-seat play - triaged from one operator's hand-played session, 2026-08-29.
Nothing here is measured; the code claims are read from the files cited. Which
of them may be handed to a worker is S12 and `docs/worklane.md`.

- [ ] **"q36 is terse and robotic" is a claim about a model, and there is no
      bench.** Candidates offered: RP-tuned Anubis-mini-8B, Rocinante-X-12B,
      Rocinante-XL-16B, Cydonia-24B against untuned gemma, qwen36-35b-a3b,
      qwen3.8-27B and its MTP build. **Read the direction note first** - gates #2
      and #3 measure a model and decay with the next checkpoint. It earns GPU on
      one parlor-shaped question only: whether fallback rate and deduction move
      together or apart across tunes, which is what an RP tune is supposed to buy.
      Serial local lane; `--no-thinking` is a property of the rung, not the bench.
- [ ] **Changeling: respond to measured randomness.** Four levers and their order:
      `docs/open-arms.md` §"changeling feels random". Every rules or prompt change
      re-baselines this reading. A changeling heuristic rung
      (`docs/scripted-rungs-cabal.md` §0) is still unbuilt and would say what
      un-random looks like here.

Spikes and unbuilt arms:

- [ ] **Spike #2: off-map faction heartbeat - BUILT (S24, `games/heartbeat/`),
      merged, never seated in a game.** `docs/faction-heartbeat.md`. **Not an
      alternative to the adjudicator spike; the small version of its hardest
      part.** Ticks are counted and the schedule derives from the game seed - a
      wall-clock actor voids the seed invariant. The silent gate #1 failure is
      audited against the entitlement snapshot taken when a render was BUILT.
- [ ] **Seat the heuristic against the MODEL - BUILT 2026-09-02, unlaunched, on
      `slice/changeling-mixed` (`b788121`)**, over the heuristic rung. Two arms,
      `mixed-village` and `mixed-pack`, the suffix naming the LIVE side;
      `docs/changeling-mixed-criterion.md`, recipe `eval/runs/changeling-mixed.cmd
      <predecessor-log>`. Two calls inside it: the control is `cl-heuristic.json`
      RESCORED over its own first 200 seeds, because the published 1000-game
      figure is a superset and not the pair; and the void bar reads the LIVE
      side's own fallback rate off the JSONL, because a run-level rate divides a
      live seat's refusals by seats that cannot refuse. Found in doing it - the
      no-backend guard tested `startswith("llm")`, which a `mixed-` arm passes,
      so 200 games would have scored the random policy. Reads against the
      artifact warning in `docs/measurements.md` §Measured first. Runs BEFORE the
      source-rules merge or its twin figure comes from a different game.
      **Operator call before launch:** arm 1 is `mixed-village` and arm 2 gates
      on its marker, so a card with time for one runs the weaker arm.
- [ ] **Gate #3 was never blocked on the table talk - that read was wrong.** It
      was model capability: identical prompts, -0.2% on the 12B against +66% on
      120B-class. `--simultaneous` is built and unmeasured; the salience line has
      no measured benefit anywhere and is a removal candidate.
- [ ] **Turn-taking - the random-active arm is FROZEN 2026-09-02 (S27),
      unlaunched, on `slice/fanout-s27` (`c2c68ad`).** `--turns random-active`:
      a round is a budget of n turns, the floor drawn with replacement from the
      seed's own stream, the active seat offered an idle `listen`. Two
      referee strings move, the opening event and the active ask - the event had
      to, or the referee would say "seat 0 first" of a random floor; the test
      whitelists exactly that line. `docs/changeling-turns-criterion.md`,
      `eval.turns_pair_verdict`, one arm against `cl-rounds2`. Merge queue above.
      **Playable at the console on `slice/fanout-s27-demo` (`5f57b77`)**, which
      branches from the arm: `--turns` on `demo.py` plus one console note. Found
      in doing it - no demo loop was needed, `play_game` already iterates
      `speaking_order()`, so a human seat is asked only on the clock and a bare
      `say` listens through the existing shorthand. Console furniture only.
      Still unmeasured: cabal's `--simultaneous` and bidding; if either is ever
      run on changeling it shares this criterion's shape, not a second one.
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
