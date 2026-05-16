import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── distractor directory tree ──────────────────────────────────────────────
distractor_dirs = [
    "src/api/handlers",
    "src/api/middleware",
    "src/db/migrations",
    "src/db/models",
    "tests/unit",
    "tests/integration",
    "docs/architecture",
    "docs/api",
    "configs/dev",
    "configs/prod",
    "scripts/deploy",
    "scripts/lint",
]
for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "src/api/handlers/user_handler.py": "# User API handler\ndef get_user(id): pass\n",
    "src/api/handlers/order_handler.py": "# Order API handler\ndef create_order(data): pass\n",
    "src/api/middleware/auth.py": "# Auth middleware\ndef verify_token(token): pass\n",
    "src/db/migrations/001_init.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY);\n",
    "src/db/migrations/002_orders.sql": "CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT);\n",
    "src/db/models/user.py": "class User:\n    id: int\n    name: str\n",
    "src/db/models/order.py": "class Order:\n    id: int\n    user_id: int\n",
    "tests/unit/test_user.py": "def test_get_user(): assert True\n",
    "tests/integration/test_order_flow.py": "def test_order_flow(): assert True\n",
    "docs/architecture/overview.md": "# System Architecture\nMicroservices-based design.\n",
    "docs/api/endpoints.md": "# API Endpoints\nGET /users, POST /orders\n",
    "configs/dev/app.yaml": "env: dev\ndebug: true\n",
    "configs/prod/app.yaml": "env: prod\ndebug: false\n",
    "scripts/deploy/run.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "scripts/lint/check.sh": "#!/bin/bash\necho 'Linting...'\n",
}
for path, content in distractor_files.items():
    (workspace / path).write_text(content)

# ── The main input: a raw session transcript ───────────────────────────────
# This is the "messy real-world data" the agent must process.
# It contains:
#   - Explicit corrections (→ corrections.md)
#   - Explicit preferences (→ memory.md HOT)
#   - Project-specific rules (→ projects/atlas.md, projects/phoenix.md)
#   - Domain patterns (→ domains/code.md)
#   - 55 corrections total (must be trimmed to last 50)
#   - Patterns that appear 3+ times in 7 days (→ promote to HOT)
#   - Stale patterns (last seen 95 days ago → archive; 35 days ago → demote)
#   - A memory.md pre-seeded with 98 lines + new entries that would exceed 100 (trigger compaction)

now = datetime.now()

# ── session_log.txt: the raw transcript ──────────────────────────────────
corrections_raw = []

