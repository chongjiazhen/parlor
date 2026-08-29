"""A human seat, wearing the backend interface.

The arena's claim is that a seat's un-entitled secrets are absent from the bytes
sent to its model. A human sitting in a seat is the most direct way to check
that: the person is handed ``ref.prompt_for(seat)`` - the same string a model
gets, through the same gate-#1 audit - and nothing else. If the human can deduce
something, they deduced it from the bytes; if they cannot, no model at that seat
could either.

The seam is already in the right place, so this costs one class and no game
edits. ``LLMPolicy`` in both games talks to its backend through exactly one
method, ``complete_meta(context) -> (reply, served_by)``. Standing a console in
that slot buys the whole apparatus for free:

  - the same prompt, because the policy renders it, not the backend;
  - the same parser, so ``vote y`` and ``card fail`` are read by the coercion the
    models' replies go through (``core.replies``);
  - the same refuse-and-retell loop, so an illegal move is answered with the
    REFEREE's own complaint and re-asked, instead of a second validation path
    that could disagree with the first;
  - the same record, with ``served_by`` reading ``human`` per decision, so a
    mixed table's JSONL says which moves a person made.

What it deliberately does NOT do is show the human anything a seat is not
entitled to. The caller owns that in two places, and both are guarded here or in
the demos rather than left to a comment:

  - **One human seat per game** (``human_seats``). A terminal is one channel, so
    two people playing from it read each other's private view.
  - A demo that prints one seat's view for the reader's benefit has to stop
    doing it once a person is playing. See ``opening_view`` in ``games/*/demo.py``.
"""

from __future__ import annotations

import json
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: Returned as the served-upstream id for every human decision. It lands in
#: ``Decision.served_by`` and the per-run ``upstreams`` census, so a record of a
#: mixed table attributes each move rather than crediting the model with all of
#: them.
HUMAN = "human"

BANNER = """\
You are playing a seat by hand. Everything below is the exact text this seat's
model would receive - it is this seat's whole world, and nothing that is not
printed is knowable from here.

Answer in shorthand:  <key> <value>       e.g.  vote y
                                                team 0 3
                                                card fail
                                                target 2
                                                say seat 2 proposed a tainted team
Several at once, separated by ';' before a key:
                                                say I'll wait; think 1 and 4 look paired
Or type a JSON object directly, on one or more lines: {"vote": true}
'?' reprints the view. 'rules' prints this game's full rules, 'help' this text.
Ctrl-C ends the game.
"""

#: Typed at the same prompt as a move, and not moves. A command is answered here,
#: never reaches the game, never spends a retry and never enters the reply.
#:
#: **Why this does not touch the payload.** A seat's view is what the referee
#: renders and gate #1 audits; none of this text is in it and none of it goes back.
#: The console has always printed one such block - ``BANNER`` - for the same
#: reason: a model arrives knowing how to emit JSON and a person does not, so the
#: orientation a person needs is console furniture rather than context. Putting a
#: standing objective into ``render_context`` instead would change the bytes every
#: MODEL receives and re-baseline every number this repo has recorded, to save a
#: person a lookup. That is the line - the ask stays byte-identical, the furniture
#: around it is allowed to help.
#:
#: A game whose ``ACTION_KEYS`` held one of these words would have it shadowed, so
#: the disjointness is asserted in ``core/test_console.py`` rather than noticed.
COMMANDS = ("?", "help", "rules", "model")


class TooManyHumans(SystemExit):
    """More than one person was seated at a single terminal."""


