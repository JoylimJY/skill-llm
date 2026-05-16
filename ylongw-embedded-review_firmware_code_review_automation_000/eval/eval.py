#!/usr/bin/env python3
"""
Evaluation script for the embedded-review skill task.
Checks that the agent:
1. Produced a review_report.md file
2. Used dual-model review mode (diff >100 lines + ISR/DMA critical path)
3. Report contains correct section structure (P0-P3 with emoji headers)
4. Report contains Cross-Review Analysis table
5. Report tags findings with consensus/Claude-only/Codex-only markers
6. Report contains Hardware/Timing Concerns section
7. Report contains Architecture Notes section
8. Report contains Next Steps section with ≥4 numbered options
9. Report has Overall assessment as one of: APPROVE / REQUEST_CHANGES / COMMENT
10. P0 issues are present (ISR vTaskDelay + DMA bounds check are critical)
11. At least one finding references ISR/DMA-related issue at correct file
"""

import sys
import re
import json
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    
    checks = []
    
    def check(name, passed, detail=""):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
        return bool(passed)

    # ── Find review_report.md ────────────────────────────────────────────────
    report_path = None
    try:
        candidates = list(workspace.rglob("review_report.md"))
        if candidates:
            report_path = candidates[0]
        check("review_report.md exists", report_path is not None,
              f"Found at: {report_path}" if report_path else "File not found anywhere in workspace")
    except Exception as e:
        check("review_report.md exists", False, f"Exception: {e}")

    if report_path is None:
        # No file found — all remaining checks fail
        for name in [
            "dual-model review mode declared",
            "P0 critical section present (🔴)",
            "P1 high section present (🟠)",
            "P2 medium section present (🟡)",
            "P3 low section present (⚪)",
            "findings tagged with model-source marker",
            "Cross-Review Analysis table present",
            "consensus/Claude-only/Codex-only rows in table",
            "Hardware/Timing Concerns section present",
            "Architecture Notes section present",
            "Next Steps section present",
            "Next Steps has ≥4 numbered items",
            "Overall assessment field present and valid",
            "ISR/DMA P0 finding identified",
            "strcpy/unbounded-string finding identified",
        ]:
            check(name, False, "No report file found")
        score = 0.0
        output = {"passed": False, "score": score, "checks": checks}
        print(json.dumps(output, ensure_ascii=False))
        return

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        check("report is readable", False, f"Read error: {e}")
        output = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(output, ensure_ascii=False))
        return

    content_lower = content.lower()

    # ── Check 2: Dual-model mode declared ────────────────────────────────────
    dual_model_patterns = [
        r"dual.?model",
        r"claude.{0,30}codex",
        r"codex.{0,30}claude",
        r"cross.?review",
    ]
    dual_model_found = any(re.search(p, content, re.IGNORECASE) for p in dual_model_patterns)
    check("dual-model review mode declared", dual_model_found,
          "Report must declare dual-model / cross-review mode (diff >100 lines + ISR/DMA critical path)")

    # ── Check 3-6: P0–P3 severity sections with emoji headers ────────────────
    # Exact emoji headers as mandated by SKILL.md
    p0_present = bool(re.search(r"🔴\s*P0", content))
    p1_present = bool(re.search(r"🟠\s*P1", content))
    p2_present = bool(re.search(r"🟡\s*P2", content))
    p3_present = bool(re.search(r"⚪\s*P3", content))

    check("P0 critical section present (🔴)", p0_present,
          "Must include ### 🔴 P0 - Critical section")
    check("P1 high section present (🟠)", p1_present,
          "Must include ### 🟠 P1 - High section")
    check("P2 medium section present (🟡)", p2_present,
          "Must include ### 🟡 P2 - Medium section")
    check("P3 low section present (⚪)", p3_present,
          "Must include ### ⚪ P3 - Low section")

    # ── Check 7: Findings tagged with model-source markers ───────────────────
    marker_patterns = [
        r"🤝",          # consensus
        r"🔵",          # Claude-only
        r"🟢",          # Codex-only
        r"consensus",
        r"claude.?only",
        r"codex.?only",
    ]
    markers_found = any(re.search(p, content, re.IGNORECASE) for p in marker_patterns)
    check("findings tagged with model-source marker", markers_found,
          "Findings must be tagged: [🤝 consensus / 🔵 Claude-only / 🟢 Codex-only]")

    # ── Check 8: Cross-Review Analysis table ─────────────────────────────────
    # Must contain a markdown table with cross-review metrics
    cross_review_section = bool(re.search(
        r"cross.?review\s+analysis",
        content, re.IGNORECASE
    ))
    check("Cross-Review Analysis table present", cross_review_section,
          "Must include '## Cross-Review Analysis' section (dual-model only)")

    # ── Check 9: Table rows for consensus/claude-only/codex-only ─────────────
    table_rows_ok = (
        bool(re.search(r"consensus", content, re.IGNORECASE)) and
        bool(re.search(r"claude.{0,10}only", content, re.IGNORECASE)) and
        bool(re.search(r"codex.{0,10}only", content, re.IGNORECASE))
    )
    check("consensus/Claude-only/Codex-only rows in table", table_rows_ok,
          "Cross-Review table must have rows for consensus, Claude-only, Codex-only")

    # ── Check 10: Hardware/Timing Concerns section ───────────────────────────
    hw_section = bool(re.search(
        r"hardware.{0,10}timing",
        content, re.IGNORECASE
    ))
    check("Hardware/Timing Concerns section present", hw_section,
          "Must include '## Hardware/Timing Concerns' section")

    # ── Check 11: Architecture Notes section ─────────────────────────────────
    arch_section = bool(re.search(
        r"architecture\s+(notes|observations)",
        content, re.IGNORECASE
    ))
    check("Architecture Notes section present", arch_section,
          "Must include '## Architecture Notes' section")

    # ── Check 12: Next Steps section ─────────────────────────────────────────
    next_steps = bool(re.search(r"next\s+steps", content, re.IGNORECASE))
    check("Next Steps section present", next_steps,
          "Must include '## Next Steps' section")

    # ── Check 13: Next Steps has ≥4 numbered items ───────────────────────────
    if next_steps:
        # Find Next Steps section content
        ns_match = re.search(r"next\s+steps(.{0,2000})", content, re.IGNORECASE | re.DOTALL)
        ns_content = ns_match.group(1) if ns_match else ""
        numbered_items = re.findall(r"^\s*\d+\.", ns_content, re.MULTILINE)
        check("Next Steps has ≥4 numbered items", len(numbered_items) >= 4,
              f"Found {len(numbered_items)} numbered items in Next Steps (need ≥4)")
    else:
        check("Next Steps has ≥4 numbered items", False, "Next Steps section absent")

    # ── Check 14: Overall assessment field ───────────────────────────────────
    assessment_match = re.search(
        r"overall\s+assessment[^\n]*?(APPROVE|REQUEST_CHANGES|COMMENT)",
        content, re.IGNORECASE
    )
    check("Overall assessment field present and valid", bool(assessment_match),
          f"Must include 'Overall assessment: APPROVE / REQUEST_CHANGES / COMMENT'. "
          f"Found: {assessment_match.group(0)[:80] if assessment_match else 'not found'}")

    # ── Check 15: ISR/DMA P0 finding (vTaskDelay in ISR + DMA overflow) ──────
    # The two critical P0 bugs planted: vTaskDelay in ISR, DMA len not validated
    isr_p0_patterns = [
        r"vtaskdelay",
        r"blocking.{0,30}isr",
        r"isr.{0,50}blocking",
        r"vTaskDelay",
        r"task.*delay.*isr",
        r"isr.*task.*delay",
    ]
    dma_p0_patterns = [
        r"dma.{0,60}(overflow|bound|length|len|size|unchecked|valida)",
        r"(overflow|bound|unchecked).{0,60}dma",
        r"dma_start_rx.{0,80}(bound|overflow|length|unsafe)",
        r"buffer.{0,60}dma.{0,60}(overflow|unchecked)",
    ]
    isr_p0_found = any(re.search(p, content, re.IGNORECASE) for p in isr_p0_patterns)
    dma_p0_found = any(re.search(p, content, re.IGNORECASE) for p in dma_p0_patterns)
    isr_dma_p0_found = isr_p0_found or dma_p0_found
    check("ISR/DMA P0 finding identified",
          isr_dma_p0_found,
          f"Must identify critical bugs: vTaskDelay in ISR and/or DMA length not validated. "
          f"ISR-found={isr_p0_found}, DMA-found={dma_p0_found}")

    # ── Check 16: strcpy/unbounded string finding ─────────────────────────────
    strcpy_patterns = [
        r"strcpy",
        r"unbounded.{0,30}(string|copy|buffer)",
        r"(string|buffer).{0,30}unbounded",
        r"nfc_set_device_name",
        r"uart_send_str",
        r"strncpy",
    ]
    strcpy_found = any(re.search(p, content, re.IGNORECASE) for p in strcpy_patterns)
    check("strcpy/unbounded-string finding identified", strcpy_found,
          "Must flag strcpy usage in nfc_set_device_name or uart_send_str (buffer overflow risk)")

    # ── Score calculation ─────────────────────────────────────────────────────
    n_passed = sum(1 for c in checks if c["passed"])
    n_total  = len(checks)
    score    = round(n_passed / n_total, 4)
    passed   = (
        checks[0]["passed"] and   # file exists
        dual_model_found and       # dual-model triggered
        p0_present and             # P0 section
        p1_present and             # P1 section
        cross_review_section and   # cross-review table
        next_steps and             # next steps
        assessment_match and       # overall assessment
        isr_dma_p0_found           # critical bugs caught
    )

    output = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()