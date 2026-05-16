import os
import random
from pathlib import Path
from datetime import date

random.seed(42)

workspace = Path("/workspace")

# ── distractor structure ──────────────────────────────────────────────────────
dirs = [
    "lab_data/raw/batch_001",
    "lab_data/raw/batch_002",
    "lab_data/processed",
    "lab_data/qc_reports",
    "protocols/v1",
    "protocols/v2_draft",
    "projects/PROJ-Alpha",
    "projects/PROJ-Beta",
    "scripts",
    "archive/2023",
    "archive/2024",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "lab_data/raw/batch_001/sample_manifest.csv": "sample_id,volume_ul,concentration\nSMP-001,50,200\nSMP-002,45,180\n",
    "lab_data/raw/batch_002/sample_manifest.csv": "sample_id,volume_ul,concentration\nSMP-101,60,210\nSMP-102,55,195\n",
    "lab_data/processed/results_summary.txt": "Analysis complete for batch_001 and batch_002.\nPass rate: 94%\n",
    "lab_data/qc_reports/qc_2024_11.txt": "QC check November 2024 — all parameters within range.\n",
    "protocols/v1/extraction_protocol.txt": "Step 1: Centrifuge at 3000rpm for 10min.\nStep 2: Discard supernatant.\n",
    "protocols/v2_draft/extraction_protocol_v2.txt": "DRAFT — DO NOT USE IN PRODUCTION\nRevised centrifuge speed: 3500rpm.\n",
    "projects/PROJ-Alpha/overview.txt": "Project Alpha: whole-genome sequencing of 200 samples.\nLead: Dr. Chen.\n",
    "projects/PROJ-Beta/overview.txt": "Project Beta: CRISPR knockout validation.\nLead: Dr. Park.\n",
    "scripts/run_pipeline.sh": "#!/bin/bash\npython3 pipeline.py --input data/ --output results/\n",
    "archive/2023/old_notes.txt": "Old meeting notes from 2023 — archived.\n",
    "archive/2024/year_end_summary.txt": "Year-end summary: 12 projects completed, 3 ongoing.\n",
    "lab_data/README_INTERNAL.txt": "Internal use only. Do not share outside the lab.\n",
}

for rel, content in distractor_files.items():
    p = workspace / rel
    p.write_text(content, encoding="utf-8")

# ── THE CORE PROBLEM: messy onboarding notes ─────────────────────────────────
today = date.today().isoformat()

onboarding_notes = f"""ONBOARDING NOTES — AI Assistant Setup
Lab: GenomicsCore Research Unit
Date: {today}
Prepared by: Lab Manager Dr. Li Wei

=== ABOUT THE LAB AI ASSISTANT ===
Our new AI assistant will help researchers with:
- Literature lookup for CRISPR protocols
- Sample tracking in our LIMS (LabVantage)
- Drafting experiment summaries
- Booking equipment via the intranet portal

=== USER PREFERENCES ===
Primary user: Dr. Yuki Tanaka
Preferred name: Yuki (not "Dr. Tanaka", she finds it too formal)
Timezone: JST (UTC+9)
Email: yuki.tanaka@genomicscore.int
Language preference: English only for technical reports; casual messages can be bilingual (EN/JA)
Prefers bullet-point summaries over dense paragraphs.
Never use passive voice in action items.

=== PAST ERRORS LOGGED BY THE TEAM ===
ERROR #1 (2024-09-12): The AI confused sample ID "SMP-001" with run ID "RUN-001" in a LIMS query, 
causing a wrong batch report to be generated. 
Resolution: Always verify entity type (sample vs run) before querying LIMS.

ERROR #2 (2024-10-05): The AI generated an experiment summary using an outdated protocol version (v1 instead of v2).
Resolution: Always check protocols/v2_draft/ for the latest version and confirm with Yuki before using.

=== CORRECTIONS FROM YUKI (USER CORRECTIONS) ===
CORRECTION #1 (corrected on 2024-11-03): 
The AI wrote "centrifuge at 3000 rpm" in a protocol draft. Yuki corrected this: 
the lab upgraded equipment in October 2024 and the correct speed is now 3500 rpm for all extractions.
Correct action: Use 3500 rpm. Update protocol references automatically when drafting.

CORRECTION #2 (corrected on 2024-12-01):
The AI sent an equipment booking confirmation without checking the maintenance window schedule first.
Yuki corrected: Always check maintenance_schedule.xlsx on the intranet before confirming any booking.
Correct action: Pre-check maintenance windows before any equipment booking confirmation.

=== TOOL CONFIGURATIONS ===
LIMS Access:
  - System: LabVantage 8.6
  - Internal URL: http://lims.genomicscore.int:8080
  - Auth method: SSO via corporate IdP (no passwords stored by AI)
  - Known issue: Sessions expire after 30 minutes of inactivity; re-authenticate via SSO prompt.

Intranet Portal:
  - URL: http://intranet.genomicscore.int
  - Equipment booking module: /equipment/book
  - Maintenance schedule: /equipment/maintenance_schedule.xlsx

Sequencer data pipeline:
  - Script location: /workspace/scripts/run_pipeline.sh
  - Input data dir: /workspace/lab_data/raw/
  - Output dir: /workspace/lab_data/processed/

=== WORKFLOW: SAMPLE TRACKING TASK ===
When asked to track a sample or retrieve LIMS data:
1. Confirm entity type with user (sample ID vs run ID vs project ID).
2. Open LIMS at http://lims.genomicscore.int:8080 (SSO login).
3. Navigate to the correct module (Samples / Runs / Projects).
4. Export report as CSV.
5. Summarize findings in bullet points for Yuki.
6. Save summary to lab_data/processed/ with date-stamped filename.

=== TODAY'S COMPLETED TASKS ===
- Reviewed and confirmed onboarding notes with Dr. Li Wei.
- Verified LIMS connectivity (SSO working).
- Confirmed protocol version in use: v2_draft extraction_protocol_v2.txt.
- Introduced AI assistant to Yuki; she approved the setup.

=== IMPORTANT DECISIONS MADE TODAY ===
- Decision: Use v2_draft protocol as the authoritative source until v2 is formally released.
  Reason: v1 is outdated post-equipment upgrade in October 2024.
- Decision: AI will not store any credentials; SSO is the only auth method.
  Reason: Security policy mandated by IT.

=== FOLLOW-UP ITEMS ===
- Confirm with Dr. Park whether PROJ-Beta AI tasks need separate LIMS permissions.
- Get formal sign-off from IT on SSO integration documentation.
- Schedule first live test run of the sample tracking workflow with Yuki next week.
"""

(workspace / "ONBOARDING_NOTES.txt").write_text(onboarding_notes, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Today's date: {today}")
print(f"Key file: /workspace/ONBOARDING_NOTES.txt")