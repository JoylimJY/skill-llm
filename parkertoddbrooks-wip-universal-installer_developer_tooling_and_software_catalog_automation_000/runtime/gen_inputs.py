import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── 1. Distractor directories ──────────────────────────────────────────────────

distractor_repos = [
    "legacy-auth-service",
    "data-pipeline-v2",
    "frontend-dashboard",
    "infra-terraform-modules",
    "ml-feature-store",
]

for repo in distractor_repos:
    repo_path = os.path.join(WORKSPACE, repo)
    os.makedirs(repo_path, exist_ok=True)
    # Give each distractor a package.json but WITHOUT the correct interface markers
    pkg = {
        "name": repo,
        "version": "1.0.0",
        "description": f"Internal {repo} service",
        "scripts": {"start": "node index.js", "test": "jest"},
        "dependencies": {
            "express": "^4.18.0",
            "lodash": "^4.17.21",
        }
    }
    with open(os.path.join(repo_path, "package.json"), "w") as f:
        json.dump(pkg, f, indent=2)
    # Add some source files
    with open(os.path.join(repo_path, "index.js"), "w") as f:
        f.write(f"// {repo} main entry\nconsole.log('Running {repo}');\n")
    with open(os.path.join(repo_path, "README.md"), "w") as f:
        f.write(f"# {repo}\nInternal service. Do not redistribute.\n")
    # Add nested subdirs
    src_dir = os.path.join(repo_path, "src")
    os.makedirs(src_dir, exist_ok=True)
    with open(os.path.join(src_dir, "utils.js"), "w") as f:
        f.write("module.exports = { helper: () => {} };\n")
    test_dir = os.path.join(repo_path, "tests")
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, "index.test.js"), "w") as f:
        f.write("test('placeholder', () => expect(1).toBe(1));\n")

# ── 2. Distractor config/log files at workspace root ──────────────────────────

with open(os.path.join(WORKSPACE, "deployment.log"), "w") as f:
    f.write("2024-01-15 10:23:01 INFO  Deploying legacy-auth-service v2.3.1\n")
    f.write("2024-01-15 10:24:10 ERROR data-pipeline-v2 healthcheck failed\n")
    f.write("2024-01-15 10:25:00 INFO  Rollback initiated\n")

with open(os.path.join(WORKSPACE, "ci-config.yml"), "w") as f:
    f.write("""stages:
  - lint
  - test
  - deploy
variables:
  NODE_VERSION: "20"
  NPM_REGISTRY: "https://registry.npmjs.org"
""")

with open(os.path.join(WORKSPACE, "org-catalog.json"), "w") as f:
    json.dump({
        "catalog_version": "3.0",
        "registered_tools": [
            {"name": "legacy-auth-service", "interfaces": []},
            {"name": "data-pipeline-v2", "interfaces": []},
        ]
    }, f, indent=2)

# ── 3. The candidate repo: INCOMPLETE / BROKEN ────────────────────────────────
# The agent must make this repo expose ALL 6 Universal Interfaces.

candidate_path = os.path.join(WORKSPACE, "candidate-tool")
os.makedirs(candidate_path, exist_ok=True)

# package.json is present but MISSING 'bin' and 'main'/'exports' fields
# (no CLI or Module interface will be detected without them)
broken_pkg = {
    "name": "@acme/candidate-tool",
    "version": "0.3.0",
    "description": "Acme internal developer productivity tool",
    "license": "MIT",
    "author": "Acme Platform Team",
    "scripts": {
        "test": "node test.mjs"
    },
    "dependencies": {
        "chalk": "^5.3.0"
    }
    # NOTE: No "bin", no "main", no "exports" — agent must add these
}
with open(os.path.join(candidate_path, "package.json"), "w") as f:
    json.dump(broken_pkg, f, indent=2)

# A source file exists but is not wired up
os.makedirs(os.path.join(candidate_path, "src"), exist_ok=True)
with open(os.path.join(candidate_path, "src", "index.mjs"), "w") as f:
    f.write("""// candidate-tool main module
export function run(args) {
  console.log('candidate-tool running with', args);
}
export default { run };
""")

with open(os.path.join(candidate_path, "src", "cli.mjs"), "w") as f:
    f.write("""#!/usr/bin/env node
import { run } from './index.mjs';
run(process.argv.slice(2));
""")

# A test file
with open(os.path.join(candidate_path, "test.mjs"), "w") as f:
    f.write("""import { run } from './src/index.mjs';
console.log('Tests passing');
""")

# An unrelated config that might confuse the agent
with open(os.path.join(candidate_path, ".eslintrc.json"), "w") as f:
    json.dump({"env": {"es2022": True, "node": True}, "rules": {}}, f, indent=2)

with open(os.path.join(candidate_path, ".gitignore"), "w") as f:
    f.write("node_modules/\n.env\n*.log\n")

# A misleadingly-named file that is NOT the correct interface marker
# (agent might mistake this for mcp-server.mjs but it's wrong filename)
with open(os.path.join(candidate_path, "mcp_server.js"), "w") as f:
    f.write("// placeholder - wrong filename, not detected by universal installer\n")

# Another misleading file - wrong name for openclaw
with open(os.path.join(candidate_path, "plugin.json"), "w") as f:
    json.dump({"name": "candidate-tool-plugin", "type": "openclaw"}, f, indent=2)

# Changelog as additional noise
with open(os.path.join(candidate_path, "CHANGELOG.md"), "w") as f:
    f.write("""# Changelog

## 0.3.0
- Initial internal release
- Added basic CLI scaffolding

## 0.2.0
- Prototype phase
""")

print("Workspace generated successfully.")
print(f"Candidate repo: {candidate_path}")
print("Status: candidate-tool is INCOMPLETE - missing interface markers for all 6 Universal Interface types.")