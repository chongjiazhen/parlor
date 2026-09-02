@echo off
setlocal
rem Belfry night-coherence arm, prior WITHHELD - the memory arm, frozen 2026-09-02.
rem Bound by docs\belfry-night-noprior-criterion.md.

cd /d "%~dp0..\.."

set "OUTDIR=eval/records"
set "MODEL=qwen36-35b-a3b-iq3"
set "CONTROL=%OUTDIR%/belfry-night-noprior-control.json"
set "MODEL_OUT=%OUTDIR%/belfry-night-noprior-model.json"
set "LOG=%OUTDIR%/belfry-night-noprior-launch.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

if exist "%CONTROL%" exit /b 1
if exist "%CONTROL%.jsonl" exit /b 1
if exist "%MODEL_OUT%" exit /b 1
if exist "%MODEL_OUT%.jsonl" exit /b 1

echo [gate] burst-probing local/%MODEL% before either noprior arm...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.run_belfry --games 1000 --arm random --seats 9 --script compact ^
  --rounds 1 --seed 13000 --adjudicator random ^
  --out "%CONTROL%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.run_belfry --games 1000 --arm random --seats 9 --script compact ^
  --rounds 1 --seed 13000 --adjudicator model ^
  --adjudicator-backend local --adjudicator-model "%MODEL%" ^
  --adjudicator-night --adjudicator-night-no-prior --timeout 120 ^
  --out "%MODEL_OUT%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.belfry_night_verdict --criterion withheld "%CONTROL%" "%MODEL_OUT%" >>"%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo DONE rc=%RC% ^(wrapper^)>>"%LOG%"
exit /b %RC%
