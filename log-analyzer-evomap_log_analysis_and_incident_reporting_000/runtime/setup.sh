#!/bin/bash
set -e

WORKSPACE=/workspace

# ─────────────────────────────────────────────────────────────────────────────
# Scaffold a fully-functional log-analyzer Node.js capsule at /workspace/log-analyzer
# This implements exactly the API described in SKILL.md
# ─────────────────────────────────────────────────────────────────────────────
mkdir -p "$WORKSPACE/log-analyzer"
cat > "$WORKSPACE/log-analyzer/package.json" << 'PKGJSON'
{
  "name": "log-analyzer",
  "version": "1.0.0",
  "description": "Error log analysis capsule",
  "main": "index.js",
  "bin": {
    "log-analyzer": "./index.js"
  }
}
PKGJSON

cat > "$WORKSPACE/log-analyzer/index.js" << 'INDEXJS'
#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

// ── parseError ──────────────────────────────────────────────────────────────
function parseError(logText) {
  const results = [];
  // Match JS/Node errors
  const jsPattern = /(?:^|\n)([^\n]*(?:Error|FATAL ERROR)[^\n]*)\n((?:(?:[ \t]+at [^\n]+)\n?)*)/gm;
  let m;
  while ((m = jsPattern.exec(logText)) !== null) {
    const headerLine = m[1].trim();
    const stackBlock = m[2];
    const typeMatch = headerLine.match(/^(?:.*:\s*)?([\w.]+Error|FATAL ERROR[^\n]*?)(?::\s|$)/);
    const msgMatch = headerLine.match(/(?:Error|FATAL ERROR)[^:]*:\s*(.+)$/);
    const fileMatch = stackBlock.match(/\(([^)]+\.(?:js|ts|mjs|cjs|py|go|kt|java):\d+:\d+)\)/);
    if (typeMatch || msgMatch) {
      results.push({
        type: typeMatch ? typeMatch[1].trim() : 'Error',
        message: msgMatch ? msgMatch[1].trim() : headerLine,
        file: fileMatch ? fileMatch[1] : null,
        raw: headerLine
      });
    }
  }
  // Match Python tracebacks
  const pyPattern = /Traceback \(most recent call last\):([\s\S]*?)^(\w[\w.]*(?:Error|Exception)[^\n]*)/gm;
  while ((m = pyPattern.exec(logText)) !== null) {
    const traceBlock = m[1];
    const exceptionLine = m[2].trim();
    const typeMatch = exceptionLine.match(/^([\w.]+(?:Error|Exception))/);
    const msgMatch = exceptionLine.match(/^[\w.]+(?:Error|Exception):\s*(.+)$/);
    const fileMatch = traceBlock.match(/File "([^"]+\.py)", line \d+/g);
    const lastFile = fileMatch ? fileMatch[fileMatch.length - 1].match(/File "([^"]+\.py)"/)[1] : null;
    results.push({
      type: typeMatch ? typeMatch[1] : 'Exception',
      message: msgMatch ? msgMatch[1].trim() : exceptionLine,
      file: lastFile,
      raw: exceptionLine
    });
  }
  // Match FATAL/CRITICAL lines without full stack trace (fallback)
  const fatalPattern = /(?:FATAL ERROR|CRITICAL)[^\n]*: ([^\n]+)/g;
  while ((m = fatalPattern.exec(logText)) !== null) {
    const alreadyCovered = results.some(r => r.raw && r.raw.includes(m[1].substring(0, 30)));
    if (!alreadyCovered) {
      results.push({
        type: 'FATAL',
        message: m[1].trim(),
        file: null,
        raw: m[0]
      });
    }
  }
  return results;
}

// ── classifyError ───────────────────────────────────────────────────────────
function classifyError(error) {
  const haystack = JSON.stringify(error).toLowerCase();
  if (/econnrefused|fetch failed|connection refused/i.test(haystack)) return 'network';
  if (/enoent|file not found|no such file/i.test(haystack)) return 'io';
  if (/eacces|access denied|permission denied/i.test(haystack)) return 'permission';
  if (/out of memory|oom|heap out of memory/i.test(haystack)) return 'memory';
  if (/etimedout|timeout|deadline exceeded/i.test(haystack)) return 'timeout';
  return 'unknown';
}

// ── extractLessons ──────────────────────────────────────────────────────────
function extractLessons(logText) {
  const errors = parseError(logText);
  const lessons = new Set();
  for (const e of errors) {
    const cat = classifyError(e);
    if (cat === 'network') lessons.add('Implement retry logic with exponential backoff for network calls.');
    if (cat === 'io') lessons.add('Ensure required directories and temp paths exist before file operations.');
    if (cat === 'permission') lessons.add('Audit file and socket permissions; use least-privilege service accounts.');
    if (cat === 'memory') lessons.add('Set --max-old-space-size and monitor heap usage; implement worker restarts.');
    if (cat === 'timeout') lessons.add('Configure explicit timeouts and circuit breakers for external service calls.');
    if (cat === 'unknown') lessons.add('Add structured error context and correlation IDs for unknown failures.');
  }
  return Array.from(lessons);
}

