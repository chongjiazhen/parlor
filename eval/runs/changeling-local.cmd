@echo off
setlocal
rem Local changeling run, gated on a burst probe.
rem
rem Usage:  eval\runs\changeling-local.cmd [tag] [games] [seed] [model] [arm]
rem
rem   eval\runs\changeling-local.cmd s2 200 4000 qwen36-35b-a3b-iq3 llm
rem
rem A launcher is an INPUT, not run output, so this is tracked - eval\records\ is
rem gitignored and a run recipe that is not versioned cannot be reviewed after it
rem misfires. Same contract as hunt-local.cmd, which is cabal's.
rem
rem WHY THIS EXISTS SEPARATELY. hunt-local.cmd runs `eval.run_games`, which is
rem cabal's driver and takes flags this one does not have (--rounds 2 is cabal's
rem discussion default, --transcript-dir has no changeling equivalent) and lacks
rem --no-thinking, which every recorded changeling arm used. Pointing the cabal
rem launcher at the other game by editing it in place is how two games come to
rem share one denominator, which RESUME.md's standing rule forbids for exactly the
rem reasons it lists.
rem
rem THE GATE IS A BURST, NOT A PING (RESUME.md Backend notes). Local's failure mode
rem differs from cloud's - the router is exact-match, so a cold model answers 503
rem model_not_armed naming what IS live rather than silently serving a smaller one
rem - but a run that spends five hours discovering that is the same wasted run.
rem Arm the model with llm-serve first.

cd /d "%~dp0..\.."

set "TAG=%~1"
if "%TAG%"=="" set "TAG=changeling-local"
set "GAMES=%~2"
if "%GAMES%"=="" set "GAMES=20"
set "SEED=%~3"
if "%SEED%"=="" set "SEED=4000"
set "MODEL=%~4"
if "%MODEL%"=="" set "MODEL=qwen36-35b-a3b-iq3"
set "ARM=%~5"
if "%ARM%"=="" set "ARM=llm"

set "OUTDIR=eval\records"
set "LOG=%OUTDIR%\%TAG%.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The local router is keyless. require_key() lets `local` through with nothing
rem set, so this no longer has to invent a placeholder the way hunt-local.cmd did.

echo [gate] burst-probing local/%MODEL% before spending a run...>>"%LOG%"
python -m eval.probe_tier --backend local --model "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
rem FAIL CLOSED. `if errorlevel 1` means "errorlevel >= 1" and is FALSE for a
rem negative code, so a probe that is killed or crashes (rc=-1) would read as a
rem pass and launch against an untested router. Only an explicit 0 is a pass.
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - see %LOG%.
  exit /b 1
)
echo [gate] probe passed - launching %GAMES% games, arm %ARM%, seed %SEED%, model %MODEL%.>>"%LOG%"

rem --no-thinking because every recorded changeling arm used it and a run meant to
rem be read against those has to match. Serial by construction: one model, one GPU.
python -m eval.run_changeling --games %GAMES% --arm %ARM% --backend local ^
  --model "%MODEL%" --no-thinking --seed %SEED% --timeout 240 ^
  --out "%OUTDIR%\%TAG%.json" ^
  >>"%LOG%" 2>&1
rem run_changeling writes its own `PARLOR DONE rc=` line from a finally and THAT is
rem the authoritative one - hunt6b finished cleanly and wrote no wrapper line
rem because cmd.exe did not survive to echo one. This stays for the case python's
rem marker cannot cover: a crash before the driver runs at all.
echo DONE rc=%ERRORLEVEL% ^(wrapper^)>>"%LOG%"
