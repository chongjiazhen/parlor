@echo off
setlocal
rem belfry live arm #2, EXACTLY as docs\belfry-live2-criterion.md promised it.
rem
rem Usage:  eval\runs\belfry-live2.cmd
rem
rem IT TAKES NO ARGUMENTS, AND THAT IS THE POINT. belfry-local.cmd is the general
rem launcher and its defaults are a convenience; this one is a criterion. N,
rem temperature, seed, seats, script, round count and the thinking flag are
rem written into the file because a criterion-bound arm has nothing an operator is
rem allowed to get wrong at the command line - the first attempt at live1 got
rem three of them wrong precisely because they were parameters read off a queue
rem row rather than off a criterion.
rem
rem WHY THIS ARM EXISTS. live1's criterion promised temperature 0.0 WITHOUT
rem --no-thinking, and measured 2026-09-01 those settings run 58.33% fallback
rem (63/108 over two games, 10 of 10 seat-games above the 10% bar) and fire
rem live1's own void condition at both thresholds independently. q36 is a
rem reasoning distill: without the flag it fails to terminate its reasoning, the
rem parser rejects the reply, and more than half of every decision is played at
rem random. The arm as promised buys a guaranteed VOID for ~30 h of GPU.
rem
rem live2 therefore changes ONE launch setting - --no-thinking - and nothing else.
rem Every endpoint, bar, floor and void condition is carried across unedited.
rem live1's criterion is NOT edited: it has already run, its numbers are in view,
rem and editing it now would be the peeking the discipline exists to refuse.
rem
rem THE RECORD PATH IS PART OF THE CRITERION. eval.belfry_live1_verdict binds the
rem path and the expected settings as ONE object, selected by --criterion live2,
rem so this writes eval\records\belfry-live2.json and nowhere else.
rem
rem Score it with:  py -3 -m eval.belfry_live1_verdict --criterion live2

cd /d "%~dp0..\.."

set "MODEL=qwen36-35b-a3b-iq3"
set "OUTDIR=eval\records"
set "LOG=%OUTDIR%\belfry-live2.log"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

rem The per-game JSONL is APPENDED as each game lands, so a stale one from an
rem earlier attempt would silently double the file.
if exist "%OUTDIR%\belfry-live2.json.jsonl" del "%OUTDIR%\belfry-live2.json.jsonl"

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
echo [gate] probe passed - the criterion arm: 60 games, temp 0.0, --no-thinking.>>"%LOG%"

python -m eval.run_belfry --games 60 --arm llm --seats 5 --script compact ^
  --rounds 1 --backend local --model "%MODEL%" --temperature 0.0 ^
  --no-thinking --seed 6100 --timeout 240 ^
  --out "%OUTDIR%\belfry-live2.json" ^
  >>"%LOG%" 2>&1
rem run_belfry writes its own `PARLOR DONE rc=` line from a finally and THAT is the
rem authoritative one. This stays for the case python's marker cannot cover: a
rem crash before the driver runs at all.
echo DONE rc=%ERRORLEVEL% ^(wrapper^)>>"%LOG%"
