import json
import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "data",
    "profile",
    "follow_ups",
    "notes/companies",
    "notes/interviews",
    "resume/versions",
    "resume/templates",
    "scripts",
    "logs",
    "archive/2025",
]
for d in dirs:
    Path(WORKSPACE, d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "profile/career.md": """# Career Profile — Jordan Rivera

## Summary
7 years building distributed systems at scale. Former Staff Engineer at DataStream Inc.
Laid off Jan 2026 after org restructuring.

## Skills
- Languages: Python, Go, Rust, TypeScript
- Systems: Kafka, Kubernetes, PostgreSQL, Redis
- Cloud: AWS (ECS, Lambda, RDS), GCP basics

## Experience
### DataStream Inc — Staff Engineer (2021–2026)
- Led migration of monolith to microservices; reduced p99 latency 40%
- Built real-time event pipeline processing 2M events/sec
- Mentored 6 engineers across 2 teams

### Nexbridge — Senior Engineer (2019–2021)
- Owned payment reconciliation service ($500M/day throughput)
- Introduced gRPC between services; cut inter-service overhead 25%

### CloudBase (startup) — Engineer (2018–2019)
- Full-stack: React frontend + Node.js API + PostgreSQL

## Education
BSc Computer Science, State University, 2018
""",
    "notes/companies/stripe.md": "Stripe — payments infra, NYC/remote, Series H, ~8000 employees.\nKnown for bar-raising interviews.",
    "notes/companies/temporal.md": "Temporal.io — workflow orchestration, Series B.\nTech blog active, strong OSS community.",
    "notes/interviews/phone_screen_prep.md": "Generic phone screen notes — 30 min, usually 1 behavioral + 1 coding.",
    "resume/versions/resume_v3.md": "# Resume v3 — General Purpose\n(See career.md for full detail)",
    "resume/versions/resume_v4_backend.md": "# Resume v4 — Backend Focus\nHighlights Kafka and Kubernetes experience.",
    "resume/templates/cover_letter_template.txt": "Dear Hiring Manager,\n\nI am excited to apply for the [ROLE] position at [COMPANY]...",
    "scripts/export_csv.py": "# stub — export applications to CSV\nprint('not implemented')",
    "logs/activity_2026_01.log": "2026-01-15 Signed up for LinkedIn Premium\n2026-01-20 Updated resume\n2026-01-28 Started applying\n",
    "archive/2025/old_tracker.json": json.dumps({"note": "2025 job search — abandoned after receiving counter-offer"}),
    "notes/interviews/system_design_notes.md": "## System Design Patterns\n- Consistent hashing\n- Saga pattern for distributed txns\n- CQRS + event sourcing",
}
for path, content in distractors.items():
    Path(WORKSPACE, path).write_text(content)

# ── PROBLEM: messy raw applications from a spreadsheet export ────────────────
# This CSV is what the agent needs to parse and import into data/applications.json
# The dates are intentionally varied to test business-day follow-up logic.
# Reference "today" for the task: 2026-03-10 (Tuesday)
# Business-day gaps (from 2026-03-10 backwards):
#   - applied 2026-02-27 (Friday)  → 7 business days ago → OVERDUE (>5 biz days, no response)
#   - applied 2026-03-02 (Monday)  → 6 business days ago → OVERDUE
#   - applied 2026-03-03 (Tuesday) → 5 business days ago → OVERDUE (exactly 5)
#   - applied 2026-03-04 (Wednesday) → 4 business days ago → NOT overdue
#   - applied 2026-03-05 (Thursday) → 3 business days ago → NOT overdue
#   Note: 2026-03-07 and 2026-03-08 are Sat/Sun — skipped in business day count

raw_apps_csv = """\
company,role,url,status,applied_date,source,contact,notes
Stripe,Senior Backend Engineer,https://stripe.com/jobs/1,applied,2026-02-27,linkedin,,Great team culture
Temporal,Staff Software Engineer,https://temporal.io/jobs/42,applied,2026-03-02,referral,alex@temporal.io,Referred by Alex Kim
PlanetScale,Database Engineer,https://planetscale.com/jobs/7,applied,2026-03-03,company_site,,Interesting MySQL-based infra
Cloudflare,Systems Engineer,https://cloudflare.com/jobs/99,applied,2026-03-04,hacker_news,,Edge computing focus
Vercel,Backend Infrastructure Engineer,https://vercel.com/jobs/12,applied,2026-03-05,linkedin,,Next.js infra team
CockroachLabs,Distributed Systems Engineer,https://cockroachlabs.com/jobs/3,phone_screen,2026-02-20,linkedin,recruiter@cockroachlabs.com,Phone screen was 2026-03-05
DataDog,Senior Engineer - APM,https://datadoghq.com/jobs/55,applied,2026-02-15,linkedin,,Large observability stack
Figma,Infrastructure Engineer,https://figma.com/jobs/21,rejected,2026-02-10,company_site,,No feedback given
Notion,Backend Engineer,https://notion.so/jobs/8,applied,2026-02-27,linkedin,,Collaborative tools space
Anthropic,Software Engineer - Infrastructure,https://anthropic.com/jobs/6,applied,2026-03-02,company_site,,AI safety focus
"""
Path(WORKSPACE, "data/raw_applications.csv").write_text(raw_apps_csv)

# ── Existing applications.json — has one pre-existing entry + partially wrong stats
existing_data = {
    "applications": [
        {
            "id": "app_001",
            "company": "Stripe",           # DUPLICATE — agent must detect and skip
            "role": "Senior Backend Engineer",
            "url": "https://stripe.com/jobs/1",
            "status": "applied",
            "applied_date": "2026-02-27",
            "source": "linkedin",
            "contact": None,
            "notes": "Great team culture",
            "follow_up_date": "2026-03-06",
            "interviews": [],
            "outcome": None
        },
        {
            "id": "app_002",
            "company": "DataDog",
            "role": "Senior Engineer - APM",
            "url": "https://datadoghq.com/jobs/55",
            "status": "applied",
            "applied_date": "2026-02-15",
            "source": "linkedin",
            "contact": None,
            "notes": "Large observability stack",
            "follow_up_date": "2026-02-22",
            "interviews": [],
            "outcome": None
        }
    ],
    "stats": {
        "total_applied": 0,   # intentionally wrong — agent must recompute
        "responses": 0,
        "interviews": 0,
        "offers": 0,
        "response_rate": 0
    },
    "saved_roles": []
}
Path(WORKSPACE, "data/applications.json").write_text(
    json.dumps(existing_data, indent=2)
)

print("Workspace initialized.")
print(f"Files created under: {WORKSPACE}")