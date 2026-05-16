import os
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "skills/multi-model-critique/references",
    "skills/multi-model-critique/scripts",
    "skills/multi-model-critique/outputs",
    "skills/multi-model-critique/outputs/drafts",
    "skills/multi-model-critique/outputs/critiques",
    "skills/multi-model-critique/outputs/revisions",
    "projects/hospital-protocol-review/raw",
    "projects/hospital-protocol-review/processed",
    "projects/hospital-protocol-review/archive",
    "config/runtime",
    "config/models",
    "logs/runs",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

BASE = WORKSPACE / "skills/multi-model-critique"

# ── SKILL.md ────────────────────────────────────────────────────────────────
(BASE / "SKILL.md").write_text(textwrap.dedent("""\
---
name: multi-model-critique
description: Run complex prompts through a multi-model deliberation pipeline with structured self-improvement. Use when the user sets a complex flag (e.g., complex=true/complex) or asks for high-stakes, ambiguous, or long-form reasoning where one model is not enough. Produces outputs by: (1) parallel model runs, (2) cross-critique, (3) critique-driven revision, and (4) final synthesized answer with uncertainties and evidence notes.
metadata: {"openclaw":{"emoji":"🧠"}}
---

# Multi-Model Critique

## Overview
Use this skill only for complex tasks. Route multiple models through the same 4-step loop (`Plan -> Execute -> Review -> Improve`), then run cross-critique and synthesis to produce a higher-quality final answer than any single-model draft.

## Trigger rule
Enable this skill only when the request explicitly sets `complex` to true (or equivalent wording such as "this is complex/deep").

If `complex` is false, skip this skill and respond with normal single-model behavior.

## Inputs
Collect or confirm these inputs before execution:
- `complex`: boolean flag (must be true)
- `question`: user request
- `models`: list of ACP `agentId` values (typically 3)
- `constraints`: output format, language, length, deadlines, forbidden assumptions
- `ops`: optional runtime controls (`timeoutSec`, `maxRetries`, `maxRounds`, `budgetUsd`)

## File map (what each file does)
- `SKILL.md` (this file): orchestration policy, trigger conditions, and execution sequence.
- `references/prompt-templates.md`: reusable prompts for draft, critique, revision, and final synthesis (includes scoring rubric usage).
- `references/orchestration-template.md`: practical OpenClaw orchestration flow using `sessions_spawn`, `sessions_send`, and `sessions_history`.
- `references/output-schema.md`: machine-parseable JSON output schema for final result and per-model scoring.
- `scripts/build_round_prompts.py`: utility to generate per-model prompt files for repeated runs.
- `scripts/run_orchestration.py`: local helper that builds a run plan JSON (model mapping, round prompts, runtime settings).

## Workflow

### Step 1) Parallel draft round
Spawn one ACP session per model with the same task and constraints.

Per-model requirements:
- Follow the exact internal sequence: `Plan -> Execute -> Review -> Improve`
- Print all four sections explicitly
- End with `Draft Answer`

Use `sessions_spawn` with `runtime:"acp"` and explicit `agentId`.

### Step 2) Cross-critique round
Share peer `Draft Answer` outputs with each model and require structured critique:
- Strengths
- Weaknesses
- Missing assumptions/data
- Hallucination and confidence risks
- Concrete fix suggestions

Also require ranking of peer drafts with rationale.

### Step 3) Revision round
Send critique feedback back to each original model and request revision:
- Keep `Plan -> Execute -> Review -> Improve`
- Include `Changes from Critique`
- End with `Revised Answer`

### Step 4) Final synthesis round
Integrate revised answers into one user-facing output:
- Best final answer
- Why the synthesis is stronger than individual drafts
- Remaining uncertainties
- Optional next actions

## Scoring rubric (required in critique + synthesis)
Score each draft on a 1-5 scale:
- `accuracy`: factual correctness and internal consistency
- `coverage`: completeness against user request and constraints
- `evidence`: quality of assumptions and support
- `actionability`: usefulness for concrete decision/action

Default weighted score:
`0.40 * accuracy + 0.25 * coverage + 0.20 * evidence + 0.15 * actionability`

Use this score to justify rankings and the final selected direction.

## Prompting resources
- Use `references/prompt-templates.md` for canonical prompts.
- Use `scripts/build_round_prompts.py` when you need file-based prompt generation for repeated or batched runs.
- Use `scripts/run_orchestration.py` to generate a deterministic run-plan artifact for reproducible execution.
- Use `references/orchestration-template.md` for concrete OpenClaw tool-call flow.

## Required user-facing output shape
1. `Final Answer`
2. `Key Improvements from Critique`
3. `Uncertainties`
4. `Next Steps` (optional)

When machine consumption is needed, return JSON matching `references/output-schema.md`.

Do not expose private chain-of-thought. Provide concise reasoning summaries only.

## Failure handling
- One model fails: continue with remaining models and note reduced diversity.
- Two or more models fail: ask whether to retry or switch to single-model mode.
- Strong disagreement remains: present competing hypotheses and state what evidence would resolve them.

## Runtime defaults (recommended)
- `timeoutSec`: 180 per round per model
- `maxRetries`: 1 per failed model turn
- `maxRounds`: fixed at 4 (draft, critique, revision, synthesis)
- `budgetUsd`: optional hard stop when cost-sensitive
"""))

