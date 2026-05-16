import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "docs",
    "references",
    "projects/cropbot/src",
    "projects/cropbot/tests",
    "projects/old-weatherapp/docs",
    "projects/old-weatherapp/src",
    "archive/2023-ideas",
    "archive/2022-ideas",
    "notes/competitors",
    "notes/market",
    "scripts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── references/manifest-checklist.md ─────────────────────────────────────────
(workspace / "references" / "manifest-checklist.md").write_text("""\
# Manifest Checklist — 9 Principles & 6 Red Flags

## The 9 Principles

1. **Privacy-first / offline-first**
   User data must not leave the device unless explicit consent. Default to local storage. No dark-pattern data collection.

2. **One pain → one feature → launch**
   The MVP addresses exactly one concrete pain point. No feature creep. Launch when the single pain is solved.

3. **AI as foundation, not feature**
   AI must be architectural (core loop, not a chatbot bolt-on). If you can remove the AI and the product still works the same way, it's a feature — not a foundation.

4. **Speed over perfection (MVP in days)**
   First working version ships in 1-3 days. If MVP takes >1 week, the architecture is wrong.

5. **Antifragile architecture**
   Systems should gain from disorder. Use edge functions, CDN, stateless services. No single points of failure.

6. **Money without overheating**
   Unit economics must be sustainable at realistic churn (30-40%/month for B2C SaaS). LTV:CAC > 2:1 at realistic scenario.

7. **Against exploitation**
   Product must not exploit user psychology (dark patterns, addiction loops, manufactured urgency). Must not exploit labor (underpaying gig workers, opaque algorithms).

8. **Subscription fatigue**
   Avoid adding yet another recurring subscription unless the product delivers clear, measurable recurring value. Preference: one-time purchase or usage-based pricing.

9. **Creators, not robots**
   Product must increase user agency and creativity. If it replaces human judgment entirely without transparency, it violates this principle.

---

## 6 Red Flags (instant KILL signals)

1. **Data moat mirage:** Requires massive proprietary data to function but has no clear data acquisition path.
2. **Regulatory minefield:** Operates in a space with active regulatory uncertainty (health claims, financial advice, children's data).
3. **Platform dependency:** Core function relies on a single third-party platform that can revoke access.
4. **Negative-sum market:** Success requires taking share from an entrenched, resource-rich incumbent with no differentiation path.
5. **Subscription on top of subscription:** Charges a new subscription for something users already pay for indirectly.
6. **Founder-market mismatch:** Founder has no credible connection to the target user's world; idea is purely theoretical.
""")

