import os
import random
import json

random.seed(42)

WORKSPACE = "/workspace"

# ── 1. Create the skill itself ───────────────────────────────────────────────
skill_dir = os.path.join(WORKSPACE, "skills", "code-stats")
os.makedirs(skill_dir, exist_ok=True)

# The real index.js that the skill executes
index_js = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const LANGUAGE_MAP = {
  '.js':   'JavaScript',
  '.jsx':  'JavaScript',
  '.ts':   'TypeScript',
  '.tsx':  'TypeScript',
  '.py':   'Python',
  '.json': 'JSON',
  '.yaml': 'YAML',
  '.yml':  'YAML',
  '.md':   'Markdown',
  '.sh':   'Shell',
  '.bash': 'Shell',
  '.html': 'HTML',
  '.htm':  'HTML',
  '.css':  'CSS',
};

const IGNORED_DIRS = new Set(['node_modules', '.git', '__pycache__', '.cache', 'dist', 'build', '.next', 'venv', '.venv']);

function countLines(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return content.split('\n').length;
  } catch {
    return 0;
  }
}

function walk(dir, stats) {
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
  catch { return; }

  for (const entry of entries) {
    if (IGNORED_DIRS.has(entry.name)) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath, stats);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name).toLowerCase();
      const lang = LANGUAGE_MAP[ext];
      if (!lang) continue;           // unsupported → skip
      const lines = countLines(fullPath);
      if (!stats[lang]) stats[lang] = { files: 0, lines: 0 };
      stats[lang].files++;
      stats[lang].lines += lines;
    }
  }
}

const cwd = process.cwd();
const langStats = {};
walk(cwd, langStats);

let totalFiles = 0;
let totalLines = 0;
for (const lang of Object.values(langStats)) {
  totalFiles += lang.files;
  totalLines += lang.lines;
}

console.log(`\n📊 Code Stats for ${cwd}`);
console.log('========================================');
console.log(`Total Files: ${totalFiles}`);
console.log(`Total Lines: ${totalLines.toLocaleString()}`);
console.log('\nBy Language:');

