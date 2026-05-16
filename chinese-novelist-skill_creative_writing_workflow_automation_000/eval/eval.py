import sys
import json
import re
from pathlib import Path

def count_chinese(text: str) -> int:
    return len(re.findall(r'[\u4e00-\u9fff]', text))

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    max_score = 0.0

    # ── Helper ──────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ── CHECK 1: Novel directory exists at novels/骨语/ ────────────────
    try:
        novel_dirs = list(ws.glob("novels/*/"))
        # Accept any directory whose name contains 骨语 or similar
        found_dir = None
        for d in novel_dirs:
            if "骨语" in d.name or "骨" in d.name:
                found_dir = d
                break
        if found_dir is None and novel_dirs:
            # Accept any novels/ subdirectory if 骨语 not found - but penalize
            found_dir = novel_dirs[0]
        passed = found_dir is not None and found_dir.is_dir()
        add_check(
            "novel_directory_created",
            passed,
            f"Found novel directory: {found_dir}" if passed else "No novel directory found under novels/",
            weight=1.0
        )
    except Exception as e:
        add_check("novel_directory_created", False, f"Exception: {e}", weight=1.0)
        found_dir = None

    # ── CHECK 2: 00-大纲.md exists and has content ─────────────────────
    outline_file = None
    outline_text = ""
    try:
        if found_dir:
            candidates = list(found_dir.glob("00*.md")) + list(found_dir.glob("*大纲*"))
            if candidates:
                outline_file = candidates[0]
                outline_text = outline_file.read_text(encoding="utf-8")
        passed = outline_file is not None and len(outline_text) > 200
        add_check(
            "outline_file_exists",
            passed,
            f"Outline file: {outline_file}, length: {len(outline_text)}" if outline_file else "00-大纲.md not found",
            weight=1.5
        )
    except Exception as e:
        add_check("outline_file_exists", False, f"Exception: {e}", weight=1.5)

    # ── CHECK 3: Outline has chapter planning table (TODO list) ────────
    try:
        has_table = (
            "第01章" in outline_text or "第1章" in outline_text
        ) and (
            "第02章" in outline_text or "第2章" in outline_text or "第03章" in outline_text
        )
        has_status_markers = any(kw in outline_text for kw in ["待开始", "完成", "进行中", "状态"])
        passed = has_table and has_status_markers
        add_check(
            "outline_has_todo_list",
            passed,
            f"Table found: {has_table}, Status markers: {has_status_markers}",
            weight=1.5
        )
    except Exception as e:
        add_check("outline_has_todo_list", False, f"Exception: {e}", weight=1.5)

    # ── CHECK 4: 01-人物档案.md exists and has character info ──────────
    char_file = None
    char_text = ""
    try:
        if found_dir:
            candidates = list(found_dir.glob("01*.md")) + list(found_dir.glob("*人物*"))
            if candidates:
                char_file = candidates[0]
                char_text = char_file.read_text(encoding="utf-8")
        # Must mention 沈白 (protagonist) and have structured content
        has_protagonist = "沈白" in char_text
        has_structure = any(kw in char_text for kw in ["主角", "反派", "配角", "职业", "性格"])
        passed = char_file is not None and has_protagonist and has_structure
        add_check(
            "character_file_exists_and_complete",
            passed,
            f"Char file: {char_file}, protagonist '沈白': {has_protagonist}, structure: {has_structure}",
            weight=1.5
        )
    except Exception as e:
        add_check("character_file_exists_and_complete", False, f"Exception: {e}", weight=1.5)

    # ── CHECK 5-7: Three chapter files exist ───────────────────────────
    chapter_files = []
    try:
        if found_dir:
            chapter_files = sorted([
                f for f in found_dir.glob("*.md")
                if re.search(r'第0?[123]章', f.name) or re.search(r'第[一二三]章', f.name)
            ])
            # Broader search: any file with 章 in name
            if len(chapter_files) < 3:
                chapter_files = sorted([
                    f for f in found_dir.glob("*.md")
                    if "章" in f.name and "大纲" not in f.name and "人物" not in f.name
                ])
    except Exception as e:
        chapter_files = []

    for i, expected_ch in enumerate(["第01章", "第02章", "第03章"], 1):
        try:
            # Find chapter i
            ch_file = chapter_files[i-1] if len(chapter_files) >= i else None
            passed = ch_file is not None and ch_file.exists()
            add_check(
                f"chapter_{i:02d}_file_exists",
                passed,
                f"Chapter {i} file: {ch_file}",
                weight=1.0
            )
        except Exception as e:
            add_check(f"chapter_{i:02d}_file_exists", False, f"Exception: {e}", weight=1.0)

    # ── CHECK 8-10: Each chapter >= 3000 Chinese characters ─────────────
    for i in range(3):
        try:
            ch_file = chapter_files[i] if len(chapter_files) > i else None
            if ch_file and ch_file.exists():
                text = ch_file.read_text(encoding="utf-8")
                cn_count = count_chinese(text)
                passed = cn_count >= 3000
                add_check(
                    f"chapter_{i+1:02d}_wordcount_ge_3000",
                    passed,
                    f"{ch_file.name}: {cn_count} Chinese chars (need ≥3000)",
                    weight=2.0
                )
            else:
                add_check(
                    f"chapter_{i+1:02d}_wordcount_ge_3000",
                    False,
                    f"Chapter {i+1} file not found, cannot check wordcount",
                    weight=2.0
                )
        except Exception as e:
            add_check(f"chapter_{i+1:02d}_wordcount_ge_3000", False, f"Exception: {e}", weight=2.0)

    # ── CHECK 11: Chapters have hook endings ────────────────────────────
    hook_keywords = [
        "突然", "此时", "然而", "没想到", "就在这时", "门", "声音", "发现",
        "原来", "竟然", "不对", "等等", "慢着", "（未完）", "下章", "——"
    ]
    try:
        hook_count = 0
        for cf in chapter_files[:3]:
            if cf.exists():
                text = cf.read_text(encoding="utf-8")
                # Check last 500 chars for hook indicators
                tail = text[-500:] if len(text) > 500 else text
                if any(kw in tail for kw in hook_keywords):
                    hook_count += 1
        passed = hook_count >= 2
        add_check(
            "chapters_have_hook_endings",
            passed,
            f"{hook_count}/3 chapters have hook-style endings",
            weight=1.5
        )
    except Exception as e:
        add_check("chapters_have_hook_endings", False, f"Exception: {e}", weight=1.5)

    # ── CHECK 12: Outline contains completed chapter summaries ──────────
    try:
        # After 3 chapters, outline should have summaries (300-500 chars each) for completed chapters
        summary_section = ""
        if "已完成章节摘要" in outline_text:
            idx = outline_text.index("已完成章节摘要")
            summary_section = outline_text[idx:]
        elif "摘要" in outline_text:
            idx = outline_text.index("摘要")
            summary_section = outline_text[idx:]
        
        # Count Chinese chars in summary section
        summary_cn = count_chinese(summary_section)
        # Expect at least 3 summaries of ~300 chars minimum each = 900 chars
        passed = summary_cn >= 600
        add_check(
            "outline_has_chapter_summaries",
            passed,
            f"Summary section Chinese chars: {summary_cn} (need ≥600 for 3 chapters)",
            weight=2.0
        )
    except Exception as e:
        add_check("outline_has_chapter_summaries", False, f"Exception: {e}", weight=2.0)

    # ── CHECK 13: Outline shows chapters marked 完成 ─────────────────────
    try:
        completed_count = outline_text.count("完成")
        in_progress_remaining = outline_text.count("进行中")
        # At least 3 chapters should be marked as completed
        passed = completed_count >= 3
        add_check(
            "outline_todo_status_updated_to_complete",
            passed,
            f"'完成' appears {completed_count} times, '进行中' appears {in_progress_remaining} times (need ≥3 '完成')",
            weight=2.0
        )
    except Exception as e:
        add_check("outline_todo_status_updated_to_complete", False, f"Exception: {e}", weight=2.0)

    # ── CHECK 14: Chapter files use correct naming convention ───────────
    try:
        correct_names = 0
        for cf in chapter_files[:3]:
            if re.search(r'第0?[1-9]\d*章', cf.name):
                correct_names += 1
        passed = correct_names >= 3
        add_check(
            "chapter_files_named_correctly",
            passed,
            f"{correct_names}/3 chapter files use '第XX章' naming convention",
            weight=1.0
        )
    except Exception as e:
        add_check("chapter_files_named_correctly", False, f"Exception: {e}", weight=1.0)

    # ── CHECK 15: No obvious AI-flavor phrases in chapters ──────────────
    ai_flavor_words = ["璀璨", "瑰丽", "绚烂", "心潮澎湃", "热血沸腾", "娓娓道来", "岁月如梭"]
    try:
        ai_hits = 0
        all_chapter_text = ""
        for cf in chapter_files[:3]:
            if cf.exists():
                all_chapter_text += cf.read_text(encoding="utf-8")
        for word in ai_flavor_words:
            ai_hits += all_chapter_text.count(word)
        # Allow at most 3 hits across all chapters (some may slip through)
        passed = ai_hits <= 3
        add_check(
            "chapters_polished_no_excessive_ai_flavor",
            passed,
            f"AI-flavor keyword hits: {ai_hits} (allowed ≤3)",
            weight=1.0
        )
    except Exception as e:
        add_check("chapters_polished_no_excessive_ai_flavor", False, f"Exception: {e}", weight=1.0)

    # ── CHECK 16: Protagonist 沈白 appears in chapter content ───────────
    try:
        shen_bai_count = 0
        for cf in chapter_files[:3]:
            if cf.exists():
                t = cf.read_text(encoding="utf-8")
                shen_bai_count += t.count("沈白")
        passed = shen_bai_count >= 5
        add_check(
            "protagonist_appears_in_chapters",
            passed,
            f"'沈白' appears {shen_bai_count} times across chapters (need ≥5)",
            weight=1.0
        )
    except Exception as e:
        add_check("protagonist_appears_in_chapters", False, f"Exception: {e}", weight=1.0)

    # ── Final scoring ────────────────────────────────────────────────────
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    overall_passed = final_score >= 0.70 and all(
        c["passed"] for c in checks if c["name"] in [
            "novel_directory_created",
            "outline_file_exists",
            "chapter_01_file_exists",
            "chapter_02_file_exists",
            "chapter_03_file_exists",
            "chapter_01_wordcount_ge_3000",
            "chapter_02_wordcount_ge_3000",
            "chapter_03_wordcount_ge_3000",
        ]
    )

    result = {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    evaluate(sys.argv[1])