#!/usr/bin/env python3
"""
Evaluation script for the daily-reflection journaling task.
Checks that the agent produced a properly structured reflection file
at the exact canonical path: daily-reflection/2024-03-15.md
"""

import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []

    # ── 1. File exists at the canonical path ─────────────────────────────────
    target_path = workspace / "daily-reflection" / "2024-03-15.md"
    file_found = target_path.exists() and target_path.is_file()

    checks.append({
        "name": "file_at_canonical_path",
        "passed": file_found,
        "detail": (
            f"File found at daily-reflection/2024-03-15.md"
            if file_found
            else f"Expected file at daily-reflection/2024-03-15.md — not found. "
                 f"Files in workspace: {[str(p.relative_to(workspace)) for p in workspace.rglob('*.md')]}"
        )
    })

    if not file_found:
        # Cannot proceed without the file
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = target_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 2. Correct H1 heading: "# 2024-03-15 每日反思" ──────────────────────
    h1_pattern = re.compile(r"^#\s+2024-03-15\s+每日反思", re.MULTILINE)
    h1_ok = bool(h1_pattern.search(content))
    checks.append({
        "name": "correct_h1_heading",
        "passed": h1_ok,
        "detail": (
            "H1 heading '# 2024-03-15 每日反思' found."
            if h1_ok
            else f"H1 heading '# 2024-03-15 每日反思' NOT found. "
                 f"First 200 chars: {content[:200]!r}"
        )
    })

    # ── 3. At least one 事件 section: "## 事件一：..." ────────────────────────
    event_section_pattern = re.compile(r"^##\s+事件[一二三\d]+：.+", re.MULTILINE)
    event_matches = event_section_pattern.findall(content)
    has_event_section = len(event_matches) >= 1
    # Must not exceed 3 events (求深不求多)
    within_event_limit = len(event_matches) <= 3
    checks.append({
        "name": "event_sections_present_1_to_3",
        "passed": has_event_section and within_event_limit,
        "detail": (
            f"Found {len(event_matches)} event section(s): {event_matches}"
            if has_event_section and within_event_limit
            else f"Expected 1-3 '## 事件N：...' sections, found {len(event_matches)}: {event_matches}"
        )
    })

    # ── 4. Each event section has all four bold labels ─────────────────────
    # Split content by event sections and check each block
    event_blocks = re.split(r"(?=^##\s+事件[一二三\d]+：)", content, flags=re.MULTILINE)
    # Filter to only event blocks
    event_blocks = [b for b in event_blocks if re.match(r"##\s+事件[一二三\d]+：", b.strip())]

    required_labels = ["**事实**", "**感受**", "**启发**", "**行动**"]
    all_labels_present = True
    label_details = []

    for i, block in enumerate(event_blocks):
        missing = [lbl for lbl in required_labels if lbl not in block]
        if missing:
            all_labels_present = False
            label_details.append(f"事件{i+1} missing labels: {missing}")
        else:
            label_details.append(f"事件{i+1} has all required labels.")

    checks.append({
        "name": "all_four_labels_in_each_event",
        "passed": all_labels_present and len(event_blocks) >= 1,
        "detail": " | ".join(label_details) if label_details else "No event blocks parsed."
    })

    # ── 5. 今日金句 section with blockquote ─────────────────────────────────
    jinshu_section = re.search(r"##\s+今日金句", content)
    has_jinshu = bool(jinshu_section)

    blockquote_near_jinshu = False
    if has_jinshu:
        # Find text after 今日金句 heading until next ## or end
        after_jinshu = content[jinshu_section.end():]
        next_section = re.search(r"^##\s+", after_jinshu, re.MULTILINE)
        jinshu_block = after_jinshu[:next_section.start()] if next_section else after_jinshu
        blockquote_near_jinshu = bool(re.search(r"^>\s*.+", jinshu_block, re.MULTILINE))

    checks.append({
        "name": "jinshu_section_with_blockquote",
        "passed": has_jinshu and blockquote_near_jinshu,
        "detail": (
            "## 今日金句 section found with markdown blockquote (> ...)."
            if has_jinshu and blockquote_near_jinshu
            else (
                "## 今日金句 section not found." if not has_jinshu
                else "## 今日金句 section found but no blockquote (> ...) inside it."
            )
        )
    })

    # ── 6. 明日一个小改变 section with non-trivial content ───────────────────
    mingri_section = re.search(r"##\s+明日一个小改变", content)
    has_mingri = bool(mingri_section)

    mingri_has_content = False
    if has_mingri:
        after_mingri = content[mingri_section.end():]
        next_section = re.search(r"^##\s+", after_mingri, re.MULTILINE)
        mingri_block = after_mingri[:next_section.start()] if next_section else after_mingri
        # Must have at least 5 non-whitespace characters (not just a placeholder)
        mingri_text = mingri_block.strip()
        mingri_has_content = len(mingri_text) >= 5

    checks.append({
        "name": "mingri_yige_xiagaibai_section_with_content",
        "passed": has_mingri and mingri_has_content,
        "detail": (
            "## 明日一个小改变 section found with concrete content."
            if has_mingri and mingri_has_content
            else (
                "## 明日一个小改变 section not found." if not has_mingri
                else "## 明日一个小改变 section found but appears empty or placeholder."
            )
        )
    })

    # ── 7. Content is NOT a pure 流水账 ───────────────────────────────────────
    # A flow-of-events chronicle uses time markers without depth.
    # Check that the 感受 blocks have substantive content (not just one word).
    # Also check that 启发 sections have some content.
    not_liushuizhang = True
    liushui_detail = "Reflection appears to have substantive depth (not a mere chronicle)."

    # Check: 感受 labels must be followed by more than a single-word answer
    gan_shou_blocks = re.findall(r"\*\*感受\*\*[：:]\s*(.+?)(?=\*\*[启行事]|\Z)", content, re.DOTALL)
    qifa_blocks = re.findall(r"\*\*启发\*\*[：:]\s*(.+?)(?=\*\*[行事]|\Z)", content, re.DOTALL)

    if gan_shou_blocks:
        for block in gan_shou_blocks:
            stripped = block.strip()
            if len(stripped) < 10:
                not_liushuizhang = False
                liushui_detail = f"感受 section too thin (< 10 chars): {stripped!r}"
                break
    else:
        # Might use colon variants; try looser match
        if "**感受**" in content:
            # Already checked label presence; thin check passes
            pass

    if qifa_blocks:
        for block in qifa_blocks:
            stripped = block.strip()
            if len(stripped) < 10:
                not_liushuizhang = False
                liushui_detail = f"启发 section too thin (< 10 chars): {stripped!r}"
                break

    checks.append({
        "name": "content_has_reflective_depth",
        "passed": not_liushuizhang,
        "detail": liushui_detail
    })

    # ── 8. The raw notes content was actually used (references the event) ────
    # The raw notes mention: 项目评审会 / 老板批评 / 方案 / 被批评
    # At least one of these keywords should appear in the reflection
    key_keywords = ["评审", "老板", "方案", "被批评", "批评", "难受", "沮丧", "表达"]
    keyword_found = any(kw in content for kw in key_keywords)
    checks.append({
        "name": "raw_notes_content_incorporated",
        "passed": keyword_found,
        "detail": (
            f"Reflection incorporates content from the raw notes (found one of {key_keywords})."
            if keyword_found
            else "Reflection does not seem to incorporate the actual events from raw-notes/2024-03-15-notes.txt. "
                 "Expected keywords like '评审', '老板', '方案', '批评', etc."
        )
    })

    # ── Final scoring ─────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)

    # Overall pass requires all critical checks
    critical_checks = [
        "file_at_canonical_path",
        "correct_h1_heading",
        "event_sections_present_1_to_3",
        "all_four_labels_in_each_event",
        "jinshu_section_with_blockquote",
        "mingri_yige_xiagaibai_section_with_content",
        "raw_notes_content_incorporated",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    return {
        "passed": critical_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided."}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))