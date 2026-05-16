import json
import os
import random

random.seed(42)

# Create the workspace directory structure
base = "/workspace"
os.makedirs(base, exist_ok=True)

# Create deeply nested distractor structure
dirs = [
    "engineering/backend/api",
    "engineering/backend/database",
    "engineering/frontend/components",
    "engineering/frontend/styling",
    "engineering/infra/ci_cd",
    "engineering/infra/monitoring",
    "product/specs",
    "product/roadmap",
    "hr/hiring",
    "finance/q3_budget",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files
distractor_files = {
    "engineering/backend/api/migration_notes.txt": """
API v1 to v2 migration - partial notes
Started: 2024-01-15
Status: IN PROGRESS (nobody assigned currently)
Blockers: auth service refactor not done
""",
    "engineering/backend/database/slow_query_log.txt": """
2024-03-01 14:22:01 [WARN] Query took 4200ms: SELECT * FROM orders JOIN users...
2024-03-01 14:22:45 [WARN] Query took 3800ms: SELECT * FROM products WHERE...
2024-03-02 09:11:00 [WARN] Query took 5100ms: SELECT * FROM analytics_events...
Total slow queries this week: 847
""",
    "engineering/frontend/components/tech_debt.md": """
# Frontend Tech Debt
- jQuery still used in 3 legacy pages
- No unit tests on checkout flow
- Bundle size: 4.2MB (target: <1MB)
""",
    "engineering/infra/ci_cd/pipeline_failures.log": """
build_failed: 2024-03-01 - reason: flaky test in auth module
build_failed: 2024-03-02 - reason: docker registry timeout
build_failed: 2024-03-03 - reason: flaky test in auth module
build_failed: 2024-03-04 - reason: flaky test in payment module
""",
    "engineering/infra/monitoring/alerts.txt": """
CRITICAL: Database CPU > 90% - 3 times last week
WARNING: API p99 latency > 2s - daily occurrence
INFO: Memory usage trending up 5% per week
""",
    "product/specs/q2_features.txt": """
Q2 Feature Requests (from sales):
1. Multi-tenant dashboard - URGENT (3 enterprise deals blocked)
2. CSV export functionality - nice to have
3. SSO/SAML integration - 2 enterprise deals asking
4. Webhook notifications - developer customers requesting
""",
    "product/roadmap/priorities_draft.txt": """
Draft priority list (not finalized):
- Feature: Multi-tenant dashboard (HIGH)
- Infra: Security audit + fixes (CRITICAL - compliance)
- Tech: API v2 migration (MEDIUM)
- Tech: DB optimization (HIGH - performance)
- Infra: CI/CD stability (MEDIUM)
- Feature: SSO integration (HIGH)
- Tech: Frontend bundle optimization (LOW)
- Infra: Observability/tracing setup (MEDIUM)
NOTE: Everything is high priority. Team is burned out.
""",
    "hr/hiring/open_roles.txt": """
Open Engineering Roles:
- Senior Backend Engineer (posted 3 months, no hire yet)
- DevOps Engineer (posted 6 weeks, 2 final round candidates)
Current team: 3 engineers (Alice, Bob, Carlos) + 1 CTO
""",
    "finance/q3_budget/constraints.txt": """
Engineering budget Q3:
- Cloud infrastructure: $8,000/month (currently $11,200 - OVER BUDGET)
- No contractor budget approved
- Tool licenses: $500/month available
""",
    "engineering/backend/api/openapi_v1_spec.json": json.dumps({
        "openapi": "3.0.0",
        "info": {"title": "Legacy API v1", "version": "1.0.0"},
        "paths": {
            "/users": {"get": {"deprecated": True}},
            "/orders": {"get": {"deprecated": True}},
        }
    }, indent=2),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(base, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# THE CORE PROBLEM INPUT: messy backlog
backlog = {
    "team": {
        "name": "Acme SaaS Engineering",
        "available_engineers": 3,
        "engineers": ["Alice", "Bob", "Carlos"],
        "sprint_capacity_points": 42,
        "note": "All engineers currently context-switching across multiple tasks. Velocity has dropped 40% in last 6 weeks."
    },
    "current_status": "CRITICAL: Team is spread across 8 concurrent initiatives. Nothing is completing. Leadership is asking for results.",
    "initiatives": [
        {
            "id": "INIT-001",
            "title": "API v2 Migration (REST → GraphQL)",
            "description": "Migrate all endpoints from legacy REST API v1 to new GraphQL API v2. Required by enterprise clients.",
            "effort_points": 34,
            "urgency": "medium",
            "business_impact": "unblocks 2 enterprise deals worth $180k ARR",
            "dependencies": ["INIT-003"],
            "blocks": ["INIT-006"],
            "isolation_score": 2,
            "current_progress_pct": 15,
            "readiness": {
                "spec_complete": False,
                "team_has_expertise": True,
                "blocker": "Depends on auth service refactor (INIT-003) being done first"
            }
        },
        {
            "id": "INIT-002",
            "title": "Database Query Optimization",
            "description": "Identify and fix top 20 slow queries. Add indexes. Reduce avg query time from 4.2s to <200ms.",
            "effort_points": 13,
            "urgency": "high",
            "business_impact": "fixes customer complaints, reduces cloud costs by ~$2000/month, unblocks INIT-007",
            "dependencies": [],
            "blocks": ["INIT-007"],
            "isolation_score": 8,
            "current_progress_pct": 0,
            "readiness": {
                "spec_complete": True,
                "team_has_expertise": True,
                "blocker": None
            }
        },
        {
            "id": "INIT-003",
            "title": "Auth Service Refactor (JWT → OAuth2)",
            "description": "Replace homegrown JWT auth with proper OAuth2. Required for SSO feature and API v2.",
            "effort_points": 21,
            "urgency": "high",
            "business_impact": "prerequisite for INIT-001 and INIT-006; fixes 3 known security vulnerabilities",
            "dependencies": [],
            "blocks": ["INIT-001", "INIT-006"],
            "isolation_score": 6,
            "current_progress_pct": 30,
            "readiness": {
                "spec_complete": True,
                "team_has_expertise": True,
                "blocker": None
            }
        },
        {
            "id": "INIT-004",
            "title": "Security Audit & Compliance Fixes",
            "description": "External security audit scheduled for Q3. Must fix all critical findings before audit date.",
            "effort_points": 18,
            "urgency": "critical",
            "business_impact": "SOC2 compliance required for 5 enterprise pipeline deals; regulatory risk",
            "dependencies": ["INIT-003"],
            "blocks": [],
            "isolation_score": 3,
            "current_progress_pct": 0,
            "readiness": {
                "spec_complete": False,
                "team_has_expertise": False,
                "blocker": "Needs auth refactor done first. No one on team has done SOC2 before - need external guidance."
            }
        },
        {
            "id": "INIT-005",
            "title": "CI/CD Pipeline Stabilization",
            "description": "Fix flaky tests causing 60% build failure rate. Add proper test isolation and retry logic.",
            "effort_points": 8,
            "urgency": "medium",
            "business_impact": "restores team velocity, reduces deployment fear, saves ~3hrs/week per engineer",
            "dependencies": [],
            "blocks": [],
            "isolation_score": 9,
            "current_progress_pct": 0,
            "readiness": {
                "spec_complete": True,
                "team_has_expertise": True,
                "blocker": None
            }
        },
        {
            "id": "INIT-006",
            "title": "SSO/SAML Integration",
            "description": "Add SSO login for enterprise customers. Two deals explicitly require this feature.",
            "effort_points": 16,
            "urgency": "high",
            "business_impact": "unblocks 2 enterprise deals worth $240k ARR combined",
            "dependencies": ["INIT-001", "INIT-003"],
            "blocks": [],
            "isolation_score": 2,
            "current_progress_pct": 0,
            "readiness": {
                "spec_complete": False,
                "team_has_expertise": False,
                "blocker": "Requires INIT-001 and INIT-003 to be complete. Spec not finalized."
            }
        },
        {
            "id": "INIT-007",
            "title": "Observability & Distributed Tracing Setup",
            "description": "Implement OpenTelemetry tracing across all services. Set up Grafana dashboards.",
            "effort_points": 11,
            "urgency": "low",
            "business_impact": "improves debugging speed, helps with INIT-002 long-term, no direct revenue impact",
            "dependencies": ["INIT-002"],
            "blocks": [],
            "isolation_score": 5,
            "current_progress_pct": 0,
            "readiness": {
                "spec_complete": True,
                "team_has_expertise": True,
                "blocker": "Should follow INIT-002 for maximum value"
            }
        },
        {
            "id": "INIT-008",
            "title": "Multi-Tenant Dashboard Feature",
            "description": "Build per-tenant analytics dashboard. Sales team says 3 enterprise deals are blocked on this.",
            "effort_points": 28,
            "urgency": "high",
            "business_impact": "unblocks 3 enterprise deals worth $310k ARR",
            "dependencies": ["INIT-002"],
            "blocks": [],
            "isolation_score": 4,
            "current_progress_pct": 5,
            "readiness": {
                "spec_complete": False,
                "team_has_expertise": True,
                "blocker": "DB performance (INIT-002) must improve first or dashboard will be unusable. Spec 60% done."
            }
        }
    ],
    "constraints": [
        "Only 3 engineers available, no hiring in next 3 months",
        "Sprint capacity: 42 story points per 2-week sprint",
        "Cloud bill must be reduced (currently 40% over budget)",
        "Enterprise pipeline worth $730k ARR is stalled due to technical gaps",
        "Team morale is low due to constant context-switching",
        "External security audit date is fixed: 8 weeks from now"
    ]
}

with open(os.path.join(base, "backlog.json"), "w", encoding="utf-8") as f:
    json.dump(backlog, f, indent=2, ensure_ascii=False)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files)} distractor files + backlog.json")