# Decisions already locked, and the criteria that were pre-committed

Moved out of `RESUME.md` 2026-08-28: settled, not queue. Verbatim.
Code invariants are NOT here - they are in `CLAUDE.md`, which is always loaded,
and two copies of one rule is how the stale copy wins an argument.

## Decisions already locked

**Code invariants moved to `CLAUDE.md`** - it is always loaded, these are not,
and two copies of one rule is how the stale copy wins an argument. What stays
here is project state: the route calls and what a run measured.

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
  a live row below: if the hunter lands marginal, **respecify the metric rather
  than buying games**, because gate #3 is bottlenecked on its lowest-power half.
- The discipline itself, the `hunt20b` error it exists to refuse, and why pooling
  runs after the fact is the same move as peeking:
  `docs/evidence-discipline.md` §Pre-committing a statistic.
