#!/usr/bin/env python3
import os
import random
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Create the filesystem CLI tool (Node.js) ─────────────────────────────
skill_dir = WORKSPACE / ".clawdbot" / "skills" / "filesystem"
skill_dir.mkdir(parents=True, exist_ok=True)

filesystem_js = r"""#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const command = args[0];

function parseArgs(argv) {
  const opts = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (!next || next.startsWith('--') || next.startsWith('-')) {
        opts[key] = true;
      } else {
        opts[key] = next;
        i++;
      }
    } else if (a.startsWith('-') && a.length === 2) {
      const key = a.slice(1);
      const next = argv[i + 1];
      if (!next || next.startsWith('--') || next.startsWith('-')) {
        opts[key] = true;
      } else {
        opts[key] = next;
        i++;
      }
    }
  }
  return opts;
}

function globToRegex(glob) {
  return new RegExp('^' + glob.replace(/\./g, '\\.').replace(/\*\*/g, '§§').replace(/\*/g, '[^/]*').replace(/§§/g, '.*').replace(/\?/g, '[^/]') + '$');
}

function walkDir(dirPath, recursive, maxDepth, currentDepth) {
  currentDepth = currentDepth || 0;
  let results = [];
  let entries;
  try { entries = fs.readdirSync(dirPath, { withFileTypes: true }); } catch(e) { return results; }
  const excludes = ['node_modules', '.git', '.DS_Store'];
  for (const e of entries) {
    if (excludes.includes(e.name)) continue;
    const full = path.join(dirPath, e.name);
    if (e.isDirectory()) {
      if (recursive && (maxDepth == null || currentDepth < maxDepth)) {
        results = results.concat(walkDir(full, recursive, maxDepth, currentDepth + 1));
      }
    } else {
      results.push(full);
    }
  }
  return results;
}

function humanSize(bytes) {
  if (bytes < 1024) return bytes + 'B';
  if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + 'KB';
  if (bytes < 1024*1024*1024) return (bytes/1024/1024).toFixed(1) + 'MB';
  return (bytes/1024/1024/1024).toFixed(1) + 'GB';
}

// ── list ────────────────────────────────────────────────────────────────────
if (command === 'list') {
  const opts = parseArgs(args.slice(1));
  const dir = opts['path'] || opts['p'] || '.';
  const recursive = !!(opts['recursive'] || opts['r']);
  const filterPat = opts['filter'] || opts['f'];
  const details = !!(opts['details'] || opts['d']);
  const sortField = opts['sort'] || opts['s'] || 'name';
  const fmt = opts['format'] || 'list';

  let files = walkDir(dir, recursive, null);
  if (filterPat) {
    const re = globToRegex(filterPat);
    files = files.filter(f => re.test(path.basename(f)));
  }

  let entries = files.map(f => {
    let st;
    try { st = fs.statSync(f); } catch(e) { return null; }
    return { path: f, name: path.basename(f), size: st.size, mtime: st.mtime, ext: path.extname(f) };
  }).filter(Boolean);

  if (sortField === 'size') entries.sort((a,b) => b.size - a.size);
  else if (sortField === 'date') entries.sort((a,b) => b.mtime - a.mtime);
  else entries.sort((a,b) => a.name.localeCompare(b.name));

  if (fmt === 'json') {
    const out = entries.map(e => ({
      path: e.path, name: e.name, size: e.size,
      size_human: humanSize(e.size),
      modified: e.mtime.toISOString(), ext: e.ext
    }));
    console.log(JSON.stringify(out, null, 2));
  } else if (fmt === 'table') {
    console.log('Name\t\tSize\t\tModified');
    console.log('─'.repeat(60));
    for (const e of entries) {
      console.log(`${e.name}\t\t${humanSize(e.size)}\t\t${e.mtime.toISOString()}`);
    }
  } else {
    for (const e of entries) {
      if (details) {
        console.log(`${e.path}\t${humanSize(e.size)}\t${e.mtime.toISOString()}`);
      } else {
        console.log(e.path);
      }
    }
  }

// ── search ──────────────────────────────────────────────────────────────────
} else if (command === 'search') {
  const opts = parseArgs(args.slice(1));
  const pattern = opts['pattern'];
  const dir = opts['path'] || opts['p'] || '.';
  const contentSearch = !!(opts['content'] || opts['c']);
  const contextLines = parseInt(opts['context']) || 0;
  const includePat = opts['include'];
  const excludePat = opts['exclude'];

  let files = walkDir(dir, true, null);

  if (includePat) {
    const re = globToRegex(includePat);
    files = files.filter(f => re.test(path.basename(f)));
  }
  if (excludePat) {
    const re = globToRegex(excludePat);
    files = files.filter(f => !re.test(path.basename(f)));
  }

  if (!pattern) { console.error('--pattern required'); process.exit(1); }
  const searchRe = new RegExp(pattern, 'i');

  if (contentSearch) {
    for (const f of files) {
      let content;
      try { content = fs.readFileSync(f, 'utf8'); } catch(e) { continue; }
      const lines = content.split('\n');
      let matched = false;
      for (let i = 0; i < lines.length; i++) {
        if (searchRe.test(lines[i])) {
          if (!matched) { console.log(`\n==> ${f} <==`); matched = true; }
          const start = Math.max(0, i - contextLines);
          const end = Math.min(lines.length - 1, i + contextLines);
          for (let j = start; j <= end; j++) {
            const prefix = j === i ? '>' : ' ';
            console.log(`${j+1}${prefix} ${lines[j]}`);
          }
        }
      }
    }
  } else {
    for (const f of files) {
      if (searchRe.test(path.basename(f))) {
        console.log(f);
      }
    }
  }

// ── copy ────────────────────────────────────────────────────────────────────
} else if (command === 'copy') {
  const opts = parseArgs(args.slice(1));
  const pattern = opts['pattern'];
  const destDir = opts['to'];
  const dryRun = !!(opts['dry-run']);
  const overwrite = !!(opts['overwrite']);
  const preserve = !!(opts['preserve']);

  if (!pattern || !destDir) {
    console.error('--pattern and --to are required');
    process.exit(1);
  }

  const searchDir = opts['path'] || opts['p'] || '.';
  const re = globToRegex(pattern);
  let files = walkDir(searchDir, true, null).filter(f => re.test(path.basename(f)));

  if (!dryRun) {
    fs.mkdirSync(destDir, { recursive: true });
  }

  let copied = 0;
  for (const src of files) {
    const dest = path.join(destDir, path.basename(src));
    if (!overwrite && !dryRun && fs.existsSync(dest)) {
      console.log(`SKIP (exists): ${src} -> ${dest}`);
      continue;
    }
    if (dryRun) {
      console.log(`[DRY-RUN] Would copy: ${src} -> ${dest}`);
    } else {
      fs.copyFileSync(src, dest);
      if (preserve) {
        const st = fs.statSync(src);
        fs.utimesSync(dest, st.atime, st.mtime);
      }
      console.log(`Copied: ${src} -> ${dest}`);
      copied++;
    }
  }
  if (dryRun) {
    console.log(`\n[DRY-RUN] Would copy ${files.length} file(s) to ${destDir}`);
  } else {
    console.log(`\nCopied ${copied} file(s) to ${destDir}`);
  }

// ── tree ────────────────────────────────────────────────────────────────────
} else if (command === 'tree') {
  const opts = parseArgs(args.slice(1));
  const dir = opts['path'] || opts['p'] || '.';
  const maxDepth = opts['depth'] || opts['d'] ? parseInt(opts['depth'] || opts['d']) : null;
  const dirsOnly = !!(opts['dirs-only']);
  const showSize = !!(opts['size']);

  function printTree(p, prefix, depth) {
    if (maxDepth != null && depth > maxDepth) return;
    let entries;
    try { entries = fs.readdirSync(p, { withFileTypes: true }); } catch(e) { return; }
    const excludes = ['node_modules', '.git', '.DS_Store'];
    entries = entries.filter(e => !excludes.includes(e.name));
    if (dirsOnly) entries = entries.filter(e => e.isDirectory());
    for (let i = 0; i < entries.length; i++) {
      const e = entries[i];
      const isLast = i === entries.length - 1;
      const connector = isLast ? '└── ' : '├── ';
      const childPrefix = isLast ? '    ' : '│   ';
      const full = path.join(p, e.name);
      let sizeStr = '';
      if (showSize && !e.isDirectory()) {
        try { sizeStr = ' [' + humanSize(fs.statSync(full).size) + ']'; } catch(ex) {}
      }
      console.log(prefix + connector + e.name + sizeStr);
      if (e.isDirectory()) {
        printTree(full, prefix + childPrefix, depth + 1);
      }
    }
  }
  console.log(dir);
  printTree(dir, '', 1);

// ── analyze ─────────────────────────────────────────────────────────────────
} else if (command === 'analyze') {
  const opts = parseArgs(args.slice(1));
  const dir = opts['path'] || opts['p'] || '.';
  const showStats = !!(opts['stats']);
  const showTypes = !!(opts['types']);
  const showSizes = !!(opts['sizes']);
  const largestN = opts['largest'] ? parseInt(opts['largest']) : null;
  const fmt = opts['format'] || 'table';

  let files = walkDir(dir, true, null);
  let entries = files.map(f => {
    let st;
    try { st = fs.statSync(f); } catch(e) { return null; }
    return { path: f, name: path.basename(f), size: st.size, ext: path.extname(f) || '(none)' };
  }).filter(Boolean);

  const totalSize = entries.reduce((s, e) => s + e.size, 0);
  const totalFiles = entries.length;

  const typeMap = {};
  for (const e of entries) {
    typeMap[e.ext] = typeMap[e.ext] || { count: 0, totalSize: 0 };
    typeMap[e.ext].count++;
    typeMap[e.ext].totalSize += e.size;
  }

  const sorted = [...entries].sort((a, b) => b.size - a.size);
  const largest = largestN ? sorted.slice(0, largestN) : [];

  if (fmt === 'json') {
    const out = {
      path: dir,
      total_files: totalFiles,
      total_size: totalSize,
      total_size_human: humanSize(totalSize)
    };
    if (showStats || showTypes) {
      out.file_types = {};
      for (const [ext, v] of Object.entries(typeMap)) {
        out.file_types[ext] = {
          count: v.count,
          total_size: v.totalSize,
          total_size_human: humanSize(v.totalSize)
        };
      }
    }
    if (showSizes) {
      out.size_distribution = {
        tiny_under_1KB: entries.filter(e => e.size < 1024).length,
        small_1KB_to_100KB: entries.filter(e => e.size >= 1024 && e.size < 102400).length,
        medium_100KB_to_1MB: entries.filter(e => e.size >= 102400 && e.size < 1048576).length,
        large_over_1MB: entries.filter(e => e.size >= 1048576).length
      };
    }
    if (largestN) {
      out.largest_files = largest.map(e => ({ path: e.path, size: e.size, size_human: humanSize(e.size) }));
    }
    console.log(JSON.stringify(out, null, 2));
  } else {
    console.log(`\nDirectory Analysis: ${dir}`);
    console.log('─'.repeat(50));
    if (showStats) {
      console.log(`Total files : ${totalFiles}`);
      console.log(`Total size  : ${humanSize(totalSize)}`);
    }
    if (showTypes || showStats) {
      console.log('\nFile Types:');
      for (const [ext, v] of Object.entries(typeMap)) {
        console.log(`  ${ext.padEnd(12)} ${v.count} files  ${humanSize(v.totalSize)}`);
      }
    }
    if (showSizes) {
      console.log('\nSize Distribution:');
      console.log(`  < 1KB   : ${entries.filter(e => e.size < 1024).length} files`);
      console.log(`  1KB-100KB: ${entries.filter(e => e.size >= 1024 && e.size < 102400).length} files`);
      console.log(`  100KB-1MB: ${entries.filter(e => e.size >= 102400 && e.size < 1048576).length} files`);
      console.log(`  > 1MB   : ${entries.filter(e => e.size >= 1048576).length} files`);
    }
    if (largestN) {
      console.log(`\nLargest ${largestN} Files:`);
      for (const e of largest) {
        console.log(`  ${humanSize(e.size).padEnd(10)} ${e.path}`);
      }
    }
  }

} else {
  console.error(`Unknown command: ${command}`);
  console.error('Available: list, search, copy, tree, analyze');
  process.exit(1);
}
"""

