import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "docs/architecture",
    "docs/onboarding",
    "src/router",
    "src/parser",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "config/envs",
    "config/bots",
    "logs/2024-Q1",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "docs/architecture/system_overview.md": "# System Overview\nThis document describes the multi-topic chat routing layer.\n",
    "docs/architecture/data_flow.md": "# Data Flow\nMessages enter → parser → router → handler.\n",
    "docs/onboarding/getting_started.md": "# Getting Started\nClone the repo, run `make dev`, profit.\n",
    "src/router/base_router.py": "class BaseRouter:\n    def route(self, msg): raise NotImplementedError\n",
    "src/parser/tokenizer.py": "def tokenize(text): return text.split()\n",
    "src/utils/helpers.py": "def flatten(lst): return [x for sub in lst for x in sub]\n",
    "tests/unit/test_parser.py": "def test_placeholder(): assert True\n",
    "tests/integration/test_end_to_end.py": "def test_e2e(): pass\n",
    "config/envs/dev.json": json.dumps({"env": "dev", "debug": True}),
    "config/bots/assistant.json": json.dumps({"name": "AssistBot", "version": "1.0"}),
    "logs/2024-Q1/app.log": "2024-01-01 INFO startup complete\n2024-01-02 WARN high latency\n",
    "config/envs/prod.json": json.dumps({"env": "prod", "debug": False}),
}
for path, content in distractor_files.items():
    full = os.path.join(workspace, path)
    with open(full, "w") as f:
        f.write(content)

# ── The core problem input ───────────────────────────────────────────────────
# A batch of raw chat messages the agent must classify.
# These are deliberately messy: conflicts, long-form aliases, mid-message tags,
# no tags, ambiguous combos, platform-relevant content, and reuse scenarios.

messages = [
    {
        "id": "msg_001",
        "platform": "slack",
        "text": "[ISO: project-alpha][NOMEM] What is the current sprint velocity for alpha team?"
    },
    {
        "id": "msg_002",
        "platform": "slack",
        "text": "[GLOBAL][REM] Remember: all financial figures should be reported in USD unless specified."
    },
    {
        "id": "msg_003",
        "platform": "telegram",
        "text": "[SCOPE: marketing] How is the Q3 campaign performing compared to Q2?"
    },
    {
        "id": "msg_004",
        "platform": "slack",
        "text": "[ISO: legal][GLOBAL] Is the new vendor contract compliant with GDPR?"
    },
    {
        "id": "msg_005",
        "platform": "discord",
        "text": "[REM][NOMEM] Store the decision: we use snake_case for all database columns."
    },
    {
        "id": "msg_006",
        "platform": "whatsapp",
        "text": "What time is the next standup?"
    },
    {
        "id": "msg_007",
        "platform": "slack",
        "text": "[Isolated Context: backend-infra] Show me all open P0 incidents."
    },
    {
        "id": "msg_008",
        "platform": "telegram",
        "text": "[Global Context OK][Remember] Default date format should be ISO-8601 going forward."
    },
    {
        "id": "msg_009",
        "platform": "slack",
        "text": "Hey team! [SCOPE: devops] Can you check the deployment pipeline status?"
    },
    {
        "id": "msg_010",
        "platform": "discord",
        "text": "[No Memory][ISO: sandbox-test] Run a quick experiment with the new ranking model."
    },
    {
        "id": "msg_011",
        "platform": "slack",
        "text": "[NOMEM][REM] Note for later: prefer async patterns over sync in new services."
    },
    {
        "id": "msg_012",
        "platform": "telegram",
        "text": "[SCOPE: finance][GLOBAL] Pull revenue numbers from last quarter and cross-check with marketing spend."
    },
]

input_path = os.path.join(workspace, "raw_messages.json")
with open(input_path, "w") as f:
    json.dump(messages, f, indent=2)

print(f"Generated {len(messages)} messages → {input_path}")
print("Distractor files created:", len(distractor_files))