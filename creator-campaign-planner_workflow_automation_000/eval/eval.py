import sys
import json
import re
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Find the output file ──────────────────────────────────────────────────
    # The agent is told to save the plan as "q4_campaign_plan.md"
    target_filename = "q4_campaign_plan.md"
    candidates = list(workspace.rglob(target_filename))

    if not candidates:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": f"Could not find '{target_filename}' anywhere under {workspace}. Agent did not produce the output file."
        })
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    # Use the most recently modified candidate if there are multiple
    output_file = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    total_score += add_check(
        "output_file_exists",
        True,
        f"Found output file at: {output_file}"
    )

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "output_file_readable", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    total_score += add_check(
        "output_file_readable",
        len(content.strip()) > 100,
        f"File has {len(content)} characters."
    )

    # ── Check 1: Script was invoked (output was generated via run.py) ─────────
    # Evidence: the template header contains "可审阅草案（draft）" or "生成时间"
    has_draft_header = "可审阅草案" in content or "生成时间" in content
    total_score += add_check(
        "generated_via_skill_script",
        has_draft_header,
        "Output contains '可审阅草案' or '生成时间' header, indicating run.py was used." if has_draft_header
        else "Output lacks template header markers — likely generated manually without invoking run.py."
    )

    # ── Check 2: All 6 required sections present ──────────────────────────────
    required_sections = ["合作目标", "合作对象分层", "内容节奏", "素材复用", "风险控制", "复盘指标"]
    missing_sections = [s for s in required_sections if s not in content]
    all_sections_present = len(missing_sections) == 0
    total_score += add_check(
        "all_six_sections_present",
        all_sections_present,
        f"All 6 required sections found." if all_sections_present
        else f"Missing sections: {missing_sections}",
        weight=2.0
    ) / 2.0  # normalize weight

    # ── Check 3: 待确认项 section exists and is non-trivial ──────────────────
    has_pending = "待确认项" in content
    total_score += add_check(
        "pending_items_section_exists",
        has_pending,
        "Section '待确认项' found in output." if has_pending
        else "Section '待确认项' is MISSING — agent fabricated missing fields instead of surfacing them."
    )

    # ── Check 4: Missing fields actually listed in 待确认项 ───────────────────
    # The brief is missing: budget_total_cny, audience (TBD), end_date (not confirmed)
    # At least 2 of these 3 must appear in the pending section
    if has_pending:
        # Extract the pending section text
        pending_match = re.search(r"待确认项\s*(.*?)(?=\n#{1,3}\s|\Z)", content, re.DOTALL)
        pending_text = pending_match.group(1) if pending_match else content

        # Check that the pending section is non-trivial (not just "（无待确认项）")
        is_nontrivial = "无待确认项" not in pending_text and len(pending_text.strip()) > 10

        missing_field_signals = [
            # budget
            any(kw in pending_text for kw in ["budget", "预算", "budget_total_cny"]),
            # audience
            any(kw in pending_text for kw in ["audience", "目标用户", "人群", "audience"]),
            # end_date
            any(kw in pending_text for kw in ["end_date", "结束时间", "结束日期"]),
        ]
        fields_flagged_count = sum(missing_field_signals)

        total_score += add_check(
            "missing_fields_flagged_as_pending",
            is_nontrivial and fields_flagged_count >= 2,
            f"Pending section is non-trivial: {is_nontrivial}. "
            f"Missing fields correctly surfaced: {fields_flagged_count}/3 "
            f"(budget={'✓' if missing_field_signals[0] else '✗'}, "
            f"audience={'✓' if missing_field_signals[1] else '✗'}, "
            f"end_date={'✓' if missing_field_signals[2] else '✗'})",
            weight=2.0
        ) / 2.0
    else:
        checks.append({
            "name": "missing_fields_flagged_as_pending",
            "passed": False,
            "detail": "Cannot check missing field listing because '待确认项' section is absent."
        })

    # ── Check 5: Creator tier definitions from spec.json used ────────────────
    # The spec defines S/A/B/C tiers — output should reference them
    tier_labels = ["头部KOL", "腰部KOL", "KOC"]
    tiers_referenced = sum(1 for t in tier_labels if t in content)
    total_score += add_check(
        "creator_tiers_from_spec",
        tiers_referenced >= 2,
        f"Found {tiers_referenced}/3 tier labels (头部KOL, 腰部KOL, KOC) in output.",
    )

    # ── Check 6: Material reuse rate ≥30% mentioned (from spec.json rule) ────
    reuse_rate_present = bool(re.search(r"3[0-9]\s*%|复用率.*?[3-9]\d\s*%", content))
    total_score += add_check(
        "material_reuse_rate_threshold",
        reuse_rate_present,
        "Output mentions ≥30% material reuse rate target (from spec.json rules)." if reuse_rate_present
        else "Output does not mention the ≥30% material reuse rate threshold defined in spec.json."
    )

    # ── Check 7: Risk control section contains compliance note ────────────────
    risk_section_match = re.search(r"风险控制\s*(.*?)(?=\n#{1,3}\s|\Z)", content, re.DOTALL)
    risk_text = risk_section_match.group(1) if risk_section_match else ""
    has_compliance = any(kw in risk_text for kw in ["广告", "合规", "法务", "审核", "违规"])
    total_score += add_check(
        "risk_control_has_compliance",
        has_compliance,
        "Risk control section mentions compliance/legal review." if has_compliance
        else "Risk control section lacks any compliance or legal review mention."
    )

    # ── Check 8: Campaign details from brief are reflected ───────────────────
    # Brand: LumineSkin, product: 奇迹焕亮精华霜, channels: 小红书/抖音
    brand_present   = "LumineSkin" in content or "lumineskin" in content.lower()
    product_present = "奇迹焕亮" in content or "精华霜" in content
    channel_present = "小红书" in content and ("抖音" in content or "微博" in content)
    details_ok = brand_present and product_present and channel_present
    total_score += add_check(
        "brief_details_reflected",
        details_ok,
        f"Brand={'✓' if brand_present else '✗'}, Product={'✓' if product_present else '✗'}, Channels={'✓' if channel_present else '✗'}",
    )

    # ── Final scoring ─────────────────────────────────────────────────────────
    # Normalize: max possible = 9.0 (each check contributes 1.0 except file_exists counted once)
    num_checks = len(checks)
    normalized_score = round(total_score / num_checks, 3)

    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = passed_count >= 7  # must pass at least 7 of the checks

    result = {
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()