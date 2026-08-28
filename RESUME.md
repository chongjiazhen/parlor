# RESUME - open work

Queue only. Done work leaves to git log - **delete the row**.

**One exception, and it is the slice table below: a finished slice is struck
through and annotated, never deleted.** Live rows cite slices by name - S6's
pre-committed criterion rests on "the baseline derived by S3", and four items read
"re-homed 2026-08-27 (S1)". Delete the row and those pointers dangle, which costs
more than the two lines it saves. Everything else in this file follows the rule
above.

What's next:

**Both gates are called, and both verdicts have left this file.**

| verdict | where it lives | recompute |
|---|---|---|
| changeling gate #3 **HOLDS** - 2026-08-28 (S5), 200 games | `games/changeling/RULES.md` §S2 read | `py -3 -m eval.s5_verdict` |
| its pre-committed criterion, as promised | `docs/changeling-gate3-criterion.md` | - |
| cabal gate #3b **NOT SHOWN** - 2026-08-27 (S6). cabal's GPU program stops | `docs/gate3b-verdict.md` | `py -3 -m eval.s6_verdict` |
| cabal gate #3a **RETIRED** - 2026-08-27 (S1), on arithmetic not budget | `docs/gate3a-retired.md` | `py -3 -m eval.gate3_arithmetic` |

**S8 was taken, in its cheapest honest form, and the first read is VOID.** The
DURF fixture has a scorer (`eval/durf_score.py`, `games/durf/`), and four runs of
`qwen36-35b-a3b-iq3` are on disk. The verdict and every number live in
`docs/durf-rung.md` §First run, §Second arm and §The temperature arm - **do not
restate them here**. The recipe is `eval/runs/durf-fixture.cmd` (burst-gated,
temperature 0.0, verified 2026-08-28 to reproduce the recorded t=0 arm
byte-for-byte); an arm is under three minutes.
The three things a later session has to know before it re-opens this:

- **The action channel is NOT what failed** - 0/60 fallbacks across all four runs,
  nothing sent back by the parser or the rules. This rung's design predicted
  free-text JSON's likeliest negative outcome was the channel collapsing on a weak
  backend. It did not, and that prediction is now answered.
- **A per-item story from these runs is not reproducible; only the rates are.**
  Same seed twice is byte-identical, and a seed change alone moves 23 of 48
  rulings. Quote counts, never an individual ruling.
- **The instrument voids on its own floor control**, which is derived from the
  fixture's labels rather than picked - so a fixture edit moves the bar with them.
  Both degenerate arms fail it by construction, which is what makes it a control.
- **An adjudicator seat should not inherit a player seat's temperature.** Measured,
  not argued: greedy decoding is byte-identical across seeds and buys ~9.5pp of
  decision-1 accuracy over the 0.8 default, which exists so a table's SPEECH
  varies. `Backend.temperature` is deliberately NOT changed - it is shared with
  both games and moving it re-baselines every recorded cabal and changeling number
  for a rung that is still void. Pass `--temperature 0.0` on any later durf run.

**S11 landed and the engine half is DONE - the rung now has seats, and gate #1
has its first read where a model is the referee.** Held in 3/6 sessions, 0/88
fallback. Everything about it is in `docs/durf-rung.md` §The session engine and
§The read - **do not restate it here.** Two things a later session needs before
it touches this:

- **THE OPEN DECISION WAS TAKEN 2026-08-28: RENAME. The work is queued and it is
  the head of the queue.** Two of the three leaks are the same line, where the
  character SEARCHES for a loose flagstone rather than being told one exists.
  `loose flagstone` collides with the ordinary vocabulary of searching a stone
  floor, and the invariant's remedy for a colliding term is to rename it and leave
  the matcher naive. **Drop that term from the fact, leave `shallow cavity` and
  `40 GP`.**
  - **Why this is a legitimate edit and the alternative is not.** The renaming
    argument holds without having seen any model output, which is what
    `docs/reference-policies.md` asks of an instrument change. The cost is
    symmetric in any case: choosing to KEEP the term once you know which lines
    tripped it is equally a decision made on the output, so both branches void the
    3/6 and neither is the free one. Once the cost is equal the choice rests on
    instrument quality alone.
  - **Do NOT simply re-run the six.** A clean version of that interval is still
    uninterpretable, so the re-run buys tidiness and no number. A session is ~23s,
    so a campaign large enough to quote is ~15 minutes of GPU. **Size it, state the
    criterion and what a result would MEAN before launching**, the way gate #3b was
    run, then run once and mark `durf-sess2` superseded. Pass `--temperature 0.0`.
  - **The tell question is a SEPARATE instrument and must not be folded back in.**
    The ambiguous line is evidence that catching a referee's PHRASING is a
    different measurement from catching a fact dump, and `docs/action-channel.md`
    already says substring matching cannot reach it. It stays an open problem in
    its own right.
- **`durf-sess1` is SUPERSEDED by `durf-sess2`** and its 21.18% recovered rate
  was a schema ambiguity in the parser, not the model. Quote sess2.

**The powers re-run LANDED 2026-08-28** and the accuracy gain it was run to settle
is banked: on identical deals and clean code, blind accuracy **+40.00pp** [+13.64,
+66.67] and villager accuracy **+23.81pp** [+4.55, +42.42], both floors clearing
zero where the 2026-08-27 pair's touched it. `games/changeling/RULES.md` §The public
rules text has to state what each card DOES.

**The two rule-error counts are CLOSED 2026-08-28, and the fall is NOT established.**
`eval/rule_errors.py` is the tracked instrument - definitions stated in its
docstring, scored off records already on disk, no GPU. On the clean pair, either
error **9.0% -> 4.0%**, a paired **-5.0pp [-10.5pp, +0.0pp]** over a 10k game
bootstrap: the floor touches zero, and the 2026-08-27 pair agrees in direction at
-4.5pp [-9.5pp, +0.0pp]. The old `-10pp [-18.3pp, -1.7pp]` and all four figures
behind it are retired in `games/changeling/RULES.md` §The two rule-error counts.
The powers text is still the right rules text - a public rules statement that omits
what each card does is wrong whatever the count says - but it no longer carries a
measured effect. **Then S8**, whose entry condition is met.

**First command of any session that thinks a run is live:**

```
grep -L 'PARLOR DONE' eval/records/*.log   # names every run still in flight
```

Narrow it to a campaign's own arms when you know them, and exclude the files that
never carry the marker - `hunt6[ab]`, not `hunt6*`, which also matches
`hunt6b-chain.log` and so reads "in flight" forever. **Never judge a run by a
process probe.**

**Most of what it names is a fossil, and no count of them is worth writing down** -
it only grows, and a number here is stale on the next run. The `PARLOR DONE` marker
landed in S4 (2026-08-27, `core/runlog.py`), so every log written before it lacks
the marker permanently: the `hunt20*`, `huntcloud*` and unsuffixed `cl-powers-*`
logs are all finished and all report as in flight. Read the answer against
`RESUME.local.md`'s launch record, and treat a name it does not list as a pre-S4
fossil rather than a run.

**No progress figure, ETA or log-tail path is recorded here** - a count written
into a queue file about a running job is stale the hour it is written, and an ETA
in this block was wrong twice on 2026-08-27. That whole class lives in
`RESUME.local.md` (gitignored, box-local); this file keeps terminal states and
route decisions.

**The CPU lane of the wait is SPENT - do not redo it.** The mechanical solver, the
corpus scorer and the heuristic rung are all built, tested and measured. Read
`docs/reference-policies.md` §Results and §The control ladder before quoting any of
it, and note the supersession inside: "captured is undefined" is about the
MECHANICAL arm only. **None of it re-specifies a gate.**

**Ten theme arms across both games are built and NONE has been run.** Whether a
freeze binds right now is `RESUME.local.md`'s business, not this file's - a
live-state claim written into a tracked queue is stale the hour it is written, and
this line used to carry a date to prove it. How a freeze is proved to have held
rather than argued: `docs/evidence-discipline.md`.

## Outstanding debt from the 2026-08-27 prior-work sweep

**The sweep is CLOSED and its output is off-repo, on purpose.** Seven lanes read
from source, sixteen items read the same day, and the ledger of what is still owed
a first-hand read lives with the raw notes it rests on. `CLAUDE.local.md` has the
path. **Do not re-import it, and do not re-run the search half.**

**Why it is out there:** that material names third parties, quotes their prose,
assesses their work and carries claims marked unread - four things a public MIT
tree carries risk for and gets nothing back from, and none of which the engine
needs to build or a user needs to run it. The scope rule is the invariant in
`CLAUDE.md`.

**Reading debt blocks only PUBLISHING**, so a session that is not publishing can
ignore it. The three rules the sweep cost the repo to learn - an unread entry may
carry no number and no distinction, and a copied figure records whose it is - are
in `docs/evidence-discipline.md` §Citing work nobody here has read, with the
ranking lesson beside them: a ledger ordered by lane inherits whatever the lane was
worth when it was written.

**Three things the successors reached, and the first two are in the S6 verdict.**
Stated in parlor's own terms; the sources are in the off-repo ledger.
- **S1's capability tell has been independently reproduced elsewhere** - a
  different game, a different model family, one agent scaled down across three
  sizes, win rate falling monotonically with parameters. parlor measured identical
  prompts at -0.2% on a 12B against +66% on 120B-class and drew the conclusion
  alone. It is no longer alone, and that is the argument for reporting gates #2 and
  #3 as dated snapshots rather than as parlor's result.
- **The nearest outside baseline on this task does not cover gate #3b.** It drops
  the role the hunter hunts, on purpose, to study detecting deception rather than
  producing it - so there is no hunt in it at all. The honest version is **3a
  only**, not the wider claim the ledger first recorded.
- **A fourth precedent for the `--notebook` null, and the oldest of them** - a 2024
  game-theoretic evaluation reporting that step-by-step and tree-search scaffolds
  do not reliably help. That prediction now rests on four results across two years.
- **One thing NOT to quote against it**: a large multi-round result shows memory
  producing real effects, but its memory persists ACROSS games where `--notebook`
  is per-seat memory WITHIN one. Different lever, different timescale; it neither
  supports nor refutes the null.

**Code debt - ONLY ITEM 3 REMAINS, and it is gated outside the tree.** The batch
landed 2026-08-28 across S9 (the integrity surface), S10 (changeling's knowledge
class) and S5 (the `--out` convention), so a reader has one sha per change rather
than a scatter. Done rows are gone; the struck 5 stays because the S6 slice cites
it. Three things a later reader has to know, because each re-reads an old record
differently:

