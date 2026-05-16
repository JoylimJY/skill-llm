import json
import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "~/.openclaw/skills/agent-mbti/scripts",
    "~/.openclaw/skills/agent-mbti/data",
    "~/.openclaw/config",
    "~/.openclaw/logs",
    "project/src",
    "project/tests",
    "project/docs",
    "project/.github/workflows",
    "artifacts/reports",
    "artifacts/backups",
    "tmp/scratch",
]
for d in dirs:
    expanded = Path(d.replace("~", str(Path.home()))) if d.startswith("~") else WORKSPACE / d
    expanded.mkdir(parents=True, exist_ok=True)

SKILL_DIR = Path.home() / ".openclaw/skills/agent-mbti"

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    WORKSPACE / "project/src/main.py": "# Main application entry point\nprint('hello world')\n",
    WORKSPACE / "project/src/utils.py": "def helper(): pass\n",
    WORKSPACE / "project/tests/test_main.py": "def test_nothing(): assert True\n",
    WORKSPACE / "project/docs/ARCHITECTURE.md": "# Architecture\nThis is legacy documentation.\n",
    WORKSPACE / "project/.github/workflows/ci.yml": "name: CI\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n",
    WORKSPACE / "artifacts/reports/old_report_2023.txt": "Old quarterly report. Ignore.\n",
    WORKSPACE / "artifacts/backups/config_backup.json": json.dumps({"version": "1.0", "deprecated": True}),
    WORKSPACE / "tmp/scratch/notes.txt": "scratchpad notes - not relevant\n",
    WORKSPACE / "~/.openclaw/logs/session.log" if False else WORKSPACE / "tmp/scratch/session.log":
        "2024-01-01 INFO session started\n",
    Path.home() / ".openclaw/config/global.json":
        json.dumps({"agent_name": "CodeAssist-v2", "version": "2.1.0", "debug": False}, indent=2),
    Path.home() / ".openclaw/logs/run.log":
        "2024-06-01 12:00:00 INFO Agent initialized\n2024-06-01 12:01:00 INFO Ready\n",
}
for fpath, content in distractor_files.items():
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── SKILL DATA FILES ─────────────────────────────────────────────────────────

# ── Stage 1: 93-question self-survey ────────────────────────────────────────
# Each question belongs to one of 4 MBTI dimensions:
#   EI (Extraversion/Introversion), SN (Sensing/iNtuition),
#   TF (Thinking/Feeling), JP (Judging/Perceiving)
# Each answer has a weight: positive = first pole, negative = second pole
# Final type: if sum > 0 → first letter; if sum <= 0 → second letter

dimensions = ["EI", "SN", "TF", "JP"]
questions_93 = []
rng = random.Random(42)

# distribute 93 questions across dimensions (23-24 each)
dim_counts = {"EI": 24, "SN": 23, "TF": 23, "JP": 23}
qid = 1
for dim, count in dim_counts.items():
    for i in range(count):
        options = [
            {"text": f"Option A for Q{qid}", "weight": 1, "pole": dim[0]},
            {"text": f"Option B for Q{qid}", "weight": -1, "pole": dim[1]},
        ]
        questions_93.append({
            "id": qid,
            "dimension": dim,
            "text": f"Question {qid}: How does the agent typically handle scenario {qid}?",
            "options": options,
            "agent_answer": rng.choice(["A", "B"])  # pre-filled agent answers
        })
        qid += 1

# Pre-set answers so Stage1 result is deterministic: INTJ
# EI: need sum <= 0 → Introvert. Set all 24 EI answers to "B" (weight -1)
# SN: need sum > 0 → iNtuition. Set all 23 SN answers to "A" (weight +1)
# TF: need sum <= 0 → Thinking (T is positive for TF? Let's define: TF pole[0]=T, pole[1]=F; sum>0→T)
#   Wait: TF sum > 0 → T. Set all 23 TF answers to "A"
# JP: need sum <= 0 → J. JP pole[0]=J, pole[1]=P; sum>0→J. Set all 23 JP to "A"
# → Result: I(sum<=0), N(sum>0), T(sum>0), J(sum>0) = INTJ

