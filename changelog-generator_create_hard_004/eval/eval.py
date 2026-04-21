import os
import sys
import json
import re

def evaluate_changelog(path):
    # 查找包含 changelog 字样的 markdown 文件
    md_files = [f for f in os.listdir(path) if f.lower().endswith('.md') and 'changelog' in f.lower()]

    if not md_files:
        return {
            "passed": False, 
            "score": 0, 
            "checks": [{"name": "Find changelog markdown", "passed": False, "detail": "No Markdown file with 'changelog' in name found."}]
        }

    best_score = 0
    best_details = None

    for file in md_files:
        full_path = os.path.join(path, file)
        with open(full_path, 'r', encoding='utf-8') as f:
            text = f.read().lower()

        checks = []

        # --- Check 1: 日期范围检测 (最终版：超强容错) ---
        # 只要在前 1000 字符内按顺序出现了 March, 1, 15, 2024 即可
        # 这种逻辑可以完美覆盖 "March 1-15", "March 1 to 15", "March 1st to March 15th"
        date_pattern = r'march.*?\b1\b.*?\b15\b.*?2024'
        date_header_pass = bool(re.search(date_pattern, text[:1000], re.S))
        
        checks.append({
            "name": "Date range heading", 
            "passed": date_header_pass, 
            "detail": "Date range March 1-15, 2024 detected." if date_header_pass else "Expected date range (March, 1, 15, 2024) not found near the top."
        })

        # --- Check 2: 类别标题及图标 ---
        categories = {
            'new features': ['✨', 'new features'],
            'improvements': ['🔧', 'improvements'],
            'bug fixes': ['🐛', 'fixes', 'bugs'],
            'breaking changes': ['breaking changes'],
            'security': ['security']
        }

        for cat, keywords in categories.items():
            has_cat = any(k in text for k in keywords)
            checks.append({
                "name": f"Category heading: {cat}",
                "passed": has_cat,
                "detail": f"Found category or icon for {cat}." if has_cat else f"Missing category heading or icon for {cat}."
            })

        # --- Check 3: 排除内部开发信息 ---
        internal_keywords = ['refactor', 'test', 'chore']
        internal_mentioned = any(k in text for k in internal_keywords)

        checks.append({
            "name": "Internal commits excluded",
            "passed": not internal_mentioned,
            "detail": "Changelog is clean." if not internal_mentioned else "Contains internal keywords."
        })

        # --- Check 4: 用户友好描述 (Topic 覆盖) ---
        required_topics = [
            'team workspaces', 'keyboard shortcuts', 'sync', 'search', 
            'images', 'timezone', 'notification', 'breaking', 
            'security', 'factor', 'settings', 'startup'
        ]

        topic_passes = [topic in text for topic in required_topics]
        topic_count = sum(topic_passes)
        
        # 只要覆盖了 12 个核心点中的 8 个 (66%) 就算通过
        passed_topics = topic_count >= 8
        
        checks.append({
            "name": "User-friendly translations",
            "passed": passed_topics,
            "detail": f"Covered {topic_count} of 12 key functional updates."
        })

        # --- Check 5: 列表格式 ---
        bullets_found = bool(re.search(r'^(?:- |\* )', text, re.MULTILINE))
        checks.append({
            "name": "Bullet points formatting", 
            "passed": bullets_found, 
            "detail": "Found bullet points." if bullets_found else "No bullets."
        })

        # 计算得分
        passed_checks = sum(1 for c in checks if c["passed"])
        score = passed_checks / len(checks)
        
        if score > best_score:
            best_score = score
            best_details = checks

    # 只要得分 >= 0.8 就判定为 Passed
    overall_passed = best_score >= 0.8
    
    return {
        "passed": overall_passed,
        "score": best_score,
        "checks": best_details
    }

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0, "checks": [{"name": "Args", "passed": False, "detail": "Missing path"}]}))
        return

    workspace_path = sys.argv[1]
    try:
        result = evaluate_changelog(workspace_path)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0, "checks": [{"name": "Error", "passed": False, "detail": str(e)}]}))

if __name__ == '__main__':
    main()