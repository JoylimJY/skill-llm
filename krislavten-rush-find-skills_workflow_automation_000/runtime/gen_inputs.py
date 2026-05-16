#!/usr/bin/env python3
import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Create deeply nested distractor file structure ---
dirs = [
    "src/components/ui",
    "src/components/forms",
    "src/pages/dashboard",
    "src/pages/settings",
    "src/utils",
    "src/api/endpoints",
    "tests/unit",
    "tests/integration",
    "docs/architecture",
    ".github/workflows",   # distractor: .github/ alone doesn't imply copilot
    ".cursor/themes",      # TRAP: cursor dir exists but should be OVERRIDDEN by skills.json
    "scripts/build",
    "scripts/lint",
    "config/environments",
    "node_modules/.cache",  # distractor
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "src/components/ui/Button.tsx": "export const Button = ({children}) => <button>{children}</button>;\n",
    "src/components/ui/Modal.tsx": "export const Modal = ({open, children}) => open ? <div>{children}</div> : null;\n",
    "src/components/forms/LoginForm.tsx": "export const LoginForm = () => <form><input type='email'/><button>Login</button></form>;\n",
    "src/pages/dashboard/index.tsx": "import React from 'react';\nexport default function Dashboard() { return <div>Dashboard</div>; }\n",
    "src/pages/settings/index.tsx": "import React from 'react';\nexport default function Settings() { return <div>Settings</div>; }\n",
    "src/utils/helpers.ts": "export const formatDate = (d: Date) => d.toISOString().split('T')[0];\n",
    "src/api/endpoints/users.ts": "export const getUsers = async () => fetch('/api/users').then(r => r.json());\n",
    "tests/unit/helpers.test.ts": "import {formatDate} from '../../src/utils/helpers';\ntest('formatDate', () => expect(formatDate(new Date('2024-01-01'))).toBe('2024-01-01'));\n",
    "tests/integration/api.test.ts": "describe('API', () => { it('returns users', async () => { expect(true).toBe(true); }); });\n",
    "docs/architecture/overview.md": "# Architecture Overview\nThis project uses a micro-frontend architecture with React.\n",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n",
    "scripts/build/webpack.config.js": "module.exports = { entry: './src/index.tsx', output: { path: __dirname + '/dist' } };\n",
    "scripts/lint/.eslintrc.json": json.dumps({"extends": ["eslint:recommended"], "rules": {"no-unused-vars": "warn"}}, indent=2) + "\n",
    "config/environments/production.env": "NODE_ENV=production\nAPI_URL=https://api.example.com\nLOG_LEVEL=error\n",
    "config/environments/staging.env": "NODE_ENV=staging\nAPI_URL=https://staging.api.example.com\nLOG_LEVEL=debug\n",
    # Cursor dir marker file - this is the TRAP
    ".cursor/themes/dark.json": json.dumps({"theme": "dark", "colors": {"background": "#1e1e1e", "foreground": "#d4d4d4"}}, indent=2) + "\n",
    # Distractor: a skills.json that looks incomplete/broken in a subdirectory
    "src/skills.json": json.dumps({"version": "1.0", "skills": []}, indent=2) + "\n",
    "node_modules/.cache/README": "Cache directory - do not edit\n",
    "package.json": json.dumps({
        "name": "devops-dashboard",
        "version": "1.0.0",
        "description": "Internal DevOps dashboard application",
        "scripts": {
            "build": "webpack",
            "test": "jest",
            "lint": "eslint src/"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        },
        "devDependencies": {
            "typescript": "^5.0.0",
            "webpack": "^5.80.0",
            "jest": "^29.5.0"
        }
    }, indent=2) + "\n",
    "tsconfig.json": json.dumps({
        "compilerOptions": {
            "target": "ES2020",
            "module": "commonjs",
            "jsx": "react",
            "strict": True,
            "outDir": "./dist"
        },
        "include": ["src/**/*"],
        "exclude": ["node_modules", "dist"]
    }, indent=2) + "\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE KEY CONFIG: skills.json in workspace root ---
# This should override .cursor/ directory detection (Priority 2 > Priority 3)
skills_config = {
    "version": "1.0.0",
    "defaults": {
        "targetAgents": ["claude-code", "codex"],
        "publishRegistry": "https://rush.zhenguanyu.com/"
    },
    "skills": []
}

with open(os.path.join(workspace, "skills.json"), "w") as f:
    json.dump(skills_config, f, indent=2)
    f.write("\n")

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1} files")
print("Key trap: .cursor/ directory exists but skills.json overrides targetAgents to claude-code and codex")