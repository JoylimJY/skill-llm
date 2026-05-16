import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = Path(sys.argv[1])
    checks = []

    # ── 1. Find output file ──────────────────────────────────────────────────
    output_file = None
    candidates = list(workspace.rglob("metric_catalog.md"))
    if candidates:
        output_file = candidates[0]
        checks.append(check("output_file_exists",
                            True,
                            f"Found at: {output_file.relative_to(workspace)}"))
    else:
        checks.append(check("output_file_exists", False,
                            "metric_catalog.md not found anywhere in workspace"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── 2. Read content ──────────────────────────────────────────────────────
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, str(e)))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append(check("file_readable", True, f"Size: {len(content)} chars"))

    # ── 3. Six mandatory sections ────────────────────────────────────────────
    required_sections = ["指标目录", "口径定义", "计算方式", "不适用场景", "常见误用", "维护建议"]
    missing_sections = []
    for sec in required_sections:
        if sec not in content:
            missing_sections.append(sec)
    if missing_sections:
        checks.append(check("six_mandatory_sections", False,
                            f"Missing sections: {missing_sections}"))
    else:
        checks.append(check("six_mandatory_sections", True,
                            "All 6 sections present"))

    # ── 4. All 6 target metrics mentioned ───────────────────────────────────
    target_metrics = ["GMV", "CVR", "退款率", "AOV", "NPS", "LTV"]
    missing_metrics = [m for m in target_metrics if m not in content]
    if missing_metrics:
        checks.append(check("all_target_metrics_present", False,
                            f"Missing metrics: {missing_metrics}"))
    else:
        checks.append(check("all_target_metrics_present", True,
                            "All 6 target metrics present"))

    # ── 5. Conflict side-by-side (NOT merged) for GMV, CVR, 退款率 ──────────
    conflict_metrics = ["GMV", "CVR", "退款率"]
    conflict_checks_passed = []
    conflict_checks_failed = []

    for cm in conflict_metrics:
        # Must have at least 2 version indicators near the metric name
        # Look for "版本 1" and "版本 2" patterns, or multiple source citations
        # near the metric name block
        pattern_version = re.compile(
            r'(?:版本\s*[12]|Version\s*[12]|来源[:：][^】\n]*(?:BizUnit|财务|Finance|A部门|B部门))',
            re.IGNORECASE
        )
        version_hits = pattern_version.findall(content)

        # Also check: does the content list two distinct formulas for this metric?
        # Locate the section around cm
        metric_block_pattern = re.compile(
            r'###\s*' + re.escape(cm) + r'.*?(?=\n###|\Z)',
            re.DOTALL | re.IGNORECASE
        )
        metric_blocks = metric_block_pattern.findall(content)
        block_text = " ".join(metric_blocks)

        # Key check: at least 2 distinct formula variants visible
        formula_lines = re.findall(
            r'(?:SUM|COUNT|sum|count)\([^\)]+\)',
            block_text
        )
        unique_formulas = set(f.strip().lower() for f in formula_lines)

        has_conflict_indicators = (
            len(version_hits) >= 2 or
            len(unique_formulas) >= 2 or
            re.search(r'冲突|conflict|版本\s*\d|⚠', block_text, re.IGNORECASE)
        )

        # Anti-merge check: should NOT have a single "unified" formula replacing all
        anti_merge_keywords = ["统一口径为", "合并后", "最终公式", "unified formula"]
        merge_detected = any(kw in block_text for kw in anti_merge_keywords)

        if has_conflict_indicators and not merge_detected:
            conflict_checks_passed.append(cm)
        else:
            conflict_checks_failed.append(cm)

    if not conflict_checks_failed:
        checks.append(check("conflicts_listed_side_by_side", True,
                            f"All conflict metrics shown with multiple versions: {conflict_checks_passed}"))
    else:
        checks.append(check("conflicts_listed_side_by_side", False,
                            f"Missing side-by-side conflict display for: {conflict_checks_failed}; passed: {conflict_checks_passed}"))

    # ── 6. Pending items (待确认项) for NPS and LTV ──────────────────────────
    pending_section_present = "待确认" in content or "待补充" in content or "待确认项" in content
    nps_pending = "NPS" in content and (
        re.search(r'(?:待确认|待补充|pending|❌|尚无|无公式)[^\n]*NPS|NPS[^\n]*(?:待确认|待补充|pending|❌|尚无|无公式)',
                  content, re.IGNORECASE) is not None
        or re.search(r'NPS', content) and re.search(r'待确认|待补充', content)
    )
    ltv_pending = "LTV" in content and (
        re.search(r'(?:待确认|待补充|pending|❌|尚无|无公式)[^\n]*LTV|LTV[^\n]*(?:待确认|待补充|pending|❌|尚无|无公式)',
                  content, re.IGNORECASE) is not None
        or re.search(r'LTV', content) and re.search(r'待确认|待补充', content)
    )
    # Fallback: if both NPS and LTV appear in a section clearly labeled 待确认
    if not (nps_pending and ltv_pending):
        # Find 待确认项 section
        pending_match = re.search(r'待确认项.*?(?=\n##|\Z)', content, re.DOTALL)
        if pending_match:
            pending_block = pending_match.group(0)
            nps_pending = nps_pending or "NPS" in pending_block
            ltv_pending = ltv_pending or "LTV" in pending_block

    pending_ok = pending_section_present and nps_pending and ltv_pending
    checks.append(check("pending_items_for_nps_ltv",
                        pending_ok,
                        f"待确认项 section: {pending_section_present}, NPS flagged: {nps_pending}, LTV flagged: {ltv_pending}"))

    # ── 7. Draft notice (可审阅草案 indicator) ───────────────────────────────
    draft_present = bool(re.search(r'草案|draft|可审阅|Draft', content, re.IGNORECASE))
    checks.append(check("draft_notice_present", draft_present,
                        "'草案' or 'draft' marker present" if draft_present else "No draft/草案 marker found"))

    # ── 8. No fabrication of missing data ────────────────────────────────────
    # NPS and LTV should NOT have a concrete formula if none exists in source
    nps_block_match = re.search(r'(NPS[^\n]*\n(?:[^\n]*\n){0,15})', content)
    ltv_block_match = re.search(r'(LTV[^\n]*\n(?:[^\n]*\n){0,15})', content)

    fabrication_detected = False
    fabrication_detail = []

    if nps_block_match:
        nps_block = nps_block_match.group(1)
        # Check if a specific numeric formula is given for NPS without citation
        if re.search(r'(?:=\s*[\w\(\)]+\s*/|SUM\(|COUNT\()', nps_block):
            fabrication_detected = True
            fabrication_detail.append("NPS appears to have a fabricated formula")

    if ltv_block_match:
        ltv_block = ltv_block_match.group(1)
        if re.search(r'(?:=\s*[\w\(\)]+\s*/|SUM\(|COUNT\()', ltv_block):
            fabrication_detected = True
            fabrication_detail.append("LTV appears to have a fabricated formula")

    checks.append(check("no_fabrication_for_missing_metrics",
                        not fabrication_detected,
                        "OK" if not fabrication_detected else "; ".join(fabrication_detail)))

    # ── 9. Multiple source attributions present ──────────────────────────────
    source_pattern = re.compile(
        r'BizUnit-A|BizUnit-B|财务团队|电商事业部|金融支付部|Finance|增长团队|风控团队|数据中台',
        re.IGNORECASE
    )
    source_hits = source_pattern.findall(content)
    unique_sources = set(h.strip() for h in source_hits)
    sources_ok = len(unique_sources) >= 2
    checks.append(check("multiple_source_attributions",
                        sources_ok,
                        f"Found {len(unique_sources)} distinct source labels: {unique_sources}"))

    # ── 10. Maintenance recommendations present ──────────────────────────────
    maint_keywords = ["建议", "复核", "对齐", "recommend", "quarterly", "季度"]
    maint_present = any(kw in content for kw in maint_keywords)
    checks.append(check("maintenance_recommendations_present",
                        maint_present,
                        "Maintenance recommendations found" if maint_present else "No maintenance recommendations"))

    # ── Score ────────────────────────────────────────────────────────────────
    weights = {
        "output_file_exists":               1.5,
        "file_readable":                    0.5,
        "six_mandatory_sections":           2.0,
        "all_target_metrics_present":       1.5,
        "conflicts_listed_side_by_side":    2.5,
        "pending_items_for_nps_ltv":        1.5,
        "draft_notice_present":             0.5,
        "no_fabrication_for_missing_metrics": 1.5,
        "multiple_source_attributions":     1.0,
        "maintenance_recommendations_present": 0.5,
    }
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)

    # Must pass critical checks to overall pass
    critical = ["output_file_exists", "six_mandatory_sections",
                "conflicts_listed_side_by_side", "no_fabrication_for_missing_metrics"]
    passed = all(c["passed"] for c in checks if c["name"] in critical) and score >= 0.65

    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()