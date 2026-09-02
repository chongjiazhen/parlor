"""Does the code play the game RULES.md describes, and does it hold together?

Two classes of check, and neither is what a code review finds.

**Conformance** parses `RULES.md` and asserts its claims against the code. That
file is canonical - every gate stratum and every baseline in this repo derives from
it - so a drift between the two does not look like a bug, it looks like a NUMBER.
Restating its tables here in Python would just move the drift; these read the
markdown, so editing the doc without the code (or the code without the doc) fails.

**Properties** assert invariants over many random nights. This is the class that
found the real defect: `require_seated_pack` does exactly what its code says, and
the CLAIM about its consequence was wrong by 2.8% - visible only by running games,
never by reading either one.
"""

from __future__ import annotations

import collections
import random
import re
import pathlib
import unittest

from games.changeling.night import (centre_ref, is_centre, legal_targets,
                                    resolve_night)
from games.changeling.roles import (ALL_CARDS, CARDS, NIGHT_ORDER, SETUP_5,
                                    SETUPS, THEMES, Act, Side, indefinite)

RULES = pathlib.Path(__file__).with_name("RULES.md").read_text(encoding="utf-8")


def table_rows(header_cell: str) -> list[list[str]]:
    """Rows of the markdown table whose header starts with ``header_cell``."""
    rows: list[list[str]] = []
    seen_header = False
    for line in RULES.splitlines():
        if not line.startswith("|"):
            if seen_header and rows:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0] == header_cell:
            seen_header = True
            continue
        if not seen_header or set(cells[0]) <= set("-: "):
            continue
        rows.append(cells)
    return rows


def key_of(cell: str) -> str:
    m = re.search(r"`([a-z]+)`", cell)
    return m.group(1) if m else cell


class TestRulesTablesMatchTheCode(unittest.TestCase):
    def test_the_deck_table_matches_the_setup(self):
        """Counts and sides, read from the doc, asserted against SETUP_5."""
        rows = table_rows("card key")
        self.assertTrue(rows, "could not find the deck table in RULES.md")
        doc = {key_of(r[0]): (r[1], int(r[2])) for r in rows}
        code = collections.Counter(c.key for c in SETUP_5.deck)
        self.assertEqual({k: v[1] for k, v in doc.items()}, dict(code))
        for key, (side, _) in doc.items():
            want = Side.PACK if side == "evil" else Side.VILLAGE
            self.assertIs(CARDS[key].side, want, f"{key} side differs from RULES.md")

    def test_the_knowledge_class_table_matches_the_cards(self):
        """The gate stratifies on these. A doc/code drift here mislabels a whole
        stratum and the number still renders."""
        rows = table_rows("dealt card")
        self.assertTrue(rows, "could not find the knowledge-class table")
        doc = {key_of(r[0]): key_of(r[1]) for r in rows}
        self.assertEqual(doc, {k: c.knowledge_class for k, c in CARDS.items()})

    def test_the_numbered_night_order_matches_NIGHT_ORDER(self):
        listed = re.findall(r"^\d+\. `([a-z]+)`", RULES, re.M)
        self.assertEqual(len(listed), len(NIGHT_ORDER))
        self.assertEqual([CARDS[k].act for k in listed], list(NIGHT_ORDER))

    def test_five_seats_and_eight_cards_as_stated(self):
        self.assertIn("**Five seats. Eight cards.**", RULES)
        self.assertEqual(SETUP_5.n, 5)
        self.assertEqual(len(SETUP_5.deck), 8)
        self.assertIn("three to the centre", RULES)
        self.assertEqual(SETUP_5.centre, 3)

    def test_the_degenerate_deal_arithmetic_in_the_doc_is_right(self):
        """RULES.md claims 6/56 = 10.7% of unconstrained deals seat no pack. It is
        quoted as the reason the constraint exists, so it has to be true."""
        self.assertIn("6/56 = 10.7%", RULES)
        from math import comb
        deck = SETUP_5.deck
        packs = sum(1 for c in deck if c.side is Side.PACK)
        both_in_centre = comb(len(deck) - packs, SETUP_5.centre - packs)
        total = comb(len(deck), SETUP_5.centre)
        self.assertEqual((both_in_centre, total), (6, 56))
        self.assertAlmostEqual(both_in_centre / total, 0.107, places=3)

    def test_each_card_power_is_stated_in_the_public_rules(self):
        """The measured fix. A card added without a power would render a bare name
        and put the models back to inventing one."""
        for key, card in CARDS.items():
            self.assertTrue(card.power, f"{key} has no public power text")

    def test_no_power_text_names_another_card(self):
        """The preamble's audit exclusion rests on it being seat-invariant AND
        association-free. A power that named another card would put an association
        into text the audit does not scan."""
        for key, card in CARDS.items():
            for other in CARDS:
                if other != key:
                    self.assertNotIn(other, card.power.lower(),
                                     f"{key}'s power names {other}")


