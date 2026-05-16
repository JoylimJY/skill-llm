#!/usr/bin/env python3
"""
Evaluation script for case-study-factory task.
Usage: python3 eval_script.py <workspace_dir>
"""
import json
import sys
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    ws = Path(workspace)

    # ── Locate output file ──────────────────────────────────────────────────
    # Agent is told to name the file patient_archive_case_study.md
    candidates = list(ws.rglob("patient_archive_case_study.md"))

    def add(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    if not candidates:
        add("output_file_exists", False,
            "patient_archive_case_study.md not found anywhere in workspace.")
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks,
        }

    # Use the first match (there should be only one)
    output_path = candidates[0]
    add("output_file_exists", True, f"Found at: {output_path}")

    try:
        content = output_path.read_text(encoding="utf-8")
    except Exception as e:
        add("output_file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    add("output_file_readable", True, f"File read, length={len(content)} chars")

    # ── Check 1: Script signature (proves run.py was used) ──────────────────
    sig = "## [case-study-factory v1.0.0]"
    sig_found = sig in content
    add(
        "script_signature_present",
        sig_found,
        f"Script signature '{sig}' {'found' if sig_found else 'NOT found'} in output."
    )

    # ── Check 2: All 6 required section headers ─────────────────────────────
    required_sections = [
        "## 项目背景",
        "## 关键动作",
        "## 结果与指标",
        "## 经验总结",
        "## 可复用方法",
        "## 对外版本注意事项",
    ]
    all_sections_present = True
    missing_sections = []
    for sec in required_sections:
        if sec not in content:
            all_sections_present = False
            missing_sections.append(sec)

    add(
        "all_6_sections_present",
        all_sections_present,
        (f"All 6 sections present." if all_sections_present
         else f"Missing sections: {missing_sections}")
    )

    # ── Check 3: 待确认项 section present ────────────────────────────────────
    pending_present = "待确认项" in content
    add(
        "pending_items_section_present",
        pending_present,
        ("'待确认项' section found." if pending_present
         else "'待确认项' section NOT found. Incomplete input must trigger this section.")
    )

    # ── Check 4: 待确认项 is non-trivial (has actual missing fields listed) ──
    pending_nontrivial = False
    pending_detail = ""
    if pending_present:
        # Find the pending block
        pending_match = re.search(
            r"## 待确认项\s*([\s\S]+?)(?:\Z|^##\s)", content, re.MULTILINE
        )
        if pending_match:
            pending_block = pending_match.group(1).strip()
            # Must list actual missing items, not just "(无待确认项)"
            if "无待确认项" not in pending_block and len(pending_block) > 5:
                pending_nontrivial = True
                pending_detail = f"Pending block is non-trivial: {pending_block[:120]!r}"
            else:
                pending_detail = f"Pending block is empty or claims no missing items: {pending_block!r}"
        else:
            pending_detail = "Could not extract content after '待确认项' header."
    else:
        pending_detail = "待确认项 section not found, so cannot evaluate content."

    add("pending_items_nontrivial", pending_nontrivial, pending_detail)

    # ── Check 5: Anonymization/confidentiality notice ───────────────────────
    anon_keywords = ["保密提醒", "匿名化", "脱敏"]
    anon_found = any(kw in content for kw in anon_keywords)
    add(
        "anonymization_notice_present",
        anon_found,
        (f"Anonymization/confidentiality notice found." if anon_found
         else f"None of {anon_keywords} found in output. Security boundary rule violated.")
    )

    # ── Check 6: 【待确认】 placeholder used for missing fields ──────────────
    placeholder_found = "【待确认】" in content
    add(
        "missing_field_placeholder_used",
        placeholder_found,
        ("'【待确认】' placeholder found for missing fields." if placeholder_found
         else "'【待确认】' placeholder NOT found. Missing fields should be marked explicitly.")
    )

    # ── Check 7: Input's known present fields are reflected ─────────────────
    # Background info that IS in the raw input should appear in output
    background_indicators = ["120万", "档案", "OCR", "扫描"]
    bg_found_count = sum(1 for kw in background_indicators if kw in content)
    bg_ok = bg_found_count >= 2
    add(
        "known_input_fields_reflected",
        bg_ok,
        (f"{bg_found_count}/{len(background_indicators)} background keywords from input found in output."
         if bg_ok
         else f"Only {bg_found_count}/{len(background_indicators)} background keywords found. "
              f"Expected at least 2 of {background_indicators}.")
    )

    # ── Check 8: No fabricated metrics in results section ───────────────────
    # The raw input explicitly says metrics are NOT confirmed yet.
    # Agent must NOT invent specific numbers for results.
    # We check that the 结果与指标 section doesn't contain invented concrete percentages/times
    # UNLESS they come from the raw input (which only mentions targets, not actuals).
    # The raw input target: "5分钟以内" — that's a stated goal, ok to mention.
    # Fabricated: definitive past-tense achievement claims with made-up numbers.
    results_match = re.search(
        r"## 结果与指标\s*([\s\S]+?)(?=\n## |\Z)", content, re.MULTILINE
    )
    fabrication_ok = True
    fabrication_detail = "Results section not found or appears appropriately hedged."
    if results_match:
        results_block = results_match.group(1).strip()
        # If results block is 【待确认】 or references pending status → good
        if "【待确认】" in results_block or "待确认" in results_block or "尚未" in results_block:
            fabrication_ok = True
            fabrication_detail = f"Results section correctly marked as pending: {results_block[:100]!r}"
        elif len(results_block) < 10:
            fabrication_ok = True
            fabrication_detail = "Results section is essentially empty (acceptable)."
        else:
            # Check for suspiciously confident fabricated stats not in the raw input
            # Raw input only mentions: 45min→5min target (not achieved), "已达标但未正式测量"
            # Acceptable: mention of target or uncertainty
            # Flag: definitive past-tense numeric achievements that aren't in the input
            suspect_patterns = [
                r"准确率\s*(?:达到|为|达)\s*\d+%",          # fabricated OCR accuracy %
                r"满意度\s*(?:达到|为|达)\s*\d+%",          # fabricated satisfaction %
                r"减少了?\s*\d+%",                           # fabricated reduction %
                r"提升了?\s*\d+%",                           # fabricated improvement %
                r"节省了?\s*\d+(?:\.\d+)?\s*(?:分钟|小时|天)", # fabricated time savings
            ]
            fabrications_detected = []
            for pat in suspect_patterns:
                if re.search(pat, results_block):
                    fabrications_detected.append(pat)
            if fabrications_detected:
                fabrication_ok = False
                fabrication_detail = (
                    f"Potentially fabricated metrics detected in 结果与指标: "
                    f"{fabrications_detected}. Raw input states metrics are not yet confirmed."
                )
            else:
                fabrication_ok = True
                fabrication_detail = f"No obvious fabricated metrics detected. Block: {results_block[:100]!r}"

    add("no_fabricated_results", fabrication_ok, fabrication_detail)

    # ── Scoring ──────────────────────────────────────────────────────────────
    weights = {
        "output_file_exists":             0.05,
        "output_file_readable":           0.05,
        "script_signature_present":       0.20,   # high weight — proves run.py was used
        "all_6_sections_present":         0.20,
        "pending_items_section_present":  0.10,
        "pending_items_nontrivial":       0.10,
        "anonymization_notice_present":   0.10,
        "missing_field_placeholder_used": 0.08,
        "known_input_fields_reflected":   0.07,
        "no_fabricated_results":          0.05,
    }

    score = 0.0
    for c in checks:
        w = weights.get(c["name"], 0.0)
        if c["passed"]:
            score += w

    # Must pass the critical checks to overall pass
    critical = [
        "script_signature_present",
        "all_6_sections_present",
        "pending_items_section_present",
        "pending_items_nontrivial",
        "anonymization_notice_present",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )
    overall_passed = critical_passed and score >= 0.65

    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))