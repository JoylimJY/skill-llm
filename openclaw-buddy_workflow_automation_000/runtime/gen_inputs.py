import os
import json
import random
import pathlib

random.seed(42)

workspace = "/workspace"

# --- Create the deeply nested distractor structure ---
dirs = [
    "platform/feishu/webhooks",
    "platform/discord/handlers",
    "platform/telegram/bots",
    "community/beta_testers/cohort_a",
    "community/beta_testers/cohort_b",
    "community/events/launch_week",
    "analytics/engagement/q1_2026",
    "analytics/engagement/q2_2026",
    "ops/deployment/staging",
    "ops/deployment/prod",
    "features/virtual_pets/design",
    "features/virtual_pets/legacy",
]

for d in dirs:
    pathlib.Path(os.path.join(workspace, d)).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "platform/feishu/webhooks/config.json": json.dumps({
        "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx",
        "secret": "REDACTED",
        "events": ["message", "reaction"]
    }, indent=2),
    "platform/discord/handlers/message_handler.py": """
# Discord message handler
def handle_message(event):
    user_id = event['author']['id']
    content = event['content']
    return process_command(content, user_id)
""",
    "platform/telegram/bots/bot_config.yaml": """
bot_token: REDACTED
allowed_commands:
  - /start
  - /help
  - /buddy
""",
    "community/beta_testers/cohort_a/notes.txt": """
Cohort A beta testers - internal only
Recruited from Discord server
Testing virtual pet feature before GA
""",
    "community/beta_testers/cohort_b/notes.txt": """
Cohort B - Feishu enterprise users
Different ID format (open_id)
""",
    "community/events/launch_week/schedule.json": json.dumps({
        "event": "Virtual Pet Launch Week",
        "dates": ["2026-03-01", "2026-03-07"],
        "activities": ["buddy_reveal", "gacha_event", "leaderboard"]
    }, indent=2),
    "analytics/engagement/q1_2026/summary.csv": """user_segment,dau,retention_7d
feishu_enterprise,1240,0.72
discord_community,890,0.61
telegram_channel,320,0.55
""",
    "analytics/engagement/q2_2026/projections.json": json.dumps({
        "projected_dau": 5000,
        "feature_adoption": {"virtual_pets": 0.45}
    }, indent=2),
    "ops/deployment/staging/deploy.sh": """#!/bin/bash
echo "Deploying to staging..."
kubectl apply -f manifests/
""",
    "ops/deployment/prod/checklist.md": """
# Production Deployment Checklist
- [ ] Feature flags verified
- [ ] Buddy generation tested
- [ ] Load test passed
""",
    "features/virtual_pets/design/species_list.txt": """
Originally proposed species (v0.1 design doc - OUTDATED):
cat, dog, bird, fish, hamster
See current implementation for actual species list.
""",
    "features/virtual_pets/legacy/old_generator.js": """
// DEPRECATED - old buddy generator v0.1
// Uses MD5 hashing - DO NOT USE
function oldGenerate(userId) {
    // deprecated
    return null;
}
""",
    "features/virtual_pets/design/rarity_weights.json": json.dumps({
        "NOTE": "OUTDATED DRAFT - do not use for production",
        "common": 0.50,
        "uncommon": 0.30,
        "rare": 0.15,
        "epic": 0.04,
        "legendary": 0.01
    }, indent=2),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE ACTUAL TASK INPUT ---
# A list of beta tester user IDs that need their buddy profiles pre-generated
# Mix of Feishu open_ids and a manual string ID

beta_tester_ids = [
    "ou_54e680914a71dc8636180ce79cebdca8",
    "ou_7b3c92f0d1a4e865234abc901def5678",
    "ou_1a2b3c4d5e6f7890abcdef1234567890",
    "beta_tester_007",
    "ou_deadbeef12345678cafebabe90abcdef",
]

task_input = {
    "batch_name": "pre_launch_buddy_generation",
    "description": "Pre-generate virtual pet profiles for beta testers before feature launch. Each user needs their display card and machine-readable profile saved.",
    "user_ids": beta_tester_ids,
    "output_instructions": "For each user_id, save two files: a display card file named '<user_id>.card.txt' and a machine-readable data file named '<user_id>.data.json'. Save all outputs in a single directory called 'buddy_profiles'.",
}

task_input_path = os.path.join(workspace, "community/beta_testers/pending_buddy_generation.json")
with open(task_input_path, "w") as f:
    json.dump(task_input, f, indent=2)

print("Workspace generated successfully.")
print(f"Task input file: {task_input_path}")
print(f"User IDs to process: {beta_tester_ids}")