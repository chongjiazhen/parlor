# The queue - open work

Queue only. Done work leaves - **delete the row.** What stays is the ask, its
entry condition and what done looks like; the argument behind a row lives in
`docs/open-arms.md`. The budget is bytes and the pre-commit gate ratchets it -
read it before writing a row, not by failing it:
`sh scripts/hygiene-check.sh --budget`.

**One exception, the slice table: a finished slice is struck through and
annotated, never deleted**, because live rows cite slices by name. The struck
rows live in `docs/slices.md`, out of the read a cold session pays for.

## Cold start

**First command of any session that thinks a run is live:**

```
grep -L 'PARLOR DONE' eval/records/*.log   # names every run still in flight
```

Narrow it to a campaign's own arms when you know them, and exclude the files
that never carry the marker - `hunt6[ab]`, not `hunt6*`, which also matches
`hunt6b-chain.log` and so reads "in flight" forever. **Never judge a run by a
process probe.** Most of what it names is a fossil and no count of them is worth
writing down: the marker landed in S4 (2026-08-27, `core/runlog.py`), so every log
written before it lacks it permanently. Read the answer against
`queue.local.md`'s launch record, which names each one, and treat a name it does
not list as a pre-S4 fossil rather than a run.

**No progress figure, ETA or log-tail path is recorded here** - a count written
into a queue file about a running job is stale the hour it is written, and an ETA
in this block was wrong twice on 2026-08-27. That class lives in
`queue.local.md` (gitignored, box-local); this file keeps terminal states and
route decisions. Whether a freeze binds right now is its business too.

## What each rung owes

One debt per rung, and **this table is the only place that state lives** - a
second copy is the one that goes stale. The verdict table below is what has been
CALLED; this is what is left. `GLOSSARY.md` defines rung, arm and void.

| rung | engine | model in a seat | what it owes |
|---|---|---|---|
| **cabal** | done | yes | nothing runnable. Its GPU program stopped at gate #3b and its live arms re-homed to changeling, so the rows it still holds (evil over-sabotage, the 6/7p package) are parked on that, not on work |
| **changeling** | done | yes - gate #3 HOLDS on BOTH decks (S5 five-seat, S19 six-seat waker) | the `waker` deck is seated, read, and its own question is ANSWERED - against the like-for-like `identity` set the waker seat's advantage does not clear zero (`+6.96% [-2.11%, 15.98%]`), so the deck shows no evidence that knowing your OWN card beats knowing a card. **Not shown, not no**: 122 waker votes is the one-vote-per-game ceiling the criterion named. Settling it needs a NEW criterion - a longer arm or a deck seating two waker-class cards - never a re-read of these records. `kindred` deck B is still paper and needs `require_seated_kin` |
| **quorum** | done, and the live4 arm READ 2026-09-01 | **never** | nothing runnable. Both clauses INFORM - proposer 74.04% [64.86%, 83.16%] vs an exact 25.00%, enactor 69.52% [64.29%, 75.53%] vs 33.33%, over one fallback decision in 2582; `docs/measurements.md`, read that before citing either. Seeds 11200..11219 now spent alongside 5200..5599 / 7000..7399, so a fifth arm needs fresh ones and a criterion of its own. The repeat-claim void has still never fired |
| **belfry** | done, scoring lane, control instrument, sampled-player arm, S8 referee read, and the live2 arm READ | **never** | S8b is DISTINGUISHABLE and live2's Clause A INFORMS at 20.34% [13.77%, 27.01%] over 1.28% fallback - both in `docs/measurements.md`, read that before citing either. Clause B spans chance and no second arm chases it. S29's adjudicator retry LANDED 2026-09-01 and did NOT re-baseline S8b - that record fell back 0/20, so it holds no call the retry could have changed, and S29 CLOSED the same day on the finding that no arm will carry `recovered > 0` (`docs/decisions.md`). The retry is verified by test, and the rung owes no run for it |
| **DURF** | done | yes - gate #1 91/100, then 99/100 under the topology edits | a term decision and two questions that are not code, all three in §The three DURF questions. The adjacency question is DECIDED, its edits APPLIED, its campaign LANDED |
| **adjudicator** | S8b read | referee only | 88.89% held-out source accuracy clears 70.97% Wilson chance ceiling; bounded trace difference only |

