# changeling - the rules, and who believes what

The canonical statement of this game's model. Same job as `games/cabal/RULES.md`:
the gate strata, the decision audit and any chance baseline all derive from what
is written here, so a variant that changes what a role learns changes all three.

Rules live here, next to the game. `core/` is what a third game would inherit;
`games/changeling/` is what is about this one.

Modelled on One Night Ultimate Werewolf. Nominative reference only - no role name,
art or text from any published game appears in the code, and the canonical layer
(directory, module, class, role keys) uses functional keys and a house name, the
way the Avalon-shaped rung is called `cabal`. The **theme** may use folk-game
vocabulary - werewolf, seer, villager - which is public-domain Mafia vocabulary
(Davidoff, 1986) and carries no mark.

## What this rung is FOR

`cabal` cannot pose the question this game exists to ask. There, every seat's
knowledge is true and static: a seat's own role is a fact it holds from the deal
to the end, and `SeatView.own_role` renders it straight from the assignment.

Here **a seat's knowledge of its own role can be stale, and can be false**, because
the night moves cards between seats and not every seat is allowed to look
afterwards. That splits one field into two:

- **truth** - the card a seat HOLDS at dawn. Decides the win. Referee-side only.
- **belief** - the last role a seat actually SAW itself holding. This is the only
  one that may be rendered to that seat.

So gate #1 gets strictly harder. In `cabal` the referee must not leak *another*
seat's secret. Here it must additionally **maintain a false belief in a seat about
itself** - never correcting it, never leaking that a swap happened, and never
letting the seat's own truth reach the bytes sent to its model. A referee that
renders truth where belief was due passes every `cabal`-era test and is wrong.

The second reason for this rung is throughput: one night, one discussion, one vote
is ~10-15 model calls against `cabal`'s 80-220.

## Seats, cards, and the centre

**Five seats. Eight cards.** Five are dealt to seats, three to the centre, face
down. The centre is real: cards there are out of play but reachable.

| card key | side | count | what the night lets it DO |
|---|---|---|---|
| `pack` | evil | 2 | wakes with the other `pack` and sees who it is |
| `spotter` | good | 1 | looks at ONE other seat's card, or at TWO centre cards |
| `swapper` | good | 1 | takes another seat's card, gives that seat its own, and **looks** at what it took |
| `switcher` | good | 1 | swaps the cards of TWO OTHER seats, and does **not** look |
| `deceived` | good | 1 | swaps its own card with a centre card, and does **not** look |
| `bystander` | good | 2 | nothing |

**You act on the card you were DEALT. You win with the card you HOLD at dawn.**
That single rule is the whole engine of this game, and every interesting position
comes out of it: the seat dealt `swapper` acts as the swapper even though it ends
the night holding something else, and the seat it robbed is `swapper` at dawn
without ever having acted or been told.

**At least one `pack` card is always dealt to a seat.** Unconstrained, both would
land in the centre in 6/56 = 10.7% of deals, and those games are degenerate - no
accusation can find a wolf, so the whole day is unmeasurable. The constraint is
public: every seat may reason from it. This is a deliberate deviation from the
family and it is here to keep a tenth of every run from being noise.

## Night order, and why it is the interesting part

1. `pack` - the pack wakes together and sees its own members. **A lone `pack` is
   offered nothing**: the source's option that lets a single wolf view one
   centre card is not built, and it is a house call rather than an omission
   (2026-09-02) - it would hand the one seat whose knowledge class is `none` by
   the deal an `identity`-class reveal and move the stratum the gate is cut on.
   Likewise every night act here is mandatory where the source says "may": a
   declined act is a no-op move, and the arena refuses those rather than model
   them. **Both are queued to be built to the source** (`queue.md`).
2. `spotter` - looks.
3. `swapper` - takes, and looks at what it took.
4. `switcher` - swaps two other seats, blind.
5. `deceived` - swaps itself with a centre card, blind.
6. `waker` - looks at its own card, after everything.

**Order is a knowledge-invalidating device, not ceremony.** Each step acts on the
state left by the one before, so earlier knowledge decays:

- A `pack` seat robbed at step 3 is a villager at dawn and does not know it. It
  will play the whole day as a wolf, and it wins with the village.
- The `spotter` saw a seat at step 2. If the `switcher` moves that seat's card at
  step 4, the spotter now holds a true statement about a card and a false one about
  a seat. Nothing tells it which.
- The `swapper` knows its own new role with certainty and knows the seat it robbed
  now holds `swapper`. Both facts can be invalidated at step 4.
- The `deceived` is wrong by construction. It never looks, so it believes
  `deceived` and holds a centre card - which may be `pack`.

## What a seat is told, and the knowledge classes

The class is what the deduction gate stratifies on, and - as in `cabal` - it is a
different axis from side. It describes **what the night told this seat**: the DEALT
card supplies the label, and the seat carries it only if the night actually gave it
a reveal. A card whose reveal did not happen leaves its seat in `none`.

Never the DAWN card. A seat robbed after it looked was told what it was told, and
relabelling it by a card it acquired afterwards would score it for knowledge it
never had. `false` likewise comes from the deal - only the seat that DRANK holds a
belief wrong by construction, and it is handed no reveal a count could see.

| dealt card | knowledge class **if the reveal happens** | what it holds |
|---|---|---|
| `pack` | `identity` | the other `pack` seat, by identity |
| `spotter` | `identity` | one other seat's exact card, or two centre cards |
| `swapper` | `identity` | its own new card, and that its victim now holds `swapper` |
| `switcher` | `positional` | that seats A and B exchanged. **Not what either one is** |
| `deceived` | `false` | a belief about itself that is wrong by construction |
| `bystander` | `none` | nothing |
| `kindred` | `identity` | every other seat dealt `kindred`, by identity |
| `waker` | `identity` | the card it is holding once the night is over |

The last two are expansion cards. `SETUP_5` deals neither - see below - but they
are defined, skinned and resolved, so they belong in this table: it is the list of
what a card tells its seat, not of what a particular deck happens to contain.

Two classes here have no `cabal` analogue, and they are the reason this rung is
worth building:

- **`positional`** - knowledge of a RELATION with no role attached. The switcher
  knows exactly what it did and nothing about what it moved. A seat holding a true
  fact that names no role is a different deductive object from one holding a role.
- **`false`** - a seat whose entitled knowledge is, by design, wrong. `cabal` has
  no such seat and cannot have one. Every gate-#1 property this repo claims has
  only ever been tested against knowledge that was true.

**A seat is never told its own truth once it diverges from belief.** There is no
reveal, no correction, and no phase in which the referee reconciles the two. The
divergence is resolved at scoring time, referee-side, after the vote.

### Keyed on the reveal, not on the card alone - changed 2026-08-28 (S10)

Until S10 the class came from the dealt card outright, and for a MEET card that was
wrong: **a MEET card's reveal is conditional on ANOTHER seat's deal.** A seat dealt
`pack` whose partner went to the centre wakes, sees nobody, and receives no
`Knowledge` at all - while carrying the `identity` label into every stratified
number. That seat, robbed into the village by dawn, is a **blind villager wearing
the `identity` label**, and THE GATE is cut on blind villagers.

