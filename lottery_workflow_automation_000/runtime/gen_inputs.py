import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create the actual scripts/script.sh tool (the skill under test) ---
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

script_content = r"""#!/usr/bin/env bash
# lottery skill v3.0.0 - BytesAgain

STORAGE_DIR="$HOME/.local/share/lottery"
mkdir -p "$STORAGE_DIR"
HISTORY_FILE="$STORAGE_DIR/history.json"
STATS_FILE="$STORAGE_DIR/stats.json"

# Initialize files if missing
if [ ! -f "$HISTORY_FILE" ]; then
  echo "[]" > "$HISTORY_FILE"
fi
if [ ! -f "$STATS_FILE" ]; then
  echo '{"total_picks":0,"total_checks":0,"wins":0,"powerball_plays":0,"mega_plays":0}' > "$STATS_FILE"
fi

# Helper: update stats field
update_stat() {
  local field="$1"
  local file="$STATS_FILE"
  local val
  val=$(python3 -c "import json,sys; d=json.load(open('$file')); d['$field']+=1; print(json.dumps(d))")
  echo "$val" > "$file"
}

# Helper: append to history
append_history() {
  local entry="$1"
  python3 -c "
import json, sys
with open('$HISTORY_FILE') as f:
    data = json.load(f)
data.append($entry)
with open('$HISTORY_FILE', 'w') as f:
    json.dump(data, f)
"
}

CMD="$1"
shift

case "$CMD" in
  pick)
    COUNT="$1"
    MAX="$2"
    if [ -z "$COUNT" ] || [ -z "$MAX" ]; then
      echo "Usage: script.sh pick <count max>"
      exit 1
    fi
    NUMBERS=$(python3 -c "
import random, sys
count=int('$COUNT')
max_val=int('$MAX')
nums = random.sample(range(1, max_val+1), count)
nums.sort()
print(' '.join(map(str, nums)))
")
    echo "Pick: $NUMBERS"
    update_stat "total_picks"
    append_history "{'type':'pick','count':$COUNT,'max':$MAX,'numbers':'$NUMBERS'}"
    ;;

  powerball)
    MAIN=$(python3 -c "
import random
nums = random.sample(range(1,70), 5)
nums.sort()
print(' '.join(map(str, nums)))
")
    PB=$(python3 -c "import random; print(random.randint(1,26))")
    echo "Powerball: $MAIN | Powerball: $PB"
    update_stat "powerball_plays"
    append_history "{'type':'powerball','main':'$MAIN','powerball':$PB}"
    ;;

  mega)
    MAIN=$(python3 -c "
import random
nums = random.sample(range(1,71), 5)
nums.sort()
print(' '.join(map(str, nums)))
")
    MB=$(python3 -c "import random; print(random.randint(1,25))")
    echo "Mega Millions: $MAIN | Mega Ball: $MB"
    update_stat "mega_plays"
    append_history "{'type':'mega','main':'$MAIN','mega_ball':$MB}"
    ;;

  check)
    NUMBERS="$1"
    WINNING="$2"
    if [ -z "$NUMBERS" ] || [ -z "$WINNING" ]; then
      echo "Usage: script.sh check <numbers winning>"
      exit 1
    fi
    RESULT=$(python3 -c "
nums = set('$NUMBERS'.split())
win  = set('$WINNING'.split())
matched = nums & win
print(f'Checked: $NUMBERS | Winning: $WINNING | Matched: {len(matched)} numbers: {\" \".join(sorted(matched, key=int)) if matched else \"none\"}')
")
    echo "$RESULT"
    MATCHED_COUNT=$(python3 -c "
nums = set('$NUMBERS'.split())
win  = set('$WINNING'.split())
print(len(nums & win))
")
    update_stat "total_checks"
    if [ "$MATCHED_COUNT" -gt 0 ]; then
      update_stat "wins"
    fi
    append_history "{'type':'check','numbers':'$NUMBERS','winning':'$WINNING','matched':$MATCHED_COUNT}"
    ;;

  history)
    echo "=== Lottery History ==="
    python3 -c "
import json
with open('$HISTORY_FILE') as f:
    data = json.load(f)
for i,entry in enumerate(data):
    print(f'{i+1}. {entry}')
if not data:
    print('No history yet.')
"
    ;;

  stats)
    echo "=== Lottery Stats ==="
    python3 -c "
import json
with open('$STATS_FILE') as f:
    d = json.load(f)
for k,v in d.items():
    print(f'{k}: {v}')
"
    ;;

  *)
    echo "Unknown command: $CMD"
    echo "Commands: pick <count max> | powerball | mega | check <numbers winning> | history | stats"
    exit 1
    ;;
esac
"""

script_path = scripts_dir / "script.sh"
script_path.write_text(script_content)

# --- Distractor files (deeply nested, irrelevant) ---
distractors = [
    ("club/members/roster_2024.csv", "id,name,tickets\n1,Alice,5\n2,Bob,3\n3,Carol,7\n"),
    ("club/members/dues_record.txt", "March dues collected: $120\nApril dues collected: $95\n"),
    ("club/events/schedule_q1.txt", "Jan 15 - Weekly draw\nFeb 12 - Jackpot special\nMar 8 - Monthly mega\n"),
    ("club/events/archive/2023_results.csv", "date,game,jackpot\n2023-12-01,powerball,50000\n2023-11-15,mega,75000\n"),
    ("finances/budget_2024.txt", "Operating budget: $5000\nPrize pool: $2000\nAdmin: $500\n"),
    ("finances/invoices/inv_001.txt", "Ticket printing: $200\nDelivery: $15\n"),
    ("finances/invoices/inv_002.txt", "Marketing materials: $350\n"),
    ("admin/config/club_settings.ini", "[general]\nclub_name=Lucky Stars Lottery Club\nfounded=2019\nmembers=42\n"),
    ("admin/config/email_list.txt", "alice@example.com\nbob@example.com\ncarol@example.com\n"),
    ("admin/logs/access_2024_03.log", "2024-03-01 09:00 alice login\n2024-03-01 09:05 bob login\n2024-03-02 10:30 carol login\n"),
    ("admin/logs/errors_2024_03.log", "2024-03-05 ERROR: db connection timeout\n2024-03-07 WARNING: slow query\n"),
    ("reports/monthly/feb_2024_summary.txt", "Total tickets sold: 120\nRevenue: $480\nTop winner: Alice\n"),
    ("reports/monthly/jan_2024_summary.txt", "Total tickets sold: 98\nRevenue: $392\nTop winner: Bob\n"),
    ("reports/archive/2023_annual.txt", "Annual tickets: 1440\nAnnual revenue: $5760\n"),
]

for rel_path, content in distractors:
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# --- Task instruction file (business context, no hints about commands) ---
task_file = workspace / "TASK.md"
task_file.write_text("""# Lottery Club Automation Task

Our lucky stars lottery club coordinator needs help with the following:

1. Generate a custom quick-pick: 6 numbers from 1-49
2. Generate one Powerball ticket
3. Generate one Mega Millions ticket
4. Check the custom pick numbers against the winning numbers: 7 14 21 28 35 42
5. After all operations, display the session history
6. After all operations, display the session statistics
7. Save the final stats output to a file named `lottery_report.txt` in the workspace

Please automate this workflow using the available lottery tool in the scripts/ folder.
The final `lottery_report.txt` should contain ONLY the output of the stats command.
""")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")