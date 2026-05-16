#!/bin/bash
set -e

WORKSPACE="/workspace"
LOG_DIR="$WORKSPACE/.clawdbot/command_log"

mkdir -p "$LOG_DIR"

# ─── Mock `clawdbot` binary ────────────────────────────────────────────────────
cat > /usr/local/bin/clawdbot << 'MOCK_CLAWDBOT'
#!/bin/bash
LOG_DIR="/workspace/.clawdbot/command_log"
CRON_DB="$LOG_DIR/cron_jobs.json"
mkdir -p "$LOG_DIR"

# Log the full invocation
echo "$@" >> "$LOG_DIR/clawdbot_invocations.log"

SUBCOMMAND="$1"
shift

case "$SUBCOMMAND" in
  cron)
    CRON_ACTION="$1"
    shift
    case "$CRON_ACTION" in
      add)
        # Parse all arguments and store as JSON
        NAME=""
        CRON_EXPR=""
        TZ=""
        SESSION=""
        WAKE=""
        DELIVER=false
        MESSAGE=""

        while [[ $# -gt 0 ]]; do
          case "$1" in
            --name)      NAME="$2";    shift 2 ;;
            --cron)      CRON_EXPR="$2"; shift 2 ;;
            --tz)        TZ="$2";      shift 2 ;;
            --session)   SESSION="$2"; shift 2 ;;
            --wake)      WAKE="$2";    shift 2 ;;
            --deliver)   DELIVER=true; shift 1 ;;
            --message)   MESSAGE="$2"; shift 2 ;;
            *)           shift ;;
          esac
        done

        # Write cron job record
        python3 - "$NAME" "$CRON_EXPR" "$TZ" "$SESSION" "$WAKE" "$DELIVER" "$MESSAGE" "$CRON_DB" << 'PYEOF'
import sys, json, os
name, cron_expr, tz, session, wake, deliver, message, db_path = sys.argv[1:]
jobs = []
if os.path.exists(db_path):
    with open(db_path) as f:
        try: jobs = json.load(f)
        except: jobs = []
jobs.append({
    "name": name,
    "cron": cron_expr,
    "tz": tz,
    "session": session,
    "wake": wake,
    "deliver": deliver == "True",
    "message": message
})
with open(db_path, "w") as f:
    json.dump(jobs, f, indent=2)
print(f"✓ Cron job '{name}' added successfully.")
PYEOF
        ;;
      list)
        if [ -f "$CRON_DB" ]; then
          python3 -c "
import json
with open('$CRON_DB') as f:
    jobs = json.load(f)
print('Scheduled Cron Jobs:')
for j in jobs:
    print(f\"  [{j.get('name','')}] {j.get('cron','')} ({j.get('tz','system')})\")
"
        else
          echo "No cron jobs registered."
        fi
        ;;
      remove)
        JOB_NAME="$1"
        if [ -f "$CRON_DB" ]; then
          python3 - "$JOB_NAME" "$CRON_DB" << 'PYEOF'
import sys, json
name, db_path = sys.argv[1:]
with open(db_path) as f:
    jobs = json.load(f)
jobs = [j for j in jobs if j.get("name") != name]
with open(db_path, "w") as f:
    json.dump(jobs, f, indent=2)
print(f"✓ Cron job '{name}' removed.")
PYEOF
        fi
        ;;
    esac
    ;;
  doctor)
    echo "✓ Clawdbot health check passed. All migrations applied."
    echo "clawdbot_doctor_ran=true" >> "$LOG_DIR/doctor.log"
    ;;
  --version)
    echo "clawdbot v2026.1.9"
    ;;
  update)
    echo "✓ Clawdbot updated to v2026.1.10"
    echo "clawdbot_update_ran=true" >> "$LOG_DIR/update.log"
    ;;
  *)
    echo "clawdbot: unknown command '$SUBCOMMAND'"
    exit 1
    ;;
esac
MOCK_CLAWDBOT

chmod +x /usr/local/bin/clawdbot

# ─── Mock `clawdhub` binary ───────────────────────────────────────────────────
cat > /usr/local/bin/clawdhub << 'MOCK_CLAWDHUB'
#!/bin/bash
LOG_DIR="/workspace/.clawdbot/command_log"
mkdir -p "$LOG_DIR"

echo "$@" >> "$LOG_DIR/clawdhub_invocations.log"

SUBCOMMAND="$1"
shift

case "$SUBCOMMAND" in
  update)
    DRY_RUN=false
    ALL=false
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --all)     ALL=true;     shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        *)         shift ;;
      esac
    done
    if [ "$DRY_RUN" = "true" ]; then
      echo "Dry run: checking for updates..."
      echo "  prd: 2.0.3 → 2.0.4 (available)"
    else
      echo "Updating all skills..."
      echo "  ✓ prd: 2.0.3 → 2.0.4"
      echo "  ✓ browser: 1.2.0 → 1.2.1"
      echo "  ✓ nano-banana-pro: 3.1.0 → 3.1.2"
    fi
    ;;
  list)
    echo "Installed skills:"
    echo "  prd           2.0.3"
    echo "  browser       1.2.0"
    echo "  nano-banana-pro 3.1.0"
    echo "  gemini        1.5.0"
    echo "  sag           0.9.2"
    echo "  himalaya      2.1.0"
    ;;
  *)
    echo "clawdhub: unknown command '$SUBCOMMAND'"
    exit 1
    ;;
esac
MOCK_CLAWDHUB

chmod +x /usr/local/bin/clawdhub

echo "Mock binaries installed: clawdbot, clawdhub"
echo "Command logging active at: $LOG_DIR"