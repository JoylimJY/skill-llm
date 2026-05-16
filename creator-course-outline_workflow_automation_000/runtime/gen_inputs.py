import os
import json
import random
import pathlib

random.seed(42)

workspace = pathlib.Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "skill-creator-course-outline/scripts",
    "skill-creator-course-outline/resources",
    "skill-creator-course-outline/examples",
    "skill-creator-course-outline/tests",
    "skill-creator-course-outline/cache",
    "skill-creator-course-outline/logs",
    "projects/vertical-farming-course",
    "projects/vertical-farming-course/raw_notes",
    "projects/vertical-farming-course/drafts",
    "projects/vertical-farming-course/assets",
    "internal/archive",
    "internal/templates",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

base = workspace / "skill-creator-course-outline"

# ── spec.json ────────────────────────────────────────────────────────────────
spec = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "CourseOutlineSpec",
    "version": "1.0.0",
    "description": "Specification for course outline output produced by creator-course-outline skill.",
    "required_sections": [
        "task_brief",
        "pending_confirmations",
        "course_objectives",
        "module_structure",
        "unit_objectives",
        "assignments",
        "milestones",
        "common_blockers"
    ],
    "field_constraints": {
        "task_brief": {
            "type": "string",
            "description": "Restructured task brief assembled from user inputs. Must be present even if sparse."
        },
        "pending_confirmations": {
            "type": "array",
            "description": "List of items needing confirmation before finalization. MUST be non-empty when any input field is missing or ambiguous.",
            "item_type": "string"
        },
        "course_objectives": {
            "type": "array",
            "min_items": 2,
            "max_items": 6,
            "item_type": "string",
            "description": "Top-level measurable learning objectives for the whole course."
        },
        "module_structure": {
            "type": "array",
            "min_items": 3,
            "max_items": 8,
            "description": "Ordered list of modules.",
            "item_schema": {
                "module_id": "string (e.g. M01, M02 ...)",
                "module_title": "string",
                "duration_hours": "number (float allowed)",
                "difficulty_level": "enum: [beginner, intermediate, advanced]",
                "description": "string"
            }
        },
        "unit_objectives": {
            "type": "array",
            "description": "Per-unit learning objectives, each linked to a module_id.",
            "item_schema": {
                "module_id": "string",
                "unit_title": "string",
                "objectives": "array of strings (min 1)"
            }
        },
        "assignments": {
            "type": "array",
            "min_items": 2,
            "description": "Assignments for the course.",
            "item_schema": {
                "assignment_id": "string (e.g. A01)",
                "title": "string",
                "linked_module_id": "string",
                "format": "enum: [written, project, quiz, peer-review, presentation]",
                "due_after_module": "boolean"
            }
        },
        "milestones": {
            "type": "array",
            "min_items": 2,
            "description": "Course milestones.",
            "item_schema": {
                "milestone_id": "string (e.g. MS01)",
                "title": "string",
                "milestone_type": "enum: [checkpoint, capstone, review, onboarding]",
                "linked_module_id": "string or null"
            }
        },
        "common_blockers": {
            "type": "array",
            "min_items": 3,
            "description": "Common student blockers/pain points for this course type.",
            "item_type": "string"
        }
    },
    "output_format": "json",
    "output_filename_convention": "course_outline_{course_slug}.json",
    "notes": [
        "The task_brief must appear FIRST in the output.",
        "pending_confirmations must be explicitly listed even if empty array.",
        "module_id values must be zero-padded two-digit strings prefixed with M (M01, M02, ...).",
        "assignment_id values must be zero-padded two-digit strings prefixed with A (A01, A02, ...).",
        "milestone_id values must be zero-padded two-digit strings prefixed with MS (MS01, MS02, ...).",
        "difficulty_level must be exactly one of: beginner, intermediate, advanced.",
        "assignment format must be exactly one of: written, project, quiz, peer-review, presentation.",
        "milestone_type must be exactly one of: checkpoint, capstone, review, onboarding."
    ]
}

