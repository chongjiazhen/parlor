"""Per-upstream cloud scoring uses stored decision provenance, never run totals."""

import json
import tempfile
import unittest
from pathlib import Path

from eval import cloud_strata as cs


def game(upstream: str, *, clean: bool, tainted: bool, hunt_hit: bool,
         fallback: bool = False) -> dict:
    """One complete synthetic record with results joined to served decisions."""
    return {
        "decisions": 4,
        "decision_log": [
            {"turn": 1, "seat": 0, "phase": "vote", "fell_back": False,
             "served_by": upstream},
            {"turn": 2, "seat": 1, "phase": "vote", "fell_back": False,
             "served_by": upstream},
            {"turn": 3, "seat": 4, "phase": "hunt", "fell_back": False,
             "served_by": upstream},
            {"turn": 4, "seat": 2, "phase": "discuss", "fell_back": fallback,
             "served_by": upstream},
        ],
        "votes": [
            {"turn": 1, "seat": 0, "approved": clean, "seat_is_evil": False,
             "team_has_evil": False, "knowledge_class": "none"},
            {"turn": 2, "seat": 1, "approved": tainted, "seat_is_evil": False,
             "team_has_evil": True, "knowledge_class": "none"},
        ],
        "hunt": {"hunter": 4, "hit": hunt_hit},
    }


class TestCloudStrata(unittest.TestCase):

    def test_each_upstream_keeps_its_own_votes_hunts_and_fallback_rate(self):
        """Pooling these cells would erase opposite vote and hunt results."""
        score = cs.score_records([
            game("120b", clean=True, tainted=False, hunt_hit=True),
            game("nano", clean=False, tainted=True, hunt_hit=False, fallback=True),
        ])

        self.assertEqual(score["120b"]["votes"],
                         {"clean": 1, "clean_votes": 1, "tainted": 0,
                          "tainted_votes": 1, "discrimination": 1.0})
        self.assertEqual(score["120b"]["hunts"]["hits"], 1)
        self.assertEqual(score["120b"]["hunts"]["total"], 1)
        self.assertEqual(score["nano"]["votes"],
                         {"clean": 0, "clean_votes": 1, "tainted": 1,
                          "tainted_votes": 1, "discrimination": -1.0})
        self.assertEqual(score["nano"]["hunts"]["hits"], 0)
        self.assertEqual(score["nano"]["integrity"],
                         {"decisions": 4, "fallbacks": 1, "fallback_rate": 1 / 4})

    def test_cells_accumulate_across_stored_runs(self):
        """A later 120B run grows its existing cell instead of making a run mix."""
        score = cs.score_records([
            game("120b", clean=True, tainted=False, hunt_hit=True),
            game("120b", clean=False, tainted=True, hunt_hit=False),
        ])

        self.assertEqual(score["120b"]["votes"],
                         {"clean": 1, "clean_votes": 2, "tainted": 1,
                          "tainted_votes": 2, "discrimination": 0.0})
        self.assertEqual(score["120b"]["hunts"]["hits"], 1)
        self.assertEqual(score["120b"]["hunts"]["total"], 2)

    def test_missing_provenance_is_refused_not_pooled(self):
        """Legacy decision rows cannot enter a model cell by inference."""
        record = game("120b", clean=True, tainted=False, hunt_hit=True)
        record["decision_log"][2].pop("served_by")

        with self.assertRaisesRegex(ValueError, "served_by"):
            cs.score_records([record])

    def test_legacy_vote_rows_do_not_block_a_provenanced_hunt(self):
        """A stored hunt remains useful when old vote rows lack their turn key."""
        record = game("nano", clean=True, tainted=False, hunt_hit=True)
        for vote in record["votes"]:
            vote.pop("turn")

        score = cs.score_records([record])

        self.assertIsNone(score["nano"]["votes"]["discrimination"])
        self.assertEqual(score["nano"]["hunts"]["hits"], 1)

    def test_transport_fallback_without_an_upstream_is_exposed(self):
        """No served model means no model cell, never a silently smaller rate."""
        record = game("120b", clean=True, tainted=False, hunt_hit=True)
        record["decision_log"][3]["served_by"] = ""
        record["decision_log"][3]["fell_back"] = True

        score = cs.score_records([record])

        self.assertEqual(score[cs.UNATTRIBUTED]["integrity"],
                         {"decisions": 1, "fallbacks": 1, "fallback_rate": 1.0})

    def test_a_multi_upstream_fallback_is_not_charged_to_its_last_retry(self):
        """Two served retries leave no honest per-upstream fallback denominator."""
        record = game("up-b", clean=True, tainted=False, hunt_hit=True)
        fallback = record["decision_log"][3]
        fallback["fell_back"] = True
        fallback["attempted_upstreams"] = ["up-a", "up-b"]

        score = cs.score_records([record])

        self.assertEqual(score["up-b"]["integrity"]["fallbacks"], 0)
        self.assertEqual(score[cs.UNATTRIBUTED]["integrity"]["fallbacks"], 1)

    def test_report_shows_vote_denominators(self):
        """Approval counts without vote totals cannot price a thin cell."""
        text = cs.report(cs.score_records([
            game("120b", clean=True, tainted=False, hunt_hit=True),
        ]))

        self.assertIn("1/1 clean approvals, 0/1 tainted approvals", text)

    def test_paired_summary_and_jsonl_inputs_are_refused(self):
        """One run writes both artifacts; loading both would double every cell."""
        with tempfile.TemporaryDirectory() as tmp:
            summary = Path(tmp) / "run.json"
            jsonl = Path(f"{summary}.jsonl")
            payload = game("120b", clean=True, tainted=False, hunt_hit=True)
            summary.write_text(json.dumps({"games": [payload]}), encoding="utf-8")
            jsonl.write_text(json.dumps({"game": 0, **payload}) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "paired"):
                cs.load_paths([str(summary), str(jsonl)])


if __name__ == "__main__":
    unittest.main()
