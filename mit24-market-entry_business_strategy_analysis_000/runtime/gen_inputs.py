import os
import json
import yaml
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure with distractor files ──────────────────────────────
dirs = [
    "internal/finance/q3",
    "internal/finance/q4",
    "internal/marketing/campaigns",
    "internal/marketing/brand",
    "internal/sales/scripts",
    "internal/sales/crm_exports",
    "internal/product/roadmap",
    "internal/product/specs",
    "research/competitors",
    "research/market_sizing",
    "templates/decks",
    "templates/contracts",
    "deliverables",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "internal/finance/q3/budget_variance.csv": (
        "category,budget,actual\nR&D,120000,134500\nHR,80000,77200\nOperations,45000,48900\n"
    ),
    "internal/finance/q4/forecast_draft.txt": (
        "Q4 Revenue Forecast\nScenario A: $2.1M\nScenario B: $1.8M\nScenario C: $2.4M\n"
        "NOTE: These are preliminary numbers. Do not distribute.\n"
    ),
    "internal/marketing/campaigns/email_open_rates.csv": (
        "campaign,sent,opened,clicked\nProduct Launch,5000,1200,340\n"
        "Feature Update,3200,890,210\nCase Study,2100,760,190\n"
    ),
    "internal/marketing/brand/brand_guidelines_v2.txt": (
        "Brand Colors: #2C5F8A (primary), #F4A623 (accent)\n"
        "Typography: Inter (headings), Source Sans (body)\n"
        "Logo usage: minimum 40px height\n"
    ),
    "internal/sales/scripts/cold_call_template.txt": (
        "Opening: Hi [Name], I'm calling from BuildTrack...\n"
        "Hook: Did you know 68% of construction projects run over budget?\n"
        "Pitch: Our platform gives project managers real-time visibility...\n"
    ),
    "internal/sales/crm_exports/leads_oct.csv": (
        "lead_id,company,status,value\nL001,Apex Construction,qualified,45000\n"
        "L002,Meridian Builders,contacted,28000\nL003,SkyForm Inc,demo_scheduled,62000\n"
    ),
    "internal/product/roadmap/q4_roadmap.md": (
        "# Q4 Product Roadmap\n## Must Have\n- Gantt chart integration\n- Mobile punch-list\n"
        "## Nice to Have\n- Subcontractor portal\n- Document version control\n"
    ),
    "internal/product/specs/rfp_integration_spec.txt": (
        "Integration Requirements for BuildTrack v3.2\n"
        "- Procore sync (bidirectional)\n- Autodesk BIM 360 read access\n"
        "- QuickBooks export (weekly batch)\n"
    ),
    "research/competitors/comp_analysis_draft.txt": (
        "Competitor: Procore\nStrength: Market leader, 10k+ customers\nWeakness: Expensive, complex\n\n"
        "Competitor: PlanGrid\nStrength: Strong mobile UX\nWeakness: Limited financials module\n"
    ),
    "research/market_sizing/tam_notes.txt": (
        "Global construction management software TAM: $1.8B (2023)\nSAM (North America SMB): ~$320M\n"
        "SOM Year 1 target: $2.5M ARR\nSource: Gartner, IBISWorld estimates\n"
    ),
    "templates/decks/pitch_deck_outline.txt": (
        "Slide 1: Problem\nSlide 2: Solution\nSlide 3: Market Size\nSlide 4: Product Demo\n"
        "Slide 5: Business Model\nSlide 6: Traction\nSlide 7: Team\nSlide 8: Ask\n"
    ),
    "templates/contracts/nda_template.txt": (
        "NON-DISCLOSURE AGREEMENT\nThis agreement is entered into between BuildTrack Inc. (Disclosing Party)\n"
        "and [Recipient] (Receiving Party)...\n[TEMPLATE - LEGAL REVIEW REQUIRED]\n"
    ),
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── PRIMARY INPUT FILE 1: Raw, messy cost data ─────────────────────────────
# Intentionally messy: mixed labels, some irrelevant rows, comments
cost_data_raw = """\
# BuildTrack Sales & Marketing Expenditure Report
# Period: Q3 2024 (July - September)
# Prepared by: Finance Team (draft)

CATEGORY | SUBCATEGORY | AMOUNT (USD) | NOTES
---------|-------------|--------------|------
Marketing | Google Ads (Search) | 18500 | Core demand-gen channel
Marketing | LinkedIn Sponsored Content | 12300 | Enterprise segment targeting
Marketing | Content Marketing (blog, SEO) | 8700 | Includes freelance writers
Marketing | Webinars & Virtual Events | 5200 | 3 webinars hosted in period
Marketing | Tradeshows (World of Concrete) | 14000 | Booth + travel + collateral
Marketing | Brand Design Refresh | 3100 | One-time, agency fee
Sales | Sales Rep Salaries (2 FTE, 3 months) | 52000 | Base only, no bonus
Sales | Sales Rep Commissions (Q3) | 9800 | Paid on 7 closed deals
Sales | CRM License (Salesforce, 3 months) | 2700 | 3 seats
Sales | Sales Enablement Tools (Gong, Outreach) | 1800 | 3-month prorated
Sales | Demo environment hosting | 600 | AWS costs for demo instances
Sales | Sales Travel & Entertainment | 4200 | Client visits, 3 cities
OVERHEAD | Office allocation (sales/mktg share) | 6500 | Estimated, see note [1]
OVERHEAD | Finance team time allocation | 1200 | 10% of 1 FTE for reporting
OTHER | R&D prototype testing | 7800 | NOT sales/mktg - misclassified here
OTHER | Legal (contract templates) | 2400 | NOT sales/mktg - misclassified

# [1] Office allocation is estimated based on headcount ratio
# New customers acquired in Q3 2024: 7
# NOTE: The 2 "OTHER" line items above were mistakenly included in this report.
# CLV for BuildTrack average customer: $42,000 (36-month contract, avg)
# Monthly revenue per customer: $1,167 (avg)
# Gross margin: 71%
"""

with open(os.path.join(workspace, "internal/finance/q4/cost_report_q3_DRAFT.txt"), "w") as f:
    f.write(cost_data_raw)

# ── PRIMARY INPUT FILE 2: Business brief ──────────────────────────────────
business_brief = """\
BUILDTRACK INC. — BUSINESS BRIEF FOR MARKET ENTRY REVIEW
=========================================================
Product: B2B SaaS platform for construction project management (PMC)
Target Segment: Small-to-mid-size general contractors (GC) in North America, 10-200 employees
Pricing: $1,167/month per customer (annual contract required, billed monthly)
Contract length: 3 years average

INTERNAL TEAM BELIEFS & ASSUMPTIONS (unvalidated):
---------------------------------------------------
A1. Small GCs (10-200 employees) lose significant money due to poor project tracking — 
    the founders believe this is a severe daily pain point for 80%+ of this segment.
    [Team confidence: HIGH but based on 3 founder interviews only]

A2. The total addressable market in North America for this segment is ~$320M/year.
    [Source: analyst estimate, single report from 2021]

A3. BuildTrack's mobile punch-list and Gantt view will be sufficient to win customers 
    over Procore (the dominant player), because Procore is "too complex" for small GCs.
    [Based on 2 lost-deal post-mortems where customers cited Procore complexity]

A4. Customers will pay $1,167/month for this solution. 
    [Only tested with 2 design partners who are also personal contacts of CEO]

A5. The primary acquisition channel will be LinkedIn outreach + cold email, 
    reaching decision-makers (project managers and owners) at target GCs.
    [No channel test has been run yet]

A6. Sales cycle will average 45 days, and CAC will stay below $18,000 as we scale.
    [Based on Q3 actuals with 2 senior sales reps; assumes productivity stays constant]

A7. Gross margin will remain above 70% as we scale to 100+ customers.
    [Based on current infrastructure costs; assumes no major re-architecture needed]

CURRENT SALES MOTION (informal description):
--------------------------------------------
- SDRs find leads on LinkedIn and send cold emails
- If a lead responds, an AE does a discovery call (30 min)  
- AE determines if there's budget and a project in the next 90 days
- AE does a live demo on Zoom
- Prospect usually asks about Procore integration or data migration
- AE sends proposal; typical back-and-forth on pricing for 1-2 weeks
- Contract signed, onboarding begins
- No formal post-sale follow-up process exists today

OPEN QUESTIONS FROM LEADERSHIP:
--------------------------------
- Are we spending our sales/marketing budget efficiently?
- Which of our business assumptions is most likely to sink us?  
- What experiments should we run in the next 60 days to de-risk our model?
"""

with open(os.path.join(workspace, "internal/sales/market_entry_brief.txt"), "w") as f:
    f.write(business_brief)

# ── Instruction file for the agent ────────────────────────────────────────
task_instruction = """\
TASK: Market Entry Strategy Report
===================================
The leadership team at BuildTrack Inc. needs a comprehensive market entry 
strategy analysis. 

Please review the available financial data and business brief in the workspace 
and produce a complete market entry strategy report named:

    market_entry_strategy_report.json

The file should be placed anywhere in the workspace (we'll find it).
Use the MIT 24-step entrepreneurship framework Phase 4 methodology 
as your analytical foundation.

The report must cover all four analytical components the framework requires 
for this phase, based strictly on the data provided.
"""

with open(os.path.join(workspace, "TASK.md"), "w") as f:
    f.write(task_instruction)

print("Workspace generated successfully.")
print(f"Files created: {sum(len(files) for _, _, files in os.walk(workspace))}")