import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "hr/recruitment/2024/finance",
    "hr/recruitment/2024/operations",
    "hr/competency/archive/2022",
    "hr/competency/archive/2023",
    "finance/reports/Q1",
    "finance/reports/Q2",
    "finance/reports/Q3",
    "finance/tools/templates",
    "it/systems/erp",
    "it/systems/bi",
    "legal/compliance/2024",
    "strategy/planning/FY2025",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "hr/recruitment/2024/finance/jd_cfo_draft.txt": """
CFO Job Description Draft (INCOMPLETE)
- Lead financial planning and strategy
- Oversee treasury and capital markets
- Manage investor relations
Status: Pending Review
""",
    "hr/recruitment/2024/operations/jd_ops_manager.txt": """
Operations Manager JD v2
- Supply chain oversight
- Logistics optimization
- KPI: On-time delivery rate > 95%
""",
    "hr/competency/archive/2022/old_framework_v1.csv": """
competency,level,description
financial_analysis,3,Can build P&L statements
budgeting,2,Basic budget tracking
""",
    "hr/competency/archive/2023/framework_notes.txt": """
2023 competency framework notes:
- Merged treasury and risk into one dimension
- Added ESG compliance module
- Removed standalone reporting dimension
""",
    "finance/reports/Q1/cashflow_summary.txt": """
Q1 Cash Flow Summary
Operating CF: +120M
Investing CF: -45M
Financing CF: +30M
Net Change: +105M
""",
    "finance/reports/Q2/variance_analysis.txt": """
Q2 Budget vs Actual Variance
Revenue: +3.2% over budget
OpEx: -1.8% under budget
CAPEX: on track
""",
    "finance/reports/Q3/liquidity_report.txt": """
Q3 Liquidity Report
Current Ratio: 1.85
Quick Ratio: 1.42
Cash Coverage: 3.1x
""",
    "finance/tools/templates/budget_template.xlsx.placeholder": """
[Placeholder for budget template - see SharePoint]
""",
    "it/systems/erp/sap_modules.txt": """
SAP Modules in use:
- FI (Financial Accounting)
- CO (Controlling)
- TR (Treasury)
- MM (Materials Management)
""",
    "it/systems/bi/powerbi_dashboards.txt": """
Power BI Dashboard List:
1. Executive Finance Summary
2. Cash Flow Monitor
3. Budget Execution Tracker
4. Risk Heatmap
""",
    "legal/compliance/2024/sox_checklist.txt": """
SOX Compliance Checklist 2024:
[ ] Internal controls documented
[ ] IT general controls reviewed
[ ] Management assessment complete
[ ] External auditor sign-off pending
""",
    "strategy/planning/FY2025/strategic_priorities.txt": """
FY2025 Strategic Priorities:
1. Expand into SEA markets
2. Achieve investment-grade credit rating
3. Complete ERP modernization
4. Build AI-driven finance function
""",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE CORE PROBLEM FILE: messy, aliased, incomplete HR notes
# Uses garbled English aliases for the six canonical Chinese dimensions
# The agent must map these to the correct canonical dimensions from SKILL.md

problem_file_content = """
INTERNAL MEMO — FINANCE TALENT ASSESSMENT INITIATIVE
Project: AI Knowledge Base — Finance Capability Dictionary
Owner: HRBP Finance (Group Level)
Date: 2024-11-15
Status: DRAFT — DO NOT DISTRIBUTE

Background:
----------
The Group HR team is building an internal AI-powered knowledge base for assessing
finance talent across the group's business units. We need a standardized, machine-readable
capability model covering all core finance competencies for senior roles.

Our finance leads have provided rough notes on the capability areas we care about.
These notes are informal — please treat them as input signals, not final definitions.

Finance Lead Notes (raw):
--------------------------

AREA A: "Cash & Liquidity Control"
  - Cash forecasting, pooling structures, managing short-term liquidity risk,
    knowing how to use cash management platforms
  - We want to assess whether candidates can run a treasury operation

AREA B: "Fundraising & Capital Mix"
  - Equity vs debt decisions, optimizing the balance sheet, bank relationships,
    keeping cost of capital low
  - Candidates should know about different financing instruments

AREA C: "Budget Planning & Resource Allocation"
  - Full-cycle budgeting: from plan to execution to variance review
  - Should cover how budget links to strategy and performance management

AREA D: "Asset Control & Corporate Deals"
  - Fixed asset lifecycle, M&A analysis, restructuring, divesting non-core assets
  - Need candidates who have done deals, not just theory

AREA E: "Business Performance Analysis"
  - KPI dashboards, financial analysis reports, DuPont, value chain,
    helping leadership make decisions with data
  - Must be commercially minded, not just a number-cruncher

AREA F: "Fintech & Risk Compliance"
  - Digital finance tools (ERP, RPA, data platforms), internal controls,
    compliance frameworks, data visualization
  - The group is going through digital transformation so this is critical

Deliverable Required:
---------------------
Please produce a single structured file called `finance_capability_model.json`
that captures all six areas above in a format suitable for our AI knowledge base.
Each area entry must be complete and ready for use in automated candidate screening.

Notes from IT team:
- The file will be ingested by our vector search system
- Must be valid JSON (array at top level)
- Each entry needs to have enough detail to generate interview questions automatically

Please use the proper capability taxonomy and terminology from our internal standards.
"""

problem_file_path = os.path.join(workspace, "hr/recruitment/2024/finance/finance_talent_initiative_memo.txt")
with open(problem_file_path, "w", encoding="utf-8") as f:
    f.write(problem_file_content)

print("Workspace initialized successfully.")
print(f"Problem file: {problem_file_path}")
print(f"Total distractor files: {len(distractor_files)}")