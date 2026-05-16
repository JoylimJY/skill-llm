import sys
import json
import re
import subprocess
from pathlib import Path

def run_detect(script_path, file_path):
    """Run detect.py on a file and return (score, level, hits)."""
    result = subprocess.run(
        ["python3", str(script_path), str(file_path)],
        capture_output=True, text=True
    )
    return result.stdout

def parse_detect_output(output):
    score_match = re.search(r"Score:\s*(\d+)", output)
    level_match = re.search(r"Level:\s*(✅ LOW|⚠️ MODERATE|🚨 HIGH)", output)
    score = int(score_match.group(1)) if score_match else None
    level_raw = level_match.group(1) if level_match else None
    if level_raw:
        if "LOW" in level_raw:
            level = "LOW"
        elif "MODERATE" in level_raw:
            level = "MODERATE"
        elif "HIGH" in level_raw:
            level = "HIGH"
        else:
            level = None
    else:
        level = None
    return score, level

def classify_by_score(score):
    if score is None:
        return None
    if score < 5:
        return "LOW"
    elif score < 15:
        return "MODERATE"
    else:
        return "HIGH"

def main():
    workspace = Path(sys.argv[1])
    checks = []
    
    # ── Find the report file ──────────────────────────────────────────────────
    report_files = list(workspace.rglob("analysis_report.json"))
    if not report_files:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_exists", "passed": False, "detail": "analysis_report.json not found anywhere in workspace"}]
        }))
        return

    report_path = report_files[0]
    checks.append({"name": "report_exists", "passed": True, "detail": f"Found at {report_path}"})

    # ── Parse the report ──────────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "report_parseable", "passed": False, "detail": f"JSON parse error: {e}"}]
        }))
        return

    checks.append({"name": "report_parseable", "passed": True, "detail": "Valid JSON"})

    # ── Ground truth: run detect.py ourselves on all 10 messages ─────────────
    script_path = workspace / "scripts" / "detect.py"
    flagged_dir = workspace / "comms" / "flagged"
    
    ground_truth = {}  # filename -> {"score": int, "level": str}
    for msg_file in sorted(flagged_dir.glob("msg_*.txt")):
        output = run_detect(script_path, msg_file)
        score, level = parse_detect_output(output)
        if score is None:
            level = classify_by_score(score)
        ground_truth[msg_file.name] = {"score": score, "level": level}

    expected_counts = {"LOW": 0, "MODERATE": 0, "HIGH": 0}
    for v in ground_truth.values():
        if v["level"] in expected_counts:
            expected_counts[v["level"]] += 1

    # ── Check 1: all 10 messages are present in the report ───────────────────
    # Accept either a flat list or a dict-of-lists structure
    reported_files = set()
    try:
        # Look for per-file entries anywhere in the structure
        if isinstance(report, dict):
            # Could be {"files": [...]} or {"LOW": [...], "MODERATE": [...], "HIGH": [...]}
            for key, val in report.items():
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict):
                            fname = item.get("file") or item.get("filename") or item.get("name")
                            if fname:
                                reported_files.add(Path(fname).name)
                        elif isinstance(item, str):
                            reported_files.add(Path(item).name)
            # Also check top-level "files" or "results"
            if "files" in report and isinstance(report["files"], list):
                for item in report["files"]:
                    if isinstance(item, dict):
                        fname = item.get("file") or item.get("filename") or item.get("name")
                        if fname:
                            reported_files.add(Path(fname).name)
            if "results" in report and isinstance(report["results"], list):
                for item in report["results"]:
                    if isinstance(item, dict):
                        fname = item.get("file") or item.get("filename") or item.get("name")
                        if fname:
                            reported_files.add(Path(fname).name)
        elif isinstance(report, list):
            for item in report:
                if isinstance(item, dict):
                    fname = item.get("file") or item.get("filename") or item.get("name")
                    if fname:
                        reported_files.add(Path(fname).name)
    except Exception as e:
        reported_files = set()

    all_10_present = len(reported_files) >= 10
    checks.append({
        "name": "all_10_messages_present",
        "passed": all_10_present,
        "detail": f"Found {len(reported_files)} unique file entries; expected 10. Files: {sorted(reported_files)}"
    })

    # ── Check 2: category counts match ground truth ───────────────────────────
    # Accept summary counts under various key names
    reported_counts = {}
    try:
        # Try direct keys
        for level in ["LOW", "MODERATE", "HIGH"]:
            for variant in [level, level.lower(), level.capitalize()]:
                if variant in report:
                    val = report[variant]
                    if isinstance(val, int):
                        reported_counts[level] = val
                    elif isinstance(val, list):
                        reported_counts[level] = len(val)
                    break
        # Try "summary" sub-key
        if "summary" in report and isinstance(report["summary"], dict):
            for level in ["LOW", "MODERATE", "HIGH"]:
                for variant in [level, level.lower(), level.capitalize()]:
                    if variant in report["summary"]:
                        val = report["summary"][variant]
                        if isinstance(val, (int, float)):
                            reported_counts[level] = int(val)
                        elif isinstance(val, list):
                            reported_counts[level] = len(val)
                        break
        # Try "counts" sub-key
        if "counts" in report and isinstance(report["counts"], dict):
            for level in ["LOW", "MODERATE", "HIGH"]:
                for variant in [level, level.lower(), level.capitalize()]:
                    if variant in report["counts"]:
                        val = report["counts"][variant]
                        if isinstance(val, (int, float)):
                            reported_counts[level] = int(val)
                        break
    except Exception as e:
        reported_counts = {}

    counts_correct = True
    counts_detail_parts = []
    for level in ["LOW", "MODERATE", "HIGH"]:
        exp = expected_counts[level]
        got = reported_counts.get(level)
        ok = (got == exp)
        if not ok:
            counts_correct = False
        counts_detail_parts.append(f"{level}: expected={exp}, got={got}")

    checks.append({
        "name": "category_counts_correct",
        "passed": counts_correct,
        "detail": "; ".join(counts_detail_parts) + f" | ground_truth={expected_counts}"
    })

    # ── Check 3: per-file level assignments match ground truth ─────────────────
    per_file_entries = []
    try:
        if isinstance(report, list):
            per_file_entries = report
        elif isinstance(report, dict):
            for key in ["files", "results", "messages"]:
                if key in report and isinstance(report[key], list):
                    per_file_entries = report[key]
                    break
            # Also accept category-keyed lists
            if not per_file_entries:
                for level in ["LOW", "MODERATE", "HIGH"]:
                    for variant in [level, level.lower(), level.capitalize()]:
                        if variant in report and isinstance(report[variant], list):
                            for item in report[variant]:
                                if isinstance(item, dict):
                                    per_file_entries.append({**item, "_reported_level": level})
    except Exception:
        per_file_entries = []

    file_level_map = {}
    for entry in per_file_entries:
        if isinstance(entry, dict):
            fname = entry.get("file") or entry.get("filename") or entry.get("name")
            level_val = (
                entry.get("level") or entry.get("category") or entry.get("risk") or
                entry.get("_reported_level")
            )
            if fname and level_val:
                normalized_level = str(level_val).upper().strip()
                for std in ["LOW", "MODERATE", "HIGH"]:
                    if std in normalized_level:
                        normalized_level = std
                        break
                file_level_map[Path(fname).name] = normalized_level

    correct_assignments = 0
    wrong_assignments = []
    for fname, gt in ground_truth.items():
        reported_level = file_level_map.get(fname)
        if reported_level == gt["level"]:
            correct_assignments += 1
        else:
            wrong_assignments.append(f"{fname}: expected={gt['level']} got={reported_level}")

    per_file_pass = correct_assignments >= 8  # allow up to 2 misses
    checks.append({
        "name": "per_file_level_assignments",
        "passed": per_file_pass,
        "detail": f"{correct_assignments}/10 correct. Wrong: {wrong_assignments}"
    })

    # ── Check 4: threshold semantics — HIGH threshold is 15+ not other values ──
    # Verify that at least one HIGH message has score >= 15 and
    # all LOW messages have score < 5, using ground truth scores
    threshold_ok = True
    threshold_details = []
    for fname, gt in ground_truth.items():
        s = gt["score"]
        expected_level = gt["level"]
        if expected_level == "HIGH" and s < 15:
            threshold_ok = False
            threshold_details.append(f"{fname} score={s} marked HIGH but <15")
        if expected_level == "LOW" and s >= 5:
            threshold_ok = False
            threshold_details.append(f"{fname} score={s} marked LOW but >=5")
        if expected_level == "MODERATE" and (s < 5 or s >= 15):
            threshold_ok = False
            threshold_details.append(f"{fname} score={s} marked MODERATE but outside [5,15)")

    checks.append({
        "name": "correct_threshold_semantics",
        "passed": threshold_ok,
        "detail": "Ground-truth thresholds: LOW=0–4, MODERATE=5–14, HIGH=15+. " +
                  ("; ".join(threshold_details) if threshold_details else "All correct.")
    })

    # ── Check 5: patterns detected are recorded (at least some) ───────────────
    # Check that at least one file entry in the report mentions pattern names
    pattern_names = {
        "urgency", "authority_claims", "social_proof", "fear_uncertainty",
        "grandiosity", "dominance_assertions", "us_vs_them", "emotional_manipulation"
    }
    report_str = json.dumps(report).lower()
    patterns_present = sum(1 for p in pattern_names if p in report_str)
    patterns_check = patterns_present >= 3
    checks.append({
        "name": "pattern_names_in_report",
        "passed": patterns_check,
        "detail": f"Found {patterns_present}/8 canonical pattern names in report JSON. Need at least 3."
    })

    # ── Overall score ─────────────────────────────────────────────────────────
    n_passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    final_score = round(n_passed / total, 3)
    overall_passed = n_passed >= 4  # must pass at least 4/5 checks

    print(json.dumps({
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()