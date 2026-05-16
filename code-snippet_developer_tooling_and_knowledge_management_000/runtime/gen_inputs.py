import os
import json
import random
import stat

random.seed(42)

# Create deep directory structure with distractor files
dirs = [
    "scripts",
    "docs",
    "tests",
    "config",
    "data/raw",
    "data/processed",
    "src/utils",
    "src/core",
    "logs",
    "backup/snippets_old",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "docs/architecture.md": "# Architecture\nThis document describes system architecture.\n",
    "docs/api_reference.txt": "GET /api/v1/snippets\nPOST /api/v1/snippets\nDELETE /api/v1/snippets/{id}\n",
    "config/settings.json": json.dumps({"debug": False, "max_snippets": 1000, "db_path": "snippets.json"}, indent=2),
    "config/tags.txt": "python\njavascript\nbash\nsql\ngo\n",
    "tests/test_search.py": "# Test search functionality\ndef test_search():\n    pass\n",
    "tests/test_add.py": "# Test add functionality\ndef test_add():\n    pass\n",
    "data/raw/sample_snippets.csv": "title,code,language\nHello World,print('hello'),python\nFetch URL,fetch(url),javascript\n",
    "data/processed/exported.json": json.dumps([{"id": 1, "title": "old snippet", "code": "pass", "lang": "python"}], indent=2),
    "src/utils/helpers.py": "def slugify(text):\n    return text.lower().replace(' ', '-')\n",
    "src/core/db.py": "# Database layer\nimport json\n\nclass SnippetDB:\n    pass\n",
    "logs/app.log": "[2024-01-01 10:00:00] INFO: Application started\n[2024-01-01 10:01:00] INFO: Loaded 0 snippets\n",
    "backup/snippets_old/snippets_2023.json": json.dumps([{"id": 1, "title": "old backup", "code": "x = 1", "lang": "python", "tags": ["python"]}], indent=2),
}

for filepath, content in distractor_files.items():
    with open(filepath, "w") as f:
        f.write(content)

# Create the actual snippet.py script in scripts/
snippet_script = '''#!/usr/bin/env python3
"""Code Snippet Manager - Save and search code snippets"""

import click
import json
import os
import sys
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "snippets_db.json")

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"snippets": [], "next_id": 1}
    return {"snippets": [], "next_id": 1}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

@click.group()
def cli():
    """Code Snippet Manager"""
    pass

@cli.command()
@click.argument("title")
@click.option("--code", required=True, help="Code content (use \\\\n for newlines)")
@click.option("--lang", default="text", help="Programming language")
@click.option("--tag", multiple=True, help="Tags for categorization")
def add(title, code, lang, tag):
    """Add a new code snippet"""
    db = load_db()
    # Handle escaped newlines
    code = code.replace("\\\\n", "\\n").replace("\\n", "\\n")
    snippet = {
        "id": db["next_id"],
        "title": title,
        "code": code,
        "lang": lang,
        "tags": list(tag),
        "created_at": datetime.now().isoformat()
    }
    db["snippets"].append(snippet)
    db["next_id"] += 1
    save_db(db)
    click.echo(f"✅ Snippet saved: [{snippet[\'id\']}] {title}")

@cli.command()
@click.argument("query")
def search(query):
    """Search snippets by keyword"""
    db = load_db()
    results = []
    query_lower = query.lower()
    for s in db["snippets"]:
        if (query_lower in s["title"].lower() or
            query_lower in s["code"].lower() or
            query_lower in s["lang"].lower() or
            any(query_lower in t.lower() for t in s["tags"])):
            results.append(s)
    if not results:
        click.echo("No snippets found.")
        return
    for s in results:
        click.echo(f"[{s[\'id\']}] {s[\'title\']} ({s[\'lang\']})")
        click.echo(f"  Tags: {\', \'.join(s[\'tags\']) if s[\'tags\'] else \'none\'}")
        click.echo(f"  Code: {s[\'code\'][:80]}")
        click.echo("")

@cli.command("list")
@click.option("--tag", default=None, help="Filter by tag")
def list_snippets(tag):
    """List all snippets, optionally filtered by tag"""
    db = load_db()
    snippets = db["snippets"]
    if tag:
        snippets = [s for s in snippets if tag.lower() in [t.lower() for t in s["tags"]]]
    if not snippets:
        click.echo("No snippets found.")
        return
    for s in snippets:
        click.echo(f"[{s[\'id\']}] {s[\'title\']} ({s[\'lang\']})")
        click.echo(f"  Tags: {\', \'.join(s[\'tags\']) if s[\'tags\'] else \'none\'}")
        click.echo("")

@cli.command()
@click.argument("snippet_id", type=int)
def get(snippet_id):
    """Get a snippet by ID (copies to clipboard if possible)"""
    db = load_db()
    for s in db["snippets"]:
        if s["id"] == snippet_id:
            click.echo(s["code"])
            return
    click.echo(f"Snippet #{snippet_id} not found.")

if __name__ == "__main__":
    cli()
'''

with open("scripts/snippet.py", "w") as f:
    f.write(snippet_script)

os.chmod("scripts/snippet.py", 0o755)

# Also create a misleading snippets.py at root level (wrong path trap)
misleading_script = '''#!/usr/bin/env python3
"""This is NOT the main script. Use scripts/snippet.py instead."""
import sys
print("ERROR: Wrong script. Use: python3 scripts/snippet.py")
sys.exit(1)
'''
with open("snippets.py", "w") as f:
    f.write(misleading_script)
os.chmod("snippets.py", 0o755)

# Create a partial/empty SKILL.md reference (as it would exist in project)
skill_content = '''---
name: code-snippet
version: 1.0.0
description: 代码片段收藏夹。快速保存和搜索常用代码片段，支持多语言和高亮。
---

# Code Snippet

See documentation for full usage.
'''
with open("SKILL.md", "w") as f:
    f.write(skill_content)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in os.walk('.'))}")