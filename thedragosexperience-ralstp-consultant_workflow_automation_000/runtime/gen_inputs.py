import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ─── Directory structure with distractors ────────────────────────────────────
dirs = [
    "scripts",
    "docs/architecture",
    "docs/retrospectives",
    "pipeline/configs",
    "pipeline/templates",
    "reports/drafts",
    "reports/archive",
    "team/roles",
    "infra/terraform",
    "infra/k8s",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "docs/architecture/system_overview.md": "# System Overview\nMicroservices architecture with 12 services.\n",
    "docs/architecture/adr_001.md": "# ADR 001: Use Kubernetes\nDecision: adopt k8s for container orchestration.\n",
    "docs/retrospectives/sprint_42.md": "## Sprint 42 Retro\n- Deployments took too long\n- Security scans blocked releases\n",
    "pipeline/configs/ci_config.yaml": "stages:\n  - build\n  - test\n  - scan\n  - deploy\ntimeout: 3600\n",
    "pipeline/templates/deploy_template.sh": "#!/bin/bash\necho 'Deploy template placeholder'\n",
    "pipeline/templates/rollback.sh": "#!/bin/bash\necho 'Rollback script'\n",
    "reports/drafts/q3_release_notes.md": "# Q3 Release Notes\nDraft — not for distribution.\n",
    "reports/archive/2023_complexity_report.pdf.stub": "Binary stub — original PDF not included.\n",
    "team/roles/responsibilities.md": "## Team Roles\n- Developer: writes code\n- Tester: writes tests\n- Ops: deploys to prod\n- Security: runs audits\n",
    "infra/terraform/main.tf": 'provider "aws" {\n  region = "eu-west-1"\n}\n',
    "infra/k8s/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app\n",
    "pipeline/configs/environments.json": json.dumps({
        "environments": ["dev", "staging", "prod"],
        "gates": {"staging": "manual_approval", "prod": "security_sign_off"}
    }, indent=2),
}

for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.write_text(content)

# ─── PDDL Domain: Software Deployment Pipeline ───────────────────────────────
# Agents (dynamic - appear as first arg in effects):
#   developer, tester, security_scanner, ops_engineer
# Passive (static - never first arg in effects):
#   feature_branch, artifact, ticket, environment, registry
#
# Entanglement: HIGH
#   - developer + tester share 'artifact' (developer builds it, tester uses it)
#   - security_scanner depends on artifact produced by developer
#   - ops_engineer depends on security clearance AND tested artifact
#   - Multiple agents need 'at' same environment for handoffs
#   - Shared predicates: at, available, busy, artifact-ready, cleared, tested

