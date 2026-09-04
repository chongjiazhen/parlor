"""What a table outside this repo may depend on, and nothing else.

Everywhere else in `core/` the referee contract is duck-typed. That was right
while every consumer sat in this tree: `core/registry.py` declines a referee
factory on exactly that ground - nothing needed one, and a table of
`(factory, driver, flags)` would have been a shape with no caller. A consumer
outside the tree changes the calculus, because a rename here then breaks it
silently, in a checkout this suite cannot see, and the break surfaces the next
time somebody sits down to play rather than the next time the tests run.

**This module is a contract, not a base class.** Nothing inherits from it and no
game changes to adopt it: the four rungs already satisfy what they satisfy, and
a table satisfies it structurally the same way. Adding a base class would make
the seam load-bearing at import time in five places that do not need it.

**What is declared here is the table-facing set, not the intersection of the
rungs**, because there is no universal referee contract to intersect. Measured
2026-09-04 by importing every referee class rather than reading the source: `n`,
`phase`, `prompt_for`, `render_context` and `seat_view` are common to all four;
`acting_seats` is on three and disagrees on return type; `secret_terms`, `ask`
and `audit` are on two; `entitled_seats` is on one. So `changeling` is the only
rung that satisfies the whole of what a table needs, and `core/test_seam.py`
records that rather than papering over it.

**Presence is not signature.** `runtime_checkable` below permits `isinstance`,
and `isinstance` checks only that an attribute EXISTS - never what it accepts or
returns. A rename is caught by it; a changed signature is not. That is why the
tests call through every member instead of resting on the check, and why an
`isinstance` added here later would cover less than it appears to.

Everything in `core/` that is not named below stays free to move.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from core.observability import SecretKey, SeatView, find_leaks


@runtime_checkable
class Rendered(Protocol):
    """The rendering core - the five members every rung in this tree holds.

    A table implements this to seat players at all. It says nothing about
    secrets, which is deliberate: `quorum` renders and has no `secret_terms`, so
    a single fat protocol would make a conformance assertion over the rungs
    unwritable.
    """

    #: Seats at the table.
    n: int
    #: Where the game is. A string or an enum member; the seam does not narrow it,
    #: because the rungs disagree and none of them needs the other's phases.
    phase: object

    def prompt_for(self, seat: int, include_speech: bool = True) -> str:
        """The exact bytes that leave for this seat's model - context and ask."""

    def render_context(self, seat: int, include_speech: bool = True) -> str:
        """The context half alone, without the ask appended."""

    def seat_view(self, seat: int) -> SeatView:
        """Everything this seat may see. The only private channel."""


@runtime_checkable
class Audited(Protocol):
    """The entitlement half: what secrets exist, and who was told which.

    Split from `Rendered` because it is what gate #1 needs and two rungs do not
    have it. A table that hides nothing implements only `Rendered`; a table with
    a GM implements both.
    """

    def secret_terms(self) -> dict[SecretKey, list[str]]:
        """Every secret, mapped to the strings that would betray it.

        Keyed by seat, or by `(seat, axis)` where one seat holds several
        independent secrets. Both forms are what `find_leaks` already accepts.
        """

    def entitled_seats(self, viewer: int) -> set[SecretKey]:
        """The keys this viewer was legitimately told.

        A bare seat in the set grants every axis of that seat; a `(seat, axis)`
        key grants one. Entitlement is the whole difference between a reveal and
        a leak, so a table that returns too much here defeats the audit while
        every test still passes.
        """


@runtime_checkable
class Asked(Protocol):
    """A referee that puts a question to a seat on the clock.

    Separate from `Rendered` because two rungs have no `ask` - their prompt is
    the context alone - and separate from `Audited` because asking and hiding are
    independent.
    """

    def acting_seats(self) -> Sequence[int]:
        """Which seats are on the clock.

        `Sequence`, not `list` or `tuple`: cabal returns a list and the others a
        tuple, and a seam that picked one would exclude a live rung for no
        behavioural reason.
        """

    def ask(self, seat: int) -> str:
        """The question. Bytes leaving for the model, and audited as such."""


@runtime_checkable
class Transport(Protocol):
    """How a decision is obtained. One method, and both of its return values.

    A model backend, the console, and a browser seat are three implementations of
    this and nothing else - which is what makes a second front end an addition
    rather than a rewrite.
    """

    def complete_meta(self, context: str,
                      history: list[tuple[str, str]] | None = None
                      ) -> tuple[str, str]:
        """The reply, and the id of the upstream that actually served it.

        The second half is not optional decoration: a routing alias picks a
        different upstream per request and nothing in the catalog says which one
        answered, so a transport that dropped it would make every number taken
        through it unattributable.
        """


def audit_render(ref: Audited, viewer: int, rendered: str
                 ) -> list[tuple[SecretKey, str]]:
    """Scan bytes about to reach ``viewer``'s model for a secret it may not hold.

    Empty list means gate #1 holds for these bytes. The one place a table reaches
    the matcher, so `find_leaks`' arguments have a single caller in the seam
    rather than one per table - and the matcher itself is untouched, which is
    what makes the repo invariant that keeps it naive apply here by construction
    instead of by promise.

    **It takes the rendered string rather than producing it.** A caller audits
    the exact bytes it is about to send, at the moment it has them. durf found
    the alternative silently wrong: entitlement recomputed at audit time lets a
    fact declared LATER make an earlier render read clean, and that failure is
    invisible in every output.
    """
    return find_leaks(rendered, ref.secret_terms(), ref.entitled_seats(viewer),
                      viewer)