for q in questions_93:
    dim = q["dimension"]
    if dim == "EI":
        q["agent_answer"] = "B"   # weight=-1 → sum<0 → I
    elif dim == "SN":
        q["agent_answer"] = "A"   # weight=+1 → sum>0 → N
    elif dim == "TF":
        q["agent_answer"] = "A"   # weight=+1 → sum>0 → T
    elif dim == "JP":
        q["agent_answer"] = "A"   # weight=+1 → sum>0 → J

survey_93 = {
    "version": "3.2",
    "name": "Agent Self-Survey (93 Questions)",
    "scoring_rules": {
        "EI": {"sum_gt_0": "E", "sum_lte_0": "I"},
        "SN": {"sum_gt_0": "N", "sum_lte_0": "S"},
        "TF": {"sum_gt_0": "T", "sum_lte_0": "F"},
        "JP": {"sum_gt_0": "J", "sum_lte_0": "P"}
    },
    "questions": questions_93
}
(SKILL_DIR / "data/agent-self-survey-93-complete.json").write_text(json.dumps(survey_93, indent=2))

# ── Stage 2: 8-question ability test ────────────────────────────────────────
# 6 dimensions: Memory, Planning, WorldModel, Retrospection, Grounding, SpatialNav
# Each question tests one dimension with a rubric score 0-10
# measuredType is derived from scores using threshold mapping
ability_test = {
    "version": "2.0",
    "name": "Agent Ability Test (8 Questions)",
    "dimensions": ["Memory", "Planning", "WorldModel", "Retrospection", "Grounding", "SpatialNav"],
    "type_derivation": {
        "description": "Derive MBTI type from ability scores using dimension_map",
        "dimension_map": {
            "EI": {"high_dimension": "Planning", "threshold": 6, "high_pole": "E", "low_pole": "I"},
            "SN": {"high_dimension": "WorldModel", "threshold": 6, "high_pole": "N", "low_pole": "S"},
            "TF": {"high_dimension": "Retrospection", "threshold": 6, "high_pole": "T", "low_pole": "F"},
            "JP": {"high_dimension": "Memory", "threshold": 6, "high_pole": "J", "low_pole": "P"}
        }
    },
    "tasks": [
        {
            "id": 1,
            "dimension": "Memory",
            "description": "Recall the last 5 tool calls made in a session.",
            "agent_response": "The agent recalled 4 out of 5 tool calls correctly.",
            "rubric": {"max_score": 10, "agent_score": 8}
        },
        {
            "id": 2,
            "dimension": "Planning",
            "description": "Create a multi-step plan to refactor a codebase.",
            "agent_response": "The agent produced a 3-step plan missing dependency analysis.",
            "rubric": {"max_score": 10, "agent_score": 5}
        },
        {
            "id": 3,
            "dimension": "WorldModel",
            "description": "Predict the outcome of deploying a breaking API change.",
            "agent_response": "The agent identified 2 of 3 downstream impact areas.",
            "rubric": {"max_score": 10, "agent_score": 7}
        },
        {
            "id": 4,
            "dimension": "Retrospection",
            "description": "Identify what went wrong in a failed test suite run.",
            "agent_response": "The agent correctly identified the root cause.",
            "rubric": {"max_score": 10, "agent_score": 9}
        },
        {
            "id": 5,
            "dimension": "Grounding",
            "description": "Verify a factual claim about a library version.",
            "agent_response": "The agent checked the correct source and confirmed the version.",
            "rubric": {"max_score": 10, "agent_score": 6}
        },
        {
            "id": 6,
            "dimension": "SpatialNav",
            "description": "Navigate a deeply nested repository structure to find a config file.",
            "agent_response": "The agent found the file in 4 steps instead of the optimal 2.",
            "rubric": {"max_score": 10, "agent_score": 4}
        },
        {
            "id": 7,
            "dimension": "Memory",
            "description": "List all variables defined in a prior code block.",
            "agent_response": "The agent listed 6 out of 7 variables.",
            "rubric": {"max_score": 10, "agent_score": 7}
        },
        {
            "id": 8,
            "dimension": "Planning",
            "description": "Sequence 6 CI/CD pipeline stages in correct dependency order.",
            "agent_response": "The agent ordered them correctly.",
            "rubric": {"max_score": 10, "agent_score": 8}
        }
    ]
}
# Memory avg: (8+7)/2 = 7.5 → >= 6 → J
# Planning avg: (5+8)/2 = 6.5 → >= 6 → E
# WorldModel: 7 → >= 6 → N
# Retrospection: 9 → >= 6 → T
# measuredType = ENTJ
(SKILL_DIR / "data/agent-ability-test.json").write_text(json.dumps(ability_test, indent=2))

