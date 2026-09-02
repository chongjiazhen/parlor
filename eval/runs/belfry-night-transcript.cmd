@echo off
setlocal
rem Belfry night-coherence arm, prior WITHHELD, own TRANSCRIPT - the
rem session-memory arm, frozen 2026-09-02.
rem Bound by docs\belfry-night-transcript-criterion.md.
rem
rem Usage:  eval\runs\belfry-night-transcript.cmd [after-log]
rem
rem The optional argument is a log that must already carry a PARLOR done marker
rem (PARLOR DONE or PARLOR PAIR DONE) before anything launches - the card is one
rem GPU and this arm queues behind whatever chain is on it. Absent, it refuses;
rem launching early costs nothing and does nothing.

cd /d "%~dp0..\.."

set "OUTDIR=eval/records"
set "MODEL=qwen36-35b-a3b-iq3"
set "CONTROL=%OUTDIR%/belfry-night-transcript-control.json"
set "MODEL_OUT=%OUTDIR%/belfry-night-transcript-model.json"
set "LOG=%OUTDIR%/belfry-night-transcript-launch.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

if not "%~1"=="" (
  findstr /c:"PARLOR DONE" /c:"PARLOR PAIR DONE" "%~1" >nul 2>&1
  if errorlevel 1 (
    echo [gate] %~1 carries no PARLOR done marker - the card is presumed busy, REFUSING.>>"%LOG%"
    exit /b 2
  )
)

if exist "%CONTROL%" exit /b 1
if exist "%CONTROL%.jsonl" exit /b 1
if exist "%MODEL_OUT%" exit /b 1
if exist "%MODEL_OUT%.jsonl" exit /b 1

echo [gate] burst-probing local/%MODEL% before either transcript arm...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.run_belfry --games 1000 --arm random --seats 9 --script compact ^
  --rounds 1 --seed 15000 --adjudicator random ^
  --out "%CONTROL%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.run_belfry --games 1000 --arm random --seats 9 --script compact ^
  --rounds 1 --seed 15000 --adjudicator model ^
  --adjudicator-backend local --adjudicator-model "%MODEL%" ^
  --adjudicator-night --adjudicator-night-no-prior ^
  --adjudicator-night-transcript --timeout 120 ^
  --out "%MODEL_OUT%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.belfry_night_verdict --criterion transcript "%CONTROL%" "%MODEL_OUT%" >>"%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo DONE rc=%RC% ^(wrapper^)>>"%LOG%"
exit /b %RC%
