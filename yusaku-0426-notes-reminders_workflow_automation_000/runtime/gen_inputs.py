import os
import json
import random

random.seed(42)

# Create workspace directory structure
workspace = "/workspace"

# Create distractor directory structure
dirs = [
    "docs/architecture",
    "docs/meetings",
    "src/components",
    "src/utils",
    "config/env",
    "tests/unit",
    "tests/integration",
    "scripts",
    "data/exports",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "docs/architecture/system_design.md": "# System Design\n\nThis document describes the overall architecture...\n\n## Components\n- Frontend\n- Backend\n- Database",
    "docs/meetings/2024_q4_review.txt": "Q4 Review Meeting Notes\nDate: 2024-12-15\nAttendees: Alice, Bob, Charlie\nTopics: Performance review, roadmap planning",
    "docs/meetings/standup_template.txt": "Daily Standup Template\n- What did I do yesterday?\n- What will I do today?\n- Any blockers?",
    "src/components/header.js": "// Header component\nconst Header = () => {\n  return '<header>App</header>';\n};\nmodule.exports = Header;",
    "src/components/footer.js": "// Footer component\nconst Footer = () => {\n  return '<footer>Footer</footer>';\n};\nmodule.exports = Footer;",
    "src/utils/date_helper.js": "// Date utilities\nfunction formatDate(date) {\n  return date.toISOString();\n}\nmodule.exports = { formatDate };",
    "src/utils/string_helper.js": "// String utilities\nfunction truncate(str, len) {\n  return str.substring(0, len);\n}\nmodule.exports = { truncate };",
    "config/env/development.json": json.dumps({"NODE_ENV": "development", "PORT": 3000, "LOG_LEVEL": "debug"}, indent=2),
    "config/env/production.json": json.dumps({"NODE_ENV": "production", "PORT": 8080, "LOG_LEVEL": "error"}, indent=2),
    "tests/unit/date_helper.test.js": "const { formatDate } = require('../../src/utils/date_helper');\ntest('formats date', () => {\n  expect(typeof formatDate(new Date())).toBe('string');\n});",
    "tests/integration/api.test.js": "// Integration tests for API endpoints\ndescribe('API', () => {\n  it('returns 200 for health check', async () => {\n    // mock test\n    expect(true).toBe(true);\n  });\n});",
    "data/exports/users_export_2024.csv": "id,name,email,created_at\n1,Alice,alice@example.com,2024-01-15\n2,Bob,bob@example.com,2024-03-22\n3,Charlie,charlie@example.com,2024-07-08",
    "data/exports/projects_export_2024.csv": "id,name,status,owner\n101,Project Alpha,active,Alice\n102,Project Beta,completed,Bob\n103,Project Gamma,planning,Charlie",
    "logs/app.log": "[2024-12-01 09:00:00] INFO Server started on port 3000\n[2024-12-01 09:01:22] INFO Database connected\n[2024-12-01 10:15:33] WARN High memory usage detected\n[2024-12-01 11:00:00] INFO Scheduled job executed",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create the scripts directory and implement mock scripts
# notes.js - stores notes in data/notes_db.json
notes_js = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const DB_PATH = path.join(__dirname, '..', 'data', 'notes_db.json');

function loadDb() {
  if (!fs.existsSync(DB_PATH)) return { notes: [] };
  try { return JSON.parse(fs.readFileSync(DB_PATH, 'utf8')); } catch(e) { return { notes: [] }; }
}

function saveDb(db) {
  fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
  fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2), 'utf8');
}

function parseArgs(argv) {
  const args = {};
  for (const arg of argv.slice(3)) {
    const m = arg.match(/^--([^=]+)=(.*)$/s);
    if (m) args[m[1]] = m[2];
  }
  return args;
}

const cmd = process.argv[2];
const args = parseArgs(process.argv);

