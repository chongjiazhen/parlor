# The queue - open work

Queue only. Done work leaves - **delete the row.** What stays is the ask, its
entry condition and what done looks like. What leaves goes by lifetime, and
**nothing is rewritten on the way out** - a moved paragraph goes verbatim under a
dated heading in `docs/open-arms.md` (the argument behind a row),
`docs/measurements.md` (a dated reading), `docs/decisions.md` (a settled call) or
`docs/slices.md` (a struck slice). The budget is bytes and the pre-commit gate
ratchets it - read it before writing a row, not by failing it:
`sh scripts/hygiene-check.sh --budget`.

**One exception: a finished slice is struck and annotated, never deleted**,
because live rows cite slices by name.

## Cold start

**First command of any session that thinks a run is live:**

```
grep -L 'PARLOR DONE' eval/records/*.log   # names every run still in flight
```

Narrow it to a campaign's own arms when you know them, and exclude the files that
never carry the marker - `hunt6[ab]`, not `hunt6*`, which also matches
`hunt6b-chain.log` and so reads "in flight" forever. **Never judge a run by a
process probe.** Most of what it names is a fossil: the marker landed in S4
(`core/runlog.py`), so every earlier log lacks it permanently. Read the answer
against `queue.local.md`'s launch record and treat a name it does not list as a
fossil rather than a run.

**No progress figure, ETA or log-tail path is recorded here** - a count about a
running job is stale the hour it is written, and an ETA in this block was wrong
twice on 2026-08-27. That class lives in `queue.local.md`, along with whether a
freeze binds right now; this file keeps terminal states and route decisions.

## What each rung owes

One debt per rung, and **this table is the only place that state lives** - a
second copy is the one that goes stale. `GLOSSARY.md` defines rung, arm and void.
**No reading is restated here**: they are `docs/measurements.md`, the calls are
`docs/decisions.md`.

| rung | engine | model in a seat | what it owes |
|---|---|---|---|
| **cabal** | done | yes | nothing runnable. Its GPU program stopped at gate #3b and its live arms re-homed to changeling, so what it holds is parked, not work: **over-sabotage (b), naming the partner, is measured to HURT** and is an arm of its own if ever tried (`docs/open-arms.md`); **6/7p is dealt and baselined**, and what is left is a model (`docs/measurements.md`) |
| **changeling** | done | yes - gate #3 HOLDS on BOTH decks (S5 five-seat, S19 six-seat waker) | the `waker` deck is read and its question ANSWERED: the waker seat's advantage does not clear zero. **Not shown, not no** - the deck hit the one-vote-per-game ceiling its criterion named, so settling it needs a NEW criterion, a longer arm or a deck seating two waker-class cards, never a re-read of these records. `kindred` deck B is FROZEN and unlaunched - its row below |
| **quorum** | done, and the live4 arm READ 2026-09-01 | **never** | nothing runnable. Both clauses INFORM over one fallback decision in 2582; read `docs/measurements.md` before citing either. Seeds 11200..11219 are spent alongside 5200..5599 / 7000..7399, so a fifth arm needs fresh ones and a criterion of its own. The repeat-claim void has still never fired |
| **belfry** | done, scoring lane, control instrument, sampled-player arm, S8 referee read, live2 READ | **never** | nothing runnable. The session-memory night arm RAN and is READ 2026-09-03 - COHERENT, NO RECALL, BELOW SUPPLIED - and what it left is an observation row below, not a run. S8b is DISTINGUISHABLE and live2's Clause A INFORMS; Clause B spans chance and no second arm chases it. **S29's central prediction is FALSIFIED**: that arm carries `recovered 27` over 2454 calls at 0.00% fallback, so the retry now has the live record S29 said no arm would produce - its refusal to buy one stands, its stated mechanism does not (`docs/decisions.md`) |
| **DURF** | done | yes, and gate #1 held under the topology edits | a term decision and two questions that are not code, all three in §The three DURF questions. The adjacency question is DECIDED, its edits APPLIED, its campaign LANDED |
| **adjudicator** | S8b read | referee only | held-out source accuracy clears its Wilson chance ceiling; bounded trace difference only |

