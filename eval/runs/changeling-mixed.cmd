@echo off
setlocal
rem Changeling mixed cells - the hand-written rung seated against LIVE seats.
rem Two arms, serial, on the one card: --arm mixed-pack then --arm mixed-village.
rem Bound by docs\changeling-mixed-criterion.md; every value below is a copy of
rem that file's and nothing here may be tuned without editing it, which the
rem criterion forbids after launch.
rem
rem Usage:  eval\runs\changeling-mixed.cmd <predecessor-log>
rem
rem The predecessor log is the run that currently owns the GPU - its name is not
rem hardcoded because the changeling chain's order is decided in queue.md and not
rem here, and a launcher that names its own predecessor goes stale silently the
rem first time the chain is reordered. It is REQUIRED: defaulting it would make a
rem forgotten argument look like a satisfied gate.

cd /d "%~dp0..\.."

set "OUTDIR=eval\records"
set "MODEL=qwen36-35b-a3b-iq3"
set "SEED=5000"
set "GAMES=200"
set "LOG=%OUTDIR%\cl-mixed.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

set "PRED=%~1"
if "%PRED%"=="" (
  echo [gate] no predecessor log given - usage: changeling-mixed.cmd ^<predecessor-log^>. Refusing.>>"%LOG%"
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
if exist "%OUTDIR%\cl-mixed-pack.json" exit /b 1

echo [gate] burst-probing local/%MODEL%...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  exit /b 1
)

rem ---- arm 1: live pack against the rung's village ---------------------------
echo [arm1] mixed-pack starting %DATE% %TIME%>>"%LOG%"
py -3 -m eval.run_changeling --games %GAMES% --arm mixed-pack --backend local ^
  --model "%MODEL%" --no-thinking --seats 5 --theme folk --rounds 2 --seed %SEED% --timeout 240 ^
  --out "%OUTDIR%\cl-mixed-pack.json" >>"%LOG%" 2>&1
echo [arm1] wrapper rc=%ERRORLEVEL%>>"%LOG%"

rem Arm 2 is judged on arm 1's OWN marker, not on the wrapper's exit code. A
rem driver that dies mid-run still returns through the wrapper, and the marker is
rem the only line that names how many games actually landed.
findstr /c:"PARLOR DONE rc=0 games=%GAMES%/%GAMES%" "%LOG%" >nul 2>&1
if errorlevel 1 (
  echo [gate] arm1 wrote no PARLOR DONE rc=0 games=%GAMES%/%GAMES% - refusing arm2, the pair is lost.>>"%LOG%"
  exit /b 1
)

rem ---- arm 2: live village against the rung's pack ---------------------------
echo [arm2] mixed-village starting %DATE% %TIME%>>"%LOG%"
py -3 -m eval.run_changeling --games %GAMES% --arm mixed-village --backend local ^
  --model "%MODEL%" --no-thinking --seats 5 --theme folk --rounds 2 --seed %SEED% --timeout 240 ^
  --out "%OUTDIR%\cl-mixed-village.json" >>"%LOG%" 2>&1
echo [arm2] wrapper rc=%ERRORLEVEL%>>"%LOG%"
echo PARLOR MIXED DONE %DATE% %TIME%>>"%LOG%"
