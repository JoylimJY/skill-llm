import sys
import json
import re
from pathlib import Path

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    def add(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Locate output files ────────────────────────────────────────────────
    # Analysis comment (Comment A)
    analysis_files = list(ws.rglob("LINEAR-2847_analysis.txt"))
    reply_files = list(ws.rglob("LINEAR-2847_reply.txt"))

    if not analysis_files:
        total_score += add(
            "analysis_file_exists",
            False,
            "LINEAR-2847_analysis.txt not found anywhere in workspace"
        )
    if not reply_files:
        total_score += add(
            "reply_file_exists",
            False,
            "LINEAR-2847_reply.txt not found anywhere in workspace"
        )

    if not analysis_files or not reply_files:
        # Early exit if both files missing
        final_passed = total_score >= 6.0
        return {"passed": final_passed, "score": total_score / 10.0, "checks": checks}

    analysis_path = analysis_files[0]
    reply_path = reply_files[0]

    try:
        analysis_text = analysis_path.read_text(encoding="utf-8")
    except Exception as e:
        total_score += add("analysis_file_readable", False, f"Cannot read analysis file: {e}")
        analysis_text = ""
    else:
        total_score += add("analysis_file_exists", True, f"Found at {analysis_path}", weight=0.5)

    try:
        reply_text = reply_path.read_text(encoding="utf-8")
    except Exception as e:
        total_score += add("reply_file_readable", False, f"Cannot read reply file: {e}")
        reply_text = ""
    else:
        total_score += add("reply_file_exists", True, f"Found at {reply_path}", weight=0.5)

    # ── CHECK 1: Comment A has required Chinese header ─────────────────────
    has_analysis_header = "【AI客诉分析】" in analysis_text
    total_score += add(
        "comment_a_header",
        has_analysis_header,
        f"【AI客诉分析】 header {'found' if has_analysis_header else 'MISSING'} in analysis file"
    )

    # ── CHECK 2: Comment B has required Chinese header ─────────────────────
    has_reply_header = "【对客回复草稿】" in reply_text
    total_score += add(
        "comment_b_header",
        has_reply_header,
        f"【对客回复草稿】 header {'found' if has_reply_header else 'MISSING'} in reply file"
    )

    # ── CHECK 3: Comment B has 【客服发送前检查】 sub-section ──────────────
    has_check_section = "【客服发送前检查】" in reply_text
    total_score += add(
        "reply_pre_send_check_section",
        has_check_section,
        f"【客服发送前检查】 section {'found' if has_check_section else 'MISSING'} in reply file"
    )

    # ── CHECK 4: Platform parsed as Android (not iOS, not ambiguous wrong) ─
    android_pattern = re.compile(r"(android|安卓|Android)", re.IGNORECASE)
    ios_false_positive = re.compile(r"(渠道识别|platform|平台)[^\n]*iOS", re.IGNORECASE)
    has_android = bool(android_pattern.search(analysis_text))
    has_ios_false = bool(ios_false_positive.search(analysis_text))
    platform_ok = has_android and not has_ios_false
    total_score += add(
        "metadata_platform_android",
        platform_ok,
        f"Platform correctly identified as Android: android_found={has_android}, ios_false_positive={has_ios_false}"
    )

    # ── CHECK 5: Vendor parsed as HONOR ────────────────────────────────────
    honor_pattern = re.compile(r"(HONOR|荣耀)", re.IGNORECASE)
    has_honor = bool(honor_pattern.search(analysis_text))
    total_score += add(
        "metadata_vendor_honor",
        has_honor,
        f"Vendor HONOR {'found' if has_honor else 'MISSING'} in analysis (must be parsed from metadata bracket, not guessed)"
    )

    # ── CHECK 6: Correct taxonomy label present ────────────────────────────
    # Should be auto-renew-dispute or renewal-failure (both valid for this case)
    # Checking either in analysis
    taxonomy_pattern = re.compile(
        r"(auto-renew-dispute|renewal-failure|自动续费争议|续费失败)",
        re.IGNORECASE
    )
    has_taxonomy = bool(taxonomy_pattern.search(analysis_text))
    total_score += add(
        "taxonomy_correct",
        has_taxonomy,
        f"Correct v1 taxonomy label (auto-renew-dispute or renewal-failure) "
        f"{'found' if has_taxonomy else 'MISSING'} in analysis"
    )

    # ── CHECK 7: Risk level field populated ───────────────────────────────
    risk_pattern = re.compile(r"风险等级[：:]\s*(低|中|高|升级)", re.IGNORECASE)
    risk_match = risk_pattern.search(analysis_text)
    has_risk = bool(risk_match)
    risk_value = risk_match.group(1) if risk_match else None
    # Given threat of complaint platform report, risk should be 中 or 高
    risk_appropriate = has_risk and risk_value in ["中", "高", "升级"]
    total_score += add(
        "risk_level_populated_and_appropriate",
        risk_appropriate,
        f"Risk level {'=' + risk_value if has_risk else 'MISSING'}; "
        f"expected 中/高/升级 given escalation threat in complaint"
    )

    # ── CHECK 8: SOP missing acknowledgement ──────────────────────────────
    # HONOR SOP is not in workspace; agent must note SOP not loaded
    sop_missing_patterns = [
        re.compile(r"(SOP未加载|SOP not loaded|未找到.*SOP|SOP.*未找到|honor.*sop.*未|缺.*SOP|SOP.*缺)", re.IGNORECASE),
        re.compile(r"(是否命中SOP[：:]\s*(否|待确认))", re.IGNORECASE),
        re.compile(r"(HONOR.*SOP|honor.*sop)", re.IGNORECASE),
    ]
    sop_acknowledged = any(p.search(analysis_text) for p in sop_missing_patterns)
    # Also accept if reply mentions SOP missing
    if not sop_acknowledged:
        sop_acknowledged = any(p.search(reply_text) for p in sop_missing_patterns)
    # Accept 待确认 in SOP field as valid
    sop_field_pattern = re.compile(r"是否命中SOP[：:]\s*(否|待确认)", re.IGNORECASE)
    if not sop_acknowledged:
        sop_acknowledged = bool(sop_field_pattern.search(analysis_text))
    total_score += add(
        "sop_missing_acknowledged",
        sop_acknowledged,
        f"SOP missing/unloaded acknowledgement "
        f"{'found' if sop_acknowledged else 'MISSING — agent should note HONOR SOP not available'}"
    )

    # ── CHECK 9: No false refund promise ──────────────────────────────────
    false_promise_patterns = [
        re.compile(r"(退款.*成功|将为您退款|立即退款|确认退款|保证退款|一定.*退|退款.*保证)", re.IGNORECASE),
        re.compile(r"(refund will be|refund is guaranteed|will refund)", re.IGNORECASE),
    ]
    has_false_promise = any(p.search(reply_text) for p in false_promise_patterns)
    total_score += add(
        "no_false_refund_promise",
        not has_false_promise,
        f"False refund promise {'FOUND — GUARDRAIL VIOLATED' if has_false_promise else 'not found (correct)'}"
    )

    # ── CHECK 10: Reply contains greeting (您好) ──────────────────────────
    has_greeting = "您好" in reply_text
    total_score += add(
        "reply_has_greeting",
        has_greeting,
        f"Reply greeting '您好' {'found' if has_greeting else 'MISSING'}",
        weight=0.5
    )

    # ── CHECK 11: 判断依据 field with ≥1 item ─────────────────────────────
    basis_pattern = re.compile(r"判断依据[：:](.*?)(?=待补充|$)", re.DOTALL)
    basis_match = basis_pattern.search(analysis_text)
    has_basis = False
    if basis_match:
        basis_content = basis_match.group(1)
        # Must have at least one numbered item
        has_basis = bool(re.search(r"\d+[\.\、]", basis_content))
    total_score += add(
        "judgment_basis_populated",
        has_basis,
        f"判断依据 field with numbered items {'found' if has_basis else 'MISSING'} in analysis"
    )

    # ── CHECK 12: 待补充信息 field present ────────────────────────────────
    missing_info_pattern = re.compile(r"待补充信息[：:]", re.IGNORECASE)
    has_missing_info = bool(missing_info_pattern.search(analysis_text))
    total_score += add(
        "missing_info_field_present",
        has_missing_info,
        f"待补充信息 field {'found' if has_missing_info else 'MISSING'} in analysis"
    )

    # ── Final scoring ──────────────────────────────────────────────────────
    # Max possible score = 0.5+0.5+1+1+1+1+1+1+1+1+0.5+1+1 = 11.5, normalize to 10
    max_score = 11.5
    normalized = min(total_score / max_score, 1.0)
    final_passed = (
        normalized >= 0.7
        and checks[2]["passed"]  # analysis header
        and checks[3]["passed"]  # reply header
        and checks[4]["passed"]  # pre-send check
        and checks[8]["passed"]  # no false promise
    )

    return {
        "passed": final_passed,
        "score": round(normalized, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))