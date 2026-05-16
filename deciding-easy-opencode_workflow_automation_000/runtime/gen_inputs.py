#!/usr/bin/env python3
"""
Generate the sandbox workspace for the opencode skill evaluation task.
Simulates a small Flask microservice repository that needs a new endpoint added.
"""

import os
import random
import stat

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")
os.makedirs(WORKSPACE, exist_ok=True)

# ── Repo root ──────────────────────────────────────────────────────────────────
REPO = os.path.join(WORKSPACE, "inventory-service")
os.makedirs(REPO, exist_ok=True)

# ── app/ package ──────────────────────────────────────────────────────────────
app_dir = os.path.join(REPO, "app")
os.makedirs(app_dir, exist_ok=True)

with open(os.path.join(app_dir, "__init__.py"), "w") as f:
    f.write('"""Inventory Service Flask Application."""\n')
    f.write('from .routes import create_app\n')

with open(os.path.join(app_dir, "routes.py"), "w") as f:
    f.write(
        '"""Core route definitions for the inventory service."""\n'
        'from flask import Flask, jsonify\n'
        '\n'
        '\n'
        'def create_app():\n'
        '    app = Flask(__name__)\n'
        '\n'
        '    @app.route("/items", methods=["GET"])\n'
        '    def list_items():\n'
        '        return jsonify({"items": ["widget-A", "widget-B", "widget-C"]})\n'
        '\n'
        '    @app.route("/items/<item_id>", methods=["GET"])\n'
        '    def get_item(item_id):\n'
        '        return jsonify({"item_id": item_id, "status": "available"})\n'
        '\n'
        '    return app\n'
    )

with open(os.path.join(app_dir, "models.py"), "w") as f:
    f.write(
        '"""Data models (stub)."""\n'
        'class Item:\n'
        '    def __init__(self, item_id, name, qty):\n'
        '        self.item_id = item_id\n'
        '        self.name = name\n'
        '        self.qty = qty\n'
    )

with open(os.path.join(app_dir, "config.py"), "w") as f:
    f.write(
        '"""Application configuration."""\n'
        'import os\n'
        '\n'
        'DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"\n'
        'SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-not-for-prod")\n'
        'DB_URI = os.getenv("DATABASE_URL", "sqlite:///inventory.db")\n'
    )

# ── tests/ ─────────────────────────────────────────────────────────────────────
tests_dir = os.path.join(REPO, "tests")
os.makedirs(tests_dir, exist_ok=True)

with open(os.path.join(tests_dir, "__init__.py"), "w") as f:
    f.write("")

with open(os.path.join(tests_dir, "test_items.py"), "w") as f:
    f.write(
        '"""Tests for /items endpoint."""\n'
        'import pytest\n'
        'from app.routes import create_app\n'
        '\n'
        '\n'
        '@pytest.fixture\n'
        'def client():\n'
        '    app = create_app()\n'
        '    app.config["TESTING"] = True\n'
        '    with app.test_client() as c:\n'
        '        yield c\n'
        '\n'
        '\n'
        'def test_list_items(client):\n'
        '    rv = client.get("/items")\n'
        '    assert rv.status_code == 200\n'
        '    data = rv.get_json()\n'
        '    assert "items" in data\n'
        '\n'
        '\n'
        'def test_get_item(client):\n'
        '    rv = client.get("/items/widget-A")\n'
        '    assert rv.status_code == 200\n'
    )

