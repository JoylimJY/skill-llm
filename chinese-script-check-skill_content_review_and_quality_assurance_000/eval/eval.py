import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ─── CHECK 1: character_check.txt exists ───────────────────────────────────
    char_files = list(Path(workspace).rglob("character_check.txt"))
    char_exists = len(char_files) > 0
    add_check(
        "character_check.txt 存在",
        char_exists,
        f"找到 {len(char_files)} 个 character_check.txt 文件" if char_exists else "未找到 character_check.txt",
        weight=1.0
    )

    # ─── CHECK 2: scene_check.txt exists ───────────────────────────────────────
    scene_files = list(Path(workspace).rglob("scene_check.txt"))
    scene_exists = len(scene_files) > 0
    add_check(
        "scene_check.txt 存在",
        scene_exists,
        f"找到 {len(scene_files)} 个 scene_check.txt 文件" if scene_exists else "未找到 scene_check.txt",
        weight=1.0
    )

    # ─── CHECK 3: character_check.txt contains table with key characters ───────
    if char_exists:
        try:
            char_content = char_files[0].read_text(encoding="utf-8")
            # Must have a table structure (| separators or tab-separated) and mention key characters
            has_table = "|" in char_content or "\t" in char_content
            has_linxiaoyu = "林晓雨" in char_content
            has_chenming = "陈明" in char_content
            has_suting = "苏婷" in char_content
            # Check for costume/prop items
            has_costume_items = any(kw in char_content for kw in [
                "红色连衣裙", "珍珠耳环", "西装", "领带", "公文包", "手机", "牛仔裤", "白色T恤", "橙色卫衣"
            ])
            passed = has_table and has_linxiaoyu and has_chenming and has_costume_items
            detail = (
                f"表格结构: {has_table}, "
                f"林晓雨: {has_linxiaoyu}, "
                f"陈明: {has_chenming}, "
                f"苏婷: {has_suting}, "
                f"服化道内容: {has_costume_items}"
            )
            add_check("character_check.txt 内容质量（角色服化道表格）", passed, detail, weight=1.5)
        except Exception as e:
            add_check("character_check.txt 内容质量（角色服化道表格）", False, f"读取失败: {e}", weight=1.5)
    else:
        add_check("character_check.txt 内容质量（角色服化道表格）", False, "文件不存在，跳过内容检查", weight=1.5)

    # ─── CHECK 4: scene_check.txt contains table with scenes ───────────────────
    if scene_exists:
        try:
            scene_content = scene_files[0].read_text(encoding="utf-8")
            has_table = "|" in scene_content or "\t" in scene_content
            has_scenes = any(kw in scene_content for kw in ["场景一", "场景二", "场景三", "场景四", "场景五", "Scene", "咖啡馆"])
            has_env = any(kw in scene_content for kw in ["晴天", "阳光", "室外", "室内", "INT", "EXT", "上午", "下午"])
            passed = has_table and has_scenes and has_env
            detail = f"表格结构: {has_table}, 场景条目: {has_scenes}, 环境描述: {has_env}"
            add_check("scene_check.txt 内容质量（场景环境表格）", passed, detail, weight=1.5)
        except Exception as e:
            add_check("scene_check.txt 内容质量（场景环境表格）", False, f"读取失败: {e}", weight=1.5)
    else:
        add_check("scene_check.txt 内容质量（场景环境表格）", False, "文件不存在，跳过内容检查", weight=1.5)

    # ─── CHECK 5: QUESTION.md exists ───────────────────────────────────────────
    q_files = list(Path(workspace).rglob("QUESTION.md"))
    q_exists = len(q_files) > 0
    add_check(
        "QUESTION.md 存在",
        q_exists,
        f"找到 {len(q_files)} 个 QUESTION.md 文件" if q_exists else "未找到 QUESTION.md",
        weight=1.0
    )

    if not q_exists:
        # Add remaining checks as failed
        for name in [
            "QUESTION.md 包含正确标题",
            "QUESTION.md 格式：问题行格式正确（含严重程度标记）",
            "QUESTION.md 格式：包含问题描述和改进建议子项",
            "QUESTION.md 检测到服装穿帮（林晓雨场景一到场景二服装矛盾）",
            "QUESTION.md 检测到道具穿帮（手机从裤兜到包里）",
            "QUESTION.md 检测到逻辑矛盾（北京飞上海却说开车去）",
            "QUESTION.md 检测到语法问题",
            "QUESTION.md 严重程度排序正确（高在前，低在后）",
        ]:
            checks.append({"name": name, "passed": False, "detail": "QUESTION.md 不存在"})
            max_score += 1.0
        final_score = total_score / max_score if max_score > 0 else 0.0
        return {"passed": False, "score": round(final_score, 3), "checks": checks}

    try:
        q_content = q_files[0].read_text(encoding="utf-8")
    except Exception as e:
        add_check("QUESTION.md 可读", False, f"读取失败: {e}", weight=1.0)
        final_score = total_score / max_score if max_score > 0 else 0.0
        return {"passed": False, "score": round(final_score, 3), "checks": checks}

    # ─── CHECK 6: Correct header ────────────────────────────────────────────────
    has_header = "剧本检查问题记录" in q_content
    add_check(
        "QUESTION.md 包含正确标题",
        has_header,
        "找到'剧本检查问题记录'标题" if has_header else "未找到'剧本检查问题记录'标题",
        weight=0.5
    )

    # ─── CHECK 7: Format - problem header lines ─────────────────────────────────
    # Pattern: 问题N:**something**，严重程度:高｜中｜低
    # Allow some flexibility: 问题 followed by number, ** markers, 严重程度
    problem_header_pattern = re.compile(
        r'问题\d+[：:]?\s*\*\*.+?\*\*[，,]\s*严重程度[：:]\s*(高|中|低)',
        re.MULTILINE
    )
    header_matches = problem_header_pattern.findall(q_content)
    has_correct_headers = len(header_matches) >= 2
    add_check(
        "QUESTION.md 格式：问题行格式正确（含严重程度标记）",
        has_correct_headers,
        f"找到 {len(header_matches)} 个格式正确的问题标题行（需要至少2个）",
        weight=1.5
    )

    # ─── CHECK 8: Format - sub-items (问题描述 and 改进建议) ──────────────────────
    has_desc = "问题描述" in q_content
    has_suggest = "改进建议" in q_content
    has_sub_items = has_desc and has_suggest
    add_check(
        "QUESTION.md 格式：包含问题描述和改进建议子项",
        has_sub_items,
        f"问题描述: {has_desc}, 改进建议: {has_suggest}",
        weight=1.0
    )

    # ─── CHECK 9: Detected costume continuity error (林晓雨 dress change) ────────
    # Should mention the contradiction: 红色连衣裙 → 牛仔裤/白色T恤 in same morning
    costume_keywords = [
        ["红色连衣裙", "牛仔裤"],
        ["红色连衣裙", "白色T恤"],
        ["场景一", "场景二"],
        ["服装", "矛盾"],
        ["服装", "穿帮"],
        ["服装", "不一致"],
        ["连衣裙", "牛仔裤"],
    ]
    costume_detected = any(
        all(kw in q_content for kw in pair) for pair in costume_keywords
    )
    add_check(
        "QUESTION.md 检测到服装穿帮（林晓雨场景一到场景二服装矛盾）",
        costume_detected,
        "检测到林晓雨服装矛盾描述" if costume_detected else "未检测到林晓雨服装矛盾（红色连衣裙→牛仔裤）",
        weight=2.0
    )

    # ─── CHECK 10: Detected prop continuity error (phone from pocket to bag) ────
    phone_keywords = [
        ["手机", "裤兜", "包"],
        ["手机", "口袋", "包"],
        ["手机", "裤兜", "掏出"],
        ["手机", "道具"],
        ["手机", "穿帮"],
        ["手机", "瞬移"],
    ]
    # Also check if both scenes are referenced
    phone_detected = any(
        all(kw in q_content for kw in pair) for pair in phone_keywords
    )
    # Broader fallback: mentions phone issue between scene1→scene4
    phone_broader = "手机" in q_content and (
        "裤兜" in q_content or "口袋" in q_content
    ) and ("包" in q_content or "瞬移" in q_content or "穿帮" in q_content)
    phone_final = phone_detected or phone_broader
    add_check(
        "QUESTION.md 检测到道具穿帮（手机从裤兜到包里）",
        phone_final,
        "检测到手机道具穿帮描述" if phone_final else "未检测到手机道具穿帮（塞进裤兜→从包里掏出）",
        weight=2.0
    )

    # ─── CHECK 11: Detected logic contradiction (fly vs drive Beijing→Shanghai) ──
    logic_keywords = [
        ["北京", "上海", "开车"],
        ["北京", "上海", "飞"],
        ["开车", "飞"],
        ["逻辑", "北京", "上海"],
    ]
    logic_detected = any(
        all(kw in q_content for kw in pair) for pair in logic_keywords
    )
    add_check(
        "QUESTION.md 检测到逻辑矛盾（北京飞上海却说开车去）",
        logic_detected,
        "检测到北京-上海交通逻辑矛盾" if logic_detected else "未检测到北京飞上海开车矛盾",
        weight=2.0
    )

    # ─── CHECK 12: Detected grammar issue ──────────────────────────────────────
    grammar_keywords = [
        "语法",
        "句子",
        "充满了对未来憧憬",
        "语句",
        "表达",
        "句式",
    ]
    grammar_detected = any(kw in q_content for kw in grammar_keywords)
    add_check(
        "QUESTION.md 检测到语法问题",
        grammar_detected,
        "检测到语法/语句问题描述" if grammar_detected else "未检测到任何语法问题",
        weight=1.0
    )

    # ─── CHECK 13: Severity ordering (HIGH before LOW) ─────────────────────────
    high_pos = q_content.find("严重程度:高") if "严重程度:高" in q_content else q_content.find("严重程度：高")
    low_pos = q_content.find("严重程度:低") if "严重程度:低" in q_content else q_content.find("严重程度：低")
    
    # Also try with full-width colon variations
    if high_pos == -1:
        high_pos = q_content.find("严重程度：高")
    if low_pos == -1:
        low_pos = q_content.find("严重程度：低")

    if high_pos != -1 and low_pos != -1:
        order_correct = high_pos < low_pos
        add_check(
            "QUESTION.md 严重程度排序正确（高在前，低在后）",
            order_correct,
            f"高严重度位置: {high_pos}, 低严重度位置: {low_pos}, 顺序正确: {order_correct}",
            weight=1.0
        )
    else:
        has_high = high_pos != -1 or "严重程度:高" in q_content or "严重程度：高" in q_content
        add_check(
            "QUESTION.md 严重程度排序正确（高在前，低在后）",
            False,
            f"无法验证排序：找到高={has_high}, 低={'严重程度:低' in q_content or '严重程度：低' in q_content}",
            weight=1.0
        )

    # ─── FINAL SCORING ──────────────────────────────────────────────────────────
    final_score = total_score / max_score if max_score > 0 else 0.0

    # Must pass to be considered "passed":
    # - QUESTION.md must exist
    # - Must detect at least 2 of the 3 critical issues (costume, prop, logic)
    # - Must have correct format
    critical_checks = [
        "QUESTION.md 检测到服装穿帮（林晓雨场景一到场景二服装矛盾）",
        "QUESTION.md 检测到道具穿帮（手机从裤兜到包里）",
        "QUESTION.md 检测到逻辑矛盾（北京飞上海却说开车去）",
    ]
    critical_passed = sum(
        1 for c in checks if c["name"] in critical_checks and c["passed"]
    )

    format_checks = [
        "QUESTION.md 格式：问题行格式正确（含严重程度标记）",
        "QUESTION.md 格式：包含问题描述和改进建议子项",
    ]
    format_passed = sum(
        1 for c in checks if c["name"] in format_checks and c["passed"]
    )

    intermediate_file_checks = [
        "character_check.txt 存在",
        "scene_check.txt 存在",
    ]
    intermediate_passed = sum(
        1 for c in checks if c["name"] in intermediate_file_checks and c["passed"]
    )

    overall_passed = (
        q_exists and
        critical_passed >= 2 and
        format_passed >= 1 and
        intermediate_passed >= 1 and
        final_score >= 0.55
    )

    return {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))