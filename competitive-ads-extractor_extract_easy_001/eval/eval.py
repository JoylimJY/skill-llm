import os
import sys
import json
import re

def check_screenshots(path):
    ads_folder = os.path.join(path, 'acmecorp-ads')
    if not os.path.isdir(ads_folder):
        return False, 'Missing folder acmecorp-ads'
    files = os.listdir(ads_folder)
    png_files = [f for f in files if f.lower().endswith('.png')]
    if len(png_files) < 2:
        return False, f'Less than 2 PNG screenshot files found. Found: {png_files}'
    return True, 'Screenshots folder and files correct'

def check_markdown_report(path):
    # 路径匹配增强
    md_path = os.path.join(path, 'acmecorp-analysis.md')
    if not os.path.exists(md_path):
        return False, 'No analysis markdown file named acmecorp-analysis.md found'

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            text = f.read()
            text_lower = text.lower()
    except Exception as e:
        return False, f'Error reading file: {e}'

    # 1-4. 核心标题检查
    checks = [
        'overview' in text_lower,
        'key problems' in text_lower,
        'successful creative patterns' in text_lower,
        'recommendations' in text_lower
    ]

    # 辅助函数：提取两个二级标题之间的内容，防止被 \n\n 意外截断
    def extract_section(section_name, content):
        # 寻找当前标题到下一个二级标题（##）或文件末尾的内容
        pattern = rf'##\s*{section_name}.*?(?=##|$)'
        match = re.search(pattern, content, re.I | re.S)
        return match.group(0) if match else ""

    # 5. 检查问题数量 (支持 ###, 1., -, 或者粗体开头的段落)
    prob_content = extract_section('Key Problems', text)
    # 匹配三级标题、列表项或数字列表
    prob_items = re.findall(r'(###|^\s*[\-\*\d\.]+|^\s*\*\*)', prob_content, re.M)
    checks.append(len(prob_items) >= 2)

    # 6. 检查创意模式数量
    creative_content = extract_section('Successful Creative Patterns', text)
    creative_items = re.findall(r'(###|^\s*[\-\*\d\.]+|^\s*\*\*)', creative_content, re.M)
    checks.append(len(creative_items) >= 2)

    score = sum(1 for c in checks if c) / len(checks)
    detail = f"Markdown checks: {checks} (Found {len(prob_items)} problems, {len(creative_items)} patterns)"
    
    # 只要分数达到 1.0 (即全部通过) 才返回 True
    return score == 1.0, detail

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    passed_scr, det_scr = check_screenshots(workspace)
    passed_md, det_md = check_markdown_report(workspace)
    
    # 构建符合格式的最终输出
    results = [
        {"name": "Screenshots folder and files", "passed": passed_scr, "detail": det_scr},
        {"name": "Analysis markdown completeness", "passed": passed_md, "detail": det_md}
    ]
    
    score = sum(1 for r in results if r['passed']) / len(results)
    print(json.dumps({
        "passed": score == 1.0,
        "score": score,
        "details": results
    }, indent=2))

if __name__ == '__main__':
    main()