fs_script = skill_dir / "filesystem"
fs_script.write_text(filesystem_js)

# Also put it in /usr/local/bin for easy access
(WORKSPACE / "bin").mkdir(exist_ok=True)
(WORKSPACE / "bin" / "filesystem").write_text(filesystem_js)

# ── 2. Create the messy logs directory structure ────────────────────────────
logs_dir = WORKSPACE / "logs"

def create_log_content(has_error=False, has_critical=False, svc="app"):
    lines = []
    ts_base = datetime(2024, 3, 15, 8, 0, 0)
    for i in range(random.randint(30, 80)):
        ts = ts_base + timedelta(minutes=i * 2 + random.randint(0, 5))
        ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S")
        level = random.choice(["INFO", "INFO", "INFO", "DEBUG", "WARN"])
        msg = random.choice([
            "Request processed successfully",
            "Cache hit for key user_session_" + str(random.randint(1000,9999)),
            "Database query took " + str(random.randint(2, 150)) + "ms",
            "Heartbeat OK",
            "Config reloaded",
            "Worker thread idle",
            "Memory usage nominal",
            "Connection pool size: " + str(random.randint(5, 20)),
        ])
        lines.append(f"[{ts_str}] [{level}] [{svc}] {msg}")
    
    if has_error:
        for _ in range(random.randint(3, 7)):
            i = random.randint(0, len(lines)-1)
            ts = ts_base + timedelta(minutes=i*2)
            ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S")
            error_code = random.choice(["E1042", "E2099", "E5001", "E3301"])
            lines.insert(i, f"[{ts_str}] [ERROR] [{svc}] Connection refused - code {error_code}: upstream timeout")

    if has_critical:
        for _ in range(random.randint(1, 3)):
            i = random.randint(0, len(lines)-1)
            ts = ts_base + timedelta(minutes=i*2)
            ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S")
            lines.insert(i, f"[{ts_str}] [CRITICAL] [{svc}] OOM killer invoked - process {random.randint(1000,9999)} terminated")

    return "\n".join(lines) + "\n"

