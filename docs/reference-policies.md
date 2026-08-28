# Reference policies - what a number is scored AGAINST

Written 2026-08-27, after that day's literature pass. Design note; nothing here is
built. **Read before implementing any of it, and before quoting a gate number as a
fraction of anything.**

## The problem: a floor is not a denominator

Every gate in this repo is scored against **chance**. Gate #3b compares the
hunter to `1/len(legal_targets)`; gate #3a compares good's approval of clean
teams to its approval of tainted ones. Chance is a floor - it says the model did
better than nothing. It cannot say the model did well, because nothing in the
repo knows what "well" would have been.

That gap is why the S1 verdict had to be so careful. "+9pp per saboteur" is
unanchored: it could be 90% of the available signal or 9% of it, and the number
reads identically either way.

The 2026 social-deduction work supplies the missing instrument, though not for
this purpose. `arXiv:2506.17788` externalizes belief inference to a structured
probabilistic model and uses the LLM only for language; `arXiv:2511.06175`
(CSP4SDG) does the constraint-propagation version. Their goal is to WIN. Ours is
to **measure**, and the same machinery is a better instrument than it is a player.

## The build: exhaustive enumeration, because this game is small

`SETUP_5.roles` is `(SEER, WATCHER, LOYALIST, MIMIC, HUNTER)` - five distinct
roles over five seats, so **120 possible assignments**. Enumerable in full. No
sampling, no approximation, no belief-propagation, no GPU. The whole instrument is
a filter over 120 candidates.

**The filter takes exactly what a seat is entitled to**, which is what makes this
fit rather than fight the architecture:

- `ref.entitled_knowledge(seat)` - the seat's own night knowledge, as a hard
  constraint on which assignments are possible.
- `ref.public_events` - the record every seat has.

So it is a `SolverPolicy` with the same `act(ref, seat)` signature as
`RandomPolicy` and `LLMPolicy`, droppable into the same `policies` dict, and it
passes gate #1 **by construction** - it is incapable of consulting anything the
referee did not render to that seat.

### What actually constrains the set

Keep two categories apart; conflating them is how this instrument would start
lying.

**Hard (mechanical) constraints - certain, and rules-derived:**
- The role multiset is fixed, so exactly two seats are evil.
- A mission returning *k* fails had **at least *k* evil seats on that team**,
  because `validate_card` refuses a good seat playing fail. This is the strong
  one, and on a 2-fail mission it is very strong.
- The seat's own night knowledge.
- Hunt legality (`legal_hunt_targets`) - a seat the night named as an ally
  cannot be the seer.

**Soft (behavioural) evidence - votes and speech.** These carry real information
and are NOT usable as hard constraints, because reading them requires a model of
how seats play. A seat voting to approve a tainted team is legal and, per the
audit's own finding, sometimes correct play by a concealing seer.

**The solver uses hard constraints only.** That is deliberate and it is the whole
design.

## Why hard-constraints-only is the point, not a limitation

A mechanical solver computes what is derivable **without listening to anyone**. So
its score is not the ceiling - it is the *no-discussion reference*. And then:

> **LLM performance minus mechanical-solver performance = what the table talk was
> worth.**

That is the quantity this repo has wanted since its first measurement and has
never had. §Measured has carried "votes are ALREADY independent, just uninformed"
since 2026-08-25 without any way to say how uninformed, or how informed they could
have been. This says it.

It also fixes the framing problem gates #2 and #3 have - they decay with model
releases, since each measures whichever checkpoint was armed: **"captured X% of the derivable signal"** is far
more stable across checkpoints than a raw rate, because the denominator is a
property of the game rather than of the model.

## Two products, one instrument

1. **A reference policy.** Seat it as an arm. `--arm solver` against `--arm llm`
   on the same seeds is a controlled comparison with no prompt variable at all.
2. **Derivable-bits, per decision.** At each hunt: how many assignments remain
   consistent, and what is the entropy over "which seat is the seer"? If the
   surviving set is large and flat, the record carries little about the seer and a
   hunter near chance is *playing correctly*. If it is sharply peaked, a hunter at
   chance is failing to read a record that told it the answer.

**Careful with the second one - it is a lower bound on available information, not
a measure of the task's difficulty.** A near-zero mechanical reading does NOT show
gate #3b is impossible; it shows the signal is not in the mechanics, which means
all of it must come from behaviour - and that is exactly what gate #3 claims to
measure. So this sharpens the gate rather than retiring it. A doc that said
otherwise would be the instrument overclaiming in its first week.

