#!/bin/sh
# Pre-commit hygiene gate. Runs on every commit so publish hygiene is a
# property of the commit rather than a pass somebody remembers to run.
#
# It reads ADDED LINES ONLY, from the staged diff. That is the whole reason it
# needs no allowlist: a line already in the tree cannot fire it, so the gate
# never argues with a decision that was already made and reviewed.
#
# Every pattern is STRUCTURAL - an email shape, a user-profile path shape, a
# key shape. None of them is a literal name, address or secret. A public
# checker that grepped for the actual value would be the disclosure it exists
# to prevent: the forbidden string would then ship, in plaintext, in the one
# file every clone carries.
#
# What it CANNOT check is the judgement half - whether a new doc assesses a
# third party, quotes unread work, or names an author where an identifier
# would do. That is the scope invariant in AGENTS.md and it is checked when a
# doc lands, by a reader.
#
# Usage:  sh scripts/hygiene-check.sh          # staged changes (what the hook runs)
#         sh scripts/hygiene-check.sh --range origin/main..HEAD
# Install as a hook:  sh scripts/install-hooks.sh

set -e
cd "$(git rev-parse --show-toplevel)"

# ---------------------------------------------------------------------------
# The queue does not grow once it is over budget.
#
# queue.md's own first rule is that done work leaves to git log. It stopped
# being kept and the file reached 1200 lines - a read every cold session pays
# for, most of it work that had already landed. Prose could not enforce it,
# because the rule had no destination: annotations had to stay somewhere, and
# appending was the only move available. They have one now (docs/slices.md,
# docs/measurements.md, docs/decisions.md), so the rule can be a gate.
#
# It is a RATCHET, not a ceiling. Under CEILING the file is free. Over it, a
# commit may shrink the file or leave it flat, never grow it. A flat ceiling
# would have blocked the next commit outright at the 916 lines it started from,
# which teaches the author to pass --no-verify rather than to prune.
#
# **The budget is BYTES, and it was lines until 2026-08-28.** A line count is a
# proxy for what a cold session pays, and it is defeatable without paying
# anything: rewrapping two lines into one satisfies a line ratchet and saves
# zero tokens. Measured when this bit for the first time - a row was trimmed
# from 17 lines to 12, and part of that trim was reflow rather than cuts. Bytes
# are what the read actually costs, so bytes are what the gate counts. The
# ceiling is the old 400-line budget at this file's own 75 bytes/line.
#
# Both sides are read through `git show` rather than off disk, so the count is
# the BLOB's - line endings are whatever git stores, and the same number comes
# back on a CRLF checkout and an LF one.
QUEUE_CEILING=30000
QUEUE_PATH=queue.md

# The old side of the ratchet has to follow a RENAME, or the rename reads as
# growth from zero.
#
# git resolves HEAD:<new path> to nothing on the commit that moves the file,
# `2>/dev/null` swallows the error, QUEUE_OLD falls back to 0, and the whole
# file then counts as added - so the gate blocks a commit that changed nothing
# but the name. It fails silent in both directions: no line of output says the
# old side was never found, and the byte numbers it prints look like a real
# reading. Rename detection hands back the pre-rename path, which is the blob
# the count actually wants to compare against.
queue_old_path() {
    # $1 = the diff selector (--cached, or a range). $2 = the current path.
    # Falls back to the current path, which is the right answer whenever the
    # file was not renamed in this commit.
    git diff "$1" -M --name-status 2>/dev/null | awk -v new="$2" '
        $1 ~ /^R/ && $3 == new { print $2; found = 1; exit }
        END { if (!found) print new }
    '
}

if [ "$1" = "--budget" ]; then
    QUEUE_NOW=$(git show "HEAD:$QUEUE_PATH" 2>/dev/null | wc -c | tr -d ' ')
    [ -z "$QUEUE_NOW" ] && QUEUE_NOW=0
    echo "$QUEUE_PATH at HEAD: $QUEUE_NOW bytes, ceiling $QUEUE_CEILING."
    if [ "$QUEUE_NOW" -gt "$QUEUE_CEILING" ]; then
        echo "Over budget, so this commit may shrink it or hold it flat, never grow it."
        echo "Write the row to fit, or move something out in the same commit."
    else
        echo "Under budget: free to grow by $((QUEUE_CEILING - QUEUE_NOW)) bytes."
    fi
    IDX=$(git show HEAD:docs/README.md 2>/dev/null | wc -l | tr -d ' ')
    [ -z "$IDX" ] && IDX=0
    echo "docs/README.md at HEAD: $IDX lines, advisory ceiling 150."
    exit 0
