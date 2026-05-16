#!/usr/bin/env bash
set -e

echo "=== Runtime initialization ==="

# Ensure openclaw skill scripts are accessible
SKILL_DIR="$(npm root -g)/openclaw/skills/multi-step-workflow"

if [ ! -d "$SKILL_DIR" ]; then
    echo "WARNING: openclaw skill directory not found at $SKILL_DIR"
    echo "Attempting manual scaffold..."
    mkdir -p "$SKILL_DIR/scripts"

    # Scaffold state-machine.js
    cat > "$SKILL_DIR/scripts/state-machine.js" << 'STATEJS'
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const os = require('os');

const DB_FILE = path.join(os.homedir(), '.openclaw_state_machine.json');

function loadDB() {
    if (!fs.existsSync(DB_FILE)) return {};
    try { return JSON.parse(fs.readFileSync(DB_FILE, 'utf8')); } catch { return {}; }
}
function saveDB(db) { fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2)); }

const VALID_STATES = ['IDLE','PLANNING','DELEGATING','EXECUTING','WAITING_SUBAGENT','MEMORYING','BLOCKED','DONE','FAILED'];
const VALID_TRANSITIONS = {
    'IDLE': ['PLANNING'],
    'PLANNING': ['DELEGATING', 'FAILED'],
    'DELEGATING': ['EXECUTING', 'WAITING_SUBAGENT', 'BLOCKED', 'FAILED'],
    'WAITING_SUBAGENT': ['EXECUTING', 'BLOCKED'],
    'EXECUTING': ['MEMORYING', 'BLOCKED', 'FAILED', 'DONE'],
    'BLOCKED': ['EXECUTING', 'DONE'],
    'MEMORYING': ['DONE', 'FAILED'],
    'DONE': [],
    'FAILED': ['PLANNING'],
};

const [,, cmd, ...args] = process.argv;

const db = loadDB();

if (cmd === 'init') {
    const [task_id, task_name] = args;
    if (!task_id || !task_name) { console.error('Usage: init <task_id> <task_name>'); process.exit(1); }
    db[task_id] = { task_id, task_name, state: 'IDLE', history: [], created: new Date().toISOString() };
    saveDB(db);
    console.log(JSON.stringify({ ok: true, task_id, state: 'IDLE' }));
} else if (cmd === 'get') {
    const [task_id] = args;
    if (!db[task_id]) { console.error('Task not found: ' + task_id); process.exit(1); }
    console.log(JSON.stringify(db[task_id]));
} else if (cmd === 'transition') {
    const [task_id, from_state, to_state] = args;
    if (!db[task_id]) { console.error('Task not found: ' + task_id); process.exit(1); }
    if (db[task_id].state !== from_state) {
        console.error(`State mismatch: current=${db[task_id].state}, expected from=${from_state}`);
        process.exit(1);
    }
    const allowed = VALID_TRANSITIONS[from_state] || [];
    if (!allowed.includes(to_state)) {
        console.error(`Invalid transition: ${from_state} → ${to_state}. Allowed: ${allowed.join(', ')}`);
        process.exit(1);
    }
    db[task_id].history.push({ from: from_state, to: to_state, at: new Date().toISOString() });
    db[task_id].state = to_state;
    saveDB(db);
    console.log(JSON.stringify({ ok: true, task_id, from: from_state, to: to_state }));
} else if (cmd === 'list') {
    console.log(JSON.stringify(Object.values(db)));
} else if (cmd === 'delete') {
    const [task_id] = args;
    delete db[task_id];
    saveDB(db);
    console.log(JSON.stringify({ ok: true, deleted: task_id }));
} else {
    console.error('Unknown command: ' + cmd);
    process.exit(1);
}
STATEJS

    # Scaffold task-tracker.py
    cat > "$SKILL_DIR/scripts/task-tracker.py" << 'TRACKERPY'
#!/usr/bin/env python3
import sys, json, os
from pathlib import Path

DB_FILE = Path.home() / '.openclaw_task_tracker.json'

def load():
    if DB_FILE.exists():
        try: return json.loads(DB_FILE.read_text())
        except: return {}
    return {}

def save(db):
    DB_FILE.write_text(json.dumps(db, indent=2))

