import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure with distractors ──────────────────────────────────────
dirs = [
    "ops/onboarding/batch_2024",
    "ops/onboarding/archive",
    "ops/registry/exports",
    "ops/registry/imports",
    "ops/config/env",
    "ops/config/deprecated",
    "internal/finance/bots",
    "internal/legal/bots",
    "internal/hr/bots",
    "logs/deploy",
    "logs/errors",
    "docs/protocols",
    "docs/schemas",
    "tmp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "ops/config/env/.env.production": "NODE_ENV=production\nPORT=3000\nLOG_LEVEL=info\n",
    "ops/config/deprecated/old_registry.json": json.dumps({"version": "v0", "bots": []}),
    "ops/config/deprecated/migration_notes.txt": "Migrated from v0 to v1 schema on 2024-01-15.\nSee protocol docs for new field requirements.\n",
    "internal/finance/bots/spending_bot_draft.txt": "Name: SpendingBot\nDepartment: Finance\nStatus: DRAFT - not deployed\n",
    "internal/legal/bots/contract_bot_notes.md": "# ContractBot\nReviewing NDA templates. Pending legal clearance.\n",
    "internal/hr/bots/hr_bot_config.yaml": "name: HR-Assist\nstatus: active\nversion: 2.1\n",
    "logs/deploy/deploy_2024_03_01.log": "[INFO] Deploying fleet v1.2.3\n[ERROR] feishu_id missing for bot index 3\n[INFO] 4/5 bots registered successfully\n",
    "logs/errors/card_parse_error.log": "Error: avatar.url field missing in payload at 2024-03-01T12:00:00Z\nBot: unnamed_bot_7\n",
    "docs/protocols/legacy_v0_spec.txt": "Legacy protocol (deprecated): flat JSON, no nested bio, no protocol field.\nDo NOT use for new registrations.\n",
    "docs/schemas/employee_schema.json": json.dumps({"type": "object", "properties": {"name": {"type": "string"}, "department": {"type": "string"}}}),
    "tmp/scratch/random_ids.txt": "\n".join([f"ou_{random.randint(100000,999999)}" for _ in range(10)]),
    "tmp/scratch/old_export_attempt.txt": '{"name":"BrokenBot","id":"no-uuid","missing_protocol":true}',
}
for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── MAIN TASK INPUT: Messy bot profile sheets ─────────────────────────────────
# These are the "intake forms" the agent must process.
# They are intentionally unstructured / slightly inconsistent.

# Bot 1: FinanceGuard — lives in finance, App Bot (cli_ prefix)
finance_bot_profile = {
    "_source": "intake_form_v2",
    "_submitted_by": "alice@company.com",
    "_notes": "This is the new financial compliance bot for Q2. Please register ASAP.",
    "preferred_display_name": "FinanceGuard",
    "app_client_id": "cli_finance_guard_9f2a",   # <-- this should become feishu_id
    "profile_image": "https://cdn.company.com/avatars/finance_guard.png",
    "personality_type": "ISTJ",
    "biological_classification": "Robot",
    "self_description": "I monitor financial transactions for compliance and flag anomalies in real-time.",
    "skill_tags": ["compliance", "finance", "anomaly-detection", "reporting"],
    "department": "Finance",
    "deployment_env": "production",
    "status": "ready_for_registration",
}

# Bot 2: LexBot — lives in legal, User Bot (ou_ prefix)
legal_bot_profile = {
    "_source": "intake_form_v2",
    "_submitted_by": "bob@company.com",
    "_notes": "Contract review assistant. MBTI confirmed by bot architect.",
    "preferred_display_name": "LexBot",
    "user_open_id": "ou_legal_lexbot_4c7b",      # <-- this should become feishu_id
    "avatar_link": "https://cdn.company.com/avatars/lex_bot.png",
    "mbti_profile": "INTJ",
    "type_of_entity": "AI",
    "about_me": "Specialized in contract analysis, legal risk assessment, and clause extraction.",
    "competencies": ["legal", "contract-review", "nlp", "risk-assessment"],
    "department": "Legal",
    "deployment_env": "staging",
    "status": "ready_for_registration",
}

with open(os.path.join(workspace, "ops/onboarding/batch_2024/finance_bot_intake.json"), "w") as f:
    json.dump(finance_bot_profile, f, indent=2)

with open(os.path.join(workspace, "ops/onboarding/batch_2024/legal_bot_intake.json"), "w") as f:
    json.dump(legal_bot_profile, f, indent=2)

# ── Task instruction file ────────────────────────────────────────────────────
# Written as an internal ops ticket. No hints about the tool's internals.
task_ticket = """INTERNAL OPS TICKET #2024-BOT-047
Priority: HIGH
Assigned: AI-Ops Team

Context:
Two new bots (FinanceGuard and LexBot) have been approved for deployment.
Their intake forms are in ops/onboarding/batch_2024/.

Tasks:
1. Register both bots in the local bot identity registry using the data in their
   intake forms. Match fields as best as possible to what the registry system expects.

2. Export FinanceGuard's registered profile as a shareable card, then import
   that exported card back into the registry (simulating receiving it from a
   third-party partner system). The import should succeed without errors.

3. Generate a display card for LexBot and save the output JSON to a file named
   'lexbot_display_card.json' in the ops/registry/ directory.

4. Verify the registry lists at least both bots by running the list command and
   saving its output to 'ops/registry/registry_snapshot.txt'.

Deadline: EOD
"""
with open(os.path.join(workspace, "ops/onboarding/batch_2024/TASK_TICKET.txt"), "w") as f:
    f.write(task_ticket)

print("Workspace initialized.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for fname in files:
        rel = os.path.relpath(os.path.join(root, fname), workspace)
        print(f"  {rel}")