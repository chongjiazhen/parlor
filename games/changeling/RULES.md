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

## No chance baseline is asserted here

`cabal` can state its hunt baseline as 1-in-3 because the hunter's legal target set
is a closed derivation. **This game's accusation baseline is not derivable that
way** - it depends on the tie rule, on how many seats hold `pack` at dawn (one or
two, and the deal constraint bounds but does not fix it), and on the vote
distribution a policy produces. Any number quoted as "chance" here must come from a
measured `--arm random` run, not from arithmetic in this file. Writing a plausible
fraction here and scoring against it is the exact failure the `cabal` gate #3a
strata were rebuilt to remove.

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
assumption.

## Themes are display-only

As in `cabal`: a `Theme` renames sides and roles and carries a premise blurb. It
changes no rule, no entitlement, and no byte of private knowledge - and is
therefore a MEASURED change, not a cosmetic one.
