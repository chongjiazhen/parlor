# The information model, in the vocabulary that already exists for it

Gate #1 is not a new idea and does not need a private vocabulary. Everything this
repo calls entitlement has a settled name in the general-game-playing and
game-theory literature, and borrowing those names is compression: it buys the
known pitfalls with the word, and it lets a reader outside this tree check the
claim without first learning parlor's dialect.

**This file fixes the translation.** It says what each parlor artefact IS in the
standard terms, and nothing about what anyone else's system is worth - that
judgement is a working note and lives off-tree per `AGENTS.md`. Sources are cited
by identifier, never by author, and the read depth behind each is at the foot.

## The five terms worth taking

**Information set.** The set of histories a player cannot tell apart. A strategy
is well formed only if it is constant across an information set - a player cannot
act on a distinction it cannot make. **This is gate #1, stated in one line: the
bytes sent to a seat must be a function of that seat's information set, and of
nothing else.** Introduced in *Extensive Games and the Problem of Information*
(Contributions to the Theory of Games II, 1953, pp. 193-216).

**Percept.** What a player is told after a move, as distinct from the state that
produced it. `core/observability.py`'s `Knowledge(seat, label)` is a percept, and
`entitled_knowledge` is a percept function. The label discipline already written
there - "the label is the whole reveal, never the other seat's exact role" - is
the standard requirement that a percept name an equivalence class rather than a
state.

**Perfect recall**, and specifically **synchronous perfect recall**: a player
cannot distinguish two states if it made the same moves and had the same
perceptions along both histories from the initial state. Taken verbatim from
*Model Checking Games in GDL-II* (2012). **cabal's `--notebook` is a perfect-recall
lever.** A seat without it does not retain its own earlier reads, which is
imperfect recall - the case where behavioural and mixed strategies stop being
interchangeable. The predicted `--notebook` null is therefore a claim about
imperfect recall and can be stated against a literature rather than against three
scattered 2026 results.

**Chance move, and the transformation that produces one.** A game where players
are uncertain about each other's payoffs or types is a game of *incomplete*
information; one where they cannot observe all moves or state is *imperfect*
information. The standard move converts the first into the second by having chance
draw the types up front - *Games with Incomplete Information Played by "Bayesian"
Players, I* (Management Science 14(3):159, 1967, DOI 10.1287/mnsc.14.3.159).
**The deal is that chance move.** Which is also the cleanest statement of why
`--seed` has to seed the sampler as well as the deal: both are draws inside the
same game, and seeding one of them describes half a game.

**Public versus private observation.** The two channels each rung already draws.
The record is common knowledge; a private reveal is not. Naming them this way is
what makes "a seat's speech is gameplay, the referee's bytes are the leak" a
statement about observation channels rather than a house rule.

## What GDL-II settles, and it is the design quorum reached by hand

GDL-II is GDL plus two keywords: `sees(?r, ?p)`, the percepts a role receives, and
`random`, a role for chance. The base language covers finite synchronous
deterministic complete-information games; those two additions cover randomness and
imperfect or asymmetric information. Source: *A General Game Description Language
for Incomplete Information Games* (AAAI 2010, 24(1):994-999, DOI
10.1609/aaai.v24i1.7647), keyword list read from *Model Checking Games in GDL-II*
(2012).

The load-bearing part for this repo is where `sees` sits. **It is a relation over
the state and the joint move, not a property of a role.** What a player perceives
is recomputed at every transition. Read through that:

| rung | its percept function | |
|---|---|---|
| `cabal` | constant in the state | entitlement is dealt once, from flags on `Role` |
| `changeling` | varies over roles | the night moves cards, so what a seat may be told changes |
| `quorum` | varies over state and move | keyed on `(office, phase)`, recomputed per event |

So cabal is the special case where the percept function happens not to depend on
the state, changeling the case where it depends on the deal's outcome, and quorum
the general one. That is a sharper statement of why the third rung exists than
"the entitlement cascades", and it was arrived at from the mechanics rather than
from the formalism - which is worth something, because the two agreeing is
evidence the mechanics are right rather than merely different.

**What the formalism does NOT give parlor is the thing parlor is for.** `sees`
declares what a player perceives; it does not check that an implementation's
outgoing bytes match the declaration. That gap is the whole project: a declared
percept relation is a specification, and gate #1 is the test that the render obeys
it.

## What quorum's audit is, formally

`games/quorum/audit.py` tests that each seat's rendered context is **measurable
with respect to that seat's information partition** - constant across states the
seat cannot distinguish. It does it the direct way: substitute a different legal
value for every field the seat is not entitled to, re-render, and require the two
renders to be byte-identical. A render that moves has read outside the partition.

That is why it catches what substring matching cannot. Scanning for a term asks
whether a secret's *name* appears; measurability asks whether the output *depends*
on the secret, which is the property the gate actually wants and is blind to how
innocent the surface text looks.

## What does not transfer

Ludii describes games as structures of ludemes and lists "Deterministic, stochastic
and hidden information games" among the types it can implement (*An Overview of the
Ludii General Game System*, arXiv:1907.00240; the system paper is arXiv:1905.05013,
ECAI 2020). Its vocabulary is built around board-game equipment and move
generation, which is a different axis from per-seat entitlement, so there is no
term here parlor is missing. Nothing further about that system belongs in this
tree.

## Read depth

- *A General Game Description Language for Incomplete Information Games* - title,
  venue, year, pagination, DOI and full abstract read from the publisher's record.
  The body was not read; nothing above attributes a formal definition to it beyond
  the two keywords, which are read from the 2012 paper below.
- *Model Checking Games in GDL-II* - full text read. The keyword list and the
  synchronous-perfect-recall definition quoted above come from it directly.
- Ludii - the ECAI 2020 abstract and the game-type list in arXiv:1907.00240 read.
  The hidden-information line above is the whole of what those sources say on it;
  no mechanism is described in either, and none is claimed here.
- Kuhn 1953 and Harsanyi 1967 - **not read first-hand.** They are cited as the
  origin of "information set" and of the incomplete-to-imperfect transformation,
  which is a bibliographic claim confirmed against secondary sources. No number and
  no distinction rests on either, per `docs/evidence-discipline.md`. A session that
  wants to lean harder on Kuhn's theorem - the equivalence of behavioural and mixed
  strategies under perfect recall, which is what would make the `--notebook`
  argument formal rather than suggestive - has to read it first.
