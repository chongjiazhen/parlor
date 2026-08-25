# parlor

**Read `RESUME.md` first** - it is the queue, the locked decisions, and the dated
measurements. `README.md` has the three gates and the two public channels. Raw run
output lives in `eval/records/` (gitignored, durable); the rendered transcript that
evidences a claim is what gets committed, in `transcripts/`.

No `@import`s here on purpose. `measurement-standards.md` and `shell-fidelity.md`
are already routed on demand by the always-on rules, and this file is the pointer,
not the payload.

## Invariants a reasonable edit would break

These are decisions, not accidents. Change them only against a measurement.

- **`find_leaks` stays naive substring matching.** A false positive is a loud test
  failure; a false negative is a shipped leak. A colliding term gets RENAMED - do
  not quiet it with word boundaries.
- **Gate #1 is the driver's guarantee, not a caller's.** `play_game` audits every
  turn and RAISES. Never make it opt-in: the eval lane once forgot to pass the
  callback and ran live models unaudited for a session.
- **What a player says is gameplay; only the referee's own bytes are a leak.**
  Speech is audited out (`include_speech=False`); a seat's private `think` reaches
  neither public channel. It does appear in the referee-side transcript section,
  which no model ever receives.
- **Every number ships beside its fallback rate**, and the scorer voids verdicts
  above 10%. A decision no model could make legally is played at random and counted
  - a run that hides that is the random policy wearing a model's name.
- **Gate #2 is conditional on gate #3.** Measured: with good voting at chance, evil
  wins ~65% with no deception at all.
- **`core/` is what game #2 inherits; `games/<name>/` is what is about that game.**
  Resist promoting anything until a second game actually needs it.
- **Canonical layer is branding-free functional keys.** Prose may name the games a
  rung is modelled on; a game's role names, art, or text never enter the code.

## Running it

```bash
python -m unittest discover -s . -p "test_*.py"     # no dependencies
python -m games.cabal.demo --transcript game.md     # one game, random players
```

Live players need a backend (`--backend local|clean|gray`, `PARLOR_API_KEY` for the
cloud tiers). Judge a detached run only by its own log/JSONL - never by CPU, IO
counters, or an exit code - and probe a cloud tier with a burst, not one call.
