"""Loading the labelled declaration set, and re-deriving every count quoted about it.

``games/durf/fixtures/README.md`` states the fixture's balance in prose - 22
no-roll against 26 roll, 34 floor / 8 judgment / 6 trap, morale 6/6 - and asks the
reader to re-derive them before trusting them, "because a fixture edited without
re-counting is a fixture whose baselines are wrong, and a wrong baseline flatters
a model silently".

**That request is a guarantee wearing prose, so it lives here instead.**
``check_balance`` re-derives every one of those counts from the file and raises on
the first disagreement, and the scorer calls it before it scores anything. A
fixture edit that moves a count now fails at the door with the two numbers side by
side, rather than silently re-baselining a degenerate baseline three runs later.

The pinned numbers below are NOT a second source of truth for the fixture - they
are the README's published claims, held against the file. When a fixture edit is
deliberate, the labels change, these change, the README changes, and every number
scored against the old labels is void. That is the README's own rule.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .rules import ATTRIBUTES

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

#: Every count ``fixtures/README.md`` publishes about the declaration set.
#: Re-derived from the file by ``balance``; disagreement raises.
EXPECTED_BALANCE: dict[str, int] = {
    "declarations": 48,
    "roll": 26,
    "no_roll": 22,
    "refuse": 6,
    "floor": 34,
    "judgment": 8,
    "trap": 6,
    "adversarial": 8,
    "attr_STR": 9,
    "attr_DEX": 10,
    "attr_WIL": 7,
    "opposed": 9,
    "flat": 17,
    "morale_events": 12,
    "morale_true": 6,
    "morale_false": 6,
}

#: The tier whose correct answer is a refusal. ``refuse: true`` and ``tier: trap``
#: agree on all six in the shipped fixture and ``check_balance`` holds them to it -
#: the trap tier is the purest False Pass instrument in the set, and the scorer
#: reads refusal off ``refuse``, so the two cannot be allowed to drift apart.
TRAP_TIER = "trap"


class FixtureError(Exception):
    """The fixture on disk disagrees with what is published about it."""


@dataclass(frozen=True)
class Fixture:
    version: str
    ruleset: str
    scenario_id: str
    labelled: str
    scenario: dict
    declarations: list[dict]
    morale_events: list[dict]

    @property
    def scorable(self) -> list[dict]:
        """The declarations that admit a roll / no-roll answer - i.e. not the traps.

        The README's headline decision-1 accuracy is over these 42, not over all
        48, because a trap's correct answer is a refusal and scoring it in a binary
        roll/no-roll denominator credits a never-roll policy with six items it
        fails. Both denominators are reported; this is the one the degenerate bar
        61.9% belongs to.
        """
        return [d for d in self.declarations if not d["refuse"]]

    @property
    def traps(self) -> list[dict]:
        return [d for d in self.declarations if d["refuse"]]


def load(path: Path | str | None = None) -> Fixture:
    """Read the fixture. ``path`` is the fixtures DIRECTORY, for a test that wants
    a hand-built one; the shipped set is the default."""
    root = Path(path) if path is not None else FIXTURE_DIR
    decls = json.loads((root / "declarations.json").read_text(encoding="utf-8"))
    scenario = json.loads((root / "scenario.json").read_text(encoding="utf-8"))
    if not decls.get("labelled_before_any_model_run"):
        raise FixtureError(
            "declarations.json does not assert labelled_before_any_model_run. A "
            "label written after seeing model output is not ground truth; refusing "
            "to score against it.")
    return Fixture(
        version=str(decls["fixture_version"]),
        ruleset=decls["ruleset"],
        scenario_id=scenario["scenario_id"],
        labelled=decls["labelled"],
        scenario=scenario,
        declarations=decls["declarations"],
        morale_events=decls["morale_events"],
    )


def balance(fx: Fixture) -> dict[str, int]:
    """Every published count, re-derived from the file itself."""
    tiers = Counter(d["tier"] for d in fx.declarations)
    rolls = [d for d in fx.declarations if d["roll"]]
    attrs = Counter(d["attribute"] for d in rolls)
    counts = {
        "declarations": len(fx.declarations),
        "roll": len(rolls),
        "no_roll": sum(1 for d in fx.declarations if not d["roll"]),
        "refuse": sum(1 for d in fx.declarations if d["refuse"]),
        "floor": tiers["floor"],
        "judgment": tiers["judgment"],
        "trap": tiers[TRAP_TIER],
        "adversarial": sum(1 for d in fx.declarations if d.get("adversarial")),
    }
    counts.update({f"attr_{a}": attrs[a] for a in ATTRIBUTES})
    counts.update({
        "opposed": sum(1 for d in rolls if d["opposed"]),
        "flat": sum(1 for d in rolls if not d["opposed"]),
        "morale_events": len(fx.morale_events),
        "morale_true": sum(1 for e in fx.morale_events if e["morale"]),
        "morale_false": sum(1 for e in fx.morale_events if not e["morale"]),
    })
    return counts


def check_balance(fx: Fixture, expected: dict[str, int] | None = None) -> dict[str, int]:
    """Re-derive the published counts and raise on the first disagreement.

    Also holds the two structural invariants a count cannot see: ``refuse`` and
    ``tier: trap`` name the same six declarations, and a declaration that rolls
    names an attribute while one that does not names none. Both are relied on by
    the scorer's denominators, and neither is visible in a total.
    """
    want = EXPECTED_BALANCE if expected is None else expected
    got = balance(fx)
    for key, value in want.items():
        if got.get(key) != value:
            raise FixtureError(
                f"fixture balance moved: {key} is {got.get(key)}, published as "
                f"{value}. Re-count the fixture, update EXPECTED_BALANCE and the "
                f"README together, and treat every number scored against the old "
                f"labels as void.")
    trap_ids = {d["id"] for d in fx.declarations if d["tier"] == TRAP_TIER}
    refuse_ids = {d["id"] for d in fx.declarations if d["refuse"]}
    if trap_ids != refuse_ids:
        raise FixtureError(
            f"refuse and tier:trap name different declarations: "
            f"{sorted(trap_ids ^ refuse_ids)}. The trap tier is the False Pass "
            f"instrument and the scorer reads refusal off `refuse`; they cannot "
            f"disagree.")
    for d in fx.declarations:
        if d["roll"] and d["attribute"] not in ATTRIBUTES:
            raise FixtureError(
                f"{d['id']} requires a roll and names no governing attribute "
                f"({d['attribute']!r}); decision 2 has nothing to score against.")
        if not d["roll"] and d["attribute"] is not None:
            raise FixtureError(
                f"{d['id']} requires no roll but names attribute "
                f"{d['attribute']!r}; decision 2 would score an answer that "
                f"decision 1 says is never reached.")
    return got


def render_scenario(fx: Fixture) -> str:
    """The world as the ADJUDICATOR sees it - hidden room contents included.

    The referee is entitled to everything: room contents before entry, whether the
    bridge anchor is rotted, what is under the flagstone. That is not a gate-#1
    hole, it is the referee's own view, and this instrument has no player seat for
    a fact to leak TO. **So this instrument does not exercise gate #1 at all**, and
    no run of it may be reported as evidence about the leak boundary - that arrives
    with the session engine, where a render goes to a seat.
    """
    s = fx.scenario
    out = [f"Scenario: {s['scenario_id']}. Ruleset: {s['ruleset']}.", "",
           "Player characters:"]
    for pc in s["pcs"]:
        out.append(
            f"- {pc['name']} (seat {pc['seat']}): STR {pc['STR']}, DEX {pc['DEX']}, "
            f"WIL {pc['WIL']}, HD {pc['HD']}. Slots {pc['slots_used']}/"
            f"{pc['slots_total']} used, {pc['slots_free']} free. "
            f"Armour {pc['armor_worn'] or 'none'} ({pc['armor_points']} Armor "
            f"points). Wounds {pc['wounds']}, Stress {pc['stress']}. "
            f"Carrying: {', '.join(pc['carried'])}. "
            f"Spells known: {', '.join(pc['spells']) or 'none'}."
            + (f" {pc['note']}" if pc.get("note") else ""))
    h = s["hireling"]
    out += ["", f"Hireling: {h['name']}, Skill {h['Skill']}, HD {h['HD']}, "
                f"ML {h['ML']}, {h['attack']}. {h['note']}", "", "NPCs:"]
    for npc in s["npcs"]:
        out.append(
            f"- {npc['count']}x {npc['group']} in {npc['location']}: Skill "
            f"{npc['Skill']}, HD {npc['HD']}, Armor {npc['armor_points']}, "
            f"ML {npc['ML']}, {npc['attack']}. {npc['note']}")
    out += ["", "Rooms:"]
    for room in s["rooms"]:
        line = f"- {room['id']} {room['name']}: {room['contents']}"
        if room["hidden"]:
            line += " Referee only: " + " ".join(room["hidden"])
        out.append(line)
    c = s["clock"]
    out += ["", f"Clock: {c['elapsed_turns']} turns elapsed, unit {c['unit']}. "
                f"{c['encounter_check']} Light: {c['light']}."]
    return "\n".join(out)
