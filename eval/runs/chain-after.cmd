@echo off
setlocal
rem Wait for a run to finish, then launch the next one. Keeps the GPU busy across
rem the gap between an evening run and an overnight one.
rem
rem Usage:  eval\runs\chain-after.cmd <sentinel-file> <tag> [games] [seed] [model]
rem                                   [max-polls] [on-timeout: launch|refuse]
rem
rem The last two exist because the 45-minute default below was sized against a
rem first run "well under that" and silently becomes a footgun when it is not: a
rem 6-hour first arm would time the wait out and launch a SECOND 35B onto the one
rem 16 GB card while the first is still using it. Both default to the original
rem behaviour; a long first run passes its own bound and `refuse`.
rem
rem The sentinel is a file the FIRST run writes only when it completes - its report
rem file, not its log, because a log has content from the first line and would fire
rem this immediately. Waiting on produced STATE rather than on a pid also survives
rem pid reuse and does not care which session owned the first run.
rem
rem A launcher is an INPUT, not run output, so this is tracked - eval\records\ is
rem gitignored and an untracked recipe leaves no reviewable record of what ran.

cd /d "%~dp0..\.."

set "SENTINEL=%~1"
set "TAG=%~2"
if "%TAG%"=="" set "TAG=chained"
set "GAMES=%~3"
if "%GAMES%"=="" set "GAMES=20"
set "SEED=%~4"
if "%SEED%"=="" set "SEED=1000"
set "MODEL=%~5"
set "MAXPOLLS=%~6"
if "%MAXPOLLS%"=="" set "MAXPOLLS=90"
set "ONTIMEOUT=%~7"
if "%ONTIMEOUT%"=="" set "ONTIMEOUT=launch"

set "CHAINLOG=eval\records\%TAG%-chain.log"
if not exist "eval\records" mkdir "eval\records"

echo [chain] started %DATE% %TIME% - waiting for %SENTINEL% to be non-empty>>"%CHAINLOG%"

rem Structural bound beside the predicate. The predicate decides WHETHER to go on;
rem this decides that the loop ends at all, because a first run that dies without
rem writing its sentinel would otherwise leave this spinning unattended forever.
rem MAXPOLLS x 30s, default 90 = 45 minutes. Size it against the FIRST run's
rem expected length, not this one's: the bound is what stops an unattended spin,
rem and a bound shorter than the run it waits on fires while that run is healthy.
set /a TRIES=0
:wait
for %%A in ("%SENTINEL%") do if %%~zA GTR 0 goto ready
set /a TRIES+=1
if %TRIES% GEQ %MAXPOLLS% (
  rem Redirect the GROUP, not the last line. cmd redirects only the line carrying
  rem the `>>`, so a four-line message with one redirect writes three lines to a
  rem stdout that a detached launch throws away - the log then holds the verdict
  rem with none of the reasoning. (This file shipped that bug until 2026-08-27.)
  rem No computed minutes either: a `set /a` in here is invisible to the echoes
  rem below it without delayed expansion. Poll count x 30s.
  if /i "%ONTIMEOUT%"=="refuse" (
    (
      echo [chain] waited %MAXPOLLS% polls x 30s and %SENTINEL% is still empty - REFUSING.
      echo [chain] on-timeout=refuse, so the first run is presumed still holding the
      echo [chain] GPU. A second model on the one card is worse than an idle one.
      echo [chain] Launch %TAG% by hand once the first run's log ends in PARLOR DONE.
    )>>"%CHAINLOG%"
    exit /b 1
  )
  (
    echo [chain] waited %MAXPOLLS% polls x 30s and %SENTINEL% is still empty. Launching anyway -
    echo [chain] at this point the first run has either finished abnormally or hung,
    echo [chain] and the burst gate below is what decides whether the box can carry
    echo [chain] a run. An idle GPU is the worse outcome.
  )>>"%CHAINLOG%"
  goto ready
)
rem ping, not timeout: `timeout` needs a console and fails "Input redirection is
rem not supported" when this is launched detached with no stdin.
ping -n 31 127.0.0.1 >nul
goto wait

:ready
echo [chain] proceeding at %TIME% after %TRIES% poll(s) - launching %TAG%>>"%CHAINLOG%"
call "%~dp0hunt-local.cmd" %TAG% %GAMES% %SEED% %MODEL%
echo [chain] hunt-local returned rc=%ERRORLEVEL% at %DATE% %TIME%>>"%CHAINLOG%"