def main():
    db = load()
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''

    if cmd == 'new':
        task = sys.argv[2]
        steps_raw = sys.argv[3]
        steps = [s.strip() for s in steps_raw.split('|') if s.strip()]
        db[task] = {
            'task': task,
            'steps': [{'idx': i+1, 'name': s, 'done': False} for i, s in enumerate(steps)],
            'created': __import__('datetime').datetime.now().isoformat()
        }
        save(db)
        print(json.dumps({'ok': True, 'task': task, 'steps': len(steps)}))

    elif cmd == 'done':
        task = sys.argv[2]
        idx = int(sys.argv[3])
        if task not in db:
            print(f'Task not found: {task}', file=sys.stderr); sys.exit(1)
        found = False
        for s in db[task]['steps']:
            if s['idx'] == idx:
                s['done'] = True
                s['completed_at'] = __import__('datetime').datetime.now().isoformat()
                found = True
                break
        if not found:
            print(f'Step {idx} not found in task {task}', file=sys.stderr); sys.exit(1)
        save(db)
        print(json.dumps({'ok': True, 'task': task, 'step': idx, 'done': True}))

    elif cmd == 'list':
        print(json.dumps(list(db.values()), indent=2))

    else:
        print(f'Unknown command: {cmd}', file=sys.stderr); sys.exit(1)

main()
TRACKERPY

    # Scaffold context-snapshot.js
    cat > "$SKILL_DIR/scripts/context-snapshot.js" << 'SNAPSHOTJS'
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const os = require('os');

const SNAP_FILE = path.join(os.homedir(), '.openclaw_context_snapshot.json');
const [,, cmd, ...args] = process.argv;

if (cmd === 'save') {
    const [task, findings, pending] = args;
    if (!task || !findings || !pending) {
        console.error('Usage: save "<task>" "<findings>" "<pending>"');
        process.exit(1);
    }
    const snap = { task, findings, pending, saved_at: new Date().toISOString() };
    fs.writeFileSync(SNAP_FILE, JSON.stringify(snap, null, 2));
    console.log(JSON.stringify({ ok: true, saved: SNAP_FILE }));
} else if (cmd === 'load') {
    if (!fs.existsSync(SNAP_FILE)) { console.error('No snapshot found.'); process.exit(1); }
    console.log(fs.readFileSync(SNAP_FILE, 'utf8'));
} else if (cmd === 'clear') {
    if (fs.existsSync(SNAP_FILE)) fs.unlinkSync(SNAP_FILE);
    console.log(JSON.stringify({ ok: true, cleared: true }));
} else {
    console.error('Unknown command: ' + cmd);
    process.exit(1);
}
SNAPSHOTJS

    # Scaffold delegate.js
    cat > "$SKILL_DIR/scripts/delegate.js" << 'DELEGATEJS'
#!/usr/bin/env node
const pct = parseFloat(process.argv[2]);
if (isNaN(pct)) { console.error('Usage: delegate.js <context_pct>'); process.exit(1); }
const recommendation = pct < 30 ? 'MAIN' : pct < 60 ? 'MAIN_ONLY' : pct < 85 ? 'SUBAGENT' : 'BLOCK';
console.log(JSON.stringify({
    context_pct: pct,
    recommendation,
    note: 'Model decides final action. This is informational only.',
    timestamp: new Date().toISOString()
}));
DELEGATEJS

    chmod +x "$SKILL_DIR/scripts/state-machine.js"
    chmod +x "$SKILL_DIR/scripts/context-snapshot.js"
    chmod +x "$SKILL_DIR/scripts/delegate.js"
    echo "Scaffolded skill scripts at $SKILL_DIR"
else
    echo "openclaw skill directory found at $SKILL_DIR"
fi

# Make python script executable
chmod +x "$SKILL_DIR/scripts/task-tracker.py" 2>/dev/null || true

# Export SKILL_DIR for the agent's convenience (not a hint, just environment)
echo "export SKILL_DIR=\"$SKILL_DIR\"" >> /etc/environment
echo "SKILL_DIR=$SKILL_DIR" >> /etc/profile.d/openclaw.sh
chmod +x /etc/profile.d/openclaw.sh

echo "=== Setup complete ==="
echo "SKILL_DIR: $SKILL_DIR"
node "$SKILL_DIR/scripts/state-machine.js" list 2>/dev/null || echo "(state-machine clean start)"