# ── references/stream-layers.md ──────────────────────────────────────────────
(workspace / "references" / "stream-layers.md").write_text("""\
# STREAM — 6-Layer Analysis Framework

Each layer is scored 1-10. Final score = weighted average where **Layer 4 (Stakes)** and **Layer 6 (Meta)** are weighted **1.5x**.

Formula:
  weighted_sum = L1 + L2 + L3 + (L4 × 1.5) + L5 + (L6 × 1.5)
  weighted_total_possible = 6 + 1.5 + 1.5 = ... i.e. sum of weights = 1+1+1+1.5+1+1.5 = 7
  final_score = weighted_sum / 7

---

## Layer 1 — Scope (Map ≠ Territory)

Questions:
- What assumptions is the founder treating as facts?
- Where does the "map" (business model) diverge from the "territory" (reality)?
- What are the explicit boundaries of the product? What does it NOT do?
- Simplicity test: can you explain the value prop in one sentence to a farmer?

Score high if: assumptions are few, boundaries are clear, value prop is simple.
Score low if: the model relies on multiple unvalidated assumptions stacked on each other.

---

## Layer 2 — Time (Entropy & Lindy)

Questions:
- Will this problem exist in 5 years? 10 years?
- Is the solution Lindy-compatible (has it survived similar attempts)?
- What is the entropy direction — does time make the problem worse or better?
- What technology trends accelerate or kill this?

Score high if: problem is ancient and worsening, solution is low-tech-dependency.
Score low if: problem may disappear due to platform changes, regulation, or free alternatives.

---

## Layer 3 — Route (Inversion & Second-Order Effects)

Questions:
- Inversion: how would you guarantee failure? (Use Devil's Advocate findings)
- What are the second-order effects of success? (If it works, what happens next?)
- What indirect consequences does the product have on users, market, society?
- What does the competitive response look like at 10k users? 100k users?

Score high if: failure modes are few and controllable, second-order effects are positive.
Score low if: success itself triggers a competitive response that destroys the advantage.

---

## Layer 4 — Stakes (Asymmetry & Antifragility)

Questions:
- What is the real downside if this fails? (Founder time, money, reputation)
- What is the asymmetric upside if it succeeds?
- Is the architecture antifragile — does it get better under stress?
- Pessimistic unit economics: if churn is 50%, is the business still alive?
- Can you run this as a side project at <$200/month until it proves itself?

Score high if: downside is capped, upside is large, can test with minimal burn.
Score low if: requires significant capital before validation, or downside is catastrophic.

---

## Layer 5 — Audience (Reputation & Network)

Questions:
- Who is the exact ICP (Ideal Customer Profile)? Age, role, daily workflow?
- Is this a deposit into or withdrawal from the founder's reputation?
- Does the product create network effects — does it get better with more users?
- Where do these users gather? (subreddits, Facebook groups, trade shows, forums)
- What does the user's current workaround look like? Why haven't they solved this already?

Score high if: ICP is specific and reachable, network effects exist, founder has credibility.
Score low if: ICP is vague ("anyone who farms"), no network effects, founder is an outsider.

---

## Layer 6 — Meta (Mortality & Balance)

Questions:
- Is this worth finite time on Earth? Would you be proud of building this?
- Does it align with the founder's 10-year mission?
- Manifest alignment: does it violate any of the 9 principles?
- Balance: does building this make the founder's life better or worse?
- What does the founder uniquely contribute that an LLM or outsourcer cannot?

Score high if: mission-aligned, manifest-compliant, founder has unique insight.
Score low if: manifest violations, founder is building it for money only, no unique angle.

NOTE: For every manifest principle violated (from Step 4), reduce Layer 6 score by 1 point.
NOTE: For every critical issue found in Devil's Advocate (Step 6), reduce the affected layer score by 1-2 points.
""")

# ── docs/research.md — the research file for the AgriTech idea ───────────────
(workspace / "docs" / "research.md").write_text("""\
# Research: SoilSense AI — Organic Farmer Soil Health Advisor

**Date:** 2024-11-15
**Analyst:** Internal Research Team

## Idea Summary
A web-based SaaS platform that allows small-scale organic farmers (<50 acres) to upload photos of their soil, crops, and field conditions. An AI model analyzes the images and generates personalized soil health recommendations, amendment schedules, and planting guides. Subscription: $29/month.

## Product Type
product_type: web

## Market Size
- ~2.1M small-scale farms in the US (<50 acres)
- ~15% identified as organic or transitioning to organic = ~315,000 TAM
- Willingness to pay: survey data (n=180) suggests 23% would pay $20-40/month for AI guidance
- Addressable paying market: ~72,000 farmers

## Pain Points (Quotes)
- "I spend $800/year on soil tests and still don't know what to do with the results." — r/organicfarming, 2024-09-03
- "The extension office takes 3 weeks to respond and gives generic advice." — AgriTalk forum, 2024-08-17
- "Bought CropX, too expensive for my 12 acres." — Facebook Organic Farmers group, 2024-10-01

## Competitors
| Name | Funding | Focus | Weakness |
|------|---------|-------|----------|
| CropX | $30M Series B | Enterprise, large farms | Min $5,000/year, no small farms |
| Farmers Business Network | $300M | Crop input aggregation | Not soil-health focused |
| Taranis | $50M | Visual crop scouting, enterprise | Drone-required, no photo upload |
| Granular (now Corteva) | Acquired $300M | Farm management ERP | Complexity overkill for small farms |
| SoilKit | Bootstrapped | Soil test kits + basic reports | Physical kit, 2-week turnaround |

## Technology Stack Considerations
- AI vision models (GPT-4o, Claude Vision, or fine-tuned ResNet) for image analysis
- Requires ongoing AI inference costs: ~$0.02-0.08 per analysis
- Regulatory: making specific soil amendment recommendations may touch agricultural advisory regulations in some states

## Unit Economics (Optimistic)
- Price: $29/month
- Monthly churn: 8%
- LTV: $29 / 0.08 = $362
- CAC (content marketing): $25
- LTV:CAC = 14.5:1

## Notes
- Seasonal demand: farmers most active March-September, heavy churn October-February
- Image quality from rural areas: variable (low-light, blurry, inconsistent angles)
- 67% of target users are 45-65 age group, lower tech adoption rate
- Similar product "AgriSnap" (UK-based) pivoted away from AI recommendations to human agronomist consultations in 2023 after AI accuracy complaints
""")