def human_seats(spec: str | None, n: int, seed: int | None = None) -> set[int]:
    """``--human 0`` -> ``{0}``. At most ONE seat, and that is not a shortcut.

    ``--human random`` -> one seat drawn from ``seed``. A person who always plays
    seat 0 only ever sees one position in the deal, which is the narrowest
    possible sample of the thing the console exists to check.

    A console is one channel. Two people playing from it read each other's
    private view as it scrolls past - which is precisely the property this arena
    exists to demonstrate the absence of, defeated by the harness rather than by
    the referee. The referee's audit cannot see it: it grades what the REFEREE
    renders to each seat, and both renders are correct. What is wrong is that one
    pair of eyes receives both.

    So the limit is the invariant asserting itself, not an unfinished feature. A
    second human seat needs a second channel (a socket, a second terminal, a
    process per seat), and until one exists the honest thing is to refuse.

    Lives in ``core`` because both games need the identical rule and it is a
    guarantee, not a parse: two copies is how one of them later grows a second
    human seat nobody re-argued.
    """
    if not spec:
        return set()
    if spec.strip().lower() == "random":
        if seed is None:
            raise SystemExit(
                "--human random needs --seed. A wall-clock draw would make two "
                "runs at one seed seat the person differently, and every number "
                "recorded under that seed is a claim that they would not.")
        # Its OWN generator, keyed on the seed and on this decision's name, for
        # two reasons that both bite. A draw taken from the caller's `rng` would
        # consume from the stream the policies deal out of, so choosing a seat
        # would change what every random seat then played at that same seed. And
        # both callers here resolve the flag independently - `main` and
        # `build_policies` - so a draw that depended on stream position would give
        # them different seats and seat the person in one place while the console
        # went to another.
        return {random.Random(f"human-seat:{seed}").randrange(n)}
    seats = set()
    for piece in spec.replace(",", " ").split():
        seat = int(piece)
        if not 0 <= seat < n:
            raise SystemExit(f"seat {seat} is outside 0..{n - 1}")
        seats.add(seat)
    if len(seats) > 1:
        raise TooManyHumans(
            f"one human seat per game, got {sorted(seats)}. Two people share this "
            "terminal, so each would read the other's private view - the arena's "
            "whole claim, broken by the harness rather than by the referee. "
            "Seat one person and let models hold the rest."
        )
    return seats


