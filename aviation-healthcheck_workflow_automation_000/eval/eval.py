import sys
import json
import re
import subprocess
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Find the report file ──────────────────────────────────────────────────
    report_files = list(workspace.rglob("aviation_healthcheck_report.txt"))
    
    file_found = len(report_files) > 0
    checks.append({
        "name": "report_file_exists",
        "passed": file_found,
        "detail": f"Found {len(report_files)} file(s) named aviation_healthcheck_report.txt" if file_found else "No file named aviation_healthcheck_report.txt found anywhere in workspace"
    })
    
    if not file_found:
        return checks, 0.0

    report_path = report_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return checks, 0.0

    checks.append({"name": "file_readable", "passed": True, "detail": f"File read successfully ({len(content)} chars)"})

    # ── Check 1: Unicode box-drawing border (═══) ─────────────────────────────
    has_unicode_border = '═══' in content
    checks.append({
        "name": "unicode_box_border",
        "passed": has_unicode_border,
        "detail": "Found ═══ Unicode box-drawing characters" if has_unicode_border else "Missing ═══ Unicode box-drawing borders (ASCII === is NOT acceptable)"
    })
    if has_unicode_border:
        total_score += 0.10

    # ── Check 2: Report title with airplane emoji ─────────────────────────────
    has_title = '✈️' in content and '航空维修健康检查报告' in content
    checks.append({
        "name": "report_title",
        "passed": has_title,
        "detail": "Found ✈️ emoji and 航空维修健康检查报告 in title" if has_title else "Missing ✈️ emoji or 航空维修健康检查报告 title"
    })
    if has_title:
        total_score += 0.10

    # ── Check 3: Date/time field with 📅 emoji ────────────────────────────────
    has_datetime = '📅' in content and ('检查时间' in content)
    # Also check that there's an actual date-like string
    date_pattern = re.search(r'📅.*?检查时间.*?(\d{4}-\d{2}-\d{2})', content, re.DOTALL)
    checks.append({
        "name": "datetime_field",
        "passed": has_datetime and date_pattern is not None,
        "detail": "Found 📅 检查时间 with date" if (has_datetime and date_pattern) else "Missing 📅 检查时间: YYYY-MM-DD HH:mm field"
    })
    if has_datetime and date_pattern:
        total_score += 0.08

    # ── Check 4: Chinese section headers with 【】 brackets ───────────────────
    has_avinfo_section = '【航空资讯更新】' in content
    has_sysstate_section = '【系统状态】' in content
    has_recommend_section = '【建议事项】' in content
    all_sections = has_avinfo_section and has_sysstate_section and has_recommend_section
    checks.append({
        "name": "chinese_section_headers",
        "passed": all_sections,
        "detail": f"Sections found: 【航空资讯更新】={has_avinfo_section}, 【系统状态】={has_sysstate_section}, 【建议事项】={has_recommend_section}"
    })
    if all_sections:
        total_score += 0.10

    # ── Check 5: FAA AD count line ────────────────────────────────────────────
    faa_pattern = re.search(r'✓\s*FAA AD:\s*(\d+)\s*条新指令', content)
    has_faa = faa_pattern is not None
    checks.append({
        "name": "faa_ad_line",
        "passed": has_faa,
        "detail": f"Found FAA AD line: {faa_pattern.group(0)}" if has_faa else "Missing '✓ FAA AD: X 条新指令' line"
    })
    if has_faa:
        total_score += 0.08

    # ── Check 6: EASA AD count line ───────────────────────────────────────────
    easa_pattern = re.search(r'✓\s*EASA AD:\s*(\d+)\s*条新指令', content)
    has_easa = easa_pattern is not None
    checks.append({
        "name": "easa_ad_line",
        "passed": has_easa,
        "detail": f"Found EASA AD line: {easa_pattern.group(0)}" if has_easa else "Missing '✓ EASA AD: X 条新指令' line"
    })
    if has_easa:
        total_score += 0.08

    # ── Check 7: CAAC count line ──────────────────────────────────────────────
    caac_pattern = re.search(r'✓\s*CAAC:\s*(\d+)\s*条新指令', content)
    has_caac = caac_pattern is not None
    checks.append({
        "name": "caac_ad_line",
        "passed": has_caac,
        "detail": f"Found CAAC AD line: {caac_pattern.group(0)}" if has_caac else "Missing '✓ CAAC: X 条新指令' line"
    })
    if has_caac:
        total_score += 0.08

    # ── Check 8: Industry news count line ────────────────────────────────────
    news_pattern = re.search(r'✓\s*行业新闻:\s*(\d+)\s*条更新', content)
    has_news = news_pattern is not None
    checks.append({
        "name": "industry_news_line",
        "passed": has_news,
        "detail": f"Found 行业新闻 line: {news_pattern.group(0)}" if has_news else "Missing '✓ 行业新闻: X 条更新' line"
    })
    if has_news:
        total_score += 0.05

    # ── Check 9: OpenClaw status line ─────────────────────────────────────────
    # Must show 运行中 (running) based on mock openclaw output
    openclaw_running = re.search(r'✓\s*OpenClaw:\s*运行中', content)
    checks.append({
        "name": "openclaw_status_running",
        "passed": openclaw_running is not None,
        "detail": "Found '✓ OpenClaw: 运行中'" if openclaw_running else "Missing '✓ OpenClaw: 运行中' - agent must have called openclaw status or health --json"
    })
    if openclaw_running:
        total_score += 0.10

    # ── Check 10: Disk space as percentage available (XX% 可用) ───────────────
    disk_pattern = re.search(r'✓\s*磁盘空间:\s*(\d+)%\s*可用', content)
    has_disk = disk_pattern is not None
    checks.append({
        "name": "disk_space_available_pct",
        "passed": has_disk,
        "detail": f"Found disk space line: {disk_pattern.group(0)}" if has_disk else "Missing '✓ 磁盘空间: XX% 可用' - agent must call df -h and compute available %"
    })
    if has_disk:
        # Validate the percentage is plausible (1-99%)
        pct = int(disk_pattern.group(1))
        plausible = 1 <= pct <= 99
        checks.append({
            "name": "disk_space_pct_plausible",
            "passed": plausible,
            "detail": f"Disk space {pct}% is {'plausible' if plausible else 'implausible (must be 1-99%)'}"
        })
        total_score += 0.08
        if plausible:
            total_score += 0.02

    # ── Check 11: Security audit result ──────────────────────────────────────
    audit_passed = re.search(r'✓\s*安全审计:\s*通过', content)
    checks.append({
        "name": "security_audit_passed",
        "passed": audit_passed is not None,
        "detail": "Found '✓ 安全审计: 通过'" if audit_passed else "Missing '✓ 安全审计: 通过' - agent must call openclaw security audit"
    })
    if audit_passed:
        total_score += 0.08

    # ── Check 12: Recommendations section has bullet points ──────────────────
    bullet_points = re.findall(r'•\s*.+', content)
    has_bullets = len(bullet_points) >= 1
    checks.append({
        "name": "recommendations_bullet_points",
        "passed": has_bullets,
        "detail": f"Found {len(bullet_points)} bullet point(s) with • symbol" if has_bullets else "Missing bullet points (•) in 【建议事项】section"
    })
    if has_bullets:
        total_score += 0.05

    # ── Final pass/fail ───────────────────────────────────────────────────────
    total_score = min(round(total_score, 3), 1.0)
    return checks, total_score


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace dir provided"}]}))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    try:
        checks, score = run_checks(workspace_dir)
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]}))
        sys.exit(1)

    # Pass threshold: must have file + all 3 sections + openclaw status + at least 0.60 overall
    critical_checks = ["report_file_exists", "chinese_section_headers", "openclaw_status_running", "unicode_box_border"]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    passed = critical_passed and score >= 0.60

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()