#!/usr/bin/env python3
"""
Evaluation script for the Chinese copywriting rewrite task.
Usage: python eval_script.py <workspace_dir>

Looks for a file named 'release-notes-revised.md' anywhere in the workspace.
Checks:
1. File exists and is non-empty.
2. Proper noun casing: iOS (not "ios" or "IOS"), GitHub (not "github"), WiFi (not "wifi"), App Store (not "app store"), JavaScript (not "javascript").
3. Spacing: spaces between Chinese and English/numbers in key phrases.
4. Punctuation: fullwidth comma/period in Chinese sentences, fullwidth parentheses, Chinese ellipsis.
5. No duplicate exclamation/question marks.
6. Output format: contains "Revised", "Changes" sections.
7. Changes are grouped by rule category (spacing / punctuation / proper nouns, etc.).
"""

import sys
import json
import re
import pathlib

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_str):
    workspace = pathlib.Path(workspace_str)
    checks = []
    
    # ── Find output file ──────────────────────────────────────────────────────
    candidates = list(workspace.rglob("release-notes-revised.md"))
    if not candidates:
        checks.append(check("output_file_exists", False, "No file named 'release-notes-revised.md' found in workspace."))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    output_file = candidates[0]
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("output_file_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append(check("output_file_exists", True, f"Found at {output_file.relative_to(workspace)}"))
    
    # ── Check output format sections ─────────────────────────────────────────
    has_revised = bool(re.search(r'(?i)revised', content))
    has_changes = bool(re.search(r'(?i)changes', content))
    checks.append(check(
        "output_format_revised_section",
        has_revised,
        "'Revised' section found." if has_revised else "Missing 'Revised' section in output."
    ))
    checks.append(check(
        "output_format_changes_section",
        has_changes,
        "'Changes' section found." if has_changes else "Missing 'Changes' section in output."
    ))
    
    # ── Extract the revised text block (everything after "Revised" header) ───
    # Try to isolate the revised Markdown content for detailed checks
    revised_match = re.search(r'(?i)#*\s*revised[:\s]*\n+(.*?)(?=\n#*\s*(changes|notes)\b|$)', content, re.DOTALL)
    revised_text = revised_match.group(1) if revised_match else content
    
    # ── PROPER NOUN CHECKS ───────────────────────────────────────────────────
    
    # iOS: must NOT appear as "ios" or "IOS" (case-sensitive: standalone token)
    bad_ios = bool(re.search(r'\bios\b', revised_text, re.IGNORECASE) and 
                   not re.search(r'\biOS\b', revised_text))
    # More precise: look for wrong forms
    has_wrong_ios = bool(re.search(r'\b(?:IOS|ios)\b', revised_text))
    has_correct_ios = bool(re.search(r'\biOS\b', revised_text))
    ios_ok = has_correct_ios and not has_wrong_ios
    checks.append(check(
        "proper_noun_iOS",
        ios_ok,
        f"iOS casing correct: {has_correct_ios}, wrong forms (IOS/ios) absent: {not has_wrong_ios}"
    ))
    
    # GitHub: must NOT appear as "github" (case insensitive wrong forms)
    has_wrong_github = bool(re.search(r'\bgithub\b', revised_text, re.IGNORECASE) and 
                            not re.search(r'\bGitHub\b', revised_text))
    has_correct_github = bool(re.search(r'\bGitHub\b', revised_text))
    github_ok = has_correct_github and not bool(re.search(r'\b(?:github|GITHUB|Github)\b', revised_text))
    checks.append(check(
        "proper_noun_GitHub",
        github_ok,
        f"GitHub casing correct: {has_correct_github}, wrong forms absent: {not bool(re.search(r'(?:github|GITHUB|Github)', revised_text))}"
    ))
    
    # WiFi: must NOT appear as "wifi" or "WIFI"
    has_correct_wifi = bool(re.search(r'\bWiFi\b', revised_text))
    has_wrong_wifi = bool(re.search(r'\b(?:wifi|WIFI|Wifi)\b', revised_text))
    wifi_ok = has_correct_wifi and not has_wrong_wifi
    checks.append(check(
        "proper_noun_WiFi",
        wifi_ok,
        f"WiFi correct: {has_correct_wifi}, wrong forms absent: {not has_wrong_wifi}"
    ))
    
    # App Store: must NOT appear as "app store" (all lowercase)
    has_correct_appstore = bool(re.search(r'\bApp Store\b', revised_text))
    has_wrong_appstore = bool(re.search(r'\bapp store\b', revised_text, re.IGNORECASE) and not has_correct_appstore)
    appstore_ok = has_correct_appstore and not bool(re.search(r'\b(?:app store|APP STORE)\b', revised_text))
    checks.append(check(
        "proper_noun_App_Store",
        appstore_ok,
        f"App Store correct: {has_correct_appstore}, wrong forms absent: {not bool(re.search(r'(?:app store|APP STORE)', revised_text))}"
    ))
    
    # JavaScript: must NOT appear as "javascript"
    has_correct_js = bool(re.search(r'\bJavaScript\b', revised_text))
    has_wrong_js = bool(re.search(r'\b(?:javascript|Javascript|JAVASCRIPT)\b', revised_text))
    js_ok = has_correct_js and not has_wrong_js
    checks.append(check(
        "proper_noun_JavaScript",
        js_ok,
        f"JavaScript correct: {has_correct_js}, wrong forms absent: {not has_wrong_js}"
    ))
    
    # ── SPACING CHECKS ───────────────────────────────────────────────────────
    
    # Rule: space between Chinese characters and Latin letters/digits
    # Check that "ios版本" style (no space) is gone → "iOS 版本" style present
    # We check for a few key phrases that should now have spaces
    
    # "iOS" followed by Chinese without space should NOT exist
    no_space_ios_cn = bool(re.search(r'iOS[\u4e00-\u9fff]', revised_text))
    checks.append(check(
        "spacing_ios_before_chinese",
        not no_space_ios_cn,
        "No missing space between 'iOS' and following Chinese character." if not no_space_ios_cn
        else "Found 'iOS' directly touching Chinese character (missing space)."
    ))
    
    # Chinese character directly followed by "GitHub" without space should NOT exist
    no_space_cn_github = bool(re.search(r'[\u4e00-\u9fff]GitHub', revised_text))
    checks.append(check(
        "spacing_chinese_before_GitHub",
        not no_space_cn_github,
        "No missing space between Chinese and 'GitHub'." if not no_space_cn_github
        else "Found Chinese character directly touching 'GitHub' (missing space)."
    ))
    
    # "200ms" without space should be fixed (number + English unit needs space)
    # Check that "200ms" (no space) is gone
    bad_200ms = bool(re.search(r'200ms', revised_text, re.IGNORECASE))
    checks.append(check(
        "spacing_number_unit_ms",
        not bad_200ms,
        "No unspaced '200ms' found." if not bad_200ms
        else "Found '200ms' without space between number and unit."
    ))
    
    # "800ms" same
    bad_800ms = bool(re.search(r'800ms', revised_text, re.IGNORECASE))
    checks.append(check(
        "spacing_number_unit_800ms",
        not bad_800ms,
        "No unspaced '800ms' found." if not bad_800ms
        else "Found '800ms' without space between number and unit."
    ))
    
    # Check "500MB" without space
    bad_500mb = bool(re.search(r'500MB', revised_text, re.IGNORECASE))
    checks.append(check(
        "spacing_number_unit_MB",
        not bad_500mb,
        "No unspaced '500MB' found." if not bad_500mb
        else "Found '500MB' without space between number and unit."
    ))
    
    # ── PUNCTUATION CHECKS ───────────────────────────────────────────────────
    
    # Fullwidth comma should be used in Chinese sentences (not halfwidth comma)
    # The original had "缩短至200ms,提升了" — the comma in Chinese context should be fullwidth ，
    # Check: halfwidth comma between Chinese characters should be gone
    bad_halfwidth_comma_cn = bool(re.search(r'[\u4e00-\u9fff],[^\s]', revised_text))
    checks.append(check(
        "punctuation_fullwidth_comma_in_chinese",
        not bad_halfwidth_comma_cn,
        "No halfwidth comma directly after Chinese character." if not bad_halfwidth_comma_cn
        else "Found halfwidth comma ',' after Chinese character (should be fullwidth '，')."
    ))
    
    # Halfwidth period at end of Chinese sentence should be fixed
    # Original: "感谢您的支持." → should be "感谢您的支持。"
    bad_halfwidth_period = bool(re.search(r'[\u4e00-\u9fff]\.', revised_text))
    checks.append(check(
        "punctuation_fullwidth_period_in_chinese",
        not bad_halfwidth_period,
        "No halfwidth period after Chinese character." if not bad_halfwidth_period
        else "Found halfwidth period '.' after Chinese character (should be fullwidth '。')."
    ))
    
    # Halfwidth parentheses in Chinese context should be fullwidth
    # Original: "(仅限付费用户)" → "（仅限付费用户）"
    bad_halfwidth_paren = bool(re.search(r'\([\u4e00-\u9fff]', revised_text))
    checks.append(check(
        "punctuation_fullwidth_parentheses",
        not bad_halfwidth_paren,
        "No halfwidth opening paren before Chinese character." if not bad_halfwidth_paren
        else "Found halfwidth '(' before Chinese character (should be fullwidth '（')."
    ))
    
    # Western ellipsis "..." should be replaced with Chinese ellipsis "……"
    bad_western_ellipsis = bool(re.search(r'\.{3}', revised_text))
    has_chinese_ellipsis = bool(re.search(r'……', revised_text))
    checks.append(check(
        "punctuation_chinese_ellipsis",
        not bad_western_ellipsis and has_chinese_ellipsis,
        f"Western ellipsis '...' absent: {not bad_western_ellipsis}, Chinese ellipsis '……' present: {has_chinese_ellipsis}"
    ))
    
    # Duplicate punctuation "!!" should be gone
    bad_double_exclaim = bool(re.search(r'!!|！！', revised_text))
    checks.append(check(
        "punctuation_no_duplicate_exclamation",
        not bad_double_exclaim,
        "No duplicate exclamation marks." if not bad_double_exclaim
        else "Found duplicate exclamation marks '!!' or '！！'."
    ))
    
    # ── CHANGES SECTION: grouped by rule category ────────────────────────────
    changes_match = re.search(r'(?i)#*\s*changes[:\s]*\n+(.*?)(?=\n#*\s*notes\b|$)', content, re.DOTALL)
    changes_text = changes_match.group(1) if changes_match else ""
    
    # Check that at least 2 distinct rule categories are mentioned in Changes
    spacing_mentioned = bool(re.search(r'(?i)spac|间距|空格', changes_text))
    punct_mentioned = bool(re.search(r'(?i)punct|标点|符号', changes_text))
    proper_noun_mentioned = bool(re.search(r'(?i)proper.noun|专有名词|大小写|casing', changes_text))
    categories_count = sum([spacing_mentioned, punct_mentioned, proper_noun_mentioned])
    checks.append(check(
        "changes_grouped_by_category",
        categories_count >= 2,
        f"Found {categories_count}/3 expected rule categories in Changes section "
        f"(spacing: {spacing_mentioned}, punctuation: {punct_mentioned}, proper nouns: {proper_noun_mentioned})."
    ))
    
    # ── Final scoring ────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    passed = score >= 0.80  # must pass at least 80% of checks
    
    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided."}
        ]}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))