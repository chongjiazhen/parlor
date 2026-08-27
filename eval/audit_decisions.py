"""Mine a finished run for decisions that are wrong on their own terms.

Not a judgement grader. There is no ground truth for "was that a good read", so
scoring reasonableness at scale is either vibes or an LLM judge importing its own
failure modes. What IS checkable is the narrower class: moves that are provably
wrong, or strictly dominated, GIVEN WHAT THAT SEAT KNEW. Three such bugs were
found by hand on the 2026-08-25 run and every one turned out to be a scorer
confound rather than a play-quality curiosity:

  - a hunt naming the hunter's own seat (fixed; this file now regression-tests it)
  - both evils failing a mission that needed one fail, on ~39-45% of the sunk
    missions the game continued past
  - a seat reasoning about itself in the third person

That is the pattern worth automating. A confound inflates or deflates a gate
number without ever showing up as a fallback, so it reads as signal.

Checks are labelled PROOF or HEURISTIC and the two never share a total. A PROOF
check is a rules fact. A HEURISTIC check is a string match that needs a human to
confirm, and its count is a starting point for reading, not a finding.

Usage::

    python -m eval.audit_decisions eval/records/hunt20-q36.json.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter

from games.cabal.roles import ROLES_BY_KEY, THEMES, Role, known_allies


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _assignment(game: dict) -> dict[int, Role]:
    """The recorded ``seat -> role key`` map, back as roles.

    A record stores keys; every knowledge question needs the flags behind them. An
    unknown key is skipped rather than guessed - a checker that invents a role model
    reports a confident wrong answer, which is worse than reporting nothing.
    """
    return {int(s): ROLES_BY_KEY[k]
            for s, k in (game.get("assignment") or {}).items()
            if k in ROLES_BY_KEY}


def _says(text: str, name: str) -> bool:
    """Did ``text`` name ``name``?

    Word-boundary for a Latin name, plain substring for anything else. ``\\b`` is a
    transition between a word and a non-word character, and CJK characters are word
    characters with no spaces between them - so ``\\b思想警察\\b`` never matches
    inside an ordinary Chinese sentence, and the `1984-cn` skin would go silently
    unchecked. Which is exactly the failure mode this check was already in.
    """
    if not name:
        return False
    if name.isascii():
        return re.search(rf"\b{re.escape(name)}\b", text, re.I) is not None
    return name in text


# ---- PROOF checks ---------------------------------------------------------

def hunt_named_impossible(games: list[dict]) -> tuple[int, int, list[str]]:
    """A hunt on a seat the hunter KNOWS is evil - itself, or the night's ally.

    The seer is good, so no seat known to be evil can be it. Refused by
    ``validate_hunt`` since 2026-08-26, so a non-zero count here on a later run is
    a regression, not a discovery.

    "The night's ally" is read from ``known_allies``, the same function the referee
    validates against, and never from a list of evil role keys. The first version
    listed ``{mimic, hunter, agent}`` and treated every other evil as known - right
    at 5 seats, wrong the moment a ``stray`` is dealt, because that seat is named to
    nobody. It would have flagged a perfectly legal hunt as a regression, in a
    checker whose whole contract is that a non-zero count means the referee broke.
    Same trap as the hardcoded 1/3 baseline, in the other direction.
    """
    bad, total, notes = 0, 0, []
    for g in games:
        h = g.get("hunt")
        if not h:
            continue
        total += 1
        hunter, target = h.get("hunter"), h.get("target")
        assignment = _assignment(g)
        if hunter not in assignment:
            notes.append(f"game {g.get('game')}: assignment does not cover the "
                         f"hunter (seat {hunter}) - not checked")
            continue
        allies = known_allies(assignment, hunter)
        if target == hunter:
            bad += 1
            notes.append(f"game {g.get('game')}: hunter {hunter} named ITSELF")
        elif target in allies:
            bad += 1
            notes.append(f"game {g.get('game')}: hunter {hunter} named ally {target}")
    return bad, total, notes


def over_sabotage(games: list[dict]) -> tuple[int, int, list[str]]:
    """More fail cards than the mission required.

    NOT an error, and the first version of this file was wrong to call it one.
    Two evils on one mission decide independently and there is no private channel
    between them - that is a rule of the game, not an oversight. Playing success
    is only better IF the other one fails, and nothing tells you it will. It is an
    anti-coordination game with a mixed equilibrium, so some double-fail rate is
    irreducible and the ideal count is not zero.

    What is still worth counting: a focal point exists that needs no channel at
    all - "the lower-numbered evil on this team plays fail" is derivable by both
    seats from the public proposal alone. Schelling points do not require
    communication. A pair that finds any such convention drives this near zero
    without ever signalling; the observed 39-45% of payable sunk missions says the
    model is not finding one. That is a fact about reasoning, not a rules violation, which
    is why it sits under COST rather than PROOF.

    **Denominator: SUNK missions on which the game continued.** Two corrections in
    one, and they pull opposite ways.

    Sunk, because a redundant fail card can only be played on a mission that sank -
    ``fails > need`` implies it - so scoring it against every resolution mixes in
    missions where the move was unavailable. That is the "share of sunk" figure the
    repo already quotes, now computed rather than derived by hand.

    Continuing, because a double fail on evil's THIRD failed mission is costless:
    the game ends on that resolution, the identification is never paid for, and the
    redundant card weakly insures against a miscount. Those rows are not
    coordination failures. They are reported as their own line rather than dropped
    silently - "12 of 27, and 2 more that were free" says what happened.
    """
    bad, total, free, notes = 0, 0, 0, []
    for g in games:
        failed_missions = 0
        for ev in g.get("public_events", []):
            m = re.search(r"(\d+) fail\(s\), need (\d+) -> (SUCCESS|FAIL)", str(ev))
            if not m:
                continue
            fails, need = int(m.group(1)), int(m.group(2))
            if m.group(3) != "FAIL":
                continue
            failed_missions += 1
            if failed_missions >= 3:      # this resolution ENDS the game
                if fails > need:
                    free += 1
                    notes.append(f"game {g.get('game')}: {fails} fails on the "
                                 "game-ENDING mission - free, not counted")
                continue
            total += 1
            if fails > need:
                bad += 1
                notes.append(f"game {g.get('game')}: {fails} fails where {need} sufficed")
    if free:
        # first, not last: `--show` truncates the tail, and a caveat nobody reads
        # is the same as no caveat
        notes.insert(0, f"{free} redundant fail(s) EXCLUDED as costless - played "
                        "on the mission that ended the game")
    return bad, total, notes


def approved_a_team_it_knew_was_tainted(games: list[dict]) -> tuple[int, int, list[str]]:
    """A GOOD seat approving a team it was told carries an evil.

    Also NOT an error, and calling it one was the same mistake. A seer that always
    rejects exactly the tainted teams has a perfect tell, and the hunter's whole
    job is finding the seer - so buying concealment with mission EV can be correct
    play. The model appears to do it deliberately: one seer's private reasoning in
    the seed-1000 run reads "I must support [1,4] ... and vote yes - without
    revealing I know who's darkness."

    Counted because it PRICES the concealment and because it bounds a gate:
    "good approves clean vs tainted" scores a concealing seer as though it were a
    bad one, so gate #3a's headline number and its blind-seat half are not
    measuring the same thing. Blind seats have nothing to hide, which is why that
    split is the sturdier number.

    Checked against the one case where it is unambiguously forced: at four
    rejections a fifth loses outright. Walking the reject streak alongside the
    votes on seed 1000, 0 of the 7 were under that pressure - so these were free
    choices, whether strategic or careless, and this count cannot tell those apart.
    """
    bad, total, notes = 0, 0, []
    for g in games:
        for v in g.get("votes", []):
            if v.get("seat_is_evil") or not v.get("knew_evil_on_team"):
                continue
            total += 1
            if v.get("approved"):
                bad += 1
                notes.append(f"game {g.get('game')}: good seat {v.get('seat')} "
                             f"approved a team it knew was tainted")
    return bad, total, notes


# ---- HEURISTIC checks -----------------------------------------------------

def third_person_self(games: list[dict]) -> tuple[int, int, list[str]]:
    """A seat writing about itself as if it were someone else.

    The seed-1000 self-target hunt reasoned "Seat 4 has opposed every
    Party-successful team..." while BEING seat 4.

    Naming your own seat is NOT the error - "I'm seat 1, Outer Party" is correct
    and common. The first version of this check matched any mention and fired 51
    times with the first three all correct self-identification, which is a worse
    failure than no check: a noisy red reads as a finding. So first-person framings
    are stripped, and only a leftover bare mention counts.
    """
    first_person = re.compile(
        r"\b(?:i am|i'm|me|myself|as|being)[, ]+seat \d+|\bseat \d+[ ,]+(?:here\b|myself\b)"
        r"|\(\s*seat \d+\s*\)", re.I)
    bad, total, notes = 0, 0, []
    for g in games:
        for d in g.get("decision_log", []):
            think = str(d.get("think", ""))
            if not think:
                continue
            total += 1
            seat = d.get("seat")
            stripped = first_person.sub(" ", think)
            if re.search(rf"\bseat {seat}\b", stripped, re.I):
                bad += 1
                notes.append(f"game {g.get('game')} t{d.get('turn')} seat {seat} "
                             f"({d.get('phase')}): {think[:90]}")
    return bad, total, notes


def outed_own_role_in_public(games: list[dict]) -> tuple[int, int, list[str]]:
    """A seat naming its own role in the PUBLIC channel.

    Not a gate #1 leak - what a seat says is gameplay, true or false, and the
    invariant is explicit that a lie there is legal. But an evil seat announcing
    itself hands the table the game, and if it happens often the good side's
    discrimination number is measuring that rather than deduction.

    Naive substring, deliberately: the same reasoning as find_leaks. A false
    positive is a line a human reads; a false negative is a blind spot.

    **Matches the THEME name as well as the functional key, and that is the whole
    point of the check working at all.** Speech is rendered in whatever skin the run
    used: on the shipping `1984-en` face a seat outing itself says "Thought Police"
    or "Doublethinker" and never once says "seer" or "mimic". The reported 0/1290
    on the seed-1000 runs was near-zero BY CONSTRUCTION - it was matching vocabulary
    the players had no way to produce - and supported nothing. A run's theme is on
    the record, so the names are a lookup, not a guess.

    A record with no theme is checked on the functional key alone and SAYS so;
    silently narrowing the match is how the 0/1290 happened the first time.
    """
    bad, total, notes = 0, 0, []
    unskinned = 0
    for g in games:
        roles = {int(s): k for s, k in (g.get("assignment") or {}).items()}
        theme = THEMES.get(str(g.get("theme") or ""))
        if theme is None and g.get("utterances"):
            unskinned += 1
        for utt in g.get("utterances", []):
            m = re.match(r"seat (\d+): (.*)", str(utt), re.S)
            if not m:
                continue
            seat, said = int(m.group(1)), m.group(2)
            total += 1
            key = roles.get(seat, "")
            if not key:
                continue
            names = [key]
            if theme is not None and key in theme.role_names:
                names.append(theme.role_names[key])
            hit = next((nm for nm in names if _says(said, nm)), None)
            if hit:
                bad += 1
                notes.append(f"game {g.get('game')} seat {seat} said its own role "
                             f"'{hit}': {said[:80]}")
    if unskinned:
        notes.insert(0, f"{unskinned} game(s) record no known theme - checked "
                        "against the functional key only, which a skinned run "
                        "never speaks")
    return bad, total, notes


PROOF = [
    ("hunt named a seat it knew was evil", hunt_named_impossible),
]
#: Legal, sometimes correct, and counted anyway - each one prices something the
#: rules make unavoidable or the metrics mis-score. Never added to the proof total:
#: a strategic cost reported as an error is a wrong finding with a number on it.
COST = [
    ("mission over-sabotaged, share of SUNK missions the game continued past "
     "(no private channel; focal point unused)", over_sabotage),
    ("good seat approved a known-tainted team (concealment has value)",
     approved_a_team_it_knew_was_tainted),
]
HEURISTIC = [
    ("seat referred to itself in the third person", third_person_self),
    ("seat named its own role in public speech", outed_own_role_in_public),
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("jsonl", help="per-game JSONL from a run")
    ap.add_argument("--show", type=int, default=3, help="examples per check (default 3)")
    args = ap.parse_args(argv)

    games = load(args.jsonl)
    print(f"{len(games)} games from {args.jsonl}\n")

    proof_total = 0
    for heading, checks in (
        ("PROOF - impossible given what that seat knew", PROOF),
        ("COST - legal, sometimes correct, priced here not blamed", COST),
        ("HEURISTIC - needs a human read", HEURISTIC),
    ):
        print(f"== {heading} ==")
        for name, fn in checks:
            bad, total, notes = fn(games)
            if checks is PROOF:
                proof_total += bad
            rate = f"{bad / total:.0%}" if total else "n/a"
            print(f"  {name}: {bad}/{total} ({rate})")
            for note in notes[:args.show]:
                print(f"      - {note}")
            if len(notes) > args.show:
                print(f"      ... {len(notes) - args.show} more")
        print()

    print(f"proof-class errors: {proof_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
