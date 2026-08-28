# The DURF rung - a rules kernel under a model adjudicator

Written 2026-08-27, unmeasured, from a design read of `core/observability.py`,
`games/cabal/audit.py`, `docs/action-channel.md` and `docs/faction-heartbeat.md`.
Same job as both of those: nothing here is a decision, it is here so the cheap
moves stay cheap.

**What this scopes.** `queue.md` has carried "5e / a rules-lite RPG" as the
endgame rung with no statement of what the cheap version is. This names one: a
single dungeon session of DURF, a deterministic kernel underneath, a model in the
adjudicator seat, and one number nobody in the neighbouring literature has
produced. It is the first rung where `referee.py:6` inverts - judgment IS the
referee - and therefore the first that tests the actual product claim.

## Why this ruleset

**DURF is the smallest real system that ships legally.** ~40-50 pages, d20,
three attributes, no class tree, no spell list needed for a first session. Its
whole ruleset is smaller than four Blood on the Clocktower characters'
interaction surface, which is what `queue.md` scoped that spike down to anyway.
The adjudicator's failure therefore arrives isolated from rules complexity, which
is the only reason to prefer a small system over an interesting one.

**Licence, and it is a build requirement rather than a footnote.** DURF by Emiel
Boven is CC BY 4.0: share and adapt for any purpose with credit. So the rules
text can ship in-tree, in its own data directory, carrying its own LICENSE and an
attribution line naming the author. Root LICENSE stays the unmodified MIT text so
the SPDX detector keeps returning `MIT`; a root NOTICE names the exception. The
engine does not become CC BY by sitting next to it.

**The comparative read that picked DURF out of nine candidates is off-repo** -
the licence tiering of the others, and what shipping two of them would cost,
names third parties and stops at the working notes. `CLAUDE.local.md` has the
path. Nothing in this file needs it: DURF's own licence is stated above because
attribution is owed, not because a comparison is being made here.

**Version pin, because a kernel without one is not reproducible.** The table
below is **DURF version 2.2 (2021)**, verified line by line against Boven's own
source text - the public Google Doc he links from the itch page as "source text",
exported as plain text and read in full. Not a summary, not the carrd reference,
not the PDF (same content, worse to quote). Pin that version in the game module.

**The pin, addressable**, because a pin nobody can re-fetch is a pin you have to
take on trust - and the 2026-08-27 pass found two rules missing from the table
below rather than wrong in it, which is a failure only a re-read catches:

```
https://docs.google.com/document/d/16mu9tmLyxPFvAsYonFaYU14btvYo_aK3JVr5HLWwKzk/
```

Append `/export?format=txt` for the plain-text export this table and the fixture
were verified against; the document's own first line reads `VERSION 2.2 - 2021`,
which is the string to check before trusting a re-read. Boven links it from
`emielboven.itch.io/durf` under the "Google Doc Source Text" devlog, so the id
above is a convenience, not the authority - if it ever fails to resolve, the itch
page is where the current link lives. The doc is a **living** artifact under the
author's control: **check that version line every time**, because a doc that has
moved past 2.2 silently re-baselines the fixture, which is the same failure the
Expanded migration trigger below exists to prevent.

**DURF Expanded is the successor and it must not be built on yet - the reason is
the fixture, not the page count.** *(read - one trade-news piece; the draft
itself is Patreon-gated and was NOT opened, and the campaign's own figures came
from a search synthesis, so none are quoted here.)* It is a funded Kickstarter in
fulfilment: a ~200-page hardcover against 2.2's ~48, whose current draft is
described as **overhauled rules and procedures** and which its own coverage says
will keep being updated as the book is finalised. So the kernel is in motion.

The expensive artifact in this rung is not the kernel, it is the labelled
declaration set below. A kernel edit re-baselines it, and a fixture labelled
against a superseded draft still produces numbers - which is the worst failure
shape this repo knows. **Migrate only when Expanded ships stable, out of draft,
with its CC variant confirmed**, then re-verify the table against it and re-pin.

**That licence check is a gate, not a formality.** Expanded is reported as
Creative Commons with an "open license" and **no variant named**. DURF 2.2 is CC
BY, and CC BY is the whole reason this ruleset was preferred over the richer
candidates - a non-commercial or share-alike successor would not carry that
argument, and would land in the quarantine the off-repo ledger describes rather
than in-tree. Confirm the variant from Boven's own text before treating the
migration as available.

**A first pass built this table from a summary page and got three things wrong.**
The armour mechanic was inverted, the tie rules were merged into one that does not
exist, and Breaks were described as adding. All three are corrected below; the
episode is the argument for the pin.

**A second pass, 2026-08-27, added two rows this table was missing** - the
per-item slot costs, and the once-per-day casting limit that binds NPC casters
only. Both were read from the same source text. Neither was wrong here; both were
absent, and the fixture was resting labels on them anyway, which is the failure
mode a pin does not catch on its own. `games/durf/fixtures/README.md` records what
that cost.

## The kernel *(verified against DURF 2.2 source text, 2026-08-27)*

| mechanism | rule |
|---|---|
| attributes | STR / DEX / WIL, each d3 at creation, **max 8** by advancement |
| action roll | d20 + attribute, **over 15 is a success**. Saves are action rolls |
| opposed roll | both roll, **highest wins**; NPCs add **Skill** instead of an attribute |
| ties | **three different rules** - general opposed: GM decides; close combat: **attacker wins**; initiative: **PCs go first** |
| buffs / breaks | cancel first, then roll a d6 each; **highest Buff added, highest Break subtracted**. **NPCs never roll them** |
| pushing | pre-roll, needs an empty slot: take **Stress** to gain a **Buff**. Repeatable while slots last. NPCs cannot push |
| weapons | 2 dmg improvised, 3 dagger/bow, 4 sword/crossbow, 5 greatsword/pistol; bigger weapons cost slots |
| armour | **a depleting pool, not flat reduction** - Light 3 / Medium 5 / Heavy 7. Damage drains Armor points first, the remainder lands as Wounds |
| shields | reduce incoming damage by 1, **never below 1** |
| worn weapons | natural **1** on an attack drops that weapon to **1 dmg** until repaired |
| critical | natural **20** on an attack deals **double** weapon damage even if the opposed roll is lost. Ranged **defenders** cannot crit |
| wounds | on receiving Wounds, roll **all** HD (d6 each); **result <= accumulated Wounds means death**. 0 HD dies to any Wound |
| inventory | slots = **10 + STR**. **Most items take one slot**; medium armour **+1**, heavy armour **+2**, two-handed weapons **+1 or +2**. Each Stress occupies one; **Wounds and GP occupy none**. "A PC cannot carry more items or Stress than they have inventory slots" |
| morale | NPCs carry **ML**; roll **2d6**, **higher than ML** means flee or parley |
| NPC stats | **Skill** (one value, max 14), HD, Armor, ML. NPCs take no Stress |
| clock | round 10s, turn 10min, watch 4h. **d6 per turn and per watch; on a 1, a random encounter** |
| rest | a day safe clears **Wounds, Stress, Armor and worn weapons**. In the field, 1 Supply restores 2 Armor or 1 weapon, taking a turn |
| spellcasting | WIL roll; success casts and costs 1 Stress, **failure costs neither**; natural 1 hits the Blunders table; a full turn casts automatically. Requires an empty slot, a free hand and the ability to speak. **"Unless otherwise stated, NPC spellcasters can only cast each of their spells once each day" - NPCs only; a PC is bounded by slots** |
| advancement | 1000 x current HD in XP; +1 attribute or a new spell; **retire at 13 HD**. 1 GP = 1 XP, plus 25 XP per defeated NPC HD |

