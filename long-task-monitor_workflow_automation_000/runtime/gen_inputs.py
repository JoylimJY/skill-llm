import os
import json
import random
import string
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── distractor files to simulate a messy real-world environment ──────────────
distractors = [
    ("pipeline_config.yaml", "scheduler:\n  interval: 300\n  retries: 3\njobs:\n  - name: preprocess\n    cmd: python preprocess.py\n"),
    ("run_log_2024-01-15.txt", "2024-01-15 08:00:01 INFO Starting preprocessing\n2024-01-15 08:00:05 INFO Loaded 120000 records\n2024-01-15 09:15:44 ERROR OOM killed\n"),
    ("run_log_2024-01-16.txt", "2024-01-16 08:00:01 INFO Restarting after OOM\n2024-01-16 11:30:22 INFO Completed 45% of dataset\n"),
    ("requirements.txt", "numpy==1.24.3\npandas==2.0.1\nscikit-learn==1.3.0\ntorch==2.1.0\n"),
    ("deprecated_task_runner.sh", "#!/bin/bash\n# OLD VERSION - do not use\npython train.py --epochs 100 --lr 0.001\n"),
    ("monitor_notes.md", "## Notes\n- Old approach used cron jobs\n- Switched to session-based approach in Jan 2025\n- Watch out for zombie sessions\n"),
    ("env_template.env", "WORKER_TIMEOUT=600\nMONITOR_INTERVAL=60\nMAX_ROUNDS=10\n"),
    ("data/raw/schema.json", json.dumps({"version": "1.2", "fields": ["id", "timestamp", "value", "label"]}, indent=2)),
    ("data/raw/sample_batch.csv", "id,timestamp,value,label\n1,1700000000,0.92,1\n2,1700000001,0.11,0\n3,1700000002,0.77,1\n"),
    ("data/processed/.gitkeep", ""),
    ("scripts/preprocess.py", "import pandas as pd\ndf = pd.read_csv('../data/raw/sample_batch.csv')\nprint(df.head())\n"),
    ("scripts/train.py", "# Placeholder training script\nfor epoch in range(100):\n    loss = 1.0 / (epoch + 1)\n    print(f'Epoch {epoch}: loss={loss:.4f}')\n"),
    ("tmp/last_session.txt", "session_id: old-session-789\nstarted: 2024-12-01T10:00:00Z\nstatus: stale\n"),
]

for rel_path, content in distractors:
    full = workspace / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)

# ── The long-task.js CLI script (the skill's main tool) ──────────────────────
skill_dir = Path("/root/.openclaw/workspace/skills/long-task-monitor")
skill_dir.mkdir(parents=True, exist_ok=True)

