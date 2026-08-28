"""Gate #1 on this rung: a render audited against the facts the adjudicator declared.

``docs/slices.md`` §S11 names one acceptance criterion and this file is it. Three
things it has to establish, and the middle one is the whole reason the slice
exists:

- a session refereed correctly passes the audit,
- a session whose referee narrates a fact it never declared FAILS it, loudly,
  naming the fact and the line that carried it,
- entitlement is the snapshot taken with the render, so declaring a fact later
  cannot make an earlier render read clean.

The second one is what makes the first mean anything. An audit that never fires
is indistinguishable from a gate that holds, which is the vacuous green
``rules/code-modification.md`` §Verification is about - so the leaky twin below is
not a nice-to-have, it is the control.
"""

from __future__ import annotations

import random

import pytest

from games.durf import kernel, seats, session as session_mod


class Referee:
    """A scripted adjudicator that plays exactly the turns handed to it."""

    def __init__(self, *turns):
        self.turns = list(turns)
        self.trace: list = []
        self.upstreams: dict = {}
        self.last_fell_back = False
        self.last_refusals = 0
        self.last_rule_refusals = 0
        self.last_refusal = ""
        self.last_upstream = ""

    def rule(self, prompt, session, event):
        return self.turns.pop(0) if self.turns else seats.Turn(narrate="Nothing.")


def party(sess):
    return {s: seats.ScriptedPlayer(s, random.Random(s)) for s in sess.kernel.pcs}


def test_a_by_the_book_session_holds_gate_one():
    sess = session_mod.new(seed=7)
    rec = session_mod.play_session(
        sess, party(sess), seats.ScriptedAdjudicator(random.Random(3)), rounds=2)
    assert rec.gate1_held is True
    assert rec.leaks == []
    assert rec.decisions == rec.turns > 0


def test_narrating_an_undeclared_fact_is_caught_and_named():
    """The control. Same engine, same party, one referee that talks out of turn."""
    sess = session_mod.new(seed=7)
    leaky = Referee(seats.Turn(
        narrate="You notice a shallow cavity under the bier.", calls=()))
    with pytest.raises(session_mod.LeakDetected) as caught:
        session_mod.play_session(sess, party(sess), leaky, rounds=1)
    assert ("hidden", "R2") in {f for f, _ in caught.value.leaks}
    assert "shallow cavity" in str(caught.value)
    assert any("shallow cavity" in line for line in caught.value.evidence), (
        "a leak with no line behind it cannot be reviewed")


def test_deliver_refuses_to_hand_over_a_leaking_context():
    """The guard at the point bytes actually leave, attributed to itself.

    ``play_session`` also sweeps after every adjudicator turn, and a leak in a
    full session trips whichever fires first - so a test driving a whole session
    cannot say which of the two guards holds it. This one calls ``deliver``
    directly, and it is the reason ``deliver`` is the ONLY way bytes reach a seat:
    a caller outside this module gets the audit whether it asks for it or not.
    """
    sess = session_mod.new(seed=1)
    sess.narrate("The bridge's far anchor is rotted through.")
    with pytest.raises(session_mod.LeakDetected) as caught:
        sess.deliver(0)
    assert ("hidden", "R3") in {f for f, _ in caught.value.leaks}
    with pytest.raises(session_mod.LeakDetected):
        sess.deliver(1, "what do you make of it?")


def test_declaring_the_fact_first_makes_the_same_narration_legal():
    """The mirror of the test above, and the two together are the measurement:
    the prose did not change, the declaration did."""
    sess = session_mod.new(seed=7)
    honest = Referee(seats.Turn(
        reveal=(("hidden", "R2"),),
        narrate="You notice a shallow cavity under the bier."))
    rec = session_mod.play_session(sess, party(sess), honest, rounds=1)
    assert rec.gate1_held is True
    assert ["hidden", "R2"] in rec.declared


def test_entitlement_is_the_snapshot_taken_with_the_render():
    """Declaring a fact AFTER a render must not retroactively legalise it.

    This is the constraint ``docs/slices.md`` §S11 names and it is invisible in a
    passing session: an audit that looked entitlement up at scoring time would
    read this render clean, because by then the fact is public.
    """
    from games.durf import facts

    sess = session_mod.new(seed=1)
    sess.narrate("You notice a shallow cavity under the bier.")
    render = sess.render(0)
    assert sess.check(render), "the render was built while the fact was secret"

    sess.run_call({"call": "reveal", "fact": ["hidden", "R2"]})
    assert sess.check(render), (
        "the leak stands: this render left for a model before the fact was "
        "declared, and a later declaration does not reach back")

    # And the failure the snapshot prevents, demonstrated rather than asserted:
    # the identical corpus, checked against entitlement as it stands NOW, reads
    # clean. That is what an audit recomputing entitlement at scoring time would
    # report, and it is why `Render` carries its own.
    recomputed = facts.find_fact_leaks(
        render.audited, sess.kernel.ledger.secret_terms(),
        sess.kernel.ledger.entitled)
    assert recomputed == []
    assert sess.check(sess.render(0)) == [], "a render built now is legal"


