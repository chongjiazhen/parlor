"""Tests for the pre-committed Belfry model-adjudicator arm."""

from __future__ import annotations

import copy
import random
import shlex
import unittest
from pathlib import Path

from eval.belfry_adjudicator_verdict import (
    ARMS,
    Trace,
    V2_CONTROL_ARGS,
    V2_MODEL_ARGS,
    feature,
    held_out_accuracy,
    report,
    resolve,
    split_traces,
)
from games.belfry.roles import Align, COMPACT, ROLES
from games.belfry.state import deal


SEEDS = range(6100, 6160)


def _launcher_recipes() -> dict[str, dict]:
    """Derive each run_belfry argv from the frozen Windows launcher."""
    lines = (Path(__file__).parent / "runs" / "belfry-adjudicator.cmd").read_text(
        encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    for line in lines:
        if line.lower().startswith('set "') and line.endswith('"'):
            name, value = line[5:-1].split("=", 1)
            values[name] = value

    def expand(value: str) -> str:
        for _ in values:
            for name, replacement in values.items():
                value = value.replace(f"%{name}%", replacement)
        return value

    recipes = {}
    for index, line in enumerate(lines):
        if not line.startswith("py -3 -m eval.run_belfry "):
            continue
        command = line
        next_index = index
        while command.rstrip().endswith("^"):
            next_index += 1
            command = command.rstrip()[:-1] + " " + lines[next_index].strip()
        tokens = shlex.split(command.split(">>", 1)[0])
        args: dict[str, object] = {}
        cursor = tokens.index("eval.run_belfry") + 1
        while cursor < len(tokens):
            option = tokens[cursor]
            cursor += 1
            key = option.removeprefix("--").replace("-", "_")
            if option == "--no-thinking":
                args[key] = True
                continue
            args[key] = expand(tokens[cursor])
            cursor += 1
        for key in ("games", "seats", "rounds", "seed"):
            args[key] = int(args[key])
        args["timeout"] = float(args.get("timeout", 120.0))
        recipes[args["adjudicator"]] = args
    return recipes


def _args(adjudicator: str) -> dict:
    return {
        "games": 60,
        "arm": "random",
        "seats": 5,
        "script": "compact",
        "backend": None,
        "model": "auto",
        "rounds": 1,
        "max_days": 12,
        "register": "character",
        "retries": 2,
        "temperature": 0.8,
        "max_tokens": 1536,
        "timeout": 120.0,
        "no_thinking": True,
        "seed": 6100,
        "adjudicator": adjudicator,
        "adjudicator_backend": "local" if adjudicator == "model" else None,
        "adjudicator_model": (
            "qwen36-35b-a3b-iq3" if adjudicator == "model" else None
        ),
        "adjudicator_temperature": 0.0 if adjudicator == "model" else None,
        "out": (
            "eval/records/belfry-adjudicator-model.json"
            if adjudicator == "model"
            else "eval/records/belfry-adjudicator-control.json"
        ),
    }


def _deal_row(seed: int) -> tuple[dict, object]:
    grim = deal(5, COMPACT, random.Random(seed))
    return ({
        "index": seed - 6100,
        "dealt": {str(s.index): s.dealt.key for s in grim.seats},
        "log": list(grim.log),
        "decisions": 10,
        "fallbacks": 0,
        "error": None,
        "adjudicator": None,
    }, grim)


def _arm(adjudicator: str, *, model_rank: int | None = None,
         adjudicator_fallbacks: int = 0,
         adjudicator_recovered: int = 0) -> tuple[dict, list[dict]]:
    rows = []
    events_seen = 0
    recovered_left = adjudicator_recovered
    for seed in SEEDS:
        row, grim = _deal_row(seed)
        if adjudicator == "model" and grim.find_believer("diviner") is not None:
            options = [str(s.index) for s in grim.seats if s.align is Align.GOOD]
            selected = options[(model_rank or 0) % len(options)]
            fallback = events_seen < adjudicator_fallbacks
            recovered = not fallback and recovered_left > 0
            recovered_left -= int(recovered)
            event = {
                "key": "herring_registration",
                "options": options,
                "selected": selected,
                "fallback": fallback,
                "recovered": recovered,
                "upstream": None if fallback else "qwen36-35b-a3b-iq3",
            }
            row["adjudicator"] = {
                "calls": 1,
                "fallbacks": int(fallback),
                "recovered": int(recovered),
                "events": [event],
                "upstreams": {} if fallback else {"qwen36-35b-a3b-iq3": 1},
            }
            row["log"] = [line for line in row["log"]
                          if "reads as the demon to the diviner" not in line]
            row["log"].append(
                f"discretion: seat {selected} reads as the demon to the "
                "diviner all game")
            events_seen += 1
        rows.append(row)

    decisions = sum(row["decisions"] for row in rows)
    fallbacks = sum(row["fallbacks"] for row in rows)
    adjudicator_calls = sum(
        (row["adjudicator"] or {}).get("calls", 0) for row in rows)
    adjudicator_falls = sum(
        (row["adjudicator"] or {}).get("fallbacks", 0) for row in rows)
    adjudicator_recovers = sum(
        (row["adjudicator"] or {}).get("recovered", 0) for row in rows)
    score = {
        "games_requested": 60,
        "games_completed": 60,
        "integrity": {
            "decisions": decisions,
            "fallbacks": fallbacks,
            "fallback_rate": fallbacks / decisions,
        },
        "adjudicator_integrity": None,
    }
    if adjudicator == "model":
        score["adjudicator_integrity"] = {
            "calls": adjudicator_calls,
            "fallbacks": adjudicator_falls,
            "fallback_rate": adjudicator_falls / adjudicator_calls,
            "recovered": adjudicator_recovers,
            "upstreams": {
                "qwen36-35b-a3b-iq3": adjudicator_calls - adjudicator_falls,
            },
        }
    return {"args": _args(adjudicator), "score": score}, rows


def _set_player_fallbacks(evidence: tuple[dict, list[dict]], count: int) -> None:
    summary, rows = evidence
    for row in rows:
        row["fallbacks"] = 0
    left = count
    for row in rows:
        take = min(left, row["decisions"])
        row["fallbacks"] = take
        left -= take
    summary["score"]["integrity"]["fallbacks"] = count
    decisions = summary["score"]["integrity"]["decisions"]
    summary["score"]["integrity"]["fallback_rate"] = count / decisions


class TestFallbackVoids(unittest.TestCase):
    def test_adjudicator_fallback_over_ten_percent_voids_arm(self):
        lines, code = report(_arm("random"),
                             _arm("model", adjudicator_fallbacks=3))
        self.assertEqual(code, 2)
        self.assertTrue(any("VOID" in line for line in lines))

    def test_exactly_ten_percent_adjudicator_fallback_is_not_void(self):
        lines, code = report(_arm("random"),
                             _arm("model", adjudicator_fallbacks=2))
        self.assertEqual(code, 0)
        self.assertTrue(any("2/20 = 10.00%" in line for line in lines))

    def test_each_player_arm_has_its_own_fallback_void(self):
        for side in (0, 1):
            with self.subTest(side=side):
                evidence = [_arm("random"), _arm("model")]
                _set_player_fallbacks(evidence[side], 61)
                lines, code = report(*evidence)
                self.assertEqual(code, 2)
                self.assertTrue(any("player fallback" in line and "VOID" in line
                                    for line in lines))

    def test_exactly_ten_percent_player_fallback_is_not_void(self):
        control, model = _arm("random"), _arm("model")
        _set_player_fallbacks(control, 60)
        _set_player_fallbacks(model, 60)
        self.assertEqual(report(control, model)[1], 0)


class TestEvidenceBoundary(unittest.TestCase):
    def test_duplicate_game_seed_voids(self):
        control, model = _arm("random"), _arm("model")
        model[1][-1]["index"] = model[1][0]["index"]
        lines, code = report(control, model)
        self.assertEqual(code, 2)
        self.assertTrue(any("duplicate game seed" in line for line in lines))

    def test_paired_deals_must_match(self):
        control, model = _arm("random"), _arm("model")
        model[1][0]["dealt"]["0"], model[1][0]["dealt"]["1"] = (
            model[1][0]["dealt"]["1"], model[1][0]["dealt"]["0"])
        lines, code = report(control, model)
        self.assertEqual(code, 2)
        self.assertTrue(any("paired deals differ" in line for line in lines))

    def test_model_seed_with_a_choice_requires_provenance(self):
        control, model = _arm("random"), _arm("model")
        row = next(row for row in model[1] if row["adjudicator"])
        row["adjudicator"] = None
        integrity = model[0]["score"]["adjudicator_integrity"]
        integrity["calls"] -= 1
        integrity["upstreams"]["qwen36-35b-a3b-iq3"] -= 1
        integrity["fallback_rate"] = integrity["fallbacks"] / integrity["calls"]
        lines, code = report(control, model)
        self.assertEqual(code, 2)
        self.assertTrue(any("missing adjudicator provenance" in line
                            for line in lines))

    def test_classifier_rejects_a_source_label_in_event_input(self):
        control, model = _arm("random"), _arm("model")
        event = next(row["adjudicator"]["events"][0] for row in model[1]
                     if row["adjudicator"])
        event["source"] = "model"
        lines, code = report(control, model)
        self.assertEqual(code, 2)
        self.assertTrue(any("classifier input leakage" in line for line in lines))

    def test_classifier_rejects_free_form_response_text(self):
        control, model = _arm("random"), _arm("model")
        event = next(row["adjudicator"]["events"][0] for row in model[1]
                     if row["adjudicator"])
        event["response_text"] = "I chose the first seat"
        self.assertEqual(report(control, model)[1], 2)

    def test_summary_disagreement_is_corrupt_evidence(self):
        control, model = _arm("random"), _arm("model")
        model[0]["score"]["integrity"]["decisions"] += 1
        self.assertEqual(report(control, model)[1], 1)

    def test_a_recovered_choice_reads_through_and_is_reported(self):
        """Until 2026-09-01 the adjudicator held ``recovered`` at a literal False,
        so this whole path was 0 == 0 on every record ever written and could not
        fail. The rate is printed BESIDE the fallback rate, never folded into it:
        a recovered choice is the model's own, and it did not come for free."""
        control, model = _arm("random"), _arm("model", adjudicator_recovered=4)

        lines, code = report(control, model)

        self.assertEqual(code, 0)
        self.assertTrue(any("adjudicator recovered: 4/20" in line
                            for line in lines))

    def test_a_recovered_count_disagreeing_with_its_events_is_corrupt(self):
        control, model = _arm("random"), _arm("model", adjudicator_recovered=4)
        row = next(row for row in model[1]
                   if row["adjudicator"] and row["adjudicator"]["recovered"])
        row["adjudicator"]["recovered"] = 0

        lines, code = report(control, model)

        self.assertEqual(code, 1)
        self.assertTrue(any("recovered count disagrees with events" in line
                            for line in lines))

    def test_a_summary_recovered_total_the_rows_do_not_carry_is_corrupt(self):
        control, model = _arm("random"), _arm("model", adjudicator_recovered=4)
        model[0]["score"]["adjudicator_integrity"]["recovered"] = 7

        self.assertEqual(report(control, model)[1], 1)

    def test_adjudicator_upstream_census_must_match_events(self):
        control, model = _arm("random"), _arm("model")
        row = next(row for row in model[1] if row["adjudicator"])
        row["adjudicator"]["upstreams"] = {}
        self.assertEqual(report(control, model)[1], 1)

    def test_partial_arm_is_void_not_a_short_read(self):
        control, model = _arm("random"), _arm("model")
        model[1].pop()
        score = model[0]["score"]
        score["games_requested"] = 59
        score["games_completed"] = 59
        score["integrity"]["decisions"] -= 10
        self.assertEqual(report(control, model)[1], 2)


class TestRecipeBinding(unittest.TestCase):
    def test_v2_criterion_binds_fresh_record_paths(self):
        control, model = _arm("random"), _arm("model")
        control[0]["args"].update(V2_CONTROL_ARGS)
        model[0]["args"].update(V2_MODEL_ARGS)
        lines, code = report(
            control, model, control_args=V2_CONTROL_ARGS,
            model_args=V2_MODEL_ARGS,
            criterion_path="docs/belfry-adjudicator-v2-criterion.md")
        self.assertEqual(code, 0, "\n".join(lines))
        self.assertIn("v2", lines[1])

    def test_launcher_emits_a_recipe_bound_by_controller(self):
        """A launcher timeout or output spelling that differs from the criterion fails."""
        recipes = _launcher_recipes()
        self.assertEqual(set(recipes), {"random", "model"})
        control, model = _arm("random"), _arm("model")
        control[0]["args"].update(recipes["random"])
        model[0]["args"].update(recipes["model"])
        lines, code = report(control, model)
        self.assertEqual(code, 0, "\n".join(lines))

    def test_recipe_mismatch_has_its_own_exit(self):
        control, model = _arm("random"), _arm("model")
        model[0]["args"]["script"] = "full"
        lines, code = report(control, model)
        self.assertEqual(code, 3)
        self.assertTrue(any("NOT this criterion" in line for line in lines))

    def test_max_days_is_part_of_the_exact_recipe(self):
        control, model = _arm("random"), _arm("model")
        model[0]["args"]["max_days"] = 11
        self.assertEqual(report(control, model)[1], 3)

    def test_output_path_is_part_of_the_exact_recipe(self):
        control, model = _arm("random"), _arm("model")
        model[0]["args"]["out"] = "eval/records/other.json"
        self.assertEqual(report(control, model)[1], 3)

    def test_adjudicator_temperature_mismatch_is_not_this_criterion(self):
        control, model = _arm("random"), _arm("model")
        model[0]["args"]["adjudicator_temperature"] = 0.9
        self.assertEqual(report(control, model)[1], 3)


class TestAdjudicatorProvenance(unittest.TestCase):
    def test_successful_event_requires_the_committed_model_identity(self):
        control, model = _arm("random"), _arm("model")
        for row in model[1]:
            if row["adjudicator"]:
                row["adjudicator"]["events"][0]["upstream"] = "wrong-model"
                row["adjudicator"]["upstreams"] = {"wrong-model": 1}
        model[0]["score"]["adjudicator_integrity"]["upstreams"] = {
            "wrong-model": 20,
        }
        self.assertEqual(report(control, model)[1], 2)

    def test_fallback_event_carries_no_upstream_identity(self):
        control, model = _arm("random"), _arm("model", adjudicator_fallbacks=1)
        row = next(row for row in model[1]
                   if row["adjudicator"] and row["adjudicator"]["fallbacks"])
        row["adjudicator"]["events"][0]["upstream"] = "qwen36-35b-a3b-iq3"
        row["adjudicator"]["upstreams"] = {"qwen36-35b-a3b-iq3": 1}
        summary = model[0]["score"]["adjudicator_integrity"]
        summary["upstreams"] = {"qwen36-35b-a3b-iq3": 20}
        self.assertEqual(report(control, model)[1], 2)


class TestHeldOutClassifier(unittest.TestCase):
    def test_feature_cannot_see_source_or_seed(self):
        random_trace = Trace(6100, "random", "herring_registration", 3, 0)
        model_trace = Trace(6159, "model", "herring_registration", 3, 0)
        self.assertEqual(feature(random_trace), feature(model_trace))

    def test_train_and_test_game_seeds_are_disjoint(self):
        traces = [
            Trace(seed, source, "herring_registration", 3, seed % 3)
            for seed in range(6100, 6104)
            for source in ("random", "model")
        ]
        train, test = split_traces(traces)
        self.assertTrue({trace.seed for trace in train}.isdisjoint(
            {trace.seed for trace in test}))

    def test_source_discrimination_fixture(self):
        traces = []
        for seed in range(6100, 6120):
            traces.append(Trace(seed, "model", "herring_registration", 3, 0))
            traces.append(Trace(seed, "random", "herring_registration", 3,
                                seed % 3))
        self.assertGreater(held_out_accuracy(traces), 0.75)

    def test_non_void_report_prints_rates_and_control_na(self):
        lines, code = report(_arm("random"), _arm("model", model_rank=0))
        self.assertEqual(code, 0)
        self.assertTrue(any("control adjudicator fallback: n/a" in line
                            for line in lines))
        self.assertTrue(any("model adjudicator fallback:" in line
                            for line in lines))
        self.assertTrue(any("source accuracy" in line for line in lines))


class TestArmBinding(unittest.TestCase):
    """One switch moves the record paths and the expected settings together.

    The bug: --v2 switched the expected args and the criterion document while the
    positional defaults stayed on v1, so a bare --v2 scored the V1 RECORDS against
    the v2 promise and printed a criterion violation. Every assertion below on a
    v2 path fails against that code, which is what makes them worth having.
    """

    def test_bare_v2_flag_resolves_the_v2_records(self):
        arm, control, model = resolve(["--v2"])
        self.assertEqual(control, Path("eval/records/belfry-adjudicator-v2-control.json"))
        self.assertEqual(model, Path("eval/records/belfry-adjudicator-v2-model.json"))
        self.assertIs(arm, ARMS["v2"])

    def test_bare_criterion_v2_resolves_the_v2_records(self):
        self.assertEqual(resolve(["--criterion", "v2"])[1:], resolve(["--v2"])[1:])

    def test_default_is_v1_and_unchanged(self):
        arm, control, model = resolve([])
        self.assertEqual(control, Path("eval/records/belfry-adjudicator-control.json"))
        self.assertEqual(model, Path("eval/records/belfry-adjudicator-model.json"))
        self.assertIs(arm, ARMS["v1"])

    def test_the_paths_and_the_expected_args_never_half_move(self):
        """The whole point of the binding: args agree with the paths they score."""
        for name in ARMS:
            with self.subTest(arm=name):
                arm, control, model = resolve(["--criterion", name])
                self.assertEqual(Path(arm["control_args"]["out"]), control)
                self.assertEqual(Path(arm["model_args"]["out"]), model)

    def test_explicit_positionals_still_win(self):
        """The tool is pointed at ad-hoc records by hand and must keep working."""
        arm, control, model = resolve(["--v2", "a.json", "b.json"])
        self.assertEqual((control, model), (Path("a.json"), Path("b.json")))
        self.assertIs(arm, ARMS["v2"])

    def test_the_tracked_v2_recipe_still_parses(self):
        """eval/runs/belfry-adjudicator-v2.cmd:35 spells it this way, and
        docs/slices.md cites the same line as the arithmetic behind S8b."""
        arm, control, model = resolve([
            "eval/records/belfry-adjudicator-v2-control.json",
            "eval/records/belfry-adjudicator-v2-model.json",
            "--v2",
        ])
        self.assertIs(arm, ARMS["v2"])
        self.assertEqual(control.name, "belfry-adjudicator-v2-control.json")


if __name__ == "__main__":
    unittest.main()