**Do not mix cabal and changeling in one session.** Separate `RULES.md` files,
scorers and baselines - every number confusion in this file so far came from
carrying one game's intuition into the other's denominator.

## The three DURF questions that are still open

Named here, argued in `docs/open-arms.md`. None is code and none obliges a run.
**`hidden catch`** collides with ordinary searching prose and is deliberately
unfixed, because the edit voids its own read. **Movement is still unconstrained
by the exit graph** - adjacency is a RULES change and therefore a separate arm.
**The tell question is a separate instrument**, `py -3 -m eval.durf_reveal_order
<record>.json`, no GPU; reveal-ahead is a COUNT and must never be promoted into a
gate or into the quality rubric the rung still lacks.

## Session slices - what one `/new` should take

A slice is one session's worth, with an entry condition, ending in a thing that
exists. **Take exactly one.** Slice numbers are IDs, not positions, and are never
renumbered. **The live table is empty 2026-09-02** - every slice S1-S36 is struck and
annotated in `docs/slices.md`. The next slice is cut from the rows below when one
earns a session; a cold session picks up the merge list and the frozen prompt
arms first. The split that matters is GPU-bound versus attention-bound: a run
needs a launch and a log tail, not a session watching it, so a slice with a run in
it launches first and spends the wait on a CPU slice. **While a run is in
flight**, the standing menu is `docs/open-arms.md` §While the card is busy - an
instrument scored against records that already exist costs nothing and can
outrank the run it waits on.

**Direction, called 2026-08-27** and argued in `docs/open-arms.md`: gate #1
measures parlor and is durable, gates #2 and #3 measure a MODEL and decay with the
next checkpoint, and nothing built so far de-risks the product claim - so the next
spike is the **adjudicator** against 3-4 discretion-heavy characters. **Taken
2026-09-02 as belfry's first
PLAY-TIME discretion arm** - the false count a switched-off gauge is told, held
across nights. Both reads landed the same day, COHERENT supplied and COHERENT and
NEEDS MEMORY with `prior` withheld (`docs/measurements.md`). **The third arm both
reads end by naming is READ 2026-09-03** - NO RECALL, and the belfry row below
carries what it left.

**Gate #3a is RETIRED and gate #3b is NOT SHOWN, and nothing below reopens
either.** Read `docs/gate3a-retired.md` before restarting any cabal run.

## The merge list

**One list, and rows do not carry branch names.** A branch cannot touch the
checkout the chain imports from, so "no changeling arm in flight" is met on a
branch and the freeze binds only the MERGE. **The chain READ 2026-09-03, so no
freeze binds and every row below is merge-ready on its conflicts alone.**

No head sha: a copied sha is what goes stale, and a merge takes a name.

| branch | what it carries |
|---|---|
| `slice/changeling-source-rules` | the night rules - merge condition MET on the branch |
| `slice/changeling-notebook` | `--notebook` |
| `slice/fanout-s21` + `slice/fanout-s21-demo` | `--briefing`, arm then console |
| `slice/fanout-s27` + `slice/fanout-s27-demo` | `--turns random-active`, arm then console |
| `slice/fanout-simul` | `--turns simultaneous`, sits over S27 |
| `slice/fanout-replies` | the parser's complaints - **supersedes `slice/fanout-neg`**, which it sits on |
| `slice/fanout-heartbeat` | belfry `--heartbeat` |
| `slice/fanout-print` | the stale pack reference prints a labelled absence |
| `slice/fanout-wolf` | `--theme werewolf` |

**Order is forced by the controls:** every prompt arm pairs against S22's
`cl-rounds2.json`, so it must merge AND RUN before the source-rules merge
re-baselines the rung, or its pair is void. Which arm earns its ~7 h of card
first is the operator's ranking; the criteria are frozen and wait.

