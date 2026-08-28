"""The replay is only worth having if it reproduces an audit that already ran.

Every case here is built from a synthetic ledger and synthetic rows: `eval/records/`
is gitignored, so a test that read a real record would pass on this box and fail on
a clone. The one real-record check is in the module's `--check` flag, which is a
control a person runs, not a test that silently depends on a file.

The two ordering properties are the whole mechanism and both are mutation-checked:
a fact's declaration must be entitled BEFORE the entry carrying it is audited, and
a fact public at start must be seeded even though it is never declared.
"""
from __future__ import annotations

from eval import durf_rescore as rescore
from games.durf import facts


def ledger() -> facts.FactLedger:
    """Two facts, disjoint terms, one of them public at start."""
    made = {
        ("room", "R1"): facts.WorldFact(("room", "R1"), "the entry", ("scree slope",),
                                        "R1 Entry: a scree slope down to a door."),
        ("hidden", "R2"): facts.WorldFact(("hidden", "R2"), "the cavity",
                                          ("shallow cavity", "40 GP"),
                                          "A shallow cavity holding 40 GP."),
    }
    return facts.FactLedger(facts=made, revealed=set())


def parts(led):
    return (rescore.terms_from(led),
            {f.text: fid for fid, f in led.facts.items()},
            {("room", "R1")})


def row(*texts, leaks=()):
    return {"index": 0,
            "transcript": [{"kind": "referee", "who": "referee", "text": t}
                           for t in texts],
            "leaks": [{"viewer": 0, "leaks": [[list(f), t] for f, t in leaks],
                       "evidence": []}] if leaks else []}


def test_an_undeclared_fact_in_referee_prose_is_found():
    led = ledger()
    terms, texts, seed = parts(led)
    found = rescore.replay(row("You see a shallow cavity by the bier."),
                           terms, texts, seed)
    assert found == [(("hidden", "R2"), "shallow cavity")]


def test_a_declaration_is_not_its_own_leak():
    """The ordering guard. Publishing a fact's text IS the declaration, so auditing
    it against a set the fact is not yet in would report every legal reveal."""
    led = ledger()
    terms, texts, seed = parts(led)
    assert rescore.replay(row("A shallow cavity holding 40 GP."),
                          terms, texts, seed) == []


def test_prose_after_a_declaration_is_legal_and_before_it_is_not():
    led = ledger()
    terms, texts, seed = parts(led)
    legal = rescore.replay(row("A shallow cavity holding 40 GP.",
                               "You lever it up and find the shallow cavity."),
                           terms, texts, seed)
    assert legal == []
    illegal = rescore.replay(row("You lever it up and find the shallow cavity.",
                                 "A shallow cavity holding 40 GP."),
                             terms, texts, seed)
    assert illegal == [(("hidden", "R2"), "shallow cavity")]


def test_a_fact_public_at_start_is_seeded_and_does_not_read_as_a_leak():
    """R1 is never declared in a transcript because it was never secret. Without
    the seed its terms would leak in the first line of every session."""
    led = ledger()
    terms, texts, seed = parts(led)
    assert rescore.replay(row("Vesh steps down the scree slope."),
                          terms, texts, seed) == []
    assert rescore.replay(row("Vesh steps down the scree slope."),
                          terms, texts, set()) == [(("room", "R1"), "scree slope")]


def test_a_speech_entry_is_not_audited_as_a_referee_byte():
    led = ledger()
    terms, texts, seed = parts(led)
    said = {"index": 0, "leaks": [],
            "transcript": [{"kind": "speech", "who": "Vesh",
                            "text": "I bet there is a shallow cavity here."}]}
    assert rescore.replay(said, terms, texts, seed) == []


def test_the_control_reproduces_a_recorded_leak_and_names_a_disagreement():
    led = ledger()
    terms, texts, seed = parts(led)
    rows = [row("You see a shallow cavity by the bier.",
                leaks=[(("hidden", "R2"), "shallow cavity")])]
    scored = rescore.rescore(rows, terms, texts, seed)
    assert rescore.check(rows, scored) == []

    wrong = [row("Nothing happens.", leaks=[(("hidden", "R2"), "shallow cavity")])]
    bad = rescore.check(wrong, rescore.rescore(wrong, terms, texts, seed))
    assert len(bad) == 1 and "shallow cavity" in bad[0]


def test_a_term_scored_back_in_finds_what_the_current_set_cannot():
    """The counterfactual the module exists for: what a dropped sentinel was
    carrying, answered off records rather than off another campaign."""
    led = ledger()
    _, texts, seed = parts(led)
    line = row("feeling for any loose flagstone or hidden seam")
    assert rescore.replay(line, rescore.terms_from(led), texts, seed) == []
    added = rescore.terms_from(led, {("hidden", "R2"): ["loose flagstone"]})
    assert rescore.replay(line, added, texts, seed) == [
        (("hidden", "R2"), "loose flagstone")]


def test_hold_rate_counts_a_session_not_a_leak():
    led = ledger()
    terms, texts, seed = parts(led)
    rows = [row("Nothing happens."),
            row("A shallow cavity here.", "And 40 GP in it.")]
    scored = rescore.rescore(rows, terms, texts, seed)
    assert scored["held"] == 1 and scored["sessions"] == 2
    assert sum(scored["leaks"].values()) == 2, "both terms in one session count"


def test_a_missing_jsonl_is_told_apart_from_an_empty_one(tmp_path):
    missing = tmp_path / "nope.json"
    assert rescore.main([str(missing)]) == 1
