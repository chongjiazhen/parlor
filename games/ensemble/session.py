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
        "upstreams": {i: getattr(s, "upstream", None) for i, s in enumerate(seats)},
        "distribution": draft.distribution(),
        "fallbacks": draft.fallbacks,
        "transport_errors": sum(getattr(s, "transport_errors", 0) for s in seats),
        "fallback_rate": draft.fallbacks / decisions if decisions else 0.0,
    }
