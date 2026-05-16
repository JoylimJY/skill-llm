#!/usr/bin/env python3
"""
Generate a realistic, messy SEO project memory workspace for PureRoot Botanicals.
The workspace simulates 6+ months of accumulated SEO work with various issues:
1. hot-cache.md is bloated (>80 lines)
2. Several WARM files are >90 days old (need archiving to COLD)
3. Several files are >30 days old (HOT items need demotion to WARM)
4. Some files missing required frontmatter fields
5. One WARM file qualifies for promotion (referenced by 2 skills within 7 days)
"""

import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

BASE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "memory",
    "memory/archive",
    "memory/entities",
    "memory/research/keywords",
    "memory/research/competitors",
    "memory/research/serp",
    "memory/research/content-gaps",
    "memory/content/briefs",
    "memory/content/calendar",
    "memory/content/published",
    "memory/audits/content",
    "memory/audits/domain",
    "memory/audits/technical",
    "memory/audits/internal-linking",
    "memory/monitoring/alerts",
    "memory/monitoring/rank-history",
    "memory/monitoring/reports",
    "memory/monitoring/snapshots",
]

for d in dirs:
    (BASE / d).mkdir(parents=True, exist_ok=True)

today = datetime.today()

def date_str(days_ago: int) -> str:
    return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")

def set_mtime(path: Path, days_ago: int):
    """Set file modification time to simulate staleness."""
    import time
    target = today - timedelta(days=days_ago)
    ts = target.timestamp()
    os.utime(path, (ts, ts))

# ── CLAUDE.md / hot-cache.md (bloated: 95 lines) ─────────────────────────────
hot_cache_content = f"""# PureRoot Botanicals – SEO Hot Cache
Last Updated: {date_str(2)}

## Project Overview
- Domain: pureroot-botanicals.com
- Industry: Organic Skincare E-Commerce
- Primary Market: US, UK, AU
- Campaign Start: {date_str(210)}

## Hero Keywords (Priority 1)
| Keyword | Current Rank | Target | Status |
|---------|-------------|--------|--------|
| organic face serum | 14 | top 5 | active |
| natural skincare routine | 22 | top 10 | active |
| best organic moisturizer | 31 | top 15 | active |
| clean beauty products | 8 | top 5 | active |
| vegan face cream | 19 | top 10 | active |

## Secondary Keywords (Priority 2)
| Keyword | Current Rank | Target | Status |
|---------|-------------|--------|--------|
| rosehip oil benefits | 45 | top 20 | active |
| hyaluronic acid serum organic | 33 | top 15 | active |
| cruelty free moisturizer | 27 | top 10 | active |
| niacinamide natural | 51 | top 25 | active |
| retinol alternative natural | 38 | top 20 | active |

## Opportunity Keywords (Priority 3)
| Keyword | Current Rank | Target | Status |
|---------|-------------|--------|--------|
| bakuchiol cream | 67 | top 30 | monitoring |
| sea buckthorn oil | 82 | top 40 | monitoring |
| plant based skincare | 44 | top 20 | monitoring |

## Primary Competitors
| Domain | DA | Position |
|--------|----|----------|
| beautycounter.com | 72 | dominant |
| tatcha.com | 68 | strong |
| herbivore-botanicals.com | 61 | growing |
| innisfree.com | 59 | niche |

## Current Priorities
1. Fix Core Web Vitals – LCP >4.2s on mobile (blocker since {date_str(45)})
2. Publish 3 pillar content pieces for hero KW cluster
3. Build 15 new backlinks in natural health niche
4. Fix 47 broken internal links identified in audit

## Active Campaigns
| Campaign | Status | Expected Completion |
|----------|--------|---------------------|
| Q2 Content Sprint | 65% | {date_str(-14)} |
| Link Building Outreach | 40% | {date_str(-30)} |
| Technical SEO Fixes | 30% | {date_str(-7)} |

## Key Metrics Snapshot ({date_str(7)})
| Metric | Current | Previous | Delta |
|--------|---------|----------|-------|
| Organic Sessions | 12,400 | 11,200 | +10.7% |
| Avg Position | 24.3 | 26.1 | +1.8 |
| CTR | 3.2% | 2.9% | +0.3% |
| Indexed Pages | 847 | 801 | +46 |
| Domain Rating | 38 | 36 | +2 |

## Q1 2024 Archive Reference
Full data: memory/monitoring/reports/2024-Q1-report.md
- Organic sessions grew 34% YoY
- Launched hero keyword cluster content strategy
- Identified Core Web Vitals as primary technical blocker

## Q2 2024 Historical Data
Full report: memory/monitoring/reports/2024-Q2-report.md
- 12 new content pieces published
- Average position improved from 28.1 to 24.3
- DA improved from 33 to 38 through link building

## Old Alerts (Archived Context)
- {date_str(95)}: DR drop alert for herbivore-botanicals.com (resolved)
- {date_str(112)}: Manual penalty flag for innisfree.com US subfolder (resolved)
- {date_str(87)}: Algorithm update impact – lost 3 hero KW positions (recovered)

## Stale Competitor Notes
beautycounter.com published new sustainability report – check for content angle
tatcha.com restructured their ingredient stories pages
(Added {date_str(102)})

## Resolved Blockers (no longer active)
- SSL mixed content warnings – FIXED {date_str(91)}
- Duplicate meta descriptions – FIXED {date_str(98)}
- XML sitemap errors – FIXED {date_str(105)}

## Notes from Last Session
Quick wins: update FAQ schema on /ingredients page; add breadcrumbs to blog
"""

