# The faction heartbeat, and what an off-map actor breaks

Written 2026-08-27, unmeasured, from a design read of `core/observability.py`,
`docs/reproducibility.md` and `docs/action-channel.md`. Same job as the action
channel note: nothing here is a decision, it is here so the cheap moves stay cheap.

**The item this scopes.** `queue.md` has carried one line since the first commit -
"off-map faction heartbeat: factions acting on their own clock, driven by a
long-running agent process outside the game loop" - and nothing has ever said what
that would break. It was queued as free work because it runs outside the game loop
and so touches no model-facing byte, no scorer and no GPU. That is true of scoping
it. It is not true of building it, and the difference is most of this file.

## What an off-map faction is, against what parlor has

Every actor in `cabal` and `changeling` is a seat. The world moves only when the
referee asks a seat for a decision, and it moves by exactly one decision. A faction
is an actor with **no seat** - a guild, a rival house, a watch - that holds goals,
takes actions, and changes world state on a clock of its own rather than in response
to any seat's turn.

**The claim it tests is the repo's own, sharpened: entitlement gains a time axis.**
Today entitlement is a function of `(seat, phase)`, and every seat's context is
derived from one referee render at one instant. A faction that acts at tick `t`
raises a question the current model has no way to state: a seat that was present
learns at once, a seat elsewhere learns late and possibly wrong, and a seat that
never learns must carry no trace of it in its bytes. That is gate #1 with a clock
attached, and `find_leaks` has no notion of when.

## Four things it breaks, in the order they will bite

### 1. The audit loses its instant, and fails silently

`find_leaks` grades a render against the secrets that are secret **now**. With a
heartbeat, a fact can be legitimately un-leaked at `t` and legitimately public at
`t+1`. Audit a render built at `t` against entitlement recomputed at audit time and
a real leak reads clean, because by then the fact had become public by other means.

This is the worst shape of failure this repo knows: nothing raises, the audit
reports zero leaks, and the number it protects is void. The remedy is structural
and cheap if it is done first - **capture the entitlement snapshot with the render
and audit against the snapshot**, never recompute. Gate #1 is the driver's
guarantee and it audits every turn; what it must additionally carry is the tick the
turn was rendered at.

### 2. Wall-clock voids reproducibility, so the clock has to be logical

The seed invariant is that `--seed` seeds the sampler as well as the deal, and
`docs/reproducibility.md` measured what that buys: two 20-game runs at the same
seed, byte-identical across all 20 records. That property depends on a fixed call
order. A faction driven by real time has no fixed call order, and a run that cannot
be replayed is not a measurement.

So the "long-running agent process" half of the original stub is backwards. **Ticks
are counted, not clocked**, the tick schedule derives from the game seed, and
whether a separate process drives it is an implementation detail that must not be
observable in the record. If the record can tell which process produced it, the
design is wrong.

### 3. A faction's decisions are not seat decisions

Every number in this repo ships beside its fallback rate, and the scorer voids
above 10%. A faction agent makes decisions and can fall back too, so the accounting
has to be decided before the first run rather than after it:

- **Faction decisions stay out of the run's denominator.** The gates measure
  seats. Pooling a faction's calls in would inflate the denominator with decisions
  no gate is about, and every historical rate would stop being comparable.
- **The faction's fallback rate is still reported, beside the run's, never inside
  it.** A faction that fell back to random changed the world the seats then reasoned
  about, so hiding it is the random-policy-wearing-a-model's-name failure the
  invariant already names, relocated off-map.

### 4. It is the adjudicator's hardest component at a fraction of the surface

A faction acting off-map produces events the referee must **narrate**. If a model
authors that narration, gate #1 dies exactly the way `docs/action-channel.md` says
it does under a model DM: "the innkeeper looks nervous" leaks that he is the
cultist with zero substring overlap, and naive matching reads clean. The remedy
there is the remedy here - the actor declares its intended reveals as **typed
facts**, those are checked against entitlement, and the prose is audited against the
facts it did *not* declare. Keep `find_leaks` naive; change the corpus.

**Which means these are not alternatives, and `queue.md` §S8 currently lists them
as though they were.** The typed-fact channel is the expensive, unbuilt part of the
adjudicator spike, and a faction is the smallest thing that needs it: a handful of
action types against a Storyteller's 20-plus characters of discretion. Building the
heartbeat first is a way of building the adjudicator's hardest piece against a
surface small enough to test exhaustively. That reorders the queue rather than
adding to it.

## The cheapest version that tests anything

Not a process. A heartbeat is a logical clock plus an actor with no seat, and the
long-running-process framing is the expensive half and the least informative.

**One faction, three action types, a seeded tick schedule, and a propagation rule
that decides who learns what and when** - run as a step between existing phases,
inside the loop. If the audit cannot be made sound at that size, no amount of
process architecture rescues it; if it can, the process is a deployment question
and can be answered later or never.

Score it on one thing: **can a render be audited against the entitlement that held
when it was built.** Everything else here is downstream of that answer.

## What not to harden on the way

