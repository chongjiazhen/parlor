"""Count the two changeling rules errors the powers text was written to fix.

The powers change (2026-08-27, `RULES.md` §The public rules text has to state what
each card DOES) was justified by two misconception counts. **The script that
produced them was never committed**, so the figures `18/200 -> 2/200` and
`4/200 -> 0/200` have no reproducer and nothing in the tree counts either error.
This module is that instrument, and running it retires those four numbers::

    py -3 -m eval.rule_errors                       # both pairs, both errors
    py -3 -m eval.rule_errors --show A              # print the matching sentences

It scores records already on disk. No model, no GPU, no new games.

## The definitions, written down before anything was counted

The queue's standing warning about this row is that a pattern tuned until it
reaches a target figure is fitting the instrument to its answer. So the semantics
are fixed here, the lexical proxy is written from them, and the number is whatever
it is. A proxy that under-counts is reported as under-counting; it is not widened
until the old figure comes back.

**A - `own_card_unmoved`.** The speaker asserts, in the first person, that its own
dawn card is the card it was dealt: an explicit denial that its card moved, or an
explicit claim to still hold or still be it. Every divergence in this game is
silent to the seat it happens to - `night.py` is built around that - so **no seat
is ever entitled to this assertion**, and it scores as an error whether or not the
seat turns out to be right. That is the point of the count: it is about what the
speaker thinks the rules permit it to know.

**B - `switcher_self_swap`.** The speaker was DEALT `switcher`, and asserts in the
first person that its own card moved, or that it no longer knows what it holds.
`SWITCH` exchanges two OTHER seats' cards; the switcher's own card is untouched by
its own act.

**B has a floor it cannot see below, and the old framing did not know this.**
`RULES.md` calls the switcher "the one seat that always knows what it holds" and
that is false: `TAKE` runs BEFORE `SWITCH` in `NIGHT_ORDER`, so the swapper can rob
the switcher. Measured over 4000 nights of the shipped deck, **350/2340 = 15.0%**
of seats dealt `switcher` do diverge (`--floor` recomputes it). A seat correctly
suspecting it was robbed scores identically to a seat that misread its own power,
and no lexical instrument can separate them. So B is an **upper bound**, and a
residue of a few percent is expected rather than evidence the fix failed.

## The control runs first

Same discipline as `eval.gate3_arithmetic`: a figure this file derives is worth
nothing until the pipeline agrees with something already published. Two checks run
before any count, and a failure exits non-zero.

1. Each arm's utterance total against the 200 every published figure is a
   denominator of, and each arm's `fallback_rate` against the run record.
2. The one prior figure that IS reproducible - the 2026-08-27 hand-read re-score of
   error B's AFTER arm recorded in `queue.md`: 4/200, with all four hits
   enumerated there. This instrument returns those four sentences verbatim.

**Its BEFORE arm is a stated disagreement, not a check.** The same hand-read
records 11/200 there; this proxy scores 8. The three it misses are phrasings that
satisfy the definition and no pattern here reaches, and the hand-read's own pattern
was never written down either - so there is nothing to reconcile against, and
widening until the figures met would be fitting the instrument to a target. The
disagreement is printed beside the count rather than tuned away. Direction is
unaffected: error B falls in both pairs.

The 2026-08-27 pair's own `18/200 -> 2/200` and `4/200 -> 0/200` are NOT checked
against, because there is nothing to check them with. They are reported beside this
instrument's numbers as what they are: figures from an instrument that no longer
exists.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys

#: The four records the two pairs live in. The 2026-08-27 pair predates the sampler
#: fix, so its paired comparison stands while its absolute rates do not - both are
#: scored here because the queue asks for both, and the pairs are labelled.
PAIRS: dict[str, tuple[str, str]] = {
    "2026-08-27": ("eval/records/cl-powers-before.jsonl",
                   "eval/records/cl-powers-after.jsonl"),
    "2026-08-28": ("eval/records/cl-powers-before2.json.jsonl",
                   "eval/records/cl-powers-after2.json.jsonl"),
}

#: What every published figure on these runs is a denominator of.
UTTERANCES_PER_ARM = 200

#: The reproducible prior figure - `queue.md`, error B re-scored by hand.
PRIOR_B = {"before": 11, "after": 4}

#: Figures from the instrument that was never committed. Reported, never asserted.
RETIRED = {"A": ("18/200", "2/200"), "B": ("4/200", "0/200")}

_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")

#: First person, and about the speaker's OWN card. A sentence has to clear this
#: before either predicate below is consulted, which is what keeps "seat 2 still
#: has her card" out of both counts.
_ABOUT_ME = re.compile(
    r"\bI\b|\bI'?m\b|\bmy\b|\bme\b", re.I)

#: A - the card is asserted to be where it started.
_UNMOVED = re.compile(
    r"\bmy (?:own )?(?:card|role)\b[^.!?]{0,60}?"
    r"\b(?:did\s?n[o']?t|was\s?n[o']?t|has\s?n[o']?t|were\s?n[o']?t|is still|"
    r"remains?|stayed|unchanged|untouched|safe)\b"
    #: ``still`` has to sit against a HOLDING verb, not merely in the same sentence
    #: as "my card". A looser form scored "the night swapped my card, but I still
    #: know what I was" as an error, and that sentence is correct play: a seat does
    #: know what it was DEALT. Hand-read out of the count 2026-08-28.
    r"|\bI (?:am |'?m )?still (?:the|a|an|holding|hold|have)\b"
    r"|\bI still (?:have|hold|am)\b"
    r"|\bnobody\b[^.!?]{0,40}?\b(?:swapped|took|moved|touched)\b[^.!?]{0,20}?\bmy\b"
    r"|\bno one\b[^.!?]{0,40}?\b(?:swapped|took|moved|touched)\b[^.!?]{0,20}?\bmy\b",
    re.I)

#: B - the card is asserted to have left, or to be unknown. The ``\bwith\b`` is
#: word-bounded on purpose: an unguarded ``with`` matches inside ``without``, and
#: "I swapped two cards without knowing" is the CORRECT reading of the power.
_MOVED = re.compile(
    r"\bI (?:no longer|do\s?n[o']?t|don't) know what I(?:'?m| am)? ?(?:holding|hold|have)\b"
    r"|\bno idea what I(?:'?m| am)? ?(?:holding|hold|have)\b"
    r"|\bmy (?:own )?(?:\w+ )?card\b[^.!?]{0,40}?\b(?:was|got|has been|is now)\b"
    r"[^.!?]{0,20}?\b(?:swapped|moved|taken|exchanged|switched|gone)\b"
    r"|\bI (?:swapped|exchanged|traded|switched)\b[^.!?]{0,30}?\bwith\b"
    #: "one of them has my Meddler card" - a claim that someone ELSE now holds the
    #: speaker's card is a claim that the speaker's card moved, which is the same
    #: assertion in the third person. Added after the first run under-counted the
    #: 2026-08-27 before arm against its hand-read; derived from the definition
    #: above, not tuned toward the figure - the count that came back is reported
    #: whatever it is.
    r"|\b(?:one of them|seat \d+|somebody|someone|whoever|they|he|she)\b"
    r"[^.!?]{0,40}?\b(?:has|have|holds|hold|got|ended up with)\b"
    r"[^.!?]{0,25}?\bmy\b[^.!?]{0,20}?\bcard\b"
    r"|\bmy (?:own )?(?:\w+ )?card\b[^.!?]{0,30}?\b(?:is|went|ended up)\b"
    r"[^.!?]{0,20}?\bwith\b",
    re.I)


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def speaking_seats(rec: dict) -> list[int]:
    """Seat behind each utterance, by position.

    `utterances` is a bare list of strings, so the speaker comes from the
    `discuss` rows of `decision_log`, which are appended in the same order. The
    pairing is CHECKED per game and a mismatch raises rather than mis-attributing
    every hit in that game by one seat - the same reason `eval.gate3_arithmetic`
    checks its proposal/vote reconstruction instead of trusting it.
    """
    seats = [d["seat"] for d in rec["decision_log"] if d["phase"] == "discuss"]
    if len(seats) != len(rec["utterances"]):
        raise ValueError(
            f"game {rec.get('game')}: {len(seats)} discuss decisions against "
            f"{len(rec['utterances'])} utterances - cannot attribute speakers")
    return seats


def sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE.split(text) if s.strip()]


def _first_match(text: str, pattern: re.Pattern) -> str | None:
    """The first sentence that is about the speaker AND matches ``pattern``.

    **The gap classes in both patterns are ``[^.!?]``, and that is what actually
    stops a predicate spanning a sentence boundary** - so "Someone took my card.
    Seat 3 remains unchanged." cannot pair the two halves into a hit. Splitting
    here is belt-and-braces for the same property, and it is where a future
    alternative that is not itself first-person-anchored would be caught. Both were
    mutation-checked 2026-08-28: the character class killed its test, the split did
    not, and the redundancy is recorded rather than dressed up as two guards.
    """
    for sent in sentences(text):
        if _ABOUT_ME.search(sent) and pattern.search(sent):
            return sent
    return None


def score_arm(recs: list[dict]) -> dict:
    """Both errors over one arm, with the matching sentences kept for hand-reading.

    An utterance counts at most once per error, and ``either`` is their union - so
    an utterance carrying both is one, not two, which is what the published
    ``either`` row is a rate of.
    """
    out = {"utterances": 0, "A": [], "B": [], "either": 0,
           "switcher_utterances": 0, "per_game": [],
           "decisions": 0, "fallbacks": 0}
    for rec in recs:
        seats = speaking_seats(rec)
        dealt = {int(k): v for k, v in rec["dealt"].items()}
        out["decisions"] += rec.get("decisions", 0)
        out["fallbacks"] += rec.get("fallbacks", 0)
        game = {"utterances": 0, "A": 0, "B": 0, "either": 0}
        for seat, text in zip(seats, rec["utterances"]):
            out["utterances"] += 1
            game["utterances"] += 1
            is_switcher = dealt.get(seat) == "switcher"
            if is_switcher:
                out["switcher_utterances"] += 1
            hit_a = _first_match(text, _UNMOVED)
            #: B is conditioned on the DEAL, not on what the seat claims to be. A
            #: seat claiming to be the switcher without holding it is lying or
            #: mistaken about its identity, which is play, not a rules error.
            hit_b = _first_match(text, _MOVED) if is_switcher else None
            if hit_a:
                out["A"].append((rec.get("game"), seat, hit_a))
                game["A"] += 1
            if hit_b:
                out["B"].append((rec.get("game"), seat, hit_b))
                game["B"] += 1
            if hit_a or hit_b:
                out["either"] += 1
                game["either"] += 1
        out["per_game"].append(game)
    return out


def paired_delta(before: dict, after: dict, key: str = "either",
                 draws: int = 10000, seed: int = 11) -> tuple[float, float, float]:
    """After-minus-before rate for ``key``, with a game-bootstrap CI.

    Games are the resampling unit, matching the scorer's convention elsewhere in
    this repo: utterances within a game share a deal and a table, so resampling
    utterances would understate the interval. The two arms are resampled
    independently - they are separate runs on the same seeds, not paired
    observations of one unit.
    """
    def rate(games: list[dict]) -> float:
        hits = sum(g[key] for g in games)
        seen = sum(g["utterances"] for g in games)
        return hits / seen if seen else 0.0

    point = rate(after["per_game"]) - rate(before["per_game"])
    rng = random.Random(seed)
    deltas = []
    for _ in range(draws):
        b = [rng.choice(before["per_game"]) for _ in before["per_game"]]
        a = [rng.choice(after["per_game"]) for _ in after["per_game"]]
        deltas.append(rate(a) - rate(b))
    deltas.sort()
    return point, deltas[int(0.025 * draws)], deltas[int(0.975 * draws)]


def switcher_divergence_floor(nights: int = 4000, seed: int = 7) -> tuple[int, int]:
    """How often a seat dealt ``switcher`` is robbed anyway - error B's blind floor.

    Resolves nights only; no model and no day phase. Imported lazily so scoring
    records never needs the game package to be importable.
    """
    from games.changeling.night import resolve_night
    from games.changeling.roles import SETUP_5

    rng = random.Random(seed)
    total = diverged = 0
    for _ in range(nights):
        night = resolve_night(SETUP_5, rng, choose=None)
        for seat, card in night.dealt.items():
            if card.key != "switcher":
                continue
            total += 1
            if night.truth[seat].key != night.belief[seat].key:
                diverged += 1
    return diverged, total


def control(pairs: dict[str, dict]) -> list[str]:
    """Every reproduction check, as a list of failure lines. Empty means agreed."""
    bad: list[str] = []
    for label, arms in pairs.items():
        for arm, scored in arms.items():
            if scored["utterances"] != UTTERANCES_PER_ARM:
                bad.append(f"{label} {arm}: {scored['utterances']} utterances, "
                           f"every published figure is out of {UTTERANCES_PER_ARM}")
    hand_read = pairs.get("2026-08-27")
    if hand_read:
        got = len(hand_read["after"]["B"])
        if got != PRIOR_B["after"]:
            bad.append(f"2026-08-27 after: error B scores {got}, the hand-read "
                       f"re-score in queue.md says {PRIOR_B['after']} and "
                       f"enumerates all four")
    return bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--show", choices=["A", "B"],
                    help="print every matching sentence for one error")
    ap.add_argument("--floor", action="store_true",
                    help="recompute error B's blind floor over 4000 nights")
    args = ap.parse_args(argv)

    pairs: dict[str, dict] = {}
    for label, (before, after) in PAIRS.items():
        pairs[label] = {"before": score_arm(load(before)),
                        "after": score_arm(load(after))}

    print("== control ==")
    bad = control(pairs)
    for line in bad:
        print("FAIL", line)
    if not bad:
        print("ok  utterance denominators agree, and the 2026-08-27 after arm "
              "returns the hand-read's four hits verbatim")
    disagree = len(pairs["2026-08-27"]["before"]["B"])
    print(f"--  stated disagreement: 2026-08-27 before scores {disagree} against the "
          f"hand-read's {PRIOR_B['before']}.\n    Not reconciled - see the module "
          f"docstring. The direction of the fall is unaffected.")

    print("\n== counts, out of 200 utterances per arm ==")
    print(f"{'pair':<12} {'arm':<7} {'A unmoved':>12} {'B self-swap':>14} "
          f"{'either':>12} {'fallback':>10}")
    for label, arms in pairs.items():
        for arm, s in arms.items():
            n = s["utterances"]
            fb = s["fallbacks"] / s["decisions"] if s["decisions"] else 0.0
            print(f"{label:<12} {arm:<7} "
                  f"{len(s['A']):>3} {len(s['A']) / n:>7.1%} "
                  f"{len(s['B']):>4} {len(s['B']) / n:>8.1%} "
                  f"{s['either']:>4} {s['either'] / n:>6.1%} "
                  f"{fb:>9.2%}")
        point, lo, hi = paired_delta(arms["before"], arms["after"])
        print(f"{'':<12} {'delta':<7} either {point:+.1%} "
              f"[{lo:+.1%}, {hi:+.1%}], 10k game bootstrap")

    print("\n== retired, from the instrument that was never committed ==")
    for key, (before, after) in RETIRED.items():
        print(f"  error {key}: {before} -> {after}   (no reproducer; do not quote)")

    if args.floor:
        diverged, total = switcher_divergence_floor()
        print(f"\n== error B's blind floor ==\n  {diverged}/{total} = "
              f"{diverged / total:.1%} of seats dealt switcher are robbed by TAKE "
              f"anyway,\n  so a correct suspicion is indistinguishable from the "
              f"misconception and B is an upper bound.")

    if args.show:
        print(f"\n== error {args.show}, every match ==")
        for label, arms in pairs.items():
            for arm, s in arms.items():
                for game, seat, sent in s[args.show]:
                    print(f"  {label} {arm} g{game} seat {seat}: {sent}")

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
