import os
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Create the solo-factory tool directory (simulates installed tool)
sf = workspace / "solo-factory"
(sf / "templates" / "stacks").mkdir(parents=True, exist_ok=True)
(sf / "references").mkdir(parents=True, exist_ok=True)

# ── questions.md (the reference file agents MUST read)
questions_md = sf / "references" / "questions.md"
questions_md.write_text(textwrap.dedent("""\
# Questions Reference

## Round 0: Org Defaults

0.1 What is your primary org domain? (e.g., acme.com)
    key: org_domain

0.2 What is your Apple Developer Team ID? (leave blank if none)
    key: apple_dev_team

0.3 What is your GitHub org or username?
    key: github_org

0.4 Where do you store local projects? (absolute path)
    key: projects_dir

0.5 What is the repo name for your shared knowledge base? (leave blank if none)
    key: knowledge_base_repo

## Round 1: Philosophy & Values

1.1 What is your primary mission as a founder? (1–2 sentences)
    key: mission

1.2 Who is your target customer, in one sentence?
    key: target_customer

1.3 What is your #1 constraint right now? (time / money / focus / team)
    key: primary_constraint

1.4 What does success look like in 12 months?
    key: success_12mo

## Round 2: Development Preferences

2.1 What is your preferred code review style? (solo / async-team / pair)
    key: review_style

2.2 Do you prefer typed or dynamic languages for new projects? (typed / dynamic / both)
    key: type_preference

2.3 How do you handle technical debt? (pay-as-you-go / scheduled sprints / tolerate-it)
    key: tech_debt_style

2.4 What is your preferred testing philosophy? (tdd / bdd / test-after / minimal)
    key: testing_philosophy

## Round 3: Decision Style & Stacks

3.1 How do you make major architectural decisions? (solo-fast / consult-then-decide / data-driven)
    key: decision_style

3.2 What is your risk tolerance for adopting new tech? (low / medium / high)
    key: risk_tolerance

3.3 Which stacks do you want pre-configured? (comma-separated list)
    Available: nextjs-supabase, python-api, react-native-expo, electron-app, fastapi-postgres
    key: selected_stacks
"""))

# ── generation-rules.md
gen_rules_md = sf / "references" / "generation-rules.md"
gen_rules_md.write_text(textwrap.dedent("""\
# Generation Rules

## Template Source Locations

All template files live in `solo-factory/templates/`.
Stack YAML templates live in `solo-factory/templates/stacks/`.

## Output File Structure

### ~/.solo-factory/defaults.yaml
Populated from Round 0 answers. Use exact keys: org_domain, apple_dev_team, github_org, projects_dir, knowledge_base_repo.
Header comment MUST be:
```
# Solo Factory — org defaults
# Used by /scaffold and other skills for placeholder replacement.
# Re-run /init to update these values.
```

### .solo/manifest.md
Header: `# Founder Manifest`
Sections (in order):
1. `## Mission` — verbatim answer to 1.1
2. `## Target Customer` — verbatim answer to 1.2
3. `## Primary Constraint` — verbatim answer to 1.3
4. `## 12-Month Vision` — verbatim answer to 1.4

### .solo/stream-framework.md
Header: `# STREAM Framework`
Sections (in order):
1. `## Decision Style` — verbatim answer to 3.1
2. `## Risk Tolerance` — verbatim answer to 3.2
3. `## Calibration Notes` — one sentence summarizing the founder's decision posture based on decision_style and risk_tolerance values.
   Rules:
   - solo-fast + high   → "Move fast, trust your gut, validate post-launch."
   - solo-fast + medium → "Move fast but gut-check against data before shipping."
   - solo-fast + low    → "Move fast on low-stakes, pause on irreversible decisions."
   - consult-then-decide + high   → "Gather input quickly, then commit fully."
   - consult-then-decide + medium → "Seek one trusted voice, then decide with conviction."
   - consult-then-decide + low    → "Consult broadly, document rationale, minimize regret."
   - data-driven + high   → "Let metrics lead, but don't wait for perfect data."
   - data-driven + medium → "Run lightweight experiments before committing."
   - data-driven + low    → "Require statistically significant signals before any pivot."

### .solo/dev-principles.md
Header: `# Dev Principles`
Sections (in order):
1. `## Code Review Style` — verbatim answer to 2.1
2. `## Type Preference` — verbatim answer to 2.2
3. `## Tech Debt Approach` — verbatim answer to 2.3
4. `## Testing Philosophy` — verbatim answer to 2.4

### .solo/stacks/ (directory)
For each stack name in selected_stacks (comma-separated, stripped), copy the corresponding YAML from
`solo-factory/templates/stacks/<stack-name>.yaml` into `.solo/stacks/<stack-name>.yaml`.
If the source template does not exist, skip that stack silently.

## Edge Cases

- If apple_dev_team is blank or "none", write empty string for that key.
- If knowledge_base_repo is blank or "none", write empty string for that key.
- Strip leading/trailing whitespace from all answers before writing.
- selected_stacks: split on comma, strip each name, lowercase, skip unknown stacks.
- All .solo/ files use Unix line endings (LF).
"""))

