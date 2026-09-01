# Gate #3a retired - 2026-08-27 (S1), on arithmetic rather than on budget

**cabal's gate #3a is abandoned at 5 seats and at every other table size.** Decided
on `hunt20c`'s own interval plus arithmetic over records already in hand, with no
new games. **Every number here is recomputable**: `py -3 -m eval.gate3_arithmetic`,
which prints its own instrument control first and exits non-zero if the
reconstruction stops checking. A verdict that retires a gate should not rest on
arithmetic nobody can re-run.

The instrument was controlled before anything was derived from it: the analysis
pipeline reproduced the recorded +8.82%/+9.00% slopes of `hunt20b`/`hunt20c`, their
binary figures and all four CIs exactly, and reconstructed every vote's team
membership from `public_events` with proposals x 5 == votes in 20 of 20 games.

Gate #3b is a separate verdict and a separate document - `docs/gate3b-verdict.md`,
where the S6 campaign returned NOT SHOWN and cabal's GPU program stopped.

The review that started this is `docs/gate3-modelling-review.md` (2026-08-26,
promoted 2026-08-27 with a resolution header). It found that the old blind gate's
clean term still carried the seer, and every ranked fix below it landed - but read
its header before its body: its line citations are stale and the gate it was
sharpening is the one this file retires. Its last open item, the over-sabotage
reframe, landed 2026-08-28 in S9; the review is closed on all six.

## The reason to stop is NOT that N is unaffordable

`queue.md` said "cannot show gate #3a at an affordable N" from `hunt20d` onward.
That was written before anyone priced it, and it is wrong. Priced against
`hunt20c`'s own per-game bootstrap SD (4.75% on the graded slope):

| target | games for a 95% floor above 0 | GPU at 19.85 min/game |
|---|---|---|
| at the raw +9.00% effect | ~22 | 7.3 h |
| if the honest effect is 75% of it | ~38 | 13 h |
| if the honest effect is 50% of it | ~86 | 28 h |

Two to four overnight runs. Affordable. **The problem is what arrives at the end of
them:** the affordable N buys precision on a quantity that is not the gate's.

## The deconfounded estimator accrues at ~0.3-0.4 votes per game, and no table size fixes it

The self-membership confound is not a bias to correct, it is a sampling floor: at 5
seats a clean 3-team holds ALL three good seats, so an off-team blind vote on a
clean team can only occur on a 2-person clean team. Measured on both post-fix runs:

| blind stratum | `hunt20b` | `hunt20c` |
|---|---|---|
| all blind (the reported binary) | +19.94% (n=44/71) | +18.11% (n=50/108) |
| ON-team | +22.01% (n=38/33) | +8.91% (n=42/43) |
| **OFF-team - the only unconfounded cell** | **+9.65% (n=6/38)** | **+18.08% (n=8/65)** |

**The two runs put the split in OPPOSITE directions** - `hunt20b` says the
confounded cell is the flattering one, `hunt20c` says the reverse - on 6 and 8
off-team clean votes respectively (9 in `hunt20`). That instability IS the finding:
the cell that would answer gate #3a is too thin to hold a sign across two draws, so
no amount of reasoning about the direction of the confound rescues the headline.
Forty such votes is ~100-134 games (33-44 h) and a hundred is ~250-330 games, and
that is the raw sample count before any interval is asked of it. The metric that
would actually answer gate #3a costs an order of magnitude more than the confounded
one, and the confounded one is all any affordable run measures.

**7p and 8p do not reopen it - checked, not assumed.** Off-team-clean good votes per
vote event, random teams, official mission sizes: 5p **0.120**, 7p **0.160**, 8p
**0.100**. 7p's +33% raw yield is eaten by 40% more speaking seats (0.0229 vs 5p's
0.0240 per unit speaking cost) and 8p is half as good. This closes the door the 6/7p
item left ajar: there is no cabal configuration where the honest gate-#3a number
gets cheaper. Consistent with `docs/player-counts.md`, which reached the same
conclusion from the clean-team side.

## A second, independent reason: the declared statistic cannot be repaired after the fact

