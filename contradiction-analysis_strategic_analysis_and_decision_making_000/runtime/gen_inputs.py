import os
import json
import random

random.seed(42)

BASE = "/workspace"

# Create a deeply nested, realistic SaaS company workspace with distractor files
dirs = [
    "company/strategy/2024",
    "company/strategy/2023",
    "company/engineering/backend",
    "company/engineering/frontend",
    "company/engineering/infra",
    "company/product/roadmap",
    "company/product/feedback",
    "company/sales/q1",
    "company/sales/q2",
    "company/hr/recruiting",
    "company/finance/reports",
    "company/marketing/campaigns",
    "company/legal/contracts",
    "company/ops/incidents",
    "company/ops/monitoring",
    "skills",
    "skills/contradiction-analysis",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ---- DISTRACTOR FILES ----

# 1. Old strategy doc
with open(os.path.join(BASE, "company/strategy/2023/annual_goals.md"), "w") as f:
    f.write("""# 2023 Annual Goals
- Reach 500 paying customers
- Launch mobile app
- Reduce churn below 5%
- Hire 10 engineers
""")

# 2. Engineering OKRs
with open(os.path.join(BASE, "company/engineering/backend/okr_q4.md"), "w") as f:
    f.write("""# Backend OKR Q4
O1: Reduce p99 latency to <200ms
KR1: Refactor legacy auth service
KR2: Add database connection pooling
KR3: Migrate 3 services to async
""")

# 3. Frontend sprint notes
with open(os.path.join(BASE, "company/engineering/frontend/sprint_45_notes.txt"), "w") as f:
    f.write("""Sprint 45 Notes
- Blocked on API changes from backend
- Design system still not finalized
- 3 features from PM waiting for review
- Accessibility audit: 14 open issues
""")

# 4. Infrastructure incident log
with open(os.path.join(BASE, "company/ops/incidents/inc_2024_08_outage.md"), "w") as f:
    f.write("""# Incident Report: 2024-08 Major Outage
Duration: 4 hours
Root cause: DB connection pool exhaustion under high load
Impact: 73% of enterprise customers affected
Action items:
  - Add circuit breaker (owner: @wei, due: 2024-09-15)
  - Review capacity planning (owner: @ops, due: 2024-10-01)
  - Customer communication playbook (owner: @cs, due: 2024-09-30)
""")

# 5. Product feedback dump (messy)
with open(os.path.join(BASE, "company/product/feedback/customer_feedback_raw.txt"), "w") as f:
    f.write("""Customer: Acme Corp
"Your API is too slow. We had 3 outages last month caused by your service."

Customer: TechFlow Inc
"We love the product but the UI hasn't changed in 18 months. Competitors have better dashboards."

Customer: DataPipe Ltd
"The new features you shipped broke our existing workflows. Why no migration guide?"

Customer: StartupX
"Price increase announcement was a shock. No warning, no negotiation."

Customer: GlobalBank
"Your SOC2 compliance gap is blocking us from signing. We've been waiting 8 months."

Customer: NovaSoft
"Support tickets take 5 days to resolve. Unacceptable for enterprise tier."
""")

# 6. Sales pipeline
with open(os.path.join(BASE, "company/sales/q2/pipeline_summary.csv"), "w") as f:
    f.write("""deal_id,company,value,stage,blocker
D001,GlobalBank,500000,Security Review,SOC2 compliance not ready
D002,MegaCorp,200000,Negotiation,Price too high
D003,TechFlow,80000,Trial,Performance issues
D004,DataPipe,150000,Renewal Risk,Recent outage damage
D005,StartupX,30000,Churned,Price increase
""")

# 7. Engineering headcount freeze notice
with open(os.path.join(BASE, "company/hr/recruiting/hiring_freeze_notice.txt"), "w") as f:
    f.write("""INTERNAL NOTICE - CONFIDENTIAL
Effective 2024-09-01, all new engineering headcount requests are frozen
pending Q3 financial review. Existing open reqs: 4 backend engineers.
Exception process: VP Engineering approval required.
""")

# 8. Technical debt tracker
with open(os.path.join(BASE, "company/engineering/infra/tech_debt_tracker.json"), "w") as f:
    debt = {
        "items": [
            {"id": "TD-001", "description": "Monolith DB has no read replicas", "severity": "critical", "age_months": 14},
            {"id": "TD-002", "description": "Auth service using deprecated JWT library", "severity": "high", "age_months": 8},
            {"id": "TD-003", "description": "No automated integration tests for billing", "severity": "high", "age_months": 6},
            {"id": "TD-004", "description": "Hardcoded config in 12 services", "severity": "medium", "age_months": 20},
            {"id": "TD-005", "description": "No distributed tracing", "severity": "medium", "age_months": 10},
        ],
        "estimated_resolution_weeks": 32,
        "available_engineer_weeks": 8
    }
    json.dump(debt, f, indent=2)

# 9. PM roadmap
with open(os.path.join(BASE, "company/product/roadmap/q4_roadmap_draft.md"), "w") as f:
    f.write("""# Q4 2024 Roadmap (DRAFT)
## Must Ship (Customer Commitments)
- Advanced reporting dashboard (committed to GlobalBank, TechFlow)
- SSO / SAML integration (GlobalBank blocker)
- Bulk import API v2 (DataPipe request)

## Want to Ship
- Mobile app v1
- New onboarding flow
- AI-assisted query builder

## Engineering Requests (deprioritized by PM)
- DB sharding prep
- Test coverage to 80%
- Service mesh migration
""")

# 10. Finance warning
with open(os.path.join(BASE, "company/finance/reports/runway_alert.txt"), "w") as f:
    f.write("""CONFIDENTIAL - FINANCE ALERT
Current MRR: $420,000
Churn rate (last 90 days): 8.3% (above target of 5%)
Monthly burn: $680,000
Runway at current burn: 11 months
Required MRR to break even: $680,000

Note: If churn continues at this rate, runway drops to 7 months.
Enterprise pipeline at risk: ~$850,000 ARR (see sales pipeline)
""")

# 11. CEO message (sets urgency/context)
with open(os.path.join(BASE, "company/strategy/2024/ceo_all_hands_notes.txt"), "w") as f:
    f.write("""CEO All Hands - September 2024 Notes

"We are at a critical juncture. We have enough runway but not enough margin for error.
Engineering says they can't ship features because of tech debt and stability issues.
Product says we'll lose customers if we don't ship the roadmap.
Sales says we're losing deals because of missing compliance and features.
Customer success says churn is accelerating because of reliability problems.

I need a clear analysis of what our main problem is and how we should focus.
Everyone thinks their problem is the most urgent. We can't solve everything at once."

Key tensions surfaced:
1. Technical debt / reliability vs. feature velocity
2. Enterprise compliance requirements vs. current engineering capacity
3. Short-term revenue retention vs. long-term architectural health
4. Team morale (fatigue from firefighting) vs. business pressure to deliver
5. Engineering autonomy (wants to fix foundation) vs. PM control (wants feature delivery)
""")

# 12. Marketing campaigns (irrelevant distractor)
with open(os.path.join(BASE, "company/marketing/campaigns/q3_campaign_results.md"), "w") as f:
    f.write("""# Q3 Campaign Results
- LinkedIn ads: 2.3% CTR, 45 SQLs
- Content: 12 blog posts, 8,400 organic visits
- Webinar series: 3 events, 210 attendees
- G2 review push: +18 reviews, avg 4.2 stars
""")

# 13. Legal/compliance gap analysis
with open(os.path.join(BASE, "company/legal/contracts/soc2_gap_analysis_summary.txt"), "w") as f:
    f.write("""SOC2 Type II Gap Analysis Summary (Confidential)
Auditor: Shield Compliance Partners
Date: 2024-07-15

Gaps identified: 23
Critical gaps: 7 (access control, incident response, data encryption at rest)
Estimated remediation effort: 6-9 months with dedicated team
Current responsible owner: 1 part-time security engineer
Risk: Without SOC2, GlobalBank ($500K ARR) and 3 other enterprise prospects blocked.
""")

# ---- THE PROBLEM FILE: This is what the agent must analyze ----
# A brief from the CEO asking for a structured strategic analysis

with open(os.path.join(BASE, "company/strategy/2024/ceo_analysis_request.txt"), "w") as f:
    f.write("""STRATEGIC ANALYSIS REQUEST
From: CEO
To: Strategy Team
Date: 2024-09-10
Priority: URGENT

We need a rigorous structural analysis of our current situation. I have read about
contradiction analysis as a methodology and believe it is the right tool here.

Please use the contradiction analysis methodology from our skills library
(see: skills/contradiction-analysis/) to produce a formal analysis document.

The analysis must cover our FULL situation using all steps of the methodology.

The output should be saved as: contradiction_analysis.json

Context materials are available in company/ directory.
""")

# ---- SKILL.md placeholder reference ----
# The agent should look here for methodology
os.makedirs(os.path.join(BASE, "skills/contradiction-analysis"), exist_ok=True)
# NOTE: Per instructions, all scripts mentioned in SKILL.md already exist in workspace.
# The SKILL.md itself is the methodology guide - agent must read it from the skill context.
# We place a pointer file so agent knows where to look
with open(os.path.join(BASE, "skills/contradiction-analysis/README.md"), "w") as f:
    f.write("""# Contradiction Analysis Skill
This skill provides a structured 6-step methodology for analyzing complex problems
with multiple competing forces.

See the SKILL.md document provided in your context for the full methodology.
Follow ALL steps of the methodology to produce your analysis.
""")

print("Workspace generated successfully.")
print(f"Files created in {BASE}")