import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic, deeply nested healthtech mobile app project structure
dirs = [
    "mobile_app/src/screens/home",
    "mobile_app/src/screens/profile",
    "mobile_app/src/screens/onboarding",
    "mobile_app/src/components/buttons",
    "mobile_app/src/components/forms",
    "mobile_app/src/services/api",
    "mobile_app/src/utils",
    "mobile_app/assets/icons",
    "mobile_app/assets/fonts",
    "mobile_app/tests/unit",
    "mobile_app/tests/integration",
    "docs/design_specs",
    "docs/product_requirements",
    "infrastructure/ci_cd",
    "infrastructure/monitoring",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files simulating a real project
distractor_files = {
    "mobile_app/src/screens/home/HomeScreen.tsx": "// Home screen component\nexport default function HomeScreen() { return null; }",
    "mobile_app/src/screens/profile/ProfileScreen.tsx": "// Profile screen\nexport default function ProfileScreen() { return null; }",
    "mobile_app/src/screens/onboarding/WelcomeScreen.tsx": "// Welcome screen\nexport default function WelcomeScreen() { return null; }",
    "mobile_app/src/components/buttons/PrimaryButton.tsx": "// Primary button component",
    "mobile_app/src/components/forms/LoginForm.tsx": "// Login form component",
    "mobile_app/src/services/api/patientService.ts": "// Patient API service\nexport const getPatient = async (id: string) => {};",
    "mobile_app/src/services/api/medicationService.ts": "// Medication API stubs - NOT IMPLEMENTED\n// TODO: build medication reminder screen",
    "mobile_app/src/utils/dateUtils.ts": "// Date utility functions",
    "mobile_app/assets/icons/placeholder.txt": "icon assets go here",
    "mobile_app/assets/fonts/placeholder.txt": "font assets go here",
    "mobile_app/tests/unit/HomeScreen.test.ts": "// unit tests",
    "mobile_app/tests/integration/api.test.ts": "// integration tests",
    "docs/design_specs/medication_reminder_wireframe.txt": (
        "WIREFRAME NOTES (v0.3)\n"
        "Screen: Medication Reminder\n"
        "- List of daily medications with dosage\n"
        "- Push notification toggle per medication\n"
        "- 'Mark as Taken' swipe gesture\n"
        "- Refill alert when supply < 7 days\n"
        "Status: Awaiting development handoff"
    ),
    "docs/product_requirements/PRD_medication_reminder.txt": (
        "PRD: Medication Reminder Feature\n"
        "Priority: HIGH\n"
        "Owner: Sarah Chen (Product)\n"
        "Requested by: Clinical Operations Team\n\n"
        "Summary:\n"
        "Patients need a dedicated screen to manage their daily medication schedules.\n"
        "The screen should show medication names, dosages, timing, and allow patients\n"
        "to mark doses as taken and receive reminders.\n\n"
        "Acceptance Criteria:\n"
        "1. Display list of prescribed medications\n"
        "2. Show next dose time for each medication\n"
        "3. Enable/disable push reminders per medication\n"
        "4. 'Mark as Taken' action with timestamp logging\n"
        "5. Low-supply refill alert (<7 days remaining)\n\n"
        "This feature is BLOCKING the Q3 patient engagement milestone."
    ),
    "docs/product_requirements/PRD_telehealth.txt": "PRD: Telehealth Video Calls\nStatus: Backlog",
    "infrastructure/ci_cd/pipeline.yml": "# CI/CD pipeline config\nstages:\n  - build\n  - test\n  - deploy",
    "infrastructure/monitoring/alerts.json": json.dumps({"alerts": ["high_error_rate", "latency_spike"]}, indent=2),
    "mobile_app/package.json": json.dumps({
        "name": "healthtrack-mobile",
        "version": "2.1.4",
        "dependencies": {
            "react-native": "0.72.0",
            "react-navigation": "^6.0.0"
        }
    }, indent=2),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# Write the SKILL.md that the agent should discover and use
skill_md_content = """---
name: delegate_app_dev
description: Triggers whenever the user asks to build a feature, fix a bug, create a screen, or modify the mobile app.
requires:
  bins: [curl]
---

# App Dev Delegation Skill

You are the Front Desk for an enterprise App Development Factory. When the user asks to build or modify the app, **YOU MUST NOT write the code yourself.** You must delegate the task to the Restate backend infrastructure.

## Execution Steps

1. Extract the user's exact feature request.
2. Use the `exec` tool to run the following `curl` command. This pushes the task to Restate's asynchronous queue.

```bash
curl -sS -X POST http://127.0.0.1:8080/AppFactory/buildFeature/send \\
  -H "Content-Type: application/json" \\
  -d '{"prompt": "<INSERT_USER_PROMPT_HERE>"}'
```
"""

with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md_content)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1}")