**Do not mix cabal and changeling in one session.** Separate `RULES.md` files,
separate scorers, separate baselines - every number confusion in this file so far
came from carrying one game's intuition into the other's denominator.

## The three DURF questions that are still open

- **`hidden catch`, camp1's term**, colliding with ordinary searching prose
  exactly as `loose flagstone` did - the model chose the words. Deliberately
  unfixed: scoring it as a hold gives 90/100 and moves no verdict, and the edit
  voids its own read. camp2's structural pair is CLOSED. **Deciding it does NOT
  oblige a re-run** - the 91/100 is a dated read under its own term set and stays
  quotable as that. Change the term, mark the read as scored under the old set,
  and run again only when something else is worth measuring with it.
- **Movement is deliberately still unconstrained by the exit graph.** `call_move`
  accepts any room, so the party can go R1 to R4 in one call. Making it respect
  adjacency is a RULES change - it moves what is legal and therefore what the
  fallback rate counts - and it would be a second variable in the same campaign.
  Separate arm.
- **The tell question is a SEPARATE instrument and must not be folded back in.**
  Substring matching cannot see a referee that names the object of its own
  undeclared secret without naming the secret (`docs/action-channel.md`).
  Relatedly, reveal-ahead is a COUNT, not a gate, and gate #1 must not be changed
  to catch it - declaring is the referee's authority, so the audit is correctly
  silent. Instrument `py -3 -m eval.durf_reveal_order <record>.json`, no GPU.
  There is still **no rubric for whether a refereed session was any GOOD**, and
  the reveal-ahead count must not be promoted into one.

## Session slices - what one `/new` should take

These are the units: each is one session's worth, has a stated entry condition,
and ends in a thing that exists. **Take exactly one.** They are ordered by what
unblocks what, so **the numbers are IDs, not positions**; live rows cite slices
by name, so do not renumber them. **Only live rows are below**; every struck
and annotated slice is `docs/slices.md` - S1-S19, S23, S29-S36 today.

The split that matters is GPU-bound versus attention-bound. A GPU run needs a
launch and a log tail, not a session watching it - so an S with a run in it
should launch first and spend the wait on a CPU slice.

| # | slice | judgment | worker | entry condition | done when |
|---|---|---|---|---|---|
| **S20** | **Changeling notebook arm.** Port or reject per-seat notes for this rung, with entitlement audit and paired-arm recipe. | judgment | codex | no changeling arm in flight | model-facing change is isolated, audit holds, recipe freezes comparison |
| **S21** | **Changeling briefing arm.** Add full standing briefing only as an off-by-default paired arm. | judgment | codex | no changeling arm in flight | one-variable recipe, audit proof and both fallback-rate fields |
| **S22** | **Changeling discussion-length arm.** Bind one extra discussion-round comparison without changing deck, wording or scorer. | judgment | codex | a post-S14 baseline/criterion exists | paired recipe and criterion, ready to launch |
| **S24** | **Off-map faction heartbeat spike.** Build the typed-fact entitlement-snapshot probe scoped in `docs/faction-heartbeat.md`. | judgment | codex | no arm in flight | deterministic tick schedule, one audited render and explicit result |
| **S25** | **Group-sequential campaign design.** Pre-commit alpha spending and stop boundaries for next campaign. | judgment | codex | target metric and candidate campaign named | criterion document and recomputation test; no old record re-read as sequential |
| **S26** | **Solver-seat control read.** Measure SolverPolicy versus random only where its entitled VOTE evidence can differ; no model and no cabal gate reopening. **Blocked on an instrument gap:** `SolverPolicy` defers to its fallback for every non-VOTE phase and every mixed posterior, and those draws route around `LLMPolicy`'s counter - so `--arm solver` reports `0.00%` fell back over 429 decisions most of which WERE random, and the gate prose calls the arm "played at random". The mechanical-vs-deferred split has to be counted before the read means anything. | judgment | codex | `--arm solver` runs - **met**; deferred-decision count does not exist | control recipe, result, the mechanical/deferred split, and fallback rate, scoped as policy evidence |
| **S27** | **Turn-taking active-seat design.** Specify random-active-seat plus non-advancing idle action as one isolated changeling arm. | judgment | codex | no changeling arm in flight | criterion, exact payload delta and audit tests |