**GPU order was decided 2026-09-02 and RE-RANKED the next day.** The 09-02
reasoning is `docs/decisions.md` §GPU order for the frozen changeling arms and
is not restated here; what binds is the line below.

**Re-ranked 2026-09-03** (`docs/decisions.md`): the partner arm takes slot 3 and
notebook slips to the deferred group, so the pre-merge set is mixed-pack, briefing,
partner (~12 h). Partner's effect has been observed twice against an 8.7-point MDE
where notebook has a prediction and no observation, and it closes the honesty debt
of two unadjusted free reads published with no pre-committed test. It runs BEFORE
the merge, which would leave its numbers readable while changing what they
replicate.

**Two conflict pairs are foreseen, each with a required order.** In
`games/changeling/referee.py` simul rewrites the turn machinery source-rules also
moves: merge source-rules FIRST, then rebase simul onto it and re-run its 20-seed
byte-identity pins, which are what would catch a silent drift. In
`games/changeling/player.py` replies threads `complaints` through `parse_action`
where s27 and simul both edit the discussion path: re-run the replies golden
sha256 after any merge touching `parse_action`. The demo pair conflicts on one
argparse block and is trivial.

## The queue

Open rows, unordered - the slice section above is what ranks them. **The reasoning
behind each is `docs/open-arms.md`; read the entry before taking the row**, and
the reference each names is indexed in `docs/README.md`. A second index here is
the one that goes stale.

- [ ] **Run the partner arm - the pack statistic, PRIMARY, on fresh seeds.**
      Two unadjusted free reads on two different axes both landed on the partner
      vote and neither pair's primary could see it (`docs/measurements.md`: the
      skin pair 2026-09-02, the rounds pair 2026-09-03). The criterion is
      WRITTEN - `docs/changeling-partner-criterion.md`, one arm on fresh seeds
      17000.., ~5 h - and the tool and recipe are written. What it owes is the
      card, and it must run BEFORE the source-rules merge, which would leave
      every number readable while changing what is replicated. The axis question
      - which of name form or round count causes it - is deliberately NOT in it:
      four arms split 2-2 and no single variable separates them, so that is a
      later pair against this arm's record.
- [ ] **The same-seeds folk-vs-greek vocabulary read lapsed on 2026-09-03, and
      needs fresh seeds now.** Two criteria built the door and neither walked
      through it: the skin pair's §"What this does NOT compare" says a folk-vs-greek
      read "needs its own folk arm on these seeds under HEAD - a separate row, a
      separate criterion", and the rounds pair's §Settings put its two-round `folk`
      arm on seeds 5000..5199 for exactly that, with one condition - the vocabulary
      criterion "is written before that arm is read, never after." The greek arms
      were read 09-02 and `cl-rounds2` printed its own blind accuracy at 05:38 on
      09-03. No such criterion exists in `docs/`. **The seeds are spent**; the read
      is still worth having, but it costs a fresh folk arm and a fresh greek arm on
      new seeds, ~10 h, not the zero it was priced at. Cheaper alternative first:
      decide whether vocabulary is worth 10 h at all, given the skin pair showed
      NOT SHOWN on the name-form axis. The general lesson is the row that matters -
      **an arm that doubles as a future control has a criterion deadline, and the
      deadline is the moment the arm's own report prints.**
- [ ] **`slice/transport-retry` is not on the merge list, and it re-solves a
      `core/` problem main solved a different way.** Found in the 2026-09-03
      triage; nothing in this file has ever named it. Four commits, 971
      insertions: a whole unlisted rung `games/bureau/` (deal, referee, session
      and three test files), a shared rate budget so a transport stall does not
      kill a rung, edits to `games/durf/facts.py`, and
      `refactor(core): find_leaks keys a secret to any hashable, not a seat` -
      which is a SECOND, independent generalisation of the key that `ed6bf11`
      generalised this morning. It conflicts in exactly those two files,
      `core/observability.py` and `core/test_observability.py`. Two branches
      solved the gate #1 primitive apart and neither knows about the other, so
      neither is trustworthy until one is chosen. Done when the two keyings are
      read side by side and one is kept; **not** by merging and resolving, which
      would pick a winner by textual accident in the repo's most load-bearing
      primitive.
