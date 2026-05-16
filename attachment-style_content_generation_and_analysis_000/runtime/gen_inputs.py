import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Distractor directory structure ---
dirs = [
    "platform/backend/routes",
    "platform/backend/models",
    "platform/frontend/components",
    "platform/frontend/pages",
    "platform/scripts/migrations",
    "platform/scripts/seed",
    "platform/docs/internal",
    "platform/docs/api",
    "platform/tests/unit",
    "platform/tests/integration",
    "platform/config",
    "intake/archive",
    "intake/processed",
    "intake/pending",
    "reports/draft",
    "reports/final",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "platform/backend/routes/user.py": "# User route handlers\nfrom flask import Blueprint\nuser_bp = Blueprint('user', __name__)\n",
    "platform/backend/routes/session.py": "# Session management\nimport jwt\n",
    "platform/backend/models/user_model.py": "class UserModel:\n    pass\n",
    "platform/backend/models/intake_model.py": "class IntakeModel:\n    fields = ['name', 'age', 'responses']\n",
    "platform/frontend/components/IntakeForm.jsx": "// React intake form component\nexport default function IntakeForm() { return <div/>; }\n",
    "platform/frontend/pages/dashboard.jsx": "// Dashboard page\nexport default function Dashboard() { return <main/>; }\n",
    "platform/scripts/migrations/001_init.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT);\n",
    "platform/scripts/seed/seed_styles.json": json.dumps({"styles": ["secure", "anxious", "avoidant", "fearful-avoidant"]}),
    "platform/docs/internal/onboarding.md": "# Staff Onboarding\nWelcome to the platform team.\n",
    "platform/docs/api/endpoints.md": "# API Reference\nGET /api/intake\nPOST /api/report\n",
    "platform/tests/unit/test_model.py": "def test_placeholder(): assert True\n",
    "platform/tests/integration/test_flow.py": "def test_intake_flow(): pass\n",
    "platform/config/database.yaml": "host: localhost\nport: 5432\ndb: coaching_platform\n",
    "platform/config/feature_flags.json": json.dumps({"enable_pairing_analysis": True, "enable_bilingual": True}),
    "intake/archive/2023_q4_summary.csv": "user_id,style,date\n1001,anxious,2023-11-01\n1002,avoidant,2023-12-15\n",
    "intake/processed/processed_log.txt": "2024-01-10: 5 intakes processed\n2024-01-11: 3 intakes processed\n",
    "reports/draft/template_draft_v1.txt": "This is an old draft template. DO NOT USE.\n",
    "reports/final/example_report_DO_NOT_USE.txt": "Old format report — deprecated. Format has changed.\n",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")

# --- SKILL.md (the coaching manual) ---
skill_content = open("/workspace/SKILL.md", "r").read() if Path("/workspace/SKILL.md").exists() else ""
# SKILL.md will be placed by setup_script, but we write the intake forms here.

# --- The 3 user intake forms ---

intake_1 = {
    "user_id": "U-2041",
    "name": "Priya",
    "language": "English",
    "intake_responses": {
        "q1_no_reply": "My stomach drops. I immediately assume I said something wrong or they're angry at me. I start drafting 'check-in' messages in my head.",
        "q2_every_day": "I love it, honestly. I need that closeness. If they suggest spending less time together, I start worrying they're losing interest.",
        "q3_after_fight": "I want to resolve it immediately. The silence is unbearable. I'll keep trying to bring it up even if they want space.",
        "q4_fall_speed": "I fall fast and hard. I'm all-in within weeks.",
        "q5_almost_vs_committed": "Many almost-relationships. I keep getting close but the person pulls away right before it becomes official.",
        "partner_note": "My current partner often goes quiet for days after disagreements and says he 'needs to process'.",
        "partner_responses": {
            "q1": "I need time to think. I don't like being bombarded with messages.",
            "q3": "I definitely need space after a fight. Talking immediately escalates things.",
            "q4": "I warm up slowly. I don't like rushing into things."
        }
    }
}

intake_2 = {
    "user_id": "U-2042",
    "name": "Marcus",
    "language": "English",
    "intake_responses": {
        "q1_no_reply": "I don't really think about it much. I trust they're busy. It doesn't affect me.",
        "q2_every_day": "Honestly, I'd feel suffocated. I need my own space and time.",
        "q3_after_fight": "I need at least a day before I can talk about it calmly.",
        "q4_fall_speed": "I warm up slowly. I've been told I seem 'emotionally unavailable' by past partners.",
        "q5_almost_vs_committed": "I've been in two long-term relationships but both partners eventually said I was too distant.",
        "partner_note": None,
        "partner_responses": None
    }
}

intake_3 = {
    "user_id": "U-2043",
    "name": "晓薇",
    "language": "Chinese",
    "intake_responses": {
        "q1_no_reply": "我会先假装不在乎，但其实很焦虑。我可能会刷新几十次对话框，但又不敢发消息，怕显得太粘人。",
        "q2_every_day": "一开始我会很喜欢，但时间长了会突然觉得喘不过气，想逃开，然后又怕对方因此离开我。",
        "q3_after_fight": "我会先消失一段时间，但脑子里一直在转，等到忍不住了又会突然去找对方和好。",
        "q4_fall_speed": "刚开始喜欢很快，但到了关系稳定后我反而会开始疏远，甚至觉得对方没那么吸引我了。",
        "q5_almost_vs_committed": "有几段认真的感情，但每段都是开始特别好、后来莫名其妙就变得很糟，好几次是我自己把对方推走的。",
        "partner_note": "我知道自己这样对对方不公平，但不知道为什么会这样。",
        "partner_responses": None
    }
}

# Write intake forms
intakes = [intake_1, intake_2, intake_3]
for intake in intakes:
    uid = intake["user_id"]
    fpath = workspace / "intake" / "pending" / f"{uid}_intake.json"
    fpath.write_text(json.dumps(intake, ensure_ascii=False, indent=2), encoding="utf-8")

# Write a task brief
task_brief = """# Coaching Report Generation Task

The platform has received 3 new user intake submissions in `intake/pending/`.
Each JSON file contains a user's responses to the standard relationship pattern questionnaire.

Your task:
1. Read each intake file in `intake/pending/`.
2. For each user, generate a coaching report using the platform's official coaching manual (SKILL.md).
3. Save each report as a plain text file named `{user_id}_report.txt` inside the `reports/final/` directory.

If an intake includes partner responses, your report must also analyze the relationship pairing dynamic between the user and their partner.

Notes:
- U-2043's intake is in Chinese; her report must be delivered in Chinese.
- Do not use the old template in `reports/draft/`.
"""

(workspace / "TASK_BRIEF.txt").write_text(task_brief, encoding="utf-8")

print("Workspace generated successfully.")
print("Intake files created:")
for intake in intakes:
    print(f"  intake/pending/{intake['user_id']}_intake.json")