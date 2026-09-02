"""Group-sequential boundaries for a one-sided binomial test - S25.

    py -3 -m eval.sequential --n 272 --looks 0.5 1.0 --alpha 0.025 --spend obf
    py -3 -m eval.sequential --n 272 --looks 0.5 1.0 --alpha 0.025 --spend obf --p0 0.3014

**What this is.** A pre-committed fixed N with no early stop is the honest
design this repo has run every campaign under, because stopping when a floor
happens to cross is peeking (`docs/evidence-discipline.md` §Pre-committing a
statistic). The named fix is not "don't look": it is to compute, BEFORE the run,
a boundary at each of a small number of pre-declared interim looks such that the
total chance of a false positive across all of them is still the overall alpha.
That is group-sequential design with a Lan-DeMets alpha-spending function
(Lan & DeMets 1983). Two spending shapes are offered:

- ``obf`` - O'Brien-Fleming-type spending, the DEFAULT. Spends almost nothing
  early, so an early stop needs overwhelming evidence and the final boundary sits
  close to the single-look value. This is the conservative shape and the one a
  campaign should use unless it has a reason not to.
- ``pocock`` - Pocock-type spending, the named alternative. Spends alpha nearly
  evenly, so early stops are easier and the final boundary is materially higher
  than a single-look test's.

The test is ONE-SIDED on a binomial proportion against a pre-committed chance
bar ``p0`` - exactly the shape of changeling gate #3 (blind villager accuracy
against a derived chance bar). The UNIT is the thing the criterion counts: blind
VOTES, never games. The waker criterion prices ~272 blind votes at 200 games, and
it is the vote count on the record at a look that fixes the information fraction,
not the game count.

**What this is NOT.** It computes nothing about a record and reads no record. A
boundary is applied by a verdict module written against a criterion that
DECLARED the looks before launch; ``look`` refuses a look at any total that was
not declared, and that refusal is the guard, not a convenience.

The arithmetic
--------------

Under the null the sequential statistic at look ``k`` is ``Z_k``, and on the
B-value scale ``B_k = Z_k * sqrt(t_k)`` is standard Brownian motion observed at
the information fractions ``t_1 < ... < t_K = 1``: ``B_1 ~ N(0, t_1)`` and
``B_k - B_{k-1} ~ N(0, t_k - t_{k-1})`` independently. The spending function
``a(t)`` says how much of alpha may have been spent by information ``t``; the
boundary ``c_k`` at look ``k`` is the value such that

    P(B_1 < c_1 sqrt(t_1), ..., B_{k-1} < c_{k-1} sqrt(t_{k-1}), B_k >= c_k sqrt(t_k))
        = a(t_k) - a(t_{k-1}).

The left side is computed by the standard recursion (Armitage, McPherson & Rowe
1969): keep the sub-density ``f_k(b)`` of ``B_k`` on the continuation region on a
grid, and integrate the Gaussian increment kernel against it to get ``f_{k+1}``.
The exit probability at look ``k`` is the integral of ``f_{k-1}`` against the
upper tail of the increment, which needs no grid above the boundary. ``c_k`` is
then found by bisection, since the exit probability is monotone in it.

**The grid.** Uniform on the B scale from ``GRID_LO`` (-8; ``B_k`` has standard
deviation at most 1, so the mass below it is under 1e-15) to the current
boundary, at a fixed step ``GRID_STEP`` (0.02, so ~500-600 points per look),
trapezoid rule. A fixed STEP rather than a fixed count means the Gaussian kernel
between two looks depends only on the index offset and is tabulated once, which
keeps a pure-Python O(n^2) convolution to ~0.1 s per look. Trapezoid on a
Gaussian is spectrally accurate away from the truncation at the boundary, where
it is O(step^2); the classic O'Brien-Fleming and Pocock constants from the
published tables are reproduced to 0.005 in z (``eval/test_sequential.py``), and
halving the step moves the K=3 and K=5 boundaries by under 1e-4, which is the honest
statement of the grid's accuracy. A 20000-trial null simulation lands inside
the Wilson interval of alpha.

The normal CDF is ``math.erf``; its inverse is a bisection over that CDF, so the
module is stdlib only, on purpose - a boundary that needs scipy to recompute
is a boundary a cold session cannot check.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass

#: The grid the recursion integrates on. See the module docstring.
GRID_LO = -8.0
GRID_STEP = 0.02

#: Verdicts returned by ``look``.
CROSSED = "CROSSED"
CONTINUE = "CONTINUE"

SPENDING = ("obf", "pocock")


class UndeclaredLook(ValueError):
    """A look at a total that the boundary never declared. A peek, and the
    sequential read is void the moment one happens; refused loudly instead."""


# ---- the normal distribution, stdlib only ------------------------------------

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def norm_pdf(z: float) -> float:
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def norm_ppf(p: float) -> float:
    """Inverse CDF by bisection over ``norm_cdf``, to 1e-12 in z."""
    if not 0.0 < p < 1.0:
        raise ValueError(f"norm_ppf needs 0 < p < 1, got {p}")
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-12:
            break
    return 0.5 * (lo + hi)


# ---- spending functions --------------------------------------------------------

def spend_obf(t: float, alpha: float) -> float:
    """O'Brien-Fleming-type Lan-DeMets spending: a(t) = 2 - 2 Phi(z_{1-alpha/2} / sqrt(t))."""
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return alpha
    return 2.0 - 2.0 * norm_cdf(norm_ppf(1.0 - alpha / 2.0) / math.sqrt(t))


