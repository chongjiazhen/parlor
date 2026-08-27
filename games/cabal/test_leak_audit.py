"""Gate #1: no seat's rendered context ever reveals another seat's secret role,
beyond that seat's entitled night reveals. Plus: the night reveals are exactly
right, and the watcher genuinely cannot tell the seer from the mimic.
"""

import unittest

from core.observability import find_leaks
from games.cabal.audit import leak_audit, self_line
from games.cabal.referee import CabalReferee
from games.cabal.roles import (
    AGENT,
    HUNTER,
    LOYALIST,
    MIMIC,
    SEER,
    SETUP_5,
    THEME_1984_CN,
    THEME_1984_EN,
    THEME_BNW_EN,
    THEME_PLAIN,
    THEMES,
    WATCHER,
    Setup,
    Team,
)

#: Every shipped skin, so a repeated-role deal is checked in the faces a run can
#: actually be launched with rather than only the default one.
ALL_THEMES = tuple(THEMES.values())

FIXED = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: MIMIC, 4: HUNTER}


def ref(theme=THEME_1984_EN):
    return CabalReferee(setup=SETUP_5, assignment=dict(FIXED), theme=theme, leader=0)


def secret_terms(r):
    return {s: [role.key, r.theme.role_names[role.key]] for s, role in r.assignment.items()}


def leaks_for(r):
    terms = secret_terms(r)
    found = []
    for viewer in r.assignment:
        entitled = {k.seat for k in r.entitled_knowledge(viewer)}
        found += [(viewer, *hit) for hit in
                  find_leaks(r.render_context(viewer), terms, entitled, viewer)]
    return found


class TestGate1NoLeak(unittest.TestCase):
    def test_clean_default_face(self):
        self.assertEqual(leaks_for(ref(THEME_1984_EN)), [])

    def test_clean_chinese_skin(self):
        self.assertEqual(leaks_for(ref(THEME_1984_CN)), [])

    def test_clean_brave_new_world_skin(self):
        # Short display names ("Beta") and a blurb in the same vocabulary as the
        # role names are the collision risk here, and the audit is substring-naive.
        self.assertEqual(leaks_for(ref(THEME_BNW_EN)), [])

    def test_clean_plain_skin(self):
        # "Loyalist" role vs "The Faithful" faction - a substring-collision risk
        self.assertEqual(leaks_for(ref(THEME_PLAIN)), [])

    def test_clean_across_many_random_deals(self):
        for seed in range(50):
            r = CabalReferee.new(5, seed=seed)
            self.assertEqual(leaks_for(r), [], f"leak on seed {seed}")

    def test_a_deliberate_leak_is_caught(self):
        # sanity: if a render DID name a foreign role, the audit must fire
        r = ref()
        rendered = r.render_context(2) + "\npssst seat 3 is the mimic"
        terms = secret_terms(r)
        hits = find_leaks(rendered, terms, entitled=set(), viewer=2)
        self.assertIn((3, "mimic"), hits)


class TestRepeatedRole(unittest.TestCase):
    """Two seats dealt the SAME role hold the same secret term by construction, so
    the repo's usual remedy for a colliding term - rename it - cannot reach them.
    These pin the corpus narrowing that makes such a deal auditable, and pin that it
    narrowed the corpus rather than weakening the matcher.

    Nothing ships a repeated role yet: ``SETUP_5`` is five distinct ones. The deal
    below is the hand-built 7-seat shape the unbuilt setups would use, and this is
    setup work done before the setup so the audit is not discovered to be unsound
    on the first run that needs it.
    """

    SETUP_7 = Setup(n=7,
                    roles=(SEER, WATCHER, LOYALIST, LOYALIST, MIMIC, HUNTER, AGENT),
                    team_sizes=(2, 3, 3, 4, 4), fails_required=(1, 1, 1, 1, 1))
    DEAL = {0: SEER, 1: WATCHER, 2: LOYALIST, 3: LOYALIST,
            4: MIMIC, 5: HUNTER, 6: AGENT}

    def ref7(self, theme):
        return CabalReferee(setup=self.SETUP_7, assignment=dict(self.DEAL),
                            theme=theme, leader=0)

    def test_two_loyalist_seats_do_not_leak_each_other(self):
        # Before the fix this reported a MUTUAL leak in every skin - seat 2 and seat
        # 3 each reading the other's term out of its own "Your role:" line.
        for theme in ALL_THEMES:
            with self.subTest(theme=theme.name):
                self.assertEqual(leak_audit(self.ref7(theme)), [])

    def test_the_self_line_is_really_in_every_payload(self):
        # The strip is only sound while the line it removes is the line the referee
        # actually renders. `audit.self_line` re-templates it, so this is what stops
        # that duplicate drifting: a render change makes the strip match nothing and
        # this fails, instead of the audit silently going back to false positives.
        for theme in ALL_THEMES:
            for r in (self.ref7(theme), ref(theme)):
                for seat in r.assignment:
                    with self.subTest(theme=theme.name, n=r.n, seat=seat):
                        self.assertIn(self_line(r, seat),
                                      r.render_context(seat, include_speech=False))

    def test_a_repeated_term_outside_the_self_line_is_still_caught(self):
        # The soundness half. If the strip had been a blanket skip of same-role
        # seats, this leak would be invisible; it removes one line, so it is not.
        r = self.ref7(THEME_1984_EN)
        name = THEME_1984_EN.role_names["loyalist"]
        clean = r.render_context

        def leaky(seat, *a, **kw):
            return clean(seat, *a, **kw) + f"\npssst seat 3 is the {name}"

        r.render_context = leaky
        self.assertIn((2, 3, name), leak_audit(r))


class TestEntitlement(unittest.TestCase):
    def know(self, r, seat):
        return {(k.seat, k.label) for k in r.entitled_knowledge(seat)}

    def test_seer_sees_both_evil_as_evil(self):
        r = ref()
        self.assertEqual(self.know(r, 0), {(3, "evil"), (4, "evil")})

    def test_seer_cannot_tell_mimic_from_hunter(self):
        # both evil carry the same label; no field distinguishes them
        r = ref()
        self.assertEqual({k.label for k in r.entitled_knowledge(0)}, {"evil"})

    def test_evil_see_each_other(self):
        r = ref()
        self.assertEqual(self.know(r, 3), {(4, "fellow-evil")})
        self.assertEqual(self.know(r, 4), {(3, "fellow-evil")})

    def test_watcher_sees_two_magic_indistinguishable(self):
        r = ref()
        self.assertEqual(self.know(r, 1), {(0, "magic"), (3, "magic")})
        # exactly seer(0) and mimic(3), same label -> cannot tell which is real
        self.assertEqual({k.label for k in r.entitled_knowledge(1)}, {"magic"})

    def test_loyalist_knows_nothing(self):
        self.assertEqual(self.know(ref(), 2), set())


if __name__ == "__main__":
    unittest.main()
