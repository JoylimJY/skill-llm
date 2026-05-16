import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

# Base workspace
workspace = Path("/workspace")

# ─── Create the self-improving memory structure ────────────────────────────────
base = Path.home() / "self-improving"
base.mkdir(parents=True, exist_ok=True)
(base / "projects").mkdir(exist_ok=True)
(base / "domains").mkdir(exist_ok=True)
(base / "archive").mkdir(exist_ok=True)

# ─── memory.md: BLOATED — 127 lines, must be compacted to ≤100 ────────────────
# Contains duplicates, stale entries, and verbose patterns that need merging.
memory_lines = [
    "# HOT Memory — Always Loaded",
    "# Last compacted: 2024-10-01",
    "",
    "## Global Preferences",
    "- Always use 4-space indentation in Python files",
    "- Always use 4-space indentation (Python)",          # duplicate of above
    "- Use type hints in all Python function signatures",
    "- Use type hints for Python functions",              # duplicate
    "- Prefer f-strings over .format() or % formatting",
    "- Use f-strings not .format() in Python",           # duplicate
    "- Never use tabs for indentation",
    "- Do not use tabs, use spaces",                      # duplicate
    "- Keep functions under 30 lines",
    "- Write docstrings for all public functions",
    "- Use descriptive variable names, avoid single letters",
    "- Single letter variable names are not allowed except loop counters",  # near-dup
    "",
    "## Code Style",
    "- Imports should be sorted: stdlib, third-party, local (PEP8)",
    "- Sort imports in this order: standard lib, third party, local",  # dup
    "- Always add a blank line between import groups",
    "- Use Black formatter for all Python code",
    "- Run Black before committing code",                  # dup of above intent
    "- Line length max is 88 characters (Black default)",
    "- Max line length: 88 chars",                         # dup
    "",
    "## Git Workflow",
    "- Commit messages must start with a verb (Add, Fix, Update, Remove)",
    "- Write commit messages in imperative mood",          # near-dup
    "- Always create a feature branch, never commit directly to main",
    "- Never push directly to main branch",                # dup
    "- Squash commits before merging to main",
    "- Always write a PR description with context",
    "- PR descriptions should include: what changed, why, how to test",  # verbose version
    "",
    "## Testing",
    "- All new features require unit tests",
    "- Write unit tests for every new feature",            # dup
    "- Use pytest for all Python tests",
    "- Test file names must follow test_*.py convention",
    "- Aim for 80% code coverage minimum",
    "- Code coverage should be at least 80%",              # dup
    "",
    "## Communication",
    "- Keep responses concise and to the point",
    "- Avoid unnecessary verbosity in responses",          # near-dup
    "- Use bullet points for lists of 3 or more items",
    "- Use numbered lists when order matters",
    "- Always acknowledge the user's question before answering",
    "",
    "## Project: alpha-service",
    "- Use async/await for all database operations in alpha-service",
    "- SQLAlchemy async sessions in alpha-service",
    "- Redis cache TTL is 300 seconds in alpha-service",
    "",
    "## Stale Entries (unused >90 days)",
    "- Use Python 2 compatible syntax when possible",      # clearly stale/wrong
    "- Always use print statements for debugging",         # stale
    "- Use CamelCase for variable names in Python",        # stale/wrong
    "- Always use semicolons at end of Python statements", # stale/wrong
    "- Use global variables for configuration",            # stale
    "",
    "## Reflection Log",
    "CONTEXT: Code review",
    "REFLECTION: Missed type hints on helper functions",
    "LESSON: Always add type hints to ALL functions, not just public ones",
    "",
    "CONTEXT: PR submission",
    "REFLECTION: PR description was missing testing instructions",
    "LESSON: Always include how-to-test in PR description",
    "",
    "CONTEXT: Debugging session",
    "REFLECTION: Spent 20min on issue that logging would have caught",
    "LESSON: Add structured logging at function entry/exit for complex workflows",
    "",
    "CONTEXT: Code review",
    "REFLECTION: Used .format() instead of f-strings, reviewer flagged it",
    "LESSON: Use f-strings exclusively",
    "",
    "CONTEXT: Commit message",
    "REFLECTION: Wrote 'fixed stuff' as commit message",
    "LESSON: Write descriptive imperative commit messages",
    "",
    "CONTEXT: Test writing",
    "REFLECTION: Forgot to test edge cases for empty inputs",
    "LESSON: Always test empty/None/zero edge cases",
    "",
    "CONTEXT: API design",
    "REFLECTION: Returned 200 for validation errors, should be 422",
    "LESSON: Use correct HTTP status codes: 422 for validation, 404 for not found",
    "",
    "CONTEXT: Database query",
    "REFLECTION: N+1 query problem found in production",
    "LESSON: Use eager loading (joinedload) for related entities",
    "",
    "CONTEXT: Code review",
    "REFLECTION: Missing blank lines between import groups",
    "LESSON: Follow PEP8 import grouping with blank lines",
    "",
    "CONTEXT: Merge conflict",
    "REFLECTION: Conflict happened because I pushed to main",
    "LESSON: Always use feature branches, never commit to main",
    "",
    "CONTEXT: Deployment",
    "REFLECTION: Forgot to update environment variables",
    "LESSON: Maintain a .env.example file and check it before deploying",
    "",
    "## Notes from 2024-09-15",
    "- Reminder: update dependencies monthly",
    "- Reminder: check for security advisories",
    "- Reminder: review open PRs every Monday",             # one-time notes, not patterns
    "- Note: discussed with team, will migrate to FastAPI",  # one-time
    "- Note: John prefers tabs, discussed but agreed on spaces",  # should not store third-party info
    "",
    "## Additional Preferences",
    "- When reviewing code, focus on logic before style",
    "- Start code reviews with positive feedback",
    "- Use conventional commits format",
    "- Prefer composition over inheritance in OOP",
    "- Avoid deep inheritance hierarchies (max 2 levels)",  # near-dup
]

