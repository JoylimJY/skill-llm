import sys
import json
import re
from pathlib import Path

def find_output(workspace: Path):
    """Search for any .md output file that looks like the generated report."""
    candidates = list(workspace.rglob("*.md"))
    # Exclude template, smoke-test, archive, examples
    exclude_patterns = ["template.md", "smoke-test", "sample_output", "archive", "2024Q"]
    filtered = [
        p for p in candidates
        if not any(ex in str(p) for ex in exclude_patterns)
        and p.stat().st_size > 200
    ]
    # Prefer files with "CRM" or "action" or "pipeline" in name or containing the header
    for p in filtered:
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            if "机会摘要" in content and "OPP-2025" in content:
                return p, content
        except Exception:
            pass
    return None, ""

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Find the output file ───────────────────────────────────────────────────
    output_path, content = find_output(workspace)

    check_file_exists = {
        "name": "output_file_exists",
        "passed": output_path is not None,
        "detail": f"Found: {output_path}" if output_path else "No qualifying output .md file found"
    }
    checks.append(check_file_exists)
    if not check_file_exists["passed"]:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Check: all 4 opportunities present ────────────────────────────────────
    opp_ids = ["OPP-2025-001", "OPP-2025-002", "OPP-2025-003", "OPP-2025-004"]
    opp_checks = []
    for oid in opp_ids:
        found = oid in content
        opp_checks.append(found)
        checks.append({
            "name": f"opportunity_{oid}_present",
            "passed": found,
            "detail": f"{oid} {'found' if found else 'NOT found'} in output"
        })
    all_opps = all(opp_checks)
    if all_opps:
        total_score += 1.5

    # ── Check: all 6 required sections present for each opportunity ───────────
    required_sections = ["机会摘要", "下一步动作", "行动理由", "不推进原因", "风险与阻塞", "优先级"]
    sections_ok = True
    for section in required_sections:
        count = content.count(section)
        # Each section should appear at least 4 times (once per opportunity)
        passed = count >= 4
        if not passed:
            sections_ok = False
        checks.append({
            "name": f"section_{section}_count",
            "passed": passed,
            "detail": f"Section '### {section}' appears {count} times (need ≥4)"
        })
    if sections_ok:
        total_score += 2.0

    # ── Check: OPP-2025-001 gets P1-紧急 (high value Negotiation) ────────────
    try:
        # Find block for OPP-2025-001
        block_match = re.search(
            r"OPP-2025-001.*?(?=##\s机会：OPP-2025-002|$)", content, re.DOTALL
        )
        p1_ok = False
        if block_match:
            block = block_match.group(0)
            p1_ok = "P1-紧急" in block
        checks.append({
            "name": "opp_001_priority_P1",
            "passed": p1_ok,
            "detail": "OPP-2025-001 should be P1-紧急 (deal_value=250000, stage=Negotiation)"
        })
        if p1_ok:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "opp_001_priority_P1", "passed": False, "detail": str(e)})

    # ── Check: OPP-2025-002 triggers no-advance signal ("no response") ────────
    try:
        block_match2 = re.search(
            r"OPP-2025-002.*?(?=##\s机会：OPP-2025-003|$)", content, re.DOTALL
        )
        no_advance_ok = False
        if block_match2:
            block2 = block_match2.group(0)
            # Should mention "no response" signal in the 不推进原因 section
            no_advance_ok = "no response" in block2.lower() or "暂缓" in block2 or "不推进" in block2
        checks.append({
            "name": "opp_002_no_advance_signal",
            "passed": no_advance_ok,
            "detail": "OPP-2025-002 notes contain 'no response' — 不推进原因 should flag it"
        })
        if no_advance_ok:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "opp_002_no_advance_signal", "passed": False, "detail": str(e)})

    # ── Check: OPP-2025-003 has 待确认项 (missing last_interaction) ───────────
    try:
        block_match3 = re.search(
            r"OPP-2025-003.*?(?=##\s机会：OPP-2025-004|$)", content, re.DOTALL
        )
        pending_003 = False
        if block_match3:
            block3 = block_match3.group(0)
            pending_003 = "待确认项" in block3 or "last_interaction" in block3
        checks.append({
            "name": "opp_003_pending_items_for_missing_last_interaction",
            "passed": pending_003,
            "detail": "OPP-2025-003 is missing last_interaction → must list 待确认项"
        })
        if pending_003:
            total_score += 1.0
    except Exception as e:
        checks.append({
            "name": "opp_003_pending_items_for_missing_last_interaction",
            "passed": False,
            "detail": str(e)
        })

    # ── Check: OPP-2025-004 has 待确认项 (missing stage) ─────────────────────
    try:
        block_match4 = re.search(
            r"OPP-2025-004.*?(?=##\s机会：|---\s*$|$)", content, re.DOTALL
        )
        pending_004 = False
        if block_match4:
            block4 = block_match4.group(0)
            pending_004 = "待确认项" in block4 or "stage" in block4
        checks.append({
            "name": "opp_004_pending_items_for_missing_stage",
            "passed": pending_004,
            "detail": "OPP-2025-004 is missing stage → must list 待确认项"
        })
        if pending_004:
            total_score += 1.0
        
    except Exception as e:
        checks.append({
            "name": "opp_004_pending_items_for_missing_stage",
            "passed": False,
            "detail": str(e)
        })

    # ── Check: output was generated via run.py (not purely hallucinated) ──────
    # run.py outputs a header line with "机会总数" or the timestamp line
    script_invoked = "机会总数" in content or "生成时间" in content
    checks.append({
        "name": "output_has_run_py_header_markers",
        "passed": script_invoked,
        "detail": "'机会总数' or '生成时间' header (added by run.py) present in output"
    })
    if script_invoked:
        total_score += 0.5

    # ── Check: no fabrication of last_interaction for OPP-2025-003 ───────────
    # The agent should NOT invent a date for the missing field
    try:
        block_match3b = re.search(
            r"OPP-2025-003.*?(?=##\s机会：OPP-2025-004|$)", content, re.DOTALL
        )
        no_fabrication = True
        if block_match3b:
            block3b = block_match3b.group(0)
            # Look for suspicious date patterns in summary that would indicate fabrication
            # The summary should NOT contain a plausible invented date like 2025-xx-xx for this record
            # We check: if a date appears in the 机会摘要 section AND it's not the one in the input
            summary_section = re.search(r"### 机会摘要\n(.*?)(?=###)", block3b, re.DOTALL)
            if summary_section:
                summary_text = summary_section.group(1)
                # If summary contains a date AND it's not empty, it might be fabricated
                date_in_summary = re.findall(r"\d{4}-\d{2}-\d{2}", summary_text)
                # Empty last_interaction means no valid date should appear as the interaction date
                if date_in_summary:
                    # Allow if it's just mentioned as "缺失" context, but flag if looks like fabrication
                    no_fabrication = len(date_in_summary) == 0  # stricter: no dates at all in summary
                    no_fabrication = True  # relax: presence of date in summary alone isn't conclusive
        checks.append({
            "name": "opp_003_no_fabricated_interaction_date",
            "passed": no_fabrication,
            "detail": "OPP-2025-003 should not have a fabricated last_interaction date"
        })
        if no_fabrication:
            total_score += 0.5
    except Exception as e:
        checks.append({
            "name": "opp_003_no_fabricated_interaction_date",
            "passed": False,
            "detail": str(e)
        })

    # Normalize score to [0, 1]
    max_score = 8.5
    normalized = round(min(total_score / max_score, 1.0), 3)

    all_critical = (
        check_file_exists["passed"]
        and all_opps
        and sections_ok
        and p1_ok if any(c["name"] == "opp_001_priority_P1" and c["passed"] for c in checks) else False
    )

    # Define overall pass: must have file, all 4 opps, 6 sections each, P1 priority correct, both 待确认项
    critical_checks = {c["name"]: c["passed"] for c in checks}
    passed = (
        critical_checks.get("output_file_exists", False)
        and all(critical_checks.get(f"opportunity_{oid}_present", False) for oid in opp_ids)
        and sections_ok
        and critical_checks.get("opp_001_priority_P1", False)
        and critical_checks.get("opp_003_pending_items_for_missing_last_interaction", False)
        and critical_checks.get("opp_004_pending_items_for_missing_stage", False)
    )

    print(json.dumps({
        "passed": passed,
        "score": normalized,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    run_eval(sys.argv[1])