def spend_pocock(t: float, alpha: float) -> float:
    """Pocock-type Lan-DeMets spending: a(t) = alpha * ln(1 + (e - 1) t)."""
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return alpha
    return alpha * math.log(1.0 + (math.e - 1.0) * t)


def spending(name: str):
    if name == "obf":
        return spend_obf
    if name == "pocock":
        return spend_pocock
    raise ValueError(f"unknown spending function {name!r}; one of {SPENDING}")


# ---- the recursion --------------------------------------------------------------

def _grid(hi: float) -> list[float]:
    """Uniform grid at GRID_STEP ending EXACTLY at ``hi`` and starting at or
    below GRID_LO. Anchored at the cut, not at GRID_LO: a grid whose last point
    rounded up past the cut carried mass from above the boundary into the
    continuation density, and measured 0.003-0.013 high on the classic
    constants, growing with K. Fixed SPACING rather than a fixed count, so the
    Gaussian kernel between two looks depends only on the index offset plus one
    constant shift and is tabulated once per look."""
    n = int(math.ceil((hi - GRID_LO) / GRID_STEP)) + 1
    return [hi - (n - 1 - i) * GRID_STEP for i in range(n)]


def _trap(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return GRID_STEP * (sum(values) - 0.5 * (values[0] + values[-1]))


def _exit_prob(prev_grid, prev_f, dt, b_cut: float) -> float:
    """P(continue through k-1, then B_k >= b_cut), from the sub-density of
    B_{k-1} on its continuation grid. Exact in the tail: no grid above the cut."""
    sd = math.sqrt(dt)
    return _trap([f * (1.0 - norm_cdf((b_cut - u) / sd)) for u, f in zip(prev_grid, prev_f)])


def _next_density(prev_grid: list[float], prev_f: list[float], dt: float,
                  new_grid: list[float]) -> list[float]:
    """Convolve the sub-density with the N(0, dt) increment onto the next grid.
    Both grids share GRID_STEP, so b_i - u_j = shift + (i - j) * step and the
    kernel is one table indexed by i - j."""
    sd = math.sqrt(dt)
    m, n = len(prev_f), len(new_grid)
    shift = new_grid[0] - prev_grid[0]
    span = max(m, n)
    kern = [norm_pdf((shift + k * GRID_STEP) / sd) / sd for k in range(-span, span + 1)]
    # trapezoid weights on the OLD grid, folded into the density once
    w = list(prev_f)
    w[0] *= 0.5
    w[-1] *= 0.5
    out = []
    for i in range(n):
        base = i + span
        out.append(GRID_STEP * sum(w[j] * kern[base - j] for j in range(m)))
    return out


def _bisect(fn, target: float, lo: float = -1.0, hi: float = 12.0, tol: float = 1e-9) -> float:
    """Smallest cut with fn(cut) <= target; fn is decreasing in cut."""
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if fn(mid) > target:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def _first_density(t: float, grid: list[float]) -> list[float]:
    sd = math.sqrt(t)
    return [norm_pdf(b / sd) / sd for b in grid]


def z_boundaries(fractions: list[float], alpha: float, spend: str = "obf") -> list[float]:
    """Efficacy z-boundaries at each declared information fraction, by the
    recursion in the module docstring. Fractions must be strictly increasing,
    in (0, 1], and end at 1."""
    _check_fractions(fractions)
    fn = spending(spend)
    return _boundaries_for(fractions, [fn(t, alpha) for t in fractions])


def _boundaries_for(fractions: list[float], cumulative: list[float],
                    fixed: list[float | None] | None = None) -> list[float]:
    """Boundaries such that the cumulative exit probability at look k under the
    null equals ``cumulative[k]``. The general form; the spending functions
    reduce to it, and ``_total_alpha`` is the same walk with the cuts given.

    ``fixed[k]``, when not None, is a z-boundary used VERBATIM at look k - the
    alpha it actually spends is carried forward, and only the unfixed looks are
    solved. That is how ``refit_final`` keeps the declared interim boundaries
    and re-solves the last one at the information the record actually holds.
    """
    fixed = fixed or [None] * len(fractions)
    bounds: list[float] = []
    prev_grid: list[float] = []
    prev_f: list[float] = []
    prev_t = 0.0
    spent = 0.0
    for k, t in enumerate(fractions):
        dt = t - prev_t
        if k == 0:
            def exit_k(cut, t=t):
                return 1.0 - norm_cdf(cut / math.sqrt(t))
        else:
            def exit_k(cut, g=prev_grid, f=prev_f, dt=dt):
                return _exit_prob(g, f, dt, cut)
        if fixed[k] is None:
            b_cut = _bisect(exit_k, max(cumulative[k] - spent, 0.0))
            spent = cumulative[k]
        else:
            b_cut = fixed[k] * math.sqrt(t)
            spent += exit_k(b_cut)
        bounds.append(b_cut / math.sqrt(t))
        if k < len(fractions) - 1:
            grid = _grid(b_cut)
            f_k = _first_density(t, grid) if k == 0 else _next_density(prev_grid, prev_f, dt, grid)
            prev_grid, prev_f, prev_t = grid, f_k, t
    return bounds


def classic_boundaries(k: int, alpha: float, shape: str = "obf") -> list[float]:
    """The CLASSIC O'Brien-Fleming (c_k = C sqrt(K/k)) or Pocock (c_k = C)
    boundaries at K equally spaced looks, with C solved so the total one-sided
    type-I error is alpha. These are the values the published tables carry
    (Jennison & Turnbull, Tables 2.1 and 2.3, at two-sided 2*alpha), and they
    are what the reference test recomputes. They are NOT the spending-function
    boundaries, which agree in shape and differ in the second decimal."""
    if shape not in SPENDING:
        raise ValueError(shape)
    fractions = [i / k for i in range(1, k + 1)]

    def cuts_for(const: float) -> list[float]:
        if shape == "obf":
            return [const * math.sqrt(k / i) for i in range(1, k + 1)]
        return [const] * k

    const = _bisect(lambda c: _total_alpha(fractions, cuts_for(c)), alpha,
                    lo=1.0, hi=8.0, tol=1e-5)
    return cuts_for(const)


def _total_alpha(fractions: list[float], cuts: list[float]) -> float:
    """Total one-sided type-I error of a given z-boundary, by the same recursion."""
    total = 0.0
    prev_f: list[float] = []
    prev_grid: list[float] = []
    prev_t = 0.0
    for k, (t, c) in enumerate(zip(fractions, cuts)):
        dt = t - prev_t
        b_cut = c * math.sqrt(t)
        total += (1.0 - norm_cdf(c)) if k == 0 else _exit_prob(prev_grid, prev_f, dt, b_cut)
        if k < len(fractions) - 1:
            grid = _grid(b_cut)
            f_k = _first_density(t, grid) if k == 0 else _next_density(prev_grid, prev_f, dt, grid)
            prev_grid, prev_f, prev_t = grid, f_k, t
    return total


def _check_fractions(fractions: list[float]) -> None:
    if not fractions:
        raise ValueError("at least one look")
    if any(not 0.0 < t <= 1.0 for t in fractions):
        raise ValueError(f"information fractions must lie in (0, 1]: {fractions}")
    if any(b <= a for a, b in zip(fractions, fractions[1:])):
        raise ValueError(f"information fractions must strictly increase: {fractions}")
    if abs(fractions[-1] - 1.0) > 1e-12:
        raise ValueError(f"the last look is the full sample, fraction 1.0: {fractions}")


# ---- the boundary as a hit count ----------------------------------------------

@dataclass(frozen=True)
class Look:
    index: int          # 1-based
    fraction: float     # declared information fraction
    total: int          # the unit count at this look - what a record must show
    z: float            # efficacy boundary on the z scale
    min_hits: int       # smallest hit count that crosses at this look
    alpha_spent: float  # cumulative alpha spent through this look


@dataclass(frozen=True)
class Boundary:
    n: int
    p0: float
    alpha: float
    spend: str
    looks: tuple[Look, ...]

    def totals(self) -> tuple[int, ...]:
        return tuple(l.total for l in self.looks)


def min_hits(total: int, p0: float, z: float) -> int:
    """Smallest hit count whose score statistic (hits - n p0) / sqrt(n p0 q0)
    reaches z. At z = 1.96 this is the count whose Wilson 95% floor clears p0 -
    the Wilson interval is the inversion of exactly this statistic - so a
    one-look boundary reproduces the repo's existing gate arithmetic."""
    mean = total * p0
    sd = math.sqrt(total * p0 * (1.0 - p0))
    return max(0, min(total, math.ceil(mean + z * sd - 1e-9)))


def design(n: int, fractions: list[float], alpha: float, p0: float,
           spend: str = "obf") -> Boundary:
    """The full pre-committed boundary for a campaign counting ``n`` units."""
    if not 0.0 < p0 < 1.0:
        raise ValueError(f"p0 must be a proportion: {p0}")
    if n <= 0:
        raise ValueError("n must be positive")
    zs = z_boundaries(fractions, alpha, spend)
    fn = spending(spend)
    looks = []
    for i, (t, z) in enumerate(zip(fractions, zs), start=1):
        total = int(round(t * n))
        looks.append(Look(i, t, total, z, min_hits(total, p0, z), fn(t, alpha)))
    totals = [l.total for l in looks]
    if len(set(totals)) != len(totals):
        raise ValueError(f"two looks round to the same total at n={n}: {totals}")
    return Boundary(n, p0, alpha, spend, tuple(looks))


def exact_type1(boundary: Boundary) -> float:
    """The EXACT probability, under Bin(., p0), that the integer hit-count
    boundary is crossed at some look. Not the normal-approximation alpha: an
    integer boundary rounds the z boundary to a hit count, and the binomial is
    discrete, so the true error sits above or below alpha by an amount the
    z table cannot show. This is what a criterion publishes beside the table.
    Exact by recursion over the hit count carried into each look; no grid."""
    p0 = boundary.p0
    # mass over hit counts still in play after each look
    carry = {0: 1.0}
    crossed = 0.0
    done = 0
    for lk in boundary.looks:
        m = lk.total - done
        pm = [math.comb(m, j) * p0 ** j * (1 - p0) ** (m - j) for j in range(m + 1)]
        nxt: dict[int, float] = {}
        for h, mass in carry.items():
            for j, pj in enumerate(pm):
                total_h = h + j
                if total_h >= lk.min_hits:
                    crossed += mass * pj
                else:
                    nxt[total_h] = nxt.get(total_h, 0.0) + mass * pj
        carry = nxt
        done = lk.total
    return crossed


def refit_final(boundary: Boundary, n_final: int) -> Boundary:
    """The boundary at the FINAL look, at the total the record actually holds.

    A campaign is priced in votes and run in games, so it lands near the
    planned N and never on it. The standard Lan-DeMets answer: every interim
    look keeps the z and hit count it was DECLARED with (the alpha they spent is
    what it was), the final look's information fraction becomes 1 at
    ``n_final``, the interim fractions are re-expressed as their declared totals
    over ``n_final``, and only the final z is re-solved so the total is alpha.
    Nothing about WHEN the looks happen is data-driven - the interims were fixed
    counts and the final is the run's planned end - which is the one condition
    the design needs. ``n_final`` below the last declared interim total is
    refused: that is a run that stopped short, not a final look.
    """
    interims = boundary.looks[:-1]
    if n_final <= 0:
        raise ValueError("n_final must be positive")
    if interims and n_final <= interims[-1].total:
        raise ValueError(f"n_final={n_final} is not past the last interim look at "
                         f"{interims[-1].total}: a run that stopped short has no final look")
    fractions = [lk.total / n_final for lk in interims] + [1.0]
    fixed: list[float | None] = [lk.z for lk in interims] + [None]
    fn = spending(boundary.spend)
    cumulative = [fn(t, boundary.alpha) for t in fractions]
    zs = _boundaries_for(fractions, cumulative, fixed)
    z_final = zs[-1]
    looks = tuple(interims) + (Look(len(interims) + 1, 1.0, n_final, z_final,
                                    min_hits(n_final, boundary.p0, z_final), boundary.alpha),)
    return Boundary(n_final, boundary.p0, boundary.alpha, boundary.spend, looks)


def look(boundary: Boundary, hits: int, total: int) -> str:
    """Apply the boundary at one look. ``CROSSED`` or ``CONTINUE``.

    ``total`` must be one of the declared look totals exactly. Any other total is
    a look the criterion never declared - a peek - and is REFUSED rather than
    interpolated, because interpolating it is exactly the alpha the design did
    not spend.
    """
    if not 0 <= hits <= total:
        raise ValueError(f"hits {hits} outside 0..{total}")
    for lk in boundary.looks:
        if lk.total == total:
            return CROSSED if hits >= lk.min_hits else CONTINUE
    raise UndeclaredLook(
        f"a look at total={total} was never declared; the boundary declares "
        f"{boundary.totals()}. A look at any other point is a peek and voids the "
        "sequential read.")


# ---- CLI --------------------------------------------------------------------------

def table(boundary: Boundary) -> list[str]:
    b = boundary
    out = [f"group-sequential boundary - n={b.n} units, one-sided alpha={b.alpha}, "
           f"spending={b.spend}, p0={b.p0:.4f}",
           f"  grid: step {GRID_STEP:g} from {GRID_LO:g} on the B scale, trapezoid",
           "",
           f"  {'look':>4}  {'frac':>6}  {'total':>6}  {'z':>7}  {'min hits':>8}  "
           f"{'min rate':>8}  {'alpha spent':>11}"]
    for lk in b.looks:
        out.append(f"  {lk.index:>4}  {lk.fraction:>6.3f}  {lk.total:>6}  {lk.z:>7.3f}  "
                   f"{lk.min_hits:>8}  {lk.min_hits / lk.total:>8.2%}  {lk.alpha_spent:>11.5f}")
    z1 = norm_ppf(1.0 - b.alpha)
    single = min_hits(b.n, b.p0, z1)
    single_exact = exact_type1(Boundary(b.n, b.p0, b.alpha, b.spend,
                                        (Look(1, 1.0, b.n, z1, single, b.alpha),)))
    last = b.looks[-1]
    out += ["",
            f"  exact binomial type-I error of this integer boundary: {exact_type1(b):.4f} "
            f"(nominal {b.alpha})",
            f"  single-look reference at n={b.n}: z={z1:.3f}, min hits {single} "
            f"({single / b.n:.2%}), exact type-I {single_exact:.4f} - the Wilson-floor gate",
            f"  cost of the design at full information: {last.min_hits - single} more "
            f"hit(s) ({last.min_hits / b.n - single / b.n:+.2%}); z {last.z:.3f} vs {z1:.3f}"]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="pre-committed group-sequential boundaries")
    ap.add_argument("--n", type=int, required=True,
                    help="planned total of the UNIT the criterion counts (votes, not games)")
    ap.add_argument("--looks", type=float, nargs="+", required=True,
                    help="information fractions of the declared looks, ending at 1.0")
    ap.add_argument("--alpha", type=float, default=0.025, help="overall one-sided alpha")
    ap.add_argument("--spend", choices=SPENDING, default="obf")
    ap.add_argument("--p0", type=float, default=0.5, help="the pre-committed chance bar")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(chr(10).join(table(design(args.n, args.looks, args.alpha, args.p0, args.spend))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