- [ ] **No criterion states the effect it EXPECTS, only the one it could see.**
      Every measured changeling pair is NOT SHOWN and each predicted it would be:
      resolution ~9-10 points at 200 games, observed prompt effects 1-3. The only
      arm that INFORMED swapped a whole policy. Argument, the real counter and
      the one cheap fix: `docs/open-arms.md` §Is the changeling arm program
      powered. Done when a criterion must name its expected effect before launch.
- [ ] **`docs/README.md` is the merge list's standing collision point.** 195
      lines against its 150 advisory as of 2026-09-03, and it conflicts on seven
      of the nine unmerged branches, because each adds its criterion to one flat
      index. The advisory is not a block and the per-merge resolution is cheap,
      so this is a row about whether the flat directory still pays: the other
      three triggers and the split that would follow are `docs/decisions.md`
      §This directory stays flat. Done when the ceiling is met or deliberately
      raised with a reason.
- [ ] **The per-game JSONL is opened in APPEND mode and the summary beside it
      is TRUNCATED.** `core/runlog.py` hands out both paths and
      `eval/run_changeling.py:437` appends each game, while the summary is
      written `"w"` - so a second run onto an existing record path stacks a
      block, and the two files then describe different populations with nothing
      raising. Three records are already in that state: `cl-heuristic`,
      `-pack` and `-village` hold 3000 lines for 1000 games. **The first block
      of `cl-heuristic.json.jsonl` is a stale play of the same seeds at 71.55%
      pack wins against the published 56.09%**, so a naive read of that file
      blends to about 61% - plausible, five points off. No published number is
      affected (`docs/measurements.md`'s 77.36% and 49.26% both reproduce from
      the deduped read). `eval/mixed_verdict.py` dedupes to the last write and
      checks the recovery against the summary's own counts, but that is one
      scorer defending itself; every other tool reading a `.jsonl` is exposed.
      Done when a re-run onto an existing record path cannot silently stack -
      the recipes' `if exist` guard is the only thing standing between this and
      a wrong published figure, and it is per-recipe prose, not a property of
      the writer.
- [ ] **Find what writes a stale `.git/index.lock` in this repo.** 2026-08-28: a
      0-byte lock at 08:44, no `git.exe` running, blocked a commit 40 minutes
      later with the index intact. An unattended run that commits its own records
      would have died on it silently. Cheap probe: log the lock's ctime against
      the tool-call transcript next time. Done when the writer is named.
- [ ] **Gate #2 has a cheaper falsifiable design than waiting on gate #3** -
      `--arm llm` vs `--arm llm-good` on the same seeds, using arms that exist, and
      `rate_ok`'s 5% CI-floor bar is pre-declared nowhere. **The changeling twin is
      READ 2026-09-03 and INFORMS** (`docs/measurements.md`, criterion
      `docs/changeling-gate2-pair-criterion.md`): the live pack costs itself 17.9
      points against the same live village, and its named free read says the
      village deduces WORSE against an unreadable pack. **The mechanism is
      untested and is what survives as a row**: the arm moves the whole pack
      policy at once, so "speech is evidence" is a reading, not a finding, and
      separating speech from votes is a new pair with a criterion of its own. The
      cabal half is parked with cabal's GPU program.
