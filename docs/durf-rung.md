# The DURF rung - a rules kernel under a model adjudicator

Written 2026-08-27, unmeasured, from a design read of `core/observability.py`,
`games/cabal/audit.py`, `docs/action-channel.md` and `docs/faction-heartbeat.md`.
Same job as both of those: nothing here is a decision, it is here so the cheap
moves stay cheap.

**What this scopes.** `RESUME.md` has carried "5e / a rules-lite RPG" as the
endgame rung with no statement of what the cheap version is. This names one: a
single dungeon session of DURF, a deterministic kernel underneath, a model in the
adjudicator seat, and one number nobody in the neighbouring literature has
produced. It is the first rung where `referee.py:6` inverts - judgment IS the
referee - and therefore the first that tests the actual product claim.

## Why this ruleset

**DURF is the smallest real system that ships legally.** ~40-50 pages, d20,
three attributes, no class tree, no spell list needed for a first session. Its
whole ruleset is smaller than four Blood on the Clocktower characters'
interaction surface, which is what `RESUME.md` scoped that spike down to anyway.
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

## The cheapest version that tests anything

One dungeon, hand-authored, fixed. Three to four player seats. One session, no
levelling, no spells, no downtime, no campaign state. The kernel implements the
mechanics table and nothing else. The adjudicator answers the four decisions and
declares its reveals as typed facts.

**Score it on one thing: can a render be audited against the facts the
adjudicator declared, with `find_leaks` still naive.** Everything else is
downstream of that answer, exactly as the heartbeat note says of its own scope.

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

**This is an argument, not a queue edit.** `RESUME.md` §S8 and its standing-menu
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
