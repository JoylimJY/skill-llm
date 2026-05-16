#!/usr/bin/env python3
"""
Evaluation script for the hardware assessment validation task.
Usage: python3 eval.py <workspace_dir>
"""

import sys
import json
import re
from pathlib import Path


def normalize(text: str) -> str:
    return re.sub(r'\s+', '', text).lower()


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

    checks = []
    total_score = 0.0
    max_score = 4.0

    # ── Find the output file ──────────────────────────────────────────────────
    # The agent was asked to write to 'assessment_validation_result.txt'
    result_files = list(workspace.rglob("assessment_validation_result.txt"))

    if not result_files:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "assessment_validation_result.txt not found anywhere in workspace"
        })
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": checks
        }))
        return

    result_file = result_files[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found at {result_file}"
    })

    try:
        content = result_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Cannot read file: {e}"
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({
        "name": "output_file_readable",
        "passed": True,
        "detail": f"File read successfully ({len(content)} chars)"
    })

    # ── Check 1: 单病种系统 should be "ok" ────────────────────────────────────
    # The client provided all 3 required elements: 年出院人次, 单病种病种数量, 医护人员总数
    norm_content = normalize(content)

    # Look for "ok" associated with 单病种系统
    # The result must contain something like "客户A" or "单病种系统" + "ok"
    # We check if the content mentions "ok" in context of 单病种系统

    # Strategy: find lines/sections related to 单病种 and check for "ok"
    lines = content.splitlines()

    # Find any section referencing 单病种系统
    danbingzhong_section = []
    in_section = False
    for line in lines:
        norm_line = normalize(line)
        if "单病种" in norm_line or "客户a" in norm_line:
            in_section = True
        elif in_section and ("客户b" in norm_line or "vte" in norm_line):
            in_section = False
        if in_section:
            danbingzhong_section.append(line)

    danbingzhong_text = " ".join(danbingzhong_section).lower()
    # For 单病种系统: all 3 elements provided, so result should be "ok"
    danbingzhong_ok = (
        "ok" in normalize(danbingzhong_text) and
        "缺少" not in normalize(danbingzhong_text)
    ) or (
        # Alternatively the output might not be sectioned but just contain "ok" for 单病种 case
        # Try a broader check: content has 单病种 and ok without 缺少 near it
        False
    )

    # Broader fallback: check if the word "ok" appears in the content 
    # and "单病种系统" context does not show missing items
    if not danbingzhong_ok:
        # Try: look for 单病种 followed by ok within 200 chars
        idx = content.find("单病种")
        if idx == -1:
            idx = content.find("客户A")
        if idx != -1:
            snippet = normalize(content[idx:idx+300])
            danbingzhong_ok = "ok" in snippet and "缺少" not in snippet

    checks.append({
        "name": "danbingzhong_result_ok",
        "passed": danbingzhong_ok,
        "detail": (
            "单病种系统 with all elements provided should yield 'ok'. "
            f"Relevant text found: '{' '.join(danbingzhong_section[:5])}'"
            if danbingzhong_section else
            f"No relevant section found for 单病种系统 in output. Content preview: {content[:200]}"
        )
    })
    if danbingzhong_ok:
        total_score += 1.0

    # ── Check 2: VTE系统 should report missing elements ───────────────────────
    # Client B provided: 年出院人次, 外科床位数
    # Required by VTE: 年出院人次, 外科床位数, ICU床位数, 医护人员总数
    # Missing: ICU床位数, 医护人员总数

    vte_section = []
    in_vte = False
    for line in lines:
        norm_line = normalize(line)
        if "vte" in norm_line or "客户b" in norm_line:
            in_vte = True
        elif in_vte and ("单病种" in norm_line or "客户a" in norm_line or "cdss" in norm_line):
            in_vte = False
        if in_vte:
            vte_section.append(line)

    vte_text = " ".join(vte_section)
    norm_vte = normalize(vte_text)

    # Must contain "缺少" (missing elements report)
    vte_has_missing = "缺少" in norm_vte

    # Must mention ICU床位数
    vte_mentions_icu = "icu床位数" in norm_vte or "icu" in norm_vte

    # Must mention 医护人员总数
    vte_mentions_staff = "医护人员总数" in norm_vte

    checks.append({
        "name": "vte_result_missing_reported",
        "passed": vte_has_missing,
        "detail": (
            f"VTE系统 result should contain '缺少'. "
            f"VTE section text: '{vte_text[:300]}'"
        )
    })
    if vte_has_missing:
        total_score += 0.5

    checks.append({
        "name": "vte_missing_icu_beds",
        "passed": vte_mentions_icu,
        "detail": (
            f"VTE系统 missing items should include 'ICU床位数'. "
            f"VTE section text: '{vte_text[:300]}'"
        )
    })
    if vte_mentions_icu:
        total_score += 1.0

    checks.append({
        "name": "vte_missing_staff_count",
        "passed": vte_mentions_staff,
        "detail": (
            f"VTE系统 missing items should include '医护人员总数'. "
            f"VTE section text: '{vte_text[:300]}'"
        )
    })
    if vte_mentions_staff:
        total_score += 1.0

    # ── Check 3: compare_elements.py was used correctly (kb_dir) ─────────────
    # Indirect check: the script can only return correct results if kb_dir was
    # set to /workspace/kb (not the default /Users/hushuai/... path).
    # If both VTE missing items are correctly identified, it implies correct kb_dir usage.
    # We verify the KB files are intact (not corrupted by the agent).
    vte_kb_file = workspace / "kb" / "VTE系统" / "VTE-标准单产品硬件资源测算.md"
    try:
        vte_kb_content = vte_kb_file.read_text(encoding="utf-8")
        kb_intact = "ICU床位数" in vte_kb_content and "医护人员总数" in vte_kb_content
    except Exception as e:
        kb_intact = False

    checks.append({
        "name": "kb_files_intact",
        "passed": kb_intact,
        "detail": (
            f"KB file at {vte_kb_file} should be intact with all required elements. "
            f"{'File found and valid.' if kb_intact else 'File missing or corrupted.'}"
        )
    })
    if kb_intact:
        total_score += 0.5

    # ── Final scoring ─────────────────────────────────────────────────────────
    final_score = round(total_score / max_score, 4)
    all_critical_passed = danbingzhong_ok and vte_has_missing and vte_mentions_icu and vte_mentions_staff

    print(json.dumps({
        "passed": all_critical_passed,
        "score": final_score,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()