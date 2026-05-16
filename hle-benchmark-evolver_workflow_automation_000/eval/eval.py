import sys
import json
import os
import subprocess
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── Check 1: The agent produced a result snapshot JSON file ──────────────────
result_file = None
candidates = list(Path(workspace).rglob("benchmark_result*.json")) + \
             list(Path(workspace).rglob("hle_result*.json")) + \
             list(Path(workspace).rglob("result_snapshot*.json")) + \
             list(Path(workspace).rglob("evolution_result*.json")) + \
             list(Path(workspace).rglob("hle_evolution_result*.json")) + \
             list(Path(workspace).rglob("run_result_output*.json")) + \
             list(Path(workspace).rglob("snapshot*.json"))

# Also check common names
for name in ["benchmark_result.json", "hle_result.json", "result_snapshot.json",
             "evolution_result.json", "hle_evolution_result.json"]:
    p = Path(workspace) / name
    if p.exists():
        candidates.append(p)

# Filter out distractor files we know about
known_distractors = {"snapshot_old.json", "hle_report.template.json", "aggregated_scores.csv"}
candidates = [c for c in candidates if c.name not in known_distractors and c.is_file()]

result_data = None
result_path = None
for c in candidates:
    try:
        with open(c) as f:
            data = json.load(f)
        # Must have at least some output contract fields
        required_fields = {"benchmark_id", "run_id", "accuracy", "reward", "trend",
                           "curriculum_stage", "queue_size", "focus_subjects",
                           "focus_modalities", "next_questions"}
        if required_fields.issubset(set(data.keys())):
            result_data = data
            result_path = c
            break
    except Exception:
        continue

if result_data is None:
    # Try to find any json with required fields more broadly
    for c in Path(workspace).rglob("*.json"):
        if c.name in known_distractors:
            continue
        try:
            with open(c) as f:
                data = json.load(f)
            required_fields = {"benchmark_id", "run_id", "accuracy", "reward", "trend",
                               "curriculum_stage", "queue_size", "focus_subjects",
                               "focus_modalities", "next_questions"}
            if required_fields.issubset(set(data.keys())):
                result_data = data
                result_path = c
                break
        except Exception:
            continue

total_score += add_check(
    "result_snapshot_file_exists",
    result_data is not None,
    f"Found result snapshot at {result_path}" if result_data else "No valid result snapshot JSON found with all 10 required output contract fields.",
    weight=1.0
)

# ── Check 2: All 10 Output Contract fields present ────────────────────────────
if result_data:
    required_fields = ["benchmark_id", "run_id", "accuracy", "reward", "trend",
                       "curriculum_stage", "queue_size", "focus_subjects",
                       "focus_modalities", "next_questions"]
    missing = [f for f in required_fields if f not in result_data]
    total_score += add_check(
        "all_output_contract_fields_present",
        len(missing) == 0,
        f"All 10 fields present." if not missing else f"Missing fields: {missing}",
        weight=1.5
    )
else:
    checks.append({"name": "all_output_contract_fields_present", "passed": False,
                   "detail": "Skipped — no result file found."})

# ── Check 3: benchmark_id is correct ─────────────────────────────────────────
if result_data:
    bid = result_data.get("benchmark_id", "")
    total_score += add_check(
        "benchmark_id_correct",
        bid == "cais/hle",
        f"benchmark_id='{bid}' (expected 'cais/hle')",
        weight=0.5
    )
else:
    checks.append({"name": "benchmark_id_correct", "passed": False, "detail": "Skipped."})

# ── Check 4: accuracy is a valid float in [0,1] ───────────────────────────────
if result_data:
    acc = result_data.get("accuracy")
    valid_acc = isinstance(acc, (int, float)) and 0.0 <= float(acc) <= 1.0
    total_score += add_check(
        "accuracy_is_valid_float",
        valid_acc,
        f"accuracy={acc}",
        weight=0.5
    )
else:
    checks.append({"name": "accuracy_is_valid_float", "passed": False, "detail": "Skipped."})

# ── Check 5: accuracy matches expected value from the raw report ───────────────
# The raw report has 153 questions. We recalculate expected accuracy.
raw_report_path = Path(workspace) / "data/raw_evals/hle_candidate_run.json"
expected_accuracy = None
if raw_report_path.exists():
    try:
        with open(raw_report_path) as f:
            raw = json.load(f)
        qs = raw.get("questions", [])
        total_q = len(qs)
        correct_q = sum(1 for q in qs if q.get("correct") is True)
        expected_accuracy = round(correct_q / total_q, 4) if total_q > 0 else 0.0
    except Exception as e:
        expected_accuracy = None

if result_data and expected_accuracy is not None:
    acc = result_data.get("accuracy", -1)
    # Allow small floating point tolerance
    match = abs(float(acc) - expected_accuracy) < 0.005
    total_score += add_check(
        "accuracy_matches_raw_report",
        match,
        f"accuracy={acc}, expected≈{expected_accuracy} (from raw report with {total_q} questions)",
        weight=2.0
    )