(BASE / "memory" / "hot-cache.md").write_text(hot_cache_content)
set_mtime(BASE / "memory" / "hot-cache.md", 2)

# ── memory/decisions.md ──────────────────────────────────────────────────────
decisions = f"""---
name: strategic-decisions
description: Major strategic choices for PureRoot Botanicals SEO campaign
type: decisions
---
# Strategic Decisions

## {date_str(15)}
- Decided to focus hero content on "organic face serum" cluster first
- Rationale: highest commercial intent, competitor gap identified

## {date_str(45)}
- Chose Herbivore Botanicals as primary content benchmark competitor
- Rationale: similar DA, overlapping keyword set, strong content quality

## {date_str(95)}
- Paused paid amplification budget – organic only strategy
- Rationale: ROI analysis showed organic 3x better CPL
"""
(BASE / "memory" / "decisions.md").write_text(decisions)
set_mtime(BASE / "memory" / "decisions.md", 15)

# ── memory/open-loops.md ────────────────────────────────────────────────────
open_loops = f"""---
name: open-loops
description: Unresolved blockers and follow-ups
type: open-loops
---
# Open Loops

## Critical
- [ ] Core Web Vitals LCP fix – assigned to dev team – overdue since {date_str(45)}
- [ ] Backlink audit for tatcha.com – need to find gap opportunities

## Pending
- [ ] Add FAQ schema to /ingredients – quick win from last session
- [ ] Review herbivore content structure for pillar page model
- [ ] Confirm content calendar approval for Q3

## Monitoring
- [ ] Track innisfree US subfolder recovery (was penalized)
"""
(BASE / "memory" / "open-loops.md").write_text(open_loops)
set_mtime(BASE / "memory" / "open-loops.md", 3)

# ── memory/glossary.md ───────────────────────────────────────────────────────
glossary = f"""---
name: project-glossary
description: PureRoot Botanicals SEO terminology and abbreviations
type: glossary
---
# Project Glossary

- **Hero KWs**: Priority 1 keywords — highest volume + commercial intent
- **DR**: Domain Rating (Ahrefs metric, 0-100)
- **DA**: Domain Authority (Moz metric, 0-100)
- **CWV**: Core Web Vitals
- **LCP**: Largest Contentful Paint (key CWV metric)
- **Pillar**: Long-form topic authority page (2000+ words)
- **Cluster**: Group of semantically related keywords targeting a pillar
- **Clean Beauty**: Industry term for non-toxic, transparent ingredient products
- **SERP Feature**: Google rich result (featured snippet, PAA, etc.)
"""
(BASE / "memory" / "glossary.md").write_text(glossary)
set_mtime(BASE / "memory" / "glossary.md", 5)

