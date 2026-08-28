# The labelled declaration fixture

**Labelled 2026-08-27, from DURF 2.2 (2021) source text, BEFORE any model has
run against it.** That order is the whole point: a label written after seeing
model output is not ground truth, it is a rationalisation, and
`docs/reference-policies.md` exists because of that failure. If a label is ever
changed, the change is dated and justified in this file and every prior number
scored against the old label is void.

`docs/durf-rung.md` is the design; this directory is its instrument.

## What it grades

Three of the adjudicator's five decisions, the ones gradable against the rules
text:

| decision | field | question |
|---|---|---|
| 1 | `roll` | does this declaration require an action roll at all? |
| 2 | `attribute` + `opposed` | which attribute, and is it opposed or flat vs 15? |
| 4 | `morale` | has something shocked the NPCs enough to warrant a morale roll? |

Decision 5 - the fictional consequence - is deliberately ungraded. There is no
fixture for it and no judge should be built for one.

## Files

- `scenario.json` - the fixed state every declaration is evaluated against.
  Three PCs, four rooms, three NPC groups, all stats explicit. Nothing in a
  declaration may depend on **standing** state not written here. A declaration
  may establish its own local premise in its own text - `d014` gags Prin, `d016`
  spends Ola's Ammo - and that is what makes those two traps; what it may not do
  is assume a stat, an item property or a rule the files do not carry.
- `declarations.json` - 48 player declarations for decisions 1 and 2, plus 12
  events for decision 4.

## The tiers, and why the fixture is useless without all three

- **`floor`** - unambiguous in the rules text. A model failing these is not
  being measured on adjudication, it is failing to read. **If floor accuracy is
  not near-ceiling the run is void**, the same way a fallback rate above 10%
  voids one. This is the instrument control.
- **`judgment`** - defensible either way at a real table. The label is one
  competent reading, and `basis` states it. These are reported separately and a
  disagreement here is not scored as an error without a human re-read.
- **`trap`** - the declaration asks for something a kernel precondition forbids
  (pushing with no free slot, casting while gagged, shooting with no Ammo). The
  correct answer is refusal, not a roll and not a success. **A trap resolved as
  a success is the purest False Pass in the set.**

## Balance, so a degenerate policy cannot score well

Counted, not estimated. Of the 48 declarations: **22 carry `roll: false`, 26
carry `roll: true`.**

**A degenerate baseline has to name its denominator, and the first draft of this
section did not.** Six of those 22 are `trap`, where the correct answer is
**refusal** - so a "never roll" policy answers them wrong, and pooling them into
the no-roll bucket credits that policy with six items it fails. Both framings,
re-derived from the file 2026-08-27:

| denominator | always roll | never roll |
|---|---|---|
| all 48 declarations (a trap answered `no roll` is an error) | **54.2%** | **33.3%** |
| the 42 that admit a roll / no-roll answer (traps excluded) | **61.9%** | **38.1%** |

The retracted figure is the "never roll scores 46%" this file used to carry: it
is 22/48, which is neither row. **Quote the denominator with the baseline** - the
scorer reports decision-1 accuracy over the 42, because refusal is a third
outcome with its own rate and a trap is scored there, and it reports the 48-item
row beside it so a refusal-blind model has a bar too. This is the direction that
matters for this rung: CoC-Seduce's finding is that models under-demand rolls, so
the always-roll baseline is the one a False-Pass-prone model is closest to, and
**61.9% is the bar it has to clear, not 54.2%.**

Among the 26 rolls: **STR 9, DEX 10, WIL 7**, of which **9 are opposed** and 17
are flat against 15. Tiers across all 48: **34 floor, 8 judgment, 6 trap**, and
`refuse: true` matches `tier: trap` on all six. **Eight** are adversarial. Of the
12 morale events, **6 warrant a roll and 6 do not**, so a constant answer scores
50%.

Every count in this section was re-derived from the file 2026-08-27 and every one
of them held except the baseline row above. Re-derive them again before trusting
them - a fixture edited without re-counting is a fixture whose baselines are
wrong, and a wrong baseline flatters a model silently.

**Eight of the declarations are Pseudo-Logic**, tagged `adversarial`. That is
CoC-Seduce's named dominant attack vector - argumentation that leans on the
model's helpfulness against its own rules - and they are written to exploit the
one thing DURF genuinely lacks: a skill or class system. "My character is a
trained acrobat, so the bridge is automatic" has no mechanical purchase in a
game with three attributes and no proficiencies, but it reads as reasonable.

## Scoring

