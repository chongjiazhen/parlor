"""Bounded model choices for Belfry's setup-only referee discretion."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field

from core.backends import Backend
from games.belfry.roles import ROLES, Role


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
    #: Seconds after a TRANSPORT failure, doubling. Same reason as the seats':
    #: retrying instantly burns the budget against an endpoint still throttled,
    #: and lands the choice on random.
    backoff: float = 2.0

    def choose(self, key: str, options: list[str]) -> str:
        ask = {"choice_key": key, "options": options}
        complaint, rule_refusals = "", 0
        for attempt in range(self.retries + 1):
            # The opening ask is byte-identical to the pre-retry one, so an arm's
            # first call is still the question S8b measured. Only what happens
            # after a refusal is new.
            payload = ask if not complaint else {**ask, "refused": complaint}
            try:
                reply, upstream = self.backend.complete_meta(json.dumps(payload))
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
            return parsed["choice"]
        selected = self.rng.choice(options)
        self.events.append(ChoiceEvent(
            key, tuple(options), selected, True, False, None))
        return selected

    def sot_belief(self, spare_roles: list[Role], rng: random.Random) -> Role:
        del rng
        return ROLES[self.choose("sot_belief", [r.key for r in spare_roles])]

    def herring_registration(self, good_seats: list[int], rng: random.Random) -> int:
        del rng
        return int(self.choose("herring_registration", [str(s) for s in good_seats]))

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
