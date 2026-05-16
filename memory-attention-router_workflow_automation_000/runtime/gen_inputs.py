import os
import json
import random
import string
from pathlib import Path

random.seed(42)

# ── workspace root ────────────────────────────────────────────────
ws = Path("/workspace")
ws.mkdir(parents=True, exist_ok=True)

# ── skill location (mirrors real OpenClaw layout) ─────────────────
skill_root = ws / "skills" / "memory-attention-router"
scripts_dir = skill_root / "scripts"
prompts_dir = scripts_dir / "prompts"
refs_dir = skill_root / "references"

for d in [scripts_dir, prompts_dir, refs_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ── distractor directory tree ─────────────────────────────────────
distractor_dirs = [
    ws / "projects" / "platform-eng" / "deploy" / "k8s",
    ws / "projects" / "platform-eng" / "ci" / "pipelines",
    ws / "projects" / "platform-eng" / "docs" / "runbooks",
    ws / "projects" / "data-pipeline" / "etl" / "transforms",
    ws / "projects" / "data-pipeline" / "schemas",
    ws / "logs" / "2024" / "q1",
    ws / "logs" / "2024" / "q2",
    ws / "archive" / "old-policies" / "2023",
    ws / "archive" / "old-policies" / "2022",
    ws / "tmp" / "scratch",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

def rand_text(n=40):
    return ''.join(random.choices(string.ascii_lowercase + ' ', k=n)).strip()

# Distractor files
distractor_files = [
    (ws / "projects" / "platform-eng" / "deploy" / "k8s" / "deployment.yaml",
     "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: platform-svc\n"),
    (ws / "projects" / "platform-eng" / "ci" / "pipelines" / "Jenkinsfile",
     'pipeline {\n  agent any\n  stages {\n    stage("Build") { steps { sh "make build" } }\n  }\n}\n'),
    (ws / "projects" / "platform-eng" / "docs" / "runbooks" / "incident_response.md",
     "# Incident Response\n\n1. Page on-call\n2. Assess blast radius\n3. Rollback if needed\n"),
    (ws / "projects" / "data-pipeline" / "etl" / "transforms" / "normalize.py",
     "def normalize(data):\n    return {k: v.strip() for k, v in data.items()}\n"),
    (ws / "projects" / "data-pipeline" / "schemas" / "event_schema.json",
     json.dumps({"type": "object", "properties": {"event_id": {"type": "string"}}}, indent=2)),
    (ws / "logs" / "2024" / "q1" / "deploy.log",
     "2024-01-15 deploy ok\n2024-02-03 deploy failed: OOM\n2024-03-20 deploy ok\n"),
    (ws / "logs" / "2024" / "q2" / "deploy.log",
     "2024-04-10 deploy ok\n2024-05-22 rollback triggered\n2024-06-01 deploy ok\n"),
    (ws / "archive" / "old-policies" / "2023" / "output_policy_v1.txt",
     "DEPRECATED: Use verbose output with full JSON blobs per deployment step.\n"),
    (ws / "archive" / "old-policies" / "2022" / "style_guide.txt",
     "DEPRECATED: Prefer long-form prose explanations in all agent outputs.\n"),
    (ws / "tmp" / "scratch" / "notes.txt",
     rand_text(120) + "\n"),
    (ws / "projects" / "platform-eng" / "docs" / "runbooks" / "memory_notes_DRAFT.txt",
     "DRAFT - do not use: some raw notes about memory storage, not finalized.\n" + rand_text(80) + "\n"),
    (ws / "archive" / "old-policies" / "2023" / "agent_rules_scratch.json",
     json.dumps({"note": "scratch", "rules": [rand_text(20), rand_text(20)]})),
]

for path, content in distractor_files:
    path.write_text(content)

# ── task brief (the WHAT, not the HOW) ───────────────────────────
task_brief = {
    "scenario": "Platform Engineering Memory Lifecycle",
    "sprint": "Q3-2024",
    "description": (
        "The platform team needs to record and manage knowledge across sprint cycles. "
        "This task exercises the full lifecycle: recording team preferences and procedures, "
        "superseding outdated rules, capturing lessons from a post-sprint reflection, "
        "deactivating stale knowledge, and finally generating focused execution and critic briefings."
    ),
    "sessions": {
        "main_session": "sess_platform_q3",
        "task_ids": {
            "deploy_workflow": "task_deploy_wf",
            "output_policy": "task_output_policy",
            "incident_review": "task_incident_review"
        }
    },
    "knowledge_to_record": [
        {
            "note": "OLD output policy (will be replaced)",
            "type": "preference",
            "content": "Always use verbose JSON blobs in deployment step outputs.",
            "keywords": ["output", "json", "deployment", "verbose"],
            "tags": ["preference", "output-policy"],
            "importance": 0.75,
            "confidence": 0.80,
            "success_score": 0.65
        },
        {
            "note": "NEW output policy replacing the old one",
            "type": "preference",
            "content": "Always keep deployment step outputs under 3 bullets. No verbose JSON blobs.",
            "keywords": ["output", "bullets", "deployment", "concise"],
            "tags": ["preference", "output-policy"],
            "importance": 0.95,
            "confidence": 0.95,
            "success_score": 0.95
        },
        {
            "note": "Deployment procedure",
            "type": "procedure",
            "content": "Run pre-flight checks, apply manifests, verify rollout, emit status summary.",
            "keywords": ["deploy", "preflight", "manifest", "rollout", "status"],
            "tags": ["procedure", "deployment"],
            "importance": 0.72,
            "confidence": 0.80,
            "success_score": 0.80
        },
        {
            "note": "Stronger-on-metadata procedure (no graph support)",
            "type": "procedure",
            "content": "Directly apply manifests and check pod status without pre-flight validation.",
            "keywords": ["deploy", "manifest", "pods", "status"],
            "tags": ["procedure", "deployment", "shortcut"],
            "importance": 0.85,
            "confidence": 0.85,
            "success_score": 0.82
        },
        {
            "note": "Episode: OOM failure in Q1",
            "type": "episode",
            "content": "Deployment to prod failed due to OOM on node pool. Pre-flight memory check was skipped.",
            "keywords": ["deploy", "oom", "failure", "prod", "preflight"],
            "tags": ["episode", "failure"],
            "importance": 0.85,
            "confidence": 0.95,
            "success_score": 0.0
        }
    ],
    "reflection_scenario": {
        "session_id": "sess_platform_q3",
        "task_id": "task_deploy_wf",
        "goal": "Deploy platform services reliably across environments",
        "outcome": "completed",
        "what_worked": [
            "Pre-flight memory and CPU checks",
            "Incremental rollout with canary verification",
            "Compact status summaries after each step"
        ],
        "what_failed": [
            "Skipping pre-flight checks caused OOM failure in Q1",
            "Verbose JSON blobs in outputs caused context overflow"
        ],
        "lessons": [
            "Always run pre-flight resource checks before applying manifests",
            "Keep step outputs under 3 bullets to prevent context overflow"
        ],
        "next_time": [
            "Store deployment procedures after successful sprint",
            "Refresh outdated output policies immediately"
        ],
        "create_procedure": True
    },
    "stale_memory_to_refresh": {
        "note": "An additional stale summary that should be deactivated via refresh",
        "type": "summary",
        "content": "Platform deployment relies on ad-hoc scripts and manual kubectl commands.",
        "keywords": ["deploy", "kubectl", "adhoc", "manual"],
        "tags": ["summary", "stale"],
        "importance": 0.60,
        "confidence": 0.70,
        "success_score": 0.40
    },
    "route_requests": {
        "executor": {
            "goal": "Execute the platform deployment workflow for Q3 sprint release",
            "step_role": "executor",
            "session_id": "sess_platform_q3",
            "task_id": "task_deploy_wf",
            "user_constraints": ["Keep outputs under 3 bullets"],
            "recent_failures": ["OOM on node pool when pre-flight skipped"],
            "unresolved_questions": ["Is canary threshold set correctly?"]
        },
        "critic": {
            "goal": "Review the Q3 platform deployment for correctness and policy compliance",
            "step_role": "critic",
            "session_id": "sess_platform_q3",
            "task_id": "task_deploy_wf",
            "user_constraints": [],
            "recent_failures": [],
            "unresolved_questions": ["Were all rollback conditions tested?"]
        }
    },
    "output_file": "memory_audit_report.json"
}

(ws / "task_brief.json").write_text(json.dumps(task_brief, indent=2))

# ── environment hint file (tells agent where the router lives) ────
env_hint = {
    "skill_base_dir": str(skill_root),
    "router_script": str(scripts_dir / "memory_router.py"),
    "db_env_var": "MAR_DB_PATH",
    "suggested_db_path": "/tmp/platform-memory-test.sqlite3"
}
(ws / "environment.json").write_text(json.dumps(env_hint, indent=2))

print("Workspace generated successfully.")
print(f"  Task brief: {ws / 'task_brief.json'}")
print(f"  Skill root: {skill_root}")
print(f"  Distractor files: {len(distractor_files)}")