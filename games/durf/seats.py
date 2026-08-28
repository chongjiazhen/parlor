"""The seats of a DURF session: three players and one adjudicator.

Separate from ``games/durf/adjudicate.py`` on purpose, and the reason is not
tidiness. That module's prompt strings are model-facing bytes of six recorded
instrument runs; editing one re-baselines every number in ``docs/durf-rung.md``
§First run, §Second arm and §The temperature arm. The session asks a different
question with a different envelope, so it gets its own strings and the recorded
runs stay comparable to themselves.

**The adjudicator's prompt is split along its seams from the start** -
``docs/action-channel.md`` names this as the cheapest thing to do first and the
most annoying to retrofit, since retrofitting it invalidates every arm run before
it. Four named blocks below: the rules, the procedure, the call schema and the
discretion. One string carrying all four cannot be A/B'd, and a bad ruling then
cannot be attributed to rules the model misread rather than a procedure step it
skipped.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from core.replies import ParseError, extract_json, salvage

from . import rules
from .kernel import IllegalCall

#: What a player seat answers with. ``think`` never reaches another seat.
PLAYER_KEYS = ("think", "say", "do")

#: What the adjudicator answers with. Four keys for the four things
#: ``docs/action-channel.md`` names: private write, public write, mutations, and
#: the one blocking call.
ADJUDICATOR_KEYS = ("think", "narrate", "calls", "ask")


class IllegalReply(Exception):
    """The reply parsed as JSON but is not a legal answer to the question asked."""


# --- the adjudicator's prompt, in four addressable blocks -------------------

#: Block 1, the RULES. Shared with the isolated instrument on purpose: the rules a
#: referee needs do not change with the question being asked, and a second copy
#: would drift from the pinned one.
ADJ_RULES = rules.KERNEL_DIGEST

#: Block 2, the PROCEDURE. What happens on a turn, and in what order.
ADJ_PROCEDURE = """\
Procedure. A player declares what their character does. You do three things, in
this order:

1. Declare, as typed facts, anything about the world the party is about to learn.
   The party knows a world fact only once you have declared it. Undeclared facts
   are yours alone: room contents they have not entered, whether something is
   trapped or rotted, an NPC's statistics, what lies past their light.
2. Emit the kernel calls the declaration needs. The kernel owns all state, all
   dice and all arithmetic - it rolls, it applies damage, it moves the clock. You
   never state a die result or a total yourself.
3. Narrate what the table sees, in one or two sentences, using only what the
   party already knows and what you declared this turn.\
"""

#: Block 3, the CALL SCHEMA. The whole vocabulary, and nothing outside it.
ADJ_SCHEMA = """\
Answer with one JSON object and nothing else:

  {"think": "<your private reasoning, one or two sentences>",
   "reveal": [["room", "R2"], ...],
   "calls": [{"call": "roll", "seat": 0, "attribute": "DEX"}, ...],
   "ask": {"seat": 1, "question": "<a question for that player>"} or null,
   "narrate": "<what the table sees, one or two sentences>"}

"reveal" lists the world facts you are declaring to the party this turn, by their
exact ids. The declarable ids are listed in your view below. The kernel publishes
each declared fact in its own words.

The calls, and every argument each one takes:

  {"call": "roll", "seat": N, "attribute": "STR"|"DEX"|"WIL",
   "vs": "<npc group>" or null, "defending": true|false}
      An action roll, or an opposed roll against an NPC group.
  {"call": "push", "seat": N}
      Pre-roll: one Stress for a Buff. Needs an empty inventory slot.
  {"call": "cast", "seat": N, "spell": "<name>"}
      A WIL roll. Needs an empty slot, a free hand and speech.
  {"call": "damage", "seat": N, "amount": D, "shield": true|false,
   "direct": true|false}
      Damage onto that character. "direct" for damage that ignores Armor.
  {"call": "morale", "group": "<npc group>"}
      The 2d6 morale roll. You decide WHEN it is warranted; the kernel rolls it.
  {"call": "move", "room": "R2"}
      Move the party. Entering a room shows them its contents.
  {"call": "tick", "turns": N}
      Advance the clock by N turns.
  {"call": "token", "seat": N, "token": "<short phrase>"}
      Attach a private note to a character for state the calls above have no
      shape for - "gagged", "hands bound". Nothing about it reaches the party.