class TestTheExpansionDecksMatchTheirProse(unittest.TestCase):
    """The shipped deck's composition is asserted from a markdown TABLE above. The
    expansion decks are specified in PROSE instead, which is the weaker surface: a
    card list inside a sentence drifts from the code silently, and a deck
    composition is not a typo - it re-baselines every number played on it.

    So each registered deck's multiset is read back out of the sentence that
    specifies it. Written when deck B landed, and deliberately covering deck A too:
    deck A shipped with its prose unchecked and a 200-game campaign was read off it.
    """

    def deck_from_prose(self, sentence: str) -> collections.Counter:
        """The card list in a deck's spec sentence, as a multiset.

        ``pack`` x2 means two, a bare ``spotter`` means one. This PARSES the doc
        rather than restating it, which is the whole point - a test carrying its own
        copy of the list would just move the drift into itself.
        """
        start = RULES.find(sentence)
        self.assertNotEqual(start, -1, f"could not find {sentence!r} in RULES.md")
        body = RULES[start + len(sentence):]
        # The spec runs to the first bullet of the argument below it. Bounded
        # rather than greedy, and the bound is what
        # `test_the_parse_is_not_vacuous` checks: the first version cut on a
        # blank line, which does not exist here, so it swallowed the bullets and
        # read `kindred` seven times.
        body = body.split("\n- ")[0]
        got: collections.Counter = collections.Counter()
        for key, mult in re.findall(r"`([a-z]+)`(?:\s*x(\d+))?", body):
            got[key] += int(mult) if mult else 1
        return got

    def assert_deck_matches_prose(self, sentence: str, seats: int) -> None:
        setup = SETUPS[seats]
        self.assertEqual(self.deck_from_prose(sentence),
                         collections.Counter(c.key for c in setup.deck))
        self.assertEqual((setup.n, setup.centre), (seats, 3))
        self.assertEqual(len(setup.deck), seats + 3)

    def test_deck_A_is_the_deck_its_sentence_specifies(self):
        self.assert_deck_matches_prose(
            "**Deck A, for `waker`: 6 seats, 3 centre, 9 cards.**", 6)

    def test_deck_B_is_the_deck_its_sentence_specifies(self):
        self.assert_deck_matches_prose(
            "**Deck B, for `kindred`: 7 seats, 3 centre, 10 cards, plus a seating "
            "constraint.**", 7)

    def test_the_parse_is_not_vacuous(self):
        """The control for the two above. A `deck_from_prose` that returned an empty
        counter, or one that swallowed the surrounding argument, would pass or fail
        them for reasons that have nothing to do with the deck - so pin what it
        actually read off deck B's sentence."""
        got = self.deck_from_prose(
            "**Deck B, for `kindred`: 7 seats, 3 centre, 10 cards, plus a seating "
            "constraint.**")
        self.assertEqual(sum(got.values()), 10, f"parsed {dict(got)}")
        self.assertEqual(got["pack"], 2)
        self.assertEqual(got["kindred"], 2)
        self.assertNotIn("waker", got, "the parse ran past deck B's own sentence")

    def test_the_kin_constraint_the_doc_promises_is_the_one_the_deck_carries(self):
        """RULES.md states the constraint publicly so seats may reason from it, and
        lists it among the surfaces a fabricated belief must survive. A deck that
        shipped without the flag would make both of those statements false while
        dealing a game that looks entirely legal."""
        self.assertIn("`require_seated_kin`: **both seated or both in the centre**",
                      RULES)
        self.assertTrue(SETUPS[7].require_seated_kin)
        self.assertTrue(any(c.key == "kindred" for c in SETUPS[7].deck),
                        "the kin constraint is on a deck holding no kindred")

    def test_the_shipped_deck_carries_neither_expansion_card(self):
        """A deck change re-baselines every recorded number, and `SETUP_5` is the
        deck all of them were played on."""
        keys = [c.key for c in SETUP_5.deck]
        for expansion in ("kindred", "waker"):
            self.assertNotIn(expansion, keys)
        self.assertFalse(SETUP_5.require_seated_kin)


