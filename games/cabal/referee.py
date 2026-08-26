"""Deterministic referee for the hidden-role mission game.

The referee is pure code: it deals roles, computes each seat's entitled night
knowledge, validates and applies the actions players choose (speak, propose, vote,
play a mission card, hunt), tracks state, and detects the win. It never decides a
proposal or a vote - that is the players' job (random or LLM). No judgment lives
here, which is why this game is spike #1: the referee is a unit test, not an
opinion.

Two channels leave this module, and the difference is the whole point:

  - ``public_events`` tagged ``"event"`` are referee-authored facts. Everyone sees
    them, so they are audited by gate #1 - a referee that named a role here would
    be leaking.
  - ``public_events`` tagged ``"speech"`` are what a player chose to say out loud.
    A lie there is gameplay, not a leak, so the audit skips them
    (``render_context(seat, include_speech=False)``). What never enters either
    channel is a player's private reasoning: ``speak()`` takes exactly the one
    string the player nominated as public.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from core.observability import Knowledge, SeatView
from games.cabal.roles import DEFAULT_THEME, SETUPS, Role, Setup, Team, Theme


class Phase(Enum):
    PROPOSE = "propose"
    DISCUSS = "discuss"
    VOTE = "vote"
    MISSION = "mission"
    HUNT = "hunt"
    DONE = "done"


class IllegalAction(Exception):
    """A player tried something the rules forbid. The referee refuses; it never
    silently coerces (a coerced illegal move would hide a real agent bug)."""


#: Hard cap on one utterance. A player that rambles pays for everyone's context.
MAX_UTTERANCE_CHARS = 280

#: Hard cap on one notebook line, and how many lines a seat's notebook keeps.
#:
#: The notebook is not ``think``. ``think`` is written once and dropped, so it
#: costs one reply; a notebook line is re-sent to its author on EVERY later call,
#: so it is a standing bill that grows with the game unless something bounds it.
#: A rolling window of the last few lines is also the honest model of what it is
#: for - a human carries a handful of reads into the next round, not a ledger.
MAX_NOTE_CHARS = 160
MAX_NOTEBOOK_LINES = 6

#: How many lines of public record a seat sees. A 5-seat game never reaches this,
#: but the record is re-sent on EVERY call, so an unbounded one turns a long game
#: into a quadratic context bill - and the games further up the ladder are longer.
#: Trimming is safe for gate #1: what scrolls off the render leaves the model's
#: payload too, so it cannot leak what it no longer contains.
MAX_RECORD_LINES = 60


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
    # discussion: round-robin utterances between PROPOSE and VOTE. Bounded, because
    # on a serial local backend each round costs n model calls.
    discussion_rounds: int = 1
    #: Sequential discussion (the default) hands each speaker everything said before
    #: it in the same round, so late seats are anchored on early ones by
    #: construction - and a table that only ever restates the first read has no
    #: disagreement for deduction to work with. Simultaneous discussion collects a
    #: round against ONE board state and publishes it together: every seat commits
    #: before it sees any of its neighbours. Off by default because it changes what
    #: the game is, not just how it reads; measure the two against the same seeds.
    simultaneous: bool = False
    #: Per-seat private notebook: a seat's own words, filed under its own seat and
    #: shown back to it and to nobody else. It closes the one real gap in "play like
    #: a human" - ``think`` is dropped every turn, so a seat re-derives its read from
    #: scratch and cannot remember that it caught seat 2 lying in round 1.
    #:
    #: Off by default, and that is not timidity: it rides on every call and changes
    #: what the seats can do, so it is a MEASURED change under
    #: ``.claude/rules/model-facing-text.md`` - same seeds, one variable, and the
    #: runs already in flight were scored without it.
    notebook: bool = False
    notes: dict[int, list[str]] = field(default_factory=dict)
    _pending_speech: list[tuple[str, str]] = field(default_factory=list)
    speech_ptr: int = 0                                  # slots consumed this discussion
    max_record_lines: int = MAX_RECORD_LINES
    # ("event", text) referee-authored | ("speech:<seat>", text) player-authored.
    # Order preserved: the record is one interleaved timeline.
    public_events: list[tuple[str, str]] = field(default_factory=list)

    # ---- construction -----------------------------------------------------

    @classmethod
    def new(
        cls,
        n: int = 5,
        seed: int | None = None,
        theme: Theme = DEFAULT_THEME,
        discussion_rounds: int = 1,
        simultaneous: bool = False,
        notebook: bool = False,
    ) -> "CabalReferee":
        setup = SETUPS[n]
        rng = random.Random(seed)
        roles = list(setup.roles)
        rng.shuffle(roles)
        assignment = {seat: role for seat, role in zip(range(n), roles)}
        ref = cls(
            setup=setup,
            assignment=assignment,
            theme=theme,
            leader=rng.randrange(n),
            discussion_rounds=discussion_rounds,
            simultaneous=simultaneous,
            notebook=notebook,
        )
        # deal is referee-side only: it never enters public_events
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

    # ---- public channels --------------------------------------------------

    def _event(self, text: str) -> None:
        """A referee-authored public fact. Audited by gate #1."""
        self.public_events.append(("event", text))
        self.log.append(text)

    def _private_log(self, text: str) -> None:
        """Referee-side bookkeeping. Never rendered to any seat."""
        self.log.append(text)

    def note(self, seat: int, text: str) -> str | None:
        """File one line in ``seat``'s private notebook. Returns the stored line, or
        ``None`` if there was nothing to store.

        This is a THIRD channel and it belongs to neither of the other two: not an
        event (the referee did not author it), not speech (the table never reads
        it). It is the only text a seat writes that it will read again.

        No refusal here, unlike ``speak()``. A seat owes the referee a move every
        turn; it owes it nothing at all in the notebook, so an empty note is a seat
        choosing not to write, not an illegal action. Truncation is silent for the
        same reason: a rambling note costs its author context and nobody else, so
        refusing the whole decision over it would burn a retry on bookkeeping.
        """
        if not self.notebook:
            return None
        said = " ".join(str(text).split())[:MAX_NOTE_CHARS]
        if not said:
            return None
        line = f"[mission {self.mission_index + 1}] {said}"
        kept = self.notes.setdefault(seat, [])
        kept.append(line)
        del kept[:-MAX_NOTEBOOK_LINES]
        self._private_log(f'seat {seat} notes: "{said}"')
        return line

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
            "record": [text for kind, text in self.public_events if kind == "event"],
            "table_talk": [text for kind, text in self.public_events
                           if kind.startswith("speech")],
            "next_speaker": self.next_speaker(),
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

    def render_context(self, seat: int, include_speech: bool = True,
                       include_notes: bool | None = None) -> str:
        """The exact text a player agent would receive for this seat. Whatever is
        not here is invisible to that agent - so this string is what gate #1 audits.

        ``include_speech=False`` drops what other players *said*, leaving only what
        the referee itself put in front of this seat. That is the audit view: a
        player accusing another of a role is playing the game, while a referee doing
        it is the leak the gate exists to catch.

        ``include_notes`` follows ``include_speech`` unless set, and that default is
        the load-bearing part. A notebook line is player-authored text, the same
        class as speech, and it must leave the audit view for a sharper reason than
        speech does: ``find_leaks`` is naive substring matching by design, so a seat
        writing down a correct GUESS - "seat 3 is the seer" - would trip the audit
        as a leak the referee never committed. Defaulting the two flags together
        means the audit cannot be left holding a channel somebody forgot to pass.

        The gate itself is unweakened, because the notebook cannot carry anything
        into a payload that was not already in one: the only writer of seat N's
        notebook is seat N, working from bytes the referee had already given it, and
        the only reader is seat N.
        """
        if include_notes is None:
            include_notes = include_speech
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
        if p["proposal"] is not None:
            lines.append(f"Proposed team: {p['proposal']}.")
        # A seat's own words are marked "(you)". Without that marker a mid-size model
        # loses track of which voice in the transcript is its own and starts replying
        # to itself in the third person - observed on a live 12B, first run.
        record: list[tuple[bool, str]] = []          # (is a referee fact, rendered)
        for kind, text in self.public_events:
            if kind == "event":
                record.append((True, f"  {text}"))
            elif include_speech:
                mine = kind == f"speech:{seat}"
                record.append((False, f"  {'(you) ' if mine else ''}{text}"))
        if record:
            kept, dropped = self._trim(record)
            lines.append("Public record (everyone sees this):")
            if dropped:
                lines.append(f"  [{dropped} earlier line(s) trimmed - oldest table "
                             "talk goes first, mission results and votes last]")
            lines += kept
        # Last, so it sits closest to the ask: it is this seat's own carried read,
        # and the thing it was written to survive is the next decision.
        if include_notes and self.notebook and self.notes.get(seat):
            lines.append("Your private notebook (you wrote this; only you read it):")
            lines += [f"  {text}" for text in self.notes[seat]]
        return "\n".join(lines)

    def _trim(self, record: list[tuple[bool, str]]) -> tuple[list[str], int]:
        """Fit the record into the budget by dropping the OLDEST SPEECH, never a
        referee fact.

        The budget exists because the record is re-sent on every call and an
        unbounded one turns a long game into a quadratic context bill. Trimming
        oldest-first was wrong about WHAT to drop: speech outnumbers referee facts
        four to one at two discussion rounds, so a flat trim evicted missions 1 and
        2 - who was on the team that failed, and how each seat voted on it - while
        keeping eighty lines of table talk. Measured on the first live runs: 10 of
        16 games crossed the cap, so most games asked their seats to deduce from
        evidence the referee had already deleted.

        Facts are few (about 20 a game) and are the whole substrate of deduction;
        old chatter is what a human forgets first. The budget itself still holds -
        facts have priority within it, not exemption from it, so the record stays
        bounded for the longer games up the ladder and a line that scrolls off
        still leaves the model's payload.
        """
        if len(record) <= self.max_record_lines:
            return [text for _, text in record], 0
        budget = self.max_record_lines
        facts_at = [i for i, (is_fact, _) in enumerate(record) if is_fact]
        speech_at = [i for i, (is_fact, _) in enumerate(record) if not is_fact]
        keep = set(facts_at[-budget:] if budget else [])
        left = budget - len(keep)
        if left > 0:
            keep |= set(speech_at[-left:])
        kept = [text for i, (_, text) in enumerate(record) if i in keep]
        return kept, len(record) - len(kept)

    # ---- discussion -------------------------------------------------------

    def speaking_order(self) -> list[int]:
        """Who speaks, in order, for one discussion: round-robin from the leader,
        repeated ``discussion_rounds`` times."""
        one = [(self.leader + i) % self.n for i in range(self.n)]
        return one * self.discussion_rounds

    def next_speaker(self) -> int | None:
        if self.phase is not Phase.DISCUSS:
            return None
        order = self.speaking_order()
        return order[self.speech_ptr] if self.speech_ptr < len(order) else None

    def speak(self, seat: int, text: str) -> None:
        """Put one seat's chosen public utterance on the table.

        ``text`` is exactly what the player nominated as public - the caller must
        never pass a model's private reasoning here. The referee normalises and
        truncates it, appends it to the public record, and advances the round-robin;
        when every slot is used the discussion closes and the vote opens.
        """
        self._require(Phase.DISCUSS)
        expected = self.next_speaker()
        if seat != expected:
            raise IllegalAction(f"seat {expected} speaks now, not seat {seat}")
        said = " ".join(str(text).split())[:MAX_UTTERANCE_CHARS]
        if not said:
            raise IllegalAction("an utterance cannot be empty")
        entry = (f"speech:{seat}", f'seat {seat} says: "{said}"')
        if self.simultaneous:
            self._pending_speech.append(entry)
        else:
            self.public_events.append(entry)
        self._private_log(f'seat {seat} says: "{said}"')
        self.speech_ptr += 1
        if self.simultaneous and self.speech_ptr % self.n == 0:
            self._flush_round()
        if self.speech_ptr >= len(self.speaking_order()):
            self._flush_round()               # a partial round still reaches the table
            self.phase = Phase.VOTE

    def _flush_round(self) -> None:
        """Publish a simultaneous round's utterances together, in speaking order."""
        self.public_events.extend(self._pending_speech)
        self._pending_speech.clear()

    def _open_discussion(self) -> None:
        self.speech_ptr = 0
        self._pending_speech.clear()
        if self.discussion_rounds > 0:
            self.phase = Phase.DISCUSS
        else:
            self.phase = Phase.VOTE

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
        self._event(f"leader {leader} proposes {sorted(team)} for mission {self.mission_index + 1}")
        self._open_discussion()

    def vote(self, votes: dict[int, bool]) -> bool:
        """All seats vote approve(True)/reject(False). Returns whether it passed."""
        self._require(Phase.VOTE)
        if set(votes) != set(self.assignment):
            raise IllegalAction("every seat must vote exactly once")
        self.last_votes = dict(votes)
        approvals = sum(1 for v in votes.values() if v)
        passed = approvals * 2 > self.n
        ayes = sorted(s for s, v in votes.items() if v)
        self._event(
            f"vote on {sorted(self.proposal)}: {approvals}/{self.n} approve "
            f"(approved by {ayes}) -> {'APPROVED' if passed else 'REJECTED'}"
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

    def validate_card(self, seat: int, is_fail: bool) -> None:
        """Per-seat legality of one mission card, so a player policy can be told off
        for its own move rather than the whole team's. Same rule the bulk apply
        enforces; who played which card is never made public."""
        if self.proposal is None or seat not in self.proposal:
            raise IllegalAction(f"seat {seat} is not on the mission team")
        if is_fail and self.assignment[seat].team is Team.GOOD:
            raise IllegalAction(f"good seat {seat} cannot fail a mission")

    def mission(self, cards: dict[int, bool]) -> bool:
        """Team members play success(False)/fail(True). Good may not fail.
        Returns whether the mission succeeded."""
        self._require(Phase.MISSION)
        if set(cards) != set(self.proposal):
            raise IllegalAction("exactly the proposed team plays mission cards")
        for seat, is_fail in cards.items():
            self.validate_card(seat, is_fail)
        fails = sum(1 for f in cards.values() if f)
        need = self.setup.fails_required[self.mission_index]
        success = fails < need
        self.results.append(success)
        # the fail COUNT is public; which seat played which card never is
        self._event(
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
            self._event("three missions held; the endgame strike is called")
        else:
            self.phase = Phase.PROPOSE
        return success

    def validate_hunt(self, hunter: int, target: int) -> None:
        """Per-seat legality of one hunt, so the policy can be told off while it can
        still fix it - the same split as ``validate_card``.

        Naming a seat you KNOW is on your own side is not a bad read, it is an
        impossible one: the seer is good, so any seat you know to be evil cannot be
        it. Two seats are known that way, and the hunter is one of them.

        The night names the fellow evil, and 5 of 26 hunts in early runs struck one
        anyway - a fifth of all strikes spent on a provably wrong target.

        The hunter also knows its OWN role, more directly than it knows anything
        else, and that case was missed until the 20-game run of 2026-08-25 (seed
        1000) turned up a hunt naming its own seat, reasoning about itself in the
        third person. ``entitled_knowledge`` builds its reveals with ``s != seat``,
        so a seat is never in its own knowledge and this branch never fired. Hence
        ``| {hunter}`` rather than a second special case: the rule is one rule.

        Both halves also keep the SCORER honest, which is the real reason they are
        refusals and not advice. ``RandomPolicy`` excludes itself and its known
        ally, leaving 3 candidates - that is exactly where the 1-in-3 chance the
        gate is measured against comes from. Every target left legal here that the
        control will not pick scores the model against a baseline using knowledge
        the model was allowed to throw away.

        Refused, not silently corrected: the retry loop hands the seat this reason
        and it names someone else, which is the difference between a player learning
        the rule and the referee playing the move for it.
        """
        if self.assignment[hunter].key != "hunter":
            raise IllegalAction(f"seat {hunter} is not the hunter")
        if target not in self.assignment:
            raise IllegalAction(f"unknown target {target}")
        if target == hunter:
            raise IllegalAction(
                f"you are seat {hunter}, and you know your own role - the informant "
                "is one of the other seats at this table. Name one of them."
            )
        own = {k.seat for k in self.entitled_knowledge(hunter)
               if k.label == "fellow-evil"}
        if target in own:
            raise IllegalAction(
                f"seat {target} is one of your own - the night named them to you, "
                "so they cannot be the informant. Name a different seat."
            )

    def hunt(self, hunter: int, target: int) -> None:
        """Endgame after good reaches 3 successes: the hunter names a seat as the
        seer. Right = evil steals the win; wrong = good keeps it."""
        self._require(Phase.HUNT)
        self.validate_hunt(hunter, target)
        seer = self.seat_of("seer")
        if target == seer:
            self._win(Team.EVIL, f"hunter found the seer at seat {target}")
        else:
            self._win(Team.GOOD, f"hunter missed the seer (named seat {target})")

    def _win(self, team: Team, why: str) -> None:
        self.winner = team
        self.phase = Phase.DONE
        # the reason names roles ("hunter found the seer"), so it stays referee-side:
        # a public event is rendered into every seat's context and gate #1 audits it.
        self._private_log(f"WINNER: {self.theme.faction_names[team]} ({why})")

    # ---- what to ask the player for --------------------------------------

    def action_prompt(self, seat: int) -> str:
        """The ask appended to ``render_context`` for whichever seat acts next.

        Declares the JSON envelope. ``think`` is the sanctioned place for private
        reasoning and the driver discards it - only ``say`` is ever handed to
        ``speak()``. With the notebook on, ``note`` is the one field a seat writes
        for its own future self.
        """
        p = self.phase
        head = (
            'Reply with ONE JSON object and nothing else. A "think" field is '
            "private scratch space that is discarded and never shown to anyone - "
            "keep it under 30 words, because a reply long enough to be truncated "
            "is a reply the referee has to refuse."
        )
        scratch = '"think": "..."'
        if self.notebook:
            head += (
                ' You also keep a private notebook. Whatever you put in "note" is '
                "filed under your seat and shown back to you, and only you, on every "
                "later turn - the table never reads it. Write down the read you want "
                "to still have next round: who you doubt and what they did to earn "
                f"it, who you have decided to trust. Keep it under {MAX_NOTE_CHARS} "
                f"characters; the notebook shows your most recent "
                f"{MAX_NOTEBOOK_LINES} lines."
            )
            scratch += ', "note": "<what to carry forward>"'
        if p is Phase.PROPOSE:
            size = self.setup.team_sizes[self.mission_index]
            return (
                f"{head}\nYou are the leader. Pick the {size} seats to send on "
                f"mission {self.mission_index + 1} (you may include yourself).\n"
                f'Format: {{{scratch}, "team": [<{size} distinct seat numbers '
                f"0..{self.n - 1}>]}}"
            )
        if p is Phase.DISCUSS:
            return (
                f"{head}\nYou are seat {seat}; speak in the first person, and do not "
                "answer your own earlier lines - they are marked (you) in the record.\n"
                "Speak to the table before the vote: one or two short "
                f"sentences, at most {MAX_UTTERANCE_CHARS} characters. Everyone will "
                'read "say" and nothing else of yours. Argue, accuse, defend, or '
                "mislead as your role requires.\n"
                f'Format: {{{scratch}, "say": "<your public words>"}}'
            )
        if p is Phase.VOTE:
            return (
                f"{head}\nVote on the proposed team {list(self.proposal)}. A "
                "rejection passes the leadership on; five rejections in a row and "
                "the mission-runners lose outright."
                f"{self._night_against_the_table(seat)}\n"
                f'Format: {{{scratch}, "vote": "approve"|"reject"}}'
            )
        if p is Phase.MISSION:
            # Tailored by the seat's OWN role, which that seat already knows - a
            # human player would not need reminding what their win condition is.
            need = self.setup.fails_required[self.mission_index]
            size = len(self.proposal) if self.proposal else 0
            # How many fails sink a mission is PUBLIC rules information - a human
            # reads it off the board before choosing a card. It reached the seats
            # only in the post-resolution event, so a seat was asked to weigh a
            # fail against a threshold it had never been given. Restoring it is a
            # rules fix, not a hint; it says nothing about who else is on the team.
            rule = (f"This mission fails if {need} or more of the {size} cards "
                    f"played are fails, and succeeds otherwise.")
            if self.assignment[seat].team is Team.EVIL:
                stake = (
                    "Your side wins by making three missions fail, and nobody learns "
                    f"who played which card - only the count. {need} fail card(s) "
                    "sink this one. Weigh what a fail here buys your side against "
                    "the suspicion the count would put on this team."
                )
            else:
                stake = (
                    "Your side may only play success; playing fail would be refused "
                    "by the referee."
                )
            return (
                f"{head}\nYou are on the mission. Play a card in secret - only the "
                f"number of fails becomes public. {rule} {stake}\n"
                f'Format: {{{scratch}, "card": "success"|"fail"}}'
            )
        if p is Phase.HUNT:
            return (
                f"{head}\nThree missions held, so your side has one strike left: "
                "name the seat you believe holds the hidden informant. Right, and "
                "you take the game; wrong, and it is lost.\n"
                f'Format: {{{scratch}, "target": <seat 0..{self.n - 1}>}}'
            )
        raise IllegalAction(f"no action is open in phase {p.value}")

    def _night_against_the_table(self, seat: int) -> str:
        """Restate this seat's OWN night knowledge against the proposal in front of
        it. Adds nothing to what the seat already holds - every seat named here was
        named to this seat by ``entitled_knowledge``, and the same names are already
        in its rendered context - so it is gate #1-neutral by construction.

        It is here because the knowledge being present is not the same as the
        knowledge being used. Measured on the local 12B, n=30 per cell, seer votes
        in isolation: with the context as-is the seer approved a team carrying a
        seat it had been told serves darkness 83% of the time (vs 90% for a clean
        team - discrimination +7%, i.e. nothing). With this line, 37% vs 100%,
        discrimination +63%. The model could always use the fact; nothing asked it
        to line the fact up against the table.
        """
        if self.proposal is None:
            return ""
        known = sorted(k.seat for k in self.entitled_knowledge(seat)
                       if k.label == "evil")
        if not known:
            return ""
        on_team = [s for s in sorted(self.proposal) if s in known]
        tail = (f"contains {on_team}" if on_team else "contains none of them")
        return (f"\nWhat the night told you: seat(s) {known} serve darkness. "
                f"The proposed team {sorted(self.proposal)} {tail}.")

    def prompt_for(self, seat: int, include_speech: bool = True) -> str:
        """The complete outgoing payload for one seat: its view plus its ask. This
        is the string a player policy sends, so this is the string gate #1 audits."""
        return f"{self.render_context(seat, include_speech)}\n\n{self.action_prompt(seat)}"

    def acting_seats(self) -> list[int]:
        """Which seats owe the referee a move right now."""
        p = self.phase
        if p is Phase.PROPOSE:
            return [self.leader]
        if p is Phase.DISCUSS:
            nxt = self.next_speaker()
            return [nxt] if nxt is not None else []
        if p is Phase.VOTE:
            return sorted(self.assignment)
        if p is Phase.MISSION:
            return sorted(self.proposal)
        if p is Phase.HUNT:
            return [self.seat_of("hunter")]
        return []