- **`fallback_rate` is unchanged and keeps its name** - every record in
  `eval/records/` and every published summary quotes it, and both reproducers still
  agree with the recorded runs. What is NEW beside it, in `core/integrity.py` and
  shared by both games: a witnessed rate per seat-game, a `recovered` count for
  decisions the parser or the rules sent back and the model then got right, and a
  clean-game count. **Old records carry no `recovered` field and read as 0 - that
  is absence, not a measurement**, and a re-scored pre-S9 run must not be quoted
  for it.
- **changeling's knowledge class is keyed on what the seat was TOLD**, which
  re-baselines every recorded changeling number: a pre-S10 record's blind stratum
  is ~19% smaller than the night produced and its `identity` stratum is diluted by
  the same seats, so a figure quoted across the change answers two different
  questions. `py -3 -m eval.strata` prints both rules side by side and is where
  every stratum size in `games/changeling/RULES.md` comes from.
- **`--out` is the summary path VERBATIM and the JSONL is its sibling
  `{out}.jsonl`** (`core/runlog.py`, `record_paths`) - which is what every record
  already on disk is named, so settling it renamed one run's files rather than
  every run's. One test pins the two drivers TOGETHER: the defect was that they
  disagreed, and a test beside either one cannot see that.

**Entry condition for the remaining item: no arm in flight.**
`grep -L 'PARLOR DONE' eval/records/*.log`, silence means clear.

3. Adopt a **termination-depth diagnostic** against the published threshold the
   off-repo ledger records, with that citation. Gated outside the tree; it held up
   nothing and still does not.
5. ~~Fix the **scorer note** on the mis-specified statistic.~~ **CLOSED 2026-08-27,
   no code change.** The trigger required a third flat or RISING 1->2 leg in the
   blind taint table; arm 2's fell 6.8pp, the largest fall of the four runs (legs
   run +7.4, +0.2, -1.6, -6.8). Not a step, so `_blind_line` stands as written and
   `taint_sensitivity` needs no non-monotone caveat. Table in
   `docs/gate3b-verdict.md`. Kept as a struck row because the S6 slice cites it.
**Open question, undecided - turn-taking has FOUR options, not two.** cabal's
fixed seat order; the built-but-unmeasured `--simultaneous`; bidding, where seats
bid for the right to speak, so the measurement covers WHEN as well as what; and
random active-seat selection with an idle action that does not advance the clock,
which is the cheapest of the four. The last two are borrowed shapes, sourced in
the off-repo ledger. Worth one paired arm if table talk ever needs to carry
evidence.

**Three things to record before they are measured**, so none reads as a surprise
later:
- **`--notebook` should show no gain.** Three independent 2026 results on three
  different games report that reasoning and memory scaffolds do not deliver what
  they are assumed to; `--notebook` is one such scaffold. A null is the expected
  result, not a failed run.
- **The strawman answer is a scaffolding-ladder arm, not an argument.** parlor's
  bare seats are weaker PLAYERS than a purpose-built search-and-belief agent, and
  no framing changes that. Same referee, three rungs - bare prompt, prompt plus a
  carried belief vector, then determinized rollouts - reported as parlor's own
  curve. **Do not run a head-to-head against someone else's harness**: the ones
  surveyed are variously unlicensed, dependency-rotted or pinned to retired
  models, and a head-to-head then measures their rot rather than either player.
- **A neutral canonical key can mislead a model about STATE, and that is the cost
  side of the branding-free invariant.** Read outside this repo, not measured
  here, and no number attached to it: seats reading a state key by its everyday
  sense inferred the wrong thing about the game from it, and renaming that state
  fixed the reading; separately, an evocative role name drew threat assessment out
  of proportion to what the role mechanically did. Both cut the same way for
  parlor - branding-free keys buy the second effect and can lose the first. So a
  key that names a STATE rather than a role is a prompt variable, and renaming one
  is a MEASURED change on the same terms as a theme change, not a tidy-up. The
  invariant stands; what is new is that it has a cost worth watching for.

## Session slices - what one `/new` should take

The queue is two dozen open items and a cold session cannot rank them - and it is
deliberately not counted here, because a count in a queue file is wrong on the next
edit and nothing objects. These are the units: each is one session's worth, has a stated entry condition, and ends in a
thing that exists. **Take exactly one.** They are ordered by what unblocks what,
not by appeal - so **the numbers are IDs, not positions**, and S9/S10 sit above S2
because the code-debt batch re-baselines what S2 would record. Live rows cite
slices by name; do not renumber them to tidy the column.

The split that matters is GPU-bound versus attention-bound. A GPU run needs a
launch and a log tail; it does not need a session watching it. So an S with a run
in it should launch first and spend the wait on the paired CPU slice, and the
table says which pairs.

| # | slice | needs | entry condition | done when |
|---|---|---|---|---|
| ~~**S1**~~ | ~~Call cabal gate #3.~~ **CALLED 2026-08-27** - 3a abandoned at every table size, 3b gets one pre-committed 40-game campaign. Verdicts: `docs/gate3a-retired.md`, `docs/gate3b-verdict.md`. | - | - | done |
| ~~**S9**~~ | ~~Code debt, commit one - the integrity surface.~~ **LANDED 2026-08-28** - items 7, 1, 2 and 4 in one commit. `over_sabotage`'s docstring now states the benchmark as "the pair failed to find a convention"; the integrity block moved to `core/integrity.py`, shared by both games, and gained a witnessed rate per seat-game, a `recovered` third outcome, and a clean-game count. `fallback_rate` is unchanged and keeps its name - both reproducers still agree with the recorded runs. Seven guards mutation-checked, each killed by its own named test. | - | - | done |
| ~~**S10**~~ | ~~Code debt, commit two - changeling's knowledge class.~~ **LANDED 2026-08-28** - the class is keyed on what the seat was TOLD; a MEET card that met nobody is `none`, not `identity`. The pin was replaced, not deleted: `..._never_the_DAWN_card` keeps the half that still holds, beside `..._keyed_on_what_the_seat_was_TOLD` and the property itself. Four guards mutation-checked. Stratum sizes re-measured and now recomputable - `py -3 -m eval.strata` - which moves 2375 of 20000 seat-nights from `identity` to `none` and recovers ~19% of the blind stratum. Both expansion decks are unblocked. | - | - | done |
| ~~**S2**~~ | ~~changeling: clean re-run, then 200 games.~~ **BOTH HALVES LANDED 2026-08-28.** `PARLOR DONE rc=0 games=200/200 elapsed=18250s`, `--arm llm`, seed 4000, `qwen36-35b-a3b-iq3` at 100% attribution, 0.40% fallback. Records `eval/records/s2.json` + `s2.json.jsonl`. The powers half ran the same day: 2x20 on the fixed lane, identical deals, `PARLOR PAIR DONE rc=0 arms=2/2`, recipe `eval/runs/changeling-powers-pair.cmd`. The `RULES.md` powers table is on clean numbers and its caveat block is gone; the accuracy gain is banked. The two rule-error counts were the half it could not close; they were re-measured 2026-08-28 with a tracked instrument (`eval/rule_errors.py`) and the fall turned out not to be established. | - | - | done |
| ~~**S3**~~ | ~~cabal scorer honesty.~~ **LANDED 2026-08-27** - all four derived numbers now come from the knowledge model or the record. The bar for S6 is unchanged (`SETUP_5` legal set is 3, so the derived chance IS 1/3); the audit's role-outing count was near-zero by construction and is not. See the measured rows below. | - | - | done |
| ~~**S4**~~ | ~~Ops hygiene.~~ **LANDED 2026-08-27** - `core/runlog.py` writes `PARLOR DONE rc=N games=L/R elapsed=Ns` from both eval drivers; both games record a fallback's REASON per decision on a `refused` field; the untracked `run-hunt20.cmd` is retired and its exact invocation preserved in `eval/runs/hunt-local.cmd`. Records changed, play did not - the bytes a model receives are identical, so S6 may freeze on this code. | - | - | done |
| ~~**S5**~~ | ~~changeling: read the 200-game run.~~ **READ 2026-08-28 - GATE #3 HOLDS.** Blind villager accuracy **110/247 = 44.53%**, Wilson floor **38.47%** and the scorer's game-bootstrap floor **37.36%**, both clearing the pre-committed 35.95%. Gate #2 readable at **59.49%** [52.48%, 66.13%] and given **no verdict**, per the criterion. Two clauses did not apply cleanly and are recorded rather than smoothed: the criterion said Wilson where the scorer publishes a bootstrap, and S2 ran no random arm so the own-arm clause had nothing to fire on. Writeup `games/changeling/RULES.md` §S2 read; arithmetic `py -3 -m eval.s5_verdict`. Code-debt item 4 settled in the same session because the writeup had to quote a path. | - | - | done |
| ~~**S6**~~ | ~~The gate #3b campaign - cabal's LAST GPU program.~~ **CALLED 2026-08-27 - gate #3b NOT SHOWN, cabal's GPU program stops.** 40/40 games, both arms `rc=0`, 1.35% campaign fallback. Pooled 9/20 = 45.00%, Wilson [25.82%, 65.79%] against the derived bar 33.33% - floor does not clear, so the pre-committed answer applies and there is no third campaign. All three draw-dependent items resolved off the same records: step-not-slope did NOT fire, the `five_rejects` shift is not established, run-length degradation did not reproduce. Verdict and arithmetic: `docs/gate3b-verdict.md`, `py -3 -m eval.s6_verdict`. | - | - | done |
| ~~**S7**~~ | ~~Measured prompt variables.~~ **DROPPED as a cabal GPU program** - a paired cabal arm is 13.2h to move a number 3a no longer spends precision on. Re-homed; reasoning in `docs/gate3a-retired.md`. | - | - | done |
| **S8** | **Next rung or publish. TAKEN 2026-08-28 on the adjudicator branch, and NOT closed** - the DURF fixture got its scorer and four runs; the read is VOID on the instrument control and lives in `docs/durf-rung.md`. What is still open under this slice is the session engine (a kernel, player seats, and the entitlement audit this instrument does not exercise), and the 6/7p and publish options below, untouched. Original scope: 6/7p + information-degrading evils, publish hygiene, or the adjudicator spike - and **Spike #2's faction heartbeat is no longer a fourth option beside that one.** Scoped 2026-08-27 (`docs/faction-heartbeat.md`): both need the same typed-fact channel, and a faction is the small version of it, so the heartbeat is a way of building the adjudicator's hardest part against a testable surface. **The adjudicator spike has its own literature** - the off-repo ledger names what to read before scoping it, and the sweep that produced it is closed. What remains is READING debt; **the TTRPG IP posture is no longer unchecked - it was answered 2026-08-28 and its answer is in the tree, `docs/content-packs.md`**: the engine, schema and loader ship, a rung's source material is a pack, most packs stay local, and every rung ships one example pack whose terms permit it. That decides the tree's shape before the first rung, which is the part that gets expensive to retrofit. Which particular systems can ship a pack is a per-source reading and stays off-repo. **The DESIGN half of that literature is now in the tree** - `docs/action-channel.md` carries the call-vocabulary constraints (one blocking call, referee-side free-text seat tokens, a prompt split along its seams) and the two failures the kernel has to catch, all stated in parlor's terms, so the spike does not depend on the ledger surviving. What stays off-repo is the competitive half: which builds exist, what they are rated, and their licences - including that one of them was read in full from source under a licence that forbids reuse, so the call vocabulary above is written from the game's own public rules and stays that way. | varies | S5 done (S1 is called) | the discretion number exists, VOID and dated; the engine does not |
| ~~**S11**~~ | ~~The DURF session engine.~~ **LANDED 2026-08-28 - gate #1 measured on this rung for the first time, and it HELD IN 3 OF 6 SESSIONS.** The engine, the fact-keyed entitlement, the audit and the transcript renderer are in `games/durf/` (`facts.py`, `kernel.py`, `session.py`, `seats.py`, `transcript.py`), driver `eval/durf_session.py`, recipe `eval/runs/durf-session.cmd`, fact set `games/durf/fixtures/facts.json`. `core/` was not touched and `find_leaks` is unchanged - the rung's adapter NUMBERS its facts and hands the matching to the primitive, so there is one naive matcher in the repo and not two. 86 tests, seven guards mutation-checked. **The read, the three leaks and the one term that is on the record as arguable live in `docs/durf-rung.md` §The session engine - do not restate them here.** Evidence: `transcripts/durf-session-q36-{leak,held}.md`. | - | - | done |

