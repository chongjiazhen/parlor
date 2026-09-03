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
| **belfry** | done, scoring lane, control instrument, sampled-player arm, S8 referee read, live2 READ | **never** | **one arm frozen 2026-09-02, unlaunched: the session-memory night arm** - its row below, queued behind the changeling chain. S8b is DISTINGUISHABLE and live2's Clause A INFORMS; Clause B spans chance and no second arm chases it. S29 CLOSED on the finding that no arm will carry `recovered > 0` (`docs/decisions.md`), so the rung owes no run for the adjudicator retry |
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
earns a session; a cold session picks up the merge list and the frozen prompt
arms first. The split that matters is GPU-bound versus attention-bound: a run
needs a launch and a log tail, not a session watching it, so a slice with a run in
it launches first and spends the wait on a CPU slice. **While a run is in
flight**, the standing menu is `docs/open-arms.md` §While the card is busy - an
instrument scored against records that already exist costs nothing and can
outrank the run it waits on.

**Direction, called 2026-08-27** and argued in `docs/open-arms.md`: gate #1
measures parlor and is durable, gates #2 and #3 measure a MODEL and decay with the
next checkpoint, and nothing built so far de-risks the product claim - so the next
spike is the **adjudicator** against 3-4 discretion-heavy characters. **Taken
2026-09-02 as belfry's first
PLAY-TIME discretion arm** - the false count a switched-off gauge is told, held
across nights. Both reads landed the same day, COHERENT supplied and COHERENT and
NEEDS MEMORY with `prior` withheld (`docs/measurements.md`). **The third arm both
reads end by naming is FROZEN** - the belfry row below.

**Gate #3a is RETIRED and gate #3b is NOT SHOWN, and nothing below reopens
either.** Read `docs/gate3a-retired.md` before restarting any cabal run.

## The merge list

**One list, and rows do not carry branch names.** A branch cannot touch the
checkout the chain imports from, so "no changeling arm in flight" is met on a
branch and the freeze binds only the MERGE. All of it waits on the chain reading.

No head sha: a copied sha is what goes stale, and a merge takes a name.

| branch | what it carries |
|---|---|
| `slice/changeling-source-rules` | the night rules - merge condition MET on the branch |
| `slice/changeling-heuristic` | the control ladder's middle rung |
| `slice/changeling-notebook` | `--notebook` |
| `slice/fanout-s21` + `slice/fanout-s21-demo` | `--briefing`, arm then console |
| `slice/fanout-s27` + `slice/fanout-s27-demo` | `--turns random-active`, arm then console |
| `slice/fanout-simul` | `--turns simultaneous`, sits over S27 |
| `slice/fanout-replies` | the parser's complaints - **supersedes `slice/fanout-neg`**, which it sits on |
| `slice/changeling-mixed` | the mixed cells, arm order swapped before launch |
| `slice/fanout-heartbeat` | belfry `--heartbeat` |
| `slice/fanout-print` | the stale pack reference prints a labelled absence |
| `slice/fanout-wolf` | `--theme werewolf` |

**Order is forced by the controls:** every prompt arm pairs against S22's
`cl-rounds2.json`, so it must merge AND RUN before the source-rules merge
re-baselines the rung, or its pair is void. Which arm earns its ~7 h of card
first is the operator's ranking; the criteria are frozen and wait.

