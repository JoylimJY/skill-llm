import os
import json
import random

random.seed(42)

BASE = "/workspace"

# --- Directory Structure ---
dirs = [
    "market_research/interviews",
    "market_research/surveys",
    "market_research/competitor_data",
    "internal_notes/product",
    "internal_notes/sales",
    "financial_models/drafts",
    "financial_models/archived",
    "team_docs/weekly_updates",
    "team_docs/retrospectives",
    "legal/contracts",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)


# --- Distractor Files ---
distractor_files = {
    "internal_notes/product/feature_backlog.txt": """
Feature Backlog (Q3 2024)
=========================
- Real-time soil moisture sensor integration
- Multi-farm dashboard
- API for ERP connectors
- Weather forecast overlay
- Yield prediction model v2
- Mobile app offline mode
TODO: Prioritize with PM team before sprint planning
""",
    "internal_notes/sales/pipeline_notes.txt": """
Sales Pipeline Notes - July 2024
- Lead: Sunridge Farms (CA) - warm, uses competitor X
- Lead: Midwest Grain Co - cold, no budget confirmed
- Prospect: Vertical Farm Group - evaluating 3 vendors
- Lost: FreshPath Organics - went with manual spreadsheets
Notes: Need better case studies for large farms.
""",
    "financial_models/drafts/cost_model_v2.csv": """
Category,Monthly Cost (USD),Notes
Cloud Infra,1200,AWS estimate
Salaries,45000,5 engineers + 1 PM
Marketing,5000,Digital ads
Support,800,Zendesk
Misc,400,Office + subscriptions
""",
    "financial_models/archived/old_projections_2023.txt": """
2023 Projections (ARCHIVED - DO NOT USE)
Year 1 Revenue: $120,000
Year 2 Revenue: $480,000
Year 3 Revenue: $1,200,000
Assumptions: 5% market share, $2000 ACV
NOTE: These were pre-product assumptions, invalid now.
""",
    "team_docs/weekly_updates/week_28.txt": """
Week 28 Update
--------------
- Completed beta testing with 3 farms
- NPS score: 62
- Two bugs fixed in irrigation module
- Demo scheduled with Agri-Corp next Tuesday
- Competitor Y launched new pricing tier
""",
    "team_docs/retrospectives/q2_retro.txt": """
Q2 Retrospective
What went well: Customer feedback sessions, fast deployment cycles
What didn't: Sales cycle too long, unclear ICP definition
Action items: Define target customer more precisely, improve onboarding
""",
    "legal/contracts/template_saas_agreement.txt": """
SaaS Master Agreement Template (DRAFT)
Parties: [Company] and [Customer]
Term: 12 months auto-renewing
Payment: Annual upfront
Liability cap: 12 months of fees
Data: Customer owns all farm data
DRAFT - not for distribution
""",
    "market_research/competitor_data/competitor_overview.txt": """
Competitor Overview (Research Dept, Aug 2024)
=============================================
Competitor A: Large enterprise ag-tech, $500M ARR, focuses on >5000 acre farms
Competitor B: Mobile-first startup, seed stage, targets hobby farmers
Competitor C: ERP giant with ag module, complex implementation (6+ months), $50k+/yr
Competitor D: Free tier tool, no support, used by small operations
Gap identified: Mid-size commercial farms (500-5000 acres) are underserved.
""",
    "market_research/surveys/survey_raw_results.txt": """
Survey Results - 40 responses (June 2024)
==========================================
Q: What's your biggest operational challenge?
- Labor costs: 38%
- Water management: 27%
- Crop yield unpredictability: 20%
- Regulatory compliance: 15%

Q: Would you pay for software to address this?
- Yes, if ROI clear: 61%
- Maybe: 24%
- No: 15%

Q: Current budget for farm management software:
- $0 (none): 22%
- $1k-$5k/yr: 35%
- $5k-$20k/yr: 30%
- $20k+/yr: 13%
""",
    "internal_notes/product/tech_specs_draft.txt": """
Technical Architecture Notes (Draft)
IoT sensor layer: MQTT protocol, 15-min polling
Backend: Python/FastAPI, PostgreSQL
Frontend: React, mobile-responsive
Integrations: John Deere Operations Center API, Climate FieldView
Hosting: AWS us-east-1 + eu-west-1
Security: SOC2 Type II in progress
""",
}

for path, content in distractor_files.items():
    with open(os.path.join(BASE, path), "w") as f:
        f.write(content)


# --- Core Problem Input Files ---

