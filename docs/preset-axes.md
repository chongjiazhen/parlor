# Preset axes - why the endgame is not one engine with a flag list

**2026-08-28, unmeasured.** A design decision, not a result. It exists because a
session asked the obvious next question after `docs/content-packs.md`: if a rung
loads a pack, could every system parlor ever runs be a *preset* over one
configurable engine - d20 or d6, skills or no skills, narrative resolution or
tabular, referee or no referee, each a flag?

**The answer is no, and the useful part is why.** The options that look like
flags are three different kinds of thing, and only one kind composes.

## The pattern, named

Configurable-by-toggle is an established tabletop design pattern with three
decades of published instances behind it, and its known failure mode is
published too: past a certain count the toggles stop being a convenience and
become a decision the table must make before anything is playable. Borrowing the
pattern is fine. Borrowing it whole means inheriting that.

Whose instances those are, and how well each is thought to work, is assessment of
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
for it: **arXiv:2205.00451** (*abstract read at source 2026-08-28, body unread*)
proves that language capable of representing any **finite** non-deterministic
imperfect-information **extensive-form** game, extending an earlier result for
the finite deterministic fully-observable case.

That boundary is the citation's whole value here. parlor's deduction rungs sit
inside it; the endgame rung does not, because an unbounded declaration channel is
not a finite extensive-form game. So the proof marks where a description language
stops covering this problem rather than covering it, and it is the reason the
adjudicator is a seat rather than a grammar.

**It is also a reason not to build a DSL.** That work needed one because a search
agent had to read the description. Here a person picks the preset, so a typed
interface per axis is the whole implementation, and a language would be the
second thing to encode game #1.

## What this does not decide

The schema, same as `docs/content-packs.md` - write it against two rungs, not in
advance. Nothing here says a second kernel is worth building yet; **the axes are a
claim about shape, and shape is cheap to state and expensive to retrofit**, which
is the only reason to state it before the evidence.
