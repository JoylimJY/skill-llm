import os
import random

random.seed(42)

BASE = "/workspace"

# --- Create the memory/ directory structure (Layer 1: recent memories) ---
os.makedirs(f"{BASE}/memory", exist_ok=True)
os.makedirs(f"{BASE}/memory/archive", exist_ok=True)

# memory/*.md files — some contain CX-7749, some are distractors
memory_files = {
    "memory/2024-11-15_meeting_notes.md": """# Team Meeting - Nov 15
Discussed Q4 budget allocation and headcount planning.
Reviewed progress on compound CX-7749 synthesis pathway.
Next steps: order reagents for batch 3.
Tags: #meeting #budget #CX-7749
""",
    "memory/2024-11-20_lab_update.md": """# Lab Update
Weekly status: fermentation run completed.
Note: CX-7749 showed unexpected binding affinity in assay A12.
Need to revisit the docking simulation parameters.
Tags: #lab #assay #CX-7749
""",
    "memory/2024-10-05_project_kickoff.md": """# Project Kickoff Notes
Initiated Phase II trials for compound series CX-6000 through CX-7100.
Team leads assigned. Budget approved.
Tags: #kickoff #Phase2 #CX-6000
""",
    "memory/2024-09-18_vendor_call.md": """# Vendor Call
Discussed reagent pricing with BioSupply Inc.
No specific compound discussed. General procurement topics.
Tags: #vendor #procurement
""",
    "memory/2024-12-01_safety_review.md": """# Safety Review
Annual lab safety audit completed. All equipment certified.
No incidents reported. Next review: June 2025.
Tags: #safety #audit
""",
}

# memory/archive/*.md — archived older memories, some contain CX-7749
archive_files = {
    "memory/archive/2024-06-10_early_synthesis.md": """# Early Synthesis Log - June 2024
Initial synthesis attempt for CX-7749. Yield: 34%.
Protocol: standard Suzuki coupling. Solvent: DMF.
Requires optimization. See batch_log_001.
Tags: #synthesis #CX-7749 #archive
""",
    "memory/archive/2024-07-22_regulatory_note.md": """# Regulatory Pre-submission Note
Pre-IND meeting scheduled for CX-7749 with FDA counterpart team.
Prepared briefing document. Outcome: favorable preliminary feedback.
Tags: #regulatory #CX-7749 #FDA #archive
""",
    "memory/archive/2024-05-01_compound_library.md": """# Compound Library Inventory
Full inventory of Series CX compounds: CX-1000 to CX-8000.
Storage conditions and expiry dates logged.
No specific protocol details here.
Tags: #inventory #compounds #archive
""",
    "memory/archive/2024-03-15_deprecated_protocol.md": """# Deprecated Protocol - March 2024
Old HPLC protocol for CX-3200 series. Now superseded.
Do not use for current compounds.
Tags: #deprecated #HPLC #CX-3200 #archive
""",
}

# Workspace-wide files (Layer 3 territory) — scattered .md files
workspace_files = {
    "projects/cx7749/batch_log_001.md": """# Batch Log 001 — CX-7749
Date: 2024-06-08
Operator: Dr. Chen
Batch size: 50mg
Reaction conditions: 80°C, 12h, N2 atmosphere
Result: 34% yield — see early_synthesis archive note
Status: Archived, superseded by batch_log_003
""",
    "projects/cx7749/batch_log_003.md": """# Batch Log 003 — CX-7749
Date: 2024-10-22
Operator: Dr. Patel
Batch size: 200mg
Reaction conditions: 85°C, 10h, Ar atmosphere, Pd catalyst optimized
Result: 71% yield — significant improvement
Status: Active reference protocol
Tags: #CX-7749 #synthesis #optimized
""",
    "projects/shared/literature_refs.md": """# Literature References
1. Smith et al. 2022 - JACS - Pd-catalyzed cross-coupling
2. Lee et al. 2023 - Nature Chem - Binding affinity prediction
3. CX-7749 structural analog discussed in Kumar et al. 2021
No direct CX-7749 data in literature section.
""",
    "projects/cx6000/protocol_v2.md": """# CX-6000 Series Protocol v2
Updated reaction conditions for CX-6100 and CX-6200.
Solvent switch from DCM to THF.
No CX-7749 content here.
Tags: #CX-6000 #protocol
""",
    "reports/Q3_summary.md": """# Q3 Summary Report
Overall lab productivity up 12%.
Key milestones: CX-7749 Phase I data submitted.
Headcount stable. Budget on track.
Tags: #Q3 #summary #CX-7749
""",
    "reports/Q4_forecast.md": """# Q4 Forecast
Projected spend: $2.3M. Headcount +2 FTEs.
CX-9000 series to begin Q1 2025.
No CX-7749 specific content.
Tags: #Q4 #forecast
""",
    "data/assay_results/assay_A12_raw.md": """# Assay A12 Raw Results
Compound: CX-7749
IC50: 23nM
Selectivity ratio: >100x
Run date: 2024-11-18
Operator: Dr. Kim
Status: Confirmed positive hit
""",
    "data/assay_results/assay_B05_raw.md": """# Assay B05 Raw Results
Compound: CX-6500
IC50: 450nM
Run date: 2024-10-10
Status: Deprioritized
""",
    "docs/onboarding/new_member_guide.md": """# New Member Guide
Welcome to the lab. Please read all safety protocols.
Refer to the compound library for inventory.
Contact the lab manager for access to archived data.
""",
    "docs/sops/sop_hplc.md": """# SOP: HPLC Analysis
Standard operating procedure for HPLC analysis.
Applies to all CX-series compounds.
Updated: 2024-09-01
""",
}

all_files = {**memory_files, **archive_files, **workspace_files}

for rel_path, content in all_files.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Total files created: {len(all_files)}")