# Raw market segmentation brainstorm (messy, unsorted)
with open(os.path.join(BASE, "market_research/raw_segment_brainstorm.txt"), "w") as f:
    f.write("""
MARKET SEGMENTATION BRAINSTORM SESSION - Aug 5, 2024
Participants: CEO, Head of Sales, 2x Customer Success
(unedited notes)

Possible customer types we discussed:
---
1. Large commodity grain farms (corn/soy/wheat), 2000-10000 acres, Midwest USA
   - Big operations, have dedicated ops managers
   - Currently use legacy ERP or nothing digital
   - Pain: labor tracking, water usage compliance (new EPA regs 2024)
   - Budget: $20k-80k/yr range
   - Tough to reach: dominated by big ag-tech companies
   - Competition: Competitor A owns this space, very hard to break in
   - Lots of them: ~45,000 farms of this size in USA
   - Growth: ~2% annually, fairly stable

2. Mid-size vegetable/specialty crop farms, 200-2000 acres, CA/FL/TX
   - Owner-operated or family businesses
   - Huge labor cost pressure, water restrictions in CA
   - Pain: real-time field monitoring, labor compliance (wage laws)
   - Budget: $5k-20k/yr, willing to pay if ROI proven
   - Reachable via farm bureaus, trade shows (World Ag Expo etc.)
   - Weak competition: Competitor C too expensive, B too simple
   - Estimated: ~18,000 farms this profile in target states
   - Growth: ~7% annually (specialty crops booming)

3. Vertical/indoor farming operations, 10,000-100,000 sq ft facilities
   - Tech-savvy, VC-backed often
   - Already use some software, need integration
   - Pain: energy cost optimization, climate control automation
   - Budget: $15k-60k/yr
   - Reachable via LinkedIn, industry conferences (Indoor AgTech)
   - Competition: Several well-funded startups competing here
   - Estimated: ~2,000 facilities in USA
   - Growth: ~25% annually (hot sector)

4. Agricultural cooperatives (co-ops), multi-member organizations
   - Represent many smaller farms collectively
   - Long procurement cycles, committee decisions
   - Pain: member reporting, compliance aggregation
   - Budget: $30k-150k/yr (org level)
   - Hard to reach: procurement through formal RFP process
   - Competition: Enterprise software vendors (SAP Agri etc.)
   - Estimated: ~3,000 co-ops in USA
   - Growth: ~1% annually

5. Small organic farms, <200 acres, various regions
   - Very price-sensitive
   - Pain: certification tracking, market access
   - Budget: <$2k/yr, often grant-funded
   - Reachable via USDA programs, organic associations
   - Competition: Many free tools, Competitor D
   - Estimated: ~25,000 farms
   - Growth: ~4% annually

INITIAL VOTE on priority (3=high, 1=low):
Segment 1: 1 (too competitive)
Segment 2: 3 (best fit?)
Segment 3: 2 (fast growing but crowded)
Segment 4: 1 (long sales cycles)
Segment 5: 1 (no budget)
""")


# Interview transcripts (messy, unstructured)
with open(os.path.join(BASE, "market_research/interviews/interview_carlos_mendoza.txt"), "w") as f:
    f.write("""
CUSTOMER INTERVIEW TRANSCRIPT
Interviewee: Carlos Mendoza
Role: Farm Operations Manager
Farm: Mendoza Family Farms, 850 acres, bell peppers + tomatoes, Fresno CA
Date: July 18, 2024
Interviewer: Head of Sales

[Lightly edited for readability]

Q: What's your biggest headache right now?
A: Honestly, water. We're under a water district restriction since last year. I have to report weekly usage to the district and if we go over quota, fines are crazy. I'm doing this in Excel right now and it takes me half a day every week. Plus I'm always worried I miscounted something.

Q: What does a typical day look like for you?
A: I'm up at 5am, check soil moisture readings (we have some sensors but they're old), then schedule the irrigation run, coordinate with 40-50 seasonal workers for the day. A lot of my day is just managing people and making sure we hit our harvest windows.

Q: What software do you currently use?
A: QuickBooks for accounting. A very old farm management thing my dad bought in 2015 - it's basically useless now. And a lot of spreadsheets. I looked at Competitor C's product but it was $45,000 a year and needed a 6-month setup - no way.

Q: If you had a tool that automated your water reporting, what would you pay?
A: Honestly, if it saved me the half-day a week and kept me compliant, I'd pay $8,000-10,000 a year easy. My time is worth more than that.

Q: Who else would need to sign off on buying new software?
A: My father (he owns the farm), and our accountant would want to know it integrates with QuickBooks. That's basically it for a purchase this size. My dad trusts me on operational stuff.

Q: Where do you get information about new tools?
A: World Ag Expo in Tulare, the California Farm Bureau newsletter, and honestly word of mouth from other farmers at the water district meetings.

Q: What would make you nervous about buying a new system?
A: Honestly, data security - I don't want my planting and yield data going to competitors. And I've been burned before by software that promises a lot and then the company disappears or stops updating it.
""")

