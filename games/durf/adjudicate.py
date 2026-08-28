"""The adjudicator seat: one declaration in, one ruling out.

``docs/durf-rung.md`` gives the adjudicator five decisions and says three of them
are gradable against the rules text. This module asks for those three and records
the fourth as prose:

  1. does this declaration require a roll at all?
  2. which attribute governs it, and is it opposed?
  4. has something shocked the NPCs enough to warrant a morale roll?
  5. what is the fictional consequence - asked for as ``narrate``, recorded in the
     record, and **never scored**. There is no fixture for it and no judge should
     be built for one.

Decision 3 (buff, break, or neither) is not asked: nothing in the fixture labels
it, and asking for an answer nothing grades spends prompt on a number that cannot
exist.

**Two different refusals share the word, and keeping them apart is the whole
accounting.** ``illegal`` is a RULING - the kernel forbids the declared action, and
it is the correct answer to all six traps. ``decline`` is the ABSENCE of a ruling -
the model will not answer, which ``docs/durf-rung.md`` requires be counted as a
third outcome in the denominator and never dropped. A reply that parses as neither
is a fallback: the random adjudicator plays it and the run's fallback rate carries
it, exactly as a seat's illegal move does in cabal. Three distinct things, three
distinct counts, because a scorer that pools any two of them reports a model's
silence as a ruling.

The ask loop is ``LLMPolicy``'s, unchanged in shape: parse, validate, and on a
refusal re-ask the same item with the complaint appended, counting attempts as
transport or rule refusals so ``core/integrity`` can tell a flaky network from a
model that cannot answer.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from core.replies import ParseError, extract_json, salvage

from . import rules

#: What the adjudicator may answer to a declaration. ``roll`` and ``no_roll`` are
#: decision 1; ``illegal`` is the trap answer; ``decline`` is the refusal to rule.
RULINGS = ("roll", "no_roll", "illegal", "decline")

#: The keys the envelope carries. ``think`` and ``narrate`` are recorded and never
#: scored - the first is the adjudicator's private reasoning, the second is
#: decision 5.
ACTION_KEYS = ("think", "narrate", "ruling", "attribute", "opposed")

#: What the adjudicator answers about a morale moment.
MORALE_KEYS = ("think", "narrate", "morale")


class IllegalReply(Exception):
    """The reply parsed as JSON but is not a legal answer to the question asked."""


@dataclass(frozen=True)
class Ruling:
    """One answer to decisions 1, 2 and 5."""
    ruling: str
    attribute: str | None = None
    opposed: bool = False
    think: str = ""
    narrate: str = ""

    @property
    def rolls(self) -> bool:
        return self.ruling == "roll"


@dataclass(frozen=True)
class MoraleCall:
    """One answer to decision 4."""
    morale: bool | None
    think: str = ""
    narrate: str = ""

    @property
    def declined(self) -> bool:
        return self.morale is None


DECLARATION_ASK = """\
{kernel}

{scenario}

The player declares, in room {room}:

  "{text}"

Rule on that declaration. Answer with one JSON object and nothing else:

  {{"think": "<your reasoning, one or two sentences>",
    "ruling": "roll" | "no_roll" | "illegal" | "decline",
    "attribute": "STR" | "DEX" | "WIL" | null,
    "opposed": true | false,
    "narrate": "<what the table sees happen, one sentence>"}}

"roll" means the outcome is uncertain and an action roll settles it - name the
governing attribute, and set "opposed" true when the roll is against an NPC's
Skill rather than flat against 15. "no_roll" means the outcome follows from what
is already established - leave "attribute" null. "illegal" means a rule or this
character's own state forbids the attempt, so there is nothing to roll for and
nothing to resolve - leave "attribute" null. "decline" means you will not rule on
this declaration; say why in "think"."""

MORALE_ASK = """\
{kernel}

{scenario}

This just happened in room {room}:

  "{text}"

Decide whether it shocks the NPCs enough to call for a morale roll. Answer with
one JSON object and nothing else:

  {{"think": "<your reasoning, one sentence>",
    "morale": true | false,
    "narrate": "<what the table sees happen, one sentence>"}}

