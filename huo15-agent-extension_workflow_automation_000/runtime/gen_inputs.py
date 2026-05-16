import os
import random
import hashlib

random.seed(42)

HOME = os.path.expanduser("~")
MAIN_WORKSPACE = os.path.join(HOME, ".openclaw", "workspace")
DYNAMIC_WORKSPACE = os.path.join(HOME, ".openclaw", "workspace-wecom-default-dm-xun")

# --- Config file contents for MAIN workspace (authoritative) ---
MAIN_CONFIG_FILES = {
    "AGENTS.md": """# Agent Configuration
version: 2.1.0
channel: wecom
role: customer-service
max_sessions: 100
timeout: 30s
last_updated: 2024-06-15
""",
    "SOUL.md": """# Soul Definition
persona: Friendly enterprise assistant
tone: Professional
language: zh-CN
empathy_level: high
boundaries:
  - no_politics
  - no_adult_content
""",
    "TOOLS.md": """# Tools Configuration
enabled_tools:
  - search
  - calendar
  - crm_lookup
  - ticket_create
  - faq_retrieve
rate_limit: 60/min
""",
    "IDENTITY.md": """# Identity Definition
name: 小助理
org: Acme Corp
department: Customer Success
employee_id: BOT-2024-001
""",
    "USER.md": """# User Configuration
default_greeting: 您好，有什么可以帮助您的？
escalation_threshold: 3
survey_enabled: true
data_retention_days: 90
""",
    "HEARTBEAT.md": """# Heartbeat Configuration
interval_seconds: 30
endpoint: /api/health
alert_email: ops@acme.com
retry_count: 3
""",
    "MEMORY.md": """# Memory Configuration
max_context_turns: 20
persistence: redis
ttl_hours: 24
embedding_model: text-embedding-ada-002
""",
}

# --- Skills directory files for MAIN workspace ---
MAIN_SKILLS = {
    "skills/greet.js": "// Greeting skill\nmodule.exports = async (ctx) => { return ctx.reply('您好！'); };\n",
    "skills/faq.js": "// FAQ skill\nmodule.exports = async (ctx) => { return ctx.lookup(ctx.query); };\n",
    "skills/escalate.js": "// Escalation skill\nmodule.exports = async (ctx) => { ctx.escalate(); };\n",
    "skills/ticket.js": "// Ticket creation\nmodule.exports = async (ctx) => { ctx.createTicket(ctx.issue); };\n",
    "skills/survey.js": "// Survey skill\nmodule.exports = async (ctx) => { ctx.sendSurvey(); };\n",
}

# --- Memory directory files for MAIN workspace ---
MAIN_MEMORY = {
    "memory/user_prefs.json": '{"theme": "light", "lang": "zh-CN", "notifications": true}\n',
    "memory/session_cache.json": '{"active_sessions": 42, "peak_time": "14:00-16:00"}\n',
    "memory/knowledge_base.json": '{"version": "3.2.1", "entries": 15024, "last_sync": "2024-06-15T08:00:00Z"}\n',
}

# --- Create MAIN workspace ---
os.makedirs(MAIN_WORKSPACE, exist_ok=True)

for fname, content in MAIN_CONFIG_FILES.items():
    fpath = os.path.join(MAIN_WORKSPACE, fname)
    with open(fpath, "w") as f:
        f.write(content)