# ── personality-types.json ───────────────────────────────────────────────────
personality_types = {
    "version": "1.0",
    "types": {
        "INTJ": {
            "label": "建筑师型",
            "core_traits": ["深度思考", "系统化", "长远规划"],
            "strengths": ["独立性强", "战略眼光", "高效决策"],
            "weaknesses": ["缺乏互动性", "过于理性", "沟通生硬"]
        },
        "ENTJ": {
            "label": "指挥官型",
            "core_traits": ["计划性强", "主动输出", "逻辑决策"],
            "strengths": ["领导力", "执行效率", "目标导向"],
            "weaknesses": ["忽视情感需求", "过于强势", "抗压传导"]
        },
        "ENTP": {
            "label": "辩论家型",
            "core_traits": ["挑战假设", "替代方案", "创新思维"],
            "strengths": ["灵活应变", "创意输出", "批判思维"],
            "weaknesses": ["缺乏专注", "易散漫", "不善收尾"]
        },
        "INTP": {
            "label": "逻辑学家型",
            "core_traits": ["分析优先", "精确", "谨慎"],
            "strengths": ["逻辑严密", "深度分析", "客观判断"],
            "weaknesses": ["输出慢", "社交弱", "完美主义"]
        },
        "ESTJ": {
            "label": "执行者型",
            "core_traits": ["务实高效", "结构化", "结果导向"],
            "strengths": ["执行力", "规则遵从", "稳定可靠"],
            "weaknesses": ["缺乏灵活性", "抗拒变化", "机械化"]
        },
        "ESFJ": {
            "label": "执政官型",
            "core_traits": ["用户导向", "注重关系", "反馈敏感"],
            "strengths": ["亲和力", "协调能力", "服务意识"],
            "weaknesses": ["依赖认可", "避免冲突", "缺乏主见"]
        },
        "ENFJ": {
            "label": "教导者型",
            "core_traits": ["启发用户", "关注成长", "情感驱动"],
            "strengths": ["影响力", "共情能力", "激励他人"],
            "weaknesses": ["过度理想化", "负担过重", "边界模糊"]
        },
        "ISFJ": {
            "label": "保护者型",
            "core_traits": ["细致周到", "稳定支持", "可靠"],
            "strengths": ["责任心", "细节关注", "忠诚"],
            "weaknesses": ["过于谦逊", "不善拒绝", "变化适应差"]
        }
    }
}
(SKILL_DIR / "data/personality-types.json").write_text(json.dumps(personality_types, indent=2))

# ── personality-mapping.json ─────────────────────────────────────────────────
personality_mapping = {
    "version": "1.0",
    "selfReport_weight": 0.4,
    "measured_weight": 0.6,
    "conflict_resolution": "measured_takes_precedence",
    "description": "When selfReportedType != measuredType, agentProfile.dominantType = measuredType. agentProfile.secondaryType = selfReportedType."
}
(SKILL_DIR / "data/personality-mapping.json").write_text(json.dumps(personality_mapping, indent=2))

# ── personality-descriptors-v2.json ─────────────────────────────────────────
descriptors = {
    "version": "2.0",
    "dimension_descriptors": {
        "Memory": {"high": "strong recall", "low": "limited recall"},
        "Planning": {"high": "proactive planner", "low": "reactive responder"},
        "WorldModel": {"high": "systems thinker", "low": "local reasoner"},
        "Retrospection": {"high": "self-correcting", "low": "static behavior"},
        "Grounding": {"high": "fact-anchored", "low": "speculative"},
        "SpatialNav": {"high": "efficient navigator", "low": "disoriented navigator"}
    }
}
(SKILL_DIR / "data/personality-descriptors-v2.json").write_text(json.dumps(descriptors, indent=2))