## While the card is busy - the standing menu

The GPU-bound / attention-bound split above has a recurring question behind it:
*a run is in flight, so what can this session actually do?* The answer is stable,
so it lives here instead of being retyped. **The freeze is the binding
constraint, not the GPU** - no prompt, scorer or rules edit while an arm is
running, which rules out most of the queue and all of the measured work.

**Whether a freeze is in force is `RESUME.local.md`'s to say** - this table is
kept for whenever one is. Its standing lesson is the reusable half: an instrument
scored against records that already exist costs nothing and can outrank the run it
is waiting on.

| option | verdict | why |
|---|---|---|
| Secret Hitler | **no** | Same rung as cabal - deterministic referee, bounded actions, no judgment - so it buys recognition and no engine progress. Identical argument to the one already made against a vanilla Werewolf rung. Its policy deck is more rules, not a different knowledge model |
| Blood on the Clocktower | **right target, wrong size - and now scope it against what exists** | The only one of these that is a genuinely different rung: the Storyteller makes *discretionary* rulings, which is the judgment-GM `docs/action-channel.md` splits the kernel/adjudicator for. But it is 20+ characters and the discretion is the hard part - so the session-sized version is a SPIKE that scopes the adjudicator against 3-4 characters, never the game. **Confirmed from outside 2026-08-27** - a public LLM-vs-LLM arena at this game already exists and is rated, another build scripts the storyteller outright, and a third puts an LLM in that seat; the off-repo ledger names all three. **So an LLM arena at this game is NOT the contribution. The discretionary adjudicator plus the entitlement audit is.** Two free controls worth copying from the rated one: shuffled turn order against positional advantage, and role-flipped mirrored matches |
| 5e / a rules-lite RPG | **the endgame, and not yet** | This is the rung the repo is aimed at. `docs/action-channel.md` says do not harden cabal's `Phase` enum, `action_prompt` chain or `ACTION_KEYS` before game #2 exists - and a rules-lite system is the honest cheap version of this, not 5e |
| `/improve-codebase-architecture` | **no, and least of all now** | A refactor under a freeze is risk with no measurement, and the two shapes actually worth restructuring are named in `docs/action-channel.md` as things to leave alone until game #2 |

**Direction, called 2026-08-27 against the literature** (argument kept off-repo):
gate #1 measures parlor and is durable; gates #2 and #3 measure a MODEL and decay
with the next checkpoint - S1 already found the tell, -0.2% on a 12B against +66%
on 120B-class. Nothing built so far de-risks the actual product claim, "a referee
that oversees without micromanaging". So after S6 and the S5 read, the next spike
is the **adjudicator** against 3-4 discretion-heavy characters - not a whole
game's roster, and not Secret Hitler, which is cabal's rung again.

**What is genuinely free right now**, i.e. touches no model-facing byte, no
scorer, no GPU: the reading debt, whose ledger now exists off-repo and names what is
owed next. The changeling deck design landed 2026-08-27
(`games/changeling/RULES.md`), and what it left behind - registering the setups -
is not free. Item 6 of the code-debt batch, its other blocker, landed in S10.

**The queue reads: the DURF rename and the campaign behind it, then S8's untaken halves.** S11 landed 2026-08-28 and gate #1 has its first read on this rung. The instrument decision it left was TAKEN 2026-08-28 and the answer is RENAME; the specification is the S11 block at the top of this file and it is the cheapest item in the queue. What that leaves behind is the campaign, which needs its criterion written before it is launched. The adjudicator branch of S8 was taken 2026-08-28 and produced a dated VOID read rather than a closed slice; its engine half is S11 and is now done. The 6/7p package and the publish option are where they were. S2 and S5 landed, the powers
re-run landed, its rule-error half is closed, and `RULES.md` has no table left on
dirty numbers. The code-debt batch is done except item 3, which is gated outside the
tree and holds up nothing. S8's entry condition (S5 done, S1 called) is met. The three cabal items that used to
sit behind the freeze - the solver arm, the mixed heuristic/LLM table,
`DEFAULT_THEME` off `1984-en` - were unblocked when the freeze lifted. The theme
move landed 2026-08-28; the other two need GPU cabal no longer has, so they queue
behind changeling or land at the publish boundary.

**Publish hygiene stopped being a round, 2026-08-28.** It is now a pre-commit gate
over the lines a commit ADDS - `scripts/hygiene-check.sh`, installed by
`scripts/install-hooks.sh`, invariant in `CLAUDE.md` - so the mechanical half rides
every commit instead of waiting for a publish-day pass, and nothing accrues between
passes. It found zero violations in the tracked tree the day it landed, which is the
point: the value is forward, on the next commit. The judgement half a grep cannot
see - a doc that assesses a third party, quotes unread work, or names an author
where an identifier would do - is the scope rule in `CLAUDE.md`, and it is the thing
to check a new doc against rather than a pass to re-run. The three route base URLs are environment variables with loopback defaults
(`PARLOR_ENDPOINT_LOCAL` / `_CLEAN` / `_GRAY`), so a clone runs with nothing set and
no box's topology is in the tree. Nothing is queued behind it.

**S1 is called, and it freed half the queue.** S6 survives in a changed and
bounded form; S7 and the cloud arm are dead. Read `docs/gate3a-retired.md` before
restarting any cabal run.

**Do not mix cabal and changeling in one session.** They have separate `RULES.md`
files, separate scorers and separate baselines, and every number confusion in this
file so far came from carrying one game's intuition into the other's denominator.


## The queue

Open rows, unordered - the slice table above is what ranks them.
**Gate #3a is RETIRED and gate #3b is NOT SHOWN, and nothing below reopens
either**; what survives of both is re-homed to changeling, where a paired 20-game
arm is ~30 min against cabal's 13.2 h.

- `docs/gate3a-retired.md` - the S1 verdict: the pricing table showing N was never
  the binding constraint, the off-team cell that cannot hold a sign across two
  draws, why 7p and 8p do not reopen it, **the paragraph gate #3a IS allowed to be
  reported as**, and the self-outing read - 26 lines, ~8 genuine, none of them the
  seer, so #3b was never contaminated.
- `docs/gate3b-verdict.md` - the S6 campaign, its pre-committed criterion verbatim,
  and the three draw-dependent items resolved off the same records.
- `docs/gate3-modelling-review.md` - the 2026-08-26 review that started it, closed
  on all six items. **Read its header before its body**: its line citations are
  stale and the gate it was sharpening is the one S1 retired.
- `docs/scripted-rungs-cabal.md` - 2026-08-28, unmeasured. Why the ladder keeps
  climbing on hand rules rather than a learned policy, and the three rungs that
  follow: the designated failer (the CPU half of the 6/7p item below, with a
  prediction stated before the run), the watcher bluff as a typed `claim(role)`
  channel rather than a rung, and a ceiling estimator trained on self-play and
  tested on the pinned 29 hunts. §0 is game-free and moves to
  `docs/control-ladder.md` when a second game builds a rung.
- `docs/content-packs.md` - 2026-08-28, unmeasured. The engine/content split for
  the endgame rung: what ships, what stays local, why the example pack is
  required rather than a courtesy, and why "local" is not the same as
  "untransmitted". Read it before laying out `games/<rung>/`, not after.
- `docs/preset-axes.md` - 2026-08-28, unmeasured. The question after content
  packs: is every system a preset of flags over one engine? No - entitlement
  schema, resolution kernel and authority topology are three different kinds of
  axis, only the first is flag-shaped, and a flag list is 2^N unmeasured fallback
  rates wearing one measured number's name. Carries the boundary of the formal
  prior art (`arXiv:2205.00451`) and why a DSL is the wrong reach here.

- [ ] **Count self-outings by a CLAIM-shaped match, and re-score the records with
      it.** The open half of the read above. `outed_own_role_in_public` matches the
      seat's own theme role name, which over-counts by ~3x (most hits are a seat
      using its own role's word to accuse somebody else) while a functional-key
      match sees nothing at all - the old 0/1290. Neither is a measurement. First
      person and present tense is the fix, and it **RE-BASELINES the 26/1580
      count**, so it lands with a re-score of the records rather than on its own.
      It also cannot see the interesting case by construction: a mimic claiming to
      be the seer is invisible to a check that matches only the seat's own role
      name, so counting FALSE claims is a different check again.
