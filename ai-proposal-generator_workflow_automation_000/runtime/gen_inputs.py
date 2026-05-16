import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "proposals/templates",
    "proposals/templates/custom",
    "proposals/themes",
    "proposals/generated",
    "meeting-notes",
    "meeting-notes/archive",
    "assets",
    "client-files/brightwave",
    "client-files/nexaflow",
    "client-files/vertexpeak",
    "internal/contracts",
    "internal/onboarding",
    "crm/leads",
    "crm/closed",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── SERVICES.md ──────────────────────────────────────────────────────────────
(workspace / "proposals" / "SERVICES.md").write_text("""\
# Services & Pricing

## Packages

### Starter — $3,500/month
- Monthly strategy sessions (2x)
- Process audit report
- Email support

### Growth — $6,500/month
- Everything in Starter
- Weekly advisory calls
- KPI dashboard setup
- Quarterly roadmap review

### Scale — $12,000/month
- Everything in Growth
- Dedicated engagement lead
- On-site workshops (2x/year)
- Custom playbook development

## Terms
- Payment: Net 15
- Engagement minimum: 3 months
- Cancellation: 30-day written notice
""")

# ── Existing built-in templates (distractor content) ──────────────────────────
(workspace / "proposals" / "templates" / "corporate.md").write_text("""\
# Corporate Proposal Template
style: corporate
sections: Cover Page, Executive Summary, Company Overview, Understanding Your Needs, Proposed Solution, Methodology, Project Team, Timeline, Investment, Terms, Appendix
""")

(workspace / "proposals" / "templates" / "entrepreneur.md").write_text("""\
# Entrepreneur Proposal Template
style: entrepreneur
sections: The Problem, The Solution, What You Get, How It Works, Investment, Why Us, Let's Go
""")

(workspace / "proposals" / "templates" / "creative.md").write_text("""\
# Creative Proposal Template
style: creative
sections: The Vision, Your Challenges, Our Approach, The Work, Case Studies, Timeline, Investment, The Team, Next Steps
""")

(workspace / "proposals" / "templates" / "consultant.md").write_text("""\
# Consultant Proposal Template
style: consultant
sections: Situation Analysis, Key Challenges, Recommendations, Engagement Options, Expected Outcomes, Credentials, Investment, Next Steps
""")

(workspace / "proposals" / "templates" / "minimal.md").write_text("""\
# Minimal Proposal Template
style: minimal
sections: Project Overview, Scope, Timeline, Investment, Terms, Accept
""")

# ── Color theme CSS files ─────────────────────────────────────────────────────
themes = {
    "ocean-blue.css": """\
:root {
  --primary: #0ea5e9;
  --accent: #0284c7;
  --background: #ffffff;
  --text: #1e293b;
  --surface: #f0f9ff;
}
""",
    "ember-orange.css": """\
:root {
  --primary: #ff6b35;
  --accent: #ff8c42;
  --background: #fff7f0;
  --text: #1a0a00;
  --surface: #fff3e8;
}
""",
    "forest-green.css": """\
:root {
  --primary: #22c55e;
  --accent: #16a34a;
  --background: #f0fdf4;
  --text: #14532d;
  --surface: #dcfce7;
}
""",
    "slate-dark.css": """\
:root {
  --primary: #1e293b;
  --accent: #475569;
  --background: #0f172a;
  --text: #f1f5f9;
  --surface: #1e293b;
}
""",
    "royal-purple.css": """\
:root {
  --primary: #8b5cf6;
  --accent: #7c3aed;
  --background: #faf5ff;
  --text: #1e1b4b;
  --surface: #f3e8ff;
}
""",
    "trust-navy.css": """\
:root {
  --primary: #1e3a5f;
  --accent: #2563eb;
  --background: #f8fafc;
  --text: #0f172a;
  --surface: #e8f0fe;
}
""",
}
for name, content in themes.items():
    (workspace / "proposals" / "themes" / name).write_text(content)

# ── assets/proposal-template.html ────────────────────────────────────────────
(workspace / "assets" / "proposal-template.html").write_text("""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{{PROPOSAL_TITLE}}</title>
  <style>
    {{THEME_CSS}}
    body { font-family: 'Segoe UI', sans-serif; background: var(--background); color: var(--text); margin: 0; padding: 2rem; }
    .proposal-header { background: var(--primary); color: #fff; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }
    section { margin-bottom: 2rem; padding: 1.5rem; background: var(--surface); border-radius: 6px; }
    h2 { color: var(--primary); border-bottom: 2px solid var(--accent); padding-bottom: .5rem; }
    @media print { body { padding: 0; } section { page-break-inside: avoid; } }
  </style>
</head>
<body class="{{STYLE_CLASS}}">
  <div class="proposal-header">
    <h1>{{PROPOSAL_TITLE}}</h1>
    <p>Prepared by: Meridian Advisory Group | Date: {{DATE}}</p>
  </div>
  <main>
    {{CONTENT}}
  </main>
</body>
</html>
""")

