# The control ladder - the part that generalises

Moved verbatim from `docs/scripted-rungs-cabal.md` §0 on 2026-09-02, the day the
promotion trigger it named fired: a second game built a ladder rung
(`games/changeling/heuristic.py`, measured in `docs/measurements.md` §changeling
heuristic rung). Nothing below was rewritten. The cabal rungs stay in that file;
this is the argument they and every later rung stand on.

---

## 0. The part that generalises

**Promotion trigger: when a second game builds a ladder rung, this section moves
to `docs/control-ladder.md` verbatim and this file points at it.** (Fired
2026-09-02; this is that file.) It is written game-free on purpose. The three
cabal rungs stay in `docs/scripted-rungs-cabal.md`.

### The ladder's job is a denominator, not a player

Gates #2 and #3 measure a model and decay with the next checkpoint - S1 already
found the tell. A denominator does not decay only if it is a property of the
**game**, which is what `docs/reference-policies.md` §Why hard-constraints-only
is the point rests on. A hand-written rule qualifies: it is fixed, readable,
re-runnable, and gate #1 clean by inspection - every branch consumes
`entitled_knowledge(seat)` and `public_events` and nothing else.

A learned policy fails that test on four counts, and only the first is about
compute:

1. Its score is a fact about its own training run and seed. Re-train and the
   denominator moves, which is exactly the decay the ladder exists to escape.
2. Gate #1 stops being true by inspection and becomes an audit of a featuriser.
   That is a new correctness surface bought for no measurement.
3. Self-play produces the self-play equilibrium. It answers "what do two copies
   of this learner converge to", not "what was extractable from the record the
   models left", and the second is the question every offline arm in
   `eval/ladder.py` asks.
4. Cost: a torch dependency on a box with known arch traps, against the
   no-new-dependencies rule, for a rung whose output is less legible than sixty
   lines of tallies.

The steelman for learning survives all four and is answered in §4: the honest
objection to a hand rule is that 94.3% is *some* rule's score and not the
ceiling. That is a real gap and it does not need RL to close.

### The ceiling estimator protocol

When the ladder needs a ceiling rather than another rung, fit the cheapest model
that admits the question - and **train it somewhere the test set is not**.

- **Train on self-play.** Random and heuristic arms are CPU, unbounded, free,
  and the referee is the same one the models played against.
- **Test on the LLM corpus**, held out entirely, tie-averaged like every other
  offline arm.
- Report it as `ceiling` beside `captured`, and state that it is still a **lower
  bound on extractable signal**, for the same reason the solver's zero is.

The reason the split is not optional: cabal's pinned corpus is 29 hunts. Fitting
anything on 29 points and quoting the fit as a denominator publishes a memorised
answer as a measurement. Self-play is the only sample source that is large,
free, and not the thing being measured.

### Two discipline constraints the rungs inherit

- **A rung is printed beside a gate, never in place of one.** Same constraint as
  `docs/reference-policies.md` §The discipline constraint. If a rung's statistic
  is to become a gate, it is pre-committed before a run like every other gate.
- **Swap one side at a time.** The all-heuristic hunter arm reads 99.5% and is an
  artifact - a deterministic seer's votes track taint exactly, so the rule reads
  its own twin. Any new rung inherits that trap the moment it is seated on both
  sides.
