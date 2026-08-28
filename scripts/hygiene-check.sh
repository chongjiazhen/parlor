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
# would do. That is the scope invariant in CLAUDE.md and it is checked when a
# doc lands, by a reader.
#
# Usage:  sh scripts/hygiene-check.sh          # staged changes (what the hook runs)
#         sh scripts/hygiene-check.sh --range origin/main..HEAD
# Install as a hook:  sh scripts/install-hooks.sh

set -e
cd "$(git rev-parse --show-toplevel)"

if [ "$1" = "--range" ] && [ -n "$2" ]; then
    DIFF=$(git diff --unified=0 "$2")
else
    DIFF=$(git diff --cached --unified=0)
fi

[ -z "$DIFF" ] && exit 0

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

    if (index(line, endash) || index(line, emdash))
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
