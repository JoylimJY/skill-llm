#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=/workspace

# ── Mock `arh` binary ─────────────────────────────────────────────────────────
cat > /usr/local/bin/arh << 'ARHMOCK'
#!/usr/bin/env bash
# Mock arh — records every invocation, simulates state side-effects.

LOG=/workspace/arh_invocations.log
STATEDIR=/workspace/.arh_state
mkdir -p "$STATEDIR"

ARGS="$*"
echo "arh $ARGS" >> "$LOG"

subcmd="${1:-}"

case "$subcmd" in
  feature)
    shift
    if [ "${1:-}" = "next" ]; then
        shift
        FEATURE="$1"
        # Read current feature
        CURRENT=$(cat "$STATEDIR/current_feature" 2>/dev/null || echo "main")
        echo "$CURRENT" > "$STATEDIR/parent_of_${FEATURE}"
        echo "$FEATURE" > "$STATEDIR/current_feature"
        # Create actual git branch
        git -C /workspace checkout -b "feature/${FEATURE}" 2>/dev/null || true
    else
        FEATURE="$1"
        # Branch off main
        echo "main" > "$STATEDIR/parent_of_${FEATURE}"
        echo "$FEATURE" > "$STATEDIR/current_feature"
        git -C /workspace checkout main 2>/dev/null || true
        git -C /workspace checkout -b "feature/${FEATURE}" 2>/dev/null || true
    fi
    echo "[arh] Created feature: $FEATURE"
    ;;
  publish)
    FEATURE=$(cat "$STATEDIR/current_feature" 2>/dev/null || echo "unknown")
    echo "[arh] Published PR for feature: $FEATURE with args: $ARGS"
    ;;
  pull)
    echo "[arh] Pulled latest from origin main"
    ;;
  rebase)
    echo "[arh] Rebased with args: $ARGS"
    ;;
  tidy)
    echo "[arh] Tidy executed with args: $ARGS"
    ;;
  log)
    echo "[arh] Log tree displayed"
    ;;
  checkout|co)
    shift
    TARGET="$1"
    echo "$TARGET" > "$STATEDIR/current_feature"
    echo "[arh] Checked out: $TARGET"
    ;;
  version|-v)
    echo "arh version 0.0.42"
    ;;
  lint)
    echo "[arh] Lint passed"
    ;;
  test)
    echo "[arh] Tests passed"
    ;;
  -s)
    echo "[arh] Status tree displayed"
    ;;
  *)
    # Could be -s, -c, etc. combined
    echo "[arh] Command: $ARGS"
    ;;
esac

exit 0
ARHMOCK
chmod +x /usr/local/bin/arh

# ── Mock `git-bzl` binary ─────────────────────────────────────────────────────
cat > /usr/local/bin/git-bzl << 'GITBZLMOCK'
#!/usr/bin/env bash
LOG=/workspace/git_bzl_invocations.log
echo "git-bzl $*" >> "$LOG"
subcmd="${1:-}"
case "$subcmd" in
  refresh)
    echo "[git-bzl] Build graph refreshed."
    ;;
  *)
    echo "[git-bzl] Called with: $*"
    ;;
esac
exit 0
GITBZLMOCK
chmod +x /usr/local/bin/git-bzl

# ── Git config so commits inside mock work ────────────────────────────────────
git -C /workspace config user.email "dev_UBER@uber.com"
git -C /workspace config user.name  "Dev UBER"
git -C /workspace checkout main 2>/dev/null || true

echo "setup_script: mock binaries installed."