import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # --- Find the output file ---
    candidates = list(workspace.rglob("sales_dashboard.js"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "File sales_dashboard.js exists",
        "passed": file_found,
        "detail": f"Found at: {candidates[0]}" if file_found else "File not found anywhere in workspace"
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = candidates[0].read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({
            "name": "File readable",
            "passed": False,
            "detail": str(e)
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    # --- Check 1: Proprietary wrapper start ---
    wrapper_start = bool(re.search(r'javascript:\s*\(function\s*\(\s*\)\s*\{', content))
    checks.append({
        "name": "Proprietary Axure wrapper: starts with javascript:(function(){",
        "passed": wrapper_start,
        "detail": f"Content starts with: {content[:80]!r}" if not wrapper_start else "OK"
    })

    # --- Check 2: backtick template literal for var html ---
    backtick_html = bool(re.search(r'var\s+html\s*=\s*`', content))
    checks.append({
        "name": "Uses backtick template literal: var html=`...`",
        "passed": backtick_html,
        "detail": "var html=`...` pattern found" if backtick_html else "Missing backtick template literal for html variable"
    })

    # --- Check 3: document.write(html) call ---
    doc_write = bool(re.search(r'd\.document\.write\s*\(\s*html\s*\)', content))
    checks.append({
        "name": "Contains d.document.write(html)",
        "passed": doc_write,
        "detail": "OK" if doc_write else "Missing d.document.write(html) — wrong Axure format"
    })

    # --- Check 4: document.close() call ---
    doc_close = bool(re.search(r'd\.document\.close\s*\(\s*\)', content))
    checks.append({
        "name": "Contains d.document.close()",
        "passed": doc_close,
        "detail": "OK" if doc_close else "Missing d.document.close()"
    })

    # --- Check 5: wrapper closes with })(); ---
    wrapper_end = bool(re.search(r'\}\s*\)\s*\(\s*\)\s*;?\s*$', content.strip()))
    checks.append({
        "name": "Wrapper closes with })();",
        "passed": wrapper_end,
        "detail": f"Content ends with: {content.strip()[-40:]!r}" if not wrapper_end else "OK"
    })

    # --- Check 6: ECharts CDN reference ---
    echarts_cdn = bool(re.search(r'echarts', content, re.IGNORECASE))
    echarts_cdn_url = bool(re.search(r'cdn\.jsdelivr\.net.*echarts|unpkg\.com.*echarts|cdnjs.*echarts|echarts\.min\.js', content))
    checks.append({
        "name": "ECharts CDN script included",
        "passed": echarts_cdn and echarts_cdn_url,
        "detail": "ECharts CDN found" if (echarts_cdn and echarts_cdn_url) else f"echarts mention: {echarts_cdn}, CDN URL: {echarts_cdn_url}"
    })

    # --- Check 7: ECharts bar chart (柱状图) ---
    has_bar = bool(re.search(r"type\s*:\s*['\"]bar['\"]", content))
    checks.append({
        "name": "ECharts bar chart (type:'bar') present",
        "passed": has_bar,
        "detail": "OK" if has_bar else "No ECharts bar chart found (type:'bar')"
    })

    # --- Check 8: ECharts line chart (折线图) ---
    has_line = bool(re.search(r"type\s*:\s*['\"]line['\"]", content))
    checks.append({
        "name": "ECharts line chart (type:'line') present",
        "passed": has_line,
        "detail": "OK" if has_line else "No ECharts line chart found (type:'line')"
    })

    # --- Check 9: Chinese text labels ---
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    chinese_matches = chinese_pattern.findall(content)
    has_chinese = len(chinese_matches) >= 20  # At least 20 Chinese characters
    # Check for key required Chinese terms
    has_key_chinese = (
        bool(re.search(r'销售|收入|用户|增长|月', content)) and
        bool(re.search(r'万元|客单价|流失', content))
    )
    checks.append({
        "name": "Chinese labels throughout (20+ Chinese chars, key terms present)",
        "passed": has_chinese and has_key_chinese,
        "detail": f"Found {len(chinese_matches)} Chinese chars. Key terms: {has_key_chinese}" if not (has_chinese and has_key_chinese) else "OK"
    })

    # --- Check 10: Red for positive growth (Chinese convention) ---
    # Look for red color codes near growth/positive indicators
    red_colors = re.findall(r'#[fF][fF][0-9a-fA-F]{4}|#[eE][0-9a-fA-F][0-9a-fA-F]{4}|#[cCdD][0-9a-fA-F]{5}|color:\s*red\b|color:\s*#[fF]', content)
    # More specific: look for typical red hex used for gains
    red_gain_color = bool(re.search(
        r'#ff4d4f|#FF4D4F|#f00|#FF0000|#ff0000|#e74c3c|#E74C3C|#ff3333|#FF3333|#cc0000|#CC0000|#dd0000|#DD0000|color:\s*red',
        content
    ))
    # Also accept any reddish hex near positive indicators
    generic_red = bool(re.search(r'#[fF]{2}[0-9a-fA-F]{4}', content))
    has_red = red_gain_color or generic_red
    checks.append({
        "name": "Red color used for positive/gain indicators (Chinese convention 红涨)",
        "passed": has_red,
        "detail": "Red color found for gains" if has_red else "No red color for gains found — must use 红涨 (red=up) Chinese convention"
    })

    # --- Check 11: Microsoft YaHei font ---
    has_yahei = bool(re.search(r'Microsoft\s+YaHei|微软雅黑', content, re.IGNORECASE))
    checks.append({
        "name": "Microsoft YaHei font specified",
        "passed": has_yahei,
        "detail": "OK" if has_yahei else "Missing 'Microsoft YaHei' font — required per SKILL.md Chinese-localization spec"
    })

    # --- Check 12: Dark theme background ---
    dark_bg = bool(re.search(
        r'#0[aA]1[fF]3[dD]|#0[dD]2137|#1[aA]1[aA]2[eE]|#0[dD]0[dD]0[dD]|#111|#1[0-9a-fA-F]{5}|#0[0-9a-fA-F]{5}|background.*#[01][0-9a-fA-F]{5}',
        content
    ))
    # More liberal: any very dark background
    dark_bg_liberal = bool(re.search(
        r'background(?:-color)?\s*:\s*#[0-1][0-9a-fA-F]{5}|background(?:-color)?\s*:\s*#[0-1][0-9a-fA-F]{2}\b',
        content
    ))
    has_dark = dark_bg or dark_bg_liberal
    checks.append({
        "name": "Dark theme background color present",
        "passed": has_dark,
        "detail": "Dark background color found" if has_dark else "No dark background color found — dashboard should use dark/navy theme"
    })

    # --- Check 13: setOption called (ECharts configured) ---
    has_setoption = len(re.findall(r'setOption\s*\(', content)) >= 2
    checks.append({
        "name": "ECharts setOption called at least twice (bar + line charts)",
        "passed": has_setoption,
        "detail": f"Found {len(re.findall(r'setOption', content))} setOption calls" if not has_setoption else "OK"
    })

    # --- Check 14: window.open() for Axure inline frame ---
    has_window_open = bool(re.search(r'window\.open\s*\(', content))
    checks.append({
        "name": "Uses window.open() for Axure inline frame rendering",
        "passed": has_window_open,
        "detail": "OK" if has_window_open else "Missing window.open() — required for Axure inline frame compatibility"
    })

    # --- Scoring ---
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)

    # Must pass critical checks to pass overall
    critical_checks = [
        "File sales_dashboard.js exists",
        "Proprietary Axure wrapper: starts with javascript:(function(){",
        "Uses backtick template literal: var html=`...`",
        "Contains d.document.write(html)",
        "ECharts bar chart (type:'bar') present",
        "ECharts line chart (type:'line') present",
        "Chinese labels throughout (20+ Chinese chars, key terms present)",
        "Red color used for positive/gain indicators (Chinese convention 红涨)",
        "Microsoft YaHei font specified",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Script error", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))