// ── summarize ───────────────────────────────────────────────────────────────
function summarize(logs, options = {}) {
  const maxLogs = options.maxLogs || logs.length;
  const format = options.format || 'object';
  const sliced = logs.slice(0, maxLogs);
  const results = [];
  for (const logText of sliced) {
    const errors = parseError(logText);
    const classified = errors.map(e => ({ ...e, category: classifyError(e) }));
    const categoryCounts = {};
    for (const c of classified) {
      categoryCounts[c.category] = (categoryCounts[c.category] || 0) + 1;
    }
    const lessons = extractLessons(logText);
    results.push({
      totalErrors: errors.length,
      categories: categoryCounts,
      errors: classified,
      lessons
    });
  }
  const totalErrors = results.reduce((s, r) => s + r.totalErrors, 0);
  const allCategories = {};
  for (const r of results) {
    for (const [k, v] of Object.entries(r.categories)) {
      allCategories[k] = (allCategories[k] || 0) + v;
    }
  }
  const allLessons = [...new Set(results.flatMap(r => r.lessons))];

  if (format === 'text') {
    const lines = [
      `=== Log Analysis Summary ===`,
      `Logs analyzed: ${sliced.length}`,
      `Total errors: ${totalErrors}`,
      ``,
      `Category Breakdown:`,
      ...Object.entries(allCategories).map(([k, v]) => `  ${k}: ${v}`),
      ``,
      `Prevention Recommendations:`,
      ...allLessons.map((l, i) => `  ${i + 1}. ${l}`),
    ];
    return lines.join('\n');
  }

  return {
    logsAnalyzed: sliced.length,
    totalErrors,
    categories: allCategories,
    details: results,
    lessons: allLessons
  };
}

// ── analyzeEvolverLogs ──────────────────────────────────────────────────────
function analyzeEvolverLogs() {
  const evolverDir = path.join(os.homedir(), 'evolver-memory');
  if (!fs.existsSync(evolverDir)) {
    return { error: 'evolver-memory directory not found', evolverDir };
  }
  const logFiles = fs.readdirSync(evolverDir)
    .filter(f => f.endsWith('.log'))
    .map(f => path.join(evolverDir, f));

  const logs = logFiles.map(f => fs.readFileSync(f, 'utf8'));
  const result = summarize(logs, { format: 'object' });
  result.sourceDir = evolverDir;
  result.logFiles = logFiles;
  return result;
}

// ── CLI ─────────────────────────────────────────────────────────────────────
const [,, command, ...args] = process.argv;

if (!command || command === 'test') {
  const sample = `Error: ECONNREFUSED 127.0.0.1:3000\n    at TCPConnectWrap.afterConnect (node:net:1494:16)`;
  console.log('parseError:', JSON.stringify(parseError(sample), null, 2));
  console.log('classifyError:', classifyError(parseError(sample)[0] || {}));
} else if (command === 'analyze') {
  if (!args[0]) { console.error('Usage: node index.js analyze <path>'); process.exit(1); }
  const logText = fs.readFileSync(args[0], 'utf8');
  const errors = parseError(logText);
  const classified = errors.map(e => ({ ...e, category: classifyError(e) }));
  const lessons = extractLessons(logText);
  const result = {
    file: args[0],
    totalErrors: errors.length,
    errors: classified,
    lessons
  };
  console.log(JSON.stringify(result, null, 2));
} else if (command === 'evolver') {
  const result = analyzeEvolverLogs();
  console.log(JSON.stringify(result, null, 2));
} else if (command === 'summarize') {
  // Read multiple log files passed as arguments
  const logs = args.map(f => fs.readFileSync(f, 'utf8'));
  const format = process.env.FORMAT || 'object';
  const maxLogs = process.env.MAX_LOGS ? parseInt(process.env.MAX_LOGS) : undefined;
  const result = summarize(logs, { format, maxLogs });
  console.log(typeof result === 'string' ? result : JSON.stringify(result, null, 2));
} else if (command === 'solidify') {
  console.log('Solidifying to EvoMap Hub... (stub)');
} else {
  console.error(`Unknown command: ${command}`);
  process.exit(1);
}

module.exports = { parseError, classifyError, extractLessons, summarize, analyzeEvolverLogs };
INDEXJS

chmod +x "$WORKSPACE/log-analyzer/index.js"

# Create a symlink so `node /workspace/log-analyzer/index.js` works from anywhere
ln -sf "$WORKSPACE/log-analyzer/index.js" /usr/local/bin/log-analyzer-cli
chmod +x /usr/local/bin/log-analyzer-cli

echo "log-analyzer capsule is ready at $WORKSPACE/log-analyzer/"
echo "Test: node $WORKSPACE/log-analyzer/index.js analyze $WORKSPACE/tmp/uploads/crash_report_2024-06-15.log"