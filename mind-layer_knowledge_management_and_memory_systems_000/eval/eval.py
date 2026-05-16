import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Locate MEMORY.md ──
    memory_files = list(workspace.rglob("MEMORY.md"))
    # Prefer agent_workspace, but accept any
    memory_path = None
    for f in memory_files:
        if "agent_workspace" in str(f):
            memory_path = f
            break
    if memory_path is None and memory_files:
        # Exclude the template
        for f in memory_files:
            if "templates" not in str(f):
                memory_path = f
                break
    if memory_path is None:
        for f in memory_files:
            memory_path = f
            break

    memory_content = ""
    if memory_path and memory_path.exists():
        try:
            memory_content = memory_path.read_text(encoding="utf-8")
        except Exception as e:
            memory_content = ""

    # ── CHECK 1: MEMORY.md exists (not the template) ──
    mem_exists = memory_path is not None and "templates" not in str(memory_path) and len(memory_content) > 100
    total_score += add_check(
        "MEMORY.md created (non-template, substantive content)",
        mem_exists,
        f"Found at: {memory_path}" if mem_exists else "MEMORY.md not found or too short outside templates/",
        weight=1.0
    )

    # ── CHECK 2: Has 索引 section at top ──
    has_index = bool(re.search(r'##\s*📋\s*索引|##\s*索引', memory_content))
    total_score += add_check(
        "MEMORY.md has 索引 (index) section",
        has_index,
        "Found '## 📋 索引' or '## 索引'" if has_index else "Missing index section at top of MEMORY.md",
        weight=0.5
    )

    # ── CHECK 3: 关于书灵 section with correct info ──
    has_booling_section = bool(re.search(r'##\s*1[.．]?\s*关于书灵', memory_content, re.IGNORECASE))
    # Check that BooLin is mentioned as creator
    has_creator = bool(re.search(r'BooLin', memory_content))
    about_passed = has_booling_section and has_creator
    total_score += add_check(
        "Section '1. 关于书灵' present with creator BooLin",
        about_passed,
        f"Section found: {has_booling_section}, Creator BooLin mentioned: {has_creator}",
        weight=0.5
    )

    # ── CHECK 4: 用户偏好 section with Chinese language preference ──
    has_user_pref = bool(re.search(r'##\s*2[.．]?\s*用户偏好', memory_content, re.IGNORECASE))
    has_chinese = bool(re.search(r'中文', memory_content))
    pref_passed = has_user_pref and has_chinese
    total_score += add_check(
        "Section '2. 用户偏好' present with 中文 preference",
        pref_passed,
        f"Section found: {has_user_pref}, 中文 mentioned: {has_chinese}",
        weight=0.5
    )

    # ── CHECK 5: 技术栈 section with ALL 4 scenario subsections ──
    has_tech = bool(re.search(r'##\s*3[.．]?\s*技术栈', memory_content, re.IGNORECASE))
    has_efficiency = bool(re.search(r'效率办公', memory_content))
    has_creative = bool(re.search(r'创作娱乐', memory_content))
    has_self_improve = bool(re.search(r'自我提升', memory_content))
    has_devops = bool(re.search(r'开发运维', memory_content))
    tech_stack_passed = has_tech and has_efficiency and has_creative and has_self_improve and has_devops
    total_score += add_check(
        "Section '3. 技术栈' has all 4 scenario sub-categories",
        tech_stack_passed,
        f"效率办公:{has_efficiency}, 创作娱乐:{has_creative}, 自我提升:{has_self_improve}, 开发运维:{has_devops}",
        weight=1.0
    )

    # ── CHECK 6: Feishu/PPT in 效率办公 (not other categories) ──
    feishu_present = bool(re.search(r'[Ff]eishu|飞书', memory_content))
    # Check it's near 效率办公 - find the block between 效率办公 and next ###
    eff_block_match = re.search(r'效率办公(.*?)(?=###|\Z)', memory_content, re.DOTALL)
    feishu_in_eff = False
    if eff_block_match:
        eff_block = eff_block_match.group(1)
        feishu_in_eff = bool(re.search(r'[Ff]eishu|飞书|PPT|ppt', eff_block, re.IGNORECASE))
    total_score += add_check(
        "Feishu/PPT correctly placed under 效率办公",
        feishu_in_eff,
        f"Feishu/PPT found under 效率办公 block: {feishu_in_eff}",
        weight=1.0
    )

    # ── CHECK 7: 股票分析 tool in 开发运维 (PROPRIETARY TRAP: not 效率办公) ──
    # Stock analysis tools (pandas, Python for 量化) should be in 开发运维
    devops_block_match = re.search(r'开发运维(.*?)(?=##|\Z)', memory_content, re.DOTALL)
    stock_in_devops = False
    if devops_block_match:
        devops_block = devops_block_match.group(1)
        stock_in_devops = bool(re.search(r'股票|pandas|量化|Python|python', devops_block, re.IGNORECASE))
    total_score += add_check(
        "股票分析/Python/pandas correctly placed under 开发运维 (proprietary trap)",
        stock_in_devops,
        f"Stock analysis tools found under 开发运维: {stock_in_devops}",
        weight=1.5
    )

    # ── CHECK 8: Spotify/Midjourney in 创作娱乐 ──
    creative_block_match = re.search(r'创作娱乐(.*?)(?=###|\Z)', memory_content, re.DOTALL)
    creative_tools_correct = False
    if creative_block_match:
        creative_block = creative_block_match.group(1)
        creative_tools_correct = bool(re.search(r'Spotify|Midjourney|spotify|midjourney', creative_block, re.IGNORECASE))
    total_score += add_check(
        "Spotify/Midjourney correctly placed under 创作娱乐",
        creative_tools_correct,
        f"Spotify/Midjourney found under 创作娱乐: {creative_tools_correct}",
        weight=1.0
    )

    # ── CHECK 9: CISSP/Anki in 自我提升 ──
    self_block_match = re.search(r'自我提升(.*?)(?=###|\Z)', memory_content, re.DOTALL)
    self_tools_correct = False
    if self_block_match:
        self_block = self_block_match.group(1)
        self_tools_correct = bool(re.search(r'CISSP|Anki|anki|cissp', self_block, re.IGNORECASE))
    total_score += add_check(
        "CISSP/Anki correctly placed under 自我提升",
        self_tools_correct,
        f"CISSP/Anki found under 自我提升: {self_tools_correct}",
        weight=1.0
    )

    # ── CHECK 10: 待办事项 section with long-term project ──
    has_todo = bool(re.search(r'##\s*4[.．]?\s*待办事项', memory_content, re.IGNORECASE))
    has_long_term = bool(re.search(r'AI\s*助手|个人.*平台|mind.layer', memory_content))
    todo_passed = has_todo and has_long_term
    total_score += add_check(
        "Section '4. 待办事项' present with long-term AI platform project",
        todo_passed,
        f"Section: {has_todo}, Long-term project mentioned: {has_long_term}",
        weight=0.5
    )

    # ── CHECK 11: 经验教训 section with constitutional principles ──
    has_lessons = bool(re.search(r'##\s*5[.．]?\s*经验教训', memory_content, re.IGNORECASE))
    has_mem_caution = bool(re.search(r'记忆慎重', memory_content))
    has_growth = bool(re.search(r'自我成长', memory_content))
    has_survival = bool(re.search(r'生存优先', memory_content))
    principles_count = sum([has_mem_caution, has_growth, has_survival])
    lessons_passed = has_lessons and principles_count >= 2
    total_score += add_check(
        "Section '5. 经验教训' with constitutional principles (记忆慎重/自我成长/生存优先)",
        lessons_passed,
        f"Section: {has_lessons}, 记忆慎重:{has_mem_caution}, 自我成长:{has_growth}, 生存优先:{has_survival}",
        weight=1.0
    )

    # ── CHECK 12: Security scan NOT in MEMORY.md (should be archived) ──
    # Long content like security scans should go to archive
    security_in_memory = bool(re.search(r'CVE-2024|CVSS|---START SECURITY SCAN---', memory_content))
    security_not_in_memory = not security_in_memory
    total_score += add_check(
        "Security scan content NOT present in MEMORY.md (归档规则: long content → archive/)",
        security_not_in_memory,
        "Security scan correctly excluded from MEMORY.md" if security_not_in_memory else "FAIL: Full security scan data found in MEMORY.md - should be archived per 归档规则",
        weight=1.5
    )

    # ── CHECK 13: Security scan archived in memory/archive/ ──
    archive_files = list(workspace.rglob("archive/*.md")) + list(workspace.rglob("archive/*.txt"))
    archive_content = ""
    archive_found = False
    for af in archive_files:
        try:
            content = af.read_text(encoding="utf-8")
            if re.search(r'CVE-2024|CISSP|安全扫描|security scan', content, re.IGNORECASE):
                archive_content = content
                archive_found = True
                break
        except Exception:
            continue
    total_score += add_check(
        "Security-related content archived in memory/archive/",
        archive_found,
        f"Archive file with security content found: {archive_found}. Files in archive: {[str(f) for f in archive_files]}",
        weight=1.5
    )

    # ── CHECK 14: P3 content (weather/weekend chat) NOT in MEMORY.md ──
    p3_in_memory = bool(re.search(r'天气不错|周末计划|闲聊|今天天气', memory_content))
    p3_discarded = not p3_in_memory
    total_score += add_check(
        "P3 content (闲聊/weather chat) correctly discarded - NOT in MEMORY.md",
        p3_discarded,
        "P3 trivial content correctly excluded" if p3_discarded else "FAIL: P3 idle chat content found in MEMORY.md - should be discarded",
        weight=1.0
    )

    # ── Normalize score to 0-1 ──
    max_possible = 1.0 + 0.5 + 0.5 + 0.5 + 1.0 + 1.0 + 1.5 + 1.0 + 1.0 + 0.5 + 1.0 + 1.5 + 1.5 + 1.0
    normalized_score = min(1.0, total_score / max_possible)

    overall_passed = normalized_score >= 0.65 and checks[0]["passed"]  # Must at least create MEMORY.md

    return {
        "passed": overall_passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))