"""The two phrasings, and the pin that keeps the default from drifting.

A model-facing string edit is a measured change (`docs/model-facing-text.md`), so
the rewrite ships as an ARM: `as-is` renders the bytes every recorded changeling
number was played on, `positive` renders the negation pass. Two things have to be
true for that to be an arm rather than a silent re-baseline, and both are tested
here rather than asserted in prose:

- **`as-is` is byte-identical to what shipped.** ``GOLDEN_AS_IS`` is a sha256 over
  a fixed corpus - five seeded games' prompts in both phases, the public events a
  flat vote produces, both register preambles, and the four refusal complaints.
  It was computed against the tree BEFORE the phrasing table existed. A drift in
  any of those strings fails here, which is the only reason the default may be
  cited beside a record played before the flag existed.
- **`positive` actually removes the prohibitions.** A table whose `positive` column
  was copied from `as-is` would pass every leak and render test in the repo, so the
  vocabulary scan below asserts BOTH directions: the token is present under `as-is`
  and absent under `positive`. One direction alone is vacuous.

Gate #1 runs over both phrasings, honest and leaky, because the audit reads the ask
and the ask is one of the strings the table swaps.
"""

from __future__ import annotations

import hashlib
import unittest

from core.backends import REGISTERS, REGISTERS_POSITIVE
from games.changeling.audit import leak_audit
from games.changeling.phrasing import AS_IS, POSITIVE, PHRASINGS
from games.changeling.player import RandomPolicy, play_game
from games.changeling.referee import ChangelingReferee
from games.changeling.roles import THEME_FOLK
from games.changeling.test_referee import LeaksOwnTruth


#: sha256 of ``corpus(AS_IS)``, computed on the tree before this module landed.
GOLDEN_AS_IS = "060bace18231558a63bec3f15427eabf6fec6fd4df2a3cff26ad8b35de091801"

#: Steering vocabulary the pass exists to remove. Each entry must appear in the
#: `as-is` corpus and be gone from the `positive` one - a token that fails the
#: first half is a stale list, not a passing test.
BANNED = ("cannot", "was refused", "not a move", "no seat drew",
          "nothing to go on", "no theatrics", "do not defer", "Never reveal",
          "not real deceit", "worth nothing")


def corpus(phrasing, registers) -> str:
    """Every string this arm can put in front of a model, in a fixed order."""
    out: list[str] = []
    for seed in range(5):
        ref = ChangelingReferee.new(5, seed=seed, theme=THEME_FOLK,
                                    phrasing=phrasing)
        for s in range(ref.n):
            out.append(ref.prompt_for(s))
        for _ in range(ref.discussion_rounds):
            for s in range(ref.n):
                ref.speak(s, f"seat {s} says something")
            ref.close_round()
        for s in range(ref.n):
            out.append(ref.prompt_for(s))
        for s in range(ref.n):
            ref.cast(s, (s + 1) % ref.n)
        out += [t for _, t in ref.public_events]
    out += [registers["character"], registers["plain"]]
    out += [phrasing.retry.format(complaint='unparsed - missing "vote"'),
            phrasing.self_vote.format(seat=3, legal=[0, 1, 2, 4]),
            phrasing.missing_say, phrasing.missing_vote]
    return "\n<<>>\n".join(out)


class DefaultIsPinned(unittest.TestCase):
    def test_as_is_corpus_is_byte_identical_to_what_shipped(self):
        text = corpus(AS_IS, REGISTERS)
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),
                         GOLDEN_AS_IS)

    def test_default_referee_is_as_is(self):
        self.assertIs(ChangelingReferee.new(5, seed=1).phrasing, AS_IS)

    def test_both_phrasings_are_registered(self):
        self.assertEqual(PHRASINGS["as-is"], AS_IS)
        self.assertEqual(PHRASINGS["positive"], POSITIVE)


class PositiveRemovesTheProhibitions(unittest.TestCase):
    """Both directions. A `positive` column copied from `as-is` fails the second
    assertion, which is the mutation this pair is here to catch."""

    def test_banned_vocabulary_is_present_as_is_and_gone_positive(self):
        as_is = corpus(AS_IS, REGISTERS)
        positive = corpus(POSITIVE, REGISTERS_POSITIVE)
        for token in BANNED:
            with self.subTest(token=token):
                self.assertIn(token, as_is)
                self.assertNotIn(token, positive)

    def test_the_two_corpora_differ(self):
        self.assertNotEqual(corpus(AS_IS, REGISTERS),
                            corpus(POSITIVE, REGISTERS_POSITIVE))


class Gate1HoldsUnderBoth(unittest.TestCase):
    def test_no_leak_over_200_seeded_games_under_either_phrasing(self):
        for phrasing in (AS_IS, POSITIVE):
            for seed in range(200):
                ref = ChangelingReferee.new(5, seed=seed, theme=THEME_FOLK,
                                            phrasing=phrasing)
                self.assertEqual(leak_audit(ref), [], f"{phrasing.name}/{seed}")

    def test_a_leaky_referee_is_still_caught_under_positive(self):
        caught = 0
        for seed in range(60):
            ref = LeaksOwnTruth.new(5, seed=seed, theme=THEME_FOLK,
                                    phrasing=POSITIVE)
            if ref.night.diverged() and leak_audit(ref):
                caught += 1
        self.assertGreater(caught, 0, "the audit went blind under --phrasing "
                                      "positive")


class RecordCarriesThePhrasing(unittest.TestCase):
    def test_game_record_names_the_arm(self):
        import random
        played = []
        for phrasing in (AS_IS, POSITIVE):
            ref = ChangelingReferee.new(5, seed=7, theme=THEME_FOLK,
                                        phrasing=phrasing)
            rng = random.Random(7)
            rec = play_game(ref, {s: RandomPolicy(rng) for s in range(ref.n)})
            self.assertEqual(rec.phrasing, phrasing.name)
            played.append(rec)

    def test_the_random_control_is_identical_under_both_phrasings(self):
        """A random seat reads no prompt, so one control serves both arms - which
        is why the pair costs one run and not two. Asserted rather than assumed:
        the criterion spends the saving."""
        import random
        out = []
        for phrasing in (AS_IS, POSITIVE):
            ref = ChangelingReferee.new(5, seed=11, theme=THEME_FOLK,
                                        phrasing=phrasing)
            rng = random.Random(11)
            rec = play_game(ref, {s: RandomPolicy(rng) for s in range(ref.n)})
            out.append((rec.winner, rec.accused, rec.truth,
                        [(v.seat, v.target) for v in rec.votes]))
        self.assertEqual(out[0], out[1])


if __name__ == "__main__":
    unittest.main()
