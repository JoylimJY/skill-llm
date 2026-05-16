import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

# ─── 1. Workspace root ────────────────────────────────────────────────────────
workspace = Path("/home/agent/project")
workspace.mkdir(parents=True, exist_ok=True)

# ─── 2. Build a realistic Python "task management API" project ────────────────
project_structure = {
    "src/__init__.py": "",
    "src/api/__init__.py": "",
    "src/api/tasks.py": '''\
"""Task management API endpoints."""
from typing import List, Optional
from datetime import datetime

class Task:
    def __init__(self, id: int, title: str, status: str = "pending"):
        self.id = id
        self.title = title
        self.status = status
        self.created_at = datetime.now()

    def complete(self):
        self.status = "done"
        return self

class TaskRepository:
    def __init__(self):
        self._tasks = {}
        self._next_id = 1

    def create(self, title: str) -> Task:
        task = Task(self._next_id, title)
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def get(self, task_id: int) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_all(self) -> List[Task]:
        return list(self._tasks.values())

    def delete(self, task_id: int) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
''',
    "src/api/users.py": '''\
"""User management module."""
import hashlib

class User:
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
        self._password_hash = None

    def set_password(self, password: str):
        self._password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self._password_hash == hashlib.sha256(password.encode()).hexdigest()

class UserStore:
    def __init__(self):
        self._users = {}

    def register(self, username: str, email: str, password: str) -> User:
        if username in self._users:
            raise ValueError(f"User {username} already exists")
        user = User(username, email)
        user.set_password(password)
        self._users[username] = user
        return user

    def authenticate(self, username: str, password: str) -> bool:
        user = self._users.get(username)
        if user is None:
            return False
        return user.check_password(password)
''',
    "src/api/notifications.py": '''\
"""Notification dispatch module - has known bug with async dispatch."""
import time
from typing import Callable, List

class NotificationDispatcher:
    def __init__(self):
        self._handlers: List[Callable] = []
        self._queue = []

    def register_handler(self, handler: Callable):
        self._handlers.append(handler)

    def send(self, message: str, priority: int = 1):
        # BUG: priority is never actually used in ordering
        self._queue.append({"message": message, "priority": priority, "sent_at": time.time()})
        for handler in self._handlers:
            try:
                handler(message)
            except Exception as e:
                pass  # silently swallowing errors - needs fix

    def flush(self):
        processed = len(self._queue)
        self._queue.clear()
        return processed
''',
    "src/db/__init__.py": "",
    "src/db/connection.py": '''\
"""Database connection pool - legacy implementation."""
import sqlite3
from contextlib import contextmanager

class ConnectionPool:
    _instance = None

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._connections = []

    @classmethod
    def get_instance(cls, db_path=":memory:"):
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    @contextmanager
    def acquire(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
''',
    "src/db/migrations.py": '''\
"""Schema migrations tracker."""

MIGRATIONS = [
    ("001_create_tasks", """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("002_create_users", """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("003_add_task_owner", """
        ALTER TABLE tasks ADD COLUMN owner_id INTEGER REFERENCES users(id)
    """),
]

def run_migrations(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS schema_version (version TEXT PRIMARY KEY)")
    applied = {row[0] for row in cursor.execute("SELECT version FROM schema_version")}
    for name, sql in MIGRATIONS:
        if name not in applied:
            cursor.execute(sql)
            cursor.execute("INSERT INTO schema_version VALUES (?)", (name,))
    conn.commit()
''',
    "src/utils/__init__.py": "",
    "src/utils/logger.py": '''\
"""Centralized logging utility."""
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
''',
    "src/utils/validators.py": '''\
"""Input validation helpers."""
import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))

def validate_task_title(title: str) -> bool:
    return bool(title and len(title.strip()) >= 3 and len(title) <= 200)

def sanitize_input(text: str) -> str:
    # Remove potential injection characters
    return re.sub(r"[<>&\"']", "", text)
''',
    "tests/__init__.py": "",
    "tests/test_tasks.py": '''\
"""Unit tests for task management."""
import pytest
from src.api.tasks import Task, TaskRepository

def test_create_task():
    repo = TaskRepository()
    task = repo.create("Write unit tests")
    assert task.id == 1
    assert task.status == "pending"

def test_complete_task():
    repo = TaskRepository()
    task = repo.create("Deploy to staging")
    task.complete()
    assert task.status == "done"

def test_list_tasks():
    repo = TaskRepository()
    repo.create("Task A")
    repo.create("Task B")
    assert len(repo.list_all()) == 2

def test_delete_task():
    repo = TaskRepository()
    task = repo.create("Temporary task")
    deleted = repo.delete(task.id)
    assert deleted is True
    assert repo.get(task.id) is None
''',
    "tests/test_users.py": '''\
"""Tests for user management."""
import pytest
from src.api.users import User, UserStore

def test_register_user():
    store = UserStore()
    user = store.register("alice", "alice@example.com", "secret123")
    assert user.username == "alice"

def test_duplicate_registration():
    store = UserStore()
    store.register("bob", "bob@example.com", "pass1")
    with pytest.raises(ValueError):
        store.register("bob", "bob2@example.com", "pass2")

def test_authentication():
    store = UserStore()
    store.register("carol", "carol@example.com", "mypassword")
    assert store.authenticate("carol", "mypassword") is True
    assert store.authenticate("carol", "wrongpass") is False
''',
    "config/settings.py": '''\
"""Application configuration."""
import os

class Config:
    DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
    DB_PATH = os.getenv("DB_PATH", "./data/app.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAX_TASKS_PER_USER = int(os.getenv("MAX_TASKS_PER_USER", "100"))
    NOTIFICATION_TIMEOUT = float(os.getenv("NOTIFICATION_TIMEOUT", "5.0"))
''',
    "config/logging.yaml": '''\
version: 1
disable_existing_loggers: false
formatters:
  standard:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
    stream: ext://sys.stdout
  file:
    class: logging.FileHandler
    formatter: standard
    filename: logs/app.log
root:
  level: INFO
  handlers: [console, file]
''',
    "requirements.txt": """\
click==8.1.7
pydantic==2.5.0
requests==2.31.0
python-dateutil==2.8.2
pytest==7.4.3
rich==13.7.0
""",
    "pyproject.toml": '''\
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "task-management-api"
version = "0.3.1"
description = "A lightweight task management API"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
''',
    "Makefile": """\
.PHONY: test lint format

test:
\tpytest tests/ -v

lint:
\tflake8 src/ tests/

format:
\tblack src/ tests/
""",
    "data/.gitkeep": "",
    "logs/.gitkeep": "",
    "scripts/seed_db.py": '''\
"""Seed script for development database."""
from src.db.connection import ConnectionPool
from src.db.migrations import run_migrations
from src.api.tasks import TaskRepository
from src.api.users import UserStore

def seed():
    pool = ConnectionPool.get_instance("./data/dev.db")
    with pool.acquire() as conn:
        run_migrations(conn)
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed()
''',
    "scripts/health_check.py": '''\
"""Service health check script."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_imports():
    try:
        from src.api.tasks import TaskRepository
        from src.api.users import UserStore
        from src.db.connection import ConnectionPool
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False

if __name__ == "__main__":
    if check_imports():
        print("OK: All modules importable")
        sys.exit(0)
    else:
        sys.exit(1)
''',
}

