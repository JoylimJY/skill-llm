import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a deeply nested distractor directory structure (logistics company context)
dirs = [
    "ops/fulfillment/warehouse-A/inbound",
    "ops/fulfillment/warehouse-A/outbound",
    "ops/fulfillment/warehouse-B/inbound",
    "ops/fulfillment/warehouse-B/outbound",
    "ops/capacity-planning/q3-2025",
    "ops/capacity-planning/q4-2025",
    "finance/budget/2025/approved",
    "finance/budget/2025/draft",
    "hr/headcount/engineering",
    "hr/headcount/operations",
    "tech/infra/networking",
    "tech/infra/monitoring",
    "tech/apps/wms",
    "tech/apps/tms",
    "legal/contracts/vendors",
    "legal/compliance/audits",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "ops/fulfillment/warehouse-A/inbound/manifest_2025_06.csv": "order_id,sku,qty\n10001,SKU-A,50\n10002,SKU-B,120",
    "ops/fulfillment/warehouse-A/outbound/shipment_log.txt": "2025-06-01: 340 units shipped\n2025-06-02: 290 units shipped",
    "ops/fulfillment/warehouse-B/inbound/backlog_report.txt": "Backlog as of 2025-06-10: 1,200 units pending",
    "ops/capacity-planning/q3-2025/assumptions.txt": "Growth rate: 15%\nPeak days: Prime Day, Black Friday",
    "ops/capacity-planning/q4-2025/draft_capacity_model.csv": "month,projected_volume,current_capacity,gap\nOct,50000,42000,8000\nNov,75000,42000,33000\nDec,90000,42000,48000",
    "finance/budget/2025/draft/capex_requests.txt": "Forklift upgrade: $120k\nSorter belt replacement: $85k",
    "finance/budget/2025/approved/headcount_budget.txt": "Approved FTEs: 12 operations, 4 engineering",
    "hr/headcount/operations/open_roles.txt": "Warehouse Supervisor x2\nInbound Lead x1\nOutbound Coordinator x3",
    "hr/headcount/engineering/current_team.txt": "Alice (WMS lead), Bob (TMS), Carol (Infra), Dave (Data)",
    "tech/infra/networking/topology.txt": "VPC: 10.0.0.0/16\nSubnets: 10.0.1.0/24 (ops), 10.0.2.0/24 (mgmt)",
    "tech/infra/monitoring/alerts.txt": "WMS latency >2s: 3 incidents last week\nSorter downtime: 4h on 2025-06-09",
    "tech/apps/wms/known_issues.txt": "Issue #4421: Inbound scan failure rate 2.3%\nIssue #4398: Putaway routing error on cold storage",
    "tech/apps/tms/integration_notes.txt": "Carrier API v2 migration due: 2025-08-01\nFallback to v1 disabled after migration",
    "legal/contracts/vendors/sorter_vendor_sla.txt": "Uptime SLA: 99.5%\nPenalty: $500/hr beyond 4h downtime",
    "legal/compliance/audits/2025_q1_findings.txt": "Finding 1: Cycle count frequency below threshold\nFinding 2: Hazmat labeling gap in cold storage",
    "ops/fulfillment/warehouse-B/outbound/carrier_performance.csv": "carrier,on_time_pct,damage_pct\nFedEx,94.2,0.8\nUPS,91.5,1.1\nDHL,88.3,2.0",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# The OpenGoat mock server state file — pre-seeded with org hierarchy and an existing in-progress task
# This is loaded by the mock server at startup
opengoat_state = {
    "agents": {
        "amazon-senior-manager": {
            "agentId": "amazon-senior-manager",
            "name": "Senior Manager – Fulfillment Ops",
            "role": "senior-manager",
            "managerId": None,
            "directReports": ["logistics-ops-lead", "wms-engineering-lead"],
        },
        "logistics-ops-lead": {
            "agentId": "logistics-ops-lead",
            "name": "Ops Lead – Logistics",
            "role": "ops-lead",
            "managerId": "amazon-senior-manager",
            "directReports": ["warehouse-supervisor-1", "warehouse-supervisor-2"],
        },
        "wms-engineering-lead": {
            "agentId": "wms-engineering-lead",
            "name": "Engineering Lead – WMS",
            "role": "engineering-lead",
            "managerId": "amazon-senior-manager",
            "directReports": ["wms-dev-1", "wms-dev-2"],
        },
        "warehouse-supervisor-1": {
            "agentId": "warehouse-supervisor-1",
            "name": "Warehouse Supervisor – Site A",
            "role": "supervisor",
            "managerId": "logistics-ops-lead",
            "directReports": [],
        },
        "warehouse-supervisor-2": {
            "agentId": "warehouse-supervisor-2",
            "name": "Warehouse Supervisor – Site B",
            "role": "supervisor",
            "managerId": "logistics-ops-lead",
            "directReports": [],
        },
        "wms-dev-1": {
            "agentId": "wms-dev-1",
            "name": "WMS Developer – Inbound",
            "role": "developer",
            "managerId": "wms-engineering-lead",
            "directReports": [],
        },
        "wms-dev-2": {
            "agentId": "wms-dev-2",
            "name": "WMS Developer – Outbound",
            "role": "developer",
            "managerId": "wms-engineering-lead",
            "directReports": [],
        },
        # Intentional distractor: NOT in the reporting tree
        "finance-analyst": {
            "agentId": "finance-analyst",
            "name": "Finance Analyst",
            "role": "analyst",
            "managerId": "cfo",
            "directReports": [],
        },
        "cfo": {
            "agentId": "cfo",
            "name": "CFO",
            "role": "executive",
            "managerId": None,
            "directReports": ["finance-analyst"],
        },
    },
    "tasks": {
        "TASK-001": {
            "taskId": "TASK-001",
            "title": "Investigate: WMS inbound scan failure spike",
            "description": "Context:\n- Inbound scan failure rate rose to 2.3% in June\n\nDeliverable:\n- Root cause analysis document\n\nAcceptance criteria:\n- Root cause identified and documented\n- Remediation plan proposed\n\nConstraints:\n- Must complete before Q3 peak prep",
            "status": "doing",
            "assignedTo": "wms-dev-1",
            "project": "tech/apps/wms",
            "blockers": [],
            "artifacts": [],
            "worklogs": [],
            "createdBy": "amazon-senior-manager",
        }
    },
    "task_id_counter": 2,
}

state_path = os.path.join(workspace, "opengoat_state.json")
with open(state_path, "w") as f:
    json.dump(opengoat_state, f, indent=2)

print("Workspace and OpenGoat state initialized.")
print(f"State file: {state_path}")