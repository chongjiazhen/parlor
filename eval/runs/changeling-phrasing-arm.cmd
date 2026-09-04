@echo off
setlocal
rem Changeling negation pass - the ONE new arm, --phrasing positive on folk.
rem Bound by docs\changeling-phrasing-criterion.md; pairs against S22's
rem cl-rounds2.json, which must already exist. Every value is a copy of the
rem criterion's.
rem
rem Usage:  eval\runs\changeling-phrasing-arm.cmd [predecessor-log]
rem
rem %1 is the log of whatever run currently holds the card - the one this must
rem wait behind. It defaults to the pair this arm reads against, which is the
rem common case; pass another when this is chained behind a later run. Naming it
rem as an argument rather than hardcoding it is what lets the same recipe sit at
rem different points of a queue without an edit that then differs from the
rem criterion.

cd /d "%~dp0..\.."

set "OUTDIR=eval\records"
set "MODEL=qwen36-35b-a3b-iq3"
set "SEED=5000"
set "LOG=%OUTDIR%\cl-phrasing-positive.log"
set "PRED=%~1"
if "%PRED%"=="" set "PRED=%OUTDIR%\cl-rounds2.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The control this arm pairs against must be down. The criterion reads S22's
rem cl-rounds2 record as the as-is arm, so its 200 games are a hard predecessor
rem and not merely a busy card.
findstr /c:"PARLOR DONE rc=0 games=200/200" "%OUTDIR%\cl-rounds2.log" >nul 2>&1
if errorlevel 1 (
  echo [gate] cl-rounds2.log carries no PARLOR DONE rc=0 games=200/200 - nothing to pair against, refusing.>>"%LOG%"
  exit /b 1
)

rem And the card must be free. The predecessor is whatever %1 named.
findstr /c:"PARLOR DONE" "%PRED%" >nul 2>&1
if errorlevel 1 (
  echo [gate] %PRED% carries no PARLOR DONE - the card is busy, refusing.>>"%LOG%"
  exit /b 1
)
if exist "%OUTDIR%\cl-phrasing-positive.json" exit /b 1

echo [gate] burst-probing local/%MODEL%...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  exit /b 1
)

py -3 -m eval.run_changeling --games 200 --arm llm --backend local ^
  --model "%MODEL%" --no-thinking --seats 5 --theme folk --rounds 2 --seed %SEED% ^
  --phrasing positive --timeout 240 ^
  --out "%OUTDIR%\cl-phrasing-positive.json" >>"%LOG%" 2>&1
echo DONE rc=%ERRORLEVEL% ^(wrapper^)>>"%LOG%"