## Spec - pinned 2026-08-27, before any record was scored

Written and committed BEFORE the instrument was pointed at anything, because a
denominator chosen with the numerator in view is not a denominator. What had been
seen at pin time: `hunt6a`'s progress lines, which carry per-game WINNERS and
fallback rates and nothing about hunts. `hunt6a.json.jsonl` was unopened, and the
corpus below deliberately excludes both S6 arms.

**Candidate space.** All `5!` = 120 bijections of `SETUP_5.roles` onto seats
`0..4`.

**Hard constraints, and this is the closed list:**

1. *Own role.* The candidate seats the observer's actual role at the observer's
   seat.
2. *Own night knowledge, by equality.* `entitled_knowledge(seat)` computed under
   the candidate must equal, as an ordered tuple, what the seat was actually told.
   Equality, not containment: a seat knows exactly what the night said, so a
   candidate that would have told it something else is impossible. This subsumes
   hunt legality - `legal_hunt_targets` is derived from `known_allies`, which is
   the same knowledge.

   **Correction, same day: equality and containment are the same filter here, and
   the first draft of this line implied otherwise.** How many reveals a role
   receives is fixed by the role multiset rather than by the permutation, so a
   candidate's reveal set can never be a strict superset of the observed one, and
   the choice is unobservable in every shipped setup. It was caught by
   mutation-checking the test that claimed to prove the difference - the mutant
   survived. Equality is still what is written, because it states the epistemics
   correctly and stays right for a variant that varies the count, which `lurker`
   and `stray` are queued to do. The test now asserts the *equivalence* over all
   120 deals, which is a claim that can fail.
3. *Mission arithmetic.* For every COMPLETED mission with team `T` returning `k`
   fails, `|T ∩ evil(candidate)| >= k`. Lower bound only: `validate_card` stops a
   good seat failing, and nothing stops an evil seat playing success - the audit
   found both, so there is no upper bound to be had.

Nothing else. Votes, speech, notebooks, `five_rejects`, and who led are all
excluded, and the exclusion is §The build, not an omission.

**No second knowledge model.** Constraint 2 is evaluated by constructing a
`CabalReferee` shell over the candidate assignment and calling the referee's own
`entitled_knowledge`. The alternative - reimplementing the night inside the solver
- is the failure `ROLES_BY_KEY` was introduced against and the one the decision
audit hit: a checker that invents a role model reports a confident wrong answer.

**Statistics, defined here so they cannot be redefined later.** All are computed
at the hunt, over the survivors of the three constraints applied from the
HUNTER's seat.

- `survivors` - how many of the 120 remain.
- `H_post` - Shannon entropy in bits of the posterior over "which seat is the
  seer", the posterior being uniform over survivors.
- `H_prior` - `log2(len(legal_hunt_targets(hunter)))`. This is the gate #3b
  baseline written as entropy, so the two are the same statement.
- `bits_gained` = `H_prior - H_post`. Zero means the record mechanically said
  nothing the hunter did not already know from the night.
- `solver_accuracy` - the posterior mass the argmax rule puts on the true seer,
  tie-averaged (`1/ties` when the true seer is among the argmax set, else 0).
  Tie-averaged rather than tie-broken so the number does not carry tiebreak luck.
- `captured` = `(llm_rate - chance) / (solver_accuracy - chance)`, chance being
  the mean `1/len(legal_hunt_targets)`. **It may exceed 1, and that is a
  reading, not an error**: the denominator is a lower bound on available
  information, so above 1 says the hunter used behavioural signal the solver
  refuses to look at. Reported undefined when the denominator is within noise of
  zero, never clamped.

**Corpus, fixed now:** `hunt20-q36`, `hunt20b`, `hunt20c` - **three** distinct
20-game runs, 60 games, 29 hunts. S6's arms are excluded and scored separately when
they land.

*Corrected within the hour of pinning: the first version named `hunt20d` as a
fourth run. It is a byte-identical re-run of `hunt20c` at the same seed
(`docs/reproducibility.md`), so pooling it would have tightened every interval
while adding no evidence and nothing in the output would have said so. The scorer
now fingerprints games and excludes repeats itself, because the file list is
exactly where this mistake is easy to make twice.*

## Results - 2026-08-27, the pinned corpus

Reproduce with `python -m eval.derivable eval/records/hunt20{-q36,b,c}.json.jsonl
--pooled`. All `qwen36-35b-a3b-iq3`, 60 games, pooled fallback rate 1.0%.

