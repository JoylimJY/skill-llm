import sys
import os
import re
import json
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def evaluate(workspace):
    checks = []

    # --- Find the output file ---
    candidates = list(Path(workspace).rglob("chengdu_recommendations.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "chengdu_recommendations.md not found anywhere in workspace"}]
        }

    report_path = candidates[0]
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    # --- Check 1: File exists ---
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {report_path}"})

    # --- Check 2: Main title contains 成都 and 景点推荐 ---
    def check_title():
        pattern = r'#\s*成都.{0,10}景点推荐'
        match = re.search(pattern, content)
        if match:
            return True, f"Found title: {match.group()}"
        return False, f"No title matching '# 成都...景点推荐' found in content"
    checks.append(run_check("has_chengdu_title", check_title))

    # --- Check 3: Has fly.ai attribution (at least once) ---
    def check_flyai_attribution():
        if "fly.ai" in content and "实时结果" in content:
            return True, "Found 'fly.ai 实时结果' attribution"
        return False, "Missing 'fly.ai 实时结果' brand attribution"
    checks.append(run_check("has_flyai_attribution", check_flyai_attribution))

    # --- Check 4: Has summary line with correct format ---
    def check_summary_line():
        pattern = r'共推荐\s*\*\*\d+\*\*\s*个景点，其中5A级\s*\*\*\d+\*\*\s*个，热门好评\s*\*\*\d+\*\*\s*个'
        match = re.search(pattern, content)
        if match:
            return True, f"Found summary line: {match.group()}"
        return False, "Missing required summary line: '共推荐 **N** 个景点，其中5A级 **N** 个，热门好评 **N** 个'"
    checks.append(run_check("has_summary_line", check_summary_line))

    # --- Check 5: Has 5A景区 section header ---
    def check_5a_section():
        if re.search(r'##\s*5A级景区', content):
            return True, "Found '## 5A级景区' section"
        return False, "Missing '## 5A级景区' section header"
    checks.append(run_check("has_5a_section", check_5a_section))

    # --- Check 6: Has 热门好评推荐 section header ---
    def check_hot_section():
        if re.search(r'##\s*热门好评推荐', content):
            return True, "Found '## 热门好评推荐' section"
        return False, "Missing '## 热门好评推荐' section header"
    checks.append(run_check("has_hot_section", check_hot_section))

    # --- Check 7: At least 5 attraction cards (numbered headings) ---
    def check_attraction_count():
        # Look for ### N. pattern
        attractions = re.findall(r'###\s*\d+\.\s*.+', content)
        count = len(attractions)
        if count >= 5:
            return True, f"Found {count} attraction cards (>= 5 required)"
        return False, f"Only {count} attraction card(s) found, need at least 5"
    checks.append(run_check("min_five_attractions", check_attraction_count))

    # --- Check 8: 5A label in attraction headings ---
    def check_5a_label():
        pattern = r'###\s*\d+\.\s*.+\(5A\)'
        matches = re.findall(pattern, content)
        if len(matches) >= 1:
            return True, f"Found {len(matches)} attraction(s) labeled with (5A)"
        return False, "No attraction headings contain '(5A)' label"
    checks.append(run_check("has_5a_label_in_headings", check_5a_label))

    # --- Check 9: Ticket integration - check for proper ticket formats ---
    def check_ticket_format():
        # Should contain at least one of the valid ticket format strings
        valid_formats = [
            "免费开放",
            "收费（",
            "价格请以景区为准",
        ]
        found = []
        for fmt in valid_formats:
            if fmt in content:
                found.append(fmt)
        if found:
            return True, f"Found valid ticket formats: {found}"
        return False, "No valid ticket integration formats found (expected '免费开放', '收费（...）', or '价格请以景区为准')"
    checks.append(run_check("ticket_integration_format", check_ticket_format))

    # --- Check 10: Has image markdown syntax ---
    def check_image_syntax():
        matches = re.findall(r'!\[\]\(https?://[^\)]+\)', content)
        if len(matches) >= 1:
            return True, f"Found {len(matches)} image(s) with proper markdown syntax"
        return False, "No images found with '![](url)' syntax"
    checks.append(run_check("has_image_syntax", check_image_syntax))

    # --- Check 11: Has booking links ---
    def check_booking_links():
        matches = re.findall(r'\[点击预订\]\(https?://[^\)]+\)', content)
        if len(matches) >= 1:
            return True, f"Found {len(matches)} booking link(s) with '点击预订'"
        return False, "No booking links '点击预订' found"
    checks.append(run_check("has_booking_links", check_booking_links))

    # --- Check 12: Has required structured fields per card ---
    def check_structured_fields():
        required_fields = ["**类别**", "**地址**", "**门票**", "**游玩时长**", "**交通指南**"]
        missing = []
        for field in required_fields:
            if field not in content:
                missing.append(field)
        if not missing:
            return True, f"All required structured fields present"
        return False, f"Missing structured fields: {missing}"
    checks.append(run_check("has_structured_fields", check_structured_fields))

    # --- Check 13: Has timestamp pattern ---
    def check_timestamp():
        # Looking for a timestamp in the content
        ts_pattern = r'\d{4}-\d{2}-\d{2}'
        if re.search(ts_pattern, content):
            return True, "Found date/timestamp in content"
        return False, "No timestamp found in content"
    checks.append(run_check("has_timestamp", check_timestamp))

    # --- Check 14: Verify 5A section comes before 热门好评 section ---
    def check_section_order():
        pos_5a = content.find("## 5A级景区")
        pos_hot = content.find("## 热门好评推荐")
        if pos_5a == -1 or pos_hot == -1:
            return False, "One or both sections missing, cannot verify order"
        if pos_5a < pos_hot:
            return True, f"5A section (pos {pos_5a}) correctly appears before 热门好评 section (pos {pos_hot})"
        return False, f"Section order wrong: 5A (pos {pos_5a}) should appear before 热门好评 (pos {pos_hot})"
    checks.append(run_check("correct_section_order", check_section_order))

    # --- Check 15: Footer attribution (second occurrence at bottom) ---
    def check_footer_attribution():
        occurrences = content.count("基于 fly.ai 实时结果")
        if occurrences >= 2:
            return True, f"Found {occurrences} occurrences of attribution (header + footer)"
        elif occurrences == 1:
            return False, f"Only 1 occurrence of 'fly.ai 实时结果' found; expected at both top and bottom"
        return False, "No 'fly.ai 实时结果' attribution found"
    checks.append(run_check("has_header_and_footer_attribution", check_footer_attribution))

    # --- Check 16: Content is substantial (not just a skeleton) ---
    def check_content_length():
        if len(content) >= 1000:
            return True, f"Content length {len(content)} chars is substantial"
        return False, f"Content length {len(content)} chars is too short (< 1000), likely incomplete"
    checks.append(run_check("content_is_substantial", check_content_length))

    # --- Check 17: Does NOT use old deprecated format ---
    def check_no_old_format():
        # Old format would be "1. Name | Address | Level" style
        if re.search(r'\d+\.\s+\S+\s*\|\s*\S+\s*\|\s*(5A|4A)', content):
            return False, "Content uses deprecated pipe-separated format from old instructions"
        return True, "No deprecated format detected"
    checks.append(run_check("no_deprecated_format", check_no_old_format))

    # --- Compute score ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total

    # Must pass critical checks to be considered overall passed
    critical_checks = [
        "file_exists",
        "has_chengdu_title",
        "has_5a_section",
        "has_hot_section",
        "min_five_attractions",
        "has_structured_fields",
        "ticket_integration_format",
    ]
    critical_results = {c["name"]: c["passed"] for c in checks}
    all_critical_passed = all(critical_results.get(cn, False) for cn in critical_checks)

    overall_passed = all_critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))