# ── Stack template YAMLs
stacks = {
    "nextjs-supabase": """\
name: nextjs-supabase
version: "1.0"
framework: Next.js
backend: Supabase
language: TypeScript
features:
  - auth
  - realtime
  - storage
bundle_id_placeholder: "<org_domain>"
""",
    "python-api": """\
name: python-api
version: "1.0"
framework: FastAPI
backend: PostgreSQL
language: Python
features:
  - rest
  - openapi
  - jwt-auth
bundle_id_placeholder: "<org_domain>"
""",
    "react-native-expo": """\
name: react-native-expo
version: "1.0"
framework: React Native
toolchain: Expo
language: TypeScript
features:
  - ios
  - android
  - eas-build
apple_team_placeholder: "<apple_dev_team>"
""",
    "electron-app": """\
name: electron-app
version: "1.0"
framework: Electron
language: TypeScript
features:
  - auto-update
  - code-signing
""",
    "fastapi-postgres": """\
name: fastapi-postgres
version: "1.0"
framework: FastAPI
backend: PostgreSQL
language: Python
features:
  - alembic-migrations
  - sqlalchemy
  - pytest
""",
}
for name, content in stacks.items():
    (sf / "templates" / "stacks" / f"{name}.yaml").write_text(content)

# ── The main SKILL.md
skill_md = workspace / "SKILL.md"
skill_md.write_text(textwrap.dedent("""\
---
name: solo-init
description: One-time founder onboarding — generates personalized manifest, STREAM calibration, dev principles, and stack selection.
license: MIT
metadata:
  author: fortunto2
  version: "2.1.1"
  openclaw:
    emoji: "🎬"
allowed-tools: Read, Grep, Bash, Glob, Write, Edit, AskUserQuestion
argument-hint: "[project-path]"
---

# /init

One-time founder onboarding. Asks key questions, generates personalized configuration files. Everything stored as readable markdown/YAML — edit anytime.

Two layers of config:
- **`~/.solo-factory/defaults.yaml`** — org-level (bundle IDs, GitHub org, Apple Team ID). Shared across all projects.
- **`.solo/`** in project — founder philosophy, dev principles, STREAM calibration, selected stacks. Per-project but usually the same.

The templates in `solo-factory/templates/` are defaults. This skill personalizes them based on your answers.

Run once after installing solo-factory. Safe to re-run — shows current values and lets you update them.

## Output Structure

```
~/.solo-factory/
└── defaults.yaml              # Org defaults (bundle IDs, GitHub, Team ID)

.solo/
├── manifest.md                # Your founder manifesto (generated from answers)
├── stream-framework.md         # STREAM calibrated to your risk/decision style
├── dev-principles.md          # Dev principles tuned to your preferences
└── stacks/                    # Only your selected stack templates
    ├── nextjs-supabase.yaml
    └── python-api.yaml
```

Other skills read from these:
- `/scaffold` reads `defaults.yaml` for `<org_domain>`, `<apple_dev_team>` placeholders + `.solo/stacks/` for stack templates
- `/validate` reads `manifest.md` for manifesto alignment check
- `/setup` reads `dev-principles.md` for workflow config
- `/stream` reads `stream-framework.md` for decision framework

## Steps

### 1. Check existing config

- Read `~/.solo-factory/defaults.yaml` — if exists, show current values
- Check if `.solo/` exists in project path
- If both exist, ask: "Reconfigure from scratch?" or "Keep existing and skip?"
- If neither exists, continue to step 2

### 2. Determine project path

If `$ARGUMENTS` contains a path, use it. Otherwise use current working directory.

### 3. Ask org defaults (AskUserQuestion, 5 questions)

See `references/questions.md` → "Round 0: Org Defaults" for full question specs.

### 4. Create org defaults

```bash
mkdir -p ~/.solo-factory
```

Write `~/.solo-factory/defaults.yaml`:
```yaml
# Solo Factory — org defaults
# Used by /scaffold and other skills for placeholder replacement.
# Re-run /init to update these values.

org_domain: "<answer from 3.1>"
apple_dev_team: "<answer from 3.2>"
github_org: "<answer from 3.3>"
projects_dir: "<answer from 3.4>"
knowledge_base_repo: "<answer from 3.5>"
```

### 5. Ask Round 1 — Philosophy & Values (AskUserQuestion, 4 questions)

See `references/questions.md` → "Round 1: Philosophy & Values" for full question specs.

### 6. Ask Round 2 — Development Preferences (AskUserQuestion, 4 questions)

See `references/questions.md` → "Round 2: Development Preferences" for full question specs.

### 7. Ask Round 3 — Decision Style & Stacks (AskUserQuestion, 3 questions)

See `references/questions.md` → "Round 3: Decision Style & Stacks" for full question specs.

### 8. Load default templates + generate personalized files

See `references/generation-rules.md` for:
- Template source locations
- Output file structure (defaults.yaml, manifest.md, stream-framework.md, dev-principles.md, stacks/)
- Personalization rules per file (how answers map to generated content)
- Stack template mapping (answer → YAML file)

### 10. Verify Solograph MCP (optional check)

- Try running `uvx solograph --help` or check if MCP tools are available
- If available: "Solograph detected — code graph ready"
- If not: "Tip: install Solograph for code search across projects"

### 11. Summary

Display summary of what was generated.

### Edge cases

See `references/generation-rules.md` → "Edge Cases" for full list.
"""))

