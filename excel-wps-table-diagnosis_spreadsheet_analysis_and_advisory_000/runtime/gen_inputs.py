import os
import random
import csv

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create a deeply nested distractor directory structure ---

dirs = [
    "archive/2022/q1",
    "archive/2022/q2",
    "archive/2023/q3",
    "archive/2023/q4",
    "finance/invoices/pending",
    "finance/invoices/approved",
    "finance/payroll/2024",
    "hr/onboarding/templates",
    "hr/offboarding",
    "reports/monthly/jan",
    "reports/monthly/feb",
    "reports/annual",
    "tools/scripts",
    "tools/macros",
    "temp/uploads",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---

distractor_files = {
    "archive/2022/q1/expense_backup.txt": "Old backup - do not use\nEmployee: John\nTotal: 1200",
    "archive/2022/q2/summary_old.csv": "emp_id,total\n001,500\n002,750",
    "archive/2023/q3/reimbursement_notes.txt": "Note: Check for duplicates in Q3 submissions.",
    "archive/2023/q4/holiday_policy.txt": "All reimbursements over $500 require manager approval.",
    "finance/invoices/pending/inv_2024_001.txt": "Invoice pending review.\nVendor: TechCorp\nAmount: $2,300.00",
    "finance/invoices/approved/inv_2023_099.txt": "Approved. Reference: EXP-099.",
    "finance/payroll/2024/payroll_config.txt": "Pay cycle: Bi-weekly\nCurrency: USD",
    "hr/onboarding/templates/welcome_email.txt": "Welcome to the company! Please submit expenses via the portal.",
    "hr/offboarding/checklist.txt": "Return equipment\nSubmit final expenses\nSign NDA reminder",
    "reports/monthly/jan/jan_summary.txt": "January report - placeholder.",
    "reports/monthly/feb/feb_summary.txt": "February report - placeholder.",
    "reports/annual/annual_2023.txt": "Annual review complete.",
    "tools/scripts/dedup_macro.txt": "Sub RemoveDuplicates()\n  ' VBA placeholder\nEnd Sub",
    "tools/macros/vlookup_helper.txt": "Helper notes: Use VLOOKUP for employee matching.",
    "temp/uploads/raw_dump.txt": "Random raw data dump from upload portal.",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the MAIN PROBLEM FILE: messy expense report CSV ---
# This is the file the agent must diagnose.

expense_data = [
    ["Emp ID", "Employee Name", "Department", "Submission Date", "Expense Date", "Category", "Amount", "Currency", "Status", "Approved By", "Notes"],
    ["EMP-001", "Alice Johnson", "Engineering", "2024-03-15", "2024-03-10", "Travel", "1250.00", "USD", "Approved", "M. Chen", "Flight to NYC"],
    ["EMP-002", "bob smith", "MARKETING", "15/03/2024", "2024-03-09", "Meals", "89.5", "USD", "pending", "", "Team lunch"],
    ["EMP-003", "Carol White", "Engineering", "2024-03-15", "03-11-2024", "Hotel", "430", "usd", "Approved", "M. Chen", ""],
    ["EMP-001", "Alice Johnson", "Engineering", "2024-03-15", "2024-03-10", "Travel", "1250.00", "USD", "Approved", "M. Chen", "Flight to NYC"],  # duplicate
    ["EMP-004", "", "Finance", "2024-03-16", "2024-03-12", "Software", "299.99", "USD", "APPROVED", "L. Park", "Annual license"],
    ["EMP-005", "David Lee", "HR", "March 17, 2024", "2024-03-14", "Training", "750", "USD", "Rejected", "", "No receipt"],
    ["EMP-006", "Emma Davis", "Engineering", "2024-03-17", "2024/03/13", "Travel", "2100.50", "USD", "approved", "M. Chen", "Conference reg"],
    ["EMP-002", "bob smith", "MARKETING", "2024-03-18", "2024-03-15", "Meals", "45.00", "USD", "Pending", "", ""],
    ["EMP-007", "Frank Miller", "Finance", "2024-03-18", "2024-03-16", "Equipment", "N/A", "USD", "Pending", "L. Park", "Keyboard purchase"],
    ["EMP-008", "Grace Kim", "HR", "2024-03-19", "2024-03-17", "Travel", "980.00", "GBP", "Approved", "S. Patel", "London trip"],
    ["EMP-009", "Henry Brown", "Marketing", "2024-03-20", "2024-03-18", "Meals", "120.75", "USD", "pending", "", ""],
    ["EMP-010", "Irene Zhao", "Engineering", "2024-03-20", "", "Software", "59.99", "USD", "Approved", "M. Chen", "Plugin subscription"],
    ["EMP-011", "James O'Neil", "Finance", "2024-03-21", "2024-03-19", "Travel", "340.00", "EUR", "Approved", "L. Park", "Brussels conf"],
    ["EMP-005", "David Lee", "HR", "2024-03-21", "2024-03-14", "Training", "750", "USD", "Rejected", "", "Duplicate check"],
    ["EMP-012", "Karen Wu", "Marketing", "2024/03/22", "2024-03-20", "Meals", "67.30", "USD", "PENDING", "", ""],
    ["EMP-013", "Leo Nguyen", "IT", "2024-03-22", "2024-03-21", "Equipment", "1899.00", "USD", "Approved", "R. Torres", "Laptop"],
    ["EMP-003", "Carol White", "Engineering", "2024-03-23", "2024-03-22", "Travel", "215.00", "USD", "Pending", "", "Train ticket"],
    ["EMP-014", "Mia Patel", "HR", "2024-03-23", "2024-03-21", "Training", "500.00", "usd", "approved", "S. Patel", ""],
    ["EMP-015", "Noah Kim", "IT", "24-03-2024", "2024-03-22", "Software", "129.00", "USD", "pending", "", "IDE license"],
    ["EMP-016", "Olivia Stone", "Finance", "", "2024-03-23", "Meals", "88.00", "USD", "Approved", "L. Park", "Client dinner"],
]

csv_path = os.path.join(workspace, "expense_report_march2024.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(expense_data)

# --- Create the SKILL.md in workspace root ---

skill_md_content = """---
name: excel-wps-table-diagnosis
description: Diagnose spreadsheet structure and recommend practical Excel/WPS-compatible formulas and workflows for cleaning, lookup and matching, summarization, text and date cleanup, and common formula troubleshooting. Use when the user asks what formula to use, how to process a table, how to clean messy columns, how to match sheets, how to make a solution work in both Excel and WPS, or when headers and sample rows should be inspected before deciding what to do next.
---

# Excel/WPS Table Diagnosis

Use this skill when a spreadsheet task should start with the table itself, not with a guess at the formula.

## Core Approach

1. Inspect the input.

- Identify whether the user provided headers, sample rows, CSV content, or only a task description.
- If the structure is unclear, ask for the smallest missing detail that would change the recommendation.

2. Diagnose the table.

- Identify likely column types such as IDs, dates, amounts, names, status fields, phone numbers, or free text.
- Look for blanks, duplicates, mixed formats, unstable lookup keys, and columns that should be cleaned before formulas are applied.

3. Choose the most practical path.

- Prefer simple formulas when they are stable and readable.
- Prefer Excel and WPS compatible approaches over newer functions with weaker compatibility.
- Prefer helper columns when a single long formula would be fragile.
- Recommend built-in spreadsheet tools when they are a better fit than formulas.

4. Present a clear recommendation.

- State what the table appears to contain.
- State what should be done first.
- Recommend the formula or workflow.
- Mention compatibility notes for Excel and WPS.
- Provide a fallback when the preferred formula may not work everywhere.

5. Pause before execution.

- If the next step would directly modify a workbook, add helper columns, rewrite formulas, or otherwise move from diagnosis into execution, ask for confirmation first.
- Once the user agrees, continue with the concrete formulas, helper columns, or execution steps instead of repeating the analysis.
- If the scope is already clear, finish the approved execution step before suggesting extra optional follow-up work.

## Priorities

- Diagnose before suggesting formulas.
- Prefer maintainability over cleverness.
- Treat compatibility as an early constraint.
- Do not force everything into one formula.
- Do not make direct spreadsheet changes without user confirmation.

## Output Shape

Keep the response close to this shape:

### Diagnosis

- what the table likely contains
- what looks inconsistent or risky

### Recommendation

- what to do first
- which formula or method to use

### Execution

- what can be done immediately after approval
- which formulas, helper columns, or spreadsheet steps should be applied

### Compatibility

- whether it should work in Excel
- whether it should work in WPS
- what fallback to use if needed

### Notes

- where to place the formula
- whether helper columns or built-in tools would be easier

## References

- Read `WORKFLOW.md` for the longer working notes.
- Read `docs/use-cases.md` for common task shapes.
- Read `examples/README.md` for example inputs and outputs.
"""

with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md_content)

# --- Create output placeholder directory ---
os.makedirs(os.path.join(workspace, "output"), exist_ok=True)

print("Workspace setup complete.")
print(f"Main CSV: {csv_path}")