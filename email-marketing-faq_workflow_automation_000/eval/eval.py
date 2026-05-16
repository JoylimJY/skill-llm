import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── 1. 邮件内容.html EXISTS ───────────────────────────────────────────────────
try:
    # Search broadly — agent might put it in Desktop or workspace root
    candidates = list(workspace.rglob("邮件内容.html"))
    if candidates:
        html_path = candidates[0]
        html_content = html_path.read_text(encoding="utf-8")
        total_score += add_check(
            "邮件内容.html exists",
            True,
            f"Found at {html_path.relative_to(workspace)} ({len(html_content)} chars)"
        )
    else:
        html_content = ""
        total_score += add_check("邮件内容.html exists", False, "File not found anywhere in workspace")
except Exception as e:
    html_content = ""
    total_score += add_check("邮件内容.html exists", False, f"Error: {e}")

# ── 2. HTML is valid (has <html>, <body>, <head> tags) ───────────────────────
try:
    has_html = bool(re.search(r'<html[\s>]', html_content, re.IGNORECASE))
    has_head = bool(re.search(r'<head[\s>]', html_content, re.IGNORECASE))
    has_body = bool(re.search(r'<body[\s>]', html_content, re.IGNORECASE))
    valid_html = has_html and has_head and has_body
    total_score += add_check(
        "HTML has proper structure (html/head/body)",
        valid_html,
        f"<html>:{has_html}, <head>:{has_head}, <body>:{has_body}"
    )
except Exception as e:
    total_score += add_check("HTML has proper structure", False, f"Error: {e}")

# ── 3. Responsive viewport meta tag ──────────────────────────────────────────
try:
    has_viewport = bool(re.search(r'viewport', html_content, re.IGNORECASE))
    total_score += add_check(
        "HTML has responsive viewport meta tag",
        has_viewport,
        "viewport meta tag present" if has_viewport else "Missing viewport meta tag (required for mobile-friendly email)"
    )
except Exception as e:
    total_score += add_check("HTML responsive viewport", False, f"Error: {e}")

# ── 4. 【kol name】 placeholder preserved EXACTLY ────────────────────────────
try:
    has_kol_name = "【kol name】" in html_content
    total_score += add_check(
        "【kol name】 placeholder preserved in HTML",
        has_kol_name,
        "Found 【kol name】" if has_kol_name else "Missing 【kol name】 — placeholder was NOT preserved (must use 【】 brackets, not {{}} or other formats)"
    )
except Exception as e:
    total_score += add_check("【kol name】 placeholder", False, f"Error: {e}")

# ── 5. 【gender】 placeholder preserved EXACTLY ──────────────────────────────
try:
    has_gender = "【gender】" in html_content
    total_score += add_check(
        "【gender】 placeholder preserved in HTML",
        has_gender,
        "Found 【gender】" if has_gender else "Missing 【gender】 — placeholder must use 【】 bracket format exactly"
    )
except Exception as e:
    total_score += add_check("【gender】 placeholder", False, f"Error: {e}")

# ── 6. Core product content preserved (not garbled/truncated) ────────────────
try:
    core_phrases = ["DataViz Pro", "【kol name】", "数据分析", "合作"]
    found = [p for p in core_phrases if p in html_content]
    content_ok = len(found) >= 3
    total_score += add_check(
        "Core content from 邮件文案.txt preserved in HTML",
        content_ok,
        f"Found {len(found)}/{len(core_phrases)} core phrases: {found}"
    )
except Exception as e:
    total_score += add_check("Core content preserved", False, f"Error: {e}")

# ── 7. faq.txt EXISTS with correct Q:/A: format ──────────────────────────────
try:
    faq_candidates = list(workspace.rglob("faq.txt"))
    # Exclude old distractor
    faq_candidates = [f for f in faq_candidates if "archive" not in str(f) and "old" not in str(f)]
    if faq_candidates:
        faq_path = faq_candidates[0]
        faq_content = faq_path.read_text(encoding="utf-8")
        total_score += add_check(
            "faq.txt exists (non-archive)",
            True,
            f"Found at {faq_path.relative_to(workspace)} ({len(faq_content)} chars)"
        )
    else:
        faq_content = ""
        total_score += add_check("faq.txt exists", False, "faq.txt not found (needed for auto-reply system)")
