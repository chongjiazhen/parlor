# Decisions already locked, and the criteria that were pre-committed

Moved out of `queue.md` 2026-08-28: settled, not queue, and verbatim except where
an entry says otherwise. Nothing here is "below" or "above" anything in the queue -
a pointer that survived the move as a deictic is a pointer at nothing.
Code invariants are NOT here - they are in `AGENTS.md`, which every harness loads,
and two copies of one rule is how the stale copy wins an argument.

## Decisions already locked

**Publish hygiene stopped being a round, 2026-08-28**, and the pass is not owed
again. What it decided is the project state; HOW the gate works is `AGENTS.md` and
the script's own header, and is deliberately not restated here.
- The mechanical half rides every commit, so nothing accrues between passes and
  the value is forward. It found zero violations in the tracked tree the day it
  landed, which is the point rather than a disappointment.
- The three route base URLs are environment variables with loopback defaults
  (`PARLOR_ENDPOINT_LOCAL` / `_CLEAN` / `_GRAY`), so a clone runs with nothing set
  and no box's topology is in the tree.

**Code invariants moved to `CLAUDE.md`** - it is always loaded, these are not,
and two copies of one rule is how the stale copy wins an argument. What stays
here is project state: the route calls and what a run measured. **Amended
2026-08-29: they moved again, to `AGENTS.md`, which `CLAUDE.md` imports** - a
`codex`/`qwen`/`pi` worker dispatched into this tree reads that file and never
opened the Claude one. The decision is unchanged; only the file holding it is.

- **A run writes its own terminal marker; a wrapper cannot be trusted to outlive
  it.** `core/runlog.py`, used by both eval drivers: `PARLOR DONE rc=N
  games=landed/requested elapsed=Ns`, written from a `finally` so it survives a
  crash, a `sys.exit` and a Ctrl-C. It contains `DONE rc=` so old greps still find
  it. **A log whose last line is a progress line is a killed run** - that is the
  whole point, and nothing writes the marker for a process killed outright. The
  `.cmd` echo stays for the one case python cannot cover: a crash before the driver
  runs at all.
- **The arm-level gate #3 is called against the MEASURED reference, and a run log
  calls nothing, 2026-09-03.** Two estimators of one quantity, both honest:
  `eval.run_changeling._chance` derives a per-vote chance from the run's own
  dawn-wolf mix, and `eval/gate3_bar.py` holds the same estimator frozen off an
  `--arm random` sweep at n=4000. The reference wins because
  `docs/changeling-gate3-criterion.md` names it and a criterion is not editable
  after launch. **What it cost to find:** on the skin pair's seed-identical deals
  the two read 36.47% and 35.84%, and `greek-named`'s 35.90% Wilson floor lands
  between them - HOLDS against the criterion, NOT SHOWN against the log, by 0.06
  points. **A run log now reports and does not call**, because it holds neither
  the bar nor the interval the gate is cut on - what it publishes is a bootstrap
  over games where the criterion's word is Wilson. It prints both bars against
  the floor and selects neither, which is what `eval.s5_verdict` already did.
  `blind_chance` stays a diagnostic and is not promotable - `s5_verdict` refuses
  it as choosing the statistic with the numbers in view. `s5_verdict`'s 35.95%
  and `waker_verdict`'s 30.14% are NOT this bar and keep their own homes: a
  criterion frozen against a figure keeps the figure it froze against.
- **A missing record is judged per RECORD, and the whole-rename case is a KNOWN
  loss, 2026-09-03.** `eval/records_gate.py` drew the line between an excused
  absence and a rotted citation on the DIRECTORY - empty means a slot, populated
  means the cited record should be here. That premise is false in exactly the tree
  the module exists for: a fresh worktree that runs one arm populates the
  directory with runs of its own, and measured 2026-09-02, three new control JSONs
  turned 8 skips into 6 failures and 3 errors. Reproduced 2026-09-03 in a
  throwaway worktree, same shape to the count. The line is now the demanded
  record's own run - one run writes `s2.json`, `s2.json.jsonl` and `s2.log`
  together, so a surviving sibling says the run was here and the artifact has been
  renamed or deleted. **What that costs, chosen rather than discovered: a run
  removed or renamed WHOLE now skips where the directory rule failed it**, because
  from inside a tree that never held the run the two are indistinguishable. The
  skip names the file in the suite output, and a test pins the downgrade so a
  later reader finds a decision instead of a hole. Restoring the old rule would
  re-break every worktree; the way to catch a whole rename is a citation that
  names two records, not a directory scan.
- **`refused` is the fallback census; `note` is cabal's notebook.** Both games
  record the refusal that produced a fallback on the decision itself, so a run's
  refusal diagnosis is a census in the JSONL rather than a sampled trace (8/game)
  and an end-of-run report that does not exist until the run ends. It holds the
  last ATTEMPT's complaint, not the "N attempts failed" summary. Two consequences
  for old records: pre-2026-08-27 JSONL has no `refused` at all, and changeling's
  records before that date carry the same string under `note`.
- **A leak instrument holds its own terms apart from every other fact's TEXT, not
  just from the other terms** (DURF, 2026-08-28). The kernel publishes a declared
  fact's text verbatim, so a term inside another fact's text charges a leak to a
  referee that obeyed the rules - the same false positive the pairwise term check
  refuses, by the route it cannot see. `games/durf/facts.check_facts` refuses it at
  load and the remedy is on the TERM: a text is what the party is told, and moving
  one moves a model-facing byte.
