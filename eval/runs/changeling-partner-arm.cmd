@echo off
setlocal enabledelayedexpansion
rem Changeling partner protection - ONE live arm and its CPU control.
rem Bound by docs\changeling-partner-criterion.md; every value below is a copy
rem of that file's §Settings block, and eval.partner_verdict pins the record's
rem own args back against it.
rem
rem MUST RUN BEFORE the source-rules merge. The read is a replication of
rem cl-rounds2's configuration on fresh seeds, so it has to play the rules that
rem record played. The control is this arm's OWN, so the merge would not void
rem the difference - it would quietly change what the replication replicates.
rem
rem enabledelayedexpansion + !TIME! on purpose: %TIME% inside a parenthesised
rem block expands when cmd PARSES the block, which misdated every per-arm line
rem in five earlier recipes (queue.md).

cd /d "%~dp0..\.."

set "OUTDIR=eval\records"
set "MODEL=qwen36-35b-a3b-iq3"
set "SEED=17000"
set "LOG=%OUTDIR%\cl-partner.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem One card, one lane: the changeling chain must be down first.
findstr /c:"PARLOR TAIL DONE" "%OUTDIR%\cl-chain-tail.log" >nul 2>&1
if errorlevel 1 (
  echo [gate] cl-chain-tail.log carries no PARLOR TAIL DONE - the card is busy, refusing.>>"%LOG%"
  exit /b 1
)

rem Never overwrite a record. A second launch is a new criterion, not a re-run.
if exist "%OUTDIR%\cl-partner.json" exit /b 1
if exist "%OUTDIR%\cl-partner-random.json" exit /b 1

echo [arm] started !DATE! !TIME! - 200 games, seed %SEED%, model %MODEL%>>"%LOG%"

echo [control] --arm random, 1000 games on the arm's own seed>>"%LOG%"
py -3 -m eval.run_changeling --games 1000 --arm random --theme folk --seats 5 ^
  --rounds 2 --seed %SEED% --out "%OUTDIR%\cl-partner-random.json" >>"%LOG%" 2>&1
if errorlevel 1 (
  echo [gate] the CPU control did not finish - refusing to spend the card.>>"%LOG%"
  echo PARLOR ARM DONE rc=1 >>"%LOG%"
  exit /b 1
)

echo [gate] burst-probing local/%MODEL%...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if errorlevel 1 (
  echo [gate] probe did not pass - not launching.>>"%LOG%"
  echo PARLOR ARM DONE rc=1 >>"%LOG%"
  exit /b 1
)

echo [arm] --arm llm, 200 games - log %OUTDIR%\cl-partner-arm.log>>"%LOG%"
py -3 -m eval.run_changeling --games 200 --arm llm --backend local ^
  --model "%MODEL%" --no-thinking --seats 5 --theme folk --rounds 2 --seed %SEED% --timeout 240 ^
  --out "%OUTDIR%\cl-partner.json" >>"%OUTDIR%\cl-partner-arm.log" 2>&1

rem Judged on the arm's OWN log, never on an exit code.
findstr /c:"PARLOR DONE rc=0 games=200/200" "%OUTDIR%\cl-partner-arm.log" >nul
if errorlevel 1 (
  echo [arm] no PARLOR DONE rc=0 games=200/200 in the arm log - REFUSING.>>"%LOG%"
  echo PARLOR ARM DONE rc=1 >>"%LOG%"
  exit /b 1
)

echo [arm] down !DATE! !TIME!>>"%LOG%"
echo PARLOR ARM DONE rc=0 arms=1/1 >>"%LOG%"
