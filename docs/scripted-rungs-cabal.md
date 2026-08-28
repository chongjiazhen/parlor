# Scripted rungs - cabal

Written 2026-08-28, unmeasured. A route decision and three scoped rungs, from a
read of the veteran-Avalon convention set against what this repo already built.
**Nothing here is a gate and nothing here re-specifies one.** Read
`docs/reference-policies.md` §The control ladder first; this is that section's
next three rungs and the argument for why they are hand-written rather than
learned.

The prompt was an outside one: a DCSS agent that hands every decision-free turn
to a scripted layer and wakes a model only on the turns that carry a decision.
The question it raised here was whether parlor's ladder should keep climbing on
if-statements or switch to a learned policy. It should keep climbing on
if-statements, and §0 is why.

---

## 0. The part that generalises

**Promotion trigger: when a second game builds a ladder rung, this section moves
to `docs/control-ladder.md` verbatim and this file points at it.** It is written
game-free on purpose. The three rungs below are cabal's and stay here.

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

---

## 1. What did not transfer, and the one thing that might

The DCSS split is **scripted layer owns every turn with no decision in it, model
woken by a gate**. It is a cost and legibility lever: hundreds of model calls per
game instead of tens of thousands.

**It does not transfer to the deduction ladder.** cabal has no decision-free
turns - every phase a seat acts in is a measured decision, so a hybrid seat does
not save cost, it destroys attribution. There is already a queued
"mixed heuristic/LLM table" item and this is the reason it is a *labelled arm*
rather than a default.

The one thing that might transfer is narrower. Discussion is the most expensive
and least-scored decision at the table, and games-per-GPU-hour is the binding
constraint behind every interval in `queue.md` - 29 hunts is the whole cabal
hunt corpus. A scripted `_say` with a model-driven vote and hunt would buy games.
It is a separate program from this one, it needs its own arm label, and it must
not be folded into a rung quietly.

---

## 2. Rung A - the designated failer, and where it actually lives

The veteran convention is a total order over evil roles that designates exactly
one saboteur per mission, so the fail count on a tainted mission is 1 rather
than 2. `heuristic.py` currently plays the opposite: **an evil seat always plays
fail**, stated in its docstring as a deliberate upper bound on over-sabotage.

Three things are already settled about this and must not be re-derived:

- **The focal point is derivable with zero communication** and the ideal
  double-fail count for capable reasoners is ~0, not "some":
  `docs/gate3-modelling-review.md` §3. Both evils know both identities, the
  proposal is public, so "lowest-numbered evil on the team fails" is common
  knowledge. `over_sabotage`'s benchmark is already stated as "the pair failed to
  find a convention" (S9).
- **The convention leaks nothing incremental about *attribution*.** Card
  attribution is never public; only the count is emitted. Good cannot tell a
  focal-point 1-fail from a lucky mixed 1-fail. Do not write the rung up as if it
  hides who failed.
- **What it does move is the COUNT**, from `{0, 2}` onto `{1}` - and the count is
  the strongest hard constraint the solver can ever receive. `|T ∩ evil| >= k` at
  `k=2` on a 2-seat team pins both evils exactly; on a 3-seat team it puts 2 of 3.
  In `SETUP_5` there are exactly two evils, so a double fail is the single largest
  information event in the game. Eliminating it is measurable with the instrument
  that already exists.

**The prediction, stated before the run:** replacing always-fail with the focal
point should lower `end-of-game bits` (pooled 0.732 mean over 180 good seats,
79 above zero) and should not move `bits_gained` at the hunt, which is zero by
proof. A fall in the first with no movement in the second is the result. Movement
in the second means the offline path has drifted from `test_solver.py`.

**It will not become a usable win-rate rung and that is not the point.** In
`SETUP_5` every mission needs one fail, so a designated failer sinks exactly the
missions always-fail sinks; the evil arm stays near 100% against a
non-coordinating good side, which is a statement about the good side. The rung is
an **information** rung, and it isolates the information variable while holding
the outcome fixed. That is a cleaner experiment than the win-rate one cabal
cannot have.

**Where the veteran ordering actually becomes non-trivial: 3 evil seats.** At 5
seats the order is one line - MIMIC and HUNTER both see each other, so the
convention is "lowest-numbered evil on the team". The published orderings put the
non-coordinating roles at the top of the priority list precisely because they
cannot defer: parlor's `STRAY` neither sees its own side nor is seen by it, so it
must always fail and everyone else must yield to it, and `LURKER` is hidden from
the seer rather than from its partners. Both are 7+ roles by construction
(`roles.py`), and `queue.md` already packages **6/7p + the two
information-degrading evils** as one item for the same reason.

