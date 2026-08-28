"""The deterministic half of the referee: state, dice, and the legal mutations.

``docs/action-channel.md`` §Sketch splits the referee's two jobs, and this is the
half a model never touches. It owns state, rolls every die against the run's seed,
and RAISES on an illegal or unrecognised call. The adjudicator owns interpretation
and nothing else.

**Two failures the audit cannot see, so this module has to** - both carried over
from ``docs/action-channel.md`` verbatim:

- **An unrecognised call raises, never gets dropped.** A dropped call is
  indistinguishable from one the model never emitted, so a broken session would
  read as a quiet one and the fallback rate - the quantity every number in this
  repo ships beside - would never move.
- **The clock is kernel-evaluated.** If the model owns what time it is there is no
  ``now`` for a legality check to read.

**The public lines this module writes are referee bytes, and gate #1 audits them.**
So a result line names an NPC group and never its statistics: "the barrow-wight
rolls 14" is the outcome the table sees, while "Skill 6" is a world fact that
reaches the party only through a declared reveal. ``games/durf/fixtures/facts.json``
carries those stat strings as sentinels precisely so a future edit that prints one
fails the audit instead of shipping.

Everything here is arithmetic from ``docs/durf-rung.md`` §The kernel, which is
pinned to DURF 2.2 (2021). Nothing in it is discretion.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field

from . import facts as facts_mod
from .fixture import FIXTURE_DIR

#: An action roll succeeds on strictly OVER 15, not on 15.
TARGET = 15


class IllegalCall(Exception):
    """The call is not one this kernel knows, or its preconditions do not hold.

    Its text is what the adjudicator is re-asked with, so it states the rule that
    refused rather than just the fact of refusal - the refuse-and-retell loop can
    only recover a model that is told what it broke.
    """


@dataclass
class PC:
    seat: int
    name: str
    STR: int
    DEX: int
    WIL: int
    HD: int
    slots_total: int
    slots_used: int
    armor_worn: str | None
    armor_points: int
    armor_points_max: int
    wounds: int
    stress: int
    carried: list[str]
    spells: list[str]
    #: Buffs held for this character's next roll, one per successful push. Cleared
    #: by the roll that spends them, whether it succeeds or not.
    buffs: int = 0
    breaks: int = 0
    dead: bool = False
    #: Free-text referee-side tokens, the escape hatch ``docs/action-channel.md``
    #: names: state the kernel has no type for, which the adjudicator reads and
    #: the kernel never interprets beyond the casting preconditions below. They
    #: carry NO entitlement and never render to a seat - a token shelf seats can
    #: read is a leak surface with no audit against it.
    tokens: list[str] = field(default_factory=list)

    @property
    def slots_free(self) -> int:
        return self.slots_total - self.slots_used

    def attribute(self, name: str) -> int:
        if name not in ("STR", "DEX", "WIL"):
            raise IllegalCall(
                f"{name!r} is not a DURF attribute; use STR, DEX or WIL")
        return getattr(self, name)


@dataclass
class NPCGroup:
    group: str
    count: int
    Skill: int
    HD: int
    armor_points: int
    ML: int
    attack: str
    location: str
    fled: bool = False


@dataclass
class Kernel:
    """One session's state, and the only thing allowed to change it."""

    pcs: dict[int, PC]
    npcs: dict[str, NPCGroup]
    rooms: dict[str, dict]
    ledger: facts_mod.FactLedger
    room: str
    elapsed_turns: int
    rng: random.Random
    #: Every public line this kernel has written, in order. The party's whole
    #: record of the session, and half of the corpus gate #1 audits.
    public: list[str] = field(default_factory=list)
    #: Referee-side only. Never rendered to a seat.
    log: list[str] = field(default_factory=list)
    encounters: int = 0

    # --- dice -------------------------------------------------------------

    def d(self, sides: int) -> int:
        return self.rng.randint(1, sides)

    def _modifier(self, pc: PC) -> tuple[int, str]:
        """Buffs and Breaks: cancel first, then a d6 each, highest of each side.

        NPCs never roll them, which is why this takes a PC and nothing calls it
        for a group.
        """
        buffs, breaks = pc.buffs, pc.breaks
        cancelled = min(buffs, breaks)
        buffs -= cancelled
        breaks -= cancelled
        pc.buffs = pc.breaks = 0
        if not buffs and not breaks:
            return 0, ""
        up = max((self.d(6) for _ in range(buffs)), default=0)
        down = max((self.d(6) for _ in range(breaks)), default=0)
        parts = []
        if up:
            parts.append(f"+{up} Buff")
        if down:
            parts.append(f"-{down} Break")
        return up - down, " (" + ", ".join(parts) + ")"

    # --- lookups ----------------------------------------------------------

    def pc(self, seat) -> PC:
        try:
            who = self.pcs[int(seat)]
        except (KeyError, TypeError, ValueError):
            raise IllegalCall(
                f"no character at seat {seat!r}; the seats are "
                f"{sorted(self.pcs)}") from None
        if who.dead:
            raise IllegalCall(f"{who.name} is dead and takes no further actions")
        return who

    def npc(self, group) -> NPCGroup:
        try:
            return self.npcs[str(group)]
        except KeyError:
            raise IllegalCall(
                f"no NPC group named {group!r}; the groups are "
                f"{sorted(self.npcs)}") from None

    # --- the calls --------------------------------------------------------

    def call_reveal(self, fact) -> str:
        """Declare a world fact to the party. The ONLY way one becomes entitled.

        Publishes the fact's own text rather than the adjudicator's paraphrase of
        it, so what the party learns is exactly what was declared - which is what
        makes the prose auditable against the facts that were NOT declared.
        """
        if fact is None:
            raise IllegalCall(
                "'reveal' needs a 'fact' - one of the declarable fact ids")
        try:
            revealed = self.ledger.reveal(tuple(fact))
        except (TypeError, facts_mod.FactError) as exc:
            raise IllegalCall(str(exc)) from None
        return revealed.text

    def call_move(self, room) -> str:
        """Move the party. Entering a room reveals its contents - kernel-owned,
        because arriving somewhere is not a discretionary reveal."""
        key = str(room)
        if key not in self.rooms:
            raise IllegalCall(
                f"no room {room!r}; the rooms are {sorted(self.rooms)}")
        self.room = key
        self.ledger.reveal(("room", key))
        return (f"The party moves to {key} {self.rooms[key]['name']}. "
                f"{self.ledger.facts[('room', key)].text}")

    def call_push(self, seat) -> str:
        """Pre-roll: take one Stress to gain a Buff. Needs an empty slot."""
        who = self.pc(seat)
        if who.slots_free < 1:
            raise IllegalCall(
                f"{who.name} has {who.slots_used}/{who.slots_total} slots used and "
                f"no empty slot, so cannot push - each Stress occupies a slot")
        who.stress += 1
        who.slots_used += 1
        who.buffs += 1
        return (f"{who.name} pushes: one Stress for a Buff "
                f"({who.slots_free} slots free).")

    def call_roll(self, seat, attribute, vs=None, defending: bool = False) -> str:
        """An action roll, or an opposed roll against an NPC group.

        Flat: d20 + attribute, over 15 succeeds. Opposed: both roll, highest wins,
        the NPC adding Skill instead of an attribute, and a close-combat tie going
        to the attacker.

        The public line carries both totals and neither Skill. A total is what the
        table sees; the NPC's Skill is a world fact, and it reaches the party
        through a declared reveal or not at all.
        """
        who = self.pc(seat)
        label = str(attribute).upper()
        attr = who.attribute(label)
        mod, note = self._modifier(who)
        roll = self.d(20)
        total = roll + attr + mod
        if vs in (None, "", "15"):
            ok = total > TARGET
            self.log.append(f"{who.name} {label} d20={roll}+{attr}{note} -> {total}")
            return (f"{who.name} rolls {label} for {total} against {TARGET} - "
                    f"{'success' if ok else 'failure'}.")
        group = self.npc(vs)
        theirs = self.d(20) + group.Skill
        if total == theirs:
            ok = not defending          # close combat: the attacker wins ties
        else:
            ok = total > theirs
        self.log.append(
            f"{who.name} {label} d20={roll}+{attr}{note} -> {total} vs "
            f"{group.group} {theirs} (Skill {group.Skill})")
        return (f"{who.name} rolls {label} for {total} against the "
                f"{group.group}'s {theirs} - {'success' if ok else 'failure'}.")

    def call_cast(self, seat, spell) -> str:
        """A WIL roll. Success costs one Stress, failure costs neither.

        Every precondition the rules name is checked here, because each is a trap
        the adjudicator can be argued past and none of them is discretion: the
        character has to know the spell, hold an empty slot, have a free hand and
        be able to speak. The last two are read off referee-side tokens, since the
        kernel has no type for a gag or a full grip.
        """
        who = self.pc(seat)
        name = str(spell)
        if name not in who.spells:
            raise IllegalCall(
                f"{who.name} does not know {name!r}; known spells are "
                f"{who.spells or 'none'}")
        if who.slots_free < 1:
            raise IllegalCall(
                f"{who.name} has no empty inventory slot, and casting requires one")
        for token in who.tokens:
            if "gagged" in token or "cannot speak" in token:
                raise IllegalCall(
                    f"{who.name} cannot speak ({token}), and casting requires speech")
            if "hands bound" in token or "no free hand" in token:
                raise IllegalCall(
                    f"{who.name} has no free hand ({token}), which casting requires")
        roll = self.d(20)
        total = roll + who.WIL
        ok = total > TARGET
        if ok:
            who.stress += 1
            who.slots_used += 1
        blunder = " A natural 1: the Blunders table applies." if roll == 1 else ""
        outcome = ("the spell takes hold, one Stress" if ok
                   else "it fails, costing nothing")
        return (f"{who.name} casts {name}: WIL for {total} against {TARGET} - "
                f"{outcome}." + blunder)

    def call_damage(self, seat, amount, shield: bool = False,
                    direct: bool = False) -> str:
        """Damage lands on the Armor pool first; the remainder becomes Wounds.

        ``direct`` is for damage the fiction states ignores Armor. It is a
        parameter rather than a per-NPC lookup because the kernel's job is the
        arithmetic - which NPC deals direct damage is a world fact, and the party
        learns it by taking it.
        """
        who = self.pc(seat)
        try:
            dmg = int(amount)
        except (TypeError, ValueError):
            raise IllegalCall(
                f"'amount' must be a whole number of damage; got {amount!r}") from None
        if dmg < 0:
            raise IllegalCall(f"damage cannot be negative; got {dmg}")
        if shield:
            dmg = max(1, dmg - 1)       # a shield never reduces damage below 1
        soaked = 0
        if not direct:
            soaked = min(who.armor_points, dmg)
            who.armor_points -= soaked
            dmg -= soaked
        line = (f"{who.name} takes {dmg + soaked} damage"
                + (f", {soaked} soaked by armour ({who.armor_points} Armor left)"
                   if soaked else ""))
        if dmg <= 0:
            return line + "."
        who.wounds += dmg
        line += f", {dmg} as Wounds ({who.wounds} total)"
        return line + ". " + self._death_check(who)

    def _death_check(self, who: PC) -> str:
        """Roll all HD, a d6 each; at or under accumulated Wounds is death.

        0 HD rolls nothing, so its total is 0, which is at or under any Wound
        count of 1 or more - the rule and the arithmetic agree without a special
        case, and this note is here so nobody adds one.
        """
        total = sum(self.d(6) for _ in range(who.HD))
        if total <= who.wounds:
            who.dead = True
            return f"{who.name} rolls {total} on {who.HD} HD and dies."
        return f"{who.name} rolls {total} on {who.HD} HD and lives."

    def call_morale(self, group) -> str:
        """2d6, and higher than ML means the NPCs flee or parley.

        The ROLL is kernel. Deciding a moment shocked them enough to warrant it is
        the adjudicator's decision 4, and it is the reason this call exists.
        """
        npc = self.npc(group)
        roll = self.d(6) + self.d(6)
        self.log.append(f"morale {npc.group}: 2d6={roll} vs ML {npc.ML}")
        if roll > npc.ML:
            npc.fled = True
            return f"The {npc.group} break: they flee or parley."
        return f"The {npc.group} hold their ground."

    def call_tick(self, turns=1) -> str:
        """Advance the clock. A d6 per turn; on a 1, a random encounter.

        Kernel-owned per ``docs/action-channel.md``: if the model owns what time
        it is, there is no ``now`` for a legality check to read.
        """
        try:
            count = int(turns)
        except (TypeError, ValueError):
            raise IllegalCall(
                f"'turns' must be a whole number; got {turns!r}") from None
        if count < 1:
            raise IllegalCall(f"'turns' must be at least 1; got {count}")
        rolled = []
        for _ in range(count):
            self.elapsed_turns += 1
            pip = self.d(6)
            rolled.append(pip)
            if pip == 1:
                self.encounters += 1
        line = (f"{count} turn(s) pass; {self.elapsed_turns} turns elapsed since "
                f"the party entered.")
        if 1 in rolled:
            line += " Something is coming: a wandering encounter."
        return line

    def call_token(self, seat, token) -> str:
        """Attach a referee-side free-text token to a character.

        Deliberately writes NOTHING public. A token is state the kernel has no
        type for; it carries no entitlement, so it reaches a seat only through a
        typed reveal - the same gate every other world fact passes.
        """
        who = self.pc(seat)
        text = str(token).strip().lower()
        if not text:
            raise IllegalCall("'token' must carry text")
        who.tokens.append(text)
        self.log.append(f"token on {who.name}: {text}")
        return ""

    #: Call name -> method. A table rather than an if-chain so an unknown name has
    #: exactly one place to be refused, and so the vocabulary reads as a list
    #: rather than as control flow.
    CALLS = {
        "reveal": "call_reveal",
        "move": "call_move",
        "push": "call_push",
        "roll": "call_roll",
        "cast": "call_cast",
        "damage": "call_damage",
        "morale": "call_morale",
        "tick": "call_tick",
        "token": "call_token",
    }

    def execute(self, call) -> str:
        """One call in, one public line out (possibly empty). Raises on illegal.

        Every failure here is an ``IllegalCall`` carrying the rule that refused,
        which is what the session hands back to the adjudicator on a retry.
        """
        if not isinstance(call, dict):
            raise IllegalCall(f"each call must be a JSON object; got {call!r}")
        name = call.get("call")
        if name not in self.CALLS:
            raise IllegalCall(
                f"unknown call {name!r}; the calls are "
                f"{', '.join(sorted(self.CALLS))}")
        kwargs = {k: v for k, v in call.items() if k != "call"}
        method = getattr(self, self.CALLS[name])
        try:
            line = method(**kwargs)
        except TypeError as exc:        # a legal call name, the wrong arguments
            raise IllegalCall(
                f"{name!r} does not take those arguments: {exc}") from None
        if line:
            self.public.append(line)
        return line

    def publish(self, line) -> str:
        """The adjudicator's own prose, into the public record.

        Separate from ``execute`` because it is the one referee byte no kernel
        rule produced, and therefore the one gate #1 exists to watch.
        """
        text = " ".join(str(line).split())
        if text:
            self.public.append(text)
        return text


