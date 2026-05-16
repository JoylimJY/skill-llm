#!/usr/bin/env python3
"""
Generate a realistic, messy project workspace for the filesystem skill task.
Deterministic with fixed seeds.
"""

import os
import random
import time
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Directory structure ---
dirs = [
    "project/src",
    "project/src/utils",
    "project/src/api",
    "project/src/models",
    "project/logs",
    "project/logs/archive_old",
    "project/data",
    "project/data/cache",
    "project/config",
    "project/tests",
    "project/tmp",
    "archive",        # destination for backup (exists but empty logs subdir should be created by agent)
]

for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Helper ---
def write_file(path, content, size_bytes=None):
    """Write content to file; optionally pad to size_bytes."""
    full = WORKSPACE / path
    full.parent.mkdir(parents=True, exist_ok=True)
    if size_bytes and len(content.encode()) < size_bytes:
        content += " " * (size_bytes - len(content.encode()))
    full.write_text(content, encoding="utf-8")

# --- Source files ---
write_file("project/src/app.js", """\
// Main application entry point
const express = require('express');
const app = express();

// TODO: add middleware
app.get('/', (req, res) => res.send('Hello World'));
app.listen(3000);
""")

write_file("project/src/utils/helpers.js", """\
// Utility helpers
function formatDate(d) { return d.toISOString(); }
function sanitize(s) { return s.replace(/<[^>]*>/g, ''); }
// FIXME: sanitize does not handle nested tags
module.exports = { formatDate, sanitize };
""")

write_file("project/src/api/routes.js", """\
// API route definitions
const router = require('express').Router();
router.get('/health', (req, res) => res.json({ status: 'ok' }));
router.post('/data', (req, res) => {
  // TODO: validate input
  res.json({ received: req.body });
});
module.exports = router;
""")

write_file("project/src/models/user.js", """\
// User model
class User {
  constructor(id, name, email) {
    this.id = id;
    this.name = name;
    this.email = email;
  }
  validate() {
    // FIXME: email validation incomplete
    return this.email.includes('@');
  }
}
module.exports = User;
""")

write_file("project/config/database.json", json.dumps({
    "host": "localhost",
    "port": 5432,
    "name": "appdb",
    "pool": {"min": 2, "max": 10}
}, indent=2))

write_file("project/config/app.json", json.dumps({
    "env": "production",
    "port": 3000,
    "debug": False,
    "logLevel": "warn"
}, indent=2))

# --- Log files (some with ERROR/CRITICAL, some without) ---
write_file("project/logs/app-2024-01-10.log", """\
2024-01-10 08:00:01 INFO  Server started on port 3000
2024-01-10 08:01:15 INFO  GET /health 200 4ms
2024-01-10 08:05:33 WARN  Slow query detected: 450ms
2024-01-10 08:07:44 ERROR Database connection lost: ECONNREFUSED 127.0.0.1:5432
2024-01-10 08:07:45 ERROR Retrying connection (1/3)
2024-01-10 08:07:48 INFO  Connection restored
2024-01-10 08:30:00 INFO  Daily backup started
""")

write_file("project/logs/app-2024-01-11.log", """\
2024-01-11 00:00:01 INFO  Log rotation complete
2024-01-11 09:10:22 INFO  GET /data 200 12ms
2024-01-11 09:15:00 WARN  Memory usage at 78%
2024-01-11 09:16:03 CRITICAL Out of memory: killed process 4421
2024-01-11 09:16:04 ERROR  Service restarting due to OOM
2024-01-11 09:17:01 INFO  Service restarted successfully
2024-01-11 11:00:00 INFO  Scheduled maintenance window
""")

write_file("project/logs/app-2024-01-12.log", """\
2024-01-12 00:00:01 INFO  Log rotation complete
2024-01-12 10:00:00 INFO  GET /health 200 3ms
2024-01-12 10:05:10 INFO  POST /data 201 8ms
2024-01-12 10:10:45 INFO  GET /health 200 4ms
2024-01-12 12:00:00 INFO  Noon checkpoint OK
""")

write_file("project/logs/access-2024-01.log", """\
127.0.0.1 - - [10/Jan/2024:08:01:15 +0000] "GET /health HTTP/1.1" 200 24
10.0.0.5  - - [10/Jan/2024:08:05:00 +0000] "POST /data HTTP/1.1" 201 88
10.0.0.5  - - [11/Jan/2024:09:10:22 +0000] "GET /data HTTP/1.1" 200 312
192.168.1.1 - - [11/Jan/2024:09:16:10 +0000] "GET /health HTTP/1.1" 503 0
""")

# Large log file - should appear in largest files
large_log_content = "2024-01-09 INFO  Routine check OK\n" * 600
write_file("project/logs/archive_old/app-2024-01-09.log", large_log_content)

# --- Data files ---
write_file("project/data/users.json", json.dumps([
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob",   "email": "bob@example.com"},
    {"id": 3, "name": "Carol", "email": "carol@example.com"},
], indent=2))

# Large data file
large_data = json.dumps({"records": [{"id": i, "value": "x" * 80} for i in range(400)], "meta": "cache"}, indent=2)
write_file("project/data/cache/bigcache.json", large_data)

# Another large file to ensure interesting largest-5 results
write_file("project/data/dump.csv", "\n".join(
    ["id,name,score,timestamp"] +
    [f"{i},user_{i},{random.randint(0,100)},2024-01-{(i%28)+1:02d}" for i in range(500)]
))

# --- Test files ---
write_file("project/tests/app.test.js", """\
const assert = require('assert');
const app = require('../src/app');
describe('App', () => {
  it('should start', () => {
    assert.ok(app);
  });
  // TODO: add more tests
});
""")

write_file("project/tests/helpers.test.js", """\
const { sanitize } = require('../src/utils/helpers');
describe('sanitize', () => {
  it('removes simple tags', () => {
    const r = sanitize('<b>hello</b>');
    // ERROR: this test is known broken - sanitize fails on nested
    // assert.strictEqual(r, 'hello');
  });
});
""")

# --- Temp/junk files ---
write_file("project/tmp/session_abc123.tmp", "session data: user=1 token=abc expire=3600")
write_file("project/tmp/upload_xyz.tmp",     "binary blob placeholder " * 30)
write_file("project/tmp/.lock",              "PID:4421")

# --- A markdown README in tmp to act as distractor ---
write_file("project/tmp/NOTES.md", "# scratch notes\n- check logs\n- fix ERROR in helpers")

# Summary: 
# Log files with ERROR/CRITICAL: app-2024-01-10.log, app-2024-01-11.log, tests/helpers.test.js (has "ERROR" comment)
# Log files: 5 .log files total
# Largest files: bigcache.json, dump.csv, archive_old/app-2024-01-09.log are probably largest

print("Workspace generated successfully.")
print("Files created:")
for f in sorted((WORKSPACE / "project").rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)} ({f.stat().st_size} bytes)")