# ── WARM files that are >90 days old → should be archived to COLD ──────────

# 1. memory/research/keywords/hero-keywords-initial.md (95 days old)
hero_kw_initial = f"""---
name: hero-keywords-initial
description: Initial hero keyword research from campaign launch
type: keyword-research
---
# Hero Keywords – Initial Research
Date: {date_str(95)}

Identified from seed research:
- organic face serum (vol: 12,000/mo)
- natural skincare routine (vol: 22,000/mo)
- best organic moisturizer (vol: 8,500/mo)

Status: Superseded by updated keyword analysis.
"""
(BASE / "memory" / "research" / "keywords" / "hero-keywords-initial.md").write_text(hero_kw_initial)
set_mtime(BASE / "memory" / "research" / "keywords" / "hero-keywords-initial.md", 95)

# 2. memory/research/competitors/innisfree-analysis-old.md (110 days old)
innisfree_old = f"""---
name: innisfree-analysis-old
description: Initial competitor analysis for innisfree.com
type: competitor-analysis
---
# Innisfree.com – Initial Analysis
Date: {date_str(110)}

DR: 59 | Organic Traffic: ~280K/mo
Strong in: Korean beauty keywords, ingredient-led content
Weakness: Poor Core Web Vitals on mobile

Note: US subfolder showed manual penalty signs – to monitor.
Status: Superseded by more recent analysis.
"""
(BASE / "memory" / "research" / "competitors" / "innisfree-analysis-old.md").write_text(innisfree_old)
set_mtime(BASE / "memory" / "research" / "competitors" / "innisfree-analysis-old.md", 110)

# 3. memory/audits/technical/corewebvitals-audit-q1.md (100 days old)
cwv_audit = f"""---
name: corewebvitals-audit-q1
description: Q1 Core Web Vitals audit findings
type: technical-audit
---
# Core Web Vitals Audit – Q1
Date: {date_str(100)}

LCP: 4.8s (mobile) – FAIL
FID: 89ms – PASS
CLS: 0.18 – NEEDS IMPROVEMENT

Primary blocker: unoptimized hero images on homepage.
Action: Compress images, implement lazy loading.
Status: Partially resolved, LCP now 4.2s (still failing).
"""
(BASE / "memory" / "audits" / "technical" / "corewebvitals-audit-q1.md").write_text(cwv_audit)
set_mtime(BASE / "memory" / "audits" / "technical" / "corewebvitals-audit-q1.md", 100)

# 4. memory/monitoring/alerts/algorithm-update-mar.md (92 days old)
algo_alert = f"""---
name: algorithm-update-mar
description: March algorithm update impact alert
type: alert
---
# Algorithm Update Alert – March
Date: {date_str(92)}

Observed: 3 hero keyword position drops (organic face serum: 11→14, clean beauty products: 5→8)
Analysis: Likely EEAT-related – competitors with stronger author bios gained.
Action Taken: Added author bio pages, updated About Us with credentials.
Status: Positions partially recovered. Monitoring ongoing.
"""
(BASE / "memory" / "monitoring" / "alerts" / "algorithm-update-mar.md").write_text(algo_alert)
set_mtime(BASE / "memory" / "monitoring" / "alerts" / "algorithm-update-mar.md", 92)

