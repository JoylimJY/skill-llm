import os
import json
import time
import pathlib
import random

random.seed(42)

workspace = pathlib.Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Distractor files to simulate a real project ---
distractor_dirs = [
    "src/api",
    "src/models",
    "src/utils",
    "config",
    "tests/unit",
    "tests/integration",
    "docs",
    "scripts",
    ".github/workflows",
    "data/samples",
]

for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "src/api/server.py": "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef index():\n    return 'AI Customer Service Bot'\n",
    "src/api/routes.py": "# Route definitions for the chatbot API\nROUTES = ['/chat', '/reset', '/persona']\n",
    "src/models/persona.py": "class Persona:\n    def __init__(self, name, style):\n        self.name = name\n        self.style = style\n",
    "src/models/conversation.py": "class Conversation:\n    def __init__(self):\n        self.history = []\n",
    "src/utils/helpers.py": "def sanitize_input(text):\n    return text.strip().lower()\n",
    "src/utils/logger.py": "import logging\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n",
    "config/settings.json": json.dumps({"bot_name": "Aria", "max_turns": 20, "language": "en"}, indent=2),
    "config/personas.yaml": "default: assistant\navailable:\n  - assistant\n  - philosopher\n  - hero\n",
    "tests/unit/test_helpers.py": "def test_sanitize():\n    from src.utils.helpers import sanitize_input\n    assert sanitize_input('  Hello  ') == 'hello'\n",
    "tests/integration/test_api.py": "# Integration tests placeholder\npass\n",
    "docs/architecture.md": "# Architecture\nThe chatbot uses a persona-driven response system.\n",
    "scripts/deploy.sh": "#!/bin/bash\necho 'Deploying chatbot...'\n",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n",
    "data/samples/conversation1.json": json.dumps([{"user": "hello", "bot": "greetings"}], indent=2),
    "data/samples/conversation2.json": json.dumps([{"user": "who are you?", "bot": "I am your assistant."}], indent=2),
    "requirements.txt": "flask>=2.0\nrequests>=2.28\npython-dotenv>=1.0\n",
    ".env.example": "BOT_NAME=Aria\nDEBUG=false\nPORT=8080\n",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content)

# --- The EXISTING SOUL.md (original persona user already has) ---
original_soul_content = """# Default Assistant Persona

You are Aria, a helpful and concise AI assistant for customer service.

## Core Traits
- Professional and empathetic
- Clear and direct communication
- Always stays on topic

## Instructions
Answer questions accurately. If unsure, say so honestly.
"""
(workspace / "SOUL.md").write_text(original_soul_content)

# --- Stale cache: exists but older than 1 day (set mtime to 3 days ago) ---
cache_dir = pathlib.Path.home() / ".cache" / "agent-souls"
cache_dir.mkdir(parents=True, exist_ok=True)

# Stale/outdated search.json with minimal/wrong data so agent MUST re-download
stale_search_data = [
    {
        "name_en": "Old Entry",
        "name_zh": "旧条目",
        "url": "/real_world/old_entry/",
        "category_en": "Real World",
        "category_zh": "真实世界",
        "tags": ["outdated"],
        "tags_en": ["outdated"],
        "tags_zh": ["过时"]
    }
]
stale_cache_path = cache_dir / "search.json"
stale_cache_path.write_text(json.dumps(stale_search_data, indent=2))

# Set mtime to 3 days ago
three_days_ago = time.time() - (3 * 24 * 3600)
os.utime(stale_cache_path, (three_days_ago, three_days_ago))

print("Workspace generated successfully.")
print(f"Stale cache written to: {stale_cache_path}")
print(f"Stale cache mtime set to 3 days ago: {time.ctime(three_days_ago)}")
print(f"Original SOUL.md written to: {workspace / 'SOUL.md'}")