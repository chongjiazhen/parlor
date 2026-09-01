"""Combined UAT plus incremental-transcript contract."""

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


class TestUATTranscriptIntegration(unittest.TestCase):
    def test_constrained_human_run_marks_record_and_streams_same_log(self):
        """Break caught: constrained deal not reaching referee, or sidecar not
        reflecting final GameRecord.log from same UAT game."""
        seed = 7
        rng = random.Random(seed)
        # Setup constrained deal with human role
        dealt, centre = constrained_deal(SETUP_5, random.Random(seed), 0, "spotter")
        console = ConsoleBackend(keys=ACTION_KEYS)
        console.stdin = io.StringIO("say I will wait\nvote 1\n" * 40)
        console.stdout = io.StringIO()
        with TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "referee.log"
            with ChangelingReferee.new(
                    5, seed=seed, discussion_rounds=1, dealt=dealt,
                    centre=centre, transcript_path=out_path) as ref:
                human = LLMPolicy(backend=console, retries=8,
                                  fallback=RandomPolicy(rng))
                policies = {s: (human if s == 0 else RandomPolicy(rng))
                            for s in range(ref.n)}
                rec = play_game(ref, policies, uat=True)
                self.assertTrue(rec.uat, "UAT flag not set on record")
                self.assertEqual(ref.night.dealt[0].key, "spotter")
                self.assertEqual(out_path.read_text(encoding="utf-8").splitlines(),
                                 rec.log)


if __name__ == "__main__":
    unittest.main()
