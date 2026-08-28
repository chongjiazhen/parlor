# Content packs - how a rung ships without shipping its source material

**2026-08-28, unmeasured.** A design decision, not a result. It exists because
S8's endgame rung is a published TTRPG and the queue carried "the IP posture is
unchecked" as an open item. This is the answer in parlor's terms; it decides the
tree's shape and nothing about any particular system.

## The split

**parlor ships an engine, a schema and a loader. A rung's source material is a
pack, and most packs stay on the machine that plays them.**

This is the standard engine/content separation - the shape ScummVM, OpenMW and
OpenXcom use, where a reimplemented engine is public and the data files are the
operator's own. It is not a new pattern and does not need inventing; the reason
to write it down is that parlor's tree has to be arranged for it *before* the
first rung, because retrofitting it means moving files that a reader has already
cloned.

It also composes with what the tree already does. `core/` is what game #2
inherits and `games/<name>/` is what is about that game; a pack is one level
further out again - what is about a particular *table's* material.

## Layout

```
games/<rung>/
  RULES.md          tracked. parlor's own statement of what THIS implements
  schema.py         tracked. what a pack must provide
  referee.py        tracked. procedure
  packs/
    README.md       tracked. what belongs here and how to obtain it
    example/        tracked. a pack whose terms permit redistribution
    <local>/        gitignored
```

`packs/*/` is gitignored except the example. The `.gitignore` line carries no
comment and names nothing beyond the pattern, for the reason the hygiene
invariant already gives: a list of what is excluded is a map to it.

## The line, stated once

**Procedure ships. Expression does not.** A referee that computes whether a
seat's tier entitles it to a fact is procedure, and stays procedure however
faithfully it reproduces the behaviour it was modelled on. A file that restates
somebody's rules in their words, or in a close paraphrase of them, is not.

Two consequences that are easy to get wrong:

- **A complete table with the names changed is still that table.** Selection and
  arrangement is its own layer, so a pack that reproduces every entry of a
  published set in the same structure is a renamed copy rather than an
  implementation. Rungs take the smallest set that exercises the mechanism -
  four or five entries prove a schema; twenty is content volume, which the repo
  already declines to chase elsewhere.
- **The framing is a bigger exposure than the files.** A tree with no source
  material in it can still misuse a name by advertising itself with one. The
  standing invariant covers this - prose may name the game a rung is modelled
  on, canonical keys stay functional and branding-free - and it governs the
  README and the repo description, not only the code.

## The example pack is required

A rung whose `packs/` holds nothing runs for nobody, cannot be tested in CI, and
teaches a reader nothing about the schema. **Every rung ships one pack under
terms that permit it**, carrying its own LICENSE in its own directory, with the
root LICENSE left as unmodified MIT so the SPDX detector keeps reading it. The
example is the executable half of the schema documentation and the fixture the
loader is tested against. It is not a courtesy.

This is also the honest reason the arrangement is worth having rather than
merely permissible: **the pack format is the deliverable.** A rung that loads a
pack is a rung anyone can point at their own material, which is worth more than
a rung wired to one system.

## Local is not the same as untransmitted

parlor's entire mechanism is rendering bytes into a model's context. A pack that
stays out of the tree still reaches whatever backend serves the seats, so
"local" here means *not distributed*, never *not sent*. A material-heavy pack is
therefore an argument for a local backend, and that is a routing decision the
operator makes per run, not something the loader should decide.

Gate #1 is unaffected either way: it audits what each seat receives against what
that seat is entitled to, and where the bytes originated is not one of its
inputs.

## What this does not decide

Nothing here says which systems can ship a pack, which cannot, or on what terms.
That is a per-source reading, it is assessment of somebody else's work, and it
belongs in the working notes rather than the tree - the same division
`docs/action-channel.md` already draws, where the design half is in-repo and the
competitive half is not.

The schema itself is also undecided. It should be written against the first two
rungs rather than in advance, because a pack format designed before two rungs
exist will encode one of them.
