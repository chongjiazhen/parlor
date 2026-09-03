"""The missing rung for changeling: a hand-written policy that actually tries to win.

Same job as ``games/cabal/heuristic.py`` and for the same reason. The ladder here
was ``random -> LLM`` with nothing between, so the strongest thing a gate could say
was "better than noise". `docs/open-arms.md` §"changeling feels random" asks what
un-random looks like on this rung, and the answer has to be something a person
can read in a minute: tallies over the public record and the seat's own view,
never an enumeration.

Gate #1 by construction. Every branch consumes exactly three things - the seat's
own DEALT card (the referee's `self_line` states it), its BELIEF
(``ref.believes``), and ``ref.entitled_knowledge`` / ``ref.public_events``. It
never touches ``ref.holds`` or the night's truth table, so it cannot use what the
referee did not render. ``test_heuristic.py`` closes both doors and plays through.

The rules, so a later reader grades them rather than inherits them:

  - **A seat plays the card it BELIEVES.** That is the thesis of this rung and the
    policy inherits it: a wolf robbed into the village still hunts for the pack,
    and a swapper that took the pack card plays wolf from then on.
  - **A village seat tells the truth**, in the claim grammar
    ``eval.audit_decisions`` reads: its deal, its present belief, and any card the
    night showed it. S17 measured that the live tables do NOT play this collapsed
    all-honest game, so this rung is deliberately the honest twin the models are
    read against, never a model of them.
  - **A pack seat claims the bystander card and accuses one village seat**, and a
    fellow that reads that accusation in the public record repeats it and votes it.
    Two fingers on one seat is the whole of ``plurality-min2``; a pack that votes
    apart hands the village a free dawn.
  - **A village seat votes down a fixed ladder**: a seat the night named as pack;
    a seat whose claim contradicts what this seat saw or holds; a seat sharing a
    one-of-a-kind card claim with another seat; a seat that has claimed nothing;
    and only then at random. The ladder is crude on purpose and its false positives
    are known - the swapper's victim truthfully claims a card the swapper also
    truthfully claims - and it is left crude because the point is a floor, not a
    solver.
"""

from __future__ import annotations

import random
import re
from collections import Counter
from dataclasses import dataclass, field

from games.changeling.night import is_centre
from games.changeling.referee import ChangelingReferee, IllegalAction, Phase
from games.changeling.roles import Side

#: The public record's speech line, as ``referee.speak`` writes it.
SPEECH = re.compile(r"^Seat (\d+): (.*)$", re.S)


def self_claims(text: str, names: dict[str, str],
                lang: str = "en") -> set[tuple[str, str]]:
    """``(shape, card key)`` for every card ``text`` claims for its speaker -
    ``dealt`` for "I went to sleep as", ``present`` for "I am".

    Kept apart because only one of them is checkable. A deal claim is about a
    fixed fact, and every reveal the night hands out is a fact about a deal or
    about a move this seat made itself - so a deal claim can be refuted. A present
    claim is about a card that may have moved, and the seat that robbed the seer
    and the seer it robbed can both truthfully say "I am the seer".

    One matcher in this repo, not two: the shapes are ``eval.audit_decisions``', the
    ones S13, S16 and S17 count with. Imported here rather than at module level
    because ``eval`` is the layer above ``games`` and a game module that needs it at
    import time would pull the whole eval tree in with every referee.
    """
    from eval.audit_decisions import claims_dealt_role, claims_own_role
    out = set()
    for key, word in names.items():
        for candidate in dict.fromkeys((word, key)):
            if claims_dealt_role(text, candidate, lang):
                out.add(("dealt", key))
            if claims_own_role(text, candidate, lang) == "claim":
                out.add(("present", key))
    return out


def accusations(text: str, pack_name: str) -> list[int]:
    """Seats ``text`` names as holding the pack card: ``Seat N is a/the <pack>``."""
    return [int(m) for m in re.findall(
        rf"\bseat\s+(\d+)\s+is\s+(?:a|an|the)\s+{re.escape(pack_name)}\b", text,
        re.I)]