**GPU order, decided 2026-09-02** (reasoning in `docs/decisions.md`):
mixed-pack (`slice/changeling-mixed`, ~2 h) first - cheapest, only arm that
shows the heuristic village's 77.36% against a random pack collapsing
against a live one. Then briefing (`slice/fanout-s21`, ~5 h) - tests
`AGENTS.md`'s own standing-context position; either sign changes a written
invariant. Then notebook (`slice/changeling-notebook`, ~5 h) - largest
prompt change, a prediction recorded in advance, second point on briefing's
axis. **Cut after #3**: run those three (~12 h), then merge source-rules -
owed a fresh baseline anyway, so deferring turn-taking (`slice/fanout-s27`,
`slice/fanout-simul` - shares s27's recipe, decide before launch whether it
rides alone) and phrasing (`slice/fanout-replies` - primary stat is refusal
rate, near 0%, lowest information per hour) costs a criterion rewrite each
against the post-merge baseline, not an extra control run. mixed-village
(arm 2 of mixed-pack's recipe, ~3 h) rides along unless cut. Kindred
re-bars after the merge - its bar does not depend on the control's rules,
a fresh one is minutes of CPU.

**Re-ranked 2026-09-03** (`docs/decisions.md`): the partner arm takes slot 3 and
notebook slips to the deferred group, so the pre-merge set is mixed-pack, briefing,
partner (~12 h). Partner's effect has been observed twice against an 8.7-point MDE
where notebook has a prediction and no observation, and it closes the honesty debt
of two unadjusted free reads published with no pre-committed test. It runs BEFORE
the merge, which would leave its numbers readable while changing what they
replicate.

**Two conflict pairs are foreseen, each with a required order.** In
`games/changeling/referee.py` simul rewrites the turn machinery source-rules also
moves: merge source-rules FIRST, then rebase simul onto it and re-run its 20-seed
byte-identity pins, which are what would catch a silent drift. In
`games/changeling/player.py` replies threads `complaints` through `parse_action`
where s27 and simul both edit the discussion path: re-run the replies golden
sha256 after any merge touching `parse_action`. The demo pair conflicts on one
argparse block and is trivial.

## The queue

Open rows, unordered - the slice section above is what ranks them. **The reasoning
behind each is `docs/open-arms.md`; read the entry before taking the row**, and
the reference each names is indexed in `docs/README.md`. A second index here is
the one that goes stale.

- [ ] **The skin pair's effect landed on the PACK, and its primary statistic
      could not see it.** Free read, `eval.changeling_audit`, both arms 2026-09-02:
      a pack seat voted the fellow it was told 49/198 = 24.75% under `greek`,
      27/198 = 13.64% under `greek-named`, diff -11.11% Newcombe [-18.75%,
      -3.35%]. `greek` sits ON its control's 25.69%; `greek-named` is below it,
      so proper names read as the pack PROTECTING its partner. The village-side
      shown-village count moved +2.70% [-7.31%, +12.65%] - nothing. The pair's
      primary is blind villager accuracy, a VILLAGE statistic, so the one thing
      that moved is structurally outside it. **Not promotable**: the criterion
      declares the audit a free read and forbids a bar after the fact, and this
      is one of ~6 such reads, so the interval is unadjusted. **The rounds pair
      moved the same statistic the same way** (2026-09-03, `docs/measurements.md`),
      so the criterion is WRITTEN - `docs/changeling-partner-criterion.md`, one arm
      on fresh seeds 17000.., ~5 h, primary the partner vote against its own
      control. Tool and recipe are WRITTEN; what it owes is the
      card - and it must run BEFORE the source-rules merge, which would leave
      every number readable while changing what is replicated. The axis question - which of name form or round count causes it - is
      deliberately NOT in it: four arms split 2-2 and no single variable separates
      them, so that is a later pair against this arm's record.
- [ ] **The same-seeds folk-vs-greek vocabulary read lapsed on 2026-09-03, and
      needs fresh seeds now.** Two criteria built the door and neither walked
      through it: the skin pair's §"What this does NOT compare" says a folk-vs-greek
      read "needs its own folk arm on these seeds under HEAD - a separate row, a
      separate criterion", and the rounds pair's §Settings put its two-round `folk`
      arm on seeds 5000..5199 for exactly that, with one condition - the vocabulary
      criterion "is written before that arm is read, never after." The greek arms
      were read 09-02 and `cl-rounds2` printed its own blind accuracy at 05:38 on
      09-03. No such criterion exists in `docs/`. **The seeds are spent**; the read
      is still worth having, but it costs a fresh folk arm and a fresh greek arm on
      new seeds, ~10 h, not the zero it was priced at. Cheaper alternative first:
      decide whether vocabulary is worth 10 h at all, given the skin pair showed
      NOT SHOWN on the name-form axis. The general lesson is the row that matters -
      **an arm that doubles as a future control has a criterion deadline, and the
      deadline is the moment the arm's own report prints.**
- [ ] **Five `.cmd` recipes stamp a WRONG time on every per-arm line.** Measured
      2026-09-03 and REPRODUCED in isolation the same day: inside a parenthesised
      block `%TIME%` prints the block's parse time on every iteration while
      `!TIME!` prints the real one. Hits `chain-after`,
      `changeling-{powers,rounds,skin}-pair`, `solver-control`; `chain-tail.cmd`
      and `changeling-partner-arm.cmd` set `enabledelayedexpansion` and are
      correct - the latter is the worked fix to copy. Lines outside the loop are
      fine, which is why it survived. The arm logs and JSON mtimes are the
      authority either way. One line per recipe, and it cannot be done while the
      chain holds those files.
- [ ] **Find what writes a stale `.git/index.lock` in this repo.** 2026-08-28: a
      0-byte lock at 08:44, no `git.exe` running, blocked a commit 40 minutes
      later with the index intact. An unattended run that commits its own records
      would have died on it silently. Cheap probe: log the lock's ctime against
      the tool-call transcript next time. Done when the writer is named.
- [ ] **Gate #2 has a cheaper falsifiable design than waiting on gate #3** -
      `--arm llm` vs `--arm llm-good` on the same seeds, using arms that exist, and
      `rate_ok`'s 5% CI-floor bar is pre-declared nowhere. **The changeling twin is
      FROZEN 2026-09-02**, `docs/changeling-gate2-pair-criterion.md` - `llm` vs
      `llm-village` on S22's seeds, one new arm
      (`eval/runs/changeling-gate2-arm.cmd`), LAUNCHED as the chain's last leg and
      unread. The cabal half is parked with cabal's GPU program.
- [ ] **Merge the changeling source rules when the campaign chain has read.**
      The cabal half, the evil conference before the hunt, LANDED 2026-09-02 and
      re-baselines cabal (`docs/measurements.md`). The changeling
      half - a lone `pack` views one centre card at MEET, an `identity`-class
      reveal that moves the strata and the chance baseline - MUST NOT merge while
      the gate #2 arm is unread: its criterion froze under the current rules. The
      skin pair and S22 are READ (`docs/measurements.md`). Merging re-baselines the rung and the RULES.md notes flip
      then. **Merge condition MET on the branch:** the control never declines and
      the guard is mutation-checked; what it does to the baseline is
      `docs/decisions.md`. What remains is the chain reading, then merge and
      re-measure the bar.

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
- [ ] **Does the standing frame belong in the PAYLOAD? `--briefing` (S21).** The
      frame is 553 bytes on a 1620-byte render, off by default and byte-identical
      off. **It renders inside `seat_lines`, never `preamble`**: measured, a leaky
      frame placed in the preamble escapes gate #1's per-seat scan and is caught
      from `seat_lines`. That is the rule for every standing-context arm.
      `docs/changeling-briefing-criterion.md`, `eval.briefing_pair_verdict`, one
      arm against `cl-rounds2`. Playable at the console on its demo branch, which
      moves no model-facing byte, so the criterion still binds.
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
- [ ] **Seat the heuristic against the MODEL.** Two arms over the heuristic rung,
      `mixed-pack` then `mixed-village`, the suffix naming the LIVE side;
      `docs/changeling-mixed-criterion.md`, recipe `eval/runs/changeling-mixed.cmd
      <predecessor-log>`. **`mixed-pack` runs first, swapped before launch** - it
      closes the artifact read and is the cheaper arm, so a card with time for one
      gets the informative one. The criterion carries the two calls inside it: a
      control rescored over its own first 200 seeds, and a void bar read off the
      LIVE side's own fallback rate rather than the run's. Found in doing it - the
      guard tested `startswith("llm")`, which a `mixed-` arm passes, so 200 games
      would have scored the random policy. Reads against the artifact warning in
      `docs/measurements.md`
      §Measured first. Runs BEFORE the source-rules merge or its twin figure comes
      from a different game.
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
      Entry condition: no changeling arm in flight - it queues behind the chain
      in `queue.local.md`. A new deck re-baselines everything under it.
- [ ] **Read the belfry session-memory night arm - LAUNCHED, it is the chain's
      last leg.** Not a row that wants card: `eval/runs/chain-tail.cmd` holds it
      as recipe 3 of 3 and it starts when the gate #2 arm's log carries its
      marker. The withheld night ask carrying the referee's own transcript,
      `prior` still dropped; criterion `docs/belfry-night-transcript-criterion.md`,
      seeds 15000..15999, ~1 h. Read `py -3 -m eval.belfry_night_verdict
      --criterion transcript`: RECALLS or NO RECALL against the withheld arm,
      BELOW or AS GOOD AS the supplied one, on intervals.
- [ ] **Spike #2 heartbeat is SEATED in belfry - `--heartbeat`, off by default,
      unmeasured.** No Phase, turn kind or ACTION_KEYS entry was needed: a tick is
      a night, taken at the top of `_begin_night`. What seating found, and how the
      audit's third scan is graded, is `docs/faction-heartbeat.md` §Seated in
      belfry, on the branch. Open, each its own row when taken: the rumour rule is
      LINEAR on a circular table, and at 5 seats most scheduled beats never fire.
      **Entry condition is the merge list, as first written.** The correction
      that stood here - that heartbeat is link 3 of the launched chain and runs
      ahead of the ranked arms - is FALSE, checked 2026-09-03 against
      `eval/runs/chain-tail.cmd`'s own argument list: the three legs are the
      rounds pair, the gate #2 arm and `belfry-night-transcript.cmd`, no recipe
      in the tree passes `--heartbeat`, and the flag is not on main. It was the
      belfry session-memory row's slot, read onto this one.

Human-seat play, triaged from one hand-played session 2026-08-29. Nothing here is
measured. Which of it may be handed to a worker is S12 and `docs/worklane.md`.

- [ ] **"q36 is terse and robotic" is a claim about a model, and there is no
      bench.** RP tunes against `ablx` and q36, on ONE parlor-shaped question:
      whether fallback rate and deduction move together or apart. **Each tune is
      TWO arms** - gate #2 is unreadable without that tune's own gate #3 control.
      Candidates, the two corrections to them and the one candidate already
      measured: `docs/open-arms.md` §The RP-tune bench. **Entry condition: the
      source-rules MERGE, not an idle card** - every frozen arm pairs against a
      control recorded on q36, so a re-arm before those run voids them.
- [ ] **Two pre-measurement positions in `docs/` were refuted by work built the
      same week, and neither was reconciled.** `docs/action-channel.md:82` on
      gate #1 and a model DM, against the DURF campaign that measured it;
      `docs/open-arms.md` §While the card is busy on Secret Hitler, against
      `games/quorum/RULES.md:11` which argues the opposite hours later. Both
      instances in full: `docs/open-arms.md` §Two pre-measurement positions. CPU,
      no card. Done when each doc states the position the measurement supports,
      the superseded reading kept and dated rather than deleted.

- [ ] **Changeling: respond to measured randomness.** Four levers and their order:
      `docs/open-arms.md` §"changeling feels random". Every rules or prompt change
      re-baselines this reading. The heuristic rung (`docs/scripted-rungs-cabal.md`
      §0) is BUILT and says what un-random looks like here; it waits on the merge
      list, and the mixed arms read it against a live seat.

- [ ] **Build the Paranoia-shaped rung, branding-free** - called 2026-09-03 and
      the pre-committed falsifier did NOT fire, `docs/decisions.md`. **The gate #1
      half is DONE, 2026-09-03**: `find_leaks` takes a `(seat, axis)` key, so one
      seat's several secrets are entitled separately, and seat-level entitlement
      still covers every axis (`core/test_observability.py`, both branches
      mutation-checked). The rung inherits it and owes no `core/` change. What was
      actually wrong is narrower than this row claimed - tuple keys already
      discriminated; what they lacked was the self-skip and the seat-level grant,
      whose absence reports the VIEWER'S OWN secrets at a game that adopts axes and
      pushes it back to the flat seat key where the false negative lives.
      Functional keys only - the setting, its role names and its text stay out of
      the tree. Done when a seat holds four orthogonal secrets and the audit
      distinguishes them.

- [ ] **The play lane, after session 0.** The draft is BUILT and RUN
      (`docs/measurements.md` 2026-09-03); what is left is the scene loop and the
      economy-compliance read, neither of which has a rubric yet. Still not
      sequenced against the Paranoia rung.
Publishing:

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