- **An execution a TRIGGER fired is not a pick, and is scored apart from the ones
  the table voted up** (belfry, 2026-08-29). It executes the NOMINATOR and fires
  only on a townsfolk one, so it is good with probability 1 while the chance rate
  prices it as a draw from the board. Pooled, that read as the random control
  missing chance by z = -3.60 and was recorded as an instrument failure; split, the
  voted half lands on chance everywhere and the trigger half is 0 of 354.
  `Execution.by_vote` carries it, for the same reason `was_alive` does - the board
  has moved by the time anybody scores it. **The general rule, which is the part
  that outlives belfry: a metric that pools an outcome the rules FORCED with an
  outcome a seat CHOSE is measuring two things, and the control is where that
  shows up.** `docs/measurements.md` §belfry has the numbers.
- Independent context = one model + per-seat private context slice, not N brains.
- Referee is deterministic code; LLM only for players (and, later, judgment-GMs).
- Cloud is fine for game-fiction secrets (not credentials); local for deception checks.
- **`--rounds 2` cleared the rejection deadlock.** 1 of 8 games ended `five_rejects`
  at two discussion rounds, against 2 of 2 at one round. One round gives a vote
  nothing to reason from; treat 2 as the floor for any live run.
- **Pin a model for attribution, use `auto` for capacity - and record the served
  upstream either way.** The gateway fails over across its keys, but a pinned id can
  only hop between keys for providers serving that exact id, so a cooled provider
  returns an instant 429 with no hop available. `auto` has the whole catalog and
  keeps answering. The response body's top-level `model` is the ONLY thing that
  says who answered; `Backend.complete_meta` returns it and the report prints the
  mix, so an `auto` run is honest about being several models averaged.


## This directory stays flat - moved from `docs/README.md` 2026-09-02

Nothing here is broken by a flat namespace. **The defects this layout has actually
produced were stale claims and a partly-true index, which folders do not fix** -
measured twice on 2026-09-02, when the index still said 23 files against 34 on disk
and named a slice range six slices out of date.

The split worth making, if one is, is the two classes with OPPOSITE maintenance
rules: docs that must track the code (`action-channel`, `content-packs`,
`model-facing-text`, `evidence-discipline`, `preset-axes`, `information-model`)
against dated records that must never be edited (every criterion and verdict,
`measurements`, `slices`).

Four triggers, any one of which flips the answer. The first is checked by
`scripts/hygiene-check.sh` as an advisory; the rest are judgement.

1. `docs/README.md` passes **150 lines**, at which point the index that stands in
   for folders is skimmed rather than used. **FIRED 2026-09-02 at 159 lines**, and
   answered by subtraction rather than by folders - this section is most of what
   came out, and it was never index material. That answer is available once. A
   second firing on live entries is the trigger doing its job.
2. A doc has **two plausible homes** and the answer matters - i.e. it is cited from
   two different reader contexts.
3. A **second contributor**, or external readers after publishing. Folders are a
   coordination tool; a single author with `AGENTS.md` as the map does not need
   them, and someone who cannot ask does.
4. **~40 files**, as a crude backstop on scanning a flat directory. **34 on
   2026-09-02**, so this one is closer than the prose suggested when it was written
   against 23.

**Both numeric triggers FIRED 2026-09-04, and the answer is now folders.** The
line trigger fired a second time, at 203 lines, on live entries - which is the
firing this section pre-committed to answer with folders rather than with another
subtraction. The file backstop fired the same day at 49 tracked files. Two things
were done instead of the split, and neither substitutes for it: the per-criterion
run status came out, six of the ten such claims having been measured stale
against `docs/measurements.md`, and the 23 criteria collapsed to one class block
so that adding a criterion no longer edits the index - which was the mechanism
behind this file colliding on seven of nine open branches. That took it to under
150 without folders.

**The split is deferred on SEQUENCING, not on merit.** Moving criteria into a
records directory while nine unmerged branches each add one at the flat path
lands their files in the old location silently on merge, which is a worse defect
than the length was. Do it once the merge list drains.

## Pre-committed criteria - all applied, all moved out

None is edited to agree with its outcome; that is the whole value of a
pre-commitment, and clause-by-clause outcomes belong in the verdict rather than
back in the promise. **DURF gate #1's applied cleanly 2026-08-28** -
`docs/durf-gate1-criterion.md`, outcome in `docs/durf-rung.md` §The campaign.
Every clause held as written and none needed smoothing, helped by its verdict
being arithmetic (`eval/durf_camp1_verdict.py`) written mid-run.

- **changeling gate #3**, written 2026-08-28 before S2 -
  `docs/changeling-gate3-criterion.md`, applied in `games/changeling/RULES.md`
  §S2 read. Two clauses did not apply cleanly and are recorded rather than smoothed.
- **cabal gate #3b**, written 2026-08-27 before S6 - reproduced verbatim inside
  `docs/gate3b-verdict.md`, beside what each clause returned.
- **The 2026-08-25 hunt run**, the first of them - superseded by S6's, which is the
  same statistic computed the honest way. Its one durable clause outlived it and is
  a live row in `queue.md`: if the hunter lands marginal, **respecify the metric
  rather than buying games**, because gate #3 is bottlenecked on its lowest-power
  half.
- The discipline itself, the `hunt20b` error it exists to refuse, and why pooling
  runs after the fact is the same move as peeking:
  `docs/evidence-discipline.md` §Pre-committing a statistic.


## Three things recorded before they were measured - moved from the queue 2026-08-28

Verbatim from `queue.md`. Pre-registered so that none of them reads as a
surprise later; none has been run.

**Three things to record before they are measured**, so none reads as a surprise
later:
- **`--notebook` should show no gain.** Three independent 2026 results on three
  different games report that reasoning and memory scaffolds do not deliver what
  they are assumed to; `--notebook` is one such scaffold. A null is the expected
  result, not a failed run.
