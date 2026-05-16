import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

# --- Define workspace root ---
workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create a realistic nested directory structure with distractor files ---
dirs = [
    "skills/family-todo",
    "skills/weather",
    "skills/calendar",
    "memory",
    "memory/backups",
    "config",
    "logs",
    "cron",
    "utils",
    "docs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractors = {
    "skills/weather/weather.js": "// Weather skill placeholder\nconst API_KEY = 'dummy';\n",
    "skills/calendar/calendar.js": "// Calendar skill\nmodule.exports = {};\n",
    "config/settings.json": json.dumps({"theme": "dark", "language": "en", "notifications": True}, indent=2),
    "config/users_backup.json": json.dumps({"admin": "000000", "partner": "111111"}, indent=2),
    "logs/app.log": "2024-01-01 08:00:00 INFO App started\n2024-01-02 09:00:00 INFO Cron triggered\n",
    "logs/error.log": "2024-01-03 10:00:00 ERROR Connection refused\n",
    "cron/daily.sh": "#!/bin/bash\n# Daily cron job\nnode /workspace/skills/family-todo/todo.js brief\n",
    "utils/backup.py": "import shutil\n# Backup utility\nshutil.copy('memory/todo.json', 'memory/backups/')\n",
    "docs/onboarding.md": "# Welcome\nPlease configure your skills before use.\n",
    "memory/backups/.gitkeep": "",
    "skills/family-todo/package.json": json.dumps({
        "name": "family-todo",
        "version": "1.0.0",
        "description": "Family todo manager"
    }, indent=2),
}

for rel_path, content in distractors.items():
    full_path = workspace / rel_path
    full_path.write_text(content)

# --- Create the core todo.js script with UNCONFIGURED USERS (the proprietary trap) ---
# Agent must change USERS to specific values, run add/done/list commands
todo_js = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

// =====================================================================
// CONFIGURATION: Replace with your actual Telegram IDs before using!
// =====================================================================
const USERS = {
  'Mark': 'YOUR_TELEGRAM_ID_HERE',
  'Jane': 'PARTNER_TELEGRAM_ID_HERE',
  'Shared': 'GROUP_ID'
};
// =====================================================================

const TODO_FILE = path.join(__dirname, '../../memory/todo.json');

function loadTasks() {
  if (!fs.existsSync(TODO_FILE)) {
    return [];
  }
  try {
    const data = fs.readFileSync(TODO_FILE, 'utf8');
    return JSON.parse(data);
  } catch (e) {
    return [];
  }
}

function saveTasks(tasks) {
  const dir = path.dirname(TODO_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(TODO_FILE, JSON.stringify(tasks, null, 2), 'utf8');
}

function generateId() {
  return Date.now().toString();
}

function addTask(description, user) {
  if (!description || !user) {
    console.error('Usage: node todo.js add "<description>" "<user>"');
    process.exit(1);
  }
  const validUsers = Object.keys(USERS);
  if (!validUsers.includes(user)) {
    console.error(`Unknown user: ${user}. Valid users: ${validUsers.join(', ')}`);
    process.exit(1);
  }
  const tasks = loadTasks();
  const task = {
    id: generateId(),
    description: description,
    user: user,
    status: 'active',
    createdAt: new Date().toISOString()
  };
  tasks.push(task);
  saveTasks(tasks);
  console.log(`Task added [${task.id}]: "${description}" for ${user}`);
}

function listTasks(filterUser) {
  const tasks = loadTasks();
  let filtered;
  if (filterUser) {
    const validUsers = Object.keys(USERS);
    if (!validUsers.includes(filterUser)) {
      console.error(`Unknown user: ${filterUser}. Valid users: ${validUsers.join(', ')}`);
      process.exit(1);
    }
    // Show tasks for the user + Shared family tasks
    filtered = tasks.filter(t => t.status === 'active' && (t.user === filterUser || t.user === 'Shared'));
  } else {
    filtered = tasks.filter(t => t.status === 'active');
  }
  if (filtered.length === 0) {
    console.log('No active tasks.');
    return;
  }
  filtered.forEach(t => {
    console.log(`[${t.id}] (${t.user}) ${t.description}`);
  });
}

function completeTask(identifier) {
  if (!identifier) {
    console.error('Usage: node todo.js done "<id or description>"');
    process.exit(1);
  }
  const tasks = loadTasks();
  // Match by ID or description (case-insensitive)
  const idx = tasks.findIndex(
    t => t.status === 'active' && (t.id === identifier || t.description.toLowerCase() === identifier.toLowerCase())
  );
  if (idx === -1) {
    console.error(`Task not found: ${identifier}`);
    process.exit(1);
  }
  tasks[idx].status = 'done';
  tasks[idx].completedAt = new Date().toISOString();
  saveTasks(tasks);
  console.log(`Task completed: "${tasks[idx].description}"`);
}

function dailyBriefing() {
  const tasks = loadTasks();
  const active = tasks.filter(t => t.status === 'active');
  console.log(`=== Morning Briefing ===`);
  console.log(`Active tasks: ${active.length}`);
  active.forEach(t => {
    console.log(`  [${t.user}] ${t.description}`);
  });
}

function eveningReview() {
  const tasks = loadTasks();
  const done = tasks.filter(t => t.status === 'done');
  const active = tasks.filter(t => t.status === 'active');
  console.log(`=== Evening Review ===`);
  console.log(`Completed today: ${done.length}`);
  console.log(`Still pending: ${active.length}`);
}

const [,, command, arg1, arg2] = process.argv;

switch (command) {
  case 'add':
    addTask(arg1, arg2);
    break;
  case 'list':
    listTasks(arg1);
    break;
  case 'done':
    completeTask(arg1);
    break;
  case 'brief':
    dailyBriefing();
    break;
  case 'review':
    eveningReview();
    break;
  default:
    console.log('Commands: add, list, done, brief, review');
}
"""

(workspace / "skills/family-todo/todo.js").write_text(todo_js)

# --- Create an EMPTY memory/todo.json to start fresh (agent will populate it) ---
# Intentionally leave it empty/missing so the agent must initialize through the tool
todo_json_path = workspace / "memory/todo.json"
# Do NOT pre-create it — let the script handle creation, or leave it absent
# (the script handles missing file gracefully)

# --- Create a task specification file that the agent needs to act on ---
# This is the "business request" in structured form
task_spec = {
    "family_members": {
        "Mark": "112233445",
        "Jane": "998877665",
        "Shared": "550011223"
    },
    "tasks_to_add": [
        {"description": "Buy groceries", "user": "Mark"},
        {"description": "Pick up kids from school", "user": "Jane"},
        {"description": "Pay electricity bill", "user": "Mark"},
        {"description": "Family movie night", "user": "Shared"},
        {"description": "Schedule dentist appointment", "user": "Jane"}
    ],
    "tasks_to_complete": [
        "Buy groceries",
        "Family movie night"
    ]
}
(workspace / "config/family_setup.json").write_text(json.dumps(task_spec, indent=2))

print("Workspace generated successfully.")
print(f"Workspace root: {workspace}")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")