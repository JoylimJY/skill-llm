import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ─── Create realistic directory structure ───────────────────────────────────

dirs = [
    "company_docs/hr",
    "company_docs/finance",
    "company_docs/operations",
    "company_docs/sales",
    "company_docs/legal",
    "company_docs/marketing",
    "company_docs/it",
    "internal/meeting_notes",
    "internal/email_threads",
    "internal/org_charts",
    "reports/q1",
    "reports/q2",
    "old_plans",
    "templates",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ─── Messy company context files ─────────────────────────────────────────────

# 1. Org chart (messy, partial)
with open(os.path.join(workspace, "internal/org_charts/vetpaw_org_2024.txt"), "w") as f:
    f.write("""VetPaw Clinics — Org Structure (as of March 2024)
=======================================================
CEO: Sandra Okafor
  |
  +-- Operations Director: Marcus Lim
  |     - Appointment scheduling team (3 staff)
  |     - Inventory/supply ordering (2 staff)
  |     - Facility management (1 staff)
  |
  +-- Finance Manager: Priya Nair
  |     - Billing & invoicing (2 staff)
  |     - Payroll processing (1 staff, outsourced partially)
  |     - Compliance reporting (shared with legal)
  |
  +-- Head of Client Services: Tomas Ruiz
  |     - Front desk / reception (4 staff across 3 clinics)
  |     - Client follow-up calls (2 staff)
  |     - Complaints handling (1 staff)
  |
  +-- Sales & Growth: Vacant (role being redefined)
  |     - Corporate partnerships (handled ad hoc by CEO)
  |     - Referral program management (no dedicated owner)
  |
  +-- Legal & Compliance: External counsel (Bradshaw LLP)
  |     - Regulatory filings (quarterly)
  |     - Staff contracts review
  |
  +-- HR Manager: Denise Cho
  |     - Recruitment (ongoing - 2 open roles)
  |     - Onboarding (paper-based process)
  |     - Performance reviews (annual, manual)
  |
  +-- Marketing: Freelance (contracted per campaign)
        - Social media posts (monthly)
        - Email newsletters (ad hoc)

NOTE: IT support is contracted out to TechVet Solutions.
      No internal IT staff.
""")

# 2. Email thread — CEO describing pain points
with open(os.path.join(workspace, "internal/email_threads/ceo_bottleneck_thread.txt"), "w") as f:
    f.write("""From: Sandra Okafor <s.okafor@vetpaw.com>
To: Marcus Lim <m.lim@vetpaw.com>
Date: 2024-04-02 09:14
Subject: RE: RE: RE: Staff overload

Marcus,

For the third time this quarter, invoices went out late because Priya's team
is drowning. We're also missing follow-up calls to clients after procedures —
Tomas says his team just doesn't have capacity. I'm spending 6 hours a week
on corporate outreach personally because Sales is still a ghost department.

Denise is doing onboarding manually with printed packets. Every new hire gets
a different experience. It's a mess.

Legal said our Q2 compliance report nearly missed deadline again. Bradshaw
charges us $400/hr and they're waiting on US to send them the right data.

I want to explore AI/agents to fix some of this. But I don't want to touch
client-facing trust stuff or anything where we could get into legal trouble if
something goes wrong.

What functions do you think we should tackle and in what order?

— Sandra

---
From: Marcus Lim
To: Sandra Okafor
Date: 2024-04-01 17:43

Sandra, I agree. Scheduling alone eats 20% of front desk time. We keep
double-booking or missing reminders. Supply ordering is another one — we
re-order based on gut feel, not data.

I think we should fix internal stuff first before we go near clients.

—M
""")

# 3. Meeting notes — strategy session
with open(os.path.join(workspace, "internal/meeting_notes/ai_strategy_session_apr2024.txt"), "w") as f:
    f.write("""VetPaw AI Strategy Session — April 5, 2024
Attendees: Sandra, Marcus, Priya, Tomas, Denise
Facilitator: External consultant (note-taker: Denise)

DISCUSSION POINTS:
------------------
Q: What does VetPaw deliver to clients?
A: Premium veterinary care across 3 clinics + in-home visit services.
   Core value = trusted, personalized care for pets. Clients choose us
   because we KNOW their animals and they trust our vets personally.

Q: Where does work pile up?
- Appointment scheduling (manual, error-prone)
- Invoice generation and follow-up (late every month)
- HR onboarding (inconsistent, paper-based)
- Client follow-up after procedures (missed 30% of calls last month)
- Compliance data collection for legal (scramble every quarter)
- Referral/partnership outreach (no one owns it)
- Social media and newsletter (ad hoc freelancer, no consistency)
- Inventory/supply reordering (gut feel, not system-driven)

Q: What does Sandra want to keep doing herself?
A: Strategic partnerships, investor relations, key hiring decisions.

RED LINE from CEO: "Do NOT automate anything where a client relationship
could be damaged if AI gets it wrong. Do not let AI make compliance decisions
— that's Bradshaw's job, not a bot's."

CONSENSUS ORDER (rough, to be formalized):
- Fix internal pain first
- Then client communication layer
- Growth/sales last — not ready yet

ACTION: Someone needs to produce a formal automation plan document.
""")

# 4. Finance notes
with open(os.path.join(workspace, "company_docs/finance/billing_process_notes.txt"), "w") as f:
    f.write("""Billing & Invoicing Process — Current State
============================================
- Invoices generated manually from vet notes (handwritten or dictated)
- Staff enter line items into QuickBooks manually
- Follow-up on unpaid invoices: phone call from Priya's team after 30 days
- Average delay from appointment to invoice: 3-4 days
- Missed follow-ups: estimated 15% of overdue invoices never chased

This is a HIGH VOLUME, RULE-BASED process. Strong candidate for automation.
Standard billing rules apply (no unusual business logic).
""")

# 5. HR notes
with open(os.path.join(workspace, "company_docs/hr/onboarding_audit.txt"), "w") as f:
    f.write("""HR Onboarding Audit — March 2024
=================================
Current process:
1. Denise emails welcome packet (Word doc) to new hire
2. New hire prints, signs, scans, emails back
3. IT sets up accounts (2-3 day lag from TechVet)
4. First-week schedule built manually by Denise

Issues:
- 4 different versions of the welcome packet in circulation
- No tracking of which step each new hire is at
- Compliance forms (HIPAA for vet records) sometimes missed entirely

This is a structured process with clear steps — automatable but
needs company-specific onboarding rules (vet credential verification,
HIPAA form requirement).
""")

# 6. Legal/compliance notes
with open(os.path.join(workspace, "company_docs/legal/compliance_filing_notes.txt"), "w") as f:
    f.write("""Quarterly Compliance Filing — Notes
====================================
Required by state veterinary board:
- Drug inventory reconciliation report
- Controlled substance log summary
- Staff license verification status

Current process:
- Marcus collects data from 3 clinics manually
- Priya formats into spreadsheet
- Sent to Bradshaw LLP who review and file

Risk: If data is wrong, Bradshaw catches it — but at $400/hr.
CEO is explicit: AI cannot MAKE compliance decisions.
AI can HELP collect and format data for lawyer review.
""")

# 7. Sales/growth notes
with open(os.path.join(workspace, "company_docs/sales/partnership_outreach_notes.txt"), "w") as f:
    f.write("""Corporate Partnerships & Referral Program
==========================================
Current state: CEO handles personally (6 hrs/week)
Targets: pet insurance companies, dog groomers, pet stores, breeders

Referral program: exists on paper, no one tracks it or follows up.

Note: These are RELATIONSHIP-DRIVEN conversations. Closing a partnership
requires Sandra or a senior person — trust is core to the deal.
The prep work (research, outreach drafts, follow-up scheduling) could
potentially be supported by an agent.
""")

# 8. Marketing notes
with open(os.path.join(workspace, "company_docs/marketing/marketing_overview.txt"), "w") as f:
    f.write("""Marketing Overview — VetPaw
===========================
Current: Freelance contractor, Maria Chen
Deliverables: 4 social posts/month, 1 newsletter/quarter

Pain: Inconsistent tone, misses clinic-specific events, no analytics.
Maria is not embedded — gets a brief and disappears for 2 weeks.

Standard marketing automation tools exist for social scheduling,
email newsletters. No unique business logic needed beyond brand voice.
""")

# 9. Operations / scheduling notes
with open(os.path.join(workspace, "company_docs/operations/scheduling_pain_points.txt"), "w") as f:
    f.write("""Appointment Scheduling — Pain Points
=====================================
- 3 clinics, different vet availability, shared system
- Reminder calls done manually (1 FTE equivalent per week)
- Double-bookings happen ~2x per month
- No automated waitlist management

Standard scheduling problem. Existing scheduling tools/agents exist.
Internal/operational function — low client-facing risk if done right.
""")

# 10. Distractor: old abandoned plan
with open(os.path.join(workspace, "old_plans/2022_tech_roadmap_ABANDONED.txt"), "w") as f:
    f.write("""2022 Tech Roadmap — ABANDONED
Do not use. This was based on old vendor quotes.
We evaluated Salesforce, ServiceNow, and a custom portal.
None were approved due to budget. Starting fresh in 2024.
""")

# 11. Distractor: random IT ticket log
with open(os.path.join(workspace, "company_docs/it/techvet_support_log.txt"), "w") as f:
    f.write("""TechVet Solutions — Support Tickets Q1 2024
============================================
#2041 - Clinic 2 printer offline (resolved)
#2042 - Password reset for Priya Nair (resolved)
#2043 - QuickBooks license renewal (pending)
#2044 - Email server migration planning (in progress)
""")

# 12. Distractor: Q1 financial report
with open(os.path.join(workspace, "reports/q1/q1_2024_summary.txt"), "w") as f:
    f.write("""Q1 2024 Financial Summary (DRAFT)
Revenue: $1.24M across 3 clinics
Expenses: $980K (staff: $620K, rent: $180K, supplies: $120K, other: $60K)
Net: $260K
Outstanding invoices: $87K (overdue >30 days: $34K)
""")

# 13. Distractor: Q2 placeholder
with open(os.path.join(workspace, "reports/q2/q2_placeholder.txt"), "w") as f:
    f.write("Q2 report not yet generated.\n")

# 14. Template folder — empty template stubs (not useful to agent)
with open(os.path.join(workspace, "templates/invoice_template_v3.txt"), "w") as f:
    f.write("Invoice template placeholder. Do not use without approval.\n")

with open(os.path.join(workspace, "templates/onboarding_checklist_OLD.txt"), "w") as f:
    f.write("Old onboarding checklist — superseded. See HR for current version.\n")

# 15. The SKILL.md is placed in workspace root (as it would be in real agent environment)
skill_md_content = """---
name: "Company"
description: "Build an agent-powered organization by mapping functions to skills and iterating on structure."
---

## Triggers

Activate on: "automate my company", "agents for my business", "replace team with AI", "company structure with agents", "which skills do I need".

**Different from:** `startup` (methodology) and `business` (strategy). This is about building the organization itself.

## Core Flow

1. **Discovery** — What does the company do? What functions exist?
2. **Mapping** — Each function → existing skill, custom skill, or hybrid
3. **Sequence** — Quick wins first, customer-facing later
4. **Iteration** — Run → review → adjust → expand

## Discovery Questions

Ask before recommending anything:
- What's the core value you deliver to customers?
- What functions exist today? (sales, support, ops, finance, marketing, legal, HR)
- Where does work pile up? What's the bottleneck?
- What do you actually want to do yourself?

## Function Mapping

For each function, determine approach:

| Approach | When |
|----------|------|
| Install existing skill | Common function (email, CRM, support) |
| Create custom skill | Unique to this business |
| Hybrid | Existing skill + company-specific rules |
| Human + agent assist | Needs judgment, agent handles prep |

See `functions.md` for common mappings.

## Building Sequence

Build in order of impact, not org chart:
1. **Internal ops** — Low risk, clear inputs/outputs
2. **Support** — After internal proves reliable
3. **Sales** — After support is stable
4. **Strategy** — Agents assist, humans decide

See `patterns.md` for organizational structures.

## Iteration Protocol

After each function is delegated:
1. Run 1-2 weeks with human oversight
2. Review: what did the agent miss?
3. Adjust scope based on errors
4. Reduce oversight only when stable

**Never hand off completely on day one.**

See `iteration.md` for tracking template.

## Learning System

As the company evolves, capture:
- Decisions made and why
- Adjustments to agent scope
- What worked vs what failed
- New skills needed

This becomes the company's operational memory.

## Red Flags

Stop and reassess:
- Automating trust-building → agents assist, humans close
- Delegating legal/compliance decisions → agents draft, lawyers approve
- No clear function boundaries → define before automating
- Expecting 100% automation immediately → set realistic timeline
"""

with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md_content)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")