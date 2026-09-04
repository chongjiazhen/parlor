"""The off-map faction heartbeat, at the smallest size that tests anything.

``docs/faction-heartbeat.md`` scopes this: one faction with no seat, three action
types, a tick schedule that is a pure function of the seed, a propagation rule
deciding which seats learn what and when, run as a step inside a loop. It is
scored on one thing - **a render is audited against the entitlement snapshot
captured when it was built**, never against entitlement recomputed at audit time.

Three decisions from that note are enforced here rather than remembered:

- **Ticks are counted, never clocked.** ``schedule`` draws from ``random.Random
  (seed)``; nothing reads a wall clock, and the record carries no timestamp, so
  whether a separate process drove the loop is unobservable in the record.
- **The faction's decisions are tallied in their own denominator**, with their own
  fallback rate. There are no seat decisions in the spike, and if there were they
  would not share ``Tally``.
- **The matcher is not reimplemented.** The faction declares its actions as typed
  facts in the ``WorldFact`` shape of ``games/durf/facts.py`` and hands matching to
  that adapter, which hands it to ``core.observability.find_leaks`` unchanged.
  This module is therefore the SECOND consumer of the fact-keyed adapter - the
  promotion evidence the ``core/`` invariant asks for. The promotion itself is a
  later slice; importing across ``games/`` is the cheapest way to leave the trail
  and touch nothing in ``core/``.

Not touched, by the same note: no game's ``Phase`` enum, ``action_prompt`` chain
or ``ACTION_KEYS``.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import Callable, Protocol

from games.durf.facts import (FactError, FactId, FactLedger, WorldFact,
                              check_facts, find_fact_leaks)

#: The three action types. Each lays one fact into the world at the tick it
#: happens and propagates it by place: ``scout`` and ``raid`` are seen by every
#: seat AT the place at once and reach adjacent places as late rumour; ``bribe``
#: reaches exactly the bribed seat and nobody else, ever.
ACTION_KINDS = ("scout", "bribe", "raid")

#: A seat that never learns a fact by propagation. Any tick past the run.
NEVER = 10 ** 6


@dataclass(frozen=True)
class Action:
    kind: str
    target: int  # a place for scout/raid, a seat for bribe
    tick: int

    @property
    def fact_id(self) -> FactId:
        return (self.kind, f"t{self.tick:02d}")


@dataclass(frozen=True)
class Snapshot:
    """Entitlement as it stood at ``tick``, frozen with the render it audits.

    ``terms`` is every fact that EXISTED at the tick, whether or not any seat may
    know it - a fact laid later cannot be in a render built earlier, and if its
    term somehow is, that is the renderer's bug to catch elsewhere. ``entitled``
    maps each seat to the facts it held at that tick. Both are frozen so nothing
    downstream can watch them move.
    """

    tick: int
    terms: dict[FactId, tuple[str, ...]]
    entitled: dict[int, frozenset[FactId]]

    def to_json(self) -> dict:
        return {"tick": self.tick,
                "terms": {"/".join(k): list(v) for k, v in self.terms.items()},
                "entitled": {str(s): sorted("/".join(f) for f in fs)
                             for s, fs in self.entitled.items()}}


@dataclass(frozen=True)
class Render:
    """One seat's outgoing context at one tick, with the snapshot it was built under."""

    tick: int
    seat: int
    text: str
    snapshot: Snapshot

    def to_json(self) -> dict:
        return {"tick": self.tick, "seat": self.seat, "text": self.text,
                "snapshot": self.snapshot.to_json()}


def audit(render: Render, snapshot: Snapshot) -> list[tuple[FactId, str]]:
    """Every ``(fact, term)`` the render exposes that its seat was not entitled to.

    Takes a render and a snapshot and nothing else, so the caller decides which
    snapshot - and the loop below passes ``render.snapshot``. Passing a later one
    is the recompute failure; the guard test does it on purpose to show the gap.
    """
    return find_fact_leaks(render.text, snapshot.terms,
                           snapshot.entitled.get(render.seat, frozenset()))