Both already stated in `docs/action-channel.md` and both apply verbatim - a faction
is another game's shape arriving early. Do not add faction phases to `cabal`'s
`Phase` enum or to the `action_prompt` if-chain, and do not grow `ACTION_KEYS` into
a shared flat tuple.

One more, from the repo invariant: **the clock does not go in `core/` yet.** `core/`
is what game #2 inherits, and promotion waits on evidence that a second game needs
it. No game in the tree has a faction, the RPG rung that would is not built, and a
scheduler written speculatively into the primitive layer is the hardening this file
exists to warn about.

## Built 2026-09-02 - what the spike found

`games/heartbeat/` is the cheapest version above, built S24 and scored on the one
question. **The snapshot audit is sound at this size.** Each render carries the
entitlement snapshot taken in the same step it was built - tick, the facts that
existed, and what each seat held - and `audit(render, snapshot)` takes those two
things and nothing else. Fixture (`test_fixture_counts_caught_against_missed`):
six leaks injected at ticks 2-7, four of whose facts went public at t+1 by a
route the faction did not own. **Snapshot audit: 6 of 6 caught. Recompute at end
of run: 4 of 6 missed, 2 caught** - the two whose facts never went public. The
first version of the loop audited at the end against the world as it then stood,
and the guard test went red against it; that red run is the mutation check, and
it was repeated by hand after the fix.

Two things the build settled beyond the note:

- **A fact's statement must carry its own sentinel**, and `World.add_fact`
  refuses one that does not. The first guard fixture leaked a statement whose
  term was not in it, and the leak audited clean with the snapshot in place - a
  fact the matcher cannot see leave is unaudited whatever the snapshot says.
- **The clock is `random.Random(f"schedule:{seed}")` and nothing else.** Records
  are byte-identical across two runs at one seed; no record field names a time,
  a pid or a process, so the deployment question stays a deployment question.

**Promotion evidence, not promotion.** The heartbeat imports `WorldFact`,
`find_fact_leaks` and `check_facts` from `games/durf/facts.py` - it is the second
consumer of the fact-keyed adapter, which is what the `core/` invariant asks for
before a thing moves. It stays in `games/durf/` until a slice moves it; nothing in
`core/`, no game's `Phase` enum, `action_prompt` chain or `ACTION_KEYS` was
touched. Faction decisions are tallied in their own `Tally` with their own
fallback rate; there are no seat decisions in the spike to pool them with, and
the seam (`Policy.choose`) is where a model policy would drop in.

## Seated in belfry 2026-09-02 - what seating found

`games/belfry/heartbeat.py` seats the S24 spike at belfry's table, off by default
behind `--heartbeat` on `eval/run_belfry.py`. The world, the three action types,
the propagation rule, the schedule and the snapshot audit are imported from
`games/heartbeat/heartbeat.py` unchanged; the seating adds no model of a faction.

**Nothing in belfry's `Phase` handling had to move.** The warning in
`docs/action-channel.md` was about the three shapes that harden early, and the
faction needs none of them: it takes no seat decision, so the referee's cursor
never learns it exists. A tick is a NIGHT, taken at the top of `_begin_night`
before any role wakes, and that is the whole hook - two lines, no phase, no turn
kind, no `ACTION_KEYS` entry.

Four things seating settled that the spike could not:

- **Gate #1 covers the new bytes by construction.** `BelfryReferee.audit` grows a
  third scan over the faction's facts, so `play_game`'s default-on audit raises on
  a leaky faction render exactly as it does on a leaked role. The leaked thing is
  not a seat, so the scan reports seat `-1` and names the fact in the term slot.
  Measured: the leaky renderer is caught, the honest one is clean over 50 seeds
  played to the end, and removing the scan kills the named test.
- **The render and its snapshot are one object, and the audit grades that pair.**
  `seat_lines` builds the pair and `audit` reads the one just built, so the
  recompute failure cannot arise inside a turn. It is still reachable from
  outside - anything re-scoring a stored render - which is what
  `heartbeat_render` exists for and what the guard test drives: a leaky render
  built on night 1, the world moved on a night, the fact published by another
  route, snapshot audit dirty and recompute clean. Mutating `leaks` to recompute
  kills that test.
- **The flag off is byte-identical, and it is pinned rather than argued.** The
  digest in `games/belfry/test_heartbeat.py` covers every prompt sent over 20
  seeded games plus each game's outcome, referee log and public channel, and it
  was computed on the commit BEFORE the faction existed. A digest taken after the
  change would have pinned the change to itself.
- **Scheduled and taken come apart, and both ship.** The schedule runs to the day
  bound; a 5-seat game ends in about three days, so most beats are never reached.
  Reading only the taken count would let a run whose faction never acted pass as a
  faction arm.

Two things seating did NOT settle, and neither is a blocker:

- **The rumour rule is linear, and belfry's table is a circle.** A seat's place is
  its seat number, and the spike reaches `place +/- 1`, so seats 0 and n-1 are not
  neighbours for rumour though they sit beside each other. Making it circular is a
  change to a merged spike and a second variable; it is written down rather than
  fixed quietly.
- **No model has played against a faction.** The policy seam is `Policy.choose`
  and the control policy is what ran. Whether an off-map actor changes how a table
  reasons is unmeasured, and no criterion is written.
