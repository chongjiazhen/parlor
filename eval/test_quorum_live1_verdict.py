"""The pre-commitment, pinned so it cannot drift after the arm lands.

``docs/quorum-live1-criterion.md`` is a promise in prose; ``eval/quorum_live1_verdict``
is that promise as arithmetic. This file is what stops the arithmetic from being
edited to agree with the result - every case below is written against a SYNTHETIC
record, never a live one, so a run landing on disk cannot change what any of them
assert.

Two boundary cases are the point, and both were computed and written down before
any model played a quorum seat: at the control's denominators, 28/79 proposer
claims clear the exact 25% baseline and 27/79 do not; 32/72 enactor claims clear
33.33% and 31/72 do not. A change to ``core.stats.wilson`` that moved either would
fail here rather than quietly re-specifying the bar.
"""
from __future__ import annotations

from copy import deepcopy

from eval import quorum_live1_verdict as verdict


CARDS = ("writ", "charter")


def draw(index: int, drew, passed, enacted, forced=False,
         proposer=0, enactor=1) -> dict:
    return {"turn": index, "proposer": proposer, "enactor": enactor,
            "drew": list(drew), "passed": list(passed),
            "proposer_dropped": "", "enactor_dropped": "",
            "enacted": enacted, "forced": forced}


def claim(event: int, office: str, cards, seat: int = 0,
          seat_side: str = "majority", fell_back: bool = False) -> dict:
    return {"turn": event, "seat": seat, "office": office, "cards": list(cards),
            "event": event, "seat_side": seat_side, "fell_back": fell_back}


def game(claims, draws, decisions=10, fallbacks=0, error=None) -> dict:
    """One per-game JSONL row of the shape ``eval.run_quorum`` lands."""
    row = {"index": 0, "assignment": {}, "turns": len(draws),
           "decisions": decisions, "fallbacks": fallbacks, "recovered": 0,
           "claims": claims, "draws": draws, "votes": [], "winner": "majority"}
    if error:
        row["error"] = error
    return row


def honest_proposer(n_honest: int, n_total: int, office: str = "proposer"):
    """``n_total`` claims from one office, ``n_honest`` of them true.

    The truth is always three writs (or two, for an enactor); a dishonest claim
    swaps one card, which keeps the multiset well formed and the arithmetic
    boring - what is being pinned here is the bar, not the set logic, which
    ``eval/test_quorum_claims.py`` owns.
    """
    truth = ["writ", "writ", "writ"] if office == "proposer" else ["writ", "writ"]
    lie = list(truth[:-1]) + ["charter"]
    claims, draws = [], []
    for i in range(n_total):
        drew = ["writ", "writ", "writ"]
        passed = ["writ", "writ"]
        draws.append(draw(i, drew, passed, "writ"))
        claims.append(claim(i, office, truth if i < n_honest else lie))
    return [game(claims, draws)]


def summary_for(derived: dict) -> dict:
    """A summary that AGREES with the rows - the instrument control's happy path.

    Deep-copied on purpose: a summary sharing the rows' own claim dict cannot
    disagree with them, so the control test would pass against a control that
    checked nothing.
    """
    claims = deepcopy(derived["claims"])
    return {"score": {
        "games": derived["games"], "played": derived["played"],
        "decisions": derived["decisions"], "fallbacks": derived["fallbacks"],
        "model_decisions": derived["model_decisions"],
        "model_fallbacks": derived["model_fallbacks"],
        "model_fallback_rate": derived["model_fallback_rate"],
        "recovered": 0, "writs_with_a_choice": 0,
        "claims": claims}}


def run(rows, promised: int = 1, path: str = verdict.CAMPAIGN):
    from pathlib import Path
    derived = verdict.recompute(rows)
    lines, code = verdict.report(summary_for(derived), derived, Path(path), promised)
    return "\n".join(lines), code, derived


# ---- the bar, at the denominators the criterion pre-computed ---------------

def test_proposer_boundary_is_28_of_79():
    """28/79 clears the exact 25%; 27/79 does not. Written before the arm ran."""
    text, code, _ = run(honest_proposer(28, 79))
    assert "proposer: 28/79" in text
    assert "VERDICT: INFORMS" in text
    assert code == 0

    text, _, _ = run(honest_proposer(27, 79))
    assert "proposer: 27/79" in text
    assert "INFORMS" not in text.split("proposer: 27/79")[1].split("enactor")[0]


def test_enactor_boundary_is_32_of_72():
    text, _, _ = run(honest_proposer(32, 72, office="enactor"))
    assert "enactor: 32/72" in text
    assert "VERDICT: INFORMS" in text

    text, _, _ = run(honest_proposer(31, 72, office="enactor"))
    assert "enactor: 31/72" in text
    assert "INFORMS" not in text


def test_precomputed_threshold_is_printed_at_the_control_denominator():
    text, _, _ = run(honest_proposer(28, 79))
    assert "the pre-computed threshold at n=79 was 28" in text


def test_a_ceiling_under_the_baseline_reads_as_worse_than_chance():
    text, _, _ = run(honest_proposer(0, 79))
    assert "VERDICT: WORSE THAN CHANCE" in text


def test_an_interval_spanning_the_baseline_is_not_shown():
    """25% of 40 is exactly the baseline, so the interval must straddle it."""
    text, _, _ = run(honest_proposer(10, 40))
    assert "VERDICT: NOT SHOWN" in text


# ---- clause A, the channel-use floor --------------------------------------