@dataclass
class World:
    """Seats at places, the facts the faction has laid, and who learns them when.

    ``learn_tick[fact][seat]`` is the tick at which ``seat`` becomes entitled to
    ``fact`` (``NEVER`` if it does not). Entitlement at tick T is the set of facts
    whose learn tick is ``<= T`` - a pure read, so ``snapshot`` is cheap and the
    loop can afford one per render.
    """

    seed: int
    places: dict[int, int]  # seat -> place
    n_places: int
    facts: dict[FactId, WorldFact] = field(default_factory=dict)
    laid_at: dict[FactId, int] = field(default_factory=dict)
    learn_tick: dict[FactId, dict[int, int]] = field(default_factory=dict)

    @classmethod
    def build(cls, seed: int, n_seats: int, n_places: int) -> "World":
        rng = random.Random(f"places:{seed}")
        return cls(seed=seed, n_places=n_places,
                   places={s: rng.randrange(n_places) for s in range(n_seats)})

    @property
    def seats(self) -> list[int]:
        return sorted(self.places)

    def add_fact(self, fact_id: FactId, term: str, text: str, tick: int) -> FactId:
        if fact_id in self.facts:
            raise FactError(f"fact {fact_id!r} already laid")
        if term.lower() not in text.lower():
            # The statement is what a render carries; the term is what the audit
            # matches. A statement without its own sentinel is a fact the audit
            # cannot see leave, and the first guard fixture shipped exactly that.
            raise FactError(
                f"fact {fact_id!r}: its text {text!r} does not carry its term "
                f"{term!r}, so a render that states it would audit clean")
        self.facts[fact_id] = WorldFact(fact_id=fact_id, label=term,
                                        terms=(term,), text=text)
        self.laid_at[fact_id] = tick
        self.learn_tick[fact_id] = {s: NEVER for s in self.places}
        return fact_id

    def learn(self, fact_id: FactId, seat: int, tick: int) -> None:
        """Seat becomes entitled at ``tick`` - or earlier, if it already was."""
        row = self.learn_tick[fact_id]
        row[seat] = min(row[seat], tick)

    def publish(self, fact_id: FactId, tick: int) -> None:
        """The OTHER route: the fact becomes public to every seat at ``tick``.

        A seat announcing it, a scene revealing it - anything that is not the
        faction's own propagation. This is what makes recompute unsound.
        """
        for seat in self.places:
            self.learn(fact_id, seat, tick)

    def entitled(self, seat: int, tick: int) -> frozenset[FactId]:
        return frozenset(f for f, row in self.learn_tick.items()
                         if row[seat] <= tick)

    def snapshot(self, tick: int) -> Snapshot:
        terms = {f: fact.terms for f, fact in self.facts.items()
                 if self.laid_at[f] <= tick}
        return Snapshot(tick=tick, terms=terms,
                        entitled={s: self.entitled(s, tick) for s in self.seats})

    def check_terms(self) -> None:
        """Hold the laid facts to what naive matching needs (durf's rule, reused)."""
        check_facts(FactLedger(facts=dict(self.facts), revealed=set()))

    def apply(self, action: Action, rng: random.Random) -> FactId:
        """Lay the action's fact and decide who learns it when. The propagation rule."""
        term = f"{action.kind}@p{action.target}#t{action.tick:02d}"
        if action.kind == "bribe":
            term = f"bribe@s{action.target}#t{action.tick:02d}"
        text = {"scout": f"the faction scouted place {action.target} [{term}]",
                "bribe": f"the faction bribed seat {action.target} [{term}]",
                "raid": f"the faction raided place {action.target} [{term}]",
                }[action.kind]
        fid = self.add_fact(action.fact_id, term, text, action.tick)
        if action.kind == "bribe":
            self.learn(fid, action.target, action.tick)
            return fid
        for seat, place in self.places.items():
            if place == action.target:
                self.learn(fid, seat, action.tick)
            elif abs(place - action.target) == 1:
                self.learn(fid, seat, action.tick + rng.randint(1, 3))
        return fid


def schedule(seed: int, ticks: int, beats: int) -> tuple[int, ...]:
    """The ticks the faction acts on. A pure function of the seed, nothing else."""
    if beats > ticks:
        raise ValueError(f"{beats} beats do not fit in {ticks} ticks")
    return tuple(sorted(random.Random(f"schedule:{seed}").sample(range(ticks),
                                                                 beats)))


class Policy(Protocol):
    def choose(self, tick: int, legal: list[Action],
               rng: random.Random) -> Action | None: ...


class RandomPolicy:
    """The control policy. A model policy drops into the same seam."""

    def choose(self, tick, legal, rng):
        return rng.choice(legal)


