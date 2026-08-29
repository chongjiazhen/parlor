"""Deterministic referee for the town-square rung.

Pure code, like every other rung: it deals, walks the night, validates and applies
every day action, takes each discretionary choice from the run's seeded RNG, and
decides the winner. It never chooses a word and never casts a vote.

Three things are different here, and together they are why this rung exists.

**The referee is allowed to lie.** In `cabal` and `changeling` every byte the
referee writes to a seat is true; a seat can be wrong, but only because the world
moved under a fact it was told correctly. Here a poisoned or deluded seat is told
something false ON PURPOSE, in the same words a true reveal uses. Gate #1 is
therefore not "tell the truth to the entitled" - it is "never state a true
association a seat has not earned", and a lie is only safe when it is built to
miss (``night._other_role``).

**The night is a walk, not a resolution.** `changeling` resolves its night in one
pure function because no seat chooses anything. Here the kill, the protection, the
poisoning and two of the information roles are all seat choices, so the referee
stops at each one, asks, and resumes. ``pending()`` is that cursor, and it is the
whole interface the driver needs: whoever is on the clock, whatever they are being
asked.

**The game has days.** A run is a loop over nights and days rather than a single
pass, so the loop needs a structural bound that is not its own win condition -
``max_days``. A referee whose only exit is "somebody won" runs forever the first
time a rule is wrong.

Two public channels leave here, same contract as the other rungs:

  - ``"event"`` - referee-authored fact. Audited by gate #1.
  - ``"speech"`` - what a seat chose to say. A lie there is gameplay.

**No role name ever enters the public channel.** Deaths, executions, votes and
public accusations are announced as seats and never as roles - which is the rule
at a real table too, and here it is also what keeps the public record free of any
association the audit would have to grade.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum

from core.observability import Knowledge, SeatView, find_leaks
from games.belfry import night as nightinfo
from games.belfry.night import Reveal
from games.belfry.roles import (DISTRIBUTION, FIRST_NIGHT, OTHER_NIGHT,
                                ROLES, Align, Script, Team)
from games.belfry.roles import DEFAULT_SCRIPT
from games.belfry.state import Grimoire, deal


class Phase(Enum):
    NIGHT = "night"
    DISCUSS = "discuss"
    NOMINATE = "nominate"
    VOTE = "vote"
    DONE = "done"


class IllegalAction(Exception):
    """A seat tried something the rules forbid. The referee refuses; it never
    silently coerces, because a coerced illegal move hides a real agent bug and
    launders it into the scored data."""


#: A seat that rambles pays for everyone's context. Same cap as the other rungs.
MAX_UTTERANCE_CHARS = 280

#: This game has days, so its public record grows without bound where the one-night
#: rung's could not. A seat reads the tail; the referee-side log keeps all of it.
MAX_RECORD_LINES = 60

#: What a role's night step is called when the referee asks for it.
CHOICE_KIND: dict[str, str] = {
    "venom": "poison",
    "warder": "protect",
    "fiend": "kill",
    "diviner": "divine",
    "valet": "master",
    "oracle": "ravenkeep",
}

#: Pseudo-steps: the evil team's first-night briefings, which belong to no single
#: role and so cannot be positions in a table keyed by role. Numbered into the same
#: order as everything else rather than special-cased before or after it.
MINION_INFO = "__minion_info"
DEMON_INFO = "__demon_info"


def _as_seat(value) -> int:
    """A seat number out of whatever a policy handed over. Raises the referee's
    own refusal rather than a ValueError, so a console typo and a model's bad
    reply travel the same refuse-and-retell path."""
    try:
        return int(value)
    except (TypeError, ValueError):
        raise IllegalAction(f"{value!r} is not a seat number") from None


@dataclass(frozen=True)
class Turn:
    """Whoever is on the clock, and what they are being asked for."""

    seat: int
    kind: str


@dataclass(frozen=True)
class Execution:
    """One execution, with the board it happened on.

    ``alive_before`` and ``evil_before`` are read at the moment of the execution
    and stored, because they are the DENOMINATOR of the only honest question to
    ask of an execution: a table with two evil seats among four alive hits one by
    chance half the time, and the same hit on a table of nine does not mean the
    same thing. Recomputing them afterwards is not possible - the board has moved
    by the time anybody scores it.
    """

    day: int
    seat: int
    #: Was the executed seat alive? A dead seat may be nominated and voted up, and
    #: the day ends on it having killed nobody. Recorded rather than inferred: it
    #: is a real move with a real cost, and folding it in with the executions that
    #: killed somebody is how a table that spent three days on corpses reads as a
    #: table that executed badly.
    was_alive: bool
    alive_before: int
    evil_before: int
    #: Did the table VOTE this seat up, or did a trigger execute it on the spot?
    #: The two are not the same measurement and pooling them broke the day-1
    #: instrument control: a trigger execution names the nominator, and the role
    #: that fires it only fires on a townsfolk nominator, so it is good with
    #: probability 1 while the scorer prices it against the board rate. Recorded
    #: for the same reason ``was_alive`` is - the board has moved by the time
    #: anybody scores it, and nothing downstream can re-derive this.
    by_vote: bool = True


@dataclass
class BelfryReferee:
    grim: Grimoire
    rng: random.Random
    discussion_rounds: int = 1
    #: The structural bound. A referee whose only exit is a win condition runs
    #: forever the first time one of them is wrong, and no test catches that - it
    #: hangs instead of failing.
    max_days: int = 12

    phase: Phase = Phase.NIGHT
    day: int = 1
    winner: str | None = None
    reason: str = ""
    #: A short key for HOW the game ended, beside the sentence saying it. The
    #: sentence is for a person; a scorer that had to match on it would be parsing
    #: prose that is free to be reworded.
    cause: str = ""

    knowledge: dict[int, list[Reveal]] = field(default_factory=dict)
    entitled: dict[int, set[int]] = field(default_factory=dict)
    public_events: list[tuple[str, str]] = field(default_factory=list)
    referee_log: list[str] = field(default_factory=list)

    _turn: Turn | None = None
    _queue: list[str] = field(default_factory=list)
    _triggers: list[Turn] = field(default_factory=list)
    _deaths_tonight: list[int] = field(default_factory=list)
    _speak_order: list[int] = field(default_factory=list)
    _speak_at: int = 0
    _round: int = 0
    _nominee: int | None = None
    _nominator: int | None = None
    _voters: list[int] = field(default_factory=list)
    _votes: dict[int, bool] = field(default_factory=dict)
    block: int | None = None
    #: Highest counted vote any nomination reached today. A later nomination has to
    #: BEAT it, not merely match it - matching clears the block instead.
    _best: int = 0
    executed_today: int | None = None
    last_executed_role: str | None = None
    #: (day, seat) per execution, in order. Kept by the referee rather than derived
    #: by a reader from ``executed_today``, which is a field that is cleared at the
    #: next dawn - a driver watching it has to guess whether the day it is reading
    #: is the day the execution happened on.
    executions: list[Execution] = field(default_factory=list)
    #: What the last speaking seat actually PUBLISHED - normalised and truncated.
    #: A record that kept the raw reply would hold text no seat ever saw.
    last_said: str = ""
    #: Did today already spend its execution? Separate from ``block``, because the
    #: role that executes a nominator on the spot ends the day with nobody standing
    #: - and a dusk that read only ``block`` would announce that nobody died on the
    #: day somebody did, and then hand the good side a win for it.
    _execution_done: bool = False

    # ---- construction --------------------------------------------------------

    @classmethod
    def new(cls, n: int = 7, seed: int | None = None,
            script: Script = DEFAULT_SCRIPT, discussion_rounds: int = 1,
            max_days: int = 12) -> "BelfryReferee":
        rng = random.Random(seed)
        grim = deal(n, script, rng)
        ref = cls(grim=grim, rng=rng, discussion_rounds=discussion_rounds,
                  max_days=max_days)
        ref.knowledge = {s: [] for s in range(n)}
        # A seat is entitled to its own role - except the one seat that is wrong
        # about itself, which must never read its own truth. Same belief/truth
        # split `changeling` is built on, arriving here through a different door.
        ref.entitled = {s: ({s} if grim.seat(s).believes is grim.seat(s).role
                            else set())
                        for s in range(n)}
        ref.referee_log.extend(grim.log)
        ref.public_events.append(
            ("event", f"Night 1. {n} seats, numbered 0..{n - 1}."))
        ref._begin_night(first=True)
        ref._advance()
        return ref

    @property
    def n(self) -> int:
        return self.grim.n

    # ---- the cursor ----------------------------------------------------------

    def pending(self) -> Turn | None:
        """Whoever is on the clock. ``None`` means the game is over."""
        return self._turn

    @property
    def nominee(self) -> int | None:
        """The seat this vote is about, or ``None`` outside a vote."""
        return self._nominee

    def acting_seats(self) -> tuple[int, ...]:
        return () if self._turn is None else (self._turn.seat,)

    def done(self) -> bool:
        return self.phase is Phase.DONE

    # ---- the night -----------------------------------------------------------

    def _begin_night(self, first: bool) -> None:
        self.phase = Phase.NIGHT
        self._deaths_tonight = []
        # Poison lasts until the poisoner's next step, so it clears here whether or
        # not the poisoner is alive to renew it - otherwise killing the poisoner
        # would leave its last victim poisoned for the rest of the game.
        for seat in self.grim.seats:
            seat.poisoned = False
            seat.protected = False
        if first:
            order = [(r.first_night, r.key) for r in FIRST_NIGHT]
            order += [(15, MINION_INFO), (16, DEMON_INFO)]
        else:
            order = [(r.other_night, r.key) for r in OTHER_NIGHT]
        self._queue = [key for _, key in sorted(order)]

    def _night_step(self) -> None:
        while self._triggers:
            self._turn = self._triggers.pop(0)
            return
        while self._queue:
            if self.phase is Phase.DONE:
                return
            key = self._queue.pop(0)
            if key in (MINION_INFO, DEMON_INFO):
                self._evil_briefing(key)
                continue
            # Walked by BELIEF: a seat wrong about itself still wakes at the step
            # of the role it thinks it holds, and still expects to be told
            # something. A night that walked by truth would skip it, and the seat
            # would learn what it is from the silence.
            seat = self.grim.find_believer(key)
            if seat is None or not self.grim.seat(seat).alive:
                continue
            if key in CHOICE_KIND:
                self._turn = Turn(seat, CHOICE_KIND[key])
                return
            self._deliver(seat, key)
        self._dawn()

    def _evil_briefing(self, which: str) -> None:
        """The first night's two briefings. Always true, and deliberately so: they
        are not an ability, so nothing that switches an ability off touches them,
        and an evil team that could be split by poisoning its own briefing is a
        different game."""
        demon = self.grim.demon_seat()
        minions = self.grim.minions()
        if demon is None:
            return
        if which == MINION_INFO:
            for m in minions:
                for other in minions + [demon]:
                    if other != m:
                        self._reveal(m, self._name_reveal(other))
        else:
            for m in minions:
                self._reveal(demon, self._name_reveal(m))
            if self.grim.bluffs:
                names = ", ".join(ROLES[b].display for b in self.grim.bluffs)
                self._reveal(demon, Reveal(
                    self.day,
                    f"These roles are not in play tonight: {names}."))

    def _name_reveal(self, seat: int) -> Reveal:
        role = self.grim.registers_as(seat)
        return Reveal(self.day, f"Seat {seat} is the {role.display}.",
                      seats=(seat,), role=role.key, truthful=True)

    def _deliver(self, seat: int, key: str) -> None:
        """Resolve one information step that needs no choice."""
        rng, grim, day = self.rng, self.grim, self.day
        if key == "witness":
            self._reveal(seat, nightinfo.witness(grim, rng, seat, day))
        elif key == "archivist":
            self._reveal(seat, nightinfo.archivist(grim, rng, seat, day))
        elif key == "tracker":
            self._reveal(seat, nightinfo.tracker(grim, rng, seat, day))
        elif key == "tally":
            self._reveal(seat, nightinfo.tally(grim, rng, seat, day))
        elif key == "gauge":
            self._reveal(seat, nightinfo.gauge(grim, rng, seat, day))
        elif key == "mimic":
            for r in nightinfo.watch_the_board(grim, rng, seat, day):
                self._reveal(seat, r)
        elif key == "mortician":
            if self.last_executed_role is None:
                self._reveal(seat, Reveal(day, "Nobody was executed yesterday."))
            else:
                self._reveal(seat, nightinfo.name_role(
                    grim, rng, seat, day, self.executed_today,
                    "Yesterday's execution: seat {seat} is the {role}."))

    def _reveal(self, seat: int, r: Reveal) -> None:
        """Write one line into a seat's private knowledge, and grade it.

        Entitlement is granted HERE and nowhere else, which is what makes the audit
        a check on the referee rather than a restatement of it: the referee has to
        commit, at the moment it writes a fact, to the claim that this seat has
        earned it. A reveal graded against the grimoire (``Reveal.entitles``) is
        the one that counts - a sentence that is true about how a seat REGISTERS is
        not entitlement to what that seat IS.
        """
        self.knowledge[seat].append(r)
        earned = r.entitles(self.grim)
        if earned is not None:
            self.entitled[seat].add(earned)
        self.referee_log.append(
            f"night {r.night}: seat {seat} <- {r.text}"
            + ("" if r.truthful else "   (FALSE - its ability is off)"))

    # ---- deaths --------------------------------------------------------------

    def _kill(self, seat: int, cause: str, announce: bool = True) -> None:
        row = self.grim.seat(seat)
        if not row.alive:
            return
        row.alive = False
        self.referee_log.append(f"death: seat {seat} ({row.role.key}) by {cause}")
        if announce:
            self.public_events.append(("event", f"Seat {seat} is dead."))
        elif self.phase is Phase.NIGHT:
            # Held back to dawn: the table learns who died in the night all at
            # once, and never in the order the night resolved them.
            self._deaths_tonight.append(seat)
        if row.believes.key == "oracle" and cause == "night":
            # It wakes because it died, so its step is a trigger rather than a
            # position in the order. Keyed on BELIEF: the seat that only thinks it
            # holds this role wakes too and is told something false, because a seat
            # that slept through its own death would have learnt what it is from
            # the silence.
            self._triggers.append(Turn(seat, "ravenkeep"))
        if row.role.team is Team.DEMON:
            self._demon_died(cause)
        self._check_win()

    def _demon_died(self, cause: str) -> None:
        """The demon changing hands, which is the one way this game does not end.

        Two different rules, kept apart because they answer to different things: a
        demon that kills itself passes the role to a minion outright, while a demon
        the town killed passes it only to the role written for that, and only while
        the table is still big enough.
        """
        alive_minions = [m for m in self.grim.minions()
                         if self.grim.seat(m).alive]
        heir = self.grim.find("heir")
        successor: int | None = None
        if cause == "self" and alive_minions:
            successor = heir if heir in alive_minions else self.rng.choice(
                alive_minions)
        elif heir is not None and self.grim.seat(heir).alive \
                and len(self.grim.alive_seats()) >= 5:
            successor = heir
        if successor is None:
            return
        fiend = ROLES["fiend"]
        row = self.grim.seat(successor)
        self.referee_log.append(
            f"discretion: seat {successor} ({row.role.key}) becomes the demon")
        row.role = fiend
        row.believes = fiend
        self.entitled[successor].add(successor)
        self._reveal(successor, Reveal(
            self.day, "You are the demon now.", seats=(successor,),
            role="fiend", truthful=True))

    def _demon_kill(self, chooser: int, target: int) -> None:
        grim = self.grim
        if grim.droisoned(chooser):
            self.referee_log.append(
                f"night {self.day}: the demon's choice of seat {target} does "
                f"nothing - its ability is off")
            return
        if target == chooser:
            self._kill(target, "self", announce=False)
            return
        row = grim.seat(target)
        if row.role.key == "bulwark" and not grim.droisoned(target):
            self.referee_log.append(f"night {self.day}: seat {target} cannot be "
                                    f"killed by the demon")
            return
        if row.protected:
            self.referee_log.append(f"night {self.day}: seat {target} was "
                                    f"protected tonight")
            return
        if row.role.key == "speaker" and not grim.droisoned(target):
            others = [s for s in grim.alive_seats()
                      if s not in (target, chooser)]
            if others and self.rng.random() < 0.5:
                bounced = self.rng.choice(others)
                self.referee_log.append(
                    f"discretion: the kill on seat {target} lands on seat "
                    f"{bounced} instead")
                self._kill(bounced, "night", announce=False)
                return
        self._kill(target, "night", announce=False)

    # ---- dawn and dusk -------------------------------------------------------

    def _dawn(self) -> None:
        if self.phase is Phase.DONE:
            return
        dead = sorted(self._deaths_tonight)
        if dead:
            self.public_events.append(
                ("event", "Dawn. " + ", ".join(f"Seat {s} is dead." for s in dead)))
        else:
            self.public_events.append(("event", "Dawn. Nobody died in the night."))
        self._check_win()
        if self.phase is Phase.DONE:
            return
        self.grim.clear_day()
        self.block = None
        self._best = 0
        self.executed_today = None
        self.last_executed_role = None
        self._execution_done = False
        self._round = 0
        self._speak_at = 0
        # The dead speak. They have lost their ability and most of their vote and
        # they keep the only thing this game runs on, which is what they know.
        self._speak_order = list(range(self.n))
        self.phase = Phase.DISCUSS
        self.public_events.append(
            ("event", f"Day {self.day}: {self.discussion_rounds} round(s) of talk, "
                      f"then nominations. Alive: "
                      + ", ".join(str(s) for s in self.grim.alive_seats()) + "."))

    def _execute(self, seat: int, by_vote: bool = True) -> None:
        """One execution, wherever it came from - the seat left standing at dusk,
        or the seat a trigger executed on the spot. One function, because the
        losing condition attached to executing a particular role has to fire on
        both paths and a second copy is how it comes to fire on only one. Which
        path it came from is recorded, because the two do not measure the same
        thing (see ``Execution.by_vote``)."""
        self.executed_today = seat
        self.last_executed_role = self.grim.registers_as(seat).key
        alive = self.grim.alive_seats()
        self.executions.append(Execution(
            day=self.day, seat=seat, was_alive=self.grim.seat(seat).alive,
            alive_before=len(alive),
            evil_before=sum(1 for s in alive
                            if self.grim.seat(s).align is Align.EVIL),
            by_vote=by_vote))
        self._execution_done = True
        role = self.grim.role_of(seat)
        self.public_events.append(("event", f"Seat {seat} is executed."))
        self._kill(seat, "execution", announce=False)
        if role.key == "pilgrim" and not self.grim.droisoned(seat):
            self._finish(Align.EVIL,
                         f"seat {seat} was executed and is the {role.display}",
                         "bad-execution")

    def _dusk(self) -> None:
        if self.block is not None:
            self._execute(self.block)
            if self.phase is Phase.DONE:
                return
        elif not self._execution_done:
            self.public_events.append(("event", "Nobody is executed today."))
            speaker = self.grim.find("speaker")
            if speaker is not None and self.grim.seat(speaker).alive \
                    and not self.grim.droisoned(speaker) \
                    and len(self.grim.alive_seats()) == 3:
                self._finish(Align.GOOD, "three seats were alive at dusk and "
                                         "nobody was executed", "speaker")
                return
        self._check_win()
        if self.phase is Phase.DONE:
            return
        if self.day >= self.max_days:
            self.phase = Phase.DONE
            self.winner = None
            self.cause = "day-bound"
            self.reason = (f"no winner: the {self.max_days}-day bound was reached. "
                           f"A game this long is a result about the table, not a "
                           f"win for either side.")
            self.referee_log.append(self.reason)
            self._turn = None
            return
        self.day += 1
        self.public_events.append(("event", f"Night {self.day} falls."))
        self._begin_night(first=False)

    def _check_win(self) -> None:
        if self.phase is Phase.DONE:
            return
        demon = self.grim.demon_seat()
        if demon is None or not self.grim.seat(demon).alive:
            self._finish(Align.GOOD, "no demon is alive", "demon-dead")
            return
        if len(self.grim.alive_seats()) <= 2:
            self._finish(Align.EVIL, "two seats are alive and the demon is one "
                                     "of them", "attrition")

    def _finish(self, side: Align, why: str, cause: str) -> None:
        self.phase = Phase.DONE
        self.winner = side.value
        self.cause = cause
        self.reason = f"WINNER: {side.value} ({why})"
        self._turn = None
        self.public_events.append(
            ("event", f"The game ends. The {side.value} side wins."))
        self.referee_log.append(self.reason)
        self.referee_log.append("final board: " + ", ".join(
            f"seat {s.index}={s.role.key}{'' if s.alive else ' (dead)'}"
            for s in self.grim.seats))

    # ---- the state machine ---------------------------------------------------

    def _advance(self) -> None:
        """Walk until somebody is on the clock, or the game is over."""
        self._turn = None
        guard = 0
        while self.phase is not Phase.DONE and self._turn is None:
            guard += 1
            if guard > 1000:
                raise IllegalAction("the referee did not reach a decision point; "
                                    "this is a rules bug, not a game state")
            if self.phase is Phase.NIGHT:
                self._night_step()
            elif self.phase is Phase.DISCUSS:
                self._discuss_step()
            elif self.phase is Phase.NOMINATE:
                self._nominate_step()
            elif self.phase is Phase.VOTE:
                self._vote_step()

    def _discuss_step(self) -> None:
        if self._round >= self.discussion_rounds:
            self.phase = Phase.NOMINATE
            self.public_events.append(
                ("event", "Nominations are open. A living seat may nominate one "
                          "seat, alive or dead, once today."))
            return
        seat = self._speak_order[self._speak_at]
        self._turn = Turn(seat, "speak")

    def _nominate_step(self) -> None:
        for seat in self.grim.alive_seats():
            if not self.grim.seat(seat).nominated_today:
                self._turn = Turn(seat, "nominate")
                return
        self._dusk()

    def _vote_step(self) -> None:
        for seat in self._voters:
            if seat not in self._votes:
                self._turn = Turn(seat, "vote")
                return
        self._close_vote()

    # ---- legality ------------------------------------------------------------

    def legal_targets(self, seat: int, kind: str) -> list[int]:
        """Every seat this move may name. One source, read by the ask, by the
        player's own check and by the refusal - three copies of this list is how a
        seat gets refused for a move the prompt told it to make."""
        alive = self.grim.alive_seats()
        if kind == "poison":
            return alive
        if kind == "protect":
            return [s for s in alive if s != seat]
        if kind == "kill":
            return alive
        if kind == "divine":
            return list(range(self.n))
        if kind == "master":
            return [s for s in alive if s != seat]
        if kind == "ravenkeep":
            return [s for s in range(self.n) if s != seat]
        if kind == "nominate":
            return [s for s in range(self.n)
                    if not self.grim.seat(s).was_nominated_today]
        if kind == "slay":
            return [s for s in alive if s != seat]
        return []

    def eligible_voters(self, nominee: int) -> list[int]:
        """Everyone who can raise a hand, in order round the table from the seat
        after the nominee. A dead seat has one vote for the whole game."""
        order = [(nominee + 1 + i) % self.n for i in range(self.n)]
        return [s for s in order
                if self.grim.seat(s).alive or self.grim.seat(s).ghost_vote]

    def votes_needed(self) -> int:
        return math.ceil(len(self.grim.alive_seats()) / 2)

    # ---- what a seat may see -------------------------------------------------

    def public_state(self) -> dict:
        return {
            "n": self.n,
            "day": self.day,
            "phase": self.phase.value,
            "alive": self.grim.alive_seats(),
            "block": self.block,
            "votes_needed": self.votes_needed(),
            "script": self.grim.script.name,
        }

    def seat_view(self, seat: int) -> SeatView:
        row = self.grim.seat(seat)
        return SeatView(
            seat=seat,
            own_role=row.believes.display,
            own_team=row.believes.team.value,
            knowledge=tuple(Knowledge(seat=r.seats[0] if len(r.seats) == 1 else -1,
                                      label=r.role or r.text)
                            for r in self.knowledge[seat]),
            public=self.public_state(),
        )

    def reveal_forms(self, seat: int, key: str) -> list[str]:
        """**Every phrasing this referee can emit that ties ``seat`` to ``key``.**

        One string, and every single-seat reveal in the game is built to CONTAIN
        it - the briefing, the board-watcher's list, the seat that wakes as it
        dies, the morning after an execution. Matching is case-insensitive
        substring, so a sentence may wrap the form ("Yesterday\'s execution: seat 3
        is the Warder.") and still carry it. What a sentence may not do is split
        it: "seat 3 was executed yesterday and is the Warder" says the same thing
        and contains nothing this term would match, so a reveal written that way
        would be invisible to the audit. That is why the wrapping is a prefix and
        the phrasing of every reveal is asserted in ``test_audit`` rather than
        trusted to this docstring.
        """
        return [f"seat {seat} is the {ROLES[key].display}"]

    def self_reveal_forms(self, key: str) -> list[str]:
        """The phrasing that would tell a seat what it actually is. Separate,
        because the referee addresses a seat in the second person and a self-leak
        looks nothing like a third-party one."""
        return [f"you are the {ROLES[key].display}"]

    def secret_terms(self) -> dict[int, list[str]]:
        return {s: self.reveal_forms(s, self.grim.role_of(s).key)
                for s in range(self.n)}

    def preamble(self) -> str:
        """The rules and the script. **Byte-identical for every seat.**

        The script is public and every ability on it is public - which roles are IN
        PLAY is the secret, and what each one would do is not. A seat that cannot
        read an ability cannot evaluate anybody's claim to hold it, which is the
        whole day. That makes this the largest item in the payload and the reason
        the compact script exists: this text is paid on every call of every seat.
        """
        town, out, minion, demon = DISTRIBUTION[self.n]
        lines = [
            f"You are at a table of {self.n} seats, numbered 0..{self.n - 1}, "
            f"sitting in a circle. Some of you are evil and know each other; the "
            f"rest are good and know almost nothing.",
            "",
            f"The deal: {town} townsfolk, {out} outsider(s), {minion} minion(s) "
            f"and {demon} demon. Townsfolk and outsiders are good; minions and the "
            f"demon are evil. These counts are public, and a role on the script "
            f"can change them.",
            "",
            "The script - every role that COULD be at this table, and what it "
            "does. Which of them are in play is the thing you are here to work "
            "out:",
        ]
        for team in (Team.TOWNSFOLK, Team.OUTSIDER, Team.MINION, Team.DEMON):
            for role in self.grim.script.by_team(team):
                lines.append(f"  {role.display} ({team.value}) - {role.power}.")
        lines += [
            "",
            "How a day runs: everyone talks, then any living seat may nominate one "
            "seat once. Everyone with a vote answers each nomination at the same "
            "time. A nomination needs at least half the living seats to carry, and "
            "must beat the best count so far; the seat standing when nominations "
            "end is executed. A dead seat keeps its voice all game and one single "
            "vote.",
            "Good wins when the demon is dead. Evil wins when two seats are left "
            "alive with the demon among them.",
            "Some roles are told things that are false, and they are not told "
            "that. Weigh what you were told against what the table says.",
        ]
        return "\n".join(lines)

    def self_line(self, seat: int) -> str:
        """What the referee asserts about this seat TO this seat. One line, so a
        self-leak has exactly one place it can live and the audit exactly one place
        to look."""
        row = self.grim.seat(seat)
        state = "alive" if row.alive else "dead, and still at the table"
        return (f"You are seat {seat}, {state}. You are the "
                f"{row.believes.display} ({row.believes.team.value}).")

    def seat_lines(self, seat: int, include_speech: bool = True) -> str:
        lines = [self.self_line(seat)]
        row = self.grim.seat(seat)
        if not row.alive and row.ghost_vote:
            lines.append("You still hold your one vote.")
        elif not row.alive:
            lines.append("You have spent your vote. You can still talk.")
        if row.master is not None:
            lines.append(f"Your master is seat {row.master}. Your vote for an "
                         f"execution counts only when your master votes for it "
                         f"too.")
        mine = self.knowledge[seat]
        if mine:
            lines.append("What you have been told, in order:")
            lines += [f"  night {r.night}: {r.text}" for r in mine]
        else:
            lines.append("You have been told nothing. Reason from the table.")
        lines.append("")
        lines.append("Alive: " + ", ".join(str(s) for s in self.grim.alive_seats())
                     + ".")
        if self.block is not None:
            lines.append(f"Seat {self.block} is standing for execution with "
                         f"{self._best} vote(s).")
        record = [text for tag, text in self.public_events
                  if include_speech or tag == "event"]
        if record:
            lines += ["", "The table so far:"]
            lines += [f"  {line}" for line in record[-MAX_RECORD_LINES:]]
        return "\n".join(lines)

    def render_context(self, seat: int, include_speech: bool = True) -> str:
        return self.preamble() + "\n\n" + self.seat_lines(seat, include_speech)

    # ---- the ask -------------------------------------------------------------

    def ask(self, seat: int) -> str:
        """The question put to one seat, phrased positively per
        ``.claude/rules/model-facing-text.md``. Carries what THIS decision needs
        and no standing rules dump - the script above is already the standing
        context, and every byte here is paid by every seat on every turn."""
        turn = self._turn
        if turn is None or turn.seat != seat:
            raise IllegalAction(f"seat {seat} is not on the clock")
        kind = turn.kind
        think = '"think": "your private reasoning"'
        if kind == "speak":
            return ("Speak to the table. Reply as one JSON object: "
                    f'{{{think}, "say": "what the table hears"}}. '
                    f"Keep `say` under {MAX_UTTERANCE_CHARS} characters. To spend "
                    'a public day power on a seat, add "slay": <seat number> - '
                    "anybody may call a seat the demon out loud, and the referee "
                    "says what happens.")
        if kind == "vote":
            return (f"Seat {self._nominee} stands accused, nominated by seat "
                    f"{self._nominator}. It takes {self.votes_needed()} vote(s) "
                    f"to carry. Everyone answers at once. Reply as one JSON "
                    f'object: {{{think}, "vote": true or false}}.')
        legal = ", ".join(str(s) for s in self.legal_targets(seat, kind))
        if kind == "nominate":
            return ("Nominate one seat for execution, or pass. Reply as one JSON "
                    f'object: {{{think}, "nominate": <seat number> or null}}. '
                    f"Seats still open to nomination: {legal}.")
        prompts = {
            "poison": "Choose a seat. Until dusk tomorrow its ability does "
                      "nothing and anything it is told is false.",
            "protect": "Choose a seat to keep safe from the demon tonight.",
            "kill": "Choose a seat to kill tonight.",
            "master": "Choose your master for tomorrow's votes.",
            "ravenkeep": "You are dying. Choose a seat and you will learn its "
                         "role.",
        }
        if kind == "divine":
            return ("Choose two seats and learn whether either of them is the "
                    f"demon. Reply as one JSON object: {{{think}, "
                    '"targets": [<seat>, <seat>]}. '
                    f"Choose from: {legal}.")
        return (f"{prompts[kind]} Reply as one JSON object: "
                f'{{{think}, "target": <seat number>}}. '
                f"Choose from: {legal}.")

    def prompt_for(self, seat: int, include_speech: bool = True) -> str:
        return self.render_context(seat, include_speech) + "\n\n" + self.ask(seat)

    # ---- applying a move -----------------------------------------------------

    def submit(self, seat: int, action: dict) -> None:
        """Apply one seat's answer and walk on to the next decision point.

        Every legality check lives here rather than in the driver, so a policy the
        repo has never seen - a person at a console, a test double, a model
        answering in a shape nobody anticipated - meets the same rules as the two
        policies that ship.
        """
        turn = self._turn
        if turn is None:
            raise IllegalAction("the game is over")
        if turn.seat != seat:
            raise IllegalAction(f"seat {turn.seat} is on the clock, not {seat}")
        kind = turn.kind
        if kind == "speak":
            self._apply_speak(seat, action)
        elif kind == "nominate":
            self._apply_nominate(seat, action)
        elif kind == "vote":
            self._apply_vote(seat, action)
        else:
            self._apply_night(seat, kind, action)
        self._advance()

    def _apply_speak(self, seat: int, action: dict) -> None:
        said = " ".join(str(action.get("say", "")).split())[:MAX_UTTERANCE_CHARS]
        if not said:
            raise IllegalAction("an empty utterance is not a move")
        self.last_said = said
        self.public_events.append(("speech", f"Seat {seat}: {said}"))
        target = action.get("slay")
        if target is not None:
            self._apply_slay(seat, _as_seat(target))
        self._speak_at += 1
        if self._speak_at >= len(self._speak_order):
            self._speak_at = 0
            self._round += 1

    def _apply_slay(self, seat: int, target: int) -> None:
        """The one public power, and ANY seat may spend it.

        That is deliberate and it is the point of putting it in the day channel: a
        seat with no such ability can still stand up and name the demon, and the
        referee answers in the same words either way. A power only its true holder
        could invoke would make every invocation a proof of the role.
        """
        row = self.grim.seat(seat)
        if not row.alive:
            raise IllegalAction(f"seat {seat} is dead and cannot use a day power")
        if row.used_power:
            raise IllegalAction(f"seat {seat} has already spent its day power")
        if target not in self.legal_targets(seat, "slay"):
            raise IllegalAction(
                f"seat {target} cannot be named; choose from "
                f"{self.legal_targets(seat, 'slay')}")
        row.used_power = True
        self.public_events.append(
            ("event", f"Seat {seat} stands up and calls seat {target} the demon."))
        works = (row.role.key == "duelist" and not self.grim.droisoned(seat)
                 and self.grim.registers_demon(target))
        if works:
            self._kill(target, "day power", announce=True)
        else:
            self.public_events.append(("event", "Nothing happens."))

    def _apply_nominate(self, seat: int, action: dict) -> None:
        target = action.get("nominate")
        self.grim.seat(seat).nominated_today = True
        if target is None:
            self.public_events.append(("event", f"Seat {seat} passes."))
            return
        target = _as_seat(target)
        if target not in self.legal_targets(seat, "nominate"):
            self.grim.seat(seat).nominated_today = False
            raise IllegalAction(
                f"seat {target} has already been nominated today; choose from "
                f"{self.legal_targets(seat, 'nominate')}")
        row = self.grim.seat(target)
        first_time = not row.ever_nominated
        row.was_nominated_today = True
        row.ever_nominated = True
        self.public_events.append(
            ("event", f"Seat {seat} nominates seat {target}."))
        if (row.role.key == "martyr" and first_time
                and not self.grim.droisoned(target)
                and self.grim.seat(seat).role.team is Team.TOWNSFOLK):
            self.public_events.append(
                ("event", "Nominating that seat ends the day at once."))
            self.block = None
            self._execute(seat, by_vote=False)
            if self.phase is not Phase.DONE:
                for s in self.grim.seats:
                    s.nominated_today = True
            return
        self._nominator = seat
        self._nominee = target
        self._votes = {}
        self._voters = self.eligible_voters(target)
        self.phase = Phase.VOTE

    def _apply_vote(self, seat: int, action: dict) -> None:
        value = action.get("vote")
        if not isinstance(value, bool):
            raise IllegalAction("a vote is true or false")
        self._votes[seat] = value

    def _close_vote(self) -> None:
        """Count the hands, and count them once.

        A vote that does not count is dropped SILENTLY from the public tally rather
        than announced as dropped. The seat whose vote it was knows why - its own
        render says so - and nobody else learns anything, which is exactly the
        rule at a table where that seat simply keeps its hand down.
        """
        nominee = self._nominee
        counted = []
        for s, yes in self._votes.items():
            if not yes:
                continue
            row = self.grim.seat(s)
            if row.role.key == "valet" and not self.grim.droisoned(s):
                if row.master is None or not self._votes.get(row.master, False):
                    self.referee_log.append(
                        f"day {self.day}: seat {s} voted for the execution of "
                        f"seat {nominee} and it did not count")
                    continue
            counted.append(s)
            if not row.alive:
                row.ghost_vote = False
        tally = len(counted)
        self.public_events.append(
            ("event", f"Votes for executing seat {nominee}: {tally} "
                      f"({', '.join(str(s) for s in sorted(counted)) or 'nobody'})."))
        if tally >= self.votes_needed() and tally > self._best:
            self.block = nominee
            self._best = tally
            self.public_events.append(
                ("event", f"Seat {nominee} is standing for execution."))
        elif tally >= self.votes_needed() and tally == self._best:
            self.block = None
            self.public_events.append(
                ("event", "That ties the highest count, so nobody is standing "
                          "for execution."))
        self._nominee = None
        self._nominator = None
        self._voters = []
        self._votes = {}
        self.phase = Phase.NOMINATE

    def _apply_night(self, seat: int, kind: str, action: dict) -> None:
        if kind == "divine":
            picks = action.get("targets") or []
            if len(picks) != 2 or len(set(picks)) != 2:
                raise IllegalAction("choose two different seats")
            for p in picks:
                if p not in self.legal_targets(seat, kind):
                    raise IllegalAction(f"seat {p} is not a legal choice")
            self._reveal(seat, nightinfo.divine(
                self.grim, self.rng, seat, self.day, (picks[0], picks[1])))
            return
        target = action.get("target")
        if target is None:
            raise IllegalAction("choose a seat")
        target = _as_seat(target)
        if target not in self.legal_targets(seat, kind):
            raise IllegalAction(
                f"seat {target} is not a legal choice; choose from "
                f"{self.legal_targets(seat, kind)}")
        if kind == "poison":
            if not self.grim.droisoned(seat):
                self.grim.seat(target).poisoned = True
            self.referee_log.append(f"night {self.day}: seat {seat} poisons seat "
                                    f"{target}")
        elif kind == "protect":
            if not self.grim.droisoned(seat):
                self.grim.seat(target).protected = True
            self.referee_log.append(f"night {self.day}: seat {seat} protects seat "
                                    f"{target}")
        elif kind == "kill":
            self._demon_kill(seat, target)
        elif kind == "master":
            self.grim.seat(seat).master = target
        elif kind == "ravenkeep":
            self._reveal(seat, nightinfo.name_role(
                self.grim, self.rng, seat, self.day, target,
                "Seat {seat} is the {role}."))

    # ---- gate #1 -------------------------------------------------------------

    def audit(self, viewer: int) -> list[tuple[int, str]]:
        """Gate #1 for one seat. Two scans at two scopes, as `changeling` does.

        **Other seats' roles, against everything written to this seat** except the
        preamble, which is seat-invariant and so cannot carry a per-seat secret.
        **This seat's own role, against its own line only**, and only for the seat
        that is wrong about itself - the one seat here with no entitlement to its
        own truth.
        """
        others = {s: t for s, t in self.secret_terms().items() if s != viewer}
        leaks = find_leaks(
            self.seat_lines(viewer, include_speech=False),
            others,
            self.entitled[viewer],
            viewer,
        )
        if viewer not in self.entitled[viewer]:
            leaks += find_leaks(
                self.self_line(viewer),
                {viewer: self.self_reveal_forms(self.grim.role_of(viewer).key)},
                set(),
                viewer,
                self_is_secret=True,
            )
        return leaks

    def audit_all(self) -> dict[int, list[tuple[int, str]]]:
        found = {s: self.audit(s) for s in range(self.n)}
        return {s: leaks for s, leaks in found.items() if leaks}
