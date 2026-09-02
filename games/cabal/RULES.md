# cabal - the rules, and who learns what

The canonical statement of this game's model. It exists because three separate
things depend on it and until now none of them could be checked against anything:
the gate #3a strata, `eval/audit_decisions.py`, and the hunt baseline
`RandomPolicy` draws against. Before this file, reading a gate number meant reconstructing the
knowledge model from boolean flags in `roles.py` and the derivation in
`referee.entitled_knowledge`.

Rules live here, next to the game, not in `docs/` - `core/` is what game #2
inherits, `games/<name>/` is what is about that game. Game #2 gets its own
`RULES.md`; nothing here is meant to generalise.

Modelled on The Resistance: Avalon. Nominative reference only - no role name, art
or text from any published game appears in the code. The canonical layer uses
functional keys.

## Seats and what the night tells them

Five seats, three good, two evil. `SETUP_5` in `roles.py`.

| seat key | side | what the night tells it | knowledge class |
|---|---|---|---|
| `seer` | good | **both evil seats, by identity** | `identity` |
| `watcher` | good | an **aura pair** - `{seer, mimic}` - one of the two is evil, not which | `aura` |
| `loyalist` | good | nothing | `none` |
| `mimic` | evil | its partner (`hunter`). Also *carries* the aura, so the watcher cannot tell it from the seer | `identity` |
| `hunter` | evil | its partner (`mimic`) | `identity` |

### Two evils no shipped setup seats yet

`agent` is generic evil for larger counts. Two more exist as data only - defined,
named in every skin, dealt by nothing:

| seat key | side | what the night tells it | and what it costs the others |
|---|---|---|---|
| `lurker` | evil | its fellow evil, as `agent` does | the **seer does not see it** (`seen_by_seer=False`) |
| `stray` | evil | **nothing** (`sees_fellow_evil=False`) | its own side does not see it either; the seer still does |

They are 7+ roles: at five seats the seer would see exactly one evil, or two evils
would play knowing nothing of each other, and either is swing rather than signal.
What they buy is stated in `queue.md` - they degrade information in a principled
way, which is what turns the seer's measured edge into a claim about deduction and
gate #2 into deception between agents that were never introduced.

The knowledge class is what gate #3a stratifies on, and it is a different axis
from side: a good seat can hold identity knowledge (the seer does). Naming the
class `evil` put two opposite meanings of the word on one seat, so the classes are
`identity` / `aura` / `none`. Evil votes are filtered out of the discrimination
metric before stratification, so in the gate the three strata are exactly
seer / watcher / loyalist - one seat each per game.

Every reveal is derived in `referee.entitled_knowledge` from flags on `Role`
(`sees_evil`, `seen_by_seer`, `sees_fellow_evil`, `seen_by_fellow_evil`,
`sees_magic`, `shown_to_watcher`), never hardcoded per role. Variants change data,
not code - which is why the classes are derived from labels rather than role keys.

### What each seat can DERIVE

Not written anywhere in the prompts; a strong player finds it.

- **Watcher.** It knows `{seer, mimic}` holds exactly one evil. Two evils exist and
  it is not one, so `{hunter, loyalist}` - the other two seats - holds exactly one
  evil too. **A 2-seat team that is either of those pairs is certified tainted**
  without deduction. This is why the watcher is not "blind" and cannot sit in the
  gate's blind stratum.
- **Evil pair.** Both know both identities and the proposal is public, so a
  convention is available with no communication: e.g. "the lower-numbered evil on
  this team plays the fail card". Sharing a mission with no such convention is an
  anti-coordination problem - see `eval/audit_decisions.py` over-sabotage.
- **Seer.** It knows every clean team is clean, so it can certify as well as
  accuse. That certification is handed knowledge and is why `p_clean` must be
  restricted to the blind stratum before it means anything.

## Flow

`PROPOSE -> DISCUSS -> VOTE -> (MISSION | back to PROPOSE) -> ... -> CONFER -> HUNT`

1. **Propose.** The leader names a team of exactly `team_sizes[mission]` distinct
   seats, and may include itself.
2. **Discuss.** Round-robin from the leader, `discussion_rounds` passes (default 1;
   2 is the measured floor - one round leaves a vote nothing to reason from).
   One utterance each, at most 280 characters. Only the nominated `say` string is
   published; a seat's private `think` reaches no one.
3. **Vote.** Every seat votes approve/reject. **Strict majority passes**
   (`approvals * 2 > n`, so 3 of 5). The tally, the outcome, and **which seats
   approved** are all public.
   - Passed: reject streak resets, go to Mission.
   - Rejected: streak increments, leadership passes to the next seat.
     **Five rejections in a row and the mission-runners lose outright.**
4. **Mission.** Each seat on the team plays a card in secret. Good **may only play
   success** - the referee refuses a good fail. The mission fails if
   `fails_required[mission]` or more fails are played (always 1 at 5 seats).
   **Only the COUNT is public; who played which card never is.** Leadership
   advances, the reject streak resets.