### The hunt: the denominator is zero, and that is a theorem

`bits_gained` is **0.000 on all 29 hunts**, max 0.000. It could not have been
anything else: `test_solver.py` proves by exhaustion over 192,000 deal-and-history
combinations that the hunter derives nothing mechanically in `SETUP_5`. The hunter
already holds the evil placement exactly - itself, plus the ally the night named -
and mission arithmetic constrains evil placement and nothing else, so no hard
constraint separates seer from watcher from loyalist.

So the corpus run of this section is an **instrument control**, not a finding: a
non-zero would mean the offline path had drifted from the proof, and the scorer
says so in its own output.

| | pooled, 29 hunts |
|---|---|
| mechanical hunter | 0.333 (= chance, necessarily) |
| the model | 0.483 (14/29), 95% Wilson [0.314, 0.656] |
| `captured` vs the mechanical arm | **undefined - that denominator is zero** |

**Superseded the same day, and this is where to read on.** "Undefined" was correct
about the *mechanical* denominator and it is not the end of the sentence. The
heuristic rung, built hours later, supplies a BEHAVIOURAL denominator on the same
29 hunts - and it is large. See §The control ladder below: `captured` is **24.5%**,
not undefined. The mechanical zero is what makes that number mean something,
because it says all 24.5 points of it are behavioural.

**What this does to gate #3b.** The gate is unchanged and S6's pre-committed
criterion is untouched. What changes is the reading: a hunter above `1/3` is not
"partly mechanical, partly behavioural" and cannot be. It is reading behaviour,
necessarily, because there is nothing else to read. That is the flat case this doc
anticipated, now stated as a proof rather than a hope, and it sharpens the gate.

### The vote: the un-entitled good seats are not reading the record

Approval rate by what the record had **proved** about the team, to that seat, at
that moment. Stratified by the night's gift, never pooled.

| role | provably clean | record unsure | provably tainted | clean - tainted |
|---|---|---|---|---|
| loyalist | 72.4% (n=29) | 75.5% (n=265) | **69.4% (n=108)** | **+3.0%** |
| watcher | 76.9% (n=26) | 61.6% (n=224) | 60.5% (n=152) | +16.4% |
| seer | 94.6% (n=147) | - (n=0) | 12.2% (n=255) | +82.4% |

The same thing as a mean gap, bootstrapped over games because votes inside one
share a deal:

| role | mean derivable taint on approved | on rejected | gap [95%] |
|---|---|---|---|
| loyalist | 0.724 | 0.765 | +0.040 [**-0.041**, +0.115] |
| watcher | 0.728 | 0.764 | +0.036 [**-0.013**, +0.089] |
| seer | 0.182 | 0.966 | +0.783 [+0.723, +0.840] |

**A blind seat approves a provably tainted team 69.4% of the time**, three points
below its rate on a provably clean one, and its gap interval spans zero at 402
votes over 60 games. The watcher moves 16 points. The seer moves 82, and that is
**entitlement, not reading**: it was handed both evils at deal time, which is why
its row has no unsure cell at all.

So the discrimination that a pooled gate #3a number would report is carried by the
seat that was told the answer. This is not a contradiction of the `+8.82%/+9.00%`
blind-taint rows in `docs/measurements.md` §Measured - those score response to **actual**
taint, and this scores response to **derivable** taint. Read together they say
something sharper than either: whatever the blind seats are responding to, it is
not the mechanically derivable part of the record, so it is behavioural signal or
it is correlation with actual taint that the seat could not have derived.

**This does not re-specify gate #3a and must not be used to.** S1 abandoned 3a on
sample grounds and that verdict stands in its own words. What the denominator adds
is that the un-entitled strata were measured, well-powered, against what was
provable - and read flat.

### The other number worth keeping

`end-of-game bits` - how much the whole public record told a good seat beyond the
night - pooled to **0.732 bits mean over 180 good seats, 79 of them above zero**.
So the record is not silent; it carries derivable content in a bit under half the
good seats, and the blind ones are not spending it.

## The discipline constraint - additive, never substitutive

**This must not re-specify a gate after results are in view.** S6's pre-committed
criterion is a Wilson floor on the hunter rate against the S3-derived baseline,
and it stays reported exactly as pre-committed, in those words, whatever the
solver says. The solver adds a denominator BESIDE it.

Swapping the gate to the new statistic because the new statistic reads better is
the `hunt20b` error wearing a fourth hat, and this repo has now voided one verdict
over precisely that. If the solver's statistic is to become a gate, it is
pre-committed before a run like every other gate.

