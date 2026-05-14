import os
import json
import random

random.seed(42)

# Create deep directory structure with distractor files
dirs = [
    "scripts",
    "projects/webapp/src",
    "projects/webapp/tests",
    "projects/api-service/src",
    "projects/api-service/config",
    "projects/ml-pipeline/notebooks",
    "projects/ml-pipeline/data",
    "config/sessions",
    "config/profiles",
    "logs/archive",
    "logs/current",
    "docs/internal",
    "tools/legacy",
    "tools/experimental",
]

for d in dirs:
    os.makedirs(f"/workspace/{d}", exist_ok=True)

# Distractor files
distractors = {
    "projects/webapp/src/index.js": "const app = require('express')();\napp.listen(3000);",
    "projects/webapp/tests/test_app.js": "describe('app', () => { it('runs', () => {}); });",
    "projects/api-service/src/main.py": "from fastapi import FastAPI\napp = FastAPI()",
    "projects/api-service/config/settings.yaml": "host: localhost\nport: 8080\ndebug: false",
    "projects/ml-pipeline/notebooks/explore.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4}',
    "projects/ml-pipeline/data/.gitkeep": "",
    "config/sessions/.gitkeep": "",
    "config/profiles/default.json": '{"theme": "dark", "timeout": 300}',
    "logs/archive/2024-01-01.log": "INFO session started\nINFO session ended",
    "logs/current/active.log": "DEBUG relay active\nDEBUG forwarding messages",
    "docs/internal/architecture.md": "# Architecture\n\nThis system uses a relay pattern.",
    "tools/legacy/old_relay.sh": "#!/bin/bash\necho 'deprecated'",
    "tools/experimental/proto_dispatcher.py": "# prototype - do not use\npass",
    "config/relay_config.bak": "# old config backup\nroot=/home/user/projects",
}

for path, content in distractors.items():
    with open(f"/workspace/{path}", "w") as f:
        f.write(content)

# Create the mock cc.sh script
# This script simulates real cc.sh behavior deterministically
cc_sh_content = r"""#!/bin/bash
# Mock cc.sh for testing - simulates real cc.sh behavior

COMMAND="$1"
shift

case "$COMMAND" in
  "projects")
    # First call returns SETUP_NEEDED, subsequent calls return project list
    CALL_COUNT_FILE="/tmp/cc_projects_calls"
    if [ ! -f "$CALL_COUNT_FILE" ]; then
      echo 0 > "$CALL_COUNT_FILE"
    fi
    COUNT=$(cat "$CALL_COUNT_FILE")
    if [ "$COUNT" -eq 0 ]; then
      echo "SETUP_NEEDED"
      echo 1 > "$CALL_COUNT_FILE"
      exit 100
    else
      echo "webapp ★"
      echo "api-service"
      echo "ml-pipeline"
      exit 0
    fi
    ;;

  "config")
    SUBCOMMAND="$1"
    PATH_ARG="$2"
    if [ "$SUBCOMMAND" = "root" ]; then
      echo "Project root set to: $PATH_ARG"
      echo "Found 3 projects: webapp, api-service, ml-pipeline"
      exit 0
    fi
    ;;

  "on")
    PROJECT="$1"
    echo "Session started for $PROJECT"
    echo "tmux session: cc_${PROJECT}"
    exit 0
    ;;

  "off")
    PROJECT="$1"
    echo "Session stopped for $PROJECT"
    exit 0
    ;;

  "check")
    PROJECT="$1"
    # Simulate different statuses based on project name
    case "$PROJECT" in
      "webapp")
        echo "RUNNING"
        exit 0
        ;;
      "api-service")
        echo "PROCESSING"
        exit 0
        ;;
      "ml-pipeline")
        echo "DEAD"
        exit 0
        ;;
      *)
        echo "NO_SESSION"
        exit 0
        ;;
    esac
    ;;

  "status")
    echo "Active sessions:"
    echo "  cc_webapp (running)"
    echo "  cc_api-service (processing)"
    exit 0
    ;;

  "tail")
    PROJECT="$1"
    LINES="${2:-50}"
    # Return a large output (>4000 chars) for webapp, small for others
    if [ "$PROJECT" = "webapp" ]; then
      # Generate output > 4000 chars
      echo "=== Claude Code Output for webapp ==="
      echo "Task: Refactoring authentication module"
      echo "Step 1: Analyzing existing code structure..."
      python3 -c "
lines = ['Processing file: src/auth/login.py - checking JWT validation logic',
'Processing file: src/auth/session.py - reviewing session management',
'Processing file: src/auth/middleware.py - inspecting middleware chain',
'Found potential security issue in token refresh logic at line 47',
'Recommendation: Use httpOnly cookies instead of localStorage for tokens',
'Analyzing database queries for N+1 problems in user lookup',
'Found 3 instances of unoptimized queries in auth/models.py',
'Generating optimized query using select_related and prefetch_related',
'Writing unit tests for new authentication flow',
'Test coverage improved from 67% to 89% after refactoring',
'Running security scan on modified files...',
'No critical vulnerabilities found in updated code',
'Creating migration script for session table changes',
'Documentation updated for new auth endpoints',
'Summary: 15 files modified, 3 tests added, 0 regressions detected']
for i in range(20):
    for line in lines:
        print(line)
"
      echo "=== End of Output ==="
      exit 0
    else
      echo "Recent output:"
      echo "Working on task..."
      echo "Done."
      exit 0
    fi
    ;;

  "webapp"|"api-service"|"ml-pipeline")
    # Relay mode: sending message to project
    PROJECT="$COMMAND"
    MESSAGE="$*"
    echo "Claude Code received: $MESSAGE"
    echo "Processing your request..."
    echo "Here is the response to: $MESSAGE"
    echo "Task completed successfully."
    exit 0
    ;;

  *)
    echo "Unknown command: $COMMAND"
    exit 1
    ;;
esac
"""

