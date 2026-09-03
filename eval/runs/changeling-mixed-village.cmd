@echo off
setlocal
rem Changeling mixed cells, ARM 2 ONLY - the live village against the rung's pack.
rem
rem This is `changeling-mixed.cmd`'s arm-2 block, byte-copied, run alone because
rem arm 1 (`mixed-pack`) already landed via `changeling-mixed-pack.cmd` and the
rem two-arm recipe refuses the moment `cl-mixed-pack.json` exists. Nothing here
rem is tuned: every value below is the frozen recipe's, and the criterion
rem (docs\changeling-mixed-criterion.md) forbids an edit after launch. Shares
rem `cl-mixed.log` with the arm-1 sibling, same as the two-arm recipe would have
rem written it - a reader sees one log per arm pair, not per invocation.
rem
rem Usage:  eval\runs\changeling-mixed-village.cmd <predecessor-log>

cd /d "%~dp0..\.."

set "OUTDIR=eval\records"
set "MODEL=qwen36-35b-a3b-iq3"
set "SEED=5000"
set "GAMES=200"
set "LOG=%OUTDIR%\cl-mixed.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

set "PRED=%~1"
if "%PRED%"=="" (
  echo [gate] no predecessor log given - usage: changeling-mixed-village.cmd ^<predecessor-log^>. Refusing.>>"%LOG%"
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
if exist "%OUTDIR%\cl-mixed-village.json" exit /b 1

echo [gate] burst-probing local/%MODEL%...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  exit /b 1
)

echo [arm2] mixed-village starting %DATE% %TIME%>>"%LOG%"
py -3 -m eval.run_changeling --games %GAMES% --arm mixed-village --backend local ^
  --model "%MODEL%" --no-thinking --seats 5 --theme folk --rounds 2 --seed %SEED% --timeout 240 ^
  --out "%OUTDIR%\cl-mixed-village.json" >>"%LOG%" 2>&1
echo [arm2] wrapper rc=%ERRORLEVEL%>>"%LOG%"
echo PARLOR MIXED-VILLAGE DONE %DATE% %TIME%>>"%LOG%"
