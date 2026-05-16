import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deep directory structure with distractor files ---

dirs = [
    "client_files/old_proposals",
    "client_files/contracts",
    "client_files/invoices",
    "resources/templates",
    "resources/rate_cards",
    "resources/competitors",
    "portfolio/dashboards",
    "portfolio/data_pipelines",
    "portfolio/web_projects",
    "admin/taxes",
    "admin/subscriptions",
    "notes/meetings",
    "notes/research",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "client_files/old_proposals/ecommerce_scraping_v2.txt": """
Client: RetailCo
Project: Scrape 10,000 product listings
Status: WON - Delivered 2023-11-15
Rate: $65/hr
""",
    "client_files/old_proposals/wordpress_fix_REJECTED.txt": """
Proposal sent for WordPress theme customization.
Client went with someone cheaper. Rate was $80/hr.
Lesson: Lower rate for simple jobs.
""",
    "client_files/contracts/nda_template.txt": """
NON-DISCLOSURE AGREEMENT
This agreement is entered into between Freelancer and Client...
[TEMPLATE - NOT FINALIZED]
""",
    "client_files/invoices/INV_2024_003.txt": """
Invoice #2024-003
Client: DataViz Corp
Amount: $2,400
Services: Dashboard development (24 hrs @ $100/hr)
Status: PAID
""",
    "resources/templates/generic_proposal_DO_NOT_USE.txt": """
Dear Sir/Madam,

I am writing to express my interest in your project. I am confident that my 5 years
of experience make me the perfect candidate. I look forward to hearing from you.

Best regards,
[YOUR NAME]
""",
    "resources/rate_cards/2023_rates_OUTDATED.txt": """
Web Dev: $45/hr
Data Analysis: $55/hr
Design: $40/hr
NOTE: These rates are from 2023, update before quoting!
""",
    "resources/competitors/market_survey_Q3.txt": """
Competitor analysis Q3 2024:
- TopCoder freelancers avg: $85/hr for BI work
- Upwork Top Rated avg: $95/hr for Tableau
- Fiverr Pro: $500-2000 per dashboard project
""",
    "portfolio/dashboards/tableau_retail_case_study.txt": """
Project: Retail Sales Dashboard
Client: MegaMart (NDA)
Deliverable: 12-page Tableau workbook with live SQL connections
Result: Reduced reporting time from 3 days/week to 2 hours/week
Technologies: Tableau Desktop, PostgreSQL, Python ETL
Duration: 3 weeks
""",
    "portfolio/dashboards/powerbi_manufacturing.txt": """
Project: Manufacturing KPI Monitor
Client: IndustrialCo
Deliverable: Power BI dashboard with 8 KPI panels
Result: Identified $200k/yr in production waste
Technologies: Power BI, Azure SQL, DAX
Duration: 2 weeks
""",
    "portfolio/data_pipelines/etl_ecommerce.txt": """
Project: Nightly ETL Pipeline
Stack: Python (pandas, SQLAlchemy), Airflow, Snowflake
Volume: ~500k rows/night
Outcome: Replaced manual Excel process, saved 10 hrs/week
""",
    "portfolio/data_pipelines/api_integration.txt": """
Project: Salesforce → BigQuery sync
Stack: Python, REST APIs, Google Cloud Functions
Schedule: Every 15 minutes
Outcome: Real-time sales visibility for 50-person team
""",
    "portfolio/web_projects/flask_dashboard.txt": """
Internal web dashboard for logistics company.
Stack: Flask, Plotly Dash, SQLite
Users: 30 internal staff
""",
    "admin/taxes/2024_quarterly.txt": """
Q1 2024: $8,200 gross, $2,050 estimated tax
Q2 2024: $11,400 gross, $2,850 estimated tax
""",
    "admin/subscriptions/tools.txt": """
Active subscriptions:
- Tableau Creator: $70/mo
- GitHub Pro: $4/mo
- Notion: $8/mo
- Loom: $12.50/mo
""",
    "notes/meetings/discovery_call_notes.txt": """
Call with HealthTech startup - 2024-09-12
They need a patient outcomes dashboard
Budget: unclear, "flexible"
Contact: Sarah M.
Follow up: Send portfolio by Friday
""",
    "notes/research/upwork_algorithm_notes.txt": """
Upwork JSS (Job Success Score) notes:
- Respond within 1 hour improves ranking
- Proposals with questions get 2x callback rate (anecdotal)
- Top proposals are 200-250 words on average
- Never copy-paste the same proposal
""",
}

for path, content in distractors.items():
    full_path = workspace / path
    full_path.write_text(content.strip())

# --- THE ACTUAL TASK INPUT: The job listing ---

job_listing_content = """
PLATFORM: Upwork
POSTED: 2 days ago
CLIENT HISTORY: 47 hires, $180k+ spent, 4.9/5.0 rating, 91% hire rate
BUDGET: Fixed Price — $1,800–$2,500
CATEGORY: Data Science & Analytics

--- JOB TITLE ---
Build Real-Time Sales Dashboard in Tableau + Python ETL Pipeline

--- JOB DESCRIPTION ---
We're a 60-person SaaS company. Our ops team currently pulls sales data manually
from three sources every morning: Salesforce CRM, Stripe (payments), and our
internal PostgreSQL database. This takes 2-3 hours daily and the numbers are
always slightly out of sync because the exports happen at different times.

What we need:
- Python-based ETL pipeline that pulls from Salesforce API, Stripe API, and
  PostgreSQL, normalizes the data, and loads into a single PostgreSQL staging
  schema (we'll handle the hosting)
- Tableau dashboard (we have Tableau Server) connected to the staging schema,
  showing: MRR, churn rate, new vs expansion revenue, top accounts by ARR
- Refresh frequency: every 30 minutes
- Deliverables: Python scripts (with requirements.txt), Tableau .twbx file,
  and brief technical rundown of the architecture

We're not looking for someone to explain what ETL means. We know our stack.
We need someone who has done this before and can deliver clean, maintainable
code. Timeline: 7-10 business days.

Skills required: Python, Tableau, Salesforce API, Stripe API, PostgreSQL, ETL
---
"""

job_listing_path = workspace / "current_job_listing.txt"
job_listing_path.write_text(job_listing_content.strip())

print("Workspace initialized.")
print(f"Job listing written to: {job_listing_path}")
print(f"Total distractor files: {len(distractors)}")