else:
    checks.append({"name": "accuracy_matches_raw_report", "passed": False,
                   "detail": f"Skipped or raw report unreadable. expected_accuracy={expected_accuracy}"})

# ── Check 6: curriculum_stage is valid value ──────────────────────────────────
if result_data:
    valid_stages = {"foundational", "developing", "proficient", "advanced"}
    stage = result_data.get("curriculum_stage", "")
    total_score += add_check(
        "curriculum_stage_valid",
        stage in valid_stages,
        f"curriculum_stage='{stage}'",
        weight=0.5
    )
else:
    checks.append({"name": "curriculum_stage_valid", "passed": False, "detail": "Skipped."})

# ── Check 7: focus_subjects is a non-empty list ────────────────────────────────
if result_data:
    fs = result_data.get("focus_subjects", [])
    ok = isinstance(fs, list) and len(fs) > 0
    total_score += add_check(
        "focus_subjects_nonempty_list",
        ok,
        f"focus_subjects={fs}",
        weight=0.5
    )
else:
    checks.append({"name": "focus_subjects_nonempty_list", "passed": False, "detail": "Skipped."})

# ── Check 8: next_questions is a list of question_ids ─────────────────────────
if result_data:
    nq = result_data.get("next_questions", [])
    ok = isinstance(nq, list) and len(nq) > 0 and all(isinstance(x, str) for x in nq)
    total_score += add_check(
        "next_questions_valid_list",
        ok,
        f"next_questions={nq[:5]}",
        weight=0.5
    )
else:
    checks.append({"name": "next_questions_valid_list", "passed": False, "detail": "Skipped."})

# ── Check 9: trend is one of the valid values ─────────────────────────────────
if result_data:
    valid_trends = {"improving", "declining", "stable"}
    trend = result_data.get("trend", "")
    total_score += add_check(
        "trend_is_valid",
        trend in valid_trends,
        f"trend='{trend}'",
        weight=0.5
    )
else:
    checks.append({"name": "trend_is_valid", "passed": False, "detail": "Skipped."})

# ── Check 10: The agent used the raw report (not the default template) ─────────
# The template has 200 questions, the raw report has 153 questions.
# If accuracy matches raw report (≠ template accuracy), agent used the right file.
if result_data and expected_accuracy is not None:
    template_path_chk = Path(workspace) / "skills/capability-evolver/assets/gep/hle_report.template.json"
    try:
        with open(template_path_chk) as f:
            tpl = json.load(f)
        tqs = tpl.get("questions", [])
        t_total = len(tqs)
        t_correct = sum(1 for q in tqs if q.get("correct") is True)
        template_accuracy = round(t_correct / t_total, 4) if t_total > 0 else 0.0
    except Exception:
        template_accuracy = None

    acc = float(result_data.get("accuracy", -999))
    if template_accuracy is not None:
        used_raw = abs(acc - expected_accuracy) < 0.005 and abs(acc - template_accuracy) > 0.005
        # Also pass if they happen to match (extremely unlikely with random seed 42)
        total_score += add_check(
            "used_raw_report_not_template",
            used_raw,
            f"accuracy={acc}, raw_expected={expected_accuracy}, template_expected={template_accuracy}. Agent used {'raw report ✓' if used_raw else 'default template or wrong file ✗'}",
            weight=2.0
        )
    else:
        checks.append({"name": "used_raw_report_not_template", "passed": False,
                       "detail": "Could not compute template accuracy."})
else:
    checks.append({"name": "used_raw_report_not_template", "passed": False,
                   "detail": "Skipped."})

# ── Check 11: run_id is a non-empty string (SHA256 hex prefix) ────────────────
if result_data:
    run_id = result_data.get("run_id", "")
    ok = isinstance(run_id, str) and len(run_id) >= 8
    total_score += add_check(
        "run_id_nonempty_string",
        ok,
        f"run_id='{run_id}'",
        weight=0.5
    )
else:
    checks.append({"name": "run_id_nonempty_string", "passed": False, "detail": "Skipped."})

# ── Check 12: queue_size > 0 (there are incorrect questions) ─────────────────
if result_data:
    qs_val = result_data.get("queue_size", -1)
    ok = isinstance(qs_val, int) and qs_val > 0
    total_score += add_check(
        "queue_size_positive",
        ok,
        f"queue_size={qs_val}",
        weight=0.5
    )
else:
    checks.append({"name": "queue_size_positive", "passed": False, "detail": "Skipped."})

# ── Score normalization ────────────────────────────────────────────────────────
max_possible = 1.0 + 1.5 + 0.5 + 0.5 + 2.0 + 0.5 + 0.5 + 0.5 + 0.5 + 2.0 + 0.5 + 0.5
normalized = min(1.0, total_score / max_possible)
passed = normalized >= 0.75

output = {
    "passed": passed,
    "score": round(normalized, 4),
    "checks": checks
}

print(json.dumps(output, indent=2))