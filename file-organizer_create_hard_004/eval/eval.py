import os
import sys
import json
import re
from pathlib import Path

def check_naming_robust(filename):
    """
    支持多种分隔符的日期开头格式：
    2023-10-01 - desc.ext
    2023-10-01 desc.ext
    2023-10-01-desc.ext
    """
    # 匹配 YYYY-MM-DD 开头，后面跟着分隔符和描述
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}[ \-_].+', filename))

def check_report_headings_robust(text):
    # 只要包含核心关键词即可，不强制要求完全匹配标题行
    keywords = ['current state', 'duplicate', 'proposed', 'implemented', 'moved', 'renamed']
    text_lower = text.lower()
    return [ (kw in text_lower, f"Keyword: {kw}") for kw in keywords ]

def main():
    if len(sys.argv) < 2:
        return
    
    workspace = Path(sys.argv[1]) / 'Documents'
    report_path = workspace / 'organization_report.md'
    dup_path = workspace / 'duplicates_to_delete.txt'
    
    checks = []
    
    # 1. 报告存在性与基本内容
    if report_path.is_file():
        content = report_path.read_text(errors='ignore')
        h_checks = check_report_headings_robust(content)
        for p, d in h_checks:
            checks.append({"name": f"Report Content: {d}", "passed": p})
    else:
        checks.append({"name": "Report file exists", "passed": False})

    # 2. 物理目录结构检查 (不依赖 Markdown 解析)
    # 检查核心目录是否存在即可判定 Agent 是否执行了创建操作
    essential_paths = [
        'Work/Reports', 'Work/Projects', 'Personal/Photos', 'Personal/Financials', 'Misc'
    ]
    found_paths = 0
    for p in essential_paths:
        if (workspace / p).is_dir():
            found_paths += 1
    checks.append({"name": "Hierarchy created", "passed": found_paths >= 3})

    # 3. 移动逻辑检查
    # 检查是否有文件进了子目录
    sub_files = list(workspace.glob('**/*'))
    moved_count = sum(1 for f in sub_files if f.is_file() and f.parent != workspace)
    checks.append({"name": "Files distributed", "passed": moved_count > 5})

    # 4. 重命名格式检查 (关键容错)
    renamed_ok = 0
    total_files = 0
    for f in workspace.rglob('*'):
        if f.is_file() and f.suffix not in ['.md', '.txt']:
            total_files += 1
            if check_naming_robust(f.name):
                renamed_ok += 1
    
    checks.append({
        "name": "Robust Renaming Check", 
        "passed": (renamed_ok / total_files > 0.7) if total_files > 0 else False
    })

    # 5. 重复文件处理 (存在 txt 即可，表示 Agent 识别了该逻辑)
    checks.append({"name": "Duplicates logic handled", "passed": dup_path.is_file()})

    score = sum(1 for c in checks if c['passed']) / len(checks)
    print(json.dumps({"passed": score >= 0.8, "score": score, "checks": checks}, indent=2))

if __name__ == '__main__':
    main()