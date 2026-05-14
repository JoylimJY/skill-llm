import os
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested distractor directory structure
dirs = [
    "company/hr/wellness_programs/2023",
    "company/hr/wellness_programs/2024",
    "company/it/scripts/monitoring",
    "company/it/scripts/deployment",
    "company/it/scripts/backup",
    "company/engineering/onboarding",
    "company/engineering/tooling/ide_configs",
    "company/engineering/tooling/linters",
    "company/facilities/desk_setup",
    "company/facilities/ergonomics_reports",
    "drafts/scripts",
    "drafts/docs",
    "archive/old_scripts",
    "archive/deprecated",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "company/hr/wellness_programs/2023/annual_report.txt": (
        "Wellness Program Annual Report 2023\n"
        "Total participants: 142\n"
        "Most popular activity: Standing desk usage\n"
        "Eye strain complaints reduced by 12%\n"
    ),
    "company/hr/wellness_programs/2024/goals.md": (
        "# 2024 Wellness Goals\n"
        "- Deploy automated break reminders to all engineering workstations\n"
        "- Reduce RSI incidents by 20%\n"
        "- Increase eye break compliance to 80%\n"
    ),
    "company/it/scripts/monitoring/cpu_monitor.sh": (
        "#!/bin/bash\n"
        "# CPU monitoring script\n"
        "while true; do\n"
        "  echo \"CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')%\"\n"
        "  sleep 60\n"
        "done\n"
    ),
    "company/it/scripts/deployment/deploy.sh": (
        "#!/bin/bash\n"
        "# Deployment script\n"
        "echo 'Deploying application...'\n"
        "git pull origin main\n"
        "npm install\n"
        "npm run build\n"
    ),
    "company/it/scripts/backup/backup.sh": (
        "#!/bin/bash\n"
        "# Backup script\n"
        "BACKUP_DIR=/var/backups\n"
        "tar -czf $BACKUP_DIR/backup_$(date +%Y%m%d).tar.gz /home/\n"
    ),
    "company/engineering/onboarding/setup_guide.md": (
        "# Engineering Onboarding Setup Guide\n\n"
        "## Required Tools\n"
        "- VSCode or JetBrains IDE\n"
        "- Docker Desktop\n"
        "- Node.js 18+\n"
        "- Python 3.10+\n\n"
        "## Recommended Extensions\n"
        "- ESLint, Prettier, GitLens\n"
    ),
    "company/engineering/tooling/ide_configs/vscode_settings.json": (
        '{\n'
        '  "editor.fontSize": 14,\n'
        '  "editor.tabSize": 2,\n'
        '  "editor.formatOnSave": true,\n'
        '  "workbench.colorTheme": "One Dark Pro"\n'
        '}\n'
    ),
    "company/engineering/tooling/linters/.eslintrc.json": (
        '{\n'
        '  "env": {"browser": true, "es2021": true},\n'
        '  "extends": "eslint:recommended",\n'
        '  "rules": {"indent": ["error", 2]}\n'
        '}\n'
    ),
    "company/facilities/desk_setup/checklist.txt": (
        "Ergonomic Desk Setup Checklist\n"
        "[ ] Monitor at eye level\n"
        "[ ] Chair lumbar support adjusted\n"
        "[ ] Keyboard at elbow height\n"
        "[ ] Mouse close to keyboard\n"
        "[ ] Feet flat on floor or footrest\n"
        "[ ] Monitor 20-28 inches from eyes\n"
    ),
    "company/facilities/ergonomics_reports/q3_2024.txt": (
        "Q3 2024 Ergonomics Incident Report\n"
        "Carpal tunnel cases: 3 new, 2 ongoing\n"
        "Neck/shoulder pain reports: 11\n"
        "Lower back complaints: 8\n"
        "Eye strain tickets: 24\n"
        "Recommendation: Automate break reminder scripts on all Ubuntu workstations\n"
        "Priority: HIGH - target heavy users (8+ hours/day)\n"
    ),
    "drafts/scripts/old_reminder.sh": (
        "#!/bin/bash\n"
        "# Old draft - DEPRECATED\n"
        "# Simple one-liner reminder - does not follow new standards\n"
        "while true; do\n"
        "  echo 'Take a break!'\n"
        "  sleep 3600\n"
        "done\n"
    ),
    "drafts/docs/break_schedule_draft.txt": (
        "DRAFT - Break Schedule Proposal\n"
        "Option A: Every hour remind users\n"
        "Option B: 20-20-20 rule implementation\n"
        "Option C: Heavy user profile - TBD\n"
        "Status: Pending IT approval\n"
    ),
    "archive/old_scripts/notify_v1.sh": (
        "#!/bin/bash\n"
        "# Version 1 - archived\n"
        "notify-send 'Break time!' 'Stand up and stretch'\n"
    ),
    "archive/deprecated/wellness_v0.sh": (
        "#!/bin/bash\n"
        "# Completely deprecated wellness script v0\n"
        "echo 'This script is no longer maintained'\n"
    ),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# Create a requirements/brief file that motivates the task
brief_content = (
    "IT Wellness Automation Brief\n"
    "============================\n"
    "Date: 2024-11-15\n"
    "From: IT Manager\n"
    "To: DevOps Team\n\n"
    "We need to deploy an automated health reminder script on all engineering Ubuntu Linux\n"
    "workstations. Our engineers are classified as Heavy Users (8+ hours/day at computers).\n\n"
    "The script should be named: ergocare_heavy.sh\n\n"
    "Requirements:\n"
    "- Must run silently in background on Linux\n"
    "- Must handle ALL types of breaks: eye, quick stretch, energy, and full routine\n"
    "- Must follow the Heavy User schedule (highest intensity profile)\n"
    "- Must use desktop notifications\n"
    "- Must include all exercise types (eyes, back, neck, wrists)\n"
    "- Configuration variables must be easily editable at top of script\n"
    "- Must support sound alerts (enabled by default)\n"
    "- Notification type should cover all delivery methods\n\n"
    "Deliverable: A single bash script file ready for deployment.\n"
)

with open(os.path.join(workspace, "it_wellness_brief.txt"), "w") as f:
    f.write(brief_content)

print("Workspace initialized successfully.")
print(f"Created {len(distractor_files)} distractor files in nested directories.")