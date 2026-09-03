# The action channel, and what the RPG rung breaks

Written 2026-08-25, unmeasured, from a design read of `core/replies.py`,
`referee.action_prompt`, and `player.parse_action`. Nothing here is a decision
yet; it is here so the cheap moves stay cheap. **Extended 2026-08-28** with the
adjudicator's call-vocabulary constraints and the two kernel-owned failures, so
that the scoping session for that rung inherits them from the tree rather than
from a working note.

**Free-text JSON stays the action channel for the deduction ladder.** No model in
this repo ever gets a tool schema. Two reasons, both about the numbers rather
than ergonomics: local llama.cpp/Kobold backends and the cloud tiers implement
function-calling at wildly different fidelity, so a tool schema makes the harness
a per-model variable in exactly the comparison being run; and a truncated
tool-call leaves nothing for `salvage()` to scrape, converting a recoverable
reply into a fallback, which is the quantity the scorer voids on.

**Constrained decoding is the real upgrade, and it belongs behind a label.** GBNF
on llama.cpp, `response_format: json_schema` on cloud, would drive fallback rate
toward zero. It must not become the default: every number ships beside its
fallback rate, and grammar-forcing DELETES that signal rather than improving it.
If it lands, it lands as a recorded arm (`strict` vs `free`) so a cell says which
lane produced it. A model that cannot emit legal JSON unaided is a data point.
The label is also what keeps this a decision rather than a default: typing the
action as an enum over the legal-action list is the obvious reach for anyone
building this, and the cost - a deleted signal, not a worse one - is invisible at
the point of reaching. `strict` is not a better `free`; it is a different
measurement, and the arm is how a reader can tell which one they are holding.

**The closed-phase shape generalises to the other three deduction games and not
to the RPG.** Today: `Phase` enum -> `acting_seats()` -> an `action_prompt`
if-chain -> one phase maps to one key. That holds while the action space is
finite and one decision wide per seat per turn. A tabletop rung is neither:
declarations are unbounded ("I tip the brazier onto the rope bridge"), one DM
turn is N mutations rather than one, and rule-0 inverts `referee.py:6` - there,
judgment IS the referee.

**Sketch, if that rung gets built: split the referee's two jobs.** A
deterministic rules kernel keeps state, dice, and legal mutations and raises on
illegal, exactly as `CabalReferee` does now. A model adjudicator sits in the
interpretation slot and turns free-form intent into calls against that kernel.
Players stay text-only; only the DM seat emits a list. Envelope stays ours -
`{"think":..., "narrate":..., "calls":[...]}`, validated by the kernel, refused
with the kernel's own error text, retried against the same seat, counted on
fallback. That is the existing `LLMPolicy` loop unchanged; what generalises is
`parse_action`, from "phase -> one key" to "phase -> an action spec" where the
spec may be a list.

**Three things that sketch's call vocabulary should settle early, because all
three are cheap to get wrong and expensive to change once records exist.**

- **One blocking call, one private write, one public write, and the rest are state
  mutations.** parlor already has the two writes - the two public channels map
  onto them directly. What the deduction ladder has never needed is the blocking
  one: ask a named seat a question and wait for its answer before continuing the
  turn. A DM channel without it forces the adjudicator to assume answers it should
  have asked for, and an assumed answer is unauditable in a way a refused call is
  not.
- **Free-text tokens on a seat are the honest escape hatch beside a typed
  kernel.** A string attached to a seat, which the adjudicator reads and the
  kernel does not interpret, for state the kernel has no type for. The alternative
  - a modelled lifecycle per effect - loses to the first ability that adds or
  clears state at a time nobody enumerated. Constraint: a token is referee-side
  and carries no entitlement. It becomes visible to a seat only through a typed
  reveal, which is the same gate the paragraph below describes; a token shelf that
  seats can read is a leak surface with no audit against it.
- **Split the adjudicator's system prompt along its seams from the start** -
  rules, procedure, call schema and discretion as separate blocks. One string
  carrying all four cannot be A/B'd, and a bad ruling then cannot be attributed to
  rules the model misread rather than a procedure step it skipped. This is the
  cheapest thing on the list to do first and the most annoying to retrofit, since
  retrofitting it invalidates every arm run before it.

**Two failures the audit cannot see, so the kernel has to.** An unrecognised call
must RAISE, never be dropped: a dropped call is indistinguishable from one the
model never emitted, so a broken game reads as a quiet one and the fallback rate
- the quantity every number ships beside - never moves. And the phase clock and
the win condition stay kernel-evaluated. If the model owns what time it is, there
is no `now` for a legality check to read; if the model owns whether the game is
over, the transcript records a claim where it should record a result.

**Gate #1 does not survive a model DM, and the fix is not a smarter matcher.**
*(The 2026-08-25 design read, kept as written and REFUTED - see the two paragraphs
below.)*
`find_leaks` is sound today because the referee's private bytes are a fixed set
of strings. A model DM paraphrases private state: "the innkeeper looks nervous"
leaks that he is the cultist with zero substring overlap, and the audit reads
clean. Keep `find_leaks` naive and change the corpus instead - the DM declares
its intended reveals as typed facts, those are checked against entitlement, and
the prose is audited against the facts it did NOT declare. Same naive matching,
right input. This is the RPG rung's hardest problem and it is worth knowing about
before anything is built on it.

**Measured 2026-08-28, and the reading above is refuted: gate #1 HELD under a
model referee.** The DURF rung is the model DM this paragraph anticipated, and
the audit read **91/100 sessions [83.77%, 95.19%]**, then **99/100 [94.55%,
99.82%]** under the topology edits (`docs/durf-rung.md` §The campaign, §The
paired arm; both calls in `docs/decisions.md`). The paragraph's own worked
example is what the measurement reclassifies. `docs/durf-rung.md` §What working
that question turned up decides the opposite call: **a declared fact is entitled
by definition, so the audit is correctly silent** - a referee that infers a
nervous novice and telegraphs it is doing the job, and the forward-reveal
behaviour is a COUNT with no criterion, which must never be promoted into the
gate or into a quality rubric.

**What survives is narrower, and it is the real open question: declaring sets
its own bar.** Nothing constrains what the referee may declare, so entitlement
moves off the matcher and onto the declaration - a second instrument, which has
no criterion. So the 08-25 prescription stands unchanged and for a better
reason: keep `find_leaks` naive, declare intended reveals as typed facts, audit
the prose against the facts NOT declared. What was wrong is only its premise -
that the audit would read clean while a real leak went out.

**`LLMPolicy`'s refuse -> re-prompt-with-referee-error -> count-fallback loop is
the strongest promotion candidate in the repo** and it currently lives in
`games/cabal/player.py`. Promote on evidence, per the invariant, so it moves when
game #2 needs it and not before - but it is the piece to watch for, since the RPG
sketch above reuses it verbatim.

**Two shapes not to harden before game #2.** Don't add another game's phases to
cabal's `Phase` enum or to the `action_prompt` if-chain; don't grow `ACTION_KEYS`
into a shared flat tuple. Both are this document's on-ramp and both are cheap to
lift while they are still one game wide.
