@echo off
setlocal
rem The DURF session engine - N live sessions with the entitlement audit on.
rem
rem Usage:  eval\runs\durf-session.cmd [tag] [seed] [model] [sessions] [rounds]
rem
rem   eval\runs\durf-session.cmd durf-sess 4200 qwen36-35b-a3b-iq3 5 3
rem
rem A launcher is an INPUT, not run output, so this is tracked - eval\records\ is
rem gitignored and a run recipe that is not versioned cannot be reviewed after it
rem misfires. Same contract as durf-fixture.cmd and hunt-local.cmd.
rem
rem WHAT THIS RUNS THAT durf-fixture.cmd DOES NOT. That one wraps eval.durf_score:
rem 60 independent items against a fixed scenario, no kernel, no seats, and - in
rem its own words - no exercise of gate #1 at all. This wraps eval.durf_session:
rem three player seats, a deterministic kernel, and the entitlement audit on every
rem render. Its unit is a session, not an item, and the two are not comparable.
rem
rem RUN THE FREE CONTROL FIRST, EVERY TIME:
rem
rem   py -3 -m eval.durf_session --arm scripted --sessions 3 --seed 4200
rem
rem It needs no model and no GPU. Its referee declares before it narrates by
rem construction, so a leak in it means the ENGINE leaks and nothing from a live
rem arm means anything until that is fixed.
rem
rem TEMPERATURE DEFAULTS TO 0.0 IN THE DRIVER, for the reason durf-fixture.cmd
rem records: measured 2026-08-28, greedy decoding is byte-identical across seeds
rem and buys ~9.5pp of decision-1 accuracy over the 0.8 player default, which
rem exists so a table's SPEECH varies. Backend.temperature itself is unchanged -
rem it is shared with both games and moving it would re-baseline every recorded
rem cabal and changeling number.
rem
rem THE GATE IS A BURST, NOT A PING. Same reasoning as durf-fixture.cmd: the local
rem router is exact-match, so a cold model answers 503 model_not_armed naming what
rem IS live rather than silently serving a smaller one. Arm the model with
rem llm-serve first.

cd /d "%~dp0..\.."

set "TAG=%~1"
if "%TAG%"=="" set "TAG=durf-session"
set "SEED=%~2"
if "%SEED%"=="" set "SEED=4200"
set "MODEL=%~3"
if "%MODEL%"=="" set "MODEL=qwen36-35b-a3b-iq3"
set "SESSIONS=%~4"
if "%SESSIONS%"=="" set "SESSIONS=5"
set "ROUNDS=%~5"
if "%ROUNDS%"=="" set "ROUNDS=3"

set "OUTDIR=eval\records"
set "LOG=%OUTDIR%\%TAG%.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The per-session JSONL is APPENDED as each session lands, so a stale one from
rem an earlier run of the same tag would silently double the file. The summary
rem .json is rewritten and needs no such care.
if exist "%OUTDIR%\%TAG%.json.jsonl" del "%OUTDIR%\%TAG%.json.jsonl"

echo [control] the free scripted arm before spending a live one...>>"%LOG%"
python -m eval.durf_session --arm scripted --sessions 3 --rounds %ROUNDS% ^
  --seed %SEED% >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [control] the scripted arm did not pass ^(rc=%ERRORLEVEL%^) - the engine, not the model. Not launching.>>"%LOG%"
  echo [control] the scripted arm did not pass ^(rc=%ERRORLEVEL%^) - see %LOG%.
  exit /b 1
)

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
echo [gate] probe passed - %SESSIONS% sessions x %ROUNDS% rounds, seed %SEED%, model %MODEL%.>>"%LOG%"

rem --no-thinking for the same reason every recorded durf and changeling arm used
rem it: this model is a reasoning distill that can fail to TERMINATE its reasoning,
rem and no token cap fixes that.
python -m eval.durf_session --arm llm --backend local ^
  --model "%MODEL%" --no-thinking --sessions %SESSIONS% --rounds %ROUNDS% ^
  --seed %SEED% --out "%OUTDIR%\%TAG%.json" ^
  >>"%LOG%" 2>&1
rem durf_session writes its own `PARLOR DONE rc=` line from a finally and THAT is
rem the authoritative one. This stays for the case python's marker cannot cover: a
rem crash before the driver runs at all.
echo DONE rc=%ERRORLEVEL% ^(wrapper^)>>"%LOG%"