# services/web/
web_dir = logs_dir / "services" / "web"
web_dir.mkdir(parents=True)

# access.log - no errors (distractor)
(web_dir / "access.log").write_text(create_log_content(False, False, "nginx"))
# error.log - has errors
(web_dir / "error.log").write_text(create_log_content(True, False, "nginx"))
# app.log - has both
(web_dir / "app.log").write_text(create_log_content(True, True, "webserver"))
# debug.log - no errors (distractor)
(web_dir / "debug.log").write_text(create_log_content(False, False, "webserver"))

# services/api/
api_dir = logs_dir / "services" / "api"
api_dir.mkdir(parents=True)

(api_dir / "api-server.log").write_text(create_log_content(True, False, "api"))
(api_dir / "scheduler.log").write_text(create_log_content(False, False, "scheduler"))
(api_dir / "worker.log").write_text(create_log_content(True, True, "worker"))
# A .txt file that contains errors - should NOT be picked up by *.log filter
(api_dir / "notes.txt").write_text("ERROR: manual note\nSome random CRITICAL observations\n")

# services/db/
db_dir = logs_dir / "services" / "db"
db_dir.mkdir(parents=True)

(db_dir / "postgres.log").write_text(create_log_content(True, False, "postgres"))
(db_dir / "slow_queries.log").write_text(create_log_content(False, False, "postgres"))
(db_dir / "replication.log").write_text(create_log_content(False, True, "postgres-repl"))
(db_dir / "backup.log").write_text(create_log_content(False, False, "pg_dump"))