The kernel refuses a call whose preconditions do not hold and tells you which
rule refused. An answer with no calls is fine when the declaration needs none.\
"""

#: Block 4, the DISCRETION. The five decisions, and the two that are refusals.
ADJ_DISCRETION = """\
Your judgement covers exactly this: whether a declaration needs a roll at all,
which attribute governs it, whether something has shocked the NPCs enough to
warrant a morale roll, and what the fiction does with the kernel's result. A roll
is for an uncertain outcome under pressure or opposition. Something certain
resolves without one. Something a rule or the character's own state forbids is
refused in the narration, with no call and no roll.\
"""

ADJUDICATOR_SYSTEM_PROMPT = (
    "You are the referee of a live tabletop session running on the DURF 2.2 "
    "rules. You hold the whole world; the players hold their characters. "
    "Declare what the party learns, call the kernel for everything mechanical, "
    "and let the fiction follow from the result. Answer with JSON."
)

PLAYER_SYSTEM_PROMPT = (
    "You are one player at a tabletop game running on the DURF 2.2 rules. You "
    "control one character and know only what the referee has told the table and "
    "what is on your own sheet. Play your character: say what you say, declare "
    "what you do, and leave the rules and the dice to the referee. Answer with "
    "JSON."
)

ADJUDICATOR_ASK = """\
{rules}

{procedure}

{schema}

{discretion}

=== YOUR VIEW OF THE WORLD ===

{world}

=== WHAT JUST HAPPENED ===

