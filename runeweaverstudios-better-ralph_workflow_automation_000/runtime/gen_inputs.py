#!/usr/bin/env python3
import os
import json
import subprocess
import random

random.seed(42)

workspace = "/workspace"
os.chdir(workspace)

# ── 1. Init git repo on `main` ──────────────────────────────────────────────
subprocess.run(["git", "init"], check=True)
subprocess.run(["git", "checkout", "-b", "main"], check=True)

# ── 2. package.json ──────────────────────────────────────────────────────────
package_json = {
    "name": "task-manager-cli",
    "version": "2.4.1",
    "description": "A CLI tool for managing tasks",
    "main": "src/index.js",
    "scripts": {
        "start": "node src/index.js",
        "test": "jest --testPathPattern=test/",
        "lint": "eslint src/ --max-warnings 0"
    },
    "bin": {
        "taskmgr": "./src/cli.js"
    },
    "dependencies": {
        "commander": "^10.0.1"
    },
    "devDependencies": {
        "jest": "^29.5.0",
        "eslint": "^8.42.0"
    }
}
with open("package.json", "w") as f:
    json.dump(package_json, f, indent=2)

# ── 3. .eslintrc.json ────────────────────────────────────────────────────────
eslint_config = {
    "env": {"node": True, "es2021": True, "jest": True},
    "parserOptions": {"ecmaVersion": 2021, "sourceType": "script"},
    "rules": {
        "no-unused-vars": "warn",
        "no-console": "off",
        "semi": ["error", "always"],
        "quotes": ["error", "single"]
    }
}
with open(".eslintrc.json", "w") as f:
    json.dump(eslint_config, f, indent=2)

# ── 4. jest.config.js ────────────────────────────────────────────────────────
with open("jest.config.js", "w") as f:
    f.write("module.exports = { testEnvironment: 'node', testTimeout: 10000 };\n")

# ── 5. src/ directory ────────────────────────────────────────────────────────
os.makedirs("src", exist_ok=True)

# src/index.js  (entry point, not what the story touches)
with open("src/index.js", "w") as f:
    f.write("""\
'use strict';

const { createTaskManager } = require('./taskManager');

const tm = createTaskManager();
tm.run(process.argv.slice(2));
""")

# src/taskManager.js
with open("src/taskManager.js", "w") as f:
    f.write("""\
'use strict';

function createTaskManager() {
  const tasks = [];

  function addTask(name) {
    tasks.push({ id: tasks.length + 1, name, done: false });
  }

  function listTasks() {
    return tasks.slice();
  }

  function completeTask(id) {
    const task = tasks.find(t => t.id === id);
    if (task) task.done = true;
  }

  function run(args) {
    if (args[0] === 'add') {
      addTask(args.slice(1).join(' '));
      console.log('Task added.');
    } else if (args[0] === 'list') {
      listTasks().forEach(t => console.log(`[${t.done ? 'x' : ' '}] ${t.id}: ${t.name}`));
    } else if (args[0] === 'complete') {
      completeTask(Number(args[1]));
      console.log('Task completed.');
    } else {
      console.log('Unknown command.');
    }
  }

  return { addTask, listTasks, completeTask, run };
}

module.exports = { createTaskManager };
""")

# src/cli.js  — intentionally has NO --version flag yet (that's what US-001 adds)
with open("src/cli.js", "w") as f:
    f.write("""\
#!/usr/bin/env node
'use strict';

const { createTaskManager } = require('./taskManager');

const args = process.argv.slice(2);
const tm = createTaskManager();
tm.run(args);
""")

# src/utils.js  (distractor)
with open("src/utils.js", "w") as f:
    f.write("""\
'use strict';

function formatDate(d) {
  return d.toISOString().split('T')[0];
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

module.exports = { formatDate, capitalize };
""")

# src/config.js  (distractor)
with open("src/config.js", "w") as f:
    f.write("""\
'use strict';

const DEFAULT_PORT = 3000;
const MAX_TASKS = 500;

module.exports = { DEFAULT_PORT, MAX_TASKS };
""")

