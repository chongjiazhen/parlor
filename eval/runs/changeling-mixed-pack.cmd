@echo off
setlocal
rem Changeling mixed cells, ARM 1 ONLY - the live pack against the rung's village.
rem
rem This is `changeling-mixed.cmd`'s arm-1 block, byte-copied, with arm 2 left
rem unrun. It exists because the pair is ~4 h of card and its two arms are read
rem SEPARATELY, each against its own control (docs\changeling-mixed-criterion.md
rem §The statistic), so a card with time for one gets the informative one - the
rem queue's standing call. Nothing here is tuned: every value below is the frozen
rem recipe's, and the criterion forbids an edit after launch.
rem
rem Arm 2 (`mixed-village`) is NOT queued by this file and is a separate decision.
rem Run the two-arm `changeling-mixed.cmd` only on a card with the whole window.
rem
rem Usage:  eval\runs\changeling-mixed-pack.cmd <predecessor-log>

cd /d "%~dp0..\.."

set "OUTDIR=eval\records"
set "MODEL=qwen36-35b-a3b-iq3"
set "SEED=5000"
set "GAMES=200"
set "LOG=%OUTDIR%\cl-mixed.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

set "PRED=%~1"
if "%PRED%"=="" (
  echo [gate] no predecessor log given - usage: changeling-mixed-pack.cmd ^<predecessor-log^>. Refusing.>>"%LOG%"
  exit /b 1
)
if not exist "%PRED%" (
  echo [gate] predecessor log %PRED% does not exist - refusing.>>"%LOG%"
  exit /b 1
)

rem The card must be free. A second 35B onto the one 16 GB card corrupts the
rem first run's timings and can starve both.
findstr /c:"PARLOR DONE rc=0" "%PRED%" >nul 2>&1
if errorlevel 1 (
  echo [gate] %PRED% carries no PARLOR DONE rc=0 - the card is busy, refusing.>>"%LOG%"
  exit /b 1
)

rem Never overwrite a record. A rerun that lands on top of an existing one
rem destroys the arm it was meant to pair against.
if exist "%OUTDIR%\cl-mixed-pack.json" exit /b 1

echo [gate] burst-probing local/%MODEL%...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  exit /b 1
)

echo [arm1] mixed-pack starting %DATE% %TIME%>>"%LOG%"
py -3 -m eval.run_changeling --games %GAMES% --arm mixed-pack --backend local ^
  --model "%MODEL%" --no-thinking --seats 5 --theme folk --rounds 2 --seed %SEED% --timeout 240 ^
  --out "%OUTDIR%\cl-mixed-pack.json" >>"%LOG%" 2>&1
echo [arm1] wrapper rc=%ERRORLEVEL%>>"%LOG%"
echo PARLOR MIXED-PACK DONE %DATE% %TIME%>>"%LOG%"