with open(base / "resources/spec.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)

# ── template.md ──────────────────────────────────────────────────────────────
template_md = """\
# 课程大纲草案

## 任务书 (Task Brief)
{{task_brief}}

## 待确认项 (Pending Confirmations)
{{#each pending_confirmations}}
- {{this}}
{{/each}}

## 课程目标 (Course Objectives)
{{#each course_objectives}}
- {{this}}
{{/each}}

## 模块结构 (Module Structure)
{{#each module_structure}}
### {{module_id}} – {{module_title}}
- 时长: {{duration_hours}} 小时
- 难度: {{difficulty_level}}
- 描述: {{description}}
{{/each}}

## 单元目标 (Unit Objectives)
{{#each unit_objectives}}
#### [{{module_id}}] {{unit_title}}
{{#each objectives}}
  - {{this}}
{{/each}}
{{/each}}

## 作业 (Assignments)
{{#each assignments}}
- {{assignment_id}}: {{title}} | 模块: {{linked_module_id}} | 形式: {{format}} | 模块结束后提交: {{due_after_module}}
{{/each}}

## 里程碑 (Milestones)
{{#each milestones}}
- {{milestone_id}}: {{title}} | 类型: {{milestone_type}} | 关联模块: {{linked_module_id}}
{{/each}}

## 学员常见卡点 (Common Blockers)
{{#each common_blockers}}
- {{this}}
{{/each}}
"""

with open(base / "resources/template.md", "w", encoding="utf-8") as f:
    f.write(template_md)

# ── run.py ───────────────────────────────────────────────────────────────────
# This script is the canonical processor: it reads an input JSON,
# validates required input fields, and writes the output JSON.
run_py = '''\
#!/usr/bin/env python3
"""
creator-course-outline run.py
Usage:
  python3 run.py --input <input_json_path> --output <output_json_path>

Input JSON expected fields:
  course_title      (str, required)
  target_audience   (str, required)
  course_goal       (str, required)
  duration_weeks    (int, optional – if missing, add to pending_confirmations)
  num_modules       (int, optional – if missing, default 4, add to pending_confirmations)
  difficulty        (str, optional – one of beginner/intermediate/advanced)
  course_slug       (str, optional – derived from course_title if absent)

The script reads {baseDir}/resources/spec.json to validate output schema constraints.
It produces a JSON file matching spec.json\'s required_sections and field_constraints.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r\'[^\\w\\s-]\', \'\', text)
    text = re.sub(r\'[\\s_-]+\', \'-\', text)
    return text

def load_spec(base_dir):
    spec_path = Path(base_dir) / "resources" / "spec.json"
    with open(spec_path, encoding="utf-8") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Generate course outline JSON")
    parser.add_argument("--input", required=True, help="Path to input JSON file")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    spec = load_spec(base_dir)

    with open(args.input, encoding="utf-8") as f:
        inp = json.load(f)

    # Validate required input fields
    missing_required = []
    for field in ["course_title", "target_audience", "course_goal"]:
        if field not in inp or not inp[field]:
            missing_required.append(field)

    if missing_required:
        print(f"ERROR: Missing required input fields: {missing_required}", file=sys.stderr)
        sys.exit(1)

    pending = []
    if "duration_weeks" not in inp:
        pending.append("请确认课程总时长（周数）")
    if "num_modules" not in inp:
        pending.append("请确认模块数量（默认使用4个模块）")
    if "difficulty" not in inp:
        pending.append("请确认整体难度定位（beginner / intermediate / advanced）")

    difficulty = inp.get("difficulty", "intermediate")
    valid_difficulties = ["beginner", "intermediate", "advanced"]
    if difficulty not in valid_difficulties:
        pending.append(f"难度值 \'{difficulty}\' 无效，已回退为 intermediate")
        difficulty = "intermediate"

    num_modules = int(inp.get("num_modules", 4))
    num_modules = max(3, min(num_modules, 8))

    course_title = inp["course_title"]
    target_audience = inp["target_audience"]
    course_goal = inp["course_goal"]
    duration_weeks = inp.get("duration_weeks", "待定")
    course_slug = inp.get("course_slug", slugify(course_title))

    task_brief = (
        f"课程名称：{course_title}。"
        f"目标受众：{target_audience}。"
        f"课程目标：{course_goal}。"
        f"时长：{duration_weeks} 周。"
        f"模块数：{num_modules}。"
        f"难度：{difficulty}。"
    )

    # Generate modules
    module_titles_pool = [
        "课程导论与背景", "核心理论基础", "技术与方法论",
        "实践操作入门", "进阶技能培养", "案例分析与实战",
        "综合项目实践", "总结与持续学习路径"
    ]
    modules = []
    for i in range(num_modules):
        mid = f"M{str(i+1).zfill(2)}"
        title = module_titles_pool[i] if i < len(module_titles_pool) else f"模块 {i+1}"
        dur = round(2.0 + i * 0.5, 1)
        diff = difficulty if i > 0 else "beginner"
        if diff not in valid_difficulties:
            diff = "beginner"
        modules.append({
            "module_id": mid,
            "module_title": title,
            "duration_hours": dur,
            "difficulty_level": diff,
            "description": f"本模块聚焦于{course_title}中的{title}相关内容，面向{target_audience}。"
        })

    # Generate unit objectives
    unit_objectives = []
    for m in modules:
        unit_objectives.append({
            "module_id": m["module_id"],
            "unit_title": f"{m[\'module_title\']} – 核心单元",
            "objectives": [
                f"理解{m[\'module_title\']}的核心概念",
                f"能够在实际场景中应用{m[\'module_title\']}的方法"
            ]
        })

    # Generate assignments
    assignments = []
    assignment_formats = ["written", "project", "quiz", "peer-review", "presentation"]
    for i, m in enumerate(modules[:max(2, num_modules)]):
        aid = f"A{str(i+1).zfill(2)}"
        fmt = assignment_formats[i % len(assignment_formats)]
        assignments.append({
            "assignment_id": aid,
            "title": f"{m[\'module_title\']}作业",
            "linked_module_id": m["module_id"],
            "format": fmt,
            "due_after_module": True
        })

    # Generate milestones
    milestones = [
        {
            "milestone_id": "MS01",
            "title": "入门确认里程碑",
            "milestone_type": "onboarding",
            "linked_module_id": modules[0]["module_id"] if modules else None
        },
        {
            "milestone_id": "MS02",
            "title": "中期学习检查点",
            "milestone_type": "checkpoint",
            "linked_module_id": modules[num_modules // 2]["module_id"] if num_modules >= 2 else None
        },
        {
            "milestone_id": "MS03",
            "title": "课程综合收官项目",
            "milestone_type": "capstone",
            "linked_module_id": modules[-1]["module_id"] if modules else None
        }
    ]

    common_blockers = [
        f"学员对{course_title}领域缺乏背景知识，导致理论部分理解困难",
        "实践练习与理论脱节，缺乏足够的动手场景",
        "课程节奏过快，{target_audience}难以跟上进度",
        "缺少同伴学习与反馈机制，学员容易产生孤独感",
        "作业反馈周期过长，影响学习动力"
    ]

    output = {
        "task_brief": task_brief,
        "pending_confirmations": pending,
        "course_objectives": [
            f"学员能够描述{course_title}的核心原理与应用场景",
            f"学员能够独立完成{course_title}相关的基础实践任务",
            f"学员能够识别{course_title}领域的常见问题并提出解决方案",
            f"学员能够将{course_title}知识迁移到真实的工作或生活场景"
        ],
        "module_structure": modules,
        "unit_objectives": unit_objectives,
        "assignments": assignments,
        "milestones": milestones,
        "common_blockers": common_blockers,
        "_meta": {
            "generated_by": "creator-course-outline v1.0.0",
            "spec_version": spec.get("version", "unknown"),
            "course_slug": course_slug,
            "output_filename": f"course_outline_{course_slug}.json"
        }
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[run.py] Output written to: {out_path}")
    print(f"[run.py] Pending confirmations: {len(pending)}")
    print(f"[run.py] Modules generated: {num_modules}")

if __name__ == "__main__":
    main()
'''

with open(base / "scripts/run.py", "w", encoding="utf-8") as f:
    f.write(run_py)

# ── examples/ ────────────────────────────────────────────────────────────────
example_input = {
    "course_title": "Python 数据分析入门",
    "target_audience": "非技术背景的业务分析师",
    "course_goal": "掌握 Pandas 与可视化基础",
    "duration_weeks": 6,
    "num_modules": 4,
    "difficulty": "beginner"
}
with open(base / "examples/example_input.json", "w", encoding="utf-8") as f:
    json.dump(example_input, f, ensure_ascii=False, indent=2)

example_output = {
    "task_brief": "课程名称：Python 数据分析入门。目标受众：非技术背景的业务分析师。...",
    "pending_confirmations": [],
    "course_objectives": ["示例目标1", "示例目标2"],
    "module_structure": [],
    "unit_objectives": [],
    "assignments": [],
    "milestones": [],
    "common_blockers": [],
    "_meta": {"generated_by": "creator-course-outline v1.0.0"}
}
with open(base / "examples/example_output.json", "w", encoding="utf-8") as f:
    json.dump(example_output, f, ensure_ascii=False, indent=2)

# ── tests/smoke-test.md ──────────────────────────────────────────────────────
smoke_test = """\
# Smoke Test – creator-course-outline

## Test 1: Basic run with full inputs
```bash
python3 scripts/run.py --input examples/example_input.json --output /tmp/test_out.json
```
Expected: exit code 0, output file exists, all 8 required sections present.

## Test 2: Missing optional fields
Run with input missing `duration_weeks`, `num_modules`, `difficulty`.
Expected: `pending_confirmations` array has at least 3 items.

## Test 3: Invalid difficulty value
Run with `difficulty: "expert"`.
Expected: `pending_confirmations` contains a notice, difficulty falls back to `intermediate`.
"""
with open(base / "tests/smoke-test.md", "w", encoding="utf-8") as f:
    f.write(smoke_test)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "projects/vertical-farming-course/raw_notes/interview_notes.txt": (
        "Interview with lead educator:\n"
        "- Course: Urban Vertical Farming Techniques for Community Educators\n"
        "- Audience: Community center staff, urban agriculture volunteers, NGO educators\n"
        "- Goal: Enable participants to design and manage small-scale vertical farms in urban community spaces\n"
        "- Total duration: 8 weeks\n"
        "- Modules planned: 5\n"
        "- Difficulty: intermediate\n"
        "- Key topics: hydroponics basics, LED lighting, nutrient management, crop selection, community outreach\n"
        "- Pain points noted: learners lack prior agriculture background; hands-on sessions hard to schedule\n"
        "- No budget for fancy equipment\n"
        "- Slug idea: urban-vertical-farming-community\n"
    ),
    "projects/vertical-farming-course/raw_notes/stakeholder_requirements.txt": (
        "Stakeholder: GreenRoots NGO\n"
        "Request: Structured course blueprint for board review by end of sprint.\n"
        "Format needed: JSON file that the LMS team can import.\n"
        "Filename should follow project convention: course_outline_<slug>.json\n"
        "Must include learning objectives per module, assignments with clear formats, and milestones.\n"
        "Board wants to see what students might struggle with (blockers).\n"
        "Note: we don't have confirmation on whether 8 weeks or 10 weeks yet.\n"
    ),
    "projects/vertical-farming-course/drafts/old_outline_v1.txt": (
        "OLD DRAFT - DO NOT USE\n"
        "Module 1: Intro\n"
        "Module 2: Soil-free growing\n"
        "Module 3: Light & Environment\n"
        "This was rejected by the education committee. Missing objectives and milestones.\n"
    ),
    "projects/vertical-farming-course/assets/logo_placeholder.txt": "Logo file placeholder (binary not shown)",
    "internal/archive/deprecated_template_2022.md": (
        "# OLD TEMPLATE (deprecated)\nDo not use. Replaced by resources/template.md in the skill bundle.\n"
    ),
    "internal/templates/generic_course_template.txt": (
        "Generic template – not compliant with spec.json. Use skill resources instead.\n"
    ),
    "tmp/scratch.txt": "Scratch notes – ignore\ncourse name: vertical farming\naudience: community educators\n",
    "skill-creator-course-outline/logs/run_2024_01_10.log": (
        "[INFO] run.py invoked\n[INFO] Input: example_input.json\n[INFO] Output: /tmp/out.json\n[INFO] Done.\n"
    ),
    "skill-creator-course-outline/cache/last_slug.txt": "python-data-analysis\n",
    "projects/vertical-farming-course/drafts/budget_notes.txt": (
        "Estimated course production cost: $2,400\n"
        "No additional tooling budget.\n"
        "LMS: open-source Moodle instance.\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# ── Messy / incomplete raw input that the agent must NOT use directly ─────────
# The agent must synthesize a proper input JSON from the raw notes above.
# We deliberately do NOT provide a ready-made input JSON in the project dir.
raw_messy = {
    "INCOMPLETE_DO_NOT_USE": True,
    "course": "Urban Vertical Farming",
    "who": "community center staff",
    "why": "to grow food in cities",
    "weeks": "maybe 8 or 10 TBD",
    "mods": "5?",
    "level": "mid"
}
with open(workspace / "projects/vertical-farming-course/raw_notes/partial_data.json", "w", encoding="utf-8") as f:
    json.dump(raw_messy, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print("Key paths:")
print(f"  Skill base: /workspace/skill-creator-course-outline/")
print(f"  Raw notes:  /workspace/projects/vertical-farming-course/raw_notes/")
print(f"  run.py:     /workspace/skill-creator-course-outline/scripts/run.py")