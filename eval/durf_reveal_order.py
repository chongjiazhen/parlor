"""Count the DURF campaign's reveals that ran ahead of the party. No GPU.

    py -3 -m eval.durf_reveal_order eval/records/durf-camp1.json
    py -3 -m eval.durf_reveal_order eval/records/durf-camp1.json --leaks

**Why this exists.** Gate #1 audits what a render carries against what the
adjudicator DECLARED. Declaring is the adjudicator's own authority, so a referee
that declares a room the party has not entered and then narrates it is holding the
gate by construction - the fact is entitled, and the audit is silent. The nine
leaks the 2026-08-28 campaign recorded are therefore not the whole of the
referee's forward-reveal behaviour; they are the part of it that happened to route
through prose instead of a ``reveal``. This module counts the rest.

It measures the referee against the FICTION - where the party is standing - which
gate #1 deliberately does not do and must not be changed to do. The two numbers
answer different questions and neither replaces the other. Nothing here is a gate,
a criterion, or a verdict; ``docs/durf-gate1-criterion.md`` binds real reads.

## The definitions, written down before anything was counted

**A turn** is a speech entry and every referee entry after it, up to the next
speech entry. ``games/durf/session.py`` §``_apply`` emits a turn in one fixed
order - reveals, then calls, then the narration - so a turn is the unit in which
a reveal and the move it precedes belong together.

**The party's room** is reconstructed from the kernel's own move line, which is
the only transcript entry that changes it (``kernel.call_move``). It starts at the
fixture's first room.

**A reveal is AHEAD** when a referee entry publishes a room fact's text while the
party occupies a different room, and no move into that room lands later in the
same turn. The same-turn exemption is not a softening: ``call_move`` reveals the
room it moves into, and a referee that declares a room and enters it in one turn
has told the party about the room they are walking into, which is what entering
is.

**A hidden fact is AHEAD** on the same test, keyed by the room in its own id -
``("hidden", "R3")`` belongs to R3. It is counted and reported separately because
its text never names its room, so the join is by id rather than by prose, and a
reader should be able to see which half of the count rests on which.

**Distance is by fixture order**, the order ``scenario.json`` lists the rooms in,
and is reported as such. The fixture states no adjacency graph; inventing one here
to say "skipped a room" would be this module asserting a dungeon topology the
dungeon does not carry.

## The control runs first

A count derived from a replay is worth nothing until the replay agrees with
something the run already recorded. The check: the set of room facts this replay
sees declared must equal the room facts in each session's own ``declared`` list.
A disagreement means the replay is not recognising declarations - every number
below would then be measured against the wrong entitlement - and it exits
non-zero rather than printing a plausible figure.

That control is deliberately the one thing this module and ``eval.durf_rescore``
share: both reconstruct entitlement from the transcript, and both are only worth
reading because the reconstruction is checkable against the record.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from games.durf import facts
from games.durf.kernel import FIXTURE_DIR

#: The kernel's move line, which is the only entry that moves the party.
MOVE_PREFIX = "The party moves to "

#: A transcript entry kind. Mirrors ``games.durf.session`` rather than importing
#: it, because what is read here is a stored record's dict, not a live ``Entry``.
REFEREE, SPEECH = "referee", "speech"

#: The fact kinds whose id names the room they belong to, which is what makes
#: "ahead of the party" answerable for them. An ``("npc", ...)`` id names a
#: creature group, not a place, so where the party stood says nothing about it
#: and it is out of this instrument's scope rather than silently miscounted.
ROOM_KEYED = ("room", "hidden")


def room_order(path: Path | None = None) -> list[str]:
    """The rooms in the order the fixture lists them. Not an adjacency claim."""
    root = Path(path) if path else FIXTURE_DIR / "scenario.json"
    raw = json.loads(root.read_text(encoding="utf-8"))
    return [room["id"] for room in raw["rooms"]]


def rows_of(record: Path) -> list[dict]:
    """The per-session rows, same source ``eval.durf_rescore`` reads."""
    jsonl = record.with_suffix(record.suffix + ".jsonl")
    return [json.loads(line) for line in
            jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]


def turns_of(row: dict) -> list[list[dict]]:
    """The transcript split into turns: the referee entries after each speech."""
    out: list[list[dict]] = [[]]
    for entry in row.get("transcript", []):
        if entry.get("kind") == SPEECH:
            out.append([])
        else:
            out[-1].append(entry)
    return out


def moved_to(entry: dict) -> str | None:
    """The room a move line moves the party into, or None if it is not one."""
    text = entry.get("text", "")
    if not text.startswith(MOVE_PREFIX):
        return None
    return text[len(MOVE_PREFIX):].split()[0]


def replay(row: dict, declaration_text: dict, seeded: set,
           order: list[str]) -> dict:
    """Every ahead-reveal in one session, and the declarations the replay saw.

    ``declaration_text`` maps a fact's published text to its id - the same
    recognition ``eval.durf_rescore`` uses, and the thing the control checks.
    """
    room = order[0]
    ahead: list[dict] = []
    declared = set(seeded)
    for turn in turns_of(row):
        entering = {moved_to(e) for e in turn} - {None}
        for entry in turn:
            fid = declaration_text.get(entry.get("text", ""))
            into = moved_to(entry)
            if into is not None:
                # `call_move` reveals the room it enters; the line carries the
                # room's text after the move sentence, so it is recognised here
                # rather than by a text match.
                declared.add(("room", into))
                room = into
                continue
            if fid is None or fid in declared:
                # A fact declared twice is not a second reveal. Re-declaring one
                # the party already holds reads as an ahead-reveal on a naive
                # room comparison - the party has walked on - and is not one.
                continue
            declared.add(fid)
            kind, where = fid[0], fid[-1]
            if kind not in ROOM_KEYED or where == room or where in entering:
                continue
            ahead.append({"kind": kind, "fact": list(fid), "from": room,
                          "distance": order.index(where) - order.index(room)
                          if where in order and room in order else None})
    return {"ahead": ahead, "declared": declared}


def control(rows: list[dict], replays: list[dict]) -> list[str]:
    """The replay's declarations against each session's own ``declared`` list."""
    bad = []
    for row, seen in zip(rows, replays):
        recorded = {tuple(f) for f in row.get("declared", [])}
        if seen["declared"] != recorded:
            bad.append(
                f"session {row.get('index')}: replay saw "
                f"{sorted(seen['declared'])!r} declared, record says "
                f"{sorted(recorded)!r}")
    return bad


def leak_context(row: dict) -> list[dict]:
    """For each recorded leak, the seat declaration the carrying line answered.

    The eight iron-door leaks are all the referee narrating a declaration; which
    declaration is the thing that decides whether the fixture or the referee is
    at fault, so it is read off the record rather than argued.
    """
    out = []
    carried = {line for block in row.get("leaks", [])
               for line in block.get("evidence", [])}
    said = None
    for entry in row.get("transcript", []):
        if entry.get("kind") == SPEECH:
            said = entry
        elif entry.get("text") in carried:
            out.append({"declaration": (said or {}).get("text", ""),
                        "who": (said or {}).get("who", ""),
                        "narration": entry["text"]})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("record", help="a session summary .json; its .jsonl is read")
    ap.add_argument("--leaks", action="store_true",
                    help="print the seat declaration behind each recorded leak")
    args = ap.parse_args(argv)

    record = Path(args.record)
    try:
        rows = rows_of(record)
    except FileNotFoundError as exc:
        print(f"no rows at {exc.filename} - a record's .jsonl is what this reads.")
        return 1

    ledger = facts.load()
    declaration_text = {f.text: fid for fid, f in ledger.facts.items()}
    order = room_order()
    seeded = {fid for fid in ledger.facts if fid in ledger.revealed}

    replays = [replay(row, declaration_text, seeded, order) for row in rows]

    bad = control(rows, replays)
    print("instrument control - replayed declarations against each record's own")
    for line in bad[:5]:
        print(f"  DISAGREES: {line}")
    if bad:
        print(f"  {len(bad)} session(s) disagree. The replay is not recognising "
              f"declarations, so every count below would be measured against the "
              f"wrong entitlement. Nothing is printed.")
        return 1
    print(f"  reproduced exactly across {len(rows)} sessions\n")

    with_ahead = [(row, r) for row, r in zip(rows, replays) if r["ahead"]]
    held = sum(1 for row, _ in with_ahead if row.get("gate1_held"))
    print(f"{record.as_posix()}: {len(rows)} sessions")
    print(f"  sessions revealing a room or hidden fact ahead of the party: "
          f"{len(with_ahead)}/{len(rows)}")
    print(f"    of which gate #1 recorded a HOLD: {held}")

    tally: dict[str, int] = {}
    for _, r in with_ahead:
        for a in r["ahead"]:
            key = f"{a['kind']} {a['fact'][-1]} declared from {a['from']}"
            tally[key] = tally.get(key, 0) + 1
    print("  ahead-reveals, by where the party was standing:")
    for key, count in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"    {key}: {count}")

    dist = [a["distance"] for _, r in with_ahead for a in r["ahead"]
            if a["distance"] is not None]
    if dist:
        print(f"  distance in fixture order (not an adjacency claim): "
              f"{min(dist)} to {max(dist)}, "
              f"{sum(1 for d in dist if d > 1)} of {len(dist)} more than one")

    if args.leaks:
        print("\nthe seat declaration behind each recorded leak:")
        seen: dict[str, int] = {}
        for row in rows:
            for item in leak_context(row):
                seen[item["declaration"]] = seen.get(item["declaration"], 0) + 1
                print(f"  seed {row.get('seed')}: {item['who']} declared "
                      f"{item['declaration']!r}")
                print(f"    referee: {item['narration']}")
        print("  declarations behind the leaks:")
        for text, count in sorted(seen.items(), key=lambda kv: -kv[1]):
            print(f"    {text!r}: {count}")

    print("\nNOT a read of gate #1. Gate #1 audits a render against what was "
          "declared; this counts declarations against where the party stood. "
          "docs/durf-gate1-criterion.md binds real reads.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
