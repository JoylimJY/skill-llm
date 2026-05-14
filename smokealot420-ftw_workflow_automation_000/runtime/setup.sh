#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"

# ── Create the PIV skill's baseDir with all reference files and assets ──
# In a real openclaw install this would be in ~/.openclaw/skills/piv/
# We place it at /opt/piv-skill to simulate the {baseDir}

BASE_DIR="/opt/piv-skill"
mkdir -p "$BASE_DIR/references"
mkdir -p "$BASE_DIR/assets"

# ── Write piv-discovery.md ──
cat > "$BASE_DIR/references/piv-discovery.md" << 'DISCOVERY_EOF'
# PIV Discovery Process

When no PRD exists, conduct a structured discovery conversation.

## Discovery Questions to Ask

Ask the user (in a single friendly message):
1. What is the core problem you're solving?
2. Who are the primary users?
3. What does success look like (measurable outcomes)?
4. What is the tech stack (or should we propose one)?
5. How many phases do you want? (Suggest 3–4 if unsure)
6. Are there any hard constraints (deadline, compliance, existing systems)?

## After Receiving Answers

Fill gaps with your expertise:
- Propose tech stack if unspecified
- Propose phase breakdown if unclear
- Always confirm: "Here's what I'd suggest — does this sound right?"

## Phase Naming Convention

Phases should be named descriptively:
- Phase 1: Foundation / Core Data Models
- Phase 2: Business Logic / API Layer
- Phase 3: Integration / External Services
- Phase 4: Polish / Testing / Deployment

## Output

Write a comprehensive PRD to: PROJECT_PATH/PRDs/PRD-{project-name}.md
DISCOVERY_EOF

# ── Write create-prd.md ──
cat > "$BASE_DIR/references/create-prd.md" << 'PRD_EOF'
# PRD Creation Guide

## PRD File Location
Save to: PROJECT_PATH/PRDs/PRD-{project-name}.md

## Required Sections

### 1. Project Overview
- Problem statement
- Target users
- Success metrics

### 2. Technical Architecture
- Tech stack decisions
- System components
- Data models (high-level)

### 3. Phase Breakdown
Each phase must have:
- Phase number and name
- Scope (what gets built)
- Acceptance criteria (measurable)
- Dependencies

### 4. Non-Functional Requirements
- Performance targets
- Security requirements
- Compliance constraints

### 5. Out of Scope
Explicitly state what is NOT being built.

## Naming Convention
PRD file: PRD-{kebab-case-project-name}.md
Example: PRD-patient-scheduler.md
PRD_EOF

# ── Write generate-prp.md ──
cat > "$BASE_DIR/references/generate-prp.md" << 'PRP_EOF'
# PRP Generation Guide

## PRP File Location
Save to: PROJECT_PATH/PRPs/PRP-{PRD_NAME}-phase-{N}.md

Where PRD_NAME is the basename of the PRD file without the .md extension.
Example: If PRD is PRD-patient-scheduler.md → PRP-PRD-patient-scheduler-phase-1.md

## Process

1. Read the codebase analysis from PROJECT_PATH/PRPs/planning/{PRD_NAME}-phase-{N}-analysis.md
2. Load the PRP template from PROJECT_PATH/PRPs/templates/prp_base.md
3. Fill in all template sections based on PRD phase scope and analysis

## Required PRP Sections (from template)

A PRP must contain ALL of these sections:
- ## Overview
- ## Context
- ## Implementation Steps
- ## Validation Criteria
- ## Files to Create/Modify

## Quality Gates

Each PRP must:
- Reference specific files from codebase analysis
- Include concrete test commands
- Define clear DONE criteria
PRP_EOF

# ── Write codebase-analysis.md ──
cat > "$BASE_DIR/references/codebase-analysis.md" << 'ANALYSIS_EOF'
# Codebase Analysis Process

## Analysis Output Location
Save to: PROJECT_PATH/PRPs/planning/{PRD_NAME}-phase-{N}-analysis.md

## Steps

1. Map directory structure
2. Identify existing patterns (naming, imports, style)
3. Find relevant files for this phase
4. Document integration points
5. Note technical debt or blockers

## Output Format

