import os
import sys
import json
import re

def check_bundle_html(path):
    checks = []
    filepath = None
    # 查找 bundle.html
    for fname in os.listdir(path):
        if fname.lower() == 'bundle.html':
            filepath = os.path.join(path, fname)
            break
            
    if not filepath:
        return False, 0.0, [{'name': 'Bundle file existence', 'passed': False, 'detail': 'bundle.html not found'}]

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, 0.0, [{'name': 'File Reading', 'passed': False, 'detail': str(e)}]

    passed_checks = 0
    
    # Check 1: HTML tags (更宽松的正则)
    has_html_tag = bool(re.search(r'<html.*?>', content, re.I)) and bool(re.search(r'</html>', content, re.I))
    checks.append({'name': 'HTML tag presence', 'passed': has_html_tag, 'detail': 'HTML tags found' if has_html_tag else 'Missing <html> tags'})

    # Check 2: React root div (兼容压缩 HTML: id=root, id="root", id='root')
    # 同时也匹配 Vite 常见的 __vite_root__
    has_root_div = bool(re.search(r'id=["\']?(root|__vite_root__)["\']?', content))
    checks.append({'name': 'React root div presence', 'passed': has_root_div, 'detail': 'React root div found' if has_root_div else 'React root div not found'})

    # Check 3: Inline JS (检查 script 标签内是否有实际内容)
    # 不再因为存在 sourceMappingURL 而判定失败，而是检查脚本块是否达到一定长度（内联代码通常很长）
    script_blocks = re.findall(r'<script.*?>([\s\S]*?)</script>', content, re.I)
    has_significant_js = any(len(block.strip()) > 100 for block in script_blocks) 
    
    # 兼容性检查：如果脚本块较短但有 src 指向（虽然任务要求 inline，但为了鲁棒性这里只看 inline 逻辑）
    checks.append({'name': 'Inline JS presence', 'passed': has_significant_js, 'detail': 'Inline JS detected' if has_significant_js else 'No significant inline JS found'})

    for c in checks:
        if c['passed']:
            passed_checks += 1

    score = passed_checks / len(checks)
    return score == 1.0, score, checks

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': []}))
        return

    workspace_path = sys.argv[1]
    passed, score, checks = check_bundle_html(workspace_path)
    print(json.dumps({'passed': passed, 'score': score, 'details': checks}))

if __name__ == '__main__':
    main()