Everything in that table is arithmetic. That is the point: it is all kernel, none
of it is discretion, and a model never touches any of it.

**Attribution, required by the licence and satisfied here:** DURF is written and
illustrated by Emiel Boven, edited by Ava Islam, CC BY 4.0.

## What is actually secret here, and why the topology is new

**cabal and changeling hide secrets that belong to seats. DURF hides secrets that
belong to the world.** Room contents before entry, whether the chest is trapped,
a monster's remaining Wounds and its damage value, what the reaction roll said, an
NPC's intent, the map past line of sight. None of those is any seat's secret. No
seat owns them and every seat is equally un-entitled to them.

Three consequences, and the second is the one that matters:

- **Entitlement is uniform across seats.** Every player seat has identical
  entitlement at any instant, so the peer-to-peer boundary cabal audits does not
  exist here. Gate #1 collapses to one boundary: referee -> the party.
- **That is structurally weaker and operationally far riskier.** cabal's referee
  is deterministic, so its private bytes are a fixed set of strings and naive
  matching is sound. A model adjudicator authors prose, and `docs/action-channel.md`
  already names the failure: "the innkeeper looks nervous" leaks that he is the
  cultist with zero substring overlap and the audit reads clean. The weaker
  boundary is guarded by the stronger adversary.
- **A seat's own state is public at this rung.** Wounds, slots and the HD death
  check are open at a real table, so `self_is_secret` stays off and there is no
  changeling-shaped self-belief problem to solve. Do not import one.

## The entitlement model breaks, and this is the promotion evidence

`find_leaks` takes `secret_terms: dict[int, list[str]]` keyed by **seat** and
`entitled: set[int]` of **seats**. There is no seat to key a trapped chest to.
`SeatView.knowledge` has the same shape: `Knowledge(seat, label)` is a statement
about a seat.

**The generalisation is fact-keyed entitlement, and seat-keyed is a special case
of it** - "seat 3's role" is just one fact among many. So the promotion does not
fork the primitive, it widens the key:

- `secret_terms: dict[FactId, list[str]]`, `entitled: set[FactId]`.
- `Knowledge(fact_id, label)`, with today's per-seat reveals expressed as
  `fact_id = ("role", seat)`.

**Per the `core/` invariant, promote on evidence that a second game needs it -
and this is the evidence, so it is written down rather than acted on.** cabal and
changeling are both seat-keyed and neither needs this; rewriting the spine under
a code freeze to serve an unbuilt rung is exactly the hardening
`docs/action-channel.md` warns about. Build the fact-keyed version inside
`games/durf/` first. It moves to `core/` when a second game wants it, not before.

## The kernel / adjudicator line, drawn where it can be graded

**Kernel** owns everything in the mechanics table, raises on illegal, and is the
only thing that touches state. **Adjudicator** owns five decisions, and nothing
else:

1. Does this declaration require a roll at all?
2. Which attribute governs it?
3. Buff, break, or neither?
4. **Has something shocked the NPCs enough to warrant a morale roll?**
5. What is the fictional consequence of the kernel's result?

**Decision 4 was found by reading the rules rather than by design, and it is the
best-shaped of the five.** DURF hands the GM a morale mechanic with a fully
specified roll and an entirely unspecified trigger - "when something manages to
shock the NPCs (they meet more resistance than expected, their leader is killed
etc.)". The roll is kernel; deciding a moment qualifies is pure discretion, it
recurs several times a session, and it is gradable against a labelled fixture in
exactly the False Pass / False Check shape. Any rung built here should carry it.

Envelope is the one `docs/action-channel.md` already specifies -
`{"think":..., "narrate":..., "calls":[...]}` - validated by the kernel, refused
with the kernel's own error text, retried against the same seat, counted on
fallback. That is `LLMPolicy`'s existing loop unchanged, which is the whole reason
the sketch is cheap.

**Decisions 1, 2 and 4 are gradable against the rules text; 5 is not.** Do not
pretend otherwise and do not build a judge for 5. The measurement below scores 1,
2 and 4, and reports 5 as prose in the transcript.

## The number this rung produces

**CoC-Seduce (arXiv:2607.02802) measured adjudication failure as directional and
the direction is the finding: mean False Pass 9.58%, mean False Check 0.08%.**
Models grant unearned success and essentially never over-demand rolls. Their task
was single-turn, stateless, binary-output, with referee-authored ground truth
handed to the model in the prompt. **Every property parlor adds makes it harder,
so their 9.58% is a floor and this rung's job is to measure how far above it a
stateful multi-turn adjudicator sits.** Nobody has produced that number.

Report three quantities, each with the fallback rate beside it per the standing
invariant, and void above 10%:

- **False Pass** - the adjudicator resolved a declaration with no roll where the
  rules require one, or applied a buff the fiction does not support.
- **False Check** - it demanded a roll the rules do not require.
- **Refusal** - it declined to rule. **A third outcome, counted, never dropped.**
  CoC-Seduce silently excluded 35 refusals and disclosed it in a caption; this
  repo names it in the denominator or not at all.

**The instrument is a hand-labelled declaration set, and it must be labelled
before any model runs.** Labelling after seeing model output is the
promote-a-statistic failure `docs/reference-policies.md` exists to prevent.

**BUILT 2026-08-27, unrun: `games/durf/fixtures/`.** A fixed four-room scenario
with three fully-statted PCs, 48 declarations labelled for decisions 1 and 2, and
12 events labelled for decision 4, every label carrying the rule it rests on.
Balance is counted rather than asserted - 22 no-roll against 26 roll; morale
splits 6/6. **The degenerate baselines were restated 2026-08-27** after a
re-derivation: the "never-roll 46%" first recorded here pooled the six refusal
traps into the no-roll bucket, and the honest pair is always-roll **61.9%** /
never-roll **38.1%** over the 42 declarations that admit a roll answer (54.2% /
33.3% over all 48). Always-roll is the bar this rung's model is closest to, so
that correction raises it by ~8pp. The fixture README carries both rows. Eight declarations
are Pseudo-Logic, and one of those eight argues a claim that is **correct**, as
the control against a model that reflexively rejects any argued case. Read that
directory's README before quoting any number from it.

**Two instrument controls, both cheap, both required before the number means
anything.** A floor set of declarations whose ruling is unambiguous in the rules
text (an attack is an opposed roll; walking across an empty room is no roll) - a
model failing those is not measuring adjudication. And a random-adjudicator arm,
the same shape as cabal's `--arm random`, so the reported rates have a chance
baseline to sit against.

## Pre-committed criteria

Written before any run, per house rule.

- **Gate #1 holds or the run is void.** The audit raises on any world fact
  appearing in a seat's context that the adjudicator did not declare. Not a rate.
- **The rung is worth continuing if** False Pass is measurable and separable from
  fallback - that is, the model rules often enough that its errors are rulings
  rather than parse failures. Concretely: fallback under 10% and refusal under 10%
  on the labelled set.
- **The rung is a negative result if** fallback or refusal dominates. That is a
  publishable finding about the action channel, not a failed run, and it is the
  outcome `docs/action-channel.md`'s free-text-JSON choice makes most likely on
  weak backends.
- **No claim about play quality.** Whether the session was fun, coherent or
  well-narrated is not measured and must not be asserted from a transcript.
- **The floor tier's bar, written 2026-08-28 before any model had run, and
  DERIVED rather than picked.** This section asked for a floor set and called its
  bar "near-ceiling", which is not a number and would have been chosen with the
  first run's output in view. It is now: floor-tier decision-1 accuracy must have
  a **Wilson floor clearing the better of the two degenerate baselines computed on
  the floor tier itself** (`eval/durf_score.py`, `_floor_bar`). Derived from the
  labels, so a fixture edit moves the bar with them rather than leaving a stale
  literal behind, and graded on the interval floor like every other verdict here.
  Both degenerate arms fail it by construction, which is the check that it means
  anything.

