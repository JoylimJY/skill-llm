import os
import stat
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── 1. Create a realistic, deeply nested project directory structure ──────────
dirs = [
    "project_notes",                          # This is the intended NOTE_TAKER_DIR
    "src/auth",
    "src/payments",
    "src/api/v1",
    "src/api/v2",
    "tests/unit",
    "tests/integration",
    "docs/architecture",
    "docs/runbooks",
    "infra/terraform",
    "infra/k8s/manifests",
    "scripts/deploy",
    "scripts/migration",
    ".github/workflows",
    "frontend/components",
    "frontend/pages",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── 2. Distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "src/auth/auth.py": "# OAuth2 implementation\ndef verify_token(token): pass\n",
    "src/payments/stripe_client.py": "# Stripe integration\nAPI_KEY = 'sk_test_...'\n",
    "src/api/v1/routes.py": "from flask import Blueprint\nv1 = Blueprint('v1', __name__)\n",
    "src/api/v2/routes.py": "from flask import Blueprint\nv2 = Blueprint('v2', __name__)\n",
    "tests/unit/test_auth.py": "def test_verify_token(): assert True\n",
    "tests/integration/test_payments.py": "def test_stripe_webhook(): pass\n",
    "docs/architecture/overview.md": "# Architecture\nMicroservices pattern with event sourcing.\n",
    "docs/runbooks/deploy.md": "# Deploy Runbook\n1. Run tests\n2. Push to registry\n3. Apply k8s manifests\n",
    "infra/terraform/main.tf": 'provider "aws" { region = "us-east-1" }\n',
    "infra/k8s/manifests/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\n",
    "scripts/deploy/deploy.sh": "#!/bin/bash\nkubectl apply -f infra/k8s/manifests/\n",
    "scripts/migration/migrate.py": "# DB migration runner\nimport subprocess\n",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
    "frontend/components/Button.tsx": "export const Button = () => <button>Click</button>;\n",
    "frontend/pages/index.tsx": "export default function Home() { return <div>Home</div>; }\n",
    "sprint_backlog.csv": "id,title,status\n1,Auth refactor,TODO\n2,Payment retry logic,IN_PROGRESS\n3,API rate limiting,TODO\n",
    "retrospective_template.md": "# Sprint Retro\n## What went well\n## What didn't\n## Action items\n",
    "config.json": '{"env": "staging", "version": "1.4.2", "debug": false}\n',
    "Makefile": "test:\n\tpytest tests/\ndeploy:\n\tbash scripts/deploy/deploy.sh\n",
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── 3. Install the note-taker CLI as a pure-bash script ───────────────────────
# The script faithfully implements the SKILL.md behavior
note_taker_script = textwrap.dedent(r"""
    #!/usr/bin/env bash
    set -euo pipefail

    # Resolve data directory
    if [[ -n "${NOTE_TAKER_DIR:-}" ]]; then
        DATA_DIR="${NOTE_TAKER_DIR}"
    elif [[ -n "${XDG_DATA_HOME:-}" ]]; then
        DATA_DIR="${XDG_DATA_HOME}/note-taker"
    else
        DATA_DIR="${HOME}/.local/share/note-taker"
    fi

    DATA_FILE="${DATA_DIR}/data.log"
    HISTORY_FILE="${DATA_DIR}/history.log"

    mkdir -p "${DATA_DIR}"
    touch "${DATA_FILE}" "${HISTORY_FILE}"

    log_history() {
        echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "${HISTORY_FILE}"
    }

    CMD="${1:-help}"
    shift || true

    case "${CMD}" in
        add)
            ITEM="$*"
            if [[ -z "${ITEM}" ]]; then
                echo "Usage: note-taker add <text>" >&2; exit 1
            fi
            ENTRY="$(date '+%Y-%m-%d') ${ITEM}"
            echo "${ENTRY}" >> "${DATA_FILE}"
            log_history "add: ${ITEM}"
            echo "Added: ${ITEM}"
            ;;

        list)
            if [[ ! -s "${DATA_FILE}" ]]; then
                echo "(empty)"
            else
                cat "${DATA_FILE}"
            fi
            ;;

        done)
            ITEM="$*"
            if grep -qF "${ITEM}" "${DATA_FILE}" 2>/dev/null; then
                # Mark line with [DONE]
                sed -i "s|${ITEM}|${ITEM} [DONE]|g" "${DATA_FILE}"
                log_history "done: ${ITEM}"
                echo "Marked done: ${ITEM}"
            else
                echo "Item not found: ${ITEM}" >&2; exit 1
            fi
            ;;

        priority)
            ITEM="$1"; shift || true
            LEVEL="${1:-medium}"
            if grep -qF "${ITEM}" "${DATA_FILE}" 2>/dev/null; then
                sed -i "s|${ITEM}|${ITEM} [priority:${LEVEL}]|g" "${DATA_FILE}"
                log_history "priority: ${ITEM} -> ${LEVEL}"
                echo "Priority set: ${ITEM} -> ${LEVEL}"
            else
                echo "Item not found: ${ITEM}" >&2; exit 1
            fi
            ;;

        clear)
            if [[ ! -s "${DATA_FILE}" ]]; then
                echo "Nothing to clear."
            else
                BEFORE=$(wc -l < "${DATA_FILE}")
                grep -v '\[DONE\]' "${DATA_FILE}" > "${DATA_FILE}.tmp" || true
                mv "${DATA_FILE}.tmp" "${DATA_FILE}"
                AFTER=$(wc -l < "${DATA_FILE}")
                REMOVED=$(( BEFORE - AFTER ))
                log_history "clear: removed ${REMOVED} completed items"
                echo "Cleared ${REMOVED} completed item(s)."
            fi
            ;;

        today)
            TODAY="$(date '+%Y-%m-%d')"
            RESULTS=$(grep "^${TODAY}" "${DATA_FILE}" 2>/dev/null || true)
            if [[ -z "${RESULTS}" ]]; then
                echo "No items for today."
            else
                echo "${RESULTS}"
            fi
            ;;

        week)
            echo "=== Weekly Overview ==="
            cat "${DATA_FILE}" 2>/dev/null || echo "(empty)"
            ;;

        remind)
            ITEM="$1"; shift || true
            TIME="${*:-tomorrow}"
            log_history "remind: ${ITEM} at ${TIME}"
            echo "Reminder set: ${ITEM} at ${TIME}"
            ;;

        stats)
            COUNT=$(wc -l < "${DATA_FILE}" 2>/dev/null || echo 0)
            echo "Total items: ${COUNT}"
            ;;

        export)
            cat "${DATA_FILE}"
            ;;

        version)
            echo "note-taker v2.0.0"
            ;;

        help|*)
            echo "note-taker v2.0.0 — Task & Note Manager"
            echo ""
            echo "Commands:"
            echo "  add <text>              Add a new item"
            echo "  list                    List all items"
            echo "  done <item>             Mark item as completed"
            echo "  priority <item> <level> Set priority (low/medium/high)"
            echo "  clear                   Remove completed items"
            echo "  today                   Show today's items"
            echo "  week                    Show weekly overview"
            echo "  remind <item> <time>    Set a reminder"
            echo "  stats                   Show item count"
            echo "  export                  Dump all data to stdout"
            echo "  version                 Print version"
            echo ""
            echo "Config:"
            echo "  NOTE_TAKER_DIR          Override data directory"
            echo "  XDG_DATA_HOME           XDG base directory"
            ;;
    esac
""")

script_path = WORKSPACE / "scripts" / "note-taker"
script_path.write_text(note_taker_script)
script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── 4. Create the task specification file the agent must read ──────────────────
task_spec = textwrap.dedent("""
    SPRINT 14 TASK TRACKER SETUP
    =============================

    We need to initialise the project's task tracker for Sprint 14.
    All tracker data must be stored inside the `project_notes/` folder
    (located at the root of this workspace), not in any system-wide location.

    Tasks to register (in this order):
      1. "Refactor authentication middleware"
      2. "Write integration tests for payment service"
      3. "Fix memory leak in worker process"
      4. "Update API documentation for v2 endpoints"
      5. "Deploy staging environment for QA team"

    Urgency levels to apply AFTER all tasks are added:
      - "Refactor authentication middleware"  → high
      - "Write integration tests for payment service" → low
      - "Fix memory leak in worker process"   → high
      - "Deploy staging environment for QA team" → medium

    (Note: "Update API documentation for v2 endpoints" does NOT get a priority assigned.)

    Completed work (mark these as done AFTER priorities are set):
      - "Fix memory leak in worker process"
      - "Deploy staging environment for QA team"

    After marking those done, remove all completed tasks from the active list.

    Finally, export the remaining active task list to a file named
    `sprint14_export.txt` inside the `project_notes/` folder.
""")

(WORKSPACE / "sprint14_setup.txt").write_text(task_spec)

print("Workspace generated successfully.")
print(f"Workspace root: {WORKSPACE}")
print(f"note-taker script: {script_path}")