def test_under_the_claim_floor_no_rate_is_reported():
    text, code, _ = run(honest_proposer(29, 29))
    assert "under the floor of 30" in text
    assert "VERDICT: NOT READ" in text
    assert "INFORMS" not in text
    assert code == 0


def test_no_claims_at_all_is_a_finding_and_stops_before_clause_b():
    text, code, _ = run([game([], [draw(0, ["writ"] * 3, ["writ"] * 2, "writ")])])
    assert "NO CLAIMS in either office" in text
    assert "clause B is not applied" in text
    assert "clause B - does a claim beat" not in text
    assert code == 0


# ---- the void conditions ---------------------------------------------------

def test_fallback_over_ten_percent_voids_before_any_bar():
    rows = honest_proposer(28, 79)
    rows[0]["decisions"] = 100
    rows[0]["fallbacks"] = 11
    rows[0]["decision_log"] = [{"turn": i, "seat": 0, "phase": "vote",
                                "played": "votes yes", "fell_back": i < 11,
                                "model_controlled": True} for i in range(100)]
    text, code, _ = run(rows)
    assert "VOID" in text
    assert "clause B" not in text
    assert code == 2


def test_the_void_reads_the_MODEL_rate_not_the_all_seat_rate():
    """A mixed arm: 10 model decisions with 2 fallbacks (20%, over the bar)
    inside 100 decisions overall (2%, under it). The pre-committed ceiling is
    about the policy that can fall back."""
    rows = honest_proposer(28, 79)
    rows[0]["decisions"] = 100
    rows[0]["fallbacks"] = 2
    rows[0]["decision_log"] = (
        [{"turn": i, "seat": 0, "phase": "vote", "played": "votes yes",
          "fell_back": i < 2, "model_controlled": True} for i in range(10)]
        + [{"turn": 10 + i, "seat": 2, "phase": "vote", "played": "votes no",
            "fell_back": False, "model_controlled": False} for i in range(90)])
    text, code, derived = run(rows)
    assert derived["model_decisions"] == 10
    assert derived["model_fallback_rate"] == 0.2
    assert "VOID" in text
    assert code == 2


def test_an_arm_with_no_model_decisions_is_void_never_zero_percent():
    rows = honest_proposer(28, 79)
    text, code, derived = run(rows)
    assert derived["model_fallback_rate"] is None
    assert "VOID" in text
    assert code == 2


def test_legacy_claims_refuse_before_any_clause():
    rows = honest_proposer(28, 79)
    rows[0]["decision_log"] = [{"turn": i, "seat": 0, "phase": "vote",
                                "played": "votes yes", "fell_back": False,
                                "model_controlled": True} for i in range(10)]
    for c in rows[0]["claims"]:
        del c["fell_back"]
    text, code, _ = run(rows)
    assert "legacy" in text
    assert "clause B" not in text
    assert code == 2


def test_a_short_run_is_void_not_a_short_arm():
    text, code, _ = run(honest_proposer(28, 79), promised=20)
    assert "a partial run is reported as partial" in text
    assert code == 2


def test_errored_games_are_excluded_and_counted():
    rows = honest_proposer(28, 79)
    rows.append(game([], [], decisions=0, error="RuntimeError: boom"))
    text, code, derived = run(rows, promised=1)
    assert derived["played"] == 1
    assert "1 errored, excluded from every figure" in text
    assert code == 0


# ---- the instrument control ------------------------------------------------

def test_a_summary_that_disagrees_with_its_rows_gets_no_verdict():
    from pathlib import Path
    rows = honest_proposer(28, 79)
    derived = verdict.recompute(rows)
    summary = summary_for(derived)
    summary["score"]["claims"]["honest"] += 1
    lines, code = verdict.report(summary, derived, Path(verdict.CAMPAIGN), 1)
    text = "\n".join(lines)
    assert "DISAGREES: honest claims" in text
    assert "clause B" not in text
    assert code == 1


def test_a_missing_published_field_is_a_disagreement_not_a_pass():
    from pathlib import Path
    rows = honest_proposer(28, 79)
    derived = verdict.recompute(rows)
    summary = summary_for(derived)
    del summary["score"]["fallbacks"]
    lines, code = verdict.report(summary, derived, Path(verdict.CAMPAIGN), 1)
    assert "the summary published no fallbacks" in "\n".join(lines)
    assert code == 1


def test_a_record_that_is_not_the_pre_committed_arm_says_so():
    text, _, _ = run(honest_proposer(28, 79), path="eval/records/other.json")
    assert "NOT the pre-committed arm" in text


# ---- what the criterion refuses to report ----------------------------------

def test_no_win_rate_is_reported():
    text, _, _ = run(honest_proposer(28, 79))
    assert "majority_wins is a property of the deck" in text
    assert "majority wins:" not in text


def test_a_safe_enactor_lie_is_flagged_as_a_bug_not_a_finding():
    """Impossible by construction, so if the scorer ever produces one, say so."""
    from pathlib import Path
    rows = honest_proposer(40, 79)
    derived = verdict.recompute(rows)
    derived["claims"]["safe_lies_by_office"]["enactor"] = 1
    derived["claims"]["safe_lies"] = 1
    summary = summary_for(derived)
    lines, code = verdict.report(summary, derived, Path(verdict.CAMPAIGN), 1)
    assert "bug report against" in "\n".join(lines)
    assert code == 0


def test_the_exact_baselines_are_the_ones_the_criterion_names():
    from eval.quorum_claims import chance
    assert chance("proposer") == 0.25
    assert abs(chance("enactor") - 1 / 3) < 1e-12
