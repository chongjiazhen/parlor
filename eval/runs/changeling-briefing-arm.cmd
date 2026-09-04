@echo off
setlocal
rem Changeling standing-briefing pair - the ONE new arm, --briefing on folk.
rem Bound by docs\changeling-briefing-criterion.md; pairs against S22's
rem cl-rounds2.json, which must already exist. Every value is a copy of the
rem criterion's. Takes the predecessor log to gate on as %1, defaulting to the
rem rounds pair's - the criterion says one live arm on the card at a time and
rem the predecessor is whichever arm is currently holding it.

cd /d "%~dp0..\.."

set "OUTDIR=eval\records"
set "MODEL=qwen36-35b-a3b-iq3"
set "SEED=5000"
set "PRED=%~1"
if "%PRED%"=="" set "PRED=%OUTDIR%\cl-rounds-pair.log"
set "LOG=%OUTDIR%\cl-briefing.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The record this arm pairs against must be down, and the card must be free.
findstr /c:"PARLOR DONE rc=0 games=200/200" "%OUTDIR%\cl-rounds2.log" >nul 2>&1
if errorlevel 1 (
  echo [gate] cl-rounds2.log carries no PARLOR DONE rc=0 games=200/200 - nothing to pair against, refusing.>>"%LOG%"
  exit /b 1
)
findstr /c:"PARLOR PAIR DONE" "%PRED%" >nul 2>&1
if errorlevel 1 (
  echo [gate] %PRED% carries no PARLOR PAIR DONE - the card is busy, refusing.>>"%LOG%"
  exit /b 1
)
if exist "%OUTDIR%\cl-briefing.json" exit /b 1

echo [gate] burst-probing local/%MODEL%...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  exit /b 1
)

py -3 -m eval.run_changeling --games 200 --arm llm --backend local ^
  --model "%MODEL%" --no-thinking --seats 5 --theme folk --rounds 2 --briefing ^
  --seed %SEED% --timeout 240 ^
  --out "%OUTDIR%\cl-briefing.json" >>"%LOG%" 2>&1
echo DONE rc=%ERRORLEVEL% ^(wrapper^)>>"%LOG%"
