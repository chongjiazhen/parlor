"""Run one session-0 draft and return the record it is scored from."""

from __future__ import annotations

from .draft import Draft


def run_draft(pack, seats, seed: int | None = None) -> dict:
    """Draft in seat order. Every number ships beside its fallback rate."""
    draft = Draft(pack.names(), seats=len(seats), seed=seed)
    menu = pack.menu()
    while not draft.done:
        seat = draft.offer()
        pick = seats[seat].choose(menu, taken=tuple(draft.picks.values()))
        draft.take(pick if pick is not None else "")
    decisions = len(seats)
    return {
        "pack": pack.label,
        "seed": seed,
        "seats": decisions,
        "picks": draft.picks,
        "distribution": draft.distribution(),
        "fallbacks": draft.fallbacks,
        "fallback_rate": draft.fallbacks / decisions if decisions else 0.0,
    }
