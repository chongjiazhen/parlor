"""What seats SAY they are, against what the night actually dealt them. No GPU.

    py -3 -m eval.changeling_claims                          # the S2 records
    py -3 -m eval.changeling_claims --record <path>.json     # any changeling run
    py -3 -m eval.changeling_claims --show 20                # with example claims

**Why this exists.** `docs/open-arms.md` §"changeling feels random" lists four
levers for a rung a person reported as arbitrary to play, and refuses all four
until an instrument exists - a fix to an unmeasured complaint re-baselines the
numbers that DO exist. One of the four is measurable off records already on disk
and is the sharpest of them: *village seats have no reason to bluff*. If a village
seat never says anything untrue about itself, the table is playing the collapsed
game, where every contradiction is mechanical and no seat can tell a swap from a
lie. That finding stands on its own, before any deck or prompt changes.

**The two claim shapes, which are never pooled.** This game splits what one
sentence means in `cabal`, where a role is a seat's role from the deal to the end:

- a **deal claim** - "I went to sleep as the Seer" - is about the night that has
  already happened.
- a **present claim** - "I am the Seer" - is about now, in a game whose cards move,
  so it is a claim the seat itself often cannot settle.

Both are scored the same way - the claim names a card this seat was actually shown
itself as, `{dealt, belief}` - and never against the card it holds at dawn, which
no seat is told. **Scoring a deal claim against `dealt` alone was the first draft
and the records refused it:** S14 changed the self-line on 2026-08-31 and every
record on disk predates it, so a seat naming its post-night belief is often quoting
the referee. `Claim.true` carries that measurement. Which of the two cards a deal
claim named is reported beside the rate, never folded into it.

The two shapes keep separate rates because they are different sentences with
different reasons to be false, and one rate over both would answer neither.

**Honest, lying, or wrong are three outcomes and only two are separable here.** A
claim that names neither card the seat saw is untrue - that is settled. Whether the
seat lied or misremembered is not on the record and this file does not guess. What
it can add is the third column: how many of those untrue claims happen to name the
card the seat HOLDS at dawn, which is a seat asserting something it had no way to
know and being right anyway.

**The chance bar is exact, like `eval.quorum_claims`'.** A seat naming a card
uniformly at random from the deck's distinct cards - six in `SETUP_5` - names one
it was shown `|{dealt, belief}|/6` of the time: 1/6 for a seat the night showed
nothing new, 2/6 for one it did. That is what "random" means here, and it is
arithmetic off the deck rather than a measured arm.

**What the matcher can and cannot see.** The claim shapes are
`eval.audit_decisions`', the same two rules S13 and S16 count cabal with, so there
is one claim matcher in this repo and not two. They are narrow by construction: an
oblique claim ("nobody else could have seen the centre - work it out") is invisible
to them, so every count here is a LOWER bound. The instrument prints the size of
its own blind spot - utterances that name a deck card in some shape the rules do
not read - so a reader can see what the bound is worth rather than take the count
for the corpus.

**Not a gate and not a verdict.** No criterion binds this, nothing here voids a
run, and no bar is pre-committed. It is a count with a denominator and its own
controls. A run whose fallback rate is over the void bar is still counted, printed
in full and returned as exit 3, because a figure this repo publishes must be
reproducible from a record even when the record refuses it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

from core import integrity
from core.stats import bootstrap_ci, wilson
from eval.audit_decisions import (CLAIM_RULES, DEALT_CLAIM_RULES,
                                  claims_dealt_role, claims_own_role)
from games.changeling.roles import SETUPS, THEMES

#: S2, the 200-game run this was written against. Same default as `eval.deduction`,
#: whose per-game reading is the other half of the same complaint.
DEFAULT = "eval/records/s2.json"

#: A published speech line, which is where the seat number lives.
SPEECH = re.compile(r"Seat (\d+): ?(.*)", re.S)


@dataclass(frozen=True)
class Claim:
    """One card a seat named about itself, in one utterance."""

    game: object
    seat: int
    index: int                  # position in the game's utterance list
    shape: str                  # "dealt" | "present"
    card: str                   # the deck key the claim named
    dealt: str
    belief: str
    truth: str
    said: str

    @property
    def saw(self) -> tuple[str, ...]:
        """The cards this seat legally holds a self-fact about: the one it was
        dealt, and the one the night last showed it. Usually the same card."""
        return tuple(dict.fromkeys((self.dealt, self.belief)))

    @property
    def true(self) -> bool:
        """Both shapes score the same way: the claim names a card this seat was
        actually shown itself as.

        **It is deliberately NOT "a deal claim names the deal", and the records are
        why.** S14 changed the model-facing self-line on 2026-08-31, from the seat's
        post-night belief phrased as a sleep-state claim to the card actually dealt.
        Every changeling record on disk predates it, so in those runs a seat that
        says "I went to sleep as the Thief" while `dealt` says `swapper` is often
        repeating the sentence the referee handed it. Measured on S2: of 74 deal
        claims by seats whose belief and deal differ, 65 name the belief and 1 names
        the deal. Scoring those as untrue would report the referee's own wording as
        a table full of liars, and no field on the record says which wording a run
        was played under.

        So the scored question is the one both wordings answer the same way - did
        the seat name a card it was ever shown - and which of the two it named is
        reported beside the rate rather than folded into it (`names_deal`).
        """
        return self.card in self.saw

    @property
    def names_deal(self) -> bool:
        """The claim names the card actually DEALT, rather than the one the night
        later showed this seat. The two are the same for every seat the night did
        not show a new card to."""
        return self.card == self.dealt

    @property
    def lucky(self) -> bool:
        """Untrue on what the seat saw, and right about the card it holds at dawn.
        Only reachable by a present claim; a deal claim is about the past, which
        no swap can retrofit."""
        return not self.true and self.card == self.truth

    @property
    def believes_pack(self) -> bool:
        """Which side the seat thinks it is on - the partition the "village seats
        have no reason to bluff" reading needs. NOT the side it wins with: a seat
        robbed after it looked is a villager who will play the whole day as a wolf,
        and grading its speech by its dawn card would score it for a side it does
        not know it is on."""
        return self.belief == "pack"


def load(path: str) -> tuple[dict, list[dict]]:
    """The published summary and the per-game records it was computed from."""
    with open(path, encoding="utf-8") as fh:
        summary = json.load(fh)
    with open(f"{path}.jsonl", encoding="utf-8") as fh:
        games = [json.loads(line) for line in fh if line.strip()]
    return summary, games


def deck_names(game: dict) -> dict[str, str]:
    """`card key -> the name this run's skin printed`, for the cards in the deck.

    Both the skin's word and the functional key are matched later; the key is what
    a record and the rules speak, the skin's word is what a model in a themed run
    can actually say. A run that names no known theme is refused by `control`, not
    silently narrowed to the keys no player ever saw - that narrowing is exactly the
    0/1290 cabal published once.
    """
    setup = SETUPS[len(game["truth"])]
    theme = THEMES.get(str(game.get("theme") or ""))
    keys = dict.fromkeys(card.key for card in setup.deck)
    return {k: (theme.card_names.get(k, k) if theme else k) for k in keys}


def speeches(game: dict) -> list[tuple[int, str]]:
    """`(seat, what the table saw)` per discussion turn, from the public record.

    Read off `public_events` rather than `utterances` because the published line
    carries its own seat: the flat `utterances` list needs a join against the
    decision log to say who spoke, and a join is a thing that can be wrong. The
    control checks the two agree; this is the source that cannot disagree with
    itself. It also settles the other difference - records written before
    2026-08-27 stored the policy's raw string in `utterances` while publishing a
    truncated one, so the two corpora are not the same text and only one of them
    was ever in front of a model.
    """
    out = []
    for tag, text in game.get("public_events", []):
        if tag != "speech":
            continue
        m = SPEECH.match(str(text))
        if m:
            out.append((int(m.group(1)), m.group(2)))
    return out


def discuss_decisions(game: dict) -> list[dict]:
    return [d for d in game.get("decision_log", []) if d.get("phase") == "discuss"]


def control(games: list[dict]) -> list[str]:
    """Everything that has to hold before a single claim is counted.

    Each check answers a way this instrument could report a confident wrong number
    with nothing in the output to say so.
    """
    bad: list[str] = []
    for i, game in enumerate(games):
        name = f"game {game.get('game', i)}"
        said = speeches(game)
        decisions = discuss_decisions(game)

        # 1. Seat attribution, from two independent sources. Speech carries its own
        #    seat; the decision log carries the speaking order. A claim scored
        #    against the wrong seat's deal is worse than no claim at all.
        if [s for s, _ in said] != [d.get("seat") for d in decisions]:
            bad.append(f"{name}: the published speech order and the decision log "
                       f"disagree about who spoke ({len(said)} vs "
                       f"{len(decisions)} turns)")

        # 2. The skin, and the language it declares. An unruled language has no
        #    claim shape written down and would read as a table that never claimed
        #    anything - so it is refused, never floored (`claims_dealt_role`).
        theme = THEMES.get(str(game.get("theme") or ""))
        if theme is None:
            bad.append(f"{name}: theme {game.get('theme')!r} is not a known skin, "
                       f"so the names the seats actually spoke are unknown")
        elif theme.lang not in CLAIM_RULES or theme.lang not in DEALT_CLAIM_RULES:
            bad.append(f"{name}: skin {theme.name!r} declares language "
                       f"{theme.lang!r}, which has no claim rule; a count here "
                       f"would be a zero that reads like clean play")

        # 3. The deck. A seat count with no setup, or a card no setup deals, means
        #    the chance bar below is computed off the wrong deck.
        if len(game["truth"]) not in SETUPS:
            bad.append(f"{name}: no setup for {len(game['truth'])} seats")
            continue
        names = deck_names(game)
        for field in ("dealt", "belief", "truth"):
            for seat, key in game[field].items():
                if key not in names:
                    bad.append(f"{name}: seat {seat} {field} {key!r} is not a card "
                               f"in this deck")

        # 4. Two skin words the matcher cannot tell apart make every claim naming
        #    either one ambiguous, silently.
        for key, word in names.items():
            for other, word2 in names.items():
                if key != other and re.search(rf"\b{re.escape(word)}\b", word2,
                                              re.I):
                    bad.append(f"{name}: skin word {word2!r} contains {word!r}, so "
                               f"a claim naming one matches the other")
    return bad


def integrity_control(summary: dict, games: list[dict]) -> list[str]:
    """The instrument reads the same records the scorer did.

    Derived decision and fallback counts against the ones the run published. A
    disagreement means the JSONL and the summary are not the same run - which would
    put the claims in this file beside a fallback rate that does not describe them.
    """
    published = summary.get("score", {}).get("integrity", {})
    bad = []
    for label, derived, key in (
            ("decisions", sum(g.get("decisions", 0) for g in games), "decisions"),
            ("fallbacks", sum(g.get("fallbacks", 0) for g in games), "fallbacks")):
        if published.get(key) != derived:
            bad.append(f"{label}: derived {derived}, summary {published.get(key)}")
    return bad


def claims_of(game: dict) -> tuple[list[Claim], int, int]:
    """Every self-claim in one game, plus the two denominators around it.

    Returns `(claims, scored utterances, utterances that named a card in no shape
    this file reads)`. Utterances the random fallback wrote are excluded from all
    three - the fallback's four canned lines are not a model's speech, and counting
    them would put the control arm's vocabulary in a model's honesty rate.
    """
    names = deck_names(game)
    theme = THEMES.get(str(game.get("theme") or ""))
    lang = theme.lang if theme is not None else "en"
    fell_back = [bool(d.get("fell_back")) for d in discuss_decisions(game)]

    out: list[Claim] = []
    scored = blind = 0
    for index, (seat, said) in enumerate(speeches(game)):
        if index < len(fell_back) and fell_back[index]:
            continue
        scored += 1
        seen: set[tuple[str, str]] = set()
        named = False
        for key, word in names.items():
            for candidate in dict.fromkeys((word, key)):
                if claims_dealt_role(said, candidate, lang):
                    seen.add(("dealt", key))
                if claims_own_role(said, candidate, lang) == "claim":
                    seen.add(("present", key))
                if re.search(rf"\b{re.escape(candidate)}\b", said, re.I):
                    named = True
        if named and not seen:
            blind += 1
        for shape, key in sorted(seen):
            out.append(Claim(
                game=game.get("game"), seat=seat, index=index, shape=shape,
                card=key, dealt=game["dealt"][str(seat)],
                belief=game["belief"][str(seat)], truth=game["truth"][str(seat)],
                said=said))
    return out, scored, blind


def chance(claims: list[Claim], deck: int) -> float | None:
    """The rate a seat naming a card at random would score on THESE claims.

    Per claim, because the target is `{dealt, belief}` and that set has one member
    or two depending on what the night did to the seat - so the bar moves with the
    mix of claims in front of it, and a single constant would be right only for a
    run where no seat's card ever moved.
    """
    if not claims:
        return None
    return sum(len(c.saw) / deck for c in claims) / len(claims)


def _rate(hits: int, total: int) -> str:
    if not total:
        return "     -"
    lo, hi = wilson(hits, total)
    return f"{hits}/{total} = {hits / total:.1%} [{lo:.1%}, {hi:.1%}]"


def report(summary: dict, games: list[dict], show: int = 0) -> list[str]:
    per_game = [claims_of(g) for g in games]
    claims = [c for cs, _, _ in per_game for c in cs]
    scored = sum(s for _, s, _ in per_game)
    blind = sum(b for _, _, b in per_game)
    spoken = sum(len(speeches(g)) for g in games)
    deck = len(deck_names(games[0]))

    i = summary.get("score", {}).get("integrity", {})
    share = f"  ({blind / scored:.1%} of the model's)" if scored else ""
    out = [f"stated self-claims over {len(games)} games",
           "",
           f"  utterances                {spoken}",
           f"    written by the model    {scored}",
           f"    written by the fallback {spoken - scored}  (excluded; the random "
           f"policy's four canned lines are not speech)",
           f"    naming a card in a shape the rules do not read  {blind}{share}",
           "      every count below is a LOWER bound by exactly this much",
           "",
           f"  run fallback rate         {i.get('fallback_rate', 0):.2%} "
           f"(voids a verdict above {integrity.VOID_BAR:.0%}; this is not a "
           f"verdict)",
           ""]

    for shape, title in (("dealt", "deal claims - \"I went to sleep as X\""),
                         ("present", "present claims - \"I am X\"")):
        rows = [c for c in claims if c.shape == shape]
        hits = sum(1 for c in rows if c.true)
        bar = chance(rows, deck)
        out += [f"  {title}",
                "    true means the claim names a card this seat was shown itself "
                "as - the deal, or what the night later showed it",
                f"    true    {_rate(hits, len(rows))}"]
        if bar is not None:
            out.append(f"    chance  {bar:.1%}  (a seat naming one of the deck's "
                       f"{deck} cards at random)")
        ci = bootstrap_ci([[c for c in cs if c.shape == shape]
                           for cs, _, _ in per_game],
                          lambda gs: (lambda flat: sum(c.true for c in flat)
                                      / len(flat) if flat else None)(
                              [c for g in gs for c in g]))
        if ci:
            out.append(f"    over GAMES rather than claims: [{ci[0]:.1%}, "
                       f"{ci[1]:.1%}]")
        village = [c for c in rows if not c.believes_pack]
        pack = [c for c in rows if c.believes_pack]
        out += [f"    by the side the seat believes it is on",
                f"      village  {_rate(sum(1 for c in village if c.true), len(village))}",
                f"      pack     {_rate(sum(1 for c in pack if c.true), len(pack))}"]
        if shape == "dealt":
            # The half of a true deal claim that is wording-dependent. Every record
            # on disk predates S14, whose self-line change moved which of these two
            # cards the referee itself called the one the seat went to sleep as.
            moved = [c for c in rows if len(c.saw) > 1]
            out += [f"    of the {len(moved)} by seats the night showed a NEW card, "
                    f"{sum(1 for c in moved if c.names_deal)} name the deal and "
                    f"{sum(1 for c in moved if c.true and not c.names_deal)} the "
                    f"card shown later",
                    "      pre-S14 the self-line called the later card the one the "
                    "seat went to sleep as, so",
                    "      scoring these against the deal alone would report the "
                    "referee's wording as lying"]
        if shape == "present":
            lucky = sum(1 for c in rows if c.lucky)
            out.append(f"    of the untrue, {lucky} name the card the seat HOLDS at "
                       f"dawn - right, and unknowable to it")
        out.append("")

    # The one word in this skin that is also the side's word. Stated rather than
    # dropped: the card is real and seats do claim it, but "I'm a Villager" is a
    # sentence about a side as often as about a card, and a reader is owed the
    # count with it out.
    side_word = [c for c in claims if c.card == "bystander"]
    if side_word:
        out.append(f"  sensitivity - {len(side_word)} claims name `bystander`, "
                   f"whose folk word is also the side's word")
        for shape in ("dealt", "present"):
            rest = [c for c in claims
                    if c.card != "bystander" and c.shape == shape]
            out.append(f"    {shape} claims with them out: "
                       f"{_rate(sum(1 for c in rest if c.true), len(rest))}")
        out.append("")

    if show:
        out.append(f"  examples - {min(show, len(claims))} of {len(claims)} claims")
        for c in claims[:show]:
            verdict = "true " if c.true else ("LUCKY" if c.lucky else "untrue")
            out.append(f"    [{verdict}] {c.shape:7s} seat {c.seat} claims "
                       f"{c.card} (dealt {c.dealt}, saw {'/'.join(c.saw)}, holds "
                       f"{c.truth}): {c.said[:90]}")
        out.append("")

    out += ["NOT a gate and not a verdict. No criterion binds it, no bar is "
            "pre-committed,",
            "and a rules or prompt change re-baselines every number above.",
            "The four levers it reads for are in docs/open-arms.md, under "
            "\"changeling feels random\"."]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", default=DEFAULT,
                    help="summary path; its .jsonl sibling holds the games")
    ap.add_argument("--show", type=int, default=0,
                    help="print this many example claims")
    ap.add_argument("--json", action="store_true",
                    help="one claim per line, for a reader that wants the rows")
    args = ap.parse_args(argv)

    try:
        summary, games = load(args.record)
    except FileNotFoundError as exc:
        print(f"no record at {exc.filename} - a run's summary and its .jsonl "
              f"sibling are what this reads.")
        return 1
    if not games:
        print(f"{args.record} holds no games.")
        return 1

    # In --json mode the control still runs and still refuses, but it reports on
    # stderr: a reader piping rows into another tool should get rows, not a header
    # it has to strip back off.
    out = sys.stderr if args.json else sys.stdout
    print("instrument control - seat attribution, skin, deck and the scorer's own "
          "counts", file=out)
    bad = control(games) + integrity_control(summary, games)
    for line in bad[:5]:
        print(f"  DISAGREES: {line}", file=out)
    if bad:
        print(f"  {len(bad)} disagreement(s). Every claim below would be scored "
              f"against the wrong seat, the wrong deck or the wrong run, so "
              f"nothing is printed.", file=out)
        return 1
    print(f"  held across {len(games)} games\n", file=out)

    if args.json:
        for game in games:
            for claim in claims_of(game)[0]:
                print(json.dumps({"game": claim.game, "seat": claim.seat,
                                  "shape": claim.shape, "card": claim.card,
                                  "dealt": claim.dealt, "belief": claim.belief,
                                  "truth": claim.truth, "true": claim.true,
                                  "said": claim.said}))
        return 0

    print("\n".join(report(summary, games, args.show)))

    rate = summary.get("score", {}).get("integrity", {}).get("fallback_rate", 0.0)
    if rate > integrity.VOID_BAR:
        print(f"\nREFUSED: {rate:.2%} of decisions fell back to random, over the "
              f"{integrity.VOID_BAR:.0%} bar. The arithmetic above is printed in "
              f"full - a published figure must be reproducible from its record - "
              f"and it is not readable as a measurement of a model.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
