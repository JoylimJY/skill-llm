import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "governance/internal/drafts",
    "governance/internal/archived",
    "governance/reports/2024",
    "governance/reports/2025",
    "partnerships/candidates",
    "partnerships/vetted",
    "legal/contracts",
    "legal/compliance_notes",
    "tech_audit/tools",
    "tech_audit/findings",
    "hr/headcount",
    "finance/budgets",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# distractor files
distractors = {
    "governance/internal/drafts/partnership_criteria_v1.txt": "Draft criteria for new marketplace partners. Focus: uptime SLA, API compatibility, user base size.",
    "governance/internal/archived/old_vendor_matrix.csv": "vendor,score,notes\nMarketA,7.2,legacy\nMarketB,8.1,preferred\nMarketC,6.0,deprecated",
    "governance/reports/2024/q3_technical_audit_summary.txt": "Technical audit of NexusSkillHub code samples. 3 of 47 samples had dependency issues. Resolved.",
    "governance/reports/2025/q1_uptime_report.txt": "NexusSkillHub uptime: 99.7%. Incident count: 2. MTTR: 43 minutes.",
    "partnerships/candidates/nexusskillhub_overview.txt": "NexusSkillHub launched 2022. Claims 12,000+ skills. 1,100 registered publishers. Operates in US/EU/APAC.",
    "partnerships/vetted/agentcore_approval.txt": "AgentCore marketplace approved for Tier-1 partnership. Technical review passed. Business review passed.",
    "legal/contracts/nexusskillhub_draft_msa.txt": "DRAFT MSA: NexusSkillHub. Indemnification clause TBD. Liability cap: $500k. Review by Legal required.",
    "legal/compliance_notes/gdpr_checklist.txt": "GDPR checklist for NexusSkillHub integration. Data residency: EU confirmed. DPA signed: pending.",
    "tech_audit/tools/scan_config.json": json.dumps({"scanner": "SkillGuard", "depth": "shallow", "last_run": "2025-01-15"}),
    "tech_audit/findings/nexusskillhub_scan_jan2025.txt": "Static scan results: 0 critical, 3 medium (all dependency version pinning). No credential leaks detected.",
    "hr/headcount/nexusskillhub_linkedin_estimates.txt": (
        "NexusSkillHub LinkedIn headcount estimates (Jan 2025):\n"
        "  Engineering: ~110\n"
        "  Product/Growth: ~72\n"
        "  Marketing: ~18\n"
        "  Safety/Trust & Safety: ~9\n"
        "  Legal/Compliance: ~6\n"
        "  Other: ~14\n"
        "Total estimated employees: ~229\n"
        "Note: These are estimates from LinkedIn profile analysis, not official figures."
    ),
    "finance/budgets/placeholder.txt": "Budget data for NexusSkillHub not available publicly.",
}
for path, content in distractors.items():
    (workspace / path).write_text(content)

# ── CORE INPUT FILES ─────────────────────────────────────────────────────────
# File 1: Publisher activity data (raw, messy)
publisher_data_path = workspace / "partnerships/candidates/nexusskillhub_publisher_activity.json"
publishers = []
# Top 10 high-volume publishers
top_publisher_names = [f"PowerPublisher_{i}" for i in range(1, 11)]
top_skills = [61, 54, 48, 43, 40, 37, 34, 31, 29, 27]  # skills published last 30 days
for i, name in enumerate(top_publisher_names):
    publishers.append({"publisher_id": f"PP{i+1:03d}", "name": name, "skills_last_30d": top_skills[i], "total_skills": top_skills[i] * 6, "verified": True})

# Remaining publishers (total 920 active publishers)
remaining_count = 910
remaining_total_skills = 0
for i in range(remaining_count):
    s = random.randint(0, 4)
    remaining_total_skills += s
    publishers.append({
        "publisher_id": f"SP{i+1:04d}",
        "name": f"SmallPublisher_{i+1}",
        "skills_last_30d": s,
        "total_skills": s * random.randint(3, 8),
        "verified": random.random() > 0.3
    })

# Total skills by top 10
top10_total = sum(top_skills)  # 404
# Total all publishers
all_skills_30d = top10_total + remaining_total_skills

publisher_data = {
    "marketplace": "NexusSkillHub",
    "snapshot_date": "2025-06-01",
    "active_publishers_count": len(publishers),
    "publishers": publishers,
    "note": "Active publisher = published at least 1 skill in last 90 days. Data exported from public API."
}
publisher_data_path.write_text(json.dumps(publisher_data, indent=2))

# Compute and stash expected values for eval
top10_pct = round(top10_total / all_skills_30d * 100, 1)

