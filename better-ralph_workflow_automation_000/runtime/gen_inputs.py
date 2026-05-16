#!/usr/bin/env python3
import os
import json
import subprocess
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(exist_ok=True)

# ── 1. Initialize a real git repo ──────────────────────────────────────────────
os.chdir(WORKSPACE)
subprocess.run(["git", "init"], check=True)
subprocess.run(["git", "config", "user.email", "ralph@test.local"], check=True)
subprocess.run(["git", "config", "user.name", "Better Ralph Test"], check=True)

# ── 2. Create the Node.js / TypeScript project structure ──────────────────────

# package.json with test, lint, typecheck scripts
package_json = {
    "name": "taskflow-cli",
    "version": "0.1.0",
    "description": "A CLI task management tool",
    "main": "dist/index.js",
    "scripts": {
        "build": "tsc",
        "test": "node tests/run_tests.js",
        "lint": "node tools/lint_check.js",
        "typecheck": "node tools/type_check.js"
    },
    "devDependencies": {}
}
(WORKSPACE / "package.json").write_text(json.dumps(package_json, indent=2))

# tsconfig.json
tsconfig = {
    "compilerOptions": {
        "target": "ES2020",
        "module": "commonjs",
        "outDir": "./dist",
        "rootDir": "./src",
        "strict": True,
        "esModuleInterop": True
    },
    "include": ["src/**/*"],
    "exclude": ["node_modules", "dist"]
}
(WORKSPACE / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

# ── 3. Source files ────────────────────────────────────────────────────────────

src = WORKSPACE / "src"
src.mkdir(exist_ok=True)

# src/types.ts
(src / "types.ts").write_text(textwrap.dedent("""\
    export type Priority = 'low' | 'medium' | 'high';

    export interface Task {
      id: string;
      title: string;
      description: string;
      priority: Priority;
      completed: boolean;
      createdAt: string;
      tags: string[];
    }

    export interface TaskStore {
      tasks: Task[];
    }
"""))

# src/store.ts
(src / "store.ts").write_text(textwrap.dedent("""\
    import { Task, TaskStore } from './types';
    import * as fs from 'fs';

    const STORE_PATH = './data/tasks.json';

    export function loadStore(): TaskStore {
      if (!fs.existsSync(STORE_PATH)) {
        return { tasks: [] };
      }
      const raw = fs.readFileSync(STORE_PATH, 'utf-8');
      return JSON.parse(raw) as TaskStore;
    }

    export function saveStore(store: TaskStore): void {
      fs.mkdirSync('./data', { recursive: true });
      fs.writeFileSync(STORE_PATH, JSON.stringify(store, null, 2));
    }

    export function getAllTasks(): Task[] {
      return loadStore().tasks;
    }

    export function addTask(task: Task): void {
      const store = loadStore();
      store.tasks.push(task);
      saveStore(store);
    }
"""))

# src/cli.ts — intentionally missing the filter function (story will add it)
(src / "cli.ts").write_text(textwrap.dedent("""\
    import { getAllTasks } from './store';
    import { Task, Priority } from './types';

    export function listTasks(): void {
      const tasks = getAllTasks();
      if (tasks.length === 0) {
        console.log('No tasks found.');
        return;
      }
      tasks.forEach(t => {
        const status = t.completed ? '[x]' : '[ ]';
        console.log(`${status} [${t.priority.toUpperCase()}] ${t.id}: ${t.title}`);
      });
    }

    // TODO: filterTasksByPriority will be added in US-003
"""))

# src/index.ts
(src / "index.ts").write_text(textwrap.dedent("""\
    import { listTasks } from './cli';

    const command = process.argv[2];

    if (command === 'list') {
      listTasks();
    } else {
      console.log('Usage: taskflow <list|filter>');
    }
"""))

# ── 4. Distractor files (10+) ─────────────────────────────────────────────────

docs = WORKSPACE / "docs"
docs.mkdir(exist_ok=True)
(docs / "architecture.md").write_text("# Architecture\n\nTaskflow uses a flat JSON store.\n")
(docs / "api_reference.md").write_text("# API Reference\n\nSee src/cli.ts for exported functions.\n")
(docs / "roadmap.md").write_text("# Roadmap\n\n- v0.2: filtering\n- v0.3: tags\n")

config_dir = WORKSPACE / "config"
config_dir.mkdir(exist_ok=True)
(config_dir / "default.json").write_text('{"maxTasks": 1000, "defaultPriority": "medium"}\n')
(config_dir / "test.json").write_text('{"maxTasks": 100, "defaultPriority": "low"}\n')

scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(exist_ok=True)
(scripts_dir / "seed_data.js").write_text(textwrap.dedent("""\
    const fs = require('fs');
    const data = { tasks: [
      { id: 't-001', title: 'Buy groceries', description: '', priority: 'low', completed: false, createdAt: '2024-01-01', tags: [] }
    ]};
    fs.mkdirSync('./data', { recursive: true });
    fs.writeFileSync('./data/tasks.json', JSON.stringify(data, null, 2));
    console.log('Seeded.');
"""))
(scripts_dir / "clean.sh").write_text("#!/bin/bash\nrm -rf dist/ data/\necho 'Cleaned.'\n")

data_dir = WORKSPACE / "data"
data_dir.mkdir(exist_ok=True)
(data_dir / "tasks.json").write_text(json.dumps({
    "tasks": [
        {
            "id": "t-001",
            "title": "Buy groceries",
            "description": "Milk, eggs, bread",
            "priority": "low",
            "completed": False,
            "createdAt": "2024-03-01",
            "tags": ["personal"]
        },
        {
            "id": "t-002",
            "title": "Write report",
            "description": "Q1 financial report",
            "priority": "high",
            "completed": False,
            "createdAt": "2024-03-02",
            "tags": ["work"]
        }
    ]
}, indent=2))

# Tests directory (the tests check for the filter function)
tests_dir = WORKSPACE / "tests"
tests_dir.mkdir(exist_ok=True)

# A test runner script — it looks for filterTasksByPriority in src/cli.ts
(tests_dir / "run_tests.js").write_text(textwrap.dedent("""\
    const fs = require('fs');
    const path = require('path');

    let passed = 0;
    let failed = 0;

    function assert(condition, message) {
      if (condition) {
        console.log('  PASS:', message);
        passed++;
      } else {
        console.error('  FAIL:', message);
        failed++;
      }
    }

    // Test: filterTasksByPriority is exported from src/cli.ts
    const cliSrc = fs.readFileSync(path.join(__dirname, '../src/cli.ts'), 'utf-8');

    assert(
      cliSrc.includes('export function filterTasksByPriority'),
      'filterTasksByPriority is exported from cli.ts'
    );

    assert(
      cliSrc.includes('Priority'),
      'filterTasksByPriority uses Priority type'
    );

    // Test: The function signature takes a Priority parameter
    assert(
      /filterTasksByPriority\s*\(\s*\w+\s*:\s*Priority/.test(cliSrc),
      'filterTasksByPriority accepts a Priority typed parameter'
    );

    // Test: Returns filtered tasks (returns Task[] or filters from getAllTasks)
    assert(
      cliSrc.includes('filter(') || cliSrc.includes('.filter('),
      'filterTasksByPriority uses array filter'
    );

    console.log(`\\nResults: ${passed} passed, ${failed} failed`);
    if (failed > 0) {
      process.exit(1);
    }
"""))

# Tools directory (lint and typecheck stubs that always pass once filter exists)
tools_dir = WORKSPACE / "tools"
tools_dir.mkdir(exist_ok=True)

(tools_dir / "lint_check.js").write_text(textwrap.dedent("""\
    const fs = require('fs');

    const cliSrc = fs.readFileSync('./src/cli.ts', 'utf-8');

    // Lint rule: no TODO comments allowed in final code
    // But we only enforce it for lines that are NOT the placeholder comment
    const lines = cliSrc.split('\\n');
    const badLines = lines.filter(l => l.trim().startsWith('// TODO:'));

    if (badLines.length > 0) {
      console.error('Lint error: TODO comments found:');
      badLines.forEach(l => console.error(' ', l.trim()));
      process.exit(1);
    }

    console.log('Lint passed.');
"""))

(tools_dir / "type_check.js").write_text(textwrap.dedent("""\
    const fs = require('fs');

    // Simplified type check: ensure no 'any' type is used in src/
    const files = ['./src/cli.ts', './src/store.ts', './src/types.ts', './src/index.ts'];
    let errors = 0;

    files.forEach(f => {
      if (!fs.existsSync(f)) {
        console.error('Typecheck error: missing file', f);
        errors++;
        return;
      }
      const src = fs.readFileSync(f, 'utf-8');
      if (src.includes(': any') || src.includes('<any>')) {
        console.error(`Typecheck error: 'any' type found in ${f}`);
        errors++;
      }
    });

    if (errors > 0) {
      process.exit(1);
    }
    console.log('Typecheck passed.');
"""))

# ── 5. prd.json — the key file with a TRICKY priority ordering ────────────────
# TRAP: Array order does NOT match priority order.
# US-004 is first in array but priority=4
# US-001 is second but priority=1 (passes=true already — skip it)
# US-003 is third but priority=3
# US-002 is fourth but priority=2  <-- This is the correct next story!
# Agent must sort by priority ascending, skip passes=true, pick US-002

prd = {
    "project": "TaskFlow CLI",
    "branchName": "ralph/filter-feature",
    "description": "Add task filtering capabilities to the TaskFlow CLI",
    "userStories": [
        {
            "id": "US-004",
            "title": "Add tag-based filtering",
            "description": "As a user, I want to filter tasks by tag so that I can see only relevant tasks.",
            "acceptanceCriteria": [
                "filterTasksByTag function is exported from cli.ts",
                "Function accepts a string tag parameter and returns matching Task[]",
                "Tests pass",
                "Lint passes",
                "Typecheck passes"
            ],
            "priority": 4,
            "passes": False,
            "notes": "Depends on US-003"
        },
        {
            "id": "US-001",
            "title": "Setup TypeScript project structure",
            "description": "As a developer, I want the project to have a proper TypeScript structure so that we can build reliably.",
            "acceptanceCriteria": [
                "tsconfig.json exists",
                "src/types.ts defines Task and Priority types",
                "Typecheck passes"
            ],
            "priority": 1,
            "passes": True,
            "notes": "Already done"
        },
        {
            "id": "US-003",
            "title": "Export filterTasksByPriority from cli module",
            "description": "As a user, I want to filter tasks by priority so that I can focus on what matters most.",
            "acceptanceCriteria": [
                "filterTasksByPriority is exported from src/cli.ts",
                "Function accepts a Priority typed parameter",
                "Function returns Task[] filtered by the given priority",
                "Uses array filter method",
                "Tests pass",
                "Lint passes",
                "Typecheck passes"
            ],
            "priority": 3,
            "passes": False,
            "notes": ""
        },
        {
            "id": "US-002",
            "title": "Remove placeholder TODO comment from cli.ts",
            "description": "As a developer, I want the codebase to be clean with no stale TODO comments so that the linter passes.",
            "acceptanceCriteria": [
                "No TODO comments remain in src/cli.ts",
                "Lint passes",
                "Typecheck passes",
                "Tests pass"
            ],
            "priority": 2,
            "passes": False,
            "notes": "The TODO comment for filterTasksByPriority must be removed"
        }
    ]
}

(WORKSPACE / "prd.json").write_text(json.dumps(prd, indent=2))

# ── 6. progress.txt — pre-existing file with Codebase Patterns ───────────────
# TRAP: Agent must APPEND to this, not overwrite it
progress_content = textwrap.dedent("""\
    # Better Ralph Progress

    ## Codebase Patterns
    - Tests are plain Node.js scripts in tests/run_tests.js — no jest/mocha needed
    - Lint check is in tools/lint_check.js — checks for TODO comments
    - Typecheck is in tools/type_check.js — forbids 'any' type usage
    - Quality check commands: npm test, npm run lint, npm run typecheck

    ---

    ## 2024-01-15T10:00:00 - US-001
    - Implemented TypeScript project structure with types.ts defining Task and Priority interfaces.
    - Files changed: src/types.ts, tsconfig.json, package.json
    - **Learnings for future iterations:**
      - This codebase uses plain Node.js scripts for tests, not a testing framework
      - Always run all three quality checks before committing
    ---
""")
(WORKSPACE / "progress.txt").write_text(progress_content)

# ── 7. Initial git commit (so we have a clean history to compare against) ─────
subprocess.run(["git", "add", "-A"], cwd=WORKSPACE, check=True)
subprocess.run(
    ["git", "commit", "-m", "chore: initial project scaffold"],
    cwd=WORKSPACE, check=True
)

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}:")
for f in sorted(WORKSPACE.rglob("*")):
    if ".git" not in str(f) and f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")