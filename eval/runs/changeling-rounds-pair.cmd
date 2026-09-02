@echo off
setlocal
rem Changeling discussion-length pair, --rounds 2 vs --rounds 3 on folk.
rem Bound by docs\changeling-rounds-pair-criterion.md; every value below is a
rem copy of that file's. Two CPU controls, then two live arms serially on one
rem card; arm 2 is refused without arm 1's own marker.

cd /d "%~dp0..\.."

set "OUTDIR=eval\records"
set "MODEL=qwen36-35b-a3b-iq3"
set "SEED=5000"
set "LOG=%OUTDIR%\cl-rounds-pair.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem One card, one lane: the name-form pair must be down first.
findstr /c:"PARLOR PAIR DONE" "%OUTDIR%\cl-skin-pair.log" >nul 2>&1
if errorlevel 1 (
  echo [pair] cl-skin-pair.log carries no PARLOR PAIR DONE - the card is busy, refusing.>>"%LOG%"
  exit /b 1
)

for %%R in (2 3) do (
  if exist "%OUTDIR%\cl-rounds%%R.json" exit /b 1
  if exist "%OUTDIR%\cl-rounds%%R-random.json" exit /b 1
)

echo [pair] started %DATE% %TIME% - 200 games/arm, seed %SEED%, model %MODEL%>>"%LOG%"
echo [gate] burst-probing local/%MODEL% before either arm...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  echo PARLOR PAIR DONE rc=1 arms=0/2 >>"%LOG%"
  exit /b 1
)

for %%R in (2 3) do (
  echo [control] --arm random --rounds %%R>>"%LOG%"
  py -3 -m eval.run_changeling --games 1000 --arm random --theme folk --seats 5 ^
    --rounds %%R --seed %SEED% --out "%OUTDIR%\cl-rounds%%R-random.json" >>"%LOG%" 2>&1
)

for %%R in (2 3) do (
  echo [arm] --arm llm --rounds %%R, 200 games - log %OUTDIR%\cl-rounds%%R.log>>"%LOG%"
  py -3 -m eval.run_changeling --games 200 --arm llm --backend local ^
    --model "%MODEL%" --no-thinking --seats 5 --theme folk --rounds %%R --seed %SEED% --timeout 240 ^
    --out "%OUTDIR%\cl-rounds%%R.json" >>"%OUTDIR%\cl-rounds%%R.log" 2>&1
  rem Judged on the arm's OWN log, so arm 1's marker can never vouch for arm 2.
  findstr /c:"PARLOR DONE rc=0 games=200/200" "%OUTDIR%\cl-rounds%%R.log" >nul
  if errorlevel 1 (
    echo [pair] arm rounds%%R did not write PARLOR DONE rc=0 games=200/200 - REFUSING to continue.>>"%LOG%"
    echo PARLOR PAIR DONE rc=1 >>"%LOG%"
    exit /b 1
  )
  echo [pair] arm rounds%%R down %DATE% %TIME%>>"%LOG%"
)

echo [pair] both arms down %DATE% %TIME%>>"%LOG%"
echo PARLOR PAIR DONE rc=0 arms=2/2 >>"%LOG%"
