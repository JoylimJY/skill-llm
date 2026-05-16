#!/bin/bash
set -e

# -------------------------------------------------------------------------
# Create the mock cli.js that simulates mac-reminders-agent behavior
# Records all CLI invocations and returns realistic JSON responses
# -------------------------------------------------------------------------

mkdir -p /workspace/skills/mac-reminders-agent

cat > /workspace/skills/mac-reminders-agent/cli.js << 'NODE_MOCK_EOF'
#!/usr/bin/env node
/**
 * MOCK mac-reminders-agent CLI
 * Simulates the full documented interface.
 * Records all calls to /workspace/cli_calls.log
 * For `parse --file`: returns structured action items from meeting_notes.txt
 * For `add`: records call, assigns deterministic ID, updates added_reminders.json
 * For `list`: returns added_reminders.json contents
 * For `edit`: records call, updates reminder in added_reminders.json
 */

const fs = require('fs');
const path = require('path');
const args = process.argv.slice(2);

const LOG_FILE = '/workspace/cli_calls.log';
const REMINDERS_FILE = '/workspace/added_reminders.json';

// Log this invocation
const callRecord = {
  timestamp: new Date().toISOString(),
  args: args,
  raw: process.argv.slice(2).join(' ')
};
const existingLog = fs.existsSync(LOG_FILE) ? fs.readFileSync(LOG_FILE, 'utf8') : '';
fs.writeFileSync(LOG_FILE, existingLog + JSON.stringify(callRecord) + '\n');

function getArg(name) {
  const idx = args.indexOf(name);
  if (idx === -1) return null;
  return args[idx + 1] || null;
}

function hasFlag(name) {
  return args.includes(name);
}

const command = args[0];

// ------------------------------------------------------------------
// PARSE command
// ------------------------------------------------------------------
if (command === 'parse') {
  const filePath = getArg('--file');
  const textArg = getArg('--text');
  const locale = getArg('--locale') || 'en';

  // Return pre-defined parse results matching the meeting_notes.txt
  const result = {
    ok: true,
    locale: locale,
    labels: {},
    items: [
      {
        title: "Prepare Q1 performance report",
        due: "2026-03-20T17:00:00+09:00",
        priority: "high",
        confidence: "high",
        source_line: "Alice: Prepare Q1 performance report by March 20 - URGENT"
      },
      {
        title: "Bi-weekly engineering standup",
        due: "2026-02-10T09:00:00+09:00",
        priority: "medium",
        confidence: "high",
        source_line: "Bob: Bi-weekly engineering standup every other Monday starting Feb 10",
        recurrence_hint: "bi-weekly"
      },
      {
        title: "Update API documentation",
        due: "2026-02-28T17:00:00+09:00",
        priority: "medium",
        confidence: "high",
        source_line: "Carol: Update API documentation deadline: February 28"
      },
      {
        title: "Schedule security audit review",
        due: "2026-02-15T17:00:00+09:00",
        priority: "high",
        confidence: "high",
        source_line: "Dave: Schedule security audit review by February 15"
      }
    ]
  };
  console.log(JSON.stringify(result, null, 2));
  process.exit(0);
}

// ------------------------------------------------------------------
// LISTS command
// ------------------------------------------------------------------
if (command === 'lists') {
  const result = {
    calendars: [
      { id: "CAL-DEFAULT-001", name: "Reminders", isDefault: true },
      { id: "CAL-WORK-002", name: "Work", isDefault: false },
      { id: "CAL-PERSONAL-003", name: "Personal", isDefault: false }
    ]
  };
  console.log(JSON.stringify(result, null, 2));
  process.exit(0);
}

// ------------------------------------------------------------------
// LIST command
// ------------------------------------------------------------------
if (command === 'list') {
  const reminders = JSON.parse(fs.readFileSync(REMINDERS_FILE, 'utf8'));
  console.log(JSON.stringify(reminders, null, 2));
  process.exit(0);
}

