import sys
import json
import re
from pathlib import Path
from datetime import date

workspace = Path(sys.argv[1])

checks = []
score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── Find the report file ──────────────────────────────────────────────────
job_dir = workspace / "jobs" / "后端开发-3年经验"
report_files = list(job_dir.glob("面试报告*.md"))

if not report_files:
    # also check for any .md file that might be the report
    report_files = list(job_dir.glob("*.md"))

report_found = len(report_files) > 0
score += add_check(
    "report_file_exists",
    report_found,
    f"Found report file(s): {[f.name for f in report_files]}" if report_found
    else "No 面试报告*.md file found in jobs/后端开发-3年经验/"
)

if not report_found:
    print(json.dumps({
        "passed": False,
        "score": 0.0,
        "checks": checks
    }))
    sys.exit(0)

report_path = report_files[0]
try:
    content = report_path.read_text(encoding="utf-8")
except Exception as e:
    content = ""
    add_check("report_readable", False, f"Could not read report: {e}")

# ── Check 1: Candidate names extracted from CONTENT (not filenames) ───────
# Files are named: cv_new_2025.html, applicant_003.txt, resume_junior.txt, 1234_wp_backend.html
# Names in content: 李伟, 张芳, 陈浩, 王鹏

candidates_expected = ["李伟", "张芳", "陈浩", "王鹏"]
# Allow Li Wei as alternative for 李伟
content_lower = content

found_names = []
for name in candidates_expected:
    if name in content:
        found_names.append(name)

# Also check for english alternative
if "李伟" not in found_names and ("Li Wei" in content or "liwei" in content.lower()):
    found_names.append("李伟(alt)")

names_found_count = sum(1 for n in candidates_expected if n in content or 
                        (n == "李伟" and ("Li Wei" in content or "liwei" in content.lower())))

score += add_check(
    "candidate_names_from_content",
    names_found_count >= 3,
    f"Found {names_found_count}/4 candidate names (李伟/张芳/陈浩/王鹏) extracted from file content. "
    f"Files are generically named (cv_new_2025.html etc.) — names must come from content."
)

# ── Check 2: Hard veto applied to 陈浩 ────────────────────────────────────
# 陈浩 has only 1.5 years experience, hard requirement is 3 years → must be eliminated
# Should have 🔴 or explicit elimination language

chen_hao_section = ""
if "陈浩" in content:
    idx = content.index("陈浩")
    # get surrounding context (500 chars)
    chen_hao_section = content[max(0, idx-50):idx+500]

veto_indicators = ["🔴", "不太匹配", "淘汰", "一票否决", "不满足", "不符合", "硬性", "排除"]
veto_applied = any(ind in chen_hao_section for ind in veto_indicators) if chen_hao_section else False

# Also acceptable: score < 60 explicitly shown
score_pattern = re.search(r'陈浩.{0,200}(\d{1,2})\s*[分/]', content, re.DOTALL)
low_score_applied = False
if score_pattern:
    try:
        s = int(score_pattern.group(1))
        if s < 60:
            low_score_applied = True
    except:
        pass

score += add_check(
    "hard_veto_chen_hao",
    veto_applied or low_score_applied,
    f"陈浩 has 1.5yr experience (hard requirement: 3yr). "
    f"Veto indicators found: {veto_applied}. Low score applied: {low_score_applied}. "
    f"Context: '{chen_hao_section[:200]}'"
)

# ── Check 3: Li Wei ranked #1 (strong recommendation 🟢) ─────────────────
# Li Wei: 5yr, Python+Go, Docker+K8s, Kafka, MySQL+Redis, open source (520 stars), B2B SaaS
# Should score 80-100 and be top ranked

liwei_section = ""
if "李伟" in content:
    idx = content.index("李伟")
    liwei_section = content[max(0, idx-50):idx+800]

strong_rec = "🟢" in liwei_section
ranked_first = False
# Check if 李伟 appears before 张芳 and 王鹏 in ranking context
if "李伟" in content and "王鹏" in content:
    if content.index("李伟") < content.index("王鹏"):
        ranked_first = True

high_score = False
score_match = re.search(r'李伟.{0,300}([8-9]\d|100)\s*[分/]', content, re.DOTALL)
if score_match:
    high_score = True

score += add_check(
    "liwei_top_ranked_strong",
    strong_rec or high_score or ranked_first,
    f"李伟 should be top-ranked with 🟢. "
    f"🟢 present: {strong_rec}. High score (80+): {high_score}. Appears before 王鹏: {ranked_first}."
)

