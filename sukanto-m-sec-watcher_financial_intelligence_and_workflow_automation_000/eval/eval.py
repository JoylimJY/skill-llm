import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── Locate the output file ────────────────────────────────────────────────
    target_files = list(workspace.rglob("filing_alert_report.md"))
    file_found = len(target_files) > 0

    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(target_files)} file(s) named 'filing_alert_report.md'" if file_found else "No file named 'filing_alert_report.md' found anywhere in workspace"
    })

    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = target_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"File at {report_path}, {len(content)} chars"})

    # ── Check 1: Report is non-trivial (at least 300 chars) ──────────────────
    non_trivial = len(content.strip()) >= 300
    checks.append({
        "name": "report_non_trivial",
        "passed": non_trivial,
        "detail": f"Content length: {len(content.strip())} chars (minimum 300)"
    })

    # ── Check 2: Uses 8-K filter (form type mention) ─────────────────────────
    has_8k = bool(re.search(r'8-K|8K', content, re.IGNORECASE))
    checks.append({
        "name": "contains_8k_filter_evidence",
        "passed": has_8k,
        "detail": "Report mentions '8-K' form type (evidence of correct --form-type flag usage)" if has_8k else "No mention of '8-K' found — agent may not have filtered by form type"
    })

    # ── Check 3: 72-hour lookback window evidence ─────────────────────────────
    # The prompt asks for 72-hour lookback; agent must use --hours 72
    # We look for dates or explicit mention of 72h, or the report structure implying a wider scan
    has_72h = bool(re.search(r'72.{0,10}hour|last\s+3\s+day|past\s+72|72h', content, re.IGNORECASE))
    checks.append({
        "name": "72_hour_lookback_mentioned",
        "passed": has_72h,
        "detail": "Report explicitly references 72-hour lookback window" if has_72h else "No reference to 72-hour window found (agent may have used default 48h)"
    })

    # ── Check 4: Proprietary filing format — emoji anchor ────────────────────
    has_filing_emoji = bool(re.search(r'📄', content))
    checks.append({
        "name": "uses_filing_emoji_format",
        "passed": has_filing_emoji,
        "detail": "Report uses 📄 emoji as specified in proprietary format" if has_filing_emoji else "Missing 📄 emoji — agent did not follow the proprietary response format"
    })

    # ── Check 5: Proprietary format fields — "Filed:" and "Why it matters:" ──
    has_filed_field = bool(re.search(r'Filed\s*:', content))
    has_why_matters = bool(re.search(r'Why it matters\s*:', content, re.IGNORECASE))
    has_summary = bool(re.search(r'Summary\s*:', content, re.IGNORECASE))

    checks.append({
        "name": "has_filed_field",
        "passed": has_filed_field,
        "detail": "'Filed:' label present in report" if has_filed_field else "Missing 'Filed:' field from proprietary format"
    })
    checks.append({
        "name": "has_why_it_matters_field",
        "passed": has_why_matters,
        "detail": "'Why it matters:' label present" if has_why_matters else "Missing 'Why it matters:' — proprietary format field absent"
    })
    checks.append({
        "name": "has_summary_field",
        "passed": has_summary,
        "detail": "'Summary:' label present" if has_summary else "Missing 'Summary:' — proprietary format field absent"
    })

    # ── Check 6: Grouping — material events appear before routine ────────────
    # Heuristic: look for section headers or ordering markers
    has_grouping = bool(re.search(
        r'(material.{0,30}event|high.{0,20}signal|routine.{0,30}disclos|high.{0,20}priority)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "groups_by_significance",
        "passed": has_grouping,
        "detail": "Report groups filings by significance (material events first)" if has_grouping else "No evidence of significance-based grouping found"
    })

    # ── Check 7: Intelligence Preview section ─────────────────────────────────
    has_intel_preview = bool(re.search(
        r'(intelligence.{0,20}preview|signal.{0,20}report.{0,30}preview|stats.{0,30}summary|pattern.{0,30}detect)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "has_intelligence_preview",
        "passed": has_intel_preview,
        "detail": "Intelligence Preview section present (required by SKILL.md)" if has_intel_preview else "Missing Intelligence Preview section — agent skipped mandatory section"
    })

    # ── Check 8: Stats in preview — total filings count numeric ──────────────
    has_stats_numbers = bool(re.search(
        r'(total.{0,30}\d+|companies.{0,30}scanned.{0,30}\d+|\d+.{0,30}filing|\d+.{0,30}compan)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "preview_contains_numeric_stats",
        "passed": has_stats_numbers,
        "detail": "Intelligence Preview includes numeric statistics" if has_stats_numbers else "No numeric stats found in Intelligence Preview"
    })

    # ── Check 9: EDGAR link present ───────────────────────────────────────────
    has_edgar_link = bool(re.search(r'(https?://www\.sec\.gov|edgar\.sec\.gov|🔗)', content, re.IGNORECASE))
    checks.append({
        "name": "has_edgar_link",
        "passed": has_edgar_link,
        "detail": "EDGAR link (🔗) present in report" if has_edgar_link else "Missing EDGAR link — proprietary format requires 🔗 [EDGAR link]"
    })

    # ── Check 10: Semiconductor / Cloud AI companies in scope ─────────────────
    # Agent should have scanned the full watchlist (or at least semis + cloud AI)
    semis = ["AMD", "Intel", "Broadcom", "Qualcomm", "TSMC", "ASML", "Marvell", "Arm"]
    cloud = ["Snowflake", "MongoDB", "Cloudflare", "Datadog", "Elastic", "UiPath", "Dynatrace"]
    all_target = semis + cloud
    matched = [c for c in all_target if re.search(c, content, re.IGNORECASE)]
    covers_target_companies = len(matched) >= 3
    checks.append({
        "name": "covers_semiconductor_and_cloud_ai_companies",
        "passed": covers_target_companies,
        "detail": f"Report mentions {len(matched)} of target companies: {matched}" if covers_target_companies else f"Only {len(matched)} target company mentions found ({matched}); expected ≥3 from semiconductor/cloud AI watchlist"
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weighted scoring
    weights = {
        "output_file_exists": 2.0,
        "file_readable": 1.0,
        "report_non_trivial": 1.0,
        "contains_8k_filter_evidence": 2.0,
        "72_hour_lookback_mentioned": 1.5,
        "uses_filing_emoji_format": 2.0,
        "has_filed_field": 1.5,
        "has_why_it_matters_field": 2.0,
        "has_summary_field": 1.5,
        "groups_by_significance": 2.0,
        "has_intelligence_preview": 2.0,
        "preview_contains_numeric_stats": 1.5,
        "has_edgar_link": 1.5,
        "covers_semiconductor_and_cloud_ai_companies": 2.0,
    }

    total_weight = sum(weights.values())
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned_weight / total_weight, 4)

    # Hard gate: must have file + format fields + intelligence preview to pass
    mandatory = ["output_file_exists", "uses_filing_emoji_format", "has_why_it_matters_field", "has_intelligence_preview"]
    mandatory_passed = all(c["passed"] for c in checks if c["name"] in mandatory)

    overall_passed = mandatory_passed and score >= 0.60

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))