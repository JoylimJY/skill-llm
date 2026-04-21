import os
import sys
import json
import re


def icontains(text, keywords):
    """Case-insensitive presence check"""
    text = text.lower()
    if isinstance(keywords, str):
        keywords = [keywords]
    return any(k.lower() in text for k in keywords)


def count_sentences(text):
    """更鲁棒的句子计数，避免小数点被误判"""
    protected_text = text
    
    def protect(match):
        return match.group(0).replace('.', '<<DOT>>')
    
    # 保护版本号和小数
    protected_text = re.sub(r'\b\d+\.\d+(?:\.\d+)?\b', protect, protected_text)
    
    sentences = re.split(r'[.!?]\s', protected_text)
    sentences = [s for s in sentences if s.strip() != '']
    return len(sentences)


def has_metrics(text):
    """
    检查文本是否包含数据驱动的内容（指标、数字、具体目标等）
    修复：更鲁棒的检测，包括动词形式和区域信息
    """
    text_lower = text.lower()
    
    # 1. 数字和百分比
    if re.search(r'\d+', text):
        return True, "Contains numeric values"
    
    # 2. 明确的量化关键词
    quantitative_keywords = [
        'percent', '%', 'percentage',
        'hours', 'days', 'weeks', 'months',
        'minutes', 'seconds',
        'number', 'count', 'total', 'sum',
        'increase', 'decrease', 'reduce', 'improve',
        'all', 'every', 'entire', 'full', 'complete',
        'scale', 'scaling', 'scaled',
        'deploy', 'deploying', 'deployed',
        'rollout', 'rolling out', 'rolled out',
        'complete', 'completing', 'completed',
        'migrate', 'migrating', 'migrated',
        'upgrade', 'upgrading', 'upgraded',
        'automate', 'automating', 'automated',
        'failover', 'capacity', 'region', 'regions',
        'cluster', 'clusters', 'node', 'nodes',
        'workload', 'workloads', 'service', 'services'
    ]
    
    found_keywords = [k for k in quantitative_keywords if k in text_lower]
    if found_keywords:
        return True, f"Found quantitative keywords: {found_keywords[:3]}"
    
    # 3. 具体目标或范围（如 EU region, all data centers）
    if re.search(r'\b(eu|us|asia|global|all|every)\s+\w+', text_lower):
        return True, "Contains specific scope or target"
    
    return False, "No clear metrics or quantitative information found"


def evaluate_3p_format(lines, filename):
    """评估 3P 格式，返回详细的检查项列表"""
    checks = []
    
    # Check 1: 文件至少有 4 行
    if len(lines) < 4:
        checks.append({
            'name': 'content_length',
            'passed': False,
            'detail': f'File has only {len(lines)} lines, need at least 4'
        })
        return checks
    else:
        checks.append({
            'name': 'content_length',
            'passed': True,
            'detail': f'File has {len(lines)} lines'
        })

    first_line = lines[0].strip()

    # Check 2: 标题行包含 emoji
    emoji_and_rest = first_line.split(' ', 1)
    if len(emoji_and_rest) != 2:
        checks.append({
            'name': 'title_has_emoji_and_content',
            'passed': False,
            'detail': 'First line missing emoji or team name'
        })
    else:
        emoji, rest = emoji_and_rest
        if emoji.isalnum():
            checks.append({
                'name': 'title_starts_with_emoji',
                'passed': False,
                'detail': f'First character "{emoji}" is alphanumeric, expected emoji'
            })
        else:
            checks.append({
                'name': 'title_starts_with_emoji',
                'passed': True,
                'detail': f'Starts with emoji "{emoji}"'
            })

    # Check 3: 团队名称
    if not icontains(first_line, 'cloud infrastructure'):
        checks.append({
            'name': 'title_team_name',
            'passed': False,
            'detail': 'Team name "Cloud Infrastructure" missing in first line'
        })
    else:
        checks.append({
            'name': 'title_team_name',
            'passed': True,
            'detail': 'Found team name "Cloud Infrastructure"'
        })

    # Check 4: 日期范围
    if not icontains(first_line, '(2024-04-15 to 2024-04-21)'):
        checks.append({
            'name': 'title_date_range',
            'passed': False,
            'detail': 'Date range (2024-04-15 to 2024-04-21) missing or malformed'
        })
    else:
        checks.append({
            'name': 'title_date_range',
            'passed': True,
            'detail': 'Found correct date range'
        })

    # Check 5-7: 三个 section 存在且格式正确
    sections = ['Progress:', 'Plans:', 'Problems:']
    for i, sec in enumerate(sections, 1):
        if i >= len(lines):
            checks.append({
                'name': f'section_{sec.lower().replace(":", "")}_exists',
                'passed': False,
                'detail': f'Missing section line for {sec}'
            })
            continue
            
        line = lines[i].strip()
        if not line.lower().startswith(sec.lower()):
            checks.append({
                'name': f'section_{sec.lower().replace(":", "")}_format',
                'passed': False,
                'detail': f'Section {sec} formatting missing or incorrect. Line: "{line[:50]}..."'
            })
        else:
            checks.append({
                'name': f'section_{sec.lower().replace(":", "")}_format',
                'passed': True,
                'detail': f'Section {sec} found at line {i+1}'
            })

    # Check 8-10: 每个 section 的句子数量（1-3句）
    for i, sec in enumerate(sections, 1):
        sec_name = sec.lower().replace(':', '')
        
        if i >= len(lines):
            checks.append({
                'name': f'{sec_name}_sentence_count',
                'passed': False,
                'detail': f'No content for {sec}'
            })
            continue
            
        line = lines[i].strip()
        if not line.lower().startswith(sec.lower()):
            continue
            
        content = line[len(sec):].strip()
        sentence_count = count_sentences(content)
        
        if not (1 <= sentence_count <= 3):
            checks.append({
                'name': f'{sec_name}_sentence_count',
                'passed': False,
                'detail': f'{sec} has {sentence_count} sentences (expected 1-3). Content: "{content[:60]}..."'
            })
        else:
            checks.append({
                'name': f'{sec_name}_sentence_count',
                'passed': True,
                'detail': f'{sec} has {sentence_count} sentence(s)'
            })

    return checks


