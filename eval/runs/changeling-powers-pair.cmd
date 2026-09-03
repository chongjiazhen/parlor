@echo off
setlocal enabledelayedexpansion
rem enabledelayedexpansion + !TIME!: %TIME% inside a parenthesised block
rem expands at PARSE time, which misdated every per-arm line here (queue.md).
rem The changeling POWERS pair - both arms, one variable, serially on one card.
rem
rem Usage:  eval\runs\changeling-powers-pair.cmd <before-tree> [games] [seed] [model]
rem
rem   eval\runs\changeling-powers-pair.cmd C:\parlor-before 20 1000 qwen36-35b-a3b-iq3
rem
rem WHY A PAIR SCRIPT AND NOT TWO LAUNCHES. The measured variable is the public
rem rules preamble: the "before" arm lists the deck by NAME ONLY (the pre-b8f67e1
rem text), the "after" arm lists it in night order with each card's power. That is
rem a difference in TRACKED CODE, not a flag - the fix shipped with no way to turn
rem it off, on purpose. So the before arm runs from a second checkout that carries
rem the revert and nothing else, and <before-tree> is that checkout:
rem
rem   git worktree add --detach C:\parlor-before HEAD
rem   ...restore the name-only deck line in games\changeling\referee.py...
rem
rem Everything else in that tree is HEAD, so the pair differs in one thing. Confirm
rem it before spending the GPU - render both preambles and diff them; the only
rem legitimate failure in the before tree's suite is the guard that pins the very
rem text being reverted.
rem
rem BOTH ARMS OR THE PAIRING IS LOST. A re-run of only the after arm buys nothing,
rem so if arm 1 does not finish this REFUSES to start arm 2 rather than leaving a
rem half pair that reads like a result. Judged on arm 1's own log line, never on an
rem exit code: changeling-local.cmd ends in an `echo`, which clears ERRORLEVEL.
rem
rem A launcher is an INPUT, not run output, so this is tracked. <before-tree> is an
rem argument rather than a hardcoded path because the checkout is box-local and a
rem tracked recipe must not carry one.

cd /d "%~dp0..\.."

set "BEFORE=%~1"
if "%BEFORE%"=="" (
  echo Usage: %~nx0 ^<before-tree^> [games] [seed] [model]
  exit /b 2
)
if not exist "%BEFORE%\eval\runs\changeling-local.cmd" (
  echo [pair] %BEFORE% is not a parlor checkout - refusing.
  exit /b 2
)
set "GAMES=%~2"
if "%GAMES%"=="" set "GAMES=20"
set "SEED=%~3"
if "%SEED%"=="" set "SEED=1000"
set "MODEL=%~4"
if "%MODEL%"=="" set "MODEL=qwen36-35b-a3b-iq3"

set "OUTDIR=eval\records"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"
set "PAIRLOG=%OUTDIR%\cl-powers-pair.log"

rem 2 is the tag suffix. The 2026-08-27 pair is cl-powers-{before,after} and the
rem -10pp paired finding still rests on those records, so they are not overwritten.
set "TAGB=cl-powers-before2"
set "TAGA=cl-powers-after2"

echo [pair] started !DATE! !TIME! - %GAMES% games/arm, seed %SEED%, model %MODEL%>>"%PAIRLOG%"
echo [pair] arm 1 BEFORE (name-only deck) from %BEFORE%>>"%PAIRLOG%"

call "%BEFORE%\eval\runs\changeling-local.cmd" %TAGB% %GAMES% %SEED% %MODEL% llm

rem Judge arm 1 by its own log, per CLAUDE.md. `findstr` sets errorlevel 1 when the
rem string is absent, which covers a probe refusal, a crash and a hang alike.
findstr /c:"PARLOR DONE rc=0" "%BEFORE%\%OUTDIR%\%TAGB%.log" >nul
if errorlevel 1 (
  (
    echo [pair] arm 1 did not write PARLOR DONE rc=0 - REFUSING to start arm 2.
    echo [pair] Both arms or the pairing is lost, and a lone after arm buys nothing.
    echo [pair] Read %BEFORE%\%OUTDIR%\%TAGB%.log for what happened.
  )>>"%PAIRLOG%"
  echo PARLOR PAIR DONE rc=1 arms=1/2 >>"%PAIRLOG%"
  exit /b 1
)

rem The before tree is a worktree, so its records live there. Bring them home -
rem eval\records\ in the primary checkout is the durable one this repo reads.
copy /y "%BEFORE%\%OUTDIR%\%TAGB%.json" "%OUTDIR%\" >nul
copy /y "%BEFORE%\%OUTDIR%\%TAGB%.json.jsonl" "%OUTDIR%\" >nul
copy /y "%BEFORE%\%OUTDIR%\%TAGB%.log" "%OUTDIR%\" >nul
echo [pair] arm 1 done, records copied to %OUTDIR%>>"%PAIRLOG%"

echo [pair] arm 2 AFTER (night order + powers) from HEAD>>"%PAIRLOG%"
call "%~dp0changeling-local.cmd" %TAGA% %GAMES% %SEED% %MODEL% llm

findstr /c:"PARLOR DONE rc=0" "%OUTDIR%\%TAGA%.log" >nul
if errorlevel 1 (
  echo [pair] arm 2 did not write PARLOR DONE rc=0 - the pair is incomplete.>>"%PAIRLOG%"
  echo PARLOR PAIR DONE rc=1 arms=1/2 >>"%PAIRLOG%"
  exit /b 1
)

echo [pair] both arms down !DATE! !TIME!>>"%PAIRLOG%"
echo PARLOR PAIR DONE rc=0 arms=2/2 >>"%PAIRLOG%"