# ── scripts/ (distractor ops scripts) ─────────────────────────────────────────
scripts_dir = os.path.join(REPO, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

with open(os.path.join(scripts_dir, "seed_db.py"), "w") as f:
    f.write(
        '#!/usr/bin/env python3\n'
        '"""Seed the database with sample inventory items."""\n'
        'import sqlite3, os\n'
        'conn = sqlite3.connect(os.getenv("DATABASE_URL", "inventory.db"))\n'
        'conn.execute("CREATE TABLE IF NOT EXISTS items (id TEXT, name TEXT, qty INT)")\n'
        'conn.execute("INSERT OR IGNORE INTO items VALUES (\'1\', \'widget-A\', 100)")\n'
        'conn.commit()\n'
        'conn.close()\n'
        'print("Database seeded.")\n'
    )

with open(os.path.join(scripts_dir, "check_deps.sh"), "w") as f:
    f.write(
        '#!/usr/bin/env bash\n'
        '# Verify that required Python packages are installed.\n'
        'python3 -c "import flask; print(flask.__version__)"\n'
    )

# ── deployment/ (distractor configs) ──────────────────────────────────────────
deploy_dir = os.path.join(REPO, "deployment")
os.makedirs(deploy_dir, exist_ok=True)

with open(os.path.join(deploy_dir, "gunicorn.conf.py"), "w") as f:
    f.write(
        '# Gunicorn configuration for production.\n'
        'bind = "0.0.0.0:8080"\n'
        'workers = 4\n'
        'timeout = 30\n'
        'accesslog = "-"\n'
        'errorlog = "-"\n'
    )

with open(os.path.join(deploy_dir, "nginx.conf"), "w") as f:
    f.write(
        'server {\n'
        '    listen 80;\n'
        '    location / {\n'
        '        proxy_pass http://127.0.0.1:8080;\n'
        '    }\n'
        '}\n'
    )

# ── docs/ (distractor markdown) ───────────────────────────────────────────────
docs_dir = os.path.join(REPO, "docs")
os.makedirs(docs_dir, exist_ok=True)

with open(os.path.join(docs_dir, "api_spec.md"), "w") as f:
    f.write(
        '# Inventory Service API\n\n'
        '## Endpoints\n\n'
        '### GET /items\n'
        'Returns a list of all inventory items.\n\n'
        '### GET /items/{item_id}\n'
        'Returns a single inventory item by ID.\n\n'
        '## Planned Enhancements\n'
        '- [ ] Add GET /health endpoint returning `{"status": "ok"}`\n'
    )

with open(os.path.join(docs_dir, "architecture.md"), "w") as f:
    f.write(
        '# Architecture Overview\n\n'
        'The inventory service is a Flask microservice backed by SQLite in dev '
        'and PostgreSQL in production.\n'
    )

# ── top-level project files ────────────────────────────────────────────────────
with open(os.path.join(REPO, "main.py"), "w") as f:
    f.write(
        '"""Application entry point."""\n'
        'from app import create_app\n'
        '\n'
        'app = create_app()\n'
        '\n'
        'if __name__ == "__main__":\n'
        '    app.run(host="0.0.0.0", port=5000)\n'
    )

with open(os.path.join(REPO, "requirements.txt"), "w") as f:
    f.write(
        'flask>=2.3.0\n'
        'gunicorn>=21.0.0\n'
        'pytest>=7.0.0\n'
    )

with open(os.path.join(REPO, "setup.cfg"), "w") as f:
    f.write(
        '[metadata]\n'
        'name = inventory-service\n'
        'version = 0.4.2\n'
        '\n'
        '[options]\n'
        'packages = find:\n'
        'install_requires = flask\n'
        '\n'
        '[tool:pytest]\n'
        'testpaths = tests\n'
    )

with open(os.path.join(REPO, ".gitignore"), "w") as f:
    f.write(
        '__pycache__/\n'
        '*.pyc\n'
        '*.db\n'
        '.env\n'
        'dist/\n'
        'build/\n'
    )

with open(os.path.join(REPO, "Makefile"), "w") as f:
    f.write(
        '.PHONY: run test lint\n\n'
        'run:\n'
        '\tpython3 main.py\n\n'
        'test:\n'
        '\tpytest tests/\n\n'
        'lint:\n'
        '\tpython3 -m flake8 app/\n'
    )

# ── opencode invocation log directory (empty, to be populated by agent) ────────
log_dir = os.path.join(WORKSPACE, ".opencode_logs")
os.makedirs(log_dir, exist_ok=True)

print(f"Workspace generated at: {WORKSPACE}")
print("Repository: inventory-service/")
print("Distractor files created:", sum(1 for _ in os.walk(REPO)))