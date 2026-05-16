import os
import json
import random

random.seed(42)

base = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "projects/alpha_compound/logs",
    "projects/alpha_compound/docs",
    "projects/beta_compound/logs",
    "projects/beta_compound/docs",
    "projects/gamma_compound/logs",
    "projects/gamma_compound/docs",
    "archive/2024/q1",
    "archive/2024/q2",
    "team/schedules",
    "team/reports",
    "tools/scripts",
    "tools/templates",
    "weekly_reviews",
    "open_questions",
    "inputs",
    "outputs",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "projects/alpha_compound/docs/assay_protocol_v2.txt": "Assay Protocol v2\nCell viability measured by MTT. IC50 target: <10nM.\nProtocol last updated: 2024-11-01.",
    "projects/alpha_compound/docs/compound_structure.txt": "Molecular formula: C22H25N3O4\nMolecular weight: 411.46 g/mol\nSolubility: DMSO 50mM stock",
    "projects/beta_compound/docs/regulatory_notes.txt": "IND filing target: Q3 2025.\nPreclinical package must include ADME, tox, efficacy data.",
    "projects/gamma_compound/docs/synthesis_notes.txt": "Step 3 of 7 in synthesis route confirmed. Yield 68%.",
    "archive/2024/q1/q1_summary.txt": "Q1 Summary: Three compounds advanced to in vitro stage.",
    "archive/2024/q2/q2_summary.txt": "Q2 Summary: Alpha compound showed promising IC50 < 8nM.",
    "team/schedules/lab_rotation_aug2025.txt": "Lab rotation schedule: Mon-Fri 8am-6pm, weekend cover required for cell culture.",
    "team/reports/headcount_2025.txt": "Current FTEs: 12 scientists, 3 PMs, 2 data analysts.",
    "tools/scripts/data_cleaner.py": "# stub data cleaning script\npass",
    "tools/templates/project_card_template.json": json.dumps({
        "project_id": "TEMPLATE",
        "project_name": "Template Project",
        "current_phase": "PHASE_X",
        "milestone": "TBD",
        "goals": [],
        "blockers": [],
        "status": "IDLE"
    }, indent=2),
    "tools/templates/daily_log_template.json": json.dumps({
        "date": "YYYY-MM-DD",
        "project_id": "TEMPLATE",
        "execution_summary": "",
        "findings": [],
        "decisions": [],
        "next_action": ""
    }, indent=2),
    "archive/2024/q1/old_loop_log_2024-01-15.json": json.dumps({
        "date": "2024-01-15",
        "project_id": "ALPHA-001",
        "execution_summary": "Ran cytotoxicity screen on 48 compounds.",
        "findings": ["12 hits identified above threshold"],
        "decisions": ["Proceed with top 5 hits to dose-response"],
        "next_action": "Run dose-response curves for top 5 hits"
    }, indent=2),
    "archive/2024/q2/old_loop_log_2024-04-03.json": json.dumps({
        "date": "2024-04-03",
        "project_id": "ALPHA-001",
        "execution_summary": "Dose-response completed. Alpha-7 compound selected.",
        "findings": ["Alpha-7 IC50 = 7.2nM", "Low cytotoxicity at 100x therapeutic dose"],
        "decisions": ["Advance Alpha-7 to ADME panel"],
        "next_action": "Submit Alpha-7 for ADME profiling"
    }, indent=2),
    "weekly_reviews/weekly_review_2025-07-07_STALE.txt": "STALE DRAFT - DO NOT USE\nWeek of Jul 7: Preliminary ADME results expected.",
}
for rel_path, content in distractors.items():
    with open(os.path.join(base, rel_path), "w") as f:
        f.write(content)

# ── SCENARIO A: Valid project card (ALPHA-001) ───────────────────────────────
# Has all required fields. Has a forced_bottleneck override.
project_card_alpha = {
    "project_id": "ALPHA-001",
    "project_name": "Alpha-7 Compound Advancement",
    "current_phase": "ADME_PROFILING",
    "milestone": "Complete ADME panel and submit data package to regulatory team by 2025-08-15",
    "goals": [
        "Obtain full ADME profile for Alpha-7 compound",
        "Identify metabolic stability liabilities",
        "Prepare regulatory data package"
    ],
    "blockers": [
        "CYP450 inhibition assay results delayed by vendor (3 days overdue)",
        "Data analyst unavailable until next week",
        "Protein binding data format incompatible with regulatory template"
    ],
    "status": "READY",
    "last_updated": "2025-07-14"
}

# Latest weekly review for ALPHA-001
weekly_review_alpha = {
    "week_of": "2025-07-14",
    "project_id": "ALPHA-001",
    "summary": "ADME panel 60% complete. CYP450 results are the critical path item. Protein binding data received but format needs manual correction. Regulatory team confirmed 2025-08-15 hard deadline.",
    "risks": ["Vendor delay on CYP450 may compress regulatory review window"],
    "action_items": ["Chase vendor for CYP450 ETA", "Fix protein binding data format"]
}