## The control ladder - BUILT 2026-08-27, and the model loses to it

Was: `random -> LLM`, nothing in between, so the only thing a gate could say was
"better than noise". Now `games/cabal/heuristic.py`, ~60 lines of tallies over the
public record, run by `python -m eval.ladder`.

It is deliberately **not** the solver, and the difference is why the ladder needs
both. The solver enumerates and refuses votes because reading them needs a model of
how seats play. The heuristic does no enumeration at all and reads votes precisely
because that is where a cheap rule gets leverage. The mechanical zero above is what
forces the split: a policy that refuses behaviour *cannot* hunt above chance here,
so the middle rung had to be built out of the half the solver throws away.

### The hunt, on the corpus the models produced - 29 hunts, no new games

| who | accuracy | 95% Wilson |
|---|---|---|
| chance | 33.3% | - |
| **the model itself** | **48.3%** (14/29) | [31%, 66%] |
| rejections only (the dumb control) | 77.6% (22.50/29) | [58%, 88%] |
| **votes, taint-conditioned** | **94.3%** (27.33/29) | [78%, 98%] |

`captured = (48.3 - 33.3) / (94.3 - 33.3) = ` **24.5%**. Against the dumb control,
33.8%. The model captured about a quarter of what sixty lines extract from the
record it produced itself - and because the mechanical denominator is zero, every
one of those points is behavioural on both sides of the ratio.

This is AvalonBench's finding replicated rather than invented: their rule-based
bots beat their LLM agents 38.2% to 22.2% for the good side, and here a rule beats
the model 94.3% to 48.3% at the hunt.

**The dumb control is what makes it legible.** A rule that ignores the hunter's
night knowledge entirely and simply names whoever rejected most still hits 77.6%.
So the tell is not subtle: *the seer gives itself away by being cautious*, and
conditioning on taint only adds seventeen points on top. Consistent across all
three runs - 94.4% / 89.4% / 100.0%.

It also joins up with the vote finding above. The seer's approval runs 94.6% on
provably clean teams against 12.2% on provably tainted ones, which is exactly the
signature a vote-reading rule needs, and no seat at the table spent it.

### The seated arms - one side swapped at a time

| arm | good wins | hunter |
|---|---|---|
| random / random (the floor) | 40.3% [35%, 46%] | 50/171 = 29.2% |
| **heuristic good / random evil** | **49.7% [44%, 55%]** | 88/237 = 37.1% |
| random good / heuristic evil | 0.0% [0%, 1%] | no hunts reached |
| heuristic / heuristic | 0.3% | 207/208 = 99.5% **(artifact)** |

Only the middle two are controlled: swapping both sides changes good and evil at
once, and the win rate then measures neither. The all-heuristic hunter figure is
**not a result** - a deterministic seer's votes track taint exactly, so the rule is
reading its own twin's tell. It is printed, labelled, because it is what a careless
"heuristic vs random" reading would produce, and because it is the exact trap the
offline half avoids by scoring against records the rule never played.

The always-fail evil rule dominates: it wins essentially every game against a
random good side. That is a statement about a non-coordinating good side, not a
finding about the model, and it is why the evil arm is not a usable rung.

### What this does NOT license

It does not re-specify gate #3b, and S6's pre-committed criterion stays reported in
its own words. It is a denominator printed beside the gate, which is the whole
discipline constraint above. What it changes is what a reader may conclude from a
hunter at 48%: not "above chance, therefore reading the table", but "capturing
about a quarter of the behavioural signal its own table left lying in the record".

## Cost, and why it can go first

CPU only. ~150-250 lines plus tests for the solver, ~60 for the heuristic. It does
**not** compete with S2's GPU claim, and it can be scored against the
`hunt20b`/`hunt20c` records that already exist - so every number in §Measured
acquires a denominator with **no new games run**.

That makes it the natural companion to the S6 verdict session rather than a
separate program: same session, no GPU, and it re-reads the whole history.

## What this does not do

- It does not make cabal's numbers comparable to AvalonBench's. Different setup,
  different metric; the win-rate axis is still not the one to compete on.
- It does not rescue gate #3a. The S1 verdict turned on the unconfounded cell
  accruing at 0.3-0.4 votes per game, and a denominator does not create samples.
  It does let 3a's confounded number be reported as a fraction, which is a more
  honest presentation of the same evidence.
- It says nothing about deception (gate #2). A solver has no theory of the other
  seats lying; that is the soft half it deliberately refuses.
