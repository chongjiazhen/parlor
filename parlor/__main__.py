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
usage: parlor play <game> [that game's own flags]
       parlor doctor [--probe]
       parlor --list

Registered rungs:
{listing}

A game's flags are its own - `play cabal --help` prints cabal's.
`doctor` reports which backend routes this box can reach and what they will
serve - the question no --help can answer, because its answer is about the box.
Each rung seats ONE person (`--human <seat>`): a terminal is one channel, so two
people at it would read each other's private view.

Installed (`pip install -e .`) the command is `parlor`; from a clone it is
`py -3 -m parlor`. They are the same entry point."""


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
    if argv[0] == "doctor":
        # Imported on dispatch, not at module scope, so `--list` and `play` cost
        # no network module and a doctor that failed to import could not take the
        # listing down with it - the rule the registry already applies to games.
        from core.doctor import main as doctor
        return doctor(argv[1:])
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


def cli() -> int:
    """The installed ``parlor`` console script.

    It exists because ``console_scripts`` calls this function and never runs the
    ``__main__`` block below, so the ``UnknownRung`` handling that turns a mistyped
    game name into the list of the real ones would have been silently absent from
    the installed command - the one a person actually types - while staying present
    in the clone-local ``py -3 -m parlor``. Both entry points route through here.
    """
    try:
        return main()
    except UnknownRung as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())
