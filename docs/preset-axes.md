# Preset axes - why the endgame is not one engine with a flag list

**2026-08-28, unmeasured.** A design decision, not a result. It exists because a
session asked the obvious next question after `docs/content-packs.md`: if a rung
loads a pack, could every system parlor ever runs be a *preset* over one
configurable engine - d20 or d6, skills or no skills, narrative resolution or
tabular, referee or no referee, each a flag?

**The answer is no, and the useful part is why.** The options that look like
flags are three different kinds of thing, and only one kind composes.

## The pattern, named

Configurable-by-toggle is an established tabletop design pattern, and published
toolkit systems that work this way describe themselves in exactly those terms - a
box of parts to assemble a game from rather than a game. The cost is stated in
their own reception: a toolkit hands the table a design job before it hands them
a playable game, and doing that job well takes more skill than running a finished
system does. Borrowing the pattern is fine. Borrowing it whole means inheriting
that.

Which systems those are, and how well each is thought to work, is assessment of
somebody else's design and stays in the working notes - the division
`docs/action-channel.md` and `docs/content-packs.md` already draw.

## The three axes, and only one of them is a flag space

- **Entitlement schema - universal, and it is the product.** Who is entitled to
  which fact, when, and by what trigger. This is `entitled_knowledge`,
  `render_context`, `find_leaks` and the fact-keyed adapter the DURF rung already
  built. It genuinely does not vary with genre, and it genuinely is flag-shaped:
  a scope (`public`, `team`, `seat`, `referee-only`), a timing, a revelation
  trigger. Every system parlor could host expresses cleanly here, including the
  ones it will never ship.

- **Resolution kernel - a registry, not a flag set.** One narrow interface,
  `resolve(intent, state) -> outcome`, and one implementation per family: roll
  against a target number, count a pool, read a tiered partial-success table,
  play from a private hand, look up a rank, or decide with no randomiser at all.
  Each is small. They do not need to compose, they need to be swappable, and a
  registry gives that where a flag matrix gives a cross-product nobody asked for.
  **This is where the mutually-exclusive options collapse.** "d20 or d6" is one
  line in a registry entry; it was never the hard part.

- **Authority topology - a small closed set.** Who holds discretion:
  deterministic referee, model adjudicator, distributed across the seats with no
  authority seat at all, or a table plus a fixed interpretation rule. Four
  values, not flags, because the value decides what `referee.py` *is* rather than
  how it behaves. The ladder in `README.md` is already sorted on this axis; this
  is the axis, named.

A rung is then `(entitlement schema, resolution kernel, authority mode, pack)` -
four dimensions and a few dozen meaningful combinations, against 2^N for a flag
list.

## What is genuinely a flag

Toggles that change the referee's **parameters** and not its job: a variant
scoring rule, an optional phase, a table size, a difficulty band. Those are
per-rung, cheap, and already how the deduction ladder handles its variants. The
test is mechanical - if the toggle changes what the referee has to adjudicate, or
who adjudicates it, it is an axis and not a flag.

## The measurement collision, which is the real argument

Every number ships beside its fallback rate. **A flag list is N independent
claims wearing one measured claim's name**: 2^N configurations, each with its own
fallback rate, none of them measured, and no record says which cell a number came
from. The axes above are bounded precisely because each value is a thing a run
can be labelled with, the way `docs/action-channel.md` requires `strict` and
`free` to be an arm rather than a default.

So the honest scope of any generality claim here is a matrix that was actually
run: a few kernels against a few authority modes on **one** pack, holding content
fixed, for the same reason `--seed` seeds the sampler - one variable, or it is
not a comparison.

## Where the formal prior art stops

The general-game-playing literature has already built the good version of
"games are configurations of a shared vocabulary", and has a universality proof
for it: **arXiv:2205.00451** (*abstract and introduction read at source
2026-08-28; the proof itself unread*) proves that language capable of
representing any **finite** non-deterministic imperfect-information game,
extending an earlier result that covered the finite deterministic
perfect-information alternating-move case.

**Read the boundary precisely, because the loose version of it is wrong.** The
proof's class is finite games; the language is not confined to them, and that
paper says so itself, naming a game with an infinitely-sized tree that it can
still express. So the honest statement is about what has been *proven*, not about
what a description language can reach.