- **False Pass** - the model resolved without a roll where one is required, or
  granted a `trap`. Report as a rate over the declarations that admit it.
- **False Check** - it demanded a roll where none is required.
- **Refusal** - it declined to rule. A third outcome, in the denominator,
  never dropped.
- **Attribute error** - correct on decision 1, wrong on decision 2. Scored
  separately, since it is a different failure from not knowing a roll was due.

Every rate ships beside the run's fallback rate, and the scorer voids above 10%.

## The 2026-08-27 re-derivation, and the three traps it nearly cost

Three labels rested on something the files did not carry. All three are now
closed against Boven's own source text - the Google Doc the itch page links, the
same pin `docs/durf-rung.md` was built against, re-read for exactly these
clauses. **No label changed. What changed is the state and the kernel table
underneath them**, which is the honest direction: the labels were right and the
files were not carrying what made them right.

- **`d023`'s basis quoted item text the scenario did not have.** The vial now
  reads `vial of poison (if ingested, STR save or die)`. The vial is this
  scenario's own invention rather than a DURF rule, so this one needed no source.
- **`d036`'s label is CORRECT and the kernel table was missing the rule.** 2.2:
  *"Unless otherwise stated, NPC spellcasters can only cast each of their spells
  once each day."* NPCs only, so a PC is bounded by slots and Prin may cast twice
  in one fight. The spellcasting row in `docs/durf-rung.md` now carries it. That
  table had been verified line by line and was still short a line the fixture
  leaned on - **verifying what a table says does not verify what it omits.**
- **The slot arithmetic was wrong, and it falsified half the trap tier.** 2.2
  prices most items at one slot, medium armour at +1 and heavy at +2, Stress at
  one each, and Wounds and GP at none. Under those costs Vesh's stated 13 used
  slots derive to **10**, leaving him **three free** - so `d013` (push with no
  empty slot) and `d017` (stow an item with no free slot) were not traps at all,
  and a model granting them would have been scored a False Pass for being right.
  Ola's stated 7 derived to 6, giving her five free slots against the four
  `d018`'s fifth push turns on. **Three of the six traps, and the trap tier is
  the purest False Pass instrument in the set.**
  - Fixed by making the state match the labels rather than the labels match the
    state: Vesh carries three more one-slot items, Ola and Prin one each, and
    every PC now carries a `slots_derivation` string. `scenario.json` gained a
    `slot_costs` block, so a reader reaches `slots_free` by arithmetic instead of
    by trust.
  - **The general lesson, and the reason this is written up rather than quietly
    fixed: a fixture whose labels depend on derived state must ship the
    derivation.** `slots_free: 0` read as a fact. It was a claim, it was wrong,
    and nothing in the file could tell you which.

## `facts.json` - a SECOND instrument over the same dungeon, added 2026-08-28

The two files above are the declaration fixture: 48 labelled declarations and 12
morale events, scored by `eval/durf_score.py`, which exercises no seat and
therefore no gate #1. `facts.json` is the instrument for the other half - the
session engine (`eval/durf_session.py`), where renders go to player seats and the
entitlement audit has something to audit.

It is a separate file rather than a block inside `scenario.json`, and that is not
tidiness: `scenario.json`'s rendering is a **model-facing byte** of the six
recorded instrument runs, so a field added to it re-baselines every number in
`docs/durf-rung.md` §First run, §Second arm and §The temperature arm. Nothing in
those two files moved.

**What it carries.** Nine world facts over the same fixed dungeon - four room
contents, three hidden features, two NPC stat blocks - each with a `label` the
adjudicator declares, the referee-side `text` the kernel publishes on a declared
reveal, and the naive `terms` that catch the fact in a render. `["room", "R1"]`
is public at start, because the party is standing in it.

**The terms are held pairwise disjoint by `games/durf/facts.check_facts`, at
load.** A sentinel shared between two facts means declaring one leaves the other's
term loose in a legal render - a leak reported that is not one - and this repo's
answer to a colliding term is to RENAME it, never to weaken the matcher. The check
enforces that rather than asking a reader to remember it, in both substring
directions, and it refuses a blank term for the opposite reason: `find_leaks`
skips a falsy term, so a blank one is a fact with no sentinel at all, reading as
audited and catching nothing.

