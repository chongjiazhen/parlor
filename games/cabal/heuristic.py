"""The missing rung: a hand-written non-LLM policy that actually tries to win.

The control ladder was `random -> LLM` with nothing between, so the strongest thing
a gate could say was "better than noise". This is the rung in the middle, and it is
cribbed straight from AvalonBench, whose rule-based bots BEAT its LLM agents (38.2%
against 22.2% for the good side). A model losing to sixty lines of if-statements is
a far more legible finding than a model beating a coin, and it replicates a
published result rather than inventing a metric.

Deliberately NOT the mechanical solver, and the difference is the point of having
both rungs. The solver enumerates 120 assignments and refuses votes and speech
because reading them needs a model of how seats play. This one is the opposite
trade: no enumeration at all, just tallies over the public record, and it reads
votes precisely because that is where a cheap policy can get leverage. They are
different instruments, and `games/cabal/solver.py` proves the ladder needs the
second one - the hunt is mechanically flat, so a solver that refuses behaviour
cannot hunt above chance and a rule that reads votes might.

Gate #1 by construction. Every branch below consumes exactly two things: the seat's
own role, and `ref.entitled_knowledge(seat)` / `ref.public_events`. It never touches
`ref.assignment` for another seat, so it cannot use what the referee did not render
to it - the same standing `RandomPolicy` has, and for the same reason.

Two rules here are choices rather than deductions, and both are stated so a later
reader grades them rather than inherits them:

  - **An evil seat always plays fail.** It is the simplest sabotage rule and it
    over-sabotages by construction. The audit measured live models doing the same
    on 39-45% of payable sinkings, so a bot that always does it is a fair upper
    bound on that behaviour, not a strawman.
  - **The fifth proposal is approved unconditionally.** A rules bot that rejects on
    suspicion alone hands evil the game at `five_rejects`, which is a bug in the
    bot rather than a finding about the game.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field

from games.cabal.referee import CabalReferee, IllegalAction, Phase
from games.cabal.roles import Team
from games.cabal.solver import parse_missions, parse_votes


@dataclass
class HeuristicPolicy:
    """Sixty lines of if-statements, and the second rung of the control ladder."""

    #: Tie-breaks only. A deterministic tie-break by seat order would bias every
    #: statistic towards low seat numbers over a corpus, which reads as a finding
    #: about seat 0.
    rng: random.Random = field(default_factory=random.Random)

    def act(self, ref: CabalReferee, seat: int) -> dict:
        p = ref.phase
        if p is Phase.PROPOSE:
            return {"team": self._propose(ref, seat)}
        if p is Phase.DISCUSS:
            return {"say": self._say(ref, seat)}
        if p is Phase.VOTE:
            return {"vote": self._vote(ref, seat)}
        if p is Phase.MISSION:
            # good may not fail; evil always does - see the module docstring
            return {"card": ref.assignment[seat].team is Team.EVIL}
        if p is Phase.HUNT:
            return {"target": self._hunt(ref, seat)}
        raise IllegalAction(f"no action in phase {p.value}")

    # ---- what the seat is entitled to -------------------------------------

    def _known_evil(self, ref: CabalReferee, seat: int) -> set[int]:
        """Seats the NIGHT named as evil to this one. Empty for a blind seat, which
        is most of them - the tallies below are what such a seat has instead."""
        return {k.seat for k in ref.entitled_knowledge(seat)
                if k.label in ("evil", "fellow-evil")}

    def _suspicion(self, ref: CabalReferee) -> Counter:
        """Fails charged to every seat that was aboard the mission that returned
        them. Crude on purpose: it is a tally any player can keep in their head off
        the public record, which is the register this rung is written in."""
        out: Counter = Counter()
        for team, fails in parse_missions(ref.public_events):
            for member in team:
                out[member] += fails
        return out

    # ---- the four decisions ------------------------------------------------

    def _propose(self, ref: CabalReferee, seat: int) -> list[int]:
        size = ref.setup.team_sizes[ref.mission_index]
        known_evil = self._known_evil(ref, seat)
        suspicion = self._suspicion(ref)
        others = [s for s in sorted(ref.assignment) if s != seat]

        if ref.assignment[seat].team is Team.EVIL:
            # get a saboteur aboard: self, then an ally if there is room, then the
            # seats the table has least reason to doubt, so the team still passes
            ally = sorted(known_evil)
            picks = [seat] + ally[:max(0, size - 1)]
            rest = [s for s in others if s not in picks]
        else:
            picks = [seat]
            rest = [s for s in others if s not in known_evil]
        self.rng.shuffle(rest)
        rest.sort(key=lambda s: suspicion[s])
        picks += rest[:size - len(picks)]
        # a shortfall can only happen if the filters left too few seats; fill from
        # everyone rather than propose an illegal team the referee would refuse
        if len(picks) < size:
            spare = [s for s in sorted(ref.assignment) if s not in picks]
            self.rng.shuffle(spare)
            picks += spare[:size - len(picks)]
        return sorted(picks[:size])

    def _say(self, ref: CabalReferee, seat: int) -> str:
        """Public facts only. This rung has no theory of persuasion, and a bot that
        voiced its night knowledge would be handing the table gate #1 for free -
        legally, since speech is gameplay, but it would stop being a control."""
        suspicion = self._suspicion(ref)
        worst = [s for s, n in suspicion.items() if n and s != seat]
        if worst:
            top = max(worst, key=lambda s: suspicion[s])
            return f"Seat {top} has been aboard {suspicion[top]} failed mission(s)."
        return "Nothing has failed yet, so I have nothing to go on."

    def _vote(self, ref: CabalReferee, seat: int) -> bool:
        team = set(ref.proposal or ())
        known_evil = self._known_evil(ref, seat)
        # the fifth rejection loses the game outright, so it is never the right
        # move on suspicion alone
        if ref.reject_count >= 4:
            return True
        if ref.assignment[seat].team is Team.EVIL:
            # approve exactly the teams a saboteur can act on
            return bool(team & (known_evil | {seat}))
        if team & known_evil:
            return False
        # Reject only the seats the record points at HARDEST, not everyone it has
        # charged with anything. "Approve nothing with a fail against it" reads like
        # the strict rule and is a self-inflicted loss: once two missions have gone
        # down, most seats carry a fail, the bot rejects every proposal, and it
        # hands the game away at `five_rejects`. Measured at 0.5% good wins before
        # this line, against 41% for the random control.
        suspicion = self._suspicion(ref)
        worst = max(suspicion.values(), default=0)
        return not (worst and any(suspicion[s] >= worst for s in team))

    def _hunt(self, ref: CabalReferee, seat: int) -> int:
        arg = hunt_by_votes(ref.legal_hunt_targets(seat),
                            self._known_evil(ref, seat) | {seat},
                            parse_votes(ref.public_events))
        return self.rng.choice(arg)


# ---- the hunt rules, as functions ------------------------------------------
#
# Lifted out of the policy because they are also run OFFLINE, over records the
# policy never played: `eval/ladder.py` scores them against the LLM corpus, which
# is the only way to ask "how much behavioural signal is in what the models
# actually did". One implementation, two callers, tested once.
#
# Both return the ARGMAX SET rather than a pick. The tie-break belongs to the
# caller: seated, it is `rng.choice`; offline it is tie-averaged, so a corpus number
# carries no tie-break luck.


def hunt_by_votes(legal: list[int], known_evil: set[int],
                  votes: tuple[tuple[tuple[int, ...], frozenset[int]], ...]) -> list[int]:
    """Name the legal target that voted least like a saboteur.

    The one rule here that is a real read rather than bookkeeping, and the solver is
    why it has to be: `test_solver.py` proves by exhaustion that the hunter derives
    NOTHING mechanically in this setup, so anything above chance must come from
    behaviour. This is the cheapest behavioural rule there is.

    The hunter knows both evil seats, so it knows which teams were tainted. A good
    seat that saw through the game rejected those and approved the clean ones; a seat
    voting blind did neither. Score each legal target on that agreement and take the
    best - the seer is the good seat most likely to have managed it.
    """
    score: Counter = Counter({t: 0 for t in legal})
    for team, approvers in votes:
        tainted = bool(set(team) & known_evil)
        for target in legal:
            score[target] += 1 if ((target in approvers) != tainted) else -1
    best = max(score.values())
    return [t for t in legal if score[t] == best]


def hunt_by_rejections(legal: list[int], known_evil: set[int],
                       votes: tuple[tuple[tuple[int, ...], frozenset[int]], ...]) -> list[int]:
    """Name the legal target that rejected most, and look at nothing else.

    A deliberately DUMBER rung than `hunt_by_votes`, and it exists as that rule's
    control: it ignores the hunter's night knowledge entirely, so whatever it scores
    is the tell that survives with no private information at all. If the two land
    together, the taint-conditioning in the smarter rule is decoration, and the
    finding is only that a cautious seat is conspicuous.

    `known_evil` is accepted and unused so the two rules share one signature and a
    caller cannot silently pass the wrong one.
    """
    score: Counter = Counter({t: 0 for t in legal})
    for _, approvers in votes:
        for target in legal:
            score[target] += 0 if target in approvers else 1
    best = max(score.values())
    return [t for t in legal if score[t] == best]