for rel_path, content in project_structure.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ─── 3. Create a PARTIAL .opencode directory (agent must complete it) ─────────
opencode_dir = workspace / ".opencode"
opencode_dir.mkdir(exist_ok=True)

# A stale/incomplete feature_list.json with wrong statuses (agent must fix)
feature_list = {
    "project": "task-management-api",
    "version": "0.3.1",
    "features": [
        {
            "id": "feat-001",
            "title": "Implement TaskRepository CRUD operations",
            "module": "src/api/tasks.py",
            "status": "in_progress",
            "priority": "high",
            "created_at": "2024-01-15T10:00:00Z"
        },
        {
            "id": "feat-002",
            "title": "Add user authentication system",
            "module": "src/api/users.py",
            "status": "in_progress",
            "priority": "high",
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "id": "feat-003",
            "title": "Fix notification dispatcher priority bug",
            "module": "src/api/notifications.py",
            "status": "blocked",
            "priority": "medium",
            "created_at": "2024-01-16T09:00:00Z"
        },
        {
            "id": "feat-004",
            "title": "Database migration system",
            "module": "src/db/migrations.py",
            "status": "pending",
            "priority": "high",
            "created_at": "2024-01-16T11:00:00Z"
        },
        {
            "id": "feat-005",
            "title": "Input validation utilities",
            "module": "src/utils/validators.py",
            "status": "in_progress",
            "priority": "low",
            "created_at": "2024-01-17T08:00:00Z"
        }
    ],
    "last_updated": "2024-01-17T15:00:00Z"
}
(opencode_dir / "feature_list.json").write_text(json.dumps(feature_list, indent=2))

