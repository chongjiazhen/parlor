"""Integration test for UAT workflow and transcript generation.

Ensures that a UAT run creates a transcript file, the file contains the public
record, and private information (think/debug) is not rendered.
"""

import io
import random
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from games.changeling.demo import constrained_deal
from games.changeling.referee import ChangelingReferee
from games.changeling.roles import SETUP_5
from games.changeling.player import ACTION_KEYS, LLMPolicy, RandomPolicy, play_game
from core.console import ConsoleBackend
from games.changeling import transcript as changeling_transcript


class TestUATTranscriptIntegration(unittest.TestCase):
    def test_uat_run_creates_valid_transcript(self):
        seed = 7
        rng = random.Random(seed)
        # Setup constrained deal with human role
        ref = ChangelingReferee.new(5, seed=seed, discussion_rounds=1)
        dealt, centre = constrained_deal(SETUP_5, random.Random(seed), 0, "spotter")
        console = ConsoleBackend(keys=ACTION_KEYS)
        console.stdin = io.StringIO("say I will wait\nvote 1\n" * 40)
        console.stdout = io.StringIO()
        human = LLMPolicy(backend=console, retries=8, fallback=RandomPolicy(rng))
        policies = {s: (human if s == 0 else RandomPolicy(rng)) for s in range(ref.n)}
        rec = play_game(ref, policies, uat=True)
        self.assertTrue(rec.uat, "UAT flag not set on record")
        # Write transcript to temporary file
        with TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "run.md"
            changeling_transcript.write(str(out_path), changeling_transcript.render(rec))
            self.assertTrue(out_path.exists(), "Transcript file not created")
            text = out_path.read_text(encoding="utf-8")
            # Verify public events appear
            for _, msg in ref.public_events:
                self.assertIn(msg, text)
            # Verify private think/debug never rendered
            self.assertNotIn("I am the mimic", text)
            self.assertNotIn("assignment =", text)
            # Verify UAT marker appears in the rendered meta section
            self.assertIn("uat: true", text.lower())


if __name__ == "__main__":
    unittest.main()