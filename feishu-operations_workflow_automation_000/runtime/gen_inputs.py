import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create directory structure
dirs = [
    "/workspace/feishu-skill/references",
    "/workspace/feishu-skill/archive",
    "/workspace/projects/mobile-app-launch",
    "/workspace/projects/mobile-app-launch/drafts",
    "/workspace/projects/mobile-app-launch/old_configs",
    "/workspace/team-docs",
    "/workspace/templates",
    "/workspace/logs",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Create distractor files
distractor_files = {
    "/workspace/projects/mobile-app-launch/drafts/meeting_notes_draft.txt": """
Meeting notes from kick-off:
- Need task tracking for iOS and Android teams
- PM needs full oversight
- External QA contractor needs limited access
- Auto-notify when tasks are overdue
- Weekly status reports via bot
Draft - not finalized yet
""",
    "/workspace/projects/mobile-app-launch/old_configs/old_permissions.json": """
{
  "version": "1.0_deprecated",
  "roles": {
    "viewer": "read_only",
    "editor": "read_write",
    "admin": "full_access"
  },
  "note": "This is the old format - DO NOT USE"
}
""",
    "/workspace/projects/mobile-app-launch/old_configs/notification_spec_v1.txt": """
Notification config (OLD):
- When task done: send text message
- When late: alert manager
- Format: plain text only
DEPRECATED - see new spec
""",
    "/workspace/team-docs/team_roster.csv": """name,role,email
Alice Zhang,Product Manager,alice@company.com
Bob Li,iOS Developer,bob@company.com
Carol Wang,Android Developer,carol@company.com
Dave Chen,QA Contractor,dave@external.com
Eve Liu,Department Head,eve@company.com
""",
    "/workspace/team-docs/access_matrix_draft.txt": """
Access requirements (DRAFT - needs proper permission levels):
- Dave Chen (QA Contractor): Should only be able to VIEW the task table, cannot edit
- Bob Li + Carol Wang (Developers): Should be able to CREATE and EDIT tasks
- Alice Zhang (PM): Should be able to INVITE collaborators and manage the table
- Eve Liu (Department Head): Should have MAXIMUM access including transferring ownership
- Note: Need to figure out the exact permission tier names for Feishu
""",
    "/workspace/templates/webhook_template_wrong.json": """
{
  "type": "message",
  "body": {
    "msg": "Task overdue alert"
  },
  "note": "THIS FORMAT IS WRONG - check documentation for correct structure"
}
""",
    "/workspace/logs/setup_attempts.log": """
2024-01-15 10:23:11 - Attempted to create bitable for task tracking
2024-01-15 10:45:33 - Tried to set up webhook but wrong format
2024-01-15 11:02:17 - Permission setup unclear - what are the tier names?
2024-01-15 14:30:00 - Need to finalize automation triggers
""",
    "/workspace/feishu-skill/archive/old_guide.md": """
# Old Feishu Guide (ARCHIVED)
This guide is outdated. Please refer to the current reference documents.
Permission levels used to be: read, write, admin
Message format used to be different.
DO NOT USE THIS GUIDE.
""",
    "/workspace/templates/automation_ideas.txt": """
Automation ideas for project:
1. When a task record is created -> notify the assignee
2. When status changes to "completed" -> notify PM
3. When due date equals today -> send reminder
4. Need correct trigger condition names from official docs
""",
    "/workspace/projects/mobile-app-launch/requirements.md": """
# Mobile App Launch Project - Workspace Requirements

## Team Members
1. Alice Zhang - Product Manager
2. Bob Li - iOS Developer  
3. Carol Wang - Android Developer
4. Dave Chen - External QA Contractor
5. Eve Liu - Department Head / Stakeholder

## What We Need
1. A bitable (task tracking table) with proper fields
2. Automation: notify assignee when task is CREATED
3. Automation: notify Alice (PM) when a task record's status field changes to completed  
4. A custom robot webhook message (for overdue alerts) that sends a CARD message type
5. Proper permission assignments for each team member

## Permission Requirements (need exact Feishu tier names)
- Dave Chen: view only, no editing
- Bob Li + Carol Wang: can edit tasks but cannot manage permissions or invite others
- Alice Zhang: can invite collaborators and manage comments but NOT manage permissions
- Eve Liu: highest possible permission, including ownership transfer

## Output
Please produce: workspace_config.json
""",
}

for filepath, content in distractor_files.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip())

# Create a partial/wrong config that the agent must NOT just copy
wrong_partial_config = {
    "_warning": "THIS IS A PARTIAL DRAFT - DO NOT SUBMIT AS FINAL",
    "project": "mobile-app-launch",
    "bitable_fields": [
        {"name": "任务名称", "type": "WRONG_TYPE"},
        {"name": "负责人", "type": "text_probably"}
    ],
    "automations": [
        {
            "trigger": "when_something_happens",
            "action": "send_notification"
        }
    ],
    "permissions": {
        "Dave Chen": "viewer_maybe",
        "Alice Zhang": "admin_or_something"
    }
}

with open("/workspace/projects/mobile-app-launch/drafts/partial_config_draft.json", "w", encoding="utf-8") as f:
    json.dump(wrong_partial_config, f, indent=2, ensure_ascii=False)

print("Workspace generated successfully.")
print("Files created:")
for d in dirs:
    print(f"  {d}/")
for fp in distractor_files:
    print(f"  {fp}")