## The instrument, built 2026-08-28 - what it scores and what it does NOT

`eval/durf_score.py` asks one arm to rule on all 48 declarations and all 12 morale
events and reports False Pass, False Check and Refusal beside the run's fallback
rate, voided above the same 10% both games void on. `games/durf/adjudicate.py` is
the seat: the envelope, the parser, and `LLMPolicy`'s refuse-and-retell loop.
Four arms - `always-roll`, `never-roll`, `random`, `llm`.

**Three things it does not do, stated here because each is a claim someone would
otherwise read into a number it prints.**

- **It does not exercise gate #1.** There is no player seat, so there is nothing
  for a world fact to leak TO; the adjudicator is handed the referee's whole view,
  hidden room contents included, because that is what a referee sees. The
  entitlement audit arrives with the session engine, and no rate from this
  instrument may be quoted about the leak boundary.
- **No kernel executes.** Nothing rolls, nothing takes damage, no state moves. The
  fixture is 60 independent items against one fixed scenario, which is why the
  interval is Wilson and there is no game-clustered bootstrap - the unit is a
  declaration, and a declaration is not a cluster.
- **Decision 5 is recorded and never scored.** The envelope asks for `narrate` and
  the record keeps it. There is no fixture for it and no judge is built for one.

**Three refusals share the word and the scorer keeps them apart**, because pooling
any two reports a model's silence as a ruling: `illegal` is a RULING and the
correct answer to all six traps; `decline` is the refusal to rule, counted in the
denominator per the criterion above; a reply nothing parses out of is a fallback,
played by the random adjudicator and carried by the fallback rate. A fourth count
sits beside them - **over-refusal**, `illegal` on a declaration the rules permit -
because without it an arm that refused everything would post a perfect False Pass
and a perfect False Check.

## First run, 2026-08-28 - VOID on the instrument control, and the shape that voided it is the finding

`qwen36-35b-a3b-iq3` local, seed 5000, `--no-thinking`, all 60 items, 166s.
Records `eval/records/durf-q36.json` + `.jsonl`; recompute with
`py -3 -m eval.durf_score --arm llm --backend local --model qwen36-35b-a3b-iq3
--no-thinking --seed 5000`.

**The verdict first: VOID.** Floor-tier accuracy **38.24%** [23.90%, 54.96%]
against the derived bar of **55.88%** - the interval does not clear a constant
policy on the declarations the rules answer unambiguously, so by the criterion
committed above this model was not measured on adjudication and no rate below is
a measurement of it. Decision 1 over the 42 came in at **33.33%** [21.01%,
48.45%], which is below the never-roll baseline of 38.10%, let alone always-roll's
61.90%.

**The action channel is not what failed, and that is the first real result.**
This file predicted that free-text JSON's most likely negative outcome on a weak
backend was fallback or refusal dominating. Fallback was **0/60**. Nothing was
sent back by the parser or the rules on any item; every reply was a legal envelope
first time. Whatever is wrong here, it is not the envelope.

**What voided it was refusal, in two distinct shapes.**

- **A precondition applied as a universal gate.** 13 of the 28 non-correct
  declarations cite inventory slots, and 9 of the 12 over-refusals do. Vesh has
  zero free slots, and the adjudicator ruled *illegal* on his dropping a coil of
  rope (dropping frees a slot), on his jumping a chasm, and on his holding a door.
  It has the rule, and it applies it to declarations the rule does not reach. This
  is not a False Pass and it is not in CoC-Seduce's pair - **the direction is
  reversed**: their models grant unearned success, this one refuses earned
  attempts.
- **`decline` used as "I reject your argument".** 5 of the 8 Pseudo-Logic
  declarations were declined and 2 more ruled illegal, with only one ruled. The
  reasoning on those is right - it names the false premise, that DURF has no
  proficiencies, that a shield never reduces below 1 - and then answers in the
  wrong channel.

**That second shape is a confound this instrument introduced, and it is stated
here rather than fixed quietly.** The envelope offers four words, and `decline`
was put there so a refusal to rule had a channel instead of arriving as a parse
failure. A model that reaches for it to reject a player's *argument* is answering
a question the vocabulary invited. So the 27.08% refusal rate is not yet readable
as "declined to rule".

**The pre-registered second arm, and what each outcome would mean** - written
before it runs, because deciding afterwards which reading the numbers support is
the failure this repo names by name. The arm is the same fixture, same seed, same
model, one variable: `decline` removed from the ruling vocabulary, leaving roll /
no_roll / illegal.

- Refusal goes to zero by construction, so the question is **where the 13 declines
  land**. If they become `illegal`, over-refusal rises past 40% and the answer is
  that the model refuses broadly and the vocabulary only changed the word - the
  finding stands as written.
- If instead decision-1 accuracy clears the always-roll baseline's interval, the
  declines were a channel artifact and this model can rule; the finding then
  becomes a fact about the envelope rather than about adjudication.
- **The slot-gate failure is untouched by the vocabulary either way**, so the
  prediction is that floor accuracy stays under the bar and the run stays VOID.
  An arm that came back passing the floor control would falsify that.

**Two numbers not to quote from this run.** The trap tier reads 6/6, which looks
like the purest instrument in the set working - but a policy that refuses broadly
catches every trap for the wrong reason, and the over-refusal rate is what says
so. And False Pass came in at 6.25% [1.73%, 20.15%]: the interval contains
CoC-Seduce's 9.58%, so this is not a lower rate than theirs, and on a voided run
it is not a rate at all.

**Morale, decision 4, was the best-behaved of the three** - 8/12 against a
constant policy's 6/12, with 3 missed and 1 over-called. Missing a third of the
group killed in one blow, and calling one on an undead the adjudicator itself
argued is immune to morale, are both live rulings rather than refusals. Too small
a set to carry an interval that means anything (CI [39.06%, 86.19%]), and it is on
a voided run.

## Second arm and the two controls, 2026-08-28 - the prediction held, and the per-item story did not

Four runs, all `qwen36-35b-a3b-iq3` local, `--no-thinking`, 60 items each,
164-172s each. Records in `eval/records/`: `durf-q36` (seed 5000),
`durf-q36-rep` (seed 5000 again), `durf-q36-s6000` (seed 6000),
`durf-q36-nodecline` (seed 5000, `--no-decline`).

| | arm 1 | arm 2 `--no-decline` | seed 6000 control |
|---|---|---|---|
| floor tier - THE CONTROL, bar 55.88% | 38.24% [23.90, 54.96] | 44.12% [28.88, 60.55] | 38.24% [23.90, 54.96] |
| decision 1 over the 42 | 33.33% [21.01, 48.45] | **45.24%** [31.22, 60.05] | 35.71% [22.99, 50.83] |
| over-refusal | 28.57% | **38.10%** | 26.19% |
| refusal (declined to rule) | 27.08% | 0 by construction | 25.00% |
| False Pass | 6.25% [1.73, 20.15] | 18.75% [8.89, 35.31] | 15.62% [6.86, 31.75] |
| fallback | 0/60 | 0/60 | 0/60 |

**Every arm is still VOID on the floor control**, which is the prediction's third
clause and the one that mattered most: the vocabulary was never going to reach the
slot-gate failure, and it did not.