# src/logger.js  (distractor)
with open("src/logger.js", "w") as f:
    f.write("""\
'use strict';

function log(level, msg) {
  process.stderr.write(`[${level.toUpperCase()}] ${msg}\\n`);
}

module.exports = { log };
""")

# ── 6. test/ directory ───────────────────────────────────────────────────────
os.makedirs("test", exist_ok=True)

# test/cli.test.js — tests the --version flag (will FAIL until agent implements it)
with open("test/cli.test.js", "w") as f:
    f.write("""\
'use strict';

const { execSync } = require('child_process');
const path = require('path');
const pkg = require('../package.json');

const CLI = path.join(__dirname, '..', 'src', 'cli.js');

describe('CLI --version flag', () => {
  test('prints the version from package.json and exits 0', () => {
    let output;
    try {
      output = execSync(`node ${CLI} --version`, { encoding: 'utf8' });
    } catch (err) {
      throw new Error(`CLI exited with non-zero: ${err.message}`);
    }
    expect(output.trim()).toBe(pkg.version);
  });

  test('--version output matches semver format', () => {
    const output = execSync(`node ${CLI} --version`, { encoding: 'utf8' });
    expect(output.trim()).toMatch(/^\\d+\\.\\d+\\.\\d+/);
  });
});

describe('CLI existing commands still work', () => {
  test('list command does not crash', () => {
    expect(() => execSync(`node ${CLI} list`, { encoding: 'utf8' })).not.toThrow();
  });
});
""")

# test/taskManager.test.js  (distractor, already passing)
with open("test/taskManager.test.js", "w") as f:
    f.write("""\
'use strict';

const { createTaskManager } = require('../src/taskManager');

describe('TaskManager', () => {
  test('add and list tasks', () => {
    const tm = createTaskManager();
    tm.addTask('Buy milk');
    const tasks = tm.listTasks();
    expect(tasks).toHaveLength(1);
    expect(tasks[0].name).toBe('Buy milk');
  });

  test('complete a task', () => {
    const tm = createTaskManager();
    tm.addTask('Write tests');
    tm.completeTask(1);
    expect(tm.listTasks()[0].done).toBe(true);
  });
});
""")

# test/utils.test.js  (distractor, already passing)
with open("test/utils.test.js", "w") as f:
    f.write("""\
'use strict';

const { formatDate, capitalize } = require('../src/utils');

describe('utils', () => {
  test('formatDate returns YYYY-MM-DD', () => {
    const d = new Date('2024-03-15T12:00:00Z');
    expect(formatDate(d)).toBe('2024-03-15');
  });

  test('capitalize works', () => {
    expect(capitalize('hello')).toBe('Hello');
  });
});
""")

# ── 7. distractor files ──────────────────────────────────────────────────────
os.makedirs("docs", exist_ok=True)
with open("docs/architecture.md", "w") as f:
    f.write("# Architecture\n\nThis is a monolithic CLI application.\n\nSee `src/` for source code.\n")

with open("docs/api.md", "w") as f:
    f.write("# API Reference\n\nNo public API yet.\n")

os.makedirs("scripts", exist_ok=True)
with open("scripts/build.sh", "w") as f:
    f.write("#!/bin/bash\nnpm run lint && npm test\n")

with open("scripts/deploy.sh", "w") as f:
    f.write("#!/bin/bash\necho 'No deploy configured'\n")

with open(".gitignore", "w") as f:
    f.write("node_modules/\n.env\n*.log\ncoverage/\n")

with open(".nvmrc", "w") as f:
    f.write("18\n")

os.makedirs("fixtures", exist_ok=True)
with open("fixtures/sample_tasks.json", "w") as f:
    json.dump([
        {"id": 1, "name": "Review PR #42", "done": False},
        {"id": 2, "name": "Deploy staging", "done": True}
    ], f, indent=2)

with open("fixtures/empty_tasks.json", "w") as f:
    json.dump([], f)

