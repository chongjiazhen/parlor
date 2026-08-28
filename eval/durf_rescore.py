"""Re-audit a DURF session record from what it already stored. No GPU, no re-run.

    py -3 -m eval.durf_rescore eval/records/durf-sess2.json

**The question this answers is "what would a different fact set have caught?"**
The 2026-08-28 rename dropped `loose flagstone` from ``["hidden", "R2"]`` and
voided the read scored against it. That was decided on the invariant, but the
COST of such a decision - how many recorded leaks a term was carrying - used to
be unanswerable without spending another campaign. It is not: a session record
carries its whole referee transcript, and entitlement at any point in it is
reconstructible from that transcript alone.

**How the reconstruction works, and why it is exact rather than approximate.**
``games/durf/session.py`` publishes a declared fact by writing the fact's own
referee-side ``text`` into the transcript as a referee entry, and it does so
BEFORE the narration that describes it. So a referee entry whose text is exactly
some fact's ``text`` IS that fact's declaration, and replaying entries in order -
adding a fact to the entitled set as its declaration goes past, then auditing the
entry - reproduces the entitlement snapshot each render was built against. The
one fact this cannot see is the one that was never declared: ``["room", "R1"]``
is public at start and is never published, so it is seeded rather than replayed.

**This is an instrument control before it is anything else.** Run against a
record's own term set it must reproduce that record's own leaks exactly - same
sessions, same facts, same terms. If it does not, the replay is wrong and no
counterfactual it computes means anything, so ``--check`` runs that comparison
and exits non-zero on a disagreement.

It measures nothing about a model. It re-runs an audit over bytes a model already
produced, which is why it is free and why it may never be reported as a new read:
a rate recomputed under a term set the run did not use is a counterfactual, and
``docs/durf-gate1-criterion.md`` is what a real read is bound by.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from games.durf import facts

#: Declared in the fixture and never published as a transcript entry, so replay
#: has to seed it. Read from the fixture rather than hardcoded here - a fixture
#: that makes a second fact public at start would otherwise be silently missed.
PUBLIC_AT_START = "public_at_start"


def public_at_start(path: Path | None = None) -> set[tuple[str, ...]]:
    root = Path(path) if path else facts.FACTS_FILE
    raw = json.loads(root.read_text(encoding="utf-8"))
    return {tuple(fid) for fid in raw.get(PUBLIC_AT_START, [])}


def rows_of(record: Path) -> list[dict]:
    """The per-session rows. The summary is derived from these, never the reverse."""
    jsonl = record.with_suffix(record.suffix + ".jsonl")
    return [json.loads(line) for line in
            jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]


def replay(row: dict, terms: dict, declaration_text: dict,
           seeded: set) -> list[tuple[tuple[str, ...], str]]:
    """Every leak this session's referee entries carry under ``terms``.

    ``declaration_text`` maps a fact's published ``text`` to its id - that is what
    makes a declaration recognisable in the transcript. ``seeded`` is what was
    public before the session began.
    """
    entitled = set(seeded)
    found = []
    for entry in row.get("transcript", []):
        if entry.get("kind") != "referee":
            continue
        text = entry.get("text", "")
        declared = declaration_text.get(text)
        if declared is not None:
            # The declaration lands BEFORE the prose that describes it, which is
            # the order `_apply` uses. Auditing the declaration against a set it
            # is not yet in would report every legal reveal as a leak.
            entitled.add(declared)
        found += facts.find_fact_leaks(text, terms, frozenset(entitled))
    return found


def recorded_leaks(row: dict) -> list[tuple[tuple[str, ...], str]]:
    """What the audit found at run time, flattened to the same shape as a replay."""
    out = []
    for block in row.get("leaks", []):
        for fid, term in block.get("leaks", []):
            out.append((tuple(fid), term))
    return out


def rescore(rows: list[dict], terms: dict, declaration_text: dict,
            seeded: set) -> dict:
    """Per-session leaks under ``terms``, and the hold rate that implies."""
    per_session = [replay(row, terms, declaration_text, seeded) for row in rows]
    held = sum(1 for found in per_session if not found)
    tally: dict[str, int] = {}
    for found in per_session:
        for fid, term in found:
            key = f"{list(fid)} via {term!r}"
            tally[key] = tally.get(key, 0) + 1
    return {"sessions": len(rows), "held": held, "leaks": tally,
            "per_session": per_session}


def check(rows: list[dict], scored: dict) -> list[str]:
    """The control: a replay under the run's own terms must reproduce its leaks."""
    bad = []
    for row, found in zip(rows, scored["per_session"]):
        if sorted(found) != sorted(recorded_leaks(row)):
            bad.append(f"session {row.get('index')}: replay {sorted(found)!r} "
                       f"against recorded {sorted(recorded_leaks(row))!r}")
    return bad


def terms_from(ledger: facts.FactLedger, add: dict[tuple, list[str]] | None = None):
    """The current fact set's terms, optionally with terms added back for a
    counterfactual - which is how the cost of a dropped sentinel is measured."""
    out = {fid: list(f.terms) for fid, f in ledger.facts.items()}
    for fid, extra in (add or {}).items():
        out[fid] = list(extra) + out.get(fid, [])
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("record", help="a session summary .json; its .jsonl is read")
    ap.add_argument("--add", action="append", default=[], metavar="FACT=TERM",
                    help="score a term back in, e.g. \"hidden,R2=loose flagstone\"")
    ap.add_argument("--check", action="store_true",
                    help="require the replay to reproduce the record's own leaks")
    args = ap.parse_args(argv)

    record = Path(args.record)
    try:
        rows = rows_of(record)
    except FileNotFoundError as exc:
        print(f"no rows at {exc.filename} - a record's .jsonl is what this reads.")
        return 1

    ledger = facts.load()
    declaration_text = {f.text: fid for fid, f in ledger.facts.items()}
    seeded = public_at_start()

    add: dict[tuple, list[str]] = {}
    for spec in args.add:
        key, _, term = spec.partition("=")
        add.setdefault(tuple(key.split(",")), []).append(term)

    scored = rescore(rows, terms_from(ledger, add), declaration_text, seeded)
    print(f"{record.as_posix()}: {scored['sessions']} sessions")
    if add:
        shown = {",".join(k): v for k, v in add.items()}
        print(f"  counterfactual: terms scored back in - {shown}")
    print(f"  held {scored['held']}/{scored['sessions']} under this term set")
    for key, count in sorted(scored["leaks"].items()):
        print(f"    {key}: {count}")
    if not scored["leaks"]:
        print("    no leak under this term set")

    if args.check:
        bad = check(rows, rescore(rows, terms_from(ledger, add),
                                  declaration_text, seeded))
        print("\ninstrument control - replay against the record's own leaks")
        for line in bad:
            print(f"  DISAGREES: {line}")
        if bad:
            print("  EITHER the replay is wrong and nothing it computes means "
                  "anything, OR the term set scored here is not the one the run "
                  "used - which is the ordinary case under --add. The control is "
                  "only meaningful against the run's OWN terms.")
            return 1
        print("  reproduced exactly")
    print("\nNOT a read. A rate under a term set the run did not use is a "
          "counterfactual; docs/durf-gate1-criterion.md binds real reads.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