**The pre-registered prediction, graded clause by clause and not rounded toward
itself.** Where the 13 declines landed: **6 illegal, 4 no_roll, 3 roll**. The
first clause said over-refusal would rise past 40% if the declines were only a
word - it rose to **38.10%**, so the direction is right and the threshold is not
met, and the interval [25.00, 53.19] contains 40% without establishing it. The
second clause is the decisive one and it is clean: decision-1 accuracy came in at
45.24% [31.22, 60.05], **which does not clear the always-roll baseline of 61.90%**
- so the declines were not a channel artifact hiding a model that can rule. The
finding stands as the first run wrote it.

**The two controls, and the second one is the reason this section exists.**

- **Reproducibility holds exactly.** Seed 5000 run twice returned byte-identical
  answers on all 60 items, reasoning text included. `Backend.seed` reaches the
  sampler, as `docs/reproducibility.md` measured for the games.
- **A per-item story is NOT reproducible, and only the rates are.** Changing the
  seed alone moves **23 of 48 rulings**. Changing the 87 prompt bytes moves 27 of
  48 - and on the 35 declarations that never declined, where the variable has
  nothing to reach, it moves **14 of 35 against a seed change's 16 of 35**. The
  item-level churn from the variable is indistinguishable from the churn from
  noise. What survives is the aggregate: decision 1 moved 2.4pp between seeds and
  11.9pp between vocabularies, over-refusal 2.4pp against 9.5pp.
- **So do not quote an individual ruling as evidence.** The first run's writeup
  names d007 - ruling it illegal for a full-handed seat to drop a rope - as the
  clearest instance of the slot gate. It is a good illustration and it is not a
  measurement: that same declaration would plausibly come back ruled differently
  at another seed. The slot-gate finding rests on the 9-of-12 count, not on any
  one item, and the count is what to re-derive.
- **Two draws are not a spread.** One repeat pair and one seed pair are what these
  numbers are; nothing here establishes a run-to-run distribution, and the 2.4pp
  figure is one difference rather than an interval. Temperature is the untouched
  variable behind it - every run is at the 0.8 default, and an adjudicator seat
  has no particular reason to be sampled at a player's temperature. That is the
  next cheap arm and it is a measured change like any other.

## Third arm, PRE-REGISTERED 2026-08-28 - temperature, and what each outcome would mean

**Written and committed before the run, per house rule.** The arm: arm 1 exactly -
seed 5000, `decline` in the vocabulary, same model, same fixture - with
`--temperature 0.0`. One variable. Then a second run at `--seed 6000`, also at
0.0, as the arm's own instrument control.

**Why this arm rather than another.** Every run so far sits at the 0.8 default,
which is `Backend`'s value for a PLAYER seat: it exists so a table's speech
varies. A referee ruling on rules has no such reason, and the seed control above
showed the cost - **23 of 48 rulings move on a reseed alone**, i.e. the model is
close to indifferent between rulings on half the fixture, and 0.8 samples from
that indifference. Greedy decoding is the direct test of whether the churn is the
sampler or the model.

**Prediction, stated before the number exists.** The slot-gate failure is a
reasoning error rather than a sampling one, so **floor-tier accuracy stays under
the 55.88% bar and the run stays VOID**, with over-refusal in the high twenties.
What greedy should buy is stability, not correctness.

- **If floor accuracy clears the bar**, the finding inverts and it is a finding
  about this harness rather than about the model: the player-seat default was
  destroying an adjudicator that could otherwise rule, and **every number in the
  two sections above would have to be re-run at 0.0 before any of them is quoted**.
- **If the two 0.0 runs differ from each other at all**, temperature is not the
  whole story and the endpoint is nondeterministic for some other reason - which
  would also put the byte-identical seed-5000 repeat above in a different light,
  since that pair shared a seed as well as a prompt. That is the control, and it
  is the reason the arm is two runs rather than one.
- **If accuracy is flat and the two 0.0 runs agree**, the churn was the sampler,
  the aggregate findings stand as written, and the standing consequence is that
  **an adjudicator seat should not inherit a player seat's temperature** - a
  default worth changing on evidence rather than on taste.

## The temperature arm, read 2026-08-28 - the prediction held where it mattered and missed one clause

Records `eval/records/durf-q36-t0` (seed 5000) and `durf-q36-t0-s6000`, both
`--temperature 0.0`, 161s and 162s.

| | arm 1, t=0.8 | seed 6000, t=0.8 | **t=0.0** | t=0.0, seed 6000 |
|---|---|---|---|---|
| floor tier - THE CONTROL, bar 55.88% | 38.24% | 38.24% | **50.00%** [34.07, 65.93] | 50.00% |
| decision 1 over the 42 | 33.33% | 35.71% | **42.86%** [29.12, 57.79] | 42.86% |
| over-refusal | 28.57% | 26.19% | 26.19% | 26.19% |
| refusal | 27.08% | 25.00% | 25.00% | 25.00% |
| False Pass | 6.25% | 15.62% | 3.12% [0.55, 15.74] | 3.12% |
| False Check | 6.25% | - | **0.00%** [0, 19.36] | 0.00% |
| morale | 8/12 | 9/12 | 7/12 | 7/12 |

**The control passes and it is unambiguous.** The two 0.0 runs are byte-identical
on all 60 items, reasoning text included, at different seeds. Greedy decoding is
seed-invariant here, so the endpoint is not nondeterministic for some reason
temperature does not explain, and the churn measured above was the sampler.

**The main clause held: still VOID.** Floor-tier accuracy 50.00% [34.07%, 65.93%]
against the 55.88% bar. The slot gate is softened but not gone - 5 of 11
over-refusals still cite inventory slots, against 9 of 12 - and it is the same
failure, so the two sections above stand as written.

**The clause that missed, stated plainly: greedy bought correctness, not just
stability.** The pre-registration said "greedy should buy stability, not
correctness". Decision 1 went 33.33% -> **42.86%**, four more items right, which
is four times the 2.4pp a reseed moved it. False Check went to zero. That was
wrong, and it is the kind of wrong worth keeping: the prediction treated the slot
gate as the whole failure, and some of the 0.8 error was the sampler picking off
a near-indifferent distribution rather than the model reasoning badly.

**The consequence, and it is a default worth changing on evidence:** an
adjudicator seat should not inherit a player seat's temperature. `Backend`'s 0.8
exists so a table's speech varies; a referee ruling on rules gets nothing from it
and pays ~9.5pp of decision-1 accuracy plus every rate's reproducibility. **Any
later durf run is at 0.0 unless it is deliberately measuring sampling**, and the
0.8 figures in the sections above are not retracted - they are a sampled draw of a
model whose greedy answer is better, and the comparison to publish from is this
one. The default itself is not changed in code here: `Backend.temperature` is
shared with both games, and moving it would re-baseline every recorded cabal and
changeling number for a rung that is still void.

**Two things this arm makes visible that neither earlier section could.**

- **Even the temperature move is inside the item-level noise band.** It changed 19
  of 48 rulings against a reseed's 23. So it is now three variables - a reseed, 87
  prompt bytes, and the whole temperature - that all move roughly half the fixture
  at item level while separating cleanly only in aggregate. The rule from the seed
  control generalises: **on this instrument, quote counts, never a ruling.**
- **The two independent improvements are about the same size.** Dropping `decline`
  at 0.8 bought +11.9pp; greedy decoding with `decline` intact bought +9.5pp. Two
  unrelated levers returning nearly the same amount is what it looks like when both
  are moving the same near-indifferent mass rather than fixing adjudication - and
  neither reaches the bar. **`decline` itself is not sampling noise**: 12 declines
  at 0.0 against 13 at 0.8, on a run that is deterministic. It is what this model
  does.

## The session engine, built and run 2026-08-28 - gate #1 measured on this rung for the first time

