@echo off
setlocal
rem Belfry S8 adjudicator paired arm - frozen 2026-08-31T08:13:07Z.
rem
rem This is a tracked recipe, not run output. It first burst-probes the exact
rem local adjudicator route, then writes the random control and model arm to the
rem distinct summary and JSONL paths bound by docs\belfry-adjudicator-criterion.md.
rem Do not launch a GPU/model arm from this recipe until the operator has armed
rem qwen36-35b-a3b-iq3 and verified the probe's logged result.

cd /d "%~dp0..\.."

set "OUTDIR=eval/records"
set "MODEL=qwen36-35b-a3b-iq3"
set "CONTROL=%OUTDIR%/belfry-adjudicator-control.json"
set "MODEL_OUT=%OUTDIR%/belfry-adjudicator-model.json"
set "LOG=%OUTDIR%/belfry-adjudicator-launch.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem JSONL is append-only. A retry over old evidence duplicates game seeds and
rem guarantees a VOID, so archive or remove every bound path before launch.
if exist "%CONTROL%" (
  echo [gate] bound evidence exists: %CONTROL% - archive or remove it first.
  exit /b 1
)
if exist "%CONTROL%.jsonl" (
  echo [gate] bound evidence exists: %CONTROL%.jsonl - archive or remove it first.
  exit /b 1
)
if exist "%MODEL_OUT%" (
  echo [gate] bound evidence exists: %MODEL_OUT% - archive or remove it first.
  exit /b 1
)
if exist "%MODEL_OUT%.jsonl" (
  echo [gate] bound evidence exists: %MODEL_OUT%.jsonl - archive or remove it first.
  exit /b 1
)

rem A ping can pass on a cooled or wrong route. Three completion requests prove
rem the exact model route before this 60-game arm spends the local serial lane.
echo [gate] burst-probing local/%MODEL% before either S8 arm...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - see %LOG%.
  exit /b 1
)

rem Random players stay random in both sides. The control deliberately supplies
rem no adjudicator route: seeded referee RNG is the only discretion source.
py -3 -m eval.run_belfry --games 60 --arm random --seats 5 --script compact ^
  --rounds 1 --no-thinking --seed 6100 --adjudicator random ^
  --out "%CONTROL%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

rem Only this route moves. It is separate from player routing, and the driver
rem fixes its temperature at 0.0; do not add a player backend/model to this arm.
py -3 -m eval.run_belfry --games 60 --arm random --seats 5 --script compact ^
  --rounds 1 --no-thinking --seed 6100 --adjudicator model ^
  --adjudicator-backend local --adjudicator-model "%MODEL%" ^
  --timeout 120 --out "%MODEL_OUT%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

rem A finished model arm is still unusable if its bound controller finds a void,
rem recipe mismatch, missing evidence, or disagreement between summary and JSONL.
py -3 -m eval.belfry_adjudicator_verdict "%CONTROL%" "%MODEL_OUT%" >>"%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo DONE rc=%RC% ^(wrapper^)>>"%LOG%"
if %RC% NEQ 0 exit /b %RC%
exit /b 0
