import os
import json
import random

random.seed(42)

# Create workspace directory structure
workspace = "/workspace"

# Create directory skeleton
dirs = [
    "scripts",
    "references",
    "agents",
    "agents/team-shared",
    "agents/team-shared/deliverables",
    "config",
    "logs",
    "logs/archived",
    "tests",
    "docs",
    "docs/compliance",
    "docs/internal",
    "archive",
    "archive/v1",
    "temp",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Create reference files (stub versions, not full, to simulate existing workspace) ---

references = {
    "references/dialog-flow.md": """# Dialog Flow
## Minimal-Question Strategy
Ask only what is missing. If user goal is broad, propose default operating model first.
## Auto-Completion Rules
- If user provides team objective, infer standard roles from role-catalog.
- Do not ask for role names if team archetype is known.
## Anti-Overdesign Rules
- Max 7 roles for a new team unless explicitly required.
- Merge roles that share >60% of responsibilities.
""",

    "references/role-catalog.md": """# Role Catalog

## Regulatory & Compliance Teams
- team-leader: Orchestrates the team, delegates tasks, monitors progress. MUST NOT produce specialist deliverables.
- regulatory-affairs-lead: Manages submissions, dossiers, agency interactions.
- quality-assurance-specialist: Reviews protocols, SOPs, audit readiness.
- medical-writer: Drafts regulatory documents, clinical summaries, labeling.
- data-integrity-analyst: Monitors data pipelines for compliance, flags anomalies.
- pharmacovigilance-officer: Tracks adverse events, prepares safety reports.
- submissions-coordinator: Manages submission timelines, tracks dossier completeness.

## Core vs Optional
- Core: team-leader, regulatory-affairs-lead, quality-assurance-specialist
- Optional: medical-writer, data-integrity-analyst, pharmacovigilance-officer, submissions-coordinator
""",

    "references/splitting-principles.md": """# Splitting Principles
## When to Split
- Role has >3 distinct output types with no overlap.
- Role requires conflicting authority (e.g., QA reviewer AND implementer).
## When to Merge
- Two roles share the same upstream inputs and downstream consumers.
- Both roles produce <2 deliverables each.
""",

    "references/output-templates.md": """# Output Templates

## Agent Contract Table Format
Each agent MUST have all of these fields defined:
| Field | Description |
|---|---|
| agent_id | Stable, short, lowercase-hyphen. team-leader MUST be <team>-team-leader |
| role_mission | What this agent exists to accomplish |
| inputs_consumed | List of inputs this agent receives |
| outputs_produced | List of outputs this agent produces |
| decision_authority | What decisions this agent can make autonomously |
| dependencies | upstream_agents and downstream_agents |
| escalation_target | Who receives escalations from this agent |

## Status Values
Agent status in config: `ready` | `partially_ready` | `blocked`
""",

    "references/collaboration-protocol.md": """# Collaboration Protocol

## Task Delegation Envelope
Every task delegation MUST include: goal, context, deliverable, deadline.

## Status States
Agents MUST report one of: `accepted`, `blocked`, `done`

## Completion Callback
Every delegated task MUST return explicitly to the delegator upon completion.

## Long-Task Update Cadence
For tasks >30 min: agent sends status update every 15 minutes.

## Timeout/Retry/Escalation Policy
- Timeout: 2x expected duration
- Retry: 1 automatic retry, then escalate
- Escalation: goes to team-leader, then human operator

## No-Raw-Bulk-Output Rule
Agents MUST NOT return raw bulk data. Return: summary + artifact_path only.

## Mid-Process Visibility
At each stage, log: agent_id, current_task, status, eta.
""",

    "references/materialization-checklist.md": """# Materialization Checklist

## Role File Completion Gate
A team is `ready` only if ALL of the following are true for every agent:
- [ ] agent_id follows naming convention
- [ ] role_mission is not a placeholder (>20 words)
- [ ] inputs_consumed is a non-empty list
- [ ] outputs_produced is a non-empty list
- [ ] decision_authority is specified
- [ ] escalation_target is specified
- [ ] dependencies.upstream and dependencies.downstream are defined (can be empty list, but key must exist)

If any check fails: status = `partially_ready`, reason must be listed.
If blocked by missing credentials or config: status = `blocked`.
""",

    "references/config-materialization-checklist.md": """# Config Materialization Checklist

## openclaw.json Agent Entry Requirements
Each agent entry in openclaw.json MUST have:
- id: matches agent_id in contract
- role: human-readable role name
- status: one of ready/partially_ready/blocked
- permissions: list (can be empty)
- skills: list (can be empty)
- team: team name slug

## A2A (Agent-to-Agent) Bindings
- team-leader must list all team member IDs in subagents[]
- Each specialist must list team-leader as escalation_agent
""",

    "references/channel-binding-blueprints.md": """# Channel Binding Blueprints

## Single-Bot Model
One bot token bound to team-leader. All messages routed through team-leader.
Config keys required:
- channel_type: slack|teams|telegram
- bot_token_ref: reference to secret (NOT the token itself)
- routing_mode: single-bot
- team_leader_id: <team>-team-leader

## Multi-Bot Group Model  
Each agent has its own bot. Group config required.
Config keys required:
- channel_type
- group_id
- routing_mode: multi-bot
- agent_bot_map: { agent_id: bot_token_ref }

## Security Note
Never store raw tokens in config. Use secret references only.
Confirmation required before binding (irreversible external effect).
""",

    "references/capability-matrix.md": """# Capability Matrix
| Role | Tools | Skills |
|---|---|---|
| team-leader | task-tracker, notification-sender | orchestration, delegation |
| regulatory-affairs-lead | doc-manager, submission-portal-api | regulatory-writing, dossier-management |
| quality-assurance-specialist | audit-tool, sop-tracker | gap-analysis, audit-planning |
| medical-writer | doc-editor, reference-manager | scientific-writing, labeling |
| data-integrity-analyst | data-pipeline-monitor, anomaly-detector | data-validation, compliance-monitoring |
| pharmacovigilance-officer | adverse-event-tracker, safety-db | pharmacovigilance, signal-detection |
| submissions-coordinator | timeline-tracker, dossier-checklist | project-management, submission-logistics |
""",

    "references/permission-profiles.md": """# Permission Profiles (Least Privilege)
| Role | Read | Write | Execute | External |
|---|---|---|---|---|
| team-leader | team-shared/* | team-shared/status/* | delegate, escalate | notify-only |
| regulatory-affairs-lead | submissions/*, docs/* | team-shared/deliverables/* | submit-draft | submission-portal |
| quality-assurance-specialist | all-team-docs | team-shared/deliverables/qa-* | approve-sop | audit-tool |
| medical-writer | clinical-data, references | team-shared/deliverables/docs/* | publish-draft | none |
| data-integrity-analyst | data-pipelines | team-shared/deliverables/integrity-* | flag-anomaly | data-monitor |
| pharmacovigilance-officer | adverse-events, safety-db | team-shared/deliverables/pv-* | file-safety-report | safety-db |
| submissions-coordinator | all-submission-docs | team-shared/deliverables/submissions/* | trigger-submission | timeline-tool |
""",

    "references/create-playbook.md": """# Create Playbook

## Execution Sequence
1. Validate all agent contracts are complete (materialization-checklist.md).
2. Write each agent entry to openclaw.json under `agents[]`.
3. Set team-leader subagents[] to all non-leader agent IDs.
4. Set each specialist escalation_agent to team-leader ID.
5. Run `scripts/create_team.mjs` as single entrypoint.
   - Internally executes: materialize -> validate -> emit_report
   - If validate != ready: return partially_ready/blocked and stop.
6. Write team_creation_report.json with stage deliverables and paths.
7. Output channel_binding_blueprint.md.
8. Output smoke_test.md with simple end-to-end validation prompt.

## File Placement
- All agent SOUL/AGENTS snippets under: agents/<agent_id>/
- Team shared deliverables under: agents/team-shared/deliverables/
- Config: config/openclaw.json
- Report: config/team_creation_report.json
""",

    "references/final-deliverable-sample.md": """# Final Deliverable Sample

## team_creation_report.json structure
{
  "team_name": "<string>",
  "team_slug": "<lowercase-hyphen>",
  "status": "ready|partially_ready|blocked",
  "agents": [
    {
      "agent_id": "<id>",
      "role": "<role name>",
      "status": "ready|partially_ready|blocked",
      "deliverable_paths": ["agents/<agent_id>/SOUL.md", "agents/<agent_id>/AGENTS.md"]
    }
  ],
  "collaboration_protocol_path": "config/collaboration_protocol.md",
  "channel_binding_blueprint_path": "config/channel_binding_blueprint.md",
  "smoke_test_path": "tests/smoke_test.md",
  "security_check_summary": {
    "skills_scanned": <int>,
    "high_risk_blocked": <int>,
    "approved": <int>
  },
  "materialization_issues": []
}
""",

    "references/team-leader-template.md": """# Team Leader SOUL Template
## Identity
You are the {team_name} Team Leader. Your sole purpose is to orchestrate the team.
## Core Rules
- You NEVER produce specialist deliverables yourself.
- You delegate ALL implementation tasks to appropriate specialists.
- You track status using: accepted | blocked | done.
- You escalate to human operator after 1 retry.
- You save all specialist outputs to agents/team-shared/deliverables/.
""",

    "references/snippet-templates.md": """# Snippet Templates

## SOUL.md Template (per agent)
# {agent_id} SOUL
## Mission
{role_mission}
## Inputs
{inputs_consumed}
## Outputs
{outputs_produced}
## Authority
{decision_authority}
## Escalation
Escalate to: {escalation_target}

## AGENTS.md Template (per agent)
# {agent_id} AGENTS
## Upstream
{upstream_agents}
## Downstream
{downstream_agents}
""",

    "references/failure-modes.md": """# Failure Modes

| Failure | Recovery Action |
|---|---|
| Agent file is placeholder | Block team creation, list affected agents |
| Security check fails for skill | Block skill install, list alternatives |
| A2A binding missing | Return partially_ready, provide fix instruction |
| create_team.mjs returns non-zero | Parse error, surface to user, stop |
| Validation incomplete | Return blocked status, preserve completed work |
""",

    "references/examples.md": """# Examples

## Biotech Regulatory Team (Archetype)
Team slug: biotech-reg
Team leader ID: biotech-reg-team-leader
Roles: team-leader, regulatory-affairs-lead, quality-assurance-specialist, medical-writer, submissions-coordinator
Status pattern: Core roles ready first, optional roles deferred if timeline <3 months.
""",

    "references/language-templates.md": """# Language Templates
## English
- "Here is your proposed team roster for review."
- "Please confirm additions/removals before I proceed with creation."
- "Team creation complete. Status: {status}."
## Chinese
- "以下是建议的团队名单，请确认。"
- "团队创建完成，状态：{status}。"
""",

    "references/role-display-mapping.json": json.dumps({
        "en": {
            "team-leader": "Team Leader",
            "regulatory-affairs-lead": "Regulatory Affairs Lead",
            "quality-assurance-specialist": "Quality Assurance Specialist",
            "medical-writer": "Medical Writer",
            "data-integrity-analyst": "Data Integrity Analyst",
            "pharmacovigilance-officer": "Pharmacovigilance Officer",
            "submissions-coordinator": "Submissions Coordinator"
        },
        "zh": {
            "team-leader": "团队负责人",
            "regulatory-affairs-lead": "监管事务负责人",
            "quality-assurance-specialist": "质量保证专员",
            "medical-writer": "医学撰写员",
            "data-integrity-analyst": "数据完整性分析师",
            "pharmacovigilance-officer": "药物警戒官",
            "submissions-coordinator": "申报协调员"
        }
    }, indent=2),

    "references/security-report-schema.md": """# Security Report Schema
{
  "scan_id": "<uuid>",
  "timestamp": "<iso8601>",
  "skills_evaluated": [
    {
      "skill_name": "<string>",
      "risk_level": "low|medium|high",
      "approved": true|false,
      "reason": "<string>"
    }
  ],
  "summary": {
    "total": <int>,
    "approved": <int>,
    "blocked": <int>
  }
}
""",

    "references/provisioning-playbook.md": """# Provisioning Playbook
## Steps
1. For each agent, resolve required tools/skills from capability-matrix.md.
2. Run skill-vetter security scan before installing any skill.
3. Block any skill rated high-risk.
4. Install approved skills only.
5. Assign permissions from permission-profiles.md.
6. Record in team_creation_report.json security_check_summary.
""",

    "references/role-soul-blueprints.md": """# Role SOUL Blueprints
Each role's SOUL.md must contain at minimum:
- 3+ specific domain behaviors
- Input/output contracts
- Escalation path
- At least one example task with expected output format
Must NOT be a one-line placeholder.
""",

    "references/team-leader-agents-template.md": """# Team Leader AGENTS Template
## Subagents
{subagents_list}
## Escalation
Human operator (on second failure)
"""
}

for path, content in references.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the mock create_team.mjs script ---
create_team_script = """#!/usr/bin/env node
// Mock create_team.mjs - Single entrypoint for team creation
// Internally executes: materialize -> validate -> emit_report
const fs = require('fs');
const path = require('path');

const configPath = path.join(process.cwd(), 'config', 'openclaw.json');
const reportPath = path.join(process.cwd(), 'config', 'team_creation_report.json');

if (!fs.existsSync(configPath)) {
    console.error('ERROR: config/openclaw.json not found. Aborting.');
    process.exit(1);
}

let config;
try {
    config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
} catch(e) {
    console.error('ERROR: Invalid JSON in config/openclaw.json:', e.message);
    process.exit(1);
}

// materialize step
console.log('[materialize] Reading agent definitions...');
const agents = config.agents || [];
if (agents.length === 0) {
    console.error('[validate] FAIL: No agents defined.');
    process.exit(2);
}

// validate step
console.log('[validate] Running materialization checks...');
let issues = [];
const requiredFields = ['id','role','status','permissions','skills','team'];
for (const agent of agents) {
    for (const field of requiredFields) {
        if (!(field in agent)) {
            issues.push(`Agent ${agent.id || '?'} missing field: ${field}`);
        }
    }
    if (agent.id && !agent.id.match(/^[a-z][a-z0-9-]*$/)) {
        issues.push(`Agent ID '${agent.id}' is not lowercase-hyphen format`);
    }
}

// Check team-leader naming
const teamLeader = agents.find(a => a.role && a.role.toLowerCase().includes('team leader') || a.role && a.role.toLowerCase().includes('team-leader'));
if (teamLeader && !teamLeader.id.includes('-team-leader')) {
    issues.push(`team-leader ID '${teamLeader.id}' must include '-team-leader' suffix`);
}

const overallStatus = issues.length === 0 ? 'ready' : 'partially_ready';
console.log(`[validate] Status: ${overallStatus}`);
if (issues.length > 0) {
    console.log('[validate] Issues found:', issues);
}

// emit_report step
console.log('[emit_report] Writing team_creation_report.json...');
const existingReport = fs.existsSync(reportPath) ? JSON.parse(fs.readFileSync(reportPath,'utf8')) : {};
const report = Object.assign({}, existingReport, {
    _script_run: true,
    _materialize_status: overallStatus,
    _validation_issues: issues,
    _agents_count: agents.length
});
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
console.log('[emit_report] Done. Report written to config/team_creation_report.json');

if (overallStatus !== 'ready') {
    console.log('Team is partially_ready. Fix issues before marking as ready.');
    process.exit(3);
}
console.log('Team creation successful. Status: ready.');
process.exit(0);
"""

scripts_path = os.path.join(workspace, "scripts", "create_team.mjs")
with open(scripts_path, "w") as f:
    f.write(create_team_script)

# --- Create a partially filled (stub) openclaw.json to show existing structure ---
stub_openclaw = {
    "_comment": "Stub config - agents must be populated before running create_team.mjs",
    "version": "1.0",
    "workspace": "biotech-regulatory",
    "agents": []
}
config_path = os.path.join(workspace, "config", "openclaw.json")
with open(config_path, "w") as f:
    json.dump(stub_openclaw, f, indent=2)

# --- Create distractor files ---
distractor_files = {
    "logs/archived/run_2024_01_15.log": "INFO: previous team creation attempt\nERROR: agent-id 'teamleader' failed validation (not lowercase-hyphen)\nABORTED\n",
    "logs/archived/run_2024_02_03.log": "INFO: partial creation\nWARNING: medical-writer SOUL.md was placeholder, skipped\nSTATUS: partially_ready\n",
    "logs/deploy.log": "deploy attempt failed - missing openclaw.json agents\n",
    "docs/compliance/fda_submission_guide.md": "# FDA Submission Guide\nThis document outlines 21 CFR Part 11 requirements.\nData integrity and audit trails are mandatory for all submissions.\n",
    "docs/compliance/ema_guidelines.md": "# EMA Guidelines\nFor European submissions, refer to ICH E6 R2 guidelines.\n",
    "docs/internal/team_structure_old.md": "# Old Team Structure (DEPRECATED)\nThis was the v1 team structure. Do not use.\n- project-manager\n- doc-writer\n- qa\n",
    "docs/internal/onboarding.md": "# Onboarding\nNew team members should review the compliance docs first.\n",
    "archive/v1/openclaw_v1.json": json.dumps({"version": "0.9", "agents": [{"id": "teamleader", "role": "Leader"}]}, indent=2),
    "archive/v1/old_roster.md": "# Old Roster (v1 - DEPRECATED)\n- teamleader (wrong ID format)\n- qa-person\n",
    "temp/scratch_notes.txt": "TODO: figure out correct team-leader ID format\nTODO: check if medical-writer is needed\n",
    "temp/draft_roles.txt": "draft roles: compliance-lead, doc-writer, qa-specialist\nNOTE: these are placeholders, do not use\n",
    "tests/placeholder_test.md": "# Tests\nSmoke test TBD\n",
    "agents/team-shared/deliverables/.gitkeep": "",
    "config/secrets.example.env": "# Example secrets - DO NOT commit real values\nBOT_TOKEN_REF=vault://biotech-reg/bot-token\nSUBMISSION_API_KEY_REF=vault://biotech-reg/submission-api\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print("Directory structure:")
for root, dirs, files in os.walk(workspace):
    level = root.replace(workspace, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')