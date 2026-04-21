import sys
import os
import re
import json
from bs4 import BeautifulSoup

def evaluate_portfolio(workspace_path):
    checks = []
    
    # 1. 查找 HTML 文件
    html_files = [f for f in os.listdir(workspace_path) if f.endswith('.html')]
    if not html_files:
        return {"passed": False, "score": 0.0, "checks": [{"name": "HTML file exists", "passed": False, "detail": "No HTML file found"}]}
    
    # 优先找 portfolio.html
    portfolio_file = next((f for f in html_files if 'portfolio' in f.lower()), html_files[0])
    file_path = os.path.join(workspace_path, portfolio_file)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"passed": False, "score": 0.0, "checks": [{"name": "File readable", "passed": False, "detail": str(e)}]}
    
    # 使用 BeautifulSoup 进行解析
    soup = BeautifulSoup(content, 'html.parser')
    text_content = soup.get_text().lower()
    
    # --- 开始各项检查 ---
    
    # Check 1: Artist name (兼容性搜索)
    name_present = 'maya' in text_content and 'chen' in text_content
    checks.append({"name": "Artist name present", "passed": name_present, "detail": "Maya Chen name found" if name_present else "Name missing"})
    
    # Check 2: CSS styling
    has_css = bool(soup.find('style') or 'style=' in content.lower() or 'stylesheet' in content.lower())
    checks.append({"name": "CSS styling included", "passed": has_css, "detail": "CSS detected"})
    
    # Check 3: Sections
    section_keywords = ['about', 'contact', 'work', 'gallery', 'featured']
    sections_found = sum(1 for k in section_keywords if k in text_content)
    checks.append({"name": "Multiple sections present", "passed": sections_found >= 3, "detail": f"Found {sections_found} sections"})
    
    # Check 4: Custom Typography (排除通用字体)
    font_families = re.findall(r'font-family\s*:\s*([^;]+)', content, re.I)
    generic = ['arial', 'helvetica', 'sans-serif', 'serif', 'times']
    has_custom = any(not any(g in f.lower() for g in generic) for f in font_families) or 'google' in content.lower()
    checks.append({"name": "Custom typography", "passed": has_custom, "detail": "Distinctive fonts detected"})
    
    # Check 5: Interactions
    has_js = bool(soup.find('script') or 'addEventListener' in content or '@keyframes' in content or 'transition:' in content)
    checks.append({"name": "Interactive elements", "passed": has_js, "detail": "Animations or JS found"})
    
    # Check 6: Contact
    contact_ok = any(k in text_content for k in ['email', 'instagram', 'behance', '@'])
    checks.append({"name": "Contact information", "passed": contact_ok, "detail": "Contact info present"})

    # 最终分值计算
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    
    return {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    # 路径容错
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    if not os.path.exists(workspace):
        workspace = '.'
        
    result = evaluate_portfolio(workspace)
    
    # 核心修复：使用 json.dumps 确保输出标准 JSON 格式
    print(json.dumps(result, indent=2))