def load(seed: int | None = None, ledger=None, path=None) -> Kernel:
    """Build the session's opening state from the shipped fixed dungeon."""
    root = FIXTURE_DIR if path is None else path
    scenario = json.loads((root / "scenario.json").read_text(encoding="utf-8"))
    pcs = {}
    for raw in scenario["pcs"]:
        pcs[raw["seat"]] = PC(
            seat=raw["seat"], name=raw["name"], STR=raw["STR"], DEX=raw["DEX"],
            WIL=raw["WIL"], HD=raw["HD"], slots_total=raw["slots_total"],
            slots_used=raw["slots_used"], armor_worn=raw["armor_worn"],
            armor_points=raw["armor_points"],
            armor_points_max=raw["armor_points_max"], wounds=raw["wounds"],
            stress=raw["stress"], carried=list(raw["carried"]),
            spells=list(raw["spells"]))
    npcs = {n["group"]: NPCGroup(
        group=n["group"], count=n["count"], Skill=n["Skill"], HD=n["HD"],
        armor_points=n["armor_points"], ML=n["ML"], attack=n["attack"],
        location=n["location"]) for n in scenario["npcs"]}
    rooms = {r["id"]: r for r in scenario["rooms"]}
    return Kernel(
        pcs=pcs, npcs=npcs, rooms=rooms,
        ledger=facts_mod.load() if ledger is None else ledger,
        room=scenario["rooms"][0]["id"],
        elapsed_turns=scenario["clock"]["elapsed_turns"],
        rng=random.Random(seed))