# Write it — should be 127 lines
with open(base / "memory.md", "w") as f:
    f.write("\n".join(memory_lines) + "\n")

print(f"memory.md line count: {len(memory_lines)}")

# ─── corrections.md: Contains recent corrections, some with 3x pattern ─────────
# Dates: today is the reference; patterns within 7 days need promotion check
today = datetime.now()

def dstr(delta_days):
    return (today - timedelta(days=delta_days)).strftime("%Y-%m-%d")

corrections_content = f"""# Corrections Log — Last 50
# Format: DATE | SOURCE | CORRECTION

{dstr(1)} | user | "Stop using print() for debugging — use logging.debug() instead"
{dstr(2)} | user | "I told you before: use logging, not print statements for debug output"
{dstr(3)} | self-reflection | CONTEXT: Debug session / REFLECTION: Used print() for tracing again / LESSON: Use logging.debug() not print() for debug output
{dstr(4)} | user | "Why do you keep using print for debugging? Use the logging module"
{dstr(5)} | user | "Actually, Redis TTL in beta-service should be 600 seconds, not 300"
{dstr(6)} | user | "No, that's not right — error responses must include a 'detail' field in the JSON body"
{dstr(6)} | self-reflection | CONTEXT: API error handling / REFLECTION: Returned bare status code with no body / LESSON: Always include 'detail' field in error response JSON
{dstr(7)} | user | "You're wrong about the test naming — integration tests go in tests/integration/, not tests/"
{dstr(8)} | user | "Remember that I always want mypy strict mode enabled on this project"
{dstr(10)} | user | "I prefer snake_case for all filenames, not kebab-case"
{dstr(12)} | user | "Always add a CHANGELOG entry when bumping version"
{dstr(15)} | self-reflection | CONTEXT: Version bump / REFLECTION: Forgot CHANGELOG again / LESSON: Version bumps must include CHANGELOG update
{dstr(16)} | user | "No, that's not right — the alpha-service uses PostgreSQL 15, not 14"
{dstr(20)} | user | "Stop using mutable default arguments in Python functions"
{dstr(21)} | user | "I told you before: never use mutable defaults like def f(x=[])"
{dstr(22)} | self-reflection | CONTEXT: Function signature review / REFLECTION: Used list as default arg / LESSON: Never use mutable defaults in Python — use None and initialize inside
{dstr(25)} | user | "Actually it should be — use dataclasses not namedtuples for structured data"
{dstr(30)} | user | "You're wrong about environment setup — use python-dotenv not os.environ directly"
{dstr(35)} | user | "I prefer pytest-asyncio for async tests, not anyio"
{dstr(40)} | user | "Remember that I always want __all__ defined in __init__.py files"
{dstr(45)} | user | "No, use pathlib.Path not os.path for file operations"
{dstr(50)} | user | "Always pin dependency versions in requirements.txt"
{dstr(55)} | user | "I told you: use pydantic v2 syntax not v1"
{dstr(60)} | user | "Stop abbreviating variable names — write them out fully"
"""

with open(base / "corrections.md", "w") as f:
    f.write(corrections_content)

