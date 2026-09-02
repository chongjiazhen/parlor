# belfry - the rules, and who is told what

The canonical statement of this game's model. Same job as the other rungs'
`RULES.md`: the gate strata, the decision audit and any chance baseline all derive
from what is written here, so a variant that changes what a role learns changes all
three.

Rules live here, next to the game. `core/` is what a fourth game would inherit;
`games/belfry/` is what is about this one.

Modelled on the town-square family of games in which a referee holds a board of
tokens, wakes players one at a time, and is allowed to choose. Nominative reference
only - no role name, ability text or art from any published game appears in the
code, and the canonical layer (directory, module, class, role keys) uses functional
keys and a house name, the way the Avalon-shaped rung is called `cabal`. The role
names below are English words for what each role DOES.

## What this rung is FOR

The three rungs before it share a property they never had to name: **the referee
tells the truth**. In `cabal` a seat's knowledge is true and static. In
`changeling` a seat can be wrong about itself, but only because the world moved
under a fact it was told correctly. In `quorum` what a seat may see is a fact about
the state.

Here **the referee lies on purpose, to a seat that is not told it is being lied
to**, and it does so as a rule of the game rather than as a failure. A poisoned or
deluded seat is told a specific, plausible, wrong thing in the same words a true
reveal uses.

That turns gate #1 from "tell the truth to the entitled" into the sharper claim:

> **Never state a true association a seat has not earned.**

A lie is safe only when it is built to miss. `night._other_role` draws a false
answer from what a seat is NOT - excluding both what it holds and what it registers
as - and the board shown to a poisoned watcher is a derangement rather than a
shuffle, because a shuffle leaves fixed points and a fixed point is a true fact
delivered to a seat with no entitlement to it. That would be a real leak wearing a
lie's provenance, and the audit would fail it, correctly.

Two other things arrive with this rung, both of which the ladder had not needed:

- **Many days.** A run is a loop rather than a single pass, so it needs a
  structural bound that is not a win condition (`max_days`) and a driver bound that
  is not the referee's (`MAX_DECISIONS`). A referee whose only exit is "somebody
  won" hangs the first time a rule is wrong, and a hang is not a failure anybody
  can read.
- **Discretion.** The referee of this family is a person who is allowed to choose.
  A deterministic referee cannot have taste, so every such choice is drawn from the
  run's seeded RNG and written to the referee-side log. See §Discretion.

## The table

5 to 12 seats in a circle, numbered `0..n-1`. The published proportions, which are
public and which every seat may reason from:

| seats | townsfolk | outsiders | minions | demon |
|---|---|---|---|---|
| 5 | 3 | 0 | 1 | 1 |
| 6 | 3 | 1 | 1 | 1 |
| 7 | 5 | 0 | 1 | 1 |
| 8 | 5 | 1 | 1 | 1 |
| 9 | 5 | 2 | 1 | 1 |
| 10 | 7 | 0 | 2 | 1 |
| 11 | 7 | 1 | 2 | 1 |
| 12 | 7 | 2 | 2 | 1 |

Townsfolk and outsiders are GOOD. Minions and the demon are EVIL. One role on the
script changes the counts, and the printed table is what every seat is told - so
the counts are a public claim that can be false, and that is the role's whole
value.

## The script

Which roles are IN PLAY is the secret. What each role WOULD do is public: every
seat reads every ability, because a seat that cannot read an ability cannot
evaluate anybody's claim to hold it, and the day is nothing but claims.

**Townsfolk.** `witness` (first night: one of two seats is a named townsfolk),
`archivist` (the same, for an outsider, or "none in play"), `tracker` (the same,
for a minion), `tally` (first night: how many neighbouring pairs are both evil),
`gauge` (each night: how many of its two living neighbours are evil), `diviner`
(each night: picks two seats, learns whether either registers as the demon),
`mortician` (each night after the first: the role executed that day), `warder`
(each night after the first: one seat is safe from the demon), `oracle` (killed at
night, it wakes, picks a seat and learns its role), `bulwark` (the demon cannot
kill it), `speaker` (three alive and no execution wins for good; a kill on it may
be redirected), `duelist` (once, in the day, publicly names a seat; if that seat
registers as the demon it dies), `martyr` (the first seat to nominate it, if a
townsfolk, is executed at once).

**Outsiders.** `sot` (believes it holds an out-of-play townsfolk role; its ability
does nothing and everything it is told is false), `valet` (picks a master; its vote
counts only alongside its master's), `hermit` (may register as evil, and as a
minion or the demon), `pilgrim` (executed, the evil side wins).

**Minions.** `venom` (poisons a seat until dusk tomorrow), `mimic` (sees the whole
board each night; may register as good and as a townsfolk or an outsider), `heir` (becomes the
demon if the demon dies with five or more alive), `warp` (two extra outsiders are
in play, in place of two townsfolk).

**Demon.** `fiend` (kills each night after the first; killing itself passes the
role to a minion).

### Two scripts, and the second one is a budget

