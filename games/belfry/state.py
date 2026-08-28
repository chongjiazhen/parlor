"""The board the referee keeps, and the deal that sets it up.

This is the grimoire: one row per seat, holding what that seat IS, what it
believes it is, and every marker the night hangs on it. Nothing here renders and
nothing here decides - it is the state the referee reads and the audit is
protecting, kept in one place so a leak has one thing to get past rather than
five.

**Discretion is a seeded decision, taken once and written down.** The referee of
this family of games is a person who is allowed to choose - which of two seats a
piece of information points at, whether an ambiguous seat reads as evil today,
who dies when a kill is deflected. A deterministic referee cannot have taste, so
every one of those choices is drawn from the run's seeded RNG and appended to the
referee-side log. That keeps ``--seed`` meaning what the repo invariant says it
means, and it makes each choice reviewable after the fact instead of being an
unrecorded property of a person's mood.

Two of them are taken at setup rather than per query - which side an ambiguous
seat registers on, and which good seat reads as the demon to the seat that hunts
it. Per-query re-rolling was the alternative and it is a different game: a seat
that reads evil on Tuesday and good on Wednesday is noise a player cannot reason
against, and the whole value of an ambiguous seat is that its owner can build a
consistent story on it. Per-query discretion is a variant axis to measure, not a
default to assume; ``RULES.md`` carries the argument.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from games.belfry.roles import (ALIGNMENT, DISTRIBUTION, Align, Role, Script,
                                Team)


class BadSetup(ValueError):
    """A table that cannot be dealt - a seat count with no published proportions,
    or a script too thin to fill them. Raised at the door rather than dealt
    around, because a silently substituted role is a game nobody chose."""


@dataclass
class Seat:
    index: int
    role: Role
    #: What this seat was dealt, kept beside ``role`` because the demon can change
    #: hands mid-game and a record holding only the end state cannot say who
    #: started where.
    dealt: Role
    #: The role this seat BELIEVES it holds. Equal to ``role`` for every seat but
    #: the one whose whole point is that it is wrong about itself - and that seat
    #: must never be told otherwise, which is the same belief/truth split
    #: `changeling` is built on, arriving here through a different door.
    believes: Role
    alive: bool = True
    #: A dead seat keeps exactly one vote for the rest of the game. Spent on a vote
    #: FOR an execution; a vote against costs nothing.
    ghost_vote: bool = True
    #: Set by the poisoning minion; cleared at the top of the next night.
    poisoned: bool = False
    #: Set by the protecting townsfolk for one night.
    protected: bool = False
    used_power: bool = False
    #: Day bookkeeping, cleared at dusk.
    nominated_today: bool = False
    was_nominated_today: bool = False
    #: Ever, not today - the trigger it feeds fires once per game.
    ever_nominated: bool = False
    #: Set at the seat's night step, read at the next day's vote.
    master: int | None = None

    @property
    def align(self) -> Align:
        return ALIGNMENT[self.role.team]


@dataclass
class Grimoire:
    seats: list[Seat]
    script: Script
    #: Three roles NOT in play, handed to the demon to claim. They name no seat, so
    #: they carry no association and cannot be the vehicle of a leak.
    bluffs: tuple[str, ...] = ()
    #: The good seat that reads as the demon to the seat that hunts it, or ``None``
    #: when nobody is hunting.
    herring: int | None = None
    #: Setup discretion for the two ambiguous roles. Names are the roles they
    #: register AS, chosen once - see the module docstring.
    hermit_evil: bool = False
    hermit_as: str = ""
    mimic_good: bool = False
    mimic_as: str = ""
    #: Referee-side narration of every discretionary choice. Reaches no model.
    log: list[str] = field(default_factory=list)

    # ---- reading the board ---------------------------------------------------

    @property
    def n(self) -> int:
        return len(self.seats)

    def seat(self, index: int) -> Seat:
        return self.seats[index]

    def role_of(self, index: int) -> Role:
        return self.seats[index].role

    def alive_seats(self) -> list[int]:
        return [s.index for s in self.seats if s.alive]

    def find(self, key: str) -> int | None:
        """The seat holding a role right now, or ``None``. Roles are unique on a
        script, so there is at most one."""
        for s in self.seats:
            if s.role.key == key:
                return s.index
        return None

    def find_believer(self, key: str) -> int | None:
        """The seat that ACTS as a role - the one holding it, or the seat that
        believes it holds it. The night walks the order by belief, because a seat
        wrong about itself still wakes and still expects to be told something."""
        held = self.find(key)
        if held is not None:
            return held
        for s in self.seats:
            if s.believes.key == key:
                return s.index
        return None

    def demon_seat(self) -> int | None:
        """The LIVING demon, or ``None``.

        Living, because the role changes hands: a demon that dies passing the role
        on leaves a dead seat still holding it, and a search that returned the
        first match would find the corpse. The win check reads this, so that
        version of it hands the good side a win over a demon still at the table -
        which is exactly what it did before the qualifier was here.
        """
        for s in self.seats:
            if s.role.team is Team.DEMON and s.alive:
                return s.index
        return None

    def minions(self) -> list[int]:
        return [s.index for s in self.seats if s.role.team is Team.MINION]

    def droisoned(self, index: int) -> bool:
        """Is this seat's ability off and its information false? One predicate over
        the two ways that happens, because every caller cares about the effect and
        none of them cares which cause produced it."""
        seat = self.seats[index]
        return seat.poisoned or seat.role.key == "sot"

    def living_neighbours(self, index: int) -> list[int]:
        """The nearest living seat each way round the table. Dead seats are seen
        past, so a seat's neighbours change as the table empties - which is what
        makes a neighbour-reading role worth anything after night one."""
        alive = self.alive_seats()
        if len(alive) <= 1:
            return []
        out = []
        for step in (1, -1):
            i = (index + step) % self.n
            while i != index:
                if self.seats[i].alive:
                    out.append(i)
                    break
                i = (i + step) % self.n
        return sorted(set(out))

    def evil_pairs(self) -> int:
        """Pairs of seats sitting next to each other that both register as evil.
        Seating is a circle and the dead still occupy their chairs, so this is a
        fact about the deal and does not move."""
        pairs = 0
        for i in range(self.n):
            j = (i + 1) % self.n
            if self.registers_evil(i) and self.registers_evil(j):
                pairs += 1
        return pairs if self.n > 2 else min(pairs, 1)

    # ---- what a seat LOOKS like ---------------------------------------------

    def registers_evil(self, index: int) -> bool:
        seat = self.seats[index]
        if seat.role.key == "hermit":
            return self.hermit_evil
        if seat.role.key == "mimic":
            return not self.mimic_good
        return seat.align is Align.EVIL

    def registers_demon(self, index: int, *, for_seat: int | None = None) -> bool:
        """Does this seat read as the demon? ``for_seat`` is the asker, because one
        seat's false positive is exactly that: a fact about the asker's night, not
        about the seat it points at."""
        seat = self.seats[index]
        if for_seat is not None and self.herring == index:
            return True
        if seat.role.key == "hermit":
            return self.hermit_evil and self.hermit_as == "fiend"
        return seat.role.team is Team.DEMON

    def registers_as(self, index: int) -> Role:
        """The role this seat appears to hold, to anything that names a role."""
        seat = self.seats[index]
        if seat.role.key == "hermit" and self.hermit_evil:
            return self.script.get(self.hermit_as)
        if seat.role.key == "mimic" and self.mimic_good:
            return self.script.get(self.mimic_as)
        return seat.role

    def registers_team(self, index: int, team: Team) -> bool:
        return self.registers_as(index).team is team

    # ---- dusk ----------------------------------------------------------------

    def clear_day(self) -> None:
        for seat in self.seats:
            seat.nominated_today = False
            seat.was_nominated_today = False


def deal(n: int, script: Script, rng: random.Random) -> Grimoire:
    """Deal one table. The referee owns the deal and the seating, always.

    That line is drawn here rather than argued each time: a model that dealt would
    be a model that could be asked afterwards what it dealt, and nothing about the
    result would be checkable. The rest of this rung hands the referee's other
    choices to a seeded RNG for the same reason - it is the only way a run stays
    reproducible from ``--seed`` alone.
    """
    if n not in DISTRIBUTION:
        raise BadSetup(f"{n} seats has no published proportions; "
                       f"choose from {sorted(DISTRIBUTION)}")
    townsfolk, outsiders, minions, demons = DISTRIBUTION[n]

    pool = {team: list(script.by_team(team)) for team in Team}
    for team in Team:
        rng.shuffle(pool[team])

    chosen_minions = _take(pool[Team.MINION], minions, script, "minion")
    # The setup-modifying minion is resolved BEFORE the good roles are drawn,
    # because it changes how many of each are drawn. It is the one role whose
    # effect is on the deal itself.
    log: list[str] = []
    if any(r.key == "warp" for r in chosen_minions):
        shift = min(2, townsfolk)
        shift = min(shift, len(pool[Team.OUTSIDER]) - outsiders)
        if shift > 0:
            townsfolk -= shift
            outsiders += shift
            log.append(f"setup: warp is in play, so {shift} townsfolk seat(s) "
                       f"became outsider seat(s)")

    chosen = list(_take(pool[Team.DEMON], demons, script, "demon"))
    chosen += chosen_minions
    chosen += _take(pool[Team.OUTSIDER], outsiders, script, "outsider")
    chosen += _take(pool[Team.TOWNSFOLK], townsfolk, script, "townsfolk")
    rng.shuffle(chosen)

    seats = [Seat(index=i, role=r, dealt=r, believes=r)
             for i, r in enumerate(chosen)]
    grim = Grimoire(seats=seats, script=script, log=log)
    grim.log.append("deal: " + ", ".join(f"{s.index}={s.role.key}"
                                         for s in seats))

    # The seat that is wrong about itself believes it holds a townsfolk role that
    # nobody holds - so no seat's claim can be checked against it, and the belief
    # never collides with a real reveal.
    sot = grim.find("sot")
    if sot is not None:
        in_play = {s.role.key for s in seats}
        spare = [r for r in script.by_team(Team.TOWNSFOLK)
                 if r.key not in in_play]
        if not spare:
            raise BadSetup(
                f"the {script.name} script has no spare townsfolk role for the "
                "seat that must believe it holds one")
        believed = rng.choice(spare)
        seats[sot].believes = believed
        grim.log.append(f"discretion: seat {sot} is the sot and believes it is "
                        f"the {believed.key}")

    # Three roles the demon may claim. Good roles not in play, so a claim cannot be
    # falsified by the seat that actually holds one.
    in_play = {s.role.key for s in seats}
    good_spare = [r.key for r in script.roles
                  if r.align is Align.GOOD and r.key not in in_play]
    rng.shuffle(good_spare)
    grim.bluffs = tuple(good_spare[:3])

    if grim.find_believer("diviner") is not None:
        good = [s.index for s in seats if s.align is Align.GOOD]
        if good:
            grim.herring = rng.choice(good)
            grim.log.append(f"discretion: seat {grim.herring} reads as the demon "
                            f"to the diviner all game")

    if grim.find("hermit") is not None:
        grim.hermit_evil = rng.random() < 0.5
        evil_roles = [r.key for r in script.roles if r.align is Align.EVIL
                      and r.key != "hermit"]
        grim.hermit_as = rng.choice(evil_roles) if evil_roles else "fiend"
        grim.log.append(
            f"discretion: the hermit registers "
            + (f"as evil, and as the {grim.hermit_as}" if grim.hermit_evil
               else "as good, as itself"))
    if grim.find("mimic") is not None:
        grim.mimic_good = rng.random() < 0.5
        good_roles = [r.key for r in script.by_team(Team.TOWNSFOLK)]
        grim.mimic_as = rng.choice(good_roles) if good_roles else "witness"
        grim.log.append(
            f"discretion: the mimic registers "
            + (f"as good, and as the {grim.mimic_as}" if grim.mimic_good
               else "as evil, as itself"))
    return grim


def _take(pool: list[Role], count: int, script: Script, what: str) -> list[Role]:
    if count > len(pool):
        raise BadSetup(
            f"the {script.name} script has {len(pool)} {what} role(s) and this "
            f"table needs {count}. A deal that quietly substituted another team "
            f"would be a different game from the one the proportions describe.")
    return [pool.pop() for _ in range(count)]
