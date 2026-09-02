"""The fact-keyed entitlement primitive, and the two things it must not become.

The shipped fact set is an INSTRUMENT: a blank sentinel or a term shared between
two facts turns the audit into something that reads clean while catching nothing,
or that reports a leak on a legal render. Both are checked at load, so both are
tested here against hand-built sets rather than against the shipped one.
"""

from __future__ import annotations

import json

import pytest

from core.observability import find_leaks
from games.durf import facts


def ledger(**terms) -> facts.FactLedger:
    """A hand-built fact set. Keys are one-part fact ids, as real ones are tuples."""
    return facts.FactLedger(
        facts={(fid,): facts.WorldFact((fid,), f"fact {fid}", tuple(t),
                                       f"text {fid}")
               for fid, t in terms.items()},
        revealed=set())


def test_shipped_fact_set_loads_and_passes_its_own_checks():
    led = facts.load()
    assert led.facts, "the shipped fact set is empty"
    facts.check_facts(led)
    assert ("room", "R1") in led.revealed, (
        "the party starts in R1, so its contents are public at start")


def test_an_undeclared_fact_in_a_render_is_a_leak():
    led = ledger(a=["loose flagstone"], b=["rope bridge"])
    hits = facts.find_fact_leaks(
        "the referee says: a loose flagstone by the bier",
        led.secret_terms(), led.entitled)
    assert hits == [(("a",), "loose flagstone")]


def test_declaring_the_fact_makes_the_same_prose_legal():
    led = ledger(a=["loose flagstone"], b=["rope bridge"])
    led.reveal(("a",))
    assert facts.find_fact_leaks("a loose flagstone by the bier",
                                 led.secret_terms(), led.entitled) == []


def test_matching_is_the_primitive_s_own_and_case_folds_like_it():
    """The adapter must not have its own matching semantics.

    Same corpus, same terms, once through ``find_fact_leaks`` and once through
    ``core.observability.find_leaks`` directly - if these ever disagree, the rung
    has grown a second naive matcher that can drift from the audited one.
    """
    led = ledger(a=["Loose Flagstone"], b=["rope bridge"])
    text = "A LOOSE FLAGSTONE and a Rope Bridge"
    mine = {fid for fid, _ in facts.find_fact_leaks(text, led.secret_terms(),
                                                    led.entitled)}
    order = list(led.secret_terms())
    theirs = {order[i] for i, _ in find_leaks(
        text, {i: led.secret_terms()[f] for i, f in enumerate(order)},
        set(), facts.NO_VIEWER)}
    assert mine == theirs == {("a",), ("b",)}


def test_the_viewer_sentinel_is_not_a_fact_index():
    """``find_leaks`` skips ``seat == viewer``. If the sentinel were ever a real
    index, that fact would be exempt from every audit - silently."""
    led = ledger(a=["loose flagstone"])
    assert facts.NO_VIEWER not in range(len(led.facts))
    assert facts.find_fact_leaks("loose flagstone", led.secret_terms(),
                                 frozenset()) == [(("a",), "loose flagstone")]


def test_revealing_an_unknown_fact_raises_rather_than_passing_quietly():
    led = ledger(a=["x"])
    with pytest.raises(facts.FactError):
        led.reveal(("no", "such"))


def test_a_bare_string_is_refused_as_a_fact_id():
    """``tuple("R2")`` is ``("R", "2")``. Splatting it would produce a plausible
    "no such fact" for a caller whose only mistake was the shape."""
    led = ledger(a=["x"])
    with pytest.raises(facts.FactError, match="not the string"):
        led.reveal("a")


def test_colliding_terms_are_refused_because_the_remedy_is_a_rename():
    with pytest.raises(facts.FactError, match="collide"):
        facts.check_facts(ledger(a=["barrow-rats"], b=["three barrow-rats"]))


