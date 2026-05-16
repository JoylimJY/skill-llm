import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

HOME = Path("/home/axelhu")

# ─── 1. Build the ~/.openclaw skeleton ───────────────────────────────────────
openclaw_root = HOME / ".openclaw"
openclaw_root.mkdir(parents=True, exist_ok=True)

# ─── 2. Create the existing "primary" agent (agent-main) workspace ─────────
primary_agent_id = "agent-main"
primary_ws = openclaw_root / f"workspace-{primary_agent_id}"
primary_agent_dir = primary_ws / "agent"
primary_agent_dir.mkdir(parents=True, exist_ok=True)

primary_agents_dir = openclaw_root / "agents" / primary_agent_id / "agent"
primary_agents_dir.mkdir(parents=True, exist_ok=True)

# Primary agent template files (these serve as the "originals" to copy from)
(primary_ws / "IDENTITY.md").write_text(
    "# Identity\nName: MainBot\nEmoji: 🤖\nStyle: Professional\n"
)
(primary_ws / "SOUL.md").write_text(
    "# Soul\nPersonality: Helpful, concise, reliable.\nTone: Neutral\n"
)
(primary_ws / "USER.md").write_text(
    "# User\nOwner: axelhu\nPreferences: Markdown output preferred.\n"
)
(primary_ws / "AGENTS.md").write_text(
    "# Agents Protocol\nVersion: 1.0\nBehavior: Respond only when addressed.\nEscalation: Notify owner on error.\n"
)
(primary_ws / "MEMORY.md").write_text(
    "# Memory (Hot Cache)\nLast interaction: 2024-01-01\nContext slots: 8\n"
)

# Primary agent/models.json  — provider is "openai", model is "gpt-4o"
primary_models = {
    "primary": {
        "provider": "openai",
        "modelId": "gpt-4o",
        "temperature": 0.7,
        "maxTokens": 4096
    },
    "fallbacks": []
}
(primary_agent_dir / "models.json").write_text(json.dumps(primary_models, indent=2))

# Primary agent/auth.json
primary_auth = {
    "openai": {
        "apiKey": "sk-placeholder-main"
    }
}
(primary_agent_dir / "auth.json").write_text(json.dumps(primary_auth, indent=2))

# ─── 3. Create the skills/agent-creator/templates directory ──────────────────
templates_dir = openclaw_root / "skills" / "agent-creator" / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)

(templates_dir / "IDENTITY.md").write_text(
    "# Identity\nName: {AgentName}\nEmoji: 🐾\nStyle: Friendly\n"
)
(templates_dir / "SOUL.md").write_text(
    "# Soul\nPersonality: Empathetic, patient, solution-oriented.\nTone: Warm\n"
)
(templates_dir / "USER.md").write_text(
    "# User\nOwner: TBD\nPreferences: Clear and structured responses.\n"
)
(templates_dir / "AGENTS.md").write_text(
    "# Agents Protocol\nVersion: 1.0\nBehavior: Always confirm before action.\nEscalation: Ping owner.\n"
)
(templates_dir / "MEMORY.md").write_text(
    "# Memory (Hot Cache)\nLast interaction: N/A\nContext slots: 4\n"
)

# ─── 4. Create the existing openclaw.json ─────────────────────────────────────
openclaw_json = {
    "version": "2.1.0",
    "agents": {
        "list": [
            {
                "id": "agent-main",
                "workspace": "/home/axelhu/.openclaw/workspace-agent-main",
                "model": {
                    "primary": "openai/gpt-4o",
                    "fallbacks": []
                }
            }
        ]
    },
    "agentToAgent": {
        "allow": ["agent-main"],
        "maxHops": 3
    },
    "bindings": [],
    "channels": {
        "accounts": {}
    },
    "logging": {
        "level": "info",
        "destination": "~/.openclaw/logs/"
    }
}
(openclaw_root / "openclaw.json").write_text(json.dumps(openclaw_json, indent=2))

# ─── 5. Create realistic distractor files & directories ───────────────────────
distractors = [
    openclaw_root / "logs" / "2024-01-15.log",
    openclaw_root / "logs" / "2024-01-16.log",
    openclaw_root / "logs" / "errors.log",
    openclaw_root / "cache" / "embeddings" / "chunk_001.bin",
    openclaw_root / "cache" / "embeddings" / "chunk_002.bin",
    openclaw_root / "cache" / "sessions" / "sess_a1b2c3.json",
    openclaw_root / "cache" / "sessions" / "sess_d4e5f6.json",
    openclaw_root / "skills" / "web-search" / "SKILL.md",
    openclaw_root / "skills" / "web-search" / "handler.py",
    openclaw_root / "skills" / "code-runner" / "SKILL.md",
    openclaw_root / "skills" / "code-runner" / "sandbox.py",
    openclaw_root / "plugins" / "feishu-adapter" / "README.md",
    openclaw_root / "plugins" / "feishu-adapter" / "config.example.json",
    openclaw_root / "plugins" / "slack-adapter" / "README.md",
    HOME / ".openclaw" / "tmp" / "install_manifest.txt",
]

distractor_contents = [
    "2024-01-15 INFO Agent started\n2024-01-15 INFO Loaded 3 skills\n",
    "2024-01-16 INFO Heartbeat OK\n",
    "2024-01-15 ERROR Connection timeout after 30s\n",
    b"\x00\x01\x02\x03" * 128,
    b"\x00\x04\x05\x06" * 64,
    json.dumps({"sessionId": "a1b2c3", "start": "2024-01-15T10:00:00Z"}),
    json.dumps({"sessionId": "d4e5f6", "start": "2024-01-16T08:30:00Z"}),
    "# Web Search Skill\nSearches the web using DuckDuckGo.\n",
    "def search(query): pass\n",
    "# Code Runner Skill\nRuns Python snippets in a sandbox.\n",
    "def run(code): pass\n",
    "# Feishu Adapter Plugin\nHandles incoming Feishu webhook events.\n",
    json.dumps({"appId": "cli_example", "appSecret": "CHANGE_ME"}),
    "# Slack Adapter Plugin\nHandles Slack RTM events.\n",
    "openclaw==2.1.0\nplugin-feishu==1.3.2\nplugin-slack==1.1.0\n",
]

for path, content in zip(distractors, distractor_contents):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content)

# ─── 6. Create an intentionally incomplete partial attempt directory ──────────
# Simulate a half-done previous attempt that should NOT confuse the agent
partial_ws = openclaw_root / "workspace-agent-support" 
partial_ws.mkdir(parents=True, exist_ok=True)
(partial_ws / "IDENTITY.md").write_text("# Identity\nName: INCOMPLETE\n")
# Deliberately missing SOUL.md, USER.md, AGENTS.md, MEMORY.md, agent/ dir

print("Workspace generation complete.")
print(f"openclaw root: {openclaw_root}")
print(f"Primary agent workspace: {primary_ws}")
print(f"Templates dir: {templates_dir}")