except Exception as e:
    faq_content = ""
    total_score += add_check("faq.txt exists", False, f"Error: {e}")

# ── 8. faq.txt uses correct Q:/A: format (not "Question:"/"Answer:" etc.) ────
try:
    q_lines = [l for l in faq_content.splitlines() if l.strip().startswith("Q:")]
    a_lines = [l for l in faq_content.splitlines() if l.strip().startswith("A:")]
    correct_format = len(q_lines) >= 4 and len(a_lines) >= 4
    # Also ensure it's NOT using wrong format from archive
    wrong_format = "Question:" in faq_content or "问题：" in faq_content.replace(" ", "")
    format_ok = correct_format and not wrong_format
    total_score += add_check(
        "faq.txt uses correct Q:/A: format with ≥4 entries",
        format_ok,
        f"Q: lines={len(q_lines)}, A: lines={len(a_lines)}, wrong_format_detected={wrong_format}. Must use 'Q:' and 'A:' prefix (not 'Question:' or other variants)"
    )
except Exception as e:
    total_score += add_check("faq.txt format", False, f"Error: {e}")

# ── 9. faq.txt contains substantive content from raw_faq_data.txt ─────────────
try:
    faq_topics = ["价格", "合作", "试用", "安全"]
    found_topics = [t for t in faq_topics if t in faq_content]
    topics_ok = len(found_topics) >= 3
    # Verify refund was excluded (raw_faq explicitly says NOT to include it)
    refund_excluded = "退款" not in faq_content
    content_ok = topics_ok and refund_excluded
    total_score += add_check(
        "faq.txt contains key topics and excludes non-FAQ items (退款)",
        content_ok,
        f"Topics found: {found_topics}/{faq_topics}, refund_excluded={refund_excluded}. The raw FAQ explicitly said not to include refund policy."
    )
except Exception as e:
    total_score += add_check("faq.txt content quality", False, f"Error: {e}")

# ── 10. check_replies.py runs successfully ────────────────────────────────────
import subprocess
try:
    result = subprocess.run(
        ["python3", "email-marketing/scripts/check_replies.py"],
        capture_output=True, text=True, cwd=str(workspace), timeout=30
    )
    output = result.stdout
    ran_ok = result.returncode == 0 and "邮件营销综合效果报告" in output
    total_score += add_check(
        "check_replies.py runs and produces report",
        ran_ok,
        f"returncode={result.returncode}, output_preview={output[:200].replace(chr(10),' ')}"
    )
except Exception as e:
    output = ""
    total_score += add_check("check_replies.py runs", False, f"Exception: {e}")

# ── 11. check_replies.py report shows correct statistics ────────────────────
try:
    # total_sent=80, bounced=2, replied=0 (from assets)
    has_total = "80" in output
    has_bounce = "2" in output
    has_rate = "%" in output
    has_faq_status = "faq.txt" in output
    stats_ok = has_total and has_bounce and has_rate and has_faq_status
    total_score += add_check(
        "Report shows correct stats (80 sent, 2 bounced, % rates, faq status)",
        stats_ok,
        f"total_80={has_total}, bounce_2={has_bounce}, has_%={has_rate}, faq_status={has_faq_status}"
    )
except Exception as e:
    total_score += add_check("Report correctness", False, f"Error: {e}")

# ── 12. auto_reply_manager.py runs with faq.txt ──────────────────────────────
try:
    result2 = subprocess.run(
        ["python3", "email-marketing/scripts/auto_reply_manager.py"],
        capture_output=True, text=True, cwd=str(workspace), timeout=30
    )
    out2 = result2.stdout
    ran2_ok = result2.returncode == 0 and "扫描到" in out2 and "封未读邮件" in out2
    total_score += add_check(
        "auto_reply_manager.py scans inbox and applies FAQ matching",
        ran2_ok,
        f"returncode={result2.returncode}, output={out2[:200].replace(chr(10),' ')}"
    )
except Exception as e:
    total_score += add_check("auto_reply_manager.py", False, f"Exception: {e}")

# ── Compute final score ───────────────────────────────────────────────────────
num_checks = len(checks)
score = total_score / num_checks if num_checks > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": round(score, 4),
    "checks": checks
}, ensure_ascii=False, indent=2))