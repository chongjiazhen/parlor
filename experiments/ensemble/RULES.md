# ensemble - rules and knowledge model

A GM-less ensemble drama: seats play recurring characters whose storylines
collide across scenes. **This file is the canonical statement of what the code
implements**, and only session 0 - the playbook draft - is implemented so far.

`ensemble` is a provisional name for the rung, not a system. The rules of any
particular drama system live in a pack (`docs/content-packs.md`), most of which
stay on the machine that plays them; nothing in this directory names one.

## Session 0 - the draft

- A pack offers **playbooks**: named characters, each a set of questions with
  picklists a player answers to make the character their own.
- Seats draft in turn order. Each seat takes exactly one playbook, and **no two
  seats may hold the same one**.
- A seat that names a playbook already taken, names one the pack does not have,
  or fails to answer at all, has made an **illegal move**. The random policy
  plays it - a uniform draw from what is left - and it is **counted**. Every
  number this rung reports ships beside its fallback rate, and the scorer's 10%
  void applies unchanged.
- **A transport failure costs the seat, never the run.** A provider that accepts
  the connection and then stalls, or an endpoint that is gone, is absorbed after
  the seat's retry budget and played as an illegal move like any other - and
  counted twice over, once in the fallback rate and once in `transport_errors`,
  which is reported beside it. The second count is the point: a dead endpoint
  drives the fallback rate to 100% and would otherwise read as a model that could
  not follow the rules. Only transport exceptions are absorbed; a bug in this repo
  still crashes the run rather than being recorded as a decision nobody made.
- A fallback plays a *real* pick, so it genuinely removes that playbook. A later
  seat asking for it is then making an illegal move of its own and is counted as
  one. This is the rate doing its job rather than double-counting: it measures
  decisions the run could not honour.

## The knowledge model - there is nothing to hide

**Every seat sees the same menu and the same taken list. No seat holds anything
another seat may not.** That is a property of the game and not a simplification:
the whole point of a draft is that it is public.

Two consequences, both deliberate.

- **Gate #1 has an empty secret set here, so this rung does not call an audit.**
  An audit over no secrets is vacuously green, and a green that proves nothing is
  the failure mode the repo's verification rule names by name. The rung that
  earns gate #1 is elsewhere; this one does not pretend to.
- **What it does measure is the pick distribution.** Whether seats collapse onto
  the same few playbooks is a diversity read, and it has a human ranking to
  correlate against rather than only a uniform null. `docs/open-arms.md`
  §Session-0 carries the argument for why this is the rung's first slice.

## The ask is a budget

The choose-phase context carries **a name and one line per playbook**, plus what
is already gone - not a sheet each. A seat choosing between characters needs to
tell them apart; it does not need to fill one in. The full sheet reaches the seat
that took it, at the phase where it is actionable.

This is a position rather than an omission, and it is measurable: a run that
sends every sheet is the arm against it, written by handing each seat
`Pack.sheet()` for all of them. It is not written by editing `seats.py`.