pddl_domain = """\
(define (domain software-deployment)
  (:requirements :typing :durative-actions)

  (:types
    developer tester security_scanner ops_engineer - pipeline_agent
    feature_branch artifact ticket - work_item
    environment registry - infrastructure
  )

  (:predicates
    (at ?a - pipeline_agent ?e - environment)
    (artifact-ready ?art - artifact ?e - environment)
    (branch-merged ?b - feature_branch)
    (ticket-resolved ?t - ticket)
    (tested ?art - artifact)
    (cleared ?art - artifact)
    (deployed ?art - artifact ?e - environment)
    (available ?a - pipeline_agent)
    (busy ?a - pipeline_agent)
    (registered ?art - artifact ?r - registry)
    (smoke-passed ?e - environment)
  )

  ;; Developer builds the artifact from a feature branch
  (:durative-action build
    :parameters (?dev - developer ?b - feature_branch ?art - artifact ?e - environment)
    :duration (= ?duration 15)
    :condition (and
      (at start (at ?dev ?e))
      (at start (available ?dev))
      (at start (branch-merged ?b))
    )
    :effect (and
      (at start (busy ?dev))
      (at end (artifact-ready ?art ?e))
      (at end (available ?dev))
      (at end (not (busy ?dev)))
    )
  )

  ;; Tester runs automated test suite against the artifact
  (:durative-action run-tests
    :parameters (?tst - tester ?art - artifact ?e - environment)
    :duration (= ?duration 20)
    :condition (and
      (at start (at ?tst ?e))
      (at start (available ?tst))
      (at start (artifact-ready ?art ?e))
    )
    :effect (and
      (at start (busy ?tst))
      (at end (tested ?art))
      (at end (available ?tst))
      (at end (not (busy ?tst)))
    )
  )

  ;; Security scanner performs vulnerability scan
  (:durative-action security-scan
    :parameters (?sec - security_scanner ?art - artifact ?e - environment)
    :duration (= ?duration 10)
    :condition (and
      (at start (at ?sec ?e))
      (at start (available ?sec))
      (at start (artifact-ready ?art ?e))
      (at start (tested ?art))
    )
    :effect (and
      (at start (busy ?sec))
      (at end (cleared ?art))
      (at end (available ?sec))
      (at end (not (busy ?sec)))
    )
  )

  ;; Ops engineer registers artifact in registry
  (:durative-action register-artifact
    :parameters (?ops - ops_engineer ?art - artifact ?e - environment ?r - registry)
    :duration (= ?duration 5)
    :condition (and
      (at start (at ?ops ?e))
      (at start (available ?ops))
      (at start (cleared ?art))
      (at start (tested ?art))
    )
    :effect (and
      (at start (busy ?ops))
      (at end (registered ?art ?r))
      (at end (available ?ops))
      (at end (not (busy ?ops)))
    )
  )

  ;; Ops engineer deploys to environment
  (:durative-action deploy
    :parameters (?ops - ops_engineer ?art - artifact ?e - environment ?r - registry)
    :duration (= ?duration 8)
    :condition (and
      (at start (at ?ops ?e))
      (at start (available ?ops))
      (at start (registered ?art ?r))
    )
    :effect (and
      (at start (busy ?ops))
      (at end (deployed ?art ?e))
      (at end (available ?ops))
      (at end (not (busy ?ops)))
    )
  )

  ;; Developer runs smoke tests post-deploy
  (:durative-action smoke-test
    :parameters (?dev - developer ?art - artifact ?e - environment)
    :duration (= ?duration 5)
    :condition (and
      (at start (at ?dev ?e))
      (at start (available ?dev))
      (at start (deployed ?art ?e))
    )
    :effect (and
      (at start (busy ?dev))
      (at end (smoke-passed ?e))
      (at end (available ?dev))
      (at end (not (busy ?dev)))
    )
  )

  ;; Tester resolves ticket after successful deployment
  (:durative-action resolve-ticket
    :parameters (?tst - tester ?t - ticket ?e - environment)
    :duration (= ?duration 3)
    :condition (and
      (at start (at ?tst ?e))
      (at start (available ?tst))
      (at start (smoke-passed ?e))
    )
    :effect (and
      (at start (busy ?tst))
      (at end (ticket-resolved ?t))
      (at end (available ?tst))
      (at end (not (busy ?tst)))
    )
  )
)
"""

pddl_problem = """\
(define (problem release-v2)
  (:domain software-deployment)

  (:objects
    dev1 dev2 - developer
    tst1 - tester
    sec1 - security_scanner
    ops1 - ops_engineer
    branch-feature-x branch-hotfix-y - feature_branch
    artifact-v2 artifact-patch - artifact
    ticket-101 ticket-202 - ticket
    staging prod - environment
    nexus-registry - registry
  )

  (:init
    (at dev1 staging)
    (at dev2 staging)
    (at tst1 staging)
    (at sec1 staging)
    (at ops1 staging)
    (available dev1)
    (available dev2)
    (available tst1)
    (available sec1)
    (available ops1)
    (branch-merged branch-feature-x)
    (branch-merged branch-hotfix-y)
  )

  (:goal
    (and
      (deployed artifact-v2 prod)
      (ticket-resolved ticket-101)
      (ticket-resolved ticket-202)
      (smoke-passed prod)
    )
  )
)
"""

(workspace / "pipeline" / "domain.pddl").write_text(pddl_domain)
(workspace / "pipeline" / "problem.pddl").write_text(pddl_problem)

# ─── scripts/analyze.py ──────────────────────────────────────────────────────
# This script parses PDDL domain/problem files and outputs a JSON with:
#  - agents (dynamic types): types that appear as first arg of a predicate in any action's effects
#  - passive_objects: types that never appear as first arg in effects
#  - entanglement_data: shared predicates between agent pairs
#  - landmark_chain: ordered list of fact predicates required by goal
#  - action_landmarks: ordered list of actions that must be executed