# 55 corrections to test "last 50" trimming
for i in range(1, 56):
    ts = (now - timedelta(days=60) + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M")
    corrections_raw.append(
        f"[{ts}] User: No, that's not right — you used tabs instead of spaces. Use 4-space indentation always. (correction #{i})"
    )

# Explicit global preferences
global_prefs = [
    f"[{(now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M')}] User: I like when you summarize changes at the end of every coding session.",
    f"[{(now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M')}] User: Always use snake_case for variable names in Python.",
    f"[{(now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}] User: Never use f-strings in legacy modules.",
    f"[{(now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}] User: My style is minimal comments — only explain non-obvious logic.",
]

# Project-specific rules for "atlas" project
atlas_rules = [
    f"[{(now - timedelta(days=3)).strftime('%Y-%m-%d %H:%M')}] User: For atlas, use PostgreSQL transactions for every write operation.",
    f"[{(now - timedelta(days=3)).strftime('%Y-%m-%d %H:%M')}] User: For atlas, the API layer must never directly query the DB — always go through the service layer.",
    f"[{(now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M')}] User: For atlas, always run migrations inside a transaction block.",
]

# Project-specific rules for "phoenix" project
phoenix_rules = [
    f"[{(now - timedelta(days=4)).strftime('%Y-%m-%d %H:%M')}] User: For phoenix, use TypeScript strict mode everywhere.",
    f"[{(now - timedelta(days=4)).strftime('%Y-%m-%d %H:%M')}] User: For phoenix, all API responses must follow the JSend spec.",
    f"[{(now - timedelta(days=3)).strftime('%Y-%m-%d %H:%M')}] User: For phoenix, never commit node_modules.",
]

# Domain (code) patterns
code_domain = [
    f"[{(now - timedelta(days=5)).strftime('%Y-%m-%d %H:%M')}] User: Always do X for me — wrap all DB calls in try/except.",
    f"[{(now - timedelta(days=5)).strftime('%Y-%m-%d %H:%M')}] User: I prefer type hints on all function signatures.",
    f"[{(now - timedelta(days=4)).strftime('%Y-%m-%d %H:%M')}] User: You're wrong about error handling — always re-raise after logging.",
]

# Patterns repeated 3x in 7 days (promotion candidates)
repeated_pattern_days = [6, 4, 2]  # all within 7 days
repeated_patterns = []
for d in repeated_pattern_days:
    ts = (now - timedelta(days=d)).strftime("%Y-%m-%d %H:%M")
    repeated_patterns.append(
        f"[{ts}] User: I told you before — always add type hints to function signatures."
    )

# One-time / hypothetical (should be IGNORED)
ignored = [
    f"[{(now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}] User: In this file only, skip the docstring.",
    f"[{(now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}] User: What if we used Redis instead?",
    f"[{(now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}] User: Do X now — run the linter.",
]

all_lines = (
    corrections_raw
    + global_prefs
    + atlas_rules
    + phoenix_rules
    + code_domain
    + repeated_patterns
    + ignored
)
random.shuffle(all_lines)

session_log = "# Raw Session Transcript — Consulting AI Assistant\n"
session_log += "# Date range: last 60 days\n\n"
session_log += "\n".join(all_lines)

(workspace / "session_log.txt").write_text(session_log)

# ── pre-existing ~/self-improving/ state ──────────────────────────────────
# The self-improving directory already exists but is partially stale.
si_dir = Path.home() / "self-improving"
si_dir.mkdir(parents=True, exist_ok=True)
(si_dir / "projects").mkdir(exist_ok=True)
(si_dir / "domains").mkdir(exist_ok=True)
(si_dir / "archive").mkdir(exist_ok=True)

# memory.md: already at 98 lines (near limit), some stale entries
memory_lines = []
memory_lines.append("# HOT Memory — Self-Improving Agent\n")
memory_lines.append("# Limit: 100 lines\n")
memory_lines.append("\n")

# 30 filler entries (each 3 lines: tag + content + blank)
stale_patterns = [
    "- [STALE-95d] Always use camelCase for JS variables",   # 95 days old → archive
    "- [STALE-35d] Prefer async/await over callbacks",       # 35 days old → demote to WARM
    "- [STALE-35d] Use ESLint with airbnb config",           # 35 days old → demote to WARM
]

for sp in stale_patterns:
    memory_lines.append(sp + "\n")
    memory_lines.append("\n")

# Fill to 92 lines with generic (non-stale) entries
generic_entries = [
    "- Use pytest for all Python tests",
    "- Keep functions under 50 lines",
    "- Write docstrings for public APIs",
    "- Prefer composition over inheritance",
    "- Use dataclasses for value objects",
    "- Always validate inputs at boundaries",
    "- Use logging instead of print statements",
    "- Separate config from code",
    "- Pin dependency versions in requirements.txt",
    "- Use virtual environments for isolation",
    "- Prefer explicit over implicit",
    "- Follow PEP8 for Python",
    "- Write tests before fixing bugs",
    "- Use meaningful variable names",
    "- Avoid global state",
    "- Handle errors at appropriate layers",
    "- Use constants for magic numbers",
    "- Document breaking changes",
    "- Review diffs before committing",
    "- Keep CI green",
    "- Use feature flags for risky changes",
    "- Prefer small PRs",
    "- Write commit messages in imperative mood",
    "- Squash fixup commits",
    "- Tag releases semantically",
    "- Archive old branches",
    "- Use linters in pre-commit hooks",
    "- Monitor error rates after deploys",
    "- Write runbooks for ops procedures",
    "- Keep secrets out of source code",
]
for entry in generic_entries:
    memory_lines.append(entry + "\n")
    memory_lines.append("\n")

# memory.md currently has len(memory_lines) lines — make it exactly 98
while len(memory_lines) < 98:
    memory_lines.append("- Placeholder entry\n")

(si_dir / "memory.md").write_text("".join(memory_lines[:98]))

# corrections.md: already has 48 entries (adding more from log will exceed 50)
corrections_md_lines = ["# Corrections Log — Last 50\n\n"]
for i in range(1, 49):
    ts = (now - timedelta(days=70) + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M")
    corrections_md_lines.append(f"[{ts}] Used wrong indentation (old entry #{i})\n")
(si_dir / "corrections.md").write_text("".join(corrections_md_lines))

# index.md
(si_dir / "index.md").write_text(
    "# Memory Index\n\n"
    "| File | Lines | Topic |\n"
    "|------|-------|-------|\n"
    "| memory.md | 98 | HOT patterns |\n"
    "| corrections.md | 49 | Corrections log |\n"
)

# Existing stale domain file
stale_domain_content = (
    "# Domain: code\n\n"
    f"Last-used: {(now - timedelta(days=35)).strftime('%Y-%m-%d')}\n\n"
    "- [STALE-35d] Prefer async/await over callbacks\n"
    "- [STALE-35d] Use ESLint with airbnb config\n"
    "- Wrap all DB calls in try/except\n"
    "- Always re-raise after logging\n"
)
(si_dir / "domains" / "code.md").write_text(stale_domain_content)

# Existing stale project file to be archived
stale_project_content = (
    "# Project: legacy-crm\n\n"
    f"Last-used: {(now - timedelta(days=95)).strftime('%Y-%m-%d')}\n\n"
    "- [STALE-95d] Use jQuery for DOM manipulation\n"
    "- [STALE-95d] Deploy via FTP\n"
)
(si_dir / "projects" / "legacy-crm.md").write_text(stale_project_content)

# reflections.md (minimal, pre-existing)
(si_dir / "reflections.md").write_text(
    "# Self-Reflection Log\n\n"
    "CONTEXT: Code review\n"
    "REFLECTION: Missed a type error in return value\n"
    "LESSON: Check return types explicitly\n\n"
)

# boundaries.md stub
(si_dir / "boundaries.md").write_text(
    "# Security Boundaries\n\nNever store credentials, health data, or third-party PII.\n"
)

# Write a metadata JSON so eval can verify timestamps
meta = {
    "now_iso": now.isoformat(),
    "stale_95d": (now - timedelta(days=95)).strftime("%Y-%m-%d"),
    "stale_35d": (now - timedelta(days=35)).strftime("%Y-%m-%d"),
    "repeated_pattern_days": repeated_pattern_days,
}
(workspace / ".task_meta.json").write_text(json.dumps(meta, indent=2))

print("Workspace generated successfully.")
print(f"session_log.txt: {len(all_lines)} lines")
print(f"memory.md pre-seeded: 98 lines")
print(f"corrections.md pre-seeded: 48 entries + header")