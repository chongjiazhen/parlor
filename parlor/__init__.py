"""The command a person types. Everything the arena does lives in ``core/``,
``games/`` and ``eval/``; this package holds one entry point over the registry
and no game logic, so that ``py -3 -m parlor play <game>`` reads the way a player
would guess and nothing else has to move to make it."""