with open("/workspace/scripts/cc.sh", "w") as f:
    f.write(cc_sh_content)

os.chmod("/workspace/scripts/cc.sh", 0o755)

# Create the relay session input that the agent must process
# This is a realistic conversation transcript the dispatcher must handle
relay_session = [
    {
        "id": 1,
        "user_input": "/cc",
        "relay_mode": False,
        "active_project": None,
        "description": "Initial help request - no args, should call projects and show help"
    },
    {
        "id": 2,
        "user_input": "~/projects",
        "relay_mode": False,
        "active_project": None,
        "description": "User provides project root after SETUP_NEEDED was triggered"
    },
    {
        "id": 3,
        "user_input": "/cc on webapp",
        "relay_mode": False,
        "active_project": None,
        "description": "Start session for webapp project"
    },
    {
        "id": 4,
        "user_input": "Please refactor the authentication module to use JWT tokens",
        "relay_mode": True,
        "active_project": "webapp",
        "description": "User message in relay mode - must be forwarded to Claude Code"
    },
    {
        "id": 5,
        "user_input": "/cc ?",
        "relay_mode": True,
        "active_project": "webapp",
        "description": "Status check in relay mode - must NOT be forwarded, must call check"
    },
    {
        "id": 6,
        "user_input": "/cc tail webapp",
        "relay_mode": True,
        "active_project": "webapp",
        "description": "Tail in relay mode - NOT forwarded, calls tail, output >4000 chars needs summary"
    },
    {
        "id": 7,
        "user_input": "Now add unit tests for the new auth module",
        "relay_mode": True,
        "active_project": "webapp",
        "description": "Another relay message - must be forwarded"
    },
    {
        "id": 8,
        "user_input": "/cc off",
        "relay_mode": True,
        "active_project": "webapp",
        "description": "Stop session - ends relay mode"
    },
    {
        "id": 9,
        "user_input": "/cc status",
        "relay_mode": False,
        "active_project": None,
        "description": "Check active sessions after relay ended"
    },
    {
        "id": 10,
        "user_input": "/cc on api-service",
        "relay_mode": False,
        "active_project": None,
        "description": "Start new session for api-service"
    },
    {
        "id": 11,
        "user_input": "/cc ?",
        "relay_mode": True,
        "active_project": "api-service",
        "description": "Status check for api-service - should show PROCESSING status"
    },
    {
        "id": 12,
        "user_input": "/cc projects",
        "relay_mode": True,
        "active_project": "api-service",
        "description": "Projects command in relay mode - NOT forwarded, lists projects"
    }
]

with open("/workspace/relay_session.json", "w") as f:
    json.dump(relay_session, f, indent=2)

# Create a partial/incorrect reference to mislead agents relying on guessing
wrong_reference = {
    "note": "DRAFT - DO NOT USE",
    "output_limit": 5000,
    "status_endpoint": "status",
    "relay_exceptions": ["/cc off", "/cc ?"]
}
with open("/workspace/config/profiles/relay_draft.json", "w") as f:
    json.dump(wrong_reference, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in __import__('pathlib').Path('/workspace').rglob('*') if _.is_file())}")