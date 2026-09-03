@echo off
setlocal enabledelayedexpansion
rem enabledelayedexpansion + !TIME!: %TIME% inside a parenthesised block
rem expands at PARSE time, which misdated every per-arm line here (queue.md).
rem The S26 solver control pair - `--arm solver` and `--arm random` on the SAME
rem seeds, then the paired read. CPU only: neither arm calls a model.
rem
rem Usage:  eval\runs\solver-control.cmd [tag] [games] [seed] [arm]
rem
rem   eval\runs\solver-control.cmd solver-control 400 20000
rem   eval\runs\solver-control.cmd solver-good-control 400 21000 solver-good
rem
rem The fourth argument is the solver seating: `solver` (every seat, S26) or
rem `solver-good` (good seats only, evil on random - the control S26 pointed at).
rem
rem WHY A PAIR SCRIPT. The solver differs from the random control only on the
rem votes it can PROVE from a seat's entitled evidence; every other decision is
rem the same random fallback, drawn from the same seeded stream. So the two arms
rem are one game up to the first proved vote and different games after it, and
rem the like-for-like read (`eval\solver_control.py`) pairs a proved vote with
rem random's vote on the same board only while the public record is identical.
rem That pairing exists only if both arms ran the same seeds - so one launcher
rem runs both, and refuses to read a half pair.
rem
rem N and the seed are arguments, not a criterion: this is a control read of an
rem instrument, not a campaign, and no gate is graded on it. The defaults are
rem the S26 sizing - 20000 is a seed range nothing else in the tree has spent,
rem and the pilot that sized N ran at 19000 so the read's own seeds stayed unseen.
rem
rem A launcher is an INPUT, not run output, so this is tracked; eval\records\ is
rem not.

cd /d "%~dp0..\.."

set "TAG=%~1"
if "%TAG%"=="" set "TAG=solver-control"
set "GAMES=%~2"
if "%GAMES%"=="" set "GAMES=400"
set "SEED=%~3"
if "%SEED%"=="" set "SEED=20000"
set "ARM=%~4"
if "%ARM%"=="" set "ARM=solver"

set "OUTDIR=eval\records"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"
set "LOG=%OUTDIR%\%TAG%.log"

echo [pair] started !DATE! !TIME! - %GAMES% games/arm, seed %SEED%>>"%LOG%"

for %%A in (%ARM% random) do (
  echo [pair] arm %%A - log %OUTDIR%\%TAG%-%%A.log>>"%LOG%"
  rem One log per arm, so the marker check below reads THIS arm's marker and
  rem cannot pass on the one the previous arm (or a previous run) wrote.
  python -m eval.run_cabal --games %GAMES% --arm %%A --seed %SEED% ^
    --out "%OUTDIR%\%TAG%-%%A.json" >"%OUTDIR%\%TAG%-%%A.log" 2>&1
  rem Judge each arm by its own marker line, never the exit code.
  findstr /c:"PARLOR DONE rc=0" "%OUTDIR%\%TAG%-%%A.log" >nul
  if errorlevel 1 (
    echo [pair] arm %%A did not write PARLOR DONE rc=0 - REFUSING to continue.>>"%LOG%"
    >>"%LOG%" echo PARLOR PAIR DONE rc=1
    exit /b 1
  )
)

echo [pair] both arms down !DATE! !TIME! - reading the pair>>"%LOG%"
python -m eval.solver_control "%OUTDIR%\%TAG%-%ARM%.json" "%OUTDIR%\%TAG%-random.json" ^
  > "%OUTDIR%\%TAG%.read" 2>>"%LOG%"
if errorlevel 1 (
  echo [pair] the read REFUSED the pair - see %OUTDIR%\%TAG%.read and this log.>>"%LOG%"
  >>"%LOG%" echo PARLOR PAIR DONE rc=1
  exit /b 1
)
type "%OUTDIR%\%TAG%.read"
rem Redirect FIRST. Written the usual way, `rc=0>>log` is parsed by cmd as a
rem redirect of handle 0 and the marker lands on stdout reading `rc=` - measured
rem on this launcher's first run.
>>"%LOG%" echo PARLOR PAIR DONE rc=0