with open(os.path.join(BASE, "market_research/interviews/interview_priya_shah.txt"), "w") as f:
    f.write("""
CUSTOMER INTERVIEW TRANSCRIPT  
Interviewee: Priya Shah
Role: Co-owner / CFO
Farm: Shah Organic Greens, 340 acres, mixed vegetables, Homestead FL
Date: July 22, 2024
Interviewer: CEO

Q: What keeps you up at night business-wise?
A: Labor. We have 60+ workers during peak season, wage theft audits are getting more frequent in Florida, and I have to maintain I-9 documentation for everyone. One audit finding could cost us $100k in fines. I use paper binders right now - it's absurd.

Q: Have you looked at any software solutions?
A: Yes, a few. One HR platform wanted $15k/yr just for labor compliance, but it didn't connect to our irrigation at all. I need something that connects the operational side and the compliance side. Nobody seems to have that.

Q: What's your software budget generally?
A: We spent $6,000 last year on various tools. I think I could justify $12,000-15,000 for something that genuinely integrated labor and field operations and saved us from audit risk.

Q: Who makes the purchasing decision in your family operation?
A: Me and my husband Raj, who runs field operations. We'd decide together. For anything over $10k, we'd probably want a 30-day trial or pilot first.

Q: Where do you learn about new products?
A: Instagram ag groups, Florida Farm Bureau, and a WhatsApp group I'm in with other organic farmers in South Florida. Word of mouth is huge.

Q: What's your biggest hesitation about new software?
A: Two things: will my workers actually use it (they're not tech-savvy), and will the company be around in 3 years? I've been burned by a startup that shut down.
""")


# Partial market sizing data (messy spreadsheet dump)
with open(os.path.join(BASE, "market_research/market_sizing_raw_data.txt"), "w") as f:
    f.write("""
MARKET SIZING RAW DATA (compiled from USDA NASS 2022 Census, IBISWorld Ag-Tech report 2023)
===========================================================================================
NOTE: Numbers are approximate, cross-check before using in pitch deck

US Farm Statistics (USDA 2022):
- Total US farms: 2,000,000
- Farms 200-2000 acres (commercial mid-size): ~95,000 farms nationally
- Of those, specialty/vegetable focus: ~19,000 farms
- Of those, in CA+FL+TX (our initial target states): ~11,500 farms

Pricing research (competitor analysis + our beta interviews):
- Willingness to pay range confirmed: $6,000 - $18,000/yr for integrated solution
- Our planned pricing tier: $9,600/yr ($800/mo) - mid-market
- Beta users actually paying: $9,600 - $14,400/yr (3 beta customers)

Competitor market share estimates (mid-size specialty farms, 200-2000 acres):
- Competitor A: <5% (focuses on large farms, poor fit)
- Competitor C: ~8% (too expensive but has some customers)
- Free/no software: ~55% (massive opportunity)
- DIY spreadsheets: ~25%
- Other tools: ~7%

Serviceable geography for Year 1: CA + FL + TX = 11,500 farms
Realistic Year 1 target (based on team capacity + sales bandwidth): 
- Sales team can handle 5 demos/week = 260 demos/yr
- Estimated close rate from beta: ~15%
- Expected Year 1 customers: ~35-40 farms

Market growth rate for specialty crop farms: 6-8% per year (IBISWorld)

Global addressable market (all commercial farms worldwide needing this type of solution):
- Rough estimate from industry analyst report: $4.2B total market for farm compliance + operations software
""")


# The main task instruction file
with open(os.path.join(BASE, "task_brief.txt"), "w") as f:
    f.write("""
STRATEGIC ANALYSIS TASK BRIEF
Prepared by: CEO Office
Date: August 2024
For: Strategy Consultant / Senior Analyst

CONTEXT:
We are building a precision agriculture SaaS platform (working name: "AgroSync"). 
We have accumulated raw market research, customer interview notes, survey results, 
and internal brainstorming notes in this workspace.

YOUR TASK:
Using all available materials in this workspace, produce a comprehensive market 
segmentation and customer insights report for AgroSync.

The report must be saved as: market_insights_report.json

This report will be used to:
1. Decide which customer segment to focus on first
2. Set realistic revenue targets for our seed round pitch
3. Understand our customer's decision-making process to improve our sales approach

Please base your analysis on the actual data and interview notes available here.
The final JSON file should be structured, comprehensive, and investor-ready.
""")

print("Workspace generated successfully.")
print(f"Files created in {BASE}:")
for root, dirs_list, files in os.walk(BASE):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")