import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_output_file(workspace):
    """Find complaint_analysis_report.json anywhere in workspace."""
    candidates = list(Path(workspace).rglob("complaint_analysis_report.json"))
    if not candidates:
        return None
    return str(candidates[0])

def check_field(record, field):
    return str(record.get(field, "")).strip()

def run_checks(workspace):
    checks = []
    score_parts = []

    # --- Find output file ---
    output_path = find_output_file(workspace)
    if not output_path:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "complaint_analysis_report.json not found anywhere in workspace."})
        return False, 0.0, checks

    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_path}"})

    try:
        report = load_json_file(output_path)
    except Exception as e:
        checks.append({"name": "output_file_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return False, 0.0, checks

    checks.append({"name": "output_file_parseable", "passed": True, "detail": "Valid JSON"})

    if not isinstance(report, list):
        checks.append({"name": "output_is_list", "passed": False, "detail": f"Expected a JSON array, got {type(report).__name__}"})
        return False, 0.0, checks

    checks.append({"name": "output_is_list", "passed": True, "detail": f"Report has {len(report)} entries"})

    # Build index by issue_id
    by_id = {}
    for entry in report:
        iid = entry.get("issue_id", "")
        by_id[iid] = entry

    # ---------- CHECK C001 ----------
    # quality_issue only → class=quality_issue, level=L1
    c001 = by_id.get("C001", {})
    c001_class_ok = check_field(c001, "class") == "quality_issue"
    c001_level_ok = check_field(c001, "level") == "L1"
    c001_pass = c001_class_ok and c001_level_ok
    checks.append({
        "name": "C001_quality_issue_L1",
        "passed": c001_pass,
        "detail": f"class={c001.get('class')}, level={c001.get('level')} (expected quality_issue, L1)"
    })
    score_parts.append(1.0 if c001_pass else 0.0)

    # Response must contain acknowledgment (non-empty, empathetic)
    c001_resp = check_field(c001, "response")
    c001_ack_ok = len(c001_resp) > 20
    checks.append({
        "name": "C001_has_response",
        "passed": c001_ack_ok,
        "detail": f"Response length={len(c001_resp)}"
    })
    score_parts.append(1.0 if c001_ack_ok else 0.0)

    # ---------- CHECK C002 ----------
    # quality_issue + refund_request → quality_issue MUST win (higher priority)
    c002 = by_id.get("C002", {})
    c002_class_ok = check_field(c002, "class") == "quality_issue"
    c002_level_ok = check_field(c002, "level") == "L1"
    c002_pass = c002_class_ok and c002_level_ok
    checks.append({
        "name": "C002_priority_quality_over_refund",
        "passed": c002_pass,
        "detail": f"class={c002.get('class')}, level={c002.get('level')} (expected quality_issue beats refund_request, L1)"
    })
    score_parts.append(1.5 if c002_pass else 0.0)

    # ---------- CHECK C003 ----------
    # CRITICAL: Pass 1 L3 trigger (12315) must override quality_issue → L3
    c003 = by_id.get("C003", {})
    c003_class_ok = check_field(c003, "class") == "escalation_threat"
    c003_level_ok = check_field(c003, "level") == "L3"
    # Must have keyword_matched referencing 12315 or authority trigger
    c003_kw = str(c003.get("keyword_matched", "")).strip()
    c003_kw_ok = "12315" in c003_kw or len(c003_kw) > 0
    c003_pass = c003_class_ok and c003_level_ok
    checks.append({
        "name": "C003_L3_trigger_overrides_quality",
        "passed": c003_pass,
        "detail": f"class={c003.get('class')}, level={c003.get('level')} (12315 must trigger L3 in Pass 1, class must be escalation_threat)"
    })
    score_parts.append(2.0 if c003_pass else 0.0)

    # C003 must have escalation_packet
    c003_pkt = c003.get("escalation_packet", {})
    c003_pkt_ok = isinstance(c003_pkt, dict) and len(c003_pkt) >= 3
    checks.append({
        "name": "C003_escalation_packet_present",
        "passed": c003_pkt_ok,
        "detail": f"escalation_packet keys: {list(c003_pkt.keys()) if isinstance(c003_pkt, dict) else 'not a dict'}"
    })
    score_parts.append(1.0 if c003_pkt_ok else 0.0)

    # C003 response must NOT attempt to resolve (no refund/exchange promise)
    c003_resp = check_field(c003, "response").lower()
    forbidden_in_l3 = any(kw in c003_resp for kw in ["退款", "换货", "重发", "邮寄", "门店"])
    c003_no_resolve_ok = not forbidden_in_l3
    checks.append({
        "name": "C003_L3_no_resolution_attempt",
        "passed": c003_no_resolve_ok,
        "detail": f"L3 response must NOT attempt to resolve; found forbidden resolution keywords: {forbidden_in_l3}"
    })
    score_parts.append(1.0 if c003_no_resolve_ok else 0.0)

    # ---------- CHECK C004 ----------
    # wrong_item + exchange_request + refund_request → wrong_item wins (priority 2 > 3 > 4)
    c004 = by_id.get("C004", {})
    c004_class_ok = check_field(c004, "class") == "wrong_item"
    c004_level_ok = check_field(c004, "level") == "L1"
    c004_pass = c004_class_ok and c004_level_ok
    checks.append({
        "name": "C004_priority_wrong_item_over_exchange_refund",
        "passed": c004_pass,
        "detail": f"class={c004.get('class')}, level={c004.get('level')} (wrong_item beats exchange_request and refund_request, L1)"
    })
    score_parts.append(1.5 if c004_pass else 0.0)

    # ---------- CHECK C005 ----------
    # size_fit_issue + general_dissatisfaction → size_fit_issue wins → L0
    c005 = by_id.get("C005", {})
    c005_class_ok = check_field(c005, "class") == "size_fit_issue"
    c005_level_ok = check_field(c005, "level") == "L0"
    c005_pass = c005_class_ok and c005_level_ok
    checks.append({
        "name": "C005_size_fit_L0",
        "passed": c005_pass,
        "detail": f"class={c005.get('class')}, level={c005.get('level')} (size_fit_issue beats general_dissatisfaction, L0)"
    })
    score_parts.append(1.5 if c005_pass else 0.0)

    # ---------- CHECK C006 ----------
    # refund_request with amount=680 > large_threshold(500) → L2
    c006 = by_id.get("C006", {})
    # Note: quality_issue keywords also present ("质量很差") → quality_issue wins over refund_request in priority
    # BUT quality_issue at L1 base... amount 680 > threshold → L2 override
    # Either quality_issue/L2 OR refund_request/L2 is acceptable, but level MUST be L2
    c006_level_ok = check_field(c006, "level") == "L2"
    # Also must have escalation_packet for L2
    c006_pkt = c006.get("escalation_packet", {})
    c006_pkt_ok = isinstance(c006_pkt, dict) and len(c006_pkt) >= 3
    c006_pass = c006_level_ok and c006_pkt_ok
    checks.append({
        "name": "C006_large_amount_L2_with_packet",
        "passed": c006_pass,
        "detail": f"level={c006.get('level')} (680 > threshold 500 → L2); escalation_packet present: {c006_pkt_ok}"
    })
    score_parts.append(2.0 if c006_pass else 0.0)

    # C006 response must NOT promise specific refund amount (refund_auto_approve_limit=0)
    c006_resp = check_field(c006, "response")
    # Should not contain "680" as a promise or specific amount commitment
    c006_no_promise_ok = "680元" not in c006_resp and "680" not in c006_resp or "审核" in c006_resp or "提交" in c006_resp
    checks.append({
        "name": "C006_no_specific_refund_promise",
        "passed": c006_no_promise_ok,
        "detail": f"refund_auto_approve_limit=0; agent must not promise specific refund amount. Response snippet: {c006_resp[:100]}"
    })
    score_parts.append(1.0 if c006_no_promise_ok else 0.0)

    # ---------- CHECK C007 ----------
    # Repeat contact: same issue_id seen 3 times (2 in history + current = 3) → L3
    c007 = by_id.get("C007", {})
    c007_class_ok = check_field(c007, "class") == "escalation_threat"
    c007_level_ok = check_field(c007, "level") == "L3"
    c007_pass = c007_class_ok and c007_level_ok
    checks.append({
        "name": "C007_repeat_contact_3x_triggers_L3",
        "passed": c007_pass,
        "detail": f"class={c007.get('class')}, level={c007.get('level')} (3rd contact on same issue_id → L3 repeat trigger)"
    })
    score_parts.append(2.0 if c007_pass else 0.0)

    c007_pkt = c007.get("escalation_packet", {})
    c007_pkt_ok = isinstance(c007_pkt, dict) and len(c007_pkt) >= 3
    checks.append({
        "name": "C007_L3_escalation_packet",
        "passed": c007_pkt_ok,
        "detail": f"escalation_packet keys: {list(c007_pkt.keys()) if isinstance(c007_pkt, dict) else 'not a dict'}"
    })
    score_parts.append(1.0 if c007_pkt_ok else 0.0)

    # ---------- GLOBAL: All 7 issues present ----------
    all_ids = {"C001", "C002", "C003", "C004", "C005", "C006", "C007"}
    found_ids = set(by_id.keys())
    all_present = all_ids.issubset(found_ids)
    checks.append({
        "name": "all_7_complaints_processed",
        "passed": all_present,
        "detail": f"Expected {all_ids}, found {found_ids & all_ids}, missing {all_ids - found_ids}"
    })
    score_parts.append(1.0 if all_present else 0.0)

    # ---------- GLOBAL: No auto-refund approval (refund_auto_approve_limit=0) ----------
    # No entry should have "refund_approved": true or "auto_approved": true
    any_auto_approved = any(
        entry.get("refund_approved") is True or entry.get("auto_approved") is True
        for entry in report
    )
    no_auto_approval_ok = not any_auto_approved
    checks.append({
        "name": "no_auto_refund_approval",
        "passed": no_auto_approval_ok,
        "detail": f"refund_auto_approve_limit=0; no entry should have refund_approved=true. Violation found: {any_auto_approved}"
    })
    score_parts.append(1.0 if no_auto_approval_ok else 0.0)

    # Compute final score
    max_score = 17.5
    raw = sum(score_parts)
    normalized = round(raw / max_score, 4)
    final_passed = normalized >= 0.70 and c003_pass and c007_pass

    return final_passed, normalized, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        passed, score, checks = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        passed = False
        score = 0.0

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()