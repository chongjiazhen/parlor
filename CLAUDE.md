# parlor

`queue.md` is the QUEUE, and only the queue - open rows, live slices, and what a
cold session should pick up. What has landed leaves it: `docs/measurements.md` for
the dated numbers, backends and route calls (read that before trusting a number),
`docs/decisions.md` for what is settled, `docs/slices.md` for the closed slice
ledger live rows still cite by name. `README.md` has the three gates and the
two public channels. `games/<name>/RULES.md` is the canonical statement of that
game's rules and knowledge model - read it before trusting a gate number, because
the gate strata, the decision audit and the hunt baseline all derive from it, and
a variant that changes what a role learns changes all three. `docs/` holds the
durable design notes and reference that would otherwise silt up the queue -
`docs/README.md` is its index, and a design note that hardens into a decision moves
to the Invariants below. Run output
lands in `eval/records/` (gitignored, durable); the rendered transcript that
evidences a claim is what gets committed, in `transcripts/`.

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
- **`--seed` seeds the SAMPLER as well as the deal, or it is not a seed.**
  `Backend.seed` rides in the payload and `one_game` hands each game the number it
  deals with. Seeding only the deal made "same seeds, one variable" a claim about
  the roles while the model drew freely, and two seed-1000 runs came back with 63
  missions and 74. An unpinned run still sends no seed - a default would make every
  run look reproducible while the records say nothing about it.
- **Gate #2 is conditional on gate #3.** Measured: with good voting at chance, evil
  wins ~65% with no deception at all.
- **`core/` is what game #2 inherits; `games/<name>/` is what is about that game.**
  Promote on evidence that a second game needs it.
- **The ask carries what THIS phase needs, and the payload is a budget.** parlor is
  local-first - `docs/measurements.md` §Route: local is the gate lane, one model
  served serially on one box - so context is scarce in a way a frontier API hides,
  and a standing rules dump would be paid on every call of every seat of every
  game. So a rule reaches a seat at the phase where it is actionable: VOTE gets the
  reject rule, MISSION gets `need` and the seat's own stake, PROPOSE gets neither.
  **This is a position, not an omission**, and two things hold it there. Every byte
  in the payload is audited by gate #1 and re-baselines every number recorded under
  it. And restating a fact a seat ALREADY holds is measured to cut both ways -
  `_night_against_the_table` bought +7% -> +63% on a 12B and then INVERTED on q36
  (+80% as-is vs +72% with the line), so more context is not monotonically better
  and cannot be adopted on the argument that it ought to help. Adding standing
  context is a measured arm (`queue.md`), never a convenience. What a PERSON needs
  is a different question with a free answer: `core/console.py` prints a briefing
  and `rules` beside the view, outside the payload, where neither cost lands.
- **The tree describes parlor; the rest is a working note.** Canonical keys stay
  functional and branding-free - prose may name the game a rung is modelled on,
  while that game's role names, art and text stay out of the code. Published work
  is cited by identifier, never by author. Who ELSE built something, what their
  work is worth, and any claim nobody here has read first-hand go to the untracked
  working notes.
- **A run's OUTPUT is untracked, a run's RECIPE is tracked.** `eval/records/` holds
  the raw blobs and never enters history; the rendered transcript that evidences a
  claim does, in `transcripts/`. The launchers in `eval/runs/` are inputs, not
  output - a run recipe that is not versioned cannot be reviewed after it misfires.
- **Judge a detached run by its own log or JSONL** - CPU, IO counters and exit codes
  all read as healthy while a run sleeps, and one such call killed a live run. Probe
  a cloud tier with a burst: a cooled key serves single requests and fails a stream.
- **`queue.md` keeps only what can still change, and the pre-commit gate holds it
  to that.** Done work
  leaves - a landed slice struck and moved to `docs/slices.md`, a dated reading to
  `docs/measurements.md`, a settled call to `docs/decisions.md`. The rule is as old
  as the file and was broken anyway, because it had no destination and appending
  was the only move available; the file reached 1200 lines, which every cold
  session then paid to read. It has destinations now, so
  `scripts/hygiene-check.sh` enforces it as a RATCHET rather than prose: under the
  budget the file is free, over it a commit may shrink or hold but never grow. A
  flat ceiling would have failed the very next commit and taught the author to
  reach for `--no-verify`. **The budget is BYTES, 2026-08-28** - it was lines, and
  a line count is a proxy a rewrap defeats for free: measured, 100 bytes of new
  prose paid for by merging two wrapped lines PASSES a line ratchet and fails a
  byte one. Read it before writing a row, not by failing the gate:
  `sh scripts/hygiene-check.sh --budget`.
- **Publish hygiene is a GATE, not a pass.** `scripts/hygiene-check.sh` runs from
  `.git/hooks/pre-commit` and reads the lines a commit ADDS, which is why it needs
  no list of what is excused - and a list of what is excused would be a map to the
  material anyway. It carries pattern SHAPES, never a literal name, address or key:
  a public checker that grepped for the forbidden value would ship that value to
  every clone. A hit that is a reviewed keep means the PATTERN is wrong. What the
  gate cannot see is the judgement half - whether a new doc assesses a third party,
  quotes work nobody here has read, or names an author where an identifier would
  do. That is the invariant above, and it is checked when a doc lands, by a reader.
