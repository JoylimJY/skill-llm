import sys
import json
import os
from pathlib import Path

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Check 1: morning_digest.json exists ─────────────────────────────────
    digest_candidates = list(workspace.rglob("morning_digest.json"))
    if not digest_candidates:
        checks.append({
            "name": "morning_digest.json exists",
            "passed": False,
            "detail": "File morning_digest.json not found anywhere in workspace"
        })
        return False, 0.0, checks

    digest_path = digest_candidates[0]
    checks.append({
        "name": "morning_digest.json exists",
        "passed": True,
        "detail": f"Found at {digest_path}"
    })
    total_score += 0.05

    # ── Check 2: File is valid JSON ──────────────────────────────────────────
    try:
        with open(digest_path, "r", encoding="utf-8") as f:
            digest = json.load(f)
        checks.append({
            "name": "Valid JSON format",
            "passed": True,
            "detail": "JSON parsed successfully"
        })
        total_score += 0.05
    except (json.JSONDecodeError, OSError) as e:
        checks.append({
            "name": "Valid JSON format",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        return False, total_score, checks

    # ── Check 3: Top-level structure has required sections ───────────────────
    required_top_keys = ["market_sentiment", "margin_financing", "delivery_dates"]
    # Be flexible: also accept snake_case variants or Chinese keys
    flexible_market_keys = ["market_sentiment", "market", "sentiment", "赚钱效应", "市场情绪", "snapshot"]
    flexible_margin_keys = ["margin_financing", "margin", "融资融券", "两融", "margin_top", "financing"]
    flexible_delivery_keys = ["delivery_dates", "delivery", "交割日", "futures_delivery", "calendar"]

    def has_key_flexible(d, candidates):
        return any(k in d for k in candidates)

    has_market = has_key_flexible(digest, flexible_market_keys)
    has_margin = has_key_flexible(digest, flexible_margin_keys)
    has_delivery = has_key_flexible(digest, flexible_delivery_keys)

    checks.append({
        "name": "Contains market sentiment section",
        "passed": has_market,
        "detail": f"Keys found: {list(digest.keys())}"
    })
    if has_market:
        total_score += 0.10

    checks.append({
        "name": "Contains margin financing section",
        "passed": has_margin,
        "detail": f"Keys found: {list(digest.keys())}"
    })
    if has_margin:
        total_score += 0.10

    checks.append({
        "name": "Contains delivery dates section",
        "passed": has_delivery,
        "detail": f"Keys found: {list(digest.keys())}"
    })
    if has_delivery:
        total_score += 0.10

    # ── Check 4: Market section has sentiment_index ──────────────────────────
    market_section = None
    for k in flexible_market_keys:
        if k in digest:
            market_section = digest[k]
            break

    sentiment_index_found = False
    sentiment_label_found = False
    if market_section and isinstance(market_section, dict):
        # Look recursively for sentiment_index
        def find_key_recursive(d, target_keys):
            if not isinstance(d, dict):
                return None
            for k, v in d.items():
                if k in target_keys:
                    return v
                if isinstance(v, dict):
                    result = find_key_recursive(v, target_keys)
                    if result is not None:
                        return result
            return None

        si_val = find_key_recursive(market_section, ["sentiment_index", "赚钱效应指数"])
        sentiment_index_found = si_val is not None and si_val != ""
        sl_val = find_key_recursive(market_section, ["sentiment_label", "情绪标签", "label"])
        sentiment_label_found = sl_val is not None and sl_val != ""

    checks.append({
        "name": "Market section contains sentiment_index (from --json output)",
        "passed": sentiment_index_found,
        "detail": f"sentiment_index present: {sentiment_index_found}, market_section type: {type(market_section).__name__}"
    })
    if sentiment_index_found:
        total_score += 0.10

    # ── Check 5: ladder_detail lb_rates_map present ──────────────────────────
    # This is the proprietary trap: lb_rates_map uses string keys like "2", "3"
    ladder_data_found = False
    lb_rates_found = False

    def find_lb_rates(d, depth=0):
        if depth > 5 or not isinstance(d, dict):
            return False
        if "lb_rates_map" in d:
            val = d["lb_rates_map"]
            # Must be a dict with string numeric keys
            if isinstance(val, dict) and len(val) > 0:
                return True
        for v in d.values():
            if isinstance(v, dict):
                if find_lb_rates(v, depth + 1):
                    return True
        return False

    lb_rates_found = find_lb_rates(digest)
    # Also check if ladder_detail or ladder data is present at all
    def find_ladder_data(d, depth=0):
        if depth > 5 or not isinstance(d, dict):
            return False
        for k in d:
            if "ladder" in k.lower() or "连板" in k:
                return True
        for v in d.values():
            if isinstance(v, dict):
                if find_ladder_data(v, depth + 1):
                    return True
        return False
    ladder_data_found = find_ladder_data(digest)

    checks.append({
        "name": "Contains ladder/连板 data (from snapshot --json)",
        "passed": ladder_data_found,
        "detail": f"ladder data found in digest: {ladder_data_found}"
    })
    if ladder_data_found:
        total_score += 0.08

    checks.append({
        "name": "Contains lb_rates_map with string numeric keys (proprietary field)",
        "passed": lb_rates_found,
        "detail": "lb_rates_map is a bespoke field in ladder_detail with keys like '2','3','4'"
    })
    if lb_rates_found:
        total_score += 0.10

    # ── Check 6: Margin section has TOP-5 net-buy stocks ────────────────────
    margin_section = None
    for k in flexible_margin_keys:
        if k in digest:
            margin_section = digest[k]
            break

    top5_found = False
    delta_rz_found = False
    increase_rzye_found = False

    if margin_section:
        margin_str = json.dumps(margin_section, ensure_ascii=False)
        # Must have at least some stock names or increase_rzye data
        # Check for increase_rzye key (the proprietary field name)
        if "increase_rzye" in margin_str:
            increase_rzye_found = True
        # Check for delta indicator
        if any(k in margin_str for k in ["delta_rzye", "delta_rz", "7日", "变化"]):
            delta_rz_found = True
        # Check for at least 5 stock entries (top 5)
        if isinstance(margin_section, dict):
            def count_stocks(d):
                count = 0
                if isinstance(d, list):
                    return len(d)
                if isinstance(d, dict):
                    for v in d.values():
                        if isinstance(v, list):
                            count = max(count, len(v))
                        elif isinstance(v, dict):
                            count = max(count, count_stocks(v))
                return count
            n_stocks = count_stocks(margin_section)
            top5_found = n_stocks >= 3  # at least 3 entries

    checks.append({
        "name": "Margin section contains increase_rzye (proprietary field name)",
        "passed": increase_rzye_found,
        "detail": f"'increase_rzye' key found in margin data: {increase_rzye_found}"
    })
    if increase_rzye_found:
        total_score += 0.12

    checks.append({
        "name": "Margin section contains top movers data (>=3 entries)",
        "passed": top5_found,
        "detail": f"top movers list present with sufficient entries: {top5_found}"
    })
    if top5_found:
        total_score += 0.08

    # ── Check 7: Delivery section has events list ────────────────────────────
    delivery_section = None
    for k in flexible_delivery_keys:
        if k in digest:
            delivery_section = digest[k]
            break

    delivery_events_found = False
    delivery_has_dates = False

    if delivery_section:
        delivery_str = json.dumps(delivery_section, ensure_ascii=False)
        # Check for 'events' key or date-like strings
        if "events" in delivery_str or "date" in delivery_str:
            delivery_events_found = True
        # Check for actual date strings like 2026-
        import re
        dates_in_delivery = re.findall(r"\d{4}-\d{2}-\d{2}", delivery_str)
        delivery_has_dates = len(dates_in_delivery) >= 2

    checks.append({
        "name": "Delivery section contains events with dates",
        "passed": delivery_events_found,
        "detail": f"events/date keys found: {delivery_events_found}"
    })
    if delivery_events_found:
        total_score += 0.07

    checks.append({
        "name": "Delivery section has multiple date entries (>=2 dates)",
        "passed": delivery_has_dates,
        "detail": f"date strings found: {delivery_has_dates}"
    })
    if delivery_has_dates:
        total_score += 0.05

    # ── Check 8: signals_count handled (present or explicitly null) ──────────
    # The SKILL.md says signals_count is optional — agent must handle it gracefully
    signals_handled = False
    digest_str = json.dumps(digest, ensure_ascii=False)
    if any(k in digest_str for k in ["signals_count", "signals", "量化", "jiuzhuan", "multi_factor", "emotion_sync"]):
        signals_handled = True
    # Also OK if it's explicitly null/absent but the rest of data is good
    # We give credit if the digest was successfully constructed (implies graceful handling)
    if not signals_handled and sentiment_index_found and increase_rzye_found:
        signals_handled = True  # gracefully handled (omitted when null)

    checks.append({
        "name": "signals_count handled gracefully (present or gracefully omitted)",
        "passed": signals_handled,
        "detail": "signals_count is optional per schema; agent must not crash if absent"
    })
    if signals_handled:
        total_score += 0.05

    # ── Check 9: Data sourced via --json flag (raw JSON used, not screen-scraped) ──
    # Heuristic: if the digest contains raw schema field names like 'meta', 'schema_version',
    # or other raw API fields, it was likely obtained via --json
    raw_field_indicators = ["schema_version", "generated_at", "rzye_yi", "rqye_yi",
                             "delta_rzye_yi", "delta_pct", "lb_rates_map", "net_yi",
                             "top_net_buy", "seats", "bias_pct", "struct_diff"]
    raw_fields_found = sum(1 for f in raw_field_indicators if f in digest_str)

    checks.append({
        "name": "Raw JSON field names present (data obtained via --json flag)",
        "passed": raw_fields_found >= 3,
        "detail": f"Found {raw_fields_found}/15 raw schema field indicators: {[f for f in raw_field_indicators if f in digest_str]}"
    })
    if raw_fields_found >= 3:
        total_score += 0.05

    # ── Final pass/fail ──────────────────────────────────────────────────────
    critical_checks = [
        "morning_digest.json exists",
        "Valid JSON format",
        "Contains market sentiment section",
        "Contains margin financing section",
        "Contains delivery dates section",
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)

    final_passed = critical_passed and total_score >= 0.45

    return final_passed, min(total_score, 1.0), checks


def main():
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        passed, score, checks = run_checks(workspace_dir)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()