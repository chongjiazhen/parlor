"""Session 0 - the playbook draft, and the only illegal move it has.

Why this is the rung's first slice rather than a scene loop: a scene produces
prose, and prose needs a rubric this tree does not have. A draft produces a
number on the first run. ``docs/open-arms.md`` §Session-0 carries the argument.

**One rule, one illegal move.** Seats pick in turn from what is left. A pick that
is already taken, or is not in the pack at all, is illegal - and an illegal
decision is played at random and counted, which is the repo's standing treatment
rather than anything invented here. Every number this rung reports therefore
ships beside its fallback rate, and the scorer's 10% void applies unchanged.

**There is nothing for gate #1 to audit, and that is a statement rather than an
omission.** Every seat sees the same menu and the same taken list; no seat holds
what another may not. A rung with no entitlement asymmetry has an empty secret
set, so an audit over it is vacuously green - which is why this module does not
call one. The rung that earns gate #1 is elsewhere.
"""

from __future__ import annotations

import random


class NotEnoughPlaybooks(Exception):
    """Fewer playbooks than seats: the draft cannot end with distinct picks."""


class Draft:
    """Turn-order draft over a pack's names. Seeded, so a run is reproducible."""

    def __init__(self, names, seats: int, seed: int | None = None):
        names = tuple(dict.fromkeys(n.strip() for n in names if n and n.strip()))
        if len(names) < seats:
            raise NotEnoughPlaybooks(f"{len(names)} playbooks for {seats} seats")
        self.names = names
        self.seats = seats
        self.rng = random.Random(seed)
        self.picks: dict[int, str] = {}
        self.fallbacks = 0
        self._taken: list[str] = []
        self._offered: int | None = None

    @property
    def done(self) -> bool:
        return len(self.picks) == self.seats

    def remaining(self) -> tuple[str, ...]:
        return tuple(n for n in self.names if n not in self._taken)

    def offer(self) -> int:
        """Open the next seat's turn and return which seat it is."""
        if self.done:
            raise RuntimeError("draft is over")
        self._offered = len(self.picks)
        return self._offered

    def take(self, name) -> str:
        """Record a seat's pick. An illegal one is played at random and counted."""
        if self._offered is None:
            raise RuntimeError("take() before offer()")
        seat, self._offered = self._offered, None
        left = self.remaining()
        choice = (name or "").strip()
        if choice not in left:
            self.fallbacks += 1
            choice = self.rng.choice(left)
        self.picks[seat] = choice
        self._taken.append(choice)
        return choice

    def distribution(self) -> dict[str, int]:
        """How often each playbook was taken. The read this slice exists for."""
        out = {n: 0 for n in self.names}
        for name in self.picks.values():
            out[name] += 1
        return out