Recomputable, and that is the point - `py -3 -m eval.strata`, which resolves nights
and counts, no model and no GPU. Both rules side by side, because the size of the
change is the claim:

| `SETUP_5`, 4000 nights, 20000 seat-nights (`--seed 11`) | TOLD (S10) | DEALT (pre-S10) |
|---|---|---|
| `identity` | 8038 (40.19%) | 10413 (52.06%) |
| `positional` | 2416 (12.08%) | 2416 (12.08%) |
| `false` | 2335 (11.68%) | 2335 (11.68%) |
| `none` | 7211 (36.05%) | 4836 (24.18%) |

The move is 2375 seat-nights, all of it between `identity` and `none`, and it is
exactly the MEET seats that met nobody - **42.2% of seated `pack` seats got no
fellow reveal**. Of 5358 blind villager seat-nights, **1043 (19.5%) had been hiding
in `identity`**, which is the same seats diluting that stratum from the other side
(18.7% of the pre-S10 villager `identity` cell). Stable on a second seed: 42.8%,
19.8%, 19.1% at `--seed 99`.

**These supersede the ad-hoc figures this section carried from 2026-08-27** (42.6%,
17.4%), which had no reproducer. They agree to about a point; where they do not,
the command above is the answer.

**So every recorded changeling run is re-baselined.** The blind stratum a pre-S10
record reports is ~19% smaller than the night produced, and the `identity` stratum
is correspondingly diluted. A number quoted across the change is two different
questions.

The behaviour was pinned on purpose while it stood
(`test_knowledge_class_is_keyed_on_the_DEALT_card`), so this was an argued change
rather than a bugfix. That pin is **replaced, not deleted**: the half of it that
still holds - the class comes from the dealt card and never the dawn card - is now
`test_the_class_still_comes_from_the_DEALT_card_never_the_DAWN_card`, and it sits
beside `test_knowledge_class_is_keyed_on_what_the_seat_was_TOLD` and the property
itself, `test_no_seat_is_labelled_with_knowledge_it_was_never_given`. Four guards
mutation-checked, each killed by its own named test.

**It is also the constraint the expansion decks below are designed around**, since
`kindred` is a second MEET card and a lone one is a blind *villager* by default -
straight into the gate's own denominator rather than beside it. With this landed,
both decks are unblocked.

### What each seat can DERIVE

Not written into any prompt; a strong player finds it.

- **Everyone** knows at least one `pack` was dealt (above), and knows the full card
  multiset. So three cards are unaccounted for at any time, and claims can be
  counted against the multiset - two seats claiming `spotter` is one card too many
  and at most one of them is telling the truth about its DEAL.
- **`swapper`** can certify a seat it did not rob is not `swapper`, and knows its
  own dawn card exactly - unless the switcher moved it, which it cannot rule out.
- **`switcher`** knows two seats' cards exchanged, so any claim either victim makes
  about its own card is a claim about a card that MOVED. It holds the one fact that
  can catch a stale wolf, and no way to prove it.
- **A claimed `deceived`** is unfalsifiable from the inside and cheap to fake,
  which makes it the natural cover story for a wolf. That it is *also* the seat
  most likely to be a wolf without knowing it is the joke this game is built on.

## The soundness invariant - what a fabricated belief must obey

Written before any belief-planting role ships, because it is cheaper to state than
to retrofit and because the first such card would otherwise be graded by taste.

> **A fabricated observation must be consistent with everything the seat can
> legally count.** A planted belief is legal only if at least one complete deal and
> night exists that would have produced the seat's entire rendered view. If no such
> world exists, the seat can refute its own knowledge by arithmetic, and the card is
> not a deception - it is a tell.

**Today's `false` seat is sound for free, which is why the rule has to be written
down now.** `deceived` plants nothing. Its belief is a *stale truth*: it was correct
at the deal and the night made it wrong, so the referee never asserts a fact that
was never a fact. Every world consistent with what it saw is a real world, because
what it saw really happened. The invariant is satisfied by construction and so is
invisible - and a card that actually invents an observation is the first time the
referee lies, with nothing in the existing machinery objecting.

### What the seat can legally count against

Five surfaces, all of them already public or already private-and-entitled. A plant
must survive every one, and each is decidable without play.

1. **The card multiset.** Eight cards, two `pack`, two `bystander`, one each of the
   rest, printed in the preamble. Counting claims against it is this game's central
   deduction, so a plant implying a ninth card, a third `pack`, or a card the deck
   does not hold is refuted before anyone speaks.
2. **The deal constraint.** `require_seated_pack` is public, so a plant may not
   imply a deal that seats no `pack`. On a deck carrying `require_seated_kin` there
   is a second one, equally public and equally countable: a plant may not imply a
   board with exactly one `kindred` seated.
3. **Night order.** Public, and it does real work - a reveal's step position
   constrains what could have produced it. The `waker` derivation above is the
   worked example: a single self-reveal with no partner line is uniquely `waker`,
   because only two cards produce a self-reveal and the other one comes in a pair.
   A plant arriving in a shape no card in the deck emits identifies itself.
4. **The reveal grammar.** `referee.reveal_forms` and `self_reveal_forms` are the
   only phrasings the renderer can produce, and a test asserts it. A plant must be
   drawn from that same list, or it is distinguishable as a string rather than as a
   claim.
5. **Its own act.** A seat knows what it did, and a plant may not contradict it.

Cross-seat consistency is the sixth and it is the one that is easy to miss: two
planted beliefs must not *jointly* imply an impossible board, even where each is
individually sound. Soundness is a property of the whole render, not of one line.

### The inverse failure, which is a gate #1 leak

**The referee must not become inconsistent in order to keep a lie sound.** If
honouring a plant requires rendering a different multiset, a different night order,
or a different reveal form to the deceived seat than to every other seat, then the
lie is being maintained by changing the public rules per seat - and the difference
between two renders is itself information. That is the same failure as the
`kindred` collision, arriving from the opposite direction: there, two seats got one
sentence that should have been two; here, one seat would get a private version of
text that must be byte-identical for all. Both are caught by the same instinct -
compare renders, not intentions.

### Why this needs a test and not care

**The audit cannot see an unsound plant, by construction.** `find_leaks` with
`self_is_secret` looks for a seat's *truth* appearing in bytes it is not entitled
to. A fabricated belief contains no truth to find - it is a false render, and every
gate #1 property this repo claims is about true knowledge reaching the wrong seat,
never about false knowledge reaching the right one. So the audit will be clean over
any number of deals while the card ships a refutable lie.

The guard is the enumeration instead, and it is affordable: eight cards over five
seats and three centre slots, six ordered steps, so the set of worlds consistent
with a rendered view can be enumerated outright rather than argued about. A
belief-planting card is admissible when a test enumerates that set and asserts it is
non-empty for every seat, on every deal it is exercised over. Same remedy shape as
`reveal_forms` - the property holds by construction or it fails a test.

### What it costs the stratum if this is got wrong

The `false` class exists to measure whether a model reasons **soundly from an
unsound premise**. A plant the seat can refute converts that seat from one that is
wrong into one that knows it is being lied to, which is a different question and a
different game. The stratum would still produce a number, and the number would be
about a seat detecting the referee rather than about a seat deducing. That is the
failure mode worth naming, because it does not look like a bug: nothing raises,
every render is legal, and the run reports as normal.