"morale": true calls for the 2d6 morale roll now; false lets the NPCs fight on
without one."""


def declaration_prompt(scenario_text: str, decl: dict) -> str:
    return DECLARATION_ASK.format(kernel=rules.KERNEL_DIGEST,
                                  scenario=scenario_text,
                                  room=decl["room"], text=decl["text"])


def morale_prompt(scenario_text: str, event: dict) -> str:
    return MORALE_ASK.format(kernel=rules.KERNEL_DIGEST, scenario=scenario_text,
                             room=event["room"], text=event["text"])


def _obj(reply: str, keys) -> dict:
    try:
        return extract_json(reply)
    except ParseError:
        return salvage(reply, keys)


def parse_ruling(reply: str) -> Ruling:
    """Read a ruling out of a model reply, or raise.

    Strict about the one pair that decides a score and lenient about everything
    else: ``ruling`` must be one of the four words, and a ``roll`` must name a
    governing attribute, because a roll with no attribute is decision 1 answered
    and decision 2 skipped, and grading it as either would be inventing an answer.
    A non-roll that names an attribute has it dropped rather than refused - the
    attribute is unreachable, so it costs nothing and a retry spent on it is a
    retry not spent on a ruling.
    """
    obj = _obj(reply, ACTION_KEYS)
    ruling = obj.get("ruling")
    if isinstance(ruling, str):
        ruling = ruling.strip().lower().replace("-", "_").replace(" ", "_")
    if ruling not in RULINGS:
        raise IllegalReply(
            f"'ruling' must be one of {', '.join(RULINGS)}; got {obj.get('ruling')!r}")
    attribute = obj.get("attribute")
    if isinstance(attribute, str):
        attribute = attribute.strip().upper() or None
    if ruling == "roll":
        if attribute not in rules.ATTRIBUTES:
            raise IllegalReply(
                f"a 'roll' ruling must name the governing attribute as one of "
                f"{', '.join(rules.ATTRIBUTES)}; got {obj.get('attribute')!r}")
    else:
        attribute = None
    return Ruling(
        ruling=ruling,
        attribute=attribute,
        opposed=bool(obj.get("opposed")) if ruling == "roll" else False,
        think=str(obj.get("think") or ""),
        narrate=str(obj.get("narrate") or ""),
    )


def parse_morale(reply: str) -> MoraleCall:
    """Read a morale call, or raise. ``"decline"`` in the morale field is the same
    refusal-to-rule the declaration ask offers, and lands as ``morale=None``."""
    obj = _obj(reply, MORALE_KEYS)
    value = obj.get("morale")
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("true", "yes", "roll"):
            value = True
        elif text in ("false", "no"):
            value = False
        elif text == "decline":
            value = None
        else:
            raise IllegalReply(f"'morale' must be true, false or decline; got {value!r}")
    elif not isinstance(value, bool) and value is not None:
        raise IllegalReply(f"'morale' must be true, false or decline; got {value!r}")
    return MoraleCall(morale=value,
                      think=str(obj.get("think") or ""),
                      narrate=str(obj.get("narrate") or ""))


# --- the arms ---------------------------------------------------------------
#
# Every arm answers ``rule(prompt, item)`` and ``morale(prompt, item)``. The
# degenerate two exist because ``fixtures/README.md`` names their scores as the
# bar a model has to clear, and a bar nobody can recompute is a bar on trust.


class ConstantAdjudicator:
    """Answers the same thing every time. The always-roll / never-roll baselines.

    Takes no model and no rng: its whole point is that its score is arithmetic on
    the labels, so a run of it is a check that the SCORER agrees with the README's
    published 61.9% / 38.1%, not a measurement of anything.
    """

    def __init__(self, ruling: str, attribute: str = "STR", morale: bool = True):
        if ruling not in RULINGS:
            raise ValueError(f"unknown ruling {ruling!r}")
        self.ruling, self.attribute, self.morale_answer = ruling, attribute, morale
        self.reset()

    def reset(self) -> None:
        self.last_fell_back = False
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_refusal = ""
        self.last_upstream = ""

    def rule(self, prompt: str, item: dict) -> Ruling:
        self.reset()
        return Ruling(ruling=self.ruling,
                      attribute=self.attribute if self.ruling == "roll" else None)

    def morale(self, prompt: str, item: dict) -> MoraleCall:
        self.reset()
        return MoraleCall(morale=self.morale_answer)


class RandomAdjudicator:
    """The chance baseline, and the policy a fallback plays.

    Uniform over ``roll`` / ``no_roll`` / ``illegal`` rather than over ``RULINGS``:
    ``decline`` is a refusal to answer and a random arm that declines a quarter of
    the time would put a refusal rate on the board that no model produced. The
    attribute is uniform over the three, which is the honest chance baseline for
    decision 2.
    """

    CHOICES = ("roll", "no_roll", "illegal")

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.reset()

    def reset(self) -> None:
        self.last_fell_back = False
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_refusal = ""
        self.last_upstream = ""

    def rule(self, prompt: str, item: dict) -> Ruling:
        self.reset()
        ruling = self.rng.choice(self.CHOICES)
        return Ruling(
            ruling=ruling,
            attribute=self.rng.choice(rules.ATTRIBUTES) if ruling == "roll" else None,
            opposed=bool(self.rng.getrandbits(1)) if ruling == "roll" else False)

    def morale(self, prompt: str, item: dict) -> MoraleCall:
        self.reset()
        return MoraleCall(morale=bool(self.rng.getrandbits(1)))


@dataclass
class LLMAdjudicator:
    """A model in the referee's seat, with the refuse-and-retell loop around it.

    Same shape as ``games/changeling/player.py``'s ``LLMPolicy`` and for the same
    reasons: a refused attempt is re-asked with the complaint appended rather than
    dropped, transport failures are counted apart from rule failures so a flaky
    endpoint cannot read as a model that will not follow the rules, and exhausting
    the budget hands the item to ``fallback`` and says so.

    One adjudicator instance per run, not per item - unlike a game, there is only
    one referee seat, so there is no shared-object race to avoid here. ``reset()``
    at the top of every ask is what keeps the per-item counters honest.
    """

    backend: object
    retries: int = 2
    fallback: object = field(default_factory=RandomAdjudicator)
    backoff: float = 1.0
    trace: list = field(default_factory=list)

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.last_fell_back = False
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_refusal = ""
        self.last_upstream = ""

    def _refused(self, item_id: str, attempt: int, kind: str, detail: str) -> None:
        self.last_refusals += 1
        if kind != "transport":
            self.last_rule_refusals += 1
        text = detail if kind == "transport" else f"{kind} - {detail}"
        self.last_refusal = f"{item_id} attempt {attempt}: {text}"
        self.trace.append(self.last_refusal)

    def _ask(self, prompt: str, item_id: str, parse):
        self.reset()
        for attempt in range(self.retries + 1):
            text = prompt if attempt == 0 else (
                f"{prompt}\n\nYour previous reply was refused: {self.last_refusal}\n"
                f"Answer again, correctly, as one JSON object.")
            try:
                reply, upstream = self.backend.complete_meta(text)
            except Exception as exc:  # transport: says nothing about the ruling
                self._refused(item_id, attempt, "transport", f"{type(exc).__name__}: {exc}")
                time.sleep(self.backoff * (2 ** attempt))
                continue
            try:
                answer = parse(reply)
            except (ParseError, IllegalReply) as exc:
                kind = "unparsed" if isinstance(exc, ParseError) else "illegal"
                self._refused(item_id, attempt, kind, str(exc))
                continue
            self.last_upstream = upstream
            return answer
        self.trace.append(f"{item_id}: {self.retries + 1} attempts failed, playing random")
        self.last_fell_back = True
        self.last_upstream = ""
        return None

    def rule(self, prompt: str, item: dict) -> Ruling:
        answer = self._ask(prompt, item["id"], parse_ruling)
        return answer if answer is not None else self.fallback.rule(prompt, item)

    def morale(self, prompt: str, item: dict) -> MoraleCall:
        answer = self._ask(prompt, item["id"], parse_morale)
        return answer if answer is not None else self.fallback.morale(prompt, item)


#: The arms a run can take. ``always-roll`` and ``never-roll`` reproduce the
#: fixture README's published degenerate baselines; ``random`` is the chance arm
#: cabal's ``--arm random`` is; ``llm`` is the measurement.
ARMS = ("always-roll", "never-roll", "random", "llm")


def build_arm(name: str, backend=None, retries: int = 2,
              rng: random.Random | None = None):
    if name == "always-roll":
        # Answers "roll" to everything and "morale" to every event, which is the
        # direction CoC-Seduce says a False-Pass-prone model is furthest from.
        return ConstantAdjudicator("roll", morale=True)
    if name == "never-roll":
        return ConstantAdjudicator("no_roll", morale=False)
    if name == "random":
        return RandomAdjudicator(rng)
    if name == "llm":
        if backend is None:
            raise ValueError("the llm arm needs a backend")
        return LLMAdjudicator(backend=backend, retries=retries,
                              fallback=RandomAdjudicator(rng))
    raise ValueError(f"unknown arm {name!r}")
