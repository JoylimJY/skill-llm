import os
import random
import pandas as pd
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create deeply nested distractor directory structure ---
dirs = [
    "workspace/marketing/campaigns/q3_2024",
    "workspace/marketing/campaigns/q4_2024",
    "workspace/marketing/social/instagram",
    "workspace/marketing/social/linkedin",
    "workspace/product/roadmap/2024",
    "workspace/product/roadmap/2025",
    "workspace/seo/audits/site_health",
    "workspace/seo/audits/backlinks",
    "workspace/seo/content/drafts",
    "workspace/finance/budgets",
    "workspace/hr/hiring",
    "workspace/sales/pipeline",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractors = {
    "workspace/marketing/campaigns/q3_2024/email_performance.csv": """campaign,opens,clicks,unsubscribes
welcome_series,4200,1100,23
product_update,3100,820,15
webinar_invite,2900,640,10
""",
    "workspace/marketing/campaigns/q4_2024/budget_allocation.txt": """Q4 Budget Breakdown
Paid Search: $45,000
Content: $20,000
Events: $15,000
Social: $10,000
""",
    "workspace/marketing/social/linkedin/post_ideas.txt": """- How we reduced customer churn by 40%
- Behind the scenes: our product team
- Customer spotlight: Acme Corp
""",
    "workspace/product/roadmap/2024/features_shipped.txt": """Q1: Gantt chart view
Q2: Time tracking integration
Q3: Custom dashboards
Q4: AI task suggestions
""",
    "workspace/product/roadmap/2025/planned_features.txt": """- Resource management module
- Advanced reporting suite
- Client portal
- Mobile offline mode
""",
    "workspace/seo/audits/site_health/crawl_errors.csv": """url,error_type,status_code
/old-pricing,redirect_chain,301
/deprecated-api,broken_link,404
/blog/2019/intro,slow_page,200
""",
    "workspace/seo/audits/backlinks/raw_export_2024.csv": """source_domain,target_url,anchor_text,dr
techblog.io,/features,project management tool,45
saasreview.net,/pricing,affordable pm software,38
startupdigest.com,/blog/remote-teams,remote work tools,52
""",
    "workspace/seo/content/drafts/blog_draft_agile.txt": """Title: Agile Project Management in 2024
Status: Draft
Target keyword: agile project management software
Word count target: 2200
Notes: Need to add competitor comparison table
""",
    "workspace/finance/budgets/annual_2024.txt": """Revenue target: $8.2M
Marketing spend: $1.1M
R&D spend: $2.3M
G&A: $0.9M
""",
    "workspace/hr/hiring/open_roles.txt": """- Senior Backend Engineer (Go)
- Product Marketing Manager
- Customer Success Lead
- Data Analyst
""",
    "workspace/sales/pipeline/q3_deals.csv": """company,arr,stage,close_date
Globex Corp,48000,negotiation,2024-09-15
Initech LLC,22000,demo,2024-09-28
Umbrella Co,75000,proposal,2024-10-05
""",
    "workspace/marketing/social/instagram/content_calendar.txt": """Week 1: Product screenshot carousel
Week 2: Team culture post
Week 3: Customer quote
Week 4: Feature highlight reel
""",
}

for filepath, content in distractors.items():
    with open(filepath, "w") as f:
        f.write(content)

# --- THE MAIN PROBLEM: Messy competitor data Excel file ---
# This is the raw, messy input the agent must parse and use to build the report
# Headers are non-standard / real-world messy

competitor_data = {
    "Competitor Name": ["Asana", "Monday.com", "ClickUp", "Notion", "Basecamp"],
    "Website": ["asana.com", "monday.com", "clickup.com", "notion.so", "basecamp.com"],
    "Category": ["PM Software", "Work OS", "PM Software", "Productivity/PM", "PM Software"],
    "Est. Monthly Visits (SimilarWeb)": [14200000, 22800000, 9400000, 31000000, 2100000],
    "Organic Traffic Share (%)": [38, 44, 29, 51, 18],
    "Domain Rating (Ahrefs)": [91, 88, 85, 92, 80],
    "Top Organic Keywords": [
        "project management, asana alternatives, team tasks, work tracker",
        "monday.com alternatives, project tracking, work management, crm",
        "clickup vs asana, free project management, task manager app, agile pm",
        "notion vs confluence, note taking app, notion alternatives, wiki software",
        "basecamp alternatives, simple project management, client projects",
    ],
    "Backlinks (approx)": [4200000, 3800000, 2100000, 5100000, 890000],
    "Referring Domains": [48000, 43000, 29000, 61000, 14000],
    "Unique Linking Sites (not linking to us)": [31000, 28500, 19000, 44000, 9800],
    "Avg Content Length (words)": [2400, 2100, 2800, 1900, 1600],
    "Content H2 Topics Covered": [
        "features, pricing, integrations, use cases, templates, alternatives",
        "features, pricing, CRM, marketing, integrations, onboarding",
        "features, pricing, time tracking, goals, docs, alternatives, integrations",
        "features, pricing, templates, teams, API, use cases",
        "features, pricing, testimonials, case studies",
    ],
    "Pricing Model": [
        "Freemium; $10.99-$24.99/user/mo (billed annually)",
        "Freemium; $9-$19/user/mo (billed annually); enterprise custom",
        "Freemium; $5-$19/user/mo (billed annually)",
        "Freemium; $8-$15/user/mo (billed annually)",
        "Flat; $99/mo up to 20 users; $299/mo unlimited",
    ],
    "Key Strength": [
        "Brand recognition; enterprise integrations; robust workflows",
        "Visual UI; marketing/CRM crossover; strong onboarding",
        "Feature depth; generous free tier; heavy customization",
        "Docs + PM hybrid; developer community; API",
        "Simplicity; flat pricing; client-friendly interface",
    ],
    "Primary Target Audience": [
        "Mid-market & enterprise teams",
        "Marketing, sales, and ops teams; SMB to enterprise",
        "Startups and SMBs; power users",
        "Developers, startups, and knowledge workers",
        "Small agencies and service businesses",
    ],
    "Key Marketing Channel": [
        "Paid search; content marketing; G2/Capterra",
        "Paid social; influencer; TV/OOH; integrations marketplace",
        "SEO; YouTube; product-led growth",
        "Community; word-of-mouth; developer content",
        "Email; word-of-mouth; anti-bloat positioning",
    ],
    "Content Gap vs Us": [
        "Resource management guides; ROI calculator; enterprise case studies",
        "Industry-specific templates; CRM workflow guides",
        "Time tracking deep dives; goal-setting frameworks; sprint planning",
        "API documentation; team wiki setup; knowledge management",
        "Agency workflow templates; client onboarding guides",
    ],
    "Market Position": [
        "Market leader; premium brand",
        "Fast-growing challenger; visual-first",
        "Feature-parity disruptor; price competitive",
        "Adjacent disruptor; growing PM use case",
        "Niche simplicity play; anti-enterprise",
    ],
}

df = pd.DataFrame(competitor_data)

# Add some realistic messiness: extra blank rows, an extra metadata header block
excel_path = Path("workspace/seo/competitor_data_raw.xlsx")
with pd.ExcelWriter(str(excel_path), engine="openpyxl") as writer:
    # Write a "metadata" sheet first (distractor)
    meta_df = pd.DataFrame({
        "Export Info": ["Exported by", "Date", "Source", "Notes"],
        "Value": ["Marketing Ops Team", "2024-08-15", "SimilarWeb + Ahrefs + Manual", "Draft - verify traffic numbers before publishing"]
    })
    meta_df.to_excel(writer, sheet_name="Export_Info", index=False)
    
    # Write main data with a blank row at top (messiness)
    # Write blank header row then actual data
    df.to_excel(writer, sheet_name="Competitor_Data", index=False, startrow=2)
    
    # Also write a partial "SERP Overlap" sheet
    serp_df = pd.DataFrame({
        "Keyword": [
            "project management software",
            "best pm tools",
            "free project management app",
            "agile project management",
            "team task management",
            "project tracking software",
            "online project management",
            "work management platform",
        ],
        "Our Rank": [14, 22, 31, 8, 12, 19, 25, 38],
        "Asana Rank": [1, 2, 5, 3, 2, 1, 2, 4],
        "Monday Rank": [2, 1, 8, 7, 3, 2, 1, 1],
        "ClickUp Rank": [3, 4, 1, 5, 6, 3, 4, 6],
        "Notion Rank": [6, 8, 3, 11, 9, 7, 5, 3],
        "Monthly Search Volume": [135000, 74000, 49000, 68000, 41000, 33000, 28000, 22000],
        "Opportunity (rank 4-10?)": ["No (us:14)", "No (us:22)", "No (us:31)", "Yes (us:8)", "Yes (us:12)", "No (us:19)", "No (us:25)", "No (us:38)"],
    })
    serp_df.to_excel(writer, sheet_name="SERP_Overlap", index=False)

print(f"Created: {excel_path}")
print("Workspace structure created successfully.")

# Create a minimal project-context stub so the agent knows the company
project_context_path = Path("workspace/project-context.md")
project_context_path.write_text("""# Project Context

## Company: TaskFlow Pro
**Product**: B2B project management SaaS
**URL**: taskflowpro.com
**Target Audience**: SMB and mid-market operations teams (10–500 employees)
**Current Organic Traffic**: ~320,000 monthly visits
**Domain Rating**: 61
**Referring Domains**: 4,200
**Top Performing Content**: /blog/project-management-tips, /features/gantt-chart, /pricing

## Section 11 – Competitor Intelligence
Raw competitor data file: seo/competitor_data_raw.xlsx
Priority research types: keyword gaps, content gaps, backlink link-gap, pricing positioning
""")

print(f"Created: {project_context_path}")