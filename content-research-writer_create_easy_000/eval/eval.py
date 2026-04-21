import os
import sys
import json
import re
from pathlib import Path

def check_file_exists_and_readable(filepath, name):
    if not os.path.exists(filepath):
        return False, f"{name} file not found"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if len(content) < 50:
            return False, f"{name} file too short (less than 50 characters)"
        return True, content
    except Exception as e:
        return False, f"Error reading {name} file: {str(e)}"

def evaluate_outline(content):
    content_lower = content.lower()
    checks = []
    has_title = any(keyword in content_lower for keyword in ['title', 'productivity', 'remote'])
    checks.append(("Has title/topic", has_title, "Found title or topic" if has_title else "No title found"))
    has_sections = bool(re.search(r'#+\s+|\d+\.|[-*]\s+', content))
    checks.append(("Has structured sections", has_sections, "Found section markers" if has_sections else "No section structure"))
    return checks

def evaluate_research(content):
    content_lower = content.lower()
    checks = []
    # 统计百分比数据点
    stats = re.findall(r'\d+%', content_lower)
    has_multiple_stats = len(stats) >= 3 # 要求至少3个数据点
    checks.append(("Has multiple data points", has_multiple_stats, f"Found {len(stats)} statistical references"))
    has_sources = any(marker in content_lower for marker in ['source', 'study', 'report', 'according to'])
    checks.append(("Includes sources/citations", has_sources, "Contains source references"))
    return checks

def evaluate_introduction(content):
    content_lower = content.lower()
    checks = []
    
    # 修复逻辑：使用 bool() 包装 re.search 结果
    hooks = [
        bool(re.search(r'^["\'].{20,}', content)), # 引用开头
        any(q in content_lower[:50] for q in ['imagine', 'what if', 'did you know', 'have you ever']), # 问题开头
        bool(re.search(r'\d+%', content[:200])), # 数据开头
        len(content.split('.')) > 2 # 有实质段落
    ]
    has_hook = any(hooks)
    checks.append(("Has compelling hook", has_hook, "Found engaging opening" if has_hook else "Hook missing"))
    
    word_count = len(content.split())
    checks.append(("Sufficient length", word_count >= 50, f"Intro has {word_count} words"))
    return checks

def main():
    # 容错处理
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    try:
        os.chdir(workspace)
    except:
        pass
    
    results = []
    files_to_check = [
        ('outline.md', evaluate_outline),
        ('research.md', evaluate_research),
        ('intro.md', evaluate_introduction)
    ]
    
    for filename, eval_func in files_to_check:
        exists, content = check_file_exists_and_readable(filename, filename)
        if exists:
            file_checks = eval_func(content)
            results.extend([(f"{filename}: {n}", p, d) for n, p, d in file_checks])
        else:
            results.append((f"{filename} exists", False, content))

    formatted_checks = [{'name': n, 'passed': p, 'detail': d} for n, p, d in results]
    # 计算得分，所有检查项全过才算 Passed
    score = sum(1 for c in formatted_checks if c['passed']) / len(formatted_checks) if formatted_checks else 0.0
    
    print(json.dumps({
        'passed': score >= 0.9,
        'score': round(score, 2),
        'checks': formatted_checks
    }))

if __name__ == '__main__':
    # 语法检查：python3 -m py_compile eval.py
    main()