- [ ] **Merge the changeling source rules when the campaign chain has read.**
      The cabal half, the evil conference before the hunt, LANDED 2026-09-02 and
      re-baselines cabal (`docs/measurements.md`). The changeling
      half - a lone `pack` views one centre card at MEET, an `identity`-class
      reveal that moves the strata and the chance baseline. **Every blocker has now
      CLEARED**: the gate #2 arm, the skin pair and S22 are all READ
      (`docs/measurements.md`), and the merge condition was already met on the
      branch - the control never declines and the guard is mutation-checked.
      Merging re-baselines the rung and the RULES.md notes flip then. What
      remains is the ranked arms that must run first, then the merge, then
      re-measure the bar. **Its one conflict is TEXTUAL and resolved in advance**
      (trial merge 2026-09-03, discarded): one hunk in `night.py`, the branch's
      `PASS` constant adjacent to the `MAX_DEAL_ATTEMPTS` comment main rewrote
      for deck B; the two edit different functions and 386 tests pass with both.
      Keep the `PASS` block, keep main's comment. Kindred re-bars AFTER the merge
      (`docs/decisions.md` 2026-09-02); nothing here needs a decision.

Measured prompt arms - same seeds, one variable, reported beside both fallback
rates, landed between campaigns rather than into one. Every one is FROZEN and
unlaunched, and waits on the merge list above:

- [ ] **Negation pass over the model-facing strings.** Seventeen strings in two
      tables behind `--phrasing positive`, each default pinned to a hash computed
      before its table; one run against `cl-rounds2`, PRIMARY statistic the refusal
      rate. `docs/changeling-phrasing-criterion.md`, `eval.phrasing_pair_verdict`.
      **The replies branch supersedes the negation branch** - it adds the parser's
      complaints and pins the other four games through their own parse paths. Found
      in wiring it: `Phrasing.retry` had a golden hash and no consumer, so the
      positive arm was shipping the as-is retry sentence.
- [ ] **Does the standing frame belong in the PAYLOAD? `--briefing` (S21).** The
      frame is 553 bytes on a 1620-byte render, off by default and byte-identical
      off. **It renders inside `seat_lines`, never `preamble`**: measured, a leaky
      frame placed in the preamble escapes gate #1's per-seat scan and is caught
      from `seat_lines`. That is the rule for every standing-context arm.
      `docs/changeling-briefing-criterion.md`, `eval.briefing_pair_verdict`, one
      arm against `cl-rounds2`. Playable at the console on its demo branch, which
      moves no model-facing byte, so the criterion still binds.
- [ ] **A per-seat private notebook.** Promoted to `core/notebook.py` (two games
      needed it); `--notebook` on the changeling runner, notes stamped by round,
      off by default and byte-identical off. Criterion
      `docs/changeling-notebook-criterion.md`, one arm against `cl-rounds2.json`,
      recipe `eval/runs/changeling-notebook-arm.cmd <log>`, read
      `py -3 -m eval.notebook_pair_verdict`. Must RUN before the source-rules
      merge. Nothing quotable until it has.
- [ ] **Turn-taking is two arms, not one.** `--turns random-active` (S27) makes a
      round a budget of n turns, the floor drawn with replacement from the seed's
      own stream and the active seat offered an idle `listen`. `--turns
      simultaneous` withholds a round until it closes, then publishes it in seat
      order, so an agreement is one the seats reached apart - a different axis, not
      a stronger random-active. `docs/changeling-turns-criterion.md`,
      `eval.turns_pair_verdict`, TWO pairwise differences against `cl-rounds2`, no
      arm-vs-arm and no multiplicity correction, stated before the runs; the shared
      control means a void on `cl-rounds2` takes both. Round-1 agreement is a
      required free read, because the effect can only live there. Both are playable
      at the console on their demo branches. Cabal's own `--simultaneous`
      stays built and unmeasured - two rungs, two criteria, never one. Free with
      this row: **the salience line has no measured benefit anywhere and is a
      removal candidate**, on cabal, its own arm.
