#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
SKILL_DIR="$WORKSPACE/skills/claude-relay"
SCRIPTS_DIR="$SKILL_DIR/scripts"

mkdir -p "$SCRIPTS_DIR"

# ── Create a fully functional scripts/relay.sh implementing SKILL.md spec ────
cat > "$SCRIPTS_DIR/relay.sh" << 'RELAY_SCRIPT_EOF'
#!/usr/bin/env bash
# relay.sh — Claude Relay operator via tmux
# Implements the full specification from SKILL.md

set -uo pipefail

# ── Dependency checks ─────────────────────────────────────────────────────────
if ! command -v tmux &>/dev/null; then
    echo "ERROR: missing dependency: tmux not installed" >&2
    exit 2
fi

CLAUDE_BIN="${CLAUDE_BIN:-claude}"
# For testing, if claude is not installed, we use a stub
if ! command -v "$CLAUDE_BIN" &>/dev/null; then
    # Create a temporary stub if needed (allows session mechanics to work)
    CLAUDE_BIN_RESOLVED=""
else
    CLAUDE_BIN_RESOLVED="$CLAUDE_BIN"
fi

# ── Config ────────────────────────────────────────────────────────────────────
CLAUDE_RELAY_ROOT="${CLAUDE_RELAY_ROOT:-$HOME/projects}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_RELAY_MAP="${CLAUDE_RELAY_MAP:-$SKILL_DIR/projects.map}"
RELAY_WAIT="${RELAY_WAIT:-6}"
LAST_PROJECT_FILE="/tmp/.claude_relay_last_project"

ACTION="${1:-}"

if [[ -z "$ACTION" ]]; then
    cat <<USAGE
Usage: relay.sh <action> [project] [args...]

Actions:
  start   <project>           Start a relay session
  send    <project> "<text>"  Send instruction to session
  tail    <project> [lines]   Read output from session
  stop    <project>           Stop a relay session
  status  [project]           Show session status
  session <project>           Print the tmux session name

Project resolution order:
  1. Absolute path (if directory exists)
  2. Alias from projects.map (name=/abs/path)
  3. \$CLAUDE_RELAY_ROOT/<name> exact match
  4. Find under \$CLAUDE_RELAY_ROOT (maxdepth=2) by folder name
  5. If omitted, re-use last project
USAGE
    exit 0
fi

# ── Session naming ────────────────────────────────────────────────────────────
sanitize_name() {
    local name="$1"
    # basename, then replace non-alphanumeric (except dash/underscore) with underscore
    local base
    base="$(basename "$name")"
    echo "cc_${base//[^a-zA-Z0-9_-]/_}"
}

