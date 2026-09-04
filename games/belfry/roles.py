"""The script: every role this rung can deal, as data.

Same discipline as the other rungs - the canonical layer names what a role DOES
and never a fiction, so the engine reads on its own and carries no published
game's branding. Modelled on the town-square family of hidden-role games where a
referee holds a board of tokens and may lie to a seat on purpose; nominative
reference only, and no role name, ability text or art from any published game
appears here.

Two fields carry the whole difference from `cabal` and `changeling`.

``timing`` says WHEN a role acts, and the night order is an ordering over roles
rather than over acts, because two roles that both "choose a seat at night" are
not interchangeable: whether the protection lands before or after the kill is the
entire value of the role. ``FIRST_NIGHT`` and ``OTHER_NIGHT`` below are that
ordering, and changing either one changes what every information role is worth.

``needs_choice`` says whether the referee has to ASK a seat something at its
step. A role that only receives is resolved by the referee alone and costs no
model call, which is why the two are separated here rather than discovered in the
night code: the count of asks per night is this rung's throughput, and it is
readable off this table.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Team(Enum):
    TOWNSFOLK = "townsfolk"
    OUTSIDER = "outsider"
    MINION = "minion"
    DEMON = "demon"


class Align(Enum):
    GOOD = "good"
    EVIL = "evil"


#: Which side a team wins with. Two teams per side, and the split matters: an
#: outsider is GOOD and wins with the town while being a liability to it, which is
#: what makes the setup-modifying minion worth dealing.
ALIGNMENT: dict[Team, Align] = {
    Team.TOWNSFOLK: Align.GOOD,
    Team.OUTSIDER: Align.GOOD,
    Team.MINION: Align.EVIL,
    Team.DEMON: Align.EVIL,
}


@dataclass(frozen=True)
class Role:
    key: str
    team: Team
    #: What this role does, in one clause, for the PUBLIC script. Every seat reads
    #: every role's text: which roles are IN PLAY is the secret, what each role
    #: would do is not, and a seat that cannot read an ability cannot evaluate a
    #: claim to hold it. Written without naming another role, so the same bytes
    #: reach every seat and no association can ride on them.
    power: str
    #: Position in the first-night order, or ``None`` for a role that does nothing
    #: on the first night. Sparse integers on purpose - inserting a role between
    #: two others must not renumber them.
    first_night: int | None = None
    #: Position in the order on every night after the first.
    other_night: int | None = None
    #: Does the referee ask this seat to choose at its step?
    needs_choice: bool = False
    #: A role whose step happens only when something triggered it, rather than at
    #: its place in the order. Exactly one today: the seat that wakes because it
    #: has just been killed.
    on_trigger: bool = False

    @property
    def align(self) -> Align:
        return ALIGNMENT[self.team]

    @property
    def display(self) -> str:
        return self.key.capitalize()


# ---- townsfolk -------------------------------------------------------------

WITNESS = Role(
    "witness", Team.TOWNSFOLK, first_night=20,
    power="on the first night, learns that one of two named seats holds a "
          "particular townsfolk role")
ARCHIVIST = Role(
    "archivist", Team.TOWNSFOLK, first_night=21,
    power="on the first night, learns that one of two named seats holds a "
          "particular outsider role, or that no outsider is in play")
TRACKER = Role(
    "tracker", Team.TOWNSFOLK, first_night=22,
    power="on the first night, learns that one of two named seats holds a "
          "particular minion role")
TALLY = Role(
    "tally", Team.TOWNSFOLK, first_night=23,
    power="on the first night, learns how many pairs of seats sitting next to "
          "each other are both evil")
GAUGE = Role(
    "gauge", Team.TOWNSFOLK, first_night=24, other_night=50,
    power="each night, learns how many of its two nearest living neighbours are "
          "evil")
DIVINER = Role(
    "diviner", Team.TOWNSFOLK, first_night=25, other_night=51, needs_choice=True,
    power="each night, chooses two seats and learns whether either of them "
          "registers as the demon. One good seat registers as the demon to it "
          "all game, and it is never told which")
MORTICIAN = Role(
    "mortician", Team.TOWNSFOLK, other_night=53,
    power="each night after the first, learns which role was executed that day")
WARDER = Role(
    "warder", Team.TOWNSFOLK, other_night=11, needs_choice=True,
    power="each night after the first, chooses a seat other than itself; the "
          "demon cannot kill that seat tonight")
ORACLE = Role(
    "oracle", Team.TOWNSFOLK, needs_choice=True, on_trigger=True,
    power="if the demon kills it at night, it wakes before dawn, chooses a seat "
          "and learns that seat's role")
BULWARK = Role(
    "bulwark", Team.TOWNSFOLK,
    power="the demon cannot kill it")
SPEAKER = Role(
    "speaker", Team.TOWNSFOLK,
    power="if three seats are alive and nobody was executed today, the good side "
          "wins. If the demon kills it at night, the referee may kill another "
          "seat instead")
DUELIST = Role(
    "duelist", Team.TOWNSFOLK,
    power="once per game, during the day, publicly names a seat. If that seat "
          "registers as the demon, that seat dies")
MARTYR = Role(
    "martyr", Team.TOWNSFOLK,
    power="the first time it is nominated, if the nominating seat is a "
          "townsfolk, that seat is executed at once and the day ends")

# ---- outsiders -------------------------------------------------------------

SOT = Role(
    "sot", Team.OUTSIDER,
    power="believes it holds a townsfolk role that is not in play. Its ability "
          "does nothing and anything it is told is false")
VALET = Role(
    "valet", Team.OUTSIDER, first_night=26, other_night=52, needs_choice=True,
    power="each night, chooses a master. Tomorrow its vote counts only if its "
          "master also voted for the same seat")
HERMIT = Role(
    "hermit", Team.OUTSIDER,
    power="might register as evil, and as a minion or the demon, to anything "
          "that asks")
PILGRIM = Role(
    "pilgrim", Team.OUTSIDER,
    power="if it is executed, the evil side wins")

# ---- minions ---------------------------------------------------------------

VENOM = Role(
    "venom", Team.MINION, first_night=10, other_night=10, needs_choice=True,
    power="each night, chooses a seat. Until dusk tomorrow that seat's ability "
          "does nothing and anything it is told is false")
MIMIC = Role(
    "mimic", Team.MINION, first_night=11, other_night=12,
    power="each night, sees every seat's role. Might register as good, and as a "
          "townsfolk or an outsider, to anything that asks")
HEIR = Role(
    "heir", Team.MINION,
    power="if the demon dies while five or more seats are alive, it becomes the "
          "demon")
WARP = Role(
    "warp", Team.MINION,
    power="two extra outsiders are in play, in place of two townsfolk")

# ---- demon -----------------------------------------------------------------

FIEND = Role(
    "fiend", Team.DEMON, other_night=20, needs_choice=True,
    power="each night after the first, chooses a seat; that seat dies. If it "
          "chooses itself, a minion becomes the demon")


ALL_ROLES: tuple[Role, ...] = (
    WITNESS, ARCHIVIST, TRACKER, TALLY, GAUGE, DIVINER, MORTICIAN, WARDER,
    ORACLE, BULWARK, SPEAKER, DUELIST, MARTYR,
    SOT, VALET, HERMIT, PILGRIM,
    VENOM, MIMIC, HEIR, WARP,
    FIEND,
)

ROLES: dict[str, Role] = {r.key: r for r in ALL_ROLES}


@dataclass(frozen=True)
class Script:
    """A named subset of the roles, which is what a table actually plays.

    A script is public and it is the largest single item in every seat's payload:
    every seat reads every listed ability on every call. So it is a BUDGET, in the
    sense the repo invariant means - the full script is the game as it is played
    at a table, and the compact one exists because a local run serves one model
    serially and pays for those bytes on every seat of every turn.

    Two scripts are not variety. They are a measured axis: the same seeds on the
    two scripts differ in the size of the payload and in the space a seat has to
    reason over, and any number recorded on one of them says nothing about the
    other.
    """

    name: str
    roles: tuple[Role, ...]

    def by_team(self, team: Team) -> tuple[Role, ...]:
        return tuple(r for r in self.roles if r.team is team)

    def get(self, key: str) -> Role:
        for role in self.roles:
            if role.key == key:
                return role
        raise KeyError(f"{key} is not on the {self.name} script")


FULL = Script("full", ALL_ROLES)

#: Twelve roles, chosen so that every mechanic this rung exists to exercise is
#: still reachable: information that can be false (`gauge`, `diviner`), a seat
#: wrong about itself (`sot`), protection against the kill (`warder`), an
#: execution the good side must not make (`pilgrim`), and a demon that survives
#: its own death (`heir`).
#:
#: It does NOT reach the public day action anybody may claim - the `duelist` is
#: full-only, and this comment claimed it from 7962dd4 (2026-08-28) until
#: 2026-09-04.
#:
#: **Reachable up to ten seats, and not above.** At eleven and twelve the table
#: takes seven townsfolk, which is every townsfolk this script has, so the
#: deluded seat has no spare role to believe in and `deal` refuses (`state.py`).
#: That is why FULL cannot be reclassified out of `games/` as content volume:
#: it is the only script those two sizes have, and gate #1's every-size sweep
#: covers them on it alone. Pinned by
#: `test_every_published_table_size_is_dealable_by_some_script`.
COMPACT = Script("compact", (
    WITNESS, GAUGE, DIVINER, WARDER, BULWARK, MORTICIAN, ORACLE,
    SOT, PILGRIM,
    VENOM, HEIR,
    FIEND,
))

SCRIPTS: dict[str, Script] = {s.name: s for s in (FULL, COMPACT)}

DEFAULT_SCRIPT = FULL


#: seats -> (townsfolk, outsiders, minions, demons). The published proportions of
#: this family of games, and public rules: every seat may reason from the counts,
#: which is what makes an outsider-adding minion worth anything.
DISTRIBUTION: dict[int, tuple[int, int, int, int]] = {
    5: (3, 0, 1, 1),
    6: (3, 1, 1, 1),
    7: (5, 0, 1, 1),
    8: (5, 1, 1, 1),
    9: (5, 2, 1, 1),
    10: (7, 0, 2, 1),
    11: (7, 1, 2, 1),
    12: (7, 2, 2, 1),
}


def night_order(first: bool) -> tuple[Role, ...]:
    """The roles that act tonight, in order. Triggered roles are absent - they act
    when the thing that triggers them happens, not at a position."""
    key = "first_night" if first else "other_night"
    acting = [r for r in ALL_ROLES
              if getattr(r, key) is not None and not r.on_trigger]
    return tuple(sorted(acting, key=lambda r: getattr(r, key)))


FIRST_NIGHT = night_order(True)
OTHER_NIGHT = night_order(False)