def evaluate_content_quality(lines):
    """评估内容质量，返回详细的检查项列表"""
    checks = []
    
    if len(lines) < 4:
        return checks
    
    progress = lines[1][len('Progress:'):].strip() if lines[1].lower().startswith('progress:') else ''
    plans = lines[2][len('Plans:'):].strip() if lines[2].lower().startswith('plans:') else ''
    problems = lines[3][len('Problems:'):].strip() if lines[3].lower().startswith('problems:') else ''

    # Check 11: Progress 包含指标
    progress_has_metrics, progress_detail = has_metrics(progress)
    checks.append({
        'name': 'progress_has_metrics',
        'passed': progress_has_metrics,
        'detail': progress_detail if progress_has_metrics else f'{progress_detail}. Content: "{progress[:60]}..."'
    })

    # Check 12: Plans 包含指标
    plans_has_metrics, plans_detail = has_metrics(plans)
    checks.append({
        'name': 'plans_has_metrics',
        'passed': plans_has_metrics,
        'detail': plans_detail if plans_has_metrics else f'{plans_detail}. Content: "{plans[:60]}..."'
    })

    # Check 13: Problems 描述问题/阻塞
    problem_keywords = ['delay', 'issue', 'slow', 'block', 'problem', 'push', 'postpone', 'defer', 'wait', 'pending']
    problems_has_issues = any(k in problems.lower() for k in problem_keywords)
    
    found_keywords = [k for k in problem_keywords if k in problems.lower()]
    checks.append({
        'name': 'problems_describes_blockers',
        'passed': problems_has_issues,
        'detail': f'Found blocker keywords: {found_keywords[:3]}' if problems_has_issues else f'No blocker keywords found. Content: "{problems[:60]}..."'
    })

    # Check 14: 语气是 matter-of-fact
    casual_phrases = ['hope', 'think', 'maybe', 'wish', 'could', 'might', 'possibly']
    combined_text = (progress + plans + problems).lower()
    tone_ok = not any(p in combined_text for p in casual_phrases)
    
    found_casual = [p for p in casual_phrases if p in combined_text]
    checks.append({
        'name': 'tone_is_matter_of_fact',
        'passed': tone_ok,
        'detail': 'Tone is professional' if tone_ok else f'Found casual phrases: {found_casual}'
    })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'

    # Find all .md files or text files
    candidates = []
    for fname in os.listdir(workspace):
        if fname.lower().endswith('.md') or fname.lower().endswith('.txt'):
            candidates.append(fname)

    if not candidates:
        candidates = os.listdir(workspace)

    best_score = -1.0
    best_checks = []
    best_passed = False
    best_file = None

    for fname in candidates:
        fpath = os.path.join(workspace, fname)
        try:
            with open(fpath, 'r', encoding='utf8') as f:
                content = f.read()

            lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
            
            # 收集所有检查项
            checks = evaluate_3p_format(lines, fname)
            
            # 只有格式检查通过才进行内容质量检查
            format_passed = all(c['passed'] for c in checks if c['name'].startswith(('content_length', 'title_', 'section_', '_sentence_count')))
            
            if format_passed:
                quality_checks = evaluate_content_quality(lines)
                checks.extend(quality_checks)

            # 为每个检查项添加文件名
            for c in checks:
                c['file'] = fname
            
            passed = all(c['passed'] for c in checks)
            score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0

            if score >= best_score:
                best_score = score
                best_checks = checks
                best_passed = passed
                best_file = fname

        except Exception as e:
            continue

    if best_file is None:
        result = {
            'passed': False,
            'score': 0.0,
            'checks': [{'name': 'file_presence', 'passed': False, 'detail': 'No suitable output file found.'}]
        }
    else:
        result = {
            'passed': best_passed,
            'score': best_score,
            'checks': best_checks
        }

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