// ------------------------------------------------------------------
// ADD command
// ------------------------------------------------------------------
if (command === 'add') {
  const title = getArg('--title');
  const due = getArg('--due');
  const note = getArg('--note');
  const priority = getArg('--priority') || 'none';
  const list = getArg('--list') || 'Reminders';
  const repeat = getArg('--repeat');
  const interval = getArg('--interval');
  const repeatEnd = getArg('--repeat-end');
  const locale = getArg('--locale') || 'en';

  if (!title) {
    console.error(JSON.stringify({ ok: false, error: "--title is required" }));
    process.exit(1);
  }

  // Generate deterministic ID from title
  const hash = title.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const id = `REM-${hash.toString(16).toUpperCase().padStart(6,'0')}-${Date.now().toString(36).toUpperCase()}`;

  const newReminder = {
    id,
    title,
    due: due || null,
    list,
    priority,
    completed: false,
    note: note || null,
    repeat: repeat || null,
    interval: interval ? parseInt(interval) : (repeat ? 1 : null),
    repeatEnd: repeatEnd || null
  };

  const reminders = JSON.parse(fs.readFileSync(REMINDERS_FILE, 'utf8'));
  reminders.push(newReminder);
  fs.writeFileSync(REMINDERS_FILE, JSON.stringify(reminders, null, 2));

  const response = {
    ok: true,
    id: id,
    message: `Added '${title}' reminder${due ? ' for ' + due : ' without a due date'}.${repeat ? ' Repeats ' + repeat + (interval ? ' every ' + interval : '') + '.' : ''}`
  };
  console.log(JSON.stringify(response, null, 2));
  process.exit(0);
}

// ------------------------------------------------------------------
// EDIT command
// ------------------------------------------------------------------
if (command === 'edit') {
  const id = getArg('--id');
  if (!id) {
    console.error(JSON.stringify({ ok: false, error: "--id is required" }));
    process.exit(1);
  }

  const reminders = JSON.parse(fs.readFileSync(REMINDERS_FILE, 'utf8'));
  const idx = reminders.findIndex(r => r.id === id);
  if (idx === -1) {
    console.error(JSON.stringify({ ok: false, error: `Reminder with id '${id}' not found` }));
    process.exit(1);
  }

  const newTitle = getArg('--title');
  const newDue = getArg('--due');
  const newNote = getArg('--note');
  const newPriority = getArg('--priority');

  if (newTitle) reminders[idx].title = newTitle;
  if (newDue) reminders[idx].due = newDue;
  if (newNote) reminders[idx].note = newNote;
  if (newPriority) reminders[idx].priority = newPriority;

  fs.writeFileSync(REMINDERS_FILE, JSON.stringify(reminders, null, 2));

  console.log(JSON.stringify({ ok: true, message: "Updated reminder.", reminder: reminders[idx] }));
  process.exit(0);
}

// ------------------------------------------------------------------
// DELETE command
// ------------------------------------------------------------------
if (command === 'delete') {
  const id = getArg('--id');
  if (!id) { console.error(JSON.stringify({ ok: false, error: "--id is required" })); process.exit(1); }

  const reminders = JSON.parse(fs.readFileSync(REMINDERS_FILE, 'utf8'));
  const idx = reminders.findIndex(r => r.id === id);
  if (idx === -1) { console.error(JSON.stringify({ ok: false, error: "Not found" })); process.exit(1); }
  reminders.splice(idx, 1);
  fs.writeFileSync(REMINDERS_FILE, JSON.stringify(reminders, null, 2));
  console.log(JSON.stringify({ ok: true, message: "Deleted reminder." }));
  process.exit(0);
}

// ------------------------------------------------------------------
// COMPLETE command
// ------------------------------------------------------------------
if (command === 'complete') {
  const id = getArg('--id');
  if (!id) { console.error(JSON.stringify({ ok: false, error: "--id is required" })); process.exit(1); }

  const reminders = JSON.parse(fs.readFileSync(REMINDERS_FILE, 'utf8'));
  const idx = reminders.findIndex(r => r.id === id);
  if (idx === -1) { console.error(JSON.stringify({ ok: false, error: "Not found" })); process.exit(1); }
  reminders[idx].completed = true;
  fs.writeFileSync(REMINDERS_FILE, JSON.stringify(reminders, null, 2));
  console.log(JSON.stringify({ ok: true, message: "Marked as completed." }));
  process.exit(0);
}

// Unknown command
console.error(JSON.stringify({ ok: false, error: `Unknown command: ${command}` }));
process.exit(1);
NODE_MOCK_EOF

chmod +x /workspace/skills/mac-reminders-agent/cli.js

# Verify node is available
node --version
echo "Mock CLI ready at /workspace/skills/mac-reminders-agent/cli.js"

# Ensure log and state files are clean
echo "" > /workspace/cli_calls.log
echo "[]" > /workspace/added_reminders.json