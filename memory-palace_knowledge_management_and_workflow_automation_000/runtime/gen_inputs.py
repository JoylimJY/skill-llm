import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Deep directory structure with distractor files ---
dirs = [
    "projects/alpha/docs",
    "projects/alpha/src",
    "projects/beta/retrospectives",
    "projects/beta/logs",
    "clients/acme/briefs",
    "clients/acme/feedback",
    "clients/globex/notes",
    "onboarding/checklists",
    "onboarding/templates",
    "internal/processes",
    "internal/policies",
    "archive/2022",
    "archive/2023",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "projects/alpha/docs/architecture.md": "# Alpha Architecture\nMicroservices with event sourcing. Database: PostgreSQL 14.",
    "projects/alpha/docs/api_spec.yaml": "openapi: 3.0.0\ninfo:\n  title: Alpha API\npaths:\n  /health:\n    get:\n      summary: Health check",
    "projects/alpha/src/config.json": json.dumps({"env": "production", "debug": False, "version": "2.1.0"}),
    "projects/beta/retrospectives/sprint_12.txt": "What went well: CI pipeline speed improved.\nWhat to improve: Code review turnaround too slow.",
    "projects/beta/retrospectives/sprint_13.txt": "What went well: Zero production incidents.\nWhat to improve: Test coverage still below 80%.",
    "projects/beta/logs/errors_2024_q1.log": "ERROR 2024-01-15 DB connection pool exhausted\nERROR 2024-02-03 Memory leak in worker process",
    "clients/acme/briefs/project_brief_v3.md": "# ACME Project Brief\nObjective: Migrate legacy ERP to cloud.\nTimeline: 18 months.",
    "clients/acme/feedback/survey_results.csv": "question,score\nResponse time,4.2\nCode quality,3.8\nDocumentation,2.9",
    "clients/globex/notes/kickoff_notes.txt": "Client prefers weekly syncs. Main contact: Sarah Chen. Sensitive about deadlines.",
    "onboarding/checklists/new_engineer.md": "1. Setup dev environment\n2. Read architecture docs\n3. Shadow senior engineer for 2 days",
    "onboarding/templates/welcome_email.txt": "Welcome to the team! Please complete onboarding checklist within your first week.",
    "internal/processes/incident_response.md": "# Incident Response Process\n1. Alert on-call\n2. Create incident channel\n3. Postmortem within 48h",
    "internal/policies/code_review.md": "All PRs require 2 approvals. Security-sensitive changes need a security review.",
    "archive/2022/project_closeout.txt": "Project Zeus completed. Delivered 2 weeks late due to scope creep.",
    "archive/2023/annual_review.txt": "Revenue up 23%. Client retention 91%. Main challenge: hiring senior engineers.",
}
for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE ACTUAL TASK INPUT: Structured knowledge data to be loaded ---
# This is the "briefing document" the agent should read to know what to store
lessons_data = [
    {
        "id": "L001",
        "content": "When PostgreSQL connection pools are exhausted under load, increasing max_connections alone is insufficient; PgBouncer must be configured as a pooler to handle burst traffic effectively.",
        "category": "development",
        "applicability": "Backend services using PostgreSQL under high concurrency",
        "source": "project-alpha-incident-2024",
        "verify_count": 2  # must be verified this many times with effective=true
    },
    {
        "id": "L002", 
        "content": "Clients who prefer weekly syncs become dissatisfied if the meeting is shortened without prior notice; always send agenda 24h in advance.",
        "category": "communication",
        "applicability": "Client-facing projects with regular sync cadence",
        "source": "client-globex-feedback",
        "verify_count": 2
    },
    {
        "id": "L003",
        "content": "Scope creep delayed Project Zeus by 2 weeks; future projects must enforce a formal change request process with impact assessment before any scope addition.",
        "category": "operations",
        "applicability": "All client projects with fixed-price contracts",
        "source": "project-zeus-closeout-2022",
        "verify_count": 1  # only 1 verification - should NOT be marked verified
    },
]

preferences_data = [
    {
        "content": "Engineering team uses dark mode in all IDEs and prefers terminal-based workflows over GUI tools.",
        "location": "preferences",
        "tags": ["ui", "tooling", "engineering"],
        "importance": 0.8,
        "type": "preference"
    },
    {
        "content": "Code reviews must be completed within 24 hours; the team has agreed this is a non-negotiable SLA.",
        "location": "preferences", 
        "tags": ["process", "code-review"],
        "importance": 0.9,
        "type": "decision"
    },
    {
        "content": "TypeScript is the mandatory language for all new frontend and backend Node.js services.",
        "location": "preferences",
        "tags": ["technology", "standards"],
        "importance": 0.85,
        "type": "decision"
    },
]

facts_data = [
    {
        "content": "ACME client's main contact is Sarah Chen; she is sensitive about deadline slippage and requires proactive communication when risks emerge.",
        "location": "clients",
        "tags": ["acme", "client-relations", "communication"],
        "importance": 0.75,
        "type": "fact"
    },
    {
        "content": "Current test coverage target is 80%; projects below this threshold are flagged in sprint reviews.",
        "location": "quality",
        "tags": ["testing", "standards", "ci"],
        "importance": 0.7,
        "type": "fact"
    },
]

# Write the briefing document (the agent's primary input)
briefing = {
    "task": "AI Assistant Knowledge Base Initialization",
    "description": "Load institutional knowledge into the AI assistant before deployment. The data below must be stored and validated according to our knowledge management policy.",
    "lessons_to_record_and_verify": lessons_data,
    "preferences_and_decisions": preferences_data,
    "key_facts": facts_data,
    "post_load_requirements": {
        "simulate_access": {
            "description": "After loading, simulate that the code-review decision and the ACME client fact have each been accessed 3 times by recording their access.",
            "targets": ["code-review decision memory", "ACME client fact memory"]
        },
        "report_file": "knowledge_base_report.json",
        "report_contents": [
            "stats: full memory statistics snapshot",
            "frequently_accessed: top 5 most frequently accessed memories",
            "verified_experiences: list of all verified experiences (those with 2+ positive verifications)",
            "unverified_experiences: list of experiences that failed to reach verified status"
        ]
    }
}

with open(os.path.join(workspace, "onboarding/ai_assistant_briefing.json"), "w") as f:
    json.dump(briefing, f, indent=2, ensure_ascii=False)

print("Workspace generated successfully.")
print(f"Key file: {workspace}/onboarding/ai_assistant_briefing.json")