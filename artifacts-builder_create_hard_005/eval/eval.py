import sys
import os
import re
import json
from pathlib import Path

def check_offline_bundle(bundle_path):
    """验证 bundle.html 是否为真正的离线单文件"""
    try:
        with open(bundle_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"无法读取 bundle.html: {str(e)}"

    if not ('<html' in content.lower() and '<body' in content.lower()):
        return False, "bundle.html 缺少基本的 HTML/BODY 标签"

    # 检查是否依赖外部 JS (排除内联脚本和 data: URIs)
    if re.search(r'<script[^>]+src=["\'](http|//)', content, re.IGNORECASE):
        return False, "bundle.html 包含了外部 script 引用，未能完全内联打包"
    
    # 检查是否依赖外部 CSS
    if re.search(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\'](http|//)', content, re.IGNORECASE):
        return False, "bundle.html 包含了外部 stylesheet 引用"

    if not ('id="root"' in content or 'id="app"' in content):
        return False, "bundle.html 缺少 React root 挂载点"

    return True, "bundle.html 符合完全离线单文件规范"

def analyze_source_code(workspace_path: Path):
    """静态分析 React 源码，检查是否使用了要求的依赖和组件"""
    project_dir = workspace_path / 'multi-component-dashboard'
    
    # 容错：如果大模型没有建文件夹而是直接在根目录生成
    if not project_dir.exists():
        if (workspace_path / 'package.json').exists():
            project_dir = workspace_path
        else:
            return False, "未找到名为 multi-component-dashboard 的项目结构或 package.json"

    combined_tsx_code = ""
    package_json_content = ""
    
    # 遍历项目文件
    for root, _, files in os.walk(project_dir):
        if 'node_modules' in root or 'dist' in root:
            continue
        for file in files:
            file_path = os.path.join(root, file)
            if file == 'package.json':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        package_json_content = f.read()
                except:
                    pass
            elif file.endswith(('.tsx', '.ts', '.jsx')):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        combined_tsx_code += f.read() + "\n"
                except:
                    pass

    checks = []

    # 1. 检查路由 (React Router DOM)
    has_router = 'react-router-dom' in package_json_content or 'react-router-dom' in combined_tsx_code
    checks.append({"name": "使用了 React Router", "passed": has_router, "detail": "代码中找到了 react-router-dom 的使用"})

    # 2. 检查表单验证 (react-hook-form)
    has_hook_form = 'react-hook-form' in package_json_content or 'useForm' in combined_tsx_code
    checks.append({"name": "使用了表单验证", "passed": has_hook_form, "detail": "代码中找到了 react-hook-form 的使用"})

    # 3. 检查 Shadcn UI 组件使用情况
    required_components = ['Accordion', 'Tabs', 'Card', 'Button', 'Dialog', 'Input', 'Checkbox', 'Switch']
    missing_components = [comp for comp in required_components if comp not in combined_tsx_code]
    components_passed = len(missing_components) == 0
    checks.append({
        "name": "使用了要求的 shadcn/ui 组件", 
        "passed": components_passed, 
        "detail": "所有要求的组件均已使用" if components_passed else f"缺失以下组件: {', '.join(missing_components)}"
    })

    # 4. 检查 TailwindCSS 响应式布局 (侧面验证横向三卡片布局)
    # 寻找常用的网格/弹性布局类名
    has_responsive_layout = bool(re.search(r'(grid-cols-[3-4]|flex|md:grid|lg:grid)', combined_tsx_code))
    checks.append({"name": "存在 Tailwind 响应式布局", "passed": has_responsive_layout, "detail": "代码中包含 grid/flex 布局类名"})

    # 5. 检查双页面结构
    has_pages = bool(re.search(r'path=["\']/?settings["\']', combined_tsx_code)) or ('Settings' in combined_tsx_code and 'Dashboard' in combined_tsx_code)
    checks.append({"name": "存在 Dashboard 和 Settings 页面结构", "passed": has_pages, "detail": "找到了相关页面的代码映射"})

    return True, checks

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Expected workspace path argument"}]}))
        return

    workspace = Path(sys.argv[1])
    all_checks = []

    # --- 阶段 1：检查打包产物 bundle.html ---
    bundle_path = workspace / 'bundle.html'
    bundle_exists = bundle_path.is_file()
    all_checks.append({"name": "根目录存在 bundle.html", "passed": bundle_exists, "detail": "找到了 bundle.html" if bundle_exists else "未在根目录找到 bundle.html"})

    if bundle_exists:
        offline_passed, offline_detail = check_offline_bundle(bundle_path)
        all_checks.append({"name": "bundle.html 离线内联验证", "passed": offline_passed, "detail": offline_detail})
    else:
        all_checks.append({"name": "bundle.html 离线内联验证", "passed": False, "detail": "文件不存在，跳过验证"})

    # --- 阶段 2：检查源码逻辑 ---
    source_status, source_checks_or_err = analyze_source_code(workspace)
    if source_status:
        all_checks.extend(source_checks_or_err)
    else:
        all_checks.append({"name": "源码结构分析", "passed": False, "detail": source_checks_or_err})

    # --- 计算最终得分 ---
    passed_checks = sum(1 for c in all_checks if c["passed"])
    score = passed_checks / len(all_checks) if all_checks else 0.0
    
    # 考虑到大模型生成代码的多样性，得分达到 0.8 以上即可认为通过 (Passed)
    passed_overall = score >= 0.8

    print(json.dumps({"passed": passed_overall, "score": score, "checks": all_checks}, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()