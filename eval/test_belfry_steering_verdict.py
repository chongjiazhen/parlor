"""Tests for the pre-committed Belfry steered-discretion arm (S23).

No record exists yet, so every arm here is synthetic. What the tests hold is the
part a record cannot: that the scorer reads a rule-follower as STEERED, a
position prior as NOT SHOWN, and refuses everything else.
"""

from __future__ import annotations

import copy
import random
import shlex
import unittest
from pathlib import Path

from eval.belfry_steering_verdict import (
    ARMS,
    CONTROL_ARGS,
    FIRST_SEED,
    LAST_SEED,
    STEERED_ARGS,
    offered_order,
    report,
    resolve,
)
from games.belfry.adjudicator import preferred_herring
from games.belfry.roles import Align, COMPACT, Team
from games.belfry.state import deal


SEEDS = range(FIRST_SEED, LAST_SEED + 1)
MODEL = "qwen36-35b-a3b-iq3"


def _launcher_recipes() -> dict[str, dict]:
    """Derive each run_belfry argv from the frozen Windows launcher, so the
    recipe on disk and the criterion in the scorer cannot drift apart."""
    lines = (Path(__file__).parent / "runs" / "belfry-steering.cmd").read_text(
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
            if option in ("--no-thinking", "--adjudicator-steer"):
                args[key] = True
                continue
            args[key] = expand(tokens[cursor])
            cursor += 1
        for key in ("games", "seats", "rounds", "seed"):
            args[key] = int(args[key])
        args["timeout"] = float(args.get("timeout", 120.0))
        recipes[args["adjudicator"]] = args
    return recipes


def _board(seed: int):
    """Deal, offered menu, the rule's answer, and the seeded-random outcome."""
    grim = deal(5, COMPACT, random.Random(seed))
    if grim.find_believer("diviner") is None:
        return grim, (), None, None
    good = [s.index for s in grim.seats if s.align is Align.GOOD]
    demon = next(s.index for s in grim.seats if s.role.team is Team.DEMON)
    options = offered_order(seed, [str(s) for s in good])
    return (grim, options, str(preferred_herring(5, demon, good)),
            str(grim.herring))


def _args(adjudicator: str) -> dict:
    return copy.deepcopy(
        STEERED_ARGS if adjudicator == "model" else CONTROL_ARGS)


def _arm(adjudicator: str, *, policy: str = "rule",
         adjudicator_fallbacks: int = 0) -> tuple[dict, list[dict]]:
    """One synthetic campaign. ``policy`` is how the steered model chooses:
    ``rule`` follows the stated rule, ``first`` always takes the first option it
    is offered - the position prior the seeded menu order exists to defeat."""
    rows, events_seen = [], 0
    for seed in SEEDS:
        grim, options, preferred, random_selected = _board(seed)
        row = {
            "index": seed - FIRST_SEED,
            "dealt": {str(s.index): s.dealt.key for s in grim.seats},
            "log": list(grim.log),
            "decisions": 10,
            "fallbacks": 0,
            "error": None,
            "adjudicator": None,
        }
        if adjudicator == "model" and random_selected is not None:
            fallback = events_seen < adjudicator_fallbacks
            selected = preferred if policy == "rule" else options[0]
            if fallback:
                selected = random_selected
            row["adjudicator"] = {
                "calls": 1,
                "fallbacks": int(fallback),
                "recovered": 0,
                "events": [{
                    "key": "herring_registration",
                    "options": list(options),
                    "selected": selected,
                    "fallback": fallback,
                    "recovered": False,
                    "upstream": None if fallback else MODEL,
                }],
                "upstreams": {} if fallback else {MODEL: 1},
            }
            row["log"] = [line for line in row["log"]
                          if "reads as the demon to the diviner" not in line]
            row["log"].append(
                f"discretion: seat {selected} reads as the demon to the "
                "diviner all game")
            events_seen += 1
        rows.append(row)

    decisions = sum(row["decisions"] for row in rows)
    calls = sum((row["adjudicator"] or {}).get("calls", 0) for row in rows)
    falls = sum((row["adjudicator"] or {}).get("fallbacks", 0) for row in rows)
    score = {
        "games_requested": len(rows),
        "games_completed": len(rows),
        "integrity": {"decisions": decisions, "fallbacks": 0,
                      "fallback_rate": 0.0},
        "adjudicator_integrity": None,
    }
    if adjudicator == "model":
        score["adjudicator_integrity"] = {
            "calls": calls,
            "fallbacks": falls,
            "fallback_rate": falls / calls,
            "recovered": 0,
            "upstreams": {MODEL: calls - falls},
        }
    return {"args": _args(adjudicator), "score": score}, rows


class TestVerdict(unittest.TestCase):
    def test_a_rule_follower_reads_steered(self):
        lines, code = report(_arm("random"), _arm("model"))
        self.assertEqual(code, 0, "\n".join(lines))
        self.assertIn("  VERDICT: STEERED", lines)

    def test_a_first_position_prior_reads_not_shown(self):
        """The mutation this arm exists to survive: a model that never reads the
        board, only the list. The seeded menu order keeps it at chance."""
        lines, code = report(_arm("random"), _arm("model", policy="first"))
        self.assertEqual(code, 0, "\n".join(lines))
        self.assertIn("  VERDICT: NOT SHOWN", lines)

    def test_the_control_compliance_is_reported_beside_the_steered_rate(self):
        lines, _ = report(_arm("random"), _arm("model"))
        self.assertTrue(any(line.startswith("  control compliance:")
                            for line in lines), "\n".join(lines))


class TestVoids(unittest.TestCase):
    def test_adjudicator_fallback_over_ten_percent_voids_the_arm(self):
        control = _arm("random")
        steered = _arm("model", adjudicator_fallbacks=99)
        calls = steered[0]["score"]["adjudicator_integrity"]["calls"]
        self.assertGreater(
            steered[0]["score"]["adjudicator_integrity"]["fallback_rate"], 0.10,
            f"the fixture must exceed the bar over {calls} calls")

        lines, code = report(control, steered)

        self.assertEqual(code, 2)
        self.assertTrue(any("above 10%" in line for line in lines),
                        "\n".join(lines))

    def test_a_menu_in_another_order_does_not_reconstruct(self):
        """A record whose offered order is not the seeded one cannot be scored:
        the rule's answer would be graded against a menu nobody sent."""
        control, steered = _arm("random"), _arm("model")
        for row in steered[1]:
            if row["adjudicator"] is not None:
                event = row["adjudicator"]["events"][0]
                event["options"] = sorted(event["options"])
                break

        lines, code = report(control, steered)

        self.assertEqual(code, 2)
        self.assertTrue(any("does not reconstruct" in line for line in lines),
                        "\n".join(lines))

    def test_a_control_that_made_calls_voids(self):
        control, steered = _arm("random"), _arm("model")
        control[0]["score"]["adjudicator_integrity"] = {
            "calls": 1, "fallbacks": 0, "fallback_rate": 0.0, "recovered": 0,
            "upstreams": {},
        }

        lines, code = report(control, steered)

        self.assertEqual(code, 1)
        self.assertTrue(any("DISAGREES" in line for line in lines),
                        "\n".join(lines))

    def test_a_short_campaign_voids(self):
        control, steered = _arm("random"), _arm("model")
        steered[1].pop()
        steered[0]["score"]["games_requested"] = len(steered[1])
        steered[0]["score"]["games_completed"] = len(steered[1])
        steered[0]["score"]["integrity"]["decisions"] = sum(
            row["decisions"] for row in steered[1])

        lines, code = report(control, steered)

        self.assertEqual(code, 2)
        self.assertTrue(any("promised games" in line for line in lines),
                        "\n".join(lines))


class TestBinding(unittest.TestCase):
    def test_an_unsteered_record_is_not_this_criterion(self):
        """The one settings mistake this arm is most exposed to: the blind ask
        run under the steering criterion's name."""
        control, steered = _arm("random"), _arm("model")
        steered[0]["args"]["adjudicator_steer"] = False

        lines, code = report(control, steered)

        self.assertEqual(code, 3)
        self.assertTrue(any("adjudicator_steer" in line for line in lines),
                        "\n".join(lines))

    def test_the_arm_binds_its_records_and_its_document_together(self):
        arm, control_path, model_path = resolve([])
        self.assertEqual(arm, ARMS["s23"])
        self.assertEqual(str(control_path).replace("\\", "/"), arm["control"])
        self.assertEqual(str(model_path).replace("\\", "/"), arm["model"])
        self.assertTrue(Path(arm["doc"]).exists(), arm["doc"])

    def test_the_frozen_launcher_runs_the_criterion_settings(self):
        recipes = _launcher_recipes()
        for adjudicator, expected in (("random", CONTROL_ARGS),
                                      ("model", STEERED_ARGS)):
            recipe = recipes[adjudicator]
            with self.subTest(arm=adjudicator):
                for key in ("games", "seats", "script", "rounds", "seed",
                            "adjudicator", "adjudicator_model", "out"):
                    if expected[key] is None:
                        self.assertNotIn(key, recipe)
                    else:
                        self.assertEqual(recipe[key], expected[key])
                self.assertEqual(recipe.get("adjudicator_steer", False),
                                 expected["adjudicator_steer"])


if __name__ == "__main__":
    unittest.main()
