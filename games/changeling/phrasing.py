"""Two phrasings of the steering strings a changeling seat reads.

`docs/model-facing-text.md` says to prompt the positive, and says in the same
breath that editing one of these strings is an experiment rather than a cleanup.
Both halves are load-bearing here, so the rewrite ships as an ARM: ``as-is`` is
byte-for-byte what every recorded changeling number was played on, ``positive``
is the negation pass, and ``--phrasing`` picks between them with ``as-is`` the
default. `docs/changeling-phrasing-criterion.md` is the pre-committed read.

**A table, not scattered conditionals.** Every string that differs between the
two arms is a field below, and the referee and the player policy read it off
``ref.phrasing``. A branch at each call site would put the arm's definition in
four files, and the golden pin in ``test_phrasing`` could then only cover
whichever branch the test happened to walk.

**What stays a prohibition.** The doctrine keeps one only where the referee
enforces the rule anyway and no positive phrasing exists. Under ``positive``,
none of these qualify: the self-vote refusal has a positive target the referee
already computes (``legal_votes``), and the two register preambles have positive
targets for the same behaviour. So the ``positive`` column carries no "do not",
"cannot" or "never", and ``test_phrasing`` asserts that in both directions -
present under ``as-is``, absent under ``positive``. Where a rule of the game is
itself an absence (a day on which the village accuses nobody), the ``positive``
column states the CONDITION positively and lets the outcome be what it is; that
is a fact about the rules, not steering.

The night's factual negations in ``roles.py`` - "the other seat is not told",
"sleeps through the night and does nothing" - are deliberately NOT here. They
describe what a card does, they are per-skin text frozen against recorded runs,
and rewriting them would move the deck description rather than the steering.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Phrasing:
    """One arm's copy of every steering string that differs between the two.

    Named fields rather than a dict, so a slot that loses its consumer fails to
    construct instead of sitting unread. ``{}`` placeholders are noted per field
    and are formatted by the caller that holds the values.
    """

    name: str
    #: Rendered to a seat whose night told it nothing.
    no_knowledge: str
    #: The VOTE ask. Placeholders: ``{legal}``.
    ask_vote: str
    #: The public event for a vote in which no seat drew two fingers.
    accused_none: str
    #: Wrapper the retry loop puts around the referee's complaint.
    #: Placeholders: ``{complaint}``.
    retry: str
    #: The refusal for a seat that pointed at itself. Placeholders: ``{seat}``,
    #: ``{legal}``.
    self_vote: str
    #: Parser refusals for the two fields a seat is asked for.
    missing_say: str
    missing_vote: str


AS_IS = Phrasing(
    name="as-is",
    no_knowledge="Your night gave you nothing to go on. Reason from the table.",
    ask_vote=(
        "Point at one seat. Everyone points at once, and the seat with "
        "the most fingers is accused - if it has more than one. A vote "
        "where no seat draws two accuses nobody. Reply as one JSON object: "
        '{{"think": "your private reasoning", "vote": <seat number>}}. '
        "Choose from: {legal}."),
    accused_none="Accused: nobody (no seat drew more than one vote)",
    retry=("Your previous reply was refused: {complaint}\n"
           "Answer again, correctly, as one JSON object."),
    self_vote="seat {seat} cannot point at itself; choose from {legal}",
    missing_say='missing "say" (an empty utterance is not a move)',
    missing_vote='missing "vote"',
)

POSITIVE = Phrasing(
    name="positive",
    # "nothing to go on" names the absence first and the target second. The
    # target is the whole of what this seat can do, so it goes first and alone.
    no_knowledge=("The table is what you have to work from: the deck above, and "
                  "what each seat says. Reason from those."),
    # The as-is line spends a sentence on the vote that accuses nobody. Here the
    # threshold is stated as the condition to meet, and the flat-vote outcome
    # follows from it as a rule of the game rather than as a warning.
    ask_vote=(
        "Point at one seat. Everyone points at once, and a seat is accused "
        "once it draws two or more fingers, the most fingers of any seat. A "
        "day where every seat draws a single finger ends with the village "
        "accusing nobody. Reply as one JSON object: "
        '{{"think": "your private reasoning", "vote": <seat number>}}. '
        "Choose from: {legal}."),
    accused_none="Accused: nobody (every seat drew a single vote at most)",
    retry=("One fix is needed on your previous reply: {complaint}\n"
           "Reply again as one JSON object."),
    # The referee already computes the legal targets, so the positive form says
    # where the finger goes and lists them. Refusing it stays the referee's job.
    self_vote="seat {seat} points at another seat; choose from {legal}",
    missing_say='give "say" the words the table hears',
    missing_vote='give "vote" one seat number',
)

#: What ``--phrasing`` accepts. ``as-is`` first, because it is the default and
#: the one every existing record was played on.
PHRASINGS: dict[str, Phrasing] = {"as-is": AS_IS, "positive": POSITIVE}
