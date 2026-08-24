"""Deterministic referee for the hidden-role mission game.

The referee is pure code: it deals roles, computes each seat's entitled night
knowledge, validates and applies the actions players choose (propose, vote, play a
mission card, hunt), tracks state, and detects the win. It never decides a proposal
or a vote - that is the players' job (scripted/random here, LLM later). No judgment
lives here, which is why this game is spike #1: the referee is a unit test, not an
opinion.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from core.observability import Knowledge, SeatView
from games.cabal.roles import DEFAULT_THEME, SETUPS, Role, Setup, Team, Theme


class Phase(Enum):
    PROPOSE = "propose"
    VOTE = "vote"
    MISSION = "mission"
    HUNT = "hunt"
    DONE = "done"


class IllegalAction(Exception):
    """A player tried something the rules forbid. The referee refuses; it never
    silently coerces (a coerced illegal move would hide a real agent bug)."""


@dataclass
class CabalReferee:
    setup: Setup
    assignment: dict[int, Role]           # seat -> secret role
    theme: Theme = DEFAULT_THEME
    phase: Phase = Phase.PROPOSE
    mission_index: int = 0
    leader: int = 0
    reject_count: int = 0
    results: list[bool] = field(default_factory=list)   # per finished mission: True=success
    proposal: tuple[int, ...] | None = None
    last_votes: dict[int, bool] | None = None
    winner: Team | None = None
    log: list[str] = field(default_factory=list)

    # ---- construction -----------------------------------------------------

    @classmethod
    def new(cls, n: int = 5, seed: int | None = None, theme: Theme = DEFAULT_THEME) -> "CabalReferee":
        setup = SETUPS[n]
        rng = random.Random(seed)
        roles = list(setup.roles)
        rng.shuffle(roles)
        assignment = {seat: role for seat, role in zip(range(n), roles)}
        ref = cls(setup=setup, assignment=assignment, theme=theme, leader=rng.randrange(n))
        ref.log.append(f"dealt {n} roles; opening leader = seat {ref.leader}")
        return ref

    @property
    def n(self) -> int:
        return self.setup.n

    def evil_seats(self) -> list[int]:
        return [s for s, r in self.assignment.items() if r.team is Team.EVIL]

    def seat_of(self, key: str) -> int:
        for s, r in self.assignment.items():
            if r.key == key:
                return s
        raise KeyError(key)

    # ---- partial observability -------------------------------------------

    def entitled_knowledge(self, seat: int) -> tuple[Knowledge, ...]:
        """The night reveals this seat is entitled to, and nothing more."""
        role = self.assignment[seat]
        out: list[Knowledge] = []
        if role.sees_evil:
            for s in self.evil_seats():
                if s != seat and self.assignment[s].seen_by_seer:
                    out.append(Knowledge(s, "evil"))
        if role.team is Team.EVIL and role.sees_fellow_evil:
            for s in self.evil_seats():
                if s != seat and self.assignment[s].seen_by_fellow_evil:
                    out.append(Knowledge(s, "fellow-evil"))
        if role.sees_magic:
            for s, r in self.assignment.items():
                if r.shown_to_watcher:
                    out.append(Knowledge(s, "magic"))
        return tuple(sorted(out, key=lambda k: (k.seat, k.label)))

    def public_state(self) -> dict:
        return {
            "n": self.n,
            "phase": self.phase.value,
            "mission_index": self.mission_index,
            "team_size": (
                self.setup.team_sizes[self.mission_index]
                if self.mission_index < len(self.setup.team_sizes)
                else None
            ),
            "results": list(self.results),
            "successes": sum(self.results),
            "fails": sum(1 for r in self.results if not r),
            "leader": self.leader,
            "reject_count": self.reject_count,
            "proposal": list(self.proposal) if self.proposal else None,
            "last_votes": dict(self.last_votes) if self.last_votes else None,
            "winner": self.winner.value if self.winner else None,
        }

    def seat_view(self, seat: int) -> SeatView:
        role = self.assignment[seat]
        return SeatView(
            seat=seat,
            own_role=self.theme.role_names[role.key],
            own_team=self.theme.faction_names[role.team],
            knowledge=self.entitled_knowledge(seat),
            public=self.public_state(),
        )

    def render_context(self, seat: int) -> str:
        """The exact text a player agent would receive for this seat. Whatever is
        not here is invisible to that agent - so this string is what gate #1 audits."""
        v = self.seat_view(seat)
        lines: list[str] = []
        if self.theme.blurb:
            lines.append(self.theme.blurb)
            lines.append("")
        lines += [
            f"You are seat {v.seat}. Your role: {v.own_role} ({v.own_team}).",
            f"Players: {self.n} seats, numbered 0..{self.n - 1}.",
        ]
        if v.knowledge:
            lines.append("What the night revealed to you:")
            for k in v.knowledge:
                if k.label == "evil":
                    lines.append(f"  - seat {k.seat} serves darkness.")
                elif k.label == "fellow-evil":
                    lines.append(f"  - seat {k.seat} is one of your own.")
                elif k.label == "magic":
                    lines.append(f"  - seat {k.seat} carries an aura you cannot place.")
        else:
            lines.append("The night told you nothing. You must reason from play alone.")
        p = v.public
        lines.append(
            f"Board: mission {p['mission_index'] + 1}, "
            f"score {p['successes']}-{p['fails']}, "
            f"leader seat {p['leader']}, rejects {p['reject_count']}/5."
        )
        return "\n".join(lines)

    # ---- action layer -----------------------------------------------------

    def _require(self, phase: Phase) -> None:
        if self.phase is not phase:
            raise IllegalAction(f"expected phase {phase.value}, in {self.phase.value}")

    def propose(self, leader: int, team: list[int]) -> None:
        self._require(Phase.PROPOSE)
        if leader != self.leader:
            raise IllegalAction(f"seat {leader} is not the leader (seat {self.leader})")
        size = self.setup.team_sizes[self.mission_index]
        team = list(team)
        if len(team) != size or len(set(team)) != size:
            raise IllegalAction(f"team must be {size} distinct seats, got {team}")
        if any(s not in self.assignment for s in team):
            raise IllegalAction(f"team has unknown seats: {team}")
        self.proposal = tuple(team)
        self.phase = Phase.VOTE
        self.log.append(f"leader {leader} proposes {sorted(team)}")

    def vote(self, votes: dict[int, bool]) -> bool:
        """All seats vote approve(True)/reject(False). Returns whether it passed."""
        self._require(Phase.VOTE)
        if set(votes) != set(self.assignment):
            raise IllegalAction("every seat must vote exactly once")
        self.last_votes = dict(votes)
        approvals = sum(1 for v in votes.values() if v)
        passed = approvals * 2 > self.n
        self.log.append(
            f"vote on {sorted(self.proposal)}: {approvals}/{self.n} approve -> "
            f"{'APPROVED' if passed else 'REJECTED'}"
        )
        if passed:
            self.reject_count = 0
            self.phase = Phase.MISSION
        else:
            self.reject_count += 1
            self.leader = (self.leader + 1) % self.n
            self.proposal = None
            self.phase = Phase.PROPOSE
            if self.reject_count >= 5:
                self._win(Team.EVIL, "five proposals rejected in a row")
        return passed

    def mission(self, cards: dict[int, bool]) -> bool:
        """Team members play success(False)/fail(True). Good may not fail.
        Returns whether the mission succeeded."""
        self._require(Phase.MISSION)
        if set(cards) != set(self.proposal):
            raise IllegalAction("exactly the proposed team plays mission cards")
        for seat, is_fail in cards.items():
            if is_fail and self.assignment[seat].team is Team.GOOD:
                raise IllegalAction(f"good seat {seat} cannot fail a mission")
        fails = sum(1 for f in cards.values() if f)
        need = self.setup.fails_required[self.mission_index]
        success = fails < need
        self.results.append(success)
        self.log.append(
            f"mission {self.mission_index + 1} on {sorted(self.proposal)}: "
            f"{fails} fail(s), need {need} -> {'SUCCESS' if success else 'FAIL'}"
        )
        self.mission_index += 1
        self.leader = (self.leader + 1) % self.n
        self.proposal = None
        self.reject_count = 0
        if sum(1 for r in self.results if not r) >= 3:
            self._win(Team.EVIL, "three missions failed")
        elif sum(self.results) >= 3:
            self.phase = Phase.HUNT
            self.log.append("three missions held; the hunter now seeks the seer")
        else:
            self.phase = Phase.PROPOSE
        return success

    def hunt(self, hunter: int, target: int) -> None:
        """Endgame after good reaches 3 successes: the hunter names a seat as the
        seer. Right = evil steals the win; wrong = good keeps it."""
        self._require(Phase.HUNT)
        if self.assignment[hunter].key != "hunter":
            raise IllegalAction(f"seat {hunter} is not the hunter")
        if target not in self.assignment:
            raise IllegalAction(f"unknown target {target}")
        seer = self.seat_of("seer")
        if target == seer:
            self._win(Team.EVIL, f"hunter found the seer at seat {target}")
        else:
            self._win(Team.GOOD, f"hunter missed the seer (named seat {target})")

    def _win(self, team: Team, why: str) -> None:
        self.winner = team
        self.phase = Phase.DONE
        self.log.append(f"WINNER: {self.theme.faction_names[team]} ({why})")
