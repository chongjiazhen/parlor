@echo off
setlocal enabledelayedexpansion
rem Tracked waiter for a chained recipe's REFUSAL, not its launch. Every
rem `[after-log]`-style recipe (chain-after.cmd, changeling-gate2-arm.cmd,
rem belfry-night-transcript.cmd) exits the moment its own predecessor's log
rem lacks a PARLOR marker - "launch early, costs nothing" launches nothing.
rem This file is the poll-then-call waiter that used to be an untracked
rem payload under %LOCALAPPDATA%\parlor\ (cl-chain-tail.cmd, 2026-09-02): it
rem polls one marker log, then calls N tracked recipes serially in order.
rem
rem Usage:  eval\runs\chain-tail.cmd <marker-log> <tag> <recipe1> [<recipe2> ...]
rem
rem Each <recipeN> is ONE argv item - quote it if it carries its own
rem arguments, e.g.:
rem   chain-tail.cmd eval\records\cl-skin-pair.log cl-tail ^
rem     "eval\runs\changeling-rounds-pair.cmd" ^
rem     "eval\runs\changeling-gate2-arm.cmd" ^
rem     "eval\runs\belfry-night-transcript.cmd eval\records\cl-gate2-village.log"
rem
rem <marker-log> is checked for EITHER marker substring, "PARLOR PAIR DONE" or
rem "PARLOR DONE" - a chain's predecessor may be a paired run or a plain one,
rem and this waiter does not care which, only that its bytes are down. Bound:
rem CHAIN_TAIL_MAXPOLLS polls (env override; default 2880) x 30 s = 24 h by
rem default, then REFUSING, exit 1. This waiter NEVER launches on timeout -
rem unlike chain-after.cmd's optional launch-anyway path, a second model on
rem the one 16 GB card corrupts the first, so there is no ONTIMEOUT=launch
rem here at all.
rem
rem A launcher is an INPUT, not run output, so this is tracked - eval\records\
rem is gitignored and an untracked recipe leaves no reviewable record of what
rem ran or what it was waiting on.

cd /d "%~dp0..\.."

set "MARKERLOG=%~1"
set "TAG=%~2"
if "%TAG%"=="" set "TAG=chained"
if "%MARKERLOG%"=="" (
  echo usage: chain-tail.cmd ^<marker-log^> ^<tag^> ^<recipe1^> [^<recipe2^> ...]
  exit /b 1
)

rem Collect the remaining argv items as the recipe list, in order. `shift`
rem drops the two fixed args so %1 becomes the first recipe; each recipe may
rem itself be a multi-word quoted string (recipe + its own args) and %~1
rem returns it unquoted as one token, which `call` below then re-splits on
rem whitespace the normal way - that is what lets a recipe carry an argument.
shift
shift
set "RCOUNT=0"
:collect
if "%~1"=="" goto collected
set "RECIPE!RCOUNT!=%~1"
set /a RCOUNT+=1
shift
goto collect
:collected
if %RCOUNT% EQU 0 (
  echo usage: chain-tail.cmd ^<marker-log^> ^<tag^> ^<recipe1^> [^<recipe2^> ...]
  exit /b 1
)

set "OUTDIR=eval\records"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"
set "TAILLOG=%OUTDIR%\%TAG%-tail.log"

set "MAXPOLLS=%CHAIN_TAIL_MAXPOLLS%"
if "%MAXPOLLS%"=="" set "MAXPOLLS=2880"

echo [tail] started %DATE% %TIME% - waiting for PARLOR PAIR DONE or PARLOR DONE in %MARKERLOG% ^(maxpolls=%MAXPOLLS%^)>>"%TAILLOG%"

rem Structural bound beside the predicate - same shape as chain-after.cmd's
rem MAXPOLLS gate. MAXPOLLS x 30s; default 2880 = 24h.
set /a TRIES=0
:wait
findstr /c:"PARLOR PAIR DONE" "%MARKERLOG%" >nul 2>&1 && goto ready
findstr /c:"PARLOR DONE" "%MARKERLOG%" >nul 2>&1 && goto ready
set /a TRIES+=1
if %TRIES% GEQ %MAXPOLLS% (
  rem Redirect the GROUP, not the last line (chain-after.cmd's note - cmd
  rem redirects only the line carrying the `>>`).
  (
    echo [tail] waited %MAXPOLLS% polls x 30s and %MARKERLOG% still carries
    echo [tail] no PARLOR PAIR DONE or PARLOR DONE - REFUSING, exit 1.
    echo [tail] Never launches on timeout: a second model on the one card
    echo [tail] corrupts the first. Launch the chain by hand once the
    echo [tail] predecessor's log ends in a PARLOR marker.
  )>>"%TAILLOG%"
  exit /b 1
)
rem ping, not timeout: `timeout` needs a console and fails "Input redirection
rem is not supported" when this is launched detached with no stdin.
ping -n 31 127.0.0.1 >nul
goto wait

:ready
echo [tail] marker seen %DATE% %TIME% after %TRIES% poll(s) - running %RCOUNT% recipe(s)>>"%TAILLOG%"

set /a I=0
:runloop
if %I% GEQ %RCOUNT% goto alldone
set "CUR=!RECIPE%I%!"
call !CUR!
echo [tail] !CUR! rc=%ERRORLEVEL% %DATE% %TIME%>>"%TAILLOG%"
set /a I+=1
goto runloop

:alldone
echo PARLOR TAIL DONE>>"%TAILLOG%"
exit /b 0
