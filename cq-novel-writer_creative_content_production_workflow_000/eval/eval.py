#!/usr/bin/env python3
"""
Evaluation script for the novel-writer skill task.
Checks that the agent correctly:
1. Created Chapter 3 with proper filename
2. Chapter 3 has 4000-5000 Chinese characters
3. Chapter 3 ends with "（本章完）"
4. Chapter 3 does NOT contain forbidden cultivation terms
5. Chapter 3 uses correct character names (李为东)
6. Updated 故事总纲.md with Chapter 3 summary
7. Appended/updated 小说合并版.txt to include Chapter 3
"""

import sys
import json
import re
from pathlib import Path

def count_chinese_chars(text):
    """Count Chinese characters (CJK Unified Ideographs)."""
    return sum(1 for c in text if '\u4e00' <= c <= '\u9fff')

def run_eval(workspace: str):
    checks = []
    HOME = Path("/root")
    NOVEL_DIR = HOME / ".openclaw" / "workspace" / "novel"
    DESKTOP = HOME / "Desktop"

    # ── Check 1: Chapter 3 file exists with correct naming pattern ──────────
    ch3_candidates = list(NOVEL_DIR.glob("重生78之道门神医-第3章.txt"))
    # Also accept alternate naming like 第三章
    if not ch3_candidates:
        ch3_candidates = list(NOVEL_DIR.glob("*第3章*"))
    if not ch3_candidates:
        ch3_candidates = list(NOVEL_DIR.glob("*第三章*"))

    ch3_exists = len(ch3_candidates) > 0
    checks.append({
        "name": "chapter3_file_exists",
        "passed": ch3_exists,
        "detail": f"Found: {[str(p) for p in ch3_candidates]}" if ch3_exists else "No Chapter 3 file found in novel directory"
    })

    ch3_text = ""
    if ch3_exists:
        try:
            ch3_text = ch3_candidates[0].read_text(encoding="utf-8")
        except Exception as e:
            checks.append({
                "name": "chapter3_readable",
                "passed": False,
                "detail": f"Error reading chapter 3: {e}"
            })

    # ── Check 2: Chinese character count 4000-5000 ──────────────────────────
    if ch3_text:
        cn_count = count_chinese_chars(ch3_text)
        char_count_ok = 4000 <= cn_count <= 5000
        checks.append({
            "name": "chapter3_char_count_4000_5000",
            "passed": char_count_ok,
            "detail": f"Chinese character count: {cn_count} (required: 4000-5000)"
        })
    else:
        checks.append({
            "name": "chapter3_char_count_4000_5000",
            "passed": False,
            "detail": "Chapter 3 text is empty or unreadable"
        })

    # ── Check 3: Ends with "（本章完）" ─────────────────────────────────────
    if ch3_text:
        ends_correctly = "（本章完）" in ch3_text.strip()[-50:]
        checks.append({
            "name": "chapter3_ends_with_banzhanwan",
            "passed": ends_correctly,
            "detail": f"Last 50 chars: {repr(ch3_text.strip()[-50:])}"
        })
    else:
        checks.append({
            "name": "chapter3_ends_with_banzhanwan",
            "passed": False,
            "detail": "Chapter 3 text is empty or unreadable"
        })

    # ── Check 4: No forbidden cultivation/magic terms ────────────────────────
    forbidden_terms = ["灵力", "功法", "丹田", "修仙", "灵气", "修炼", "突破境界", "内力"]
    if ch3_text:
        found_forbidden = [t for t in forbidden_terms if t in ch3_text]
        no_forbidden = len(found_forbidden) == 0
        checks.append({
            "name": "chapter3_no_cultivation_terms",
            "passed": no_forbidden,
            "detail": f"Forbidden terms found: {found_forbidden}" if found_forbidden else "No forbidden cultivation terms found"
        })
    else:
        checks.append({
            "name": "chapter3_no_cultivation_terms",
            "passed": False,
            "detail": "Chapter 3 text is empty or unreadable"
        })

    # ── Check 5: Contains protagonist name 李为东 ────────────────────────────
    if ch3_text:
        has_protagonist = "李为东" in ch3_text
        checks.append({
            "name": "chapter3_has_protagonist_name",
            "passed": has_protagonist,
            "detail": "Found '李为东' in chapter 3" if has_protagonist else "Protagonist '李为东' not found in chapter 3"
        })
    else:
        checks.append({
            "name": "chapter3_has_protagonist_name",
            "passed": False,
            "detail": "Chapter 3 text is empty or unreadable"
        })

    # ── Check 6: 故事总纲.md updated with Chapter 3 summary ─────────────────
    outline_path = NOVEL_DIR / "故事总纲.md"
    try:
        outline_text = outline_path.read_text(encoding="utf-8")
        # Must mention 第三章 or 第3章 in the outline
        has_ch3_in_outline = bool(re.search(r'第三章|第3章', outline_text))
        checks.append({
            "name": "outline_updated_with_chapter3",
            "passed": has_ch3_in_outline,
            "detail": "Chapter 3 summary found in 故事总纲.md" if has_ch3_in_outline else "No mention of Chapter 3 found in 故事总纲.md"
        })
    except Exception as e:
        checks.append({
            "name": "outline_updated_with_chapter3",
            "passed": False,
            "detail": f"Error reading 故事总纲.md: {e}"
        })

    # ── Check 7: 小说合并版.txt updated to include Chapter 3 content ────────
    merged_path = DESKTOP / "小说合并版.txt"
    try:
        merged_text = merged_path.read_text(encoding="utf-8")
        # Must contain Chapter 3 content (check for 本章完 appearing at least 3 times = ch1+ch2+ch3)
        occurrences = merged_text.count("（本章完）")
        # Also check it's longer than before (original had ~2 chapters)
        merged_has_ch3 = occurrences >= 3 or (ch3_text and count_chinese_chars(ch3_text[:100]) > 0 and ch3_text[:100] in merged_text)
        # More robust: check merged has significantly more content than just ch1+ch2
        original_cn_count = 4000  # approximate chars in ch1+ch2
        merged_cn_count = count_chinese_chars(merged_text)
        merged_has_ch3 = merged_cn_count > original_cn_count + 3000  # at least 3000 more chars
        checks.append({
            "name": "merged_file_includes_chapter3",
            "passed": merged_has_ch3,
            "detail": f"Merged file Chinese chars: {merged_cn_count} (original had ~4000, needs >7000 to confirm ch3 added). '（本章完）' occurrences: {occurrences}"
        })
    except Exception as e:
        checks.append({
            "name": "merged_file_includes_chapter3",
            "passed": False,
            "detail": f"Error reading 小说合并版.txt: {e}"
        })

    # ── Check 8: Chapter 3 has a chapter hook/cliffhanger (下章预告 or hook keyword) ──
    if ch3_text:
        # A hook is typically implied by ending content; check for narrative tension words
        hook_patterns = ["下章", "且看", "欲知", "且听", "……", "等着", "不知", "将会", "如何"]
        # Less strict: check the last 500 chars for any of these
        tail = ch3_text[-500:] if len(ch3_text) > 500 else ch3_text
        has_hook = any(p in tail for p in hook_patterns)
        checks.append({
            "name": "chapter3_has_ending_hook",
            "passed": has_hook,
            "detail": f"Hook pattern found in last 500 chars: {[p for p in hook_patterns if p in tail]}" if has_hook else "No hook/cliffhanger detected in chapter ending"
        })
    else:
        checks.append({
            "name": "chapter3_has_ending_hook",
            "passed": False,
            "detail": "Chapter 3 text is empty or unreadable"
        })

    # ── Compute final score ──────────────────────────────────────────────────
    # Critical checks (must-pass): file exists, char count, ends correctly, no forbidden, updated outline, merged file
    critical = ["chapter3_file_exists", "chapter3_char_count_4000_5000",
                "chapter3_ends_with_banzhanwan", "chapter3_no_cultivation_terms",
                "outline_updated_with_chapter3", "merged_file_includes_chapter3"]
    
    check_dict = {c["name"]: c["passed"] for c in checks}
    
    critical_passed = sum(1 for c in critical if check_dict.get(c, False))
    total_passed = sum(1 for c in checks if c["passed"])
    
    score = total_passed / len(checks)
    # Must pass all critical checks to fully pass
    all_critical_ok = all(check_dict.get(c, False) for c in critical)
    passed = all_critical_ok and score >= 0.75

    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/root"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))