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
from dataclasses import dataclass


class ParseError(Exception):
    """The model's reply could not be read as the requested action."""


@dataclass(frozen=True)
class Complaints:
    """The text a seat reads back when its reply could not be parsed.

    These are MODEL-FACING strings (`docs/model-facing-text.md`): the retry loop
    feeds the complaint straight back into the next prompt, so their wording is a
    measured variable rather than a comment. They sit in a table rather than in
    inline f-strings because five games share this module and exactly one of them
    - changeling, via ``games/changeling/phrasing.py`` - varies them behind a
    flag. A branch at each raise site would put that arm's definition in eight
    places, and no golden pin could then cover more than the branch a test
    happened to walk.

    Every field is a ``str.format`` template, with its placeholders named below.
    The caller renders the values, so ``{value}`` arrives already ``repr``'d, and
    a template may drop a placeholder it has no use for.

    ``AS_IS_COMPLAINTS`` is the default on every function here and is what cabal,
    belfry, quorum and durf read. ``core/test_complaints.py`` pins it to a sha256
    computed before this table existed.
    """

    name: str
    #: No balanced object parsed. Placeholders: ``{reply}``.
    no_json: str
    #: Not even a key/value scrape survived. Placeholders: ``{reply}``.
    nothing_salvageable: str
    #: A word where a yes/no was asked for. Placeholders: ``{value}``.
    not_boolean: str
    #: A boolean where an index was asked for. ``{value}``, ``{noun}``,
    #: ``{last}``.
    not_index: str
    #: No digits anywhere in the value. ``{value}``, ``{noun}``, ``{last}``.
    no_index_number: str
    #: A number outside the table. ``{noun}``, ``{index}``, ``{last}``.
    index_out_of_range: str
    #: Something other than a list where a list was asked for. ``{noun}``,
    #: ``{value}``.
    not_index_list: str
    #: The wrong number of distinct indices. ``{size}``, ``{noun}``,
    #: ``{picked}``.
    wrong_index_count: str


#: What every recorded number in this repo was played on. Byte-frozen: the four
#: games that pass no table read exactly these, and changeling's ``as-is`` arm
#: is this object.
AS_IS_COMPLAINTS = Complaints(
    name="as-is",
    no_json="no JSON object in reply: {reply}",
    nothing_salvageable="nothing salvageable in reply: {reply}",
    not_boolean="cannot read {value} as a yes/no",
    not_index="{value} is not a {noun}",
    no_index_number="no {noun} number in {value}",
    index_out_of_range="{noun} {index} is outside 0..{last}",
    not_index_list="expected a list of {noun}s, got {value}",
    wrong_index_count="expected {size} distinct {noun}s, got {picked}",
)


def extract_json(reply: str, *,
                 complaints: Complaints = AS_IS_COMPLAINTS) -> dict:
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
    raise ParseError(complaints.no_json.format(reply=repr(reply[:200])))


def salvage(reply: str, keys, *,
            complaints: Complaints = AS_IS_COMPLAINTS) -> dict:
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
        raise ParseError(
            complaints.nothing_salvageable.format(reply=repr(reply[:200])))
    return out


def read_reply(reply: str, keys, *,
               complaints: Complaints = AS_IS_COMPLAINTS) -> dict:
    """``extract_json``, falling back to ``salvage``. The normal entry point."""
    try:
        return extract_json(reply, complaints=complaints)
    except ParseError:
        return salvage(reply, keys, complaints=complaints)


TRUEISH = frozenset({"approve", "yes", "true", "accept", "aye", "y", "1"})
FALSEISH = frozenset({"reject", "no", "false", "deny", "nay", "n", "0"})


def parse_bool(value, *, true_words=TRUEISH, false_words=FALSEISH,
               complaints: Complaints = AS_IS_COMPLAINTS) -> bool:
    """Read a yes/no out of a real boolean or a word. Unknown words raise rather
    than defaulting - a silent default here would be a fabricated decision."""
    if isinstance(value, bool):
        return value
    word = str(value).strip().strip(".!\"'").lower()
    if word in true_words:
        return True
    if word in false_words:
        return False
    raise ParseError(complaints.not_boolean.format(value=repr(value)))


def parse_index(value, n: int, *, noun: str = "seat",
                complaints: Complaints = AS_IS_COMPLAINTS) -> int:
    """Read a 0..n-1 index out of ``2``, ``"2"``, or ``"seat 2"``."""
    if isinstance(value, bool):
        raise ParseError(complaints.not_index.format(
            value=repr(value), noun=noun, last=n - 1))
    if isinstance(value, int):
        index = value
    else:
        m = re.search(r"\d+", str(value))
        if not m:
            raise ParseError(complaints.no_index_number.format(
                value=repr(value), noun=noun, last=n - 1))
        index = int(m.group())
    if not 0 <= index < n:
        raise ParseError(complaints.index_out_of_range.format(
            noun=noun, index=index, last=n - 1))
    return index


def parse_index_set(value, n: int, size: int, *, noun: str = "seat",
                    complaints: Complaints = AS_IS_COMPLAINTS) -> list[int]:
    """Read exactly ``size`` distinct indices out of a list, or out of prose."""
    if isinstance(value, (str, int)):
        value = re.findall(r"\d+", str(value))
    if not isinstance(value, (list, tuple)):
        raise ParseError(complaints.not_index_list.format(
            noun=noun, value=repr(value)))
    picked = [parse_index(v, n, noun=noun, complaints=complaints)
              for v in value]
    if len(set(picked)) != size:
        raise ParseError(complaints.wrong_index_count.format(
            size=size, noun=noun, picked=picked))
    return sorted(set(picked))