class TestEverySkinIsNamedAndCollisionFree(unittest.TestCase):
    """The properties a skin must have, checked as data rather than by playing.

    Ported from cabal's ``test_audit_coverage.py``, but NOT verbatim, because this
    game's audit is association-based. There a secret term is a bare role name, so
    the hazard is one name hiding inside another or inside the blurb. Here
    ``reveal_forms`` wraps every name in a frame that carries the seat number, so
    "Seat 3 held the Wolf." cannot hide inside "Seat 3 held the Werewolf." and a
    card named in the blurb reveals nothing about who holds it. Two of cabal's
    three guards therefore have no work to do here, and porting them anyway would
    be ceremony that reads as coverage.

    What survives the translation is the pair below, plus the deck-composition
    guard one rung out: a duplicate display name is the collision this game
    actually has, because it collapses two distinct cards into one term and every
    reveal about either then reads as the other.
    """

    def test_every_skin_names_every_card(self):
        for name, theme in THEMES.items():
            for card in ALL_CARDS:
                self.assertIn(card.key, theme.card_names,
                              f"{name} does not name {card.key}")

    def test_no_two_cards_in_a_skin_share_or_hide_in_a_name(self):
        """Sharing is the live hazard; hiding is insurance against the frame in
        ``reveal_forms`` ever being loosened, which would make a substring match
        the moment the seat number stops separating two terms."""
        for name, theme in THEMES.items():
            terms = {c.key: [c.key.lower(), theme.card_names[c.key].lower()]
                     for c in ALL_CARDS}
            for key, mine in terms.items():
                for other, theirs in terms.items():
                    if key == other:
                        continue
                    for a in mine:
                        for b in theirs:
                            self.assertNotIn(a, b,
                                             f"{name}: {key} term '{a}' hides in {other}")

    def test_no_power_text_names_another_card_in_any_skin(self):
        """``test_no_power_text_names_another_card`` above checks the canonical
        keys. The preamble renders ``{display name} - {power}``, so a power text
        that named another card's DISPLAY name would carry the same association in
        a skin while passing the key-level check - and power text is one string
        shared by every theme, so it is exactly where that goes unnoticed."""
        for name, theme in THEMES.items():
            for card in ALL_CARDS:
                for other in ALL_CARDS:
                    if other.key == card.key:
                        continue
                    self.assertNotIn(theme.card_names[other.key].lower(),
                                     card.power.lower(),
                                     f"{name}: {card.key}'s power names {other.key}")

    def test_no_power_text_takes_the_wrong_article_in_any_skin(self):
        """The article sits in a template shared by every skin; the noun it precedes
        comes FROM the skin. So neither author is in a position to write the pair,
        and a hardcoded "a" put "a altar card" into every seat's preamble the first
        time a skin named the pile with a vowel. Caught by reading the rendered
        prompt, which is why the check now renders rather than reading the template.
        """
        for name, theme in THEMES.items():
            for card in ALL_CARDS:
                text = card.power.format(centre=theme.centre_name,
                                         a_centre=indefinite(theme.centre_name))
                self.assertNotRegex(
                    text, r"\ba (?=[aeiou])",
                    f"{name}: {card.key} renders '{text}'")
                self.assertNotRegex(
                    text, r"\ban (?=[^aeiou])",
                    f"{name}: {card.key} renders '{text}'")


