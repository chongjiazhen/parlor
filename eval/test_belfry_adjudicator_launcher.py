"""Fail-closed guards for S8's frozen model-adjudicator recipe."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from eval.probe_tier import main as probe_main


LAUNCHER = (Path(__file__).parent / "runs" / "belfry-adjudicator.cmd")


class TestServedUpstreamGate(unittest.TestCase):
    def test_probe_rejects_a_responding_wrong_upstream(self):
        """A healthy local route is not this arm unless it served committed model."""
        with mock.patch("eval.probe_tier.probe_once",
                        return_value=(200, 0.1, "wrong-model", "ok")), \
             redirect_stdout(io.StringIO()):
            result = probe_main([
                "--backend", "local", "--model", "qwen36-35b-a3b-iq3",
                "--require-served", "qwen36-35b-a3b-iq3", "-n", "3",
            ])
        self.assertEqual(result, 1)


class TestEvidenceAndVerdictGates(unittest.TestCase):
    def test_launcher_refuses_every_bound_evidence_path_before_probe(self):
        """JSONL is append-only, so a stale path must stop before GPU work."""
        text = LAUNCHER.read_text(encoding="utf-8")
        gates = [
            'if exist "%CONTROL%"',
            'if exist "%CONTROL%.jsonl"',
            'if exist "%MODEL_OUT%"',
            'if exist "%MODEL_OUT%.jsonl"',
        ]
        for gate in gates:
            with self.subTest(gate=gate):
                self.assertIn(gate, text)
                self.assertLess(text.index(gate), text.index("eval.probe_tier"))

    def test_launcher_applies_bound_verdict_after_model_arm(self):
        """A void, mismatch, or evidence error is launcher failure, not log text."""
        text = LAUNCHER.read_text(encoding="utf-8")
        model_run = text.index("--adjudicator model")
        verdict = text.index("eval.belfry_adjudicator_verdict")
        self.assertGreater(verdict, model_run)
        self.assertIn('"%CONTROL%" "%MODEL_OUT%"', text[verdict:])
        self.assertIn('set "RC=%ERRORLEVEL%"', text[verdict:])
        self.assertIn("if %RC% NEQ 0 exit /b %RC%", text[verdict:])


if __name__ == "__main__":
    unittest.main()
