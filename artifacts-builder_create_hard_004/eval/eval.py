import sys
import os
import json
import re

def check_bundle_html(bundle_path):
    try:
        with open(bundle_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content_lower = content.lower()
        
        checks = []

        # 1. HTML Title - 允许更灵活的匹配
        title_ok = bool(re.search(r'<title>.*?</title>', content, re.I | re.S))
        checks.append(('HTML title tag present', title_ok, 'Missing <title>'))

        # 2. 外部引用 - 只拦截 http/https 的外部资源，允许 data: 和 相对路径
        external_refs = re.findall(r'(?:src|href)=["\'](http[s]?://.*?)["\']', content_lower)
        no_external = len(external_refs) == 0
        checks.append(('No external references', no_external, f'Found external refs: {external_refs[:2]}'))

        # 3. React Root - 允许不带引号或单引号的匹配 (兼容压缩模式)
        root_div = bool(re.search(r'id=["\']?root["\']?', content_lower))
        checks.append(('React root div present', root_div, 'Expected <div id="root">'))

        # 4. 页面内容关键字
        keywords = ['search', 'form']
        # 兼容性匹配：panel OR accordion OR toast
        complex_ui = any(k in content_lower for k in ['panel', 'accordion', 'toast'])
        pages_found = all(k in content_lower for k in keywords) and complex_ui
        checks.append(('Pages content present', pages_found, 'Missing core UI components keywords'))

        # 5. Tailwind CSS - 检查类名特征
        tailwind_present = bool(re.search(r'\b(bg|text|dark|flex|grid)-', content_lower))
        checks.append(('Tailwind CSS classes present', tailwind_present, 'Tailwind classes not detected'))

        # 6. 负向约束：紫色 (只在 CSS 类名或 style 中检查，避免文本干扰)
        # 匹配如 class="...bg-purple-500..." 或 color:purple
        purple_usage = bool(re.search(r'["\' ]+[^"\']*purple[^"\']*["\' ]+|[: ]+purple', content_lower))
        checks.append(('No purple gradients', not purple_usage, 'Purple color usage detected in styles'))

        # 7. 负向约束：Inter 字体 (匹配 CSS 字体声明)
        inter_font = bool(re.search(r'font-family:[^;]*inter', content_lower))
        checks.append(('No Inter font usage', not inter_font, 'Inter font-family detected'))

        score = sum(1 for c in checks if c[1]) / len(checks)
        return {'passed': score >= 0.85, 'score': score, 'checks': [{'name': c[0], 'passed': c[1], 'detail': c[2]} for c in checks]}
    except Exception as e:
        return {'passed': False, 'score': 0.0, 'checks': [{'name': 'Error', 'passed': False, 'detail': str(e)}]}

def check_project_structure(workspace):
    # 保持原有结构检查，但对 routing 检查更宽松
    essential_files = ['package.json', 'tsconfig.json', 'vite.config.ts', 'src']
    checks = []
    for f in essential_files:
        exists = os.path.exists(os.path.join(workspace, f))
        checks.append((f"{f} exists", exists, f"Missing {f}"))
    
    # 只要 src 下有任何 .tsx 包含 router 或 navigate 相关词汇即可
    routing_ok = False
    src_path = os.path.join(workspace, 'src')
    if os.path.isdir(src_path):
        for r, _, files in os.walk(src_path):
            for f in files:
                if f.endswith('.tsx'):
                    try:
                        with open(os.path.join(r, f), 'r') as f_content:
                            c = f_content.read().lower()
                            if any(k in c for k in ['router', 'link', 'navigate', 'path=']):
                                routing_ok = True; break
                    except: pass
    checks.append(('Routing logic present', routing_ok, 'No routing logic found in .tsx files'))
    
    score = sum(1 for c in checks if c[1]) / len(checks)
    return {'passed': score >= 0.8, 'score': score, 'checks': [{'name': c[0], 'passed': c[1], 'detail': c[2]} for c in checks]}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    # 寻找 bundle.html
    bundle_path = None
    for r, _, files in os.walk(workspace):
        if 'bundle.html' in files:
            bundle_path = os.path.join(r, 'bundle.html'); break
    
    b_res = check_bundle_html(bundle_path) if bundle_path else {'passed': False, 'score': 0, 'checks': [{'name': 'bundle', 'passed': False, 'detail': 'bundle.html missing'}]}
    p_res = check_project_structure(workspace)
    
    overall_score = (b_res['score'] + p_res['score']) / 2
    output = {
        'passed': overall_score > 0.9,
        'score': overall_score,
        'checks': b_res['checks'] + p_res['checks']
    }
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()