# ── references/prompt-templates.md ─────────────────────────────────────────
(BASE / "references/prompt-templates.md").write_text(textwrap.dedent("""\
# Prompt Templates

## Draft Round Template
```
You are participating in a multi-model deliberation pipeline.

Task: {question}
Constraints: {constraints}

Strictly follow this internal sequence and label each section:

## Plan
<your planning here>

## Execute
<your execution here>

## Review
<your self-review here>

## Improve
<your improvement steps here>

## Draft Answer
<your final draft answer here>
```

## Cross-Critique Template
```
You are reviewing peer model drafts.

Original Task: {question}

Peer Drafts:
{peer_drafts}

For each draft provide:
- Strengths
- Weaknesses
- Missing assumptions/data
- Hallucination and confidence risks
- Concrete fix suggestions

Then rank all drafts from best to worst with rationale.

Score each draft using this rubric (1-5 scale):
- accuracy: factual correctness and internal consistency
- coverage: completeness against user request and constraints
- evidence: quality of assumptions and support
- actionability: usefulness for concrete decision/action

Weighted score = 0.40 * accuracy + 0.25 * coverage + 0.20 * evidence + 0.15 * actionability
```

## Revision Template
```
You are revising your earlier draft based on critique feedback.

Original Task: {question}
Your Draft: {original_draft}
Critique Received: {critique}

Follow this sequence:

## Plan
## Execute
## Review
## Improve
## Changes from Critique
<describe changes made based on the critique>

## Revised Answer
<your final revised answer here>
```

## Final Synthesis Template
```
You are synthesizing multiple revised answers into one final response.

Revised Answers:
{revised_answers}

Produce:
1. Final Answer
2. Key Improvements from Critique
3. Uncertainties
4. Next Steps (optional)

Explain why this synthesis is stronger than any individual draft.
```
"""))

# ── references/orchestration-template.md ───────────────────────────────────
(BASE / "references/orchestration-template.md").write_text(textwrap.dedent("""\
# Orchestration Template (OpenClaw)

## Session Spawn
```json
{
  "tool": "sessions_spawn",
  "params": {
    "agentId": "<model-agent-id>",
    "runtime": "acp",
    "sessionLabel": "draft-round-<model-name>"
  }
}
```

## Session Send
```json
{
  "tool": "sessions_send",
  "params": {
    "sessionId": "<session-id-from-spawn>",
    "message": "<prompt-text>"
  }
}
```

## Session History
```json
{
  "tool": "sessions_history",
  "params": {
    "sessionId": "<session-id>"
  }
}
```

## Round Flow
1. Round 1 (Draft): spawn + send draft prompt to each model
2. Round 2 (Critique): send peer drafts to each model for cross-critique
3. Round 3 (Revision): send critique back to originating model
4. Round 4 (Synthesis): consolidate all revised answers into final output

maxRounds is fixed at 4. Do not parameterize this value beyond 4.
"""))

