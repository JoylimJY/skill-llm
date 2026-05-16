#!/usr/bin/env python3
"""
Evaluation script for model-resource-profiler task.
Usage: python eval.py <workspace_dir>
"""
import sys
import json
import re
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace argument provided."}
        ]}))
        return

    workspace = Path(sys.argv[1])
    checks = []

    # ── Check 1: /tmp/profile_report.md exists ───────────────────────────────
    md_path = Path("/tmp/profile_report.md")
    md_exists = md_path.exists()
    checks.append({
        "name": "md_report_exists",
        "passed": md_exists,
        "detail": f"/tmp/profile_report.md {'found' if md_exists else 'NOT FOUND'}."
    })

    # ── Check 2: /tmp/profile_report.json exists ─────────────────────────────
    json_path = Path("/tmp/profile_report.json")
    json_exists = json_path.exists()
    checks.append({
        "name": "json_report_exists",
        "passed": json_exists,
        "detail": f"/tmp/profile_report.json {'found' if json_exists else 'NOT FOUND'}."
    })

    # ── Check 3: JSON has both 'memory' and 'cpu' top-level keys ─────────────
    report_data = None
    both_keys = False
    try:
        if json_exists:
            report_data = json.loads(json_path.read_text(encoding="utf-8"))
            both_keys = "memory" in report_data and "cpu" in report_data
        detail = (
            f"Keys found: {list(report_data.keys()) if report_data else '(file missing/invalid)'}. "
            f"Both 'memory' and 'cpu' present: {both_keys}."
        )
    except Exception as e:
        detail = f"JSON parse error: {e}"
    checks.append({
        "name": "json_has_both_memory_and_cpu_keys",
        "passed": both_keys,
        "detail": detail
    })

    # ── Check 4: Memory reserved bytes correct (2,682,257,408) ───────────────
    MEM_RESERVED_EXPECTED = 2_682_257_408   # sum of all segment total_size values
    mem_reserved_correct = False
    try:
        if report_data and "memory" in report_data:
            actual = report_data["memory"]["total_reserved_bytes"]
            mem_reserved_correct = (actual == MEM_RESERVED_EXPECTED)
            detail = f"Expected {MEM_RESERVED_EXPECTED}, got {actual}."
        else:
            detail = "Memory key missing from JSON."
    except Exception as e:
        detail = f"Error reading memory.total_reserved_bytes: {e}"
    checks.append({
        "name": "memory_reserved_bytes_correct",
        "passed": mem_reserved_correct,
        "detail": detail
    })

    # ── Check 5: Fragmentation risk is HIGH ──────────────────────────────────
    # inactive = 268435456+268435456+104857600+6291456 = 648019968
    # reserved = 2682257408
    # ratio = 0.2416... > 0.20 → HIGH
    frag_risk_correct = False
    try:
        if report_data and "memory" in report_data:
            risk = report_data["memory"]["fragmentation_risk"]
            frag_risk_correct = (risk == "HIGH")
            detail = f"fragmentation_risk = '{risk}' (expected 'HIGH')."
        else:
            detail = "Memory key missing."
    except Exception as e:
        detail = f"Error: {e}"
    checks.append({
        "name": "fragmentation_risk_is_HIGH",
        "passed": frag_risk_correct,
        "detail": detail
    })

    # ── Check 6: Alloc retries = 14 ──────────────────────────────────────────
    retries_correct = False
    try:
        if report_data and "memory" in report_data:
            retries = report_data["memory"]["alloc_retries"]
            retries_correct = (retries == 14)
            detail = f"alloc_retries = {retries} (expected 14)."
        else:
            detail = "Memory key missing."
    except Exception as e:
        detail = f"Error: {e}"
    checks.append({
        "name": "alloc_retries_equals_14",
        "passed": retries_correct,
        "detail": detail
    })

    # ── Check 7: CPU dominant family is 'dataloader' ─────────────────────────
    # DataLoader::next total: 85000 + 83000 = 168000 µs — highest family
    dominant_correct = False
    try:
        if report_data and "cpu" in report_data:
            dom = report_data["cpu"]["dominant_family"]
            dominant_correct = (dom == "dataloader")
            detail = f"dominant_family = '{dom}' (expected 'dataloader')."
        else:
            detail = "CPU key missing."
    except Exception as e:
        detail = f"Error: {e}"
    checks.append({
        "name": "cpu_dominant_family_dataloader",
        "passed": dominant_correct,
        "detail": detail
    })

    # ── Check 8: Top CPU op in JSON is DataLoader::next ──────────────────────
    top_op_correct = False
    try:
        if report_data and "cpu" in report_data:
            top_ops = report_data["cpu"].get("top_ops", [])
            if top_ops:
                top_name = top_ops[0]["name"]
                top_op_correct = (top_name == "DataLoader::next")
                detail = f"top_ops[0].name = '{top_name}' (expected 'DataLoader::next')."
            else:
                detail = "top_ops list is empty."
        else:
            detail = "CPU key missing."
    except Exception as e:
        detail = f"Error: {e}"
    checks.append({
        "name": "top_cpu_op_is_DataLoader_next",
        "passed": top_op_correct,
        "detail": detail
    })

    # ── Check 9: Markdown contains Memory Analysis section ───────────────────
    md_has_memory = False
    try:
        if md_exists:
            md_text = md_path.read_text(encoding="utf-8")
            md_has_memory = "## Memory Analysis" in md_text or "Memory Analysis" in md_text
            detail = f"'Memory Analysis' section {'found' if md_has_memory else 'NOT found'} in markdown."
        else:
            detail = "Markdown file missing."
    except Exception as e:
        detail = f"Error: {e}"
    checks.append({
        "name": "md_has_memory_section",
        "passed": md_has_memory,
        "detail": detail
    })

    # ── Check 10: Markdown contains CPU Trace section ─────────────────────────
    md_has_cpu = False
    try:
        if md_exists:
            md_text = md_path.read_text(encoding="utf-8")
            md_has_cpu = "CPU Trace" in md_text or "## CPU" in md_text
            detail = f"'CPU Trace' section {'found' if md_has_cpu else 'NOT found'} in markdown."
        else:
            detail = "Markdown file missing."
    except Exception as e:
        detail = f"Error: {e}"
    checks.append({
        "name": "md_has_cpu_section",
        "passed": md_has_cpu,
        "detail": detail
    })

    # ── Check 11: Markdown contains fragmentation risk mention ────────────────
    md_has_frag = False
    try:
        if md_exists:
            md_text = md_path.read_text(encoding="utf-8")
            md_has_frag = bool(re.search(r'[Ff]ragment', md_text))
            detail = f"Fragmentation mention {'found' if md_has_frag else 'NOT found'} in markdown."
        else:
            detail = "Markdown file missing."
    except Exception as e:
        detail = f"Error: {e}"
    checks.append({
        "name": "md_mentions_fragmentation",
        "passed": md_has_frag,
        "detail": detail
    })

    # ── Check 12: CPU event count = 26 (all X-phase cpu_op events) ───────────
    event_count_correct = False
    try:
        if report_data and "cpu" in report_data:
            ec = report_data["cpu"]["event_count"]
            event_count_correct = (ec == 26)
            detail = f"event_count = {ec} (expected 26)."
        else:
            detail = "CPU key missing."
    except Exception as e:
        detail = f"Error: {e}"
    checks.append({
        "name": "cpu_event_count_is_26",
        "passed": event_count_correct,
        "detail": detail
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 10  # require at least 10/12

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()