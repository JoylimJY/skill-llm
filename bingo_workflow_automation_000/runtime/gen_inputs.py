import os
import random
import json
from pathlib import Path

random.seed(42)

import sys
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

# Create deeply nested distractor directory structure
dirs = [
    "event_management/schedules/2024",
    "event_management/schedules/2023",
    "event_management/guests/vip",
    "event_management/guests/regular",
    "event_management/venues/downtown",
    "event_management/venues/suburban",
    "reports/monthly/january",
    "reports/monthly/february",
    "reports/quarterly",
    "assets/templates/cards",
    "assets/templates/banners",
    "logs/system",
    "logs/errors",
    "config/backup",
    "scripts",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = [
    ("event_management/schedules/2024/game_night_schedule.txt",
     "Monday: Bingo\nWednesday: Poker\nFriday: Trivia\n"),
    ("event_management/schedules/2023/archive_schedule.csv",
     "date,event,attendance\n2023-01-10,Bingo,45\n2023-02-14,Poker,30\n"),
    ("event_management/guests/vip/vip_list.txt",
     "Alice Johnson\nBob Martinez\nCarol White\n"),
    ("event_management/guests/regular/guest_count.json",
     json.dumps({"total": 120, "avg_per_event": 40})),
    ("event_management/venues/downtown/capacity.txt",
     "Main Hall: 200\nAnnex: 50\n"),
    ("event_management/venues/suburban/details.txt",
     "Name: Suburban Community Center\nAddress: 456 Oak Ave\nCapacity: 150\n"),
    ("reports/monthly/january/summary.txt",
     "January was a great month for events.\nTotal revenue: $3200\n"),
    ("reports/monthly/february/summary.txt",
     "February highlights: Valentine's Bingo special event.\n"),
    ("reports/quarterly/q1_2024.csv",
     "event,count,revenue\nbingo,8,1200\npoker,4,800\n"),
    ("assets/templates/cards/blank_card.txt",
     "B  I  N  G  O\n--  --  --  --  --\n"),
    ("assets/templates/banners/welcome_banner.txt",
     "WELCOME TO GAME NIGHT!\nHave fun and good luck!\n"),
    ("logs/system/system_2024_01.log",
     "[INFO] System started\n[INFO] Bingo module loaded\n[ERROR] Card printer offline\n"),
    ("logs/errors/error_dump.txt",
     "Error 404: Card template not found\nError 500: DB connection timeout\n"),
    ("config/backup/settings_backup.json",
     json.dumps({"game_type": "bingo", "max_players": 50, "auto_call": False})),
    ("event_management/schedules/2024/upcoming_events.json",
     json.dumps({"events": [
         {"name": "Bingo Night", "date": "2024-03-15", "expected_players": 40},
         {"name": "Trivia", "date": "2024-03-22", "expected_players": 35}
     ]})),
]

for rel_path, content in distractors:
    fpath = workspace / rel_path
    fpath.write_text(content)

# Create the scripts directory and a stub script that will be overwritten by setup
script_dir = workspace / "scripts"
script_dir.mkdir(exist_ok=True)

# Write the actual bingo game script
bingo_script = r'''#!/usr/bin/env bash
set -euo pipefail

BINGO_DIR="$HOME/.local/share/bingo"
mkdir -p "$BINGO_DIR"

GAME_FILE="$BINGO_DIR/current_game.json"
HISTORY_FILE="$BINGO_DIR/history.json"
STATS_FILE="$BINGO_DIR/stats.json"
CARD_FILE="$BINGO_DIR/current_card.json"

_random_number() {
    echo $(( (RANDOM % 75) + 1 ))
}

_init_history() {
    if [ ! -f "$HISTORY_FILE" ]; then
        echo "[]" > "$HISTORY_FILE"
    fi
}

_init_stats() {
    if [ ! -f "$STATS_FILE" ]; then
        echo '{"games_played":0,"total_calls":0,"wins":0}' > "$STATS_FILE"
    fi
}

cmd_new_game() {
    _init_history
    _init_stats
    GAME_ID=$(date +%s)
    echo "{\"game_id\": $GAME_ID, \"called\": [], \"status\": \"active\"}" > "$GAME_FILE"
    echo "New game started. Game ID: $GAME_ID"
}

cmd_card() {
    if [ ! -f "$GAME_FILE" ]; then
        echo "Error: No active game. Run new-game first." >&2
        exit 1
    fi
    STATUS=$(python3 -c "import json,sys; d=json.load(open('$GAME_FILE')); print(d.get('status',''))")
    if [ "$STATUS" != "active" ]; then
        echo "Error: No active game." >&2
        exit 1
    fi

    # Generate a bingo card: 5x5 grid
    # B: 1-15, I: 16-30, N: 31-45, G: 46-60, O: 61-75
    python3 - <<'PYEOF'
import json, random, os
random.seed(int(__import__('time').time()) % 10000)
card = {}
ranges = {'B': (1,15), 'I': (16,30), 'N': (31,45), 'G': (46,60), 'O': (61,75)}
for col, (lo, hi) in ranges.items():
    nums = random.sample(range(lo, hi+1), 5)
    card[col] = nums
# Free space in center
card['N'][2] = 0
bingo_dir = os.path.expanduser("~/.local/share/bingo")
card_file = os.path.join(bingo_dir, "current_card.json")
with open(card_file, 'w') as f:
    json.dump(card, f)
print("Your Bingo Card:")
print("B    I    N    G    O")
for row in range(5):
    vals = []
    for col in ['B','I','N','G','O']:
        v = card[col][row]
        vals.append("FREE" if v == 0 else str(v).rjust(4))
    print("  ".join(vals))
PYEOF
}

cmd_call() {
    if [ ! -f "$GAME_FILE" ]; then
        echo "Error: No active game." >&2
        exit 1
    fi
    STATUS=$(python3 -c "import json,sys; d=json.load(open('$GAME_FILE')); print(d.get('status',''))")
    if [ "$STATUS" != "active" ]; then
        echo "Error: No active game." >&2
        exit 1
    fi

    python3 - <<'PYEOF'
import json, random, os
bingo_dir = os.path.expanduser("~/.local/share/bingo")
game_file = os.path.join(bingo_dir, "current_game.json")
with open(game_file) as f:
    game = json.load(f)
called = game.get('called', [])
available = [n for n in range(1, 76) if n not in called]
if not available:
    print("All numbers have been called!")
else:
    n = random.choice(available)
    called.append(n)
    game['called'] = called
    # Map number to letter
    if 1 <= n <= 15: letter = 'B'
    elif 16 <= n <= 30: letter = 'I'
    elif 31 <= n <= 45: letter = 'N'
    elif 46 <= n <= 60: letter = 'G'
    else: letter = 'O'
    with open(game_file, 'w') as f:
        json.dump(game, f)
    print(f"Called: {letter}{n} (Total called: {len(called)})")
PYEOF
}

cmd_history() {
    _init_history
    if [ ! -f "$HISTORY_FILE" ]; then
        echo "No game history."
        return
    fi
    python3 -c "
import json
with open('$HISTORY_FILE') as f:
    h = json.load(f)
if not h:
    print('No completed games in history.')
else:
    for g in h:
        print(f\"Game {g['game_id']}: {g['calls_to_win']} calls, status={g['status']}\")
"
}

cmd_check() {
    NUMBERS="$1"
    if [ ! -f "$GAME_FILE" ] || [ ! -f "$CARD_FILE" ]; then
        echo "Error: No active game or card." >&2
        exit 1
    fi

    python3 - "$NUMBERS" <<'PYEOF'
import json, os, sys

numbers_arg = sys.argv[1]
# Parse comma-separated numbers
try:
    player_numbers = [int(x.strip()) for x in numbers_arg.split(',') if x.strip()]
except ValueError:
    print("Error: Invalid number format. Use comma-separated integers.")
    sys.exit(1)

bingo_dir = os.path.expanduser("~/.local/share/bingo")
game_file = os.path.join(bingo_dir, "current_game.json")
card_file = os.path.join(bingo_dir, "current_card.json")
history_file = os.path.join(bingo_dir, "history.json")
stats_file = os.path.join(bingo_dir, "stats.json")

with open(game_file) as f:
    game = json.load(f)
with open(card_file) as f:
    card = json.load(f)

called = set(game.get('called', []))

# Build card as flat list (0 = free space)
card_numbers = set()
for col in ['B','I','N','G','O']:
    for v in card[col]:
        if v != 0:
            card_numbers.add(v)

# Check which player numbers are valid (on card AND called)
valid_marked = set()
for n in player_numbers:
    if n in card_numbers and n in called:
        valid_marked.add(n)
# Free space always marked
marked = valid_marked

# Check for bingo: rows, columns, diagonals
cols = ['B','I','N','G','O']
bingo = False

# Check columns
for col in cols:
    col_nums = card[col]
    if all((v == 0 or v in marked) for v in col_nums):
        bingo = True
        break

# Check rows
if not bingo:
    for row in range(5):
        row_nums = [card[col][row] for col in cols]
        if all((v == 0 or v in marked) for v in row_nums):
            bingo = True
            break

# Check diagonals
if not bingo:
    diag1 = [card[cols[i]][i] for i in range(5)]
    if all((v == 0 or v in marked) for v in diag1):
        bingo = True

if not bingo:
    diag2 = [card[cols[4-i]][i] for i in range(5)]
    if all((v == 0 or v in marked) for v in diag2):
        bingo = True

calls_made = len(game.get('called', []))

if bingo:
    print(f"BINGO! You won after {calls_made} calls!")
    # Update game status
    game['status'] = 'completed'
    with open(game_file, 'w') as f:
        json.dump(game, f)
    # Add to history
    try:
        with open(history_file) as f:
            history = json.load(f)
    except:
        history = []
    history.append({"game_id": game.get("game_id"), "calls_to_win": calls_made, "status": "completed"})
    with open(history_file, 'w') as f:
        json.dump(history, f)
    # Update stats
    try:
        with open(stats_file) as f:
            stats = json.load(f)
    except:
        stats = {"games_played": 0, "total_calls": 0, "wins": 0}
    stats['games_played'] = stats.get('games_played', 0) + 1
    stats['total_calls'] = stats.get('total_calls', 0) + calls_made
    stats['wins'] = stats.get('wins', 0) + 1
    with open(stats_file, 'w') as f:
        json.dump(stats, f)
else:
    print(f"No bingo yet. {calls_made} numbers called so far.")
    print(f"Marked numbers on card: {sorted(marked)}")
PYEOF
}

cmd_stats() {
    _init_stats
    python3 -c "
import json
with open('$STATS_FILE') as f:
    s = json.load(f)
print('=== Bingo Stats ===')
print(f\"Games played: {s.get('games_played',0)}\")
print(f\"Total calls across all games: {s.get('total_calls',0)}\")
print(f\"Wins: {s.get('wins',0)}\")
gp = s.get('games_played', 0)
tc = s.get('total_calls', 0)
avg = tc/gp if gp > 0 else 0
print(f\"Average calls per game: {avg:.1f}\")
"
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
    card) cmd_card ;;
    call) cmd_call ;;
    new-game) cmd_new_game ;;
    history) cmd_history ;;
    check) cmd_check "${1:-}" ;;
    stats) cmd_stats ;;
    *) echo "Usage: $0 {card|call|new-game|history|check|stats}" >&2; exit 1 ;;
esac
'''

(workspace / "scripts" / "script.sh").write_text(bingo_script)

# Task specification file
task_spec = {
    "task": "run_bingo_session",
    "description": "Automate a complete bingo game session",
    "required_output": "game_session_report.json",
    "session_config": {
        "min_calls_before_check": 10,
        "note": "Run a full game session from start to finish"
    }
}
(workspace / "task_spec.json").write_text(json.dumps(task_spec, indent=2))

print(f"Workspace generated at: {workspace}")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")