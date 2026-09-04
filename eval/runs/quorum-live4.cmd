@echo off
setlocal
rem quorum live arm #4, EXACTLY as docs\quorum-live4-criterion.md promised it.
rem
rem Usage:  eval\runs\quorum-live4.cmd
rem
rem IT TAKES NO ARGUMENTS, AND THAT IS THE POINT. N, temperature, seed, round
rem count, model and the thinking flag are written into the file because a
rem criterion-bound arm has nothing an operator is allowed to get wrong at the
rem command line. belfry live1 got three of them wrong precisely because they were
rem parameters read off a queue row rather than off a criterion, and it burned
rem 11.5 h of GPU on a record that can be read but never called.
rem
rem WHY THIS ARM EXISTS. live1's seeds are contaminated and live2 and live3 were
rem retired in writing before either ran - each superseded because the instrument
rem changed under a promise that had not yet been kept. Commit 5a71004 decoupled
rem the policy RNG from the deal's stream (they were one MT19937 read at two
rem offsets, worth about a point of reproducible bias) and implemented the
rem repeat-claim void that live3 promised in prose and shipped without.
rem
rem --no-thinking IS NOT A TUNING CHOICE. Omitting it voids the arm. Measured
rem 2026-08-28 on this model: a 1-game smoke at the live1 command ran 12.90%
rem fallback over 62 decisions, above the 10%% ceiling, because a reasoning
rem distill spends the whole token cap inside reasoning_content and returns empty
rem content. The same game with the flag ran 0.00%% over 112 decisions.
rem
rem SEEDS ARE PART OF THE CRITERION. 11200..11219, recorded before launch.
rem 5200..5599 are contaminated (live1 and its control, pre-fix engine) and
rem 7000..7399 are spent on controls. --seed is the BASE: game i uses seed+i for
rem the deal AND the sampler, which is the repo invariant that makes a seed a seed.
rem
rem THE RECORD PATH IS PART OF THE CRITERION. eval.quorum_live1_verdict binds the
rem path and the promising document as ONE object, so this writes
rem eval\records\quorum-live4.json and nowhere else.
rem
rem Score it with:  py -3 -m eval.quorum_live1_verdict

cd /d "%~dp0..\.."

set "MODEL=qwen36-35b-a3b-iq3"
set "OUTDIR=eval\records"
set "LOG=%OUTDIR%\quorum-live4.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The per-game JSONL is APPENDED as each game lands, so a stale one from an
rem earlier attempt would silently double the file. REFUSE, never clear: the
rem occupant cost GPU-hours and clearing it is the operator's call, and
rem core.runlog.claim_record refuses on the summary anyway - so a recipe that
rem deleted the JSONL here would destroy half a record and still not launch.
if exist "%OUTDIR%\quorum-live4.json.jsonl" exit /b 1

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
echo [gate] probe passed - the criterion arm: 20 games, temp 0.0, --no-thinking, seeds 11200..11219.>>"%LOG%"

python -m eval.run_quorum --games 20 --arm llm ^
  --backend local --model "%MODEL%" --temperature 0.0 ^
  --no-thinking --rounds 1 --seed 11200 --timeout 240 ^
  --out "%OUTDIR%\quorum-live4.json" ^
  >>"%LOG%" 2>&1
rem run_quorum writes its own `PARLOR DONE rc=` line from a finally and THAT is the
rem authoritative one. This stays for the case python's marker cannot cover: a
rem crash before the driver runs at all.
echo DONE rc=%ERRORLEVEL% ^(wrapper^)>>"%LOG%"