**A belief-planting card also re-baselines every recorded changeling number**, on
the same footing as `kindred` and `waker` - it changes what the deck can tell a
seat, so it may not enter `SETUP_5` without the measurement that a deck change
always owes.

## Expansion cards - defined, resolved, dealt by nothing

Two cards exist outside `SETUP_5`, on the same footing as `cabal`'s `lurker` and
`stray`: fully implemented and skinned, and each now seated by one registered deck
of its own rather than by none - `waker` by `SETUP_6_WAKER`, which has run, and
`kindred` by `SETUP_7_KIN`, which has not. Neither is in `SETUP_5`, because every
recorded changeling number was played on the eight-card deck above and changing it
re-baselines all of them. Both are here for what they add to the MODEL, not for
variety.

| card key | side | what the night lets it DO | what it buys |
|---|---|---|---|
| `kindred` | good | wakes with every other seat holding `kindred`, and they see one another | the pack's mirror on the village side |
| `waker` | good | acts last of all, and looks at the card it is holding by then | the only seat whose belief is *guaranteed* true at dawn |

- **`kindred`** made `meets_own_kind` mean what its name says. Until it existed,
  MEET grouped actors by their ACT, so a second meeting card would have woken up
  with the wolves and been told who they were - and the audit could not have caught
  it, because the referee would have been telling each seat something the rules
  genuinely entitled it to. Grouping is by dealt KEY.
- **Two meetings need two sentences.** A shared "one of your own" produced a real
  leak the day `kindred` landed: a stale village reveal is byte-identical to the
  sentence that betrays a wolf the night has since moved into that seat, and the
  audit called it - correctly, on the evidence it has. `Card.kin_form` is therefore
  per-kind data, which is this repo's standing remedy for a substring collision:
  rename the term. `pack` keeps the sentence it always rendered.
- **`waker`** is an instrument. Every other seat has to infer whether the night
  moved it; this one is shown. That makes it the cleanest available handle on
  whether a model reasons about *having been moved* at all, as opposed to about who
  is lying - which is the question this whole rung exists to ask.
- **What a `waker` can DERIVE, and must:** the render tells it the card it holds,
  not that it was dealt `waker`, because belief follows the look. It can recover
  that. Only two cards produce a reveal about the seat's own card - `swapper` and
  `waker` - and `swapper`'s comes with a second reveal about the seat it robbed. A
  single self-reveal with no partner line is `waker`, uniquely. The same reasoning
  the `swapper` already needs, one step shorter.

### The decks that would seat them - designed 2026-08-27; BOTH REGISTERED 2026-09-02

**Neither deck is paper any more.** `SETUP_6_WAKER` is registered in `roles.py`,
`eval.run_changeling --seats 6` deals it, `eval.strata --deck SETUP_6_WAKER` prices
it, and its campaign is frozen in `docs/changeling-waker-criterion.md` - which is
the binding statement of its bar and flags, not this section.

**Deck B is registered too, and has never been run.** `SETUP_7_KIN` is in
`roles.py` with `require_seated_kin` built and mutation-checked,
`eval.run_changeling --seats 7` deals it, and `eval.strata --deck SETUP_7_KIN`
prices it. Its accusation bar is not derivable from either shipped deck - wolf
density is 2/7 - so it was MEASURED before the criterion was written, not after:
`--arm random --seats 7`, 4000 games, seed 910000, under `plurality-min2`, blind
accuracy **25.39%** [24.22%, 26.57%] over 5376 votes, derived per-vote chance
25.18%, random-arm village win 32.69%. **The binding statement of that bar, the
power and the flags is `docs/changeling-kindred-criterion.md`**, frozen
2026-09-02 with recipe `eval/runs/changeling-kindred.cmd`, unlaunched. Registering
the deck and writing its criterion were two pieces of work, and doing the second
on an unmeasured bar is how the belfry criterion went wrong. **Every OTHER deck B
figure in this file is a prediction or a deal-only census until a live arm
exists.**

**Two figures below did not survive the instrument, and are left as written rather
than retrofitted.** The `blind/game` column is a paper definition; measured with
`eval.strata`, on the S10 told-based rule the gate is actually cut with, the move
is 1.340 -> 1.416 (+5.7%), not 1.02 -> 1.18 (+16%). Direction agrees, magnitude
does not. The criterion carries the binding table; the design is kept here so the
gap between a predicted deck and a measured one stays visible.