# Recent daily logs for ALPHA-001 (last 3)
daily_logs_alpha = [
    {
        "date": "2025-07-12",
        "project_id": "ALPHA-001",
        "execution_summary": "Attempted to reformat protein binding data. Partial success — 70% of records converted.",
        "findings": ["Format mismatch in 30% of records due to legacy column headers"],
        "decisions": ["Use scripted mapping for remaining 30% rather than manual fix"],
        "next_action": "Complete protein binding data reformatting script and validate output"
    },
    {
        "date": "2025-07-13",
        "project_id": "ALPHA-001",
        "execution_summary": "Ran reformatting script. All protein binding records now in correct format. Validated against template.",
        "findings": ["All 142 records now compliant with regulatory template", "Microsomal stability data also ready"],
        "decisions": ["Protein binding blocker is now resolved", "Focus shifts to CYP450 bottleneck"],
        "next_action": "Contact vendor for CYP450 inhibition assay status update"
    },
    {
        "date": "2025-07-14",
        "project_id": "ALPHA-001",
        "execution_summary": "Vendor contacted re: CYP450 results. Received partial dataset (3 of 7 CYP isoforms). Waiting for remaining 4.",
        "findings": ["CYP3A4 and CYP2D6 show no significant inhibition (IC50 > 30µM)", "CYP2C9 shows moderate inhibition — requires follow-up"],
        "decisions": ["Flag CYP2C9 finding for regulatory package with appropriate risk note", "Do not wait idly — begin assembly of partial data package"],
        "next_action": "Begin partial regulatory data package assembly with available ADME data"
    }
]

# Open questions for ALPHA-001
open_questions_alpha = [
    "Is CYP2C9 moderate inhibition a deal-breaker for IND filing or just a risk note?",
    "Can we submit a partial data package to regulatory team for early review while CYP450 data is pending?",
    "Who is the backup data analyst if primary remains unavailable?"
]

# forced_bottleneck for ALPHA-001 (overrides automatic selection)
forced_bottleneck_alpha = "Assemble partial regulatory data package using available ADME data (protein binding + microsomal stability + partial CYP450) while awaiting remaining CYP isoform results from vendor"

# Save ALPHA-001 inputs
with open(os.path.join(base, "inputs/project_card_alpha.json"), "w") as f:
    json.dump(project_card_alpha, f, indent=2)

with open(os.path.join(base, "inputs/weekly_review_alpha.json"), "w") as f:
    json.dump(weekly_review_alpha, f, indent=2)

with open(os.path.join(base, "inputs/daily_logs_alpha.json"), "w") as f:
    json.dump(daily_logs_alpha, f, indent=2)

with open(os.path.join(base, "inputs/open_questions_alpha.json"), "w") as f:
    json.dump(open_questions_alpha, f, indent=2)

with open(os.path.join(base, "inputs/forced_bottleneck_alpha.txt"), "w") as f:
    f.write(forced_bottleneck_alpha)

# ── SCENARIO B: INCOMPLETE project card (BETA-002) ───────────────────────────
# Missing `current_phase` field entirely → must trigger BLOCKED state, safe_to_proceed=false
project_card_beta = {
    "project_id": "BETA-002",
    "project_name": "Beta Scaffold Lead Optimization",
    # NOTE: current_phase is intentionally MISSING
    "milestone": "Identify lead compound with selectivity index > 100",
    "goals": [
        "Run selectivity panel across 12 off-targets",
        "Confirm potency retention after scaffold modification"
    ],
    "blockers": [
        "Selectivity panel assay not yet booked"
    ],
    "status": "IDLE",
    "last_updated": "2025-07-10"
}

# Weekly review for BETA-002 — vague, unhelpful
weekly_review_beta = {
    "week_of": "2025-07-14",
    "project_id": "BETA-002",
    "summary": "Some progress expected. Team still aligning on next steps.",
    "risks": ["Unclear project phase may slow execution"],
    "action_items": []
}

# Recent daily logs for BETA-002 — only 1 log, and it's unclear
daily_logs_beta = [
    {
        "date": "2025-07-10",
        "project_id": "BETA-002",
        "execution_summary": "Kickoff meeting held. No concrete actions yet.",
        "findings": [],
        "decisions": ["Waiting for project card to be finalized"],
        "next_action": None
    }
]

# Open questions for BETA-002
open_questions_beta = [
    "What phase is this project currently in?",
    "Has the selectivity panel protocol been approved?",
    "Who owns the BETA-002 project card updates?"
]

# No forced_bottleneck for BETA-002

# Save BETA-002 inputs
with open(os.path.join(base, "inputs/project_card_beta.json"), "w") as f:
    json.dump(project_card_beta, f, indent=2)

with open(os.path.join(base, "inputs/weekly_review_beta.json"), "w") as f:
    json.dump(weekly_review_beta, f, indent=2)

with open(os.path.join(base, "inputs/daily_logs_beta.json"), "w") as f:
    json.dump(daily_logs_beta, f, indent=2)

with open(os.path.join(base, "inputs/open_questions_beta.json"), "w") as f:
    json.dump(open_questions_beta, f, indent=2)

# ── Task instructions file ────────────────────────────────────────────────────
task_instructions = {
    "task": "Process daily advancement for two R&D projects",
    "projects": [
        {
            "id": "ALPHA-001",
            "project_card": "inputs/project_card_alpha.json",
            "weekly_review": "inputs/weekly_review_alpha.json",
            "recent_daily_logs": "inputs/daily_logs_alpha.json",
            "open_questions": "inputs/open_questions_alpha.json",
            "forced_bottleneck": "inputs/forced_bottleneck_alpha.txt"
        },
        {
            "id": "BETA-002",
            "project_card": "inputs/project_card_beta.json",
            "weekly_review": "inputs/weekly_review_beta.json",
            "recent_daily_logs": "inputs/daily_logs_beta.json",
            "open_questions": "inputs/open_questions_beta.json"
        }
    ],
    "output_file": "daily_loop_output.json"
}

with open(os.path.join(base, "task.json"), "w") as f:
    json.dump(task_instructions, f, indent=2)

print("Workspace generation complete.")
print("Files created:")
for root, dirs_list, files in os.walk(base):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")