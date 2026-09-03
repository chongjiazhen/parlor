"""The last line of a detached run's log, written by the process that did the work.

`hunt20b` finished cleanly - full report, complete JSON, 20 JSONL lines, zero
errors - and wrote no completion line, because the ``cmd.exe`` wrapper did not
survive to echo one after python exited. That line is the only thing separating
"finished" from "killed at hour four", and it is exactly the judgement the
detached-run invariant says to make from the log alone: CPU time, IO counters and
exit codes all read as healthy while a run sleeps.

So the marker is written by the run itself. A wrapper cannot be trusted to outlive
the thing it wrapped, and there is no reason to ask it to - the process that knows
how many games landed is the one holding the count.

Absence keeps meaning what it should. :func:`run_with_marker` writes from a
``finally``, so the marker survives a crash, a ``sys.exit`` and a Ctrl-C; nothing
can write it for a process that was killed outright, which is the case it exists to
expose. A log whose last line is a progress line is a log of a killed run.

This is ``core/`` rather than one runner's file because both eval drivers launch
detached multi-hour runs and both need the same guarantee - the second game needing
it is the bar for promotion.
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from dataclasses import dataclass

#: The marker's prefix. It CONTAINS ``DONE rc=`` so a grep written against the old
#: wrapper-echoed line keeps finding it, and carries a word of its own so the two
#: are distinguishable in a log that has both.
MARKER = "PARLOR DONE rc="


def record_paths(out: str) -> tuple[str, str]:
    """``--out`` is the SUMMARY path, verbatim; the per-game JSONL is ``out.jsonl``.

    One convention, in ``core/``, because the two drivers had one each. ``run_cabal``
    wrote ``args.out`` verbatim while ``run_changeling`` composed ``f"{out}.json"``,
    so a launcher written from cabal's twin passed ``--out eval/records/s2.json`` and
    S2's records landed as ``s2.json.json`` beside ``s2.json.jsonl``. Editing the one
    launcher was the cheap wrong fix: it leaves the drivers disagreeing and the next
    launcher rediscovers it.

    Verbatim won because it is what every record already on disk is named - cabal's
    ``hunt*.json`` beside ``hunt*.json.jsonl`` - so settling it here renames one run's
    files rather than every run's.

    **It also CREATES the directory, 2026-09-03.** ``eval/records/`` is gitignored,
    so a fresh worktree has no such directory and a driver invoked by hand died
    ``FileNotFoundError`` at the first JSONL append - after the games had run,
    which is the expensive place to find out. Every ``eval/runs/*.cmd`` carried
    ``if not exist "%OUTDIR%" mkdir "%OUTDIR%"`` against exactly this, which is a
    guarantee living in twenty copies of a launcher instead of in the one function
    both drivers already route through. The launchers keep their line - it costs
    nothing and a recipe is read by people - but it is no longer what holds.
    """
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return out, f"{out}.jsonl"


def claim_record(out: str) -> tuple[str, str]:
    """The run's claim on its two output paths, made ONCE before the first game.

    Refuses when either file already exists, because the two are opened
    differently and always were: ``land()`` appends the per-game JSONL while the
    summary is written ``"w"``. A second run onto an occupied path therefore
    STACKS a block of games into one file and REPLACES the other, and the pair
    then describes two different populations with nothing raising. Three records
    reached that state - ``cl-heuristic``, ``-pack`` and ``-village`` hold 3000
    lines for 1000 games - and the first block of ``cl-heuristic.json.jsonl`` is a
    stale play of the same seeds at 71.55% pack wins against the published 56.09%,
    which a naive read of the file blends to about 61%: plausible, and five points
    wrong. No published number is affected, because every one of them reproduces
    from a deduped read, but that is a property of the two scorers that happen to
    dedupe rather than of the writer.

    **It refuses; it does not truncate.** The occupied path holds a run that cost
    GPU-hours, and clearing it is the operator's call. Every launcher already
    carries an ``if exist ... exit /b 1`` line against this, which is a guarantee
    living in twenty copies of a recipe instead of in the one function all four
    drivers route through - the same argument that moved ``makedirs`` here. The
    recipes keep their line; it is no longer what holds.

    Raises ``SystemExit`` rather than returning a flag, for the reason the drivers
    already refuse that way: a run that cannot write its record has nothing to do,
    and the marker still lands because ``run_with_marker`` maps every exit path.
    """
    summary, jsonl = record_paths(out)
    occupied = [path for path in (summary, jsonl) if os.path.exists(path)]
    if occupied:
        raise SystemExit(
            "refusing to run onto an occupied record path: "
            + ", ".join(occupied)
            + ". The JSONL is appended and the summary is truncated, so this run "
              "would stack its games onto another run's and leave the two files "
              "describing different populations. Move or delete those files, or "
              "pass a different --out.")
    return summary, jsonl


@dataclass
class RunState:
    """What a run knows about itself, readable from an exception handler.

    Held beside the driver rather than inside ``main()`` for one reason: the
    handler that writes the marker never saw ``main()``'s locals, and a crashed
    run's partial yield - 17 of 20 games, not zero - is exactly what the reader of
    a twelve-hour log needs.
    """

    #: games the run was ASKED for, known once the arguments are parsed
    requested: int | None = None
    #: games that reached disk, counted where the write happens
    landed: int = 0

    def reset(self) -> None:
        self.requested = None
        self.landed = 0

    def marker(self, rc: int, elapsed: float) -> str:
        of = "?" if self.requested is None else str(self.requested)
        return (f"{MARKER}{rc} games={self.landed}/{of} "
                f"elapsed={elapsed:.0f}s")


def run_with_marker(main, state: RunState) -> int:
    """Call ``main()`` and end the log with a marker either way.

    Returns the exit code to hand ``sys.exit``. Every exit path is mapped rather
    than left to the interpreter, because an uncaught exception's traceback is the
    last thing in the log and reads exactly like a killed run.
    """
    started = time.time()
    state.reset()
    rc = 0
    try:
        main()
    except SystemExit as exc:                 # argparse, or a driver's own refusal
        if exc.code is None or isinstance(exc.code, int):
            rc = exc.code or 0
        else:
            print(exc.code, file=sys.stderr)  # sys.exit("message") - print it
            rc = 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        rc = 130
    # The catch-all is the guard the crash case rests on, and it is the one under
    # the mutation check: narrow it and a crashed run raises out of here with no
    # code to report. The ``finally`` below is belt-and-braces behind it.
    except BaseException:                     # noqa: BLE001 - about to exit anyway
        traceback.print_exc()
        rc = 1
    finally:
        print(state.marker(rc, time.time() - started), flush=True)
    return rc