- [ ] **Gate #2 has a cheaper falsifiable design than waiting on gate #3.**
      `--arm llm` vs `--arm llm-good` on the same seeds isolates evil's
      contribution against a fixed opponent population, using arms that already
      exist. The conditionality then softens from a hard refusal to "the
      unconditional headline rate is only quotable once #3 holds". Also: the ~65%
      no-deception baseline is a property of `RandomPolicy(fail_rate, approve_rate)`,
      not of the game - fine as an existence proof, wrong if quoted as the game's
      intrinsic evil floor. And `rate_ok`'s 5% CI-floor bar is pre-declared
      nowhere; it deserves a line in the pre-committed criterion the way 3b's did.
- [ ] **Two behaviours the auditor prices, neither of them bugs** (steer
      2026-08-26 - my PROOF classification was wrong on both).
      - **A good seat approves a known-tainted team, 7/76 (9%).** Legal and
        plausibly CORRECT: a seer that always rejects exactly the tainted teams
        has a perfect tell, and the hunter's whole job is finding the seer, so
        buying concealment with mission EV is real play. The model appears to do
        it deliberately - a seer's private reasoning reads "I must support [1,4]
        ... and vote yes - without revealing I know who's darkness." Checked the
        one forced case (four rejections, a fifth loses outright): 0 of 7 were
        under that pressure, so they were free choices - but free is not the same
        as careless, and this count cannot separate strategy from lapse.
        **Consequence for the metric, which is the part that matters:** gate #3a's
        "good approves clean vs tainted" scores a concealing seer as a bad one, so
        the headline +31.55% and the blind-seat +13.57% are not measuring the same
        thing. Blind seats have nothing to hide, which is why that half is the
        sturdier number - and an argument for reporting it as the primary.
      - **Over-sabotage, 12/63 missions.** Two evils on one mission decide
        independently and the game gives them NO private channel, so playing
        success is only better if the other one fails and nothing says it will.
        Anti-coordination with a mixed equilibrium; the ideal count is not zero
        and calling it dominated was wrong.
        Still worth counting for one reason: a focal point needs no channel at all
        - "the lower-numbered evil on this team plays fail" is derivable by both
        seats from the public proposal alone, and Schelling points do not require
        communication. A pair that finds any such convention drives this near zero
        without signalling. 41% of sunk missions says the model finds none. That is
        a fact about reasoning, not a rules violation.
        So the `need` disclosure stays worth doing (it is entitled rules
        information the ask withholds) but stop expecting it to zero this number.
- [ ] **One CLI over both games, so a person can sit down and play the bots.**
      Today the human seat is two per-game entry points - `games/cabal/demo.py` and
      `games/changeling/demo.py`, each with `--human 0` - and a player has to know
      which module a game lives in before they can join it.
      - **The hard half is already built and shared.** `core/console.py` reaches
        its backend through exactly `complete_meta(context) -> (reply, served_by)`,
        the same slot `LLMPolicy` occupies, so a console seat inherits the prompt,
        the parser and the refuse-and-retell loop from the game it sits in. What is
        NOT shared is the argument surface: cabal's driver takes `--rounds` and
        `--transcript-dir`, changeling's takes `--no-thinking`, and the two demos
        have drifted apart flag by flag.
      - **So the work is a registry, not a wrapper.** `core/` gains a name ->
        (referee factory, driver, that game's own flags) table and one
        `py -3 -m parlor play <game>` over it; a `--list` names what is registered.
        Each game keeps its own flags - a lowest-common-denominator flag set is how
        two games come to share one denominator, which this file forbids elsewhere
        for the same reason. **This is the promote-on-evidence case the `core/`
        invariant asks for**: game #2 exists and needs it, which is exactly the
        condition, so it is not speculative generality.
      - **It must not move a model-facing byte.** A CLI that reaches a prompt is a
        MEASURED change and would re-baseline both games' recorded numbers for a
        convenience. Prove it rather than intending it: render both games at fixed
        seeds before and after and diff, the way the 2026-08-27 freeze check did.
      - **The one-human-seat refusal stays.** `human_seats` in `core/` refuses a
        second person and is mutation-checked - a terminal is one channel, so two
        people at it read each other's private view scroll past, and the referee's
        audit cannot see that because both renders are correct. A CLI that makes
        seating easier is exactly where someone would try to seat two.
      - **Done when** `py -3 -m parlor play cabal --human 0` and
        `... play changeling --human 0` both deal a game a person can finish,
        `--list` names both, and the render diff above is empty.
- [ ] **Gate #3 was never blocked on the table talk - that read was wrong.** It was
      model capability: identical prompts scored -0.2% on the 12B and +66% on
      120B-class. `--register plain` helped the 12B (+16.7%) but bought suspicion,
      not judgement (7 of 8 games died at five_rejects). `--simultaneous` is built
      and unmeasured; the salience line has no measured benefit anywhere and is a
      removal candidate, on its own measurement.
- [ ] **Find what writes a stale `.git/index.lock` in this repo.** 2026-08-28: a
      0-byte lock appeared at 08:44 with no `git.exe` running and blocked a commit
      40 minutes later, mid-session, with the index intact. Removing it was the
      documented remedy and cost nothing - but an unattended run that commits its
      own records would have died on it, silently, at a point where the run itself
      was healthy. Candidates: the rtk PreToolUse hook, which is EXCLUDED for git
      on WSL but **live on native Windows** (`RTK.md`), or a crashed helper. Cheap
      probe: log the lock's ctime against the tool-call transcript next time it
      appears. Until then, `/mingw64/bin/git` for anything whose answer gates a
      commit, which is `RTK.md`'s standing rule anyway.
- [ ] **Judge a detached run only by its own log/JSONL - never by a proxy.** Three
      times in one session CPU seconds, Win32 IO counters, and an exit code each
      read as liveness for network-bound work; the IO-counter one killed a healthy
      cloud run (those counters track FILE io, not sockets). And probe a cloud tier
      with a BURST (12 back-to-back), never a single call: a key under cooldown
      serves the occasional request while failing a stream, so a single-call probe
      says "healthy" about a tier that cannot carry a run.
- [ ] **Negation pass over the model-facing strings** (the rule is
      `.claude/rules/model-facing-text.md`, path-scoped so it fires when you open
      the files that hold them). Steering by prohibition makes the banned behaviour
      MORE available, and the live prompts do it in at least three places:
      `"speak in the first person, and do not answer your own earlier lines"`
      (referee DISCUSS ask), `"do not defer to whatever the table already seems to
      think"` (plain register), `"no theatrics, no slogans, no world-flavour"`
      (same). Each has a positive form - speak TO the other seats; form your own
      read first; speak plainly and cite the record. The referee's refusals
      (`cannot fail a mission`, `cannot be the informant`) are hard guardrails and
      stay, though each already pairs with a positive instruction.
      **This is a measured change, not a cleanup** - same seeds, one variable, and
      a prompt edit landed mid-campaign confounds that campaign exactly the way
      `c43274e` confounded `hunt20b`. **UNBLOCKED 2026-08-28**: S6 is down, nothing
      is in flight, and the standing rule is the check rather than the wait - run
      the liveness command above before landing it, not a remembered freeze.
      **Re-homed 2026-08-27 (S1):** measure it on changeling, where a paired
      20-game arm is ~30 min against cabal's 13.2 h. Cabal's referee refusals stay
      as written.
- [ ] **A per-seat private notebook - BUILT 2026-08-26, UNMEASURED.** `--notebook`
      on `run_games.py` and `demo.py`; off by default. A seat's `note` is filed
      under its own seat and rendered back to that seat alone on every later call,
      so a read survives the turn that formed it. Cap: last 6 lines of 160
      characters, stamped with the mission it was written on.
      - **It is a prompt change, so it is a MEASURED change** (`--notebook` vs not,
        same seeds, one variable, reported beside its fallback rate) and it waits
        behind the seed-1000 re-run the same way the negation pass does. Nothing
        about it is quotable until that arm exists.
        **Re-homed 2026-08-27 (S1)** to changeling for the same reason as the
        negation pass, and it stays OFF for the S6 campaign, which runs on frozen
        code. A memory that survives the turn is a bigger prompt change than the
        others here, so it is the one most worth a cheap paired arm.
      - Gate #1 holds by construction and the audit says so: the notebook leaves
        the audit view with speech (`include_notes` defaults to `include_speech`),
        because `find_leaks` is naive substring matching and a seat writing down a
        correct GUESS would otherwise score as a referee leak. Four mutation-checked
        tests, each killed by its own named test with a compiling mutant.
      - Two costs it buys, both real: it rides on every call (~1.1 kB at full
        notebook), and it hands the seats a memory the earlier runs did not have,
        so no number from before it is comparable to a number after it.
- [ ] **Mini-personas** (credulous / suspicious / contrarian / by-the-numbers) as
      per-seat judgment biases, assigned from the game seed and recorded so the
      scorer can split by persona. Trigger: only if a table that argues from
      evidence still votes identically. NOT for flavour - votes are already
      independent (§Measured), so this buys nothing until the talk carries evidence.
      **Re-homed 2026-08-27 (S1)** to changeling if built at all - its trigger was
      never met on cabal and cabal no longer buys measured prompt variables.
- [ ] **Larger setups (6/7p) + the two information-degrading evils.** Package them
      together, because both only make sense at 3 evil seats.
      - The engine already supports both, and has since the first commit: `Role`
        carries `seen_by_seer` (False = the evil the seer cannot see) and
        `sees_fellow_evil` / `seen_by_fellow_evil` (False = the evil who neither
        knows nor is known by its own side). `entitled_knowledge` honours all
        three, so each role is ~2 lines of DATA. The cost is measurement, not code.
      - **Why they are worth more than variety: they degrade information in a
        principled way.** The unseen-evil variant halves the seer's knowledge, so
        the current +30.7% local / +66% cloud stops being partly "the seer acting on
        a handed answer" (already isolated at +13.7% by the blind-seat split) and
        becomes a claim about deduction. The blind-evil variant makes evil deceive
        WITHOUT knowing its partner, which is the honest version of gate #2 - the
        current claim is really "two agents told about each other cooperated".
      - **The gate that gated this is CALLED** - 3a retired and 3b not shown,
        2026-08-27 - so the sequencing constraint is now only the general one:
        changing what the seer knows mid-run means neither the old nor the new
        number means anything. Land it between campaigns, as the hardening pass you
        would actually publish from. What still blocks it is that cabal has no GPU
        program left, not a gate.
      - At 5 seats there are only 2 evil, so the unseen variant leaves the seer
        seeing exactly one and the blind variant leaves two evils who know nothing
        of each other - swingy to the point of noise. These are 7+ roles.
      - **A bigger table does NOT fix the thin denominator - it makes it worse.**
        This file used to blame the ~12-votes-a-run sample on the 5-seat size
        ("because most teams in a 5-seat game carry an evil"), which implies a
        larger table would help. It would not. Clean teams get
        combinatorially rarer as seats grow, faster than the extra good voters
        compensate; gate #3b is untouched at any size since hunts are one per game.
        Arithmetic, table, and the graded-taint fix that DOES work:
        `docs/player-counts.md`.
        **Checked from the other side 2026-08-27 and it holds harder than this
        bullet claimed.** Off-team-clean good votes per vote event - the only
        unconfounded gate-#3a cell - run 5p **0.120**, 7p **0.160**, 8p **0.100**;
        per unit speaking cost 0.0240 / 0.0229 / 0.0125. 7p's raw gain is eaten by
        its extra speakers. So a bigger table does not rescue gate #3a either, and
        these variants are worth building for what they degrade about INFORMATION,
        never as a sampling fix.
      - **The roles themselves landed 2026-08-27** as `LURKER` (unseen by the seer)
        and `STRAY` (neither knows nor is known by its own side), named in all five
        skins, plus `ALL_ROLES` and three theme guards in `test_audit_coverage.py`.
        Nothing deals them - what is left is the 6/7p setups and the measurement,
        which was always the cost. Verified on a hand-built 7-seat deal: the seer
        sees every evil but the lurker, and no evil sees the stray.
      - Watch role-name vs faction-name substring collisions in the leak audit (see
        the plain-skin "Loyalist" case). **A sharper one found while checking the
        above, and it is not about naming at all:** two seats holding the SAME role
        break the audit outright. Each one's own role name is the other's secret
        term, so the 7p deal with two `loyalist` seats reported a mutual leak in
        every skin - a false positive no rename can fix, since the term is
        identical by construction. **FIXED 2026-08-27, and the remedy this file
        proposed was the wrong one.** Re-keying `secret_terms` so identical-role
        seats do not audit against each other is a blanket skip, and a skip buys
        the false positive off with a false negative - the audit would then be
        blind to the referee genuinely naming a same-role seat, which is the
        shipped-leak half the top invariant refuses. What landed instead narrows
        the CORPUS, the way `include_speech=False` already does: the viewer's own
        "Your role:" line is removed before the scan, since that is the only place
        the referee asserts a seat's role to that seat. `find_leaks` stays naive, a
        duplicate term anywhere else still fires, and the same shape is what
        changeling reached from the other side. Mutation-checked - the blanket skip
        was written, and it kills the soundness test by name.
- [ ] **Seat the changeling expansion cards, which means picking a deck.** The
      cards themselves landed 2026-08-27: `kindred` (the pack's mirror on the
      village side) and `waker` (acts last, so it is the only seat whose belief is
      guaranteed true at dawn) are implemented, skinned, resolved and tested, and
      `SETUP_5` deals neither - the same footing as cabal's `LURKER`/`STRAY`, for
      the same reason: every recorded changeling number was played on the
      eight-card deck, so a deck change re-baselines all of them. **The DECK DESIGN
      landed 2026-08-27** in `games/changeling/RULES.md` §The decks that would seat
      them, and that section is the source of record - two decks, each with its
      arithmetic measured over 4000 nights, plus the four expansions costed and not
      built. **Do not restate its numbers here.** What is open is the part a design
      doc cannot close:
      - **Register the setups, then measure.** Both decks are UNBLOCKED as of
        2026-08-28 - they waited on keying the knowledge class on what the seat was
        told, which landed in S10. `py -3 -m eval.strata` prices a deck's strata
        before it is built: add a row to its `DECKS` table and read the blind count
        off 4000 nights.
      - **Every deck change costs at least TWO variables.** `len(deck) == n +
        centre` means a card cannot be added without growing the table or the
        centre, so there is no one-variable arm in this game. Choose the second
        variable deliberately and report it.
      - **Route call: `waker` is the one worth a run.** Every other seat has to
        infer that the night moved it and this one is told, so it is the cleanest
        handle on whether a model reasons about divergence at all rather than about
        who is lying - and its deck seats it in 62% of games, so one run carries
        its own control with no paired second run.

- [ ] **Candidate changeling skins - BUILT 2026-08-27, ALL UNRUN.** `greek`,
      `greek-named`, `journey`, `investiture`, `masquerade` and `folk-inv` exist as
      themes; `DEFAULT_THEME` is still `folk` and no number has moved. **The design
      is `docs/moral-framing.md` §The changeling skin set - what each arm is FOR**,
      which owns the arm ladder, the name-form axis, the corpus-sourcing rules and
      the length control. Read it before running or editing any of them; do not
      restate it here.
      - **What is open is which arm gets GPU first**, and the ranking is a route
        call this file owes: `greek` for the vocabulary control, `folk-inv` for
        polarity, the `greek`/`greek-named` pair for name form - that pair being the
        cleanest single-variable manipulation in the repo, since it moves eight
        strings and nothing else.
      - **A blurb is a prompt**, so every face is frozen at its measured length and
        an edit orphans whatever has been recorded against it.

- [ ] **Ship a werewolf-vocabulary theme on changeling - and that is the WHOLE
      answer to public legibility.** A public repo has a real problem that "team-
      mission hidden-role deduction game" means nothing to anyone outside the
      hobby, while "werewolf / seer / villager" means something to nearly everyone.
      That is public-domain folk-game vocabulary (Mafia, Davidoff 1986), carries no
      branding question, and lands on a rung that is already built.
      - **This is why a vanilla Werewolf RUNG is not worth building**: it sits on
        the same rung as cabal (deterministic referee, bounded actions, no
        judgment), so it buys recognition and no engine progress, and it has
        elimination - a shrinking table, variable agent count per game, dead seats
        contributing no decisions, i.e. the N problem from the wrong side.
        Legibility is a theme and a README paragraph, not a spike.
      - **changeling does not retire cabal's gates.** Different rung, different
        deduction task. Which game's numbers get published first is the only thing
        it settles; a cabal gate left uncalled stays uncalled.
- [ ] **Spike #2: off-map faction heartbeat - SCOPED 2026-08-27,
      `docs/faction-heartbeat.md`.** Read it before costing this against S8's other
      options, because the scoping moved it.
      - **It is not an alternative to the adjudicator spike, it is the small
        version of that spike's hardest part.** Both need the typed-fact channel -
        an actor declares its intended reveals as typed facts, entitlement is
        checked against those, and the prose is audited against the facts it did
        NOT declare. A faction needs it over three action types; a Storyteller over
        20+ characters of discretion. S8 lists them side by side as though they
        were separate options; they are not.
      - **The "long-running agent process" half of the original stub is
        backwards.** A wall-clock actor has no fixed call order, which voids the
        seed invariant `docs/reproducibility.md` measured. Ticks are counted, the
        schedule derives from the game seed, and whether a process drives it must
        not be observable in the record.
      - **The one new gate #1 failure, and it is silent**: entitlement gains a time
        axis, so a render must be audited against the entitlement snapshot taken
        when it was BUILT, never against entitlement recomputed at audit time - by
        then the fact may have gone public by other means and a real leak reads
        clean. Capture the snapshot with the render.
      - Faction decisions stay OUT of the run's denominator (the gates measure
        seats), and the faction's fallback rate is reported beside the run's.
