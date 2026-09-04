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

The shared parser's complaints (`core/replies.py`) are the other half of the
refusal text, and the retry loop feeds one straight into the next prompt. They
follow the flag too, so `ComplaintsFollowTheArm` covers them: the `as-is` column
is `core.replies.AS_IS_COMPLAINTS` BY IDENTITY - which inherits that module's own
golden pin rather than restating it, and is why the other four games cannot drift
from this arm's control - and the `positive` column goes through the same
both-directions vocabulary scan.

Gate #1 runs over both phrasings, honest and leaky, because the audit reads the ask
and the ask is one of the strings the table swaps.
"""

from __future__ import annotations

import hashlib
import unittest
from dataclasses import fields

from core.backends import REGISTERS, REGISTERS_POSITIVE
from core.replies import AS_IS_COMPLAINTS, ParseError
from games.changeling.audit import leak_audit
from games.changeling.phrasing import AS_IS, POSITIVE, PHRASINGS
from games.changeling.player import (LLMPolicy, RandomPolicy, parse_action,
                                     play_game)
from games.changeling.referee import Phase
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


def complaint_corpus(phrasing) -> str:
    """Every parser complaint this arm can put in front of a seat.

    Rendered through the arm's own table with fixed sample values, so the
    vocabulary scan reads the bytes a seat would read rather than the templates.
    Kept OUT of ``corpus`` on purpose: that function's sha256 was computed before
    the phrasing table existed, and growing its input would forfeit the one
    provenance the default pin has.
    """
    c = phrasing.complaints
    return "\n<<>>\n".join([
        c.no_json.format(reply=repr("a sentence and no object")),
        c.nothing_salvageable.format(reply=repr("a sentence and no object")),
        c.not_boolean.format(value=repr("perhaps")),
        c.not_index.format(value=repr(True), noun="seat", last=4),
        c.no_index_number.format(value=repr("the left one"), noun="seat",
                                 last=4),
        c.index_out_of_range.format(noun="seat", index=9, last=4),
        c.not_index_list.format(noun="seat", value=repr({"a": 1})),
        c.wrong_index_count.format(size=2, noun="seat", picked=[1, 1]),
    ])


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


class ComplaintsFollowTheArm(unittest.TestCase):
    """The shared parser is five games wide, so the arm hands it a table instead
    of editing it. What has to hold: the ``as-is`` column is the other games'
    bytes, the ``positive`` column is reached from changeling's own parse path,
    and no slot sits unread behind a pin."""

    def test_as_is_complaints_are_the_shared_default_by_identity(self):
        self.assertIs(AS_IS.complaints, AS_IS_COMPLAINTS)

    def test_positive_complaints_are_a_different_table(self):
        self.assertIsNot(POSITIVE.complaints, AS_IS_COMPLAINTS)
        self.assertNotEqual(complaint_corpus(AS_IS),
                            complaint_corpus(POSITIVE))

    def test_parse_action_reads_the_referees_table(self):
        """Through ``parse_action``, not through the table - a field the parse
        path never passes on would pass every other test in this file."""
        for phrasing in (AS_IS, POSITIVE):
            ref = ChangelingReferee.new(5, seed=3, theme=THEME_FOLK,
                                        phrasing=phrasing)
            with self.subTest(arm=phrasing.name, case="no object"):
                with self.assertRaises(ParseError) as caught:
                    parse_action("a sentence and no object", ref, 0)
                self.assertEqual(str(caught.exception),
                                 phrasing.complaints.nothing_salvageable.format(
                                     reply=repr("a sentence and no object")))
            while ref.phase is not Phase.VOTE:
                for s in range(ref.n):
                    ref.speak(s, f"seat {s} says something")
                ref.close_round()
            with self.subTest(arm=phrasing.name, case="not a seat"):
                with self.assertRaises(ParseError) as caught:
                    parse_action('{"vote": "the left one"}', ref, 0)
                self.assertEqual(str(caught.exception),
                                 phrasing.complaints.no_index_number.format(
                                     value=repr("the left one"), noun="seat",
                                     last=4))

    def test_every_phrasing_slot_has_a_consumer(self):
        """A slot nothing renders is a promise the arm does not keep.

        ``corpus`` hashes an unread slot as happily as a read one, so each field
        is required to appear in what a seat can actually be shown - the prompts,
        the public events, the complaints, and the retry wrapper the policy
        builds. Caught the retry slot, which was pinned by the hash and rendered
        by nobody.
        """
        text = "\n".join([corpus(POSITIVE, REGISTERS_POSITIVE),
                           complaint_corpus(POSITIVE),
                           built_retry_prompt(POSITIVE)])
        for f in fields(POSITIVE):
            if f.name in ("name", "complaints"):
                continue
            with self.subTest(slot=f.name):
                marker = getattr(POSITIVE, f.name).split("{")[0].strip()
                self.assertTrue(marker, f"{f.name} has no literal to look for")
                self.assertIn(marker, text)

    def test_the_retry_wrapper_follows_the_arm(self):
        for phrasing in (AS_IS, POSITIVE):
            with self.subTest(arm=phrasing.name):
                self.assertIn(phrasing.retry.split("{")[0].strip(),
                              built_retry_prompt(phrasing))


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


class VocabularyScanCoversTheComplaints(unittest.TestCase):
    """The ten tokens, over the parser's complaints as well as the referee's
    strings. Absence only: a complaint the shipped table never carried would fail
    a presence half against a stale list, and `core/test_complaints.py` is what
    pins the shipped wording."""

    def test_no_banned_token_survives_in_the_positive_complaints(self):
        text = complaint_corpus(POSITIVE)
        for token in BANNED:
            with self.subTest(token=token):
                self.assertNotIn(token, text)

    def test_the_scan_would_catch_an_as_is_complaint_left_in(self):
        """The mutation this pair exists to catch: a `positive` column copied
        from `as-is`. At least one banned token must be findable in the shipped
        complaints, or the assertion above is vacuous."""
        text = complaint_corpus(AS_IS)
        self.assertTrue(any(token in text for token in BANNED),
                        "no banned token in the as-is complaints - the list is "
                        "stale, so the absence assertion proves nothing")


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


class OnePrompt:
    """A backend that answers once with unparseable text, and keeps every prompt
    it was handed. The retry wrapper is only visible from here: it is built
    inside ``LLMPolicy.act`` and reaches no return value."""

    def __init__(self):
        self.prompts: list[str] = []

    def complete_meta(self, prompt: str):
        self.prompts.append(prompt)
        return "a sentence and no object", "stub"


def built_retry_prompt(phrasing) -> str:
    """The second prompt ``LLMPolicy`` builds after one refused attempt."""
    import random
    ref = ChangelingReferee.new(5, seed=5, theme=THEME_FOLK, phrasing=phrasing)
    backend = OnePrompt()
    policy = LLMPolicy(backend=backend, retries=1, backoff=0,
                       fallback=RandomPolicy(random.Random(5)))
    policy.act(ref, 0)
    assert len(backend.prompts) == 2, backend.prompts
    return backend.prompts[1]


if __name__ == "__main__":
    unittest.main()
