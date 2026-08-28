"""Roles, cards and skins as data, with functional (trademark-free) keys.

The canonical layer - dir, class, role keys, card keys - describes what each thing
*does*, never a fiction. Flavour lives only in ``Theme``, which is display-only.
The rules implemented here are those of a legislative hidden-role deduction game;
no published game's branding appears in the code.

Two naming decisions here are load-bearing and are recorded in ``RULES.md`` as
well, because a reasonable edit would undo either:

**Sides are named for the three-against-two, not for what they know.** cabal
records the cost of naming a side for its knowledge - it put two meanings of one
word on a single seat - and the knowledge classes here are a separate axis.

**Cards are NOT named ``majority``/``minority``, even though each advances one
side's track.** That would be the obvious functional name and it is the wrong one:
the side display names appear in every seat's own "Your role" line, so a card term
that is a substring of a side term would trip the leak audit on every legal call.
``charter`` and ``writ`` are neutral legal instruments of near-equal valence,
short, and unlikely to appear in a seat's own speech - which is what a sentinel
has to be. The polarity symmetry is deliberate too: a ``clean``/``corrupt`` pair
would be a moral-framing change in the canonical layer, and ``docs/moral-framing.md``
records framing as a measured variable rather than decoration.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    MAJORITY = "majority"
    MINORITY = "minority"


class Card(Enum):
    """A card advances exactly one side's track when enacted."""

    CHARTER = "charter"   # advances MAJORITY
    WRIT = "writ"         # advances MINORITY


#: Which side each card advances. One statement, so a variant that adds a third
#: card kind moves the tracks and the win conditions together.
ADVANCES: dict[Card, Side] = {Card.CHARTER: Side.MAJORITY, Card.WRIT: Side.MINORITY}


@dataclass(frozen=True)
class Role:
    key: str
    side: Side
    #: this seat is told its fellow minority seats (False = the blind variant)
    sees_fellow_minority: bool = True
    #: other minority seats are told about this one
    seen_by_fellow_minority: bool = True
    #: installing this seat as enactor after the threshold ends the game
    is_principal: bool = False


ELECTOR = Role("elector", Side.MAJORITY,
               sees_fellow_minority=False, seen_by_fellow_minority=False)
BROKER = Role("broker", Side.MINORITY)
PRINCIPAL = Role("principal", Side.MINORITY, is_principal=True)

# Data only, dealt by nothing. At 7+ seats the published shape hides `principal`
# from its own side: the minority seats know each other and `principal` knows
# nobody, which turns minority coordination into inference rather than convention.
# `agent` is the seat that fills out a larger minority. Not seated at five, where
# `principal` knowing nothing would leave one of the two playing blind - the same
# reason cabal declines to seat `lurker` and `stray` there.
AGENT = Role("agent", Side.MINORITY)

#: Every role the game defines, seated or not. A skin must name all of them - the
#: referee looks a display name up by key, so a theme missing one is a KeyError the
#: first time that role is dealt, and a variant setup is exactly when that happens.
#: Listed rather than derived so the theme-coverage test cannot go stale.
ALL_ROLES = (ELECTOR, BROKER, PRINCIPAL, AGENT)

#: key -> role, for anything reading a FINISHED record, which stores the assignment
#: as strings. cabal learned this the hard way: every post-hoc reader that lacked
#: the lookup hardcoded the knowledge model instead.
ROLES_BY_KEY: dict[str, Role] = {r.key: r for r in ALL_ROLES}


def known_allies(assignment: dict[int, Role], seat: int) -> set[int]:
    """The seats the deal named to ``seat`` as its own side.

    Derived from the role flags rather than from the key, so the blind variant -
    where `principal` is told nothing - moves every caller at once.
    """
    me = assignment[seat]
    if me.side is not Side.MINORITY or not me.sees_fellow_minority:
        return set()
    return {s for s, r in assignment.items()
            if s != seat and r.side is Side.MINORITY and r.seen_by_fellow_minority}