# archive/ - old logs compressed-like (just text but named .gz for distraction)
archive_dir = logs_dir / "archive"
archive_dir.mkdir()
(archive_dir / "2024-01-app.log.gz").write_bytes(b'\x1f\x8b' + os.urandom(50))  # fake gz
(archive_dir / "2024-02-app.log.gz").write_bytes(b'\x1f\x8b' + os.urandom(50))
(archive_dir / "2024-01-error.log").write_text(create_log_content(True, False, "archive"))

# metrics/ - JSON metrics files (not logs)
metrics_dir = logs_dir / "metrics"
metrics_dir.mkdir()
for d in range(1, 6):
    metrics = {
        "date": f"2024-03-{d:02d}",
        "requests": random.randint(10000, 50000),
        "errors": random.randint(50, 500),
        "p99_latency_ms": random.randint(100, 800),
    }
    (metrics_dir / f"metrics-2024-03-{d:02d}.json").write_text(json.dumps(metrics, indent=2))

# system/ - OS-level logs
sys_dir = logs_dir / "system"
sys_dir.mkdir()
(sys_dir / "syslog.log").write_text(create_log_content(False, False, "kernel"))
(sys_dir / "auth.log").write_text(create_log_content(True, False, "sshd"))
(sys_dir / "kernel.log").write_text(create_log_content(False, True, "kernel"))
# A README-like distractor
(sys_dir / "README.txt").write_text("System logs directory. Do not modify.\n")

# Top-level summary (distractor, non-log)
(logs_dir / "summary.csv").write_text("date,service,error_count\n2024-03-15,web,12\n2024-03-15,api,7\n")
(logs_dir / ".keep").write_text("")

# ── 3. Create a project directory with distractor files ──────────────────────
proj_dir = WORKSPACE / "project"
proj_dir.mkdir()
for name in ["main.py", "utils.py", "config.yaml", "requirements.txt", "Makefile"]:
    (proj_dir / name).write_text(f"# {name}\nplaceholder content\n")

(WORKSPACE / "README.md").write_text(
    "# Server Log Audit Workspace\n\nThis workspace contains server logs from the production environment.\n"
)

print("Workspace initialized successfully.")
print(f"Logs directory: {logs_dir}")
print(f"Filesystem CLI: {skill_dir / 'filesystem'}")