@echo off
setlocal
rem The kindred-deck campaign - SETUP_7_KIN, seven seats, gated on a burst probe.
rem
rem Usage:  eval\runs\changeling-kindred.cmd [tag] [games] [seed] [model]
rem
rem   eval\runs\changeling-kindred.cmd kin1 200 14000 qwen36-35b-a3b-iq3
rem
rem A launcher is an INPUT, not run output, so this is tracked - eval\records\ is
rem gitignored and a run recipe that is not versioned cannot be reviewed after it
rem misfires.
rem
rem THE CRITERION IS docs\changeling-kindred-criterion.md AND IT BINDS, NOT THIS
rem FILE. AGENTS.md: an arm's settings come from its criterion, never from a
rem launcher default or a queue row. The defaults below MATCH that document as it
rem stood on 2026-09-02; if the two ever disagree the criterion is right and this
rem file is the bug. Cost of the inverse: belfry live1 spent 11.5 h of GPU on a
rem record that can be read but never called.
rem
rem WHY THIS EXISTS SEPARATELY from changeling-local.cmd. That one deals SETUP_5,
rem which is what every recorded changeling number was played on, and it has no
rem --seats. Editing it in place to deal seven would silently re-baseline every
rem number recorded through it - the deck change is exactly the variable this
rem campaign is spending, so it gets its own recipe and its own tag space.
rem
rem IT RUNS TWO ARMS. The criterion's own-arm clause reads a random arm on the
rem SAME seeds, so this launches the model arm and then the random control. The
rem random arm needs no GPU and takes ~2 minutes; it runs SECOND so a probe
rem failure costs nothing and the expensive arm starts as early as it can.

cd /d "%~dp0..\.."

set "TAG=%~1"
if "%TAG%"=="" set "TAG=kin1"
set "GAMES=%~2"
if "%GAMES%"=="" set "GAMES=200"
set "SEED=%~3"
if "%SEED%"=="" set "SEED=14000"
set "MODEL=%~4"
if "%MODEL%"=="" set "MODEL=qwen36-35b-a3b-iq3"

set "OUTDIR=eval\records"
set "LOG=%OUTDIR%\%TAG%.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

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
echo [gate] probe passed - %GAMES% games on SETUP_7_KIN, seed %SEED%, model %MODEL%.>>"%LOG%"

rem Every flag below is the criterion's, and S2's before it, so the DECK is the
rem variable and the lane is not. --no-thinking because every recorded changeling
rem arm used it. Serial by construction: one model, one GPU.
python -m eval.run_changeling --games %GAMES% --arm llm --seats 7 --backend local ^
  --model "%MODEL%" --no-thinking --seed %SEED% --rounds 2 --retries 2 ^
  --temperature 0.8 --max-tokens 1536 --timeout 240 ^
  --out "%OUTDIR%\%TAG%.json" ^
  >>"%LOG%" 2>&1
set "MODELRC=%ERRORLEVEL%"
echo DONE rc=%MODELRC% ^(wrapper, model arm^)>>"%LOG%"

rem The paired control, same deck and same seeds. It runs even when the model arm
rem died - a partial model record still needs its bar, and this arm costs minutes.
echo [control] random arm, same deck and same seeds.>>"%LOG%"
python -m eval.run_changeling --games %GAMES% --arm random --seats 7 ^
  --model none --seed %SEED% --rounds 1 ^
  --out "%OUTDIR%\%TAG%-random.json" ^
  >>"%LOG%" 2>&1
echo DONE rc=%ERRORLEVEL% ^(wrapper, random arm^)>>"%LOG%"
echo PAIR DONE model_rc=%MODELRC%>>"%LOG%"
