import os
import sys
import json
import re


def count_sentences_robust(text):
    """更鲁棒的句子计数，避免小数点被误判"""
    protected_text = text
    placeholders = []
    
    def protect_decimal(match):
        placeholders.append(match.group(0))
        return f"<<DECIMAL{len(placeholders)-1}>>"
    
    # 保护版本号和小数
    protected_text = re.sub(r'\b(?:v)?\d+\.\d+(?:\.\d+)?\b', protect_decimal, protected_text)
    protected_text = re.sub(r'\b\d+\.\d+\b', protect_decimal, protected_text)
    
    # 分割句子
    sentences = re.split(r'[.!?]+', protected_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return len(sentences)


def check_3p_format(content, filename):
    """
    检查 3P Update 格式，返回详细的检查结果列表
    每个检查项包含：name, passed, detail
    """
    checks = []
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    
    # Check 1: 文件至少有 4 行
    if len(lines) < 4:
        checks.append({
            "name": "content_length",
            "passed": False,
            "detail": f"File has only {len(lines)} non-empty lines, need at least 4"
        })
        return checks
    else:
        checks.append({
            "name": "content_length",
            "passed": True,
            "detail": f"File has {len(lines)} non-empty lines"
        })

    title_line = lines[0]
    title_line_lower = title_line.lower()

    # Check 2: 标题包含团队名称和日期范围
    expected_text = "platform engineering (2024-05-06 to 2024-05-12)"
    if expected_text in title_line_lower:
        checks.append({
            "name": "title_team_and_date",
            "passed": True,
            "detail": "Title contains 'Platform Engineering (2024-05-06 to 2024-05-12)'"
        })
    else:
        checks.append({
            "name": "title_team_and_date",
            "passed": False,
            "detail": f"Title missing team name or date range: '{title_line}'"
        })

    # Check 3: 标题以 emoji 开头（非字母数字字符）
    if title_line[0].isalnum():
        checks.append({
            "name": "emoji_at_start",
            "passed": False,
            "detail": f"Title starts with alphanumeric '{title_line[0]}', expected emoji"
        })
    else:
        checks.append({
            "name": "emoji_at_start",
            "passed": True,
            "detail": f"Title starts with emoji/symbol '{title_line[0]}'"
        })

    # Check 4-6: 查找三个 section（支持 "Progress" 或 "Progress:" 格式）
    sections = {'progress': None, 'plans': None, 'problems': None}

    for i, l in enumerate(lines):
        lower = l.lower()
        for sec in sections.keys():
            if lower.startswith(sec) or lower.startswith(sec + ':'):
                sections[sec] = i

    for sec_name, idx in sections.items():
        found = idx is not None
        checks.append({
            "name": f"section_{sec_name}_exists",
            "passed": found,
            "detail": f"{sec_name.capitalize()} section {'found at line ' + str(idx+1) if found else 'NOT found'}"
        })

    if None in sections.values():
        return checks  # 提前返回

    # Check 7: Section 顺序
    idxs = [sections['progress'], sections['plans'], sections['problems']]
    if idxs[0] < idxs[1] < idxs[2]:
        checks.append({
            "name": "section_order",
            "passed": True,
            "detail": f"Sections in correct order: Progress({idxs[0]+1}) -> Plans({idxs[1]+1}) -> Problems({idxs[2]+1})"
        })
    else:
        checks.append({
            "name": "section_order",
            "passed": False,
            "detail": f"Sections not in order. Line indices: Progress={idxs[0]+1}, Plans={idxs[1]+1}, Problems={idxs[2]+1}"
        })

    # 提取各 section 文本
    results = {}
    section_names = ['progress', 'plans', 'problems']
    for i, sec in enumerate(section_names):
        sec_line_idx = sections[sec]
        sec_line = lines[sec_line_idx]
        
        # 处理 section 标题和内容在同一行的情况（如 "Progress: content..."）
        # 或不同行的情况（如 "Progress:" 单独一行，内容在下一行）
        
        # 先检查当前行是否有内容（冒号后面）
        content_from_line = ""
        if ':' in sec_line:
            # "Progress: xxx" 格式，提取冒号后的内容
            content_from_line = sec_line.split(':', 1)[1].strip()
        
        # 查找 section 结束位置（下一个 section 或文件末尾）
        start = sec_line_idx + 1
        end = len(lines)
        for j in range(i+1, len(section_names)):
            next_sec = section_names[j]
            if sections[next_sec] > sec_line_idx:
                end = sections[next_sec]
                break
        
        # 提取后续行的内容
        following_content = ' '.join(lines[start:end]).strip()
        
        # 合并内容：如果当前行有内容，加上后续行的内容
        if content_from_line and following_content:
            sec_text = content_from_line + " " + following_content
        elif content_from_line:
            sec_text = content_from_line
        else:
            sec_text = following_content
            
        results[sec] = sec_text

    # Check 8-10: 每个 section 的句子数量（1-3句）
    for sec_name in section_names:
        text = results[sec_name]
        sentence_count = count_sentences_robust(text)
        
        if sentence_count < 1:
            checks.append({
                "name": f"{sec_name}_sentence_count",
                "passed": False,
                "detail": f"{sec_name.capitalize()}: No sentences found"
            })
        elif sentence_count > 3:
            checks.append({
                "name": f"{sec_name}_sentence_count",
                "passed": False,
                "detail": f"{sec_name.capitalize()}: Too many sentences ({sentence_count}, max 3). Text: '{text[:60]}...'"
            })
        else:
            checks.append({
                "name": f"{sec_name}_sentence_count",
                "passed": True,
                "detail": f"{sec_name.capitalize()}: {sentence_count} sentence(s)"
            })

    # Check 11: Progress 包含指标
    prog_text = results['progress']
    metric_prog = re.search(r'(\d+|%|\bbuild time\b|crash|deployment|uptime)', prog_text, re.IGNORECASE) is not None
    
    checks.append({
        "name": "progress_has_metrics",
        "passed": metric_prog,
        "detail": "Progress has numeric/metric content" if metric_prog else f"Progress lacks metrics. Text: '{prog_text[:60]}...'"
    })

    # Check 12: Plans 包含指标
    plans_text = results['plans']
    metric_plans = re.search(r'(\d+|feature|autoscaling|priority|sprint|rollout)', plans_text, re.IGNORECASE) is not None
    
    checks.append({
        "name": "plans_has_metrics",
        "passed": metric_plans,
        "detail": "Plans has numeric/metric content" if metric_plans else f"Plans lacks metrics. Text: '{plans_text[:60]}...'"
    })

    return checks


def evaluate(workspace):
    md_files = [f for f in os.listdir(workspace) if f.lower().endswith('.md')]
    
    if not md_files:
        return {
            "passed": False, 
            "score": 0.0, 
            "checks": [{"name": "file_presence", "passed": False, "detail": "No markdown (.md) files found in workspace."}]
        }

    best_score = -1.0
    best_checks = None
    best_filename = None
    all_failures = []
    
    for md_file in md_files:
        try:
            with open(os.path.join(workspace, md_file), 'r', encoding='utf-8') as f:
                content = f.read()
            
            checks = check_3p_format(content, md_file)
            passed_count = sum(1 for c in checks if c["passed"])
            total_count = len(checks)
            score = passed_count / total_count if total_count > 0 else 0.0
            
            # 添加文件名到每个检查项
            for c in checks:
                c["file"] = md_file
            
            if score == 0:
                all_failures.append(f'"{md_file}": All checks failed')
            
            if score >= best_score:
                best_score = score
                best_checks = checks
                best_filename = md_file
                
        except Exception as e:
            all_failures.append(f'"{md_file}": Error - {str(e)}')
            continue

    if best_checks is None:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "validation", "passed": False, 
                       "detail": f"All files failed: {'; '.join(all_failures)}"}]
        }
    else:
        result = {
            "passed": best_score == 1.0,
            "score": best_score,
            "checks": best_checks
        }
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    evaluate(workspace)
