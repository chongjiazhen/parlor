"""Name -> the driver that plays that rung.

Today a person has to know which module a game lives in before they can join it:
``games.cabal.demo`` and ``games.changeling.demo`` are two entry points that have
drifted apart flag by flag, and nothing anywhere names the set. This is the table
that names it, and ``parlor.__main__`` is the one command over it.

**A registry, not a wrapper.** The temptation is a driver that owns the flags and
calls into each game, which would need a lowest-common-denominator flag set -
cabal has ``--rounds``, ``--speaker``, ``--notebook`` and ``--transcript``,
changeling has ``--no-thinking``, and the two overlap on about half of what they
carry. A shared denominator is how two games come to share one, which this repo
declines elsewhere for the reason that a flag two rungs agree on stops describing
either. So an entry holds a game's ``main`` and nothing about its arguments; the
game keeps its own parser and the CLI hands it the tail of the command line
verbatim.

**Why there is no referee factory here.** A table of ``(factory, driver, flags)``
was the shape sketched for this, and the factory has no consumer: ``play`` needs
the driver, ``--list`` needs a sentence, and nothing needs to construct a referee
without a driver. ``core/`` is what game #2 inherits and the bar is evidence that
a second game needs it, so the factory lands when something asks for it.

**What is registered is a rung a PERSON can sit at**, not a genre. The line is
mechanical: a rung appears here when it has a console seat, because a name in
``--list`` that answers ``--human`` with an error is worse than an absent one.
That is why ``durf`` is not below - its session engine has seats and an
entitlement audit but no ``ConsoleBackend`` anywhere in it, so there is nothing
for a person to sit in yet. When it grows one it registers here beside the
others, and the fact that it is an RPG rather than a hidden-role game is not what
decides it. The endgame rung is an RPG; a CLI that had ruled out the genre would
have to be renamed the day it arrives.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Callable


class UnknownRung(SystemExit):
    """A name that is not registered. Carries the list, because the whole point
    of the registry is that a player should not have to go looking."""


@dataclass(frozen=True)
class Rung:
    """One playable rung: what to call it, where its driver is, what it is."""

    name: str
    #: Dotted path to a module exposing ``main()``. Imported on dispatch rather
    #: than at module scope, so ``--list`` costs no game imports and one game
    #: that fails to import does not take the other's listing down with it.
    module: str
    summary: str

    def driver(self) -> Callable[[], None]:
        mod = import_module(self.module)
        entry = getattr(mod, "main", None)
        if not callable(entry):
            raise UnknownRung(
                f"{self.name} is registered at {self.module}, which has no "
                "main() to call. The registry names a module the tree no longer "
                "has in that shape - fix the entry, do not add a second driver."
            )
        return entry


_RUNGS = (
    Rung("cabal", "games.cabal.demo",
         "5-seat hidden-role missions. Every seat's knowledge is true and static; "
         "the evil pair knows itself from the deal."),
    Rung("changeling", "games.changeling.demo",
         "5-seat one-night swap. A seat's knowledge of its OWN role can be stale "
         "and can be false, because the night moves cards it may not look at."),
    Rung("quorum", "games.quorum.demo",
         "5-seat legislative cascade. A hand is dealt per event and narrows as it "
         "passes down the offices, so what a seat may see is a fact about the "
         "state and not about its role."),
    Rung("belfry", "games.belfry.demo",
         "5-12 seat town square over many days and nights. The referee is allowed "
         "to lie: a seat whose ability has been switched off is told something "
         "false in the same words, and is not told that."),
)

RUNGS: dict[str, Rung] = {r.name: r for r in _RUNGS}


def lookup(name: str) -> Rung:
    try:
        return RUNGS[name]
    except KeyError:
        raise UnknownRung(
            f"no rung named {name!r}. Registered: {', '.join(RUNGS)}."
        ) from None


def listing() -> str:
    """One line per rung, for ``--list``."""
    width = max(len(n) for n in RUNGS)
    return "\n".join(f"  {r.name:<{width}}  {r.summary}" for r in RUNGS.values())
