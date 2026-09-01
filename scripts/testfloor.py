"""Fail when a test file has FEWER tests than it started with.

A worker can turn any suite green by deleting the tests that fail, and both the
exit code and the diff look healthy when it does: slot C reported `689 passed,
exit 0` over a large, plausible diff that had removed 23 of `core/test_console`'s
26 tests. The diff proves a worker acted; only a count proves it did not buy the
green by subtraction.

    py -3 testfloor.py <test-path> <minimum> [<test-path> <minimum> ...]

Collection only - no test bodies run, so this is cheap enough to sit in front of
the real suite in an --accept chain.
"""

from __future__ import annotations

import subprocess
import sys


def collected(path: str) -> int:
    out = subprocess.run(
        [sys.executable, "-m", "pytest", path, "--collect-only", "-q"],
        capture_output=True, text=True).stdout
    return sum(1 for line in out.splitlines() if "::" in line)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or len(argv) % 2:
        print("usage: testfloor.py <test-path> <minimum> [...]", file=sys.stderr)
        return 2
    bad = False
    for path, floor in zip(argv[::2], argv[1::2]):
        n = collected(path)
        ok = n >= int(floor)
        print(f"{path}: collected {n}, floor {floor} - {'ok' if ok else 'SHRANK'}")
        bad |= not ok
    if bad:
        print("test count fell below its floor: tests were deleted or renamed out "
              "of collection. Add tests; delete none.", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
