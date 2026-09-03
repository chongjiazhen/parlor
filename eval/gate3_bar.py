"""The ONE bar the arm-level gate #3 is called against, and the clause that moves it.

There were two, and they disagreed. `eval.run_changeling._chance` derives a
per-vote chance from the RUN'S OWN mix of one- and two-wolf dawns; this module
carries the same estimator frozen off an `--arm random` sweep at n=4000. Both are
honest estimators of one quantity and neither is a mistake - the defect was that
the run log called the gate against the first while every frozen criterion names
the second, so the two answered differently on the same records.

Measured on the skin pair, 2026-09-02, which is why this file exists: both llm
arms and the control's first 200 games are seed-identical - 251 blind votes, dawn
mix 4/92/104 - so the ONLY reason the in-run log printed 36.47% and the tool
35.84% is that the control pooled 1000 games. `greek-named`'s Wilson floor is
35.90%, which HOLDS against the criterion's bar and is NOT SHOWN against the
log's, by 0.06 points. Nothing published moved: a pair figure is a difference on
identical deals, so the bar cancels out of it.

**The bar is this one**, because `docs/changeling-gate3-criterion.md` names it and
a criterion is not editable after launch: "the measured per-vote chance from
`--arm random`, n=4000", plus the clause below. A run's own deal is a diagnostic
beside it and never the thing the gate is cut on.

**`eval.s5_verdict.blind_chance` is NOT a candidate and must not be promoted** -
restricting the arithmetic to the blind stratum's own dawn-wolf mix is choosing
the statistic with the numbers in view, and `s5_verdict` already refuses it in
those words.

The value itself is `games/changeling/RULES.md` §The chance baseline. It is a
MEASUREMENT, so it moves only when that sweep is re-run: 35.95% when the gate #3
criterion was written 2026-08-28, re-measured to 35.84% on 2026-09-02. A criterion
frozen against either figure keeps the figure it froze against - `s5_verdict`
holds S2's 35.95% for that reason and does not import this.
"""

from __future__ import annotations

#: Per-vote villager chance under `plurality-min2`, `--arm random` n=4000
#: (`games/changeling/RULES.md` §The chance baseline, re-measured 2026-09-02).
REFERENCE_CHANCE = 0.3584

#: The own-arm clause, in the gate #3 criterion's own words: "the run must also
#: report its own random arm; if that arm disagrees with the reference by more
#: than a point, the run's own arm is the bar and this number is the thing that
#: was wrong." A point is a POINT, not a proportion of the rate.
OWN_ARM_TOLERANCE = 0.01

#: Binary floating point decides the boundary otherwise, and it decides it the
#: wrong way: `0.3584 + 0.01` differs from `0.3584` by 0.010000000000000009, so a
#: control exactly one point out was read as MORE than a point out and took the
#: bar off the criterion. No real control lands there - the point is that the
#: clause says "more than a point" and the code has to mean it.
_BOUNDARY_SLACK = 1e-9


def own_bar(control_rate: float | None) -> tuple[float, str]:
    """The criterion's own-arm clause, applied as written, with its reason.

    Returns the bar and the sentence saying why it is the bar - the sentence is
    not decoration. A tool that printed only the number would leave a reader
    unable to tell a reference bar from a substituted one, which is the same
    ambiguity between two chance figures that this module exists to end.
    """
    if control_rate is None:
        return REFERENCE_CHANCE, "no control read - reference bar stands"
    if abs(control_rate - REFERENCE_CHANCE) > OWN_ARM_TOLERANCE + _BOUNDARY_SLACK:
        return control_rate, (f"own arm {control_rate:.2%} is more than a point "
                              f"from {REFERENCE_CHANCE:.2%} - the own arm is the bar")
    return REFERENCE_CHANCE, (f"own arm {control_rate:.2%} agrees with "
                              f"{REFERENCE_CHANCE:.2%} - the reference is the bar")