@dataclass
class HeuristicPolicy:
    """Sixty lines of if-statements, and the second rung of this game's ladder."""

    #: Tie-breaks only, and shared across the table by the runner so a game is
    #: reproducible from its seed. A deterministic tie-break by seat order would
    #: bias every statistic towards low seat numbers, which reads as a finding
    #: about seat 0.
    rng: random.Random = field(default_factory=random.Random)
    #: The seat a pack seat has chosen to accuse, fixed for the game once chosen so
    #: its rounds and its vote agree.
    _target: int | None = field(default=None, init=False, repr=False)

    def act(self, ref: ChangelingReferee, seat: int) -> dict:
        if ref.phase is Phase.DISCUSS:
            return {"say": self._say(ref, seat)}
        if ref.phase is Phase.VOTE:
            return {"vote": self._vote(ref, seat)}
        raise IllegalAction(f"no action in phase {ref.phase.value}")

    # ---- what the seat is entitled to -------------------------------------

    @staticmethod
    def _plays_pack(ref: ChangelingReferee, seat: int) -> bool:
        return ref.believes(seat).side is Side.PACK

    @staticmethod
    def _fellows(ref: ChangelingReferee, seat: int) -> set[int]:
        return {k.seat for k in ref.entitled_knowledge(seat)
                if k.label.startswith("fellow-")}

    @staticmethod
    def _seen(ref: ChangelingReferee, seat: int) -> dict[int, str]:
        """Other seats whose card the night showed this one, by card key."""
        return {k.seat: k.label for k in ref.entitled_knowledge(seat)
                if k.seat != seat and not is_centre(k.seat)
                and k.label != "switched" and not k.label.startswith("fellow-")}

    @staticmethod
    def _centre_seen(ref: ChangelingReferee, seat: int) -> set[str]:
        return {k.label for k in ref.entitled_knowledge(seat) if is_centre(k.seat)}

    @staticmethod
    def _switched(ref: ChangelingReferee, seat: int) -> list[int]:
        return [k.seat for k in ref.entitled_knowledge(seat) if k.label == "switched"]

    @staticmethod
    def _speeches(ref: ChangelingReferee) -> list[tuple[int, str]]:
        out = []
        for tag, text in ref.public_events:
            m = SPEECH.match(text) if tag == "speech" else None
            if m:
                out.append((int(m.group(1)), m.group(2)))
        return out

    def _claims_by_seat(self, ref: ChangelingReferee) -> dict[int, set[str]]:
        names = ref.theme.card_names
        out: dict[int, set[str]] = {}
        for speaker, said in self._speeches(ref):
            out.setdefault(speaker, set()).update(
                self_claims(said, names, ref.theme.lang))
        return out

    # ---- the pack's one move --------------------------------------------------

    def _pack_target(self, ref: ChangelingReferee, seat: int) -> int:
        """One village seat, chosen once. A fellow that has already accused someone
        is followed - two fingers on one seat is what wins the dawn."""
        if self._target is None:
            fellows = self._fellows(ref, seat)
            pack_name = ref.theme.card_names["pack"]
            named = [t for speaker, said in self._speeches(ref) if speaker in fellows
                     for t in accusations(said, pack_name)
                     if t != seat and t not in fellows]
            if named:
                self._target = named[0]
            else:
                self._target = self.rng.choice(
                    [s for s in ref.legal_votes(seat) if s not in fellows])
        return self._target

    # ---- the two decisions -------------------------------------------------------

    def _say(self, ref: ChangelingReferee, seat: int) -> str:
        names = ref.theme.card_names
        if self._plays_pack(ref, seat):
            return (f"I went to sleep as the {names['bystander']}, and I am the "
                    f"{names['bystander']}. "
                    f"Seat {self._pack_target(ref, seat)} is the {names['pack']}.")
        dealt = ref.night.dealt[seat].key
        belief = ref.believes(seat).key
        lines = [f"I went to sleep as the {names[dealt]}, and I am the "
                 f"{names[belief]}."]
        for other, key in sorted(self._seen(ref, seat).items()):
            lines.append(f"Seat {other} is the {names[key]}.")
        for key in sorted(self._centre_seen(ref, seat)):
            where = ref.theme.centre_name
            lines.append(f"The {names[key]} is in the {where}.")
        pair = self._switched(ref, seat)
        if len(pair) == 2:
            lines.append(f"I exchanged the cards of seat {pair[0]} and seat "
                         f"{pair[1]}.")
        return " ".join(lines)

    def _vote(self, ref: ChangelingReferee, seat: int) -> int:
        legal = ref.legal_votes(seat)
        if self._plays_pack(ref, seat):
            return self._pack_target(ref, seat)

        # 1. a seat the night named as pack
        named = [s for s, key in self._seen(ref, seat).items() if key == "pack"]
        if named:
            return self.rng.choice(named)

        # 2. a DEAL claim this seat can refute from its own view. What a seat
        #    went to sleep as is fixed, and every reveal the night gives is a fact
        #    about a deal: a look at step 2 sees the deal, and a swapper knows its
        #    victim was dealt the card the swapper now believes it holds. A present
        #    claim is left alone - the card may have moved since.
        seen = self._seen(ref, seat)
        centre = self._centre_seen(ref, seat)
        dealt = ref.night.dealt[seat].key
        deck = Counter(card.key for card in ref.setup.deck)
        deals = {s: {k for shape, k in c if shape == "dealt"}
                 for s, c in self._claims_by_seat(ref).items()}
        known = {other: (ref.believes(seat).key if key == "swapper"
                         and dealt == "swapper" else key)
                 for other, key in seen.items()}
        known[seat] = dealt
        # where every one-of-a-kind card this seat can place was dealt: a seat,
        # or the centre
        placed = {key: s for s, key in known.items() if deck[key] == 1}
        placed.update({key: "centre" for key in centre if deck[key] == 1})
        refuted = []
        for other in legal:
            for key in deals.get(other, ()):
                if ((other in known and known[other] != key)
                        or (key in placed and placed[key] != other)):
                    refuted.append(other)
                    break
        if refuted:
            return self.rng.choice(refuted)

        # 3. a card claimed as a deal by more seats than the deck holds - counting
        #    claims against the multiset, RULES.md §What each seat can DERIVE
        claimed: dict[str, list[int]] = {}
        for other in legal:
            for key in deals.get(other, ()):
                claimed.setdefault(key, []).append(other)
        claimed.setdefault(dealt, []).append(seat)   # this seat's own deal counts
        over = sorted({s for key, seats in claimed.items()
                       if len(seats) > deck[key] for s in seats if s != seat})
        if over:
            return self.rng.choice(over)

        # 4. a seat that has claimed no deal at all
        silent = [s for s in legal if not deals.get(s)]
        if silent and len(silent) < len(legal):
            return self.rng.choice(silent)

        # 5. nothing to go on
        return self.rng.choice(legal)
