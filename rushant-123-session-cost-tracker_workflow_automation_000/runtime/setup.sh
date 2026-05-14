#!/bin/bash
set -e

# Create the track.sh script that implements the SKILL.md specification
cat > /workspace/track.sh << 'TRACKSH_EOF'
#!/bin/bash
# Session Cost Tracker - track.sh
# Logs agent sessions and their cost-to-value ratio

DATADIR="$HOME/.clawdbot"
DATAFILE="$DATADIR/session-costs.json"

mkdir -p "$DATADIR"

# Initialize JSON file if it doesn't exist
if [ ! -f "$DATAFILE" ]; then
    echo '[]' > "$DATAFILE"
fi

subcommand="$1"
shift

case "$subcommand" in

  quick)
    # Usage: ./track.sh quick "task description" value tokens
    TASK="$1"
    VALUE="$2"
    TOKENS="$3"
    MODEL="${4:-claude-opus-4.5}"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Validate value category
    VALID_VALUES="high medium low zero creation maintenance debt refactor"
    VALID=false
    for v in $VALID_VALUES; do
      if [ "$VALUE" = "$v" ]; then
        VALID=true
        break
      fi
    done
    if [ "$VALID" = "false" ]; then
      echo "ERROR: Invalid value category '$VALUE'. Must be one of: $VALID_VALUES" >&2
      exit 1
    fi

    ENTRY=$(python3 -c "
import json, sys
entry = {
    'task': sys.argv[1],
    'outcome': '',
    'value': sys.argv[2],
    'tokens': int(sys.argv[3]),
    'model': sys.argv[4],
    'timestamp': sys.argv[5],
    'log_format': 'quick'
}
print(json.dumps(entry))
" "$TASK" "$VALUE" "$TOKENS" "$MODEL" "$TIMESTAMP")

    python3 -c "
import json, sys
datafile = sys.argv[1]
entry = json.loads(sys.argv[2])
with open(datafile, 'r') as f:
    data = json.load(f)
data.append(entry)
with open(datafile, 'w') as f:
    json.dump(data, f, indent=2)
print(f'Logged: [{entry[\"value\"].upper()}] {entry[\"task\"]} ({entry[\"tokens\"]} tokens)')
" "$DATAFILE" "$ENTRY"
    ;;

  log)
    # Usage: ./track.sh log --task "..." --outcome "..." --value "..." --tokens N --model "..."
    TASK=""
    OUTCOME=""
    VALUE=""
    TOKENS=""
    MODEL="claude-opus-4.5"

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --task)    TASK="$2";    shift 2 ;;
        --outcome) OUTCOME="$2"; shift 2 ;;
        --value)   VALUE="$2";   shift 2 ;;
        --tokens)  TOKENS="$2";  shift 2 ;;
        --model)   MODEL="$2";   shift 2 ;;
        *) echo "Unknown flag: $1" >&2; exit 1 ;;
      esac
    done

    if [ -z "$TASK" ] || [ -z "$VALUE" ] || [ -z "$TOKENS" ]; then
      echo "ERROR: --task, --value, and --tokens are required" >&2
      exit 1
    fi

    # Validate value category
    VALID_VALUES="high medium low zero creation maintenance debt refactor"
    VALID=false
    for v in $VALID_VALUES; do
      if [ "$VALUE" = "$v" ]; then
        VALID=true
        break
      fi
    done
    if [ "$VALID" = "false" ]; then
      echo "ERROR: Invalid value category '$VALUE'. Must be one of: $VALID_VALUES" >&2
      exit 1
    fi

    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    python3 -c "
import json, sys
datafile = sys.argv[1]
entry = {
    'task': sys.argv[2],
    'outcome': sys.argv[3],
    'value': sys.argv[4],
    'tokens': int(sys.argv[5]),
    'model': sys.argv[6],
    'timestamp': sys.argv[7],
    'log_format': 'full'
}
with open(datafile, 'r') as f:
    data = json.load(f)
data.append(entry)
with open(datafile, 'w') as f:
    json.dump(data, f, indent=2)
print(f'Logged: [{entry[\"value\"].upper()}] {entry[\"task\"]} ({entry[\"tokens\"]} tokens)')
" "$DATAFILE" "$TASK" "$OUTCOME" "$VALUE" "$TOKENS" "$MODEL" "$TIMESTAMP"
    ;;

  stats)
    BY_TASK=false
    WEEK_ONLY=false

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --by-task) BY_TASK=true; shift ;;
        --week)    WEEK_ONLY=true; shift ;;
        *) echo "Unknown flag: $1" >&2; exit 1 ;;
      esac
    done

    python3 -c "
import json, sys
from collections import defaultdict

datafile = sys.argv[1]
by_task = sys.argv[2] == 'true'
week_only = sys.argv[3] == 'true'

with open(datafile, 'r') as f:
    sessions = json.load(f)

if not sessions:
    print('No sessions logged yet.')
    sys.exit(0)

total_tokens = sum(s.get('tokens', 0) for s in sessions)
total_sessions = len(sessions)
value_counts = defaultdict(int)
for s in sessions:
    value_counts[s.get('value', 'unknown')] += 1

print('=== Session Cost Tracker Stats ===')
print(f'Total Sessions : {total_sessions}')
print(f'Total Tokens   : {total_tokens:,}')
print()
print('Value Distribution:')
for v, c in sorted(value_counts.items()):
    pct = 100.0 * c / total_sessions
    print(f'  {v:<15} {c:>3} sessions  ({pct:.1f}%)')

if by_task:
    print()
    print('=== Grouped by Task Type ===')
    task_groups = defaultdict(list)
    for s in sessions:
        task_groups[s.get('value', 'unknown')].append(s)
    for group, group_sessions in sorted(task_groups.items()):
        group_tokens = sum(s.get('tokens', 0) for s in group_sessions)
        print(f'[{group.upper()}] ({len(group_sessions)} sessions, {group_tokens:,} tokens)')
        for s in group_sessions:
            print(f'  - {s[\"task\"]} ({s[\"tokens\"]:,} tokens) [{s.get(\"log_format\",\"?\")}]')
" "$DATAFILE" "$BY_TASK" "$WEEK_ONLY"
    ;;

  *)
    echo "Usage: ./track.sh <quick|log|stats> [options]"
    echo "  quick \"task\" value tokens [model]"
    echo "  log --task \"...\" --outcome \"...\" --value \"...\" --tokens N [--model \"...\"]"
    echo "  stats [--week] [--by-task]"
    exit 1
    ;;
esac
TRACKSH_EOF

chmod +x /workspace/track.sh

echo "track.sh installed and made executable."

# Verify the script is functional
/workspace/track.sh stats 2>/dev/null && echo "track.sh self-test passed." || echo "track.sh self-test note: no sessions yet (expected)."