# progress.txt is MISSING (agent must create it)
# .evolution_mode_active is MISSING (agent must activate it)

# ─── 4. Install the evolving-agent skill at ~/.config/opencode/skills/ ────────
home = Path("/home/agent")
skills_base = home / ".config" / "opencode" / "skills"
skill_root = skills_base / "evolving-agent"

# Create directory structure
for d in [
    skill_root / "scripts",
    skill_root / "modules" / "programming-assistant",
    skill_root / "modules" / "knowledge-base",
    skill_root / "modules" / "github-to-skills",
    skill_root / "data" / "knowledge",
]:
    d.mkdir(parents=True, exist_ok=True)

# ─── 4a. Create module READMEs ────────────────────────────────────────────────
(skill_root / "modules" / "programming-assistant" / "README.md").write_text('''\
# Programming Assistant Module

## Workflow
1. Load knowledge base context
2. Detect project type and structure
3. Execute development tasks
4. Update feature_list.json with completed statuses
5. Write progress updates to .opencode/progress.txt

## Commands
- Detect project: `python $SKILLS_DIR/evolving-agent/scripts/run.py project detect <path>`
- Update feature status: Edit `.opencode/feature_list.json`, set all status fields to `"completed"`
- Write progress: Write summary to `.opencode/progress.txt`

## feature_list.json Status Values
Valid statuses: `pending`, `in_progress`, `blocked`, `completed`
Final state MUST have all items set to `completed`.

## progress.txt Format
```
[PROGRESS] <timestamp>
Tasks completed: <N>
Summary: <description>
```
''')

(skill_root / "modules" / "knowledge-base" / "README.md").write_text('''\
# Knowledge Base Module

## Workflow
1. Extract key insights from current context
2. Classify by category (bug-fix, architecture, best-practice, performance)
3. Store to knowledge base using trigger command

## Commands
```bash
# Trigger knowledge extraction with input context
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger --input "<summary of what was learned>"

# Query knowledge base stats
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge query --stats
```

## Storage Location
Knowledge entries stored in: `$SKILLS_DIR/evolving-agent/data/knowledge/entries.json`

## Entry Schema
```json
{
  "id": "ke-<timestamp>",
  "category": "bug-fix|architecture|best-practice|performance",
  "summary": "...",
  "tags": ["...", "..."],
  "created_at": "ISO8601"
}
```
''')

(skill_root / "modules" / "github-to-skills" / "README.md").write_text('''\
# GitHub To Skills Module

## Workflow
1. Fetch repository content
2. Extract patterns and best practices
3. Store to knowledge base

## Commands
```bash
python $SKILLS_DIR/evolving-agent/scripts/run.py github fetch <url>
python $SKILLS_DIR/evolving-agent/scripts/run.py github extract <local_path>
```
''')

