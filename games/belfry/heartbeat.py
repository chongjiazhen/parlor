"""The off-map faction, seated at belfry's table. Off by default.

`docs/faction-heartbeat.md` scoped it and `experiments/heartbeat/heartbeat.py` built it
as a standalone spike; this file is that spike SEATED, and it adds nothing to the
model of a faction. The world, the three action types, the propagation rule, the
schedule and the snapshot audit are imported unchanged, because a second copy of
any of them is how the seated version comes to disagree with the measured one.

What seating decides, and it is only these:

- **A tick is a NIGHT.** The faction acts at the top of a night, before any role
  wakes, so a fact laid tonight can reach a seat's render tonight. Ticks are
  counted per night in `ticks`; nothing reads a clock, and no record field names a
  time or a process.
- **The schedule is a pure function of the game seed** (`schedule`), so a run at a
  seed replays. A game with no seed draws one from an unseeded source rather than
  from the referee's stream - an unpinned run is not reproducible either way, and
  taking the draw from `ref.rng` would move the deal.
- **A seat's place is its seat number.** The table is a circle of `n` seats and the
  faction acts on places; identity is the only mapping that does not invent a
  second geography. The spike's rumour rule reaches `place +/- 1` and is LINEAR,
  so seats 0 and n-1 are not neighbours for rumour even though they are at the
  table. Changing that is a change to a merged spike and a second variable; it is
  written down here rather than fixed quietly.

**No `Phase`, no turn kind, no `ACTION_KEYS` entry.** `docs/action-channel.md`
names those three shapes as the ones not to harden before game #2, and the faction
needs none of them: it takes no seat decision, so the referee's cursor never has to
know it exists.

The gate #1 half lives in `BelfryReferee.audit`, which grades each seat's render
against the snapshot captured when that render was BUILT. `leaks` below is the one
call that does it, and it takes the render's own snapshot and nothing else.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from games.durf.facts import FactId
from experiments.heartbeat.heartbeat import (Action, Policy, RandomPolicy, Render,
                                       Snapshot, Tally, World)
from experiments.heartbeat.heartbeat import audit as fact_audit
from experiments.heartbeat.heartbeat import schedule

#: How many nights of the run the faction acts on. Three, as the spike ran it.
DEFAULT_BEATS = 3


def honest_render(hb: "BelfryHeartbeat", seat: int, night: int) -> str:
    """What this seat has legitimately heard, and nothing else."""
    return "\n".join(hb.world.facts[f].text
                     for f in sorted(hb.world.entitled(seat, night)))


Renderer = Callable[["BelfryHeartbeat", int, int], str]


@dataclass
class BelfryHeartbeat:
    """One faction with no seat, ticking between belfry's nights."""

    world: World
    #: The nights it acts on. Seed-derived, fixed before the first night.
    nights: tuple[int, ...]
    rng: random.Random
    policy: Policy
    renderer: Renderer = honest_render
    tally: Tally = field(default_factory=Tally)
    #: night -> how many ticks the faction took that night. Counted rather than
    #: derived from `actions`, so a night it declined to act still has a row.
    ticks: dict[int, int] = field(default_factory=dict)
    actions: list[Action] = field(default_factory=list)

    @classmethod
    def build(cls, seed: int | None, n_seats: int, max_days: int = 12,
              beats: int = DEFAULT_BEATS, policy: Policy | None = None,
              renderer: Renderer = honest_render) -> "BelfryHeartbeat":
        if seed is None:
            # No game seed means no reproducible run, with or without a faction.
            # Drawing from an unseeded source rather than the referee's rng keeps
            # the deal where it was.
            seed = random.Random().randrange(1 << 32)
        world = World(seed=seed, places={s: s for s in range(n_seats)},
                      n_places=n_seats)
        nights = tuple(t + 1 for t in schedule(seed, max_days, beats))
        return cls(world=world, nights=nights,
                   rng=random.Random(f"faction:{seed}"),
                   policy=policy or RandomPolicy(), renderer=renderer)

    def legal(self, night: int) -> list[Action]:
        out = [Action("scout", p, night) for p in range(self.world.n_places)]
        out += [Action("bribe", s, night) for s in self.world.seats]
        out += [Action("raid", p, night) for p in range(self.world.n_places)]
        return out

    def tick(self, night: int) -> int:
        """One night of the faction's clock. Returns the ticks it took."""
        taken = 0
        if night in self.nights and night not in self.ticks:
            legal = self.legal(night)
            self.tally.decisions += 1
            choice = self.policy.choose(night, legal, self.rng)
            if choice not in legal:
                self.tally.fallbacks += 1
                choice = self.rng.choice(legal)
            self.actions.append(choice)
            self.world.apply(choice, self.rng)
            # Every fact's statement has to carry its own sentinel or the audit
            # cannot see it leave - checked here rather than at the end, so a bad
            # fact refuses before it reaches a render.
            self.world.check_terms()
            taken = 1
        self.ticks.setdefault(night, 0)
        self.ticks[night] += taken
        return taken

    def snapshot(self, night: int) -> Snapshot:
        return self.world.snapshot(night)

    def render(self, seat: int, night: int) -> Render:
        """The seat's lines and the entitlement they were built under, together.

        One object, because the whole finding of the spike is that these two must
        not be fetched separately: a snapshot taken later than the text it grades
        reads a real leak as clean.
        """
        return Render(tick=night, seat=seat,
                      text=self.renderer(self, seat, night),
                      snapshot=self.snapshot(night))

    def leaks(self, render: Render) -> list[tuple[FactId, str]]:
        """Gate #1 over the faction's bytes, against the render's OWN snapshot."""
        return fact_audit(render, render.snapshot)

    def report(self) -> dict:
        """The faction's own denominator. Never pooled with seat decisions."""
        return {
            "seed": self.world.seed,
            "nights": list(self.nights),
            "ticks": {str(n): c for n, c in sorted(self.ticks.items())},
            #: The schedule runs to the DAY BOUND, and a game that ends earlier
            #: never reaches the nights beyond it. So scheduled and taken come
            #: apart, and both ship: a run whose faction never acted is a run
            #: with no faction in it, and reading only the taken count would let
            #: that pass as a faction arm.
            "scheduled": len(self.nights),
            "taken": sum(self.ticks.values()),
            "decisions": self.tally.decisions,
            "fallbacks": self.tally.fallbacks,
            "fallback_rate": self.tally.fallback_rate,
            "actions": [{"kind": a.kind, "target": a.target, "night": a.tick}
                        for a in self.actions],
        }
