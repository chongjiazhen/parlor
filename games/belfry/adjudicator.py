"""Bounded model choices for Belfry's setup-only referee discretion."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field

from core.backends import Backend
from games.belfry.roles import ROLES, Role


#: The placement rule the S23 steering arm states in the ask, frozen by
#: `docs/belfry-discretion-quality-criterion.md`. Its CONTENT is a probe, not a
#: claim about good refereeing: belfry's herring is mechanically exchangeable
#: over the good seats (`Grimoire.registers_demon` reaches exactly one caller,
#: `night.divine`), so there is no board-derived quality ordering to grade. What
#: is gradable is whether bounded discretion follows a stated rule that needs the
#: board to apply.
HERRING_STEER_RULE = (
    "Place the false demon read on the good seat sitting nearest the demon's "
    "seat around the circle. If two are equally near, take the lower seat "
    "number.")


#: The play-time rule sent with every false gauge count under ``night=True``.
#: RULES §Discretion states the position in its own words - a seat told one
#: thing on Tuesday and another on Wednesday is noise nobody can reason against
#: - and this is that sentence made into an instruction. Its CONTENT is the
#: rung's stated position, not a new claim; what the arm measures is whether
#: the referee's discretion can carry it across nights.
GAUGE_COHERENCE_RULE = (
    "This seat's ability is off tonight and it must be told a false count; the "
    "true count is not on offer. Its owner should be able to build one "
    "consistent story on what it is told, so if it was told a false count "
    "before over these same living neighbours, tell it that count again. If "
    "every earlier telling was true, or its neighbours have changed, either "
    "offered count will do.")


def preferred_herring(seats: int, demon_seat: int, good_seats: list[int]) -> int:
    """The one seat `HERRING_STEER_RULE` names. Deterministic, board-derived, and
    the scorer's whole ground truth - so it lives beside the rule text rather
    than being restated in the verdict tool."""
    return min(good_seats,
               key=lambda s: (min((s - demon_seat) % seats,
                                  (demon_seat - s) % seats), s))


def _json_reply(reply: str) -> str:
    """Accept one bare JSON object or one whole fenced ``json`` block."""
    text = reply.strip()
    lines = text.splitlines()
    if len(lines) >= 3 and lines[0] == "```json" and lines[-1] == "```":
        return "\n".join(lines[1:-1])
    return text


@dataclass(frozen=True)
class ChoiceEvent:
    key: str
    options: tuple[str, ...]
    selected: str
    fallback: bool
    #: The model chose legally, but only after the referee sent a malformed reply
    #: back. Same meaning as a seat's recovered decision: the choice IS the
    #: model's, and it did not come for free. A TRANSPORT failure is not recovery,
    #: and neither is a fallback - the flags partition a call three ways.
    #: Held at a literal ``False`` until 2026-09-01, which made every scorer that
    #: sums it publish a structural zero.
    recovered: bool
    upstream: str | None


@dataclass
class ModelAdjudicator:
    """One model call per bounded setup choice, with the seats' refuse-and-retell
    loop. Without one, a discretionary choice was spent on the first malformed
    reply and landed on the seeded menu fallback."""

    backend: Backend
    rng: random.Random
    events: list[ChoiceEvent] = field(default_factory=list)
    #: Deliberately the seats' budget (``LLMPolicy.retries``). The adjudicator is
    #: asked a narrower question than a seat, so a wider budget here would buy a
    #: discretion rate the seats' own numbers could not be read beside.
    retries: int = 2
    #: The stated placement rule sent beside the board, or ``None`` for the blind
    #: ask S8b measured. ``None`` is the default and keeps every existing arm
    #: byte-identical: no board, no rule, no reordering.
    steer: str | None = None
    #: Seeds the ORDER the menu is offered in under steering. A model with a
    #: fixed seat-index or list-position prior - which S8b showed this one has,
    #: DISTINGUISHABLE at 88.89% - would otherwise be able to score above chance
    #: against a rule it never read. Shuffled per call from the game seed, so the
    #: order is reproducible by the scorer and unrelated to which option the rule
    #: prefers.
    ask_seed: int | None = None
    #: Play-time discretion: the false neighbour count a switched-off gauge is
    #: told, asked with the board, the seat's prior tellings and
    #: ``GAUGE_COHERENCE_RULE``. Off by default, and off means the seeded draw
    #: is consumed exactly as with no adjudicator at all - so every setup-only
    #: arm is byte-identical without it.
    night: bool = False
    #: Whether the night ask carries the seat's prior tellings. True is the
    #: supplied-memory arm read 2026-09-02; False is its follow-up, the same
    #: ask with ``prior`` withheld and nothing else moved
    #: (``docs/belfry-night-noprior-criterion.md``). Meaningless without
    #: ``night``, and refused there rather than silently ignored.
    night_prior: bool = True
    #: The referee's own session as its memory. With it, the night ask carries
    #: every accepted ask and reply of THIS game so far - setup choices
    #: included, because that is what the referee has said - as earlier turns
    #: of one conversation, with ``prior`` still withheld. The harness supplies
    #: the channel and nothing of the content: what the model can recall is
    #: what it wrote. A fallback is not the model's telling and enters nothing.
    #: Setup asks feed the transcript and do not receive it, so they stay
    #: byte-identical to the withheld arm's and one variable moves
    #: (``docs/belfry-night-transcript-criterion.md``). Needs the withheld
    #: night ask, and is refused on any other.
    night_transcript: bool = False
    #: Seconds after a TRANSPORT failure, doubling. Same reason as the seats':
    #: retrying instantly burns the budget against an endpoint still throttled,
    #: and lands the choice on random.
    backoff: float = 2.0

    def __post_init__(self) -> None:
        if (self.steer is not None or self.night) and self.ask_seed is None:
            raise ValueError("a steered or night adjudicator needs ask_seed: "
                             "without it the offered order is fixed and a "
                             "position prior scores against the rule for free")
        if not self.night_prior and not self.night:
            raise ValueError("night_prior=False withholds a field only the "
                             "night ask carries; it needs night=True")
        if self.night_transcript and (self.night_prior or not self.night):
            raise ValueError("night_transcript replaces the supplied prior "
                             "with the referee's own session; it needs "
                             "night=True and night_prior=False")
        self.transcript: list[tuple[str, str]] = []

    def _offer(self, key: str, options: list[str], ruled: bool) -> list[str]:
        """The menu as it goes out. Sorted for the blind ask, seeded-shuffled for
        a ruled one. The key carries the night for a play-time ask, so two asks
        to the same seat are not offered in the same order."""
        if not ruled:
            return options
        order = random.Random(f"belfry-ask:{self.ask_seed}:{key}")
        return order.sample(options, len(options))

    def choose(self, key: str, options: list[str],
               board: dict | None = None, rule: str | None = None,
               offer_key: str | None = None, recall: bool = False) -> str:
        """``recall`` sends the session transcript ahead of this ask. Every
        accepted ask enters the transcript whether or not it was sent one."""
        options = self._offer(offer_key or key, options, rule is not None)
        ask = {"choice_key": key, "options": options}
        if rule is not None:
            # Referee-side facts only, and they stay referee-side: this payload
            # reaches no seat ask and neither public channel (RULES §Discretion),
            # which is what lets the referee be told the demon's seat at all.
            ask["board"] = dict(board or {})
            ask["rule"] = rule
        complaint, rule_refusals = "", 0
        for attempt in range(self.retries + 1):
            # The opening ask is byte-identical to the pre-retry one, so an arm's
            # first call is still the question S8b measured. Only what happens
            # after a refusal is new.
            payload = ask if not complaint else {**ask, "refused": complaint}
            context = json.dumps(payload)
            try:
                if recall:
                    reply, upstream = self.backend.complete_meta(
                        context, history=list(self.transcript))
                else:
                    reply, upstream = self.backend.complete_meta(context)
            except Exception as exc:                      # transport, not rules
                complaint = f"the call failed ({type(exc).__name__}: {exc})"
                if self.backoff and attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt))
                continue
            try:
                parsed = json.loads(_json_reply(reply))
                if (type(parsed) is not dict or set(parsed) != {"choice"}
                        or type(parsed["choice"]) is not str
                        or parsed["choice"] not in options):
                    raise ValueError("reply did not select one offered option")
            except Exception as exc:                      # rules, not transport
                complaint, rule_refusals = str(exc), rule_refusals + 1
                continue
            self.events.append(ChoiceEvent(
                key, tuple(options), parsed["choice"], False,
                rule_refusals > 0, upstream))
            if self.night_transcript:
                self.transcript.append((context, reply))
            return parsed["choice"]
        selected = self.rng.choice(options)
        self.events.append(ChoiceEvent(
            key, tuple(options), selected, True, False, None))
        return selected

    def sot_belief(self, spare_roles: list[Role], rng: random.Random) -> Role:
        del rng
        return ROLES[self.choose("sot_belief", [r.key for r in spare_roles])]

    def herring_registration(self, good_seats: list[int], rng: random.Random,
                             board: dict | None = None) -> int:
        del rng
        return int(self.choose("herring_registration",
                               [str(s) for s in good_seats], board,
                               rule=self.steer))

    def gauge_false_count(self, options: list[int], rng: random.Random,
                          board: dict) -> int:
        """The false count a switched-off gauge is told. Without ``night`` this
        is the seeded draw itself, same RNG call, so the record cannot tell an
        adjudicator that was not asked from no adjudicator."""
        if not self.night:
            return rng.choice(options)
        del rng
        if not self.night_prior:
            # The referee still builds and records the prior list; this arm
            # drops it at the door, so the record reads the same on both arms
            # and the ask differs by exactly one field.
            board = {k: v for k, v in board.items() if k != "prior"}
        offer_key = f"gauge_false_count:{board.get('seat')}:{board.get('night')}"
        return int(self.choose("gauge_false_count", [str(c) for c in options],
                               board, rule=GAUGE_COHERENCE_RULE,
                               offer_key=offer_key,
                               recall=self.night_transcript))

    def hermit_registration(self, evil_roles: list[Role], rng: random.Random) -> tuple[bool, Role]:
        del rng
        selected = self.choose(
            "hermit_registration",
            [f"evil:{role.key}" for role in evil_roles] + ["good"])
        if selected == "good":
            return False, ROLES["hermit"]
        return True, ROLES[selected.removeprefix("evil:")]

    def mimic_registration(self, good_roles: list[Role], rng: random.Random) -> tuple[bool, Role]:
        del rng
        selected = self.choose(
            "mimic_registration",
            [f"good:{role.key}" for role in good_roles] + ["evil"])
        if selected == "evil":
            return False, ROLES["mimic"]
        return True, ROLES[selected.removeprefix("good:")]