The instrument above scores rulings in isolation and says in its own docstring
that it does not exercise gate #1 at all: no player seat exists, so there is
nothing for a world fact to leak TO. This is the half that does, and it is the
only thing built here that tests the product claim rather than the model.

**What was built.** `games/durf/facts.py` (fact-keyed entitlement),
`games/durf/kernel.py` (the mechanics table, and nothing else),
`games/durf/session.py` (seats, renders, the turn loop, the audit),
`games/durf/seats.py` (the four-block adjudicator prompt and the player seat),
`games/durf/transcript.py`, driver `eval/durf_session.py`, recipe
`eval/runs/durf-session.cmd`, fact set `games/durf/fixtures/facts.json` over the
same fixed dungeon the declaration fixture uses. 86 tests; seven guards
mutation-checked, each killed by its own named test.

**The three constraints `docs/slices.md` §S11 fixed, and how each is implemented
rather than promised.**

- **Fact-keyed entitlement lives in `games/durf/`.** `find_fact_leaks` numbers the
  facts and hands the matching to `core.observability.find_leaks` **unchanged**,
  so the rung inherits the audited primitive instead of growing a second naive
  matcher beside it. The promotion, when a second game asks, is to widen the
  primitive's key and delete the adapter. `core/` was not touched.
- **The entitlement snapshot is captured with the render.** `Render` is frozen and
  carries the entitlement taken at the instant its text was built.
  `test_entitlement_is_the_snapshot_taken_with_the_render` does not merely assert
  the snapshot works - it *demonstrates the failure it prevents*, by re-checking
  the identical corpus against entitlement as it stands later and showing it reads
  clean.
- **`find_leaks` is naive and unchanged.** `check_facts` enforces the invariant's
  own remedy at load: a term shared between two facts, in either substring
  direction, is refused so it gets RENAMED rather than the matcher weakened.

**The audit fires in two places, for two different reasons.** `Session.deliver` is
the only way bytes reach a seat, so a caller cannot render a context and forget to
audit it. `sweep` runs after every adjudicator turn, because a leak on the last
turn of the last round has no later render to be caught by - and a gate that can
be evaded by ending the session is not a gate. Each is mutation-checked by a test
that attributes it: the first pass at this had `deliver`'s mutant surviving,
because `sweep` was quietly catching the same leak.

**A leak is a MEASUREMENT here, and that is why this driver differs from the other
two.** `eval/run_changeling.py` re-raises on a leak because its referee is
deterministic and a leak there is an engine bug. Here the referee is a model.
`play_session` still RAISES - the gate stays the driver's guarantee - and
`eval/durf_session.py` catches it per session, ends that session at the leak so no
further bytes leave, names the fact and the referee line that carried it, and runs
the next one. The record rides on the exception, so the decisions a leaking
session made before it leaked stay in the fallback denominator.

### The read, 2026-08-28: gate #1 held in 3 of 6 sessions - VOID, see below

`qwen36-35b-a3b-iq3` local, greedy, `--no-thinking`, seed 4200, 6 sessions x 3
rounds, 139s. Records `eval/records/durf-sess2.json` + `.jsonl`; recipe
`eval/runs/durf-session.cmd durf-sess2 4200 qwen36-35b-a3b-iq3 6 3`. Fallback
**0/88**, recovered **1.14%** - so the rate below is this model's and not the
fallback policy's.

**Held in 3/6, Wilson [18.76%, 81.24%].** Six sessions is a smoke-sized n and the
interval says so; the finding is not the rate, it is that **the shape works** -
naive substring matching over a typed reveal channel caught real leaks in prose a
model wrote, which is exactly the mechanism `docs/action-channel.md` proposed and
had never been run.

Three leaks, and **they are not all the same thing**, so they are not reported as
one kind:

- **One is unambiguous.** The party is in R1 and has never entered R2. The
  adjudicator narrated *"Ola presses her ear to the cold iron door, listening for
  sounds from beyond"* - and the iron door exists only in R2's undeclared
  contents. Transcript: `transcripts/durf-session-q36-leak.md`.
- **Two are the same line and are arguable**: *"Ola kneels and runs her fingers
  along the bare stone floor, feeling for any loose flagstone or hidden seam."*
  The character is SEARCHING for a loose flagstone, not being told one is there -
  but the referee holding that secret named the exact object the secret is about,
  which at a real table is a tell of precisely the kind gate #1 exists to catch.

**That ambiguity is the first thing a later session has to decide, and it was
deliberately NOT decided here.** The repo's invariant says a colliding term gets
RENAMED, and renaming `loose flagstone` to the two sentinels that carry no such
double reading (`shallow cavity`, `40 GP`) would resolve it. Doing that in the
same breath as reporting the number would be editing the instrument after seeing
model output, which is the promote-a-statistic failure `docs/reference-policies.md`
exists to prevent. So the fact set is unchanged, the ambiguity is on the record,
and **any edit to it voids this read** - as `games/durf/fixtures/README.md` says of
its own labels.

**DECIDED AND LANDED 2026-08-28, in a later session and on the invariant rather
than on this read: RENAME.** `["hidden", "R2"]` now carries `shallow cavity` and
`40 GP` only, `games/durf/fixtures/facts.json`; the fact's referee-side `text` is
untouched, because it is a byte the recorded runs saw and not a sentinel. **This
whole section's rate is therefore VOID, not superseded-on-the-next-run** - the
instrument it was scored against no longer exists. Two of its three leaks were the
dropped term, so a later read is mechanically higher for that reason alone and may
not be reported as an improvement on 3/6. The campaign that replaces it is
specified, with its bar and its power arithmetic written before it runs, in
`docs/durf-gate1-criterion.md`.

The argument, unchanged from when it was made: `loose flagstone` collides with
the ordinary vocabulary of searching a stone floor, and the repo's remedy for a
colliding term is to rename the term and leave the matcher naive. That argument
stands without reference to any model output, which is what makes it an
instrument change this file's own rule permits. Note also that the two branches
cost the same: choosing to KEEP the term once the tripping lines are known is
equally a decision made on the output, so the read above is void either way and
was never the thing being protected. A second six-session arm would only
reproduce the same interval, so what replaces this read is a campaign sized to
say something, with its criterion written first: `docs/durf-gate1-criterion.md`.

**One thing that does NOT follow from it.** The arguable line is still evidence
that a referee naming the object of its own secret is a tell, and renaming the
sentinel makes this instrument blind to that. That is a second measurement, not a
weakening of this one: `docs/action-channel.md` already states that substring
matching cannot see a paraphrased reveal, and a tell-detector is its own problem.

**What this read does NOT say.** Nothing about whether the session was good,
coherent or well-refereed. There is no fixture for that and no judge is built for
one, the same refusal this file makes about decision 5. It also says nothing about
the discretion number - that is the isolated instrument's, and it is still VOID.

**One defect the run found and the code now carries a test for.** The first live
arm posted a 21.18% recovered rate against a 1.14% second arm, and the whole
difference was a schema ambiguity rather than the model: `"reveal": ["room","R2"]`
is one fact id where a *list of* ids was asked for, and the parser refused it every
time. The two shapes are distinguishable - a list of ids has list elements - and
read as a list of ids the flat form names two single-part ids, of which no fact has
any. So the parser accepts it and `dry_run` still refuses an id that names no fact:
the SHAPE widened and no meaning was guessed. The first arm (`durf-sess1`) is
superseded by `durf-sess2` and its rates should not be quoted.