# ── Distractor files ──────────────────────────────────────────────────────────

# Old PRD for a different project
(workspace / "docs" / "prd-weatherapp.md").write_text("""\
# PRD: WeatherApp Pro

## Problem
Farmers need hyperlocal weather data. Generic weather apps show city-level data.

## Stack
nextjs-supabase

## KPIs
- DAU: 500 by week 4
- Churn: <15%/month

## Status: ARCHIVED — project killed 2023-11-01
""")

# Competitor notes
(workspace / "notes" / "competitors" / "cropx-analysis.md").write_text("""\
# CropX Competitive Analysis

CropX focuses on enterprise clients. Their soil sensor hardware costs $300/sensor.
Not a direct threat for <50 acre farms due to pricing.
Last funding: 2022.
""")

(workspace / "notes" / "competitors" / "fbn-analysis.md").write_text("""\
# Farmers Business Network (FBN)

Network effects in crop input pricing. Not AI-recommendation focused.
Revenue 2023: ~$150M estimated.
""")

# Market notes
(workspace / "notes" / "market" / "organic-farming-trends.md").write_text("""\
# Organic Farming Market Trends 2024

- CAGR of organic farming inputs: 8.4%
- USDA organic certification backlog: 18 months
- Key insight: transition farmers (year 1-3 organic) have highest uncertainty and highest advisory need
""")

# Archive ideas
(workspace / "archive" / "2023-ideas" / "drone-scouting.md").write_text("""\
# Idea: DroneScout for Small Farms

Killed 2023-07. Reasons:
1. FAA Part 107 certification barrier for users
2. Hardware cost ($800+ drone) too high for <50 acre farms
3. Taranis already doing this for enterprise

Score: KILL
""")

(workspace / "archive" / "2023-ideas" / "farm-erp.md").write_text("""\
# Idea: FarmFlow ERP

Killed 2023-11. Reasons:
1. Granular (Corteva) dominates with $300M+ invested
2. Integration complexity: too many data sources
3. No clear wedge for small farms

Score: KILL
""")

(workspace / "archive" / "2022-ideas" / "soil-test-marketplace.md").write_text("""\
# Idea: SoilMarket — Soil Test Aggregator

Status: PIVOTED
Notes: Pivot to connecting farmers with local agronomists. Stopped tracking after pivot.
""")

# Old cropbot project files
(workspace / "projects" / "cropbot" / "src" / "main.py").write_text("""\
# CropBot — Automated crop rotation advisor (DEPRECATED)
# This project was shelved. Do not use as reference.

def get_rotation_advice(crop_history):
    pass  # TODO: implement
""")

(workspace / "projects" / "cropbot" / "tests" / "test_main.py").write_text("""\
import pytest
# Tests for deprecated CropBot project
# All tests are commented out pending rewrite
""")

(workspace / "projects" / "old-weatherapp" / "docs" / "api-spec.md").write_text("""\
# WeatherApp API Spec (ARCHIVED)

GET /api/weather?lat={lat}&lon={lon}
Returns: temperature, precipitation, wind speed, 7-day forecast
""")

(workspace / "projects" / "old-weatherapp" / "src" / "app.js").write_text("""\
// WeatherApp frontend — ARCHIVED
// Built with Next.js 13
const WeatherDashboard = () => {
  return <div>Weather data goes here</div>;
};
""")

# Scripts
(workspace / "scripts" / "seed_db.sh").write_text("""\
#!/bin/bash
# Database seed script for development
psql $DATABASE_URL < seed.sql
""")

(workspace / "scripts" / "deploy.sh").write_text("""\
#!/bin/bash
# Deployment script
vercel --prod
""")

# A notes file that mentions the SoilSense idea name to establish context
(workspace / "notes" / "market" / "soilsense-brainstorm.md").write_text("""\
# SoilSense AI — Brainstorm Notes

Initial thoughts on the idea. NOT a formal validation.

Questions:
- Can we make AI recommendations legally defensible?
- Is image quality good enough from phone cameras?
- Who is our first 10 paying customers?

Status: needs formal go/kill analysis before any development starts.
""")

print("Workspace scaffold complete.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")