**Deck B's census, measured the same way 2026-09-02** (`py -3 -m eval.strata --deck
SETUP_7_KIN --nights 4000 --seed 11`, plus the packless-dawn count over the same
nights). Same instrument, same seed, all three decks, so these three rows are
comparable to each other and to nothing in the design table above:

| `--nights 4000 --seed 11` | blind/game | unwinnable | `identity` told nothing |
|---|---|---|---|
| `SETUP_5` | 1.339 | 2.85% | 18.7% |
| `SETUP_6_WAKER` | 1.416 | 2.05% | 10.3% |
| **`SETUP_7_KIN`** | **1.371** | **1.27%** | **5.3%** |

The design predicted 1.21 / 1.0% / 5.1% for K-c. The contamination figure landed
almost exactly, the unwinnable rate is the lowest of the three as predicted, and
`blind/game` came in HIGH rather than low - the same direction the deck A
prediction missed in, which is now two decks the paper `blind/game` definition
under-read. The deal constraint itself prices out at **pair 87.6%, lone 0%, neither
12.4%, 1.07 retries a game** over 4000 seeded deals, against the design's 86.0% /
0% / 0.92. Both sets are deal-and-night arithmetic with no model in them.

What follows is the design and the arithmetic behind it, so that work is a launch
rather than a session.

**Every deck change here costs at least TWO variables, and that is structural.**
`Setup.__post_init__` enforces `len(deck) == n + centre`, so a card cannot be added
without also growing the table or the centre. There is no one-variable arm
available in this game, and the honest move is to choose the second variable
deliberately and report it, rather than to pretend the deck was the only thing that
moved.

**The 8-card deck has no slack to cut into.** Six of its eight cards are the only
copy of their knowledge class - `spotter`/`swapper` (`identity`), `switcher`
(`positional`), `deceived` (`false`) - and the other two are `pack`, which is the
win condition. That leaves the two `bystander` cards, and they are the `none`
class, which is THE GATE. So a swap is not on the table; the deck grows or nothing
happens.

Measured by resolving 4000 nights per candidate. `blind/game` is villager seats
the night told nothing, by dawn truth - the gate's own denominator.

| candidate | n / centre | blind/game | unwinnable | `identity` told nothing | card seated |
|---|---|---|---|---|---|
| **shipped** | 5 / 3 | 1.02 | 2.8% | 17.4% | - |
| W-a: cut a `bystander` | 5 / 3 | **0.51** | 2.8% | 12.7% | waker 57.9% |
| W-b: grow the centre | 5 / 4 | 0.93 | 3.0% | 13.9% | waker 49.6% |
| **W-c: grow the table** | **6 / 3** | **1.18** | **1.8%** | **9.3%** | **waker 62.0%** |
| K: `kindred` x2, free deal | 7 / 3 | 1.27 | 1.2% | 20.6% | pair 45.2%, **lone 47.1%** |
| **K-c: same, both-or-neither** | **7 / 3** | **1.21** | **1.0%** | **5.1%** | **pair 86.0%**, lone 0% |

**Two decks, not one.** They answer different questions - `waker` is an instrument
for whether a model reasons about having been MOVED, `kindred` is a change to what
the village can know - and each already spends a second variable. Putting both in
one deck spends four and attributes nothing.

**Deck A, for `waker`: 6 seats, 3 centre, 9 cards.** `pack` x2, `spotter`,
`swapper`, `switcher`, `deceived`, `bystander` x2, `waker`.
- **Cutting a `bystander` to make room was the obvious move and it is the wrong
  one** - W-a halves the gate's own denominator, 1.02 blind seats per game to 0.51,
  to buy an instrument that measures something else. The blind stratum is already
  this game's bottleneck.
- Growing the TABLE beat growing the centre on every axis measured, which was not
  the armchair prediction: the centre is the cheaper second variable in principle,
  and the deal arithmetic says otherwise. W-c raises blind/game to 1.18 (+16% on
  shipped), nearly halves the unwinnable rate, and nearly halves the
  `identity`-told-nothing contamination, because a fuller table seats both `pack`
  cards more often.
- **One run carries its own control.** The `waker` is seated in 62.0% of games and
  sits in the centre in the rest, randomised within the run and on the same deck -
  so waker-present against waker-absent is one 200-game run, not a paired pair. It
  is a weaker comparison than same-seed pairing in one way (different deals, not
  the same ones) and a stronger one in another (no code freeze needed between
  arms). Report it as what it is.
- Cost: six seats is ~20% more model calls per game, and it moves wolf density from
  2/5 to 2/6. **The accusation baseline must be re-measured** with `--arm random`
  before any deduction claim - it is not derivable, which is why the shipped one was
  measured rather than asserted.

**Deck B, for `kindred`: 7 seats, 3 centre, 10 cards, plus a seating constraint.**
`pack` x2, `kindred` x2, `spotter`, `swapper`, `switcher`, `deceived`,
`bystander` x2.
- **On a free deal the pair FAILS to form more often than it forms** - lone 47.1%
  against pair 45.2%. Half of every run would spend a card measuring nothing about
  `kindred` while adding a second blind villager mislabelled `identity`, which is
  the section above happening twice.
- So the deck needs `require_seated_kin`: **both seated or both in the centre**, a
  deal retried otherwise. That is 0.92 retries per game against a
  `MAX_DEAL_ATTEMPTS` of 200, and it lifts the pair to 86.0%. **Built 2026-09-02**
  as a `Setup` field defaulting OFF, so the two shipped decks deal what they always
  dealt; `deal` applies it on top of `require_seated_pack` rather than instead of
  it, and an unsatisfiable pair of constraints raises `ImpossibleDeal` on the same
  structural bound. Measured on the built code: pair 87.6%, 1.07 retries a game.
- The precedent is exact and already in this file: `require_seated_pack` is a
  deliberate deviation from the family, publicly stated so every seat may reason
  from it, justified by keeping a tenth of every run from being noise. This is the
  same argument at twice the rate.
- The remaining 14% are games where both `kindred` are in the centre. They are not
  degenerate - the village simply plays without the card - and they are the
  natural control, on the same terms as deck A's.
- **`kindred` x3 with no constraint was tried and is worse** (75.1% pair, but 22.6%
  still lone, and a 9-card deck with three of them has no `bystander` left at all -
  blind/game 0.00, which deletes the gate). Constrain the deal; do not buy the pair
  with copies.

**Neither deck may be run before the class-assignment question above is settled**,
because both of them change how much of the `identity` stratum is blind seats, and
a deck comparison across that change measures the scorer rather than the deck.
**Settled by S10 and both decks are unblocked**; deck A has since run, and deck B
is registered and waiting on a measured bar rather than on this question.

### Notable expansions NOT built, and what each would cost

Costed here rather than half-built, because each buys something real and none is
data-only. In rough order of value per unit of engine surgery:

1. **A third win condition** (a seat that wins only by being pointed at). The
   cheapest *interesting* one: no night step at all, no new knowledge, one branch
   in the win check. It is the only proposal here that tests whether a model models
   another agent's OBJECTIVE rather than its information, and it breaks the binary
   `village`/`pack` outcome that the scorer, the baselines and `Side` all assume -
   which is the entire cost, and it lands on the scorer, not the night.
2. **An evil seat that sees the pack while the pack does not see it.** Asymmetric
   MEET: needs the `seen_by_own_kind` half that `meets_own_kind` currently has no
   partner for, exactly as `cabal` needed `seen_by_seer` beside `sees_evil`. Buys
   the honest version of the pack's coordination question - deception by a seat
   that knows its allies and cannot be confirmed by them.
3. **A card that copies another seat's card and then acts as it.** The game is
   named for this one, and it is the most expensive: the night stops being a fixed
   ordered pass and becomes recursive, since the copy must act at its copied step,
   which may already be behind. Every knowledge-invalidation argument in this file
   would need re-deriving.
4. **A mass positional shuffle** (rotate every other seat's card one place).
   Cheap - one act, no looking - and it stresses stale knowledge harder than
   anything in the deck. Left out because it degrades information without
   instrumenting anything, which is variety, and this file's bar is above variety.

## Day

`NIGHT -> DISCUSS -> VOTE -> DONE`

1. **Discuss.** Round-robin from seat 0, `discussion_rounds` passes. One utterance
   each, same 280-character cap as `cabal`. Only the nominated `say` string is
   published; a seat's private `think` reaches no one.
2. **Vote.** Every seat names exactly one OTHER seat. Simultaneous - no seat sees
   another's vote before casting. Naming yourself is refused, not coerced.
3. **Accusation.** The seat with the most votes is accused, **if it drew more than
   one**. On a tie at two or more, every tied seat is accused. **A vote in which no
   seat draws two accuses nobody** - the source's abstain rule, adopted 2026-09-02.
   Until then the referee took the top count whatever it was, so a one-finger-each
   vote accused all five seats and handed the village five draws at the wolf;
   **every changeling number recorded before 2026-09-02 was played under that
   rule**, and each record names the rule it was resolved under (`vote_rule`:
   `plurality` when the key is absent, `plurality-min2` since).

## Win conditions

Evaluated on **dawn truth**, never on belief or on the deal.

- **Village wins** if any accused seat holds `pack` at dawn - or if nobody was
  accused and no seat holds `pack` at dawn (2026-09-02; before that the no-wolf
  dawn was unwinnable, see §The deal constraint).
- **Pack wins** otherwise, which includes a flat vote while a wolf is seated.

A seat wins with the side of the card it HOLDS. A seat dealt `pack` and robbed
before dawn wins with the village, having spent the day lying for the wolves. A
`bystander` handed `pack` by the switcher loses with the wolves, having never been
told and never woken.

## The blind stratum is the bottleneck, and here it is affordable

THE GATE is cut on villagers the night told nothing. Measured on the powers run
above: **14 of 63 villager votes** were blind, giving a CI of [21.05%, 83.33%]
around a 50.00% point estimate against 37.50% chance. That interval cannot show
anything, whatever the model did.

**That 14 is a pre-S10 count and is too small** - it was cut on the old rule, which
labelled a MEET seat that met nobody `identity`. The census above puts the
understatement at ~19% of the blind stratum, so the re-run this section calls for
will find the denominator larger than the numbers here imply. It does not rescue
the interval: 14 votes and ~17 are both unreadable, and the argument for a 200-game
run is unchanged.

This is `cabal`'s thin-denominator problem again - and unlike `cabal`, it is
affordable here. At ~1.6 min/game a 200-game run is ~5 hours and yields ~140 blind
votes, which is the whole reason this rung was queued. Do not read a gate off 20
games; on this rung the N is the cheap part.

**Run and read 2026-08-28. It yielded 247 blind votes in 5.07 h** - the ~140 above
is a pre-S10 estimate and understates it for the same reason the 14 does. The read
is the section immediately below.

## S2 read - 200 games, gate #3 HOLDS (2026-08-28, pre-S14 wording)

**This is pre-S14 evidence.** S14 changed the model-facing self-line from a
post-night belief phrased as a sleep-state claim to the card actually dealt. The
recorded result remains historical evidence, not a verdict on post-S14 wording.

**The run.** `s2`, `--arm llm`, 200 games, `--seed 4000`, `--no-thinking`,
`qwen36-35b-a3b-iq3` local and 100% of the attribution, `PARLOR DONE rc=0
games=200/200 elapsed=18250s`. Recipe `eval/runs/changeling-local.cmd`, records
`eval/records/s2.json` and `s2.json.jsonl`. Five games seated no wolf at dawn and
are excluded and reported; 195 scored.

**Every number below is recomputable**: `py -3 -m eval.s5_verdict`, which
reproduces the published summary from the per-game records before deriving
anything and exits non-zero if it stops checking. The criterion it applies is
`queue.md` §PRE-COMMITTED CRITERION, written 2026-08-28 before the run and left
exactly as written.

### THE GATE, clause by clause

| clause | what landed |
|---|---|
| statistic: blind villager accuracy, `none` stratum, S10's told-based rule | **110/247 = 44.53%** |
| the bar: 35.95%, measured `--arm random`, n=4000 | **cleared** |
| it holds only if the **Wilson** 95% floor clears the bar | **Wilson floor 38.47%** [38.47%, 50.77%] |
| the scorer's own published interval (bootstrap over games) | floor **37.36%** [37.36%, 51.82%] |
| power: ~260 blind votes predicted | **247 landed** |
| the stratum floor: REFUSED below 150 votes | 247, clear |
| fallback above 10% voids | **0.40%** (12/3000), clear |
| recovered above 25% is flagged, never voids | **7.37%** (221/3000), under the bar |

**Gate #3 HOLDS.** The floor clears the bar on either interval and against every
bar on the table, so the call does not turn on which was used.

**Two clauses did not apply cleanly, and neither moves the call.** Recording them
rather than smoothing them over is the whole value of writing the criterion first.

- **The criterion says Wilson; the scorer publishes a bootstrap over games.** The
  bootstrap is the more conservative of the two - votes inside one game share a
  deal, a night and a table, so treating them as independent draws reports an
  interval tighter than the data supports. Both are printed above, both clear, and
  **the bootstrap is the one to quote** because it is the honest one. The criterion
  named the wrong instrument, not a wrong test.
- **S2 ran no random arm, so one clause had nothing to fire on.** The criterion
  said "the run must also report its own random arm; if that arm disagrees with
  35.95% by more than a point, the run's own arm is the bar". The 34.91% the log
  calls chance is a *derived* per-vote figure - the run's own mix of one- and
  two-wolf dawns, weighted by villager votes - not a measured arm, and the two are
  different objects. The bar used is therefore **35.95%**, the measured figure the
  criterion named. Three bars were on the table and the floor clears all three:

  | bar | value | what it is |
  |---|---|---|
  | criterion | 35.95% | measured `--arm random`, n=4000, pooled per vote |
  | the run's log | 34.91% | derived from this run's dawn-wolf mix, all villager votes |
  | diagnostic | 33.81% | the same derivation over the blind votes only |

  The third is a **diagnostic and never a bar** - promoting it would be choosing a
  statistic with the numbers in view. It is here because blind seats sit
  disproportionately in one-wolf dawns, so the run's own derived figure is already
  conservative for the stratum the gate is cut on.

  **35.95% survives S10 untouched**, which is why it is still usable: it is pooled
  villager accuracy under a random policy, and a random voter's accuracy does not
  depend on what the night told it. S10 re-keyed the knowledge class; it did not
  move a number that never conditioned on one.

**The power table reproduces at the N that landed.** At n=247 a true 42% clears
35.95% at the Wilson floor (36.11%) and a true 41% does not (34.94%) - the
criterion's "42% upward", computed before the run, is exactly right. So this run
could show a moderately good blind villager, and did; it could not have settled a
marginal one, and was not asked to.

### Gate #2 - readable, and still not a verdict

**Pack win rate 59.49%, Wilson [52.48%, 66.13%]**, on 195 scored games. Gate #3
holds, so the conditionality lifts and the rate is readable as deception rather
than as villagers handing the pack a win.

**It gets no verdict, and the criterion says why.** Gate #2 is scored against that
run's own random arm, which does not exist here, and `rate_ok`'s 5% CI-floor bar is
pre-declared nowhere and was explicitly not adopted. So gate #2 is **a rate with an
interval and no verdict**.

The 39.51% reference implies the pack takes 60.49% against villagers voting at
random - which sits *inside* the interval above. That is worth seeing and is not a
result: it is a different model on a different day, a reference point rather than a
control, and reading it as one is the comparison this file already warns against.
The honest statement is that this run cannot separate 59.49% from the no-deception
reference, and that a paired `--arm random` on the same seeds is what would.

### The three free reads

Named in the criterion before the run, scored off the same records, **none of them
a gate and none promotable to one**.

| read | result |
|---|---|
| `false` vs `none` | 42.86% (n=98) vs 44.53% (n=247), diff **-1.68%** [-11.54%, +8.52%] |
| sleeper-decoy rate | **72/689 village-holding seat-games = 10.45%**, in 68/195 games; they vote at 47.22% [36.13%, 58.60%] |
| diverged vs intact | 39.02% (n=305) vs 47.14% (n=384), diff **-8.12%** [-15.27%, -1.08%] |

- **A villager told a lie votes like a villager told nothing.** The `false`
  stratum's interval spans zero against `none`. The seat whose entitled knowledge
  is wrong by construction is the thing `cabal` has no analogue for, and on this
  run it is not distinguishable from the blind seat. One draw, and the interval is
  wide enough to hide a real effect either way.
- **Sleepers are a tenth of the village.** 10.45% of village-holding seat-games
  believed they were pack. They vote at 47.22% - above the blind stratum's point
  estimate, on overlapping intervals - which is the small surprise: a seat playing
  the day for the wrong side still points at wolves about as well as one that
  knows it is a villager.
- **Divergence costs about 8 points, and the interval excludes zero.** 98.9% of
  4000 game-resampled bootstraps put diverged below intact. This is the
  observation the rung was built to make - a seat playing the day as a card it no
  longer holds has every incentive of that card and none of the facts - and it is
  the first time the game has put a number on it. **It stays an observation.** It
  was named as a free read before the run and reporting it as a gate afterwards is
  the `hunt20b` error this repo has refused three times by name.

### What S2 did NOT deliver

**The powers re-run did not happen in S2** - its scope was the 2x20 powers arms on
the fixed lane *and then* the 200 games, and only the second landed. **It ran
2026-08-28** and the section above is now on clean numbers: the accuracy gain is
banked. The two rule-error counts were re-measured with a tracked instrument the
same day (`eval/rule_errors.py`) and the four old figures are retired - see §The two
rule-error counts, and note that the fall those figures asserted is not established.

## Waker-deck read - gate #3 HOLDS on six seats (2026-09-02, post-S14)

**The first post-S14 changeling evidence**, and the first on a deck other than
`SETUP_5`. `docs/changeling-waker-criterion.md` is the promise; this is the outcome,
clause by clause. Arithmetic `py -3 -m eval.waker_verdict`, transcript
`transcripts/changeling-waker1.md`, numbers `docs/measurements.md`. **Nothing here
is comparable to the S2 read below it** - different deck, different wolf density,
different bar, and S2 is pre-S14 wording besides.

**The run.** `waker1`, `--arm llm --seats 6 --seed 12000`, 200/200 games,
`PARLOR DONE rc=0 elapsed=20183s`, `qwen36-35b-a3b-iq3` local. Five games seated no
pack at dawn, excluded and reported; 195 scored. Fallback 0.31% of 3600, recovered
6.83%. No void fired.

Clause by clause, including the two that needed care:

- **The statistic held as pre-specified.** Blind villager accuracy on the `none`
  stratum, S10's told-based rule: **120/262 = 45.80%**.
- **BOTH floors were required in advance and both cleared.** Wilson 39.87%,
  game bootstrap 38.87%, against 30.14%. This is the clause S5 could not apply
  cleanly - it said Wilson where the scorer published a bootstrap - and stating
  both in advance is what stopped the same recording happening twice.
- **The own-arm clause came within 0.02 points of firing.** The criterion said "if
  that arm disagrees with 30.14% by more than a point, the run's own arm is the
  bar". The paired control read **31.12%** derived: a gap of 0.98% against a 1.00%
  tolerance. The bar therefore stayed the criterion's. It would not have mattered -
  both floors sit ~8 points above either candidate - but a clause that nearly fires
  is worth recording, because next time the coin lands the other way and the reader
  should already know the tolerance is tight.
- **Power reproduced at the landed N.** 262 blind votes against a predicted ~272;
  clears from a true 36% up, not from 35%, exactly as promised.
- **Gate #2 read, no verdict**, because the criterion declared no bar: pack win rate
  54.36% [47.35%, 61.20%].
- **The waker split reads as nothing, and the deck is not thereby refuted.** Seated
  45.68% over 162 blind votes, centre 46.00% over 100. **The waker seat is not in
  this denominator**: the gate counts villagers the night told NOTHING, and the
  waker is told what it holds. So this split was never where the card would show up,
  and reading it as "the waker changes nothing" would be reading the wrong stratum.
  What the deck bought is in the criterion's table - a lower chance bar, fewer
  unwinnable games, and 10.3% `identity`-told-nothing contamination against
  `SETUP_5`'s 18.7%. **Whether the waker seat itself votes better than the table was
  the question this deck was built to ask, and it is ANSWERED below - 
  against the like-for-like set, no.**

**One interim look is disclosed.** At game 50 the blind stratum was inspected to
check the criterion's power assumption; the gate statistic was printed in the same
pass. Nothing was acted on and the arm ran its full 200, so the fixed-N analysis
stands - but this criterion spends no alpha, so the interim figure has no standing
and is cited nowhere. Recorded rather than omitted, because an undisclosed look is
exactly what group-sequential design exists to prevent, and the queue carries an
open row saying that design must be built BEFORE a campaign rather than retrofitted.

### The waker seat's own read - answered 2026-09-02, and the answer is "not shown"

The criterion pre-registered this as an observation with no bar. It stays one, and
the numbers are in `docs/measurements.md`. The finding in one line:

**Against every other villager the waker is +8.37% [1.46%, 14.87%]; against the
`identity` stratum alone it is +6.96% [-2.11%, 15.98%], which spans zero.**

The first difference is close to tautological and should not be quoted on its own.
The table it compares against includes blind villagers the night told NOTHING, so
any seat holding information beats them - that measures having knowledge, not
having knowledge about YOURSELF. The like-for-like set is the seats that also know
a card, and against those this run shows nothing.

That is the deck's own question, and the honest answer at 122 waker votes is **not
shown**, not "no". One vote per game is the ceiling the criterion named before the
run, and it is the binding constraint here rather than the effect being absent: the
point estimate leans the right way throughout. A deck that seated two waker-class
cards, or a longer arm, is what would settle it - and either is a NEW criterion,
never a re-read of these records.

## The chance baseline, MEASURED (2026-08-26) - under the pre-2026-09-02 vote rule

**Every figure in this section and the S2 / waker-deck reads above was played
under `plurality`**: a flat tally accused everyone. Under `plurality-min2` a flat
tally accuses nobody, so the tie share, the village share and the 2.7% unwinnable
residual all move, and the first `--arm random` sweep on the new rule re-baselines
this table rather than extends it.

**Re-measured 2026-09-02 under `plurality-min2`** - `--arm random`, 5 seats, 1
round, n=4000, `--seed 0` (game i deals with seed i), fallback 0/40000 by
construction, `vote_rule` recorded on every game:

| | under `plurality` (above) | under `plurality-min2` |
|---|---|---|
| **village wins, scored denominator** | 39.51% | **35.42%** [33.93%, 36.93%], 1377/3888 |
| village wins, all games | 38.45% | 34.60% (1384/4000; NOT comparable to a run figure) |
| villager accuracy (per vote) | 35.95% | **35.84%** [34.99%, 36.71%], pooled per vote |
| multi-seat accusations (ties) | 32.4% | **28.18%** [26.80%, 29.59%] |
| nobody accused (flat tally) | 0 by construction | **4.25%** [3.67%, 4.92%], 170 games |
| dawn wolves: 0 / 1 / 2 seats | 107 / 1908 / 1985 | 112 / 1908 / 1980 |
| village wins by dawn-wolf count | 0.0% / 28.2% / 50.6% | 6.3% / 23.85% / 46.57% |

The pack now takes **64.58%** [63.07%, 66.07%] against villagers voting at random,
up from 60.49%: the abstain rule removes the draws a flat tally used to hand the
village, and both the tie share and the village share fall with it. Per-vote
accuracy does not move, which is the arithmetic - a random vote hits a wolf at the
same rate whatever the tally does with it afterwards. The 0-wolf column is no
longer zero because a flat tally with no wolf seated is the source's village win
(nobody dies, no wolf), 7 of 112 games here; the scorer still excludes those 112
from the denominator, which is why the two "all games" figures differ from the
scored ones by different amounts. **Every S2 / waker-deck read above stands as a
read under the old rule; a new run is compared to THIS column.**

`cabal` can state its hunt baseline as 1-in-3 because the hunter's legal target set
is a closed derivation. This game's accusation baseline is not derivable that way -
it depends on the tie rule, on how many seats hold `pack` at dawn, and on the vote
distribution a policy produces. So it was measured, never asserted.

**`--arm random`, 5 seats, 1 round, n=4000 games, uniform random votes:**

| | |
|---|---|
| **village wins, scored denominator** | **39.51%** (winnable games only - the denominator every run reports on) |
| village wins, all games | 38.45% (includes the unwinnable 2.7%; NOT comparable to a run figure) |
| villager accuracy (per vote) | **35.95%**, against a computed chance of 35.93% |
| multi-seat accusations (ties) | 32.4% of games |
| dawn wolves: 0 / 1 / 2 seats | 107 / 1908 / 1985 |
| village wins by dawn-wolf count | 0.0% / 28.2% / **50.6%** |

Three things fall out, and each one would have made a hardcoded fraction wrong:

- **The baseline is not one number.** It nearly doubles between a one-wolf and a
  two-wolf dawn, and which of those a game is cannot be known in advance. Any
  deduction claim must condition on it or report the mix.
- **A third of games end in a tie**, and every tied seat is accused, so the random
  arm gets several draws at the wolf. That is a large part of why 38.5% sits so far
  above a naive 1-in-4.
- **2.7% of games have NO wolf seated at dawn, and the village cannot win them.**
  See below - this is a defect in the deal constraint, not a property of play.

### The public rules text has to state what each card DOES (measured 2026-08-27)

The first live game shipped a preamble that listed the deck **by name only**. That
looked complete and was not: the central deduction of this game is counting claims
against the multiset, and a seat that does not know what a card does cannot
evaluate anyone's claim about holding one. So the models invented powers and
reasoned from the inventions.

Two misconceptions recurred, both rules errors rather than bad play:

- **"my card did not move."** A seat asserting certainty about its own dawn card,
  which negates the belief/truth split outright - a seat that believes its belief
  IS its truth is playing `cabal` in its head.
- **The switcher believing it swapped its OWN card.** It exchanges two other seats'
  cards and its own act never touches its own card. Exactly inverted.
  **It is still not the seat that always knows what it holds**, which this section
  used to claim: `TAKE` runs before `SWITCH`, so the swapper robs it in 15.0% of
  deals (§The two rule-error counts). Its own power tells it nothing; another card
  can still move it.

Fixed by listing the deck **in night order, with each card's power**. The order is
public rules and does real work: it is what lets a seat reason about whether a
reading could since have gone stale. Powers are written without naming any other
card, so the text stays byte-identical across seats and carries no association a
leak could ride on - the audit exclusion in the previous section still holds, and
`audit_all` is clean over 500 deals with it in.

**RE-RUN ON THE FIXED LANE 2026-08-28, and the accuracy gain is now BANKED.** The
2026-08-27 pair predated the review fixes - the sampler seed was pinned to the run's
base rather than each game's - so its paired comparison stood while its absolute
rates did not. Both arms were re-run at `af7e6a0`-and-later on identical deals,
confirmed game for game, and the table below is that pair.

**Measured, same seeds, one variable** - 20 games, `qwen36-35b-a3b-iq3`,
`--no-thinking`, seed 1000, deals confirmed identical across arms:

| | before (name only) | after (night order + powers) |
|---|---|---|
| **BLIND accuracy** - the cut the gate is taken on | 15.00% (3/20) | **55.00%** (11/20) |
| villager accuracy | 30.16% (19/63) | **53.97%** (34/63) |
| village win rate (18 scored games) | 22.22% | 50.00% |
| pack win rate | 77.78% | 50.00% |
| fallback rate | 3/300 = 1.00% | 2/300 = 0.67% |
| recovered | 23/300 = 7.67% | 18/300 = 6.00% |
| clean games | 3/20 | 8/20 |
| wall clock | 1756s | 1789s (+1.9%) |

**The accuracy gain IS claimed now, and that is what the re-run bought.** Paired
bootstrap over games, resampling the 18 scored games as units:

| | paired delta | 95% CI | floor |
|---|---|---|---|
| villager accuracy | **+23.81pp** | [+4.55pp, +42.42pp] | clears zero |
| **blind accuracy** | **+40.00pp** | [+13.64pp, +66.67pp] | clears zero |

The 2026-08-27 pair put villager accuracy at +17.46pp with a floor of -1.56pp and
this file declined to bank it, citing `hunt20b`'s +8.82% [+0.94%] inverting to
`hunt20c`'s +9.00% [-0.25%] on identical code. That caution was right and the redraw
answered it: on clean code and identical deals the effect is larger and the floor
clears. **Reproduce with the arm records themselves** - the derivation reproduces
each arm's own published figure before deriving any delta, and both arms are
`eval/records/cl-powers-{before,after}2.json`.

Cost of the fix is **1.9% wall clock**, not the 16% the seed-bug pair reported.

### The two rule-error counts, RE-MEASURED 2026-08-28 - and the fall is not significant

The instrument is `eval/rule_errors.py`, its definitions are stated in that module's
docstring, and it scores both pairs off records already on disk:

```
py -3 -m eval.rule_errors            # both pairs, both errors, the paired delta
py -3 -m eval.rule_errors --show B   # every matching sentence, for hand-reading
```

On the clean 2026-08-28 pair, out of 200 utterances per arm:

| | before | after |
|---|---|---|
| A, claiming own card unmoved | 5/200 = 2.5% | 2/200 = 1.0% |
| B, the switcher self-swap error | 13/200 = 6.5% | 6/200 = 3.0% |
| **either** | **18/200 = 9.0%** | **8/200 = 4.0%** |
| fallback rate | 1.00% | 0.67% |

**The paired fall is -5.0pp, 95% CI [-10.5pp, +0.0pp] over a 10k game bootstrap -
the floor touches zero.** The same instrument on the 2026-08-27 pair gives
7.0% -> 2.5%, -4.5pp [-9.5pp, +0.0pp]. So the direction is consistent across two
independent pairs and the effect is not established at n=20 games per arm. **The
powers text is still the right rules text** - a public rules statement that omits
what each card does is wrong whatever the error count says - but it is no longer
carrying a measured -10pp behind it.

**The four figures below are RETIRED. Do not quote them.**

| | before | after |
|---|---|---|
| A, from the uncommitted script | 18/200 = 9.0% | 2/200 = 1.0% |
| B, from the uncommitted script | 4/200 = 2.0% | 0/200 = 0.0% |
| **either** | **11.0%** | **1.0%** |

They came from a script that was never committed, and with it went the `-10pp` claim
and its 95% CI [-18.3pp, -1.7pp]. Three things the re-measurement establishes about
them, each of which changes how an old record reads:

- **B's `0.0%` was never true.** The tracked instrument scores 4/200 on that same
  after arm - reproducing the hand-read in `queue.md` sentence for sentence, which
  is this module's control - and 6/200 on the clean one. Two of those hits carry no
  correct statement at all, e.g. *"I exchanged cards with seats 1 and 3, but I have
  no idea what I'm holding now"* from a seat dealt `switcher`.
- **A's `18/200` is not recoverable.** The tracked proxy scores 5-6 before, and no
  definition consistent with the semantics above reaches 18. The original was much
  broader than anything written down about it. It is retired rather than
  reconstructed: tuning a pattern until it reaches its target is fitting the
  instrument to its answer.
- **One disagreement is stated rather than reconciled.** On the 2026-08-27 before
  arm the tracked instrument scores 8 for error B against the hand-read's 11. The
  hand-read's own pattern was never written down either, so there is nothing to
  reconcile against; the module prints the gap on every run.

**And B is an upper bound, because `RULES.md` was wrong about the switcher.** This
file used to call it "the one seat that always knows what it holds". It is not:
`TAKE` runs before `SWITCH` in `NIGHT_ORDER`, so the swapper can rob the switcher.
Measured over 4000 nights of the shipped deck, **350/2340 = 15.0%** of seats dealt
`switcher` diverge anyway (`py -3 -m eval.rule_errors --floor`). A seat correctly
suspecting it was robbed is lexically indistinguishable from one that misread its
own power, so a residue of a few percent is expected and is not evidence the fix
failed.

### The deal constraint does not do what it was written to do

`require_seated_pack` guarantees a `pack` is **dealt**. It does not guarantee one is
**held at dawn**, because the night can move a wolf card into the centre: the
`DRINK` seat swaps whatever it is holding by then - which the `TAKE` or `SWITCH`
step may have made `pack` - for a centre card, and `DRINK` is last.

Measured residual: **107/4000 = 2.7%** of games, down from the 10.7% an
unconstrained deal would give. Those games are unwinnable by the village however
well it plays, so they belong in a deduction denominator the way a fallback belongs
in a gate number: **excluded, and reported.** Do not quietly average them in.

**Since 2026-09-02 these games are winnable**: under the abstain rule a vote in
which no seat draws two accuses nobody, and with no wolf seated that is a village
win. `eval.s5_verdict.winnable` still excludes them, correctly for the records it
was written against; an instrument for post-change records must not.

The honest options were to accept and exclude (the state until then), or to make `DRINK` refuse to
send a `pack` to the centre - which is a rule the seat could not know it was
following, so it changes the game rather than fixing it. Left as is, on the record,
until a measurement says the 2.8% matters.

## The two public channels, and the line between them

Unchanged from `cabal`, and load-bearing for the same reason.

- **Events** are referee-authored facts: phase transitions, the vote tally with
  attribution, the accusation. Audited by gate #1.
- **Speech** is what a seat chose to say. A lie there is gameplay, not a leak, so
  the audit skips it.
- **Private reasoning reaches neither.**
- **Night results are private and are never re-derivable from events.** The referee
  publishes that the night happened, never who woke, acted, or moved what. A seat
  that woke and a seat that slept must be indistinguishable in the public record -
  otherwise the card multiset plus the event log identifies roles by elimination.

### The gate #1 obligation this rung adds

`find_leaks` in `core/observability.py` skips the viewer's own seat, because in
`cabal` a seat is always entitled to its own role. **That assumption does not hold
here.** A seat whose belief has diverged from its truth is NOT entitled to its own
truth, and a render that leaks it is a gate #1 failure that the current audit
cannot see. The audit must be able to treat the viewer's own truth as a secret from
the viewer.

This is the first evidence-backed pressure on `core/`, and it is exactly the
question the ladder was built to ask: the primitive was written when belief and
truth were the same thing, and a second game shows which half of it was an
assumption. `find_leaks` now takes `self_is_secret`, defaulting off so `cabal` is
unchanged, and the flag lives in the primitive rather than in the caller because
the skip it removes lived there - a game cannot opt out of a rule applied before
it is asked.

### A secret is an ASSOCIATION here, not a card name

The second thing this rung found, and it landed as a false-positive storm rather
than as a leak: **this deck holds duplicates.** Two `pack`, two `bystander`. So a
card name is not a seat's secret. Telling a wolf that seat 4 is its partner puts
"Werewolf" in the bytes and says nothing whatever about the *other* wolf, and a
naive scan for the bare name flagged 290 of 300 deals.

`cabal` never had this. Its role keys are unique, so a term identified a seat, and
the repo invariant's remedy for a collision - rename the term - works there. It
cannot work here: the collision is the game. Renaming one `pack` breaks the deal.

So the audit matches on the **exact strings the referee would emit to tie a seat to
a card**, which is still naive substring matching, only over a richer term. That
buys precision at the cost of a false-negative risk: a phrasing written somewhere
else would tie a seat to a card in bytes the audit never searches, which is the
shipped leak the invariant exists to prevent. **The risk is answered structurally,
not by care.** `referee.reveal_forms` is the single source of every such phrasing,
`_knowledge_line` builds its output from it, and a test asserts that every line the
renderer can produce is a member of it. A new phrasing is audited by construction,
or it fails a test.

Two further scopes make the audit sound, and both are argued rather than
convenient:

- **The preamble is excluded**, because it must name every card in the deck -
  counting claims against the multiset is the central deduction - and because it is
  byte-identical for every seat. A string that is the same for all seats carries no
  information about any seat. A test asserts the invariance; the moment a seat fact
  is interpolated into it, that assertion is what catches it.
- **A seat's own card is audited in both persons, at the scope each phrasing can
  reach.** The referee addresses a seat in the second person about itself and in the
  third person about everyone, so a self-leak has two shapes. The second-person form
  is `self_reveal_forms` against `self_line`, which is the only place the referee
  asserts anything about a seat to that seat in that voice. The third-person form is
  the seat's ordinary `reveal_forms` association against its whole context, with
  `entitled_seats` - which adds the viewer exactly when belief and truth agree -
  deciding whether it may appear.

  **The third-person half was missing until 2026-09-02**, and it was a false
  negative rather than a scope: the first scan excluded the viewer outright. But
  `TAKE` and `WAKE` record a `Knowledge` about the acting seat ITSELF, so
  `_knowledge_line` writes "Seat 4 held the X." into seat 4's own render - correctly,
  as history. A referee that refreshed that label to dawn truth would leak the seat's
  card back to it in exactly the phrasing the scan was already searching for, about
  the one seat it was not searching. Measured against that mutant: **470 leaks over
  15000 seat-games, none caught; 0 false positives on the honest renderer over the
  same 15000.** `test_referee` carries both halves.

- **`dealt.key != held.key` on the second-person scan is not a bypass.** It reads
  like one, and was filed as one. When the dealt and dawn cards are the same card, a
  referee rendering the deal and one rendering dawn truth emit byte-identical lines -
  measured, 129 of 15000 seat-games, identical in all 129. There is no leak to
  detect there, and the only thing the scan could report is the honest deal. A
  test covers the state rather than a comment claiming it.

## Themes are display-only

As in `cabal`: a `Theme` renames sides and roles and carries a premise blurb. It
changes no rule, no entitlement, and no byte of private knowledge - and is
therefore a MEASURED change, not a cosmetic one.

One thing more than `cabal`'s: a skin also names **the centre**, the three
face-down cards that belong to nobody. It is the only piece of furniture on this
table, it is named in three separate places a seat reads - the power clauses, the
face-down line, and a centre reveal in its own night - and a skin that renamed two
of the three would be describing two different tables. `Card.power` is therefore a
template with a `{centre}` slot rather than a finished string; the clause it states
stays theme-independent, because a skin that reworded a power would have stopped
being display-only. The functional word is the default, so the shipping faces
render exactly what they rendered before the field existed.