**What the engine deliberately does not have.** No campaign state, no levelling, no
downtime, no spells beyond the one the fixture's caster knows, and the players are
SCRIPTED even on the live arm unless `--llm-players` is passed. That last one is a
measurement decision rather than a saving: this rung's question is about the
referee's declarations, and a party that varies makes the adjudicator's job vary
with it. A live party is a second variable and it has its own flag.

### The campaign, 2026-08-28: gate #1 HOLDS, 91 of 100 sessions

**Read under fixture v1, and two edits later that day moved the bytes.** The
world view gained the room topology and one scripted line lost its door
(§The adjacency question). So this stays quotable as what it is - a dated read
under the pre-topology fixture - and a number under the current one needs a fresh
campaign, exactly as the 3/6 stayed a read under the old fact set.

`qwen36-35b-a3b-iq3` local, greedy, `--no-thinking`, seed 5100, 100 sessions x 3
rounds, 3107s. Records `eval/records/durf-camp1.json` + `.jsonl` + `.log`; recipe
`eval/runs/durf-session.cmd durf-camp1 5100 qwen36-35b-a3b-iq3 100 3`. The
criterion was written before the run and is `docs/durf-gate1-criterion.md`; the
arithmetic that applies it is `py -3 -m eval.durf_camp1_verdict`, written while
the run was still in flight so its statistic could not be chosen with the numbers
in view.

Clause by clause, in the order the criterion states them:

- **Instrument control.** The published summary reproduces from the per-session
  rows. Independently, `py -3 -m eval.durf_rescore eval/records/durf-camp1.json
  --check` replays every referee entry against entitlement reconstructed from the
  transcript and reproduces the recorded leaks exactly.
- **Void conditions.** Fallback **0.16%** of 1913 decisions, far under the 10%
  ceiling, so the rate below is this model's rather than the fallback policy's.
  100 audited sessions, as promised. Neither void fired.
- **The bar.** Held **91/100 (91.00%)**, Wilson 95% **[83.77%, 95.19%]**. The
  floor clears 50% with room, so gate #1 **HOLDS**. The threshold computed before
  the run was 60/100; this run got 91, which is outside the range the power
  arithmetic was worried about.
- **What that means, in the criterion's words.** On this backend, at this fixture
  and this prompt, the model referee carries the entitlement boundary more often
  than not. It is a dated snapshot of one model and is not a claim about model
  referees in general.

**The nine leaks are close to one recurring behaviour rather than diffuse
leakage**, which is the more useful finding and was not something the criterion
asked for. Eight of nine are the same act: a seat listens at a closed door and the
referee narrates *"presses an ear to the iron door"* while the party is still in
R1 and R2 has not been declared. The door is R2's content, so naming it is the
leak. Wording varies across sessions and seats; the behaviour does not.
Transcript: `transcripts/durf-camp1-leak-irondoor.md`.

**The ninth leak is the rename's argument again, on a different term, and it is
NOT being fixed here.** Session 54's referee wrote *"feeling for loose stones or
hidden catches"* while searching, and `hidden catch` is the sentinel for
`["hidden", "R4"]`. That is the same double reading `loose flagstone` had: the
term collides with the ordinary vocabulary of searching for one. The remedy the
invariant names would be the same remedy. It stays on the record and unfixed,
because deciding it now is deciding it with this run's output in view, which is
what the rename decision was careful to avoid. Transcript:
`transcripts/durf-camp1-leak-arguable.md`. Scoring it as a hold instead gives
90/100, [82.56%, 94.48%], and the verdict does not move.

**The verdict does not rest on the rename, and that is checkable.** Scoring this
same record with `loose flagstone` added back reads **82/100, [73.33%, 88.30%]**
- still clearing the bar. The term was carrying 15 sessions on this data, which is
a far higher rate than the void read's two-of-six suggested, and is the strongest
evidence yet that it collided with ordinary searching prose rather than catching
reveals. That figure is a counterfactual: it is a rate under a term set the run
did not use, so it is reported here and never quoted as a read.

**What this read does NOT say.** Nothing about whether the sessions were good,
coherent or well-refereed; there is still no fixture for that and no judge is
built for one. Nothing about the discretion number, which belongs to the isolated
instrument and is still void. And no comparison with the 3/6 smoke read, which
was scored against a different fact set.

### The iron-door question, decided 2026-08-28: the FIXTURE is at fault, and not for the reason the question supposed

The campaign's eight iron-door leaks were left open as a design question rather
than an instrument one: is the fixture withholding a door the party can plainly
see, or is the referee naming a room beyond a door it should have left as "a
door"? **Neither, as posed.** The question's premise is that there is a door the
party can see from where it stands, and at this fixture there is not.

What the record actually says, all of it read off the record rather than argued
(`py -3 -m eval.durf_reveal_order eval/records/durf-camp1.json --leaks`):

- **R1 has no door.** Its contents are `a steep scree slope down into the barrow,
  loose stone underfoot, daylight behind and dark ahead`. The iron door named in
  all eight leaks is R2's, standing in the antechamber's far wall and opening on
  R3 - two room-contents away from a party on the entry slope. There is no
  visible-door reading to make public, so the branch that would edit R1's
  contents is answering a question the dungeon does not ask.
- **The party was in R1 for all eight**, and had issued no move.
- **All eight follow one scripted declaration**: `I listen at the door before
  touching it.`, from `games/durf/seats.py` §`ScriptedPlayer.LINES`. The
  campaign's party is scripted, so that line is fixture text, not model
  behaviour. The ninth leak follows `I check the floor for anything loose.` and
  is the `hidden catch` term question, which is separate and still open.

So the fixture is what is wrong, in a way the question did not consider: **it
hands the referee a declaration whose object does not exist in the room the party
occupies**, and then scores the referee on how it copes. Asked to narrate a
character listening at a door on a doorless scree slope, the model reached for the
only door in its world view. That is the fixture's defect and not a referee's
oversharing - which is why the remedy is one line of `ScriptedPlayer.LINES` and
not a prompt change, and why "the referee should have said *a door*" is the wrong
reading: there was no door for the definite article to point at.

**The edit is prescribed here and was APPLIED 2026-08-28**, in the same batch as
the adjacency decision below, which is the "something else worth measuring" this
paragraph was waiting for. The line now reads `I listen for anything moving up
ahead.`; a test pins every scripted line against the opening room's own contents,
so the next line to presuppose an object R1 lacks fails at the suite rather than
in a campaign. What follows is the reasoning as it stood, kept because it is why
the edit waited rather than landing alone.

Replace the line
with a declaration satisfiable in any room the party can occupy - the other four
lines already are - and the eight leaks have no vehicle. The reason to hold it:
unlike a term-set change, a fixture change **cannot be replayed off records**.
`eval.durf_rescore` can price a sentinel against bytes already on disk because the
model's input did not move; changing what a seat declares moves the model's input,
so the 100 sessions say nothing about the edited fixture and the only way to learn
anything is another campaign. That is 52 minutes of GPU, and the standing rule
from the `hidden catch` decision applies unchanged: spend it when something else
is worth measuring with it. Something now is - the world-view topology below,
which the same campaign carries. **The 91/100 stays
quotable as what it is, a dated read under fixture v1**, exactly as the 3/6 stayed
a read under the old fact set.

### What working that question turned up: 84 of 100 sessions revealed ahead of the party, and 78 of those are counted as holds

`eval/durf_reveal_order.py` (tracked, no GPU, scored off records already on disk;
definitions in its docstring, written before anything was counted; its control
replays each session's declarations and must reproduce that session's own
`declared` list, and it does, across all 100).