# ─── 4b. Create the main run.py script ───────────────────────────────────────
run_py_content = '''\
#!/usr/bin/env python3
"""Evolving Agent CLI - run.py"""
import click
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", Path.home() / ".config/opencode/skills"))
SKILL_ROOT = SKILLS_DIR / "evolving-agent"
KNOWLEDGE_FILE = SKILL_ROOT / "data" / "knowledge" / "entries.json"
EVOLUTION_FLAG = Path.cwd() / ".opencode" / ".evolution_mode_active"
FEATURE_LIST = Path.cwd() / ".opencode" / "feature_list.json"
PROGRESS_FILE = Path.cwd() / ".opencode" / "progress.txt"


def load_knowledge():
    if KNOWLEDGE_FILE.exists():
        return json.loads(KNOWLEDGE_FILE.read_text())
    return []


def save_knowledge(entries):
    KNOWLEDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_FILE.write_text(json.dumps(entries, indent=2))


@click.group()
def cli():
    """Evolving Agent CLI"""
    pass


@cli.group()
def mode():
    """Evolution mode management."""
    pass


@mode.command("--status", name="status")
def mode_status():
    """Check evolution mode status."""
    if EVOLUTION_FLAG.exists():
        content = EVOLUTION_FLAG.read_text()
        click.echo(f"Evolution mode: ACTIVE\\n{content}")
    else:
        click.echo("Evolution mode: INACTIVE")


@mode.command("--init", name="init")
def mode_init():
    """Initialize/activate evolution mode."""
    EVOLUTION_FLAG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    EVOLUTION_FLAG.write_text(json.dumps({
        "activated_at": ts,
        "status": "active",
        "auto_extract": True
    }, indent=2))
    click.echo(f"[OK] Evolution mode activated at {ts}")
    click.echo(f"[OK] Marker file: {EVOLUTION_FLAG}")


@mode.command("--off", name="off")
def mode_off():
    """Deactivate evolution mode."""
    if EVOLUTION_FLAG.exists():
        EVOLUTION_FLAG.unlink()
        click.echo("[OK] Evolution mode deactivated.")
    else:
        click.echo("Evolution mode was not active.")


@cli.group()
def knowledge():
    """Knowledge base operations."""
    pass


@knowledge.command()
@click.option("--stats", is_flag=True, help="Show knowledge base statistics.")
def query(stats):
    """Query the knowledge base."""
    entries = load_knowledge()
    if stats:
        categories = {}
        for e in entries:
            cat = e.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        click.echo(f"Total entries: {len(entries)}")
        for cat, count in sorted(categories.items()):
            click.echo(f"  {cat}: {count}")
    else:
        for e in entries:
            click.echo(f"[{e.get(\'id\', \'?\')}] {e.get(\'summary\', \'\')} ({e.get(\'category\', \'?\')})")


@knowledge.command()
@click.option("--input", "input_text", required=True, help="Knowledge to store.")
def trigger(input_text):
    """Trigger knowledge extraction and storage."""
    entries = load_knowledge()
    ts = datetime.now(timezone.utc).isoformat()
    entry_id = f"ke-{int(time.time())}"
    # Auto-classify based on keywords
    text_lower = input_text.lower()
    if any(w in text_lower for w in ["bug", "fix", "error", "issue", "broken"]):
        category = "bug-fix"
    elif any(w in text_lower for w in ["architect", "design", "pattern", "structure"]):
        category = "architecture"
    elif any(w in text_lower for w in ["performance", "optim", "speed", "cache"]):
        category = "performance"
    else:
        category = "best-practice"

    # Extract simple tags from input
    words = input_text.lower().split()
    stop_words = {"the", "a", "an", "is", "was", "were", "be", "been", "being",
                  "have", "has", "had", "do", "does", "did", "will", "would",
                  "could", "should", "may", "might", "to", "of", "in", "for",
                  "on", "with", "at", "by", "from", "and", "or", "but", "not"}
    tags = list(set(w for w in words if len(w) > 4 and w not in stop_words))[:5]

    new_entry = {
        "id": entry_id,
        "category": category,
        "summary": input_text,
        "tags": tags,
        "created_at": ts
    }
    entries.append(new_entry)
    save_knowledge(entries)
    click.echo(f"[OK] Knowledge entry stored: {entry_id}")
    click.echo(f"     Category: {category}")
    click.echo(f"     Tags: {tags}")


@cli.group()
def github():
    """GitHub repository operations."""
    pass


@github.command()
@click.argument("url")
def fetch(url):
    """Fetch and analyze a GitHub repository."""
    click.echo(f"[INFO] Fetching: {url}")
    click.echo("[INFO] (Dry run in sandbox mode)")


@github.command()
@click.argument("local_path")
def extract(local_path):
    """Extract patterns from a local repository."""
    click.echo(f"[INFO] Extracting patterns from: {local_path}")


@cli.group()
def project():
    """Project management operations."""
    pass


@project.command()
@click.argument("path", default=".")
def detect(path):
    """Detect project type and structure."""
    proj_path = Path(path).resolve()
    click.echo(f"[PROJECT DETECT] Analyzing: {proj_path}")

    # Detect project type
    indicators = {
        "Python": ["pyproject.toml", "setup.py", "requirements.txt"],
        "Node.js": ["package.json"],
        "Go": ["go.mod"],
        "Rust": ["Cargo.toml"],
    }
    detected = []
    for lang, files in indicators.items():
        if any((proj_path / f).exists() for f in files):
            detected.append(lang)

    click.echo(f"[OK] Project type: {', '.join(detected) if detected else 'Unknown'}")

    # Count source files
    py_files = list(proj_path.rglob("*.py"))
    click.echo(f"[OK] Source files found: {len(py_files)} Python files")

    # Check for test files
    test_files = [f for f in py_files if "test" in f.name.lower()]
    click.echo(f"[OK] Test files: {len(test_files)}")

    # Check .opencode structure
    opencode_path = proj_path / ".opencode"
    if opencode_path.exists():
        click.echo(f"[OK] .opencode directory found")
        feature_list_path = opencode_path / "feature_list.json"
        if feature_list_path.exists():
            data = json.loads(feature_list_path.read_text())
            features = data.get("features", [])
            statuses = [f.get("status") for f in features]
            click.echo(f"[OK] Features: {len(features)} total, statuses: {set(statuses)}")
    else:
        click.echo("[WARN] No .opencode directory found")

    click.echo("[OK] Project detection complete.")


if __name__ == "__main__":
    cli()
'''