long_task_js = r"""#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const crypto = require('crypto');

const BASE_DIR = path.join(process.env.HOME, '.openclaw', 'workspace', 'long-tasks');
fs.mkdirSync(BASE_DIR, { recursive: true });

function sanitize(input) {
  // Allow alphanumeric, spaces, hyphens, underscores, colons (for session keys), dots, slashes
  return String(input).replace(/[^a-zA-Z0-9 \-_:./]/g, '');
}

function loadTask(taskId) {
  const p = path.join(BASE_DIR, taskId, 'task.json');
  if (!fs.existsSync(p)) { console.error(`Task not found: ${taskId}`); process.exit(1); }
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function saveTask(task) {
  const dir = path.join(BASE_DIR, task.taskId);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'task.json'), JSON.stringify(task, null, 2));
}

const cmd = process.argv[2];

if (cmd === 'start') {
  const description = sanitize(process.argv[3] || 'unnamed task');
  const workerTask = sanitize(process.argv[4] || 'echo done');
  const taskId = 'task-' + crypto.randomBytes(4).toString('hex');
  const task = {
    taskId,
    description,
    workerTask,
    workerSessionKey: '',
    monitorSessionKey: '',
    createdAt: new Date().toISOString(),
    status: 'created',
    monitorRound: 0,
    workerRestartCount: 0
  };
  saveTask(task);
  console.log(JSON.stringify({ taskId, message: 'Task created', taskPath: path.join(BASE_DIR, taskId) }));

} else if (cmd === 'update') {
  const taskId = process.argv[3];
  const field = process.argv[4];
  const value = sanitize(process.argv[5] || '');
  const task = loadTask(taskId);
  if (field === 'worker') {
    if (!value.includes(':')) {
      console.error('ERROR: workerSessionKey must contain ":" character (e.g. agent:main:subagent:xxx)');
      process.exit(1);
    }
    task.workerSessionKey = value;
    task.status = 'running';
  } else if (field === 'monitor') {
    if (!value.includes(':')) {
      console.error('ERROR: monitorSessionKey must contain ":" character (e.g. agent:main:subagent:yyy)');
      process.exit(1);
    }
    task.monitorSessionKey = value;
  } else {
    console.error('Unknown field: ' + field);
    process.exit(1);
  }
  saveTask(task);
  console.log(JSON.stringify({ taskId, updated: field, value }));

} else if (cmd === 'worker-command') {
  const taskId = process.argv[3];
  const workerTaskOverride = process.argv[4];
  const task = loadTask(taskId);
  const wt = workerTaskOverride ? sanitize(workerTaskOverride) : task.workerTask;
  console.log(JSON.stringify({
    command: 'sessions_spawn',
    params: { task: wt, label: 'worker-' + taskId, cleanup: 'keep' }
  }));

} else if (cmd === 'monitor-command') {
  const taskId = process.argv[3];
  const workerSessionKey = sanitize(process.argv[4] || '');
  const roundNum = parseInt(process.argv[5] || '1', 10);
  const task = loadTask(taskId);
  const monitorTask = `Monitor worker session ${workerSessionKey} for task ${taskId}. Round ${roundNum}. Write status to ${path.join(BASE_DIR, taskId, 'monitor-rounds', 'current-round.json')}. Report via Announce every 10 minutes.`;
  console.log(JSON.stringify({
    command: 'sessions_spawn',
    params: { task: monitorTask, label: 'monitor-' + taskId, cleanup: 'delete' }
  }));

} else if (cmd === 'complete') {
  const taskId = process.argv[3];
  const result = sanitize(process.argv[4] || 'completed');
  const task = loadTask(taskId);
  const taskDir = path.join(BASE_DIR, taskId);
  const status = {
    taskId,
    result,
    completedAt: new Date().toISOString(),
    monitorRounds: task.monitorRound,
    workerSessionKey: task.workerSessionKey,
    monitorSessionKey: task.monitorSessionKey
  };
  fs.writeFileSync(path.join(taskDir, 'status.json'), JSON.stringify(status, null, 2));
  task.status = 'completed';
  saveTask(task);
  console.log(JSON.stringify({ taskId, status: 'completed', result }));

} else if (cmd === 'status') {
  const tasks = fs.readdirSync(BASE_DIR)
    .filter(d => fs.existsSync(path.join(BASE_DIR, d, 'task.json')))
    .map(d => JSON.parse(fs.readFileSync(path.join(BASE_DIR, d, 'task.json'), 'utf8')));
  console.log(JSON.stringify(tasks, null, 2));

} else if (cmd === 'round') {
  // Increment monitor round
  const taskId = process.argv[3];
  const task = loadTask(taskId);
  task.monitorRound = (task.monitorRound || 0) + 1;
  saveTask(task);
  const roundDir = path.join(BASE_DIR, taskId, 'monitor-rounds');
  fs.mkdirSync(roundDir, { recursive: true });
  const roundData = {
    round: task.monitorRound,
    recordedAt: new Date().toISOString(),
    workerSessionKey: task.workerSessionKey,
    status: 'monitoring'
  };
  // Archive current round if exists
  const currentRound = path.join(roundDir, 'current-round.json');
  if (fs.existsSync(currentRound)) {
    fs.copyFileSync(currentRound, path.join(roundDir, `round-${task.monitorRound - 1}.json`));
  }
  fs.writeFileSync(currentRound, JSON.stringify(roundData, null, 2));
  console.log(JSON.stringify(roundData));

} else {
  console.error('Unknown command: ' + cmd);
  console.error('Available: start, update, worker-command, monitor-command, complete, status, round');
  process.exit(1);
}
"""

(skill_dir / "long-task.js").write_text(long_task_js)
os.chmod(skill_dir / "long-task.js", 0o755)

# Symlink or copy to workspace for convenience
(workspace / "long-task.js").symlink_to(skill_dir / "long-task.js")

# ── A plausible "previous failed task" as distractor ─────────────────────────
old_task_dir = Path("/root/.openclaw/workspace/long-tasks/task-deadbeef")
old_task_dir.mkdir(parents=True, exist_ok=True)
old_task = {
    "taskId": "task-deadbeef",
    "description": "old failed preprocessing run",
    "workerTask": "python preprocess.py --old",
    "workerSessionKey": "",
    "monitorSessionKey": "",
    "createdAt": "2024-12-01T08:00:00Z",
    "status": "created",
    "monitorRound": 0,
    "workerRestartCount": 0
}
(old_task_dir / "task.json").write_text(json.dumps(old_task, indent=2))

print("Workspace generated successfully.")
print(f"Skill script at: {skill_dir / 'long-task.js'}")
print(f"Symlink at: {workspace / 'long-task.js'}")