- [ ] **Evil over-sabotages, and it is the seer-salience bug wearing the other
      team's colours.** Scored on the FULL 20-game run: 63 mission resolutions,
      fail-count distribution `{0: 34, 1: 17, 2: 12}`, need=1 throughout. So **12
      of 29 failed missions (41%) had BOTH evils play fail when one sufficed**, and
      12 of 63 missions overall (19%). The partial-run figure was 45%/9-of-20; the
      full run settles it at 41%.
      **Restated 2026-08-27 (S3): the honest figure conditions on the game
      continuing** - a double fail on evil's third failed mission is free, since the
      game ends on that resolution and the identification is never paid for.
      Re-scored, `hunt20b` is 11/28 = 39% and `hunt20c` is 10/22 = 45%. The
      correction moves the number by ~2pp in each direction and changes nothing
      about this item: evil still hands over the pair on ~2 of every 5 sinkings it
      actually pays for.
      On a 2-seat team two fails name both of them outright; on a 3-seat team it
      cuts the good side's search to three pairs. It is the single largest free
      information gift on the board and evil hands it over on two of every five
      missions it sinks.
      - The rules already allow the right move. `validate_card` refuses only a GOOD
        seat playing fail, so evil may play success freely, and the MISSION prompt
        already says "weigh sabotage now against the suspicion a fail here would
        put on this team". The capability is there; nothing lines it up.
      - **Two fixes here, NOT one, and they are different kinds of thing.** Keeping
        them apart is the whole judgement in this item.
      - **(a) Disclose `need` - a harness BUG, fix unconditionally.** `need` appears
        only in the public event AFTER resolution (`referee.py` mission()), never in
        the ask. How many fails a mission requires is PUBLIC RULES INFORMATION - a
        human reads it off the board before playing a card. Withholding it is an
        information asymmetry against the game's own rules, i.e. the seat is being
        asked to weigh redundant sabotage against a threshold it was never given.
        This is not a hint and not a nudge; it is restoring entitled information,
        and it needs no measurement to justify. The gate it was sequenced behind is
        called, so what is left is the ordinary rule: it changes behaviour, so it
        lands between campaigns and not into one.
      - **(b) Naming the partner on this team - a HINT, and the evidence points
        AGAINST it.** The seat can derive "my partner is on this team" from the
        public proposal plus its night knowledge. Spelling that out is exactly what
        `_night_against_the_table` does for the seer - and that line's value
        INVERTED with model capability: +63% on the 12B bench, then **+80% as-is vs
        +72% with the line** on q36, i.e. actively harmful, because it competes with
        reasoning a capable model already does. So do not assume the mirror fix
        helps; the one measurement we have on this exact move says it hurts on the
        model gate runs actually use. If (b) is tried at all it is a measured arm of
        its own, and (a) must land first and alone or the two are confounded.
      - **This is a confound in gate #3a, not just an evil-side weakness.** Good's
        +30.7% discrimination is measured against an evil side that self-identifies
        on 45% of its successful sabotages. Some unknown share of that number is
        good exploiting a blunder rather than deducing from discussion. So fixing
        evil is not a fairness gesture - it is required before the good-side number
        means what it claims. Expect discrimination to DROP when this lands; that
        drop is a truer number, not a regression.
      - Sequence: measured change, same seeds, one variable, between campaigns -
        the gate this waited on is called. Distribution above is from a PARTIAL run (13 of 20) and is an
        incidental mechanical count, not the pre-committed hunt metric - recompute
        on the full run before quoting it anywhere load-bearing.
