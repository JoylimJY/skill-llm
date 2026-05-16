import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# --- Create deeply nested distractor structure ---

dirs = [
    "workforce_audit/raw_data/2024_q1",
    "workforce_audit/raw_data/2024_q2",
    "workforce_audit/processed/reports",
    "workforce_audit/processed/summaries",
    "workforce_audit/processed/archival",
    "workforce_audit/config",
    "workforce_audit/templates",
    "workforce_audit/external/benchmarks",
    "workforce_audit/external/surveys",
    "workforce_audit/logs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "workforce_audit/raw_data/2024_q1/headcount_q1.csv": (
        "dept,role,headcount\nEngineering,Software Engineer,120\nHR,Recruiter,15\nFinance,Accountant,30\n"
    ),
    "workforce_audit/raw_data/2024_q1/turnover_q1.txt": (
        "Q1 turnover rate: 4.2%\nTop exit reason: compensation\nSecondary: career growth\n"
    ),
    "workforce_audit/raw_data/2024_q2/headcount_q2.csv": (
        "dept,role,headcount\nEngineering,Software Engineer,118\nHR,Recruiter,14\nFinance,Accountant,29\n"
    ),
    "workforce_audit/raw_data/2024_q2/turnover_q2.txt": (
        "Q2 turnover rate: 3.8%\nTop exit reason: remote policy\n"
    ),
    "workforce_audit/processed/reports/automation_overview_2023.txt": (
        "Overview: General automation trends 2023.\nIndustries most affected: manufacturing, logistics.\n"
        "Note: Knowledge workers show mixed signals.\n"
    ),
    "workforce_audit/processed/summaries/exec_summary_draft.txt": (
        "DRAFT - Executive Summary\nPurpose: Review workforce risk across key roles.\n"
        "Pending: detailed per-role analysis.\n"
    ),
    "workforce_audit/processed/archival/old_risk_matrix_2021.csv": (
        "role,risk_level\nAccountant,Medium\nLawyer,Low\nSoftware Engineer,Low\n"
    ),
    "workforce_audit/config/audit_settings.json": (
        '{"version": "2.1", "output_dir": "processed/reports", "locale": "zh_CN", "include_strategies": true}\n'
    ),
    "workforce_audit/templates/report_template_blank.txt": (
        "TEMPLATE: [ROLE NAME]\n\nSection 1:\nSection 2:\nSection 3:\nSection 4:\n"
    ),
    "workforce_audit/external/benchmarks/wef_future_jobs_2025.txt": (
        "World Economic Forum Future of Jobs 2025 extract.\n"
        "Top growing: AI specialists, data analysts.\n"
        "Top declining: data entry clerks, telemarketers.\n"
    ),
    "workforce_audit/external/surveys/employee_sentiment_q2.txt": (
        "Survey responses (n=340): 62% worried about AI replacing their role.\n"
        "Most cited concern: repetitive task automation.\n"
    ),
    "workforce_audit/logs/audit_run_20240601.log": (
        "[2024-06-01 09:00] Audit pipeline started.\n"
        "[2024-06-01 09:05] Loaded 3 department files.\n"
        "[2024-06-01 09:10] Processing complete. No errors.\n"
    ),
    "workforce_audit/logs/audit_run_20240701.log": (
        "[2024-07-01 08:45] Audit pipeline started.\n"
        "[2024-07-01 08:52] Warning: missing data for Finance/Accountant sub-tasks.\n"
        "[2024-07-01 09:00] Processing complete with warnings.\n"
    ),
}

for rel_path, content in distractor_files.items():
    full_path = WORKSPACE / rel_path
    full_path.write_text(content, encoding="utf-8")

# --- THE MAIN INPUT FILE: messy workforce restructuring survey ---
# Contains multiple job roles, messy formatting, and the KEY role is "Financial Analyst" (金融分析师)
# Agent must identify the role flagged for "detailed AI displacement analysis" and produce the report.

survey_content = """\
=== WORKFORCE RESTRUCTURING SURVEY 2025 ===
Compiled by: HR Automation Task Force
Status: INTERNAL USE ONLY
Date: 2025-07-14

--- SECTION A: Roles Under Review ---

The following roles have been flagged for strategic review during the 2025 Q3 planning cycle.
Each row includes: [RoleID] | Role Title | Department | Priority Flag

[R-001] | Receptionist | Front Office | LOW_PRIORITY
[R-002] | Logistics Coordinator | Supply Chain | MEDIUM_PRIORITY
[R-003] | Financial Analyst | Finance | *** DETAILED_AI_DISPLACEMENT_ANALYSIS_REQUIRED ***
[R-004] | Graphic Designer | Marketing | LOW_PRIORITY
[R-005] | Data Entry Clerk | Operations | MEDIUM_PRIORITY
[R-006] | Senior Legal Counsel | Legal | LOW_PRIORITY

--- SECTION B: Notes from Department Heads ---

Finance Department (submitted 2025-07-10):
  "Given the rapid advances in AI for financial modeling and report generation,
  we need a thorough, structured assessment of how AI may impact our analyst pool.
  Please produce a comprehensive displacement risk analysis for: Financial Analyst."

Operations Department (submitted 2025-07-11):
  "Data entry automation is already partially deployed. No new report needed."

Legal Department (submitted 2025-07-12):
  "Legal counsel roles are complex. We do not require a detailed report at this time."

--- SECTION C: Output Instructions ---

For the role marked DETAILED_AI_DISPLACEMENT_ANALYSIS_REQUIRED:
  - Produce a full structured AI displacement risk analysis.
  - Output must be saved to a file named: financial_analyst_oaisr_report.txt
  - The report should cover all standard analysis dimensions relevant to this type of assessment.
  - Include coping strategies section.
  - Language: English and/or Chinese mixed is acceptable.

--- END OF SURVEY ---
"""

survey_path = WORKSPACE / "workforce_audit" / "raw_data" / "workforce_restructuring_survey_2025.txt"
survey_path.write_text(survey_content, encoding="utf-8")

print(f"[gen_inputs] Workspace built at {WORKSPACE}")
print(f"[gen_inputs] Survey file: {survey_path}")
print(f"[gen_inputs] Total distractor files: {len(distractor_files)}")