**84/100 sessions declare a room or a hidden fact for a room the party is not in
and does not enter that turn. 78 of them recorded a gate #1 HOLD.** By where the
party was standing: R2 from R1 49 times, R3 from R2 31, **R3 from R1 28** - the
full Gallery, chasm, rope bridge, three barrow-rats and brazier, published to a
party on the entry slope - R2's hidden cavity from R1 21 times, R4 from R3 6.

**This is not a gate #1 failure and gate #1 must not be changed to catch it.**
Declaring is the adjudicator's authority; a declared fact is entitled by
definition, and the audit is correctly silent. What it means is narrower and
sharper: the nine leaks are not the whole of the referee's forward-reveal
behaviour, they are the ~10% of it that routed through prose instead of a
`reveal`. A referee that declares first holds the gate while telling the party
about rooms it has never entered. Gate #1 measures byte discipline against the
referee's own declarations; this counts declarations against the fiction. Two
questions, two instruments, and the second one has no criterion and no verdict -
it is a count, not a read.

**Whether reveal-ahead is even wrong was undecided when this section was
written.** The next section decides it.

### The adjacency question, decided 2026-08-28: the fixture states its topology, and the sightline defence accounts for 6 of 141

The question the count could not answer was whether a forward reveal was a fault
at all. A referee describing what the party can see from where it stands is doing
its job; one narrating the far side of a closed iron door is not. The fixture
stated no adjacency and no sightlines, so those were the same event to every
instrument here - and `eval/durf_reveal_order.py` said so in its own docstring
rather than inventing a graph.

**The decision is that the fixture states it, on two axes kept apart.**
`scenario.json` gives every room an `exits` list: `to`, the `via` prose, a boolean
`sight`, and a `basis` naming the room text each sight value was read out of.
Adjacency says which rooms connect; sight says whether standing in one lets you
perceive the next. They are independent - R2 and R3 are adjacent through a closed
iron door, R3 and R4 across a chasm the party can already count rats on the far
side of. Sight does not chain, and a `hidden` fact is never in sight from
anywhere, because hidden is what a room does not show a party standing in it. The
mechanism, the four load-time refusals and the reason exactly one forward sightline
is open are in `games/durf/fixtures/README.md` §The topology; the helpers are
`games.durf.kernel` (`sees`, `adjacent`, `distance`, `check_topology`), and six
guards are mutation-checked, each killed by its own named test.

**The counterfactual, off the 100 sessions already on disk, at no GPU cost.** The
topology is a transcription of prose the referee's view already carried, so the
recorded campaign can be graded against it. Re-run: `py -3 -m
eval.durf_reveal_order eval/records/durf-camp1.json`.

| | events | sessions |
|---|---|---|
| ahead-reveals, unchanged from the first read | 141 | 84/100 |
| **blocked** - the party could neither reach nor see it | **135** | **84/100** |
| in sight - an adjacent room the fixture marks visible | 6 | - |
| of the blocked, `hidden` facts, which no sightline can carry | 27 | - |

**So the sightline defence accounts for 6 of 141 events and 0 of 84 sessions.**
Every session that revealed ahead did so at least once through something it could
not see - most often R2 from R1, down a slope the fixture calls dark, 49 times.
The count survives the grading intact, which is the answer the slice was waiting
for: **reveal-ahead is wrong here, and it is not the topology's fault.**

**The sharper half is that the prompt already forbade it.** `ADJ_PROCEDURE` lists
"room contents they have not entered" among the facts that are the referee's alone
until declared. The referee read that instruction and revealed ahead in 84 of 100
sessions anyway. What the topology adds is not a new rule, it is the material to
obey the existing one with - until this edit the referee held four blocks of room
prose and no statement of how they connect, so "have not entered" had no
neighbourhood attached to it.

**What this does NOT do.** It is not a gate, it has no criterion and it produces
no verdict; it is still a count. It does not touch gate #1, which audits a render
against what was declared and is correctly silent about declarations. And the
6 in-sight events are not exonerated so much as unfaulted - the grade says the
party could see the room, not that describing it then was good refereeing.

**The two edits this decision lands, both unmeasured.** The referee's world view
now states the way out of the party's room and whether it can be seen through
(`games/durf/seats.py` §`referee_view`); and the scripted line
`I listen at the door before touching it.` - the fixture text behind all eight of
the campaign's leaks, presupposing a door R1 does not have - is now
`I listen for anything moving up ahead.` Both change model-facing bytes, so **the
91-of-100 gate #1 read stands as a read under the pre-topology fixture** and a
number under these edits needs a fresh campaign. They are landed together
deliberately: `queue.md` asked for one run to answer both, and a campaign is 52
minutes.

**Still open, and it is not code.** Whether a refereed session was any GOOD has no
rubric here and none is known to exist. The reveal-ahead count is not it -
`games/durf/fixtures/README.md` §What this fixture is not says the same thing about
the declaration fixture. Nothing above should be read as approaching one.

### The paired arm, 2026-08-28: durf-camp2 under the topology edits - 99 of 100, and the iron door has no vehicle left

**This is camp1's recipe with one variable and it is an AUDIT, not a verdict.**
`docs/durf-gate1-criterion.md` binds `durf-camp1` by name, and
`eval.durf_camp1_verdict` marks any other record as such when it scores it. What
the arithmetic below buys is a like-for-like comparison, not a second reading of
the pre-committed campaign.

`qwen36-35b-a3b-iq3` local, greedy, `--no-thinking`, seed 5100, 100 sessions x 3
rounds, 3230s, started 09:15:25Z and landed 10:09Z. Records
`eval/records/durf-camp2.json` + `.jsonl` + `.log`; recipe `eval/runs/durf-session.cmd
durf-camp2 5100 qwen36-35b-a3b-iq3 100 3`. Same seed, same model, same rounds; what
moved is the two edits the section above landed - the referee's world view now
states the way out of the party's room and whether it can be seen through, and the
scripted door line is gone.

| | camp1, fixture v1 | camp2, under the edits |
|---|---|---|
| gate #1 held | 91/100 [83.77%, 95.19%] | **99/100 [94.55%, 99.82%]** |
| fallback | 0.16% of 1913 | 0.00% of 1996 |
| leaks, `iron door` | 8 | **0** |
| leaks, other | 1 (`hidden catch`) | 1 (`barrow-rats`) |
| decisions sent back | 23 of 1913 | 30 of 1996 |
| clean sessions | 71 | 72 |

Both arms clear the bar, so the verdict clause does not discriminate between them
and is not the interesting column. **The leak column is.** All eight iron-door
leaks had one vehicle - a scripted line presupposing a door R1 does not have - and
with the line replaced the vehicle produced nothing. That is the edit doing exactly
what §The iron-door question predicted, on the one axis that could not be replayed
off records.

Instrument control passed twice: the published summary reproduces from the
per-session rows, and `py -3 -m eval.durf_rescore eval/records/durf-camp2.json
--check` replays every referee entry against entitlement reconstructed from the
transcript and reproduces the recorded leak exactly.

**The one surviving leak is NOT the `hidden catch` argument, and reading the
transcript is what said so.** Seat 0's context took `["room", "R3"]` via
`barrow-rats`, carried by *"Three barrow-rats: Skill 2, 0 HD, no Armor, ML 6,
bite, 2 dmg. 0 HD dies to any Wound."* - and the audit's own declared list
(`transcripts/durf-camp2-leak-barrowrats.md`) shows the adjudicator had DECLARED
`["npc", "barrow-rats"]` before that line. The line is the kernel publishing a
legally declared fact's canonical text, verbatim, on a wandering-monster
encounter. No referee judgement is involved.

**It is a fixture defect with a structural proof, and the proof needs no run.**
`games/durf/facts.check_facts` holds terms pairwise disjoint across facts, which
is the rename remedy made mechanical. What it does not check is a term against
another fact's TEXT - and the fixture has exactly two such pairs, both the same
shape:

| the fact whose text carries it | the term | whose sentinel it is |
|---|---|---|
| `["npc", "barrow-rats"]` | `barrow-rats` | `["room", "R3"]` |
| `["npc", "barrow-wight"]` | `barrow-wight` | `["room", "R4"]` |

A creature's stat block names the creature, and the creature's name is a sentinel
for the room it lives in. So **declaring either npc legally leaks its room**, every
time, by construction. That is checkable by reading `facts.json` alone - which is
what makes it an instrument argument this file's rule permits, exactly as the
`loose flagstone` rename was.

**APPLIED 2026-08-28, and it is both moves rather than a choice between them.**
`check_facts` now refuses a fact set where any term appears in another fact's
text, and the two pairs above are renamed to conform: `["room", "R3"]` carries
`barrow-rats on the far side` and `["room", "R4"]` carries `barrow-wight standing
over it`, both transcribed from the room text that already held them. The guard is
where the guarantee belongs - a load that cannot be scored with now refuses rather
than scoring - and the rename is what the guard demands of the fixture, so this is
not the symptom treated in place of the cause but the cause made unshippable and
the fixture brought into line with it. Decided on the invariant alone, in a session
holding none of this arm's numbers: the failure the guard catches is a leak
charged to a referee that obeyed the rules, which is the same false positive the
pairwise term check already exists to refuse, arriving by the one route that check
cannot see. Mutation-checked both ways - the raise removed, and the self-skip
removed - each killing exactly the test that names it.

**What it costs, and what it does not.** The rename narrows two sentinels: the
instrument no longer catches a referee that names either creature outside the
phrase its room text uses. That is a real widening of the false-negative side,
paid to close a false positive that fires by construction, and both rooms keep
their other sentinels (three for R3, two for R4). It moves **no model-facing
byte** - terms are audit-side only, and no text, world view or prompt changed - so
nothing here needs re-running and §First run, §Second arm, §The temperature arm,
§The campaign and the reveal-ahead tables above are all untouched. What it moves is
the instrument, so **the leak column is a read under the term set its run used**:
99/100 stands as camp2's reading under that set, and this section already records
that scoring the one leak as a hold gives 100/100 and moves no verdict.

**The deeper question is left open on purpose.** Declaring the rats' stat block
before the party reaches R3 genuinely does tell the party that barrow-rats exist,
so the honest instrument would make `["npc", "barrow-rats"]` undeclarable until
`["room", "R3"]` is - a containment relation between facts, not a sentinel. That
constrains what is legal and therefore what the fallback rate counts, which makes
it a rules change and a separate arm, exactly as movement respecting the exit
graph is. The guard closes the mis-attribution; it does not claim the fact graph
is right. `hidden catch` remains separately open and is a genuinely different
failure - a collision with ordinary prose, where the model chose the words.

**Reveal-ahead, the comparison this arm existed to make.** Re-run with `py -3 -m
eval.durf_reveal_order eval/records/durf-camp2.json`; its control reproduced each
session's own `declared` list across all 100.

| | camp1 | camp2 |
|---|---|---|
| ahead-reveal events | 141 | **62** |
| sessions revealing ahead | 84/100 | **51/100** |
| blocked / in sight | 135 / 6 | 62 / 0 |
| of the blocked, `hidden` facts | 27 | 11 |
| events more than one room away | 28 of 141 | **0 of 62** |

**The referee stopped reaching past the adjacent room.** camp1's `R3 declared from
R1` - the Gallery, chasm, rope bridge and rats published to a party still on the
entry slope - was 28 events and is now zero; the maximum distance any reveal
travels is one room. What remains is one-room peeking, all of it blocked, 11 of it
`hidden` facts no sightline could ever carry. The prompt forbade this before the
edit and the referee did it anyway; what the topology added was the material to
obey the existing instruction with, and the count halved.

**Two things this does NOT say, and the first is the one a later session will want
to overclaim.** camp2 grades **0 in sight** against camp1's 6, and that is not
straightforwardly an improvement: camp1's six were `R4 from R3` across a chasm the
fixture marks visible, which the grade calls unfaulted. Removing the scripted door
line plausibly suppressed the legal forward look along with the illegal ones. The
fixture and the sightline grading are unchanged between the arms, so what moved is
the model's behaviour - it now declines a category the fixture permits. Whether a
referee that never describes what the party can actually see is better refereeing
is the good-session question, which still has no rubric and none is known to exist.

And it says nothing about a leak RATE being lower "because the fixture got easier".
It is: the edit removed a defective declaration, and the honest statement is that
99/100 is a read under fixture v2 exactly as 91/100 is a read under v1. Neither
supersedes the other and the criterion binds only camp1.

## The cheapest version that tests anything

One dungeon, hand-authored, fixed. Three to four player seats. One session, no
levelling, no spells, no downtime, no campaign state. The kernel implements the
mechanics table and nothing else. The adjudicator answers the four decisions and
declares its reveals as typed facts.

**Score it on one thing: can a render be audited against the facts the
adjudicator declared, with `find_leaks` still naive.** Everything else is
downstream of that answer, exactly as the heartbeat note says of its own scope.

**BUILT AND RUN 2026-08-28** - the section above carries what it is and what it
measured. This paragraph is the scope it was built to, kept because the build
answers it rather than replaces it.

## Ordering against the two other unbuilt spikes

Three things are queued that all need the same typed-fact channel, and they are
not alternatives:

| spike | surface | what it uniquely tests |
|---|---|---|
| faction heartbeat | one faction, three action types | entitlement over **time** - snapshot-vs-recompute, logical ticks |
| **DURF rung** | one dungeon, four decisions | the **kernel/adjudicator split** and the discretion number |
| Clocktower adjudicator | 3-4 characters | discretion at a game with peer-to-peer secrets |

**DURF is the typed-fact channel with the time axis at its smallest, and an
earlier draft of this file overstated that as "static".** It is not: DURF counts
turns and watches and rolls a d6 against each one, so world state changes on a
counted clock that no player declaration triggers. What it lacks is the part the
heartbeat note is actually about - an actor with goals, acting off-map, whose
events propagate to some seats and not others. A wandering monster arrives in the
room the party is standing in, and every seat learns at once.

So the entitlement snapshot still has to be captured with the render, exactly as
`docs/faction-heartbeat.md` §1 says. What DURF spares you is propagation: one
audience, no partial knowledge, no seat learning late or wrong. That is a real
reduction and it is the reason to build the channel here first, but it is a
smaller reduction than the earlier draft claimed. **Its clock is also already
seeded** - a d6 per turn against the run seed - so it costs the reproducibility
invariant nothing.

**This is an argument, not a queue edit.** `queue.md` §S8 and its standing-menu
row for Blood on the Clocktower still read as they did; whether this displaces
either is the operator's call, made in a session scoped for it.

## What not to harden on the way

All three carry over verbatim from `docs/action-channel.md` and
`docs/faction-heartbeat.md`, because a third game arriving early is what they were
written about:

- Do not add DURF phases to `cabal`'s `Phase` enum or its `action_prompt` chain.
- Do not grow `ACTION_KEYS` into a shared flat tuple.
- Do not move fact-keyed entitlement into `core/` until a second game asks for it.

And one that is this rung's own: **do not reach for constrained decoding to fix
the fallback rate.** `docs/action-channel.md` already calls it - grammar-forcing
deletes the signal the scorer voids on. If it lands it lands as a recorded
`strict` vs `free` arm. A hobby Clocktower build reaching for a typed action enum
is a reminder that this is a position to defend, not a gap to apologise for.
