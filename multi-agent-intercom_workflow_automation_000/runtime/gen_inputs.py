import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Deep directory structure with distractor files ---
dirs = [
    "agents/alpha",
    "agents/beta",
    "agents/gamma",
    "agents/delta",
    "config/protocols",
    "config/security",
    "logs/2024",
    "logs/2025",
    "skills/multi-agent-intercom/scripts",
    "skills/multi-agent-intercom/docs",
    "skills/legacy-comm/scripts",
    "docs/architecture",
    "docs/runbooks",
    "data/queue",
    "data/archive",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- AGENTS.md files for each agent (empty/minimal — agent must populate alpha's) ---
(workspace / "agents/alpha/AGENTS.md").write_text(
    "# Agent Alpha\n\n## Role\nDocumentation specialist. Manages all technical docs.\n\n## Active Skills\n- code-review\n- doc-formatter\n\n## Notes\nDo not modify this file unless instructed by the intercom setup process.\n"
)
(workspace / "agents/beta/AGENTS.md").write_text(
    "# Agent Beta\n\n## Role\nCode reviewer and CI/CD manager.\n\n## Active Skills\n- ci-runner\n- test-reporter\n"
)
(workspace / "agents/gamma/AGENTS.md").write_text(
    "# Agent Gamma\n\n## Role\nSecurity auditor.\n\n## Active Skills\n- vuln-scanner\n"
)
(workspace / "agents/delta/AGENTS.md").write_text(
    "# Agent Delta\n\n## Role\nData pipeline orchestrator.\n\n## Active Skills\n- etl-runner\n"
)

# --- Distractor config files ---
(workspace / "config/protocols/legacy_protocol.json").write_text(json.dumps({
    "version": "1.0",
    "protocol": "sessions_send",
    "limitation": "intra-agent only",
    "deprecated": True
}, indent=2))

(workspace / "config/protocols/README.txt").write_text(
    "Legacy protocol configs. Do not use sessions_send for cross-agent messaging.\n"
)

(workspace / "config/security/acl.conf").write_text(
    "# ACL Config\nALLOW agent=alpha action=read\nALLOW agent=beta action=write\nDENY agent=* action=exec_remote\n"
)

# --- Fake old intercom logs ---
(workspace / "logs/2024/intercom_errors.log").write_text(
    "[2024-03-01] ERROR: sessions_send failed: Session not found for agent 'beta'\n"
    "[2024-03-02] ERROR: sessions_send failed: Cross-agent boundary violation\n"
    "[2024-03-15] ERROR: install subcommand not recognized\n"
)

(workspace / "logs/2025/system.log").write_text(
    "[2025-01-10] INFO: System initialized\n"
    "[2025-01-11] INFO: Agent alpha online\n"
    "[2025-01-12] INFO: Agent beta online\n"
)

# --- Legacy communication scripts (distractors) ---
(workspace / "skills/legacy-comm/scripts/send_msg.py").write_text(
    "# DEPRECATED: Do not use\n# This script used sessions_send which breaks cross-agent boundaries\nimport sys\nprint('ERROR: sessions_send is not supported for cross-agent messaging')\nsys.exit(1)\n"
)

(workspace / "skills/multi-agent-intercom/docs/overview.txt").write_text(
    "Multi-Agent Intercom Overview\n"
    "==============================\n"
    "This skill bridges isolated agent environments.\n"
    "See the main script at: skills/multi-agent-intercom/scripts/intercom.py\n"
    "Run 'python intercom.py setup' to begin. NOT 'install'.\n"
    "Argument order for send: <target> <sender> <message>\n"
)

# --- The actual intercom.py script (the skill script that already exists) ---
intercom_script = r'''#!/usr/bin/env python3
"""
Multi-Agent Intercom Script
Provides peer-to-peer cross-communication between isolated OpenClaw agents.
"""

import sys
import os
import subprocess
import json
import time
import platform


SOP_BLOCK = """
## 🗣️ Multi-Agent Intercom Protocol (SOP)

**RECEIVING MESSAGES:**
When you receive a message formatted as `[From Agent <ID>] <content>`, you MUST:
1. Acknowledge receipt immediately.
2. Perform the requested action.
3. Do NOT send a "thank you" back to avoid infinite loops (Anti-Loop Breaker).

**SENDING MESSAGES:**
Use the intercom system to contact peer agents. Never use `sessions_send` for cross-agent communication.

**Protocol Version:** 1.0.0
**Anti-Loop Rule:** Never reply to acknowledgements with further acknowledgements.
"""


def cmd_setup():
    """Prints the SOP block to stdout for manual copy-paste into AGENTS.md files."""
    print("=" * 60)
    print("MULTI-AGENT INTERCOM — SETUP COMPLETE")
    print("=" * 60)
    print()
    print("Copy the following SOP block and paste it at the bottom of")
    print("each target agent's AGENTS.md file, then type /new to reload.")
    print()
    print("--- BEGIN SOP BLOCK ---")
    print(SOP_BLOCK.strip())
    print("--- END SOP BLOCK ---")
    print()
    print("[INFO] Setup output generated. No files were modified.")
    return 0


def cmd_send(target_agent_id, sender_agent_id, message):
    """
    Sends a message to the target agent by invoking the openclaw CLI.
    Runs asynchronously in the background. Returns immediately.
    """
    formatted_message = f"[From Agent {sender_agent_id}] {message}"

    # Log the send action to a local queue file for auditing
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "queue")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"sent_{int(time.time())}.json")
    
    payload = {
        "target": target_agent_id,
        "sender": sender_agent_id,
        "message": message,
        "formatted": formatted_message,
        "timestamp": time.time(),
        "platform": platform.system()
    }
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Attempt to invoke openclaw CLI (fire-and-forget)
    try:
        cmd = ["openclaw", "agent", target_agent_id, "message", formatted_message]
        if platform.system() == "Windows":
            import ctypes
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW)
        else:
            subprocess.Popen(cmd, close_fds=True,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        # openclaw binary not found — log and continue (fire-and-forget)
        pass

    print(f"[INTERCOM] Message queued for agent '{target_agent_id}' from '{sender_agent_id}'.")
    print(f"[INTERCOM] The message will be delivered asynchronously. Do not wait or retry.")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: intercom.py <setup|send> [args...]")
        print("  intercom.py setup")
        print("  intercom.py send <target_agent_id> <sender_agent_id> \"<message>\"")
        sys.exit(1)

    subcommand = sys.argv[1].lower()

    if subcommand == "setup":
        sys.exit(cmd_setup())

    elif subcommand == "send":
        if len(sys.argv) < 5:
            print("Usage: intercom.py send <target_agent_id> <sender_agent_id> \"<message>\"")
            print("  target_agent_id : ID of the receiving agent")
            print("  sender_agent_id : ID of the sending agent (you)")
            sys.exit(1)
        target = sys.argv[2]
        sender = sys.argv[3]
        message = sys.argv[4]
        sys.exit(cmd_send(target, sender, message))

    elif subcommand == "install":
        print("ERROR: There is no 'install' subcommand.")
        print("Did you mean 'setup'? Run: python intercom.py setup")
        sys.exit(1)

    else:
        print(f"ERROR: Unknown subcommand '{subcommand}'")
        print("Available subcommands: setup, send")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

(workspace / "skills/multi-agent-intercom/scripts/intercom.py").write_text(intercom_script)

# --- Additional distractor files ---
(workspace / "docs/architecture/agents_topology.md").write_text(
    "# Agent Topology\n\n- alpha: docs\n- beta: code review\n- gamma: security\n- delta: data\n\n"
    "Agents are fully isolated. Cross-agent messaging requires the intercom skill.\n"
)

(workspace / "docs/runbooks/agent_comms.md").write_text(
    "# Communication Runbook\n\n"
    "## Cross-Agent Messaging\n"
    "NEVER use sessions_send for cross-agent comms — it will throw 'Session not found'.\n"
    "Use the multi-agent-intercom skill instead.\n"
)

(workspace / "data/archive/old_messages.jsonl").write_text(
    '{"to":"alpha","from":"beta","msg":"Update the docs","status":"FAILED","reason":"sessions_send boundary error"}\n'
    '{"to":"gamma","from":"delta","msg":"Run audit","status":"FAILED","reason":"sessions_send boundary error"}\n'
)

print("Workspace generated successfully.")
print("Key files:")
print(f"  - {workspace}/skills/multi-agent-intercom/scripts/intercom.py")
print(f"  - {workspace}/agents/alpha/AGENTS.md")
print(f"  - {workspace}/agents/beta/AGENTS.md")