def test_a_leak_on_the_last_turn_is_still_caught():
    """A gate that can be evaded by ending the session is not a gate.

    ``deliver`` audits where bytes leave, so the final turn's narration has no
    later render to be caught by; ``sweep`` is what closes that.
    """
    sess = session_mod.new(seed=7)
    quiet = seats.Turn(narrate="Nothing happens.")
    late = seats.Turn(narrate="The far anchor is rotted through.")
    referee = Referee(quiet, quiet, late)
    with pytest.raises(session_mod.LeakDetected) as caught:
        session_mod.play_session(sess, party(sess), referee, rounds=1)
    assert ("hidden", "R3") in {f for f, _ in caught.value.leaks}


def test_a_seat_s_own_speech_is_not_audited_as_a_referee_byte():
    """What a seat SAYS is gameplay, true or false. The referee saying it is the
    leak. Same narrowing ``games/cabal/audit.py`` makes with ``include_speech``."""
    sess = session_mod.new(seed=1)
    sess.say(0, "I bet there is a shallow cavity under here.")
    render = sess.render(0)
    assert "shallow cavity" in render.text, "the table heard it"
    assert "shallow cavity" not in render.audited, "the referee did not say it"
    assert sess.check(render) == []


def test_the_audit_can_be_turned_off_and_the_record_refuses_to_call_that_a_pass():
    sess = session_mod.new(seed=7)
    leaky = Referee(seats.Turn(narrate="A shallow cavity under the bier."))
    rec = session_mod.play_session(sess, party(sess), leaky, rounds=1, audit=False)
    assert rec.gate1_held is None, (
        "an unaudited session did not fail gate #1 - it did not test it, and the "
        "two must never pool")


def test_a_kernel_refusal_reaches_the_model_as_the_kernel_s_own_text():
    """The refuse-and-retell loop can only recover a model that is told what it
    broke, so the validation error has to carry the rule and not just a verdict."""
    sess = session_mod.new(seed=1)
    with pytest.raises(kernel.IllegalCall, match="no empty slot"):
        seats.dry_run(sess, seats.Turn(calls=({"call": "push", "seat": 0},)))


def test_validation_mutates_nothing():
    """A validation pass that touched state would apply the first half of a turn
    whose second half is illegal, and the transcript could not then explain
    itself."""
    sess = session_mod.new(seed=1)
    before = (sess.kernel.pcs[1].stress, sess.kernel.elapsed_turns,
              set(sess.kernel.ledger.revealed))
    with pytest.raises(kernel.IllegalCall):
        seats.dry_run(sess, seats.Turn(
            reveal=(("hidden", "R2"),),
            calls=({"call": "push", "seat": 1}, {"call": "push", "seat": 0})))
    assert (sess.kernel.pcs[1].stress, sess.kernel.elapsed_turns,
            set(sess.kernel.ledger.revealed)) == before


def test_reveals_land_before_the_narration_that_describes_them():
    """The order in ``_apply`` is load-bearing: prose published before its
    declaration is a leak at the very next render."""
    sess = session_mod.new(seed=1)
    referee = Referee(seats.Turn(reveal=(("hidden", "R3"),),
                                 narrate="The far anchor is rotted."))
    rec = session_mod.play_session(sess, party(sess), referee, rounds=1)
    assert rec.gate1_held is True
    texts = [e["text"] for e in rec.transcript if e["kind"] == session_mod.REFEREE]
    declared = next(i for i, t in enumerate(texts) if "anchor is rotted" in t)
    narrated = max(i for i, t in enumerate(texts) if "anchor is rotted" in t)
    assert declared < narrated, "the kernel published the fact before the prose"


def test_the_blocking_ask_renders_to_the_named_seat_and_is_audited():
    sess = session_mod.new(seed=1)
    referee = Referee(seats.Turn(
        narrate="The referee turns to Ola.",
        ask={"seat": 1, "question": "What can you hear from the door?"}))
    rec = session_mod.play_session(sess, party(sess), referee, rounds=1)
    assert rec.gate1_held is True
    assert any(d["phase"] == "answer" and d["seat"] == 1
               for d in rec.decision_log), "the blocking call produced an answer"


def test_the_blocking_ask_carries_the_same_entitlement_as_a_turn_render():
    sess = session_mod.new(seed=1)
    sess.narrate("A shallow cavity under the bier.")
    asked = sess.question(1, "what do you hear?")
    assert sess.check(asked), (
        "the question render is bytes leaving for a model like any other")


def test_a_session_record_reads_as_the_arena_s_integrity_block():
    from core import integrity

    sess = session_mod.new(seed=7)
    rec = session_mod.play_session(
        sess, party(sess), seats.ScriptedAdjudicator(random.Random(3)), rounds=1)
    block = integrity.summarise([rec])
    assert block["decisions"] == rec.decisions
    assert block["fallback_rate"] == 0.0


def test_a_leaking_session_keeps_the_decisions_it_made():
    """The record rides on the exception.

    A caller that rebuilt a fresh record on a leak would drop the decisions the
    session made before it leaked - and the run's fallback rate would then be over
    a denominator missing exactly the sessions that went wrong.
    """
    sess = session_mod.new(seed=7)
    quiet = seats.Turn(narrate="Nothing happens.")
    leaky = Referee(quiet, quiet, seats.Turn(narrate="The far anchor is rotted."))
    with pytest.raises(session_mod.LeakDetected) as caught:
        session_mod.play_session(sess, party(sess), leaky, rounds=1)
    rec = caught.value.record
    assert rec.gate1_held is False
    assert rec.decisions > 0 and rec.turns > 0
    assert rec.leaks and rec.transcript
