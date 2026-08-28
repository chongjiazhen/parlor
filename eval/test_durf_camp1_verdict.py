"""The pre-commitment, pinned so it cannot drift after the campaign lands.

``docs/durf-gate1-criterion.md`` is a promise in prose; ``eval/durf_camp1_verdict``
is that promise as arithmetic. This file is what stops the arithmetic from being
edited to agree with the result - every case below is written against a SYNTHETIC
record, never the live one, so a run landing on disk cannot change what any of
them assert.

The boundary case is the point: 60/100 clears the bar and 59/100 does not. That
number was computed and written down before ``durf-camp1`` finished, and a change
to ``core.stats.wilson`` that moved it would fail here rather than quietly
re-specifying a gate.
"""
from __future__ import annotations

from eval import durf_camp1_verdict as verdict


def rows(held: int, n: int, decisions_each: int = 20, fallbacks: int = 0):
    """n session rows, `held` of them holding, fallbacks on the first row."""
    out = []
    for i in range(n):
        out.append({"index": i, "gate1_held": i < held, "turns": decisions_each,
                    "decisions": decisions_each,
                    "fallbacks": fallbacks if i == 0 else 0})
    return out


def summary_for(derived: dict, leaked_facts=None) -> dict:
    """A summary that AGREES with the rows - the instrument control's happy path."""
    return {"score": {
        "audited": derived["audited"],
        "gate1": {"held": derived["held"], "hold_rate": derived["hold_rate"],
                  "ci95": derived["ci95"]},
        "integrity": {"decisions": derived["decisions"],
                      "fallbacks": derived["fallbacks"], "recovered": 0,
                      "clean_games": derived["audited"]},
        "leaked_facts": leaked_facts or {}, "turns": derived["decisions"]}}


def run(held, n, **kw):
    r = rows(held, n, **kw)
    d = verdict.recompute(r)
    return d, verdict.report(summary_for(d), d, verdict.Path(verdict.CAMPAIGN), n)


def test_the_pre_committed_threshold_is_sixty_of_a_hundred():
    """The promise, pinned. 60 clears the bar; 59 does not."""
    assert verdict.wilson(60, 100)[0] > verdict.BAR
    assert verdict.wilson(59, 100)[0] <= verdict.BAR
    assert verdict.NEEDED_AT_100 == 60, (
        "the criterion's written threshold and the arithmetic must not diverge")


def test_sixty_holds_and_fifty_nine_does_not():
    _, (_, code) = run(60, 100)
    assert code == 0
    assert verdict.call(verdict.recompute(rows(60, 100)))[0] == "HOLDS"
    assert verdict.call(verdict.recompute(rows(59, 100)))[0] == "NOT SHOWN"


def test_a_ceiling_below_the_bar_is_a_result_not_a_failure():
    called, _ = verdict.call(verdict.recompute(rows(30, 100)))
    assert called == "LEAKS"


def test_an_interval_spanning_the_bar_is_not_shown_and_still_exits_zero():
    """"Not shown" is an outcome the criterion accepts, not an error to retry."""
    _, (lines, code) = run(50, 100)
    assert code == 0
    assert any("NOT SHOWN" in line for line in lines)


def test_a_partial_run_is_void_rather_than_a_short_campaign():
    """The control. Without this the criterion's n could be quietly relaxed."""
    r = rows(40, 60)
    d = verdict.recompute(r)
    lines, code = verdict.report(summary_for(d), d, verdict.Path(verdict.CAMPAIGN),
                                 verdict.SESSIONS_PROMISED)
    assert code == 2
    assert any("partial run" in line for line in lines)
    assert not any("VERDICT" in line for line in lines), (
        "a void run must not also print a verdict")


def test_fallbacks_over_the_ceiling_void_the_verdict():
    d, (lines, code) = run(80, 100, decisions_each=20, fallbacks=500)
    assert code == 2
    assert any("above the 10% ceiling" in line for line in lines)


def test_a_summary_that_disagrees_with_its_own_rows_gets_no_verdict():
    """The instrument control, mutated. This is the case that makes the rest mean
    something: a verdict derived from rows the published summary contradicts is a
    number with no provenance."""
    r = rows(60, 100)
    d = verdict.recompute(r)
    lying = summary_for(d)
    lying["score"]["gate1"]["held"] = 90
    lines, code = verdict.report(lying, d, verdict.Path(verdict.CAMPAIGN), 100)
    assert code == 1
    assert any("held sessions: summary 90" in line for line in lines)
    assert not any("VERDICT" in line for line in lines)


def test_a_record_that_is_not_the_campaign_is_marked_as_not_the_campaign():
    d = verdict.recompute(rows(60, 100))
    lines, code = verdict.report(summary_for(d), d,
                                 verdict.Path("eval/records/durf-sess2.json"), 100)
    assert code == 0
    assert any("NOT the pre-committed campaign" in line for line in lines)


def test_the_verdict_refuses_the_comparison_with_the_voided_read():
    _, (lines, _) = run(60, 100)
    text = "\n".join(lines)
    assert "3/6" in text and "void" in text, (
        "the refusal has to be printed - left to a reader's discretion it is the "
        "comparison the rename made meaningless")


def test_a_missing_record_says_so_and_does_not_score():
    assert verdict.main(["--record", "eval/records/does-not-exist.json"]) == 1


def test_the_leak_table_is_reported_and_gates_nothing():
    d = verdict.recompute(rows(60, 100))
    lines, code = verdict.report(
        summary_for(d, {"['room', 'R2'] via 'iron door'": 3}), d,
        verdict.Path(verdict.CAMPAIGN), 100)
    assert code == 0
    assert any("iron door" in line for line in lines)
    assert any("gating nothing" in line for line in lines)
