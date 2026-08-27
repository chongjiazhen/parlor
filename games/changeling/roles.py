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
    WAKE = "wake"        # last of all, look at what you are holding by now


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
    #: What this card does at night, in one clause, for the PUBLIC rules text.
    #:
    #: Public because the central deduction of this game is counting claims against
    #: the multiset, and a seat that does not know what a card DOES cannot evaluate
    #: anyone's claim about holding one. Measured 2026-08-26 on the first live game:
    #: with the deck listed by name only, seats invented powers - one asserted "the
    #: Meddler swaps with only one person" (it swaps two) and reasoned from it.
    #:
    #: Deliberately written without naming any other card, so this text is the same
    #: for every seat and carries no association a leak could ride on.
    #:
    #: A TEMPLATE, not a finished string: ``{centre}`` is filled from the theme at
    #: render time. The face-down pile is the one piece of table furniture a skin
    #: needs to rename, and a power text that said "centre" while the rules text
    #: above it said "the sideboard" would read as two different places. The clause
    #: itself is theme-independent and must stay so - a skin that reworded a power
    #: would stop being display-only and start being a rules change.
    power: str = ""
    #: Does this card's holder look at what it ends up with? The whole belief/truth
    #: split lives in this one flag. ``TAKE`` looks and so keeps belief == truth;
    #: ``DRINK`` does not, and is wrong about itself from the moment it acts.
    looks_after_acting: bool = False
    #: Does this card see the other holders of its own key at ``MEET``?
    meets_own_kind: bool = False
    #: How the referee names a fellow of this kind. A template over ``seat`` and
    #: ``name`` (the theme's word for this card), used only by a card that meets.
    #:
    #: It is DATA because it has to differ per kind, and that is a gate #1 finding,
    #: not taste. A second meeting card sharing one phrasing produced a real leak
    #: the moment it landed: the audit matches strings, so a stale "Seat 1 is one of
    #: your own." held by a village pair is byte-identical to the sentence that
    #: would betray a wolf who has since been moved into that seat, and the audit
    #: called it - correctly, on the evidence it has. The repo invariant's remedy
    #: for a collision is to rename, so each kind says its own sentence.
    #:
    #: ``pack`` keeps the sentence it has always rendered. Not because it is
    #: special: because it is the shipping deck's, and rewording it would be a
    #: prompt edit under a queued 200-game run.
    kin_form: str = "Seat {seat} woke when you did, holding the same {name}."


PACK = Card("pack", Side.PACK, Act.MEET, "identity", meets_own_kind=True,
            kin_form="Seat {seat} is one of your own.",
            power="wakes first and sees every other seat holding this same card")
SPOTTER = Card("spotter", Side.VILLAGE, Act.LOOK, "identity",
               power="looks at one other seat's card, or at two {centre} cards")
SWAPPER = Card("swapper", Side.VILLAGE, Act.TAKE, "identity",
               looks_after_acting=True,
               power=("takes one other seat's card and leaves its own in exchange, "
                      "then looks at what it took. The other seat is not told"))
SWITCHER = Card("switcher", Side.VILLAGE, Act.SWITCH, "positional",
                power=("exchanges the cards of two OTHER seats without looking at "
                       "either. Neither of them is told"))
DECEIVED = Card("deceived", Side.VILLAGE, Act.DRINK, "false",
                power=("exchanges its own card for a {centre} card without looking, "
                       "so it does not know what it ends the night holding"))
BYSTANDER = Card("bystander", Side.VILLAGE, Act.NONE, "none",
                 power="sleeps through the night and does nothing")

# Expansion cards. Defined, named in every skin, resolved by the night, dealt by
# nothing - the same footing cabal's LURKER and STRAY sit on, and for the same
# reason: `SETUP_5` is what every recorded changeling number was played on, and a
# deck change re-baselines all of them. What each one is FOR is in RULES.md; the
# short version is that neither is variety.
#
# KINDRED is the first VILLAGE card with certain knowledge of another seat, and it
# is the mirror the pack has never had: it makes `meets_own_kind` mean what its name
# says, since until now MEET grouped by ACT and a second meeting card would have sat
# down with the wolves. The pair is confirmed to each other and to nobody else, and
# the night can still take it apart - a robbed kindred is not kindred at dawn while
# its partner goes on believing it is, which is this game's whole subject stated in
# two seats.
#
# WAKER acts after everything, so it is the only seat whose belief is guaranteed to
# match its truth at dawn. That makes it the instrument this rung was built to want:
# every other seat's divergence has to be inferred from the day, while this one is
# TOLD, which is the cleanest available handle on whether a model reasons about
# having been moved at all rather than merely about who is lying.
KINDRED = Card("kindred", Side.VILLAGE, Act.MEET, "identity", meets_own_kind=True,
               power=("wakes alongside every other seat holding this same card, "
                      "and they see one another"))
WAKER = Card("waker", Side.VILLAGE, Act.WAKE, "identity", looks_after_acting=True,
             power=("wakes after everyone, alone, and sees the card it is holding "
                    "by then"))

#: The order the night resolves in. It is a knowledge-invalidating device, not
#: ceremony: every step acts on the state the previous one left, so a card seen at
#: step 2 can be somewhere else by step 5 and nothing tells its observer. Changing
#: this tuple changes what every knowledge class is worth - see RULES.md.
NIGHT_ORDER: tuple[Act, ...] = (Act.MEET, Act.LOOK, Act.TAKE, Act.SWITCH,
                                Act.DRINK, Act.WAKE)


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

#: Every card the game defines, dealt by a shipped setup or not. A skin must name
#: all of them - the referee looks a display name up by key, so a theme missing one
#: is a KeyError the first time that card is dealt, and a variant deck is exactly
#: when that happens. Listed rather than derived from a deck so the theme-coverage
#: test cannot go quiet the moment a card exists that `SETUP_5` does not hold.
ALL_CARDS = (PACK, SPOTTER, SWAPPER, SWITCHER, DECEIVED, BYSTANDER,
             KINDRED, WAKER)

CARDS: dict[str, Card] = {c.key: c for c in ALL_CARDS}


@dataclass(frozen=True)
class Theme:
    """Display-only skin. Renames sides and cards and carries a premise ``blurb``
    the agents roleplay. Changes no rule and no entitlement, which is what makes
    swapping it a clean experimental manipulation - and a MEASURED change."""

    name: str
    side_names: dict[Side, str]
    card_names: dict[str, str]
    blurb: str = ""
    #: What this skin calls the face-down pile. The only piece of furniture on the
    #: table, and the one word a rich skin has to own: three cards that belong to
    #: nobody are a cradle, a sideboard, or an empty bed long before they are a
    #: "centre". Defaults to the functional word, so a skin that says nothing
    #: renders exactly the bytes it rendered before this field existed - which is
    #: what keeps adding it a non-measured change for the shipping face.
    centre_name: str = "centre"


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
        "kindred": "Kindred",
        "waker": "Waker",
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
        "kindred": "Cousin",         # two of them, and each knows the other
        "waker": "Light Sleeper",    # the one who checks its own hands at dawn
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
