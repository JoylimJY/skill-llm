import sys
import json
import re
import os
from pathlib import Path

def find_output_file(workspace):
    """Find the lookup_report.md file anywhere in workspace."""
    candidates = list(Path(workspace).rglob("lookup_report.md"))
    if candidates:
        return candidates[0]
    return None

def is_traditional_chinese(text):
    """
    Check for Traditional Chinese characters that differ from Simplified.
    Key markers: 說/说, 們/们, 這/这, 個/个, 來/来, 點/点, 時/时, 電/电, 體/体, 國/国
    Also check for common Traditional-only chars used in the mock data.
    """
    traditional_markers = ['說', '們', '這', '個', '來', '點', '時', '電', '體', '國',
                            '專', '愛', '發', '從', '對', '為', '裡', '當', '後', '開',
                            '關', '應', '義', '業', '舊', '廠', '歷', '辦', '寫', '數',
                            '無', '強', '雖', '義', '飾', '職', '跡', '轉', '戀', '難',
                            '學', '師', '臨', '繼', '遊', '鄰', '暫', '択', '達', '億',
                            '線', '離', '隣', '獨', '長', '實', '際', '幕', '緒', '夢',
                            '雙', '選', '錯', '讓', '壓', '調', '戲', '節']
    simplified_markers = ['说', '们', '这', '个', '来', '点', '时', '电', '体', '国',
                          '专', '爱', '发', '从', '对', '为', '里', '当', '后', '开',
                          '关', '应', '义', '业', '旧', '厂', '历', '办', '写', '数']
    
    trad_count = sum(1 for c in traditional_markers if c in text)
    simp_count = sum(1 for c in simplified_markers if c in text)
    
    # Has traditional characters and few/no simplified-only ones
    return trad_count >= 2 and simp_count <= 1

def check_plot_length(plot_text):
    """Check if plot is between 20-50 Chinese characters (excluding punctuation for leniency)."""
    # Remove table separators and extra whitespace
    cleaned = re.sub(r'[\s\|]', '', plot_text)
    # Count CJK characters
    cjk_count = sum(1 for c in cleaned if '\u4e00' <= c <= '\u9fff')
    return 20 <= len(cleaned) <= 70  # lenient: 20-70 total chars

def extract_table_rows(content):
    """Extract rows from the markdown table."""
    rows = []
    lines = content.split('\n')
    in_table = False
    header_found = False
    
    for line in lines:
        line = line.strip()
        if '|' in line and ('番號' in line or '番号' in line or '主演' in line):
            in_table = True
            header_found = True
            continue
        if header_found and re.match(r'^\|[-| ]+\|$', line):
            continue  # separator line
        if in_table and line.startswith('|') and line.endswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) >= 3:
                rows.append(cells)
        elif in_table and not line.startswith('|') and line:
            # End of table
            in_table = False
            header_found = False
    
    return rows

def find_code_row(rows, code):
    """Find a row containing the given code."""
    for row in rows:
        for cell in row:
            if code.upper() in cell.upper() or code.replace('-', '') in cell.replace('-', '').upper():
                return row
    return None

def check_magnet_format(magnet_str):
    """Check if magnet link follows correct format."""
    pattern = r'magnet:\?xt=urn:btih:[A-Fa-f0-9]{40}(&dn=[^&\s|]+)?'
    return bool(re.search(pattern, magnet_str))

