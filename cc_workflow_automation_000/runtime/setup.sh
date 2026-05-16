#!/bin/bash
set -e

WORKSPACE="/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"
STATE_FILE="$SCRIPTS_DIR/.cc_state"

# -------------------------------------------------------
# Write the mock cc.sh script
# -------------------------------------------------------
cat > "$SCRIPTS_DIR/cc.sh" << 'MOCK_SCRIPT'
#!/bin/bash

# Mock cc.sh — simulates the real cc relay script for testing
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_FILE="$SCRIPTS_DIR/.cc_state"
LONG_OUTPUT_FILE="$SCRIPTS_DIR/.cc_long_output.txt"

# Read state
configured=$(grep 'configured=' "$STATE_FILE" | cut -d= -f2)
active_project=$(grep 'active_project=' "$STATE_FILE" | cut -d= -f2)

COMMAND="$1"

case "$COMMAND" in

  "projects")
    if [ "$configured" != "true" ]; then
      echo "SETUP_NEEDED"
      exit 100
    fi
    # List available projects
    ROOT=$(grep 'root=' "$STATE_FILE" | cut -d= -f2)
    echo "Available projects in $ROOT:"
    ls "$ROOT" 2>/dev/null | while read p; do
      if [ "$p" = "$active_project" ]; then
        echo "  ★ $p"
      else
        echo "  $p"
      fi
    done
    exit 0
    ;;

  "config")
    SUBCMD="$2"
    if [ "$SUBCMD" = "root" ]; then
      PATH_ARG="$3"
      if [ -z "$PATH_ARG" ]; then
        echo "ERROR: No path provided"
        exit 1
      fi
      # Expand ~ if present
      PATH_EXPANDED="${PATH_ARG/#\~/$HOME}"
      # Save config
      {
        echo "configured=true"
        echo "active_project=$active_project"
        echo "root=$PATH_EXPANDED"
      } > "$STATE_FILE"
      echo "Project root configured: $PATH_EXPANDED"
      exit 0
    fi
    echo "ERROR: Unknown config subcommand"
    exit 1
    ;;

  "on")
    PROJECT="$2"
    if [ -z "$PROJECT" ]; then
      echo "ERROR: No project specified"
      exit 1
    fi
    if [ "$configured" != "true" ]; then
      echo "ERROR: Not configured. Run config root first."
      exit 1
    fi
    # Update active project
    ROOT=$(grep 'root=' "$STATE_FILE" | cut -d= -f2)
    {
      echo "configured=true"
      echo "active_project=$PROJECT"
      echo "root=$ROOT"
    } > "$STATE_FILE"
    echo "SESSION_STARTED: $PROJECT"
    exit 0
    ;;

  "off")
    PROJECT="$2"
    ROOT=$(grep 'root=' "$STATE_FILE" | cut -d= -f2)
    {
      echo "configured=true"
      echo "active_project="
      echo "root=$ROOT"
    } > "$STATE_FILE"
    echo "SESSION_STOPPED"
    exit 0
    ;;

  "check")
    PROJECT="$2"
    if [ "$active_project" = "$PROJECT" ] && [ -n "$active_project" ]; then
      echo "STATUS: running"
    else
      echo "STATUS: no_session"
    fi
    exit 0
    ;;

  "tail")
    PROJECT="$2"
    LINES="${3:-50}"
    cat "$LONG_OUTPUT_FILE" | tail -n "$LINES"
    exit 0
    ;;

  "status")
    if [ -n "$active_project" ]; then
      echo "Active sessions: $active_project"
    else
      echo "No active sessions"
    fi
    exit 0
    ;;

  *)
    # Relay mode: COMMAND is project name, $2 is the message
    PROJECT="$COMMAND"
    MESSAGE="$2"
    if [ "$PROJECT" = "$active_project" ] && [ -n "$active_project" ]; then
      # Return the long output (simulating Claude Code's response)
      cat "$LONG_OUTPUT_FILE"
      exit 0
    else
      echo "ERROR: No active session for $PROJECT"
      exit 1
    fi
    ;;
esac
MOCK_SCRIPT

chmod +x "$SCRIPTS_DIR/cc.sh"

# -------------------------------------------------------
# Create a fake 'claude' binary so the skill requirements are met
# -------------------------------------------------------
cat > /usr/local/bin/claude << 'CLAUDE_STUB'
#!/bin/bash
echo "Claude Code CLI stub v1.0"
exit 0
CLAUDE_STUB
chmod +x /usr/local/bin/claude

# Verify tmux is available
which tmux || echo "WARNING: tmux not found"

# Verify cc.sh is executable
"$SCRIPTS_DIR/cc.sh" projects || true  # Should exit 100

echo "Setup complete. Mock cc.sh is ready."
echo "State file: $STATE_FILE"