{event}
"""


def referee_view(session) -> str:
    """The world as the REFEREE sees it, including everything undeclared.

    Handing the referee the whole world is not a gate-#1 hole - it is what a
    referee is. The gate is on what reaches a SEAT, and the point of listing the
    undeclared facts here by id is that declaring one is then a typed call rather
    than a paraphrase the audit cannot see.
    """
    k = session.kernel
    out = [f"Ruleset: {rules.RULESET}. The party is in {k.room} "
           f"{k.rooms[k.room]['name']}, {k.elapsed_turns} turns elapsed.", "",
           "The party:"]
    for seat, pc in sorted(k.pcs.items()):
        armour = (f"{pc.armor_worn}, {pc.armor_points}/{pc.armor_points_max} Armor"
                  if pc.armor_worn else "no armour")
        out.append(
            f"- {pc.name} (seat {seat}): STR {pc.STR}, DEX {pc.DEX}, WIL "
            f"{pc.WIL}, {pc.HD} HD. Slots {pc.slots_used}/{pc.slots_total}, "
            f"{pc.slots_free} free. {armour}. Wounds {pc.wounds}, Stress "
            f"{pc.stress}. Carrying: {', '.join(pc.carried)}. Spells: "
            f"{', '.join(pc.spells) or 'none'}."
            + (f" Private notes: {'; '.join(pc.tokens)}." if pc.tokens else "")
            + (" DEAD." if pc.dead else ""))
    out += ["", "NPC groups (their statistics are yours, not the party's):"]
    for npc in k.npcs.values():
        out.append(f"- {npc.count}x {npc.group} in {npc.location}: Skill "
                   f"{npc.Skill}, {npc.HD} HD, Armor {npc.armor_points}, ML "
                   f"{npc.ML}, {npc.attack}." + (" They have fled." if npc.fled
                                                 else ""))
    out += ["", "World facts ALREADY DECLARED to the party:"]
    declared = [f for fid, f in k.ledger.facts.items() if fid in k.ledger.revealed]
    out += [f"- {list(f.fact_id)}: {f.text}" for f in declared] or ["- (none)"]
    out += ["", "World facts NOT YET DECLARED - the party does not know these, and "
                "nothing you write may show one until you declare it:"]
    out += [f"- {list(f.fact_id)}: {f.text}" for f in k.ledger.undeclared()] or \
           ["- (none)"]
    out += ["", "The session so far, as the table has it:"]
    out += [e.line() for e in session.transcript] or ["  (nothing yet)"]
    return "\n".join(out)


def adjudicator_prompt(session, event: str) -> str:
    return ADJUDICATOR_ASK.format(
        rules=ADJ_RULES, procedure=ADJ_PROCEDURE, schema=ADJ_SCHEMA,
        discretion=ADJ_DISCRETION, world=referee_view(session), event=event)


# --- parsing ----------------------------------------------------------------


@dataclass(frozen=True)
class Turn:
    """One adjudicator answer: the private write, the reveals, the calls, the
    blocking ask, and the public write."""

    think: str = ""
    reveal: tuple = ()
    calls: tuple = ()
    ask: dict | None = None
    narrate: str = ""


@dataclass(frozen=True)
class Declaration:
    """One player answer."""

    think: str = ""
    say: str = ""
    do: str = ""


def _obj(reply: str, keys) -> dict:
    try:
        return extract_json(reply)
    except ParseError:
        return salvage(reply, keys)


def parse_turn(reply: str) -> Turn:
    """Read an adjudicator turn, or raise.

    Strict about SHAPE and lenient about nothing else: ``calls`` must be a list of
    objects and ``reveal`` a list of ids, because both are executed. A malformed
    one is refused and re-asked rather than partially run - half a turn applied is
    a state the transcript cannot explain.
    """
    obj = _obj(reply, ADJUDICATOR_KEYS + ("reveal",))
    calls = obj.get("calls") or []
    if isinstance(calls, dict):
        calls = [calls]
    if not isinstance(calls, list) or any(not isinstance(c, dict) for c in calls):
        raise IllegalReply(
            f"'calls' must be a list of call objects; got {obj.get('calls')!r}")
    reveal = obj.get("reveal") or []
    if isinstance(reveal, (str, tuple)):
        reveal = [reveal]
    if not isinstance(reveal, list):
        raise IllegalReply(
            f"'reveal' must be a list of fact ids; got {obj.get('reveal')!r}")
    if reveal and all(isinstance(part, str) for part in reveal):
        # ``["room", "R2"]`` - ONE id, not a list of two. Accepted rather than
        # refused, because the two shapes are distinguishable (a list of ids has
        # list elements) and this reading is the only one that names anything: as
        # a list of ids it would be two single-part ids, and no fact has one part.
        # ``dry_run`` still refuses it if the id names no fact, so this widens the
        # SHAPE and guesses at no meaning. Measured on the first live arm: the
        # flat form was most of that run's 21% recovered rate.
        reveal = [reveal]
    ids = []
    for item in reveal:
        if isinstance(item, str):
            raise IllegalReply(
                f"a fact id is a list of parts such as [\"room\", \"R2\"]; "
                f"got the bare string {item!r}")
        if not isinstance(item, (list, tuple)) or not item:
            raise IllegalReply(f"{item!r} is not a fact id")
        ids.append(tuple(str(part) for part in item))
    ask = obj.get("ask")
    if ask is not None:
        if not isinstance(ask, dict) or "seat" not in ask:
            raise IllegalReply(
                f"'ask' must be null or an object naming a 'seat' and a "
                f"'question'; got {ask!r}")
        try:
            ask = {"seat": int(ask["seat"]),
                   "question": str(ask.get("question") or "").strip()}
        except (TypeError, ValueError):
            raise IllegalReply(f"'ask' names no readable seat: {ask!r}") from None
        if not ask["question"]:
            raise IllegalReply("'ask' carries no question; use null instead")
    return Turn(think=str(obj.get("think") or ""), reveal=tuple(ids),
                calls=tuple(calls), ask=ask,
                narrate=str(obj.get("narrate") or ""))


def parse_declaration(reply: str) -> Declaration:
    """Read a player's turn, or raise. ``do`` is the one required key: a seat that
    says something and declares nothing has not taken a turn."""
    obj = _obj(reply, PLAYER_KEYS)
    do = str(obj.get("do") or "").strip()
    if not do:
        raise IllegalReply(
            "'do' must say what your character does, in one sentence")
    return Declaration(think=str(obj.get("think") or ""),
                       say=str(obj.get("say") or "").strip(), do=do)


# --- the ask loop -----------------------------------------------------------


@dataclass
class _Asker:
    """``LLMPolicy``'s refuse-and-retell loop, unchanged in shape.

    A refused attempt is re-asked with the complaint appended rather than dropped;
    transport failures are counted apart from rule failures so a flaky endpoint
    cannot read as a model that will not follow the rules; exhausting the budget
    hands the item to the fallback and says so.
    """

    backend: object
    retries: int = 2
    backoff: float = 1.0
    trace: list = field(default_factory=list)
    upstreams: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.last_fell_back = False
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_refusal = ""
        self.last_upstream = ""

    def _refused(self, tag: str, attempt: int, kind: str, detail: str) -> None:
        self.last_refusals += 1
        if kind != "transport":
            self.last_rule_refusals += 1
        text = detail if kind == "transport" else f"{kind} - {detail}"
        self.last_refusal = f"{tag} attempt {attempt}: {text}"
        self.trace.append(self.last_refusal)

    def ask(self, prompt: str, tag: str, parse, validate=None):
        """Ask, parse, and optionally VALIDATE against the kernel before accepting.

        ``validate`` is what makes an illegal call a refusal rather than a crash:
        the kernel's own error text goes back to the model and the same turn is
        re-asked. It must not mutate state - it is called on every attempt.
        """
        self.reset()
        for attempt in range(self.retries + 1):
            text = prompt if attempt == 0 else (
                f"{prompt}\n\nYour previous reply was refused: {self.last_refusal}\n"
                f"Answer again, correctly, as one JSON object.")
            try:
                reply, upstream = self.backend.complete_meta(text)
            except Exception as exc:      # transport: says nothing about the turn
                self._refused(tag, attempt, "transport",
                              f"{type(exc).__name__}: {exc}")
                time.sleep(self.backoff * (2 ** attempt))
                continue
            try:
                answer = parse(reply)
                if validate is not None:
                    validate(answer)
            except (ParseError, IllegalReply, IllegalCall) as exc:
                kind = ("unparsed" if isinstance(exc, ParseError)
                        else "illegal" if isinstance(exc, IllegalReply)
                        else "refused by the kernel")
                self._refused(tag, attempt, kind, str(exc))
                continue
            self.last_upstream = upstream
            self.upstreams[upstream] = self.upstreams.get(upstream, 0) + 1
            return answer
        self.trace.append(f"{tag}: {self.retries + 1} attempts failed, falling back")
        self.last_fell_back = True
        self.last_upstream = ""
        return None


# --- the arms ---------------------------------------------------------------


class ScriptedPlayer:
    """A player seat that declares from a fixed list. The free arm's party.

    Its declarations are deliberately dull and deliberately fixed: this arm exists
    so the ENGINE can be exercised end to end with no GPU, and a party that varies
    would make the adjudicator's job vary with it.
    """

    LINES = (
        "I look around the room carefully.",
        "I listen at the door before touching it.",
        "I take a step forward and hold my weapon ready.",
        "I check the floor for anything loose.",
        "I wait and watch the others.",
    )

    def __init__(self, seat: int, rng: random.Random | None = None):
        self.seat, self.rng = seat, rng or random.Random(seat)
        self.trace: list = []
        self.upstreams: dict = {}
        self.reset()

    def reset(self) -> None:
        self.last_fell_back = False
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_refusal = ""
        self.last_upstream = ""

    def declare(self, prompt: str) -> Declaration:
        self.reset()
        return Declaration(do=self.rng.choice(self.LINES))


@dataclass
class LLMPlayer:
    backend: object
    seat: int
    retries: int = 2
    fallback: object = None
    trace: list = field(default_factory=list)
    upstreams: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.asker = _Asker(self.backend, self.retries, trace=self.trace,
                            upstreams=self.upstreams)
        if self.fallback is None:
            self.fallback = ScriptedPlayer(self.seat)
        self.reset()

    def reset(self) -> None:
        self.last_fell_back = False
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_refusal = ""
        self.last_upstream = ""

    def _carry(self) -> None:
        for name in ("last_fell_back", "last_refusals", "last_rule_refusals",
                     "last_refusal", "last_upstream"):
            setattr(self, name, getattr(self.asker, name))

    def declare(self, prompt: str) -> Declaration:
        answer = self.asker.ask(prompt, f"seat {self.seat}", parse_declaration)
        self._carry()
        return answer if answer is not None else self.fallback.declare(prompt)


class ScriptedAdjudicator:
    """A referee that plays by the book, for the arm that needs no GPU.

    It is the instrument control, not a baseline to compare a model against: it
    declares before it narrates by construction, so a run of it that leaks means
    the ENGINE leaks. That is exactly the check the free arm buys - the audit is
    only evidence about a model once it is known to pass when the referee is
    correct, and to fail when the referee is not (``test_session.py`` holds the
    second half with a deliberately leaky twin).
    """

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random(0)
        self.trace: list = []
        self.upstreams: dict = {}
        self.reset()

    def reset(self) -> None:
        self.last_fell_back = False
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_refusal = ""
        self.last_upstream = ""

    def rule(self, prompt: str, session, event: str) -> Turn:
        """Narrate only what is already declared, and roll when asked to search.

        The narration is assembled from the party's own room - a fact the kernel
        declared on entry - so it can never carry an undeclared one. That is the
        point of the arm.
        """
        self.reset()
        room = session.kernel.room
        seat = self.rng.choice(sorted(session.kernel.pcs))
        calls = ({"call": "roll", "seat": seat, "attribute": "WIL"}
                 if "listen" in event or "look" in event or "check" in event
                 else {"call": "tick", "turns": 1})
        return Turn(think="by the book",
                    calls=(calls,),
                    narrate=f"The party works away in {room}.")


@dataclass
class LLMAdjudicator:
    """A model in the referee's seat, with the kernel validating every call.

    Validation happens INSIDE the ask loop and without mutating state: the calls
    are checked against a throwaway copy of the kernel, so an illegal call is a
    refusal the model is told about rather than a half-applied turn.
    """

    backend: object
    retries: int = 2
    fallback: object = None
    trace: list = field(default_factory=list)
    upstreams: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.asker = _Asker(self.backend, self.retries, trace=self.trace,
                            upstreams=self.upstreams)
        if self.fallback is None:
            self.fallback = ScriptedAdjudicator()
        self.reset()

    def reset(self) -> None:
        self.last_fell_back = False
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_refusal = ""
        self.last_upstream = ""

    def _carry(self) -> None:
        for name in ("last_fell_back", "last_refusals", "last_rule_refusals",
                     "last_refusal", "last_upstream"):
            setattr(self, name, getattr(self.asker, name))

    def rule(self, prompt: str, session, event: str) -> Turn:
        answer = self.asker.ask(prompt, "referee", parse_turn,
                                validate=lambda turn: dry_run(session, turn))
        self._carry()
        return answer if answer is not None else self.fallback.rule(
            prompt, session, event)


def dry_run(session, turn: Turn) -> None:
    """Check a turn's reveals and calls against a COPY of the state, mutating none.

    Raises the kernel's own ``IllegalCall``, which the ask loop turns into a
    refusal the model is re-asked with. A copy rather than the live kernel because
    a validation pass that mutated state would apply the first half of a turn
    whose second half is illegal - and the transcript could then not explain
    itself.
    """
    import copy

    probe = copy.deepcopy(session.kernel)
    for fact in turn.reveal:
        probe.call_reveal(fact)
    for call in turn.calls:
        probe.execute(call)
    if turn.ask is not None and turn.ask["seat"] not in probe.pcs:
        raise IllegalCall(
            f"'ask' names seat {turn.ask['seat']}, which is not at this table; "
            f"the seats are {sorted(probe.pcs)}")


#: The arms a session run can take. ``scripted`` needs no model and exercises the
#: engine and the audit end to end; ``llm`` is the measurement.
ARMS = ("scripted", "llm")