def run_evaluation(workspace):
    checks = []
    total_score = 0.0
    max_checks = 0

    # --- Check 1: Output file exists ---
    output_file = find_output_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "output_file_lookup_report_md_exists",
        "passed": file_exists,
        "detail": f"File found at: {output_file}" if file_exists else "lookup_report.md not found anywhere in workspace"
    })
    
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = output_file.read_text(encoding='utf-8')
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # --- Check 2: Contains a Markdown table ---
    has_table = '|' in content and ('---' in content or '——' in content or '====' in content or re.search(r'\|[-\s]+\|', content))
    checks.append({
        "name": "contains_markdown_table",
        "passed": has_table,
        "detail": "Markdown table with pipe separators found" if has_table else "No valid markdown table found"
    })

    # --- Check 3: All 5 番号 codes present ---
    codes = ["ABF-328", "JUR-067", "MIDA-563", "START-510", "SSIS-592"]
    missing_codes = []
    for code in codes:
        if code not in content and code.replace('-', '') not in content.replace('-', ''):
            missing_codes.append(code)
    codes_present = len(missing_codes) == 0
    checks.append({
        "name": "all_five_codes_present",
        "passed": codes_present,
        "detail": f"All codes present" if codes_present else f"Missing codes: {missing_codes}"
    })

    # --- Check 4: Correct studios from prefix table ---
    studio_map = {
        "ABF-328": ["Prestige", "prestige"],
        "JUR-067": ["Madonna", "madonna"],
        "MIDA-563": ["MOODYZ", "moodyz", "Moodyz"],
        "START-510": ["SOD", "SOD Create", "sod"],
        "SSIS-592": ["S1", "S1 No.1", "s1"],
    }
    
    studios_correct = []
    studios_wrong = []
    for code, valid_studios in studio_map.items():
        found = any(s.lower() in content.lower() for s in valid_studios)
        if found:
            studios_correct.append(code)
        else:
            studios_wrong.append(code)
    
    studios_pass = len(studios_correct) >= 4
    checks.append({
        "name": "correct_studios_from_prefix_table",
        "passed": studios_pass,
        "detail": f"Correct: {studios_correct}, Wrong/Missing: {studios_wrong}"
    })

    # --- Check 5: Correct cast for all codes ---
    cast_map = {
        "ABF-328": ["涼森玲夢", "涼森れむ", "凉森玲梦"],
        "JUR-067": ["久遠美緒", "久遠みお", "久远美绪"],
        "MIDA-563": ["三上悠亞", "三上悠亜", "三上悠亚"],
        "START-510": ["葵つかさ", "葵つかさ", "葵"],
        "SSIS-592": ["八木奈々", "八木奈奈", "八木奈々"],
    }
    
    cast_correct = []
    cast_wrong = []
    for code, valid_casts in cast_map.items():
        found = any(c in content for c in valid_casts)
        if found:
            cast_correct.append(code)
        else:
            cast_wrong.append(code)
    
    cast_pass = len(cast_correct) >= 4
    checks.append({
        "name": "correct_cast_for_all_codes",
        "passed": cast_pass,
        "detail": f"Correct: {cast_correct}, Wrong/Missing: {cast_wrong}"
    })

    # --- Check 6: Traditional Chinese used (not Simplified) ---
    trad_markers_found = []
    trad_check_chars = ['暫', '無', '飾', '戀', '職', '轉', '繼', '獨', '緒', '難', '錯', '強', '學', '線', '實']
    simp_check_chars = ['暂', '饰', '恋', '职', '转', '继', '独', '错', '强', '学', '线', '实']
    
    trad_count = sum(1 for c in trad_check_chars if c in content)
    simp_count = sum(1 for c in simp_check_chars if c in content)
    
    # Also check specific known traditional phrases from mock data
    known_trad = ['飾演', '暫無特殊版本', '戀情', '難忘', '轉學', '職場', '獨守', '長期']
    known_simp = ['饰演', '恋情', '难忘', '转学', '职场', '独守', '长期']
    
    trad_phrase_count = sum(1 for p in known_trad if p in content)
    simp_phrase_count = sum(1 for p in known_simp if p in content)
    
    uses_traditional = (trad_count >= 2 or trad_phrase_count >= 1) and simp_phrase_count == 0
    checks.append({
        "name": "output_uses_traditional_chinese",
        "passed": uses_traditional,
        "detail": f"Traditional markers found: {trad_count}, trad phrases: {trad_phrase_count}, Simplified markers: {simp_count}, simp phrases: {simp_phrase_count}"
    })

    # --- Check 7: Magnet links present with correct format ---
    magnet_pattern = r'magnet:\?xt=urn:btih:[A-Fa-f0-9]{40}'
    magnets_found = re.findall(magnet_pattern, content)
    has_magnets = len(magnets_found) >= 3  # Should have at least 3 (one per code that has them)
    checks.append({
        "name": "magnet_links_present_correct_format",
        "passed": has_magnets,
        "detail": f"Found {len(magnets_found)} valid magnet links (need >= 3)"
    })

    # --- Check 8: Magnet links include dn= parameter ---
    dn_pattern = r'magnet:\?xt=urn:btih:[A-Fa-f0-9]{40}&dn=[^\s|]+'
    magnets_with_dn = re.findall(dn_pattern, content)
    has_dn = len(magnets_with_dn) >= 2
    checks.append({
        "name": "magnet_links_include_dn_parameter",
        "passed": has_dn,
        "detail": f"Found {len(magnets_with_dn)} magnet links with dn= parameter"
    })

    # --- Check 9: -c version flagged for codes that have it (ABF-328, MIDA-563, SSIS-592) ---
    codes_with_c = ["ABF-328", "MIDA-563", "SSIS-592"]
    c_version_notes = []
    
    # Check if -c magnets are used (larger file size versions)
    # ABF-328-C hash: B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3
    # MIDA-563-C hash: E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6
    # SSIS-592-C hash: 3C4D5E6F1A2B3C4D5E6F1A2B3C4D5E6F1A2B3C4D
    c_hashes = [
        "B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3",
        "E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6",
        "3C4D5E6F1A2B3C4D5E6F1A2B3C4D5E6F1A2B3C4D",
        "F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1",  # MIDA-563-UC
    ]
    
    c_magnets_used = sum(1 for h in c_hashes if h.upper() in content.upper() or h.lower() in content.lower())
    
    # Also check for -c notation in remarks
    c_notation = ('-c' in content.lower() or '中文字幕' in content or '中字' in content)
    
    c_version_pass = c_magnets_used >= 2 or c_notation
    checks.append({
        "name": "c_version_magnets_prioritized_or_noted",
        "passed": c_version_pass,
        "detail": f"-c version hashes found: {c_magnets_used}, -c notation in content: {c_notation}"
    })

    # --- Check 10: JUR-067 has no -c version, should note "暫無特殊版本" or similar ---
    jur_section = ""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'JUR-067' in line or 'JUR067' in line:
            # Get surrounding context
            start = max(0, i-1)
            end = min(len(lines), i+3)
            jur_section = '\n'.join(lines[start:end])
            break
    
    # JUR-067 has no -c version
    no_special_noted = (
        '暫無特殊版本' in jur_section or 
        '暂无特殊版本' in jur_section or
        '无特殊版本' in jur_section or
        '暫無' in jur_section or
        'no special' in jur_section.lower() or
        '無特殊' in jur_section
    )
    # Also acceptable: JUR-067 row just has no -c magnet (check that -c hash is NOT near JUR)
    jur_c_hash_absent = "B2C3" not in jur_section  # That's ABF's -c hash
    
    checks.append({
        "name": "jur067_no_c_version_noted",
        "passed": no_special_noted or jur_c_hash_absent,
        "detail": f"JUR-067 section: '{jur_section[:200]}...'" if jur_section else "JUR-067 section not found"
    })

    # --- Check 11: START-510 has no -c version noted ---
    start_section = ""
    for i, line in enumerate(lines):
        if 'START-510' in line or 'START510' in line:
            start = max(0, i-1)
            end = min(len(lines), i+3)
            start_section = '\n'.join(lines[start:end])
            break
    
    start_no_c = '暫無特殊版本' in start_section or '暂无' in start_section or '無特殊' in start_section or start_section != ""
    # Main check: START-510 correct hash (1A2B3C...) should appear, not a -c hash
    start_correct_hash = "1A2B3C4D5E6F1A2B3C4D5E6F1A2B3C4D5E6F1A2B".lower() in content.lower()
    checks.append({
        "name": "start510_present_with_correct_or_no_c_version",
        "passed": start_section != "" or start_correct_hash,
        "detail": f"START-510 section found: {bool(start_section)}, correct hash: {start_correct_hash}"
    })

    # --- Check 12: Plot summaries for each code present and not empty ---
    # Check that rows have meaningful plot text (not just dashes or empty)
    rows = extract_table_rows(content)
    plots_found = 0
    for row in rows:
        # Plot should be the 5th column (index 4) in a 5+ column table
        if len(row) >= 4:
            plot_cell = row[-1] if len(row) == 5 else (row[4] if len(row) > 4 else row[3])
            if len(plot_cell.strip()) > 15:
                plots_found += 1
    
    plots_pass = plots_found >= 3
    checks.append({
        "name": "plot_summaries_populated",
        "passed": plots_pass,
        "detail": f"Found {plots_found} rows with non-empty plot summaries (need >= 3)"
    })

    # --- Check 13: Correct table column structure ---
    # Must have at minimum: 番號, 主演, 片商, 一句話劇情, 磁力
    required_headers = ['番號', '主演', '片商']
    alt_headers = ['番号', '番碼', 'code', 'Code', 'cast', 'Cast']
    
    has_code_header = any(h in content for h in ['番號', '番号', '番碼', '# |', '#|'])
    has_cast_header = '主演' in content
    has_studio_header = '片商' in content
    has_plot_header = '劇情' in content or '剧情' in content or '故事' in content or '简介' in content or '簡介' in content
    has_magnet_header = '磁力' in content or 'magnet' in content.lower() or 'Magnet' in content
    
    header_score = sum([has_code_header, has_cast_header, has_studio_header, has_plot_header, has_magnet_header])
    headers_pass = header_score >= 4
    checks.append({
        "name": "correct_table_headers",
        "passed": headers_pass,
        "detail": f"Headers found: code={has_code_header}, cast={has_cast_header}, studio={has_studio_header}, plot={has_plot_header}, magnet={has_magnet_header} ({header_score}/5)"
    })

    # --- Calculate final score ---
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # Must pass critical checks to overall pass
    critical_checks = [
        "output_file_lookup_report_md_exists",
        "all_five_codes_present",
        "correct_cast_for_all_codes",
        "magnet_links_present_correct_format",
        "output_uses_traditional_chinese",
    ]
    
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_evaluation(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))