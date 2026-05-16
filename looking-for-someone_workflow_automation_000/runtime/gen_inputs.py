import os
import json
import random
import string
from pathlib import Path

random.seed(42)

workspace = Path("/workspace/looking-for-someone")
workspace.mkdir(parents=True, exist_ok=True)

# ── distractor files to simulate a messy real-world project ──────────────────

distractor_dir = workspace / "case_intake_forms"
distractor_dir.mkdir(exist_ok=True)

# Distractor 1: An old, badly formatted case note (wrong field names, incomplete)
old_case = {
    "full_name": "Wang Xiaoming",
    "age_years": 67,
    "sex": "male",
    "last_seen": "2024-11-03",
    "place": "Chengdu South Railway Station",
    "notes": "wearing blue jacket"
}
(distractor_dir / "old_case_draft.json").write_text(json.dumps(old_case, ensure_ascii=False, indent=2))

# Distractor 2: A partial contact sheet
contact_sheet = {
    "reporter": "Li Hua",
    "relation": "daughter",
    "mobile": "139-xxxx-8821",
    "submitted": "2024-11-04"
}
(distractor_dir / "contact_sheet.json").write_text(json.dumps(contact_sheet, ensure_ascii=False, indent=2))

# Distractor 3: Random plaintext note
(distractor_dir / "note.txt").write_text(
    "Dad left home on the morning of November 3rd. He has mild dementia. "
    "Height approx 168cm. Last seen near South Station wearing a dark blue cotton jacket and grey trousers. "
    "He sometimes mentions going back to his hometown in Leshan."
)

# Distractor 4: Fake previous run log
logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)
(logs_dir / "run_2024-10-12.log").write_text(
    "[INFO] CLI started\n[ERROR] Case file corrupted\n[INFO] Exiting\n"
)
(logs_dir / "run_2024-11-01.log").write_text(
    "[INFO] CLI started\n[INFO] No cases found\n[INFO] Exiting\n"
)

# Distractor 5: Duplicate clue file with wrong format
clues_dir = workspace / "clue_inbox"
clues_dir.mkdir(exist_ok=True)
(clues_dir / "clue_raw.txt").write_text(
    "A neighbor said they saw an elderly man matching the description boarding bus #28 towards Tianfu Square at around 9:15am on Nov 3rd."
)
(clues_dir / "clue_duplicates.json").write_text(json.dumps([
    {"timestamp": "2024-11-04T08:00:00", "source": "neighbor", "content": "saw him at bus stop"},
    {"timestamp": "2024-11-04T09:00:00", "source": "shopkeeper", "content": "bought water near exit B"}
], ensure_ascii=False, indent=2))

# Distractor 6: Random template files
templates_dir = workspace / "notice_templates"
templates_dir.mkdir(exist_ok=True)
(templates_dir / "template_v1.txt").write_text(
    "【寻人启事】\n姓名：___\n年龄：___\n失联时间：___\n联系方式：___\n请知情者拨打电话：___"
)
(templates_dir / "template_weixin_old.txt").write_text(
    "亲爱的朋友们，我们家老人走失了，恳请大家帮忙转发！"
)

# Distractor 7: A confusingly named script stub
scripts_dir = workspace / "old_scripts"
scripts_dir.mkdir(exist_ok=True)
(scripts_dir / "create_case.sh").write_text(
    "#!/bin/bash\n# DEPRECATED: do not use\n# node cli_old.js create $1\necho 'This script is deprecated'\n"
)
(scripts_dir / "generate_notice.py").write_text(
    "# DEPRECATED placeholder\nprint('Use the new CLI instead')\n"
)

# Distractor 8: Fake README-like file with wrong command syntax (adversarial)
(workspace / "QUICKSTART_OLD.txt").write_text(
    "To create a case: node scripts/cli.js create '{...}'\n"
    "To add clue: node scripts/cli.js clue <id> <content>\n"
    "To generate notice: node scripts/cli.js notice <id>\n"
    "NOTE: This file is OUTDATED. Commands may have changed.\n"
)

# Distractor 9: Misc config files
(workspace / ".editorconfig").write_text("[*]\nindent_style = space\nindent_size = 2\n")
(workspace / "tsconfig.json").write_text('{"compilerOptions": {"target": "es2020"}}\n')

# Distractor 10: Fake data directory with stale case
stale_data_dir = Path.home() / ".openclaw" / "skills-data" / "looking-for-someone"
stale_data_dir.mkdir(parents=True, exist_ok=True)
(stale_data_dir / "ARCHIVE_2023.json").write_text(json.dumps({
    "id": "STALE-0001",
    "name": "Zhang Wei",
    "status": "resolved",
    "note": "Found 2023-09-10"
}, ensure_ascii=False, indent=2))

# ── THE ACTUAL TASK INPUT: A messy intake brief the agent must process ────────
task_brief = {
    "task": "Please create a missing person case from the information below, then record the new witness clue, and finally produce a WeChat-ready public notice for wide distribution.",
    "person_info": {
        "full_name": "Wang Jianguo",
        "approximate_age": 67,
        "sex": "male",
        "date_last_seen": "2024-11-03",
        "location_last_seen": "Chengdu South Railway Station Exit B",
        "height_cm": 168,
        "clothing_description": "dark blue cotton-padded jacket, grey trousers",
        "special_notes": "mild cognitive impairment, sometimes mentions returning to Leshan hometown",
        "family_phone": "139-xxxx-8821"
    },
    "new_witness_clue": "A shopkeeper near Exit C reported seeing an elderly man matching the description purchasing bottled water at approximately 09:30 on November 3rd, 2024, and then walking toward the taxi queue.",
    "required_output": "WeChat platform notice (for sharing in family and community groups)"
}
(workspace / "task_brief.json").write_text(json.dumps(task_brief, ensure_ascii=False, indent=2))

print("Workspace initialized successfully.")
print(f"Task brief written to: {workspace / 'task_brief.json'}")