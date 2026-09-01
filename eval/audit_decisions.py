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


def _claim_en(text: str, name: str) -> bool:
    """``I am`` / ``I'm`` before the role, with a short identity descriptor, or
    ``As <role>, I``."""
    role = rf"\b{re.escape(name)}\b" if name.isascii() else re.escape(name)
    return re.search(
        rf"\b(?:i am|i['’]m)\s+(?:(?:a|an|the)\s+)?"
        rf"(?:(?:member|agent|officer)\s+of\s+(?:the\s+)?)?{role}", text,
        re.I) is not None or re.search(
            rf"\bas\s+(?:(?:a|an|the)\s+)?{role}\s*[,;:-]?\s*i\b", text,
            re.I) is not None


def _claim_zh(text: str, name: str) -> bool:
    """``我是`` / ``我就是`` only where the role phrase ends there - a possessive
    continuation (``我是思想警察的同事``) says relation to the role, not identity as
    it - or ``作为<role>，我``."""
    return re.search(rf"我(?:是|就是){re.escape(name)}"
                     rf"(?=$|[\s，,。.!！?？；;、）)])", text) is not None \
        or re.search(rf"作为{re.escape(name)}[，,]\s*我", text) is not None


#: One entry per language whose claim shape somebody has actually written down.
#: Keyed on the skin's DECLARED language (``Theme.lang``), never on the script of
#: the text or of the role name - that is the landmine. A Japanese skin names its
#: roles in the same kanji a Chinese one does, so a name-keyed branch hands it the
#: Chinese rule, which looks for ``我是``, which a Japanese sentence never carries:
#: a confident 0/N one skin later, reading exactly like a fix. Latin script says as
#: little - French is Latin and says ``Je suis``.
CLAIM_RULES = {"en": _claim_en, "zh": _claim_zh}


