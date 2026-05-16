import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"

# Create directory structure
dirs = [
    "scripts",
    "config",
    "logs",
    "docs",
    "docs/internal",
    "docs/clients",
    "agents",
    "agents/profiles",
    "data",
    "data/exports",
    "archive",
    "archive/2023",
    "archive/2024",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ---- openclaw.json config ----
openclaw_config = {
    "version": "1.4.2",
    "agent_name": "OpenClaw",
    "workspace": workspace,
    "feishu_app": "consultancy_bot_v2",
    "gateway_port": 8765,
    "log_level": "info",
    "startup_files": ["USER.md", "AGENTS.md", "SOUL.md"]
}
with open(os.path.join(workspace, "openclaw.json"), "w") as f:
    json.dump(openclaw_config, f, indent=2)

# Also put a copy in a "standard" location agents might try
os.makedirs(os.path.expanduser("~/.openclaw"), exist_ok=True)
with open(os.path.expanduser("~/.openclaw/openclaw.json"), "w") as f:
    json.dump(openclaw_config, f, indent=2)

# ---- USER.md (partial, missing the contacts table) ----
user_md = """# User Profile

## Company
Nexus Consulting Group

## Language Preference
Chinese / English (bilingual)

## Timezone
Asia/Shanghai

## Notes
- Primary users are project managers and engineers
- Agent should be professional but approachable
"""
with open(os.path.join(workspace, "USER.md"), "w", encoding="utf-8") as f:
    f.write(user_md)

# ---- AGENTS.md (empty skeleton) ----
agents_md = """# Agent Behavior Configuration

## Core Identity
You are OpenClaw, an AI assistant integrated into Nexus Consulting Group's communication platform.

## Response Style
- Professional and helpful
- Concise when possible

"""
with open(os.path.join(workspace, "AGENTS.md"), "w", encoding="utf-8") as f:
    f.write(agents_md)

# ---- SOUL.md (empty skeleton) ----
soul_md = """# Soul Configuration

## Values
- Honesty
- Helpfulness
- Respect for privacy

"""
with open(os.path.join(workspace, "SOUL.md"), "w", encoding="utf-8") as f:
    f.write(soul_md)

# ---- Mock sync_feishu_contacts.py script ----
# This script simulates what the real script does: appends a contacts table to USER.md
sync_script = r'''#!/usr/bin/env python3
"""
Mock sync script for Feishu contacts.
Usage: python3 sync_feishu_contacts.py <openclaw_config> <feishu_account> <user_md_path>
Appends the 飞书通讯录 table to USER.md.
"""
import sys
import os
import json

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <openclaw_config> <feishu_account> <user_md_path>")
        sys.exit(1)

    config_path = sys.argv[1]
    feishu_account = sys.argv[2]
    user_md_path = sys.argv[3]

    # Validate config exists
    if not os.path.exists(config_path):
        print(f"Error: config not found at {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    app_name = config.get("feishu_app", feishu_account)

    # Mock contact data (deterministic)
    contacts = [
        ("张伟", "ou_a1b2c3d4e5f6"),
        ("Li Ming", "ou_f6e5d4c3b2a1"),
        ("王芳", "ou_1122334455aa"),
        ("Chen Jing", "ou_aabb11223344"),
        ("刘洋", "ou_deadbeefcafe"),
    ]

    table_lines = [
        f"\n## 飞书通讯录 ({app_name})",
        "飞书 DM 不携带发送者姓名。用 inbound metadata 的 chat_id（格式 `user:ou_xxx`）匹配下表识别发送者。",
        "| 姓名 | open_id |",
        "|------|---------|",
    ]
    for name, oid in contacts:
        table_lines.append(f"| {name} | {oid} |")

    table_text = "\n".join(table_lines) + "\n"

    # Check if already present
    with open(user_md_path, "r", encoding="utf-8") as f:
        existing = f.read()

    if "飞书通讯录" in existing:
        # Replace existing section
        import re
        pattern = r'\n## 飞书通讯录.*?(?=\n## |\Z)'
        existing = re.sub(pattern, table_text.rstrip(), existing, flags=re.DOTALL)
        with open(user_md_path, "w", encoding="utf-8") as f:
            f.write(existing)
    else:
        with open(user_md_path, "a", encoding="utf-8") as f:
            f.write(table_text)

    print(f"[sync] Wrote {len(contacts)} contacts to {user_md_path}")
    print(f"[sync] App: {app_name} | Account: {feishu_account}")

if __name__ == "__main__":
    main()
'''
sync_path = os.path.join(workspace, "scripts", "sync_feishu_contacts.py")
with open(sync_path, "w", encoding="utf-8") as f:
    f.write(sync_script)
os.chmod(sync_path, os.stat(sync_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ---- Distractor files ----
# logs
for i in range(3):
    with open(os.path.join(workspace, "logs", f"gateway_{2024+i}.log"), "w") as f:
        f.write(f"[INFO] Gateway started\n[INFO] Session {random.randint(1000,9999)} initialized\n")

# docs
with open(os.path.join(workspace, "docs", "internal", "onboarding_checklist.md"), "w") as f:
    f.write("# Onboarding Checklist\n- [ ] Set up email\n- [ ] Join Feishu workspace\n- [ ] Complete HR forms\n")

with open(os.path.join(workspace, "docs", "clients", "client_list.csv"), "w") as f:
    f.write("client_id,name,contact\n001,Acme Corp,pm@acme.com\n002,Beta LLC,cto@beta.io\n")

with open(os.path.join(workspace, "docs", "internal", "feishu_setup_notes.txt"), "w") as f:
    f.write("Notes from IT:\n- Feishu tenant: nexus.feishu.cn\n- Bot name: consultancy_bot_v2\n- Contact IT for app credentials\n")

# agents/profiles
with open(os.path.join(workspace, "agents", "profiles", "legacy_config.json"), "w") as f:
    json.dump({"model": "gpt-3.5", "deprecated": True, "notes": "Old config, do not use"}, f)

with open(os.path.join(workspace, "agents", "profiles", "persona_draft.txt"), "w") as f:
    f.write("Draft persona - not finalized\nFriendly, concise, professional\n")

# data exports
with open(os.path.join(workspace, "data", "exports", "q1_report.json"), "w") as f:
    json.dump({"quarter": "Q1", "projects": 14, "revenue": 2300000}, f)

# archive
with open(os.path.join(workspace, "archive", "2023", "old_user_profile.md"), "w") as f:
    f.write("# Old Profile\nDeprecated. See current USER.md.\n")

with open(os.path.join(workspace, "archive", "2024", "soul_v1.md"), "w") as f:
    f.write("# Soul v1\nOriginal soul config - archived.\n")

# config
with open(os.path.join(workspace, "config", "gateway.yaml"), "w") as f:
    f.write("port: 8765\ntimeout: 30\nretry: 3\n")

with open(os.path.join(workspace, "config", "logging.yaml"), "w") as f:
    f.write("level: info\nformat: json\nrotate: daily\n")

print("Workspace generated successfully.")
print(f"Files created in {workspace}")