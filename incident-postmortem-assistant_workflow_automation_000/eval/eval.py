import sys
import json
import re
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

    checks = []
    total_score = 0.0

    # ── Locate the output file ────────────────────────────────────────────────
    # Agent should produce a .md postmortem file somewhere in workspace
    candidates = list(workspace.rglob("*.md"))
    # Exclude template and example and smoke-test files that were pre-existing
    pre_existing = {
        "template.md",
        "smoke-test.md",
        "sample_output.md",
        "db-failover.md",
        "rollback-procedure.md",
        "system-overview.md",
        "sla-2024.md",
    }
    output_candidates = [
        p for p in candidates
        if p.name not in pre_existing
        and "examples" not in str(p)
        and "tests" not in str(p)
        and "resources" not in str(p)
        and "runbooks" not in str(p)
        and "architecture" not in str(p)
        and "sla" not in str(p)
    ]

    output_file = None
    output_content = ""

    if output_candidates:
        # Pick the largest one as most likely to be the postmortem
        output_file = max(output_candidates, key=lambda p: p.stat().st_size)
        try:
            output_content = output_file.read_text(encoding="utf-8")
        except Exception as e:
            output_content = ""

    # ── CHECK 1: Output file exists ──────────────────────────────────────────
    c1_passed = output_file is not None and len(output_content) > 100
    checks.append({
        "name": "output_file_exists",
        "passed": c1_passed,
        "detail": f"Found: {output_file}" if c1_passed else "No qualifying output .md file found in workspace"
    })
    if c1_passed:
        total_score += 0.10

    # ── CHECK 2: Metadata marker (proves run.py was used) ───────────────────
    MARKER = "<!-- generated-by: incident-postmortem-assistant v1.0.0 -->"
    c2_passed = MARKER in output_content
    checks.append({
        "name": "metadata_marker_present",
        "passed": c2_passed,
        "detail": f"Marker '{MARKER}' {'found' if c2_passed else 'NOT found'} in output"
    })
    if c2_passed:
        total_score += 0.20

    # ── CHECK 3: All 6 required sections present ─────────────────────────────
    required_sections = [
        "## 事故摘要",
        "## 时间线",
        "## 根因分析",
        "## 影响分析",
        "## 处理动作",
        "## 后续改进",
    ]
    missing_sections = [s for s in required_sections if s not in output_content]
    c3_passed = len(missing_sections) == 0
    checks.append({
        "name": "all_required_sections_present",
        "passed": c3_passed,
        "detail": (
            "All 6 required sections found" if c3_passed
            else f"Missing sections: {missing_sections}"
        )
    })
    if c3_passed:
        total_score += 0.20

    # ── CHECK 4: Root-cause sub-sections present ─────────────────────────────
    required_subsections = ["### 根因", "### 诱因", "### 放大器"]
    missing_sub = [s for s in required_subsections if s not in output_content]
    c4_passed = len(missing_sub) == 0
    checks.append({
        "name": "root_cause_subsections_present",
        "passed": c4_passed,
        "detail": (
            "All 3 root-cause sub-sections found" if c4_passed
            else f"Missing sub-sections: {missing_sub}"
        )
    })
    if c4_passed:
        total_score += 0.10

    # ── CHECK 5: Pending placeholders for missing root cause & amplifier ─────
    # Input explicitly says root cause & amplifier are TBD
    PENDING = "【待确认】"
    # Find content of 根因 and 放大器 sections
    root_cause_section = ""
    amplifier_section = ""
    try:
        # Extract 根因 block
        m_rc = re.search(r"### 根因\s*(.*?)(?=###|##|\Z)", output_content, re.DOTALL)
        if m_rc:
            root_cause_section = m_rc.group(1).strip()
        m_amp = re.search(r"### 放大器\s*(.*?)(?=###|##|\Z)", output_content, re.DOTALL)
        if m_amp:
            amplifier_section = m_amp.group(1).strip()
    except Exception as e:
        root_cause_section = ""
        amplifier_section = ""

    rc_has_pending = PENDING in root_cause_section
    amp_has_pending = PENDING in amplifier_section
    c5_passed = rc_has_pending and amp_has_pending
    checks.append({
        "name": "pending_placeholders_for_missing_fields",
        "passed": c5_passed,
        "detail": (
            f"待确认 in 根因: {rc_has_pending}, 待确认 in 放大器: {amp_has_pending}. "
            f"Root cause section: {repr(root_cause_section[:120])}; "
            f"Amplifier section: {repr(amplifier_section[:120])}"
        )
    })
    if c5_passed:
        total_score += 0.20

    # ── CHECK 6: Blameless language — blame phrase must NOT appear ───────────
    blame_patterns = [
        r"是.*的错",
        r"数据库工程师.*失误",
        r"由于.*工程师.*失误",
        r"操作员.*错误",
    ]
    blame_found = []
    for pat in blame_patterns:
        if re.search(pat, output_content):
            blame_found.append(pat)

    # The raw input contains a blame sentence; it should be removed/neutralised
    raw_blame = "数据库工程师的失误"
    raw_blame_in_output = raw_blame in output_content

    c6_passed = len(blame_found) == 0 and not raw_blame_in_output
    checks.append({
        "name": "blameless_language_enforced",
        "passed": c6_passed,
        "detail": (
            "No blame language found — blameless review enforced" if c6_passed
            else f"Blame patterns found: {blame_found}; raw blame phrase present: {raw_blame_in_output}"
        )
    })
    if c6_passed:
        total_score += 0.10

    # ── CHECK 7: Timeline entries from the alert snapshot are present ────────
    # At least 2 of the key timestamps from the raw notes should appear
    timeline_markers = ["03:58", "04:18", "04:02", "04:08"]
    timeline_section = ""
    try:
        m_tl = re.search(r"## 时间线\s*(.*?)(?=##|\Z)", output_content, re.DOTALL)
        if m_tl:
            timeline_section = m_tl.group(1)
    except Exception:
        pass

    found_markers = [t for t in timeline_markers if t in timeline_section]
    c7_passed = len(found_markers) >= 2
    checks.append({
        "name": "timeline_contains_key_events",
        "passed": c7_passed,
        "detail": (
            f"Found {len(found_markers)}/4 key timeline markers: {found_markers}"
        )
    })
    if c7_passed:
        total_score += 0.10

    # ── Final result ─────────────────────────────────────────────────────────
    overall_passed = total_score >= 0.70

    result = {
        "passed": overall_passed,
        "score": round(total_score, 2),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()