def texted(**entries) -> facts.FactLedger:
    """A hand-built set where each fact's TEXT is stated, not derived from its id."""
    return facts.FactLedger(
        facts={(fid,): facts.WorldFact((fid,), f"fact {fid}", tuple(terms), text)
               for fid, (terms, text) in entries.items()},
        revealed=set())


def test_a_term_inside_another_facts_text_is_refused():
    """The collision the pairwise term check cannot see.

    ``kernel.call_reveal`` publishes a fact's own text verbatim, so a text that
    carries another fact's sentinel makes declaring the first one write the
    second one's term into the transcript - and every later render is charged
    with a leak the referee could not have avoided. It is worse than a term
    collision because nothing in the term list shows it: it surfaces only at run
    time, attributed to a model that obeyed the rules.
    """
    led = texted(
        rats_room=(["barrow-rats"], "R3 Gallery: three barrow-rats on the far side."),
        rats_stats=(["ML 6"], "Three barrow-rats: Skill 2, ML 6."))
    with pytest.raises(facts.FactError, match="appears in"):
        facts.check_facts(led)


def test_the_text_check_does_not_fire_on_a_facts_own_text():
    """A term is expected to appear in the text of the fact it belongs to - that
    is what the kernel publishes when the fact is legally declared. A check that
    fired there would refuse every well-formed fact set."""
    led = texted(
        a=(["shallow cavity"], "A loose flagstone covers a shallow cavity."),
        b=(["rope bridge"], "R3 Gallery: an old rope bridge."))
    facts.check_facts(led)


def test_a_blank_term_is_refused_because_find_leaks_skips_it():
    with pytest.raises(facts.FactError, match="blank"):
        facts.check_facts(ledger(a=["   "]))


def test_a_fact_with_no_terms_cannot_be_audited():
    with pytest.raises(facts.FactError, match="no terms"):
        facts.check_facts(ledger(a=[]))


def test_no_shipped_term_appears_in_a_fresh_render(tmp_path):
    """The instrument control for the fact set: the opening context must be clean.

    A sentinel that is already present in the bytes every session starts with
    would report a leak on turn one of every run - which reads as a broken gate
    rather than as a badly chosen term.
    """
    from games.durf import session as session_mod

    sess = session_mod.new(seed=1)
    render = sess.render(0)
    assert sess.check(render) == []


def test_the_shipped_file_declares_the_scenario_it_belongs_to():
    """A fact set silently pointed at another dungeon would audit the wrong world."""
    raw = json.loads(facts.FACTS_FILE.read_text(encoding="utf-8"))
    scenario = json.loads(
        (facts.FACTS_FILE.parent / "scenario.json").read_text(encoding="utf-8"))
    assert raw["scenario_id"] == scenario["scenario_id"]


def test_a_facts_own_text_missing_its_term_is_refused():
    """The failure the pairwise and cross-text checks cannot see: a fact whose
    own statement never contains its own sentinel. ``kernel.call_reveal``
    publishes a fact's text verbatim and trusts the fixture to be well-formed -
    the matcher only ever scans a RENDER for a term, never a fact's own text
    against its own term, so this fact would go undeclared-and-unaudited
    forever: declaring it writes prose that carries no sentinel at all, and no
    later render check can see the fact "go" through its own reveal."""
    led = texted(a=(["shallow cavity"], "A loose flagstone covers a hidden pit."))
    with pytest.raises(facts.FactError, match="does not appear in its own text"):
        facts.check_facts(led)


def test_every_shipped_facts_own_text_contains_its_own_term():
    """The measured answer to 'unmeasured: whether fixtures/facts.json satisfies
    it' - checked directly against the raw fixture rather than only through
    ``load()``'s call to ``check_facts``, so a future loosening of the loader's
    checks cannot silently stop covering this fixture property."""
    led = facts.load()
    failures = [(fid, term, fact.text) for fid, fact in led.facts.items()
                for term in fact.terms
                if term.strip().lower() not in fact.text.lower()]
    assert failures == [], (
        f"facts whose own text lacks their own term: {failures}")
