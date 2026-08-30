@echo off
setlocal
rem belfry, local route - the rung's first live arm and every one after it.
rem
rem Usage:  eval\runs\belfry-local.cmd [tag] [games] [seed] [model] [arm] [seats] [script]
rem
rem   eval\runs\belfry-local.cmd belfry-live1 100 6100 qwen36-35b-a3b-iq3 llm 5 compact
rem
rem A launcher is an INPUT, not run output, so this is tracked - eval\records\ is
rem gitignored and a run recipe that is not versioned cannot be reviewed after it
rem misfires. Same contract as hunt-local.cmd, changeling-local.cmd and
rem durf-fixture.cmd.
rem
rem WHY IT EXISTS SEPARATELY. eval.run_belfry takes two flags no other driver has,
rem and both of them decide which recorded number an arm may be read against:
rem --seats, whose cost is roughly quadratic (~49 decisions at 5 seats, ~183 at 9),
rem and --script, where a number recorded on one script says nothing about the
rem other. Defaulting them HERE rather than passing them by hand is the point: the
rem random control lives at one cell and an arm that misses the cell is not a
rem comparison, it is a second control nobody asked for.
rem
rem THE DEFAULTS ARE THE CONTROL'S CELL, NOT A TASTE. 5 seats, compact, --rounds 1,
rem seed 6100 is exactly where docs\measurements.md's belfry control was measured
rem (200 games: day-1 execution accuracy 40.00%, 44/110, on a 40.00% chance board;
rem good-seat vote accuracy 50.44% over n=2601; 0.00% fallback). Changing any of
rem the four re-baselines the arm against nothing, so change them only with a new
rem control at the new cell.
rem
rem TEMPERATURE IS THE DRIVER'S OWN 0.8 AND STAYS THERE. Unlike durf-fixture.cmd,
rem which overrides it, these are PLAYER seats: 0.8 is Backend's player value and
rem exists so a table's speech varies. The greedy-decoding argument is about a
rem referee ruling on rules and does not reach here.
rem
rem THE GATE IS A BURST, NOT A PING. Same reasoning as changeling-local.cmd. The
rem local router is exact-match, so a cold model answers 503 model_not_armed
rem naming what IS live rather than silently serving a smaller one - but a run
rem that spends nine hours discovering that is the same wasted run. Arm the model
rem with llm-serve first, and VERIFY it: `serve.py gpu <key>` only spawns when
rem :8080 is unbound, so against an already-serving port it exits 0 and changes
rem nothing. Read /v1/models, not the exit code.

cd /d "%~dp0..\.."

set "TAG=%~1"
if "%TAG%"=="" set "TAG=belfry-local"
set "GAMES=%~2"
if "%GAMES%"=="" set "GAMES=20"
set "SEED=%~3"
if "%SEED%"=="" set "SEED=6100"
set "MODEL=%~4"
if "%MODEL%"=="" set "MODEL=qwen36-35b-a3b-iq3"
set "ARM=%~5"
if "%ARM%"=="" set "ARM=llm"
set "SEATS=%~6"
if "%SEATS%"=="" set "SEATS=5"
set "SCRIPT=%~7"
if "%SCRIPT%"=="" set "SCRIPT=compact"

set "OUTDIR=eval\records"
set "LOG=%OUTDIR%\%TAG%.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The local router is keyless; require_key() lets `local` through with nothing set.

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
echo [gate] probe passed - %GAMES% games, arm %ARM%, %SEATS% seats, script %SCRIPT%, seed %SEED%, model %MODEL%.>>"%LOG%"

rem --no-thinking because the control used it and because this model is a
rem reasoning distill that can fail to TERMINATE its reasoning, which no token cap
rem fixes. --rounds 1 is the control's value and the largest single lever on cost.
python -m eval.run_belfry --games %GAMES% --arm %ARM% --seats %SEATS% ^
  --script %SCRIPT% --rounds 1 --backend local ^
  --model "%MODEL%" --no-thinking --seed %SEED% --timeout 240 ^
  --out "%OUTDIR%\%TAG%.json" ^
  >>"%LOG%" 2>&1
rem run_belfry writes its own `PARLOR DONE rc=` line from a finally and THAT is the
rem authoritative one - hunt6b finished cleanly and wrote no wrapper line because
rem cmd.exe did not survive to echo one. This stays for the case python's marker
rem cannot cover: a crash before the driver runs at all.
echo DONE rc=%ERRORLEVEL% ^(wrapper^)>>"%LOG%"