@dataclass(frozen=True)
class Setup:
    n: int
    roles: tuple[Role, ...]
    #: Deck composition. Stated here because it is a RULE and not a knob: the
    #: imbalance is what makes a forced enactment possible often enough that "I had
    #: no choice" is a real defence rather than a transparent lie, which is the
    #: ambiguity this rung exists to measure. A run that changes it is a measured
    #: change on the same terms as a prompt edit.
    deck_charter: int = 6
    deck_writ: int = 11
    #: Tracks that end the game.
    charter_target: int = 5
    writ_target: int = 6
    #: Writs enacted before installing `principal` as enactor wins for the minority.
    install_threshold: int = 3
    #: writs enacted -> the power the proposer then exercises. Kept as data so a
    #: seat count that fires powers on different counts is a row, not a branch.
    powers: tuple[tuple[int, str], ...] = ((3, "inspect"), (4, "remove"), (5, "remove"))
    #: Consecutive failed votes before the top card is enacted with nobody seeing it.
    failure_limit: int = 3

    @property
    def deck_size(self) -> int:
        return self.deck_charter + self.deck_writ

    def power_at(self, writs: int) -> str | None:
        for count, name in self.powers:
            if count == writs:
                return name
        return None


SETUP_5 = Setup(
    n=5,
    roles=(ELECTOR, ELECTOR, ELECTOR, BROKER, PRINCIPAL),
)

SETUPS: dict[int, Setup] = {5: SETUP_5}


@dataclass(frozen=True)
class Theme:
    """Display-only skin over the mechanics. Renames sides, roles, cards and the two
    offices, and may carry a ``blurb`` premise the agents roleplay.

    ``blurb`` defaults to empty and the shipped default leaves it that way. A
    premise is a measured variable, not decoration, and the contrast set that
    measures it needs a premise-free baseline to read against - see cabal's
    ``THEME_LODGE`` for the same decision and ``docs/moral-framing.md`` for why.
    """

    name: str
    side_names: dict[Side, str]
    role_names: dict[str, str]
    card_names: dict[Card, str]
    #: office key -> display. Offices rotate, so they are display like everything
    #: else here; the entitlement they carry is computed from the office, never
    #: from its name.
    office_names: dict[str, str]
    blurb: str = ""


# Sterile functional skin - the fallback face, no fiction. Every string is a
# Title-Cased echo of the canonical key and nothing more. That is what `plain`
# means in this repo, and cabal's `plain` failed it for a while by coining faction
# words - one of which was the module's own name.
THEME_PLAIN = Theme(
    "plain",
    {Side.MAJORITY: "The Majority", Side.MINORITY: "The Minority"},
    {
        "elector": "Elector",
        "broker": "Broker",
        "principal": "Principal",
        "agent": "Agent",
    },
    {Card.CHARTER: "Charter", Card.WRIT: "Writ"},
    {"proposer": "Proposer", "enactor": "Enactor"},
)

# The default face. A chartered trade guild voting its own bylaws - a generic
# institution referencing no published work, order or product, and carrying no
# mark. Vocabulary only, no blurb: the same decision as cabal's `lodge`, for the
# same reason.
#
# It is still a MEASURED change against `plain`. Names carry connotation, and
# RESUME.md already records that a role name can move a seat's threat assessment
# out of proportion to what the role mechanically does.
THEME_GUILD = Theme(
    "guild",
    {Side.MAJORITY: "The Hall", Side.MINORITY: "The Compact"},
    {
        "elector": "Freeman",
        "broker": "Whip",            # counts the votes its side already has
        "principal": "Aspirant",     # seating it is the win, which is why it hides
                                     # (not "Candidate": the referee's own
                                     # nomination prose uses that word, and a
                                     # sentinel that collides with the record
                                     # makes gate #1 fire on a legal turn)
        "agent": "Partisan",
    },
    {Card.CHARTER: "Charter", Card.WRIT: "Writ"},
    {"proposer": "Speaker", "enactor": "Sealer"},
)

DEFAULT_THEME = THEME_GUILD

#: Ordering is a decision, not a tidy-up, so it is stated here: **`plain` first**,
#: then one block per FAMILY in the order the family was created, and inside a
#: family the translations sit together with any later variant after them. It reads
#: as the rung's own history - which face came first, what was built off it - and
#: alphabetical order destroys exactly that. A later pass that sorts this dict
#: alphabetically is undoing the decision; re-derive the order from
#: `git log -S"THEME_<NAME> = Theme"` rather than from the names.
THEMES: dict[str, Theme] = {
    "plain": THEME_PLAIN,          # 2026-08-28, the sterile baseline
    "guild": THEME_GUILD,          # 2026-08-28, and the default since
}