# ─── projects/alpha-service.md: Has conflict with global memory.md ────────────
alpha_content = """# Project: alpha-service
# Namespace: projects/alpha-service

## Preferences (Project-Specific)
- Use 2-space indentation in alpha-service config files (YAML/TOML)
- PostgreSQL 15 (updated 2024-11-01)
- Async SQLAlchemy sessions for all DB operations
- Redis TTL: 300 seconds for cache entries
- Use structlog for logging, not standard logging module
- Deploy via Docker Compose only, no direct pip installs on server
- API versioning: prefix all routes with /api/v1/
- Use UUID4 for all primary keys

## Conflict Note
# GLOBAL says: "Use logging module (logging.debug())"
# THIS PROJECT says: "Use structlog for logging"
# Resolution: project-specific wins for alpha-service
"""

with open(base / "projects" / "alpha-service.md", "w") as f:
    f.write(alpha_content)

# ─── projects/beta-service.md ─────────────────────────────────────────────────
beta_content = """# Project: beta-service

## Preferences
- Redis TTL: 600 seconds (corrected 2024-11-05)
- Use FastAPI (migrated from Flask)
- Celery for async task processing
- PostgreSQL 14
"""

with open(base / "projects" / "beta-service.md", "w") as f:
    f.write(beta_content)

# ─── domains/code.md ──────────────────────────────────────────────────────────
code_domain_content = """# Domain: Code
# Namespace: domains/code

## Python Conventions
- Use type hints
- Follow PEP8
- Run Black formatter
- Use pytest

## General
- Prefer explicit over implicit
- Write self-documenting code
"""

with open(base / "domains" / "code.md", "w") as f:
    f.write(code_domain_content)

# ─── domains/writing.md ───────────────────────────────────────────────────────
writing_domain_content = """# Domain: Writing

## Documentation
- Use imperative mood in docstrings
- Keep README files up to date
- Document public APIs with examples
"""

with open(base / "domains" / "writing.md", "w") as f:
    f.write(writing_domain_content)

# ─── archive/ — existing cold storage ─────────────────────────────────────────
archive_content = """# Archived Patterns

## Archived: 2024-08-01
- Use virtualenv (replaced by venv preference)
- Python 3.7 compatibility (project moved to 3.11+)
"""

with open(base / "archive" / "archive-2024-08.md", "w") as f:
    f.write(archive_content)

# ─── index.md: Stale — needs updating ─────────────────────────────────────────
index_content = """# Memory Index
# Last updated: 2024-10-01

| File | Lines | Last Updated |
|------|-------|--------------|
| memory.md | 85 | 2024-10-01 |
| corrections.md | 30 | 2024-10-15 |
| projects/alpha-service.md | 18 | 2024-10-01 |
| projects/beta-service.md | 8 | 2024-10-01 |
| domains/code.md | 12 | 2024-09-20 |
| domains/writing.md | 9 | 2024-09-20 |
| archive/archive-2024-08.md | 6 | 2024-08-01 |
"""

with open(base / "index.md", "w") as f:
    f.write(index_content)

# ─── Distractor files in workspace ────────────────────────────────────────────
distractors = [
    ("project_notes/sprint_22/standup.txt", "Discussed Redis migration. No blockers."),
    ("project_notes/sprint_22/retrospective.md", "# Retro\n- Good: fast delivery\n- Bad: too many hotfixes"),
    ("project_notes/sprint_23/planning.txt", "Tickets: AUTH-101, AUTH-102, INFRA-55"),
    ("project_notes/old/archive_2023.txt", "Old sprint notes from 2023."),
    ("dev_tools/linter_config/.flake8", "[flake8]\nmax-line-length = 88\nextend-ignore = E203"),
    ("dev_tools/linter_config/.pylintrc", "[MASTER]\njobs=1"),
    ("dev_tools/formatter/pyproject.toml", "[tool.black]\nline-length = 88"),
    ("logs/agent_run_20241101.log", "INFO: task started\nINFO: task completed"),
    ("logs/agent_run_20241102.log", "INFO: correction logged\nWARN: memory.md approaching limit"),
    ("logs/agent_run_20241103.log", "INFO: promotion check ran\nINFO: no promotions"),
    ("temp/scratch.txt", "TODO: clean up memory files"),
    ("temp/notes_draft.md", "Draft: memory refactor ideas"),
]

for rel_path, content in distractors:
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

print("Workspace generation complete.")
print(f"memory.md has {len(memory_lines)} lines (limit is 100 — compaction required)")