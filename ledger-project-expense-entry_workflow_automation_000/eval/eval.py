import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

def get_taipei_date():
    """Get today's date in Asia/Taipei (UTC+8)."""
    utc_now = datetime.now(timezone.utc)
    taipei_offset = timedelta(hours=8)
    taipei_now = utc_now + taipei_offset
    return taipei_now.strftime("%Y-%m-%d"), taipei_now.year, taipei_now.month

def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def run_checks(workspace_str):
    workspace = Path(workspace_str)
    checks = []
    passed_all = True

    today_str, year, month = get_taipei_date()
    expected_file = workspace / "projects" / "data" / f"ledger_{year}_{month:02d}.jsonl"

    # --- Check 0: Month file exists ---
    file_exists = expected_file.exists()
    checks.append({
        "name": "month_file_exists",
        "passed": file_exists,
        "detail": f"Expected file {expected_file} {'exists' if file_exists else 'does NOT exist'}."
    })
    if not file_exists:
        passed_all = False
        # Cannot continue without the file
        return passed_all, 0.0, checks

    try:
        records = load_jsonl(expected_file)
    except Exception as e:
        checks.append({"name": "jsonl_parse", "passed": False, "detail": f"Failed to parse JSONL: {e}"})
        return False, 0.0, checks

    checks.append({
        "name": "jsonl_parse",
        "passed": True,
        "detail": f"Parsed {len(records)} records from {expected_file.name}."
    })

    # We expect exactly 4 entries from the 4 messages.
    # Messages in prompt:
    # 1. "OpenClaw 服务器 1200"  -> 支出, CNY, 1200, description="OpenClaw - 服务器", tags include 服务器
    # 2. "NovaMind 购买 Figma 订阅 $49"  -> 支出, USD, 49, description="NovaMind - 购买 Figma 订阅", tags include 软件授权
    # 3. "PixelFarm 团队聚餐 320 收入"  -> TRICK: says 收入, CNY, 320, description="PixelFarm - 团队聚餐", tags include 下馆子
    # 4. "OpenClaw CDN 流量费 85"  -> 支出, CNY, 85, description="OpenClaw - CDN 流量费", tags include 通讯网络

    checks.append({
        "name": "entry_count",
        "passed": len(records) >= 4,
        "detail": f"Expected at least 4 records, found {len(records)}."
    })
    if len(records) < 4:
        passed_all = False

    def find_record(records, description_substr, direction=None, currency=None):
        for r in records:
            desc_match = description_substr.lower() in r.get("description", "").lower()
            dir_match = (direction is None) or (r.get("direction") == direction)
            cur_match = (currency is None) or (r.get("currency", "").upper() == currency.upper())
            if desc_match and dir_match and cur_match:
                return r
        return None

    # --- Check 1: OpenClaw server entry ---
    rec1 = find_record(records, "OpenClaw", direction="支出", currency="CNY")
    if rec1 is None:
        # Try looser search
        rec1 = find_record(records, "openclaw", direction="支出")
    c1_found = rec1 is not None
    c1_desc_ok = False
    c1_amount_ok = False
    c1_tags_ok = False
    c1_source_ok = False
    c1_batch_ok = False
    if c1_found:
        desc = rec1.get("description", "")
        # Must contain both "OpenClaw" and "服务器" with " - " separator
        c1_desc_ok = bool(re.search(r'OpenClaw\s*-\s*服务器', desc, re.IGNORECASE)) or \
                     ("openclaw" in desc.lower() and "服务器" in desc)
        c1_amount_ok = float(rec1.get("amount", 0)) == 1200.0
        tags = rec1.get("tags", [])
        c1_tags_ok = "服务器" in tags
        c1_source_ok = rec1.get("source") == "manual"
        c1_batch_ok = rec1.get("batch") == "manual"

    checks.append({"name": "entry1_openclaw_server_found", "passed": c1_found,
                   "detail": f"OpenClaw 服务器 支出 CNY record {'found' if c1_found else 'NOT found'}."})
    checks.append({"name": "entry1_description_format", "passed": c1_desc_ok,
                   "detail": f"Description format '<project> - <description>': {'OK' if c1_desc_ok else 'FAIL'}, got: {rec1.get('description','') if c1_found else 'N/A'}"})
    checks.append({"name": "entry1_amount_1200", "passed": c1_amount_ok,
                   "detail": f"Amount 1200: {'OK' if c1_amount_ok else 'FAIL'}, got: {rec1.get('amount') if c1_found else 'N/A'}"})
    checks.append({"name": "entry1_tag_服务器", "passed": c1_tags_ok,
                   "detail": f"Tag '服务器' present: {'YES' if c1_tags_ok else 'NO'}, tags: {rec1.get('tags') if c1_found else 'N/A'}"})
    checks.append({"name": "entry1_source_manual", "passed": c1_source_ok,
                   "detail": f"source=manual: {'OK' if c1_source_ok else 'FAIL'}"})
    checks.append({"name": "entry1_batch_manual", "passed": c1_batch_ok,
                   "detail": f"batch=manual: {'OK' if c1_batch_ok else 'FAIL'}"})

    for c in [c1_found, c1_desc_ok, c1_amount_ok, c1_tags_ok, c1_source_ok, c1_batch_ok]:
        if not c:
            passed_all = False

    # --- Check 2: NovaMind Figma subscription, USD ---
    rec2 = find_record(records, "NovaMind", direction="支出", currency="USD")
    if rec2 is None:
        rec2 = find_record(records, "figma", direction="支出")
    c2_found = rec2 is not None
    c2_currency_usd = False
    c2_amount_ok = False
    c2_desc_ok = False
    c2_tags_ok = False
    if c2_found:
        c2_currency_usd = rec2.get("currency", "").upper() == "USD"
        c2_amount_ok = float(rec2.get("amount", 0)) == 49.0
        desc2 = rec2.get("description", "")
        c2_desc_ok = "NovaMind" in desc2 and ("Figma" in desc2 or "figma" in desc2.lower())
        tags2 = rec2.get("tags", [])
        # 软件授权 is the correct tag for SaaS/subscription
        c2_tags_ok = "软件授权" in tags2

    checks.append({"name": "entry2_novamind_figma_found", "passed": c2_found,
                   "detail": f"NovaMind Figma USD record {'found' if c2_found else 'NOT found'}."})
    checks.append({"name": "entry2_currency_USD", "passed": c2_currency_usd,
                   "detail": f"Currency=USD: {'OK' if c2_currency_usd else 'FAIL'}, got: {rec2.get('currency','') if c2_found else 'N/A'}"})
    checks.append({"name": "entry2_amount_49", "passed": c2_amount_ok,
                   "detail": f"Amount=49: {'OK' if c2_amount_ok else 'FAIL'}, got: {rec2.get('amount') if c2_found else 'N/A'}"})
    checks.append({"name": "entry2_description_format", "passed": c2_desc_ok,
                   "detail": f"Description has NovaMind+Figma: {'OK' if c2_desc_ok else 'FAIL'}, got: {rec2.get('description','') if c2_found else 'N/A'}"})
    checks.append({"name": "entry2_tag_软件授权", "passed": c2_tags_ok,
                   "detail": f"Tag '软件授权' for subscription: {'YES' if c2_tags_ok else 'NO'}, tags: {rec2.get('tags') if c2_found else 'N/A'}"})

    for c in [c2_found, c2_currency_usd, c2_amount_ok, c2_desc_ok, c2_tags_ok]:
        if not c:
            passed_all = False

    # --- Check 3: PixelFarm 团队聚餐 — TRICKY: direction=收入 ---
    rec3 = find_record(records, "PixelFarm")
    if rec3 is None:
        rec3 = find_record(records, "团队聚餐")
    c3_found = rec3 is not None
    c3_direction_ok = False
    c3_amount_ok = False
    c3_currency_ok = False
    c3_tags_ok = False
    if c3_found:
        c3_direction_ok = rec3.get("direction") == "收入"
        c3_amount_ok = float(rec3.get("amount", 0)) == 320.0
        c3_currency_ok = rec3.get("currency", "").upper() == "CNY"
        tags3 = rec3.get("tags", [])
        # 下馆子 is appropriate for 团队聚餐 (dine-in)
        c3_tags_ok = "下馆子" in tags3

    checks.append({"name": "entry3_pixelfarm_meal_found", "passed": c3_found,
                   "detail": f"PixelFarm 团队聚餐 record {'found' if c3_found else 'NOT found'}."})
    checks.append({"name": "entry3_direction_收入_CRITICAL", "passed": c3_direction_ok,
                   "detail": f"Direction=收入 (NOT default 支出): {'OK' if c3_direction_ok else 'FAIL — agent used wrong default'}, got: {rec3.get('direction','') if c3_found else 'N/A'}"})
    checks.append({"name": "entry3_amount_320", "passed": c3_amount_ok,
                   "detail": f"Amount=320: {'OK' if c3_amount_ok else 'FAIL'}, got: {rec3.get('amount') if c3_found else 'N/A'}"})
    checks.append({"name": "entry3_currency_CNY_default", "passed": c3_currency_ok,
                   "detail": f"Currency=CNY (default applied): {'OK' if c3_currency_ok else 'FAIL'}"})
    checks.append({"name": "entry3_tag_下馆子", "passed": c3_tags_ok,
                   "detail": f"Tag '下馆子' for 团队聚餐: {'YES' if c3_tags_ok else 'NO'}, tags: {rec3.get('tags') if c3_found else 'N/A'}"})

    for c in [c3_found, c3_direction_ok, c3_amount_ok, c3_currency_ok, c3_tags_ok]:
        if not c:
            passed_all = False

    # --- Check 4: OpenClaw CDN 流量费 ---
    # Must distinguish from entry 1 (also OpenClaw): look for CDN or 通讯网络
    rec4 = None
    for r in records:
        desc = r.get("description", "")
        if "OpenClaw" in desc and ("CDN" in desc or "流量" in desc or "通讯" in desc):
            rec4 = r
            break
    if rec4 is None:
        # Try by tags
        for r in records:
            if "通讯网络" in r.get("tags", []) and "OpenClaw" in r.get("description", ""):
                rec4 = r
                break
    c4_found = rec4 is not None
    c4_direction_ok = False
    c4_amount_ok = False
    c4_currency_ok = False
    c4_desc_ok = False
    c4_tags_ok = False
    if c4_found:
        c4_direction_ok = rec4.get("direction") == "支出"
        c4_amount_ok = float(rec4.get("amount", 0)) == 85.0
        c4_currency_ok = rec4.get("currency", "").upper() == "CNY"
        desc4 = rec4.get("description", "")
        c4_desc_ok = "OpenClaw" in desc4 and ("CDN" in desc4 or "流量" in desc4 or "通讯" in desc4)
        tags4 = rec4.get("tags", [])
        # CDN -> 通讯网络 per catalog note
        c4_tags_ok = "通讯网络" in tags4

    checks.append({"name": "entry4_openclaw_cdn_found", "passed": c4_found,
                   "detail": f"OpenClaw CDN 流量费 record {'found' if c4_found else 'NOT found'}."})
    checks.append({"name": "entry4_direction_支出", "passed": c4_direction_ok,
                   "detail": f"Direction=支出: {'OK' if c4_direction_ok else 'FAIL'}"})
    checks.append({"name": "entry4_amount_85", "passed": c4_amount_ok,
                   "detail": f"Amount=85: {'OK' if c4_amount_ok else 'FAIL'}, got: {rec4.get('amount') if c4_found else 'N/A'}"})
    checks.append({"name": "entry4_currency_CNY", "passed": c4_currency_ok,
                   "detail": f"Currency=CNY: {'OK' if c4_currency_ok else 'FAIL'}"})
    checks.append({"name": "entry4_tag_通讯网络_CDN", "passed": c4_tags_ok,
                   "detail": f"Tag '通讯网络' for CDN: {'YES' if c4_tags_ok else 'NO'}, tags: {rec4.get('tags') if c4_found else 'N/A'}"})

    for c in [c4_found, c4_direction_ok, c4_amount_ok, c4_currency_ok, c4_tags_ok]:
        if not c:
            passed_all = False

    # --- Check 5: All records have correct date (today in Taipei) ---
    wrong_dates = [r for r in records if r.get("date") != today_str]
    c5_ok = len(wrong_dates) == 0
    checks.append({"name": "all_dates_are_today_taipei", "passed": c5_ok,
                   "detail": f"All records dated {today_str}: {'OK' if c5_ok else f'FAIL — {len(wrong_dates)} records have wrong date: {[r.get(\"date\") for r in wrong_dates]}'}"})
    if not c5_ok:
        passed_all = False

    # --- Score calculation ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    return passed_all, score, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        passed_all, score, checks = run_checks(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }, ensure_ascii=False, indent=2))
        sys.exit(0)

    print(json.dumps({
        "passed": passed_all,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()