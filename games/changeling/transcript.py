"""Render one changeling game as a markdown transcript a human can read.

Everything here comes off the two public channels the referee already wrote, in
the order it wrote them - ``public_events`` - plus the referee-side ``log`` for
the deal and the win reason. Nothing is re-derived from end state, because a
re-derivation is a second implementation of the rules that can disagree with the
first and no test would catch it.

The channel distinction survives the render:

  - ``("event", ...)`` is the referee's own words. Italic here, and the thing gate
    #1 audits - a role named in one of these would be a leak.
  - ``("speech:<seat>", ...)`` is what a player chose to say. Plain here. A lie in
    one is a move, not a leak.
  - A seat's private ``think`` is in neither channel: the driver hands ``speak()``
    only ``say``. ``_record_lines`` whitelists the two kinds above rather than
    rendering whatever it is handed, so nothing private can enter the record by
    someone appending a new tuple kind upstream.

Private reasoning DOES appear in this file, in its own referee-side section after
the assignment reveal, and that is deliberate. Gate #1 is about the bytes a seat's
MODEL receives; a post-game document read by a human is the one place all of it is
meant to be visible, and without it a transcript shows what happened and never why.
The public record above stays clean either way.

Two inputs, one output. A live ``ChangelingReferee`` (``from_referee``) or a
``GameRecord`` - live or loaded from a JSON file.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass

from games.changeling.roles import DEFAULT_THEME, THEMES


LEGACY_BANNER = (
    "> **Reconstructed, not recorded.** This record predates `GameRecord."
    "public_events`, so the interleaved timeline it would have been rendered from "
    "does not exist. What follows is assembled from the summary fields that were "
    "kept - the utterances in order, and the votes chunked back into rounds. The "
    "proposals themselves, and where each vote sat relative to the table talk, are "
    "not in this file and are not guessed at."
)


def _as_dict(record) -> dict:
    if is_dataclass(record):
        return asdict(record)
    return dict(record)


def _theme(name: str):
    """A record written before ``GameRecord.theme`` existed names no skin, and a run
    that passed no ``--theme`` used the default - so an unnamed skin resolves the
    same way the game itself resolves it, not to bare functional keys."""
    return THEMES.get(name, DEFAULT_THEME) if name else DEFAULT_THEME


def _record_lines(public_events) -> list[str]:
    """The public timeline, in order. Only the two public kinds render; anything
    else is dropped rather than guessed at - the private channel must not acquire a
    path to this file by someone appending a new tuple kind upstream."""
    out: list[str] = []
    for entry in public_events or []:
        kind, text = entry[0], entry[1]
        if kind == "event":
            out.append(f"- *{text}*")
        elif kind == "speech" or kind.startswith("speech:"):
            out.append(f"- {text}")
    return out


def _deal_lines(rec: dict) -> list[str]:
    n = len(rec.get("assignment") or {})
    out = ["> **Dealt cards** (what each seat was shown at night, may be stale):"]
    for seat in range(n):
        dealt = rec.get("dealt", {}).get(str(seat))
        if dealt:
            out.append(f"- Seat {seat}: {dealt}")
    return out


def _log_lines(rec: dict) -> list[str]:
    """Referee-side narrative (night actions, dawn truth, divergence)."""
    out = ["> **Referee log**"]
    for line in rec.get("log") or []:
        out.append(f"- {line}")
    return out


def render(record, meta: dict | None = None) -> str:
    """One game -> markdown. ``record`` is a ``GameRecord`` or its dict form;
    ``meta`` is run context (backend, model, rounds) shown in the header."""
    rec = _as_dict(record)
    meta = meta or {}
    theme = _theme(rec.get("theme") or meta.get("theme") or "")
    timeline = _record_lines(rec.get("public_events"))

    head = ["# Changeling - game transcript"]
    ctx = [f"theme `{theme.name}`"]
    for key, label in (("backend", "backend"), ("model", "model"),
                       ("rounds", "discussion round(s)"), ("seed", "seed")):
        if meta.get(key) not in (None, "", False):
            ctx.append(f"{meta[key]} {label}" if key == "rounds"
                       else f"{label} {meta[key]}")
    if rec.get("uat"):
        ctx.append("uat: true")
    head.append("  |  ".join(ctx))
    head.append("")

    if not timeline:
        head.append(LEGACY_BANNER)
        head.append("")

    head.append("## Public record")
    head.extend(timeline)
    head.append("")

    # Assignment reveal
    head.append("## The dawn truth")
    for seat in range(len(rec.get("assignment") or {})):
        held = rec.get("holds", {}).get(str(seat))
        if held:
            head.append(f"- Seat {seat}: {held}")
    head.append("")

    # Referee log
    head.extend(_log_lines(rec))
    head.append("")

    # Decision log (referee-side, with private reasoning)
    head.append("## Every decision (referee-side)")
    for d in rec.get("decision_log") or []:
        head.append(f"- Turn {d.get('turn', '?')}, Seat {d.get('seat', '?')}: "
                    f"{d.get('phase', '?')} -> {d.get('played', '?')}")
        think = d.get("think", "")
        if think:
            head.append(f"  > {think}")
    head.append("")

    return "\n".join(head)


def write(path: str, text: str) -> str:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def from_referee(ref, rec) -> str:
    """Build a transcript from a live referee and its record (before JSON round-trip)."""
    # Ensure public_events and log are up to date
    rec.public_events = list(ref.public_events)
    rec.log = list(ref.referee_log)
    return render(rec)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="render a changeling game JSON as a readable transcript")
    ap.add_argument("path", help="a run JSON file")
    ap.add_argument("--game", type=int, default=0, help="which game in the file")
    ap.add_argument("--out", help="write here instead of stdout")
    args = ap.parse_args()

    with open(args.path, encoding="utf-8") as fh:
        data = json.load(fh)

    # Support both a single record and a list of games
    if isinstance(data, list):
        rec = data[args.game]
    elif "games" in data:
        rec = data["games"][args.game]
    else:
        rec = data

    text = render(rec)
    if args.out:
        write(args.out, text)
    else:
        print(text)


if __name__ == "__main__":
    main()