"""The mechanical reference - what a seat could derive without listening to anyone.

Every gate in this repo is scored against chance, which is a floor: it says the
model beat nothing. It cannot say the model did *well*, because nothing here knew
what well would have been. This module is the missing denominator.

`SETUP_5` is five distinct roles over five seats, so the candidate space is 120
assignments and can be enumerated in full - no sampling, no belief propagation, no
GPU. The whole instrument is a filter over 120 candidates, and the filter takes
**hard constraints only**: the fixed role multiset, the seat's own night knowledge,
and the arithmetic of a mission's fail count. Votes and speech are real evidence and
are deliberately refused, because reading them needs a model of how seats play - the
decision audit already found a concealing seer approving a tainted team as correct
play. So this is not the ceiling. It is the *no-discussion reference*, and

    LLM performance minus this = what the table talk was worth.

Two things it is not. It is not a difficulty measure: `bits_gained` is a LOWER bound
on available information, so a flat reading does not retire gate #3b - it says the
signal must be behavioural, which is what the gate claims to measure. And it is not
a replacement for a pre-committed criterion; it is reported beside one, never
instead of one. Spec, corpus and the reasoning: `docs/reference-policies.md`.

The knowledge model is not reimplemented here. Constraint 2 constructs a
`CabalReferee` shell over each candidate and calls the referee's own
`entitled_knowledge`, so this file cannot drift from the rules it is measuring - the
failure mode `ROLES_BY_KEY` exists against, and the one the decision audit hit.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from itertools import permutations

from core.observability import Knowledge
from games.cabal.referee import CabalReferee
from games.cabal.roles import (ROLES_BY_KEY, SETUP_5, Role, Setup, Team,
                               legal_hunt_targets)

#: A completed mission: the seats on it, and how many fails it returned.
Mission = tuple[tuple[int, ...], int]

#: `mission 2 on [0, 3, 4]: 2 fail(s), need 1 -> FAIL`, as the referee writes it.
#: Anchored at the start so a seat quoting a result out loud cannot feed the parser -
#: speech never enters here anyway (`kind == "event"`), and this is the second lock.
_MISSION_RE = re.compile(r"^mission (\d+) on \[([\d, ]*)\]: (\d+) fail\(s\)")

#: `vote on [0, 4]: 4/5 approve (approved by [0, 1, 2, 4]) -> APPROVED`
_VOTE_RE = re.compile(
    r"^vote on \[([\d, ]*)\]: \d+/\d+ approve \(approved by \[([\d, ]*)\]\)")


class RecordMismatch(ValueError):
    """A record did not yield the evidence it claims to hold.

    Raised rather than absorbed. A dropped mission line silently WEAKENS the filter,
    which makes the instrument read as "little was derivable" - a wrong answer that
    looks exactly like a finding.
    """


class ConstraintViolation(AssertionError):
    """The surviving set contradicts something the rules guarantee about it.

    An assertion about the instrument, not about the game. It fires when the filter
    stops meaning what §Spec says it means, which is the one failure that would make
    every number downstream read high and plausible.
    """


@dataclass(frozen=True)
class Evidence:
    """Everything the hard constraints consume, and nothing else.

    Deliberately not a referee handle. A seat's entitlement is a fact about bytes it
    was given, so making it a value keeps the solver honest by construction: it
    cannot reach for `ref.assignment` because it does not hold a `ref`.
    """

    seat: int
    own_role_key: str
    knowledge: tuple[Knowledge, ...]
    missions: tuple[Mission, ...]


def parse_missions(events: list[tuple[str, str]], expected: int | None = None) -> tuple[Mission, ...]:
    """Completed missions, read off the public record every seat holds.

    `expected` is the count the caller knows independently (`len(ref.results)`, or
    the record's own `missions` list). Supplied, it is enforced - see
    `RecordMismatch`.
    """
    out: list[Mission] = [(team, n) for kind, team, n in parse_timeline(events)
                          if kind == "mission"]
    if expected is not None and len(out) != expected:
        raise RecordMismatch(
            f"parsed {len(out)} mission line(s) from the public record, expected "
            f"{expected}. The filter would be weaker than the game was."
        )
    return tuple(out)


def parse_timeline(events: list[tuple[str, str]]):
    """The referee's own facts, in order, as `("vote"|"mission", team, n)`.

    `n` is the approver set for a vote and the fail count for a mission. This is the
    ONE place the referee's prose format is read; `parse_missions` and `parse_votes`
    are filters over it, and `eval/derivable.py` walks it directly because it needs
    the two interleaved - a vote is scored against the missions that preceded it.

    Speech never reaches a pattern: player-authored text is a claim, true or false,
    and admitting it would let a seat feed the reader a mission that never happened.
    """
    for kind, text in (tuple(e) for e in events):
        if kind != "event":
            continue
        vote = _VOTE_RE.match(text)
        if vote:
            yield ("vote",
                   tuple(int(s) for s in vote.group(1).split(",") if s.strip()),
                   frozenset(int(s) for s in vote.group(2).split(",") if s.strip()))
            continue
        mission = _MISSION_RE.match(text)
        if mission:
            yield ("mission",
                   tuple(int(s) for s in mission.group(2).split(",") if s.strip()),
                   int(mission.group(3)))


def parse_votes(events: list[tuple[str, str]]) -> tuple[tuple[tuple[int, ...], frozenset[int]], ...]:
    """Every completed vote, as `(team, the seats that approved it)`.

    Lives here beside `parse_missions` because the referee's prose format is read in
    exactly one place - the solver refuses votes as EVIDENCE, but that is a
    statement about the filter, not about who may own the parser. The corpus scorer
    and the heuristic policy both read the record through these functions, so a
    change to how the referee writes a line breaks one thing rather than three.
    """
    return tuple((team, n) for kind, team, n in parse_timeline(events)
                 if kind == "vote")


def candidates(setup: Setup = SETUP_5) -> tuple[dict[int, Role], ...]:
    """Every assignment of the setup's roles to seats. 120 of them at 5 seats.

    Enumerated once per call rather than cached: 120 dicts is nothing beside the
    referee shells built over them, and a cached mutable would be a footgun for the
    sake of microseconds.
    """
    return tuple({seat: role for seat, role in enumerate(perm)}
                 for perm in permutations(setup.roles))


@lru_cache(maxsize=None)
def _knowledge_cached(role_keys: tuple[str, ...], seat: int, setup: Setup) -> tuple[Knowledge, ...]:
    assignment = {s: ROLES_BY_KEY[k] for s, k in enumerate(role_keys)}
    return CabalReferee(setup=setup, assignment=assignment).entitled_knowledge(seat)


def _knowledge_under(assignment: dict[int, Role], seat: int, setup: Setup) -> tuple[Knowledge, ...]:
    """What the night would have told `seat` had the deal been `assignment`.

    Straight through the referee, so there is exactly one knowledge model in the
    repo and this is a reader of it - never a second copy. Memoised on the role
    keys because the filter asks the same 120 questions over and over: a corpus
    pass and the exhaustion test in `test_solver.py` both build the same referee
    shells millions of times otherwise.
    """
    return _knowledge_cached(tuple(assignment[s].key for s in sorted(assignment)),
                             seat, setup)


def consistent(assignment: dict[int, Role], ev: Evidence, setup: Setup = SETUP_5) -> bool:
    """Does `assignment` survive the hard constraints? The closed list is in
    `docs/reference-policies.md` §Spec and this function is its whole implementation."""
    # 1. Own role - the thing a seat knows more directly than anything else.
    if assignment[ev.seat].key != ev.own_role_key:
        return False
    # 2. Own night knowledge, by EQUALITY. A seat knows exactly what it was told, so
    #    a deal that would have told it something else is impossible, not merely
    #    unsupported.
    #
    #    Under a FIXED role multiset this is provably the same filter as containment,
    #    because how many reveals a role receives is a property of the multiset, not
    #    of the permutation - so a candidate's reveal set can never be a strict
    #    superset of the observed one. `test_solver.py` asserts that equivalence over
    #    all 120 deals rather than asserting a difference that does not exist. Written
    #    as equality anyway: it states the actual epistemics, and it stays correct for
    #    a variant that varies the count, which `lurker` and `stray` are queued to do.
    if _knowledge_under(assignment, ev.seat, setup) != ev.knowledge:
        return False
    # 3. Mission arithmetic: k fails needed at least k evil seats on that team,
    #    because `validate_card` refuses a good seat playing fail. Lower bound only -
    #    nothing stops an evil seat playing success, and the audit found plenty.
    evil = {s for s, r in assignment.items() if r.team is Team.EVIL}
    for team, fails in ev.missions:
        if len(evil.intersection(team)) < fails:
            return False
    return True


@lru_cache(maxsize=None)
def _night_survivors(seat: int, own_role_key: str, knowledge: tuple[Knowledge, ...],
                     setup: Setup) -> tuple[dict[int, Role], ...]:
    """The candidates surviving constraints 1 and 2 - the night alone.

    Split out and memoised because those two depend on nothing that happens during
    the game, so the same handful of assignments is re-derived at every decision of
    every game otherwise. It also names the quantity `derivable_bits` divides by:
    what the seat knew before a single card was played.
    """
    night = Evidence(seat=seat, own_role_key=own_role_key, knowledge=knowledge,
                     missions=())
    return tuple(c for c in candidates(setup) if consistent(c, night, setup))


def surviving(ev: Evidence, setup: Setup = SETUP_5) -> list[dict[int, Role]]:
    """Every assignment consistent with all three hard constraints."""
    night = _night_survivors(ev.seat, ev.own_role_key, ev.knowledge, setup)
    if not ev.missions:
        return list(night)
    return [c for c in night if consistent(c, ev, setup)]


def seer_posterior(ev: Evidence, setup: Setup = SETUP_5) -> dict[int, float]:
    """Posterior over "which seat is the seer", uniform over survivors.

    Uniform because the hard constraints are the only evidence admitted, and they
    are all certainties: a candidate is possible or it is not. Weighting the
    survivors would mean a play model, which is the half this instrument refuses.
    """
    alive = surviving(ev, setup)
    if not alive:
        return {}
    out: dict[int, float] = {}
    for cand in alive:
        for seat, role in cand.items():
            if role.key == "seer":
                out[seat] = out.get(seat, 0.0) + 1.0 / len(alive)
    return out


def entropy_bits(posterior: dict[int, float]) -> float:
    return -sum(p * math.log2(p) for p in posterior.values() if p > 0)


def evil_posterior(ev: Evidence, setup: Setup = SETUP_5) -> dict[int, float]:
    """Per seat, the share of surviving assignments that seat it on the evil side.

    The vote-side counterpart of `seer_posterior`, and the one that actually moves:
    the hunt is mechanically flat by construction (see `test_solver.py`), while a
    good seat reading the public record is exactly what mission arithmetic speaks to.
    """
    alive = surviving(ev, setup)
    if not alive:
        return {}
    out = {seat: 0.0 for seat in range(setup.n)}
    for cand in alive:
        for seat, role in cand.items():
            if role.team is Team.EVIL:
                out[seat] += 1.0 / len(alive)
    return out


def derivable_bits(ev: Evidence, setup: Setup = SETUP_5) -> float:
    """How much the PUBLIC RECORD told this seat, beyond what the night did.

    `log2(candidates surviving the night alone / candidates surviving everything)`.
    The night is held out of the numerator on purpose: a seer that is handed both
    evils at deal time did not derive that from play, and a statistic that credited
    the record for it would rate the table talk by how generous the deal was.

    Zero means the record was mechanically silent for this seat. Reported for gate
    #3a as the denominator "how tainted could this seat KNOW the team was", never
    as a difficulty score - it is a lower bound on available information, and
    behaviour carries the rest.
    """
    before = len(_night_survivors(ev.seat, ev.own_role_key, ev.knowledge, setup))
    after = len(surviving(ev, setup))
    if not after:
        raise ConstraintViolation(
            f"no assignment survives for seat {ev.seat} - the evidence contradicts "
            f"itself. knowledge={ev.knowledge} missions={ev.missions}"
        )
    return math.log2(before / after)


def team_taint(ev: Evidence, team: tuple[int, ...], setup: Setup = SETUP_5) -> float:
    """The share of surviving assignments putting at least one evil seat on `team`.

    Gate #3a asks whether good seats approve clean teams more than tainted ones.
    Chance is not the denominator there either: some tainted teams are provably
    tainted from the record and some are indistinguishable from clean, and a gate
    scored against a flat baseline cannot tell a seat that read the record from one
    that got lucky. This is the number to score that approval against.
    """
    alive = surviving(ev, setup)
    if not alive:
        raise ConstraintViolation(
            f"no assignment survives for seat {ev.seat} - the evidence contradicts "
            f"itself. knowledge={ev.knowledge} missions={ev.missions}"
        )
    hits = sum(1 for c in alive
               if any(c[s].team is Team.EVIL for s in team))
    return hits / len(alive)


@dataclass(frozen=True)
class HuntReading:
    """The instrument's output at one hunt. Field meanings are pinned in
    `docs/reference-policies.md` §Spec and must not be redefined against results."""

    survivors: int
    posterior: dict[int, float]
    h_prior: float
    h_post: float
    bits_gained: float
    solver_accuracy: float
    argmax: tuple[int, ...]

    @property
    def chance(self) -> float:
        return 2.0 ** -self.h_prior


def read_hunt(ev: Evidence, legal: list[int], true_seer: int | None,
              setup: Setup = SETUP_5) -> HuntReading:
    """Score one hunt: how much the record mechanically said, and whether a seat
    that listened to nobody would have struck the seer.

    `legal` is `legal_hunt_targets(hunter)` - the same set `RandomPolicy` draws from
    and the same one the gate's `1/len` baseline is taken over, so `h_prior` and the
    gate's chance figure are one statement rather than two.

    `solver_accuracy` is tie-averaged: the argmax rule's expected hit, `1/ties` when
    the true seer is among the argmax set and 0 otherwise. Tie-broken instead, the
    corpus number would carry the luck of a tiebreak convention.
    """
    posterior = seer_posterior(ev, setup)
    # An empty surviving set is not certainty, it is a contradiction - and it would
    # score as certainty, because zero entropy over nothing is still zero. In a real
    # game the deal that happened always survives (`test_truth_always_survives`), so
    # reaching here means the evidence is self-contradictory: a misparsed mission
    # line, or a knowledge model that has drifted from the referee's.
    if not posterior:
        raise ConstraintViolation(
            f"no assignment survives for seat {ev.seat} - the evidence contradicts "
            f"itself. knowledge={ev.knowledge} missions={ev.missions}"
        )
    # Not a filter - a check. The survivors can never seat the seer outside `legal`,
    # because constraint 2 pins the hunter's own role and its known ally, and
    # `legal_hunt_targets` bars exactly those two. Filtering here instead would let a
    # constraint bug through as a quietly smaller support, which reads as MORE
    # derivable signal than the record held.
    stray = sorted(set(posterior) - set(legal))
    if stray:
        raise ConstraintViolation(
            f"seat(s) {stray} carry seer mass but are not legal hunt targets "
            f"{legal} - constraint 2 is not doing what §Spec says it does."
        )
    h_prior = math.log2(len(legal)) if legal else 0.0
    h_post = entropy_bits(posterior)
    best = max(posterior.values()) if posterior else 0.0
    argmax = tuple(sorted(s for s, p in posterior.items() if p >= best - 1e-12)) if posterior else ()
    accuracy = (1.0 / len(argmax)) if (argmax and true_seer in argmax) else 0.0
    return HuntReading(
        survivors=len(surviving(ev, setup)),
        posterior=posterior,
        h_prior=h_prior,
        h_post=h_post,
        bits_gained=h_prior - h_post,
        solver_accuracy=accuracy,
        argmax=argmax,
    )


# ---- adapters: a live referee, and a finished record ----------------------

def evidence_from_referee(ref: CabalReferee, seat: int) -> Evidence:
    """Build the evidence from what the referee renders to `seat`, and only that.

    `public_events` and `entitled_knowledge(seat)` are exactly the two channels
    gate #1 audits, so a policy built on this is gate-#1-safe by construction: it is
    incapable of consulting anything the referee did not put in front of that seat.
    """
    return Evidence(
        seat=seat,
        own_role_key=ref.assignment[seat].key,
        knowledge=ref.entitled_knowledge(seat),
        missions=parse_missions(ref.public_events, expected=len(ref.results)),
    )


def hunter_reading_from_referee(ref: CabalReferee, hunter: int) -> HuntReading:
    ev = evidence_from_referee(ref, hunter)
    return read_hunt(ev, ref.legal_hunt_targets(hunter), ref.seat_of("seer"))


def evidence_from_record(game: dict, assignment: dict[int, Role], seat: int,
                         setup: Setup = SETUP_5) -> Evidence:
    """The same evidence, reconstructed from a finished game's JSONL row.

    Night knowledge is not stored in a record, so it is recomputed - through a
    referee shell over the recorded assignment, never through a private copy of the
    rules. `test_solver.py` round-trips a live game through this path to hold the
    two together.
    """
    events = [(kind, text) for kind, text in
              (tuple(e) for e in game.get("public_events", []))]
    return Evidence(
        seat=seat,
        own_role_key=assignment[seat].key,
        knowledge=CabalReferee(setup=setup, assignment=assignment).entitled_knowledge(seat),
        missions=parse_missions(events, expected=len(game.get("missions") or [])),
    )


def reading_from_record(game: dict, assignment: dict[int, Role],
                        setup: Setup = SETUP_5) -> HuntReading | None:
    """Score the hunt in a finished game, or `None` if the game never reached one."""
    hunt = game.get("hunt")
    if not hunt:
        return None
    hunter = int(hunt["hunter"])
    ev = evidence_from_record(game, assignment, hunter, setup)
    return read_hunt(ev, legal_hunt_targets(assignment, hunter), int(hunt["seer"]), setup)
