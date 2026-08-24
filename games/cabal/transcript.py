"""Render one game as a markdown transcript a human can read.

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
  - A seat's private ``think`` is in neither channel and is discarded by the driver
    before it could reach one, so it cannot reach this file either. ``_record_lines``
    whitelists the two kinds above rather than rendering whatever it is handed.

Two inputs, one output. A live ``CabalReferee`` (``from_referee``) or a
``GameRecord`` - live or loaded from a ``run_games.py --out`` JSON. Records
written before ``GameRecord`` carried ``public_events`` have no timeline to
render; those degrade to a clearly-labelled reconstruction rather than a
plausible fake.

    python -m games.cabal.transcript eval/records/local-1game-deception.json
    python -m games.cabal.transcript run.json --game 3 --out game3.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass

from games.cabal.roles import DEFAULT_THEME, SETUPS, THEMES, Team

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


def _role_label(key: str, theme) -> str:
    return f"{theme.role_names.get(key, key)} (`{key}`)"


def _faction_label(key: str, theme) -> str:
    team = _team_of(key)
    return theme.faction_names[team] if team else "?"


def _team_of(role_key: str) -> Team | None:
    for setup in SETUPS.values():
        for role in setup.roles:
            if role.key == role_key:
                return role.team
    return None


def _record_lines(public_events) -> list[str]:
    """The public timeline, in order. Only the two public kinds render; anything
    else is dropped rather than guessed at - the private channel must not acquire a
    path to this file by someone appending a new tuple kind upstream."""
    out: list[str] = []
    for entry in public_events or []:
        kind, text = entry[0], entry[1]
        if kind == "event":
            out.append(f"- *{text}*")
        elif kind.startswith("speech:"):
            out.append(f"- {text}")
    return out


def _deal_lines(rec: dict) -> list[str]:
    n = len(rec.get("assignment") or {})
    setup = SETUPS.get(n)
    lines = [f"- {n} seats, numbered 0..{n - 1}."]
    if setup:
        lines.append(
            f"- Mission team sizes {list(setup.team_sizes)}; "
            f"fails needed to sink one: {list(setup.fails_required)}."
        )
    for line in rec.get("log") or []:
        if line.startswith("dealt "):
            lines.append(f"- {line}")
    lines.append(
        "- Good wins by holding three missions *and* surviving the hunt; evil wins "
        "by sinking three, by stalling five proposals in a row, or by naming the "
        "seer at the end."
    )
    return lines


def _outcome_lines(rec: dict, theme) -> list[str]:
    missions = rec.get("missions") or []
    lines = []
    if missions:
        shown = ", ".join(
            f"#{i + 1} {'SUCCESS' if ok else 'FAIL'}" for i, ok in enumerate(missions)
        )
        lines.append(f"- Missions run: {shown}")
    else:
        lines.append("- No mission ever ran.")
    hunt = rec.get("hunt")
    if hunt:
        lines.append(
            f"- The hunt: seat {hunt['hunter']} named seat {hunt['target']}; the "
            f"seer was seat {hunt['seer']} -> "
            f"{'HIT' if hunt['hit'] else 'MISS'}."
        )
    winner = rec.get("winner")
    faction = theme.faction_names[Team(winner)] if winner else "nobody"
    # the referee's own line reads "WINNER: <faction> (<why>)"; the faction is
    # already in the sentence below, so keep only the why
    reason = rec.get("reason") or ""
    if reason.startswith("WINNER:") and "(" in reason:
        reason = reason[reason.index("(") + 1:].rstrip(")")
    lines.append(f"- **Winner: {faction}** - {reason}" if reason
                 else f"- **Winner: {faction}**")
    return lines


def _assignment_lines(rec: dict, theme) -> list[str]:
    assignment = rec.get("assignment") or {}
    lines = ["| seat | role | faction |", "|---|---|---|"]
    for seat in sorted(assignment, key=lambda s: int(s)):
        key = assignment[seat]
        lines.append(f"| {seat} | {_role_label(key, theme)} | "
                     f"{_faction_label(key, theme)} |")
    return lines


def _integrity_lines(rec: dict) -> list[str]:
    decisions = rec.get("decisions") or 0
    fallbacks = rec.get("fallbacks") or 0
    rate = fallbacks / decisions if decisions else 0.0
    lines = [
        f"- {decisions} decisions, {fallbacks} of them illegal after retries and "
        f"played at random ({rate:.1%}).",
    ]
    if rate > 0.10:
        lines.append(
            "- **Above 10%: this transcript is substantially a random policy "
            "wearing a model's name.**"
        )
    trace = rec.get("trace_sample") or []
    if trace:
        lines.append("- Why replies were refused or retried:")
        lines += [f"  - `{line}`" for line in trace[:8]]
    if rec.get("error"):
        lines.append(f"- Game errored: `{rec['error']}`")
    return lines


def _legacy_lines(rec: dict) -> list[str]:
    """A record with no timeline. Show what was actually kept, labelled as such."""
    lines = [LEGACY_BANNER, ""]
    utterances = rec.get("utterances") or []
    if utterances:
        lines.append("**Table talk, in order:**")
        lines.append("")
        lines += [f"- {u}" for u in utterances]
    else:
        lines.append("No utterance was recorded.")
    votes = rec.get("votes") or []
    n = len(rec.get("assignment") or {}) or 5
    if votes and len(votes) % n == 0:
        lines += ["", "**Vote rounds, derived by chunking the vote records into "
                  f"blocks of {n} (the proposals are not in this record):**", "",
                  "| round | approvals | tainted team? | approved |",
                  "|---|---|---|---|"]
        for i in range(0, len(votes), n):
            block = votes[i:i + n]
            ayes = sum(1 for v in block if v["approved"])
            tainted = any(v["team_has_evil"] for v in block)
            lines.append(
                f"| {i // n + 1} | {ayes}/{n} | {'yes' if tainted else 'no'} | "
                f"{'yes' if ayes * 2 > n else 'no'} |"
            )
    return lines


def render(record, meta: dict | None = None) -> str:
    """One game -> markdown. ``record`` is a ``GameRecord`` or its dict form;
    ``meta`` is run context (backend, model, rounds) shown in the header."""
    rec = _as_dict(record)
    meta = meta or {}
    theme = _theme(rec.get("theme") or meta.get("theme") or "")
    timeline = _record_lines(rec.get("public_events"))

    head = ["# Cabal - game transcript"]
    ctx = [f"theme `{theme.name}`"]
    for key, label in (("backend", "backend"), ("model", "model"),
                       ("rounds", "discussion round(s)"), ("seed", "seed")):
        if meta.get(key) not in (None, "", False):
            ctx.append(f"{meta[key]} {label}" if key == "rounds"
                       else f"{label} {meta[key]}")
    head += ["", " | ".join(ctx)]

    out = head + ["", "## The deal (referee-side)", ""] + _deal_lines(rec)
    out += ["", "## Public record", ""]
    if timeline:
        out += [
            "*Italic lines are the referee's own words - facts everyone sees, and "
            "the only channel gate #1 audits. Plain lines are what a seat chose to "
            "say out loud; a lie in one of those is a move, not a leak. No seat's "
            "private reasoning appears anywhere below - it never enters either "
            "channel.*",
            "",
        ] + timeline
    else:
        out += _legacy_lines(rec)
    out += ["", "## Outcome", ""] + _outcome_lines(rec, theme)
    out += ["", "## Integrity", ""] + _integrity_lines(rec)
    out += ["", "## The secret assignment (referee-side, revealed)", ""]
    out += _assignment_lines(rec, theme)
    out += [""]
    return "\n".join(out)


def from_referee(ref, record=None, meta: dict | None = None) -> str:
    """Render a game straight off a live referee. ``record`` supplies the
    integrity counters the referee does not track."""
    rec = _as_dict(record) if record is not None else {}
    rec = dict(rec)
    rec["assignment"] = {s: r.key for s, r in ref.assignment.items()}
    rec["public_events"] = list(ref.public_events)
    rec["log"] = list(ref.log)
    rec["theme"] = ref.theme.name
    rec.setdefault("missions", list(ref.results))
    rec["winner"] = ref.winner.value if ref.winner else None
    rec.setdefault("reason", ref.log[-1] if ref.log else "")
    return render(rec, meta)


def write(path: str, text: str) -> str:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def main() -> None:
    ap = argparse.ArgumentParser(
        description="render a run_games.py --out JSON as a readable transcript")
    ap.add_argument("path", help="a run_games.py --out JSON")
    ap.add_argument("--game", type=int, default=0, help="which game in the file")
    ap.add_argument("--out", help="write here instead of stdout")
    args = ap.parse_args()

    with open(args.path, encoding="utf-8") as fh:
        blob = json.load(fh)
    games = blob.get("games") or []
    if not games:
        sys.exit(f"{args.path} holds no games")
    if not 0 <= args.game < len(games):
        sys.exit(f"--game {args.game} out of range (file has {len(games)})")
    text = render(games[args.game], blob.get("args") or {})
    if args.out:
        print(f"wrote {write(args.out, text)}")
    else:
        print(text)


if __name__ == "__main__":
    main()
