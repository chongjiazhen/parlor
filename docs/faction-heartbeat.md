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