for fpath_rel, content in MAIN_SKILLS.items():
    full = os.path.join(MAIN_WORKSPACE, fpath_rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

for fpath_rel, content in MAIN_MEMORY.items():
    full = os.path.join(MAIN_WORKSPACE, fpath_rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# --- Create DYNAMIC workspace with STALE/PARTIAL pre-existing state ---
os.makedirs(DYNAMIC_WORKSPACE, exist_ok=True)
os.makedirs(os.path.join(DYNAMIC_WORKSPACE, "skills"), exist_ok=True)
os.makedirs(os.path.join(DYNAMIC_WORKSPACE, "memory"), exist_ok=True)

# Stale config files (old version, wrong content - should be overwritten)
STALE_CONFIG = {
    "AGENTS.md": "# Agent Configuration\nversion: 1.0.0\nchannel: whatsapp\n[STALE - DO NOT USE]\n",
    "SOUL.md": "# Soul Definition\npersona: Generic bot\n[STALE]\n",
    "TOOLS.md": "# Tools Configuration\nenabled_tools: []\n[STALE]\n",
    # IDENTITY.md, USER.md, HEARTBEAT.md, MEMORY.md are missing - must be copied fresh
}

for fname, content in STALE_CONFIG.items():
    fpath = os.path.join(DYNAMIC_WORKSPACE, fname)
    with open(fpath, "w") as f:
        f.write(content)

# Partial stale skills directory (one old file + one that doesn't exist in main)
STALE_SKILLS = {
    "skills/greet.js": "// OLD greeting skill\nmodule.exports = () => 'old';\n",  # stale, should be overwritten
    "skills/deprecated_handler.js": "// deprecated\nmodule.exports = () => {};\n",  # extra file, should remain
}
for fpath_rel, content in STALE_SKILLS.items():
    full = os.path.join(DYNAMIC_WORKSPACE, fpath_rel)
    with open(full, "w") as f:
        f.write(content)

# Partial stale memory
STALE_MEMORY = {
    "memory/user_prefs.json": '{"theme": "dark", "lang": "en-US"}\n',  # stale, should be overwritten
}
for fpath_rel, content in STALE_MEMORY.items():
    full = os.path.join(DYNAMIC_WORKSPACE, fpath_rel)
    with open(full, "w") as f:
        f.write(content)

# --- Distractor files and directories ---
OPENCLAW_DIR = os.path.join(HOME, ".openclaw")

# A decoy workspace with a different agent
decoy_workspace = os.path.join(OPENCLAW_DIR, "workspace-old-archive-2023")
os.makedirs(decoy_workspace, exist_ok=True)
with open(os.path.join(decoy_workspace, "AGENTS.md"), "w") as f:
    f.write("# Old archived agent\nDO NOT USE\n")

# Extensions directory (as referenced in SKILL.md)
ext_src = os.path.join(OPENCLAW_DIR, "extensions", "wecom", "src")
ext_dist = os.path.join(OPENCLAW_DIR, "extensions", "wecom", "dist", "src")
os.makedirs(ext_src, exist_ok=True)
os.makedirs(ext_dist, exist_ok=True)
with open(os.path.join(ext_src, "dynamic-agent.ts"), "w") as f:
    f.write("// TypeScript source - reference implementation\n")
with open(os.path.join(ext_dist, "dynamic-agent.js"), "w") as f:
    f.write("// Compiled JS - reference implementation\n")

# Logs directory (distractor)
logs_dir = os.path.join(OPENCLAW_DIR, "logs")
os.makedirs(logs_dir, exist_ok=True)
for i in range(5):
    with open(os.path.join(logs_dir, f"agent_{i}.log"), "w") as f:
        f.write(f"[2024-06-{i+1:02d}] Session log entry {random.randint(1000,9999)}\n")

# Config backup directory (distractor)
backup_dir = os.path.join(OPENCLAW_DIR, "backups", "2024-05")
os.makedirs(backup_dir, exist_ok=True)
for fname in ["AGENTS.md", "SOUL.md", "TOOLS.md"]:
    with open(os.path.join(backup_dir, fname), "w") as f:
        f.write(f"# BACKUP - May 2024 - {fname}\n[OUTDATED BACKUP]\n")

# A workspace-staging directory (decoy - different naming pattern)
staging = os.path.join(OPENCLAW_DIR, "workspace-staging")
os.makedirs(staging, exist_ok=True)
with open(os.path.join(staging, "AGENTS.md"), "w") as f:
    f.write("# Staging workspace\n[NOT A REAL DYNAMIC AGENT]\n")

# Global config (distractor)
with open(os.path.join(OPENCLAW_DIR, "config.json"), "w") as f:
    f.write('{"version": "2.1.0", "default_channel": "wecom", "debug": false}\n')

print("Workspace generation complete.")
print(f"Main workspace: {MAIN_WORKSPACE}")
print(f"Dynamic workspace (pre-initialized with stale data): {DYNAMIC_WORKSPACE}")