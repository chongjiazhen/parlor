@echo off
setlocal
rem Belfry S8b adjudicator paired arm - frozen 2026-08-31T12:51:51.7954079Z.
rem Bound by docs\belfry-adjudicator-v2-criterion.md.

cd /d "%~dp0..\.."

set "OUTDIR=eval/records"
set "MODEL=qwen36-35b-a3b-iq3"
set "CONTROL=%OUTDIR%/belfry-adjudicator-v2-control.json"
set "MODEL_OUT=%OUTDIR%/belfry-adjudicator-v2-model.json"
set "LOG=%OUTDIR%/belfry-adjudicator-v2-launch.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

if exist "%CONTROL%" exit /b 1
if exist "%CONTROL%.jsonl" exit /b 1
if exist "%MODEL_OUT%" exit /b 1
if exist "%MODEL_OUT%.jsonl" exit /b 1

echo [gate] burst-probing local/%MODEL% before either S8b arm...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.run_belfry --games 60 --arm random --seats 5 --script compact ^
  --rounds 1 --no-thinking --seed 6100 --adjudicator random ^
  --out "%CONTROL%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.run_belfry --games 60 --arm random --seats 5 --script compact ^
  --rounds 1 --no-thinking --seed 6100 --adjudicator model ^
  --adjudicator-backend local --adjudicator-model "%MODEL%" ^
  --timeout 120 --out "%MODEL_OUT%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.belfry_adjudicator_verdict --v2 "%CONTROL%" "%MODEL_OUT%" >>"%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo DONE rc=%RC% ^(wrapper^)>>"%LOG%"
exit /b %RC%