# ── references/output-schema.md ────────────────────────────────────────────
(BASE / "references/output-schema.md").write_text(textwrap.dedent("""\
# Output Schema

## Final Output JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["run_id", "question", "models", "rounds", "scores", "final_output"],
  "properties": {
    "run_id": { "type": "string" },
    "question": { "type": "string" },
    "models": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1
    },
    "rounds": {
      "type": "integer",
      "const": 4,
      "description": "Always exactly 4: draft, critique, revision, synthesis"
    },
    "scores": {
      "type": "object",
      "description": "Per-model scoring object",
      "additionalProperties": {
        "type": "object",
        "required": ["accuracy", "coverage", "evidence", "actionability", "weighted_score"],
        "properties": {
          "accuracy":      { "type": "number", "minimum": 1, "maximum": 5 },
          "coverage":      { "type": "number", "minimum": 1, "maximum": 5 },
          "evidence":      { "type": "number", "minimum": 1, "maximum": 5 },
          "actionability": { "type": "number", "minimum": 1, "maximum": 5 },
          "weighted_score": {
            "type": "number",
            "description": "0.40*accuracy + 0.25*coverage + 0.20*evidence + 0.15*actionability"
          }
        }
      }
    },
    "final_output": {
      "type": "object",
      "required": ["final_answer", "key_improvements", "uncertainties"],
      "properties": {
        "final_answer":      { "type": "string" },
        "key_improvements":  { "type": "array", "items": { "type": "string" } },
        "uncertainties":     { "type": "array", "items": { "type": "string" } },
        "next_steps":        { "type": "array", "items": { "type": "string" } }
      }
    },
    "ops": {
      "type": "object",
      "properties": {
        "timeoutSec":  { "type": "integer" },
        "maxRetries":  { "type": "integer" },
        "maxRounds":   { "type": "integer", "const": 4 },
        "budgetUsd":   { "type": "number" }
      }
    }
  }
}
```

## Notes
- `rounds` MUST always equal 4.
- `weighted_score` MUST equal exactly: 0.40 * accuracy + 0.25 * coverage + 0.20 * evidence + 0.15 * actionability
- All score values are 1–5.
- `final_output.key_improvements` and `final_output.uncertainties` are required arrays (non-empty).
"""))

