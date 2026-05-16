import sys
import json
import re
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── Locate the output file ──────────────────────────────────────────
    candidates = list(workspace.rglob("qingshi_2026.docx"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named qingshi_2026.docx: {[str(c) for c in candidates]}"
    })

    if not file_found:
        return checks, 0.0

    target = candidates[0]

    # ── Parse the docx ───────────────────────────────────────────────────
    try:
        from docx import Document
        doc = Document(str(target))
        all_text = "\n".join(p.text for p in doc.paragraphs)
        runs_text = []
        for para in doc.paragraphs:
            for run in para.runs:
                runs_text.append(run.text)
        full_run_text = " ".join(runs_text)
    except Exception as e:
        checks.append({"name": "parse_docx", "passed": False, "detail": f"Failed to parse docx: {e}"})
        return checks, 0.0

    checks.append({"name": "parse_docx", "passed": True, "detail": "Document parsed successfully."})

    # ── Check 1: 发文字号 uses 六角括号〔〕 (NOT [] or 【】) ────────────
    # The raw requirement had "沈大数经[2026]5号" — must be corrected to 〔〕
    has_correct_bracket = '〔2026〕' in all_text or '〔2026〕' in full_run_text
    has_wrong_bracket_square = '[2026]' in all_text
    has_wrong_bracket_corner = '【2026】' in all_text

    checks.append({
        "name": "doc_number_uses_liujiao_brackets",
        "passed": has_correct_bracket and not has_wrong_bracket_square,
        "detail": (
            f"六角括号〔〕present={has_correct_bracket}, "
            f"wrong []={has_wrong_bracket_square}, "
            f"wrong 【】={has_wrong_bracket_corner}. "
            f"Full text snippet: {all_text[:300]}"
        )
    })

    # ── Check 2: 发文字号 序号 not zero-padded (5号 not 05号) ──────────
    # The doc_number should contain "5号" not "05号"
    has_no_zero_pad_number = bool(re.search(r'〔2026〕5号', all_text))
    has_zero_pad = bool(re.search(r'〔2026〕05号', all_text))
    checks.append({
        "name": "doc_number_no_zero_padding",
        "passed": has_no_zero_pad_number and not has_zero_pad,
        "detail": f"'〔2026〕5号' found={has_no_zero_pad_number}, '〔2026〕05号' found={has_zero_pad}"
    })

    # ── Check 3: 成文日期 月/日不编虚位 (8月5日 not 8月05日) ────────────
    # The raw requirement had "2026年8月05日" — must be "2026年8月5日"
    has_correct_date = bool(re.search(r'2026年8月5日', all_text))
    has_wrong_date_zero = bool(re.search(r'2026年8月05日', all_text))
    checks.append({
        "name": "date_no_zero_padding",
        "passed": has_correct_date and not has_wrong_date_zero,
        "detail": f"'2026年8月5日' found={has_correct_date}, '2026年8月05日' found={has_wrong_date_zero}"
    })

    # ── Check 4: 公文类型 is 请示 (ending phrase: 妥否，请批示。) ────────
    has_qingshi_ending = '妥否，请批示' in all_text or '妥否，请批示。' in all_text
    checks.append({
        "name": "qingshi_ending_phrase",
        "passed": has_qingshi_ending,
        "detail": f"'妥否，请批示' present={has_qingshi_ending}"
    })

    # ── Check 5: 标题 contains key elements ──────────────────────────────
    title_correct = '申请2026年度数字经济专项发展资金' in all_text and '请示' in all_text
    checks.append({
        "name": "title_contains_key_elements",
        "passed": title_correct,
        "detail": f"Title elements found: {title_correct}. Text contains '申请2026年度数字经济专项发展资金'={'申请2026年度数字经济专项发展资金' in all_text}"
    })

    # ── Check 6: 主送机关 沈阳市工业和信息化局 ───────────────────────────
    has_recipient = '沈阳市工业和信息化局' in all_text
    checks.append({
        "name": "recipient_present",
        "passed": has_recipient,
        "detail": f"主送机关 '沈阳市工业和信息化局' found={has_recipient}"
    })

    # ── Check 7: 发文机关 沈阳市大东区数字经济发展局 ──────────────────
    has_issuer = '沈阳市大东区数字经济发展局' in all_text
    checks.append({
        "name": "issuer_present",
        "passed": has_issuer,
        "detail": f"发文机关 '沈阳市大东区数字经济发展局' found={has_issuer}"
    })

    # ── Check 8: Structural hierarchy markers present ─────────────────
    # Should have level-1 headers: 一、 二、 三、
    has_l1_markers = all(marker in all_text for marker in ['一、', '二、', '三、'])
    # Should have level-2 headers: （一） （二）
    has_l2_markers = all(marker in all_text for marker in ['（一）', '（二）'])
    struct_ok = has_l1_markers and has_l2_markers
    checks.append({
        "name": "structural_hierarchy_present",
        "passed": struct_ok,
        "detail": (
            f"Level-1 markers (一、二、三、)={has_l1_markers}, "
            f"Level-2 markers (（一）（二）)={has_l2_markers}"
        )
    })

    # ── Check 9: 抄送机关 present ───────────────────────────────────────
    has_copy_to = '沈阳市发展和改革委员会' in all_text or '大东区人民政府' in all_text
    checks.append({
        "name": "copy_to_present",
        "passed": has_copy_to,
        "detail": f"抄送机关 found={has_copy_to}"
    })

    # ── Check 10: 签发人 王建国 ───────────────────────────────────────────
    has_signee = '王建国' in all_text
    checks.append({
        "name": "signee_present",
        "passed": has_signee,
        "detail": f"签发人 '王建国' found={has_signee}"
    })

    # ── Check 11: 附件 mention ────────────────────────────────────────────
    has_attachment = '大东数字经济产业园' in all_text and ('附件' in all_text)
    checks.append({
        "name": "attachment_present",
        "passed": has_attachment,
        "detail": f"附件 mention found={has_attachment}"
    })

    # ── Scoring ──────────────────────────────────────────────────────────
    # Critical checks (must pass): doc_number bracket, date format, ending phrase
    critical_checks = [
        "doc_number_uses_liujiao_brackets",
        "doc_number_no_zero_padding",
        "date_no_zero_padding",
        "qingshi_ending_phrase",
    ]
    # Normal checks
    normal_checks = [
        "output_file_exists",
        "parse_docx",
        "title_contains_key_elements",
        "recipient_present",
        "issuer_present",
        "structural_hierarchy_present",
        "copy_to_present",
        "signee_present",
        "attachment_present",
    ]

    passed_checks = {c["name"]: c["passed"] for c in checks}

    critical_score = sum(passed_checks.get(c, False) for c in critical_checks) / len(critical_checks)
    normal_score = sum(passed_checks.get(c, False) for c in normal_checks) / len(normal_checks)

    # Critical checks are weighted 60%, normal 40%
    total_score = 0.6 * critical_score + 0.4 * normal_score

    return checks, round(total_score, 3)


def main():
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_checks(workspace_dir)
    except Exception as e:
        checks = [{"name": "fatal_error", "passed": False, "detail": str(e)}]
        score = 0.0

    passed = score >= 0.7

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()