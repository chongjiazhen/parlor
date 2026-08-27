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
import re
import sys
from dataclasses import dataclass, field
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
'?' reprints the view. Ctrl-C ends the game.
"""


class TooManyHumans(SystemExit):
    """More than one person was seated at a single terminal."""


def human_seats(spec: str | None, n: int) -> set[int]:
    """``--human 0`` -> ``{0}``. At most ONE seat, and that is not a shortcut.

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
    #: ``None`` resolves to the live ``sys.stdin``/``sys.stdout`` at call time
    #: rather than at import, so a test can hand in its own streams and a caller
    #: that reconfigures the console encoding still gets the reconfigured one.
    stdin: Any = None
    stdout: Any = None
    #: Wears the attribute an eval driver reads off a Backend, so a report that
    #: prints the model name does not crash on a human seat.
    model: str = HUMAN
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
            self._say(self.banner)
            self._greeted = True
        self._say("-" * 72)
        self._say(context)
        self._say("-" * 72)
        while True:
            line = self._readline().strip()
            if not line:
                continue
            if line == "?":
                self._say(context)
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