- [ ] **Seat the heuristic against the MODEL.** Two arms over the heuristic rung,
      `mixed-pack` then `mixed-village`, the suffix naming the LIVE side;
      `docs/changeling-mixed-criterion.md`, recipe `eval/runs/changeling-mixed.cmd
      <predecessor-log>`. **`mixed-pack` runs first, swapped before launch** - it
      closes the artifact read and is the cheaper arm, so a card with time for one
      gets the informative one. The criterion carries the two calls inside it: a
      control rescored over its own first 200 seeds, and a void bar read off the
      LIVE side's own fallback rate rather than the run's. Found in doing it - the
      guard tested `startswith("llm")`, which a `mixed-` arm passes, so 200 games
      would have scored the random policy. Reads against the artifact warning in
      `docs/measurements.md`
      §Measured first. Runs BEFORE the source-rules merge or its twin figure comes
      from a different game.
- [ ] **Theme as an experimental variable, not a default to fix**
      (`docs/moral-framing.md` owns the arm ladder). **A blurb is a prompt** - the
      four English faces are frozen at 53 words and an edit orphans what was
      recorded against them; `1984-en` stays cabal's face on every committed
      transcript. The `greek`/`greek-named` pair LAUNCHED 2026-09-02 under
      `docs/changeling-skin-pair-criterion.md`; the other four stay unrun, and a
      werewolf-vocabulary face is BUILT and unrun on the merge list. **That face is
      the WHOLE answer to public legibility**, which is why a vanilla Werewolf RUNG
      is not worth building (`docs/open-arms.md`). Read the `1984-cn` arm
      FALLBACK-FIRST: non-English play surfaces as a fallback rate, not as worse
      deduction, so a CN arm voiding on the 10% rule is a finding.

Runs that are frozen and want card - and one that is already in the chain:

- [ ] **Run `kindred` deck B - FROZEN 2026-09-02, NEVER RUN.** `SETUP_7_KIN`
      with `require_seated_kin`, `--seats 7`. Bar measured (blind 25.39% over
      5376 random votes, `eval/records/kin-chance.json`) and the criterion is
      `docs/changeling-kindred-criterion.md`; recipe
      `eval/runs/changeling-kindred.cmd kin1 200 14000 qwen36-35b-a3b-iq3`, ~7 h.
      **Entry condition MET 2026-09-03** - nothing is in flight. It still runs
      after the source-rules merge and re-bars first (`docs/decisions.md`). A new
      deck re-baselines everything under it.
- [ ] **The own-transcript arm sits BELOW the withheld arm, and no criterion has
      a verdict for that.** READ 2026-09-03 (`docs/measurements.md`): COHERENT,
      NO RECALL, BELOW SUPPLIED, all three pre-committed and clean. The unheld
      part is the direction - handing the referee its own transcript looks worse
      than handing it nothing, on non-overlapping intervals - and the criterion
      defines only RECALLS / NO RECALL, so it is an observation, not a result.
      **The population explanation is now CLOSED, 2026-09-03**: the extra 59
      pairs are genuinely deeper (29.8% at night 4+ against 18.9%) and depth
      genuinely costs coherence, but standardising either direction moves -15.7pp
      to -14.8pp / -14.3pp, so the deficit is INSIDE the strata. What that read
      also spent is the non-overlap: at the largest matched stratum the intervals
      touch, so an arm is the honest next move and the cheap CPU route is done.
      Not measured: any mechanism.
- [ ] **The adjudicator's record carries no ask SIZE, and that is where the
      transcript arm's mechanism lives.** Found 2026-09-03 in answering the row
      above. `ChoiceEvent` holds key, options, selection, fallback, recovered and
      upstream; player decisions have carried `prompt_size` and `reply_size`
      through `core/callcost` all along. So "is the transcript arm's ask longer"
      is answerable from the CODE - `choose(recall=True)` sends the whole
      accumulated session transcript, setup asks included, growing within a game
      - and from NO record, on either arm, past or future. Done when an
      adjudicator event carries the two sizes the player path already records.
      Cheap, `core/`-adjacent, and it is what would let the next transcript-class
      arm price its own ask instead of arguing it.