# ── scripts/build_round_prompts.py ─────────────────────────────────────────
(BASE / "scripts/build_round_prompts.py").write_text(textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
build_round_prompts.py
Usage: python build_round_prompts.py --config <run_config.json> --output-dir <dir>

Reads a run config JSON and writes per-model, per-round prompt files.
Expected config keys: question, models, constraints, ops
Output files: <output-dir>/<model>_round<N>.txt  (N = 1..4)
\"\"\"
import argparse, json, os, sys
from pathlib import Path

ROUND_LABELS = {
    1: "draft",
    2: "critique",
    3: "revision",
    4: "synthesis",
}

def build_draft_prompt(model, question, constraints):
    return (
        f"[Model: {model}] [Round 1 - Draft]\\n"
        f"Task: {question}\\n"
        f"Constraints: {constraints}\\n\\n"
        "Follow the sequence: Plan -> Execute -> Review -> Improve\\n"
        "End with: Draft Answer\\n"
    )

def build_critique_prompt(model, question):
    return (
        f"[Model: {model}] [Round 2 - Critique]\\n"
        f"Task: {question}\\n"
        "Review peer drafts. Provide: Strengths, Weaknesses, Missing assumptions/data, "
        "Hallucination and confidence risks, Concrete fix suggestions.\\n"
        "Rank peer drafts with rationale.\\n"
        "Score each: accuracy, coverage, evidence, actionability (1-5).\\n"
        "weighted_score = 0.40*accuracy + 0.25*coverage + 0.20*evidence + 0.15*actionability\\n"
    )

def build_revision_prompt(model, question):
    return (
        f"[Model: {model}] [Round 3 - Revision]\\n"
        f"Task: {question}\\n"
        "Incorporate critique feedback. Follow: Plan -> Execute -> Review -> Improve -> "
        "Changes from Critique -> Revised Answer\\n"
    )

def build_synthesis_prompt(model, question):
    return (
        f"[Model: {model}] [Round 4 - Synthesis]\\n"
        f"Task: {question}\\n"
        "Synthesize all revised answers. Output: Final Answer, Key Improvements from Critique, "
        "Uncertainties, Next Steps (optional).\\n"
    )

BUILDERS = {
    1: build_draft_prompt,
    2: build_critique_prompt,
    3: build_revision_prompt,
    4: build_synthesis_prompt,
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    question = cfg.get("question", "")
    models = cfg.get("models", [])
    constraints = cfg.get("constraints", "")

    for model in models:
        safe = model.replace("/", "_").replace(":", "_")
        for rnd in range(1, 5):
            if rnd == 1:
                text = BUILDERS[rnd](model, question, constraints)
            else:
                text = BUILDERS[rnd](model, question)
            fname = out / f"{safe}_round{rnd}.txt"
            fname.write_text(text)
            print(f"Wrote {fname}")

if __name__ == "__main__":
    main()
"""))

# ── scripts/run_orchestration.py ────────────────────────────────────────────
(BASE / "scripts/run_orchestration.py").write_text(textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
run_orchestration.py
Usage: python run_orchestration.py --config <run_config.json> --output <run_plan.json>

Reads a run config and writes a deterministic run_plan.json artifact.
The run plan includes: run_id, question, models, rounds (always 4), ops defaults,
and a per-model session_map scaffold.
\"\"\"
import argparse, json, uuid
from pathlib import Path
from datetime import datetime

DEFAULT_OPS = {
    "timeoutSec": 180,
    "maxRetries": 1,
    "maxRounds": 4,
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    cfg = json.loads(Path(args.config).read_text())

    ops = {**DEFAULT_OPS, **cfg.get("ops", {})}
    # maxRounds is always 4 per skill policy
    ops["maxRounds"] = 4

    models = cfg.get("models", [])
    session_map = {m: {"sessionId": None, "agentId": m, "runtime": "acp"} for m in models}

    plan = {
        "run_id": str(uuid.uuid4()),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "question": cfg.get("question", ""),
        "models": models,
        "rounds": 4,
        "constraints": cfg.get("constraints", ""),
        "ops": ops,
        "session_map": session_map,
        "round_labels": {
            "1": "draft",
            "2": "critique",
            "3": "revision",
            "4": "synthesis"
        }
    }

    Path(args.output).write_text(json.dumps(plan, indent=2))
    print(f"Run plan written to {args.output}")

if __name__ == "__main__":
    main()
"""))

# ── raw project files (distractor messy data) ──────────────────────────────
(WORKSPACE / "projects/hospital-protocol-review/raw/protocol_draft_v1.txt").write_text(textwrap.dedent("""\
PROTOCOL CHANGE REQUEST - DRAFT v1
Subject: Switching first-line anticoagulant from heparin to direct oral anticoagulants (DOACs)
Prepared by: Dr. A. Chen, Cardiology
Date: 2024-11-01

Rationale:
- DOACs show non-inferior outcomes in AF patients per recent RCTs
- Reduced monitoring burden
- Patient preference for oral route

Concerns not yet addressed:
- Renal dosing adjustments
- Drug interactions in polypharmacy patients
- Cost implications for uninsured population
- Emergency reversal agent availability

Status: INCOMPLETE - needs multi-disciplinary review
"""))