@dataclass
class Tally:
    """The faction's own denominator. Never pooled with seat decisions."""

    decisions: int = 0
    fallbacks: int = 0

    @property
    def fallback_rate(self) -> float:
        return self.fallbacks / self.decisions if self.decisions else 0.0


def default_renderer(world: World, seat: int, tick: int) -> str:
    lines = [f"tick {tick:02d}, seat {seat} at place {world.places[seat]}"]
    for fid in sorted(world.entitled(seat, tick)):
        lines.append(world.facts[fid].text)
    return "\n".join(lines)


Renderer = Callable[[World, int, int], str]


@dataclass
class Run:
    """The loop. One faction step per scheduled tick, one render per seat per tick."""

    world: World
    ticks: int
    beats: int = 3
    policy: Policy = field(default_factory=RandomPolicy)
    renderer: Renderer = default_renderer
    after_tick: dict[int, Callable[[World], None]] = field(default_factory=dict)
    schedule: tuple[int, ...] = ()
    actions: list[Action] = field(default_factory=list)
    renders: list[Render] = field(default_factory=list)
    leaks: list[tuple[int, int, FactId, str]] = field(default_factory=list)
    tally: Tally = field(default_factory=Tally)

    def legal(self, tick: int) -> list[Action]:
        out = [Action("scout", p, tick) for p in range(self.world.n_places)]
        out += [Action("bribe", s, tick) for s in self.world.seats]
        out += [Action("raid", p, tick) for p in range(self.world.n_places)]
        return out

    def play(self) -> "Run":
        self.schedule = schedule(self.world.seed, self.ticks, self.beats)
        rng = random.Random(f"faction:{self.world.seed}")
        for tick in range(self.ticks):
            if tick in self.schedule:
                self._faction_step(tick, rng)
            for seat in self.world.seats:
                # The snapshot is taken in the same step as the render, and the
                # audit runs against THAT snapshot here, before the loop moves on
                # and anything (the after_tick hook, a later beat) can change what
                # the seat is entitled to. Auditing at the end of the run against
                # the world as it then stands is the recompute failure in
                # docs/faction-heartbeat.md section 1, and the first version of this
                # loop did exactly that: the guard test went red against it.
                render = Render(tick, seat, self.renderer(self.world, seat, tick),
                                self.world.snapshot(tick))
                self.renders.append(render)
                for fid, term in audit(render, render.snapshot):
                    self.leaks.append((tick, seat, fid, term))
            hook = self.after_tick.get(tick)
            if hook is not None:
                hook(self.world)
        self.world.check_terms()
        return self

    def _faction_step(self, tick: int, rng: random.Random) -> None:
        legal = self.legal(tick)
        self.tally.decisions += 1
        choice = self.policy.choose(tick, legal, rng)
        if choice not in legal:
            self.tally.fallbacks += 1
            choice = rng.choice(legal)
        self.actions.append(choice)
        self.world.apply(choice, rng)

    def report(self) -> dict:
        end = self.world.snapshot(self.ticks - 1)
        missed = sum(1 for r in self.renders
                     if audit(r, r.snapshot) and not audit(r, end))
        return {
            "seed": self.world.seed,
            "ticks": self.ticks,
            "schedule": list(self.schedule),
            "faction": {"decisions": self.tally.decisions,
                        "fallbacks": self.tally.fallbacks,
                        "fallback_rate": self.tally.fallback_rate},
            "leaks": {"caught_by_snapshot": len(self.leaks),
                      "missed_by_recompute_at_end": missed},
        }

    def record(self) -> dict:
        return {
            **self.report(),
            "places": {str(s): p for s, p in self.world.places.items()},
            "actions": [{"kind": a.kind, "target": a.target, "tick": a.tick}
                        for a in self.actions],
            "renders": [r.to_json() for r in self.renders],
            "leak_list": [[t, s, "/".join(f), term]
                          for t, s, f, term in self.leaks],
        }

    def record_bytes(self) -> bytes:
        return json.dumps(self.record(), sort_keys=True,
                          separators=(",", ":")).encode("utf-8")


def run(seed: int, n_seats: int, n_places: int, ticks: int, beats: int = 3,
        policy: Policy | None = None) -> Run:
    return Run(World.build(seed, n_seats, n_places), ticks=ticks, beats=beats,
               policy=policy or RandomPolicy()).play()
