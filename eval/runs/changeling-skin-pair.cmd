@echo off
setlocal
rem Changeling name-form pair, greek vs greek-named - frozen 2026-09-02.
rem Bound by docs\changeling-skin-pair-criterion.md; nothing here is a setting,
rem every value below is a copy of that file's.
rem
rem Two CPU controls, then two live arms serially on one card. Arm 2 is refused
rem without arm 1's own PARLOR DONE rc=0 - both arms or the pairing is lost.

cd /d "%~dp0..\.."

set "OUTDIR=eval\records"
set "MODEL=qwen36-35b-a3b-iq3"
set "SEED=5000"
set "LOG=%OUTDIR%\cl-skin-pair.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

for %%T in (greek greek-named) do (
  if exist "%OUTDIR%\cl-skin-%%T.json" exit /b 1
  if exist "%OUTDIR%\cl-skin-%%T-random.json" exit /b 1
)

echo [pair] started %DATE% %TIME% - 200 games/arm, seed %SEED%, model %MODEL%>>"%LOG%"
echo [gate] burst-probing local/%MODEL% before either arm...>>"%LOG%"
py -3 -m eval.probe_tier --backend local --model "%MODEL%" --require-served "%MODEL%" -n 3 --timeout 120 >>"%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [gate] probe did not pass ^(rc=%ERRORLEVEL%^) - not launching.>>"%LOG%"
  echo PARLOR PAIR DONE rc=1 arms=0/2 >>"%LOG%"
  exit /b 1
)

for %%T in (greek greek-named) do (
  echo [control] --arm random --theme %%T>>"%LOG%"
  py -3 -m eval.run_changeling --games 1000 --arm random --theme %%T --seats 5 ^
    --seed %SEED% --out "%OUTDIR%\cl-skin-%%T-random.json" >>"%LOG%" 2>&1
)

for %%T in (greek greek-named) do (
  echo [arm] --arm llm --theme %%T, 200 games - log %OUTDIR%\cl-skin-%%T.log>>"%LOG%"
  py -3 -m eval.run_changeling --games 200 --arm llm --backend local ^
    --model "%MODEL%" --no-thinking --seats 5 --theme %%T --seed %SEED% --timeout 240 ^
    --out "%OUTDIR%\cl-skin-%%T.json" >>"%OUTDIR%\cl-skin-%%T.log" 2>&1
  rem Judged on the arm's OWN log, so arm 1's marker can never vouch for arm 2.
  findstr /c:"PARLOR DONE rc=0 games=200/200" "%OUTDIR%\cl-skin-%%T.log" >nul
  if errorlevel 1 (
    echo [pair] arm %%T did not write PARLOR DONE rc=0 games=200/200 - REFUSING to continue.>>"%LOG%"
    echo PARLOR PAIR DONE rc=1 >>"%LOG%"
    exit /b 1
  )
  echo [pair] arm %%T down %DATE% %TIME%>>"%LOG%"
)

echo [pair] both arms down %DATE% %TIME%>>"%LOG%"
echo PARLOR PAIR DONE rc=0 arms=2/2 >>"%LOG%"