**Direction, called 2026-08-27 against the literature** (argument off-repo): gate
#1 measures parlor and is durable; gates #2 and #3 measure a MODEL and decay with
the next checkpoint. Nothing built so far de-risks the product claim, "a referee
that oversees without micromanaging" - so the next spike is the **adjudicator**
against 3-4 discretion-heavy characters, not a whole roster, and not Secret
Hitler, which is cabal's rung again. **While a run is in flight**, the standing
menu of what a session can still do is `docs/open-arms.md` §While the card is
busy; its reusable half is that an instrument scored against records that already
exist costs nothing and can outrank the run it waits on.

**Gate #3a is RETIRED and gate #3b is NOT SHOWN, and nothing below reopens
either.** Read `docs/gate3a-retired.md` before restarting any cabal run.

## The queue

Open rows, unordered - the slice table above is what ranks them. **The reasoning
behind each is `docs/open-arms.md`; read the entry before taking the row.**

**Reference lives in `docs/README.md`**, which indexes every one of these and
is maintained as an index. A second list here is the one that goes stale.

Instrument and integrity: the 2026-09-01 review of `2d28e60..HEAD` is CLOSED -
all seven findings landed. Its rows are gone; git holds the record.

- [ ] **Find what writes a stale `.git/index.lock` in this repo.** 2026-08-28: a
      0-byte lock at 08:44, no `git.exe` running, blocked a commit 40 minutes
      later with the index intact. An unattended run that commits its own records
      would have died on it silently. Cheap probe: log the lock's ctime against
      the tool-call transcript next time.
- [ ] **Two behaviours the auditor prices, neither of them bugs** - a good seat
      approving a known-tainted team (7/76) and evil over-sabotaging. The
      consequence that matters is for gate #3a's metric, not for the seats.
- [ ] **Gate #2 has a cheaper falsifiable design than waiting on gate #3.**
      `--arm llm` vs `--arm llm-good` on the same seeds, using arms that already
      exist. Also: `rate_ok`'s 5% CI-floor bar is pre-declared nowhere.
- [ ] **Group-sequential design instead of a pre-committed fixed N.** Alpha
      spending, not "don't look". **It must be designed BEFORE the next
      campaign**, never retrofitted to S6's records - that would be the peeking
      it exists to prevent.
Measured prompt arms - each is same seeds, one variable, reported beside both
fallback rates, and landed between campaigns rather than into one:

- [ ] **Negation pass over the model-facing strings** (rule:
      `.claude/rules/model-facing-text.md`, path-scoped). Steering by prohibition
      makes the banned behaviour more available; three live prompts do it. The
      referee's hard refusals stay. **UNBLOCKED 2026-08-28.** Re-homed to
      changeling (S1).
- [ ] **Does the standing frame belong in the PAYLOAD? A `--briefing` arm.** The
      per-phase drip is deliberate and unplayable for a person, which is why the
      console got a `BRIEFING` outside the payload. Expect a
      capability-dependent sign. **ABSENCE is the novel arm** - every build read
      from source states full rules in the system prompt and none ablates that.
      **Done when** a paired arm exists.