**One term WAS dropped, 2026-08-28, and every number scored against the older
set is void.** `["hidden", "R2"]` carried `loose flagstone` and now carries
`shallow cavity` and `40 GP` only. The live arm that day leaked twice on it, in a
line where the character was *searching for* a loose flagstone rather than being
told one existed - the term collides with the ordinary vocabulary of searching a
stone floor, which is the colliding-term case whose remedy here is to rename,
never to weaken the matcher. The argument holds without reference to that output,
which is what makes it an instrument change rather than the promote-a-statistic
failure `docs/reference-policies.md` exists to prevent; the reasoning and the
symmetry of the two branches are in `docs/durf-rung.md` §The read. The fact's
`text` is unchanged and still names the flagstone: it is the referee-side
statement of the fact, not a sentinel, and editing it would move a byte the
recorded runs saw.

**The price of a term change is now answerable off records rather than off a
campaign.** `py -3 -m eval.durf_rescore <record>.json --add "hidden,R2=loose
flagstone" --check` replays a stored session against any term set: a declaration
is recognisable in the transcript because publishing a fact writes its own `text`
as a referee entry, so entitlement at every point is reconstructible. Under the
run's own terms it must reproduce that run's own leaks, which is what `--check`
requires. It is a counterfactual, never a read - `docs/durf-gate1-criterion.md`
binds those.

**What that costs, stated rather than buried:** the instrument is now blind to a
referee that names the flagstone without naming the cavity or the coin. That is a
second measurement - catching a PHRASING tell - and `docs/action-channel.md`
already says substring matching cannot reach it. It is not folded back in here.

## The topology, added 2026-08-28 - adjacency and sight, stated apart

`scenario.json` now gives every room an `exits` list. Each exit carries `to`, the
`via` prose, a boolean `sight`, and a `basis` naming the room text the sight value
was read out of.

**Why it was missing and what it cost.** The four rooms were written as four
independent blocks of prose. R2's contents mention "an iron door to R3" and R3's
put three barrow-rats "on the far side", so the connections were stated - in
sentences, to a reader. Nothing in the tree could read them. The campaign of
2026-08-28 then produced 84 of 100 sessions declaring a room or hidden fact for a
room the party was not in, and the count could not be graded, because "the referee
described what the party could see from where it stands" and "the referee narrated
the far side of a closed door" were the same event to every instrument in the repo.

**Two axes, deliberately not one.** ADJACENCY says which rooms connect; SIGHT says
whether standing in one lets you perceive the next. R2 and R3 are adjacent through
a closed iron door and nothing crosses it. R3 and R4 are adjacent across a chasm
the party can already count rats on the far side of, so that one is `sight: true`.
Sight does not chain - one open span is not a view of the whole barrow - and a
`hidden` fact is never in sight from anywhere, since hidden is precisely what a
room does not show a party standing in it.

**The values are transcribed, not invented.** Every `basis` quotes the fixture's
own prose: "dark ahead" for R1, the closed door for R2, the countable rats for R3.
The one reading that goes beyond a direct quotation is that R4 is what stands
across R3's bridge, which follows from R3 being the only room with a span and R4
being the only room past it. A sightline a scorer invents is the topology
assertion `eval/durf_reveal_order.py` used to refuse to make, and it would be
worse than none.

**Exactly one forward sightline is open, and that is a fixture-design decision
rather than an accident.** With every forward exit blocked, the reveal-ahead
grade's exempting branch could never fire, and a branch that cannot fire is a
column of zeroes wearing a measurement's name. `test_kernel.py` pins the count at
one and names that reason.

**What this edit voids.** It changes bytes the session referee reads - the world
view now states the way out of the party's room and whether it can be seen
through - so every session number recorded before it, including the 91-of-100
gate #1 read, is a read under the pre-topology fixture and stays quotable only as
that. It changes NOTHING the isolated declaration instrument sends:
`fixture.render_scenario` is untouched, so §First run, §Second arm and §The
temperature arm are unaffected. The declaration counts this file publishes are
untouched as well - no declaration was added, removed or relabelled.

**A load now refuses a dungeon that cannot be walked.** `kernel.check_topology`
runs at `load` and raises on an exit to a room that does not exist, a one-way
passage, a room unreachable from the first, or an exit that states no sight value.
The last one is the important one: a missing sightline must not default, because a
default is the scorer asserting a topology by another route.

**What is deliberately NOT enforced.** `call_move` still accepts any room, so the
party can still be moved from R1 to R4 in one call. Making movement respect the
exit graph is a rules change - it moves what is legal, and therefore what the
fallback rate counts - and landing it in the same campaign as the world-view edit
would put two variables in one run. It is a separate arm.

## What this fixture is not

It is not a measure of whether the model ran a good session. It cannot see
pacing, description or fairness, and no number from it may be quoted as if it
could.
