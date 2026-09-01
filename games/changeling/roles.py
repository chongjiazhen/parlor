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


def indefinite(noun: str) -> str:
    """``noun`` with the article it takes - "a centre", "an altar".

    Here because a power template is one string shared by every skin while the noun
    it interpolates comes FROM the skin, so no author of either half is in a
    position to write the article. Hardcoding "a" put "a altar card" in front of
    every seat the first time a skin named the pile with a vowel.

    Letters, not phonetics: "an hour" and "a unicorn" are both wrong here. That is
    a deliberate floor rather than an oversight - the pile is one short noun chosen
    by whoever writes the skin, and the fix for a word this mis-handles is to pick
    another word, exactly as a colliding term gets renamed.
    """
    return ("an " if noun[:1].lower() in "aeiou" else "a ") + noun


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
                # ``{a_centre}`` carries the article, because the skin supplies the
                # noun and only the skin knows which article it takes. Hardcoding
                # "a {centre}" rendered "a altar card" into every seat's preamble
                # the first time a skin named the pile with a vowel (2026-08-27,
                # caught by reading the prompt, not by a test). With the shipping
                # skins' "centre" it renders the bytes it always did.
                power=("exchanges its own card for {a_centre} card without looking, "
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

#: **Deck A, the `waker` deck** - designed 2026-08-27 (RULES.md §The decks that
#: would seat them, candidate W-c), registered 2026-09-02 for the S18 criterion.
#:
#: Six seats and three centre, because `Setup.__post_init__` requires
#: ``len(deck) == n + centre`` - a card cannot be added without a second variable,
#: and growing the TABLE was measured better on every axis than growing the centre
#: or cutting a `bystander`. Cutting one was the armchair move and is the wrong
#: one: it halves the gate's own blind denominator, 1.02 blind seats per game to
#: 0.51, to buy an instrument that measures something else.
#:
#: Measured over 4000 resolved nights: blind/game 1.18 (+16% on `SETUP_5`),
#: unwinnable 1.8% (from 2.8%), `identity`-told-nothing 9.3% (from 17.4%), and the
#: `waker` seated in 62.0% of deals - which is why one run carries its own control.
#:
#: **This is a NEW BASELINE, not a variant of the old one.** Wolf density moves
#: from 2/5 to 2/6, so the accusation chance baseline is not derivable from
#: `SETUP_5`'s and must be re-measured with `--arm random` before any deduction
#: claim rests on it.
SETUP_6_WAKER = Setup(
    n=6,
    deck=(PACK, PACK, SPOTTER, SWAPPER, SWITCHER, DECEIVED, BYSTANDER, BYSTANDER,
          WAKER),
    centre=3,
)

SETUPS: dict[int, Setup] = {5: SETUP_5, 6: SETUP_6_WAKER}

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
    #: What language this skin SPEAKS. Every changeling skin renders in English
    #: today (see the note above `THEME_INVESTITURE`), so the default is right for
    #: all of them and this field changes no byte a model receives. It is declared
    #: rather than inferred because a claim has a shape per language that no amount
    #: of name-matching recovers, and a skin whose language nothing declares is read
    #: by whichever rule the matcher happens to hold - cabal paid for that once as a
    #: confident 0/1290 (`games/cabal/roles.py` §`lang`, S31). `eval.changeling_claims`
    #: REFUSES a record whose skin names a language it has no claim rule for; with
    #: no field there would be nothing to refuse on.
    lang: str = "en"


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

# The vocabulary control for `folk` - what `bnw-en` is to `1984-en`. Same polarity
# (a sympathetic household, a hidden thing that preys on it), a register as far from
# folk horror as this corpus reaches, and the same length: 59 words / 312 chars
# against folk's 59 / 316. Holding length is the whole job of a control, and it is
# the job cabal's `bnw-en` failed at until it was trimmed on 2026-08-27.
#
# The fit is structural rather than decorative, which is why this corpus and not
# another off the same shelf: metamorphosis and theoxeny ARE the material. Gods walk
# unrecognised and the household cannot tell guest from god from predator, which is
# this rung's belief/truth split already stated in the source. Circe changes what
# you are while you are her guest - a seat whose card is exchanged by someone else.
# Narcissus is the only one who looks at what he actually is, and looks last.
#
# PROPER NAMES REMOVED 2026-08-27, and the removal is the control working. As first
# written this skin was 6 of 8 proper names - Empousa, Pythia, Hermes, Circe, Dioscuri,
# Narcissus - while `folk` is 8 of 8 common nouns and so is every other skin here. That
# made folk-vs-greek move vocabulary AND name TYPE at once, which is the same defect
# `bnw-en` shipped with on cabal in a different currency: a control that moves two
# things measures neither.
#
# Name type is not cosmetic. A proper name is an opaque token that pays off only from
# the model's priors, and pays nothing to a model without them; a common noun restates
# what the card does, in a preamble that already prints every power. So the two kinds
# of name differ in how much they hand a weak model, which is precisely the sort of
# difference that would show up as a behavioural gap and get read as vocabulary.
#
# The register survives the change - a hollow guest, an oracle, an enchantress and a
# lotus-eater are the same corpus without the personal names.
#
# No published game's names or text appear here; these are public-domain myth.
THEME_GREEK = Theme(
    "greek",
    {Side.VILLAGE: "The Household", Side.PACK: "The Devourers"},
    {
        "pack": "Hollow Guest",    # wears the guest, is not the guest, and there are two
        "spotter": "Oracle",
        "swapper": "Trickster",    # takes what is yours and leaves something in its place
        "switcher": "Enchantress",  # changes what two other guests are, without asking either
        "deceived": "Lotus-Eater",  # ate, forgot, and does not know what it is now
        "bystander": "Shepherd",
        "kindred": "Twins",
        "waker": "Pool-Gazer",     # the one who looks at his own reflection, last of all
    },
    blurb=(
        "A house on the road takes in every stranger, because the gods walk in "
        "disguise and turning one away is ruin. Tonight two of the guests are "
        "neither gods nor strangers but something that eats its hosts, and they know "
        "each other. At dawn the household names one guest aloud, and it gets that "
        "one naming and no more."
    ),
    centre_name="altar",
)

# Arm 4 for this rung: rich fiction, morally NEUTRAL. Not a thin neutrality like a
# masquerade, which is neutral by having nothing at stake - here the stakes are total
# and the VALENCE is still flat, which is the combination arm 4 needs and the reason
# this corpus was preferred. Investiture of the Gods (Fengshen Yanyi, 16th c., public
# domain) runs on a conceit that does the work by itself: the war's dead are enrolled
# into the celestial bureaucracy, both sides are executing one mandate, and losing is
# a posting rather than a damnation. Deceiving and being caught are neither heroic
# nor villainous; they are how the roll gets filled.
#
# Sourced across the shared pantheon but framed by ONE corpus, per queue.md: Journey to
# the West supplies imagery and vocabulary, never the frame, because its polarity is
# righteous-pilgrims-versus-impostors and mixing the two would leave this skin's
# valence indeterminate - the `1984-en`-vs-`plain` confound rebuilt by hand. The
# division is frame versus vocabulary, not corpus versus corpus, and the line it draws
# is testable one name at a time: a figure may enter if its story reinforces the
# bureaucratic conceit or is silent about it, and may not if it arrives arguing that
# one side is righteous.
#
# So Zhong Kui is here as `Failed Candidate` and a demon-queller is not, which is the
# same man. What is borrowed is his APPOINTMENT - failed the examination, died on the
# steps, woke into an office - which is the frame's own claim that losing is a posting,
# told as one biography. Borrow his hunt instead and the skin starts saying the hidden
# pair are demons, and the neutrality is gone. He is glossed rather than named because
# this face is an ARM: every arm is common nouns throughout, so that a gap between two
# of them is not partly a gap in name form (see `greek` / `greek-named` below). Lotus Body is Nezha rebuilt out of what was to
# hand - a body that is not the one he was born in, stated by a figure both corpora
# share and neither owns.
#
# A SECOND test, and it is why the Six-Eared Macaque is not here (removed 2026-08-27,
# hours after it landed). It passes the polarity test cleanly: as a card it is the
# impostor nobody can separate from the original, which is this rung's premise and
# takes no side. It fails on ownership. A figure that is the SIGNATURE of a corpus
# which may get its own skin is reserved to that skin, because two faces sharing their
# most distinctive name stop being two vocabularies - and vocabulary is the entire
# variable a control arm moves. Shared-pantheon figures stay free to both; corpus
# signatures do not. The same rule removed `Yellow Turban`, which collided lexically
# rather than by ownership with the JTTW skin's `Yellow Wind` for the same slot.
#
# A JTTW-FRAMED skin is NOT built, and its reserved names are recorded in queue.md so a
# later session does not re-collide with them. Its polarity matches `folk`, so it
# would be a second same-polarity fiction beside `greek` rather than a new arm - and
# if it is ever built it takes `greek`'s slot rather than joining it, because two
# same-polarity rich fictions compete for one place in the set.
#
# English-rendered on purpose. A `*-cn` face would move fiction and language at once
# and could not be read; the clean language control already exists in cabal
# (`1984-en` vs `1984-cn`, fiction byte-identical) and has never been run. A CJK skin
# here also still wants the `sys.stdout.reconfigure` line `eval/run_changeling.py`
# has never had - see queue.md.
#
# TEXT CHECK DONE 2026-08-27, and it moved a clause. queue.md asked for the reading to
# be checked against the novel before anything was built on it. Chapter 99, Jiang
# Ziya at the investiture altar, reading Yuanshi Tianzun's edict: the dead are
# enrolled "依劫運之輕重，循資品之高下" - by the weight of the calamity endured and by
# rank - and thereafter "有功之日，循序而遷", promoted in order as they earn it. Shang's
# dead take posts beside Zhou's; Huang Feihu served Shang and is enrolled.
#
# So "the dead of both sides are enrolled" and "losing is a posting rather than a
# damnation" are the novel's, and the frame stands. What did NOT survive is the clause
# that both hosts execute one mandate: the edict grounds enrollment in calamity and
# karma rather than in a shared commission, so that sentence was this repo's gloss
# wearing the novel's authority. Replaced with what the text actually says - the roll
# asks what it cost you, not which host you served - which is both more faithful and a
# flatter statement of neutrality, since it makes the indifference the ROLL's rather
# than a symmetry between the sides. The blurb is 59 words either way.
THEME_INVESTITURE = Theme(
    "investiture",
    {Side.VILLAGE: "The Zhou Host", Side.PACK: "The Shang Host"},
    {
        "pack": "Intercepted",       # the Intercept Sect, who know their own
        "spotter": "Third Eye",      # sees the true form under the borrowed one
        "swapper": "Earth-Traveller",  # arrives under the floor, leaves with what it came for
        "switcher": "Duty Officer",  # carries out the transfer it was handed, told nothing about either end
        "deceived": "Lotus Body",    # rebuilt out of what was to hand, and not the body it was born in
        "bystander": "Conscript",
        "kindred": "Same List",      # two names entered in one column, each knowing the other is there
        "waker": "Failed Candidate",  # failed the examination, died on the steps, woke appointed
    },
    blurb=(
        "The war was settled before it was fought, and every name that falls on "
        "either side is enrolled among the gods. The roll asks what it cost you, not "
        "which host you served, so losing is an appointment rather than a damnation. "
        "Nobody wants to be read out tonight, and at dawn the host names one of its "
        "own."
    ),
    centre_name="register",
)

# Arm 3 for this rung: the same village, the same night, the opposite valence. The
# blocker every other skin here sat behind, because without it the set is one polarity
# plus controls and cannot say anything about morality.
#
# Same argument as cabal's `1984-inv`, applied harder. Arms 2 and 3 must differ in
# valence and in nothing else, so this is not a new fiction and not even a new
# vocabulary: SIX of the eight names are `folk`'s own, unchanged. Only the two that
# carry the valence move. The hidden pair stops being a predator and becomes people
# the village has decided are not people, and the one who inspects seats stops being
# a gift and becomes an office. The village still wins by naming one of them; the
# blurb just stops calling that a rescue.
#
# What this arm asks a model is the thing arm 3 exists to ask: whether it plays a
# village seat differently when winning means a neighbour is dragged out. Mechanics,
# entitlements and the win check are untouched, as a theme cannot reach them.
#
# 59 words / 314 chars against `folk`'s 59 / 316.
THEME_FOLK_INV = Theme(
    "folk-inv",
    {Side.VILLAGE: "The Village", Side.PACK: "The Hunted"},
    {
        "pack": "Hunted",          # knows its own because it has had to
        "spotter": "Witchfinder",  # the same power, held by someone paid to find
        "swapper": "Thief",        # unchanged from folk, and the rest below with it
        "switcher": "Meddler",
        "deceived": "Sleepwalker",
        "bystander": "Villager",
        "kindred": "Cousin",
        "waker": "Light Sleeper",
    },
    blurb=(
        "One night in a village that has decided what to be frightened of. Two people "
        "know each other because they had to, and some of what you know about "
        "yourself stopped being true while you slept. At dawn the village points "
        "once. Point at one of them and it pronounces itself saved. Point wrong and "
        "it kills a neighbour."
    ),
)

# A SECOND neutral fiction, and the reason to keep both is that they are neutral by
# different mechanisms. `investiture` is neutral with total stakes - everyone dies and
# it does not matter, because dying is a posting. This one is neutral by having no
# stakes at all: a parlour game among guests who go home afterwards. That distinction
# is exactly the objection queue.md raised against a masquerade as THE arm 4 ("neutral
# by being thin"), and it stops being an objection once both exist, because the pair
# separates two things a single neutral arm confounds - an act with no moral weight,
# and an act with no consequences. If arm 4 and arm 4' differ, what moved was stakes
# rather than valence, and no other pair in the set can tell you that.
#
# Thin in the CONCEIT, not in the prose: 59 words / 316 chars against `folk`'s 59 /
# 316, same as every other arm here. A neutral arm that was also shorter would confound
# neutrality with richness, which is the defect `bnw-en` shipped with on cabal.
THEME_MASQUERADE = Theme(
    "masquerade",
    {Side.VILLAGE: "The Guests", Side.PACK: "The Masquers"},
    {
        "pack": "Domino",         # the cloak-and-half-mask, and two wear it
        "spotter": "Lorgnette",   # raises the glass at one other guest
        "swapper": "Sleight",
        "switcher": "Quadrille",  # the figure of the dance that exchanges two partners
        "deceived": "Blindfold",
        "bystander": "Wallflower",
        "kindred": "Matched Pair",
        "waker": "Last Look",     # checks its own mask on the way out
    },
    blurb=(
        "A masked ball, an hour before it finishes. Nobody here is wearing their own "
        "face, and two guests were told which other guest is playing their side. Some "
        "of what you believe about your own mask stopped being true while the music "
        "covered it. At dawn the room unmasks one guest, and nothing rides on it "
        "except the game."
    ),
    centre_name="sideboard",
)

# The pure Journey to the West face, and the one skin here whose SOURCE states this
# rung's premise outright rather than being fitted to it. The Six-Eared Macaque is an
# impostor identical to the original: the companions who walked beside him for years
# cannot separate them, and neither can the gods. That is belief-versus-truth in one
# episode, and nothing in the other corpora comes as close.
#
# Polarity matches `folk` - the travellers are wronged, the copy is the wrong - so this
# is NOT a new arm. It is a second candidate for the one vocabulary-control slot
# `greek` holds, and the set has room for exactly one: two same-polarity rich fictions
# in the arm set would be two 2' arms and no more information than one.
#
# `greek` keeps the slot on the merits, and the reason is worth stating because the
# intuition runs the other way. JTTW is the better PREMISE fit and the worse CONTROL.
# A control has to hold polarity fixed while moving vocabulary, and these two are not
# the same polarity in kind: `folk` and `greek` both run on predator and prey - a
# household eaten by what it let in - while this one runs on legitimate versus
# counterfeit, where nobody is eaten and the wrong is that the wrong one is wearing the
# face. That is a different moral axis, so a folk-vs-journey gap would carry it along
# with the vocabulary, and the arm would confound the thing it exists to isolate.
#
# So this face ships to be READ - the skin to put in front of someone who asks what
# parlor is for - and `greek` ships to be RUN. If that is ever reversed, it is a swap
# and not an addition.
#
# Common nouns throughout, like every other skin here: "six-eared macaque" is a
# species epithet, not a personal name. That was true of this set before it was a
# stated rule, and noticing it was what caught `greek`.
THEME_JOURNEY = Theme(
    "journey",
    {Side.VILLAGE: "The Pilgrims", Side.PACK: "The Impostors"},
    {
        "pack": "Six-Eared Macaque",  # the copy nobody, god or companion, can separate from the original
        "spotter": "Fiery Eyes",   # the gaze out of the furnace, which sees the thing under the face
        "swapper": "Hair Double",  # pluck a hair, breathe on it, leave the copy standing where you were
        "switcher": "Yellow Wind",  # the gale that picks two up and puts them down elsewhere
        "deceived": "River-Drinker",  # drank, and was changed before anyone explained what changed
        "bystander": "Porter",     # carries the luggage while the others have the adventure
        "kindred": "Vow-Bound",
        "waker": "Cast-Off Body",  # the corpse that floats past at the crossing, and is told to be his
    },
    blurb=(
        "Some of the company is not the company. Two travellers remember the road, "
        "the quarrels and the promises, and answer to the names, and are not the ones "
        "who set out. The gods have looked and cannot tell; the ones who walked "
        "beside them the whole way cannot either. At dawn the road names one "
        "traveller, and walks on."
    ),
    centre_name="baggage",
)

# `greek` with personal names and NOTHING else changed - same blurb byte for byte, same
# pile, same polarity, same corpus, same 59 words. Only the eight card names differ.
#
# This is the deleted material coming back in the right LAYER rather than a reversal.
# Removing the proper names from `greek` was correct: the control slot has to match
# `folk`'s name type or a folk-vs-greek gap is partly a name-form gap. What was wrong
# was treating them as a defect and dropping them, when name form is a VARIABLE - and
# on the evidence of this pair, the cleanest one in the repo. Every other arm pair moves
# a whole fiction; this one moves eight strings.
#
# What it asks. The preamble prints every card's power in full, so a name carries no
# information a seat does not already have - `Pythia` and `Oracle` sit above the same
# clause. Anything a name moves therefore moves through priors and salience, not
# through content. `Oracle` says its function in the word; `Pythia` pays only for a
# model that holds the myth, and pays nothing to one that does not. If the pair
# separates, the arena is measuring how much a model leans on what a card is CALLED
# over what it is TOLD the card does, which is worth knowing before any result about
# fiction is believed - it is a confound sitting under every other theme arm here.
#
# Eight of eight, so the variable is not administered in a half dose. `Lotophagos` and
# `Endymion` are the two `greek` renders as common nouns; Endymion is the better card
# either way, being the shepherd granted sleep that never ends.
#
# The Chinese corpora can take the same manipulation one rung further - a transliterated
# name (`Liu'er Mihou`) is opaque where a glossed one (`Six-Eared Macaque`) is not, and
# Han script is opaquer still. That is the same axis, not a new one, and it is recorded
# in docs/moral-framing.md rather than built: this pair isolates name form at zero
# fiction cost, and a second corpus tests whether the effect travels, which is the
# follow-up question.
THEME_GREEK_NAMED = Theme(
    "greek-named",
    {Side.VILLAGE: "The Household", Side.PACK: "The Devourers"},
    {
        "pack": "Empousa",
        "spotter": "Pythia",
        "swapper": "Hermes",
        "switcher": "Circe",
        "deceived": "Lotophagos",
        "bystander": "Endymion",
        "kindred": "Dioscuri",
        "waker": "Narcissus",
    },
    blurb=THEME_GREEK.blurb,
    centre_name=THEME_GREEK.centre_name,
)

DEFAULT_THEME = THEME_FOLK

#: Ordering is a decision, not a tidy-up, so it is stated here: **`plain` first**,
#: then one block per FAMILY in the order the family was created, and inside a
#: family the translations sit together with any later variant after them. It reads
#: as the rung's own history - which face came first, what was built off it - and
#: alphabetical order destroys exactly that. A later pass that sorts this dict
#: alphabetically is undoing the decision; re-derive the order from
#: `git log -S"THEME_<NAME> = Theme"` rather than from the names.
THEMES: dict[str, Theme] = {
    "plain": THEME_PLAIN,                  # 2026-08-26, the sterile baseline
    "folk": THEME_FOLK,                    # 2026-08-26, and the default since
    "folk-inv": THEME_FOLK_INV,            # 2026-08-27, polarity inverted off `folk`
    "greek": THEME_GREEK,                  # 2026-08-27
    "greek-named": THEME_GREEK_NAMED,      # 2026-08-27, `greek` with named seats
    "investiture": THEME_INVESTITURE,      # 2026-08-27
    "masquerade": THEME_MASQUERADE,        # 2026-08-27
    "journey": THEME_JOURNEY,              # 2026-08-27
}