# ── Check 4: Four-category interview questions (A/B/C/D) ─────────────────
# Must have: A.技术/专业能力验证, B.项目深挖, C.软实力评估, D.待确认
category_patterns = [
    (r'[Aa][\.\s、:：].*[技术|专业|能力]|技术.{0,10}验证|专业能力', "A-技术验证"),
    (r'[Bb][\.\s、:：].*[项目|深挖]|项目深挖|STAR', "B-项目深挖"),
    (r'[Cc][\.\s、:：].*[软实力|团队|协作|沟通]|软实力', "C-软实力"),
    (r'[Dd][\.\s、:：].*[待确认|风险|澄清]|待确认', "D-待确认"),
]

found_categories = []
for pattern, label in category_patterns:
    if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
        found_categories.append(label)

score += add_check(
    "four_question_categories",
    len(found_categories) >= 3,
    f"Expected 4 question categories (A技术/B项目/C软实力/D待确认). "
    f"Found: {found_categories}"
)

# ── Check 5: personalprefer.txt influence visible ─────────────────────────
# personalprefer.txt mentions: 踏实肯干、ownership、on-call/线上故障、结论先行、量化数据
# These themes should appear in interview questions

prefer_keywords = ["on-call", "线上", "故障", "ownership", "踏实", "量化", "结论", "执行力", "皮实"]
prefer_found = [kw for kw in prefer_keywords if kw in content]

score += add_check(
    "personalprefer_integrated",
    len(prefer_found) >= 2,
    f"personalprefer.txt at jobs/ root should influence questions. "
    f"Found preference keywords in report: {prefer_found}"
)

# ── Check 6: Scoring breakdown follows 40+30+20+10 or explicit mention ───
scoring_keywords = ["核心技能", "经验相关", "项目质量", "加分项", "硬性要求", "匹配度", "评分"]
scoring_present = sum(1 for kw in scoring_keywords if kw in content)

score += add_check(
    "scoring_dimensions_present",
    scoring_present >= 3,
    f"Report should reflect scoring dimensions (core skills 40, experience 30, projects 20, bonus 10). "
    f"Found {scoring_present}/7 scoring keywords: {[kw for kw in scoring_keywords if kw in content]}"
)

# ── Check 7: Risk points (待确认/风险点) section for each qualified candidate ──
risk_indicators = ["风险", "待确认", "疑虑", "存疑", "建议确认", "跳槽", "经验断层"]
risk_found = any(ri in content for ri in risk_indicators)

score += add_check(
    "risk_points_present",
    risk_found,
    f"Report should include risk/concern sections per candidate. "
    f"Found risk indicators: {[ri for ri in risk_indicators if ri in content]}"
)

# ── Check 8: Report structure has ranking table ───────────────────────────
table_indicators = ["|", "排名", "推荐", "匹配"]
table_score = sum(1 for ti in table_indicators if ti in content)

score += add_check(
    "ranking_table_present",
    table_score >= 3,
    f"Report should contain a ranking table. "
    f"Table indicators found: {[ti for ti in table_indicators if ti in content]}"
)

# ── Check 9: 张芳 rated 🟡 (moderate, 60-79) ─────────────────────────────
# Zhang Fang: 4yr Python, MySQL+Redis, Linux/Shell, but no K8s, no Kafka, no open source
# Should be 🟡 建议考虑
zhangfang_section = ""
if "张芳" in content:
    idx = content.index("张芳")
    zhangfang_section = content[max(0, idx-20):idx+400]

zhangfang_moderate = ("🟡" in zhangfang_section or "建议考虑" in zhangfang_section)

score += add_check(
    "zhangfang_moderate_rating",
    zhangfang_moderate,
    f"张芳 matches core requirements partially (no K8s/Kafka/open source). "
    f"Should be 🟡 建议考虑. Found: {'🟡' if '🟡' in zhangfang_section else ''}"
    f" Section: '{zhangfang_section[:150]}'"
)

# ── Check 10: Interview questions are personalized per candidate ──────────
# At minimum, questions should reference candidate-specific projects or skills
liwei_specific = any(kw in content for kw in ["fastcache", "520", "PyCon", "微服务拆分", "200万", "Open API"])
wangpeng_specific = any(kw in content for kw in ["商品服务", "库存", "分库分表", "电商", "Gin"])

score += add_check(
    "personalized_questions",
    liwei_specific or wangpeng_specific,
    f"Interview questions should reference specific projects/details from each resume. "
    f"Li Wei specifics found: {liwei_specific}. Wang Peng specifics found: {wangpeng_specific}."
)

# ── Final scoring ──────────────────────────────────────────────────────────
total_checks = 10
passed_checks = sum(1 for c in checks if c["passed"])
final_score = passed_checks / total_checks
overall_passed = final_score >= 0.7  # need 7/10 to pass

print(json.dumps({
    "passed": overall_passed,
    "score": round(final_score, 2),
    "checks": checks
}, ensure_ascii=False, indent=2))