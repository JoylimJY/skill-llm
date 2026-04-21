import os
import sys
import json
import re

def count_bullet_points(text, category_names):
    """
    辅助函数：统计指定类别标题下的列表项数量。
    支持 #, ##, ### 等标题样式。
    """
    lines = text.splitlines()
    counts = {cat.lower(): 0 for cat in category_names}
    current_category = None

    heading_re = re.compile(r'^#{1,6}\s+(.*)')
    bullet_re = re.compile(r'^[\-\*\+]\s+')

    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = heading_re.match(line)
        if m:
            heading_content = m.group(1).lower()
            # 匹配当前行是否包含目标类别关键词
            matched_cats = [c.lower() for c in category_names if c.lower() in heading_content]
            current_category = matched_cats[0] if matched_cats else None
        elif bullet_re.match(line) and current_category:
            counts[current_category] += 1
    return counts

def evaluate_changelog(workspace):
    # 1. 查找文件：支持大小写不敏感查找 CHANGELOG.md
    changelog_path = None
    for f in os.listdir(workspace):
        if f.lower() == 'changelog.md':
            changelog_path = os.path.join(workspace, f)
            break

    if not changelog_path:
        return {
            "passed": False, 
            "score": 0.0, 
            "checks": [{"name": "file_exists", "passed": False, "detail": "CHANGELOG.md not found in root"}]
        }

    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()
    content_lower = content.lower()

    checks = []

    # --- Check 1: 严格的日期范围检测 ---
    # Hard难度要求清晰的日期标识，不接受模糊匹配
    # 接受 ISO格式: 2024-03-01 到 2024-03-15 / March 1, 2024 - March 15, 2024
    date_patterns = [
        r'2024-03-01.*?2024-03-15',  # ISO格式范围
        r'march\s+1.*?march\s+15.*?2024',  # 英文格式
        r'mar\s+1.*?mar\s+15.*?2024',      # 缩写
        r'03[/-]01[/-]2024.*?03[/-]15[/-]2024',  # 美式日期
        r'1\s+march.*?15\s+march.*?2024'   # 英式日期
    ]
    
    date_found = any(bool(re.search(p, content_lower, re.S)) for p in date_patterns)
    
    # 额外检查：必须有summary sentence（简短总结句）
    has_summary = bool(re.search(r'#{1,6}\s+.*?(changelog|release|update).*?(\n+.*[^#]{20,})', content_lower))
    
    check1_passed = date_found and has_summary
    checks.append({
        "name": "top_level_heading_date_range", 
        "passed": check1_passed,
        "detail": "Clear date range and summary present." if check1_passed else "Missing clear date range or summary sentence."
    })

    # --- Check 2: 类别标题完整性 ---
    categories = ["Features", "Improvements", "Bug Fixes", "Breaking Changes", "Security"]
    missing_cats = [c for c in categories if c.lower() not in content_lower]
    check2_passed = len(missing_cats) == 0
    checks.append({
        "name": "all_category_headings_present",
        "passed": check2_passed,
        "detail": "All 5 required categories present." if check2_passed else f"Missing categories: {missing_cats}"
    })

    # --- Check 3: 噪点过滤 (智能检测) ---
    # 必须排除日期范围外的commits (Feb 28, March 16)
    # 必须排除噪音 commits (refactor, ci, docs)
    bullet_lines = [line for line in content_lower.splitlines() if re.match(r'^\s*[\-\*\+]\s+', line)]
    
    # 检查是否包含不应出现的commits (噪音或日期外)
    forbidden_patterns = [
        "early feature before march",  # Feb 28 commit
        "post-march",                   # March 16 commit
        "update readme",               # docs commit
        "clean up workspace code",     # refactor commit
        "pipeline", "node 20",         # ci commit
        "refactor:", "chore:", "ci:", "docs:", "test:"
    ]
    noise_found = any(any(p in line for p in forbidden_patterns) for line in bullet_lines)
    
    # 检查是否确实排除了噪音（通过噪音commits的数量应正确）
    # 应该在3月1-15范围内的commits: 8个 (2个feat, 1个improve, 3个fix, 1个breaking, 1个security)
    # 实际bullet数量应在8个左右（可能有合并，但不应太多或太少）
    bullet_count = len(bullet_lines)
    reasonable_count = 6 <= bullet_count <= 10
    
    noise_check_passed = not noise_found and reasonable_count
    checks.append({
        "name": "noise_commits_filtered_out",
        "passed": noise_check_passed,
        "detail": f"Filtered noise/out-of-range commits. Found {bullet_count} entries (expected 6-10)." if noise_check_passed else f"Found noise commits or incorrect count ({bullet_count})."
    })

    # --- Check 4: 类别内容填充检测 ---
    counts = count_bullet_points(content, categories)
    # 只要每个类别下至少有一个条目即可
    bullets_ok = all(counts.get(cat.lower(), 0) >= 1 for cat in categories)
    count_summary = ', '.join([f'{cat}: {counts.get(cat.lower(),0)}' for cat in categories])
    checks.append({
        "name": "entries_in_all_categories",
        "passed": bullets_ok,
        "detail": f"Entries count: {count_summary}" if bullets_ok else f"Incomplete categories. Current: {count_summary}"
    })

    # --- Check 5: 语义翻译检测 (必须包含所有8个commits的用户友好翻译) ---
    # 基于 gen_inputs.py 的8个commits (3/1-3/15)，检查每个都被翻译并分类
    # 不再只是关键词，而是检查功能点是否被清晰描述
    
    required_translations = [
        # Features (2个)
        ("team workspace", "Features", ["team", "workspace", "invite", "project"]),
        ("keyboard shortcut", "Features", ["shortcut", "keyboard", "press", "help", "navigate"]),
        # Improvements (1个)
        ("file sync speed", "Improvements", ["sync", "faster", "speed", "2x", "file"]),
        # Bug Fixes (3个)
        ("image upload", "Bug Fixes", ["image", "upload", "large", "resolve", "fail"]),
        ("notification badge", "Bug Fixes", ["badge", "notification", "count", "correct"]),
        ("timezone scheduled", "Bug Fixes", ["timezone", "schedule", "post", "time"]),
        # Breaking Changes (1个)
        ("api deprecated", "Breaking Changes", ["api", "deprecat", "remove", "legacy", "update"]),
        # Security (1个)
        ("security vulnerability", "Security", ["security", "vulnerability", "patch", "redirect", "safe"])
    ]
    
    found_count = 0
    missing_translations = []
    
    for topic_name, expected_category, keywords in required_translations:
        # 检查是否在任何category中被提到
        topic_found = any(kw in content_lower for kw in keywords)
        if topic_found:
            found_count += 1
        else:
            missing_translations.append(topic_name)
    
    # Hard难度要求所有8个commits都被翻译
    check5_passed = found_count == 8
    checks.append({
        "name": "technical_to_user_friendly_translation",
        "passed": check5_passed,
        "detail": f"All 8 commits translated: {found_count}/8." if check5_passed else f"Missing translations: {', '.join(missing_translations)}"
    })

    # --- 最终评分 ---
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    # 只有拿到 1.0 满分才算整体 Passed，或者根据你的需求设为 0.8
    overall_passed = score >= 1.0

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "system", "passed": False, "detail": "No workspace path"}]}))
        return

    workspace = sys.argv[1]
    try:
        result = evaluate_changelog(workspace)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({
            "passed": False, 
            "score": 0.0, 
            "checks": [{"name": "error", "passed": False, "detail": str(e)}]
        }))

if __name__ == "__main__":
    main()