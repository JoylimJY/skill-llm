import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── deep distractor directory structure ──────────────────────────────────────
dirs = [
    "product/roadmap/Q3",
    "product/roadmap/Q4",
    "product/specs/drafts",
    "product/specs/approved",
    "engineering/backend/services",
    "engineering/frontend/components",
    "engineering/infra/terraform",
    "design/mockups/v1",
    "design/mockups/v2",
    "stakeholder/emails/archive",
    "stakeholder/emails/pending",
    "stakeholder/meetings/notes",
    "qa/test_plans",
    "qa/bug_reports",
    "docs/internal",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "product/roadmap/Q3/roadmap_q3.md": "# Q3 Roadmap\n- Feature A\n- Feature B\n- Deprecate legacy export\n",
    "product/roadmap/Q4/roadmap_q4_draft.md": "# Q4 Draft\nTBD\n",
    "product/specs/drafts/export_spec_OLD.txt": "Old spec for CSV export. Version 0.2. Not finalized.\n",
    "product/specs/approved/auth_spec_v1.md": "# Auth Specification v1\nOAuth2 flow with PKCE.\n",
    "engineering/backend/services/export_service.py": "# placeholder\ndef export_csv(): pass\n",
    "engineering/backend/services/billing_service.py": "# billing placeholder\n",
    "engineering/frontend/components/ExportButton.tsx": "// placeholder component\nexport default function ExportButton() { return null; }\n",
    "engineering/infra/terraform/main.tf": 'provider "aws" { region = "us-east-1" }\n',
    "design/mockups/v1/export_modal_v1.png.txt": "[binary placeholder - not real image]\n",
    "design/mockups/v2/export_modal_v2_feedback.txt": "Feedback: button too small, add progress bar\n",
    "stakeholder/emails/archive/old_feature_request_jan.txt": "From: ceo@company.com\nPlease add dark mode.\n",
    "stakeholder/emails/archive/old_feature_request_feb.txt": "From: sales@company.com\nCan we have SSO?\n",
    "stakeholder/meetings/notes/kickoff_notes.txt": "Attendees: PM, Eng Lead, Designer\nTopic: Export redesign kickoff\nAction items: TBD\n",
    "qa/test_plans/export_test_plan_draft.txt": "Test plan for export feature - INCOMPLETE\n",
    "qa/bug_reports/bug_001.txt": "BUG: Export fails for >10k rows. Priority: High.\n",
    "docs/internal/glossary.txt": "CSV: Comma Separated Values\nAPI: Application Programming Interface\n",
}

for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.write_text(content, encoding="utf-8")

# ── THE CORE PROBLEM FILE ─────────────────────────────────────────────────────
# A realistic, messy stakeholder email that the agent must refine.
# It is long, multi-point, colloquial, contains repetition, filler words,
# mixed priorities, and buried constraints.

messy_input = """\
From: david.chen@bigclient.com
To: product@ourcompany.com
Subject: the export thing we talked about

hey team,

so basically we talked about this in the last call and I guess the main thing is
we really need to be able to export data from the dashboard, like the users keep
asking for this and it's been a blocker for a while now. the format should
probably be CSV but honestly JSON would also be fine, whatever is easier I guess,
but CSV is more important because the finance team uses Excel. Also we need to be
able to filter the data before exporting, not just dump everything, because
sometimes the datasets are huge and the finance team only needs like a date range
or a specific account. oh and speaking of big datasets, if the file is really big
maybe it should like send an email when it's done instead of making the user wait
there staring at the screen, idk how hard that is to build but it would be nice.
also there was something about permissions, I think only admin users should be
able to export all data, regular users should only export their own stuff, that's
probably important for compliance reasons but I'm not sure of the exact policy.
oh yeah also the export file should probably have a timestamp in the filename so
people don't get confused when they have multiple exports. I think that's mostly
it but also we want to make sure the existing import functionality doesn't break
obviously, and I guess if there's time it would be cool to also support XLSX
format but that's not urgent at all. let me know if you need anything else!

thanks
david
"""

# Write the raw input file
input_file = workspace / "stakeholder/emails/pending/david_export_request.txt"
input_file.write_text(messy_input, encoding="utf-8")

# Write the task instruction file (business goal only, no hints about the skill)
task_file = workspace / "task.txt"
task_file.write_text(
    "The file stakeholder/emails/pending/david_export_request.txt contains a messy "
    "stakeholder email about an export feature. Clean it up into a version that the "
    "engineering team can act on directly. Save your result to refined_output.txt in "
    "the workspace root.\n",
    encoding="utf-8",
)

print("Workspace generated successfully.")
print(f"Files created: {len(distractors) + 2}")