- [ ] **Spike #2 heartbeat is SEATED in belfry - `--heartbeat`, off by default,
      unmeasured.** No Phase, turn kind or ACTION_KEYS entry was needed: a tick is
      a night, taken at the top of `_begin_night`. What seating found, and how the
      audit's third scan is graded, is `docs/faction-heartbeat.md` §Seated in
      belfry, on the branch. Open, each its own row when taken: the rumour rule is
      LINEAR on a circular table, and at 5 seats most scheduled beats never fire.
      **Entry condition is the merge list, as first written.** The correction
      that stood here - that heartbeat is link 3 of the launched chain and runs
      ahead of the ranked arms - is FALSE, checked 2026-09-03 against
      `eval/runs/chain-tail.cmd`'s own argument list: the three legs are the
      rounds pair, the gate #2 arm and `belfry-night-transcript.cmd`, no recipe
      in the tree passes `--heartbeat`, and the flag is not on main. It was the
      belfry session-memory row's slot, read onto this one.

Human-seat play, triaged from one hand-played session 2026-08-29. Nothing here is
measured. Which of it may be handed to a worker is S12 and `docs/worklane.md`.

- [ ] **"q36 is terse and robotic" is a claim about a model, and there is no
      bench.** RP tunes against `ablx` and q36, on ONE parlor-shaped question:
      whether fallback rate and deduction move together or apart. **Each tune is
      TWO arms** - gate #2 is unreadable without that tune's own gate #3 control.
      Candidates, the two corrections to them and the one candidate already
      measured: `docs/open-arms.md` §The RP-tune bench. **Entry condition: the
      source-rules MERGE, not an idle card** - every frozen arm pairs against a
      control recorded on q36, so a re-arm before those run voids them.
- [ ] **Changeling: respond to measured randomness.** Four levers and their order:
      `docs/open-arms.md` §"changeling feels random". Every rules or prompt change
      re-baselines this reading. The heuristic rung (`docs/scripted-rungs-cabal.md`
      §0) is MERGED 2026-09-03 and says what un-random looks like here; the mixed
      arms read it against a live seat and are the run this row now waits on.

- [ ] **Build the Paranoia-shaped rung, branding-free** - called 2026-09-03 and
      the pre-committed falsifier did NOT fire, `docs/decisions.md`. **The gate #1
      half is DONE, 2026-09-03**: `find_leaks` takes a `(seat, axis)` key, so one
      seat's several secrets are entitled separately, and seat-level entitlement
      still covers every axis (`core/test_observability.py`, both branches
      mutation-checked). The rung inherits it and owes no `core/` change. What was
      actually wrong is narrower than this row claimed - tuple keys already
      discriminated; what they lacked was the self-skip and the seat-level grant,
      whose absence reports the VIEWER'S OWN secrets at a game that adopts axes and
      pushes it back to the flat seat key where the false negative lives.
      Functional keys only - the setting, its role names and its text stay out of
      the tree. Done when a seat holds four orthogonal secrets and the audit
      distinguishes them.

- [ ] **The play lane, after session 0.** The draft is BUILT and RUN
      (`docs/measurements.md` 2026-09-03); what is left is the scene loop and the
      economy-compliance read, neither of which has a rubric yet. Still not
      sequenced against the Paranoia rung.
Publishing:

- [ ] **Obtain the paywalled theory chapter before publishing anything about gate
      #1** - the one result that could bound gate #1's shape, and two published
      hybrids are in the same debt (`docs/open-arms.md`). **No public claim about
      gate #1 until it is read**, and done when a copy is in hand.
- [ ] **The thesis moved on 2026-08-27** - `README.md` leads on the product claim,
      the off-repo positioning argument still leads on the research one. Reconcile
      them **in the off-repo file, not here**. Done when the two name the same
      leading framing; the failure to avoid is a stale copy that disagrees.
- [ ] **Code debt, item 3 only** - adopt a **termination-depth diagnostic**
      against the published threshold the off-repo ledger records, with that
      citation. Gated outside the tree; it held up nothing and still does not.
      **Entry condition: no arm in flight.**
