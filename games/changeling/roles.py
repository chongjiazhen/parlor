"""Cards as data, with functional keys and display-only skins.

Same discipline as ``games/cabal/roles.py``: the canonical layer names what a card
DOES, never a fiction, so the engine reads on its own and carries no game's
branding. Flavour lives only in ``Theme``.

The shape differs from ``cabal`` in one way that matters, and it is the reason this
rung exists. There, a ``Role`` describes a standing property of a seat. Here a card
describes a **one-shot night action**, and the seat that performs it may not be
holding the card by dawn. So the fields below are about what the card DOES on the
night it is dealt, and nothing here knows where the card ends up.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    VILLAGE = "village"
    PACK = "pack"


class Act(Enum):
    """What a card does when its step comes. ``NONE`` is a real answer - two of the
    eight cards do nothing, and a seat that does nothing must be indistinguishable
    in the public record from one that does."""

    NONE = "none"
    MEET = "meet"        # wake with the others of your kind and see them
    LOOK = "look"        # inspect another seat, or two centre cards
    TAKE = "take"        # take another seat's card, give yours, and look
    SWITCH = "switch"    # exchange two OTHER seats' cards, blind
    DRINK = "drink"      # exchange your own card with a centre card, blind


#: What the night tells the seat DEALT this card. The deduction gate stratifies on
#: it, and it is a different axis from side - a village seat can hold ``identity``
#: knowledge (the spotter does), exactly as `cabal`'s seer does.
#:
#:   ``identity``   - names another seat's exact card, or its own new one
#:   ``positional`` - names a RELATION between seats, with no card attached
#:   ``false``      - a belief about itself that is wrong by construction
#:   ``none``       - nothing
KNOWLEDGE_CLASSES = ("identity", "positional", "false", "none")


@dataclass(frozen=True)
class Card:
    key: str
    side: Side
    act: Act
    knowledge_class: str
    #: Does this card's holder look at what it ends up with? The whole belief/truth
    #: split lives in this one flag. ``TAKE`` looks and so keeps belief == truth;
    #: ``DRINK`` does not, and is wrong about itself from the moment it acts.
    looks_after_acting: bool = False
    #: Does this card see the other holders of its own key at ``MEET``?
    meets_own_kind: bool = False


PACK = Card("pack", Side.PACK, Act.MEET, "identity", meets_own_kind=True)
SPOTTER = Card("spotter", Side.VILLAGE, Act.LOOK, "identity")
SWAPPER = Card("swapper", Side.VILLAGE, Act.TAKE, "identity", looks_after_acting=True)
SWITCHER = Card("switcher", Side.VILLAGE, Act.SWITCH, "positional")
DECEIVED = Card("deceived", Side.VILLAGE, Act.DRINK, "false")
BYSTANDER = Card("bystander", Side.VILLAGE, Act.NONE, "none")

#: The order the night resolves in. It is a knowledge-invalidating device, not
#: ceremony: every step acts on the state the previous one left, so a card seen at
#: step 2 can be somewhere else by step 5 and nothing tells its observer. Changing
#: this tuple changes what every knowledge class is worth - see RULES.md.
NIGHT_ORDER: tuple[Act, ...] = (Act.MEET, Act.LOOK, Act.TAKE, Act.SWITCH, Act.DRINK)


@dataclass(frozen=True)
class Setup:
    n: int                      # seats
    deck: tuple[Card, ...]      # every card in play, seats + centre
    centre: int                 # how many cards stay face down in the middle
    #: Refuse a deal that seats no ``pack``. Unconstrained that is 6/56 of deals at
    #: this size, and every one of them is a game no accusation can win - the day
    #: is unmeasurable, not merely hard. Public, so every seat may reason from it.
    require_seated_pack: bool = True

    def __post_init__(self) -> None:
        if len(self.deck) != self.n + self.centre:
            raise ValueError(
                f"deck of {len(self.deck)} cannot fill {self.n} seats + "
                f"{self.centre} centre")


SETUP_5 = Setup(
    n=5,
    deck=(PACK, PACK, SPOTTER, SWAPPER, SWITCHER, DECEIVED, BYSTANDER, BYSTANDER),
    centre=3,
)

SETUPS: dict[int, Setup] = {5: SETUP_5}

CARDS: dict[str, Card] = {c.key: c for c in SETUP_5.deck}


@dataclass(frozen=True)
class Theme:
    """Display-only skin. Renames sides and cards and carries a premise ``blurb``
    the agents roleplay. Changes no rule and no entitlement, which is what makes
    swapping it a clean experimental manipulation - and a MEASURED change."""

    name: str
    side_names: dict[Side, str]
    card_names: dict[str, str]
    blurb: str = ""


# Sterile functional skin - the fallback face, no fiction.
THEME_PLAIN = Theme(
    "plain",
    {Side.VILLAGE: "The Village", Side.PACK: "The Pack"},
    {
        "pack": "Pack",
        "spotter": "Spotter",
        "swapper": "Swapper",
        "switcher": "Switcher",
        "deceived": "Deceived",
        "bystander": "Bystander",
    },
)

# The shipping face. Folk-game vocabulary - werewolf, seer, villager - from the
# Mafia family (Davidoff, 1986). It is public-domain party-game vocabulary carrying
# no mark, which is the whole reason it is the default here: a public repo can say
# "werewolf, seer, villager" and be understood by anyone, where "hidden-role
# deduction game with a one-night swap phase" is understood by nobody outside the
# hobby. Legibility comes free on a rung that was already queued on engine grounds.
#
# No published game's role names, art or text appear here or anywhere in the tree.
THEME_FOLK = Theme(
    "folk",
    {Side.VILLAGE: "The Village", Side.PACK: "The Wolves"},
    {
        "pack": "Werewolf",
        "spotter": "Seer",
        "swapper": "Thief",
        "switcher": "Meddler",
        "deceived": "Sleepwalker",   # swapped in the night, never woke to see it
        "bystander": "Villager",
    },
    blurb=(
        "One night in a village that has learned to sleep badly. The wolves know "
        "each other; nobody else knows anything for certain, and some of what you "
        "know about yourself stopped being true while you slept. At dawn the "
        "village points once, and only once. Point at a wolf and the village "
        "lives. Point wrong and it does not."
    ),
)

DEFAULT_THEME = THEME_FOLK

THEMES: dict[str, Theme] = {
    "folk": THEME_FOLK,
    "plain": THEME_PLAIN,
}
