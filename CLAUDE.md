# parlor

`RESUME.md` is the queue, the dated measurements, and the route decisions - read it
before picking up work or trusting a number. `README.md` has the three gates and the
two public channels. Run output lands in `eval/records/` (gitignored, durable); the
rendered transcript that evidences a claim is what gets committed, in `transcripts/`.

## Invariants - the single source of truth for these

Decisions, not accidents. Each one is here because a reasonable edit would undo it.
Change them against a measurement, and change them HERE.

- **`find_leaks` stays naive substring matching.** A false positive is a loud test
  failure; a false negative is a shipped leak. A colliding term gets RENAMED.
- **Gate #1 is the driver's guarantee.** `play_game` audits every turn and RAISES,
  by default, for every caller. It stays that way: the eval lane once forgot to pass
  an opt-in callback and ran live models unaudited for a session.
- **Only the referee's own bytes can leak.** What a seat SAYS is gameplay, true or
  false, and is audited out (`include_speech=False`). A seat's private `think`
  reaches neither public channel; it appears only in the referee-side transcript
  section, which no model ever receives.
- **Every number ships beside its fallback rate**, and the scorer voids verdicts
  above 10%. A decision no model could make legally is played at random and counted
  - a run that hides that is the random policy wearing a model's name.
- **Gate #2 is conditional on gate #3.** Measured: with good voting at chance, evil
  wins ~65% with no deception at all.
- **`core/` is what game #2 inherits; `games/<name>/` is what is about that game.**
  Promote on evidence that a second game needs it.
- **Canonical keys are functional and branding-free.** Prose may name the games a
  rung is modelled on; a game's role names, art, or text stay out of the code.
- **Judge a detached run by its own log or JSONL** - CPU, IO counters and exit codes
  all read as healthy while a run sleeps, and one such call killed a live run. Probe
  a cloud tier with a burst: a cooled key serves single requests and fails a stream.