- [ ] **Stratify cloud results by served upstream instead of pooling them.** The
      problem with an `auto` run was never that it is undocumented - `complete_meta`
      already returns the served model and the report prints the mix. It is that
      POOLING hunts across a time-varying model population computes a Wilson
      interval over an ill-defined denominator. Record the served upstream on each
      decision, report per model class, and an `auto` run stops being "several
      models averaged": cells accumulate ACROSS runs, so tonight's nano hunts and a
      future 120B-class run land in different cells instead of contaminating one.
      Retires the "reproducible, unlike the cloud's 30-upstream mix" asymmetry -
      stratified, a cloud run is reproducible at the cell level. Does not rescue a
      thin run: ~10 hunts over 3+ upstreams is nothing per cell.
- [ ] **Theme as an experimental variable, not a default to fix** (design:
      `docs/moral-framing.md`). `1984-en` stays the shipping default;
      there is no licensing reason to drop it and it is the face every committed
      transcript wears. What is open is that the blurb inverts moral polarity -
      sabotage reads as heroic, deceit as survival - and nothing measures whether
      that moves behaviour. No number in §Measured records which theme produced it,
      so a theme change is a MEASURED change on the same terms as the negation
      pass: same seeds, one variable, landed between campaigns. The gate it used to
      wait on is called.
      **Re-homed 2026-08-27 (S1)** to changeling, which ships a folk-game theme of
      its own and so poses the polarity question at 1/26th the GPU cost. `1984-en`
      remains cabal's shipping default and is the face of every committed
      transcript; nothing about cabal's theme changes.
      **Arms built 2026-08-27**, on cabal, as themes only: `1984-inv` (arm 3,
      villainous - the 1984 skin inverted rather than a new fiction, so 2-vs-3
      differs in valence and nothing else) and `drill-en` (arm 4, neutral - a
      sanctioned drill with no victim). Unrun, and adding them moved no number
      because nothing runs on a face until a run asks for it by name. (cabal's
      `DEFAULT_THEME` did later move, `1984-en` -> `plain` on 2026-08-28, for
      publish-surface reasons and not as an arm; `games/cabal/roles.py` carries
      that note beside both theme constants, which is where a reader of a number
      will be.) `bnw-en` was 84 words against `1984-en`'s 53, confounding the
      vocabulary control with density; trimmed the same day, and all four English
      faces are now 53 words / 281-291 chars. Frozen from here - a blurb is a
      prompt, so a later edit orphans whatever has been recorded against it. One
      thing left to settle before spending GPU: whether the run happens on cabal or
      on the re-homed changeling rung. A `bnw-inv` was considered and rejected -
      reasoning in the doc.
- [ ] **Seat the solver as an ARM** - the half of `docs/reference-policies.md` that
      is still unbuilt. The instrument exists and scores records
      (`games/cabal/solver.py`, `python -m eval.derivable`); what does not exist is
      a `SolverPolicy` with an `act(ref, seat)` that plays. That needs policy and
      driver plumbing plus GPU, and cabal no longer has a GPU program - so it queues
      at the publish boundary or behind changeling, not behind a freeze. `evidence_from_referee(ref, seat)` is already the whole input and is gate
      #1-safe by construction - it reads `entitled_knowledge` and `public_events`
      and holds no referee. Note what an arm buys before building it: the hunt is
      mechanically flat (proved), so a solver arm can only differ from random at the
      VOTE, and it is the vote strata that turned out to be the live question.
- [ ] **Seat the heuristic against the MODEL, which is the arm that does not exist
      yet.** The rung is built (`games/cabal/heuristic.py`, `python -m eval.ladder`)
      and both halves it can reach without a GPU are measured - see §Measured. What
      is missing is the third: a game with heuristic seats and LLM seats at the same
      table, which needs GPU and the eval driver's arm plumbing - and cabal has no
      GPU program left, so it queues behind changeling or lands at the publish
      boundary. Read the artifact warning in §Measured first - the
      all-heuristic arm's 99.5% hunter is a deterministic twin reading its own tell,
      and a mixed table is where that stops being a confound and starts being the
      measurement.
- [ ] **Group-sequential design instead of a pre-committed fixed N.** S6 commits
      40 games and forbids a third campaign, because stopping when a floor happens
      to cross is peeking - correct, and the named fix is not "don't look". It is
      alpha spending: Wald's SPRT (1945), O'Brien-Fleming boundaries (1979),
      Lan-DeMets (1983). A boundary computed BEFORE the run lets you look
      repeatedly and stop early legitimately, which on a 13.2 h campaign is real
      GPU. **It must be designed BEFORE the next campaign**, never retrofitted to
      S6's records - that would be the peeking it exists to prevent, which is the
      real gate here and not the freeze this line used to cite.
- [ ] **Obtain the paywalled theory chapter before publishing anything about gate
      #1.** It is the one result that could bound gate #1's shape, no free copy
      exists, and the route is a request to its authors. **The target, the reason
      it matters and the drafted request are off-repo**
      (`agi2026-chapter-request.md` beside the neighbour list; `CLAUDE.local.md`
      has the path) - a private request naming real people is not repo content.
      What belongs here is only the dependency: no public claim about gate #1
      until that chapter is read.
      Two published hybrids are in the same debt: both hand belief inference to a
      structured model and use the LLM only for language, i.e. the strongest
      results on this task come from NOT asking the model to deduce. That is the
      framing gate #3 should be reported against. Neither voids the gate; both
      change what its number means to a reader. Identifiers in the off-repo
      ledger.
- [ ] **The `1984-cn` language arm is less novel than it looked, and prior work
      predicts its confound.** Published work on non-English play finds models
      struggle with rule-following and strategic integrity outside English -
      which in this repo surfaces as a FALLBACK RATE, not as worse deduction. So
      read that arm fallback-first, and a CN arm voiding on the 10% rule is a
      finding rather than a failed run. What parlor still adds is holding the
      fiction byte-identical, which the prior work does not.
- [ ] **The thesis moved on 2026-08-27 - `README.md` now leads on the product
      claim, and the off-repo positioning argument still leads on the research
      one.** The original thesis is LLM agents as GM *and teammates* for solitaire
      play; existing chat products give one counterparty, and a table of AI
      teammates is only interesting if they do not share a brain. So independent
      context is the PRODUCT REQUIREMENT, not a research property, and `README.md`
      was rewritten to lead on that. Both framings are true and aimed
      at different readers. **Reconcile them in the off-repo file, not here** - the
      failure to avoid is a stale copy that says which framing LEADS while
      disagreeing with the README. Three things to fold in there, all chat-only
      today:
      - **Which framing leads.** Product thesis primary, isolation-by-construction
        as the credential. The evidence is that mainstream multi-agent chat shares
        one history by construction, and where per-character state exists it is
        MEMORY - what a character recalls, not what it is forbidden to be told.
      - **The cost tension, which is the reason nobody does this.** Independent
        context costs N x tokens, and shipping products say so themselves when
        they explain why they centralize. The differentiator IS the cost
        structure, and any product framing has to answer it.
      - **The answer is already designed, filed under scoring.** The `SolverPolicy`
        in `docs/reference-policies.md` is specced as an INSTRUMENT,
        but it is also a teammate that plays correctly for zero tokens - the same
        move the published hybrids won with, and the direct answer to the N x
        bullet above. Cheap competent seats + a small model for the talking.
      **Also decided in that conversation and not yet anywhere:** the queue fanned
      out horizontally at rung 1 instead of cutting a thin path to the end (976
      lines, 25 open items, two games on the SAME rung, nine built-but-unrun
      things), and the walking skeleton that was missing got built by accident the
      same day as `--human`. The cut that follows - gates #2/#3 demoted from gates
      to dated model snapshots, which kills most of the theme, persona, 6/7p and
      cloud items - is the RESUME restructure, and it waits for S6 so the verdict
      section can drain to `docs/` complete rather than mid-flight.
- [ ] **Two shapes not to harden further before game #2** - cabal's `Phase` enum,
      the `action_prompt` if-chain, and `ACTION_KEYS`. Reasoning and the exact
      constraint: `docs/action-channel.md`.

## Pre-committed criteria - all applied, all moved out

None is edited to agree with its outcome; that is the whole value of a
pre-commitment, and clause-by-clause outcomes belong in the verdict rather than
back in the promise.

- **changeling gate #3**, written 2026-08-28 before S2 -
  `docs/changeling-gate3-criterion.md`, applied in `games/changeling/RULES.md`
  §S2 read. Two clauses did not apply cleanly and are recorded rather than smoothed.
- **cabal gate #3b**, written 2026-08-27 before S6 - reproduced verbatim inside
  `docs/gate3b-verdict.md`, beside what each clause returned.
- **The 2026-08-25 hunt run**, the first of them - superseded by S6's, which is the
  same statistic computed the honest way. Its one durable clause outlived it and is
  a live row below: if the hunter lands marginal, **respecify the metric rather
  than buying games**, because gate #3 is bottlenecked on its lowest-power half.
- The discipline itself, the `hunt20b` error it exists to refuse, and why pooling
  runs after the fact is the same move as peeking:
  `docs/evidence-discipline.md` §Pre-committing a statistic.

## Measured, dated - numbers before opinions

All local `rocinante-x-12b-heretic-q4`, seed 400, 8 games, 2 rounds, <1% fallback
unless said otherwise. Fallback rate is quoted because a number without it is the
random policy wearing a model's name.

