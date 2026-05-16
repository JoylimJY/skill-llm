import os
import json
import random

random.seed(42)

# Create a realistic, deeply nested workspace
dirs = [
    "workspace/ai_assistant/routing",
    "workspace/ai_assistant/logs",
    "workspace/ai_assistant/config",
    "workspace/ai_assistant/sessions",
    "workspace/company/hr",
    "workspace/company/it_ops",
    "workspace/company/finance",
    "workspace/reports/monthly",
    "workspace/reports/quarterly",
    "workspace/backups/old_sessions",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---
with open("workspace/ai_assistant/config/legacy_config.yaml", "w") as f:
    f.write("""# Legacy routing config - DEPRECATED
model_v1: gpt-3.5
model_v2: gpt-4
threshold: 0.7
""")

with open("workspace/ai_assistant/logs/system.log", "w") as f:
    f.write("""2024-01-15 09:00:01 INFO System started
2024-01-15 09:01:22 INFO Session pool initialized
2024-01-15 09:05:44 WARN Routing timeout on session-882
2024-01-15 10:12:09 INFO Daily summary generated
""")

with open("workspace/ai_assistant/sessions/session_template.json", "w") as f:
    json.dump({"session_id": "TEMPLATE", "model": "UNSET", "status": "idle"}, f, indent=2)

with open("workspace/company/hr/employee_handbook.txt", "w") as f:
    f.write("Employee Handbook v3.2\nSection 4: IT Support Requests\nAll AI assistant requests must be logged.\n")

with open("workspace/company/it_ops/infrastructure_notes.txt", "w") as f:
    f.write("Infrastructure Notes\nServer rack A: 12 nodes\nAI assistant endpoint: internal-ai.company.local\n")

with open("workspace/company/finance/budget_2024.txt", "w") as f:
    f.write("AI tooling budget 2024: $45,000\nCost per Haiku call: $0.003\nCost per Sonnet call: $0.015\nCost per Opus call: $0.075\n")

with open("workspace/reports/monthly/jan_summary.txt", "w") as f:
    f.write("January AI Usage Summary\nTotal requests: 8420\nEscalations: 312\n")

with open("workspace/reports/quarterly/q4_review.txt", "w") as f:
    f.write("Q4 Review\nModel utilization: Haiku 78%, Sonnet 19%, Opus 3%\n")

with open("workspace/backups/old_sessions/backup_manifest.txt", "w") as f:
    f.write("Backup created: 2024-01-01\nSessions archived: 15,332\n")

with open("workspace/ai_assistant/routing/routing_notes.md", "w") as f:
    f.write("""# Routing Notes (Archived)
These are OLD notes from the previous system. DO NOT USE.
Model A = fast
Model B = smart
Model C = expensive
""")

with open("workspace/ai_assistant/config/feature_flags.json", "w") as f:
    json.dump({"enable_caching": True, "fallback_on_timeout": False, "max_retries": 3}, f, indent=2)

# --- THE ACTUAL TASK INPUT ---
# A file with 8 employee requests that need to be routed to the correct AI model tier
requests_data = {
    "batch_id": "BATCH-2024-0203",
    "submitted_by": "ops_manager@company.local",
    "description": "Batch of employee AI assistant requests requiring routing for cost audit.",
    "requests": [
        {
            "id": "REQ-001",
            "employee": "alice@company.local",
            "request": "What is the capital of France?"
        },
        {
            "id": "REQ-002",
            "employee": "bob@company.local",
            "request": "Write a Python script to parse our server logs and extract all ERROR lines into a CSV file."
        },
        {
            "id": "REQ-003",
            "employee": "carol@company.local",
            "request": "Analyze why our Q3 sales dropped by 22% compared to Q2 and provide a detailed breakdown."
        },
        {
            "id": "REQ-004",
            "employee": "dave@company.local",
            "request": "Who is the current CEO of our company?"
        },
        {
            "id": "REQ-005",
            "employee": "eve@company.local",
            "request": "We need to make a critical architectural decision: should we migrate our entire monolith to microservices or adopt a modular monolith pattern? This will affect our entire engineering org for the next 5 years."
        },
        {
            "id": "REQ-006",
            "employee": "frank@company.local",
            "request": "Compare the pros and cons of PostgreSQL vs MongoDB for our new data warehouse project."
        },
        {
            "id": "REQ-007",
            "employee": "grace@company.local",
            "request": "Where is the nearest coffee machine on floor 3?"
        },
        {
            "id": "REQ-008",
            "employee": "heidi@company.local",
            "request": "Perform deep research into the long-term implications of adopting a zero-trust security model across all our cloud infrastructure, including vendor lock-in risks, compliance impact, and a multi-year rollout plan."
        }
    ]
}

with open("workspace/ai_assistant/routing/pending_requests.json", "w") as f:
    json.dump(requests_data, f, indent=2)

print("Workspace generated successfully.")
print("Task input file: workspace/ai_assistant/routing/pending_requests.json")