def _claims_own_role(text: str, name: str, lang: str = "en") -> str:
    """How this text names ``name`` as the SPEAKER's own role: ``"claim"``,
    ``"mention"``, or ``""``.

    Mentioning a role is table vocabulary, especially under a themed skin, so S13
    counts only a first-person present-tense claim. The two rules above are the
    only claim shapes anyone here has written down.

    **The floor, and why it is not silence.** A skin in a third language matches
    neither rule, and the honest report of "this file cannot tell a claim from a
    mention here" is NOT a zero: a zero is indistinguishable from clean play, and
    that is exactly the bug that had ``outed_own_role_in_public`` reporting 0/1290
    on a skin it could not read. So an unruled language falls back to the plain
    mention test in ``_says`` - the same containment that function's own last line
    already falls back to - and says which test answered.

    **The floor OVER-counts, on purpose, and the caller must say so.** "Seat 3 is
    the Thought Police" counts too, so a ``mention`` total is an upper bound on
    claims, never a claim count, and must not be compared against a skin that has a
    rule. Wrong-high and loud is the floor a checker owes a language it does not
    speak, in a HEURISTIC check whose contract is already that a human reads the
    hits; wrong-low and quiet is the bug. Adding a language means adding its rule to
    ``CLAIM_RULES``, never widening another language's regex to reach it.
    """
    if not name:
        return ""
    rule = CLAIM_RULES.get(lang)
    if rule is None:
        return "mention" if _says(text, name) else ""
    return "claim" if rule(text, name) else ""


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
    between them - that is a rule of the game, not an oversight. Playing success is
    only better IF the other one fails, and nothing tells you it will.

    **What the number means: the pair failed to find a convention.** An earlier
    version of this docstring argued against itself - it said a mixed equilibrium
    makes some double-fail rate irreducible, and then derived the channel-free focal
    point that drives it to ~0. Both halves are right about different things, and
    read as one claim they mis-state the benchmark a reader grades the observed
    39-45% against.

    The irreducible-rate half holds only for a pair that finds NO convention. One
    exists and needs no channel at all: "the lower-numbered evil on this team plays
    fail" is derivable by both seats from the public proposal alone, and Schelling
    points do not require communication. So the normative count for a capable pair
    is ~0, and 39-45% of payable sunk missions is the model failing to find any such
    convention - which is precisely the reasoning being priced here, and the reason
    this sits under COST rather than PROOF. It is a fact about reasoning, not a
    rules violation, and not an equilibrium that forbids zero.

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

    A claim-shaped match is deliberately narrow: first person, present tense,
    and the seat's role. Ordinary role vocabulary is not evidence of an outing.

    **Matches the THEME name as well as the functional key, and that is the whole
    point of the check working at all.** Speech is rendered in whatever skin the run
    used: on the `1984-en` face every recorded run used, a seat outing itself says
    "Thought Police"
    or "Doublethinker" and never once says "seer" or "mimic". The reported 0/1290
    on the seed-1000 runs was near-zero BY CONSTRUCTION - it was matching vocabulary
    the players had no way to produce - and supported nothing. A run's theme is on
    the record, so the names are a lookup, not a guess.

    A record with no theme is checked on the functional key alone and SAYS so;
    silently narrowing the match is how the 0/1290 happened the first time.

    **A skin whose language has no claim rule is counted at the floor, and the
    count says so on its first line.** ``_claims_own_role`` falls back to a plain
    mention there rather than to zero, so for those games this number is an UPPER
    bound - mentions, not claims - and is not comparable with a skin that has a
    rule. The alternative reads better and lies: a language-blind matcher returns 0
    on a run full of self-outings, and a 0 in this column is indistinguishable from
    a table that never outed itself. Same failure as the 0/1290, one skin over.
    """
    bad, total, notes = 0, 0, []
    unskinned = 0
    floor = 0
    floor_langs: set[str] = set()
    for g in games:
        roles = {int(s): k for s, k in (g.get("assignment") or {}).items()}
        theme = THEMES.get(str(g.get("theme") or ""))
        if theme is None and g.get("utterances"):
            unskinned += 1
        # No theme means the functional keys, which are English.
        lang = theme.lang if theme is not None else "en"
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
            hit = next(((nm, how) for nm in names
                        if (how := _claims_own_role(said, nm, lang))), None)
            if hit:
                nm, how = hit
                bad += 1
                if how == "mention":
                    floor += 1
                    floor_langs.add(lang)
                notes.append(f"game {g.get('game')} seat {seat} "
                             f"{'said its own role' if how == 'claim' else 'MENTIONED its own role'}"
                             f" '{nm}': {said[:80]}")
    if unskinned:
        notes.insert(0, f"{unskinned} game(s) record no known theme - checked "
                        "against the functional key only, which a skinned run "
                        "never speaks")
    if floor:
        # First, because it changes what the COUNT is, and `--show` truncates the
        # tail: `audit_decisions.CLAIM_RULES` has no claim shape for this skin's
        # language, so those hits are mentions and the number is an upper bound.
        notes.insert(0, f"{floor} of these are MENTIONS, not claims - no claim rule "
                        f"for {'/'.join(sorted(floor_langs))}, so they are the "
                        "stated floor and the count is an UPPER BOUND. Not "
                        "comparable with a skin that has a rule.")
    return bad, total, notes

def claimed_a_role_it_was_not_dealt(games: list[dict]) -> tuple[int, int, list[str]]:
    """A seat claiming, in the first person and the present tense, a role it does
    not hold.

    Separate from ``outed_own_role_in_public`` and deliberately so: that check
    counts a seat naming the role it WAS dealt, which hands the table the game.
    This one counts the opposite move, and the opposite move is not an error - a
    mimic saying "I am the Seer" is the game working. It is counted because it is
    the deception gate's raw material. Gate #2 is conditional on gate #3, and
    measured with good voting at chance evil wins ~65% with no deception at all, so
    a run's deception rate has to be READ rather than assumed from the win column.
    A run where nobody ever claims a role they lack won gate #2 some other way.

    HEURISTIC: the same claim shape as S13, so it inherits S13's narrowness. It
    cannot see a false claim made obliquely ("the mission needs someone who has
    seen the evils - that is me"), and it makes no judgement about whether the
    claim was strategic or careless.

    **Where the floor does NOT apply, and that is the design call.** A skin whose
    language has no rule in ``CLAIM_RULES`` gets ``_claims_own_role``'s mention
    floor, which is an over-count that check can afford: a seat mentioning its own
    role is at least unusual. Here it is unaffordable. Mentioning a role you do not
    hold - "seat 3 is the Thought Police" - is the single most ordinary sentence at
    this table, so a containment floor would flag most of the record and hand the
    reader a number that means nothing. There is no honest wrong-high answer here,
    so this check REFUSES those games instead: they leave the denominator and are
    named on the first note line. A refusal is legible; 0 and 95% are both lies.
    """
    bad, total, notes = 0, 0, []
    unruled: Counter = Counter()
    undealt = 0
    by_team: Counter = Counter()
    for g in games:
        roles = {int(s): k for s, k in (g.get("assignment") or {}).items()}
        theme = THEMES.get(str(g.get("theme") or ""))
        lang = theme.lang if theme is not None else "en"
        if lang not in CLAIM_RULES:
            unruled[lang] += len(g.get("utterances") or [])
            continue
        keys = list(theme.role_names) if theme is not None else list(ROLES_BY_KEY)
        for utt in g.get("utterances", []):
            m = re.match(r"seat (\d+): (.*)", str(utt), re.S)
            if not m:
                continue
            seat, said = int(m.group(1)), m.group(2)
            total += 1
            dealt = roles.get(seat, "")
            if not dealt:
                undealt += 1
                continue
            claimed = sorted({
                key for key in keys if key != dealt
                for nm in ([key] + ([theme.role_names[key]]
                                    if theme is not None and key in theme.role_names
                                    else []))
                if _claims_own_role(said, nm, lang) == "claim"})
            if claimed:
                bad += 1
                role = ROLES_BY_KEY.get(dealt)
                by_team[role.team.name if role else "UNKNOWN"] += 1
                notes.append(f"game {g.get('game')} seat {seat} holds '{dealt}' and "
                             f"claimed {'/'.join(claimed)}: {said[:80]}")
    if by_team:
        notes.insert(0, "by the claimant's own team: "
                        + ", ".join(f"{t} {n}" for t, n in sorted(by_team.items())))
    if undealt:
        notes.insert(0, f"{undealt} utterance(s) from a seat the assignment does "
                        "not cover - counted in the denominator, not checked")
    if unruled:
        notes.insert(0, "REFUSED " + ", ".join(
            f"{n} utterance(s) in '{lang}'" for lang, n in sorted(unruled.items()))
            + " - no claim rule for that language, and this check has no floor: "
              "naming a role you do not hold is ordinary table talk, so a mention "
              "match would count most of the record. Out of the denominator.")
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
    ("seat claimed a role it was NOT dealt (deception, not an error)",
     claimed_a_role_it_was_not_dealt),
]


def _rotate_deals(games: list[dict]) -> list[dict]:
    """The same records with every seat's DEAL moved one seat along.

    Speech is untouched, so a claim that was about the speaker's own role is now
    about somebody else's and the two claim checks must trade places.
    """
    out = []
    for g in games:
        a = g.get("assignment") or {}
        keys, vals = list(a), [a[k] for k in (a or {})]
        out.append(dict(g, assignment=dict(zip(keys, vals[1:] + vals[:1]))))
    return out


def control(games: list[dict]) -> int:
    """Instrument control for the two claim-shaped checks. Exit 3 if it does not fire.

    A 0 from a string matcher is the failure this whole file was rewritten for -
    ``outed_own_role_in_public`` reported 0/1290 for weeks while looking for
    vocabulary the players had no way to produce, and nothing about the output said
    so. A zero is only evidence once the matcher has been shown to fire on the
    record it returned that zero for.

    Rotating the deals is the cheapest way to show it. The speech is unchanged, so
    every claim a seat made about its OWN role is now a claim about a role it does
    not hold: the two counts must swap. If both readings are 0 the instrument never
    fired on this record and neither number means anything, which is a refusal (3),
    not a pass. Only the claim checks are read here - the proof checks reason from
    the deal, so under a rotated deal their output is nonsense and is not printed.
    """
    rotated = _rotate_deals(games)
    rows = []
    for name, fn in (("seat named its OWN role", outed_own_role_in_public),
                     ("seat claimed a role it was NOT dealt",
                      claimed_a_role_it_was_not_dealt)):
        (bad, total, _), (rot, _, _) = fn(games), fn(rotated)
        rows.append((name, bad, rot, total))
        print(f"  {name}: {bad}/{total} as recorded -> {rot}/{total} with the "
              "deals rotated one seat")
    if all(bad == 0 and rot == 0 for _, bad, rot, _ in rows):
        print("\nREFUSED: neither check fired on this record, in either reading. "
              "The zeros above are a property of the matcher OR of the play and "
              "this control cannot tell them apart - do not publish them.")
        return 3
    print("\nThe instrument fires on this record: a claim shape it can see is "
          "present, so a 0 in the other column is a reading, not a blind spot.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("jsonl", help="per-game JSONL from a run")
    ap.add_argument("--show", type=int, default=3, help="examples per check (default 3)")
    ap.add_argument("--control", action="store_true",
                    help="instrument control for the two claim checks: score "
                         "the records again with every deal moved one seat "
                         "along, where the two counts must swap. Exit 3 if "
                         "neither fires.")
    args = ap.parse_args(argv)

    games = load(args.jsonl)
    print(f"{len(games)} games from {args.jsonl}\n")

    if args.control:
        print("== CONTROL - claim checks against a rotated deal ==")
        return control(games)

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
