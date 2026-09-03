"""The seat that chooses a playbook, and the bytes it is sent.

**The ask is the budget.** ``docs/open-arms.md`` §Session-0: a full sheet per
playbook, times the pack, is a large payload paid by every seat at a phase where
it is not actionable - a seat choosing between playbooks needs to tell them
apart, not to fill one in. So the choose-phase ask carries a name and one line
each, plus what is already gone. The sheet reaches the seat that took it, at the
phase where it is actionable, and a run that sends every sheet is the measured
arm against that position.

``think`` is asked for and never leaves this module. It is the seat's own
reasoning, and the repo's standing rule is that a seat's private think reaches
neither public channel.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.replies import ParseError, extract_json, salvage

#: What a choosing seat answers with.
CHOICE_KEYS = ("think", "pick")


def render_choice_ask(seat: int, menu, taken=()) -> str:
    """The choose-phase context for one seat. Names and hooks, never a sheet."""
    lines = [
        "You are picking a character to play in a story with other players.",
        f"You are seat {seat}.",
        "",
        "Available:",
    ]
    gone = set(taken)
    for entry in menu:
        if entry["name"] in gone:
            continue
        hook = entry.get("hook", "")
        lines.append(f"  - {entry['name']}" + (f" - {hook}" if hook else ""))
    if gone:
        lines += ["", "Already taken by other seats (you cannot pick these):",
                  "  " + ", ".join(sorted(gone))]
    lines += [
        "",
        "Pick exactly one available name. Answer with JSON and nothing else:",
        '  {"think": "<your reasoning, seen by nobody>", "pick": "<name>"}',
    ]
    return "\n".join(lines)


@dataclass
class ChoosingSeat:
    """One model seat. Returns a name, or ``None`` when its budget runs out.

    ``None`` is not a pick and must not be treated as one: the caller plays the
    random policy and counts it, so the run's fallback rate carries the cost.
    """

    seat: int
    backend: object
    retries: int = 3

    def choose(self, menu, taken=()) -> str | None:
        ask = render_choice_ask(self.seat, menu, taken)
        for _ in range(max(1, self.retries)):
            reply = self.backend.complete(ask)
            try:
                action = extract_json(reply)
            except ParseError:
                try:
                    action = salvage(reply, CHOICE_KEYS)
                except ParseError:
                    continue
            pick = (action.get("pick") or "").strip()
            if pick:
                return pick
        return None
