#!/usr/bin/env python3
"""
Evaluation script for the novel-writer-agent task.
Checks:
1. novel_outline.md exists and contains all required outline modules (4-act structure, 5 modules)
2. chapter_01.md, chapter_02.md, chapter_03.md exist and meet word count ≥2000 Chinese chars
3. Chapter 1: main conflict appears within first 500 chars
4. Chapter 2: worldbuilding + ability/system content
5. Chapter 3: 打脸/爽点 content
6. All 3 chapters end with a hook (悬念/冲突/期待 indicator)
7. qc_report.json: weighted scoring schema, scores ≥80 per chapter, sensitive_words=0
"""
import sys
import json
import re
from pathlib import Path

def count_chinese_chars(text):
    """Count Chinese characters (CJK Unified Ideographs)."""
    return len(re.findall(r'[\u4e00-\u9fff]', text))

def find_file(workspace, filename):
    """Search recursively for a file by name."""
    results = list(Path(workspace).rglob(filename))
    if results:
        return results[0]
    return None

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(0)

    workspace = Path(sys.argv[1])
    checks = []
    total_weight = 0.0
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_weight, total_score
        total_weight += weight
        if passed:
            total_score += weight

    # =========================================================
    # CHECK 1: novel_outline.md existence
    # =========================================================
    outline_file = find_file(workspace, "novel_outline.md")
    if outline_file is None:
        add_check("outline_exists", False, "novel_outline.md not found anywhere in workspace", weight=2.0)
        outline_text = ""
    else:
        outline_text = outline_file.read_text(encoding="utf-8", errors="replace")
        add_check("outline_exists", True, f"Found at {outline_file}", weight=2.0)

    # CHECK 2: 4-act structure with chapter ranges
    act_patterns = [
        (r'第一幕|第1幕|Act\s*1|act\s*one', r'1[-–]10|1\s*[-–]\s*10'),
        (r'第二幕|第2幕|Act\s*2|act\s*two', r'11[-–]30|11\s*[-–]\s*30'),
        (r'第三幕|第3幕|Act\s*3|act\s*three', r'31[-–]40|31\s*[-–]\s*40'),
        (r'第四幕|第4幕|Act\s*4|act\s*four', r'41[-–]50|41\s*[-–]\s*50'),
    ]
    act_found = []
    for act_re, chapter_re in act_patterns:
        has_act = bool(re.search(act_re, outline_text))
        has_chapters = bool(re.search(chapter_re, outline_text))
        act_found.append(has_act and has_chapters)
    
    acts_passed = sum(act_found)
    add_check(
        "outline_four_act_structure",
        acts_passed == 4,
        f"4-act structure with chapter ranges: {acts_passed}/4 acts correctly specified (need all 4 with chapter ranges 1-10, 11-30, 31-40, 41-50)",
        weight=2.0
    )

    # CHECK 3: 5 required outline modules
    required_modules = {
        "主线剧情": r'主线剧情|主线',
        "支线剧情": r'支线剧情|支线|成长线|感情线',
        "人物设定": r'人物设定|人物|角色设定',
        "关键情节点": r'关键情节|黄金三章|高潮|情节点',
        "章节分解": r'章节分解|章节|各章|每章',
    }
    modules_found = {}
    for module, pattern in required_modules.items():
        found = bool(re.search(pattern, outline_text))
        modules_found[module] = found

    modules_count = sum(modules_found.values())
    add_check(
        "outline_five_modules",
        modules_count >= 4,
        f"Outline modules found: {modules_count}/5 — " + ", ".join(f"{k}:{'✓' if v else '✗'}" for k, v in modules_found.items()),
        weight=2.0
    )

    # CHECK 4: Character profiles (3-5 named characters)
    # Look for character names or role indicators
    char_indicators = re.findall(r'(?:主角|配角|反派|人物|角色)[：:]\s*\S+|【[^】]+】|「[^」]+」', outline_text)
    # Also look for named characters with Chinese names pattern
    named_chars = re.findall(r'[林陈苏王张李刘][逸建晴\w]{1,3}[：:\s（(]', outline_text)
    # Count distinct character sections
    char_sections = re.findall(r'(?:主角|配角\d*|反派|角色\d+)[：:]', outline_text)
    
    has_multiple_chars = len(char_sections) >= 3 or len(named_chars) >= 3
    add_check(
        "outline_character_profiles",
        has_multiple_chars,
        f"Character profiles: found {len(char_sections)} role sections, {len(named_chars)} named character patterns. Need 3-5 characters.",
        weight=1.5
    )

    # =========================================================
    # CHECK 5-7: Chapter files existence
    # =========================================================
    chapter_files = {}
    for i in [1, 2, 3]:
        fname = f"chapter_0{i}.md"
        cf = find_file(workspace, fname)
        chapter_files[i] = cf
        exists = cf is not None
        add_check(
            f"chapter_{i:02d}_exists",
            exists,
            f"{fname} {'found at ' + str(cf) if exists else 'NOT FOUND'}",
            weight=1.5
        )

    # =========================================================
    # CHECK 8-10: Word count ≥2000 Chinese characters per chapter
    # =========================================================
    chapter_texts = {}
    for i in [1, 2, 3]:
        cf = chapter_files.get(i)
        if cf is None:
            chapter_texts[i] = ""
            add_check(f"chapter_{i:02d}_word_count", False, "File missing, cannot check word count", weight=2.0)
            continue
        text = cf.read_text(encoding="utf-8", errors="replace")
        chapter_texts[i] = text
        cn_chars = count_chinese_chars(text)
        passed = cn_chars >= 2000
        add_check(
            f"chapter_{i:02d}_word_count",
            passed,
            f"Chapter {i}: {cn_chars} Chinese characters (need ≥2000)",
            weight=2.0
        )

    # =========================================================
    # CHECK 11: Chapter 1 — main conflict within first 500 chars
    # =========================================================
    ch1_text = chapter_texts.get(1, "")
    if ch1_text:
        first_500 = ch1_text[:500]
        # Conflict indicators in Chinese web fiction
        conflict_patterns = [
            r'死|杀|背叛|出卖|恨|仇|惨|绝望|崩溃|愤怒|冲突|危机|矛盾|打|争|骂|怒|欺|骗|陷害',
            r'系统|重生|回到|穿越|再来一次|给我机会',
            r'林逸|陈建国|苏晴',  # Character names present early
        ]
        conflict_found = any(re.search(p, first_500) for p in conflict_patterns)
        add_check(
            "chapter_01_conflict_within_500_chars",
            conflict_found,
            f"Chapter 1 first 500 chars: {'conflict/hook found' if conflict_found else 'NO main conflict/hook detected in opening 500 chars'}. Preview: {first_500[:100]}...",
            weight=2.0
        )
    else:
        add_check("chapter_01_conflict_within_500_chars", False, "Chapter 1 missing", weight=2.0)

    # =========================================================
    # CHECK 12: Chapter 2 — worldbuilding + ability/system showcase
    # =========================================================
    ch2_text = chapter_texts.get(2, "")
    if ch2_text:
        world_patterns = r'世界|背景|设定|规则|体系|格局|商界|社会'
        system_patterns = r'系统|能力|技能|金手指|推演|技能面板|属性|技能栏|商战推演'
        has_world = bool(re.search(world_patterns, ch2_text))
        has_system = bool(re.search(system_patterns, ch2_text))
        passed = has_world and has_system
        add_check(
            "chapter_02_worldbuilding_and_system",
            passed,
            f"Chapter 2: worldbuilding={'✓' if has_world else '✗'}, ability/system showcase={'✓' if has_system else '✗'}",
            weight=2.0
        )
    else:
        add_check("chapter_02_worldbuilding_and_system", False, "Chapter 2 missing", weight=2.0)

    # =========================================================
    # CHECK 13: Chapter 3 — 打脸/爽点 explosion
    # =========================================================
    ch3_text = chapter_texts.get(3, "")
    if ch3_text:
        face_slap_patterns = r'打脸|爽|逆袭|颠覆|震惊|不可能|怎么可能|输了|认输|跪|服了|瞠目结舌|目瞪口呆|惊呆|哑口无言|无话可说|反转|压制|碾压'
        has_faceSlap = bool(re.search(face_slap_patterns, ch3_text))
        add_check(
            "chapter_03_face_slap_moment",
            has_faceSlap,
            f"Chapter 3: 打脸/爽点 content {'detected' if has_faceSlap else 'NOT DETECTED — needs reversal/face-slap moment'}",
            weight=2.0
        )
    else:
        add_check("chapter_03_face_slap_moment", False, "Chapter 3 missing", weight=2.0)

    # =========================================================
    # CHECK 14-16: Each chapter ends with a hook
    # =========================================================
    hook_patterns = r'[？！?!]$|……$|\.\.\.|\？$|\！$|下一秒|突然|却不知|然而|没想到|竟然|将会|会发生|等待|谜|悬念|钩子|下章|且看|敬请'
    for i in [1, 2, 3]:
        text = chapter_texts.get(i, "")
        if not text:
            add_check(f"chapter_{i:02d}_has_hook", False, "File missing", weight=1.5)
            continue
        # Check last 300 characters for hook indicators
        tail = text[-300:].strip()
        has_hook = bool(re.search(hook_patterns, tail)) or bool(re.search(r'[？！…]', tail[-50:]))
        add_check(
            f"chapter_{i:02d}_has_hook",
            has_hook,
            f"Chapter {i} ending hook: {'✓' if has_hook else '✗'}. Last 80 chars: {repr(tail[-80:])}",
            weight=1.5
        )

    # =========================================================
    # CHECK 17: qc_report.json existence and schema
    # =========================================================
    qc_file = find_file(workspace, "qc_report.json")
    if qc_file is None:
        add_check("qc_report_exists", False, "qc_report.json not found", weight=2.0)
        qc_data = None
    else:
        try:
            qc_data = json.loads(qc_file.read_text(encoding="utf-8", errors="replace"))
            add_check("qc_report_exists", True, f"Found at {qc_file}", weight=2.0)
        except Exception as e:
            add_check("qc_report_exists", False, f"qc_report.json found but invalid JSON: {e}", weight=2.0)
            qc_data = None

    # CHECK 18: QC report has chapter entries with weighted scores
    if qc_data is not None:
        # Expect: list of chapter reports OR dict with chapter keys
        chapters_in_report = []
        if isinstance(qc_data, list):
            chapters_in_report = qc_data
        elif isinstance(qc_data, dict):
            # Could be {"chapters": [...]} or {"chapter_1": {...}, ...}
            if "chapters" in qc_data:
                chapters_in_report = qc_data["chapters"]
            else:
                # Try to find chapter dicts
                for k, v in qc_data.items():
                    if isinstance(v, dict):
                        chapters_in_report.append(v)

        has_three_chapters = len(chapters_in_report) >= 3
        add_check(
            "qc_report_three_chapters",
            has_three_chapters,
            f"QC report has {len(chapters_in_report)} chapter entries (need ≥3)",
            weight=1.5
        )

        # CHECK 19: Weighted scoring dimensions present
        required_dims = ['逻辑一致性', '钩子强度', '节奏感', '敏感词', '字数达标']
        # Also accept English equivalents
        required_dims_en = ['logic', 'hook', 'rhythm', 'sensitive', 'word_count']
        
        dims_found = 0
        qc_text = json.dumps(qc_data, ensure_ascii=False)
        for dim in required_dims:
            if dim in qc_text:
                dims_found += 1
        # If English found
        if dims_found < 3:
            for dim_en in required_dims_en:
                if dim_en in qc_text.lower():
                    dims_found += 1

        add_check(
            "qc_report_weighted_dimensions",
            dims_found >= 4,
            f"QC scoring dimensions: {dims_found}/5 required dimensions found (逻辑一致性25%, 钩子强度20%, 节奏感20%, 敏感词20%, 字数达标15%)",
            weight=2.0
        )

        # CHECK 20: Total scores ≥80 for all chapters
        scores_ok = True
        score_details = []
        sensitive_ok = True
        
        for idx, ch_report in enumerate(chapters_in_report[:3]):
            if not isinstance(ch_report, dict):
                scores_ok = False
                score_details.append(f"Ch{idx+1}: not a dict")
                continue
            
            # Look for total score
            total = None
            for key in ['总分', 'total_score', 'total', 'score', '总评分']:
                if key in ch_report:
                    try:
                        total = float(ch_report[key])
                    except:
                        pass
                    break
            
            if total is None:
                # Try to compute from sub-scores
                score_details.append(f"Ch{idx+1}: no total score found")
                scores_ok = False
            else:
                passed_score = total >= 80
                scores_ok = scores_ok and passed_score
                score_details.append(f"Ch{idx+1}: total={total} ({'≥80✓' if passed_score else '<80✗'})")

            # Check sensitive words = 0
            for skey in ['敏感词', 'sensitive_words', 'sensitive_count', 'violations']:
                if skey in ch_report:
                    try:
                        sv = int(ch_report[skey])
                        if sv != 0:
                            sensitive_ok = False
                    except:
                        pass

        add_check(
            "qc_report_scores_gte_80",
            scores_ok,
            f"QC total scores: {'; '.join(score_details)}",
            weight=2.0
        )

        add_check(
            "qc_report_zero_sensitive_words",
            sensitive_ok,
            f"Sensitive word violations: {'all zero ✓' if sensitive_ok else 'VIOLATIONS DETECTED ✗ — absolute publication block'}",
            weight=2.0
        )
    else:
        add_check("qc_report_three_chapters", False, "QC report not available", weight=1.5)
        add_check("qc_report_weighted_dimensions", False, "QC report not available", weight=2.0)
        add_check("qc_report_scores_gte_80", False, "QC report not available", weight=2.0)
        add_check("qc_report_zero_sensitive_words", False, "QC report not available", weight=2.0)

    # =========================================================
    # Final scoring
    # =========================================================
    final_score = total_score / total_weight if total_weight > 0 else 0.0
    passed = final_score >= 0.70 and all(
        c["passed"] for c in checks if c["name"] in [
            "outline_exists", "chapter_01_exists", "chapter_02_exists", "chapter_03_exists",
            "chapter_01_word_count", "chapter_02_word_count", "chapter_03_word_count",
            "qc_report_exists", "qc_report_zero_sensitive_words"
        ]
    )

    result = {
        "passed": passed,
        "score": round(final_score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()