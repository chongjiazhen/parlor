# packs

A pack is one table's material: the playbooks a draft chooses from, as JSON.
`experiments/ensemble/pack.py` is the loader and `RULES.md` is what the engine does
with it. The layout and the reasoning are `docs/content-packs.md`.

A pack directory holds `playbooks.json`:

```json
{"pack": "<label>",
 "playbooks": [{"name": "THE ...",
                "about": "One or more sentences. The first is the menu hook.",
                "questions": [{"question": "what do i want?",
                               "options": ["...", "write your own"]}]}]}
```

Names must be unique and non-empty; the loader refuses a pack that breaks either.

Subdirectories here are not tracked, except `example/`, which every rung owes:
it is the fixture the loader is tested against and the executable half of the
schema. Point `--pack` at any directory to use your own.