**So rung A is not a new lane.** It is the CPU half of that queued item: the
convention at 5 seats now, as `over_sabotage`'s reference policy, and the full
priority order when 3-evil setups are seated. The LLM half - whether models find
the convention unaided - needs GPU cabal no longer has, and queues behind
changeling or lands at the publish boundary.

---

## 3. Rung B - the watcher bluff is a channel, not a rung

The convention on the good side is the watcher claiming to be the seer, to draw
the hunt. It is trivially writable as a template string, legal (speech is
gameplay, audited out at `include_speech=False`), and gate #1 clean. It is still
not a ladder rung, for three reasons:

1. **It only means something against an LLM table.** A bot table has no belief to
   update, so its measurement is GPU-gated and cabal's GPU program stopped at the
   3b verdict.
2. **What it would measure is a deception FLOOR**, which is the thing gate #2
   lacks: can a model beat a fixed string emitted at the correct phase. That is
   the S1-shaped capability question and it is the cheapest possible version of
   it.
3. **Prediction, worth writing down before it is built: a speech-only bluff
   cannot move `hunt_by_votes`.** The bluffing watcher's votes are unchanged and
   the rule reads votes conditioned on taint. If it moves, either the rule or the
   record is wrong. So the bluff and the hunt rung measure disjoint channels,
   which is a property worth having in a ladder and a cheap instrument control.

**Build it as a typed claim, not as prose.** `docs/action-channel.md` already
argues the shape for the adjudicator: declared facts checked against entitlement,
prose audited against what was not declared. A `claim(role)` action gives a bluff
*rate* that is countable and auditable; a free-text bluff gives a substring hunt
through prose, which is the naive-matcher failure that doc names as the RPG
rung's hardest problem. Do not build the free-text version as a shortcut.

**And it is not only this rung's problem.** The queue already carries a
self-outing count that has to be rebuilt as a claim-shaped match, over-counting
~3x on the theme-name version and reading 0/1290 on the functional-key one, with
the note that a mimic claiming to be the seer is invisible to either because both
match only the seat's OWN role name. A typed claim makes that count mechanical
and makes false claims countable at the same time. So the channel serves three
callers - this rung, the self-outing re-score, and the adjudicator's typed-fact
surface - which is the argument for building it once rather than three times.

---

## 4. The ceiling estimator - the ML that belongs here

The hand rule reads 94.3% at the hunt against the model's 48.3%, and `captured`
is 24.5%. The fair objection is that 94.3% is a rule someone chose. Close it with
a fit, under §0's protocol:

- Features from the public record only, so gate #1 holds at the featuriser: vote
  agreement conditioned on taint, rejection count, mission membership, fails
  charged, plus the hunter's own night knowledge.
- Logistic regression, hand-rolled over the arrays already in the scorer. No new
  dependency.
- **Train on self-play, test on the pinned 29.** Leave-one-run-out across the
  three runs as a second reading, reported beside it rather than instead of it.

What the answer means either way: near 94% says the hand rule was already at the
ceiling and the ladder is finished at the hunt. Materially above says the model
captured less than 24.5% and the published figure needs a correction, which is
worth knowing before it is published rather than after.

---

## 5. Traps

- **A stronger scripted seer changes the corpus.** Scoring a new rule against the
  existing 29 hunts is free. A new arm that *produces* games produces a different
  corpus, and a figure quoted across the two answers two questions - the same
  shape as the S10 re-baselining.
- **Do not re-specify a gate with a rung.** S6's criterion is reported in its own
  words whatever any of this says.
- **`over_sabotage` is conditioned.** Per §3 of the modelling review, a double
  fail on the mission carrying evil's third fail is costless and is not an
  anti-coordination failure. Any rung scored against that count uses the
  conditioned version.
- **Old records carry no field a new rung invents.** Absence is not a
  measurement, and a re-scored pre-S9 run must not be quoted for `recovered`.

## 6. What this does not license

It does not make cabal's numbers comparable to anyone else's, it does not rescue
gate #3a, and it does not claim a stronger bot says anything about the models. A
rule beating a model is a finding about the ladder's shape, not about the ceiling
of either. `arXiv:2310.05036` reports rule-based agents at 38.2% against LLM
agents at 22.2% for the good side; the cabal replication of that shape is in
`docs/reference-policies.md` §The control ladder and it is a shape, not a
comparison.