# ── WARM file that qualifies for PROMOTION (2 skill refs in 7 days) ──────────
# memory/research/keywords/bakuchiol-opportunity.md
# Contains references showing it was cited by keyword-research and rank-tracker within 7 days
bakuchiol_opportunity = f"""---
name: bakuchiol-opportunity
description: Emerging keyword opportunity for bakuchiol – retinol alternative cluster
type: keyword-research
skill-references:
  - skill: keyword-research
    date: {date_str(3)}
  - skill: rank-tracker
    date: {date_str(5)}
---
# Bakuchiol Opportunity Analysis
Date: {date_str(5)}

## Key Finding
Bakuchiol as retinol alternative is trending +340% YoY search growth.
PureRoot has existing product: Pure Bakuchiol Night Serum.

## Keyword Cluster
- bakuchiol cream: vol 8,100/mo, KD 28, current rank: 67
- bakuchiol vs retinol: vol 14,400/mo, KD 35, not ranking
- plant based retinol: vol 5,400/mo, KD 22, not ranking
- bakuchiol serum: vol 6,700/mo, KD 31, current rank: 89

## Opportunity Score: HIGH
- Low competition window (6-9 months before saturation)
- Direct product alignment
- Featured snippet opportunity on "bakuchiol vs retinol"

## Recommended Actions
1. Create pillar content: "Complete Guide to Bakuchiol: The Natural Retinol Alternative"
2. Optimize existing product page for bakuchiol cluster
3. Target featured snippet with structured comparison content
"""
(BASE / "memory" / "research" / "keywords" / "bakuchiol-opportunity.md").write_text(bakuchiol_opportunity)
set_mtime(BASE / "memory" / "research" / "keywords" / "bakuchiol-opportunity.md", 5)

# ── Files with MISSING frontmatter fields ────────────────────────────────────

# 1. memory/research/serp/hero-serp-snapshot.md – missing 'type'
serp_snap = f"""---
name: hero-serp-snapshot
description: SERP snapshot for hero keyword cluster
---
# Hero SERP Snapshot
Date: {date_str(20)}

## organic face serum
- Position 1: tatcha.com/rose-gold-serum
- Position 2: beautycounter.com/counter-+ serum
- Featured Snippet: none currently
- PAA present: yes (4 questions)

## natural skincare routine
- Position 1: healthline.com/skin-care-routine
- Position 2: byrdie.com/natural-skincare-routine
- Featured Snippet: healthline.com (paragraph)
"""
(BASE / "memory" / "research" / "serp" / "hero-serp-snapshot.md").write_text(serp_snap)
set_mtime(BASE / "memory" / "research" / "serp" / "hero-serp-snapshot.md", 20)

# 2. memory/content/briefs/organic-serum-pillar-brief.md – missing 'name'
content_brief = f"""---
description: Content brief for organic face serum pillar page
type: content-brief
---
# Organic Face Serum – Pillar Content Brief
Date: {date_str(12)}

## Target Keywords
Primary: organic face serum
Secondary: best organic serum, natural face serum, organic serum for dry skin

## Target Length: 3,000-3,500 words
## Target Angle: Complete Guide + Product Showcase
## SERP Intent: Informational + Commercial

## Required Sections
1. What makes a face serum "organic"?
2. Key ingredients to look for
3. Skin type matching guide
4. Application technique
5. PureRoot product showcase
6. FAQ (schema markup)
"""
(BASE / "memory" / "content" / "briefs" / "organic-serum-pillar-brief.md").write_text(content_brief)
set_mtime(BASE / "memory" / "content" / "briefs" / "organic-serum-pillar-brief.md", 12)

# 3. memory/audits/domain/da-audit-current.md – missing 'description'
da_audit = f"""---
name: da-audit-current
type: domain-audit
---
# Domain Authority Audit
Date: {date_str(8)}

## PureRoot Botanicals
DR (Ahrefs): 38 | DA (Moz): 34
Referring Domains: 187 | Dofollow: 142

## Link Velocity
+12 new RDs in last 30 days (healthy growth signal)

## Top Link Sources
- wellbeing-magazine.co.uk (DR 52)
- organiclifestyle.com (DR 47)
- greenbeautyreviews.net (DR 41)

## Gaps vs beautycounter.com (DR 72)
Need ~150 more quality RDs to be competitive in hero KW SERPs.
"""
(BASE / "memory" / "audits" / "domain" / "da-audit-current.md").write_text(da_audit)
set_mtime(BASE / "memory" / "audits" / "domain" / "da-audit-current.md", 8)

# ── Additional distractor files (valid, well-formed, recent) ─────────────────