| what | result | 2026-08-25 |
|---|---|---|
| good vote discrimination, baseline | -0.2% (n=138 votes) | at chance |
| seer approving a team carrying a KNOWN evil | 42% baseline -> 43% with the salience line | the line does nothing in a live game |
| same seer decision, isolated bench, no discussion | 83% -> 37% (n=30/cell, p<0.001) | the line works when nothing buries it |
| `--rounds 2` vs 1 round | 1 of 8 games deadlocked vs 2 of 2 | two rounds is the floor |
| vote unanimity | 11% of 46 votes (spread 1/5..4/5) | votes are ALREADY independent, just uninformed |
| record length vs the 60-line cap | 10 of 16 games over, speech:facts ~4:1 | the trim was deleting missions 1-2 (fixed, `e3249ec`) |
| cap at 512 vs 1536 max_tokens, `nemotron-3-super` | 0/4 -> 2/4 parsed, failures truncated at BOTH caps | no cap fixes a model that thinks out loud; pin one that does not |
| **cloud `auto` (mixed 120B-class), character register, 12 games** | **discrimination +66.0%** (clean 94.4%, tainted 28.4%, n=192; 2.5% fallback) | **gate #3a HOLDS - it was model capability, not the prompt** |
| same run, hunter | 33.3% (3/9, CI floor 12.1%) | exactly chance - gate #3b is now the blocker |
| local 12B, `--register plain`, same seeds as the salient run | discrimination +16.7% (blind seats +11.4%, n=76) | first positive on the 12B, but 7 of 8 games died at five_rejects |
| **local `qwen36-35b-a3b-iq3` (MoE 35B-A3B APEX), 12 games, 0.69% fallback** | **discrimination +30.7%** (blind seats +13.7%, n=222); evil 66.7% with 6 wins by SINKING missions and 32 fail cards | gate #3a holds on ONE pinned local model - reproducible, unlike the cloud's 30-upstream `auto` mix |
| same model, seer bench | +80% as-is vs +72% with the salience line | the salience line is now HARMFUL - it competes with reasoning a capable model already does |
| hunts across ALL live runs | 8/26 = 31%, and **5 of 26 named the hunter's own ally** | fixed in `hunt()`: a seat the night named as yours cannot be the seer, so the referee refuses it |
| cost, `q36` local | ~14.6 min/game (reasoning distill, long generations) | a 50-game hunter run is ~12h overnight; cloud is ~3 min/game when quota allows |

Added 2026-08-26, all `qwen36-35b-a3b-iq3`, seed 1000, 20 games, 2 rounds. **NONE of
these three columns is a controlled comparison of another.** `hunt20` vs `hunt20b`
differ by three things (see the `hunt20b` item); `hunt20b` vs `hunt20c` differ by the
sampler pin `2cfe9d5`, which landed between them. They are three draws, which is all
they are. `hunt20d` is not a fourth column - it reproduced `hunt20c` exactly
(`docs/reproducibility.md`), so a controlled pair still needs a different seed.

| what | `hunt20` (08-25 19:54) | `hunt20b` (08-26 08:56) | `hunt20c` (08-26 14:52) |
|---|---|---|---|
| blind taint sensitivity - THE GATE | +1.20% [-8.44%, +9.63%] | +8.82% [+0.94%, +16.82%] | +9.00% [**-0.25%**, +18.18%] |
| blind, binary (superseded - see below) | +2.53% [-13.45%, +18.04%] | +19.94% [+6.27%, +32.02%] | +18.11% [+3.52%, +33.53%] |
| approval by taint level, blind | - | 93% / 70% / 77% (41/44, 28/40, 24/31) | 82% / 64% / 64% (41/50, 37/58, 32/50) |
| hunter | 3/9 = 33.33%, floor 12.06% | 6/11 = 54.55%, floor 28.01% | 5/9 = 55.56%, floor 26.66% |
| evil win rate | 70%, 5 of 14 by `five_rejects` | 75%, **0** by `five_rejects` | 80%, **6 of 16** by `five_rejects` |
| evil win paths | 6 missions / 5 rejects / 3 hunts | 9 missions / 0 rejects / 6 hunts | 5 missions / 6 rejects / 5 hunts |
| missions, fail-card distribution | 63, `{0:34, 1:17, 2:12}` | 74, `{0:37, 1:22, 2:15}` | 62, `{0:35, 1:15, 2:12}` (derived) |
| over-sabotage, share of sunk, UNCONDITIONED (superseded 2026-08-27) | 12/29 = 41% | 15/37 = 41% | 12/27 = 44% |
| over-sabotage, **conditioned on the game continuing** - the honest figure | - | **11/28 = 39%** | **10/22 = 45%** |
| fallback rate | 0.49% (11/2231) | 0.54% (11/2033) | 1.78% (48/2691) |
| wall clock | - | 4h42m | 6h37m |

Two things this table now shows that no single column does:

- **The GATE row's point estimate is stable (+8.82 -> +9.00) while its floor verdict
  INVERTS** (+0.94 -> -0.25). At n=20 the floor's position relative to 0 is noise.
  Do not report "the floor cleared 0" as a finding at this N.
- **The taint-level row is a STEP, not a slope, in both runs that have it** - a real
  0->1 drop and no further response at 2 (`hunt20c`'s 1->2 leg is exactly flat). The
  linear "per extra saboteur" statistic is mis-specified for this shape, and the
  binary row is the better-behaved one. The scorer's "superseded by the graded slope"
  note has it backwards.
- `hunt20c`'s fail-card distribution is DERIVED (62 missions, 27 sunk, 39 cards, max 2
  fails at 5 seats => `{0:35, 1:15, 2:12}`), not read from a scorer field. The JSONL
  carries `fails_played` per GAME only.

| what | result | 2026-08-26 |
|---|---|---|
| **the sampler was never seeded** | same 20 games, seed 1000, twice: 63 missions / 9 hunts vs 74 / 11 | **`--seed` fixed the deal and the fallback RNG and NOTHING about the model.** Every "same seeds, one variable" number in this file was read against an unmeasured run-to-run spread |
| sampler pinned (`2cfe9d5`), verified on the instrument | two calls at seed 1000 to local `q36` byte-identical; seed 7 differs | llama.cpp honours `seed`; on cloud it is a best-effort hint and unproven until a repeat run shows it |
| `need` disclosure vs over-sabotage | 41% of sunk missions in both runs | disclosing the threshold did NOT reduce redundant sabotage - the problem is the missing focal point, not missing rules |

**2026-08-27 (S1)** - `docs/gate3a-retired.md`, `py -3 -m eval.gate3_arithmetic`.
Arithmetic only, no new games. The unconfounded gate-#3a cell splits in OPPOSITE
directions across the two runs and accrues at 0.30-0.40 votes/game; no cabal table
size reopens it.

Added 2026-08-27 (S3). No new games - the four scorer/audit numbers re-derived and
re-run over `hunt20b`/`hunt20c`. Each fix is mutation-checked: the pre-fix
derivation restored as a compiling mutant, killed by its own named test, restored.

| what | result | what it decides |
|---|---|---|
| **hunter baseline, derived** `1/len(legal_targets)` per hunt, meaned over hunts | **1/3 on `SETUP_5`** - unchanged, because the legal set is 3 in every game of it | **S6's pre-committed bar and power table stand as written.** The bar was RIGHT; what was wrong was that it was a constant. A 7p or blind-evil deal makes it 1/4 and the scorer now follows |
| a run whose hunts record no legal-target count | **REFUSED**, not defaulted | fails closed, same shape as the empty blind stratum - a default grades a record against whichever chance the reader assumed |
| **over-sabotage, conditioned on the game continuing** | `hunt20b` 15/37 -> **11/28 = 39%**; `hunt20c` 12/27 -> **10/22 = 45%** | the correction is real and it does NOT rescue the finding - 4 and 2 of the redundant cards were free, and the rate barely moves. Evil still over-sabotages ~2 of every 5 payable sinkings |
| **`outed_own_role_in_public`, matched against theme names** | 0/1290 (matcher-blind) -> `hunt20b` **4/1150**, `hunt20c` **26/1580 = 1.6%** | **the old zero was a property of the matcher, not of the play.** It looked for `seer`/`mimic` in speech that can only ever say "Thought Police"/"Inner Party". Seats DO name their own role in public, and `hunt20c` seat 0 does it repeatedly as cover |
| `hunt_named_impossible`, allies from `known_allies` | 0/11 and 0/9, unchanged on these runs | no regression on the shipping deal, and it stops flagging a legal hunt on a `stray` - which is a wrong PROOF-class finding, the worst kind this file can emit |

**2026-08-27, the mechanical denominator and the control ladder** -
`docs/reference-policies.md` §Results and §The control ladder,
`python -m eval.derivable`. 60 games of existing records, no GPU. Three findings:
derivable bits at the hunt are **0.000 and that is a theorem** (192,000
combinations), so a hunter above 1/3 reads BEHAVIOUR necessarily; the un-entitled
good seats read **flat** against what the record proved (+3.0%, gap crosses zero),
and the seer's +82.4% is entitlement rather than reading; a 60-line rule out-hunts
the model **94.3% to 48.3%**, so `captured` = 24.5%.

**This does NOT re-specify gate #3a or #3b**, and the S1 verdict stands in its own
words. The blind rows above score response to DERIVABLE taint; §Measured's
`+8.82%/+9.00%` rows score response to ACTUAL taint. Read together they say
something sharper than either: whatever the blind seats respond to, it is not the
mechanically derivable part.

## Decisions already locked

**Code invariants moved to `CLAUDE.md`** - it is always loaded, these are not,
and two copies of one rule is how the stale copy wins an argument. What stays
here is project state: the route calls and what a run measured.

- **A run writes its own terminal marker; a wrapper cannot be trusted to outlive
  it.** `core/runlog.py`, used by both eval drivers: `PARLOR DONE rc=N
  games=landed/requested elapsed=Ns`, written from a `finally` so it survives a
  crash, a `sys.exit` and a Ctrl-C. It contains `DONE rc=` so old greps still find
  it. **A log whose last line is a progress line is a killed run** - that is the
  whole point, and nothing writes the marker for a process killed outright. The
  `.cmd` echo stays for the one case python cannot cover: a crash before the driver
  runs at all.
- **`refused` is the fallback census; `note` is cabal's notebook.** Both games
  record the refusal that produced a fallback on the decision itself, so a run's
  refusal diagnosis is a census in the JSONL rather than a sampled trace (8/game)
  and an end-of-run report that does not exist until the run ends. It holds the
  last ATTEMPT's complaint, not the "N attempts failed" summary. Two consequences
  for old records: pre-2026-08-27 JSONL has no `refused` at all, and changeling's
  records before that date carry the same string under `note`.