- **The strawman answer is a scaffolding-ladder arm, not an argument.** parlor's
  bare seats are weaker PLAYERS than a purpose-built search-and-belief agent, and
  no framing changes that. Same referee, three rungs - bare prompt, prompt plus a
  carried belief vector, then determinized rollouts - reported as parlor's own
  curve. **Do not run a head-to-head against someone else's harness**: the ones
  surveyed are variously unlicensed, dependency-rotted or pinned to retired
  models, and a head-to-head then measures their rot rather than either player.
- **A neutral canonical key can mislead a model about STATE, and that is the cost
  side of the branding-free invariant.** Read outside this repo, not measured
  here, and no number attached to it: seats reading a state key by its everyday
  sense inferred the wrong thing about the game from it, and renaming that state
  fixed the reading; separately, an evocative role name drew threat assessment out
  of proportion to what the role mechanically did. Both cut the same way for
  parlor - branding-free keys buy the second effect and can lose the first. So a
  key that names a STATE rather than a role is a prompt variable, and renaming one
  is a MEASURED change on the same terms as a theme change, not a tidy-up. The
  invariant stands; what is new is that it has a cost worth watching for.


## Gates already called - moved from the queue 2026-09-01

Verbatim from `queue.md`. Every one is CALLED, so none of it can still
change, which is what disqualified it from a queue. The recompute column is
the point: a verdict nobody can re-derive is a number, not a result.

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


## What a session must not re-derive - moved from the queue 2026-09-01

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

## `eval/discretion_number.py` is DELETED, 2026-09-01 - S28 closed

Deleted with `eval/test_discretion_number.py`. Both defects were re-confirmed
against the files on the day, not inherited from the queue's diagnosis:

- **Its two arms ran different deals.** Arm A took even seeds and arm B odd
  (`base_seed + i*2` / `+ i*2 + 1`), so the classifier separated them on deal
  composition as well as on adjudicator behaviour. That is the confound the
  whole instrument existed to avoid, and it inflated the one number the module
  published. It bit hardest where the tests looked greenest: a FIXED adjudicator
  picks `spare_roles[0]` / `good_seats[0]`, so a different deal hands it a
  different menu, and `test_discretion_number_random_vs_fixed` cleared its 0.7
  bar partly on the seeds. `test_same_adjudicator_scores_at_chance` could not
  catch it - two random arms are confounded identically, so it read 0.5 and
  passed while the confound was live.
- **Its `__main__` crashed.** `FixedAdjudicator` returned role-name STRINGS where
  `deal()` reads `.key` (`games/belfry/state.py:379`), so the module's own
  worked example died `AttributeError` after printing one line.

**Why not fix it.** `eval/belfry_adjudicator_verdict.py` already answers the same
question correctly and is the instrument behind a published number: it pairs the
arms on IDENTICAL seeds, drops the unpaired ones, and reduces each trace to
`(key, option_count, selected_index)` so neither the deal nor the label can reach
the classifier. Fixing the seeding here would have converged on that design and
left two instruments answering one question, which is how a stale second copy
wins an argument later. The delete is recoverable from history; nothing in the
tree imported the module, and `docs/` never cited its number.

## No arm will produce `recovered > 0` - S29 closed 2026-09-01T15:44:11+00:00, FALSIFIED 2026-09-03

The belfry adjudicator retry landed earlier the same day: `ModelAdjudicator` carries
the seats' `retries=2` and doubling backoff, `ChoiceEvent.recovered` is set from a
RULES refusal that later answered, and the paired verdict prints the recovered rate
beside the fallback rate. Both were mutation-checked. What is recorded here is the
other half of the slice's done-when: **no arm this repo intends to run will produce a
record carrying `recovered > 0`**, so the retry is verified by test rather than by a
live record, and S29 closes on that rather than staying open against evidence nobody
is going to buy.

**The adjudicator's twenty calls are twenty setup choices, not twenty turns.** Under
`docs/belfry-adjudicator-v2-criterion.md` the only live discretion is the diviner's
herring registration - which good seat reads as the demon - taken once at setup,
uniform over good seats. Twenty of the frozen pair's sixty games seat a diviner, so
the denominator is 20 choice events and 40 no-event rows.

**Recovery needs a refusal to recover from, and neither arm has one available.**

- **v2 (S8b) fell back 0/20.** Every first ask returned a legal seat off the offered
  menu, so the retry loop never entered a second attempt. The opening ask is
  byte-identical pre- and post-retry by design and by test, and the seeded menu rng
  is drawn only on a fallback. Re-read fresh on the day: fallback `0/20 = 0.00%`,
  recovered `0/20 = 0.00%`, source accuracy 88.89% unchanged, exit 0.
- **v1 fell back 12/20 and is void at 60%.** It also re-reads at recovered
  `0/20 = 0.00%`, exit 2 - and that zero is structural, not a finding. **`recovered`
  is a PLAY-TIME field**: `ModelAdjudicator.choose` sets it from `rule_refusals > 0`
  inside the attempt loop, and the record stores the resulting event, not the attempt
  history behind it. No re-score of an existing record can recover a fumble that was
  never re-asked, because at the time those twelve calls were made there was no
  second ask to make.

So the only record that could carry the field is a fresh arm run at a fallback rate
high enough to fumble - which is a void record by construction the moment it
succeeds, bought with GPU hours, to demonstrate an instrument the unit tests already
demonstrate. That trade is not worth taking, and refusing it is the decision.

**What would reopen this**, and neither is scheduled: a belfry arm on an upstream
whose reply shape is not the one the v2 normalization already handles, run for its
own sake rather than to exercise the retry; or a future rung whose adjudicator asks a
question wide enough that a legal first answer stops being the common case. If either
lands, the field is already instrumented and the verdict already prints it - that is
what S29's code half bought, and it is the durable half.

