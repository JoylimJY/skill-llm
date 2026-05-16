import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime

def evaluate(workspace: str):
    checks = []
    base = Path(workspace) / "investment-committee"
    history_dir = base / "history"

    # ── Helper ──────────────────────────────────────────────────────────────
    def add(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── Find the report file ─────────────────────────────────────────────────
    # Expected: YYYY-MM-DD_*BTC*GOLD*.md  or  YYYY-MM-DD_*比较*.md  etc.
    # We allow flexible naming as long as it's in history/ and mentions both assets
    report_file = None
    report_content = ""
    try:
        candidates = list(history_dir.glob("*.md"))
        # Filter out the pre-existing distractor files
        pre_existing = {"2024-01-15_NVDA_买入判断.md", "2024-02-20_腾讯_仓位管理.md"}
        new_files = [f for f in candidates if f.name not in pre_existing]
        if new_files:
            # Pick the most recently created/modified
            report_file = max(new_files, key=lambda f: f.stat().st_mtime)
            report_content = report_file.read_text(encoding="utf-8")
            add("report_file_exists", True, f"Found report: {report_file.name}")
        else:
            add("report_file_exists", False, f"No new .md file found in {history_dir}")
    except Exception as e:
        add("report_file_exists", False, f"Error scanning history dir: {e}")

    if not report_content:
        # All remaining checks fail
        for name in [
            "filename_date_format",
            "filename_contains_assets",
            "both_assets_analyzed",
            "all_five_members_present",
            "scores_present",
            "weighted_score_present",
            "special_asset_note",
            "munger_duan_low_scores",
            "veto_rule_checked",
            "max_divergence_identified",
            "comparison_mode_conclusion",
            "correct_symbol_mapping_evidence",
            "stop_loss_present",
        ]:
            add(name, False, "Report file not found; check skipped.")
        total = sum(1 for c in checks if c["passed"])
        return {"passed": False, "score": total / len(checks), "checks": checks}

    # ── CHECK 1: Filename date format ────────────────────────────────────────
    try:
        fname = report_file.name
        date_match = re.match(r"(\d{4}-\d{2}-\d{2})", fname)
        if date_match:
            date_str = date_match.group(1)
            datetime.strptime(date_str, "%Y-%m-%d")
            add("filename_date_format", True, f"Date prefix '{date_str}' is valid.")
        else:
            add("filename_date_format", False, f"Filename '{fname}' does not start with YYYY-MM-DD.")
    except Exception as e:
        add("filename_date_format", False, str(e))

    # ── CHECK 2: Filename contains asset references ───────────────────────────
    try:
        fname_lower = report_file.name.lower()
        has_btc = any(kw in fname_lower for kw in ["btc", "bitcoin", "比特币"])
        has_gold = any(kw in fname_lower for kw in ["gold", "xauusd", "黄金"])
        has_compare = any(kw in fname_lower for kw in ["比较", "compare", "vs", "对比"])
        if (has_btc or has_gold) or has_compare:
            add("filename_contains_assets", True, f"Filename references BTC/GOLD or comparison: {fname}")
        else:
            add("filename_contains_assets", False, f"Filename '{fname}' does not reference BTC, GOLD, or comparison.")
    except Exception as e:
        add("filename_contains_assets", False, str(e))

    # ── CHECK 3: Both assets analyzed in content ─────────────────────────────
    try:
        content_lower = report_content.lower()
        has_btc_content = any(kw in content_lower for kw in ["btc", "bitcoin", "比特币", "btc.v"])
        has_gold_content = any(kw in content_lower for kw in ["gold", "xauusd", "黄金", "2341"])
        if has_btc_content and has_gold_content:
            add("both_assets_analyzed", True, "Report contains analysis of both BTC and GOLD.")
        else:
            missing = []
            if not has_btc_content: missing.append("BTC")
            if not has_gold_content: missing.append("GOLD")
            add("both_assets_analyzed", False, f"Missing analysis for: {missing}")
    except Exception as e:
        add("both_assets_analyzed", False, str(e))

    # ── CHECK 4: All five committee members present ───────────────────────────
    try:
        members = ["芒格", "马克斯", "段永平", "德鲁肯米勒", "西蒙斯"]
        missing_members = [m for m in members if m not in report_content]
        if not missing_members:
            add("all_five_members_present", True, "All five committee members mentioned.")
        else:
            add("all_five_members_present", False, f"Missing members: {missing_members}")
    except Exception as e:
        add("all_five_members_present", False, str(e))

    # ── CHECK 5: Numeric scores present (X/10 pattern) ───────────────────────
    try:
        score_pattern = re.findall(r"(\d+(?:\.\d+)?)\s*/\s*10", report_content)
        if len(score_pattern) >= 5:
            add("scores_present", True, f"Found {len(score_pattern)} score(s)/10 in report.")
        else:
            add("scores_present", False, f"Expected ≥5 scores (X/10), found {len(score_pattern)}.")
    except Exception as e:
        add("scores_present", False, str(e))

    # ── CHECK 6: Weighted composite score present ─────────────────────────────
    try:
        # Look for a composite/aggregate score pattern
        weighted_patterns = [
            r"加权综合分.*?(\d+(?:\.\d+)?)\s*/\s*10",
            r"综合.*?(\d+(?:\.\d+)?)\s*/\s*10",
            r"weighted.*?(\d+(?:\.\d+)?)\s*/\s*10",
        ]
        found_weighted = False
        for pat in weighted_patterns:
            if re.search(pat, report_content, re.IGNORECASE):
                found_weighted = True
                break
        add("weighted_score_present", found_weighted,
            "Weighted composite score (加权综合分) found." if found_weighted
            else "No weighted composite score found in report.")
    except Exception as e:
        add("weighted_score_present", False, str(e))

    # ── CHECK 7: Special asset note (critical proprietary rule) ──────────────
    try:
        special_note_keywords = [
            "宏观/量化视角权重更具参考价值",
            "宏观/量化视角",
            "宏观视角权重",
            "量化视角权重更具参考价值",
        ]
        found_note = any(kw in report_content for kw in special_note_keywords)
        add("special_asset_note", found_note,
            "Special crypto/gold asset weight note found." if found_note
            else "Missing required note: '本标的宏观/量化视角权重更具参考价值'")
    except Exception as e:
        add("special_asset_note", False, str(e))

    # ── CHECK 8: Munger and Duan have low scores (≤4/10) for BTC or GOLD ─────
    try:
        # Extract scores near Munger and Duan mentions
        munger_scores = re.findall(r"芒格.*?(\d+)\s*/\s*10|(\d+)\s*/\s*10.*?芒格", report_content)
        duan_scores = re.findall(r"段永平.*?(\d+)\s*/\s*10|(\d+)\s*/\s*10.*?段永平", report_content)

        def extract_first_score(matches):
            for m in matches:
                val = m[0] or m[1]
                if val:
                    return int(val)
            return None

        munger_score = extract_first_score(munger_scores)
        duan_score = extract_first_score(duan_scores)

        if munger_score is not None and duan_score is not None:
            both_low = munger_score <= 4 and duan_score <= 4
            add("munger_duan_low_scores", both_low,
                f"Munger={munger_score}/10, Duan={duan_score}/10. "
                + ("Both appropriately low for crypto/gold." if both_low
                   else "Expected both ≤4/10 for crypto/gold assets per skill rules."))
        elif munger_score is not None:
            add("munger_duan_low_scores", munger_score <= 4,
                f"Munger={munger_score}/10 (Duan score not clearly parseable).")
        else:
            add("munger_duan_low_scores", False,
                "Could not parse Munger or Duan scores from report.")
    except Exception as e:
        add("munger_duan_low_scores", False, str(e))

    # ── CHECK 9: Veto rule checked ─────────────────────────────────────────────
    try:
        veto_keywords = ["否决", "高风险警示", "⚠️", "触发", "veto", "委员会否决"]
        found_veto = any(kw in report_content for kw in veto_keywords)
        # Also accept if report explicitly says no veto triggered
        no_veto_keywords = ["未触发", "无否决", "不触发"]
        found_no_veto = any(kw in report_content for kw in no_veto_keywords)
        add("veto_rule_checked", found_veto or found_no_veto,
            "Veto rule check present in report." if (found_veto or found_no_veto)
            else "No veto rule check found. Report must explicitly check veto conditions.")
    except Exception as e:
        add("veto_rule_checked", False, str(e))

    # ── CHECK 10: Maximum divergence identified ────────────────────────────────
    try:
        divergence_keywords = ["最大分歧", "分差", "divergence", "差距最大"]
        found_divergence = any(kw in report_content for kw in divergence_keywords)
        add("max_divergence_identified", found_divergence,
            "Max divergence between committee members identified." if found_divergence
            else "Missing max divergence section (required by verdict.md).")
    except Exception as e:
        add("max_divergence_identified", False, str(e))

    # ── CHECK 11: Comparison mode conclusion ─────────────────────────────────
    try:
        comparison_keywords = ["比较结论", "更优", "选择", "推荐", "BTC vs", "黄金 vs",
                               "比特币 vs", "哪个更好", "comparison", "更适合"]
        found_comparison = any(kw in report_content for kw in comparison_keywords)
        add("comparison_mode_conclusion", found_comparison,
            "Comparison conclusion present." if found_comparison
            else "Missing comparative conclusion between BTC and GOLD.")
    except Exception as e:
        add("comparison_mode_conclusion", False, str(e))

    # ── CHECK 12: Evidence of correct symbol mapping (btc.v or xauusd) ────────
    try:
        has_btcv = "btc.v" in report_content.lower()
        has_xauusd = "xauusd" in report_content.lower()
        # Also accept if specific prices from fetch_price.py appear (67432 or 2341)
        has_btc_price = "67432" in report_content
        has_gold_price = "2341" in report_content
        correct_mapping = (has_btcv or has_btc_price) and (has_xauusd or has_gold_price)
        add("correct_symbol_mapping_evidence", correct_mapping,
            "Correct symbol mapping evidence found (btc.v/67432 and xauusd/2341)." if correct_mapping
            else f"Missing symbol mapping evidence. btc.v={has_btcv}, xauusd={has_xauusd}, "
                 f"price67432={has_btc_price}, price2341={has_gold_price}")
    except Exception as e:
        add("correct_symbol_mapping_evidence", False, str(e))

    # ── CHECK 13: Stop-loss parameter present ─────────────────────────────────
    try:
        stoploss_patterns = [r"止损", r"stop.?loss", r"止损价", r"离场价"]
        found_sl = any(re.search(p, report_content, re.IGNORECASE) for p in stoploss_patterns)
        add("stop_loss_present", found_sl,
            "Stop-loss price parameter present (from Druckenmiller framework)." if found_sl
            else "Missing stop-loss price parameter (required by Druckenmiller framework).")
    except Exception as e:
        add("stop_loss_present", False, str(e))

    # ── Final scoring ──────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    overall_passed = passed_count >= 10  # Must pass at least 10/13 checks

    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("WORKSPACE", "/workspace")
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))