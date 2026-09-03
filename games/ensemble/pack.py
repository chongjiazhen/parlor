"""A content pack, and the menu the choose phase is allowed to send.

``docs/content-packs.md`` splits an engine from its source material: this module
is the engine half, and the material it reads is a per-table pack that mostly
stays on the machine that plays it. Nothing here names a system, and the loader
takes a path so a pack can live anywhere - the same shape ``games/durf`` already
uses for its dungeons.

**The menu is where the payload position lives.** ``docs/open-arms.md`` §Session-0
argues that a full sheet per playbook, times the whole pack, is a large payload
paid by every seat at a phase where it is not actionable. So ``menu()`` yields a
name and one line, and ``sheet()`` exists for the seat that took one. A run that
sends every sheet is the arm against that position, and it is written by handing
the model ``sheet()`` for all of them - not by editing this file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class PackError(Exception):
    """The pack on disk cannot be used."""


def _first_sentence(text: str) -> str:
    """The hook. One sentence, because the menu is a budget rather than a blurb."""
    text = " ".join((text or "").split())
    if not text:
        return ""
    cut = text.find(". ")
    return text if cut < 0 else text[:cut + 1]


@dataclass(frozen=True)
class Pack:
    label: str
    playbooks: tuple[dict, ...]

    @classmethod
    def load(cls, path) -> "Pack":
        path = Path(path)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise PackError(f"cannot read pack {path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise PackError(f"pack {path} is not JSON: {exc}") from exc
        books = raw.get("playbooks")
        if not isinstance(books, list) or not books:
            raise PackError(f"pack {path} has no playbooks")
        seen: set[str] = set()
        for b in books:
            name = (b.get("name") or "").strip()
            if not name:
                raise PackError(f"pack {path} has a playbook with no name")
            if name in seen:
                raise PackError(f"pack {path} names {name!r} twice")
            seen.add(name)
        return cls(label=raw.get("pack", path.stem), playbooks=tuple(books))

    def names(self) -> tuple[str, ...]:
        return tuple(b["name"].strip() for b in self.playbooks)

    def menu(self) -> list[dict]:
        """What the choose phase may send: a name and one line, never a sheet."""
        return [{"name": b["name"].strip(), "hook": _first_sentence(b.get("about", ""))}
                for b in self.playbooks]

    def sheet(self, name: str) -> dict:
        """The full playbook, for the seat that took it."""
        for b in self.playbooks:
            if b["name"].strip() == name:
                return b
        raise KeyError(name)