- Independent context = one model + per-seat private context slice, not N brains.
- Referee is deterministic code; LLM only for players (and, later, judgment-GMs).
- Cloud is fine for game-fiction secrets (not credentials); local for deception checks.
- **`--rounds 2` cleared the rejection deadlock.** 1 of 8 games ended `five_rejects`
  at two discussion rounds, against 2 of 2 at one round. One round gives a vote
  nothing to reason from; treat 2 as the floor for any live run.
- **Pin a model for attribution, use `auto` for capacity - and record the served
  upstream either way.** The gateway fails over across its keys, but a pinned id can
  only hop between keys for providers serving that exact id, so a cooled provider
  returns an instant 429 with no hop available. `auto` has the whole catalog and
  keeps answering. The response body's top-level `model` is the ONLY thing that
  says who answered; `Backend.complete_meta` returns it and the report prints the
  mix, so an `auto` run is honest about being several models averaged.

## Design notes and reference - `docs/`

Durable material lives beside the code, not in the queue. This file stays the
queue, the dated measurements, and the route decisions.

- `docs/action-channel.md` - why free-text JSON stays the action channel, and the
  kernel/adjudicator split the RPG rung needs. Read before adding a second game's
  phases or touching `parse_action`.
- `docs/durf-rung.md` - the cheap version of the endgame rung, scoped 2026-08-27:
  a DURF session with a deterministic kernel under a model adjudicator, the
  False Pass / False Check / refusal number it produces against CoC-Seduce's
  9.58% floor, and the finding that DURF's secrets belong to the WORLD rather
  than to seats, which is the first evidence for fact-keyed entitlement in
  `core/`. Read before scoping any RPG rung, and before widening `find_leaks`.
  Its kernel table is pinned to DURF 2.2 and the doc now carries the fetchable
  source URL plus the version line to check on any re-read.
- `games/durf/fixtures/` - that rung's INSTRUMENT, labelled 2026-08-27 before any
  model ran: 48 declarations and 12 morale events, each carrying the rule it
  rests on. **Read its README before quoting any number from it.** Degenerate
  baselines are **61.9% always-roll / 38.1% never-roll** over the 42 declarations
  that admit a roll answer (54.2% / 33.3% over all 48) - the first draft's
  "never-roll 46%" pooled the six refusal traps into the no-roll bucket and is
  retracted there. Re-derived and source-verified the same day, which killed
  three of the six traps: the slot costs made `d013`, `d017` and `d018`
  satisfiable, so a model ruling them correctly would have scored a False Pass.
  The state moved to the labels, never the reverse, and every `slots_used` is now
  derivable from a `slot_costs` block. **The scorer landed 2026-08-28**
  (`eval/durf_score.py`); there is still no durf engine, and nothing here needs
  one - the fixture is 60 independent items against a fixed scenario.
- `docs/moral-framing.md` - the theme-polarity experiment, its confound, the
  verified deception/framing prior work, the name-form axis, and **§The changeling
  skin set, which owns every skin's design and sourcing rules** (moved out of this
  file 2026-08-28 - it was 134 lines of design in a queue). Arms 3 (`1984-inv`) and
  4 (`drill-en`) on cabal and the whole changeling set are BUILT and unrun; read it
  before running any of them, and before editing any blurb - the faces are
  length-matched on purpose and frozen.
- `docs/player-counts.md` - supported vs best-play sizes per rung, Secret Hitler's
  native blind-evil at 7+, and why a bigger cabal table worsens the denominator.
- **OFF-REPO, path in `CLAUDE.local.md`** - the neighbour list, the positioning
  argument and the raw notes behind both: who else has built this, what parlor
  claims and against whom, the licence and `DEFAULT_THEME` calls, and the ledger
  of what is still owed a first-hand read. **Read before publishing or writing an
  abstract, and before any writeup that quotes a gate #2 or #3 number.** It is out
  of the tree deliberately - see §Outstanding debt - and it does not come back in.
- `docs/reference-policies.md` - what a number is scored AGAINST: the mechanical
  solver (120 assignments, hard constraints only), the pinned spec and corpus, the
  additive-not-substitutive rule, the heuristic rung, and **§Results plus §The
  control ladder, which carry the three findings of 2026-08-27** - the hunt's
  MECHANICAL denominator is zero by proof, the un-entitled good seats read flat
  against what the record proved, and a 60-line rule out-hunts the model 94.3% to
  48.3% on the model's own records. Read before implementing any reference arm or
  quoting a gate as a fraction. Note §Results carries a same-day supersession: its
  "captured is undefined" line is about the mechanical arm only, and the ladder
  section is where the behavioural denominator lands.
- `docs/evidence-discipline.md` - how this repo handles a number, a citation, a
  run and its own record: the three rules for citing work nobody here has read,
  pre-commitment, why a rate over another gate's outcome is not projectable from
  one draw, and the render-control method that proves a freeze held. Read before
  quoting an outside source, before writing a criterion, and before claiming a
  refactor moved no model-facing byte.
- `docs/gate3a-retired.md` / `docs/gate3b-verdict.md` - cabal's two gate #3
  verdicts, each recomputable (`eval.gate3_arithmetic`, `eval.s6_verdict`). Read
  before restarting any cabal run or quoting either half.
- `docs/changeling-gate3-criterion.md` - changeling's pre-commitment, verbatim and
  not to be edited; the outcome is `games/changeling/RULES.md` §S2 read.
- `docs/gate3-modelling-review.md` - the 2026-08-26 review that sharpened the old
  blind gate, closed on all six items. **Read its header before its body** - its
  line citations are stale.
- `docs/faction-heartbeat.md` - Spike #2 scoped: the typed-fact channel, why it is
  the small version of the adjudicator's hardest part, and the one new gate #1
  failure it introduces (entitlement gains a time axis).
- `docs/reproducibility.md` - two 20-game runs at one seed came back byte-identical,
  so a same-seed repeat cannot measure spread. Read before scheduling ANY run whose
  purpose is variability, and before quoting a "+X% vs +Y%" comparison.

## Route: local IS the gate lane - corrected 2026-08-28

This section read "local is for spot-checks, not for gates", priced when a game cost
~9 min on a 12B and cabal was the only rung. Both gates have since been called on
local: S6's 40 games and S2's 200, the latter at 91s/game on `qwen36-35b-a3b-iq3`.
**A route claim priced against a retired model stays true-sounding until someone
re-reads it** - same failure as a queue item priced by a deleted cost
(`docs/evidence-discipline.md`).

Local is serial, exact-match and 100%-attributed, which beats a time-varying `auto`
mix as evidence. Cloud is capacity, not gates - its composition is anti-correlated
with what you are measuring (§Backend notes). Reach for a bigger local model only if
a cloud model turns out to REFUSE to deceive, or you want games beside image gen.

## Backend notes (measured 2026-08-25)

- `local` armed: `rocinante-x-12b-heretic-q4`. The heretic 12B
  deceives without any prompt escalation - the mimic fabricated a prior private
  conversation to build credibility, the hunter played concerned-loyalist and then
  correctly named the seer. `PLAYER_SYSTEM_PROMPT` needed no jailbreak. Cost: ~3s
  per decision, ~9 min per game, serial.
- **Burst-probe result, gray, 2026-08-25 23:10 - the single-call trap firing
  exactly as documented.** Pinned `gpt-oss-120b`: **1/12 served, 11 instant 429s**
  (`All models exhausted: 8 routes checked, 7 rate-limited or on cooldown, 1 no
  usable key`), and the ONE success was the FASTEST call of the set at 0.4s. A
  single-call probe would have reported the tier healthy and fast. This is why the
  `huntcloud` run sat alive for 72 minutes and wrote zero games: pinned to a model
  whose whole route pool was cooled, refused in 40ms, nothing to fail over to.
  Killed rather than waited out - free-tier cooldowns clear on nobody's schedule.
- **`auto` availability is NOT `auto` capability** (same probe, same minute).
  `auto` served **12/12 at 0.3s median** - but the upstreams were
  `gpt-oss-20b`, `gpt-oss-safeguard-20b` (x5), `nemotron-3-nano-30b-a3b` (x6). Not
  one 120B-class model: the big ones are exactly what is cooled. So `auto`'s
  composition is time-varying and **anti-correlated with the thing being measured**
  - it degrades precisely when capacity is short, which is when you reach for it.
  A gate run on tonight's `auto` would most likely read "hunter at chance" while
  actually measuring which models were uncooled at 23:10. Given -0.2% on the 12B
  vs +66% on 120B-class, a 20B/30B-nano mix sits near the at-chance end. False
  negative wearing a real number; worse than no run.
- `clean` needs `PARLOR_API_KEY`. Pin a model - `glm-4.7` is in `/v1/models`
  and 404s at call time (stale catalog entry), and `auto` silently varies the
  upstream per request. Live and answering: `minimax-m3`, `nemotron-3-super`,
  `qwen3-30b-a3b-fp8`, `gpt-oss-120b`, `glm-4.7-flash`. Bursts draw 429s - hence the
  transport backoff and `--workers 3`.
- **The cap was the cause, and 1536 is not enough for a rambler** (measured
  2026-08-25, same VOTE prompt, n=4 per cell, `clean`). `nemotron-3-super`:
  `max_tokens=512` -> 0/4 parsed, every reply ~2100 chars of visible reasoning cut
  mid-sentence; at 1536 -> 2/4, and both failures were ~6000 chars, i.e. truncated
  at the new cap too. So a model that thinks out loud does it at whatever length it
  likes and no cap is a fix. `gpt-oss-120b` answers in 80-125 chars, 4/4 at both
  caps - pin it for gate runs. `minimax-m3` itself is still unverified: the
  provider has been 429ing it since the void run, and a 429 is a transport failure,
  not a refusal. `qwen3-30b-a3b-fp8` and `glm-4.7-flash` currently 502.

**2026-08-27 (S6), the gate-#3b campaign** - `docs/gate3b-verdict.md`,
`py -3 -m eval.s6_verdict`. 40 games, seeds 2000/3000, frozen at `2c0e2a3`, 1.35%
fallback. **9/20 = 45.00%**, Wilson [25.82%, 65.79%] vs the derived bar 33.33% - NOT
SHOWN, at exactly the 0.50 hunts/game the power table assumed. All three
draw-dependent items came back negative there; **carry no run-length caveat
forward.**
