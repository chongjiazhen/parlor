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
