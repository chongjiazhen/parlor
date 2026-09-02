@echo off
setlocal
rem Changeling turn-taking pair - the ONE new arm, --turns random-active on folk.
rem Bound by docs\changeling-turns-criterion.md; pairs against S22's cl-rounds2,
rem which must already be down. Every value here is a copy of the criterion's.
rem
rem Usage:  eval\runs\changeling-turns-arm.cmd [after-log]
rem
rem The optional argument is a log that must already carry a PARLOR done marker
rem (PARLOR DONE or PARLOR PAIR DONE) before anything launches - the card is one
rem GPU and this arm queues behind whatever chain is on it. Passed and unmarked,
rem it refuses; launching early costs nothing and does nothing.
rem
rem The criterion's hard ordering condition is NOT enforceable here and is stated
rem instead: this pair must run BEFORE the changeling source-rules merge, or the
rem read is void. A merged-rules arm 2 against a pre-merge arm 1 is two variables.

cd /d "%~dp0..\.."

set "OUTDIR=eval\records"
set "MODEL=qwen36-35b-a3b-iq3"
set "SEED=5000"
set "ARM=%OUTDIR%\cl-turns-random.json"
set "CTRL=%OUTDIR%\cl-turns-random-random.json"
set "LOG=%OUTDIR%\cl-turns-random.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

if not "%~1"=="" (
  findstr /c:"PARLOR DONE" /c:"PARLOR PAIR DONE" "%~1" >nul 2>&1
  if errorlevel 1 (
    echo [gate] %~1 carries no PARLOR done marker - the card is presumed busy, REFUSING.>>"%LOG%"
    exit /b 2
  )
)

rem The record this arm pairs against must be down and complete.
findstr /c:"PARLOR DONE rc=0 games=200/200" "%OUTDIR%\cl-rounds2.log" >nul 2>&1
if errorlevel 1 (
  echo [gate] cl-rounds2.log carries no PARLOR DONE rc=0 games=200/200 - nothing to pair against, refusing.>>"%LOG%"
  exit /b 1
)

if exist "%ARM%" exit /b 1
if exist "%ARM%.jsonl" exit /b 1

echo [gate] burst-probing local/%MODEL%...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  exit /b 1
)

rem The CPU control for this arm. Cheap, and the criterion reads gate #3 per arm
rem against the run's own random arm rather than against the other arm's.
py -3 -m eval.run_changeling --games 1000 --arm random --seats 5 --theme folk ^
  --rounds 2 --seed %SEED% --turns random-active ^
  --out "%CTRL%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.run_changeling --games 200 --arm llm --backend local ^
  --model "%MODEL%" --no-thinking --seats 5 --theme folk --rounds 2 ^
  --turns random-active --seed %SEED% --timeout 240 ^
  --out "%ARM%" >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

py -3 -m eval.turns_pair_verdict "%OUTDIR%" >>"%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo DONE rc=%RC% ^(wrapper^)>>"%LOG%"
exit /b %RC%
