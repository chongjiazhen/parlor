@echo off
setlocal
rem Changeling gate #2 pair - the ONE new arm, --arm llm-village on folk.
rem Bound by docs\changeling-gate2-pair-criterion.md; pairs against S22's
rem cl-rounds2.json, which must already exist. Every value is a copy of the
rem criterion's.

cd /d "%~dp0..\.."

set "OUTDIR=eval\records"
set "MODEL=qwen36-35b-a3b-iq3"
set "SEED=5000"
set "LOG=%OUTDIR%\cl-gate2-village.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The record this arm pairs against must be down, and the card must be free.
findstr /c:"PARLOR DONE rc=0 games=200/200" "%OUTDIR%\cl-rounds2.log" >nul 2>&1
if errorlevel 1 (
  echo [gate] cl-rounds2.log carries no PARLOR DONE rc=0 games=200/200 - nothing to pair against, refusing.>>"%LOG%"
  exit /b 1
)
findstr /c:"PARLOR PAIR DONE" "%OUTDIR%\cl-rounds-pair.log" >nul 2>&1
if errorlevel 1 (
  echo [gate] cl-rounds-pair.log carries no PARLOR PAIR DONE - the card is busy, refusing.>>"%LOG%"
  exit /b 1
)
if exist "%OUTDIR%\cl-gate2-village.json" exit /b 1

echo [gate] burst-probing local/%MODEL%...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  exit /b 1
)

py -3 -m eval.run_changeling --games 200 --arm llm-village --backend local ^
  --model "%MODEL%" --no-thinking --seats 5 --theme folk --rounds 2 --seed %SEED% --timeout 240 ^
  --out "%OUTDIR%\cl-gate2-village.json" >>"%LOG%" 2>&1
echo DONE rc=%ERRORLEVEL% ^(wrapper^)>>"%LOG%"