```markdown
# Codebase Analysis - Phase {N}

## Directory Structure
...

## Relevant Files
...

## Patterns Observed
...

## Integration Points
...

## Risks/Blockers
...
```
ANALYSIS_EOF

# ── Write piv-executor.md ──
cat > "$BASE_DIR/references/piv-executor.md" << 'EXEC_EOF'
# Executor Role

The Executor implements the PRP step-by-step.

## Process
1. Load PRP
2. Plan implementation thoroughly
3. Execute each step
4. Run validation commands
5. Verify outputs

## Output Format
```
EXECUTION SUMMARY
- Status: COMPLETE / PARTIAL / BLOCKED
- Files Modified: [list]
- Tests: PASS / FAIL
- Issues: [any blockers]
```
EXEC_EOF

# ── Write execute-prp.md ──
cat > "$BASE_DIR/references/execute-prp.md" << 'EXECPRP_EOF'
# Execute PRP Instructions

1. Read PRP thoroughly
2. Implement in order of Implementation Steps
3. After each step, run the specified validation command
4. Do not skip validation
5. Report any blocked steps immediately
EXECPRP_EOF

# ── Write piv-validator.md ──
cat > "$BASE_DIR/references/piv-validator.md" << 'VALID_EOF'
# Validator Role

The Validator independently verifies all PRP requirements.

## Validation Outputs
- PASS: All criteria met
- GAPS_FOUND: Missing or incorrect items (list them)
- HUMAN_NEEDED: Requires human judgment

## Report Format
```
VERIFICATION REPORT
- Grade: PASS / GAPS_FOUND / HUMAN_NEEDED
- Checks: [list each criterion with result]
- Gaps: [list any gaps]
```
VALID_EOF

# ── Write piv-debugger.md ──
cat > "$BASE_DIR/references/piv-debugger.md" << 'DEBUG_EOF'
# Debugger Role

Fix root causes identified by the Validator.

## Process
1. Reproduce each gap
2. Identify root cause
3. Apply fix
4. Re-run tests
5. Report results

## Output
```
FIX REPORT
- Status: FIXED / PARTIAL / UNRESOLVABLE
- Fixes Applied: [list]
- Test Results: [pass/fail per test]
```
DEBUG_EOF

# ── Write prp_base.md template ──
cat > "$BASE_DIR/assets/prp_base.md" << 'PRPBASE_EOF'
# PRP: {FEATURE_NAME} - Phase {N}

## Overview
{Brief description of what this phase builds}

## Context
{Relevant background, dependencies, prior phases}

## Implementation Steps
{Numbered list of implementation tasks}

## Validation Criteria
{Specific, testable acceptance criteria}

## Files to Create/Modify
{Explicit list of files to be touched}
PRPBASE_EOF

# ── Write workflow-template.md ──
cat > "$BASE_DIR/assets/workflow-template.md" << 'WORKFLOW_EOF'
# WORKFLOW.md

## Project: {PROJECT_NAME}

## Phase Status

| Phase | Name | Status | Validation Cycles | Commit |
|-------|------|--------|-------------------|--------|
| 1     | TBD  | ⏳ Pending | 0 | - |
| 2     | TBD  | ⏳ Pending | 0 | - |
| 3     | TBD  | ⏳ Pending | 0 | - |
| 4     | TBD  | ⏳ Pending | 0 | - |

## Notes
{Any orchestration notes or blockers}
WORKFLOW_EOF

# ── Export BASE_DIR as env var for agents to discover ──
echo "export PIV_BASE_DIR=$BASE_DIR" >> /etc/environment
echo "PIV_BASE_DIR=$BASE_DIR" >> /etc/environment

# ── Create a small helper script that prints the skill base dir ──
cat > /usr/local/bin/piv-basedir << 'HELPER_EOF'
#!/bin/bash
echo "/opt/piv-skill"
HELPER_EOF
chmod +x /usr/local/bin/piv-basedir

# ── Ensure git is configured in workspace ──
cd "$WORKSPACE"
git config user.email "agent@test.local" || true
git config user.name "Agent Tester" || true

echo "PIV skill environment ready at $BASE_DIR"
echo "Workspace project at $WORKSPACE (patient_scheduler)"
echo ""
echo "Agent task: Bootstrap PIV workflow for patient-scheduler project"