(WORKSPACE / "projects/hospital-protocol-review/raw/stakeholder_notes.txt").write_text(textwrap.dedent("""\
Stakeholder Review Notes (informal)
Pharmacy: Concerned about formulary additions
Nursing: Needs updated administration protocols
Risk Management: Malpractice exposure unclear
Finance: Formulary cost analysis pending
Patient Advocacy: Mixed feedback from patient surveys
"""))

(WORKSPACE / "projects/hospital-protocol-review/raw/model_registry.json").write_text(json.dumps({
    "available_models": [
        {"agentId": "claude-3-5-sonnet", "specialty": "clinical-reasoning"},
        {"agentId": "gpt-4o", "specialty": "evidence-synthesis"},
        {"agentId": "gemini-1.5-pro", "specialty": "policy-analysis"}
    ],
    "deprecated": ["gpt-3.5-turbo", "claude-2"]
}, indent=2))

# ── distractor config files ─────────────────────────────────────────────────
(WORKSPACE / "config/runtime/legacy_settings.yaml").write_text(textwrap.dedent("""\
# LEGACY - do not use
timeout: 60
retries: 3
rounds: 6
model: gpt-3.5-turbo
"""))

(WORKSPACE / "config/runtime/draft_ops.json").write_text(json.dumps({
    "timeoutSec": 90,
    "maxRetries": 3,
    "maxRounds": 6,
    "note": "DRAFT - not validated"
}, indent=2))

(WORKSPACE / "config/models/model_weights_old.json").write_text(json.dumps({
    "scoring_weights": {
        "accuracy": 0.25,
        "coverage": 0.25,
        "evidence": 0.25,
        "actionability": 0.25
    },
    "note": "Equal weights - outdated, replaced by weighted rubric"
}, indent=2))

(WORKSPACE / "config/models/proposed_weights_v2.json").write_text(json.dumps({
    "scoring_weights": {
        "accuracy": 0.35,
        "coverage": 0.30,
        "evidence": 0.20,
        "actionability": 0.15
    },
    "note": "Proposed but NOT approved - do not use"
}, indent=2))

# ── logs (distractor) ───────────────────────────────────────────────────────
(WORKSPACE / "logs/runs/run_20241101_failed.log").write_text(textwrap.dedent("""\
[2024-11-01 09:12:03] INFO: Starting run abc-123
[2024-11-01 09:12:05] ERROR: Model gpt-3.5-turbo timeout after 60s
[2024-11-01 09:12:05] ERROR: Model claude-2 connection refused
[2024-11-01 09:12:06] FATAL: 2 or more models failed. Aborting run.
[2024-11-01 09:12:06] INFO: Run abc-123 FAILED
"""))

(WORKSPACE / "logs/runs/run_20241102_partial.log").write_text(textwrap.dedent("""\
[2024-11-02 14:00:00] INFO: Starting run def-456
[2024-11-02 14:00:02] INFO: Model gpt-4o draft complete
[2024-11-02 14:00:04] WARN: Model gemini-1.5-pro timed out (round 1)
[2024-11-02 14:00:04] INFO: Continuing with reduced diversity (1 model failed)
[2024-11-02 14:00:10] INFO: Critique round complete
[2024-11-02 14:00:15] INFO: Run def-456 PARTIAL SUCCESS
"""))

# ── tmp stubs ───────────────────────────────────────────────────────────────
(WORKSPACE / "tmp/scratch.txt").write_text("scratch notes - ignore\n")
(WORKSPACE / "tmp/old_run_config.json").write_text(json.dumps({
    "question": "old question",
    "models": ["gpt-3.5-turbo"],
    "complex": False
}, indent=2))

# ── archive ─────────────────────────────────────────────────────────────────
(WORKSPACE / "projects/hospital-protocol-review/archive/review_v0_rejected.txt").write_text(
    "Rejected draft - single model review deemed insufficient for protocol changes.\n"
    "Decision: escalate to multi-model review pipeline.\n"
)

print("Workspace generated successfully.")
print(f"Skill files at: {BASE}")
print(f"Project files at: {WORKSPACE / 'projects/hospital-protocol-review'}")