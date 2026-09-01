@echo off
setlocal
rem Belfry S23 steered-discretion arm - frozen 2026-09-01.
rem Bound by docs\belfry-discretion-quality-criterion.md.

cd /d "%~dp0..\.."

set "OUTDIR=eval/records"
set "MODEL=qwen36-35b-a3b-iq3"
set "CONTROL=%OUTDIR%/belfry-steering-control.json"
set "MODEL_OUT=%OUTDIR%/belfry-steering-model.json"
set "LOG=%OUTDIR%/belfry-steering-launch.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

if exist "%CONTROL%" exit /b 1
if exist "%CONTROL%.jsonl" exit /b 1
if exist "%MODEL_OUT%" exit /b 1
if exist "%MODEL_OUT%.jsonl" exit /b 1

echo [gate] burst-probing local/%MODEL% before either S23 arm...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.run_belfry --games 360 --arm random --seats 5 --script compact ^
  --rounds 1 --no-thinking --seed 6100 --adjudicator random ^
  --out "%CONTROL%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.run_belfry --games 360 --arm random --seats 5 --script compact ^
  --rounds 1 --no-thinking --seed 6100 --adjudicator model ^
  --adjudicator-backend local --adjudicator-model "%MODEL%" ^
  --adjudicator-steer --timeout 120 --out "%MODEL_OUT%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.belfry_steering_verdict --criterion s23 "%CONTROL%" "%MODEL_OUT%" >>"%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo DONE rc=%RC% ^(wrapper^)>>"%LOG%"
exit /b %RC%