The scorer calls the graded slope THE GATE, and its floor is decided by noise at
this N (+0.94% then -0.25% on a point estimate that barely moved). The binary blind
figure clears 0 in both runs that have it (`hunt20b` +19.94% [+6.27%, +32.02%],
`hunt20c` +18.11% [+3.52%, +33.53%]) and is better-specified for a step-shaped
response - but promoting it now would be choosing the statistic with the results in
view, which is the `hunt20b` error wearing a third hat. So the strongest 3a evidence
in the repo sits on a statistic that cannot honestly be declared the gate, and
buying N does not change that either.

## What gate #3a IS allowed to be reported as, and it is not nothing

> Blind seats approve clean teams more than tainted ones by ~+18pp (binary, two runs
> agreeing), and ~+9pp per additional saboteur; both figures pool self-votes with
> off-team votes and are downstream of seer-originated public signal, so they
> measure *information reaching blind seats through play*, not *blind seats
> detecting evil unaided*. The unaided estimator exists (off-team, clean-vs-tainted)
> but its sample accrues at 0.4 votes/game and is unaffordable at this rung.

That paragraph is publishable and it is the end of the matter - the honest claim was
already reachable, and more GPU was only ever going to narrow an interval around the
wrong quantity.

**One caveat belongs in it**: 4 of 20 games carry a small real confound. A true "I am
the Inner Party" from a knowledge-holding good seat hands the table a fact, so good's
discrimination on those games is partly compliance rather than deduction. It does not
move this verdict - 3a is abandoned on other grounds - but it belongs in the
paragraph.

## What died with it, and what only moved

- **The cloud arm dies with 3a.** Cloud was wanted because gate #3 read as a
  cloud-scale job. 3b at 40 games is 13.2 h on a pinned local model with known
  attribution, which is strictly better evidence than a time-varying `auto` mix.
  There is no longer a condition worth watching for.
- **The negation pass, the notebook, theme polarity and mini-personas are re-homed,
  not cancelled.** Each is a prompt change and so a measured change; a paired cabal
  arm costs 13.2 h to move a number 3a no longer spends precision on. They belong on
  changeling, where a paired 20-game arm is ~30 min, or they land nowhere. Their rows
  are live in `queue.md`.
- **S7 (measured prompt variables) was dropped as a cabal GPU program** for the same
  arithmetic.

## The self-outing count, read 2026-08-27 - most of them are not self-outings

Every one of the 26 lines dumped in full against its seat's dealt role. The
heuristic's 26/1580 is **~8 genuine self-identifications, in 4 of 20 games**; the
other ~21 are a seat using its OWN role's word to accuse somebody else ("that's a
Watcher's tell", "no legitimate Outer Party member would reject every mission"),
which is the opposite of outing itself.

- **The `hunt20c` cluster was read backwards, and `queue.md` said so.** The 11-line
  cluster on one seat is game 11 seat 1, and all 11 are accusations aimed outward.
  The "that was cover. As Inner Party, I now urge..." quote is a DIFFERENT seat (game
  4 seat 0) with 4 lines. One-line truncation is what made the two look like one
  thing.
- **Root cause, and it is a theme problem, not a play problem.** On `1984-en` the
  role names ARE ordinary faction nouns of the fiction - `watcher` is "Inner Party",
  `loyalist` is "Outer Party" - so the word carries no secret and saying it is
  usually just table talk. Same class as the plain-skin "Loyalist" collision flagged
  for the leak audit. A functional-key match sees nothing (the old 0/1290) and a
  theme-name match over-counts by ~3x; neither is a measurement.
- **What the 8 real ones are: all TRUE, none of them the seer.** Game 4 seat 0, game
  9 seat 4 and game 16 seat 1 are the `watcher` naming itself; game 13 seat 4 is the
  `mimic` - an EVIL seat outing itself, twice, in one game. The seer never announced
  itself in any of the 20 games. **So gate #3b was NOT contaminated**, which is the
  part that was load-bearing while S6 was in flight.
- **The check cannot see the interesting case, BY CONSTRUCTION.** It matches only the
  seat's OWN role name, so every hit is trivially true and a mimic claiming to be the
  seer - deception working, the thing worth counting - is invisible to it. "Is the
  announcement true?" was never a question this number could answer. Counting FALSE
  claims needs a different check.

**S13 closed 2026-09-01T00:31:53.6091592Z.** Its claim-shaped matcher (first person,
present tense) re-scored the records: `hunt20b` 0/1150 at 0.54% fallback and
`hunt20c` 7/1580 at 1.78% fallback. `docs/measurements.md` carries the dated read.
The separate false-claim question remains S16.
