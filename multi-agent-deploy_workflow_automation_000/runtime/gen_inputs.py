#!/usr/bin/env python3
"""
Sets up the ~/.openclaw environment simulating an existing 2-agent deployment
(assistant + assistant2), then plants the deploy script, expecting the agent
to deploy assistant3.
"""
import os
import json
import pathlib
import stat

BASE = pathlib.Path("/home/admin/.openclaw")

# ── directory skeleton ──────────────────────────────────────────────────────

dirs = [
    BASE / "agents" / "assistant" / "agent",
    BASE / "agents" / "assistant2" / "agent",
    BASE / "workspace-assistant",
    BASE / "workspace-assistant2",
    BASE / "workspace" / "skills" / "multi-agent-deploy" / "scripts",
    BASE / "workspace" / "skills" / "multi-agent-deploy" / "docs",
    BASE / "workspace" / "skills" / "multi-agent-deploy" / "tests",
    BASE / "workspace" / "logs",
    BASE / "workspace" / "tmp",
    BASE / "workspace" / "cache" / "models",
    BASE / "workspace" / "cache" / "embeddings",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── template workspace files ────────────────────────────────────────────────

(BASE / "workspace-assistant" / "SOUL.md").write_text(
    "# Soul\nYou are a helpful daily assistant.\n"
)
(BASE / "workspace-assistant" / "AGENTS.md").write_text(
    "# Agents\n## assistant\nA general-purpose assistant agent.\n"
)
(BASE / "workspace-assistant" / "USER.md").write_text(
    "# User Preferences\n- Language: zh-CN\n- Tone: friendly\n"
)

(BASE / "workspace-assistant2" / "SOUL.md").write_text(
    "# Soul\nYou are a helpful daily assistant.\n"
)
(BASE / "workspace-assistant2" / "AGENTS.md").write_text(
    "# Agents\n## assistant2\nA second general-purpose assistant agent.\n"
)
(BASE / "workspace-assistant2" / "USER.md").write_text(
    "# User Preferences\n- Language: zh-CN\n- Tone: professional\n"
)

# ── distractor files ────────────────────────────────────────────────────────

(BASE / "workspace" / "logs" / "gateway.log").write_text(
    "[INFO] Gateway started\n[INFO] Loaded agents: assistant, assistant2\n"
)
(BASE / "workspace" / "logs" / "deploy.log").write_text(
    "2024-01-10 12:00:00 INFO Deployed assistant\n"
    "2024-01-11 09:30:00 INFO Deployed assistant2\n"
)
(BASE / "workspace" / "tmp" / "session_cache.json").write_text(
    json.dumps({"sessions": [], "last_flush": "2024-01-11T09:30:00Z"})
)
(BASE / "workspace" / "cache" / "models" / "manifest.json").write_text(
    json.dumps({"models": ["dashscope/qwen3.5-plus", "dashscope/qwen3-max"]})
)
(BASE / "workspace" / "cache" / "embeddings" / "index.bin").write_bytes(
    b"\x00" * 64
)
(BASE / "workspace" / "skills" / "multi-agent-deploy" / "docs" / "changelog.md").write_text(
    "# Changelog\n## v1.2.0\n- Auto numbering support\n## v1.1.0\n- Added workspace copy\n"
)
(BASE / "workspace" / "skills" / "multi-agent-deploy" / "tests" / "test_deploy.py").write_text(
    "import unittest\n\nclass TestDeploy(unittest.TestCase):\n    def test_placeholder(self):\n        pass\n"
)
(BASE / "agents" / "assistant" / "agent" / "config.yaml").write_text(
    "model: dashscope/qwen3.5-plus\nmax_tokens: 4096\ntemperature: 0.7\n"
)
(BASE / "agents" / "assistant2" / "agent" / "config.yaml").write_text(
    "model: dashscope/qwen3.5-plus\nmax_tokens: 4096\ntemperature: 0.7\n"
)

# ── openclaw.json ───────────────────────────────────────────────────────────

config = {
    "version": "1.2.0",
    "gateway": {
        "host": "127.0.0.1",
        "port": 8080,
        "log_level": "info"
    },
    "agents": [
        {
            "id": "assistant",
            "name": "日常助手",
            "workspace": "/home/admin/.openclaw/workspace-assistant",
            "agentDir": "/home/admin/.openclaw/agents/assistant/agent",
            "model": "dashscope/qwen3.5-plus"
        },
        {
            "id": "assistant2",
            "name": "日常助手 2",
            "workspace": "/home/admin/.openclaw/workspace-assistant2",
            "agentDir": "/home/admin/.openclaw/agents/assistant2/agent",
            "model": "dashscope/qwen3.5-plus"
        }
    ],
    "bindings": [
        {"channel": "web", "agentId": "assistant"},
        {"channel": "mobile", "agentId": "assistant2"}
    ]
}
(BASE / "openclaw.json").write_text(json.dumps(config, ensure_ascii=False, indent=2))

# ── deploy-agent.py (the actual skill script) ───────────────────────────────

deploy_script = r'''#!/usr/bin/env python3
"""
deploy-agent.py  —  Multi-Agent Deploy skill script
Auto-detects the next available assistant number and creates:
  - workspace-assistantX/  (with SOUL.md, AGENTS.md, USER.md copied from template)
  - agents/assistantX/agent/
  - Updates ~/.openclaw/openclaw.json
"""
import json
import pathlib
import re
import shutil
import sys

BASE = pathlib.Path("/home/admin/.openclaw")
CONFIG_PATH = BASE / "openclaw.json"
TEMPLATE_WORKSPACE = BASE / "workspace-assistant"
AGENTS_DIR = BASE / "agents"

def detect_next_number():
    """Find the highest existing assistantN number and return N+1 (min 2)."""
    existing = set()
    # Check agents directory
    if AGENTS_DIR.exists():
        for d in AGENTS_DIR.iterdir():
            m = re.fullmatch(r"assistant(\d+)", d.name)
            if m:
                existing.add(int(m.group(1)))
    # Also check workspaces
    if BASE.exists():
        for d in BASE.iterdir():
            m = re.fullmatch(r"workspace-assistant(\d+)", d.name)
            if m:
                existing.add(int(m.group(1)))
    if not existing:
        return 2
    return max(existing) + 1

def main():
    next_n = detect_next_number()
    agent_id = f"assistant{next_n}"
    new_workspace = BASE / f"workspace-{agent_id}"
    new_agent_dir = AGENTS_DIR / agent_id / "agent"

    # --- workspace ---
    if new_workspace.exists():
        print(f"WARNING: {new_workspace} already exists, skipping workspace creation.", file=sys.stderr)
    else:
        new_workspace.mkdir(parents=True)
        for fname in ("SOUL.md", "AGENTS.md", "USER.md"):
            src = TEMPLATE_WORKSPACE / fname
            if src.exists():
                shutil.copy2(src, new_workspace / fname)
        print(f"Created workspace: {new_workspace}")

    # --- agent dir ---
    if new_agent_dir.exists():
        print(f"WARNING: {new_agent_dir} already exists, skipping agent dir creation.", file=sys.stderr)
    else:
        new_agent_dir.mkdir(parents=True)
        print(f"Created agent dir: {new_agent_dir}")

    # --- update config ---
    config = json.loads(CONFIG_PATH.read_text())
    new_entry = {
        "id": agent_id,
        "name": f"日常助手 {next_n}",
        "workspace": str(new_workspace),
        "agentDir": str(new_agent_dir),
        "model": "dashscope/qwen3.5-plus"
    }
    # Avoid duplicates
    existing_ids = {a["id"] for a in config.get("agents", [])}
    if agent_id in existing_ids:
        print(f"WARNING: agent {agent_id} already in config, skipping.", file=sys.stderr)
    else:
        config.setdefault("agents", []).append(new_entry)
        CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2))
        print(f"Updated config: added {agent_id}")

    print(f"\nDeployment complete: {agent_id}")
    print(f"  workspace : {new_workspace}")
    print(f"  agentDir  : {new_agent_dir}")
    print(f"  model     : dashscope/qwen3.5-plus")

if __name__ == "__main__":
    main()
'''

script_path = BASE / "workspace" / "skills" / "multi-agent-deploy" / "scripts" / "deploy-agent.py"
script_path.write_text(deploy_script)
script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

print("Sandbox setup complete.")
print(f"  BASE: {BASE}")
print(f"  Existing agents: assistant, assistant2")
print(f"  Expected next deployment: assistant3")