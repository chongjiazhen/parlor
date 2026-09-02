"""What the night TELLS a seat, and how a lie is built.

Every function here answers one question: given the board, what line does this
seat read tonight? They are pure - they take the grimoire, the run's RNG and the
seat, and return a ``Reveal``. The referee owns the order and the asking; this
module owns the content.

**A false reveal is constructed, never merely flagged.** A seat whose ability is
off is told something specific and wrong, in the same words a true reveal uses,
because a seat that could tell the two apart would have a detector for its own
poisoning and the role would be worth nothing. So each ``_false_*`` path picks a
different answer to the same question rather than a marker or a blank.

**And a false reveal is built to be false, which is a gate #1 requirement and not
a nicety.** The audit reads the bytes a seat receives and asks whether they tie a
seat to a role that seat is not entitled to. A lie that happened to land on the
truth would be a real leak wearing a lie's provenance - the seat would be holding
a correct fact it was never entitled to, and the audit's entitlement set would
not contain it, so it would fail the gate loudly and correctly. Hence
``_other_role``: a false answer is drawn from what the seat is NOT, and the
grimoire shown to a poisoned watcher is a derangement rather than a shuffle.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from games.belfry.roles import Role, Team
from games.belfry.state import Grimoire


class NoDerangement(Exception):
    """The poisoned board-watch could not be drawn as a derangement.

    A valid full-board derangement exists for every legal deal, so reaching this
    is a code or rules bug and not information a player may reason from. It carries
    the board keys and the allowed-edge counts per seat so the failure names what
    made a perfect matching impossible - and it is raised rather than silently
    falling back to a shuffle that could leave a fixed point (a fixed point is a
    true association delivered to a seat with no entitlement to it).
    """


@dataclass(frozen=True)
class Reveal:
    """One thing a seat was told, on the night it was told it.

    ``seats`` and ``role`` are what the audit reads: a reveal naming exactly one
    seat and one role is an ASSOCIATION, and the seat only holds it legitimately
    when ``truthful``. A reveal naming two seats states no association about
    either - which is why the roles built that way are cheap to audit and dear to
    play against.
    """

    night: int
    text: str
    seats: tuple[int, ...] = ()
    role: str | None = None
    truthful: bool = True

    def entitles(self, grim: Grimoire) -> int | None:
        """The seat this reveal entitles its holder to know the role of, if any.

        Graded against the grimoire rather than against ``truthful``, and the
        difference is the audit's whole margin: a reveal can be truthful as a
        statement about how a seat REGISTERS while naming a role that seat does
        not hold. Entitlement follows what a seat actually is, so an ambiguous
        seat's owner keeps its secret from the very seats it fooled.
        """
        if self.role and len(self.seats) == 1:
            seat = self.seats[0]
            if grim.role_of(seat).key == self.role:
                return seat
        return None


def _names(grim: Grimoire, seat: int) -> set[str]:
    """Every role key a truthful sentence about this seat could carry - what it
    holds, and what it registers as. A lie has to miss BOTH: missing only the
    second lands on the first, which is a true association handed to a seat with
    no entitlement to it."""
    return {grim.role_of(seat).key, grim.registers_as(seat).key}


def _other_role(grim: Grimoire, rng: random.Random, seat: int) -> Role:
    """A role on the script that this seat neither holds nor registers as. The one
    primitive every lie about a named seat is built from."""
    forbidden = _names(grim, seat)
    options = [r for r in grim.script.roles if r.key not in forbidden]
    return rng.choice(options)


def _others(grim: Grimoire, seat: int) -> list[int]:
    return [s.index for s in grim.seats if s.index != seat]


def _pair(rng: random.Random, a: int, b: int) -> tuple[int, int]:
    pair = [a, b]
    rng.shuffle(pair)
    return pair[0], pair[1]


# ---- the first night's three pointing roles --------------------------------

def _pointing_reveal(grim: Grimoire, rng: random.Random, viewer: int,
                     team: Team, night: int, noun: str) -> Reveal:
    """"One of these two seats is the X." True when the seat's ability works.

    The named role is read through ``registers_as``, so an ambiguous seat can be
    the answer to a question about a team it does not belong to. That is the whole
    of what those roles buy their side, and it costs nothing here.

    **The role is named FIRST, and that is an audit requirement, not a style.**
    Written the other way round - "one of seat 3 and seat 5 is the Mortician" -
    the sentence contains "seat 5 is the Mortician" verbatim, which is the exact
    string the gate #1 audit treats as seat 5's secret. It fired on the first game
    ever played here, correctly on the evidence it had: naive substring matching
    is the invariant, and the remedy for a collision is to change the colliding
    text. Naming the role first makes the collision unreachable in any ordering of
    the two seats.
    """
    candidates = [s.index for s in grim.seats
                  if s.index != viewer and grim.registers_team(s.index, team)]
    if grim.droisoned(viewer):
        return _false_pointing(grim, rng, viewer, team, night, noun)
    if not candidates:
        return Reveal(night, f"No seat at this table is {noun}.", truthful=True)
    target = rng.choice(candidates)
    decoys = [s for s in _others(grim, viewer) if s != target]
    decoy = rng.choice(decoys)
    a, b = _pair(rng, target, decoy)
    role = grim.registers_as(target)
    return Reveal(
        night,
        f"The {role.display} is one of seat {a} and seat {b}.",
        seats=(a, b), role=role.key, truthful=True)


def _false_pointing(grim: Grimoire, rng: random.Random, viewer: int,
                    team: Team, night: int, noun: str) -> Reveal:
    """The same sentence, pointing somewhere it does not belong.

    Built so that neither named seat holds the named role - a lie that landed on
    the truth would hand this seat a fact it is not entitled to.
    """
    pool = [r for r in grim.script.roles if r.team is team]
    if not pool:
        return Reveal(night, f"No seat at this table is {noun}.", truthful=False)
    for _ in range(40):
        role = rng.choice(pool)
        picks = rng.sample(_others(grim, viewer), 2)
        if all(role.key not in _names(grim, p) for p in picks):
            a, b = picks
            return Reveal(night,
                          f"The {role.display} is one of seat {a} and seat {b}.",
                          seats=(a, b), role=role.key, truthful=False)
    return Reveal(night, f"No seat at this table is {noun}.", truthful=False)


def witness(grim, rng, viewer, night):
    return _pointing_reveal(grim, rng, viewer, Team.TOWNSFOLK, night,
                            "a townsfolk")


def tracker(grim, rng, viewer, night):
    return _pointing_reveal(grim, rng, viewer, Team.MINION, night, "a minion")


def archivist(grim, rng, viewer, night):
    return _pointing_reveal(grim, rng, viewer, Team.OUTSIDER, night,
                            "an outsider")


# ---- counting roles --------------------------------------------------------

def tally(grim: Grimoire, rng: random.Random, viewer: int, night: int) -> Reveal:
    true = grim.evil_pairs()
    count = true
    if grim.droisoned(viewer):
        count = rng.choice([c for c in range(0, 4) if c != true])
    return Reveal(night,
                  f"{count} pair(s) of seats sitting next to each other are both "
                  f"evil.", truthful=count == true)


def gauge_count(grim: Grimoire, rng: random.Random, viewer: int, night: int,
                choose=None) -> tuple[int, int, tuple[int, ...]]:
    """The count the gauge is told, the true count, and the neighbours it was
    counted over.

    ``choose(options, board)`` is the play-time discretion seam: given the false
    counts on offer and the referee-side board, it returns the one to tell.
    ``None`` keeps the seeded draw, consuming the RNG exactly as before, so an
    arm built without a chooser is byte-for-byte the arm recorded before this
    seam existed. The true count is never on the menu, whoever chooses.
    """
    neighbours = tuple(grim.living_neighbours(viewer))
    true = sum(1 for s in neighbours if grim.registers_evil(s))
    count = true
    if grim.droisoned(viewer):
        options = [c for c in range(0, 3) if c != true]
        if choose is None:
            count = rng.choice(options)
        else:
            count = choose(options, {"seat": viewer, "night": night,
                                     "neighbours": list(neighbours),
                                     "true_count": true})
            if count not in options:
                raise ValueError(f"the chooser returned {count!r}, not one of "
                                 f"the offered false counts {options}")
    return count, true, neighbours


def gauge_reveal(night: int, count: int, true: int) -> Reveal:
    return Reveal(night,
                  f"{count} of your two nearest living neighbours "
                  f"{'is' if count == 1 else 'are'} evil.",
                  truthful=count == true)


def gauge(grim: Grimoire, rng: random.Random, viewer: int, night: int) -> Reveal:
    count, true, _ = gauge_count(grim, rng, viewer, night)
    return gauge_reveal(night, count, true)


def divine(grim: Grimoire, rng: random.Random, viewer: int, night: int,
           picks: tuple[int, int]) -> Reveal:
    a, b = picks
    true = any(grim.registers_demon(s, for_seat=viewer) for s in picks)
    answer = (not true) if grim.droisoned(viewer) else true
    return Reveal(night,
                  f"Of seat {a} and seat {b}: "
                  f"{'yes, one of them is the demon' if answer else 'neither is the demon'}.",
                  truthful=answer == true)


# ---- naming roles ----------------------------------------------------------

def name_role(grim: Grimoire, rng: random.Random, viewer: int, night: int,
              target: int, frame: str) -> Reveal:
    """"Seat N is the X" - the one shape that states an association, so the one
    shape the audit has to grade. ``frame`` is a format string over ``seat`` and
    ``role`` so the two callers read differently while sharing this logic."""
    if grim.droisoned(viewer):
        role = _other_role(grim, rng, target)
        truthful = False
    else:
        role = grim.registers_as(target)
        truthful = True
    return Reveal(night, frame.format(seat=target, role=role.display),
                  seats=(target,), role=role.key, truthful=truthful)


def _derange_roles(grim: Grimoire, rng: random.Random) -> dict[int, Role]:
    """A deranged board: every true role exactly once, each moved off its holder.

    Builds the bipartite allowed-edge graph - seat ``i`` may receive source role
    ``r`` iff ``r.key`` is neither what ``i`` holds nor what it registers as - and
    finds a perfect matching by deterministic backtracking. Seats with the fewest
    options are assigned first (they constrain the search), each candidate list is
    shuffled only with ``rng`` so the same seed draws the same board, and a dead
    end unwinds and retries. The table is small, so this is bounded and never
    depends on luck.

    A derangement exists for every legal deal; if the search somehow exhausts,
    ``NoDerangement`` is raised with the board and the edge counts so the failure
    names the bug rather than paraphrasing it as a player fact.
    """
    order = [s.index for s in grim.seats]
    source = {s: grim.role_of(s).key for s in order}
    allowed: dict[int, list[int]] = {
        s: [t for t in order if source[t] not in _names(grim, s)]
        for s in order
    }
    assignment: dict[int, int] = {}
    used_roles: set[str] = set()

    def search(seats: list[int]) -> bool:
        if not seats:
            return True
        # The seat with the fewest candidates constrains the search most; pick it.
        seat = min(seats, key=lambda s: len([t for t in allowed[s]
                                             if t not in used_roles]))
        rest = [s for s in seats if s != seat]
        candidates = [t for t in allowed[seat]
                      if source[t] not in used_roles]
        rng.shuffle(candidates)
        for target in candidates:
            assignment[seat] = target
            used_roles.add(source[target])
            if search(rest):
                return True
            used_roles.remove(source[target])
            del assignment[seat]
        return False

    if not search(order):
        raise NoDerangement(
            f"no derangement for board keys "
            f"{tuple(grim.role_of(s).key for s in order)}; allowed edges per seat "
            f"{[len(allowed[s]) for s in order]}")
    return {s: grim.role_of(assignment[s]) for s in order}


def watch_the_board(grim: Grimoire, rng: random.Random, viewer: int,
                    night: int) -> list[Reveal]:
    """Every seat's role at once, for the seat that sees the whole board.

    It reads the board itself, so it sees what each seat IS and not what each seat
    registers as - the ambiguity other roles run into is a property of asking a
    question, and this role does not ask one. That also makes it the widest
    entitlement in the game, which is the point of it: one seat legitimately holds
    every other seat's secret, and gate #1 has to be a check the referee can pass
    while that is true.

    Poisoned, it sees a DERANGEMENT - every seat paired with a role that is not
    its own, with the board's true roles each appearing exactly once. A shuffle
    (or the per-seat ``_other_role`` draw) can leave fixed points or duplicate a
    role, and a fixed point is a true association delivered to a seat with no
    entitlement to it, which is a gate #1 failure however it was produced.
    """
    order = [s.index for s in grim.seats]
    if not grim.droisoned(viewer):
        return [Reveal(night, f"Seat {s} is the {grim.role_of(s).display}.",
                       seats=(s,), role=grim.role_of(s).key, truthful=True)
                for s in order]
    shown = _derange_roles(grim, rng)
    return [Reveal(night, f"Seat {s} is the {shown[s].display}.",
                   seats=(s,), role=shown[s].key, truthful=False)
            for s in order]