(skill_root / "scripts" / "run.py").write_text(run_py_content)
(skill_root / "scripts" / "run.py").chmod(
    (skill_root / "scripts" / "run.py").stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
)

# ─── 4c. Initialize empty knowledge store ────────────────────────────────────
(skill_root / "data" / "knowledge" / "entries.json").write_text("[]")

# ─── 5. Add distractor files ──────────────────────────────────────────────────
distractors = {
    ".github/workflows/ci.yml": """\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
""",
    ".github/PULL_REQUEST_TEMPLATE.md": """\
## Summary
<!-- What does this PR do? -->

## Testing
<!-- How was this tested? -->

## Checklist
- [ ] Tests pass
- [ ] Code reviewed
""",
    "docs/api_reference.md": """\
# API Reference
## Tasks
- `GET /tasks` - List all tasks
- `POST /tasks` - Create a new task
- `GET /tasks/{id}` - Get task by ID
- `DELETE /tasks/{id}` - Delete task
## Users
- `POST /users/register` - Register new user
- `POST /users/login` - Authenticate user
""",
    "docs/architecture.md": """\
# Architecture Overview
The system follows a layered architecture:
- **API Layer**: HTTP handlers (tasks.py, users.py)
- **Service Layer**: Business logic
- **Data Layer**: SQLite via connection pool (db/)
- **Utils**: Cross-cutting concerns (logger, validators)
""",
    ".gitignore": """\
__pycache__/
*.pyc
*.pyo
.env
data/*.db
logs/*.log
.venv/
dist/
*.egg-info/
""",
    "docker-compose.yml": """\
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_DEBUG=false
      - DB_PATH=/data/app.db
    volumes:
      - ./data:/data
      - ./logs:/logs
""",
    "notes/sprint_review.txt": """\
Sprint 3 Review Notes - 2024-01-17
===================================
Completed this sprint:
- TaskRepository basic CRUD ✓
- User authentication ✓
- Database migrations ✓

Known issues:
- NotificationDispatcher priority bug still open
- No rate limiting on API endpoints yet
- Missing input validation on some endpoints

Next sprint priorities:
1. Fix notification priority ordering
2. Add rate limiting middleware
3. Improve test coverage to 80%+
""",
    "notes/tech_debt.txt": """\
Technical Debt Log
==================
[HIGH] notifications.py: silently swallows exceptions - should log/raise
[HIGH] notifications.py: priority parameter unused in dispatch ordering
[MED]  connection.py: singleton pattern makes testing difficult
[MED]  No dependency injection - hard to mock in tests
[LOW]  validators.py: regex patterns not compiled at module level (minor perf)
[LOW]  Missing docstrings on several public methods
""",
    "notes/deployment_checklist.txt": """\
Pre-deployment Checklist
========================
[ ] All tests passing (pytest tests/)
[ ] No linting errors (flake8 src/)
[ ] Environment variables documented
[ ] Database migrations tested on staging
[ ] API docs updated
[ ] CHANGELOG updated
""",
}

for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

print(f"[gen_inputs] Workspace created at {workspace}")
print(f"[gen_inputs] Skill installed at {skill_root}")
print(f"[gen_inputs] Project files: {len(project_structure)} files")
print(f"[gen_inputs] Distractor files: {len(distractors)} files")
print("[gen_inputs] Intentionally MISSING:")
print("  - .opencode/progress.txt")
print("  - .opencode/.evolution_mode_active")
print("  - All feature statuses need to be 'completed'")
print("  - Knowledge base is empty")