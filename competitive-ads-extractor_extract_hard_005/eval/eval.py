import sys
import os
import json
import csv
import re

def find_file_case_insensitive(directory, target_name):
    """在目录中不区分大小写地查找文件，并支持常见扩展名"""
    if not os.path.isdir(directory): return None
    files = os.listdir(directory)
    # 尝试匹配 analysis.md, Analysis.md, analysis.markdown 等
    base_target = target_name.split('.')[0]
    for f in files:
        if f.lower() == target_name.lower() or \
           (f.lower().startswith(base_target) and f.lower().endswith(('.md', '.markdown'))):
            return os.path.join(directory, f)
    return None

def check_analysis_content(path):
    """鲁棒地检查 Markdown 内容"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except: return 0.0, "Read error"

    score = 0
    # 1. 检查标题是否存在（更灵活的正则）
    sections = ['overview', 'messaging', 'problem', 'format', 'cta', 'pattern', 'recommendation']
    found_sections = [s for s in sections if s in content]
    if len(found_sections) >= 5: score += 1
    
    # 2. 检查创意模式 (只要有列表项或提到模式即可)
    patterns = re.findall(r'(pattern|strategy|creative|approach|#)\s*\d*|[\-\*]\s+', content)
    if len(patterns) >= 3: score += 1
    
    return score / 2.0, f"Found sections: {found_sections}"

def validate_csv_robust(path):
    """不区分大小写地检查 CSV 列名"""
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            cols = [c.lower() for c in reader.fieldnames]
            required = ["filename", "copy", "cta", "theme", "format"]
            missing = [r for r in required if not any(r in c for c in cols)]
            return len(missing) == 0, f"Missing columns: {missing}"
    except: return False, "CSV Read error"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    required_folders = ['acme-crm', 'brighttech-solutions', 'datawise-analytics']
    all_checks = []

    for folder_name in required_folders:
        # 真正检查文件夹是否存在
        folder_path = os.path.join(workspace, folder_name)
        folder_exists = os.path.isdir(folder_path)
        
        all_checks.append({
            "name": f"Folder {folder_name} exists",
            "passed": folder_exists,
            "detail": "Folder path: " + folder_path
        })

        if folder_exists:
            # 1. 检查 Analysis.md (鲁棒查找)
            analysis_path = find_file_case_insensitive(folder_path, 'analysis.md')
            if analysis_path:
                content_score, detail = check_analysis_content(analysis_path)
                all_checks.append({"name": f"{folder_name} analysis content", "passed": content_score >= 0.5, "detail": detail})
            else:
                all_checks.append({"name": f"{folder_name} analysis file", "passed": False, "detail": "Missing analysis.md"})

            # 2. 检查 CSV
            csv_path = find_file_case_insensitive(folder_path, 'ads_data.csv')
            if csv_path:
                csv_pass, csv_detail = validate_csv_robust(csv_path)
                all_checks.append({"name": f"{folder_name} CSV valid", "passed": csv_pass, "detail": csv_detail})
            else:
                all_checks.append({"name": f"{folder_name} CSV file", "passed": False, "detail": "Missing ads_data.csv"})

            # 3. 检查图片 ( ad_001.png )
            pngs = [f for f in os.listdir(folder_path) if f.lower().endswith('.png') and 'ad_' in f.lower()]
            all_checks.append({"name": f"{folder_name} PNG count", "passed": len(pngs) > 0, "detail": f"Found {len(pngs)} images"})

    passed_count = sum(1 for c in all_checks if c['passed'])
    score = passed_count / len(all_checks) if all_checks else 0
    print(json.dumps({"passed": score >= 0.8, "score": score, "details": all_checks}, indent=2))

if __name__ == '__main__':
    main()