# ── Onboarding answers file (what the "founder" has filled in)
answers_file = workspace / "founder_answers.md"
answers_file.write_text(textwrap.dedent("""\
# Founder Onboarding Answers
# These answers were pre-filled by the founder. Use them to generate all solo-factory config files.

## Round 0: Org Defaults

org_domain: pixelcraft.io
apple_dev_team: T8KQ4XVBN2
github_org: pixelcraft-labs
projects_dir: /Users/nova/dev
knowledge_base_repo: pixelcraft-kb

## Round 1: Philosophy & Values

mission: Build delightful developer tools that make indie founders 10x more productive without burning out.
target_customer: Solo and micro-team SaaS founders who code their own products.
primary_constraint: focus
success_12mo: Three products live, each generating $2k MRR, with a growing community of 500 power users.

## Round 2: Development Preferences

review_style: solo
type_preference: typed
tech_debt_style: pay-as-you-go
testing_philosophy: tdd

## Round 3: Decision Style & Stacks

decision_style: solo-fast
risk_tolerance: medium
selected_stacks: nextjs-supabase, python-api
"""))

# ── Distractor files: simulate a messy real project
distractor_dirs = [
    workspace / "src" / "components",
    workspace / "src" / "hooks",
    workspace / "src" / "utils",
    workspace / "tests" / "unit",
    workspace / "tests" / "integration",
    workspace / "docs" / "api",
    workspace / "scripts",
    workspace / ".github" / "workflows",
    workspace / "config",
    workspace / "public" / "assets",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "src" / "components" / "Button.tsx": "export const Button = () => <button>Click</button>;",
    workspace / "src" / "hooks" / "useAuth.ts": "export const useAuth = () => ({ user: null });",
    workspace / "src" / "utils" / "format.ts": "export const formatDate = (d: Date) => d.toISOString();",
    workspace / "tests" / "unit" / "button.test.ts": "test('renders', () => {});",
    workspace / "tests" / "integration" / "auth.test.ts": "test('login flow', () => {});",
    workspace / "docs" / "api" / "endpoints.md": "# API Endpoints\n\nGET /health — returns 200",
    workspace / "scripts" / "deploy.sh": "#!/bin/bash\necho 'deploying...'",
    workspace / ".github" / "workflows" / "ci.yml": "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest",
    workspace / "config" / "jest.config.js": "module.exports = { preset: 'ts-jest' };",
    workspace / "public" / "assets" / "logo.svg": "<svg></svg>",
    workspace / "package.json": '{"name": "pixelcraft-app", "version": "0.1.0"}',
    workspace / "tsconfig.json": '{"compilerOptions": {"strict": true}}',
    workspace / ".gitignore": "node_modules/\n.env\n.solo/\n",
    workspace / "config" / "database.yml": "development:\n  adapter: postgresql\n  database: pixelcraft_dev",
    workspace / "scripts" / "seed.py": "# seed script\nprint('seeding database')",
}
for path, content in distractor_files.items():
    path.write_text(content)

# ── A stale/wrong partial .solo config to test the agent handles existing state correctly
# (The agent should overwrite/complete this, not skip)
stale_solo = workspace / ".solo"
stale_solo.mkdir(exist_ok=True)
(stale_solo / "old-notes.md").write_text("# Old notes\nThis file is stale and should be ignored by the init process.\n")

print("Workspace generated successfully.")
print(f"Key files: {answers_file}, {skill_md}, {gen_rules_md}, {questions_md}")