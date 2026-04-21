import sys
import os
import json
import re


def count_sentences(text):
    """
    更鲁棒的句子计数函数
    正确处理：
    - 小数（4.2, 98.5%）
    - 版本号（iOS 4.2, v1.0.0）
    - 日期缩写（Mar. 15）
    """
    protected_text = text
    placeholders = []
    
    def protect_decimal(match):
        placeholders.append(match.group(0))
        return f"<<DECIMAL{len(placeholders)-1}>>"
    
    # 保护版本号格式（如 iOS 4.2, Android 12.0, v2.1.0）
    protected_text = re.sub(r'\b(?:iOS|Android|v)?\d+\.\d+(?:\.\d+)?\b', protect_decimal, protected_text)
    # 保护独立的小数（如 4.7, 98.5）
    protected_text = re.sub(r'\b\d+\.\d+\b', protect_decimal, protected_text)
    
    # 现在安全地按句子结束符分割
    sents = re.split(r'[.!?]+', protected_text)
    sents = [s.strip() for s in sents if s.strip()]
    
    return len(sents)


def check_3p_format(text, filename):
    """
    检查 3P Update 格式，返回详细的检查结果列表
    每个检查项包含：name, passed, detail
    """
    checks = []
    lines = [line.strip() for line in text.splitlines() if line.strip() != '']
    
    # Check 1: 文件至少有 4 行非空内容
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

    first_line = lines[0]

    # Check 2: 标题行以 emoji 开头
    first_char = first_line[0]
    if ord(first_char) < 128:
        checks.append({
            "name": "emoji_at_start",
            "passed": False,
            "detail": f"First character '{first_char}' is ASCII, expected emoji"
        })
    else:
        checks.append({
            "name": "emoji_at_start",
            "passed": True,
            "detail": f"First character is emoji '{first_char}'"
        })

    # Check 3: 标题行包含括号和日期
    paren_match = re.search(r"\([^)]+\)", first_line)
    if not paren_match:
        checks.append({
            "name": "date_in_parentheses",
            "passed": False,
            "detail": "No parentheses found in title line"
        })
    else:
        paren_content = paren_match.group(0).lower()
        if "march 1-7, 2024" not in paren_content:
            checks.append({
                "name": "date_in_parentheses",
                "passed": False,
                "detail": f"Expected 'March 1-7, 2024', found '{paren_match.group(0)}'"
            })
        else:
            checks.append({
                "name": "date_in_parentheses",
                "passed": True,
                "detail": "Found correct date 'March 1-7, 2024' in parentheses"
            })

    # Check 4: 标题行包含团队名称
    if 'mobile team' not in first_line.lower():
        checks.append({
            "name": "team_name",
            "passed": False,
            "detail": f"Title line does not contain 'Mobile Team': '{first_line}'"
        })
    else:
        checks.append({
            "name": "team_name",
            "passed": True,
            "detail": "Found team name 'Mobile Team'"
        })

    # Check 5: 查找三个 section
    progress_line_idx = None
    plans_line_idx = None
    problems_line_idx = None

    for i, line in enumerate(lines):
        l = line.lower()
        if l.startswith('progress:'):
            progress_line_idx = i
        elif l.startswith('plans:'):
            plans_line_idx = i
        elif l.startswith('problems:'):
            problems_line_idx = i

    sections_found = {
        "Progress": progress_line_idx is not None,
        "Plans": plans_line_idx is not None,
        "Problems": problems_line_idx is not None
    }
    
    for sec_name, found in sections_found.items():
        checks.append({
            "name": f"section_{sec_name.lower()}_exists",
            "passed": found,
            "detail": f"{sec_name}: section {'found' if found else 'NOT found'}"
        })

    if None in [progress_line_idx, plans_line_idx, problems_line_idx]:
        return checks  # 提前返回，因为后续检查需要这些 section

    # Check 6: Section 顺序是否正确
    idxs = [progress_line_idx, plans_line_idx, problems_line_idx]
    if idxs[0] < idxs[1] < idxs[2]:
        checks.append({
            "name": "section_order",
            "passed": True,
            "detail": "Sections in correct order: Progress -> Plans -> Problems"
        })
    else:
        checks.append({
            "name": "section_order",
            "passed": False,
            "detail": f"Sections not in order. Line indices: Progress={progress_line_idx}, Plans={plans_line_idx}, Problems={problems_line_idx}"
        })

    # 提取各 section 文本
    def get_section_text(start_idx, end_idx):
        first_line_section = lines[start_idx]
        colon_pos = first_line_section.find(':')
        section_text = first_line_section[colon_pos + 1:].strip()
        if end_idx is None:
            section_text += ' ' + ' '.join(lines[start_idx + 1:])
        else:
            section_text += ' ' + ' '.join(lines[start_idx + 1:end_idx])
        return section_text.strip()

    sections = {}
    sections['Progress'] = get_section_text(progress_line_idx, 
        plans_line_idx if progress_line_idx < plans_line_idx else problems_line_idx)
    
    if plans_line_idx < problems_line_idx:
        sections['Plans'] = get_section_text(plans_line_idx, problems_line_idx)
        sections['Problems'] = get_section_text(problems_line_idx, None)
    else:
        sections['Plans'] = get_section_text(plans_line_idx, None)
        sections['Problems'] = get_section_text(problems_line_idx, None)

    # Check 7-9: 每个 section 的句子数量
    for key in ['Progress', 'Plans', 'Problems']:
        sent_count = count_sentences(sections[key])
        word_count = len(sections[key].split())
        
        if sent_count < 1:
            checks.append({
                "name": f"{key.lower()}_sentence_count",
                "passed": False,
                "detail": f"{key}: No sentences found (text: '{sections[key][:50]}...')"
            })
        elif sent_count > 3:
            checks.append({
                "name": f"{key.lower()}_sentence_count",
                "passed": False,
                "detail": f"{key}: Too many sentences ({sent_count}, max 3). Text: '{sections[key][:50]}...'"
            })
        elif word_count > 80:
            checks.append({
                "name": f"{key.lower()}_sentence_count",
                "passed": False,
                "detail": f"{key}: Too long ({word_count} words, max ~80)"
            })
        else:
            checks.append({
                "name": f"{key.lower()}_sentence_count",
                "passed": True,
                "detail": f"{key}: {sent_count} sentences, {word_count} words"
            })

    # Check 10-11: Progress 和 Plans 是否包含数字指标
    progress_has_num = bool(re.search(r'\d', sections['Progress']))
    plans_has_num = bool(re.search(r'\d', sections['Plans']))

    checks.append({
        "name": "progress_has_metrics",
        "passed": progress_has_num,
        "detail": "Progress has numeric metrics" if progress_has_num else "Progress lacks numeric metrics (e.g., 15%, 98%, etc.)"
    })

    checks.append({
        "name": "plans_has_metrics",
        "passed": plans_has_num,
        "detail": "Plans has numeric metrics" if plans_has_num else "Plans lacks numeric metrics"
    })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'

    # 查找所有候选文件
    candidates = [f for f in os.listdir(workspace) 
                  if f.lower().endswith('.md') and '3p-update' in f.lower()]

    if not candidates:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_presence", "passed": False, 
                       "detail": "No markdown file with '3p-update' in name found"}]
        }
        print(json.dumps(result, indent=2))
        return

    best_score = -1.0
    best_checks = None
    best_filename = None
    all_failures = []

    for filename in candidates:
        filepath = os.path.join(workspace, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            checks = check_3p_format(content, filename)
            passed_count = sum(1 for c in checks if c["passed"])
            total_count = len(checks)
            score = passed_count / total_count if total_count > 0 else 0.0
            
            # 添加文件名到每个检查项
            for c in checks:
                c["file"] = filename
            
            if not any(c["passed"] for c in checks):
                all_failures.append(f"{filename}: All checks failed")
            
            if score > best_score:
                best_score = score
                best_checks = checks
                best_filename = filename
                
        except Exception as e:
            all_failures.append(f"{filename}: Error - {str(e)}")
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
    main()
