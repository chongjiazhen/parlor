"""Bounded model choices for Belfry's setup-only referee discretion."""

from __future__ import annotations

import json
import random
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
    recovered: bool
    upstream: str | None


@dataclass
class ModelAdjudicator:
    backend: Backend
    rng: random.Random
    events: list[ChoiceEvent] = field(default_factory=list)

    def choose(self, key: str, options: list[str]) -> str:
        try:
            reply, upstream = self.backend.complete_meta(
                json.dumps({"choice_key": key, "options": options}))
            parsed = json.loads(_json_reply(reply))
            if (type(parsed) is not dict or set(parsed) != {"choice"}
                    or type(parsed["choice"]) is not str
                    or parsed["choice"] not in options):
                raise ValueError("reply did not select one offered option")
            selected, fallback = parsed["choice"], False
        except Exception:
            selected, upstream, fallback = self.rng.choice(options), None, True
        self.events.append(ChoiceEvent(
            key, tuple(options), selected, fallback, False, upstream))
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