`FULL` is all 22 roles. `COMPACT` is 12, chosen so every mechanic this rung exists
to exercise is still reachable: information that can be false, a seat wrong about
itself, protection, a public day action anybody may claim, an execution the good
side must not make, and a demon that survives its own death.

This is the repo's payload-budget invariant in its sharpest form. The script is the
largest item in every seat's context and it is paid on **every call of every seat
of every day**, which on this rung is a hundred-odd calls rather than fifteen. The
compact script is therefore not variety: same seeds on the two scripts differ in
the size of the payload and in the space a seat reasons over, and **a number
recorded on one says nothing about the other**.

## The night

Roles wake in a fixed order, each acting on the board the previous one left. The
order is data (`roles.py`), and changing it changes what every information role is
worth - protection resolved after the kill is worth nothing, and a poisoning
resolved after its victim's step is worth nothing.

**First night:** `venom` chooses; `mimic` reads the board; **at seven seats and
up** the minions are told each other and the demon, and the demon is told its
minions and three good roles that are NOT in play - at five and six seats the
evil side starts as strangers, as the source has it (2026-09-02; every belfry
number before that date briefed them at every size, so a 5-seat figure from
before and after is not one arm); then `witness`, `archivist`, `tracker`, `tally`, `gauge`, `diviner`,
`valet`. No kill.

**Every night after:** `venom`; `warder`; `mimic`; `fiend` kills; the `oracle`
wakes if it was the one killed; `gauge`; `diviner`; `valet`; `mortician`.

Deaths are held back and announced together at dawn. The table is told who died
and never what they were, and never in the order the night resolved.

The night is walked one step at a time rather than resolved in one pass, because
five of the steps are seat decisions. `pending()` is the cursor; the driver knows
nothing about the sequence, which is what keeps the driver from disagreeing with
the referee about the rules.

**The evil briefings are always true.** They are not an ability, so nothing that
switches an ability off touches them. An evil team that could be split by poisoning
its own briefing is a different game.

**A seat wrong about itself still wakes at the step of the role it believes it
holds** - and is told something false. A night that walked by truth would skip it,
and the seat would learn what it is from the silence.

## The day

1. **Talk.** `--rounds` passes; every seat speaks once per pass, **the dead
   included**. The dead keep their voice all game: they have lost their ability and
   most of their vote and they keep the only thing this game runs on.
2. **The public power.** A speaking seat may name a seat out loud. Any LIVING seat
   may do this - the dead keep their voice, not their power - whether or not it
   holds the role that makes it work, and the referee answers in the same words
   either way. A power only its true holder could invoke
   would make every invocation a proof of the role.
3. **Nominations.** Each living seat may nominate once; each seat may be nominated
   once per day, alive or dead.
4. **Votes.** Every seat with a vote answers each nomination at the same time.
   Carrying takes at least half the living seats AND more than the best count so
   far. Matching the best count clears the block instead - a tie executes nobody.
5. **Dusk.** The seat left standing is executed. Then night.

A dead seat holds exactly one vote for the whole game, spent when it votes FOR an
execution; voting against costs nothing.

**A vote that does not count is dropped silently.** The seat whose vote it was
knows why - its own render says so - and nobody else learns anything, which is the
rule at a table where that seat simply keeps its hand down. Announcing the drop
would identify the role that caused it.

## Win conditions

- **Good** wins when no demon is alive, or when the seat written for it is alive
  with exactly three alive and nobody executed that day.
- **Evil** wins when two seats are alive and the demon is one of them, or when the
  good side executes the seat it must not.
- **Neither** wins if the day bound is reached. That is a result about the table,
  not a win, and it is recorded as one.

The demon changing hands is the one way a dead demon does not end the game: a demon
that kills ITSELF passes the role to a minion outright, and a demon the town killed
passes it only to the role written for that, and only while five or more seats are
alive.

## Who is entitled to what

Gate #1 grades one thing: does a seat's outgoing payload contain a string tying a
seat to the role it actually holds, without that seat having earned it?

- The secret of seat `N` is the string `seat N is the <Role>`. Case-insensitive
  substring, per the repo's naive-matching invariant.
- **Entitlement is granted at the moment the referee writes a reveal**, and only
  when the named role is the role that seat actually HOLDS. A reveal can be a true
  answer to the question asked while naming a role its subject does not hold - that
  is exactly what the ambiguous roles buy their side - and it confers nothing.
- **A seat is entitled to itself**, except the seat that is wrong about itself,
  which is audited against its own line with `self_is_secret=True`.
- The board-watching minion is entitled to **every** seat. It is the widest
  entitlement in the game, and gate #1 has to be a check the referee can pass while
  it holds.

Two phrasing rules fall out of this and are asserted in tests rather than trusted:

- **Every single-seat reveal contains the canonical form.** A sentence may wrap it
  ("Yesterday's execution: seat 3 is the Warder.") and may not split it ("seat 3
  was executed yesterday and is the Warder" says the same thing and would be
  invisible to the audit).