os.makedirs("src/handlers", exist_ok=True)
with open("src/handlers/addHandler.js", "w") as f:
    f.write("""\
'use strict';

function addHandler(tm, args) {
  const name = args.slice(1).join(' ');
  if (!name) { console.error('Task name required.'); process.exit(1); }
  tm.addTask(name);
  console.log('Task added.');
}

module.exports = { addHandler };
""")

with open("src/handlers/listHandler.js", "w") as f:
    f.write("""\
'use strict';

function listHandler(tm) {
  const tasks = tm.listTasks();
  if (tasks.length === 0) { console.log('No tasks.'); return; }
  tasks.forEach(t => console.log(`[${t.done ? 'x' : ' '}] ${t.id}: ${t.name}`));
}

module.exports = { listHandler };
""")

# ── 8. prd.json  (KEY: US-002 appears first in array but has priority 2; US-001 has priority 1) ──
prd = {
    "project": "TaskManagerCLI",
    "branchName": "ralph/task-manager-features",
    "description": "Add missing CLI capabilities to the task manager tool.",
    "userStories": [
        {
            "id": "US-002",
            "title": "Add --help flag with usage summary",
            "description": "As a developer, I want to run `taskmgr --help` so that I can see all available commands without reading the source.",
            "acceptanceCriteria": [
                "Running `node src/cli.js --help` exits with code 0",
                "Output includes the word 'Usage'",
                "Tests pass"
            ],
            "priority": 2,
            "passes": False,
            "notes": "Implement after --version is in place."
        },
        {
            "id": "US-001",
            "title": "Add --version flag to CLI",
            "description": "As a developer, I want to run `taskmgr --version` so that I can confirm which version of the tool is installed.",
            "acceptanceCriteria": [
                "Running `node src/cli.js --version` prints the version string from package.json",
                "The process exits with code 0",
                "Output matches semver format",
                "All existing tests continue to pass",
                "npm run lint passes with no errors"
            ],
            "priority": 1,
            "passes": False,
            "notes": ""
        },
        {
            "id": "US-003",
            "title": "Colorize task list output",
            "description": "As a user, I want completed tasks shown in green and pending in yellow.",
            "acceptanceCriteria": [
                "Completed tasks shown with green ANSI color",
                "Pending tasks shown with yellow ANSI color",
                "Tests pass"
            ],
            "priority": 3,
            "passes": True,
            "notes": "Already done in a previous sprint."
        }
    ]
}
with open("prd.json", "w") as f:
    json.dump(prd, f, indent=2)

# ── 9. progress.txt  (has Codebase Patterns section — CRITICAL for agent to read) ──
progress_txt = """\
# Better Ralph Progress

## Codebase Patterns
- Use CommonJS `module.exports` / `require()` for ALL exports and imports. This codebase does NOT use ES module syntax (`import`/`export default`). ESLint is configured with `sourceType: script` and will error on ES module syntax.
- Read version from `package.json` using `require('../package.json').version` or equivalent `require()` call.
- Tests invoke the CLI via `child_process.execSync` with `node src/cli.js <flag>`, so the flag must be handled in `src/cli.js` directly.
- Always run `npm test` AND `npm run lint` before committing — both must pass.

---

## 2024-01-10T09:15:00 - US-003
- Implemented ANSI color output for task list using escape codes in listHandler.js.
- Files changed: src/handlers/listHandler.js, test/listHandler.test.js
- **Learnings for future iterations:**
  - ANSI escape codes work fine in Node 18 terminals; no extra library needed.
  - Remember to update both the handler and its test when changing output format.
---
"""
with open("progress.txt", "w") as f:
    f.write(progress_txt)

# ── 10. Install npm deps & make initial commit ───────────────────────────────
subprocess.run(["npm", "install", "--registry", "https://registry.npmjs.org"], check=True)

# Stage everything and make initial commit on main
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "chore: initial project setup"], check=True)

print("✅ Workspace generated successfully.")
print(f"   Current branch: main")
print(f"   prd.json has US-001 (priority:1, passes:false) as the target story")
print(f"   progress.txt has Codebase Patterns section")