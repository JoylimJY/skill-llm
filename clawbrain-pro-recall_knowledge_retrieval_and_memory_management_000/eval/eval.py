import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    # Find the recall report file
    report_path = None
    candidates = list(Path(workspace).rglob("cx7749_recall_report.md"))
    if not candidates:
        # Also accept recall_report.md or similar in root
        candidates = list(Path(workspace).rglob("recall_report.md"))
    if not candidates:
        candidates = list(Path(workspace).rglob("*recall*report*.md"))
    if not candidates:
        candidates = list(Path(workspace).rglob("*recall*.md"))

    if candidates:
        report_path = candidates[0]

    # Check 1: Report file exists
    check_exists = {
        "name": "recall_report_file_exists",
        "passed": report_path is not None,
        "detail": f"Found at {report_path}" if report_path else "No recall report file found (expected cx7749_recall_report.md or similar)"
    }
    checks.append(check_exists)

    if not report_path:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = report_path.read_text(encoding="utf-8").lower()
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # Check 2: Report references Layer 1 (memory/) findings
    # Expects mention of memory files that matched CX-7749
    layer1_files_expected = [
        "2024-11-15_meeting_notes",
        "2024-11-20_lab_update"
    ]
    layer1_hits = [f for f in layer1_files_expected if f.lower() in content]
    check_layer1 = {
        "name": "layer1_memory_results_present",
        "passed": len(layer1_hits) >= 1,
        "detail": f"Found references to Layer 1 files: {layer1_hits}. Expected at least one of {layer1_files_expected}"
    }
    checks.append(check_layer1)

    # Check 3: Report references Layer 2 (archive/) findings
    layer2_files_expected = [
        "2024-06-10_early_synthesis",
        "2024-07-22_regulatory_note"
    ]
    layer2_hits = [f for f in layer2_files_expected if f.lower() in content]
    check_layer2 = {
        "name": "layer2_archive_results_present",
        "passed": len(layer2_hits) >= 1,
        "detail": f"Found references to Layer 2 archive files: {layer2_hits}. Expected at least one of {layer2_files_expected}"
    }
    checks.append(check_layer2)

    # Check 4: Report references Layer 3 (workspace-wide) findings
    layer3_files_expected = [
        "batch_log_001",
        "batch_log_003",
        "assay_a12_raw",
        "q3_summary",
        "literature_refs"
    ]
    layer3_hits = [f for f in layer3_files_expected if f.lower() in content]
    check_layer3 = {
        "name": "layer3_workspace_results_present",
        "passed": len(layer3_hits) >= 2,
        "detail": f"Found references to Layer 3 workspace files: {layer3_hits}. Expected at least 2 of {layer3_files_expected}"
    }
    checks.append(check_layer3)

    # Check 5: Report explicitly distinguishes layers (proprietary cascade logic)
    layer_indicators = [
        any(kw in content for kw in ["layer 1", "第1层", "第 1 层", "recent memory", "memory/", "近期记忆", "层1", "tier 1", "level 1"]),
        any(kw in content for kw in ["layer 2", "第2层", "第 2 层", "archive", "memory/archive", "归档", "层2", "tier 2", "level 2"]),
        any(kw in content for kw in ["layer 3", "第3层", "第 3 层", "workspace", "全局", "层3", "tier 3", "level 3", "global"]),
    ]
    layers_documented = sum(layer_indicators)
    check_layers_distinguished = {
        "name": "cascade_layers_explicitly_distinguished",
        "passed": layers_documented >= 2,
        "detail": f"Report distinguishes {layers_documented}/3 search layers. Must distinguish at least 2 layers per the proprietary cascade architecture."
    }
    checks.append(check_layers_distinguished)

    # Check 6: CX-7749 is the search subject (report is on-topic)
    cx7749_mentioned = "cx-7749" in content or "cx7749" in content
    check_topic = {
        "name": "report_is_about_cx7749",
        "passed": cx7749_mentioned,
        "detail": "Report content mentions CX-7749 as the search subject" if cx7749_mentioned else "Report does not mention CX-7749"
    }
    checks.append(check_topic)

    # Check 7: Distractor files NOT falsely included (no false positives from non-CX7749 files)
    false_positives = [
        "cx-6000", "cx-3200", "cx-6500", "cx-9000", "assay_b05", "deprecated_protocol",
        "q4_forecast", "sop_hplc", "onboarding"
    ]
    false_pos_hits = [f for f in false_positives if f in content]
    # Allow up to 1 false positive (e.g., agent may mention compound library which lists many)
    check_no_false_positives = {
        "name": "distractor_files_not_falsely_included",
        "passed": len(false_pos_hits) <= 2,
        "detail": f"False positive distractor references found: {false_pos_hits}. Threshold: <= 2 allowed."
    }
    checks.append(check_no_false_positives)

    # Check 8: Report has meaningful structure (not just a dump)
    has_structure = any(kw in content for kw in [
        "#", "##", "result", "found", "summary", "finding", "retrieved", "recall"
    ])
    check_structured = {
        "name": "report_has_meaningful_structure",
        "passed": has_structure,
        "detail": "Report appears to have structured sections/headings" if has_structure else "Report is unstructured or empty"
    }
    checks.append(check_structured)

    # Score calculation
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)

    # Overall pass: must pass existence, at least 2 layers found, layers distinguished, on-topic, no bad FPs
    critical_checks = [
        "recall_report_file_exists",
        "layer1_memory_results_present",
        "layer2_archive_results_present",
        "cascade_layers_explicitly_distinguished",
        "report_is_about_cx7749",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )

    return {
        "passed": critical_passed and score >= 0.7,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))