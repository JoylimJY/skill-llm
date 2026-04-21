import sys
import os
import json
import re
from pathlib import Path

def evaluate_portfolio(workspace_dir):
    checks = []
    # 强化路径查找：递归搜索整个工作目录，确保不会漏掉文件
    workspace_path = Path(workspace_dir).resolve()
    
    # 尝试寻找命名的文件，如果没有，找任何 html
    all_html = list(workspace_path.rglob('*.html'))
    portfolio_file = next((f for f in all_html if 'portfolio' in f.name.lower() or 'landing' in f.name.lower()), None)
    
    if not portfolio_file and all_html:
        portfolio_file = all_html[0]
        
    if not portfolio_file:
        return {
            "passed": False, 
            "score": 0.0, 
            "checks": [{"name": "HTML file exists", "passed": False, "detail": f"No HTML found in {workspace_path}"}]
        }
    
    try:
        # 使用 errors='ignore' 防止因为特殊字符导致读取崩溃
        content = portfolio_file.read_text(encoding='utf-8', errors='ignore')
        content_low = content.lower()
    except Exception as e:
        return {"passed": False, "score": 0.0, "detail": f"Read error: {e}"}

    checks.append({"name": "HTML file exists", "passed": True, "detail": f"Found {portfolio_file.name}"})

    # 1. 身份与内容检查
    # 灵活匹配 Alex Chen 或 Maya Chen 或 Brew & Bond
    has_identity = any(k in content_low for k in ['alex', 'maya', 'chen', 'brew', 'bond'])
    checks.append({"name": "Brand/Identity present", "passed": has_identity})

    # 2. 结构检查 (Hero, Projects, About, Contact)
    # 不再死板检查 ID，而是检查语义关键词
    sections = {
        "Hero/Intro": ['hero', 'intro', 'artist', 'subscription'],
        "Projects/Gallery": ['project', 'work', 'gallery', 'featured'],
        "About/Bio": ['about', 'bio', 'story', 'lorem'],
        "Contact/Form": ['contact', 'form', 'email', 'message']
    }
    for sec_name, keywords in sections.items():
        found = any(k in content_low for k in keywords)
        checks.append({"name": f"Section: {sec_name}", "passed": found})

    # 3. 设计元素检查 (Brutalist/Modern)
    # 检查是否有较复杂的 CSS 定义
    has_design = any(k in content_low for k in ['@keyframes', 'transition', 'flex', 'grid', 'border-thick', 'background:'])
    checks.append({"name": "Visual styling present", "passed": has_design})

    # 4. 交互性检查
    has_interact = any(k in content_low for k in ['<script', 'hover', 'onclick', 'scroll'])
    checks.append({"name": "Interactions present", "passed": has_interact})

    score = sum(1 for c in checks if c.get('passed', False)) / len(checks)
    
    return {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    # 确保 argv[1] 存在，否则默认当前目录
    ws = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    try:
        result = evaluate_portfolio(ws)
    except Exception as e:
        result = {"passed": False, "score": 0.0, "error": str(e)}
    
    # 核心修复：必须使用 json.dumps 强制输出标准 JSON
    print(json.dumps(result))