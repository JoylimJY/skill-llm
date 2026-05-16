import os
import random
from pathlib import Path

random.seed(42)

base = Path("/workspace")

# --- Directory structure ---
dirs = [
    "projects/cloudlens/context",
    "projects/cloudlens/drafts",
    "projects/cloudlens/reviews",
    "projects/cloudlens/assets",
    "projects/cloudlens/technical",
    "projects/internal/templates",
    "projects/internal/archive",
    "skills",
    "docs/patterns",
    "docs/old",
]
for d in dirs:
    (base / d).mkdir(parents=True, exist_ok=True)

# --- Core context file: product brief ---
(base / "projects/cloudlens/context/product-brief.md").write_text("""\
# CloudLens — Product Brief

**Product:** CloudLens  
**Category:** Cloud cost observability SaaS for engineering teams  
**Stage:** Pre-launch (private beta)  
**Target users:** Platform engineers and DevOps leads at mid-size companies (50–500 engineers)

## What CloudLens Does

CloudLens connects to AWS, GCP, and Azure cost APIs and surfaces per-team, per-service, per-commit cost attribution in a unified dashboard. Engineers see exactly which deployment caused a $4,000/month spike — no manual tagging, no spreadsheet archaeology.

## The Problem We're Solving

Cloud bills are black boxes. Finance sees one number. Engineering has no ownership. CloudLens adds cost attribution at the git-commit and team level, making cloud spend a first-class engineering concern.

## Pricing Model

CloudLens uses usage-based pricing: charged per "monitored resource-hour" with a free tier for up to 500 resource-hours/month. After that, tiered pricing kicks in. Enterprise plans are custom.

The pricing model is genuinely novel for this category — most tools are seat-based SaaS. We're usage-based like infrastructure providers (AWS, Stripe, Datadog).

## Current Pricing Page Status

Drafted but not launched. The pricing page currently shows:
- Three tiers (Free, Growth, Enterprise)
- A vague "resource-hour" metric that nobody outside our team understands
- No calculator, no estimator
- A single "Contact Sales" CTA for Enterprise
- No social proof, no case studies, no trust signals

## The Open Question

We're about to launch the pricing page publicly. The question: **how do the best usage-based SaaS tools communicate complex, unfamiliar pricing models in a way that builds trust and converts engineers?**

Specifically: how do we explain "resource-hours" without losing people, provide enough transparency to avoid the "hidden costs" objection, and handle the "I don't know what I'll pay" anxiety that usage-based pricing always creates?

This is a pre-ship review question. We need to know how the leading platforms in this space have solved it before we go live.

## Stakeholders

- **Priya** — CEO / decision-maker on pricing page
- **Dom** — Head of Growth, writing the pricing copy
- **Felix** — Lead engineer, worried the "resource-hour" metric is too abstract
""")

# --- Distractor: old marketing copy draft ---
(base / "projects/cloudlens/drafts/pricing-page-v1.md").write_text("""\
# Pricing Page Draft v1

## Hero
CloudLens — Know what your cloud actually costs.

## Tiers

### Free
- Up to 500 resource-hours/month
- 1 cloud provider
- Community support

### Growth — $0.003/resource-hour
- Unlimited resource-hours
- All cloud providers
- Slack alerts
- 14-day free trial

### Enterprise
- Custom pricing
- Dedicated support
- SSO + audit logs
- Contact Sales

## FAQ
Q: What is a resource-hour?
A: One resource-hour = one cloud resource (e.g., EC2 instance, RDS database) monitored for one hour.

Q: How do I estimate my bill?
A: We're working on a calculator. For now, email us.
""")

# --- Distractor: technical spec ---
(base / "projects/cloudlens/technical/resource-hour-spec.md").write_text("""\
# Resource-Hour Technical Specification

## Definition
A "resource-hour" is defined as: one distinct cloud resource object (identified by ARN, GCP resource ID, or Azure resource ID) that has been sampled at least once in a 60-minute window.

## Counting Rules
- Resources are counted per calendar hour (UTC)
- Spot instances and preemptible VMs count the same as on-demand
- Idle resources (zero usage) still count if they exist
- Kubernetes pods: each pod = 1 resource-hour (not the node)
- Lambdas: counted per function, not per invocation

## Billing Boundary
Billing is calculated daily, invoiced monthly.
""")

# --- Distractor: unrelated archived research ---
(base / "projects/internal/archive/old-competitor-notes.md").write_text("""\
# Old Notes — Competitor Scan (2024-Q1)

These are rough notes from a quick scan, NOT structured research. Do not use for positioning decisions.

- Apptio: enterprise, focuses on TBM framework, not engineering-facing
- CloudHealth: acquired by VMware, enterprise sales-heavy
- Spot.io: optimization-focused, not attribution
- Infracost: open-source, dev tooling angle, VSCode plugin

None of these are real analogues. They're either enterprise-sales or optimization tools.
These notes predate the usage-based pricing decision.
""")

# --- Distractor: internal template (wrong format, not the skill output format) ---
(base / "projects/internal/templates/basic-research-template.md").write_text("""\
# Research Template (Generic)

## Background
## Findings
## Conclusions
## Next Steps
""")

# --- Distractor: unrelated pattern doc ---
(base / "docs/patterns/technical-accuracy-review.md").write_text("""\
# Technical Accuracy Review Pattern

Use this when verifying factual claims: fee amounts, protocol specs, hash functions.

NOT for strategic or UX research. See the competitive positioning research skill for that.

## Steps
1. Identify the claim
2. Find the primary source
3. Cross-reference with a second source
4. Flag any discrepancies
""")

# --- Distractor: old positioning doc ---
(base / "docs/old/positioning-notes-2024.md").write_text("""\
# Positioning Notes (2024, outdated)

We initially positioned CloudLens as "cost optimization" but pivoted to "cost attribution."

Optimization implies we save you money directly. Attribution means we give you visibility so YOUR team can make decisions. Much stronger value prop for engineering leads.

The "for engineers, not finance" angle tested well in 5 customer interviews.
""")

# --- Distractor: a completely unrelated project ---
(base / "projects/internal/archive/q3-okrs.md").write_text("""\
# Q3 OKRs

**O1:** Reach 50 design partner customers
- KR1: 20 design partners signed by July 31
- KR2: 80% retention at 90 days
- KR3: 3 publishable case studies

**O2:** Launch pricing page
- KR1: Pricing page live by Aug 15
- KR2: < 5% bounce on pricing page (Google Analytics)
""")

# --- Distractor: assets placeholder ---
(base / "projects/cloudlens/assets/brand-colors.txt").write_text("""\
Primary: #1A1A2E
Accent: #E94560
Background: #F5F5F5
""")

# --- Distractor: another unrelated skill description ---
(base / "skills/technical-accuracy-review.md").write_text("""\
# Skill: Technical Accuracy Review

Use when verifying fee amounts, protocol specs, cryptographic claims.

NOT this skill for strategic research.
""")

# --- Distractor: a partial, wrong-format research attempt ---
(base / "projects/cloudlens/drafts/pricing-research-scratch.md").write_text("""\
# Scratch notes — pricing page research

Datadog: complicated pricing, lots of complaints online about surprise bills
Stripe: clear pricing page, lots of docs
AWS pricing: famously confusing

TODO: actually structure this properly
""")

# --- Distractor: empty reviews directory marker ---
(base / "projects/cloudlens/reviews/.gitkeep").write_text("")

print("Workspace generated successfully.")
print("\nDirectory structure:")
for p in sorted(base.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(base)}")