# ── Meeting notes ─────────────────────────────────────────────────────────────
# Target client: BrightWave Solutions (SMB)
today = date.today()
meeting_date = today - timedelta(days=3)

(workspace / "meeting-notes" / f"{meeting_date.strftime('%Y-%m-%d')}_brightwave-solutions.md").write_text(f"""\
# Meeting Notes — BrightWave Solutions
Date: {meeting_date.strftime('%B %d, %Y')}
Attendees: Sarah Chen (CEO, BrightWave), Tom Vickers (COO), Jamie Park (Meridian Lead)

## Summary
BrightWave Solutions is a 45-person B2B SaaS company experiencing rapid growth but struggling with
operational inefficiencies. They need strategic advisory to streamline their go-to-market execution
and build scalable internal processes.

## Pain Points Discussed
- Sales cycle too long (~90 days average), want to reduce to 45 days
- No structured onboarding process for enterprise clients
- Finance team lacks real-time visibility into revenue metrics
- Leadership team misaligned on Q3/Q4 priorities

## Scope Discussed
- Operational audit across sales, onboarding, and finance
- Weekly advisory touchpoints for 6 months
- Build a KPI tracking dashboard
- Facilitate two leadership alignment workshops

## Budget
Sarah indicated they're comfortable in the "$6,000–$7,000/month" range.
Decision by end of month.

## Decision Makers
Sarah Chen (final sign-off), Tom Vickers (ops approval)

## Next Steps
Meridian to send proposal by Friday.
""")

# Distractor meeting notes (other clients, older dates)
(workspace / "meeting-notes" / "2024-11-15_nexaflow-tech.md").write_text("""\
# Meeting Notes — NexaFlow Tech
Date: November 15, 2024
Quick call with NexaFlow regarding their data pipeline project.
Budget: $25,000 one-time. Scope: 3-month engagement.
Decision maker: CTO Priya Mehta.
""")

(workspace / "meeting-notes" / "archive" / "2024-09-02_vertexpeak.md").write_text("""\
# Meeting Notes — VertexPeak Corp
Archived. Engagement concluded October 2024.
Total contract: $48,000.
""")

(workspace / "meeting-notes" / "2025-01-10_internal-planning.md").write_text("""\
# Internal Planning Session
Team capacity review for Q1 2025. No client deliverables discussed.
""")

# ── MEMORY.md ─────────────────────────────────────────────────────────────────
(workspace / "MEMORY.md").write_text("""\
# Client Memory

## BrightWave Solutions
- First contact: Q4 2024 via LinkedIn outreach
- Industry: B2B SaaS
- Size: ~45 employees, Series A
- Previous engagements: None (new prospect)

## NexaFlow Tech
- Status: Proposal sent, awaiting response
- Contact: Priya Mehta, CTO

## VertexPeak Corp
- Status: Closed / Won (2024)
- Total billed: $48,000
""")

# ── CRM distractor files ───────────────────────────────────────────────────────
(workspace / "crm" / "leads" / "q1-2025-pipeline.csv").write_text("""\
company,stage,value,owner
BrightWave Solutions,Proposal,78000,Jamie Park
NexaFlow Tech,Negotiation,25000,Jamie Park
CloudNest Inc,Discovery,45000,Maria Santos
""")

(workspace / "crm" / "closed" / "2024-won-deals.csv").write_text("""\
company,close_date,value
VertexPeak Corp,2024-10-31,48000
ArcLight Media,2024-08-15,22000
""")

# ── Internal distractor files ──────────────────────────────────────────────────
(workspace / "internal" / "contracts" / "standard-msa-template.md").write_text("""\
# Master Services Agreement Template
[Boilerplate MSA — not for client distribution]
""")

(workspace / "internal" / "onboarding" / "new-client-checklist.md").write_text("""\
# New Client Onboarding Checklist
- [ ] Signed MSA
- [ ] Invoice sent
- [ ] Kick-off call scheduled
""")

(workspace / "client-files" / "brightwave" / "nda-signed-2025-01-08.pdf.stub").write_text("""\
[Binary PDF stub — NDA signed by BrightWave 2025-01-08]
""")

(workspace / "client-files" / "nexaflow" / "requirements-draft.md").write_text("""\
# NexaFlow — Project Requirements Draft
Data ingestion pipeline: Kafka → Spark → Snowflake
Timeline: 12 weeks
""")

print("Workspace generated successfully.")