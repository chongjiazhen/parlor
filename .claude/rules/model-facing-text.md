---
paths:
  - "core/backends.py"
  - "games/**/referee.py"
  - "games/**/player.py"
---

# Text a model reads

Most strings in these files are not documentation - they are the prompt. The
system preamble, `action_prompt`, `render_context`, and the refusal text the retry
loop feeds back all land in a player's context and change how it plays. Two rules
apply to them and to nothing else in the repo.

## Prompt the positive

State the target behaviour. A prohibition drags the forbidden behaviour into
context and makes it MORE available: say *don't think of an elephant* and the
elephant is all there is, because the negation is a weak modifier over a strongly
activated concept. "Speak to the other seats; your own lines are marked (you)"
beats "do not answer your own earlier lines".

Keep a prohibition only where it is a hard guardrail with no positive phrasing -
a rule the referee enforces anyway - and pair it with the positive target so
attention lands on what to do.

## A prompt edit is a measured change

Editing one of these strings changes agent behaviour, so it is an experiment, not
a cleanup. Land it the way every other lever landed:

- **Same seeds, one variable.** `--seed N` with everything else fixed. Two changes
  at once and neither result is attributable.
- **Isolated first, in-game second, and expect them to disagree.** The seer
  salience line moved the decision 46 points in an isolated bench and ONE point in
  a live game - twenty lines of table talk sat between the fact and the decision.
  A bench win is a hypothesis; the game is the measurement.
- **Report it beside its fallback rate.** A prompt a model cannot answer legally
  shows up as fallbacks, and a run above 10% is the random policy wearing a
  model's name.
- **Keep the change only if a number moved.** No measured benefit anywhere means
  the line is load with no payer, whatever it looked like when written.
