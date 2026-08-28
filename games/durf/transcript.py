"""Render one DURF session as a markdown transcript a human can read.

Same contract as ``games/cabal/transcript.py`` and the same channel distinction,
which is the whole reason a transcript is the evidence a claim ships with:

  - a ``referee`` entry is the referee's own words - the kernel's result lines and
    the adjudicator's narration. Italic here, and the ONLY channel gate #1 audits.
    A world fact appearing in one of these before it was declared is the leak.
  - a ``speech`` entry is what a seat said or declared. Plain here. It is
    gameplay, and the audit drops it for the same reason cabal's does.
  - a seat's private ``think`` is in neither channel and appears nowhere below.

The gate #1 section is the point of the file: the facts the adjudicator declared,
the facts it did not, and - when the session leaked - the exact referee line that
carried the undeclared one. A leak reported as a rate with no line behind it
cannot be reviewed, which is why the evidence travels in the record.

    python -m games.durf.transcript eval/records/durf-sess2.json.jsonl --session 1
    python -m games.durf.transcript run.json.jsonl --session 0 --out sess0.md
"""

from __future__ import annotations

import argparse
import json
import sys

from . import rules


def _header(rec: dict, meta: dict | None) -> list[str]:
    meta = meta or {}
    bits = [f"seed `{rec.get('seed')}`", f"{rec.get('rounds')} round(s)",
            f"{rec.get('turns')} turns"]
    if meta.get("model"):
        bits.insert(0, f"model `{meta['model']}`")
    if meta.get("arm"):
        bits.insert(0, f"{meta['arm']} arm")
    return ["# DURF - session transcript", "",
            f"ruleset `{rules.RULESET}` | " + " | ".join(bits), "",
            f"*{rules.ATTRIBUTION}*", ""]


def _public_lines(rec: dict) -> list[str]:
    out = ["## Public record", "",
           "*Italic lines are the referee's own words - the kernel's results and "
           "the adjudicator's narration, and the only channel gate #1 audits. "
           "Plain lines are what a seat said or declared; those are gameplay. No "
           "seat's private reasoning appears anywhere below - it never enters "
           "either channel.*", ""]
    for entry in rec.get("transcript") or []:
        if entry["kind"] == "referee":
            out.append(f"- *{entry['text']}*")
        else:
            out.append(f"- {entry['who']}: \"{entry['text']}\"")
    if len(out) == 5:
        out.append("- (the session produced no public record)")
    return out + [""]


def _gate_lines(rec: dict) -> list[str]:
    held = rec.get("gate1_held")
    verdict = {True: "**HELD**", False: "**LEAKED**",
               None: "**NOT AUDITED** - which is not a pass"}[held]
    out = ["## Gate #1 - the entitlement audit", "",
           f"Verdict: {verdict}.", "",
           "Facts the adjudicator DECLARED to the party:", ""]
    out += [f"- `{fact}`" for fact in rec.get("declared") or []] or ["- (none)"]
    out += ["", "Facts it did not, which no referee byte above may show:", ""]
    out += [f"- `{fact}`" for fact in rec.get("undeclared") or []] or ["- (none)"]
    for entry in rec.get("leaks") or []:
        out += ["", f"### The leak, in seat {entry['viewer']}'s context", ""]
        out += [f"- `{fact}` reached it via the term `{term}`"
                for fact, term in entry["leaks"]]
        out += ["", "Carried by the referee line(s):", ""]
        out += [f"> {line}" for line in entry["evidence"]] or ["> (not located)"]
    return out + [""]


def _integrity_lines(rec: dict) -> list[str]:
    decisions = rec.get("decisions") or 0
    share = (rec.get("fallbacks", 0) / decisions) if decisions else 0.0
    out = ["## Integrity (referee-side)", "",
           f"- {rec.get('fallbacks', 0)}/{decisions} decisions fell back "
           f"({share:.2%})",
           f"- {rec.get('recovered', 0)} were sent back by the parser or the "
           f"kernel and then answered legally",
           f"- {rec.get('refused_attempts', 0)} refused attempts, of which "
           f"{rec.get('rule_refused_attempts', 0)} were rule refusals"]
    if rec.get("error"):
        out += ["", f"- the session ended early: `{rec['error']}`"]
    return out + [""]


def _reasoning_lines(rec: dict) -> list[str]:
    """The referee-side section, and it is deliberate.

    Gate #1 is about the bytes a seat's MODEL receives; a post-game document read
    by a human is the one place the refusals and the fallbacks are meant to be
    visible. The public record above stays clean either way.
    """
    log = rec.get("decision_log") or []
    refused = [d for d in log if d.get("refused")]
    if not refused:
        return []
    return ["## Why turns were sent back (referee-side)", ""] + \
           [f"- turn {d['turn']}, seat {d['seat']} ({d['phase']}): "
            f"`{d['refused']}`" for d in refused] + [""]


def render(record, meta: dict | None = None) -> str:
    rec = record if isinstance(record, dict) else json.loads(record)
    return "\n".join(_header(rec, meta) + _public_lines(rec) + _gate_lines(rec)
                     + _integrity_lines(rec) + _reasoning_lines(rec))


def load(path: str, index: int) -> dict:
    """One session out of a ``--out`` run's JSONL sibling."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("index") == index:
                return row
    raise SystemExit(f"no session with index {index} in {path}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("jsonl", help="the per-session JSONL a --out run wrote")
    ap.add_argument("--session", type=int, default=0)
    ap.add_argument("--arm", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--out")
    args = ap.parse_args()
    text = render(load(args.jsonl, args.session),
                  {"arm": args.arm, "model": args.model})
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