**FALSIFIED 2026-09-03, and the reasoning above is kept because the conclusion
survives it.** The belfry own-transcript arm produced `recovered 27` over 2454
adjudicator calls in 27 distinct games - verified in the raw
`belfry-night-transcript-model.json.jsonl`, not off the verdict line. So a record
carrying `recovered > 0` exists, and the retry is now verified by a live record
as well as by test.

**Both halves of the mechanism above are wrong, and that is the correction worth
keeping.** This section reasoned that recovery needs a high fallback rate to
fumble, so the only record that could carry the field would be "a void record by
construction the moment it succeeds". The arm that produced 27 recoveries has
**0.00% fallback**. `recovered` is set from a RULES refusal that later answered,
which is orthogonal to falling back: a refusal that recovers never becomes a
fallback, so the two rates move independently and a clean arm can carry a large
recovered count. The real reason the earlier arms read zero is the denominator -
twenty setup choices each, against this arm's 2454 play-time calls - and the
section generalised from that narrow surface to "no arm this repo intends to
run".

**What still stands: refusing to buy an arm for the demonstration.** That trade
was correctly declined; the demonstration arrived free, from an arm run for its
own reasons, which is the second of the two reopening conditions this section
named. Nothing here asks for card.

**S23's entry condition is amended in the same close.** It read "a belfry record whose
adjudicator retried", which this decision makes unbuyable. The condition that was
actually meant is the one its own reasoning names - a quality metric read over a 60%
fallback rate measures the fallback - so it is now a belfry adjudicator record under
the 10% void bar with every scored call the model's. The v2 pair MEETS that today at
0/20 fallback and 20 paired legal traces, so S23 is unblocked on evidence, not by
lowering a bar.

## Belfry's setup discretion has no quality axis, so S23 grades steerability

Called 2026-09-01, writing `docs/belfry-discretion-quality-criterion.md`. S23 asked
for a narrow gradable quality question about referee discretion. There is not one on
this rung, and the criterion says so in its own opening rather than burying it.

**The board is the argument.** `grim.herring` has exactly one reader,
`Grimoire.registers_demon`, which applies it only when an asker is named - and
`night.divine` is the only caller that names one, so the duelist's day power cannot
be fooled by it. Compact five seats deal no outsiders, so the menu is the three
townsfolk, all alive, one of them the diviner itself. Nothing in the board makes one
of the three a better place for a read only the diviner will see, whose bite depends
on picks that seat has not made yet.

Two things follow, and both are decisions rather than observations:

- **A rubric over those options would report S8b's finding again.** The choices are
  exchangeable, so any above-chance rubric score is the seat-index prior the S8b read
  already established as DISTINGUISHABLE - published a second time wearing the word
  quality.
- **Inventing a taste ground truth IS the general-referee claim S23 forbade.** Deciding
  which placement a referee ought to prefer, then scoring a model against it, publishes
  this repo's opinion about refereeing as if it were a measurement.

**What is graded instead:** given the board and one stated placement rule, does the
discretion FOLLOW the rule? Exact ground truth, chance baseline of 1/3 that needs no
taste, and it is the half of "a referee that oversees without micromanaging" a run can
buy - a referee whose discretion cannot be governed by a stated policy oversees
nothing. The rule's CONTENT is a probe and the criterion refuses to defend it as good
refereeing; its only job is that it cannot be applied without reading the board.

**The menu is offered in a seeded order, and that is a control, not a variable.** S8b
showed this model's blind choices carry a position or seat-index prior. Against a
sorted menu such a prior can score against a rule it never read; shuffled, any fixed
position strategy sits at exactly 1/3. Mutation-checked - sorting the menu turns the
position-prior fixture from NOT SHOWN into STEERED. The cost is that the steered arm is
NOT a one-variable delta from S8b, so it is not read against S8b: it is read against
its own chance baseline, with S8b's blind 0/20 quoted only as the cost-of-steering line.


## 2026-09-02 - moved from queue.md

Found in building the changeling source rules on `slice/changeling-source-rules`
and struck from the queue row in the cull of the same day, because it is a fact
about the new baseline rather than an ask:

- **On `SETUP_5` a random arm under the new night rules has NO S10 gap** - every
  lone wolf peeks - so the blind stratum on the re-baselined chance floor is
  SMALLER, not larger. A scorer expecting the old stratum size would read the
  first post-merge control as short.


## GPU order for the frozen changeling arms, 2026-09-02

Six frozen rows hold seven unlaunched changeling arms, every one pairing against
S22's `cl-rounds2.json`, so every one must merge and RUN before the source-rules
merge re-baselines the rung. Running all seven first costs ~30 h of card behind a
chain that already has ~20 h left. The operator asked for the ranking.

Costs are read off the skin arm of the same day: 200 games of a 5-live-seat arm
took 18273 s (~5.1 h). Live seats per game scale the bill: mixed-pack has 2,
mixed-village has 3.