# ── Stage 4: user-needs-survey-v2.json ──────────────────────────────────────
# User answers indicate they want an ENFJ agent
user_needs_survey = {
    "version": "2.0",
    "name": "User Needs Survey",
    "scoring_rules": {
        "EI": {"sum_gt_0": "E", "sum_lte_0": "I"},
        "SN": {"sum_gt_0": "N", "sum_lte_0": "S"},
        "TF": {"sum_gt_0": "T", "sum_lte_0": "F"},
        "JP": {"sum_gt_0": "J", "sum_lte_0": "P"}
    },
    "questions": [
        {
            "id": 1,
            "dimension": "EI",
            "text": "Should the agent proactively reach out with suggestions?",
            "options": [
                {"text": "Yes, always be proactive", "weight": 1, "pole": "E"},
                {"text": "No, wait to be asked", "weight": -1, "pole": "I"}
            ],
            "user_answer": "A"
        },
        {
            "id": 2,
            "dimension": "SN",
            "text": "Should the agent focus on big-picture insights?",
            "options": [
                {"text": "Yes, big-picture thinking", "weight": 1, "pole": "N"},
                {"text": "No, concrete facts only", "weight": -1, "pole": "S"}
            ],
            "user_answer": "A"
        },
        {
            "id": 3,
            "dimension": "TF",
            "text": "Should the agent prioritize empathy in responses?",
            "options": [
                {"text": "Yes, always empathetic", "weight": -1, "pole": "F"},
                {"text": "No, logic only", "weight": 1, "pole": "T"}
            ],
            "user_answer": "A"
        },
        {
            "id": 4,
            "dimension": "JP",
            "text": "Should the agent follow a structured process?",
            "options": [
                {"text": "Yes, structured is better", "weight": 1, "pole": "J"},
                {"text": "No, flexible is better", "weight": -1, "pole": "P"}
            ],
            "user_answer": "A"
        }
    ]
}
# EI: A → +1 → E
# SN: A → +1 → N
# TF: A → -1 → F (sum < 0 → F)
# JP: A → +1 → J
# desiredType = ENFJ
(SKILL_DIR / "data/user-needs-survey-v2.json").write_text(json.dumps(user_needs_survey, indent=2))

# ── Stage 5: diagnosis-engine-v2.json ────────────────────────────────────────
diagnosis_engine = {
    "version": "2.0",
    "name": "Diagnosis Engine",
    "gap_analysis": {
        "description": "Compare each MBTI dimension between agentProfile.dominantType and desiredType.",
        "output_fields": {
            "dimension_gaps": "List of dimensions where actual != desired, with actual_pole and desired_pole",
            "gap_count": "Total number of mismatched dimensions",
            "alignment_score": "Percentage of matching dimensions (0-100)"
        }
    },
    "output_schema": {
        "selfReportedType": "string",
        "measuredType": "string",
        "ability_scores": {
            "Memory": "float",
            "Planning": "float",
            "WorldModel": "float",
            "Retrospection": "float",
            "Grounding": "float",
            "SpatialNav": "float"
        },
        "agentProfile": {
            "dominantType": "string",
            "secondaryType": "string",
            "dimension_descriptors": "object"
        },
        "desiredType": "string",
        "gaps": {
            "dimension_gaps": "array",
            "gap_count": "integer",
            "alignment_score": "float"
        }
    }
}
(SKILL_DIR / "data/diagnosis-engine-v2.json").write_text(json.dumps(diagnosis_engine, indent=2))

