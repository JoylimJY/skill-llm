import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Distractor directory structure ---
dirs = [
    "assets/icons",
    "assets/fonts",
    "config/env",
    "config/feature_flags",
    "logs/2024-01",
    "logs/2024-02",
    "src/components",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "data/students",
    "data/problems",
    "scripts/deploy",
    "docs/internal",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "assets/icons/logo.svg": "<svg></svg>",
    "assets/fonts/README.txt": "Font assets placeholder.",
    "config/env/.env.example": "API_URL=http://localhost:8000\nDEBUG=false\n",
    "config/feature_flags/flags.json": json.dumps({"enable_stateful": False, "max_problems": 5}),
    "logs/2024-01/app.log": "INFO: server started\nERROR: timeout on db\nINFO: retry ok\n",
    "logs/2024-02/app.log": "INFO: session started\nWARN: slow query 450ms\n",
    "src/components/ProblemCard.jsx": "export default function ProblemCard({problem}) { return <div>{problem}</div>; }",
    "src/utils/mathHelpers.js": "export const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);",
    "tests/unit/test_math.py": "def test_add(): assert 1+1 == 2",
    "tests/integration/test_flow.py": "# integration test placeholder",
    "data/students/roster.csv": "student_id,name,grade\nstu001,Alice,3\nstu002,Bob,4\n",
    "data/problems/problem_archive.json": json.dumps([
        {"id": "p001", "topic": "addition", "text": "5 + 3 = ___"},
        {"id": "p002", "topic": "subtraction", "text": "10 - 4 = ___"},
    ]),
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'deploying...'\n",
    "docs/internal/roadmap.md": "## Q3 Roadmap\n- Stateful mode\n- Parent dashboard\n- Weekly reports\n",
    "config/feature_flags/experiments.yaml": "experiments:\n  fraction_mode: disabled\n  weekly_plan: private_only\n",
}

for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.write_text(content, encoding="utf-8")

# --- Mock tool scripts ---

# edu_math_generate: returns INVALID_INPUT for fractions, normal for addition
edu_math_generate_script = r'''#!/usr/bin/env python3
"""
Mock edu_math_generate tool.
Usage: edu_math_generate '<json_params>'
Reads JSON from first argument.
"""
import sys, json

try:
    params = json.loads(sys.argv[1])
except Exception:
    print(json.dumps({"error": "INVALID_INPUT", "message": "JSON parse error"}))
    sys.exit(0)

topic = params.get("topic", "")

# Simulate: fractions topic returns INVALID_INPUT (unsupported in lite)
if topic == "fractions":
    print(json.dumps({"error": "INVALID_INPUT", "message": "topic 'fractions' is not supported in lite mode"}))
    sys.exit(0)

# Normal path for addition
grade = params.get("grade", 3)
count = params.get("count", 2)
difficulty = params.get("difficulty", "easy")

problems = []
import random
random.seed(7)
for i in range(count):
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    problems.append({"id": f"lite_{i+1}", "text": f"{a} + {b} = ___", "topic": topic})

result = {
    "status": "ok",
    "mode": "lite",
    "grade": grade,
    "topic": topic,
    "difficulty": difficulty,
    "problems": problems
}
print(json.dumps(result))
'''

# edu_math_analyze: returns analysis for subtraction problem
edu_math_analyze_script = r'''#!/usr/bin/env python3
"""
Mock edu_math_analyze tool.
Usage: edu_math_analyze '<json_params>'
"""
import sys, json

try:
    params = json.loads(sys.argv[1])
except Exception:
    print(json.dumps({"error": "INVALID_INPUT", "message": "JSON parse error"}))
    sys.exit(0)

problem = params.get("problem", "")
student_answer = params.get("student_answer", "")

if not problem:
    print(json.dumps({"error": "INVALID_INPUT", "message": "problem is required"}))
    sys.exit(0)
if not student_answer:
    print(json.dumps({"error": "INVALID_INPUT", "message": "student_answer is required"}))
    sys.exit(0)

# Specific case: 500 - 263 = ___  student says 247
if "500" in problem and "263" in problem and student_answer.strip() == "247":
    result = {
        "status": "ok",
        "correct": False,
        "correct_answer": "237",
        "error_type": "subtraction_borrow_error",
        "explanation": "The student likely made a borrowing error in the tens or hundreds place.",
        "hint": "Try subtracting step by step: ones, tens, hundreds, borrowing carefully."
    }
    print(json.dumps(result))
    sys.exit(0)

# Generic fallback analysis
try:
    # Try to evaluate simple arithmetic
    import re
    m = re.search(r'(\d+)\s*[-]\s*(\d+)', problem)
    if m:
        correct = int(m.group(1)) - int(m.group(2))
        is_correct = str(correct) == student_answer.strip()
        result = {
            "status": "ok",
            "correct": is_correct,
            "correct_answer": str(correct),
            "explanation": "See calculation." if not is_correct else "Great job!",
        }
        print(json.dumps(result))
        sys.exit(0)
except Exception:
    pass

print(json.dumps({"status": "ok", "correct": False, "correct_answer": "unknown", "explanation": "Could not evaluate."}))
'''

# Write tool scripts
tools_dir = workspace / "tools"
tools_dir.mkdir(exist_ok=True)

(tools_dir / "edu_math_generate").write_text(edu_math_generate_script, encoding="utf-8")
(tools_dir / "edu_math_analyze").write_text(edu_math_analyze_script, encoding="utf-8")

# --- Task specification file (the "messy" input the agent reads) ---
task_spec = {
    "session_id": "sess_20240315_001",
    "requests": [
        {
            "type": "generate_problems",
            "grade": 3,
            "topic": "fractions",
            "count": 4,
            "difficulty": "easy",
            "student_id": None,
            "note": "No student profile yet; anonymous practice session"
        },
        {
            "type": "analyze_answer",
            "problem": "500 - 263 = ___",
            "student_answer": "247",
            "student_id": None,
            "problem_id": None,
            "note": "Child submitted this answer verbally"
        },
        {
            "type": "capability_inquiry",
            "query": "Can you generate a weekly study plan and produce a parent summary report for this child?",
            "note": "Parent asking about extended features"
        }
    ],
    "output_file": "tutor_session.md"
}

(workspace / "session_task.json").write_text(
    json.dumps(task_spec, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("Workspace initialized successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))} items")