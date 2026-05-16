import sys
import json
import re
from pathlib import Path

def load_file(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Check 1: tone-check output file exists ───────────────────────
    tone_files = list(workspace.rglob("tone_check_result.txt"))
    tone_content = None
    if tone_files:
        tone_content = load_file(tone_files[0])

    tone_exists = tone_content is not None
    checks.append({
        "name": "tone_check_output_exists",
        "passed": tone_exists,
        "detail": f"Found tone_check_result.txt at {tone_files[0]}" if tone_exists else "tone_check_result.txt not found anywhere in workspace"
    })
    if tone_exists:
        total_score += 0.15

    # ── Check 2: tone-check output contains tool header ──────────────
    tone_has_header = False
    if tone_content:
        tone_has_header = "公文生成器" in tone_content or "BytesAgain" in tone_content
    checks.append({
        "name": "tone_check_uses_official_tool",
        "passed": tone_has_header,
        "detail": "Tone check output contains official tool header" if tone_has_header else "Tone check output does not appear to be from scripts/official.sh tone subcommand"
    })
    if tone_has_header:
        total_score += 0.10

    # ── Check 3: tone-check detects informal phrases ──────────────────
    tone_detects_issues = False
    if tone_content:
        # The draft has: 我觉得, 差不多, 搞一下, 麻烦, 大概, 感觉, 挺, 咱们, 事儿, 批一批, 看看
        issue_markers = ["问题", "口语化", "不规范", "建议"]
        tone_detects_issues = any(m in tone_content for m in issue_markers)
    checks.append({
        "name": "tone_check_detects_colloquial_issues",
        "passed": tone_detects_issues,
        "detail": "Tone check correctly identified colloquial/informal phrases" if tone_detects_issues else "Tone check did not detect informal language issues in the draft"
    })
    if tone_detects_issues:
        total_score += 0.15

    # ── Check 4: format-check output file exists ─────────────────────
    fmt_files = list(workspace.rglob("format_check_result.txt"))
    fmt_content = None
    if fmt_files:
        fmt_content = load_file(fmt_files[0])

    fmt_exists = fmt_content is not None
    checks.append({
        "name": "format_check_output_exists",
        "passed": fmt_exists,
        "detail": f"Found format_check_result.txt at {fmt_files[0]}" if fmt_exists else "format_check_result.txt not found anywhere in workspace"
    })
    if fmt_exists:
        total_score += 0.15

    # ── Check 5: format-check output contains tool header ────────────
    fmt_has_header = False
    if fmt_content:
        fmt_has_header = "公文生成器" in fmt_content or "BytesAgain" in fmt_content
    checks.append({
        "name": "format_check_uses_official_tool",
        "passed": fmt_has_header,
        "detail": "Format check output contains official tool header" if fmt_has_header else "Format check output does not appear to be from scripts/official.sh format-check subcommand"
    })
    if fmt_has_header:
        total_score += 0.10

    # ── Check 6: format-check identifies problems ────────────────────
    fmt_detects_issues = False
    if fmt_content:
        # draft should fail: no "关于…的请示" title at start, has colloquial phrases
        issue_markers = ["不通过", "不规范", "问题", "口语化", "✗"]
        fmt_detects_issues = any(m in fmt_content for m in issue_markers)
    checks.append({
        "name": "format_check_identifies_problems",
        "passed": fmt_detects_issues,
        "detail": "Format check correctly identified formatting problems in the draft" if fmt_detects_issues else "Format check did not report any formatting issues"
    })
    if fmt_detects_issues:
        total_score += 0.10

    # ── Check 7: 请示 document generated ─────────────────────────────
    request_files = list(workspace.rglob("official_request.txt"))
    req_content = None
    if request_files:
        req_content = load_file(request_files[0])

    req_exists = req_content is not None
    checks.append({
        "name": "official_request_document_exists",
        "passed": req_exists,
        "detail": f"Found official_request.txt at {request_files[0]}" if req_exists else "official_request.txt not found anywhere in workspace"
    })
    if req_exists:
        total_score += 0.05

    # ── Check 8: 请示 uses the tool (has header/structure) ───────────
    req_has_tool_structure = False
    if req_content:
        req_has_tool_structure = (
            ("公文生成器" in req_content or "BytesAgain" in req_content) and
            ("【文种】请示" in req_content or "请示" in req_content)
        )
    checks.append({
        "name": "official_request_uses_request_subcommand",
        "passed": req_has_tool_structure,
        "detail": "官方请示文件由 scripts/official.sh request 子命令生成" if req_has_tool_structure else "The official_request.txt does not appear to be generated by 'scripts/official.sh request' subcommand"
    })
    if req_has_tool_structure:
        total_score += 0.10

    # ── Check 9: 请示 document contains server/procurement content ────
    req_has_content = False
    if req_content:
        # Must reference server/procurement topic from the original draft
        content_markers = ["服务器", "购置", "机房", "采购", "信息化"]
        req_has_content = any(m in req_content for m in content_markers)
    checks.append({
        "name": "official_request_contains_relevant_content",
        "passed": req_has_content,
        "detail": "Official request document references the server procurement topic" if req_has_content else "Official request document does not appear to address the server procurement topic"
    })
    if req_has_content:
        total_score += 0.05

    # ── Check 10: 请示 uses formal title structure ─────────────────────
    req_formal_title = False
    if req_content:
        # official.sh request generates: "关于[SUBJECT]的请示"
        req_formal_title = bool(re.search(r"关于.{2,30}的请示", req_content))
    checks.append({
        "name": "official_request_has_formal_title_structure",
        "passed": req_formal_title,
        "detail": "Official request has 关于…的请示 title structure" if req_formal_title else "Official request document missing the canonical 关于…的请示 title format from the tool"
    })
    if req_formal_title:
        total_score += 0.05

    # ── Check 11: 请示 has formal closing ─────────────────────────────
    req_formal_close = False
    if req_content:
        req_formal_close = "妥否，请批示" in req_content or "以上请示" in req_content
    checks.append({
        "name": "official_request_has_formal_closing",
        "passed": req_formal_close,
        "detail": "Official request has proper 请示 closing phrase" if req_formal_close else "Official request document missing formal closing (妥否，请批示)"
    })
    if req_formal_close:
        total_score += 0.00  # bonus structure check already tested above

    # ── Aggregate ──────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = passed_count >= 8  # must pass 8 of 11 checks

    # Clamp score
    total_score = min(1.0, total_score)

    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))