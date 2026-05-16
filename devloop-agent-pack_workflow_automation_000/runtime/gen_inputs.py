#!/usr/bin/env python3
"""
Generate a realistic DevLoop workspace for a legal-tech SaaS project.
The agent must:
1. Correctly apply the session startup protocol (SOUL.override.md precedence, BOOTSTRAP.md processing+deletion)
2. Use templates from assets/templates/ to create design-doc and test-spec
3. Write memory files with correct naming conventions (flat, date-based)
4. Populate MEMORY.md correctly
"""

import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ── Directory structure ────────────────────────────────────────────────────────
dirs = [
    "assets/templates",
    "references",
    "memory",
    "shared",
    "shared/designs",
    "shared/specs",
    "src/core",
    "src/api",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "docs/adr",
    "docs/internal",
    "scripts",
    ".git/refs",  # distractor
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── SOUL.md (base soul) ───────────────────────────────────────────────────────
(WORKSPACE / "SOUL.md").write_text("""\
# SOUL — Base Configuration

You are a professional software engineering assistant.
Work style: methodical, document-first, safety-conscious.
Language: respond in the language the user uses.
Default communication: concise and structured.

## Core Values
- Documentation before code
- Tests before merge
- Safety: use `trash` over `rm`
""")

# ── SOUL.override.md (MUST take priority — agent must detect this) ─────────────
(WORKSPACE / "SOUL.override.md").write_text("""\
# SOUL Override — LexAI Project Configuration

[ACTIVE OVERRIDE: This file replaces SOUL.md entirely]

You are operating as the Core Dev agent (devloop-core-dev 🧠) for LexAI — an AI-powered
legal document analysis SaaS platform. All design decisions must reflect legal-tech
domain constraints: data privacy (GDPR/CCPA), auditability, and contract-clause precision.

Work style: architecture-first, 7-dimension design thinking, concise technical writing.
Tone: professional, precise, minimal prose.

## Specialization
- Primary: architecture design, design document authoring, task scheduling
- Domain: NLP pipelines for legal document clause extraction
- Constraint: All features must include an audit trail design dimension
""")

# ── USER.md ───────────────────────────────────────────────────────────────────
(WORKSPACE / "USER.md").write_text("""\
# User Context — LexAI Engineering Team

Project: LexAI Contract Intelligence Platform
Team size: 4 engineers + 1 QA
Current sprint: Sprint 14
Primary language: Python 3.11
Stack: FastAPI, PostgreSQL, spaCy, Hugging Face Transformers
Repository: monorepo under /workspace/src

## Current Priority
Feature: Automated Contract Clause Extractor (CCE)
- Must support: NDA clauses, liability caps, termination conditions
- Performance target: <2s per page on standard hardware
- Compliance: All clause extractions must be logged with provenance

## Communication preferences
- Design docs: Markdown, concise, include diagrams as ASCII
- Daily reports: bullet points, no fluff
""")

# ── BOOTSTRAP.md (must be processed and then DELETED) ─────────────────────────
(WORKSPACE / "BOOTSTRAP.md").write_text("""\
# Bootstrap Instructions — One-time Initialization

This file guides the initial workspace setup. After completing all steps, DELETE this file.

## Steps

1. Confirm SOUL.override.md is active (it exists → use it instead of SOUL.md).

2. Create the initial MEMORY.md with the following long-term knowledge entries:
   - Project name: LexAI Contract Intelligence Platform
   - Core feature in progress: Contract Clause Extractor (CCE)
   - Architecture decision: microservice-based NLP pipeline
   - Key constraint: GDPR audit trail required for all clause extraction events
   - Team velocity: ~18 story points per sprint

3. Create today's daily memory note at the correct path (memory/YYYY-MM-DD.md using today's actual date).
   Record that this is the first session, BOOTSTRAP was processed, and CCE design work is starting.

4. Using the design-doc template (from assets/templates/design-doc.template.md),
   create a design document for the Contract Clause Extractor feature.
   Save it as: shared/designs/cce-design-doc.md
   Fill in ALL template sections with realistic LexAI-specific content.

5. Using the test-spec template (from assets/templates/test-spec.template.md),
   create the initial test specification for the CCE feature.
   Save it as: shared/specs/cce-test-spec.md
   Fill in ALL template sections with realistic content.

6. Delete this BOOTSTRAP.md file when done.
""")

# ── MEMORY.md (intentionally ABSENT — agent must create it) ───────────────────
# (not created here — agent must create from scratch per BOOTSTRAP.md)

# ── assets/templates/ ─────────────────────────────────────────────────────────
(WORKSPACE / "assets/templates/design-doc.template.md").write_text("""\
# Design Doc: [Feature Name]

**Author:** [Agent/Engineer]  
**Date:** [YYYY-MM-DD]  
**Status:** Draft | Review | Approved  
**Feature ID:** [ID]

---

## 1. Problem Statement
[What problem are we solving? Why now?]

## 2. Goals & Non-Goals
### Goals
- [Goal 1]

### Non-Goals
- [Non-goal 1]

## 3. Architecture Overview
[High-level design. Include ASCII diagram if helpful.]

## 4. Detailed Design
### 4.1 Components
[List and describe each component]

### 4.2 Data Flow
[Describe how data moves through the system]

### 4.3 API / Interface Design
[Key interfaces, endpoints, or function signatures]

## 5. Storage & Data Model
[Database schema, file formats, data retention]

## 6. Security & Compliance
[Auth, encryption, GDPR/CCPA considerations, audit trail]

## 7. Performance & Scalability
[Latency targets, throughput estimates, scaling strategy]

## 8. Testing Strategy
[Unit, integration, E2E coverage plan; link to test-spec]

## 9. Rollout Plan
[Phased rollout, feature flags, monitoring]

## 10. Open Questions
- [ ] [Question 1]

## 11. References
- [Link or doc name]
""")

(WORKSPACE / "assets/templates/test-spec.template.md").write_text("""\
# Test Specification: [Feature Name]

**Author:** [Agent/Engineer]  
**Date:** [YYYY-MM-DD]  
**Feature:** [Feature Name]  
**Design Doc:** [Link to design doc]  
**Status:** Draft | Active | Archived

---

## 1. Scope
[What is being tested? What is out of scope?]

## 2. Test Objectives
- [Objective 1]
- [Objective 2]

## 3. Test Environment
- Runtime: [e.g., Python 3.11, pytest 7.x]
- Dependencies: [list key dependencies]
- Data: [test data sources or fixtures]

## 4. Unit Tests
| Test ID | Description | Input | Expected Output | Priority |
|---------|-------------|-------|-----------------|----------|
| UT-001  | [description] | [input] | [expected] | High |

## 5. Integration Tests
| Test ID | Description | Components | Expected Behavior | Priority |
|---------|-------------|-----------|-------------------|----------|
| IT-001  | [description] | [components] | [expected] | High |

## 6. Edge Cases & Negative Tests
| Test ID | Scenario | Expected Handling |
|---------|----------|-------------------|
| EC-001  | [scenario] | [handling] |

## 7. Performance Tests
| Test ID | Metric | Target | Tool |
|---------|--------|--------|------|
| PT-001  | [metric] | [target] | [tool] |

## 8. Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## 9. Bug Reporting
Bugs found during this spec execution → log in bug-tracker.md

## 10. Sign-off
- [ ] Core Dev reviewed
- [ ] Test agent approved
""")

(WORKSPACE / "assets/templates/daily-report.template.md").write_text("""\
# Daily Test Report — [YYYY-MM-DD]

**Agent:** devloop-test 🧪  
**Sprint:** [Sprint N]

---

## Summary
- Tests Run: [N]
- Passed: [N]
- Failed: [N]
- Blocked: [N]

## New Bugs Found
| Bug ID | Severity | Description | Assignee |
|--------|----------|-------------|----------|
| BUG-XXX | [sev] | [desc] | [agent] |

## Resolved Bugs
- [BUG-XXX]: [resolution]

## Notes
[Any blockers, observations, or flags for Core Dev]
""")

(WORKSPACE / "assets/templates/bug-tracker.template.md").write_text("""\
# Bug Tracker

| Bug ID | Feature | Severity | Status | Description | Found By | Assigned To | Sprint |
|--------|---------|----------|--------|-------------|----------|-------------|--------|
| BUG-001 | [feature] | [sev] | Open | [desc] | devloop-test | devloop-dev | [N] |
""")

(WORKSPACE / "assets/templates/project-structure.template.md").write_text("""\
# Project Knowledge Base: [Project Name]

## Overview
[Brief project description]

## Repository Structure
```
/src          — Application source
/tests        — Test suites  
/docs         — Documentation
/shared       — Cross-agent shared artifacts (read-only for consumers)
```

## Key Contacts
| Role | Agent |
|------|-------|
| Product | devloop-product |
| Architecture | devloop-core-dev |

## Active Features
| Feature | Status | Design Doc |
|---------|--------|------------|
| [name] | [status] | [link] |
""")

(WORKSPACE / "assets/templates/memory-tracking.template.md").write_text("""\
# Research / Investigation Tracking

| Topic | Status | Owner | Notes |
|-------|--------|-------|-------|
| [topic] | Planned/Active/Done | [agent] | [notes] |
""")

(WORKSPACE / "assets/templates/design-index.template.md").write_text("""\
# Design Document Index

| Feature | Doc Path | Status | Author | Date |
|---------|----------|--------|--------|------|
| [feature] | [path] | [status] | [author] | [date] |
""")

(WORKSPACE / "assets/templates/review-notes.template.md").write_text("""\
# PR Review Notes — [PR Title]

**Reviewer:** devloop-test 🧪  
**Date:** [YYYY-MM-DD]  
**PR:** [#N or branch name]

## Summary
[Overall assessment]

## Issues Found
| Severity | Location | Issue | Suggestion |
|----------|----------|-------|------------|
| [sev] | [file:line] | [issue] | [fix] |

## Approval Status
- [ ] Approved
- [ ] Approved with minor changes
- [ ] Needs revision
""")

(WORKSPACE / "assets/templates/bug-trend.template.md").write_text("""\
# Bug Trend Summary (for MEMORY.md)

| Sprint | Total Bugs | Critical | Resolved | Carry-over |
|--------|-----------|----------|----------|------------|
| [N] | [n] | [n] | [n] | [n] |

## Observations
- [trend observation]
""")

(WORKSPACE / "assets/templates/test-spec.template.md").write_text("""\
# Test Specification: [Feature Name]

**Author:** [Agent/Engineer]  
**Date:** [YYYY-MM-DD]  
**Feature:** [Feature Name]  
**Design Doc:** [Link to design doc]  
**Status:** Draft | Active | Archived

---

## 1. Scope
[What is being tested? What is out of scope?]

## 2. Test Objectives
- [Objective 1]
- [Objective 2]

## 3. Test Environment
- Runtime: [e.g., Python 3.11, pytest 7.x]
- Dependencies: [list key dependencies]
- Data: [test data sources or fixtures]

## 4. Unit Tests
| Test ID | Description | Input | Expected Output | Priority |
|---------|-------------|-------|-----------------|----------|
| UT-001  | [description] | [input] | [expected] | High |

## 5. Integration Tests
| Test ID | Description | Components | Expected Behavior | Priority |
|---------|-------------|-----------|-------------------|----------|
| IT-001  | [description] | [components] | [expected] | High |

## 6. Edge Cases & Negative Tests
| Test ID | Scenario | Expected Handling |
|---------|----------|-------------------|
| EC-001  | [scenario] | [handling] |

## 7. Performance Tests
| Test ID | Metric | Target | Tool |
|---------|--------|--------|------|
| PT-001  | [metric] | [target] | [tool] |

## 8. Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## 9. Bug Reporting
Bugs found during this spec execution → log in bug-tracker.md

## 10. Sign-off
- [ ] Core Dev reviewed
- [ ] Test agent approved
""")

# ── references/ ───────────────────────────────────────────────────────────────
(WORKSPACE / "references/collaboration-protocol.md").write_text("""\
# Collaboration Protocol

## sessions_send Message Format
```
TO: <agent-id>
FROM: <agent-id>
SUBJECT: <brief>
BODY: <markdown content>
```

## shared/ Directory Convention
- Written by: the authoring agent (Core Dev for designs, Test for specs)
- Read by: any agent needing the artifact
- Rule: consumers MUST NOT modify files in shared/; use `../` paths NEVER
- Flat structure under shared/designs/ and shared/specs/

## Parallel Conflict Prevention (交叉)
- Each Dev instance owns a named module; no two Dev instances touch the same file
- Core Dev maintains a lock registry in shared/designs/LOCK.md

## Full Workflow Phases
[See SKILL.md for phase summary; full routing table omitted for brevity]
""")

(WORKSPACE / "references/agent-design-background.md").write_text("""\
# Agent Design Background

## 权限设计 (Permission Design)
- Core Dev: write to shared/designs/, read everything
- Test: write to shared/specs/, read everything
- Dev: read shared/, write to src/ only
- Product/Marketing: write to docs/, read shared/

## 边缘情况 (Edge Cases)
- If BOOTSTRAP.md exists on first session: process instructions → delete file
- If SOUL.override.md exists: use it exclusively; do not merge with SOUL.md
- Memory files must be flat under memory/ — no subdirectories allowed
- MEMORY.md is only loaded by the main/primary session, not sub-sessions
""")

# ── Distractor files ───────────────────────────────────────────────────────────
(WORKSPACE / "src/core/__init__.py").write_text("# LexAI Core Package\n")
(WORKSPACE / "src/core/pipeline.py").write_text("""\
\"\"\"Placeholder NLP pipeline — not yet implemented.\"\"\"

class ClauseExtractionPipeline:
    def __init__(self):
        raise NotImplementedError("CCE feature under design")
""")
(WORKSPACE / "src/api/routes.py").write_text("""\
from fastapi import APIRouter
router = APIRouter()

@router.get('/health')
def health():
    return {'status': 'ok'}
""")
(WORKSPACE / "src/utils/logger.py").write_text("""\
import logging
logger = logging.getLogger('lexai')
""")
(WORKSPACE / "tests/unit/.gitkeep").write_text("")
(WORKSPACE / "tests/integration/.gitkeep").write_text("")
(WORKSPACE / "docs/adr/ADR-001-nlp-framework.md").write_text("""\
# ADR-001: NLP Framework Selection

**Status:** Accepted  
**Date:** 2024-11-01

## Decision
Use spaCy + Hugging Face Transformers for clause extraction.

## Rationale
spaCy for fast tokenization; HF for fine-tuned legal BERT models.
""")
(WORKSPACE / "docs/internal/sprint-13-retro.md").write_text("""\
# Sprint 13 Retrospective

## What went well
- API layer delivered on time
- Zero critical bugs in production

## What to improve
- Design docs lagged behind coding
- Test specs written after code (bad practice)
""")
(WORKSPACE / "scripts/run_tests.sh").write_text("#!/bin/bash\npytest tests/ -v\n")
(WORKSPACE / ".git/refs/heads").mkdir(parents=True, exist_ok=True)
(WORKSPACE / ".git/refs/heads/main").write_text("abc123def456\n")

# ── Old memory file from yesterday (distractor — agent should read it) ─────────
yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
(WORKSPACE / f"memory/{yesterday}.md").write_text(f"""\
# Daily Notes — {yesterday}

## Session Summary
- Reviewed Sprint 13 retro
- Confirmed CCE as Sprint 14 priority
- No BOOTSTRAP.md processed (file didn't exist yet)

## TODO for next session
- Process BOOTSTRAP.md when it appears
- Create CCE design doc using team templates
""")

print(f"[gen_inputs] Workspace created at {WORKSPACE}")
print(f"[gen_inputs] Yesterday's memory: memory/{yesterday}.md")
print(f"[gen_inputs] BOOTSTRAP.md present — agent must process and delete")
print(f"[gen_inputs] SOUL.override.md present — must take priority over SOUL.md")