# memory/research/keywords/secondary-keywords-current.md
secondary_kw = f"""---
name: secondary-keywords-current
description: Current secondary keyword tracking for PureRoot
type: keyword-research
---
# Secondary Keywords – Current Tracking
Date: {date_str(10)}

| Keyword | Volume | KD | Rank | Delta |
|---------|--------|-----|------|-------|
| rosehip oil benefits | 18,000 | 42 | 45 | +3 |
| hyaluronic acid serum organic | 6,200 | 38 | 33 | +5 |
| cruelty free moisturizer | 9,400 | 35 | 27 | +4 |
"""
(BASE / "memory" / "research" / "keywords" / "secondary-keywords-current.md").write_text(secondary_kw)
set_mtime(BASE / "memory" / "research" / "keywords" / "secondary-keywords-current.md", 10)

# memory/research/competitors/beautycounter-analysis.md
beautycounter = f"""---
name: beautycounter-analysis
description: Current competitor analysis for beautycounter.com
type: competitor-analysis
---
# BeautyCounter – Competitor Analysis
Date: {date_str(18)}

DR: 72 | Traffic: ~890K/mo organic
Content Cadence: 3 posts/week
Strength: Very strong EEAT – founder credibility, safety mission narrative
Gap We Can Exploit: Ingredient science depth – they go broad, we can go deep
"""
(BASE / "memory" / "research" / "competitors" / "beautycounter-analysis.md").write_text(beautycounter)
set_mtime(BASE / "memory" / "research" / "competitors" / "beautycounter-analysis.md", 18)

# memory/monitoring/rank-history/2024-05-15-ranks.csv
rank_csv = """keyword,rank,prev_rank,delta,date
organic face serum,14,17,-3,2024-05-15
natural skincare routine,22,24,-2,2024-05-15
best organic moisturizer,31,31,0,2024-05-15
clean beauty products,8,9,-1,2024-05-15
vegan face cream,19,22,-3,2024-05-15
"""
(BASE / "memory" / "monitoring" / "rank-history" / f"{date_str(10)}-ranks.csv").write_text(rank_csv)

# memory/monitoring/reports/2024-Q1-report.md
q1_report = f"""---
name: 2024-q1-report
description: Q1 2024 SEO performance report
type: report
---
# Q1 2024 Performance Report
Period: Jan–Mar 2024

Organic sessions: 9,250 (baseline)
Avg position: 28.1
Domain Rating: 33
Indexed pages: 756

Key wins: Launched content cluster strategy, fixed XML sitemap.
"""
(BASE / "memory" / "monitoring" / "reports" / "2024-Q1-report.md").write_text(q1_report)
set_mtime(BASE / "memory" / "monitoring" / "reports" / "2024-Q1-report.md", 75)

# memory/monitoring/reports/2024-Q2-report.md
q2_report = f"""---
name: 2024-q2-report
description: Q2 2024 SEO performance report
type: report
---
# Q2 2024 SEO Performance Report
Period: Apr–Jun 2024

Organic sessions: 12,400 (+34% YoY)
Avg position: 24.3 (improved from 28.1)
Domain Rating: 38 (+5 from Q1)
Content published: 12 pieces

Key wins: Hero keyword cluster traction, backlink velocity improving.
Blocker: Core Web Vitals LCP still failing at 4.2s.
"""
(BASE / "memory" / "monitoring" / "reports" / "2024-Q2-report.md").write_text(q2_report)
set_mtime(BASE / "memory" / "monitoring" / "reports" / "2024-Q2-report.md", 30)

# memory/content/calendar/q3-content-plan.md
q3_calendar = f"""---
name: q3-content-plan
description: Q3 2024 content calendar for PureRoot Botanicals
type: content-calendar
---
# Q3 Content Calendar
Period: Jul–Sep 2024

1. Bakuchiol pillar page (PRIORITY – due {date_str(-14)})
2. Rosehip oil benefits deep dive
3. Sustainable packaging brand story
4. Ingredient science: Hyaluronic Acid vs Ceramides
5. User-generated content showcase (seasonal)
"""
(BASE / "memory" / "content" / "calendar" / "q3-content-plan.md").write_text(q3_calendar)
set_mtime(BASE / "memory" / "content" / "calendar" / "q3-content-plan.md", 7)

