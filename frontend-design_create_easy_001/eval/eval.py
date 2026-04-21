import sys
import os
import re
import json
from pathlib import Path

def evaluate_landing_page(workspace_dir):
    checks = []
    
    # 1. 寻找 HTML 文件 (不区分大小写，尝试多种可能)
    workspace = Path(workspace_dir)
    html_files = list(workspace.glob('*.html'))
    landing_file = next((f for f in html_files if 'landing' in f.name.lower()), None)
    
    if not landing_file and html_files:
        landing_file = html_files[0]
    
    if not landing_file:
        return {
            "passed": False, 
            "score": 0.0, 
            "checks": [{"name": "HTML file exists", "passed": False, "detail": "No HTML file found"}]
        }
    
    checks.append({"name": "HTML file exists", "passed": True, "detail": f"Found {landing_file.name}"})
    
    try:
        content = landing_file.read_text(encoding='utf-8').lower()
    except Exception as e:
        return {"passed": False, "score": 0.0, "detail": f"Read error: {e}"}

    # 2. 核心部分检测 (放宽关键词匹配)
    # Hero: 检查英雄区常见关键词或大标题
    hero_found = any(k in content for k in ['hero', 'banner', 'main', 'brew', 'bond'])
    checks.append({"name": "Hero section", "passed": hero_found})
    
    # Features: 检查特性介绍
    features_found = any(k in content for k in ['feature', 'benefit', 'service', 'difference'])
    checks.append({"name": "Features section", "passed": features_found})
    
    # Signup: 检查表单
    signup_found = any(k in content for k in ['form', 'input', 'subscribe', 'signup', 'join'])
    checks.append({"name": "Signup form", "passed": signup_found})
    
    # CSS & JS
    checks.append({"name": "CSS included", "passed": '<style' in content or 'style=' in content})
    checks.append({"name": "JS included", "passed": '<script' in content or 'addEventListener' in content})
    
    # 动画与交互 (检查关键 CSS 属性)
    anim_found = any(k in content for k in ['@keyframes', 'transition', 'transform', 'hover', 'animation'])
    checks.append({"name": "Animations/effects", "passed": anim_found})

    # 品牌内容
    brand_found = 'brew' in content and 'bond' in content
    checks.append({"name": "Brand consistency", "passed": brand_found})
    
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / len(checks)
    
    return {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    # 获取工作目录并确保输出为 JSON
    target_dir = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    try:
        result = evaluate_landing_page(target_dir)
    except Exception as e:
        result = {"passed": False, "score": 0.0, "error": str(e)}
    
    # 必须使用 json.dumps 确保符合 JSON 标准 (双引号, 小写布尔值)
    print(json.dumps(result))