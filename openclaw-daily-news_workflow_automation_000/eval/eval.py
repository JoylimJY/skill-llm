import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Check 1: Find the output file ──────────────────────────────────────
    candidates = list(workspace_path.rglob("daily_report_2026-03-15.md"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "Output file daily_report_2026-03-15.md exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s)" if file_found else "File not found anywhere in workspace"
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    # Read the file
    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "File readable", "passed": True, "detail": f"File size: {len(content)} chars"})

    # ── Check 2: Report date 2026-03-15 present ─────────────────────────
    date_ok = "2026-03-15" in content
    checks.append({
        "name": "Report date 2026-03-15 appears in content",
        "passed": date_ok,
        "detail": "Date string found" if date_ok else "Date '2026-03-15' not found in report"
    })

    # ── Check 3: All four standard sections present ───────────────────────
    sections = {
        "一、当日资讯概况": "## 一、" in content or "一、当日资讯概况" in content,
        "二、详细分类资讯": "## 二、" in content or "二、详细分类资讯" in content,
        "三、核心分析与展望": "## 三、" in content or "三、核心分析与展望" in content,
        "四、附录": "## 四、" in content or "四、附录" in content,
    }
    all_sections = all(sections.values())
    checks.append({
        "name": "All four standard sections present (一/二/三/四)",
        "passed": all_sections,
        "detail": f"Sections found: {[k for k,v in sections.items() if v]}, missing: {[k for k,v in sections.items() if not v]}"
    })

    # ── Check 4: All 6 category names present in section 2 ───────────────
    required_cats = [
        "安全监管与风险警示",
        "产业生态与市场动态",
        "技术发展与社区生态",
        "AI产业宏观趋势",
        "政策与监管",
        "其他重要科技进展",
    ]
    cats_found = {cat: cat in content for cat in required_cats}
    all_cats = all(cats_found.values())
    checks.append({
        "name": "All 6 standard category names present",
        "passed": all_cats,
        "detail": f"Missing categories: {[c for c,v in cats_found.items() if not v]}" if not all_cats else "All 6 categories found"
    })

    # ── Check 5: N001 (工信部, 超危漏洞) → 安全监管与风险警示, HIGH risk ──
    # The 工信部 item must appear under "安全监管" section
    n001_title_keywords = ["工信部", "高危漏洞", "预警通告", "CVE-2026"]
    n001_in_content = any(kw in content for kw in n001_title_keywords)
    # Check it's under security section and not misclassified elsewhere
    security_section_match = re.search(
        r"安全监管与风险警示.*?(?=###\s*\d+\.|##\s|$)",
        content, re.DOTALL
    )
    n001_in_security = False
    if security_section_match:
        security_text = security_section_match.group(0)
        n001_in_security = any(kw in security_text for kw in ["工信部", "CVE-2026", "高危漏洞", "超危"])
    checks.append({
        "name": "N001 (工信部高危漏洞) classified under 安全监管与风险警示",
        "passed": n001_in_security,
        "detail": "工信部 CVE item found in 安全监管 section" if n001_in_security else "工信部 CVE item NOT found in 安全监管与风险警示 section"
    })

    # ── Check 6: N001 marked as HIGH risk ────────────────────────────────
    high_risk_indicators = ["高风险", "high", "🔴"]
    n001_high_risk = False
    if security_section_match:
        security_text = security_section_match.group(0)
        n001_high_risk = any(ind in security_text for ind in high_risk_indicators)
    checks.append({
        "name": "N001 (工信部漏洞) assigned high risk level",
        "passed": n001_high_risk,
        "detail": "High risk indicator found in 安全监管 section" if n001_high_risk else "No high risk indicator found for 安全监管 items"
    })

    # ── Check 7: N004 (碳纤维) → 其他重要科技进展 (NOT AI产业宏观趋势) ──
    other_section_match = re.search(
        r"其他重要科技进展.*?(?=##\s|$)",
        content, re.DOTALL
    )
    n004_in_other = False
    if other_section_match:
        other_text = other_section_match.group(0)
        n004_in_other = "碳纤维" in other_text

    # Also check it's NOT in AI产业宏观趋势
    ai_section_match = re.search(
        r"AI产业宏观趋势.*?(?=###\s*\d+\.|##\s|$)",
        content, re.DOTALL
    )
    n004_not_in_ai = True
    if ai_section_match:
        ai_text = ai_section_match.group(0)
        if "碳纤维" in ai_text:
            n004_not_in_ai = False

    n004_correct = n004_in_other and n004_not_in_ai
    checks.append({
        "name": "N004 (碳纤维新材料) correctly classified under 其他重要科技进展",
        "passed": n004_correct,
        "detail": (
            f"In '其他重要科技进展': {n004_in_other}, "
            f"NOT in 'AI产业宏观趋势': {n004_not_in_ai}"
        )
    })

    # ── Check 8: N003 (GitHub PR) → 技术发展与社区生态 ───────────────────
    tech_section_match = re.search(
        r"技术发展与社区生态.*?(?=###\s*\d+\.|##\s|$)",
        content, re.DOTALL
    )
    n003_in_tech = False
    if tech_section_match:
        tech_text = tech_section_match.group(0)
        n003_in_tech = any(kw in tech_text for kw in ["PR-892", "多模态工具调用", "v2.4.0", "PR"])
    checks.append({
        "name": "N003 (GitHub PR) classified under 技术发展与社区生态",
        "passed": n003_in_tech,
        "detail": "GitHub PR item found in tech section" if n003_in_tech else "GitHub PR item NOT found in 技术发展与社区生态"
    })

    # ── Check 9: N005 (科技部政策) → 政策与监管 ──────────────────────────
    policy_section_match = re.search(
        r"政策与监管.*?(?=###\s*\d+\.|##\s|$)",
        content, re.DOTALL
    )
    n005_in_policy = False
    if policy_section_match:
        policy_text = policy_section_match.group(0)
        n005_in_policy = any(kw in policy_text for kw in ["科技部", "管理办法", "征求意见"])
    checks.append({
        "name": "N005 (科技部管理办法) classified under 政策与监管",
        "passed": n005_in_policy,
        "detail": "科技部 policy item found in policy section" if n005_in_policy else "科技部 policy item NOT found in 政策与监管"
    })

    # ── Check 10: N008 (比亚迪新能源汽车) → 其他重要科技进展 ─────────────
    n008_in_other = False
    if other_section_match:
        other_text = other_section_match.group(0)
        n008_in_other = any(kw in other_text for kw in ["比亚迪", "新能源汽车", "自动驾驶"])
    checks.append({
        "name": "N008 (比亚迪新能源汽车) classified under 其他重要科技进展",
        "passed": n008_in_other,
        "detail": "比亚迪/新能源汽车 item found in 其他重要科技进展" if n008_in_other else "比亚迪 item NOT found in 其他重要科技进展"
    })

    # ── Check 11: N011 (网信办约谈) → 安全监管 with HIGH risk ───────────
    n011_in_security = False
    n011_high_risk = False
    if security_section_match:
        security_text = security_section_match.group(0)
        n011_in_security = any(kw in security_text for kw in ["网信办", "约谈", "数据出境"])
        if n011_in_security:
            n011_high_risk = any(ind in security_text for ind in ["高风险", "high", "🔴"])
    checks.append({
        "name": "N011 (网信办约谈) classified under 安全监管与风险警示 with high risk",
        "passed": n011_in_security and n011_high_risk,
        "detail": f"In security section: {n011_in_security}, high risk: {n011_high_risk}"
    })

    # ── Check 12: Statistics summary present (total count) ───────────────
    # Report should show total items ≥ 10 (all 12 should be categorized)
    total_matches = re.findall(r"资讯总数[：:]\s*\*?\*?(\d+)", content)
    stat_ok = False
    stat_detail = "No '资讯总数' statistic found"
    if total_matches:
        try:
            total_num = int(total_matches[0])
            stat_ok = total_num >= 10
            stat_detail = f"Total reported: {total_num}"
        except ValueError:
            stat_detail = f"Could not parse total: {total_matches[0]}"
    checks.append({
        "name": "Statistics section shows total news count ≥ 10",
        "passed": stat_ok,
        "detail": stat_detail
    })

    # ── Check 13: N006/N012 (AI芯片/投资融资) → AI产业宏观趋势 ──────────
    n006_in_ai = False
    n012_in_ai = False
    if ai_section_match:
        ai_text = ai_section_match.group(0)
        n006_in_ai = any(kw in ai_text for kw in ["GB300", "英伟达", "AI芯片", "算力"])
        n012_in_ai = any(kw in ai_text for kw in ["120亿", "投资报告", "融资", "pitchbook", "PitchBook"])
    checks.append({
        "name": "N006 (英伟达AI芯片) and N012 (融资报告) classified under AI产业宏观趋势",
        "passed": n006_in_ai and n012_in_ai,
        "detail": f"英伟达芯片 in AI section: {n006_in_ai}, 融资报告 in AI section: {n012_in_ai}"
    })

    # ── Scoring ───────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_count / total_checks, 4)

    # Must pass critical checks to be considered overall passing
    critical_checks = [
        "Output file daily_report_2026-03-15.md exists",
        "All four standard sections present (一/二/三/四)",
        "All 6 standard category names present",
        "N001 (工信部高危漏洞) classified under 安全监管与风险警示",
        "N004 (碳纤维新材料) correctly classified under 其他重要科技进展",
        "N003 (GitHub PR) classified under 技术发展与社区生态",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    overall_passed = critical_passed and score >= 0.70

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))