analyze_script = '''\
#!/usr/bin/env python3
"""
RALSTP Formal Analyzer - scripts/analyze.py
Parses PDDL domain/problem files and outputs RALSTP-relevant data as JSON.

Usage: python scripts/analyze.py <domain.pddl> <problem.pddl>
"""

import sys
import json
import re
from pathlib import Path


def parse_types(domain_text):
    """Extract type hierarchy from PDDL domain."""
    types = {}
    type_section = re.search(r\'\\(:types([^)]+(?:\\([^)]*\\)[^)]*)*?)\\)\', domain_text, re.DOTALL)
    if not type_section:
        return types
    
    lines = type_section.group(1).strip().split(\'\\n\')
    for line in lines:
        line = line.strip()
        if \' - \' in line:
            parts = line.split(\' - \')
            parent = parts[-1].strip()
            children = parts[0].strip().split()
            for child in children:
                types[child.strip()] = parent
    return types


def parse_predicates(domain_text):
    """Extract predicate definitions."""
    predicates = {}
    pred_section = re.search(r\'\\(:predicates(.*?)\\)\\s*(?:\\(|$)\', domain_text, re.DOTALL)
    if not pred_section:
        return predicates
    
    pred_text = pred_section.group(1)
    pred_matches = re.finditer(r\'\\(([\\w-]+)([^)]*?)\\)\', pred_text)
    for m in pred_matches:
        pred_name = m.group(1)
        params_str = m.group(2).strip()
        params = []
        param_parts = params_str.split()
        i = 0
        while i < len(param_parts):
            if param_parts[i].startswith(\'?\'):
                if i + 2 < len(param_parts) and param_parts[i+1] == \'-\':
                    params.append((param_parts[i], param_parts[i+2]))
                    i += 3
                else:
                    params.append((param_parts[i], \'unknown\'))
                    i += 1
            else:
                i += 1
        predicates[pred_name] = params
    return predicates


def parse_actions(domain_text):
    """Extract durative actions with their effects."""
    actions = []
    
    action_blocks = re.finditer(
        r\'\\(:durative-action\\s+(\\S+).*?:parameters\\s*(\\([^)]+(?:\\([^)]*\\)[^)]*)*\\)).*?:effect\\s*(.*?)(?=\\(:durative-action|\\)\\s*$)\',
        domain_text, re.DOTALL
    )
    
    for m in action_blocks:
        action_name = m.group(1)
        params_str = m.group(2)
        effect_str = m.group(3)
        
        # Parse parameters
        params = {}
        param_matches = re.finditer(r\'(\\?[\\w-]+)\\s+-\\s+([\\w_-]+)\', params_str)
        for pm in param_matches:
            params[pm.group(1)] = pm.group(2)
        
        # Parse effects: find predicates in at-end effects
        at_end_effects = re.findall(r\'at end\\s*(?:\\(not\\s*)?\\(([\\w-]+)\\s+(.*?)\\)\', effect_str)
        
        effects = []
        for pred_name, args_str in at_end_effects:
            args = args_str.strip().split()
            if args:
                first_arg = args[0]
                first_arg_type = params.get(first_arg, \'unknown\')
                effects.append({
                    \'predicate\': pred_name,
                    \'first_arg\': first_arg,
                    \'first_arg_type\': first_arg_type,
                    \'args\': args
                })
        
        actions.append({
            \'name\': action_name,
            \'parameters\': params,
            \'effects\': effects
        })
    
    return actions


def identify_agents(types, actions):
    """
    RALSTP Rule: Dynamic type = appears as FIRST ARGUMENT of a predicate
    in ANY action\'s effects.
    """
    dynamic_types = set()
    
    for action in actions:
        for effect in action[\'effects\']:
            first_arg_type = effect[\'first_arg_type\']
            if first_arg_type != \'unknown\':
                dynamic_types.add(first_arg_type)
    
    # Also check parent types
    all_types = set(types.keys())
    static_types = all_types - dynamic_types
    
    return sorted(dynamic_types), sorted(static_types)


def compute_entanglement(actions, agents):
    """
    Count shared predicates between agent pairs.
    Returns entanglement factor and classification.
    """
    # For each agent type, collect predicates they appear in (as first arg in effects)
    agent_predicates = {agent: set() for agent in agents}
    
    for action in actions:
        for effect in action[\'effects\']:
            t = effect[\'first_arg_type\']
            if t in agent_predicates:
                agent_predicates[t].add(effect[\'predicate\'])
    
    # Count shared predicates between agent pairs
    shared_count = 0
    pairs = []
    agent_list = list(agents)
    for i in range(len(agent_list)):
        for j in range(i+1, len(agent_list)):
            a1, a2 = agent_list[i], agent_list[j]
            shared = agent_predicates[a1] & agent_predicates[a2]
            if shared:
                shared_count += len(shared)
                pairs.append({\'agents\': [a1, a2], \'shared_predicates\': sorted(shared)})
    
    # Entanglement classification
    if shared_count == 0:
        entanglement_label = "Low"
        entanglement_factor = 1
    elif shared_count <= 3:
        entanglement_label = "Medium"
        entanglement_factor = 2
    else:
        entanglement_label = "High"
        entanglement_factor = 3
    
    return {
        \'total_shared_predicates\': shared_count,
        \'entanglement_label\': entanglement_label,
        \'entanglement_factor\': entanglement_factor,
        \'agent_predicate_pairs\': pairs
    }


def extract_landmark_chain(domain_text, problem_text, actions):
    """
    Extract ordered fact landmarks from goal state backward to initial state.
    Landmarks = facts that MUST be true in any valid plan.
    """
    # Parse goals
    goal_section = re.search(r\'\\(:goal\\s*\\(and(.*?)\\)\\s*\\)\', problem_text, re.DOTALL)
    if not goal_section:
        goal_section = re.search(r\'\\(:goal\\s*\\((.*?)\\)\\s*\\)\', problem_text, re.DOTALL)
    
    goals = []
    if goal_section:
        goal_text = goal_section.group(1)
        goal_preds = re.findall(r\'\\(([\\w-]+)(?:\\s+[^)]+)?\\)\', goal_text)
        goals = goal_preds
    
    # Build causal chain: which predicates are required as preconditions before goals
    # We trace backward from goals through action preconditions
    predicate_producers = {}  # predicate -> actions that produce it (in at-end effects)
    predicate_consumers = {}  # predicate -> actions that require it (in conditions)
    
    for action in actions:
        for effect in action[\'effects\']:
            pred = effect[\'predicate\']
            if pred not in predicate_producers:
                predicate_producers[pred] = []
            predicate_producers[pred].append(action[\'name\'])
    
    # Parse action conditions
    action_cond_pattern = re.finditer(
        r\'\\(:durative-action\\s+(\\S+).*?:condition\\s*(.*?):effect\',
        domain_text, re.DOTALL
    )
    action_conditions = {}
    for m in action_cond_pattern:
        act_name = m.group(1)
        cond_text = m.group(2)
        cond_preds = re.findall(r\'at start\\s*\\(([\\w-]+)\\s\', cond_text)
        action_conditions[act_name] = cond_preds
    
    # Build ordered landmark chain using BFS from goals
    visited = set()
    landmark_chain = []
    queue = list(goals)
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        landmark_chain.append(current)
        
        # Find actions that produce this predicate
        producers = predicate_producers.get(current, [])
        for producer in producers:
            # Add their preconditions as earlier landmarks
            precond_preds = action_conditions.get(producer, [])
            for prec in precond_preds:
                if prec not in visited:
                    queue.append(prec)
    
    # Reverse to get init -> goal order
    landmark_chain.reverse()
    
    # Action landmarks: actions that must be executed (those producing goal facts)
    action_landmarks = []
    for goal in goals:
        producers = predicate_producers.get(goal, [])
        action_landmarks.extend(producers)
    
    return landmark_chain, list(dict.fromkeys(action_landmarks))


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/analyze.py <domain.pddl> <problem.pddl>", file=sys.stderr)
        sys.exit(1)
    
    domain_path = Path(sys.argv[1])
    problem_path = Path(sys.argv[2])
    
    domain_text = domain_path.read_text()
    problem_text = problem_path.read_text()
    
    # Parse domain
    types = parse_types(domain_text)
    actions = parse_actions(domain_text)
    
    # RALSTP Analysis
    agents, passive_types = identify_agents(types, actions)
    entanglement = compute_entanglement(actions, agents)
    landmark_chain, action_landmarks = extract_landmark_chain(domain_text, problem_text, actions)
    
    # Buksz Complexity Score
    agent_count = len(agents)
    entanglement_factor = entanglement[\'entanglement_factor\']
    buksz_score = agent_count * entanglement_factor
    
    result = {
        \'agents\': agents,
        \'passive_types\': passive_types,
        \'entanglement\': entanglement,
        \'agent_count\': agent_count,
        \'buksz_complexity_score\': buksz_score,
        \'landmark_chain\': landmark_chain,
        \'action_landmarks\': action_landmarks,
        \'types_full\': types
    }
    
    print(json.dumps(result, indent=2))


if __name__ == \'__main__\':
    main()
'''

(workspace / "scripts" / "analyze.py").write_text(analyze_script)
(workspace / "scripts" / "analyze.py").chmod(0o755)

# ─── A misleading/incomplete draft report to tempt the agent ─────────────────
draft_report = """\
# Release Complexity Assessment — DRAFT
## Pipeline Team Analysis (Q4)

Actors: developer, tester, ops_engineer, security_scanner
Status: INCOMPLETE — needs formal analysis
Estimated complexity: TBD

Notes:
- Security scanning seems to block deployments
- Need to understand sequencing
- TODO: calculate actual complexity score
"""
(workspace / "reports" / "drafts" / "complexity_draft.md").write_text(draft_report)

# ─── Misleading JSON with wrong agent list ────────────────────────────────────
wrong_agents = {
    "note": "OUTDATED - do not use",
    "agents_guessed": ["developer", "environment", "registry"],
    "complexity": "unknown"
}
(workspace / "reports" / "archive" / "old_analysis.json").write_text(
    json.dumps(wrong_agents, indent=2)
)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")