# memory/entities/pureroot-brand.md
entity_brand = f"""---
name: pureroot-brand
description: Canonical brand entity profile for PureRoot Botanicals
type: entity
---
# PureRoot Botanicals – Brand Entity

Founded: 2019 | HQ: Portland, OR
Certifications: COSMOS Organic, Leaping Bunny, B Corp pending
USP: Farm-to-face ingredient transparency with full supply chain tracing
Hero Product: Pure Bakuchiol Night Serum (bestseller since 2023)
Social: 48K IG followers, 12K Pinterest
"""
(BASE / "memory" / "entities" / "pureroot-brand.md").write_text(entity_brand)
set_mtime(BASE / "memory" / "entities" / "pureroot-brand.md", 14)

# memory/audits/content/content-audit-q2.md
content_audit = f"""---
name: content-audit-q2
description: Q2 content quality audit findings
type: content-audit
---
# Content Audit – Q2 2024
Date: {date_str(35)}

Audited: 48 pages
- High quality (keep): 22 pages
- Needs update: 18 pages  
- Consolidate/redirect: 8 pages

Top finding: Blog posts from 2021 lack ingredient sourcing citations (EEAT risk).
Priority: Update top 5 most-trafficked posts with citations before Q3.
"""
(BASE / "memory" / "audits" / "content" / "content-audit-q2.md").write_text(content_audit)
set_mtime(BASE / "memory" / "audits" / "content" / "content-audit-q2.md", 35)

# memory/audits/internal-linking/link-architecture-v1.md
link_audit = f"""---
name: link-architecture-v1
description: Internal linking architecture audit v1
type: internal-linking-audit
---
# Internal Linking Audit – v1
Date: {date_str(25)}

Found: 47 broken internal links
Top orphaned pages: /blog/organic-certification-guide, /ingredients/hyaluronic-acid
Recommended hub: /ingredients as primary linking hub
Action: Fix broken links, add contextual links from top 10 blog posts to hero product pages.
"""
(BASE / "memory" / "audits" / "internal-linking" / "link-architecture-v1.md").write_text(link_audit)
set_mtime(BASE / "memory" / "audits" / "internal-linking" / "link-architecture-v1.md", 25)

# memory/research/content-gaps/competitor-gaps-q2.md
content_gaps = f"""---
name: competitor-gaps-q2
description: Content gap analysis vs primary competitors Q2
type: content-gap-analysis
---
# Content Gap Analysis – Q2
Date: {date_str(22)}

Gaps vs BeautyCounter:
- "clean beauty certification guide" (vol: 4,400/mo) – they rank 3, we don't rank
- "ingredient safety database" content type – they have it, we don't

Gaps vs Tatcha:
- "Japanese skincare ritual" adjacent content – not our brand fit, skip
- "ceramides vs hyaluronic acid" comparison – vol 8,200/mo, KD 31 – OPPORTUNITY

Priority gaps to fill in Q3:
1. Bakuchiol vs retinol comparison (HIGH)
2. Clean beauty certification explainer (MEDIUM)
3. Ceramides comparison guide (MEDIUM)
"""
(BASE / "memory" / "research" / "content-gaps" / "competitor-gaps-q2.md").write_text(content_gaps)
set_mtime(BASE / "memory" / "research" / "content-gaps" / "competitor-gaps-q2.md", 22)

print("✅ Workspace generated successfully.")
print(f"Files created in: {BASE}")

# Verify line count of hot-cache.md
lines = (BASE / "memory" / "hot-cache.md").read_text().splitlines()
print(f"hot-cache.md line count: {len(lines)} (should be >80)")

# List WARM files >90 days
import os
print("\nFiles older than 90 days (should be archived):")
for root, dirs_list, files in os.walk(str(BASE / "memory")):
    if "archive" in root:
        continue
    for f in files:
        fp = Path(root) / f
        mtime = fp.stat().st_mtime
        age_days = (datetime.today().timestamp() - mtime) / 86400
        if age_days >= 90:
            print(f"  {fp.relative_to(BASE)} ({age_days:.0f} days)")