fi

if [ "$1" = "--range" ] && [ -n "$2" ]; then
    QUEUE_BASE=${2%%..*}
    QUEUE_TIP=${2##*..}
    [ -z "$QUEUE_TIP" ] && QUEUE_TIP=HEAD
    QUEUE_CHANGED=$(git diff --name-only "$2" -- "$QUEUE_PATH")
    QUEUE_OLD_PATH=$(queue_old_path "$2" "$QUEUE_PATH")
    QUEUE_OLD_REF="$QUEUE_BASE:$QUEUE_OLD_PATH"
    QUEUE_NEW_REF="$QUEUE_TIP:$QUEUE_PATH"
else
    QUEUE_CHANGED=$(git diff --cached --name-only -- "$QUEUE_PATH")
    QUEUE_OLD_PATH=$(queue_old_path --cached "$QUEUE_PATH")
    QUEUE_OLD_REF="HEAD:$QUEUE_OLD_PATH"
    QUEUE_NEW_REF=":$QUEUE_PATH"
fi

if [ -n "$QUEUE_CHANGED" ]; then
    QUEUE_NEW=$(git show "$QUEUE_NEW_REF" 2>/dev/null | wc -c | tr -d ' ')
    QUEUE_OLD=$(git show "$QUEUE_OLD_REF" 2>/dev/null | wc -c | tr -d ' ')
    [ -z "$QUEUE_NEW" ] && QUEUE_NEW=0
    [ -z "$QUEUE_OLD" ] && QUEUE_OLD=0
    if [ "$QUEUE_NEW" -gt "$QUEUE_CEILING" ] && [ "$QUEUE_NEW" -gt "$QUEUE_OLD" ]; then
        cat >&2 <<MSG

[hygiene] $QUEUE_PATH grew: $QUEUE_OLD -> $QUEUE_NEW bytes, over the $QUEUE_CEILING-byte budget.

The queue keeps what can still change. A landed slice is struck and moved to
docs/slices.md, a dated reading to docs/measurements.md, a settled call to
docs/decisions.md - live rows cite them by name, so they are kept, not deleted.
Move something out in this commit, or shrink what you are adding.

Read the budget BEFORE writing the row, not after - discovering it by failing
this gate costs a round trip per attempt, which is how it was found:

  sh scripts/hygiene-check.sh --budget
MSG
        exit 1
    fi
fi
if [ "$1" = "--range" ] && [ -n "$2" ]; then
    DIFF=$(git diff --unified=0 "$2")
else
    DIFF=$(git diff --cached --unified=0)
fi

[ -z "$DIFF" ] && exit 0

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# The docs index is what stands in for folders, and it has a scanning limit.
#
# ADVISORY, never fatal, and that is the whole design. Nothing is broken at 151
# lines; what happens is that `docs/README.md` stops being an index somebody uses
# and becomes a document somebody skims, at which point the flat `docs/` layout
# is being held together by a file nobody reads. That is a prompt to think, not
# a commit to refuse - a gate that blocked here would be enforcing a taste.
#
# It fires only when the commit TOUCHES the index, so it reaches the person who
# can act on it and nobody else. The judgement triggers that go with it - a doc
# with two plausible homes, a second contributor, ~40 files - cannot be counted
# and live at the top of the file itself.
DOCS_INDEX_CEILING=150

if [ "$1" = "--range" ] && [ -n "$2" ]; then
    INDEX_CHANGED=$(git diff --name-only "$2" -- docs/README.md)
    INDEX_REF="${2##*..}:docs/README.md"
    [ "$INDEX_REF" = ":docs/README.md" ] && INDEX_REF="HEAD:docs/README.md"
else
    INDEX_CHANGED=$(git diff --cached --name-only -- docs/README.md)
    INDEX_REF=":docs/README.md"
fi

if [ -n "$INDEX_CHANGED" ]; then
    INDEX_LINES=$(git show "$INDEX_REF" 2>/dev/null | wc -l | tr -d ' ')
    [ -z "$INDEX_LINES" ] && INDEX_LINES=0
    if [ "$INDEX_LINES" -gt "$DOCS_INDEX_CEILING" ]; then
        cat >&2 <<MSG

[hygiene] advisory, not a failure: docs/README.md is $INDEX_LINES lines, past $DOCS_INDEX_CEILING.

That file is what stands in for folders in a flat docs/ directory. Past this
length it is skimmed rather than used, and the layout is resting on a file
nobody reads. Its own header carries the other three triggers and what the
split would be if one fires. This commit is not blocked.
MSG
    fi
fi
# ---------------------------------------------------------------------------

# Built at runtime from octal escapes so this file holds no literal en- or
# em-dash and cannot flag itself.
ENDASH=$(printf '\342\200\223')
EMDASH=$(printf '\342\200\224')

printf '%s\n' "$DIFF" | awk -v endash="$ENDASH" -v emdash="$EMDASH" '
function report(label,   text) {
    text = line
    if (length(text) > 96) text = substr(text, 1, 96) "..."
    printf "  %s:%d  %s\n    %s\n", file, ln, label, text
    fail = 1
}
/^\+\+\+ / {
    file = substr($0, 7)
    if (file == "dev/null") file = ""
    next
}
/^@@ / {
    if (match($0, /\+[0-9]+/)) ln = substr($0, RSTART + 1, RLENGTH - 1) + 0
    next
}
/^\+/ {
    if (file == "") next
    # The checker states the patterns it looks for, so it matches itself. No
    # other file gets this, and the exemption is the file rather than a string.
    if (file == "scripts/hygiene-check.sh") { ln++; next }
    line = substr($0, 2)

    if (file ~ /^\.scratch\//)
        report("working notes must never be tracked")

    if (line ~ /C:\\Users\\[A-Za-z0-9_]+/ || line ~ /C:\/Users\/[A-Za-z0-9_]+/)
        report("personal Windows path")

    if (line ~ /\/home\/[A-Za-z][A-Za-z0-9_-]*\//)
        report("personal home path")

    if (line ~ /~\/atelier|\/atelier\/(guidelines|rules|docs)\//)
        report("personal harness path - it resolves for nobody else")

    if (line ~ /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z][A-Za-z]+/ &&
        line !~ /@users\.noreply\.github\.com/)
        report("email address")

    if (line ~ /https?:\/\/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/ &&
        line !~ /:\/\/(127\.0\.0\.1|0\.0\.0\.0)/)
        report("non-loopback endpoint - make it an env var with a loopback default")

    if (line ~ /(api[_-]?key|secret|token|password)["'"'"']?[ \t]*[:=][ \t]*["'"'"'][A-Za-z0-9_-]{16,}/)
        report("secret-shaped literal")

    if (line ~ /sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{12,}/)
        report("credential-shaped token - rotate it, a committed secret is compromised")

    if (line ~ /superpowers|atelier cluster|spec-lite|Co-Authored-By|claude -p /)
        report("harness vocabulary - it reads as process leakage in a public tree")

    # House style is about prose written HERE. A transcript is verbatim model
    # output and it is the EVIDENCE a claim ships with - editing one to satisfy
    # a style rule falsifies the thing it exists to prove. So the dash check
    # alone skips that directory; every material pattern above still applies to
    # it, because a personal path or an endpoint in a transcript is a leak
    # whoever typed it. Same shape as the exemption this file makes for itself: it
    # is a directory, not a string, so it maps nothing.
    if ((index(line, endash) || index(line, emdash)) && file !~ /^transcripts\//)
        report("en- or em-dash - house style is ASCII hyphen-minus")

    ln++
    next
}
END {
    if (fail) exit 1
}
' && exit 0

cat >&2 <<'MSG'

[hygiene] gate failed - the hits above are in lines this commit ADDS.
Fix them, or commit deliberately with --no-verify and say why in the message.
A hit that is a reviewed keep (a published-work citation, a licence-obligation
credit) means the pattern is wrong: tighten the pattern, do not add an
exception list. A list of what is excused is a map to the material.
MSG
exit 1
