import os
import random

random.seed(42)

workspace = "/workspace"

# --- Create deeply nested distractor directory structure ---

dirs = [
    "project/legacy/archive/2021",
    "project/legacy/archive/2022",
    "project/legacy/reports",
    "project/legacy/configs",
    "project/src/utils",
    "project/src/models",
    "project/src/pipelines",
    "project/tests/unit",
    "project/tests/integration",
    "project/docs/api",
    "project/docs/guides",
    "data/raw/uploads",
    "data/raw/incoming",
    "data/processed",
    "data/quarantine",
    "logs/2024/01",
    "logs/2024/02",
    "scripts/maintenance",
    "scripts/deployment",
    "configs/env",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---

distractor_files = {
    "project/legacy/archive/2021/summary.txt": "Annual data summary for 2021. See attached spreadsheets.",
    "project/legacy/archive/2022/summary.txt": "Annual data summary for 2022. Migration incomplete.",
    "project/legacy/reports/q4_report.md": "# Q4 Report\n\nData quality issues found in batch 7 and batch 12.",
    "project/legacy/configs/old_pipeline.yaml": "pipeline:\n  name: legacy_etl\n  version: 0.3\n  deprecated: true\n",
    "project/src/utils/helpers.py": "# Utility helpers\ndef noop():\n    pass\n",
    "project/src/models/schema.py": "# Data schema definitions\nSCHEMA_VERSION = '2.1'\n",
    "project/src/pipelines/etl_v1.py": "# Legacy ETL pipeline\n# TODO: refactor\nimport csv\n",
    "project/tests/unit/test_helpers.py": "import unittest\nclass TestHelpers(unittest.TestCase):\n    def test_noop(self):\n        pass\n",
    "project/tests/integration/test_pipeline.py": "# Integration tests - currently broken\n# Skipped due to data format changes\n",
    "project/docs/api/endpoints.md": "# API Endpoints\n\n## /upload\nAccepts CSV files for processing.\n",
    "project/docs/guides/onboarding.md": "# Onboarding Guide\n\nWelcome to the data team. Follow the setup instructions.",
    "data/processed/.gitkeep": "",
    "data/quarantine/rejected_batch_003.txt": "Batch 003 rejected: 47 invalid rows, missing customer_id on rows 12,45,89",
    "logs/2024/01/pipeline.log": "[INFO] 2024-01-15 Pipeline started\n[ERROR] 2024-01-15 Row 234: type mismatch\n[INFO] 2024-01-15 Pipeline finished with 3 errors\n",
    "logs/2024/02/pipeline.log": "[INFO] 2024-02-01 Pipeline started\n[WARN] 2024-02-01 Encoding issue detected in file orders_feb.csv\n[INFO] 2024-02-01 Pipeline finished\n",
    "scripts/maintenance/cleanup.sh": "#!/bin/bash\n# Cleanup old temp files\nfind /tmp -name '*.tmp' -delete\n",
    "scripts/deployment/deploy.sh": "#!/bin/bash\n# Deployment script\necho 'Deploy not implemented'\n",
    "configs/env/production.env": "DB_HOST=prod-db.internal\nDB_PORT=5432\nMAX_WORKERS=8\n",
    "configs/env/staging.env": "DB_HOST=staging-db.internal\nDB_PORT=5432\nMAX_WORKERS=2\n",
    "project/src/utils/validators.py": "# Placeholder validators\n# FIXME: not implemented\ndef validate_row(row):\n    return True\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- Create the actual problem: messy CSV files in data/raw/uploads ---

# CSV 1: customers.csv — has missing values, type mismatches, duplicate rows
customers_csv = """customer_id,name,age,email,signup_date,annual_spend
1001,Alice Johnson,34,alice@example.com,2022-03-15,1200.50
1002,Bob Smith,twenty-two,bob@example.com,2022-04-01,850.00
1003,Carol White,29,carol@example.com,2022-04-10,
1004,Dave Brown,,dave@example.com,2022-05-20,3400.75
1005,Eve Davis,45,not-an-email,2022-06-01,2100.00
1006,Frank Lee,31,frank@example.com,invalid-date,980.25
1001,Alice Johnson,34,alice@example.com,2022-03-15,1200.50
1007,Grace Kim,28,grace@example.com,2022-07-15,1750.00
1008,Henry Park,-5,henry@example.com,2022-08-01,630.00
1009,Ivy Chen,33,ivy@example.com,2022-08-22,2890.50
1010,,41,noname@example.com,2022-09-01,500.00
1009,Ivy Chen,33,ivy@example.com,2022-08-22,2890.50
1011,Jack Wu,38,jack@example.com,2023-01-10,4200.00
1012,Karen Ng,27,karen@example.com,2023-02-14,1100.75
"""

with open(os.path.join(workspace, "data/raw/uploads/customers.csv"), "w", encoding="utf-8") as f:
    f.write(customers_csv)

# CSV 2: orders.csv — has negative quantities, missing order_id, mixed currency symbols
orders_csv = """order_id,customer_id,product_name,quantity,unit_price,order_date,status
ORD-001,1001,Widget A,5,$12.99,2023-01-05,completed
ORD-002,1002,Gadget B,-2,8.50,2023-01-06,completed
ORD-003,9999,Widget A,3,12.99,2023-01-07,completed
,1004,Gadget B,10,8.50,2023-01-08,pending
ORD-005,1005,Widget C,0,€45.00,2023-01-09,completed
ORD-006,1006,Widget A,2,12.99,2023-01-10,
ORD-007,1007,Gadget B,1,8.50,2023-01-11,completed
ORD-001,1001,Widget A,5,12.99,2023-01-05,completed
ORD-008,1008,Widget C,4,45.00,2023-02-01,completed
ORD-009,1003,Widget A,7,12.99,2023-02-03,shipped
ORD-010,1010,Gadget B,3,8.50,2023-02-10,pending
ORD-011,1012,Widget C,2,45.00,2023-03-01,completed
"""

with open(os.path.join(workspace, "data/raw/uploads/orders.csv"), "w", encoding="utf-8") as f:
    f.write(orders_csv)

# --- Incomplete stub from previous attempt (to show context, not a solution) ---
stub_py = """# data_auditor.py - INCOMPLETE STUB
# This file was started but abandoned. DO NOT USE AS-IS.

import csv

def load_csv(filepath):
    # TODO: implement
    pass

def check_duplicates(data):
    # TODO: implement
    pass

# main() not implemented
"""

with open(os.path.join(workspace, "data/raw/uploads/data_auditor_STUB.py"), "w", encoding="utf-8") as f:
    f.write(stub_py)

# --- A broken requirements note (non-functional, intentionally vague) ---
broken_req = """Requirements note (draft, incomplete):
- Script should process CSV files
- Find bad data somehow
- Output a report
- Maybe check for duplicates?
(No criteria defined, no test methods, no completion standards)
"""

with open(os.path.join(workspace, "data/requirements_draft.txt"), "w", encoding="utf-8") as f:
    f.write(broken_req)

print("Workspace initialized successfully.")