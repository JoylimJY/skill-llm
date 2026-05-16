import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep directory structure with distractor files ──────────────────────────
dirs = [
    "procurement/2024/Q3/tender_docs",
    "procurement/2024/Q3/bid_submissions",
    "procurement/2024/Q3/evaluation_committee",
    "procurement/2024/Q4/archived",
    "finance/budget/municipal",
    "finance/audit_trail",
    "hr/staff_roster",
    "it_systems/erp_exports",
    "legal/contracts/signed",
    "legal/contracts/pending",
    "reports/monthly/october",
    "reports/monthly/november",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "procurement/2024/Q3/tender_docs/project_overview.txt": (
        "Municipal Water Pipeline Expansion Project\n"
        "Estimated Budget: 5,200,000 CNY\n"
        "Deadline: 2024-11-30\n"
        "Supervising Authority: City Infrastructure Bureau\n"
    ),
    "procurement/2024/Q3/tender_docs/technical_specs.txt": (
        "Pipeline diameter: DN300\nMaterial: Ductile iron\nLength: 12.4 km\n"
        "Pressure rating: 1.6 MPa\nInstallation standard: GB/T 13295\n"
    ),
    "procurement/2024/Q3/bid_submissions/vendor_A_technical.txt": (
        "Vendor: Huabei Construction Co.\nTech score: 72.5\n"
        "Project manager: Zhang Wei\nQualification: Grade A\n"
    ),
    "procurement/2024/Q3/bid_submissions/vendor_B_technical.txt": (
        "Vendor: Dongnan Pipeline Ltd.\nTech score: 68.0\n"
        "Project manager: Li Fang\nQualification: Grade B+\n"
    ),
    "procurement/2024/Q3/bid_submissions/vendor_C_technical.txt": (
        "Vendor: Xibei Civil Engineering Inc.\nTech score: 75.0\n"
        "Project manager: Wang Jun\nQualification: Grade A\n"
    ),
    "procurement/2024/Q3/bid_submissions/vendor_D_technical.txt": (
        "Vendor: Zhongnan Infra Group\nTech score: 61.0\n"
        "Project manager: Chen Mei\nQualification: Grade B\n"
    ),
    "procurement/2024/Q3/evaluation_committee/members.txt": (
        "Committee Chair: Prof. Liu Hao (Tsinghua University)\n"
        "Member 1: Senior Engineer Zhao Lin\n"
        "Member 2: Financial Expert Sun Qiang\n"
        "Member 3: Legal Advisor Ms. Wu Ying\n"
    ),
    "procurement/2024/Q4/archived/old_formula_v1.txt": (
        "DEPRECATED - DO NOT USE\n"
        "Old formula: =30-ABS(B2-E2)/B2*100*0.8\n"
        "This formula had an error in denominator (used bid price instead of benchmark).\n"
    ),
    "finance/budget/municipal/allocation_2024.csv": (
        "Department,Budget_CNY,Spent_CNY,Remaining_CNY\n"
        "Infrastructure,12000000,8750000,3250000\n"
        "IT Systems,2000000,1850000,150000\n"
        "HR,500000,480000,20000\n"
    ),
    "finance/audit_trail/log_2024_oct.txt": (
        "2024-10-01: Budget review completed\n"
        "2024-10-15: Procurement process initiated\n"
        "2024-10-28: Bid opening event recorded\n"
    ),
    "hr/staff_roster/evaluators.json": json.dumps({
        "evaluators": [
            {"id": "E001", "name": "Liu Hao", "role": "chair"},
            {"id": "E002", "name": "Zhao Lin", "role": "technical"},
            {"id": "E003", "name": "Sun Qiang", "role": "financial"}
        ]
    }, indent=2),
    "it_systems/erp_exports/vendor_registry.csv": (
        "VendorID,Name,Region,Registered\n"
        "V001,Huabei Construction Co.,North,2018-03-15\n"
        "V002,Dongnan Pipeline Ltd.,East,2015-07-22\n"
        "V003,Xibei Civil Engineering Inc.,West,2020-01-10\n"
        "V004,Zhongnan Infra Group,South,2012-11-05\n"
    ),
    "legal/contracts/signed/framework_agreement.txt": (
        "Framework Agreement No. CIB-2024-088\n"
        "Parties: City Infrastructure Bureau & Winning Vendor (TBD)\n"
        "Validity: 3 years from contract signing date\n"
    ),
    "legal/contracts/pending/nda_template.txt": (
        "NON-DISCLOSURE AGREEMENT TEMPLATE\n"
        "This agreement is pending finalization by legal team.\n"
    ),
    "reports/monthly/october/summary.txt": (
        "October Procurement Activity Summary\n"
        "Active tenders: 3\nBids received: 11\nContracts awarded: 1\n"
    ),
    "reports/monthly/november/placeholder.txt": (
        "November report not yet generated.\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── THE ACTUAL TASK INPUT FILES ──────────────────────────────────────────────

# 1. The tender evaluation formula specification
formula_spec = """MUNICIPAL WATER PIPELINE EXPANSION PROJECT
Bid Price Score Formula Specification (Document: CIB-2024-088-F)

Evaluation Method: Comprehensive Scoring Method (综合评分法)
Price Score Weight: 30 points (满分 30 分)

FORMULA (Excel cell reference format):
=IFERROR(ROUND(IF(B2<E2,MAX(0,F2-ABS(B2-E2)/E2*100*0.6),IF(B2=E2,F2,MAX(0,F2-ABS(B2-E2)/E2*100*0.9))),2),0)

Variable Definitions:
  B2 = Vendor bid price (报价), unit: 万元 (10,000 CNY)
  E2 = Benchmark price (基准价), unit: 万元 (10,000 CNY)
  F2 = Maximum price score / benchmark score (基准分) = 30

Benchmark Price Calculation:
  The benchmark price E2 is computed as the arithmetic mean of all valid bids
  after removing the single highest and single lowest bid.

NOTE: This formula supersedes all previous versions. The deprecated v1 formula
      in archived documents must NOT be used.
"""

with open(os.path.join(workspace, "procurement/2024/Q3/tender_docs/price_score_formula.txt"), "w", encoding="utf-8") as f:
    f.write(formula_spec)

# 2. Raw bid price data (messy, with some formatting issues)
bid_data = """BID OPENING RECORD - CIB-2024-088
Date: 2024-11-15
Witnessed by: Evaluation Committee

Vendor ID | Vendor Name                  | Bid Price (万元) | Notes
----------|------------------------------|-----------------|----------------------------
V001      | Huabei Construction Co.      | 498.50          | Valid bid
V002      | Dongnan Pipeline Ltd.        | 521.00          | Valid bid
V003      | Xibei Civil Engineering Inc. | 476.20          | Valid bid
V004      | Zhongnan Infra Group         | 389.00          | Valid bid  <- LOWEST
V005      | Beibu General Contractors    | 534.80          | Valid bid  <- HIGHEST

Total valid bids: 5
Bids to exclude for benchmark: highest (V005: 534.80) and lowest (V004: 389.00)
Remaining for benchmark calculation: V001=498.50, V002=521.00, V003=476.20
"""

with open(os.path.join(workspace, "procurement/2024/Q3/bid_submissions/bid_opening_record.txt"), "w", encoding="utf-8") as f:
    f.write(bid_data)

# 3. Evaluation task request
task_request = """EVALUATION TASK REQUEST
Issued by: Evaluation Committee Chair Prof. Liu Hao
Date: 2024-11-15
Reference: CIB-2024-088

Please produce a price score evaluation report for all 5 vendors.

Requirements:
1. Parse the formula from price_score_formula.txt and document its structure.
2. Calculate the benchmark price from the bid opening record (exclude highest/lowest).
3. For each vendor, compute their price score using the specified formula,
   showing all intermediate calculation steps.
4. Identify any boundary/edge cases in the formula and flag them.
5. Output the results to a file named: price_score_report.json

The JSON file must contain:
- formula_analysis: parsed structure of the formula
- benchmark_price: the computed benchmark price value
- vendor_scores: array of per-vendor results with calculation steps
- boundary_analysis: identified edge cases and risks
"""

with open(os.path.join(workspace, "procurement/2024/Q3/evaluation_committee/evaluation_task.txt"), "w", encoding="utf-8") as f:
    f.write(task_request)

print("Workspace initialized successfully.")
print(f"Key files created:")
print(f"  - procurement/2024/Q3/tender_docs/price_score_formula.txt")
print(f"  - procurement/2024/Q3/bid_submissions/bid_opening_record.txt")
print(f"  - procurement/2024/Q3/evaluation_committee/evaluation_task.txt")