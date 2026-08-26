@echo off
setlocal
rem Local hunt run, gated on a liveness probe.
rem
rem Usage:  eval\runs\hunt-local.cmd [tag] [games] [seed] [model]
rem
rem A launcher is an INPUT, not run output. eval\records\ is gitignored, so the
rem untracked copy of this recipe that produced the first seed-1000 run left no
rem reviewable record of what it launched; that is what this file fixes.
rem
rem The gate is a burst, not a ping (RESUME.md Backend notes). Local's failure
rem mode is different from cloud's - the router is exact-match, so a cold model
rem answers 503 model_not_armed naming what IS live rather than silently serving
rem the 0.6B floor - but a run that spends five hours discovering that is the
rem same wasted run either way. Arm the model with llm-serve first.

cd /d "%~dp0..\.."

set "TAG=%~1"
if "%TAG%"=="" set "TAG=hunt-local"
set "GAMES=%~2"
if "%GAMES%"=="" set "GAMES=20"
set "SEED=%~3"
if "%SEED%"=="" set "SEED=1000"
set "MODEL=%~4"
if "%MODEL%"=="" set "MODEL=qwen36-35b-a3b-iq3"

set "OUTDIR=eval\records"
set "LOG=%OUTDIR%\%TAG%.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The local router is keyless; Backend still wants the variable present.
if "%PARLOR_API_KEY%"=="" set "PARLOR_API_KEY=x"

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
echo [gate] probe passed - launching %GAMES% games, seed %SEED%, model %MODEL%.>>"%LOG%"

rem Serial by construction: one model on one GPU. run_games forces 1 worker on a
rem non-parallel endpoint anyway; --workers is not passed so the forcing is
rem visible in the log rather than hidden behind a number that does nothing.
python -m eval.run_games --games %GAMES% --arm llm --backend local ^
  --model "%MODEL%" --rounds 2 --seed %SEED% --timeout 240 ^
  --out "%OUTDIR%\%TAG%.json" ^
  --transcript-dir "%OUTDIR%\%TAG%-transcripts" ^
  --transcript "%OUTDIR%\%TAG%-game0.md" ^
  >>"%LOG%" 2>&1
echo DONE rc=%ERRORLEVEL%>>"%LOG%"