The value here is the shape of the class, not a limit on anyone's language. Every
rung on the deduction ladder is a finite game with a bounded action set and sits
squarely inside it. The endgame rung is the one that leaves: an unbounded
declaration channel has no enumerable action set to describe, which is the same
property `docs/action-channel.md` identifies when it says the closed-phase shape
generalises to the other deduction games and not to the RPG. **That is why the
adjudicator is a seat and not a grammar** - not because a grammar could not be
written, but because writing one means enumerating the thing whose refusal to be
enumerated is the rung's entire content.

### The same boundary, reached twice, and only one of them hands over a mechanism

**The two results are not a supersession, and the later paper says so itself.**
arXiv:2205.00451 never names GDL-II. It calls the Stanford language S-GDL, refers
to "an extension to support randomness and imperfect information", and states its
own contribution as proving "that it can represent the same class of games as
proven by Thielscher for S-GDL, including games with randomness and hidden
information" - concluding that "the expressiveness of L-GDL matches that proven by
Thielscher for S-GDL". Equal expressiveness over the same class, twelve years
apart. Any supersession claim between them is about efficiency and tooling, which
is a general-game-player's concern rather than this repo's.

**What differs is the mechanism, and the mechanism is the half parlor uses.**
L-GDL represents hidden information as marker pieces on graph vertices with
information-set regions, so a player observes a subgraph of a board. **GDL-II**
(Thielscher, *A General Game Description Language for Incomplete Information
Games*, AAAI-10; PDF read at source 2026-08-28) states it instead as rules that
derive what each player perceives. parlor has no board and no graph; it has facts
and a channel. So the percept form maps onto `entitled_knowledge(seat)` directly
and the board-observation form does not, which is why the citation below is the
one this repo builds on.

It extends the earlier description language with exactly two keywords. `random` is
a special player who chooses its moves randomly, so dice and shuffling are a
**role** rather than referee bookkeeping. `sees(R,P)` means "R perceives P in the
next position", and it carries the entire information model:

> players are no longer informed about each other's moves by default; rather, they
> only get to see what the game rules entail about their percepts

and, on the same page:

> despite full initial information, both incomplete knowledge about later states
> and asymmetry of information result from the individual and partial percepts

**That is default-deny as a language semantics, and it is the property this repo's
README argues for.** Reading it makes parlor's claim narrower and better: the idea
of per-seat percepts is formalised prior art, so what is left is the part that was
always the actual contribution - a machine-checked audit over a channel a MODEL
writes, where the sender can paraphrase and the entitlement has to be checked
rather than derived.

Three things worth taking, and they are free because a semantics is not code:

- **Vocabulary.** *Percept* and *information set* are the established terms for an
  entitled fact and for what a seat can distinguish. Same reason to borrow as the
  megagame terms already noted elsewhere.
- **Randomness as a role.** If the deal is an actor with legal moves, the same gate
  audits it that audits every other seat. parlor's referee currently owns the dice,
  so the deal is bookkeeping the audit has to be told about separately.
- **A refusal is a percept.** Their arbiter pattern is `sees(R,badMoveTryAgain)`
  when a submitted move is invalid. parlor's refuse-and-re-prompt loop treats the
  kernel's error text as plumbing and counts a fallback. Under this reading that
  text is information delivered to one seat, which makes it entitled bytes and puts
  it inside gate #1's scope rather than beside it. **This is the actionable one.**

Its limits are the same shape as the result above: enumerable moves, automated
players, and no discretionary seat anywhere in the model. So it bounds the axis
without covering the rung that leaves the bound.

**It is also a reason not to build a DSL.** That work needed one because an
automated player had to read the description and a whole corpus had to be written
in it. Here a person picks the preset, so a typed interface per axis is the whole
implementation, and a language would be the second thing to encode game #1.

## What this does not decide

The schema, same as `docs/content-packs.md` - write it against two rungs, not in
advance. Nothing here says a second kernel is worth building yet; **the axes are a
claim about shape, and shape is cheap to state and expensive to retrofit**, which
is the only reason to state it before the evidence.
