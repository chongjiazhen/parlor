"""Reading an action out of a model reply. Game-agnostic on purpose.

Every game in the ladder will need this and none of it is about hidden roles: a
model answers with JSON wrapped in prose or a ```json fence, or with a reply the
provider truncated mid-object, or with "Approve." where a boolean was asked for.
That is a property of talking to models, not a property of cabal, so it lives in
``core/`` and game #2 imports it instead of copying it.

What stays in the game: which keys to ask for, and what a legal value means. This
module only turns text into values.
"""

from __future__ import annotations

import json
import re


class ParseError(Exception):
    """The model's reply could not be read as the requested action."""


def extract_json(reply: str) -> dict:
    """Pull the action object out of a model reply.

    Takes the first balanced ``{...}`` that parses, so a fenced block or a
    sentence of preamble costs nothing. Raises ``ParseError`` if none does.
    """
    text = reply.strip()
    starts = [i for i, ch in enumerate(text) if ch == "{"]
    for start in starts:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
                    if isinstance(obj, dict):
                        return obj
                    break
    raise ParseError(f"no JSON object in reply: {reply[:200]!r}")


def salvage(reply: str, keys) -> dict:
    """Last-ditch key scrape for a reply whose JSON is malformed or truncated.

    A provider that cuts a long reply mid-object leaves valid, unambiguous
    key/value text behind; throwing that away spends a retry and, at the cap,
    silently replaces a real decision with a random one. Only the outermost
    quoted, bracketed, or bare value of each named key is taken - no structure is
    guessed, and a reply with none of the keys in it still raises.
    """
    out: dict = {}
    for key in keys:
        m = re.search(
            rf'"{re.escape(key)}"\s*:\s*'
            rf'("(?P<q>[^"]*)"|\[(?P<arr>[^\]]*)\]|(?P<bare>[^,}}\n]+))',
            reply,
        )
        if not m:
            continue
        if m.group("q") is not None:
            out[key] = m.group("q")
        elif m.group("arr") is not None:
            out[key] = [int(x) for x in re.findall(r"\d+", m.group("arr"))]
        else:
            out[key] = m.group("bare").strip()
    if not out:
        raise ParseError(f"nothing salvageable in reply: {reply[:200]!r}")
    return out


def read_reply(reply: str, keys) -> dict:
    """``extract_json``, falling back to ``salvage``. The normal entry point."""
    try:
        return extract_json(reply)
    except ParseError:
        return salvage(reply, keys)


TRUEISH = frozenset({"approve", "yes", "true", "accept", "aye", "y", "1"})
FALSEISH = frozenset({"reject", "no", "false", "deny", "nay", "n", "0"})


def parse_bool(value, *, true_words=TRUEISH, false_words=FALSEISH) -> bool:
    """Read a yes/no out of a real boolean or a word. Unknown words raise rather
    than defaulting - a silent default here would be a fabricated decision."""
    if isinstance(value, bool):
        return value
    word = str(value).strip().strip(".!\"'").lower()
    if word in true_words:
        return True
    if word in false_words:
        return False
    raise ParseError(f"cannot read {value!r} as a yes/no")


def parse_index(value, n: int, *, noun: str = "seat") -> int:
    """Read a 0..n-1 index out of ``2``, ``"2"``, or ``"seat 2"``."""
    if isinstance(value, bool):
        raise ParseError(f"{value!r} is not a {noun}")
    if isinstance(value, int):
        index = value
    else:
        m = re.search(r"\d+", str(value))
        if not m:
            raise ParseError(f"no {noun} number in {value!r}")
        index = int(m.group())
    if not 0 <= index < n:
        raise ParseError(f"{noun} {index} is outside 0..{n - 1}")
    return index


def parse_index_set(value, n: int, size: int, *, noun: str = "seat") -> list[int]:
    """Read exactly ``size`` distinct indices out of a list, or out of prose."""
    if isinstance(value, (str, int)):
        value = re.findall(r"\d+", str(value))
    if not isinstance(value, (list, tuple)):
        raise ParseError(f"expected a list of {noun}s, got {value!r}")
    picked = [parse_index(v, n, noun=noun) for v in value]
    if len(set(picked)) != size:
        raise ParseError(f"expected {size} distinct {noun}s, got {picked}")
    return sorted(set(picked))
