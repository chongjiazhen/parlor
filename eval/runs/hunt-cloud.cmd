@echo off
setlocal
rem Cloud hunt run, gated on a burst probe.
rem
rem Usage:  set PARLOR_API_KEY=...  &&  eval\runs\hunt-cloud.cmd [model] [games] [seed]
rem
rem The gate exists because of 2026-08-25: this run launched pinned to a model
rem whose route pool had cooled, sat alive for 72 minutes, and wrote zero games.
rem Every call was refused in 40ms. A single call would have looked healthy - the
rem one request that did serve was the FASTEST of the set - so the precondition
rem has to be a burst, not a ping. See docs/measurements.md Backend notes.

cd /d "%~dp0..\.."

set "MODEL=%~1"
if "%MODEL%"=="" set "MODEL=gpt-oss-120b"
set "GAMES=%~2"
if "%GAMES%"=="" set "GAMES=25"
set "SEED=%~3"
if "%SEED%"=="" set "SEED=2000"

set "OUTDIR=eval\records"
set "LOG=%OUTDIR%\huntcloud.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem Key is never written into the repo - the caller exports it.
if "%PARLOR_API_KEY%"=="" (
  echo [gate] PARLOR_API_KEY is not set - refusing to launch.>>"%LOG%"
  echo [gate] PARLOR_API_KEY is not set - refusing to launch.
  exit /b 2
)

echo [gate] burst-probing gray/%MODEL% before spending a run...>>"%LOG%"
python -m eval.probe_tier --backend gray --model "%MODEL%" -n 12 >>"%LOG%" 2>&1
rem FAIL CLOSED. `if errorlevel 1` means "errorlevel >= 1" and is FALSE for a
rem negative code, so a probe that is killed or crashes (rc=-1) reads as a pass
rem and the run launches against an untested tier. Caught doing exactly that on
rem 2026-08-26. Only an explicit 0 is a pass; everything else aborts.
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - see %LOG%.
  exit /b 1
)
echo [gate] probe passed - launching %GAMES% games, seed %SEED%.>>"%LOG%"

python -m eval.run_cabal --games %GAMES% --arm llm --backend gray ^
  --model "%MODEL%" --rounds 2 --workers 2 --seed %SEED% --timeout 180 ^
  --out "%OUTDIR%\huntcloud-auto.json" ^
  --transcript-dir "%OUTDIR%\huntcloud-transcripts" ^
  --transcript "%OUTDIR%\huntcloud-game0.md" ^
  >>"%LOG%" 2>&1
echo DONE rc=%ERRORLEVEL%>>"%LOG%"
