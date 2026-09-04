@echo off
setlocal
rem The DURF adjudicator fixture - one arm over all 60 labelled items.
rem
rem Usage:  eval\runs\durf-fixture.cmd [tag] [seed] [model] [temp] [extra-flag]
rem
rem   eval\runs\durf-fixture.cmd durf-q36-t0 5000 qwen36-35b-a3b-iq3 0.0
rem   eval\runs\durf-fixture.cmd durf-q36-nd 5000 qwen36-35b-a3b-iq3 0.0 --no-decline
rem
rem A launcher is an INPUT, not run output, so this is tracked - eval\records\ is
rem gitignored and a run recipe that is not versioned cannot be reviewed after it
rem misfires. Same contract as hunt-local.cmd and changeling-local.cmd.
rem
rem WHY IT EXISTS SEPARATELY, and it is not the usual reason. The two game
rem launchers wrap game drivers that deal and play; this wraps eval.durf_score,
rem which deals nothing - 60 independent items against one fixed scenario, no
rem kernel, no seats. Its flags do not overlap theirs (--no-decline, --limit, and
rem a --temperature that MATTERS here), and its unit is an item rather than a game.
rem
rem TEMPERATURE DEFAULTS TO 0.0 HERE, AND THAT IS THE ONE DELIBERATE DIVERGENCE
rem FROM THE DRIVER'S OWN DEFAULT. Measured 2026-08-28 (docs\durf-rung.md, the
rem temperature arm): greedy decoding is byte-identical across seeds on all 60
rem items and buys ~9.5pp of decision-1 accuracy over the 0.8 default, which is
rem Backend's PLAYER value and exists so a table's speech varies. A referee ruling
rem on rules gets nothing from it. Backend.temperature itself is NOT changed -
rem it is shared with both games and moving it would re-baseline every recorded
rem cabal and changeling number - so the flag lives here instead. Pass 0.8
rem explicitly to reproduce the first three runs.
rem
rem THE GATE IS A BURST, NOT A PING. Same reasoning as changeling-local.cmd, and
rem cheap insurance either way: a whole arm is under three minutes, so a probe
rem costs a fraction of what it protects. The local router is exact-match, so a
rem cold model answers 503 model_not_armed naming what IS live rather than
rem silently serving a smaller one. Arm the model with llm-serve first.

cd /d "%~dp0..\.."

set "TAG=%~1"
if "%TAG%"=="" set "TAG=durf-fixture"
set "SEED=%~2"
if "%SEED%"=="" set "SEED=5000"
set "MODEL=%~3"
if "%MODEL%"=="" set "MODEL=qwen36-35b-a3b-iq3"
set "TEMP=%~4"
if "%TEMP%"=="" set "TEMP=0.0"
set "EXTRA=%~5"

set "OUTDIR=eval\records"
set "LOG=%OUTDIR%\%TAG%.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The per-item JSONL is APPENDED as each item lands, so a stale one from an
rem earlier run of the same tag would silently double the file. REFUSE, never
rem clear: the occupant cost GPU-hours and clearing it is the operator's call.
rem The summary .json needs no line here either, and NOT because it is rewritten
rem - core.runlog.claim_record refuses on whichever of the two it finds.
if exist "%OUTDIR%\%TAG%.json.jsonl" exit /b 1

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
echo [gate] probe passed - 60 items, seed %SEED%, model %MODEL%, temp %TEMP% %EXTRA%.>>"%LOG%"

rem --no-thinking for the same reason every recorded changeling arm used it: this
rem model is a reasoning distill that can fail to TERMINATE its reasoning, and no
rem token cap fixes that. Every durf record on disk was written with it.
python -m eval.durf_score --arm llm --backend local ^
  --model "%MODEL%" --no-thinking --temperature %TEMP% --seed %SEED% %EXTRA% ^
  --out "%OUTDIR%\%TAG%.json" ^
  >>"%LOG%" 2>&1
rem durf_score writes its own `PARLOR DONE rc=` line from a finally and THAT is the
rem authoritative one. This stays for the case python's marker cannot cover: a
rem crash before the driver runs at all.
echo DONE rc=%ERRORLEVEL% ^(wrapper^)>>"%LOG%"