- **A two-seat reveal names the role FIRST.** Written the other way round, "one of
  seat 3 and seat 5 is the Mortician" contains seat 5's secret verbatim. It fired
  on the first game ever played on this rung, correctly on the evidence it had. The
  invariant's remedy for a collision is to change the colliding text.

**No role name ever enters the public channel.** Deaths, executions, nominations,
vote counts and public accusations are announced as seats. That is the rule at a
real table, and here it also keeps the public record free of any association the
audit would otherwise have to grade.

## Discretion

The choices a human referee would make with taste, made from the seeded RNG and
logged referee-side. The S8 model arm moves **setup-only** discretion: it may
choose only a bounded offered menu during setup, never a player action, public
announcement, or later night choice. Each model choice emits its offered options,
selected option, fallback/recovery state, and upstream identity into private
referee provenance. That provenance is transcript-only: it reaches neither a
seat ask nor either public channel, and it is not an audit input.

| Choice | When | How |
|---|---|---|
| which seat a pointing reveal points at, and its decoy | at the reveal | uniform over legal candidates |
| the false answer given to a switched-off seat | at the reveal | uniform, excluding every true answer - and, for a seat that can become the demon, that answer too, since a lie succession later makes true is a true association in the seat's payload (2026-09-02) |
| which good seat reads as the demon to the hunter | at setup | uniform over good seats |
| whether the ambiguous outsider reads evil, and as what | at setup | fair coin, then uniform |
| whether the ambiguous minion reads good, and as what | at setup | fair coin, then uniform |
| whether a kill on the deflecting role lands elsewhere | at the kill | fair coin, then uniform - and the seat it lands on keeps its own protection, so a bounce onto the unkillable or a warded seat kills nobody (2026-09-02) |
| which minion inherits a self-killed demon | at the kill | the written role if alive, else uniform |

The two setup choices are taken ONCE, not per query. Per-query re-rolling is a
different game: a seat that reads evil on Tuesday and good on Wednesday is noise
nobody can reason against, and the whole value of an ambiguous seat is that its
owner can build a consistent story on it. **Per-query discretion is a variant axis
to measure, not a default to assume.**

## Cost

Measured 2026-08-28 with the random policy, `--rounds 1`, compact script, seeds
0-39 per size: **5 seats mean 49 decisions per game (median 47), 7 seats mean 119
(median 111), 9 seats mean 183 (median 167)**. One decision is one model call, so 5
seats is the size a serial local run can afford and 9 is the size a cloud run can.

Over the same seeds across every table size and both scripts - 520 games - the
random-policy outcome split was **good 49.2% / evil 47.5% / no winner 3.3%**. That
is the control arm and the only honest baseline this rung has. It is a property of
the RULES rather than a prediction about models, which is why it is recorded here
and not in `docs/measurements.md`: no model has played this rung yet, and the
number to put there is the first one that does.

**Re-measured 2026-09-02 at 5 seats, after the evil briefings moved to seven
seats and up** (the split above was played with a 5-seat evil side briefed). Same
recipe, `--rounds 1`, seeds 0-39, both scripts: compact good 17 / evil 23, full
good 17 / evil 23 - **good 42.50%** [32.26%, 53.43%] over 80 games, no winner 0.
Tightened on seeds 1000-1999, 1000 games per script: compact good 472 / evil 528,
full good 484 / evil 516 - **good 47.80%** [45.62%, 49.99%] / evil 52.20% / no
winner 0.00% over 2000 games, 0 fallback by construction. A 5-seat random control
does not reach the day bound, so the "no winner" share above is a property of the
larger tables. **A 5-seat model run is read against this line**, not the pooled
split above, which mixes sizes the briefing rule now treats differently.

## What is public, what is secret

**Public** - everything said, every nomination, every vote count and the seats
whose votes counted, every death and execution, the proportions, the script, who is
alive.

**Secret** - every role, every night action, everything any seat was told, every
discretionary choice, and the whole grimoire.

**Neither** - a seat's `think` field. It reaches no channel any seat can read; it
appears only in the referee-side record.

## Variant axes, none of them defaults

Each of these is a measured arm, not a convenience:

- **Per-query discretion** for the ambiguous roles (§Discretion).
- **Play-time discretion on one sentence** - `--adjudicator-night` hands the
  model the false count a switched-off gauge is told, with the seat's prior
  tellings, and grades whether it holds the lie across nights
  (`docs/belfry-night-coherence-criterion.md`). Off, the RNG stream is untouched.
- **A setup-only model referee** for bounded setup discretion. Its route is
  separate from every player route, its temperature is fixed at 0.0, and its
  private provenance is scored separately from player fallbacks. The paired arm
  changes that source alone; it does not move player policy, payloads, or audit.
- **Talk rounds** (`--rounds`), the largest single lever on cost.
- **Script size**, which re-baselines every number.
- **Dead seats speaking**, currently on. Turning it off is a rules change and
  roughly a third of the day's calls.
