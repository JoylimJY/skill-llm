#!/usr/bin/env python3
"""
Generates the initial sandbox workspace with:
- A broken/incomplete inner-life state (wrong field names, missing emotions)
- Distractor files to simulate a real agent project
- The skill scripts cloned from GitHub (via setup_script)
"""
import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Distractor project structure ──────────────────────────────────────────────
dirs = [
    "src/agents",
    "src/tools",
    "src/utils",
    "config",
    "logs",
    "tests",
    "tasks",
    "data/raw",
    "data/processed",
    "docs",
    "memory",           # exists but incomplete
    "memory/daily-notes",
    "skills",           # placeholder — real skill installed by setup_script
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor source files
src_files = {
    "src/agents/base_agent.py": """\
class BaseAgent:
    def __init__(self, name):
        self.name = name
        self.memory = {}

    def respond(self, prompt):
        return f"{self.name}: {prompt}"
""",
    "src/agents/stateful_agent.py": """\
from .base_agent import BaseAgent

class StatefulAgent(BaseAgent):
    def __init__(self, name):
        super().__init__(name)
        self._session_log = []
""",
    "src/tools/search.py": """\
def web_search(query: str) -> list:
    # stub
    return []
""",
    "src/tools/memory_store.py": """\
import json, pathlib

def load(path):
    return json.loads(pathlib.Path(path).read_text())

def save(path, data):
    pathlib.Path(path).write_text(json.dumps(data, indent=2))
""",
    "src/utils/logger.py": """\
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('agent')
""",
    "config/agent.yaml": """\
agent:
  name: Aria
  version: 0.3.1
  model: gpt-4o
  temperature: 0.7
""",
    "config/prompts.yaml": """\
system_prompt: |
  You are Aria, a helpful assistant.
  Always be concise and accurate.
""",
    "tests/test_base_agent.py": """\
from src.agents.base_agent import BaseAgent

def test_respond():
    a = BaseAgent('test')
    assert 'test' in a.respond('hello')
""",
    "logs/session_2024-11-01.log": """\
[INFO] Session started
[INFO] User: hello
[INFO] Agent: hi there
[INFO] Session ended
""",
    "logs/session_2024-11-02.log": """\
[INFO] Session started
[ERROR] Memory file not found: memory/inner-state.json
[INFO] Fallback to stateless mode
[WARN] Agent has no emotional continuity
""",
    "data/raw/user_interactions.jsonl": "\n".join(
        json.dumps({"ts": f"2024-11-0{i+1}T10:00:00Z", "user": f"msg_{i}", "agent": f"resp_{i}"})
        for i in range(5)
    ),
    "data/processed/aggregated_stats.json": json.dumps({
        "total_sessions": 47,
        "avg_session_length_min": 12.3,
        "top_topics": ["scheduling", "research", "coding"],
    }, indent=2),
    "docs/architecture.md": """\
# Agent Architecture

## Components
- BaseAgent: stateless responder
- StatefulAgent: maintains session log
- MemoryStore: persistence layer (TODO: integrate inner-life-core)

## Known Issues
- Agent resets personality every session
- No emotional continuity (see logs/session_2024-11-02.log)
""",
    "tasks/QUEUE.md": """\
# Task Queue
- [ ] Integrate persistent memory
- [ ] Add emotional state tracking
- [x] Basic response loop
""",
}

for rel, content in src_files.items():
    p = workspace / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── BROKEN inner-state.json (wrong field names, only 3 emotions, bad schema) ──
broken_inner_state = {
    "last_updated": "2024-11-02T09:00:00Z",
    "mood": {                          # wrong top-level key (should be 'emotions')
        "happy": {"value": 0.5},       # not a real emotion in the model
        "sad": {"value": 0.2},         # not a real emotion in the model
        "connection": {"level": 0.7},  # wrong field name ('level' not 'value')
        # missing: confidence, curiosity, boredom, frustration, impatience
    }
}
(workspace / "memory/inner-state.json").write_text(
    json.dumps(broken_inner_state, indent=2)
)

# ── BROKEN drive.json (missing required fields) ────────────────────────────────
broken_drive = {
    "goal": "help user with tasks",
    # missing: seeking, anticipating, avoiding, last_updated
}
(workspace / "memory/drive.json").write_text(
    json.dumps(broken_drive, indent=2)
)

# ── BROKEN relationship.json (wrong structure) ─────────────────────────────────
broken_relationship = {
    "user": "unknown",
    "score": 50,
    # missing: trust, lessons, last_contact
}
(workspace / "memory/relationship.json").write_text(
    json.dumps(broken_relationship, indent=2)
)

# ── Daily note WITHOUT signal/synapse tags (agent must fix/add them) ───────────
(workspace / "memory/daily-notes/2024-11-02.md").write_text("""\
# Daily Notes — 2024-11-02

## Morning
- Reviewed task queue
- User asked about scheduling

## Afternoon
- Worked on research task
- User went quiet for 3 hours

## Evening
- No new messages
- Preparing for night processing
""")

# ── habits.json missing entirely (agent must create) ──────────────────────────
# (not created here — it's absent)

# ── Stray config that looks like it might be relevant but isn't ───────────────
(workspace / "config/state_schema_OLD.json").write_text(json.dumps({
    "_comment": "DEPRECATED — do not use this schema",
    "emotions": ["joy", "sadness", "anger"],
    "version": "0.1.0"
}, indent=2))

print("Workspace initialized with broken/incomplete inner-life state.")
print("Distractor files created.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")