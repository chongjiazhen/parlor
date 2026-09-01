@echo off
setlocal
rem belfry live arm #1, EXACTLY as docs\belfry-live1-criterion.md promised it.
rem
rem Usage:  eval\runs\belfry-live1.cmd
rem
rem IT TAKES NO ARGUMENTS, AND THAT IS THE POINT. belfry-local.cmd is the general
rem launcher and its defaults are a convenience; this one is a criterion. N,
rem temperature, seed, seats, script and round count are written into the file
rem because a criterion-bound arm has nothing an operator is allowed to get wrong
rem at the command line - and the first attempt at this arm got three of them
rem wrong precisely because they were parameters read off a queue row.
rem
rem THE DIVERGENCES FROM belfry-local.cmd ARE THE WHOLE REASON IT EXISTS:
rem   --temperature 0.0   the criterion's call. A vote is an adjudicable decision
rem                       rather than table speech, and a sampled one adds variance
rem                       to the figure this arm exists to read.
rem   NO --no-thinking    the criterion does not carry it. belfry-local.cmd passes
rem                       it because changeling's arms all did; that is a property
rem                       of THAT rung's recorded history, not of this promise.
rem   --games 60          fixed in advance, no stopping rule.
rem
rem KNOWN RISK, STATED BEFORE THE RUN. q36 is a reasoning distill and without
rem --no-thinking it can fail to TERMINATE its reasoning, which no token cap fixes.
rem If that happens the fallback rate rises and the criterion's own 10% void
rem condition fires. A void is a RESULT here, not a failed run: it says this arm
rem cannot be read at the settings its criterion promised, which is a fact worth
rem having and is why the criterion is not edited to avoid it.
rem
rem THE RECORD PATH IS PART OF THE CRITERION. eval.belfry_live1_verdict binds on
rem it, so this writes eval\records\belfry-live1.json and nowhere else. The
rem off-criterion 100-game run that previously held that name was copied aside to
rem belfry-live1-offcriterion.* before this recipe was first used; it is what
rem transcripts\belfry-live1.md and docs\measurements.md still describe.

cd /d "%~dp0..\.."

set "MODEL=qwen36-35b-a3b-iq3"
set "OUTDIR=eval\records"
set "LOG=%OUTDIR%\belfry-live1.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The per-game JSONL is APPENDED as each game lands, so a stale one from the
rem previous occupant of this name would silently double the file.
if exist "%OUTDIR%\belfry-live1.json.jsonl" del "%OUTDIR%\belfry-live1.json.jsonl"

echo [gate] burst-probing local/%MODEL% before spending a run...>>"%LOG%"
python -m eval.probe_tier --backend local --model "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
rem FAIL CLOSED. `if errorlevel 1` means "errorlevel >= 1" and is FALSE for a
rem negative code, so a probe that is killed or crashes (rc=-1) would read as a
rem pass and launch against an untested router. Only an explicit 0 is a pass.
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - see %LOG%.
  exit /b 1
)
echo [gate] probe passed - the criterion arm: 60 games, temp 0.0, no --no-thinking.>>"%LOG%"

python -m eval.run_belfry --games 60 --arm llm --seats 5 --script compact ^
  --rounds 1 --backend local --model "%MODEL%" --temperature 0.0 ^
  --seed 6100 --timeout 240 ^
  --out "%OUTDIR%\belfry-live1.json" ^
  >>"%LOG%" 2>&1
rem run_belfry writes its own `PARLOR DONE rc=` line from a finally and THAT is the
rem authoritative one. This stays for the case python's marker cannot cover: a
rem crash before the driver runs at all.
echo DONE rc=%ERRORLEVEL% ^(wrapper^)>>"%LOG%"
