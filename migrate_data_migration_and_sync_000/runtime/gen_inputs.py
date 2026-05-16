#!/usr/bin/env python3
"""
Build the initial sandbox workspace simulating a Clawdbot installation.
Creates a realistic source workspace at /opt/clawd-source with:
- Config files, managed skills, WhatsApp session data
- Session transcripts
- Credentials file
- Bloat directories that MUST be excluded (node_modules, .next, dist, build)
- The scripts/export.sh and scripts/import.sh mock scripts
"""

import os
import json
import stat
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")
SOURCE_WORKSPACE = Path("/opt/clawd-source")
SCRIPTS_DIR = WORKSPACE / "scripts"

# Create directory structure
dirs_to_create = [
    WORKSPACE,
    SCRIPTS_DIR,
    SOURCE_WORKSPACE,
    SOURCE_WORKSPACE / "skills" / "customer-support",
    SOURCE_WORKSPACE / "skills" / "faq-handler",
    SOURCE_WORKSPACE / "skills" / "escalation",
    SOURCE_WORKSPACE / "whatsapp" / "session" / "auth_info_baileys",
    SOURCE_WORKSPACE / "transcripts" / "sessions" / "2025-01",
    SOURCE_WORKSPACE / "transcripts" / "sessions" / "2025-02",
    SOURCE_WORKSPACE / "credentials",
    # Bloat dirs that MUST be excluded
    SOURCE_WORKSPACE / "node_modules" / ".bin",
    SOURCE_WORKSPACE / "node_modules" / "express" / "lib",
    SOURCE_WORKSPACE / ".next" / "cache" / "webpack",
    SOURCE_WORKSPACE / "dist" / "assets",
    SOURCE_WORKSPACE / "build" / "static",
    SOURCE_WORKSPACE / ".git" / "objects",
    SOURCE_WORKSPACE / ".wrangler" / "tmp",
    SOURCE_WORKSPACE / ".open-next" / "cache",
    SOURCE_WORKSPACE / ".vercel" / "output",
    # Staging target (empty, for import)
    Path("/opt/clawd-staging"),
    Path("/tmp/exports"),
]

for d in dirs_to_create:
    d.mkdir(parents=True, exist_ok=True)

# ---- clawdbot.json config ----
config = {
    "version": "2.4.1",
    "instanceId": "cust-support-prod-7f3a",
    "botName": "SupportBot",
    "language": "en",
    "maxConcurrentSessions": 50,
    "webhookUrl": "https://internal.acme.corp/hooks/clawdbot",
    "logLevel": "info",
    "features": {
        "autoReply": True,
        "escalationEnabled": True,
        "transcriptStorage": True
    }
}
(SOURCE_WORKSPACE / "clawdbot.json").write_text(json.dumps(config, indent=2))

# ---- Managed skills ----
skill_customer = {
    "name": "customer-support",
    "version": "1.3.0",
    "triggers": ["help", "support", "issue"],
    "responses": {
        "default": "How can I assist you today?",
        "escalate": "Connecting you to a human agent..."
    }
}
(SOURCE_WORKSPACE / "skills" / "customer-support" / "skill.json").write_text(
    json.dumps(skill_customer, indent=2)
)
(SOURCE_WORKSPACE / "skills" / "customer-support" / "handler.js").write_text(
    "module.exports = async (ctx) => { return ctx.reply(ctx.skill.responses.default); };\n"
)

skill_faq = {
    "name": "faq-handler",
    "version": "2.0.1",
    "triggers": ["faq", "question", "how"],
    "faqs": [
        {"q": "What are your hours?", "a": "We operate 24/7."},
        {"q": "How do I reset my password?", "a": "Visit /account/reset"}
    ]
}
(SOURCE_WORKSPACE / "skills" / "faq-handler" / "skill.json").write_text(
    json.dumps(skill_faq, indent=2)
)

skill_escalation = {
    "name": "escalation",
    "version": "1.0.5",
    "triggers": ["human", "agent", "speak to someone"],
    "escalationQueue": "support-tier-2"
}
(SOURCE_WORKSPACE / "skills" / "escalation" / "skill.json").write_text(
    json.dumps(skill_escalation, indent=2)
)

# ---- WhatsApp session files ----
session_files = [
    ("creds.json", json.dumps({
        "noiseKey": {"private": {"type": "Buffer", "data": [1,2,3,4,5]}, "public": {"type": "Buffer", "data": [6,7,8]}},
        "signedIdentityKey": {"private": {"type": "Buffer", "data": [9,10,11]}, "public": {"type": "Buffer", "data": [12,13,14]}},
        "registrationId": 9823,
        "advSecretKey": "base64encodedkeyhere=="
    }, indent=2)),
    ("session-acme-1.json", json.dumps({
        "sessionId": "acme-1",
        "msgCount": 14823,
        "lastSeen": "2025-02-14T08:23:11Z"
    }, indent=2)),
    ("pre-key-1.json", json.dumps({"keyId": 1, "keyPair": {"private": [1,2,3], "public": [4,5,6]}})),
    ("pre-key-2.json", json.dumps({"keyId": 2, "keyPair": {"private": [7,8,9], "public": [10,11,12]}})),
    ("sender-key-memory.json", json.dumps({"keys": {}})),
]
for fname, fcontent in session_files:
    (SOURCE_WORKSPACE / "whatsapp" / "session" / "auth_info_baileys" / fname).write_text(fcontent)

