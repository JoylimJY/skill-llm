import sys
import json
import re
from pathlib import Path
from datetime import datetime

def find_report(workspace: Path):
    candidates = list(workspace.rglob("anime_report.md"))
    if not candidates:
        return None
    return candidates[0]

def run_checks(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    
    report_path = find_report(workspace)
    
    # Check 1: File exists
    file_exists = report_path is not None
    checks.append({
        "name": "anime_report.md exists",
        "passed": file_exists,
        "detail": f"Found at {report_path}" if file_exists else "anime_report.md not found anywhere in workspace"
    })
    
    if not file_exists:
        return checks, 0.0
    
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        return checks, 0.0
    
    # Check 2: Has correct season header (format: # 📅 YYYY年{季节}新番热榜)
    current_month = datetime.now().month
    season_map = {range(1,4): "冬季", range(4,7): "春季", range(7,10): "夏季", range(10,13): "秋季"}
    expected_season = None
    for month_range, season in season_map.items():
        if current_month in month_range:
            expected_season = season
            break
    
    year = datetime.now().year
    season_header_pattern = rf"#\s*📅\s*{year}年{expected_season}新番热榜"
    has_season_header = bool(re.search(season_header_pattern, content))
    checks.append({
        "name": f"Correct season header (# 📅 {year}年{expected_season}新番热榜)",
        "passed": has_season_header,
        "detail": f"Expected pattern '{season_header_pattern}' in document. Season detected from month={current_month}"
    })
    
    # Check 3: Has TOP 3 section with 🔥
    has_top3 = bool(re.search(r"##\s*🔥\s*本周最热\s*TOP\s*3", content))
    checks.append({
        "name": "Has '## 🔥 本周最热 TOP 3' section",
        "passed": has_top3,
        "detail": "Section '## 🔥 本周最热 TOP 3' must be present"
    })
    
    # Check 4: TOP 3 section lists exactly 3 anime entries (### 1. ### 2. ### 3.)
    top3_entries = re.findall(r"###\s*[1-3]\.\s*《[^》]+》", content)
    has_3_entries = len(top3_entries) >= 3
    checks.append({
        "name": "TOP 3 has exactly 3 titled entries (### 1/2/3. 《...》)",
        "passed": has_3_entries,
        "detail": f"Found {len(top3_entries)} entries: {top3_entries}"
    })
    
    # Check 5: Type/Genre classification section with 📂 icon
    has_type_section = bool(re.search(r"##\s*📂\s*按类型分类", content))
    checks.append({
        "name": "Has '## 📂 按类型分类' section",
        "passed": has_type_section,
        "detail": "Section '## 📂 按类型分类' must be present"
    })
    
    # Check 6: Has markdown tables in type classification (| xxx | xxx | xxx |)
    table_rows = re.findall(r"\|[^|\n]+\|[^|\n]+\|[^|\n]+\|", content)
    has_tables = len(table_rows) >= 3  # at least 1 header + 1 separator + 1 data row
    checks.append({
        "name": "Type classification has Markdown tables",
        "passed": has_tables,
        "detail": f"Found {len(table_rows)} table rows. Expected at least 3 (header, separator, data)."
    })
    
    # Check 7: Sequels are separated into a dedicated section (续集·老粉专属)
    has_sequel_section = bool(re.search(r"续集[··]?老粉专属", content))
    checks.append({
        "name": "Sequel anime in separate '续集·老粉专属' section",
        "passed": has_sequel_section,
        "detail": "Sequels (第二季, 最终季, 剧场版, etc.) must be in a separate section named '续集·老粉专属'"
    })
    
    # Check 8: Main TOP 3 section does NOT contain sequels
    # The mock data sequels are: 败犬女主太多了！第二季, 偶像大师闪耀色彩 第2季, 物语系列 最终季, 我的青春恋爱物语 剧场版, 时光代理人 第二季
    # Top 3 by rank among non-sequels: 神之塔：新生 (#1), 迷宫饭 (#4), 暗杀教室 重制版 (#5)
    top3_section_match = re.search(r"##\s*🔥\s*本周最热\s*TOP\s*3(.*?)(?=##|\Z)", content, re.DOTALL)
    sequel_titles = ["败犬女主太多了", "偶像大师闪耀色彩", "物语系列", "我的青春恋爱物语", "时光代理人 第二季"]
    sequels_in_top3 = []
    if top3_section_match:
        top3_text = top3_section_match.group(1)
        for title in sequel_titles:
            if title in top3_text:
                sequels_in_top3.append(title)
    top3_clean = len(sequels_in_top3) == 0
    checks.append({
        "name": "Main TOP 3 does not contain sequel anime",
        "passed": top3_clean,
        "detail": f"Sequel titles found in TOP 3 section: {sequels_in_top3}. Sequels must go to '续集·老粉专属' only."
    })
    
    # Check 9: Has 💡 推荐入坑顺序 section
    has_recommendation = bool(re.search(r"##\s*💡\s*推荐入坑顺序", content))
    checks.append({
        "name": "Has '## 💡 推荐入坑顺序' section",
        "passed": has_recommendation,
        "detail": "Must have '## 💡 推荐入坑顺序' with '只追一部' and '追三部' bullets"
    })
    
    # Check 10: 推荐入坑 has both 只追一部 and 追三部
    has_only_one = bool(re.search(r"只追一部", content))
    has_three = bool(re.search(r"追三部", content))
    has_rec_bullets = has_only_one and has_three
    checks.append({
        "name": "推荐入坑顺序 has both '只追一部' and '追三部' bullets",
        "passed": has_rec_bullets,
        "detail": f"只追一部: {has_only_one}, 追三部: {has_three}"
    })
    
    # Check 11: Uncertain data annotated with 约 or 参考值
    # 迷宫饭, 凶兆侦探事务所 have followers_certain=False — data should have 约 or 参考值
    has_uncertainty_markers = bool(re.search(r"约|参考值", content))
    checks.append({
        "name": "Uncertain data annotated with '约' or '参考值'",
        "passed": has_uncertainty_markers,
        "detail": "Some anime have uncertain follower data; must be annotated with '约' or '参考值' per skill rules"
    })
    
    # Check 12: Data source line present (来源：Bilibili or similar)
    has_source_line = bool(re.search(r"来源[：:].*(Bilibili|B站|bilibili)", content, re.IGNORECASE))
    checks.append({
        "name": "Has data source line (来源：Bilibili...)",
        "passed": has_source_line,
        "detail": "The header block must contain a '来源：Bilibili 番剧热度榜' or similar attribution line"
    })
    
    # Check 13: Each TOP 3 entry has 类型, 简介, 更新, 热度 fields
    top3_block = ""
    if top3_section_match:
        top3_block = top3_section_match.group(1)
    has_all_fields = all([
        bool(re.search(r"\*\*类型\*\*", top3_block)),
        bool(re.search(r"\*\*简介\*\*", top3_block)),
        bool(re.search(r"\*\*更新\*\*", top3_block)),
        bool(re.search(r"\*\*热度\*\*", top3_block)),
    ])
    checks.append({
        "name": "TOP 3 entries have 类型/简介/更新/热度 fields",
        "passed": has_all_fields,
        "detail": "Each TOP 3 entry must have **类型**, **简介**, **更新**, **热度** bullet fields"
    })
    
    # Calculate score
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / len(checks)
    
    return checks, score

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    workspace_str = sys.argv[1]
    
    try:
        checks, score = run_checks(workspace_str)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "Eval script error", "passed": False, "detail": str(e)}]
        }))
        sys.exit(1)
    
    passed = score >= 0.75
    
    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()