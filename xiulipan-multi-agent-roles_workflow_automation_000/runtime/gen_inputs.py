import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure with distractor files ---
dirs = [
    "docs/legal-ops",
    "docs/hr",
    "config/legacy",
    "config/staging",
    "config/templates",
    "agents/old-team",
    "agents/proto",
    "logs/2023",
    "logs/2024",
    "notes/interviews",
    "notes/specs",
    "scratch",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files that look plausible but are wrong/incomplete ---

# Distractor 1: Old broken config with wrong schema (flat bindings, no peer object)
old_config = {
    "agents": [  # Wrong: should be {"list": [...]}
        {"id": "old_planner", "role": "planner"}
    ],
    "bindings": [
        {"agentId": "old_planner", "channel": "any", "peer": "direct"}  # Wrong: peer should be object
    ]
}
with open(os.path.join(WORKSPACE, "config/legacy/team_config_v1.json"), "w") as f:
    json.dump(old_config, f, indent=2)

# Distractor 2: Partial template missing required fields
partial_template = {
    "agents": {
        "list": [
            {
                "id": "example_agent",
                "workspace": "/workspaces/example",
                # Missing agentDir
                "config": {
                    "role": "Strategic Planner"
                    # Missing expertise and responsibilities
                }
            }
        ]
    }
}
with open(os.path.join(WORKSPACE, "config/templates/agent_template_partial.json"), "w") as f:
    json.dump(partial_template, f, indent=2)

# Distractor 3: Bindings with contains as string (wrong)
wrong_bindings = {
    "bindings": [
        {
            "agentId": "reviewer",
            "match": {
                "channel": "any",
                "text": {"contains": "document"}  # Wrong: should be array
            }
        }
    ]
}
with open(os.path.join(WORKSPACE, "config/staging/bindings_draft.json"), "w") as f:
    json.dump(wrong_bindings, f, indent=2)

# Distractor 4: Prose requirements document for the legal ops team
requirements_prose = """Legal Ops AI Team - Agent Requirements
=======================================

We are building a document review platform for litigation support.

TEAM COMPOSITION REQUIREMENTS:
--------------------------------

1. CASE STRATEGY LEAD (orchestrator)
   - Must receive ALL direct messages (no keyword filtering needed)
   - Role type: Strategic Planner
   - Expertise: litigation strategy, case management
   - Responsibilities:
     * Define case review objectives
     * Allocate review resources
     * Make high-level legal strategy decisions
   - Workspace: /workspaces/legal-ops/strategy
   - Agent directory: /agents/case-strategy-lead

2. DISCOVERY ANALYST
   - Triggered by keywords: evidence, discovery, data
   - Role type: Data Analyst
   - Expertise: legal data analysis, e-discovery
   - Responsibilities:
     * Analyze document sets for relevance
     * Identify patterns in discovery data
     * Generate discovery reports
   - Workspace: /workspaces/legal-ops/discovery
   - Agent directory: /agents/discovery-analyst

3. COMPLIANCE REVIEWER
   - Triggered by keywords: risk, compliance, regulation
   - Role type: Risk Manager
   - Expertise: legal compliance, regulatory risk
   - Responsibilities:
     * Identify regulatory compliance risks
     * Develop risk mitigation strategies
     * Monitor compliance factors
   - Workspace: /workspaces/legal-ops/compliance
   - Agent directory: /agents/compliance-reviewer

4. DOCUMENT QA SPECIALIST
   - Triggered by keywords: review, quality, QA
   - Role type: QA Engineer
   - Expertise: document review, quality control
   - Responsibilities:
     * Develop document review checklists
     * Execute quality checks on reviewed documents
     * Identify and report document deficiencies
   - Workspace: /workspaces/legal-ops/qa
   - Agent directory: /agents/document-qa

5. PLATFORM ARCHITECT
   - Triggered by keywords: architecture, system, technical
   - Role type: Technical Architect
   - Expertise: legal tech platforms, system integration
   - Responsibilities:
     * Design document review system architecture
     * Make platform technical decisions
     * Oversee technical implementations
   - Workspace: /workspaces/legal-ops/platform
   - Agent directory: /agents/platform-architect

ROUTING RULES:
--------------
- The Case Strategy Lead should handle all direct peer-to-peer messages regardless of content.
- All other agents are routed based on keyword matches in the message text.
- All agents listen on any channel.
"""
with open(os.path.join(WORKSPACE, "notes/specs/legal_ops_team_requirements.txt"), "w") as f:
    f.write(requirements_prose)

# Distractor 5: Notes with incorrect role names
wrong_roles_notes = """Interview notes - DO NOT USE (outdated)
Role ideas: "Legal Strategist", "Evidence Miner", "Risk Assessor"
These don't match our platform's standard role catalog.
"""
with open(os.path.join(WORKSPACE, "notes/interviews/role_brainstorm.txt"), "w") as f:
    f.write(wrong_roles_notes)

# Distractor 6: Partially correct agents config with wrong structure
partial_agents = {
    "agents": {
        "list": [
            {
                "id": "case_strategy_lead",
                "workspace": "/workspaces/legal-ops/strategy",
                "agentDir": "/agents/case-strategy-lead",
                "config": {
                    "role": "Strategic Planner",
                    "expertise": "litigation strategy, case management",
                    "responsibilities": [
                        "Define case review objectives"
                    ]
                }
            }
        ]
    }
    # Missing: rest of agents, AND bindings entirely
}
with open(os.path.join(WORKSPACE, "agents/proto/partial_legal_team.json"), "w") as f:
    json.dump(partial_agents, f, indent=2)

# Distractor 7: Fake README about a different system
with open(os.path.join(WORKSPACE, "docs/legal-ops/old_system_notes.txt"), "w") as f:
    f.write("Old ATLAS system used XML configs. Deprecated 2022. Do not reference.\n")

# Distractor 8: HR file
with open(os.path.join(WORKSPACE, "docs/hr/headcount_2024.txt"), "w") as f:
    f.write("Legal Ops team headcount request: 5 AI agents approved for Q1 2025.\n")

# Distractor 9: Scratch notes
with open(os.path.join(WORKSPACE, "scratch/todo.txt"), "w") as f:
    f.write("TODO: finalize legal_ops_team_config.json before Monday standup\n")

# Distractor 10: Log file
with open(os.path.join(WORKSPACE, "logs/2024/deploy_errors.log"), "w") as f:
    f.write("[ERROR] 2024-12-01: Agent config missing 'agentDir' field. Deployment failed.\n")
    f.write("[ERROR] 2024-12-03: Binding 'contains' must be an array. Config rejected.\n")

# Distractor 11: Staging config with wrong peer syntax
with open(os.path.join(WORKSPACE, "agents/old-team/legacy_bindings.json"), "w") as f:
    json.dump({
        "bindings": [
            {
                "agentId": "old_lead",
                "match": {
                    "channel": "any",
                    "peer": "direct"  # Wrong: string instead of {"kind": "direct"}
                }
            }
        ]
    }, f, indent=2)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_, files in os.walk(WORKSPACE):
    for file in files:
        print(f"  {os.path.join(root, file)}")