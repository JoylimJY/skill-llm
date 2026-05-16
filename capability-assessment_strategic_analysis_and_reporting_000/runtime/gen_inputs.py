import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "raw_data/survey_results",
    "raw_data/benchmarks",
    "raw_data/interviews",
    "archives/2022",
    "archives/2023",
    "strategy/templates",
    "strategy/presentations",
    "finance/q1",
    "finance/q2",
    "ops/process_docs",
    "ops/sla_reports",
    "hr/talent_review",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "raw_data/survey_results/employee_nps_2024.csv": (
        "employee_id,nps_score,department\n"
        "E001,8,Engineering\nE002,6,Sales\nE003,9,Product\nE004,5,HR\nE005,7,Operations\n"
    ),
    "raw_data/survey_results/customer_satisfaction_q2.txt": (
        "Customer Satisfaction Survey Q2 2024\n"
        "Overall CSAT: 82%\nNPS: 34\nTop complaint: onboarding complexity\n"
    ),
    "archives/2022/old_capability_matrix.csv": (
        "area,score_2022\nRegulatory,5\nAI,3\nData,4\nPatient UX,5\nInterop,3\nTalent,6\n"
    ),
    "archives/2023/strategy_snapshot.txt": (
        "2023 Strategy Snapshot\n"
        "Focus areas: AI adoption, compliance hardening\n"
        "Budget allocated: $12M\n"
    ),
    "strategy/templates/swot_template.md": (
        "# SWOT Template\n## Strengths\n## Weaknesses\n## Opportunities\n## Threats\n"
    ),
    "strategy/presentations/board_deck_outline.txt": (
        "Board Deck Q3 2024\n1. Revenue Update\n2. Product Roadmap\n3. Competitive Landscape\n"
    ),
    "finance/q1/budget_summary.txt": "Q1 Budget: $3.2M spent of $3.5M allocated\n",
    "finance/q2/budget_summary.txt": "Q2 Budget: $3.8M spent of $4.0M allocated\n",
    "ops/process_docs/incident_response_v2.md": (
        "# Incident Response Runbook v2\n## Severity Levels\nP0: < 15 min response\nP1: < 1 hr\n"
    ),
    "ops/sla_reports/uptime_report_june.txt": "Uptime June 2024: 99.82%\nTotal incidents: 3\n",
    "hr/talent_review/performance_cycle_notes.txt": (
        "Performance Cycle H1 2024\nHigh performers: 18%\nPIP candidates: 4%\n"
    ),
    "raw_data/interviews/exec_interview_notes.txt": (
        "Interview with CTO - June 2024\n"
        "Key themes: Need to accelerate AI roadmap, compliance is table-stakes now,\n"
        "hiring pipeline is thin in ML roles.\n"
        "Regulatory team feels stretched.\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── PRIMARY INPUT: Messy, fragmented capability data ─────────────────────────

# File 1: Internal scores — intentionally messy, mixed formatting
with open(os.path.join(workspace, "raw_data/survey_results/capability_self_assessment_raw.txt"), "w") as f:
    f.write(
        "MediCore Health Technologies — Internal Capability Self-Assessment\n"
        "Conducted: July 2024  |  Respondents: 14 senior leaders\n"
        "=========================================================\n"
        "\n"
        "REGULATORY COMPLIANCE\n"
        "  Average score from leadership survey: 8 out of 10\n"
        "  Notes: FDA 510(k) process well-established; SOC2 Type II certified.\n"
        "\n"
        "Clinical AI / ML Capability\n"
        "  Score: 5/10\n"
        "  Notes: Two production models; team is small (4 ML engineers). Roadmap\n"
        "  exists but execution is slow. Stakeholders frustrated.\n"
        "\n"
        "Data Infrastructure\n"
        "  Leadership rating -> 6 (out of ten)\n"
        "  Notes: EHR integrations inconsistent; data lake partially operational.\n"
        "\n"
        "Patient Experience Design\n"
        "  Scored: seven out of ten (7)\n"
        "  Notes: Mobile app rated 4.3/5 on app stores. UX team is strong.\n"
        "\n"
        "Interoperability / Integration\n"
        "  Score reported as: 4 / 10\n"
        "  Context: HL7 FHIR adoption at ~40%. Legacy HL7 v2 still dominant.\n"
        "\n"
        "Talent Pipeline & Org Capability\n"
        "  Consensus score: 6/10\n"
        "  Notes: Good mid-level talent; C-suite technical depth lacking.\n"
        "  Hiring lag for ML/data roles averaging 4 months.\n"
    )

# File 2: Benchmark data — also messy, different layout
with open(os.path.join(workspace, "raw_data/benchmarks/competitor_benchmark_data.txt"), "w") as f:
    f.write(
        "Benchmark Reference: Apex Health Systems (Best-in-Class Competitor)\n"
        "Source: Public filings, analyst reports, industry surveys (Gartner 2024)\n"
        "Assessment Date: Q2 2024\n"
        "-------------------------------------------------------------------\n"
        "\n"
        "The following scores represent Apex Health Systems' estimated capability\n"
        "levels across the same six dimensions assessed internally at MediCore.\n"
        "\n"
        "1. Regulatory Compliance    →  9/10\n"
        "   (Apex holds 23 FDA clearances; dedicated 40-person regulatory affairs team)\n"
        "\n"
        "2. Clinical AI / ML         →  9/10\n"
        "   (Apex has 6 FDA-cleared AI products, 50+ ML engineers, published research)\n"
        "\n"
        "3. Data Infrastructure      →  8/10\n"
        "   (Unified data platform; real-time FHIR R4 pipelines; 200+ hospital clients)\n"
        "\n"
        "4. Patient Experience Design → 8/10\n"
        "   (Award-winning patient portal; 4.7/5 app rating; dedicated design team of 22)\n"
        "\n"
        "5. Interoperability          →  9/10\n"
        "   (Full FHIR R4 compliance; Epic/Cerner certified; 300+ API integrations)\n"
        "\n"
        "6. Talent Pipeline           →  7/10\n"
        "   (Strong recruiting brand; university partnerships; avg fill time 6 weeks)\n"
        "\n"
        "Note: Scores above are estimates based on publicly available data and\n"
        "should be treated as directional, not absolute.\n"
    )

# File 3: Context file with suggested actions (agent should use these for the Actions column)
with open(os.path.join(workspace, "raw_data/interviews/strategic_priorities_notes.txt"), "w") as f:
    f.write(
        "Strategic Action Suggestions — Leadership Offsite July 2024\n"
        "============================================================\n"
        "\n"
        "Interoperability gap is the most critical. Action: Launch FHIR R4 migration\n"
        "program with dedicated engineering squad; target 80% FHIR coverage by Q2 2025.\n"
        "\n"
        "Clinical AI gap is significant. Action: Hire 10 senior ML engineers in H2 2024;\n"
        "establish AI Center of Excellence with external advisory board.\n"
        "\n"
        "Data Infrastructure needs investment. Action: Complete data lake phase 2;\n"
        "implement real-time EHR sync pipeline by Q1 2025.\n"
        "\n"
        "Regulatory Compliance is a strength vs internal baseline but Apex is ahead.\n"
        "Action: Expand regulatory affairs team by 5 FTEs; pursue 3 additional clearances.\n"
        "\n"
        "Patient Experience: minor gap. Action: Redesign onboarding flow; target 4.6 app rating.\n"
        "\n"
        "Talent Pipeline: small gap exists vs benchmark. Action: Launch university\n"
        "partnership program; reduce ML role fill time to 6 weeks.\n"
    )

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")