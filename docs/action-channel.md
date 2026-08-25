# The action channel, and what the RPG rung breaks

Written 2026-08-25, unmeasured, from a design read of `core/replies.py`,
`referee.action_prompt`, and `player.parse_action`. Nothing here is a decision
yet; it is here so the cheap moves stay cheap.

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

**Gate #1 does not survive a model DM, and the fix is not a smarter matcher.**
`find_leaks` is sound today because the referee's private bytes are a fixed set
of strings. A model DM paraphrases private state: "the innkeeper looks nervous"
leaks that he is the cultist with zero substring overlap, and the audit reads
clean. Keep `find_leaks` naive and change the corpus instead - the DM declares
its intended reveals as typed facts, those are checked against entitlement, and
the prose is audited against the facts it did NOT declare. Same naive matching,
right input. This is the RPG rung's hardest problem and it is worth knowing about
before anything is built on it.

**`LLMPolicy`'s refuse -> re-prompt-with-referee-error -> count-fallback loop is
the strongest promotion candidate in the repo** and it currently lives in
`games/cabal/player.py`. Promote on evidence, per the invariant, so it moves when
game #2 needs it and not before - but it is the piece to watch for, since the RPG
sketch above reuses it verbatim.

**Two shapes not to harden before game #2.** Don't add another game's phases to
cabal's `Phase` enum or to the `action_prompt` if-chain; don't grow `ACTION_KEYS`
into a shared flat tuple. Both are this document's on-ramp and both are cheap to
lift while they are still one game wide.