class TestNightInvariants(unittest.TestCase):
    """Properties over many random nights. Each one must ALWAYS hold, so each is
    written as a bound the code cannot argue with."""

    NIGHTS = 2000

    @classmethod
    def setUpClass(cls):
        cls.results = [resolve_night(SETUP_5, random.Random(s))
                       for s in range(cls.NIGHTS)]

    def test_cards_are_conserved(self):
        """The night runs three separate swaps. A bug there duplicates or loses a
        card, which corrupts every gate number instead of crashing."""
        deck = collections.Counter(c.key for c in SETUP_5.deck)
        for i, r in enumerate(self.results):
            got = collections.Counter([c.key for c in r.truth.values()]
                                      + [c.key for c in r.centre])
            self.assertEqual(got, deck, f"seed {i} did not conserve the deck")

    def test_truth_and_belief_only_ever_name_real_cards(self):
        for i, r in enumerate(self.results):
            for mapping in (r.truth, r.belief, r.dealt):
                for card in mapping.values():
                    self.assertIn(card.key, CARDS, f"seed {i}: {card.key}")

    def test_the_dealt_hand_is_never_mutated_by_the_night(self):
        """Who ACTS is read from `dealt`. If the night mutated it, a seat robbed at
        step 3 would stop being the actor for step 4 and the whole order would
        silently change.

        Asserted against a PINNED deal, because comparing the returned `dealt` to
        itself proves nothing - which is what the first version of this test did.
        """
        from games.changeling.roles import (BYSTANDER, DECEIVED, PACK, SPOTTER,
                                            SWAPPER, SWITCHER)  # noqa: F401
        pinned = {0: SWAPPER, 1: PACK, 2: SWITCHER, 3: DECEIVED, 4: SPOTTER}
        centre = [PACK, BYSTANDER, BYSTANDER]
        for seed in range(200):
            r = resolve_night(SETUP_5, random.Random(seed),
                              dealt=dict(pinned), centre=list(centre))
            self.assertEqual({s: c.key for s, c in r.dealt.items()},
                             {s: c.key for s, c in pinned.items()},
                             f"seed {seed} mutated the dealt hand")

    def test_a_seat_untouched_by_the_night_believes_what_it_holds(self):
        """The converse of the divergence property, and the one that would catch a
        night that diverged seats it never moved."""
        for i, r in enumerate(self.results):
            moved = {s for s in r.truth if r.truth[s].key != r.dealt[s].key}
            for seat in r.truth:
                if seat not in moved and r.dealt[seat].act is not Act.TAKE:
                    self.assertEqual(r.belief[seat].key, r.truth[seat].key,
                                     f"seed {i}: seat {seat} diverged untouched")

    def test_divergence_is_exactly_moved_for_every_seat_that_did_not_look(self):
        """An identity, not a bound, so it fails in BOTH directions.

        Restricted to non-takers, and the restriction is the point. The first
        version of this test asserted the identity over ALL seats and failed on
        seed 2 - correctly, against the test. The TAKE actor's belief is what it
        TOOK, not what it was dealt, so it diverges when the switcher moves that
        card at step 4: seed 2 has seat 1 rob seat 2 for `switcher`, then seat 2
        switch seats 1 and 4, leaving seat 1 holding `spotter` and believing
        `switcher`. A taker is therefore diverged on a rule the other seats do not
        share, and folding it in made the invariant wrong rather than strict.
        """
        no_mover_nights = 0
        taker_diverged = 0
        for i, r in enumerate(self.results):
            takers = {s for s in r.dealt if r.dealt[s].act is Act.TAKE}
            moved = {s for s in r.truth if r.truth[s].key != r.dealt[s].key}
            self.assertEqual(r.diverged() - takers, moved - takers,
                             f"seed {i}: a non-taker diverged without being moved, "
                             "or was moved without diverging")
            for s in takers:
                # Belief is what it took, so it can only diverge if a LATER step
                # moved that card. No later mover seated means it cannot.
                if s in r.diverged():
                    taker_diverged += 1
                    self.assertTrue(
                        any(r.dealt[x].act in (Act.SWITCH, Act.DRINK)
                            for x in r.dealt),
                        f"seed {i}: the taker diverged with no later mover seated")
            if not any(r.dealt[s].act in (Act.TAKE, Act.SWITCH, Act.DRINK)
                       for s in r.dealt):
                no_mover_nights += 1
                self.assertEqual(r.diverged(), set())
        self.assertGreater(no_mover_nights, 0,
                           "no mover-free night in range - that branch of this "
                           "test asserted nothing")
        self.assertGreater(taker_diverged, 0,
                           "the taker never diverged in range - the branch this "
                           "test was rewritten to cover asserted nothing")

    def test_a_seat_that_did_not_look_believes_exactly_what_it_was_dealt(self):
        """The rule the identity above rests on, asserted separately so a break in
        it cannot be absorbed by the identity's own arithmetic."""
        for i, r in enumerate(self.results):
            for seat, card in r.dealt.items():
                if card.act is not Act.TAKE:
                    self.assertEqual(r.belief[seat].key, card.key,
                                     f"seed {i}: seat {seat} was told something")

    def test_knowledge_never_points_at_a_seat_that_does_not_exist(self):
        for i, r in enumerate(self.results):
            for seat, ks in r.knowledge.items():
                for k in ks:
                    if is_centre(k.seat):
                        self.assertLess(-k.seat - 1, SETUP_5.centre)
                    else:
                        self.assertIn(k.seat, range(SETUP_5.n), f"seed {i}")

    def test_a_seat_is_never_told_about_itself_except_by_taking(self):
        """The swapper looks at what it took, so it alone holds a self-fact. Any
        other self-reveal would be the referee handing a seat its own truth."""
        for i, r in enumerate(self.results):
            for seat, ks in r.knowledge.items():
                for k in ks:
                    if k.seat == seat:
                        self.assertIs(r.dealt[seat].act, Act.TAKE,
                                      f"seed {i}: seat {seat} told about itself")

    def test_the_deal_always_seats_a_pack_even_though_dawn_may_not(self):
        """Both halves, because RULES.md distinguishes them and the distinction is
        the defect it records."""
        dawn_packless = 0
        for r in self.results:
            self.assertTrue(any(c.side is Side.PACK for c in r.dealt.values()))
            if not any(c.side is Side.PACK for c in r.truth.values()):
                dawn_packless += 1
        rate = dawn_packless / len(self.results)
        self.assertGreater(rate, 0.0, "no packless dawn - the defect RULES.md "
                                      "records has silently gone away")
        self.assertLess(rate, 0.06, f"packless dawns at {rate:.1%}, well above the "
                                    "2.8% RULES.md records")

    def test_no_night_action_ever_targets_its_own_actor(self):
        for act in (Act.LOOK, Act.TAKE, Act.SWITCH):
            for seat in range(SETUP_5.n):
                for kind, target in legal_targets(seat, act, SETUP_5.n,
                                                  SETUP_5.centre):
                    if kind in ("seat", "seats"):
                        seats = target if isinstance(target, tuple) else (target,)
                        self.assertNotIn(seat, seats)


class TestDeterminismIsRealNotVacuous(unittest.TestCase):
    def test_one_seed_reproduces_exactly(self):
        a = resolve_night(SETUP_5, random.Random(99))
        b = resolve_night(SETUP_5, random.Random(99))
        self.assertEqual(a.log, b.log)

    def test_seeds_actually_spread_across_the_deal_space(self):
        """Guards the mutation where the rng is ignored: perfect determinism and a
        broken deal look identical from the reproducibility test alone."""
        deals = {tuple(sorted((s, c.key) for s, c in
                              resolve_night(SETUP_5, random.Random(s)).dealt.items()))
                 for s in range(200)}
        self.assertGreater(len(deals), 50, f"only {len(deals)} distinct deals in 200")


if __name__ == "__main__":
    unittest.main()
