#!/bin/sh
# Install the repo's git hooks. Idempotent - run it again after a fresh clone.
#
# The hook is a two-line stub that calls the tracked checker, so the policy
# stays reviewable in the tree and the hook holds no logic of its own.
# .git/hooks is per-clone and untracked by definition, which is why this
# script exists at all.

set -e
ROOT=$(git rev-parse --show-toplevel)
HOOK="$ROOT/.git/hooks/pre-commit"

cat > "$HOOK" <<'EOF'
#!/bin/sh
exec sh "$(git rev-parse --show-toplevel)/scripts/hygiene-check.sh"
EOF

chmod +x "$HOOK"
echo "installed $HOOK -> scripts/hygiene-check.sh"