@dataclass
class ConsoleBackend:
    """Prompt a person at the terminal and hand their answer back as a reply.

    ``keys`` is the game's ``ACTION_KEYS``. It is passed in rather than imported
    because which keys exist is a fact about a game, and this module is core.
    """

    keys: tuple[str, ...]
    #: Printed once, before the first decision. The models get their register
    #: preamble as a system message they never see quoted back; the human gets
    #: the equivalent orientation here, and it says the same thing: this view is
    #: all there is.
    banner: str = BANNER
    #: A few lines of standing frame - the win condition, the counters on the
    #: board, what stays secret - printed once under the banner and reprinted by
    #: ``help``. Passed in by the game for the same reason ``keys`` is: what wins
    #: this game is a fact about the game, and this module is core.
    #:
    #: It exists because the per-turn ask is excellent at "what may I do now" and
    #: silent on "what am I trying to do": measured on a real hand-played game, the
    #: propose and vote prompts - where a player spends most of its turns - state
    #: neither the win condition nor what the ``rejects 0/5`` counter does at 5.
    #: A model can be indifferent to that; a person cannot play without it.
    briefing: str = ""
    #: This game's ``RULES.md``, printed in full on ``rules``. The file is already
    #: the canonical statement of the game - the gates, the strata and the hunt
    #: baseline all derive from it - so pointing the console at it means a player
    #: and a scorer are never reading two different accounts of the same rule.
    rules_path: str | None = None
    #: ``None`` resolves to the live ``sys.stdin``/``sys.stdout`` at call time
    #: rather than at import, so a test can hand in its own streams and a caller
    #: that reconfigures the console encoding still gets the reconfigured one.
    stdin: Any = None
    stdout: Any = None
    #: Wears the attribute an eval driver reads off a Backend, so a report that
    #: prints the model name does not crash on a human seat.
    model: str = HUMAN
    #: The model ID used for the non-human seats, for display to the human player.
    #: Does not affect the human seat's served-by value (which remains ``model``).
    other_model: str | None = None
    seed: int | None = None
    _greeted: bool = field(default=False, repr=False)

    # ---- streams ----------------------------------------------------------

    @property
    def _in(self):
        return self.stdin if self.stdin is not None else sys.stdin

    @property
    def _out(self):
        return self.stdout if self.stdout is not None else sys.stdout

    def _say(self, text: str = "") -> None:
        print(text, file=self._out, flush=True)

    def _readline(self) -> str:
        """One line, or a clean abort. EOF is Ctrl-D / a closed pipe, and it must
        NOT reach ``LLMPolicy``'s ``except Exception``: that would spend the retry
        budget and then play a RANDOM move on the person's behalf, which is a
        decision nobody made. ``KeyboardInterrupt`` is a ``BaseException``, so it
        passes straight through the policy and ends the game."""
        line = self._in.readline()
        if line == "":
            raise KeyboardInterrupt("input closed")
        return line.rstrip("\n").rstrip("\r")

    # ---- the backend interface --------------------------------------------

    def complete(self, context: str) -> str:
        return self.complete_meta(context)[0]

    def complete_meta(self, context: str) -> tuple[str, str]:
        """Show this seat's view, read an answer, return it as a model would."""
        if not self._greeted:
            self._greet()
            self._greeted = True
        self._say("-" * 72)
        self._say(context)
        self._say("-" * 72)
        while True:
            line = self._readline().strip()
            if not line:
                continue
            # A command is checked against the game's own keys first, so a game
            # that ever names an action ``rules`` keeps its action and merely
            # loses the shortcut. The move always wins the word.
            word = line.lower()
            if word in COMMANDS and word not in self.keys:
                self._command(word, context)
                continue
            if line.startswith("{"):
                return self._read_json(line), HUMAN
            try:
                return json.dumps(self.shorthand(line)), HUMAN
            except ValueError as exc:
                # Local, and free: a typo that never named a key is not a refused
                # MOVE, so it must not spend one of the seat's retries. Only text
                # that parsed into an action goes back to the game to be judged.
                self._say(f"  ({exc}; keys are {', '.join(self.keys)})")

    # ---- console commands, which are not moves ----------------------------

    def _greet(self) -> None:
        self._say(self.banner)
        if self.briefing:
            self._say(self.briefing.rstrip())
            self._say()
        self._say(self._table_model())

    def _command(self, word: str, context: str) -> None:
        """Answer a command and return to the same ask. Nothing here is recorded,
        because nothing here was a decision."""
        if word == "?":
            self._say(context)
        elif word == "help":
            self._greet()
        elif word == "rules":
            self._say(self._rules())
        elif word == "model":
            self._say(self._table_model())

    def _table_model(self) -> str:
        """Who is answering in the OTHER seats. Console furniture, never payload -
        and deliberately not ``self.model``, which is this seat's own served-by
        identity (``HUMAN``) and rides in the record."""
        return ("The other seats are served by: "
                f"{self.other_model if self.other_model is not None else 'unknown'}")

    def _rules(self) -> str:
        """This game's rules, or a straight account of why they are not here.

        A missing or unreadable file is reported and the game continues: the rules
        are orientation, and a seat that can still make its move must not be ended
        by a failed read of a convenience.
        """
        if not self.rules_path:
            return ("  (no rules file was passed to this seat - the game's own "
                    "RULES.md is the canonical statement)")
        try:
            return Path(self.rules_path).read_text(encoding="utf-8")
        except OSError as exc:
            return f"  (cannot read {self.rules_path}: {exc})"

    def _read_json(self, first: str) -> str:
        """Keep reading while the braces are open, so a pasted multi-line object
        arrives whole. Malformed JSON is passed through unrepaired - the game's
        parser owns that complaint, and it is the one the models get."""
        buf = [first]
        while "".join(buf).count("{") > "".join(buf).count("}"):
            buf.append(self._readline())
        return "\n".join(buf)

    def shorthand(self, line: str) -> dict:
        """``vote y`` -> ``{"vote": "y"}``. Values stay STRINGS on purpose.

        Every value a seat can play is already coerced from text by
        ``core.replies`` - ``y``/``approve`` to a boolean, ``fail`` to this
        game's card convention, ``0 3`` to a seat list - because that is how the
        models' replies are read. Coercing here as well would be a second
        implementation of the same rules, free to drift from the one the numbers
        were measured with.
        """
        parts = self._split(line)
        out: dict = {}
        for part in parts:
            head, _, rest = part.strip().partition(" ")
            key = head.strip().lower().rstrip(":")
            if key not in self.keys:
                raise ValueError(f"{head!r} is not an action key")
            out[key] = rest.strip()
        if not out:
            raise ValueError("nothing to read")
        return out

    def _split(self, line: str) -> list[str]:
        """Split on a ';' only where a known key starts the next field, so a
        semicolon inside a spoken line survives."""
        alternatives = "|".join(re.escape(k) for k in self.keys)
        return re.split(rf";\s*(?={alternatives}\b)", line)