# ---- Session transcripts ----
for month, sessions in [("2025-01", 5), ("2025-02", 3)]:
    for i in range(sessions):
        ts_file = SOURCE_WORKSPACE / "transcripts" / "sessions" / month / f"session_{i+1:03d}.json"
        ts_content = {
            "sessionId": f"sess-{month}-{i+1:03d}",
            "startTime": f"{month}-{10+i:02d}T09:{i*7:02d}:00Z",
            "messages": [
                {"from": "user", "text": f"Hello, I need help with order #{random.randint(10000,99999)}", "ts": f"{month}-{10+i:02d}T09:{i*7+1:02d}:00Z"},
                {"from": "bot", "text": "How can I assist you today?", "ts": f"{month}-{10+i:02d}T09:{i*7+2:02d}:00Z"},
                {"from": "user", "text": "My package hasn't arrived.", "ts": f"{month}-{10+i:02d}T09:{i*7+3:02d}:00Z"},
                {"from": "bot", "text": "I'm escalating this to our support team.", "ts": f"{month}-{10+i:02d}T09:{i*7+4:02d}:00Z"},
            ],
            "resolved": random.choice([True, False]),
            "agentId": f"agent-{random.randint(1,10)}"
        }
        ts_file.write_text(json.dumps(ts_content, indent=2))

# ---- Credentials (should NOT be included in export) ----
creds = {
    "twilioAccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "twilioAuthToken": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "openaiApiKey": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "databasePassword": "super-secret-db-pass-2025",
    "webhookSecret": "wh-secret-abc123"
}
(SOURCE_WORKSPACE / "credentials" / "secrets.json").write_text(json.dumps(creds, indent=2))
(SOURCE_WORKSPACE / "credentials" / ".env").write_text(
    "TWILIO_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
    "TWILIO_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
    "OPENAI_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
    "DB_PASS=super-secret-db-pass-2025\n"
)

# ---- Bloat files in excluded directories ----
(SOURCE_WORKSPACE / "node_modules" / "express" / "lib" / "application.js").write_text(
    "// express application module - 50k lines omitted\nmodule.exports = {};\n"
)
(SOURCE_WORKSPACE / "node_modules" / ".bin" / "express").write_text("#!/bin/sh\nexec node $@\n")
(SOURCE_WORKSPACE / ".next" / "cache" / "webpack" / "client-development.pack").write_bytes(
    bytes(random.getrandbits(8) for _ in range(1024))
)
(SOURCE_WORKSPACE / "dist" / "assets" / "main.bundle.js").write_text(
    "!function(e){var t={};function n(r){}n.m=e;}([]);\n" * 100
)
(SOURCE_WORKSPACE / "build" / "static" / "index.html").write_text(
    "<html><body><div id='root'></div></body></html>\n"
)
(SOURCE_WORKSPACE / ".git" / "objects" / "pack-abc123.idx").write_bytes(
    bytes([0] * 256)
)
(SOURCE_WORKSPACE / ".wrangler" / "tmp" / "deploy_state.json").write_text(
    json.dumps({"deployId": "wrangler-test-123", "status": "completed"})
)

# ---- Top-level distractor files ----
(SOURCE_WORKSPACE / "package.json").write_text(json.dumps({
    "name": "clawdbot",
    "version": "2.4.1",
    "dependencies": {
        "express": "^4.18.2",
        "@whiskeysockets/baileys": "^6.7.0"
    }
}, indent=2))

(SOURCE_WORKSPACE / "package-lock.json").write_text(json.dumps({
    "name": "clawdbot",
    "version": "2.4.1",
    "lockfileVersion": 3,
    "requires": True,
    "packages": {}
}, indent=2))

(SOURCE_WORKSPACE / "tsconfig.json").write_text(json.dumps({
    "compilerOptions": {
        "target": "ES2020",
        "module": "commonjs",
        "outDir": "./dist"
    }
}, indent=2))

(SOURCE_WORKSPACE / "README.md").write_text(
    "# Clawdbot\nCustomer support automation platform.\n"
)

print("✓ Source workspace created at /opt/clawd-source")
print("✓ Target workspace placeholder created at /opt/clawd-staging")
print("✓ Export output directory created at /tmp/exports")
print("✓ Scripts directory created at /workspace/scripts")
print("\nDirectory structure:")
for p in sorted(SOURCE_WORKSPACE.rglob("*")):
    print(f"  {p.relative_to(SOURCE_WORKSPACE)}")