"""The transcript renderer: what it must show, and what it must never show.

The load-bearing test here is ``test_private_kinds_never_render``. Everything else
checks that a human gets a readable file; that one checks that the file is not a
side door around the two-channel rule the whole arena exists to demonstrate.
"""

from __future__ import annotations

import json
import random
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from games.cabal import transcript
from games.cabal.player import RandomPolicy, play_game
from games.cabal.referee import CabalReferee


def played_game(seed: int = 3, rounds: int = 1):
    rng = random.Random(seed)
    ref = CabalReferee.new(5, seed=seed, discussion_rounds=rounds)
    rec = play_game(ref, {s: RandomPolicy(rng=rng) for s in ref.assignment})
    return ref, rec


class TestRecordCapture(unittest.TestCase):
    def test_record_carries_both_public_channels(self):
        ref, rec = played_game()
        self.assertEqual(rec.public_events, ref.public_events)
        self.assertEqual(rec.log, ref.log)
        self.assertEqual(rec.theme, ref.theme.name)

    def test_record_survives_a_json_round_trip(self):
        _, rec = played_game()
        loaded = json.loads(json.dumps(asdict(rec)))
        # tuples come back as lists; the renderer must not care
        self.assertIn("## Public record", transcript.render(loaded))


class TestRender(unittest.TestCase):
    def setUp(self):
        self.ref, self.rec = played_game(seed=11, rounds=2)
        self.text = transcript.render(self.rec)

    def test_every_public_line_reaches_the_transcript(self):
        for _, said in self.ref.public_events:
            self.assertIn(said, self.text)

    def test_speech_renders_as_speech_and_events_as_referee_words(self):
        speech = [t for k, t in self.ref.public_events if k.startswith("speech:")]
        events = [t for k, t in self.ref.public_events if k == "event"]
        self.assertIn(f"- {speech[0]}", self.text)
        self.assertIn(f"- *{events[0]}*", self.text)

    def test_private_kinds_never_render(self):
        """A tuple kind that is not one of the two public channels is dropped, not
        rendered. Without the whitelist, anything appended upstream - a private
        ``think``, a debug line - would land in a file meant to be shared."""
        rec = asdict(self.rec)
        rec["public_events"] = list(rec["public_events"]) + [
            ("think:2", "I am the mimic and seat 4 is my partner"),
            ("debug", "assignment = {0: 'seer'}"),
        ]
        text = transcript.render(rec)
        self.assertNotIn("I am the mimic", text)
        self.assertNotIn("assignment = {0:", text)

    def test_secret_assignment_is_revealed_at_the_bottom(self):
        head, _, tail = self.text.partition("## The secret assignment")
        self.assertTrue(tail)
        for seat, role in self.ref.assignment.items():
            self.assertIn(f"| {seat} |", tail)
            self.assertIn(f"`{role.key}`", tail)
        # and nowhere above it
        self.assertNotIn("`mimic`", head)

    def test_winner_and_fallback_rate_are_stated(self):
        self.assertIn("Winner:", self.text)
        self.assertIn("decisions", self.text)

    def test_high_fallback_rate_is_called_out(self):
        rec = asdict(self.rec)
        rec["decisions"], rec["fallbacks"] = 10, 9
        self.assertIn("wearing a model's name", transcript.render(rec))
        rec["fallbacks"] = 0
        self.assertNotIn("wearing a model's name", transcript.render(rec))

    def test_meta_lands_in_the_header(self):
        text = transcript.render(self.rec, {"backend": "local", "model": "m-1",
                                            "rounds": 2, "seed": 11})
        self.assertIn("backend local", text)
        self.assertIn("model m-1", text)

    def test_from_referee_matches_the_record(self):
        self.assertEqual(transcript.from_referee(self.ref, self.rec), self.text)


class TestLegacyRecord(unittest.TestCase):
    """A record written before ``public_events`` existed has no timeline. It must
    say so rather than presenting a reconstruction as the real thing."""

    def setUp(self):
        rec = asdict(played_game(seed=5)[1])
        rec.pop("public_events")
        rec.pop("log")
        self.text = transcript.render(rec)

    def test_it_announces_the_reconstruction(self):
        self.assertIn("Reconstructed, not recorded", self.text)

    def test_it_still_shows_the_talk_and_the_outcome(self):
        self.assertIn("Table talk", self.text)
        self.assertIn("Vote rounds", self.text)
        self.assertIn("Winner:", self.text)

    def test_it_does_not_invent_referee_lines(self):
        self.assertNotIn("proposes", self.text)


class TestCli(unittest.TestCase):
    def test_writes_a_file_from_a_run_json(self):
        _, rec = played_game(seed=9)
        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "run.json"
            src.write_text(json.dumps({"args": {"backend": "local"},
                                       "games": [asdict(rec)]}), encoding="utf-8")
            out = Path(tmp) / "game.md"
            transcript.write(str(out), transcript.render(
                json.loads(src.read_text(encoding="utf-8"))["games"][0]))
            self.assertIn("## Public record", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
