"""Fact-keyed entitlement, and the naive leak scan over it.

``core/observability.py`` keys a secret to a SEAT, because the first two games in
this arena hide secrets that belong to seats. DURF does not: room contents before
entry, whether the anchor is rotted, an NPC's stats - none of those is any seat's
secret, no seat owns them, and every seat is equally un-entitled to them.
``docs/durf-rung.md`` §The entitlement model breaks names the generalisation:
widen the key from a seat to a fact, of which "seat 3's role" is one case.

**It is built here rather than in ``core/`` on purpose.** The ``core/`` invariant
promotes on evidence that a SECOND game needs a thing, and one rung is not two.
cabal and changeling are both seat-keyed and neither wants this. When a second
game asks, the move is to widen ``find_leaks``' key and delete the adapter below.

**The matcher is not reimplemented here, and that is the whole design.**
``find_fact_leaks`` indexes the facts and hands the work to
``core.observability.find_leaks`` unchanged, so this rung inherits the audited
primitive's semantics rather than a second naive matcher that could drift from it.
The repo invariant - ``find_leaks`` stays naive, a colliding term gets RENAMED -
therefore applies here by construction rather than by promise, and
``check_facts`` below is what enforces the renaming half.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from core.observability import find_leaks

#: A world fact's key. A tuple so it is hashable and readable in a record:
#: ``("hidden", "R2")``, ``("room", "R3")``, ``("npc", "barrow-wight")``.
FactId = tuple[str, ...]

#: Handed to ``find_leaks`` as the ``viewer``. The adapter numbers facts from 0,
#: so -1 is not a key and the primitive's ``seat == viewer`` self-skip - which is
#: about a seat reading its own secret and has no meaning over facts - can never
#: fire. Named rather than inlined because a stray 0 here would silently exempt
#: the first fact from every audit.
NO_VIEWER = -1

FACTS_FILE = Path(__file__).resolve().parent / "fixtures" / "facts.json"


class FactError(Exception):
    """The fact set on disk cannot be used as a leak instrument."""


@dataclass(frozen=True)
class WorldFact:
    """One thing the referee knows and the party does not (yet).

    ``terms`` are the naive sentinels - the strings whose appearance in a seat's
    outgoing context means the fact reached it. ``label`` is what the adjudicator
    declares to reveal it, and ``text`` is the referee-side statement of the fact
    itself, which never reaches a seat except through prose the adjudicator writes.
    """

    fact_id: FactId
    label: str
    terms: tuple[str, ...]
    text: str


@dataclass
class FactLedger:
    """Every world fact, and which of them the party is entitled to right now.

    Revealing is one-way within a session: a fact the party has learned cannot be
    un-learned, so ``revealed`` only grows. That matters for the audit - an
    entitlement that could shrink would let a render pass at delivery and fail on
    a re-score, which is the recompute failure the snapshot exists to prevent.
    """

    facts: dict[FactId, WorldFact]
    revealed: set[FactId]
    #: Which dungeon these facts describe. Defaulted so a hand-built ledger in a
    #: test needs no id, and carried so ``kernel.load`` can refuse a pair of files
    #: that describe two different dungeons.
    scenario_id: str = ""

    def reveal(self, fact_id: FactId) -> WorldFact:
        """Declare a fact to the party. Raises on a fact that does not exist.

        Raising rather than ignoring is the kernel rule from
        ``docs/action-channel.md``: an unrecognised call must never be dropped,
        because a dropped call is indistinguishable from one the model never
        emitted, and a broken session then reads as a quiet one.
        """
        if isinstance(fact_id, str):
            # `tuple("R2")` is `("R", "2")`, which would miss every fact and
            # report a plausible-looking "no such fact ('R', '2')". Refuse the
            # shape instead, so a model passing a bare string is told what a fact
            # id actually is.
            raise FactError(
                f"a fact id is a list of parts such as ['room', 'R2'], not the "
                f"string {fact_id!r}")
        key = tuple(fact_id)
        if key not in self.facts:
            raise FactError(
                f"no such fact {key!r}; the declarable facts are "
                f"{sorted(self.facts)}")
        self.revealed.add(key)
        return self.facts[key]

    @property
    def entitled(self) -> frozenset[FactId]:
        """The snapshot. Frozen so a caller holding one cannot watch it move."""
        return frozenset(self.revealed)

    def secret_terms(self) -> dict[FactId, list[str]]:
        return {fid: list(f.terms) for fid, f in self.facts.items()}

    def undeclared(self) -> list[WorldFact]:
        return [f for fid, f in self.facts.items() if fid not in self.revealed]


def find_fact_leaks(rendered: str, secret_terms: dict[FactId, list[str]],
                    entitled) -> list[tuple[FactId, str]]:
    """Every ``(fact, term)`` this render exposes that the party is not entitled to.

    A thin index over ``core.observability.find_leaks``: facts are numbered, the
    numbers are handed to the primitive, and the answers are mapped back. The
    matching - naive, case-folded substring - is the primitive's, unchanged.
    """
    order = list(secret_terms)
    numbered = {i: secret_terms[fid] for i, fid in enumerate(order)}
    ent = {i for i, fid in enumerate(order) if fid in entitled}
    return [(order[i], term)
            for i, term in find_leaks(rendered, numbered, ent, NO_VIEWER)]


def load(path: Path | str | None = None) -> FactLedger:
    """Read the fact set, checking it before it is trusted as an instrument."""
    root = Path(path) if path is not None else FACTS_FILE
    raw = json.loads(root.read_text(encoding="utf-8"))
    facts = {}
    for entry in raw["facts"]:
        fid = tuple(entry["fact_id"])
        facts[fid] = WorldFact(fact_id=fid, label=entry["label"],
                               terms=tuple(entry["terms"]), text=entry["text"])
    ledger = FactLedger(facts=facts, revealed=set(),
                        scenario_id=raw.get("scenario_id", ""))
    for fid in raw.get("public_at_start", []):
        ledger.reveal(tuple(fid))
    check_facts(ledger)
    return ledger


def check_facts(ledger: FactLedger) -> None:
    """Hold the fact set to what naive matching needs, or refuse to score with it.

    Two properties, and both are the RENAME remedy the repo invariant names,
    enforced rather than remembered:

    - **No term is empty or blank.** ``find_leaks`` skips a falsy term, so a blank
      one is a fact with no sentinel at all - it would read as audited and catch
      nothing.
    - **Terms do not collide across facts**, in either direction of substring.
      Two facts sharing a sentinel means revealing one leaves the other's term
      loose in a legal render, which reports a leak that is not one - and this
      repo's answer to a colliding term is to rename it, never to weaken the
      matcher.
    - **No fact's term appears in another fact's TEXT.** The same failure by the
      route the pairwise check cannot see. ``kernel.call_reveal`` publishes a
      fact's own text verbatim, so a text carrying another fact's sentinel means
      declaring the first one writes the second one's term into the transcript -
      and every later render is then charged with a leak the referee could not
      have avoided, because the kernel wrote it. Worse than a term collision:
      a collision is visible in the term list, this is not, and it surfaces only
      as a run-time leak attributed to a model that obeyed the rules. The remedy
      is the same rename, and it belongs on the TERM - a fact's text is what the
      party is told, and moving it moves a model-facing byte.
    - **Every fact's term appears in its OWN text.** The mirror image of the
      cross-text check, and the one the pairwise check cannot see either: a
      fact's own statement is what ``kernel.call_reveal`` publishes when it is
      legally declared, so a term missing from its own text means declaring the
      fact writes prose that carries no sentinel at all - not another fact's,
      not its own. The fact then goes undeclared-and-unaudited by construction:
      no render check can ever see it "go" through its own reveal, because there
      is nothing in the text for a sentinel to catch.
    """
    seen: dict[str, FactId] = {}
    for fid, fact in ledger.facts.items():
        if not fact.terms:
            raise FactError(f"{fid!r} carries no terms; it cannot be audited")
        for term in fact.terms:
            low = term.strip().lower()
            if not low:
                raise FactError(f"{fid!r} carries a blank term; find_leaks skips it")
            for other, owner in seen.items():
                if owner == fid:
                    continue
                if low in other or other in low:
                    raise FactError(
                        f"terms collide across facts: {term!r} ({fid!r}) and the "
                        f"term owned by {owner!r}. Rename one - a shared sentinel "
                        f"makes a legal render read as a leak.")
            seen[low] = fid
    for fid, fact in ledger.facts.items():
        for term in fact.terms:
            low = term.strip().lower()
            if low not in fact.text.lower():
                raise FactError(
                    f"the term {term!r} ({fid!r}) does not appear in its own "
                    f"text. Declaring {fid!r} publishes that text verbatim, so a "
                    f"term missing from it means the fact carries no sentinel at "
                    f"all when revealed. Fix the term or the text so they match.")
    for fid, fact in ledger.facts.items():
        for term in fact.terms:
            low = term.strip().lower()
            for other_id, other in ledger.facts.items():
                if other_id == fid:
                    continue
                if low in other.text.lower():
                    raise FactError(
                        f"the term {term!r} ({fid!r}) appears in {other_id!r}'s "
                        f"text. Declaring {other_id!r} publishes that text, so it "
                        f"would leak {fid!r} by construction. Rename the term - "
                        f"the text is what the party is told and moving it moves "
                        f"a model-facing byte.")