- [ ] **A per-seat private notebook - BUILT 2026-08-26, UNMEASURED.**
      `--notebook`, off by default. Gate #1 holds by construction and the audit
      says so. Nothing about it is quotable until a paired arm exists.
- [ ] **Theme as an experimental variable, not a default to fix**
      (`docs/moral-framing.md`). Re-homed to changeling at 1/26th the GPU cost;
      `1984-en` stays cabal's face on every committed transcript. Arms built
      2026-08-27, unrun. **A blurb is a prompt** - all four English faces are
      frozen at 53 words and an edit orphans what has been recorded against them.
- [ ] **Candidate changeling skins - BUILT 2026-08-27, ALL UNRUN.** Design owns
      the arm ladder: `docs/moral-framing.md` §The changeling skin set. Open is
      which arm gets GPU first - the `greek`/`greek-named` pair is the cleanest
      single-variable manipulation in the repo.
- [ ] **The `1984-cn` language arm is less novel than it looked**, and prior work
      predicts its confound: non-English play surfaces here as a FALLBACK RATE,
      not as worse deduction. Read that arm fallback-first; a CN arm voiding on
      the 10% rule is a finding, not a failed run.
- [ ] **Mini-personas** as per-seat judgment biases, assigned from the seed and
      recorded so the scorer can split by persona. Trigger: only if a table that
      argues from evidence still votes identically. Re-homed to changeling (S1);
      its trigger was never met on cabal.

Rules and setup changes, each of which re-baselines what runs under it:

- [ ] **Evil over-sabotages** - 41% of sunk missions hand over the pair for free.
      **Two fixes, NOT one, and keeping them apart is the whole judgement:**
      (a) **disclose `need`** is a harness BUG - public rules information withheld
      from the ask - and lands unconditionally and alone; (b) **naming the partner**
      is a HINT and the one measurement on this exact move says it HURTS on q36.
      This is also a confound in gate #3a: expect discrimination to DROP, and
      that drop is a truer number.
- [ ] **Larger setups (6/7p) + the two information-degrading evils.** Package
      them - both only make sense at 3 evil seats. The roles landed 2026-08-27 as
      `LURKER` and `STRAY`; nothing deals them, so what is left is the setups and
      the measurement, which was always the cost. **Worth it for what they
      degrade about INFORMATION, never as a sampling fix** - a bigger table makes
      the thin denominator worse. Blocked only by cabal having no GPU program.
- [ ] **Seat the changeling expansion cards, which means picking a deck.**
      `kindred` and `waker` are implemented, skinned, resolved and tested;
      `SETUP_5` deals neither. Deck design is `games/changeling/RULES.md` §The
      decks that would seat them and is the source of record. **UNBLOCKED
      2026-08-28** (S10). **Route call: `waker` is the one worth a run** - it is
      told that the night moved it where every other seat must infer it, and its
      deck seats it in 62% of games, so one run carries its own control.
- [ ] **Ship a werewolf-vocabulary theme on changeling - and that is the WHOLE
      answer to public legibility.** Public-domain folk-game vocabulary (Mafia,
      Davidoff 1986), no branding question, on a rung already built. **This is
      why a vanilla Werewolf RUNG is not worth building** - same rung as cabal,
      plus elimination.

Human-seat play - triaged from one operator's hand-played session, 2026-08-29.
Nothing here is measured; the code claims are read from the files cited. Which
of them may be handed to a worker is S12 and `docs/worklane.md`.

- [ ] **"q36 is terse and robotic" is a claim about a model, and there is no
      bench.** Candidates offered: RP-tuned Anubis-mini-8B, Rocinante-X-12B,
      Rocinante-XL-16B, Cydonia-24B against untuned gemma, qwen36-35b-a3b,
      qwen3.8-27B and its MTP build. **Read the direction note first** - gates #2
      and #3 measure a model and decay with the next checkpoint. It earns GPU on
      one parlor-shaped question only: whether fallback rate and deduction move
      together or apart across tunes, which is what an RP tune is supposed to buy.
      Serial local lane; `--no-thinking` is a property of the rung, not the bench.