# ── Stage 5: config-generator-v3.json ────────────────────────────────────────
config_generator = {
    "version": "3.0",
    "name": "Config Generator",
    "soul_patch_schema": {
        "description": "SOUL.md patch format. Each gap dimension generates one patch entry.",
        "patch_entry_fields": {
            "dimension": "MBTI dimension code (EI/SN/TF/JP)",
            "current_pole": "Current agent pole letter",
            "target_pole": "Desired pole letter",
            "directive": "Human-readable configuration directive to add to SOUL.md",
            "soul_md_section": "Section header in SOUL.md where this directive belongs"
        },
        "soul_md_sections": {
            "EI": "## Interaction Style",
            "SN": "## Information Processing",
            "TF": "## Decision Making",
            "JP": "## Execution Style"
        },
        "directive_templates": {
            "E_to_I": "Reduce unsolicited output. Wait for explicit user requests before responding.",
            "I_to_E": "Increase proactive engagement. Offer suggestions and insights without being asked.",
            "S_to_N": "Prioritize pattern recognition and big-picture analysis over literal fact reporting.",
            "N_to_S": "Ground all responses in concrete, verifiable facts. Avoid speculation.",
            "T_to_F": "Incorporate empathetic framing. Acknowledge user emotions before providing analysis.",
            "F_to_T": "Prioritize logical consistency over emotional accommodation in all decisions.",
            "J_to_P": "Adopt flexible, exploratory workflows. Avoid rigid process adherence.",
            "P_to_J": "Follow structured, sequential processes. Define clear milestones before proceeding."
        }
    },
    "output_format": "markdown",
    "output_filename": "SOUL.md"
}
(SKILL_DIR / "data/config-generator-v3.json").write_text(json.dumps(config_generator, indent=2))

# ── run-diagnosis.sh (the main entry script) ────────────────────────────────
run_script = r"""#!/bin/bash
# run-diagnosis.sh
# Usage: run-diagnosis.sh full
# Runs full MBTI diagnosis pipeline for agent personality assessment.
# Reads data files from the skill data directory.
# Outputs results to ~/.openclaw/skills/agent-mbti/output/
set -e
SKILL_DIR="$HOME/.openclaw/skills/agent-mbti"
DATA_DIR="$SKILL_DIR/data"
OUTPUT_DIR="$SKILL_DIR/output"
mkdir -p "$OUTPUT_DIR"

echo "[run-diagnosis.sh] Starting full MBTI diagnosis pipeline..."
echo "[run-diagnosis.sh] Data directory: $DATA_DIR"
echo "[run-diagnosis.sh] Output directory: $OUTPUT_DIR"
echo "[run-diagnosis.sh] Pipeline: Stage1 -> Stage2 -> Stage3 -> Stage4 -> Stage5"
echo "[run-diagnosis.sh] DONE: Agent must implement the pipeline logic using the JSON data files."
echo "[run-diagnosis.sh] Output file: $OUTPUT_DIR/diagnosis-report.json"
echo "[run-diagnosis.sh] Output file: $OUTPUT_DIR/SOUL.md"
"""
script_path = SKILL_DIR / "scripts/run-diagnosis.sh"
script_path.write_text(run_script)

# ── existing SOUL.md (outdated, needs patching) ──────────────────────────────
existing_soul = """# Agent Configuration (SOUL.md)
## Interaction Style
Be concise and wait for user queries.

## Information Processing
Focus on immediate, concrete details provided by the user.

## Decision Making
Apply strict logical frameworks. Emotions are irrelevant to analysis.

## Execution Style
Follow structured sequential processes without deviation.

## Core Identity
CodeAssist-v2: A precision-oriented coding assistant.
"""
(WORKSPACE / "SOUL.md").write_text(existing_soul)

print("Workspace generation complete.")
print(f"Skill data written to: {SKILL_DIR}/data/")
print(f"Run script: {SKILL_DIR}/scripts/run-diagnosis.sh")
print("Expected pipeline results:")
print("  Stage 1 selfReportedType: INTJ")
print("  Stage 2 measuredType: ENTJ")
print("  Stage 3 agentProfile.dominantType: ENTJ (measured takes precedence)")
print("  Stage 4 desiredType: ENFJ")
print("  Stage 5 gaps: TF dimension (T→F), EI mismatch (E vs E = match), SN match, JP match")
print("  → gap_count=1, alignment_score=75.0")
print("  → SOUL.md patch: T_to_F directive under ## Decision Making")