5. **Confer.** Reached when good holds three missions, before the name. Each evil
   seat the night introduced to a partner says one thing, in seat order, on a
   channel **only those seats receive**. Same shape as an utterance - one `say`
   string, at most 280 characters, private `think` reaching no one - with a
   different destination: it is never a public fact and never table talk.
   **This is a THIRD channel, and the audit carries it** (`audit.conference_audit`):
   each rendered line is a secret of its speaker, entitled to the pair by the deal,
   so a byte of it in any other seat's payload is a gate #1 failure rather than a
   rules quirk. `find_leaks` stays naive - the term is the whole rendered line, so a
   good seat repeating the words out loud is gameplay and does not trip it.
   - **The channel is derived from `known_allies`, not from `Team.EVIL`.** It exists
     exactly between seats already introduced to each other, so under the blind-evil
     variant (`stray`, `sees_fellow_evil=False`) no pair is named and the hunt
     follows the third mission directly. That is the same one definition
     `entitled_knowledge`, `legal_hunt_targets` and the decision audit read, so a
     variant that changes what the night tells a seat moves the channel with it.
6. **Hunt.** The hunter names one seat as the seer. Right, evil takes the game;
   wrong, good keeps it.

**The conference re-baselines cabal's rung** (built 2026-09-02). It was a declared
house rule that no evil-only channel existed and the hunt followed the third
mission directly; it now exists, so every seat in the pair receives bytes it did
not receive before. Gate #1's corpus grew a class of secret, gate #3's deception
surface grew a private one, and the gate #2 hunt figures were measured against a
pair that could not coordinate. **A number recorded before this date was measured
on a different game** - `docs/measurements.md` is the ledger of which.

Mission team sizes at 5 seats: **2, 3, 2, 3, 3**. Fails required: **1** for all
five. (At 7+ seats mission 4 requires 2 fails - `fails_required` is a per-mission
tuple, so a 7p setup left at all-ones is silently the wrong game.)

## Win conditions

Evil wins by any of: three missions failed, five consecutive rejections, or the
hunter naming the seer. Good wins by holding three missions **and** surviving the
hunt. Good has no other route.

## Hunt legality

The hunter may not name a seat it **knows** is evil - that is not a bad read, it is
an impossible one, since the seer is good. Two such seats:

- its night-named partner, and
- **itself**.

Both are refused, not silently corrected: the retry loop hands the seat the reason
and it names again. This also keeps the scorer honest - one function,
`roles.legal_hunt_targets`, answers all three questions: what the referee refuses,
what `RandomPolicy` draws from, and what the gate's chance figure is `1/len` of.
Any target left legal here that the control will not pick scores the model against
a baseline using knowledge the model was allowed to throw away.

**The baseline is 1-in-3 only on this deal, and the scorer no longer assumes it.**
Three candidates is what is left at 5 seats with a hunter its partner was named to.
At 7p/3-evil the legal set is 4, and under the blind-evil variant (`stray`) it is 4
at 5 seats too - and the referee and the control both derive it from
`entitled_knowledge`, so under a variant they would silently agree on the wider set
while a hardcoded `1/3` kept grading against the narrower one, in the flattering
direction. Every hunt records the size of the set it faced (`hunt.legal_targets`);
the run-level chance is the mean of `1/k` over the hunts, and a record that carries
no such count is REFUSED rather than defaulted.

## The two public channels, and the line between them

- **Events** are referee-authored facts: proposals, vote tallies with the aye list,
  mission fail counts, phase transitions. Audited by gate #1 - a referee that named
  a role here would be leaking.
- **Speech** is what a seat chose to say. A lie there is gameplay, not a leak, so
  the audit skips it (`render_context(seat, include_speech=False)`).
- **Private reasoning reaches neither.** A seat's `think` is kept only in the
  referee-side transcript, which no model ever receives.
- **The conference is a channel with exactly two readers.** The pair's words
  before the strike (step 5) are rendered to the pair and to nobody else. Unlike
  speech, it does NOT leave the gate #1 view: it leaves the ROLE-name audit view
  with speech, because a partner calling a seat the seer is a claim - and it is
  then audited by `audit.conference_audit` in its own right, over the full payload
  of every seat, as a secret of its speaker. Speech is checked for what the referee
  said; the conference is checked for who received it.
- **The notebook is a channel with exactly one reader, its author.** With
  `--notebook` on (off by default), a seat's `note` is filed under that seat and
  rendered back to that seat alone on every later call, bounded to its last 6 lines
  of 160 characters. It leaves the gate #1 audit view with speech, and for a
  sharper reason: `find_leaks` is naive substring matching, so a seat writing down
  a correct *guess* would score as a leak the referee never made. The gate is not
  weakened by it - the only writer of seat N's notebook is seat N, working from
  bytes it had already been given, and the only reader is seat N.

Consequence worth stating because it drives play: votes are public **with
attribution**, and the hunter knows the ground-truth taint of every historical team
because it knows itself and its partner. So it can compute any good seat's exact
clean-versus-tainted voting split from the public record. A seer that discriminates
perfectly is not merely at risk of a tell - it is identifiable by arithmetic. That
is what makes concealment real play rather than a lapse.

## Themes are display-only

`Theme` renames factions and roles and carries a premise blurb. It changes no rule,
no entitlement, and no byte of private knowledge. **Default is `lodge` since
2026-08-28** - a fraternal-order vocabulary referencing nothing under a live mark
or copyright, and carrying no blurb, so the premise skins stay a clean contrast set
against a premise-free default. The dystopia skin it replaced is still shipped as
`--theme 1984-en`, and **every cabal number recorded before 2026-08-28 was played
on that face**; a run meant to compare against one must pass it explicitly.
`--theme plain` is the sterile fallback, as in every rung. Because a theme changes only what a seat
believes it is doing, swapping it is the cleanest available experimental
manipulation - and, for the same reason, a MEASURED change rather than a cosmetic
one.