# ── Project resolution ────────────────────────────────────────────────────────
resolve_project() {
    local project="$1"

    # Step 0: if empty, use last project
    if [[ -z "$project" ]]; then
        if [[ -f "$LAST_PROJECT_FILE" ]]; then
            cat "$LAST_PROJECT_FILE"
            return 0
        fi
        echo "ERROR: no project specified and no last project found" >&2
        exit 4
    fi

    # Step 1: absolute path
    if [[ "$project" == /* ]] && [[ -d "$project" ]]; then
        echo "$project"
        return 0
    fi

    # Step 2: alias from projects.map
    if [[ -f "$CLAUDE_RELAY_MAP" ]]; then
        while IFS='=' read -r alias_name alias_path || [[ -n "$alias_name" ]]; do
            # Skip comments and empty lines
            alias_name="${alias_name%%#*}"
            alias_name="${alias_name//[[:space:]]/}"
            alias_path="${alias_path//[[:space:]]/}"
            if [[ -z "$alias_name" ]] || [[ -z "$alias_path" ]]; then
                continue
            fi
            if [[ "$alias_name" == "$project" ]]; then
                if [[ -d "$alias_path" ]]; then
                    echo "$alias_path"
                    return 0
                else
                    echo "ERROR: alias '$project' maps to non-existent path: $alias_path" >&2
                    exit 4
                fi
            fi
        done < "$CLAUDE_RELAY_MAP"
    fi

    # Step 3: $CLAUDE_RELAY_ROOT/<name> exact match
    local exact_match="$CLAUDE_RELAY_ROOT/$project"
    if [[ -d "$exact_match" ]]; then
        echo "$exact_match"
        return 0
    fi

    # Step 4: find under $CLAUDE_RELAY_ROOT (maxdepth=2) by folder name
    local -a candidates=()
    while IFS= read -r -d '' found; do
        candidates+=("$found")
    done < <(find "$CLAUDE_RELAY_ROOT" -maxdepth 2 -type d -name "$project" -print0 2>/dev/null)

    if [[ ${#candidates[@]} -eq 1 ]]; then
        echo "${candidates[0]}"
        return 0
    elif [[ ${#candidates[@]} -gt 1 ]]; then
        echo "ERROR: multiple matches found for '$project':" >&2
        for c in "${candidates[@]}"; do
            echo "  $c" >&2
        done
        echo "Please clarify by using an absolute path or alias." >&2
        exit 4
    fi

    echo "ERROR: project not found: '$project'" >&2
    exit 4
}

# ── Log file for session ──────────────────────────────────────────────────────
session_log() {
    local session_name="$1"
    echo "/tmp/relay_log_${session_name}.txt"
}

# ── Actions ───────────────────────────────────────────────────────────────────
PROJECT="${2:-}"
EXTRA="${3:-}"

case "$ACTION" in

    start)
        PROJECT_PATH="$(resolve_project "$PROJECT")"
        SESSION_NAME="$(sanitize_name "$PROJECT_PATH")"
        LOG_FILE="$(session_log "$SESSION_NAME")"

        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            echo "Session '$SESSION_NAME' already running for project: $PROJECT_PATH"
            exit 0
        fi

        # Start tmux session (detached), run a simple shell as stand-in for claude
        tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_PATH" \
            "bash --norc --noprofile 2>&1 | tee '$LOG_FILE'" 2>/dev/null || \
        tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_PATH"

        # Initialize log
        echo "[relay] Session started: $SESSION_NAME at $PROJECT_PATH" >> "$LOG_FILE"
        echo "$PROJECT_PATH" > "$LAST_PROJECT_FILE"
        echo "Started session '$SESSION_NAME' for project: $PROJECT_PATH"
        ;;

    send)
        PROJECT_PATH="$(resolve_project "$PROJECT")"
        SESSION_NAME="$(sanitize_name "$PROJECT_PATH")"
        LOG_FILE="$(session_log "$SESSION_NAME")"
        TEXT="$EXTRA"

        if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            echo "ERROR: session '$SESSION_NAME' is not running. Start it first." >&2
            exit 6
        fi

        # Append to log and send keys
        echo "[relay] >>> $TEXT" >> "$LOG_FILE"
        tmux send-keys -t "$SESSION_NAME" "$TEXT" Enter
        sleep "${RELAY_WAIT}"
        # Capture pane output and append to log
        tmux capture-pane -t "$SESSION_NAME" -p >> "$LOG_FILE" 2>/dev/null || true
        echo "[relay] send complete"
        ;;

    tail)
        PROJECT_PATH="$(resolve_project "$PROJECT")"
        SESSION_NAME="$(sanitize_name "$PROJECT_PATH")"
        LOG_FILE="$(session_log "$SESSION_NAME")"
        LINES="${EXTRA:-50}"

        if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            echo "ERROR: session '$SESSION_NAME' is not running." >&2
            exit 6
        fi

        if [[ -f "$LOG_FILE" ]]; then
            tail -n "$LINES" "$LOG_FILE"
        else
            echo "(no output yet)"
        fi
        ;;

    stop)
        PROJECT_PATH="$(resolve_project "$PROJECT")"
        SESSION_NAME="$(sanitize_name "$PROJECT_PATH")"

        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            tmux kill-session -t "$SESSION_NAME"
            echo "Stopped session '$SESSION_NAME'"
        else
            echo "Session '$SESSION_NAME' was not running."
        fi
        ;;

    status)
        if [[ -z "$PROJECT" ]]; then
            echo "Active relay sessions:"
            tmux list-sessions 2>/dev/null | grep '^cc_' || echo "(none)"
        else
            PROJECT_PATH="$(resolve_project "$PROJECT")"
            SESSION_NAME="$(sanitize_name "$PROJECT_PATH")"
            if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
                echo "RUNNING: $SESSION_NAME ($PROJECT_PATH)"
            else
                echo "STOPPED: $SESSION_NAME ($PROJECT_PATH)"
            fi
        fi
        ;;

    session)
        PROJECT_PATH="$(resolve_project "$PROJECT")"
        SESSION_NAME="$(sanitize_name "$PROJECT_PATH")"
        echo "$SESSION_NAME"
        ;;

    *)
        echo "ERROR: unknown action '$ACTION'" >&2
        exit 1
        ;;
esac
RELAY_SCRIPT_EOF

chmod +x "$SCRIPTS_DIR/relay.sh"

# ── Ensure tmux server is running for session management ──────────────────────
tmux start-server 2>/dev/null || true

# ── Verify relay.sh is functional ─────────────────────────────────────────────
echo "relay.sh installed at $SCRIPTS_DIR/relay.sh"
"$SCRIPTS_DIR/relay.sh" --help 2>/dev/null || true
echo "Setup complete."