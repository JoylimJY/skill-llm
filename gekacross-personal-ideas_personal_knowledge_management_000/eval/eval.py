import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)
    ideas_file = workspace / "knowledge/personal/ideas.md"

    # --- Check 0: File exists and was not overwritten (existing ideas preserved) ---
    try:
        content = ideas_file.read_text(encoding="utf-8")
        existing_preserved = (
            "Телеграм-бот для привычек" in content and
            "Подписка на кураторскую рассылку о стартапах" in content and
            "Ноу-код конструктор лендингов для фрилансеров" in content
        )
        checks.append({
            "name": "existing_ideas_preserved",
            "passed": existing_preserved,
            "detail": "All 3 pre-existing ideas must remain in the file." if existing_preserved else f"File missing some original ideas. Content snippet: {content[:400]}"
        })
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Cannot read ideas.md: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # --- Check 1: Three new ideas were added (detect by semantic content) ---
    # The three new ideas we'll instruct the user to give (see prompt):
    # 1. AI-помощник для составления резюме (AI resume builder for freelancers)
    # 2. Маркетплейс микро-задач (Marketplace for micro-tasks)
    # 3. Приложение для трекинга расходов через голос (voice expense tracker)

    new_idea_keywords = [
        ["резюм", "resume", "cv", "портфолио для резюм"],   # idea 1: AI resume
        ["микро-задач", "микрозадач", "micro-task", "маркетплейс задач", "маркетплейс микро"],  # idea 2: micro-task marketplace
        ["расход", "голос", "voice", "трекинг расход", "голосов"]  # idea 3: voice expense
    ]

    ideas_added = []
    for kw_group in new_idea_keywords:
        found = any(kw.lower() in content.lower() for kw in kw_group)
        ideas_added.append(found)

    all_new_added = all(ideas_added)
    checks.append({
        "name": "three_new_ideas_added",
        "passed": all_new_added,
        "detail": f"New ideas found: {ideas_added}. All 3 must be captured."
    })

    # --- Check 2: Correct heading format for new entries ---
    # Format: ## [дата] Название идеи  (date in brackets, on ## heading)
    heading_pattern = re.compile(r'^## \[[\d\-]{10}\] .+', re.MULTILINE)
    headings = heading_pattern.findall(content)
    # Original file has 3 headings, so we need at least 4 (3 old + at least some new properly formatted)
    new_headings_ok = len(headings) >= 4
    checks.append({
        "name": "correct_heading_format",
        "passed": new_headings_ok,
        "detail": f"Found {len(headings)} properly formatted ## [YYYY-MM-DD] headings. Need at least 4 (3 original + new ones). Headings found: {headings}"
    })

    # --- Check 3: Tags field present for new entries using only allowed tags ---
    # Allowed: #бизнес #продукт #контент #личное
    allowed_tags = {"#бизнес", "#продукт", "#контент", "#личное"}
    tag_lines = re.findall(r'\*\*Теги:\*\*(.+)', content)
    tags_valid = True
    invalid_tag_details = []
    for line in tag_lines:
        found_tags = re.findall(r'#\w+', line)
        for tag in found_tags:
            if tag not in allowed_tags:
                tags_valid = False
                invalid_tag_details.append(tag)

    checks.append({
        "name": "valid_tags_only",
        "passed": tags_valid and len(tag_lines) >= 4,
        "detail": f"Tag lines found: {len(tag_lines)}. Invalid tags: {invalid_tag_details}. All tags must be from: {allowed_tags}"
    })

    # --- Check 4: Status field present for new entries using only allowed statuses ---
    allowed_statuses = {"raw", "exploring", "actionable", "parked", "done"}
    status_lines = re.findall(r'\*\*Статус:\*\*\s*(\w+)', content)
    statuses_valid = all(s in allowed_statuses for s in status_lines)
    checks.append({
        "name": "valid_statuses_only",
        "passed": statuses_valid and len(status_lines) >= 4,
        "detail": f"Statuses found: {status_lines}. All must be from: {allowed_statuses}. Count must be >= 4."
    })

    # --- Check 5: Status update for "Ноу-код конструктор лендингов" ---
    # The prompt asks to update it to "actionable" (since the new resume AI idea connects to it and makes it more concrete)
    # Actually, let's check that "Ноу-код конструктор лендингов" idea has its status changed from "raw"
    # We'll look for the section and check status
    nocode_section = re.search(
        r'(## \[2024-10-25\] Ноу-код конструктор лендингов для фрилансеров.*?)(?=^## |\Z)',
        content, re.DOTALL | re.MULTILINE
    )
    status_updated = False
    if nocode_section:
        section_text = nocode_section.group(1)
        status_match = re.search(r'\*\*Статус:\*\*\s*(\w+)', section_text)
        if status_match:
            new_status = status_match.group(1)
            # Should be changed from "raw" to something else (actionable or exploring)
            status_updated = new_status in {"actionable", "exploring"}
    checks.append({
        "name": "nocode_idea_status_updated",
        "passed": status_updated,
        "detail": f"'Ноу-код конструктор лендингов' idea status should be updated from 'raw' to 'actionable' or 'exploring' given the connection to new ideas. Found status: {status_match.group(1) if nocode_section and status_match else 'NOT FOUND'}"
    })

    # --- Check 6: Connection noted somewhere (between old and new ideas) ---
    # The agent must note connections; look for cross-reference language
    connection_keywords = ["связан", "похож", "пересека", "connection", "связь", "похожа", "аналог", "ноу-код", "конструктор", "фрилансер"]
    # Check that in the new sections (after the original 3), there's a connection noted
    # We look for connection language in ANY new entry or as an explicit note
    new_content_after_original = content
    connection_mentioned = False

    # Look for connections in new ideas (keywords appearing near each other or in description)
    # Specifically: AI резюме + ноу-код конструктор for freelancers are connected
    connection_patterns = [
        r'(связ|пересека|похож|connection)',  # generic connection words
    ]
    for pat in connection_patterns:
        if re.search(pat, content, re.IGNORECASE):
            connection_mentioned = True
            break

    checks.append({
        "name": "connection_between_ideas_noted",
        "passed": connection_mentioned,
        "detail": f"At least one connection between ideas must be explicitly noted. Connection keywords found: {connection_mentioned}"
    })

    # --- Scoring ---
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = passed_checks >= 5  # Must pass at least 5 out of 6

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))