"""What one model call cost, declared once for every game in the arena.

Promoted to ``core/`` on the bar this repo sets: four games were carrying the
same three fields and the same six lines that fill them, which is the evidence
``core/`` asks for and not a guess about a second game. Nothing here knows about
roles, phases or hidden information - it reads the bytes a policy sent and the
usage block the upstream reported back, which is arena vocabulary.

**It is not model-facing and it never becomes model-facing.** Nothing recorded
here enters ``prompt_for`` or ``render_context``, so a number measured before
these fields existed is still a number measured under the same payload. That is
the whole reason the instrument could be added without re-baselining anything.

**The size and the usage answer different questions.** ``prompt_size`` and
``reply_size`` are bytes this repo can always count, on any route, including a
route that reports no usage at all. ``usage`` is the upstream's own token
accounting and is ``None`` whenever the upstream did not send one - which is a
fact about the route, not a zero. A reader that treats a missing usage block as
zero tokens is reading the router, not the run.

**Every field defaults, and that is load-bearing.** ``Decision`` is serialised to
the per-game JSONL, so every record written before 2026-08-30 lacks all three
keys. They are keyword-only so that a game's own required fields keep their
positions, and defaulted so a legacy record still constructs.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CallCost:
    """The three fields, in the one place they are declared.

    Mixed into each game's ``Decision``. ``kw_only`` is what makes one shared
    declaration possible at all: inherited fields are laid out before the
    subclass's own, and a game's ``Decision`` opens with required fields
    (``turn``, ``seat``), which a defaulted base field would otherwise sit in
    front of and break.
    """

    #: characters in the prompt that produced this decision's landed reply, and in
    #: that reply. Zero on a decision no model answered - a fallback that never
    #: got a reply back, or a policy that never calls one.
    prompt_size: int = field(default=0, kw_only=True)
    reply_size: int = field(default=0, kw_only=True)
    #: the upstream's own usage block for that call, verbatim, or ``None`` when it
    #: reported none. Not normalised: the shape is the route's, and flattening it
    #: here would invent a schema no upstream promised.
    usage: dict | None = field(default=None, kw_only=True)


def forget(policy) -> None:
    """Clear the last call's cost. Called at the top of a decision, not a retry.

    A decision that ends in a fallback must not report the size of the last
    decision that happened to succeed, which is what leaving the fields alone
    would do.
    """
    policy.last_prompt_size = 0
    policy.last_reply_size = 0
    policy.last_usage = None


def note(policy, prompt: str, reply: str, backend) -> None:
    """Record what the attempt that just returned cost.

    Called on every attempt, so a decision that recovered reports the attempt
    that LANDED rather than the one that was refused - the landed call is the one
    whose bytes are in the record.
    """
    policy.last_prompt_size = len(prompt)
    policy.last_reply_size = len(reply)
    policy.last_usage = getattr(backend, "last_usage", None)


def spent(policy) -> dict:
    """The cost of ``policy``'s last decision, as ``Decision`` keyword arguments.

    ``getattr`` throughout: a game seats policies this module has never heard of
    - a random control, a mechanical solver, a console seat - and none of them
    call a model or carry these attributes.
    """
    return {
        "prompt_size": int(getattr(policy, "last_prompt_size", 0) or 0),
        "reply_size": int(getattr(policy, "last_reply_size", 0) or 0),
        "usage": getattr(policy, "last_usage", None),
    }
