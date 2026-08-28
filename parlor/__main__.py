"""``py -3 -m parlor play <game> [that game's flags]``.

    py -3 -m parlor --list
    py -3 -m parlor play cabal --human 0
    py -3 -m parlor play changeling --human 0 --backend local --model qwen36-35b-a3b-iq3
    py -3 -m parlor play cabal --help        # cabal's own flags, from cabal's parser

**Everything after the game name is the game's, untouched.** This module does not
parse it, does not validate it and does not know what is in it - it rewrites
``sys.argv`` and calls that game's ``main()``, which is the same function
``python -m games.cabal.demo`` calls, reaching the same parser with the same
strings. That is deliberate and it is the whole safety argument: a CLI that
reached a prompt would be a MEASURED change and would re-baseline both games'
recorded numbers for a convenience. There is no code path here that can, because
there is no code here that knows a prompt exists.

``argparse`` is not used for the dispatch itself. It would have to run in
``parse_known_args`` mode to leave the game's flags alone, and its prefix
matching would still claim an unambiguous abbreviation of one of ITS options out
of the middle of the game's command line. Two string comparisons cannot.
"""

from __future__ import annotations

import sys

from core.registry import UnknownRung, listing, lookup

USAGE = """\
usage: py -3 -m parlor play <game> [that game's own flags]
       py -3 -m parlor --list

Registered rungs:
{listing}

A game's flags are its own - `play cabal --help` prints cabal's.
Each rung seats ONE person (`--human <seat>`): a terminal is one channel, so two
people at it would read each other's private view."""


def usage() -> str:
    return USAGE.format(listing=listing())


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv or argv[0] in ("-h", "--help"):
        print(usage())
        return 0
    if argv[0] in ("-l", "--list"):
        print(listing())
        return 0
    if argv[0] != "play":
        print(f"unknown command {argv[0]!r}\n\n{usage()}", file=sys.stderr)
        return 2

    rest = argv[1:]
    if not rest:
        print("play what?", file=sys.stderr)
        print(file=sys.stderr)
        print(usage(), file=sys.stderr)
        return 2
    if rest[0] in ("-l", "--list"):
        print(listing())
        return 0

    name, tail = rest[0], rest[1:]
    driver = lookup(name).driver()

    # The game's parser reads sys.argv, and its usage line reads argv[0]. Handing
    # it the command the player actually typed means `play cabal --help` prints
    # `usage: parlor play cabal ...` rather than `usage: demo.py ...`, which is
    # the one thing the old entry points could not say. Restored afterwards so a
    # caller inside a longer-lived process (a test, a REPL) is not left holding a
    # command line it never set.
    saved = sys.argv
    sys.argv = [f"parlor play {name}", *tail]
    try:
        driver()
    finally:
        sys.argv = saved
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UnknownRung as exc:
        raise SystemExit(str(exc))
