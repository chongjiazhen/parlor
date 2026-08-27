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

1. `pack` - the pack wakes together and sees its own members.
2. `spotter` - looks.
3. `swapper` - takes, and looks at what it took.
4. `switcher` - swaps two other seats, blind.
5. `deceived` - swaps itself with a centre card, blind.

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
different axis from side. It describes **what the night told this seat**, and it is
assigned from the DEALT card, because that is what determines the reveal.

| dealt card | knowledge class | what it holds |
|---|---|---|
| `pack` | `identity` | the other `pack` seat, by identity |
| `spotter` | `identity` | one other seat's exact card, or two centre cards |
| `swapper` | `identity` | its own new card, and that its victim now holds `swapper` |
| `switcher` | `positional` | that seats A and B exchanged. **Not what either one is** |
| `deceived` | `false` | a belief about itself that is wrong by construction |
| `bystander` | `none` | nothing |

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

## Day

`NIGHT -> DISCUSS -> VOTE -> DONE`

1. **Discuss.** Round-robin from seat 0, `discussion_rounds` passes. One utterance
   each, same 280-character cap as `cabal`. Only the nominated `say` string is
   published; a seat's private `think` reaches no one.
2. **Vote.** Every seat names exactly one OTHER seat. Simultaneous - no seat sees
   another's vote before casting. Naming yourself is refused, not coerced.
3. **Accusation.** The seat with the most votes is accused. **On a tie, every tied
   seat is accused.**

## Win conditions

Evaluated on **dawn truth**, never on belief or on the deal.

- **Village wins** if any accused seat holds `pack` at dawn.
- **Pack wins** otherwise.

A seat wins with the side of the card it HOLDS. A seat dealt `pack` and robbed
before dawn wins with the village, having spent the day lying for the wolves. A
`bystander` handed `pack` by the switcher loses with the wolves, having never been
told and never woken.

## The blind stratum is the bottleneck, and here it is affordable

THE GATE is cut on villagers the night told nothing. Measured on the powers run
above: **14 of 63 villager votes** were blind, giving a CI of [21.05%, 83.33%]
around a 50.00% point estimate against 37.50% chance. That interval cannot show
anything, whatever the model did.

This is `cabal`'s thin-denominator problem again - and unlike `cabal`, it is
affordable here. At ~1.6 min/game a 200-game run is ~5 hours and yields ~140 blind
votes, which is the whole reason this rung was queued. Do not read a gate off 20
games; on this rung the N is the cheap part.

## The chance baseline, MEASURED (2026-08-26)

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
  cards and its own is untouched, so it is the one seat that always knows what it
  holds. Exactly inverted.

Fixed by listing the deck **in night order, with each card's power**. The order is
public rules and does real work: it is what lets a seat reason about whether a
reading could since have gone stale. Powers are written without naming any other
card, so the text stays byte-identical across seats and carries no association a
leak could ride on - the audit exclusion in the previous section still holds, and
`audit_all` is clean over 500 deals with it in.

> **Both arms below predate the review fixes of 2026-08-27** - the sampler seed was
> pinned to the run's base rather than each game's. Both arms carried it identically
> on identical deals, so the PAIRED comparison stands; the absolute rates inherit it
> and are not a clean estimate of what this model does per game.

**Measured, same seeds, one variable** - 20 games, `qwen36-35b-a3b-iq3`,
`--no-thinking`, seed 1000, deals confirmed identical across arms:

| | before | after |
|---|---|---|
| utterances claiming own card unmoved | 18/200 = 9.0% | 2/200 = **1.0%** |
| utterances with the switcher self-swap error | 4/200 = 2.0% | 0/200 = **0.0%** |
| **either** | **11.0%** | **1.0%** |
| villager accuracy | 38.10% | 55.56% |
| village win rate (18 scored games) | 33.33% | 55.56% |
| fallback rate | 0/300 | 1/300 |
| wall clock | 1631.7s | 1896.2s (+16%) |

**The rule-error rate is what justifies the change**: -10pp, 95% CI [-18.3pp,
-1.7pp], 99.1% of resamples showing a decrease, on a 200-utterance denominator.

**The accuracy gain is NOT claimed.** +17.46pp looks large and is in the predicted
direction, but a paired bootstrap over games gives 95% CI [-1.56pp, +36.07pp] - the
floor touches zero at n=18 games. This repo watched `hunt20b`'s +8.82% [+0.94%]
invert to `hunt20c`'s +9.00% [-0.25%] on identical code the same week. A floor
within 2pp of zero is the number that flips on redraw, so it is recorded and not
banked.

Cost of the fix is 16% wall clock, from the longer preamble on every call.

### The deal constraint does not do what it was written to do

`require_seated_pack` guarantees a `pack` is **dealt**. It does not guarantee one is
**held at dawn**, because the night can move a wolf card into the centre: the
`DRINK` seat swaps whatever it is holding by then - which the `TAKE` or `SWITCH`
step may have made `pack` - for a centre card, and `DRINK` is last.

Measured residual: **107/4000 = 2.7%** of games, down from the 10.7% an
unconstrained deal would give. Those games are unwinnable by the village however
well it plays, so they belong in a deduction denominator the way a fallback belongs
in a gate number: **excluded, and reported.** Do not quietly average them in.

The honest options are to accept and exclude (current), or to make `DRINK` refuse to
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
- **A seat's own card is audited against its own line only.** `self_line` is the
  only place the referee asserts anything about a seat to that seat, so it is the
  only place a self-leak can live. Auditing a seat's own term against its whole
  context would fire every time a wolf is told about its partner.

## Themes are display-only

As in `cabal`: a `Theme` renames sides and roles and carries a premise blurb. It
changes no rule, no entitlement, and no byte of private knowledge - and is
therefore a MEASURED change, not a cosmetic one.