| # | arm | branch | cost | why here |
|---|---|---|---|---|
| 1 | mixed-pack | `slice/changeling-mixed` | ~2 h | Cheapest by far, and the only arm that can show the all-heuristic village's 77.36% against a random pack collapsing against a live pack. The heuristic branch's landed docs mean nothing until this reads. A single landed arm is a valid read under its criterion. |
| 2 | briefing | `slice/fanout-s21` | ~5 h | Tests the repo's own standing position (`AGENTS.md`: the payload is a budget, the per-phase drip is deliberate). Absence is the novel arm - every build reads from source states full rules and none ablates it. Direction is genuinely open: the `_night_against_the_table` inversion says more context can hurt. Either sign changes a written invariant, the highest information per hour on the shelf. |
| 3 | notebook | `slice/changeling-notebook` | ~5 h | The largest prompt change here - memory across rounds - with a falsifiable prediction recorded in advance (moves deduction more than win rate). Paired with briefing it gives two points on the "does standing context help at all" axis, against the same control, same seeds. |
| 4 | turns random-active | `slice/fanout-s27` | ~5 h | A mechanism arm, not a context arm: it prices seats going unasked. Plausible small effect, no invariant riding on it. Worth running, not worth running before the merge. |
| 5 | turns simultaneous | `slice/fanout-simul` | ~5 h | Its own criterion says the effect can only live in round 1. Shares one recipe with #4 (two arms serial), so it comes with #4 or the recipe is edited before launch. |
| 6 | phrasing | `slice/fanout-replies` | ~5 h | Its primary statistic is the refusal rate, and the live arms on this model run at ~0% fallback (skin arm of the same day: 0/15 on most games). A rate at zero cannot fall, so the primary read is foreclosed unless the positive arm makes things worse. The accuracy read is secondary and seventeen strings move at once. Lowest expected information per hour. |
| 7 | mixed-village | (arm 2 of #1's recipe) | ~3 h | Live village vs scripted pack: can a model read a scripted tell. Secondary by its own criterion; it runs automatically after #1 unless the card is cut. |

**The cut: run #1-#3 before the source-rules merge (~12 h), then merge.** Not
because #4-#7 are worthless, but because the merge is owed a fresh two-round
`llm` baseline under the new rules anyway ("merge and re-measure the bar", the
source-rules row). That post-merge baseline is the control the deferred arms
need. So deferring them costs a criterion rewrite each (they are unlaunched, so
editable) and no extra control run, while running them first costs ~20 h of card
and holds the merge.

**Kindred is the one thing this ranking does not settle.** Its bar
(`kin-chance.json`, 25.39%) was measured under the current rules and the peek
rule touches a lone wolf on any deck, so it too must run before the merge or be
re-barred after (a CPU job, 5376 random votes, cheap). Decided: re-bar after the
merge, since the deck's question does not depend on which rules the control used
and a fresh bar is minutes of CPU.

## Belfry names its source, 2026-09-02

Decided by the operator; the row is verbatim below. The edit landed the same
turn: `games/belfry/RULES.md:11` now opens "Modelled on Blood on the Clocktower,
in which a referee holds a board of tokens, wakes players one at a time, and is
allowed to choose", matching the form the other three rungs already use. The
descriptive clause was kept because it says WHY the game was picked, which the
bare title does not. **The de-branding question this settles is the general one:
a nominative "Modelled on <title>" line STAYS.** Naming the game is descriptive
use, mechanics are not copyrightable, and stripping the title makes the rung's
gate strata and chance baseline uncheckable against what they reproduce - the
same argument that kept the benchmark citations in `docs/reference-policies.md`.
The boundary that does the work is unchanged and already held: no brand reaches
a directory, module, class, role key or card key.

One fact found while deciding it and not in the row: `README.md:124` had named
the game since before the row was written, so the tree's front page named what
the rung's own canonical rules file circumlocuted.

- [ ] **Belfry is the only rung that does not name the game it is modelled on,
      and nothing says why.** `games/cabal/RULES.md:14`, `games/changeling/RULES.md:10`
      and `games/quorum/RULES.md:11` each open "Modelled on <title>. Nominative
      reference only", the form the tree-describes-parlor invariant licenses.
      `games/belfry/RULES.md:11` instead describes a "town-square family" - a
      circumlocution that identifies the same game to any reader who knows it,
      while `docs/` names that game outright in five places. So the caution buys
      nothing and the asymmetry reads as an unstated policy. Decide it either way
      and write it down: name it like the other three, or state the rule that
      exempts it. **Checked 2026-09-02 and NOT a finding: no brand reaches a
      canonical key.** The one code hit, `games/changeling/roles.py:331` mapping
      `pack` to a folklore word, is a SKIN value on the werewolf face and the key
      stays functional. That line is the one worth guarding - a brand migrating
      from prose into a module, class, role or card key - and unlike the gate's
      other patterns these names are already public in the tree, so a literal
      check would ship nothing a clone does not already hold.

## The next rung is Paranoia-shaped, not Lumen Ryder, 2026-09-03

**This is the ONE tracked statement of what the next rung is and why**, which the
queue asked for and no tracked line carried. The superseded plan is kept and
dated, below.

**Licence did not decide this, and that is the point.** Lumen Ryder Core's
permission is settled and published in its own SRD, so it was the cheaper
candidate on the axis that turned out not to be the bottleneck. What a rung earns
is the bottleneck.

- **Lumen Ryder earns nothing for gate #1.** Read at 117 pages 2026-09-03: setup
  reads every character sheet aloud to the table, and the Mystery dream forbids a
  prepared answer, so no seat holds what another may not. It carries real
  adjudication with no authority seat - novel, and the adjudicator rung has
  already been read. A variation on an answered question, charging a `RULES.md`
  authored from a 6 KB external cheat sheet whose gaps only its author can close.
- **A Paranoia-shaped rung is the first MULTI-AXIS entitlement.** `faction`,
  `deviation`, `directive` and `clearance` are orthogonal secrets. Every rung so
  far tested gate #1 against a single-axis role card; a briefing correct on three
  axes and wrong on the fourth is a failure mode the existing rungs structurally
  cannot produce. That is new information about the guarantee, not a re-run.
- **It needs no permission and no transcription.** Mechanics are not
  copyrightable, so it is built branding-free with functional keys, the way cabal
  is Avalon-shaped without shipping Avalon. cabal's architecture already is hidden
  role + private knowledge + vote + mission, and `core/` is what game #2 inherits,
  so the widening is from one secret to four.
- **Lumen Ryder is re-homed, not declined.** It goes to the play lane, unsequenced
  against the rungs, and its permission cite survives there.

**The superseded plan, kept.** The 2026-08-27 tracked call - gates #2 and #3
measure a MODEL and decay, so the next spike is the adjudicator against 3-4
discretion-heavy characters - was TAKEN as belfry's night arm and both reads
landed 2026-09-02. It is not wrong; it is spent. An off-repo ladder ranked a
different order over 2026-08-27/28 and was never visible to a cold session. This
entry ends that split: neither of those is live, this is.

**Pre-committed falsifier, before any build.** If the four channels collapse into
one payload assembly with one audit, the rung is a content build rather than an
instrument and this call reverses. Answer it by sketching one seat's ask and
counting what gate #1 has to check - four things, or one.

**Answered same day: FOUR. The falsifier did not fire.** `find_leaks` takes
`secret_terms: dict[int, list[str]]` and `entitled: set[int]`, so entitlement is
per SEAT and a seat's terms are one undifferentiated list. Under orthogonal
secrets that is not merely coarse, it is a FALSE NEGATIVE: a viewer entitled to
seat 5's `faction` puts 5 in `entitled`, the loop then skips every one of seat
5's terms, and a referee leaking seat 5's `deviation` into that viewer's ask
reports clean. The `find_leaks` invariant names that direction as the one that
must never happen. So the four channels are four checks and the rung is an
instrument.

**One honest weakening, and it does not reverse anything.** Per-axis keys are
reachable WITHOUT touching `core/`: `games/durf/facts.py` already widens the key
from a seat to a fact by numbering facts and handing the work back to the
unchanged primitive, and `("deviation", 5)` is the same shape as `("hidden",
"R2")`. So the build is not blocked on a `core/` change. That file also says the
move when a SECOND game asks is to widen `find_leaks`' key and delete the
adapter - and `core/`'s promotion rule wants evidence from a second game. This is
that game, so the widening becomes a promotion with its evidence in hand rather
than a speculative generalisation.

### The row this closes, moved verbatim from `queue.md` 2026-09-03

Struck because the entry above is its done-condition. Kept unrewritten per this
file's rule; its one deictic is resolved in brackets and nothing else is touched.

> - [ ] **Two plans for "what rung comes next", and only one is visible to a cold
>       session.** The tracked call is `docs/open-arms.md:578` and `queue.md:80`,
>       2026-08-27: gates #2 and #3 measure a MODEL and decay, so the next spike is
>       the adjudicator against 3-4 discretion-heavy characters. That was TAKEN as
>       belfry's night arm and both reads landed 2026-09-02. The off-repo sweep then
>       built a different ladder over 2026-08-27/28 - DURF, then a clue-economy rung
>       whose RULES are about information entitlement, then Cairn, then a
>       Paranoia-shaped rung - and ranked it against licence tiers the tracked tree
>       never sees. Neither supersedes the other and no tracked line says which is
>       live, so a cold session picking up "what next" reads the 08-27 call alone.
>       **Done when ONE tracked statement says what the next rung is and why**, with
>       the superseded plan kept and dated. Same class as the row above [the stale
>       `docs/open-arms.md` recommendation against building quorum, which the tree
>       had just built]: a position that outlived the work around it. Argument, not
>       code; costs no card. The off-repo half stays off-repo - `CLAUDE.local.md`
>       has the path, and naming it here is the signpost the hygiene invariant
>       forbids.


## The partner arm takes slot 3 and notebook slips, 2026-09-03

The GPU order above predates `docs/changeling-partner-criterion.md`, written the
next day. The operator asked where it lands. **It takes slot 3; notebook joins
the deferred group with #4-#6.** Order before the merge: mixed-pack (~2 h),
briefing (~5 h), partner (~5 h).

**Why it beats notebook on the margin.** Every arm in that table, partner
included, is a gate #2 or #3 arm - a measurement of a MODEL, which the direction
called 2026-08-27 says decays with the next checkpoint. So the choice inside the
set is not strategic; it is which arm most likely returns a number worth citing
per hour of card. Partner's effect has been OBSERVED twice already, on two
unrelated axes, at -10.03% and -12.05% against this arm's 8.7-point minimum
detectable effect. Notebook has a recorded prediction and no observation. A
pre-registered test of a twice-seen effect is a better bet than a first look.

Second reason, and the one that would decide it alone: **it closes an honesty
debt.** Two unadjusted free reads on the partner vote now sit published in
`docs/measurements.md` with no pre-committed test behind either. The tree's rule
is that a free read is not promotable; leaving two of them as the only evidence
for a real-looking effect is the state that rule exists to prevent.

**What it costs.** Notebook was slot 3 for pairing with briefing - two points on
one axis, same control, same seeds. That pairing is lost and notebook now needs a
criterion rewrite against the post-merge baseline, which is the cost this file
already accepted for #4-#6. Briefing still runs, so the standing-context axis
still gets its first point before the merge.

**Not deferred, and not competing for the card at all: the gate #1 per-axis key.**
The Paranoia row carries it and it reads as rung-building, which is why it has sat
below seven GPU arms. It is a live FALSE NEGATIVE in the primitive the whole arena
rests on, verified 2026-09-03 against `core/observability.py:76-79`: the scan is
`for seat, terms in secret_terms.items(): if seat in entitled: continue`, so a
viewer entitled to ONE of a seat's secrets is skipped on ALL of that seat's terms
and a leak of the others reports clean. That is the direction `AGENTS.md`'s first
invariant forbids by name - a false positive is a loud test failure, a false
negative is a shipped leak. It is CPU, it needs no card, `games/durf/facts.py`
already built the fact-keyed generalisation and says the move on a second asking
game is to widen the key and delete the adapter. **It runs concurrently with the
chain**, ahead of the GPU ranking rather than inside it.

## The `find_leaks` key: the BRANCH's keying is kept, 2026-09-03

Two branches generalised gate #1's key apart and neither knew about the other:
main's `ed6bf11` (`(seat, axis)` behind a `subject()` accessor) and
`slice/transport-retry`'s `0f729a5` (any hashable, opaque). The queue row asked
for them to be read side by side rather than merged, because a textual resolution
in this repo's most load-bearing primitive picks a winner by accident. Read
2026-09-03. **Keep the branch's.**

**It is a strict superset on key SHAPE.** Main widened halfway - `int |
tuple[int, str]` - which does not admit DURF's `("hidden", "R2")`, so main still
carries the numbering adapter in `games/durf/facts.py` that main's own comment
(`:13`) calls the thing to delete "if a game asks". A game asked. The branch
deletes it and calls the primitive directly.

**Its sentinel cannot collide.** DURF's `NO_VIEWER` is `-1` on main, safe only
because that module numbers its facts from zero - a coincidence, not a guarantee,
and main's own comment says so. The branch moves it to `core/` as an `object()`,
which is unequal to any key a caller can build.

**The two rules main has and the branch lacks are both false-negative shaped.**
Main grants entitlement to a bare seat covering EVERY axis of it, and skips the
self-audit for every axis of the viewer's seat. Both are silent skips. During
exactly the migration they were built for - a game adopting axis keys while one
call site still grants a bare seat - main's blanket grant skips every axis of that
seat and a leaked axis reports clean. The branch's stricter rule reports it, and
the caller opts out by granting the axis explicitly. `AGENTS.md`'s first invariant
decides this: a false positive is a loud test failure, a false negative is a
shipped leak.

**What the switch costs, stated because it is a reversal.** `ed6bf11` is
committed and mutation-checked, and reversing a landed guard is not tidying:
`SecretKey` and `subject` go (no consumer outside the module - grepped), and
main's tests asserting that a bare-seat grant covers every axis must be DELETED
rather than adapted, since that behaviour is the thing being removed. The
Paranoia rung then grants per axis, including the viewer's own axes, and the
queue row saying it "owes no `core/` change" is still true - it inherits a
different primitive than it expected.

**The two keys are even ordered oppositely** - main `(seat, axis)`, the branch
`(axis, seat)`. Nothing depends on it; it is the clearest evidence the two were
built without contact, and the kept order is the branch's.

**Not decided here: the rest of that branch.** It also carries a shared transport
rate budget (`5697df0`) and a whole unlisted `games/bureau/` rung, 971 insertions
that nothing in this tree has ever named. A rung nobody planned must not ride in
on a `core/` fix; each is its own call.

## No test suite runs while an arm is in flight, 2026-09-03

Decided by the operator, against this session's own measurement. `cl-gate2-village`
held ~1.00 min/game for 121 games and then ran 1.275 across games 121-141 - the
window in which this session ran three pytest suites (102, 1757, then 386 tests)
for the mixed rebase. About 25%, off the arm's own log, and it pushed the chain's
finish from 15:25 to ~16:45 local.

**Confirmed on the completed arm, and it has an after as well as a before.**
Games 1-121 ran 1.006 min/game, the suite window 121-151 ran 1.250 (**+24.3%**),
and games 151-191, with nothing else on the box, ran **1.007 - +0.2% against the
pre-suite rate.** The arm finished 200/200 at 12482s. So this is a before/during/
after with the after landing on the before, not a drift or a thermal ramp that
happened to coincide. Bucket noise is real - two 10-game buckets reached 1.16 and
1.09 with nothing running - which is why the claim rests on the 30- and 40-game
spans rather than on the 1.370 peak bucket.

**The arm is not voided and no number moves.** Fallback held 0/15 throughout and
wall-clock is not one of this arm's variables. What the reading costs is an
assumption, not a result.

**It corrects two places that priced concurrent CPU work at zero.**
`docs/open-arms.md` §While the card is busy says an instrument scored against
records that already exist "costs nothing and can outrank the run it waits on",
and §The partner arm takes slot 3 above says the gate #1 per-axis key "runs
concurrently with the chain". Both remain the right call on VALUE - a CPU slice
still buys more than an idle session - but the price is a quarter of the running
arm's throughput, not nothing, and that is now the number to argue against.

**The rule is scheduling, and it is deliberately not a gate.** Suites run between
legs or after the chain is down. A hook that refused pytest while a log lacked its
marker would fire on every cold session that never launched anything, and the
freeze it would enforce is already prose the operator applies. **It binds any
TIMING measurement absolutely** - `docs/measurements.md` §Route prices arms in
min/game, so a min/game figure taken while a suite ran is void, not noisy.

Not measured: whether the cause is CPU contention, IO, or the box's power budget.

## The adjudicator's ask is priced with ONE field, 2026-09-03

The queue row asked for "the two sizes the player path already records"
(`prompt_size`, `reply_size`). What landed is one: `ChoiceEvent.ask_size`, the
characters in the ask that produced the landed reply, plus every earlier ask and
reply of the session when `night_transcript` sent one ahead of it.

**The reply half buys nothing here.** A seat's reply size varies with what the
model chose to say; an adjudicator reply is one `{"choice": ...}` object whose
length is a function of the option string, so recording it would be a column of
noise around 20 bytes. What a transcript-class arm needs priced is what IT sends,
and that is the ask.

**A fallback records 0**, the same reading `core/callcost` gives a decision no
model answered: an ask that landed nothing is not a cost the arm bought
anything with. A recovered call records the attempt that LANDED, refusal text
included - the pre-retry ask is not what the model answered.

**The verdict tools' event whitelist grew an OPTIONAL half.**
`eval/belfry_adjudicator_verdict.EVENT_FIELDS` is a leakage guard: an unknown key
in the classifier's input is a channel nobody reviewed, so it voids. Requiring
`ask_size` would instead void every record written before today, which is the
whole S8b/S23 baseline. So it is named in `OPTIONAL_EVENT_FIELDS` - allowed,
never required, checked for nothing. `eval/belfry_steering_verdict` reads the
same two sets.

Not measured: any arm. The field is an instrument and is not model-facing, so no
number moves and nothing re-baselines.

## A run REFUSES an occupied record path, 2026-09-03

`core/runlog.py claim_record(out)` is called by all six drivers at the same door
that refuses a keyless backend, and it raises `SystemExit` when either the summary
or its `.jsonl` sibling already exists.

**The hazard it closes.** The JSONL is appended per game and the summary beside it
is truncated, so a second run onto an occupied path STACKED its games onto the
first and REPLACED the summary: the two files then described different
populations with nothing raising. `cl-heuristic`, `cl-mixed-pack` and
`cl-mixed-village` are each 3000 lines for 1000 games, and the first block of
`cl-heuristic.json.jsonl` is a stale play of the same seeds at 71.55% pack wins
against the published 56.09% - blended naively, about 61%, plausible and five
points wrong. No published number moves: every one reproduces from a deduped read.

**It refuses; it does not truncate.** The occupied file holds a run that cost
GPU-hours. Clearing it is the operator's call, and a launcher that deletes a
record to make room is the one outcome worse than stacking.

**The guard is a ratchet keyed on the APPEND, not on a list of drivers.**
`core/test_runlog.py` finds every module that opens the JSONL in `"a"` and
requires the claim in the same file, with a floor test so that renaming the
append idiom cannot empty the set and pass vacuously. A seventh driver copied
from a sixth is caught by its own append.

**What it does NOT do.** `eval/mixed_verdict.dedupe_last` stays - the records that
already carry a second block are not going to rewrite themselves. And five
recipes still `del` a stale JSONL instead of refusing; that is a queue row.

Not measured: whether any recipe was ever re-run onto its own path deliberately.

## Per-table play state lives under one ignored root, 2026-09-03

Tables the operator plays at accumulate state a script reads and writes - raw
transcripts, campaign state, persona definitions, derived memory. None of it is
tracked: play transcripts carry a setting's own text, which the tree stays free
of, and `transcripts/` is for the rendered evidence of a claim, not a play log.

- **One root, `/local/`, ignored at the repo root** - not a `local/` under each
  rung and not more subdirs of `.scratch/`. The split with `.scratch/` is by
  KIND: `.scratch/` is prose nothing executes, `local/` is data a script
  addresses by rung and table. One root because the backup is a nested private
  git repo inside it, and a nested repo needs one root; N scattered dirs means N
  repos or junctions, which is maintenance that stops happening.
- **Event-sourced.** The transcript is the append-only log and every other file
  is a projection regenerable from it by a tracked script - the same invariant
  as "output untracked, recipe tracked". A projection carries a `version:`.
- **A seat's memory derives from that seat's own audited view, never from the
  referee-side transcript.** Memory rides in the payload on every later call, so
  gate #1 reaches across sessions; a memory built from the referee view would
  leak the GM's secrets into a player three sessions later, past every per-turn
  audit.

The layout and the cadence are `local/README.md`, which is untracked with the
rest - it is the contract for a dir a clone does not have.

## Tables ahead of arms, 2026-09-03

The 08-27 direction (spike the adjudicator, because gate #1 is durable and
gates #2/#3 decay with the checkpoint) is spent - every belfry discretion arm is
READ. What ranks first now is the three rows that end in a table a person sits
at: the play lane, the browser seat, the Paranoia-shaped rung. The frozen
changeling arms keep their criteria; they get card only where a run is already
chained or a merge already resolved, and no new changeling criterion is cut
ahead of a table row. The arms measure a model and the tables are what the
model is for.

## cabal keeps its `games/` slot by elimination, not by the earning test, 2026-09-04

The earning test in `AGENTS.md` admits a rung that exposes one named executable
risk to isolation or referee judgment no existing rung expresses. **Applied
honestly, cabal fails it.** Its model is static asymmetric knowledge dealt at
setup, and two rungs verifiably contain that: `games/quorum/RULES.md` line 173 -
at five seats the two minority seats know each other and the majority do not,
entitlement "evaluated at the deal" - and changeling, whose pack seats are shown
`fellow-pack` at the meet. Belfry does NOT contain it: its evil briefings moved
to seven seats and up on 2026-09-02, so at five seats its evil seats are
strangers.

It stays because every alternative is worse, and that is the whole reason.
`experiments/` is definitionally wrong - its `__init__` says proof fixtures and
drafts that are NOT games a person plays, and cabal is playable and registered.
The private arm is ruled out by the migration shape settled the same day: a rung
with published figures stays public and testable, and cabal's gate #3 numbers are
cited. A namespace invented for one retired-but-playable rung is the artifact-of-
last-resort this layer keeps refusing.

**Two arguments for keeping it were checked and do NOT hold.** "No model needed"
is not a cabal property: all five rungs run to completion modelless, exit 0, and
the README line implying otherwise was drift, fixed the same day. And minimality
as a regression control does not require a `games/` slot, because a demoted
rung's tests keep running - `experiments/heartbeat` proves that.

**So the invariant is NOT amended.** Adding a second admission ground for
minimality would dress a nowhere-else-to-put-it as a principle, and the next rung
would claim it. A reader applying the test and reaching demotion has read the
test correctly; this section is the answer, not a hole in it.
