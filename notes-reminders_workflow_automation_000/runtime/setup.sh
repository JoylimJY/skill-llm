#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=/workspace

# ── Write scripts/notes.js ────────────────────────────────────────────────────
cat > "$WORKSPACE/scripts/notes.js" << 'NOTES_JS'
#!/usr/bin/env node
/**
 * notes.js - Mock note management CLI
 * Commands: add, search
 */

const fs = require('fs');
const path = require('path');

const STORE = path.join(__dirname, '..', 'data', 'notes_store.json');

function loadNotes() {
  try { return JSON.parse(fs.readFileSync(STORE, 'utf8')); }
  catch { return []; }
}

function saveNotes(notes) {
  fs.writeFileSync(STORE, JSON.stringify(notes, null, 2), 'utf8');
}

function parseArgs(argv) {
  const args = {};
  for (const arg of argv.slice(2)) {
    const m = arg.match(/^--([^=]+)=(.*)$/s);
    if (m) args[m[1]] = m[2];
  }
  return args;
}

const cmd = process.argv[2];
const args = parseArgs(process.argv);

if (cmd === 'add') {
  if (!args.title || !args.content) {
    console.error('ERROR: --title and --content are required');
    process.exit(1);
  }
  const notes = loadNotes();
  const note = {
    id: Date.now().toString(),
    title: args.title,
    content: args.content,
    created_at: new Date().toISOString()
  };
  notes.push(note);
  saveNotes(notes);
  console.log(JSON.stringify({ status: 'ok', note }));
} else if (cmd === 'search') {
  if (!args.query) {
    console.error('ERROR: --query is required');
    process.exit(1);
  }
  const limit = parseInt(args.limit || '10', 10);
  const notes = loadNotes();
  const q = args.query.toLowerCase();
  const results = notes
    .filter(n => n.title.toLowerCase().includes(q) || n.content.toLowerCase().includes(q))
    .slice(0, limit);
  console.log(JSON.stringify({ status: 'ok', results, total: results.length }));
} else {
  console.error('Unknown command: ' + cmd);
  process.exit(1);
}
NOTES_JS

# ── Write scripts/reminders.js ────────────────────────────────────────────────
cat > "$WORKSPACE/scripts/reminders.js" << 'REMINDERS_JS'
#!/usr/bin/env node
/**
 * reminders.js - Mock reminder management CLI
 * Commands: add, list, check-and-fire
 */

const fs = require('fs');
const path = require('path');

const STORE = path.join(__dirname, '..', 'data', 'reminders_store.json');

function loadReminders() {
  try { return JSON.parse(fs.readFileSync(STORE, 'utf8')); }
  catch { return []; }
}

function saveReminders(reminders) {
  fs.writeFileSync(STORE, JSON.stringify(reminders, null, 2), 'utf8');
}

function parseArgs(argv) {
  const args = {};
  for (const arg of argv.slice(2)) {
    const m = arg.match(/^--([^=]+)=(.*)$/s);
    if (m) args[m[1]] = m[2];
  }
  return args;
}

const cmd = process.argv[2];
const args = parseArgs(process.argv);

if (cmd === 'add') {
  if (!args.message || !args.remind_at || !args.channel) {
    console.error('ERROR: --message, --remind_at, and --channel are required');
    process.exit(1);
  }
  // Validate ISO 8601 with timezone offset
  const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$/;
  if (!isoRegex.test(args.remind_at)) {
    console.error('ERROR: --remind_at must be ISO 8601 with timezone offset, e.g. 2026-02-25T10:00:00+09:00');
    process.exit(1);
  }
  const reminders = loadReminders();
  const reminder = {
    id: Date.now().toString() + Math.floor(Math.random()*1000),
    message: args.message,
    remind_at: args.remind_at,
    channel: args.channel,
    fired: false,
    created_at: new Date().toISOString()
  };
  reminders.push(reminder);
  saveReminders(reminders);
  console.log(JSON.stringify({ status: 'ok', reminder }));
} else if (cmd === 'list') {
  const reminders = loadReminders();
  const pending = reminders.filter(r => !r.fired);
  console.log(JSON.stringify({ status: 'ok', reminders: pending, total: pending.length }));
} else if (cmd === 'check-and-fire') {
  const reminders = loadReminders();
  const now = new Date();
  const fired = [];
  for (const r of reminders) {
    if (!r.fired && new Date(r.remind_at) <= now) {
      r.fired = true;
      fired.push(r);
    }
  }
  saveReminders(reminders);
  console.log(JSON.stringify({ status: 'ok', fired, total_fired: fired.length }));
} else {
  console.error('Unknown command: ' + cmd);
  process.exit(1);
}
REMINDERS_JS

chmod +x "$WORKSPACE/scripts/notes.js"
chmod +x "$WORKSPACE/scripts/reminders.js"

echo "Mock scripts installed and executable."
echo "Workspace ready."