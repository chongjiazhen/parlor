@echo off
setlocal
rem Wait for a run to finish, then launch the next one. Keeps the GPU busy across
rem the gap between an evening run and an overnight one.
rem
rem Usage:  eval\runs\chain-after.cmd <sentinel-file> <tag> [games] [seed] [model]
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

set "CHAINLOG=eval\records\%TAG%-chain.log"
if not exist "eval\records" mkdir "eval\records"

echo [chain] started %DATE% %TIME% - waiting for %SENTINEL% to be non-empty>>"%CHAINLOG%"

rem Structural bound beside the predicate. The predicate decides WHETHER to go on;
rem this decides that the loop ends at all, because a first run that dies without
rem writing its sentinel would otherwise leave this spinning unattended forever.
rem 90 x 30s = 45 minutes, against an expected first-run time well under that.
set /a TRIES=0
:wait
for %%A in ("%SENTINEL%") do if %%~zA GTR 0 goto ready
set /a TRIES+=1
if %TRIES% GEQ 90 (
  echo [chain] waited 45m and %SENTINEL% is still empty. Launching anyway - at
  echo [chain] this point the first run has either finished abnormally or hung,
  echo [chain] and the burst gate below is what decides whether the box can carry
  echo [chain] a run. An idle GPU is the worse outcome.>>"%CHAINLOG%"
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