# File 2: Job postings / review team info
job_postings_path = workspace / "partnerships/candidates/nexusskillhub_job_data.txt"
job_postings_path.write_text(
    "NexusSkillHub Open & Recently Filled Positions (scraped 2025-05-28)\n"
    "================================================================\n\n"
    "CURRENT OPENINGS:\n"
    "  - Senior ML Engineer (Growth) x2\n"
    "  - Product Manager - Discovery Algorithm x1\n"
    "  - Growth Marketing Lead x1\n\n"
    "RECENTLY FILLED (last 6 months):\n"
    "  - Trust & Safety Analyst x1 (filled Mar 2025)\n"
    "  - Trust & Safety Analyst x1 (filled Jan 2025)\n\n"
    "INFERRED REVIEW TEAM SIZE: Based on LinkedIn and job history, the Trust & Safety\n"
    "team handling skill review is estimated at 8 people currently.\n\n"
    "PUBLICATION STATS (last 30 days, from public changelog API):\n"
    "  New skills published: 3,210\n"
    "  Updates to existing skills: 8,441\n\n"
    "NOTE: NexusSkillHub has not publicly disclosed review SLAs or team composition.\n"
    "Estimate based on job board history and LinkedIn headcount.\n"
)

# File 3: Revenue model document
revenue_model_path = workspace / "partnerships/candidates/nexusskillhub_revenue_model.txt"
revenue_model_path.write_text(
    "NexusSkillHub Monetization & Revenue Model (from public documentation + press)\n"
    "==============================================================================\n\n"
    "Publisher Revenue:\n"
    "  - Publishers earn 70% of per-download fees charged to end users.\n"
    "  - NexusSkillHub retains 30% of each download transaction.\n"
    "  - Premium Placement: Publishers may pay $499/month for featured slots in\n"
    "    discovery results, boosting download visibility regardless of quality score.\n\n"
    "Marketplace Revenue Streams:\n"
    "  1. Download transaction cut (30% of all paid downloads)\n"
    "  2. Premium placement fees from publishers\n"
    "  3. Enterprise subscription fees (access to private skill registry)\n\n"
    "Publisher Acquisition:\n"
    "  - NexusSkillHub runs 'Publish More, Earn More' campaigns targeting volume.\n"
    "  - Monthly leaderboard rewards top publishers by download count with cash bonuses.\n\n"
    "Notes:\n"
    "  - No flat fee or subscription option for publishers; all revenue tied to downloads.\n"
    "  - Safety enforcement actions (delisting) directly reduce marketplace revenue.\n"
)

# File 4: Enforcement log (public actions)
enforcement_log_path = workspace / "partnerships/candidates/nexusskillhub_enforcement_log.txt"
enforcement_log_path.write_text(
    "NexusSkillHub Public Enforcement Actions Log (last 90 days)\n"
    "============================================================\n\n"
    "Small/Mid-tier Publisher Enforcement:\n"
    "  - SmallPublisher_14: Delisted 3 skills for misleading capability descriptions (2025-03-12)\n"
    "  - SmallPublisher_88: Account suspended for policy violations, skills removed (2025-03-29)\n"
    "  - SmallPublisher_203: Warning issued, 1 skill delisted for safety flag (2025-04-15)\n"
    "  - SmallPublisher_301: 2 skills delisted for undisclosed data collection (2025-05-02)\n"
    "  - MidPublisher_07: 4 skills delisted, temporary suspension (2025-05-18)\n\n"
    "Top-Tier Publisher Enforcement (Publishers in top 10 by revenue/downloads):\n"
    "  - PowerPublisher_2: 6 skills flagged by community reports for misleading descriptions.\n"
    "    Status: Under internal review. No public action taken. (Flagged 2025-02-20, still open)\n"
    "  - PowerPublisher_5: Policy violation reported by 3 enterprise customers re: data handling.\n"
    "    Status: 'Ongoing dialogue with publisher.' No enforcement action. (Since 2025-01-10)\n"
    "  - PowerPublisher_8: 2 skills with identical code to delisted SmallPublisher_14 skills.\n"
    "    Status: No action taken. Discovery algorithm still surfaces skills prominently.\n\n"
    "Summary note: Top revenue publishers have not been publicly actioned despite documented\n"
    "violations. Small publishers face faster and more definitive enforcement outcomes.\n"
)

# File 5: Minimal metadata / context file
context_path = workspace / "partnerships/candidates/assessment_context.txt"
context_path.write_text(
    "Assessment Request: NexusSkillHub Incentive Alignment\n"
    "=====================================================\n"
    "Requested by: Enterprise Partnerships Team\n"
    "Date: 2025-06-01\n"
    "Purpose: Determine whether NexusSkillHub's structural incentives are compatible\n"
    "with our enterprise clients' safety requirements before recommending as a\n"
    "preferred marketplace.\n"
    "Marketplace name for report: NexusSkillHub\n"
    "Assessment timestamp to use: 2025-06-01T09:00:00Z\n"
)

print("Workspace generated successfully.")
print(f"Total active publishers: {len(publishers)}")
print(f"Top 10 total skills (30d): {top10_total}")
print(f"All publishers total skills (30d): {all_skills_30d}")
print(f"Top 10 concentration: {top10_pct}%")
print(f"Top publisher output: {top_skills[0]} skills in 30 days")