const sorted = Object.entries(langStats).sort((a, b) => b[1].lines - a[1].lines);
for (const [lang, info] of sorted) {
  const pct = totalLines > 0 ? ((info.lines / totalLines) * 100).toFixed(1) : '0.0';
  console.log(`  ${lang}: ${info.files} files, ${info.lines.toLocaleString()} lines (${pct}%)`);
}
console.log('');
"""

with open(os.path.join(skill_dir, "index.js"), "w") as f:
    f.write(index_js)

# ── 2. Create the project codebase to be analysed ───────────────────────────
# This simulates a real mixed-language project with DISTRACTOR files in
# unsupported languages (.java, .cpp, .rb, .go) that the skill will ignore.

project_root = WORKSPACE  # skill runs from WORKSPACE

# ── Python files ────────────────────────────────────────────────────────────
py_dir = os.path.join(project_root, "src", "analytics")
os.makedirs(py_dir, exist_ok=True)

py_file1 = "\n".join([
    "import pandas as pd",
    "import numpy as np",
    "",
    "def compute_metrics(df):",
    "    \"\"\"Compute key analytics metrics.\"\"\"",
    "    result = {}",
    "    result['mean'] = df.mean()",
    "    result['std']  = df.std()",
    "    result['max']  = df.max()",
    "    result['min']  = df.min()",
    "    return result",
    "",
    "def filter_outliers(df, z_thresh=3.0):",
    "    from scipy import stats",
    "    z = np.abs(stats.zscore(df))",
    "    return df[(z < z_thresh).all(axis=1)]",
])
with open(os.path.join(py_dir, "metrics.py"), "w") as f:
    f.write(py_file1)

py_file2 = "\n".join([
    "class DataPipeline:",
    "    def __init__(self, source):",
    "        self.source = source",
    "        self.transforms = []",
    "",
    "    def add_transform(self, fn):",
    "        self.transforms.append(fn)",
    "        return self",
    "",
    "    def run(self, data):",
    "        for t in self.transforms:",
    "            data = t(data)",
    "        return data",
    "",
    "    def __repr__(self):",
    "        return f'DataPipeline(source={self.source!r}, steps={len(self.transforms)})'",
])
with open(os.path.join(py_dir, "pipeline.py"), "w") as f:
    f.write(py_file2)

# ── JavaScript files ─────────────────────────────────────────────────────────
js_dir = os.path.join(project_root, "src", "frontend")
os.makedirs(js_dir, exist_ok=True)

js_file1 = "\n".join([
    "const express = require('express');",
    "const router  = express.Router();",
    "",
    "router.get('/health', (req, res) => {",
    "  res.json({ status: 'ok', ts: Date.now() });",
    "});",
    "",
    "router.post('/data', async (req, res) => {",
    "  const { payload } = req.body;",
    "  if (!payload) return res.status(400).json({ error: 'missing payload' });",
    "  // process payload",
    "  res.json({ received: true });",
    "});",
    "",
    "module.exports = router;",
])
with open(os.path.join(js_dir, "routes.js"), "w") as f:
    f.write(js_file1)

js_file2 = "\n".join([
    "function debounce(fn, delay) {",
    "  let timer;",
    "  return (...args) => {",
    "    clearTimeout(timer);",
    "    timer = setTimeout(() => fn(...args), delay);",
    "  };",
    "}",
    "",
    "function throttle(fn, limit) {",
    "  let lastCall = 0;",
    "  return (...args) => {",
    "    const now = Date.now();",
    "    if (now - lastCall >= limit) {",
    "      lastCall = now;",
    "      return fn(...args);",
    "    }",
    "  };",
    "}",
    "",
    "module.exports = { debounce, throttle };",
])
with open(os.path.join(js_dir, "utils.js"), "w") as f:
    f.write(js_file2)

js_comp_dir = os.path.join(project_root, "src", "frontend", "components")
os.makedirs(js_comp_dir, exist_ok=True)
js_file3 = "\n".join([
    "import React, { useState, useEffect } from 'react';",
    "",
    "export function Dashboard({ userId }) {",
    "  const [data, setData] = useState(null);",
    "  const [loading, setLoading] = useState(true);",
    "",
    "  useEffect(() => {",
    "    fetch(`/api/user/${userId}`)",
    "      .then(r => r.json())",
    "      .then(d => { setData(d); setLoading(false); })",
    "      .catch(console.error);",
    "  }, [userId]);",
    "",
    "  if (loading) return <div>Loading...</div>;",
    "  return <div className='dashboard'>{JSON.stringify(data)}</div>;",
    "}",
])
with open(os.path.join(js_comp_dir, "Dashboard.jsx"), "w") as f:
    f.write(js_file3)

# ── TypeScript files ──────────────────────────────────────────────────────────
ts_dir = os.path.join(project_root, "src", "types")
os.makedirs(ts_dir, exist_ok=True)
ts_file1 = "\n".join([
    "export interface User {",
    "  id: string;",
    "  name: string;",
    "  email: string;",
    "  createdAt: Date;",
    "  roles: Role[];",
    "}",
    "",
    "export type Role = 'admin' | 'editor' | 'viewer';",
    "",
    "export interface ApiResponse<T> {",
    "  data: T;",
    "  error: string | null;",
    "  statusCode: number;",
    "}",
])
with open(os.path.join(ts_dir, "models.ts"), "w") as f:
    f.write(ts_file1)

# ── Shell scripts ─────────────────────────────────────────────────────────────
scripts_dir = os.path.join(project_root, "scripts")
os.makedirs(scripts_dir, exist_ok=True)
sh_file1 = "\n".join([
    "#!/bin/bash",
    "set -euo pipefail",
    "",
    "echo 'Building project...'",
    "npm install --frozen-lockfile",
    "npm run build",
    "",
    "echo 'Running tests...'",
    "npm test -- --coverage",
    "",
    "echo 'Done.'",
])
with open(os.path.join(scripts_dir, "build.sh"), "w") as f:
    f.write(sh_file1)

# ── YAML / JSON config files ──────────────────────────────────────────────────
config_dir = os.path.join(project_root, "config")
os.makedirs(config_dir, exist_ok=True)

yaml_content = "\n".join([
    "version: '3.8'",
    "services:",
    "  app:",
    "    image: node:18-alpine",
    "    ports:",
    "      - '3000:3000'",
    "    environment:",
    "      NODE_ENV: production",
    "      DB_HOST: postgres",
    "  postgres:",
    "    image: postgres:15",
    "    environment:",
    "      POSTGRES_DB: appdb",
    "      POSTGRES_USER: admin",
    "      POSTGRES_PASSWORD: secret",
    "    volumes:",
    "      - pgdata:/var/lib/postgresql/data",
    "volumes:",
    "  pgdata:",
])
with open(os.path.join(config_dir, "docker-compose.yml"), "w") as f:
    f.write(yaml_content)

json_content = json.dumps({
    "name": "my-project",
    "version": "1.2.3",
    "scripts": {
        "build": "tsc && webpack",
        "test": "jest",
        "lint": "eslint src/"
    },
    "dependencies": {
        "express": "^4.18.0",
        "react": "^18.0.0"
    }
}, indent=2)
with open(os.path.join(config_dir, "package.json"), "w") as f:
    f.write(json_content)

# ── Markdown ──────────────────────────────────────────────────────────────────
docs_dir = os.path.join(project_root, "docs")
os.makedirs(docs_dir, exist_ok=True)
md_content = "\n".join([
    "# Architecture Overview",
    "",
    "## Overview",
    "This document describes the high-level architecture.",
    "",
    "## Components",
    "- **Frontend**: React SPA",
    "- **Backend**: Node.js + Express",
    "- **Database**: PostgreSQL 15",
    "- **Analytics**: Python data pipeline",
    "",
    "## Data Flow",
    "1. User interacts with the React dashboard.",
    "2. React calls the REST API.",
    "3. Node.js processes the request.",
    "4. Python analytics runs batch jobs.",
    "",
    "## Deployment",
    "All services are containerised with Docker.",
])
with open(os.path.join(docs_dir, "architecture.md"), "w") as f:
    f.write(md_content)

# ── DISTRACTOR files in UNSUPPORTED languages (must be IGNORED by the skill) ─
distractor_dir = os.path.join(project_root, "legacy")
os.makedirs(distractor_dir, exist_ok=True)

java_file = "\n".join([
    "public class LegacyProcessor {",
    "    public static void main(String[] args) {",
    "        System.out.println(\"Hello from Java\");",
    "    }",
    "    private int compute(int x) { return x * 2; }",
    "    private int compute2(int x) { return x * 3; }",
    "    private int compute3(int x) { return x * 4; }",
    "    private int compute4(int x) { return x * 5; }",
    "}",
])
with open(os.path.join(distractor_dir, "LegacyProcessor.java"), "w") as f:
    f.write(java_file)

cpp_file = "\n".join([
    "#include <iostream>",
    "#include <vector>",
    "int main() {",
    "    std::vector<int> v = {1,2,3,4,5};",
    "    for (auto x : v) std::cout << x << std::endl;",
    "    return 0;",
    "}",
])
with open(os.path.join(distractor_dir, "legacy.cpp"), "w") as f:
    f.write(cpp_file)

rb_file = "\n".join([
    "class OldScript",
    "  def initialize(name)",
    "    @name = name",
    "  end",
    "  def greet",
    "    puts \"Hello #{@name}\"",
    "  end",
    "end",
])
with open(os.path.join(distractor_dir, "old_script.rb"), "w") as f:
    f.write(rb_file)

go_file = "\n".join([
    "package main",
    "import \"fmt\"",
    "func main() {",
    "    fmt.Println(\"legacy go\")",
    "}",
])
with open(os.path.join(distractor_dir, "legacy.go"), "w") as f:
    f.write(go_file)

# ── node_modules stub (should be IGNORED by the skill) ───────────────────────
nm_dir = os.path.join(project_root, "node_modules", "some-lib")
os.makedirs(nm_dir, exist_ok=True)
with open(os.path.join(nm_dir, "index.js"), "w") as f:
    f.write("module.exports = {};\n// this file should be ignored\n")
with open(os.path.join(nm_dir, "README.md"), "w") as f:
    f.write("# some-lib\nIgnore me.\n")

# ── .git stub (should be IGNORED) ─────────────────────────────────────────────
git_dir = os.path.join(project_root, ".git")
os.makedirs(git_dir, exist_ok=True)
with open(os.path.join(git_dir, "config"), "w") as f:
    f.write("[core]\n\trepositoryformatversion = 0\n")

print("✅ Workspace generated successfully.")
print(f"   Workspace root: {WORKSPACE}")