if (cmd === 'add') {
  const db = loadDb();
  if (!args.title || !args.content) {
    console.error('Error: --title and --content are required');
    process.exit(1);
  }
  const note = {
    id: Date.now(),
    title: args.title,
    content: args.content,
    created_at: new Date().toISOString()
  };
  db.notes.push(note);
  saveDb(db);
  console.log(JSON.stringify({ success: true, note }));

} else if (cmd === 'search') {
  const db = loadDb();
  const query = (args.query || '').toLowerCase();
  const limit = parseInt(args.limit || '10', 10);
  const results = db.notes
    .filter(n => n.title.toLowerCase().includes(query) || n.content.toLowerCase().includes(query))
    .slice(0, limit);
  console.log(JSON.stringify({ success: true, results, count: results.length }));

} else {
  console.error('Unknown command: ' + cmd);
  process.exit(1);
}
"""

# reminders.js - stores reminders in data/reminders_db.json
reminders_js = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const DB_PATH = path.join(__dirname, '..', 'data', 'reminders_db.json');

function loadDb() {
  if (!fs.existsSync(DB_PATH)) return { reminders: [] };
  try { return JSON.parse(fs.readFileSync(DB_PATH, 'utf8')); } catch(e) { return { reminders: [] }; }
}

function saveDb(db) {
  fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
  fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2), 'utf8');
}

function parseArgs(argv) {
  const args = {};
  for (const arg of argv.slice(3)) {
    const m = arg.match(/^--([^=]+)=(.*)$/s);
    if (m) args[m[1]] = m[2];
  }
  return args;
}

const cmd = process.argv[2];
const args = parseArgs(process.argv);

if (cmd === 'add') {
  if (!args.message || !args.remind_at || !args.channel) {
    console.error('Error: --message, --remind_at, and --channel are required');
    process.exit(1);
  }
  // Validate ISO 8601 format with timezone offset
  const isoPattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$/;
  if (!isoPattern.test(args.remind_at)) {
    console.error('Error: --remind_at must be ISO 8601 format with timezone offset (e.g., 2026-02-25T10:00:00+09:00)');
    process.exit(1);
  }
  const db = loadDb();
  const reminder = {
    id: Date.now(),
    message: args.message,
    remind_at: args.remind_at,
    channel: args.channel,
    fired: false,
    created_at: new Date().toISOString()
  };
  db.reminders.push(reminder);
  saveDb(db);
  console.log(JSON.stringify({ success: true, reminder }));

} else if (cmd === 'list') {
  const db = loadDb();
  const pending = db.reminders.filter(r => !r.fired);
  console.log(JSON.stringify({ success: true, reminders: pending, count: pending.length }));

} else if (cmd === 'check-and-fire') {
  const db = loadDb();
  const now = new Date();
  const fired = [];
  for (const r of db.reminders) {
    if (!r.fired && new Date(r.remind_at) <= now) {
      r.fired = true;
      fired.push(r);
    }
  }
  saveDb(db);
  console.log(JSON.stringify({ success: true, fired, count: fired.length }));

} else {
  console.error('Unknown command: ' + cmd);
  process.exit(1);
}
"""

with open(os.path.join(workspace, "scripts", "notes.js"), "w", encoding="utf-8") as f:
    f.write(notes_js)

with open(os.path.join(workspace, "scripts", "reminders.js"), "w", encoding="utf-8") as f:
    f.write(reminders_js)

# Create a task brief file (acts as the business context document, NOT a hint)
brief = """Project: Sprint Planning Assistant Setup
Team: Backend Engineering
Date: 2025-01-10

We need to set up our quick-capture system before the sprint begins.

ACTION ITEMS:
1. Record the following note in the system:
   Title: "Sprint 42 Kickoff"
   Content: "Discuss velocity targets, assign ownership for authentication module refactor, review tech debt backlog items #112 and #118."

2. Set a reminder for: "スプリント計画ミーティングの準備" 
   The reminder should have fired by now (use a past timestamp).
   Use channel: C1BSPRNT42X

3. After setting the reminder, run the due-check process and capture any triggered notifications
   into a file called fired_notifications.txt in the workspace root.
   Each notification line should follow the system's standard notification format.
"""

with open(os.path.join(workspace, "BRIEF.txt"), "w", encoding="utf-8") as f:
    f.write(brief)

# Create a confusing/misleading old notes file in data dir (distractor)
old_notes = {
    "notes": [
        {"id": 1700000000000, "title": "Old Idea", "content": "This is legacy data, ignore.", "created_at": "2023-11-15T08:00:00.000Z"}
    ]
}
with open(os.path.join(workspace, "data", "notes_db.json"), "w", encoding="utf-8") as f:
    json.dump(old_notes, f, indent=2)

print("Workspace generated successfully.")