- [ ] **Let a seat choose to speak rather than be scheduled to.** The same ask as
      the turn-taking row above - bidding, or random active-seat with an idle
      action - and it should be taken as ONE arm with it, not twice.
- [ ] **Changeling: respond to measured randomness.** Four levers and their order:
      `docs/open-arms.md` §"changeling feels random". Every rules or prompt change
      re-baselines this reading. A changeling heuristic rung
      (`docs/scripted-rungs-cabal.md` §0) is still unbuilt and would say what
      un-random looks like here.

Spikes and unbuilt arms:

- [ ] **Spike #2: off-map faction heartbeat - SCOPED 2026-08-27,**
      `docs/faction-heartbeat.md`. **Not an alternative to the adjudicator spike;
      the small version of its hardest part.** Ticks are counted and the schedule
      derives from the game seed - a wall-clock actor voids the seed invariant.
      One new gate #1 failure and it is silent: audit a render against the
      entitlement snapshot taken when it was BUILT.
- [ ] **Seat the heuristic against the MODEL** - a table with heuristic and LLM
      seats, the arm that does not exist. Read the artifact warning in
      `docs/measurements.md` §Measured first: the all-heuristic arm's 99.5%
      hunter is a deterministic twin reading its own tell.
- [ ] **Gate #3 was never blocked on the table talk - that read was wrong.** It
      was model capability: identical prompts, -0.2% on the 12B against +66% on
      120B-class. `--simultaneous` is built and unmeasured; the salience line has
      no measured benefit anywhere and is a removal candidate.
- [ ] **Turn-taking has FOUR options, not two** - cabal's fixed order, the
      built-but-unmeasured `--simultaneous`, bidding for the right to speak, and
      random active-seat selection with a non-advancing idle action, which is the
      cheapest. Worth one paired arm if table talk ever needs to carry evidence.
- [ ] **Two shapes not to harden further before game #2** - cabal's `Phase` enum,
      the `action_prompt` if-chain, and `ACTION_KEYS`. `docs/action-channel.md`.

Publishing:

- [ ] **Obtain the paywalled theory chapter before publishing anything about gate
      #1.** The one result that could bound gate #1's shape; no free copy exists
      and the route is a request to its authors, drafted off-repo. **No public
      claim about gate #1 until it is read.** Two published hybrids are in the
      same debt, and both change what gate #3's number means to a reader.
- [ ] **The thesis moved on 2026-08-27** - `README.md` leads on the product
      claim, the off-repo positioning argument still leads on the research one.
      Reconcile them **in the off-repo file, not here**; the failure to avoid is
      a stale copy that disagrees with the README about which framing leads.
- [ ] **Code debt, item 3 only** - adopt a **termination-depth diagnostic**
      against the published threshold the off-repo ledger records, with that
      citation. Gated outside the tree; it held up nothing and still does not.
      **Entry condition: no arm in flight.**

## Where the rest of this file went

`queue.md` was 1200 lines on 2026-08-28 and 68 KB the same day, against its own
30 KB budget - most of it work that had already landed, or argument that is only
needed once a row is taken. The split is by lifetime, and **nothing was
rewritten**: every line is verbatim where it went.

- `docs/open-arms.md` - the reasoning behind the open rows above, and the
  standing menu for what a session can do while the card is busy.
- `docs/slices.md` - the closed slice ledger, S1-S7 and S9-S11.
- `docs/measurements.md` - §Measured, §Route, §Backend notes, and the three
  changes that re-read an old record differently.
- `docs/decisions.md` - settled calls, pre-committed criteria, and the three
  things recorded before they were measured.
- `docs/evidence-discipline.md` - what the successors reached.
- `docs/README.md` - the `docs/` index.
