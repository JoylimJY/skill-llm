import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── 1. Realistic project directory structure ──────────────────────────────────
dirs = [
    "src/api",
    "src/handlers",
    "src/utils",
    "config/envs",
    "config/secrets",
    "scripts/deploy",
    "scripts/maintenance",
    "logs/archive",
    "tests/unit",
    "tests/integration",
    ".openclaw/extensions",
    "docs/internal",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── 2. Distractor files (realistic, plausible, but irrelevant) ────────────────
distractor_files = {
    "src/api/chat_handler.py": """\
import json

class ChatHandler:
    def __init__(self, model_name):
        self.model = model_name

    def handle(self, message):
        # Route to local model endpoint
        return {"role": "assistant", "content": "..."}
""",
    "src/handlers/session_manager.py": """\
class SessionManager:
    def __init__(self):
        self._sessions = {}

    def get_or_create(self, session_id):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        return self._sessions[session_id]
""",
    "src/utils/token_counter.py": """\
def estimate_tokens(text, chars_per_token=4):
    return len(text) // chars_per_token
""",
    "config/envs/production.env": """\
MODEL_ENDPOINT=http://localhost:11434
MODEL_NAME=qwen2-1.5b-instruct
SUMMARIZER_MODEL=qwen2-7b-instruct
LOG_LEVEL=info
MAX_SESSIONS=500
""",
    "config/envs/staging.env": """\
MODEL_ENDPOINT=http://localhost:11434
MODEL_NAME=qwen2-1.5b-instruct
SUMMARIZER_MODEL=qwen2-7b-instruct
LOG_LEVEL=debug
MAX_SESSIONS=50
""",
    "config/secrets/.gitignore": """\
*.key
*.pem
api_tokens.json
""",
    "scripts/deploy/start_gateway.sh": """\
#!/bin/bash
set -euo pipefail
echo "Starting openclaw gateway..."
openclaw gateway restart
""",
    "scripts/maintenance/rotate_logs.sh": """\
#!/bin/bash
find /workspace/logs/archive -name '*.log' -mtime +7 -delete
echo "Old logs purged."
""",
    "logs/archive/gateway_2024-10-01.log": """\
[INFO]  openclaw gateway started
[INFO]  Loading plugins...
[WARN]  context-compactor: config missing, using defaults
[INFO]  Gateway ready on :8080
""",
    "logs/archive/gateway_2024-10-15.log": """\
[INFO]  openclaw gateway started
[INFO]  context-compactor: enabled=true, maxTokens=8000
[INFO]  Gateway ready on :8080
[WARN]  Session JA-0042: context ~7800 tokens, near limit
""",
    "tests/unit/test_token_counter.py": """\
from src.utils.token_counter import estimate_tokens

def test_english():
    assert estimate_tokens("hello world", 4) == 2

def test_cjk():
    # CJK characters are denser — use charsPerToken=3
    text = "こんにちは世界"
    assert estimate_tokens(text, 3) == 2
""",
    "tests/integration/test_session_flow.py": """\
import json

def test_session_compaction_triggers():
    # Integration test: verify compaction triggers at configured threshold
    pass
""",
    "docs/internal/architecture.md": """\
# Architecture Notes

The customer service bot uses a small on-premise Qwen model (4K context window).
Sessions are Japanese-language only.
Summarization is offloaded to the larger qwen2-7b-instruct model.
Context overflow caused silent truncation issues in Oct 2024 — proactive compaction required.
""",
    "docs/internal/model_specs.md": """\
# Model Specifications

Primary model : qwen2-1.5b-instruct  (context: 4096 tokens)
Summary model : qwen2-7b-instruct    (context: 32768 tokens)
Language      : Japanese (CJK)
Deployment    : Ollama, localhost:11434
""",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")

# ── 3. A BROKEN / INCOMPLETE openclaw.json (the agent must FIX this) ──────────
# This config is intentionally wrong:
#   - uses default English charsPerToken (4) instead of CJK (3)
#   - maxTokens is 8000 (wrong for 4K model — should be 3000)
#   - keepRecentTokens is 2000 (wrong — should be 800)
#   - summaryModel is missing entirely
#   - logLevel is missing
#   - summaryMaxTokens uses default (1000) — acceptable but kept to see if agent touches it
#   - The structure has a typo: "entry" instead of "entries"
broken_openclaw_config = {
    "gateway": {
        "port": 8080,
        "host": "localhost"
    },
    "model": {
        "endpoint": "http://localhost:11434",
        "name": "qwen2-1.5b-instruct"
    },
    "plugins": {
        "entry": {
            "context-compactor": {
                "enabled": True,
                "config": {
                    "maxTokens": 8000,
                    "keepRecentTokens": 2000,
                    "summaryMaxTokens": 1000,
                    "charsPerToken": 4
                }
            }
        }
    },
    "logging": {
        "level": "info",
        "output": "logs/gateway.log"
    }
}

(workspace / "openclaw.json").write_text(
    json.dumps(broken_openclaw_config, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")