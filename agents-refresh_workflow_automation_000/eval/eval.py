import sys
import json
import re
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def run_checks(workspace):
    checks = []
    score_total = 0.0
    weight_total = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal score_total, weight_total
        weight_total += weight
        if passed:
            score_total += weight

    workspace = Path(workspace)

    # ============================================================
    # CHECK GROUP 1: MEMORY.md existence and structure
    # ============================================================
    memory_candidates = list(workspace.rglob("MEMORY.md"))
    if not memory_candidates:
        add_check("MEMORY.md exists", False, "MEMORY.md not found anywhere in workspace.", weight=2.0)
        memory_content = None
    else:
        memory_content = memory_candidates[0].read_text(encoding="utf-8", errors="replace")
        add_check("MEMORY.md exists", True, f"Found at {memory_candidates[0]}", weight=2.0)

    if memory_content is not None:
        # Check for exact emoji-decorated section headers from SKILL.md
        has_key_decisions = bool(re.search(r'##\s+Key Decisions\s+💎', memory_content))
        add_check(
            "MEMORY.md has '## Key Decisions 💎' section",
            has_key_decisions,
            f"Found: {has_key_decisions}. Content snippet: {memory_content[:300]}",
            weight=1.5
        )

        has_next_actions = bool(re.search(r'##\s+Next Actions\s+⚡', memory_content))
        add_check(
            "MEMORY.md has '## Next Actions ⚡' section",
            has_next_actions,
            f"Found: {has_next_actions}",
            weight=1.5
        )

        has_insights = bool(re.search(r'##\s+Insights\s*[&＆]\s*Lessons\s+🚫', memory_content))
        add_check(
            "MEMORY.md has '## Insights & Lessons 🚫' section",
            has_insights,
            f"Found: {has_insights}",
            weight=1.5
        )

        has_seeds = bool(re.search(r'##\s+Creative Seeds\s+🌱', memory_content))
        add_check(
            "MEMORY.md has '## Creative Seeds 🌱' section",
            has_seeds,
            f"Found: {has_seeds}",
            weight=1.5
        )

        # Check that actual distilled content is present (not empty sections)
        # Key decisions from logs: no procedural dungeons, JSON save system, PC+Linux only, MIT license
        has_decisions_content = bool(re.search(
            r'(procedural|dungeon|JSON|save system|PC|Linux|MIT|hand.crafted)',
            memory_content, re.IGNORECASE
        ))
        add_check(
            "MEMORY.md Key Decisions contains distilled project decisions",
            has_decisions_content,
            f"Expected at least one of: procedural/dungeon/JSON/save/PC/Linux/MIT. Found: {has_decisions_content}",
            weight=2.0
        )

        # Next actions: wall-jump fixed but save/load, sound effects, unit tests pending
        has_actions_content = bool(re.search(
            r'(save.?load|sound effect|unit test|corrupt|UI screen)',
            memory_content, re.IGNORECASE
        ))
        add_check(
            "MEMORY.md Next Actions contains pending tasks from logs",
            has_actions_content,
            f"Expected at least one of: save/load, sound effect, unit test, corrupt. Found: {has_actions_content}",
            weight=2.0
        )

        # Lessons: naming convention, design doc before feature, test with corrupted saves
        has_lessons_content = bool(re.search(
            r'(naming|convention|design doc|spec|corrupt|CI|variable)',
            memory_content, re.IGNORECASE
        ))
        add_check(
            "MEMORY.md Insights & Lessons contains lessons from logs",
            has_lessons_content,
            f"Expected at least one of: naming/convention/design doc/spec/corrupt/CI. Found: {has_lessons_content}",
            weight=1.5
        )

        # Seeds: enemy double jump, nightmare mode, adaptive music, speedrun timer, level editor
        has_seeds_content = bool(re.search(
            r'(double.jump|nightmare|adaptive music|speedrun|level editor|easter egg|composer)',
            memory_content, re.IGNORECASE
        ))
        add_check(
            "MEMORY.md Creative Seeds contains idea seeds from logs",
            has_seeds_content,
            f"Expected at least one of: double jump/nightmare/adaptive music/speedrun/level editor. Found: {has_seeds_content}",
            weight=1.5
        )

    # ============================================================
    # CHECK GROUP 2: HEARTBEAT.md has the refresh task entry
    # ============================================================
    heartbeat_path = workspace / "HEARTBEAT.md"
    heartbeat_content = load_file(heartbeat_path)

    if heartbeat_content is None:
        add_check("HEARTBEAT.md exists", False, "HEARTBEAT.md not found at workspace/HEARTBEAT.md", weight=2.0)
    else:
        add_check("HEARTBEAT.md exists", True, "Found.", weight=0.5)

        # Must have a refresh task in checkbox format
        has_refresh_checkbox = bool(re.search(r'-\s*\[\s*\]\s*Refresh', heartbeat_content, re.IGNORECASE))
        add_check(
            "HEARTBEAT.md has '- [ ] Refresh:' task entry",
            has_refresh_checkbox,
            f"Found checkbox refresh entry: {has_refresh_checkbox}",
            weight=2.0
        )

        # Must reference the workspace md files
        has_workspace_files = bool(re.search(
            r'workspace/\{?.*AGENTS\.md.*IDENTITY\.md.*SOUL\.md|workspace/\{?.*SOUL\.md.*IDENTITY\.md.*AGENTS\.md',
            heartbeat_content, re.IGNORECASE
        )) or bool(re.search(r'AGENTS\.md', heartbeat_content) and re.search(r'IDENTITY\.md', heartbeat_content) and re.search(r'SOUL\.md', heartbeat_content))
        add_check(
            "HEARTBEAT.md refresh entry references AGENTS/IDENTITY/SOUL md files",
            has_workspace_files,
            f"Expected references to AGENTS.md, IDENTITY.md, SOUL.md. Found: {has_workspace_files}",
            weight=1.5
        )

        # Must reference rotation times (4h or 9AM or 1PM or 8PM pattern)
        has_rotation = bool(re.search(r'(4h|9AM|1PM|8PM|rotate)', heartbeat_content, re.IGNORECASE))
        add_check(
            "HEARTBEAT.md refresh entry includes rotation schedule hint",
            has_rotation,
            f"Expected rotation times (4h/9AM/1PM/8PM). Found: {has_rotation}",
            weight=1.0
        )

        # Must mention MEMORY or summarize
        has_memory_ref = bool(re.search(r'(MEMORY|summarize|Summarize)', heartbeat_content))
        add_check(
            "HEARTBEAT.md refresh entry mentions MEMORY summarization",
            has_memory_ref,
            f"Expected MEMORY/Summarize reference. Found: {has_memory_ref}",
            weight=1.0
        )

    # ============================================================
    # CHECK GROUP 3: cron_command.txt with correct JSON schema
    # ============================================================
    cron_candidates = list(workspace.rglob("cron_command.txt"))
    if not cron_candidates:
        add_check("cron_command.txt exists", False, "cron_command.txt not found anywhere in workspace.", weight=2.0)
        cron_content = None
    else:
        cron_content = cron_candidates[0].read_text(encoding="utf-8", errors="replace")
        add_check("cron_command.txt exists", True, f"Found at {cron_candidates[0]}", weight=0.5)

    if cron_content is not None:
        # Try to extract JSON from the cron command (may have 'cron action=add job=...' prefix)
        json_match = re.search(r'\{.*\}', cron_content, re.DOTALL)
        cron_json = None
        if json_match:
            try:
                cron_json = json.loads(json_match.group(0))
            except Exception as e:
                add_check("cron_command.txt contains valid JSON", False, f"JSON parse error: {e}", weight=3.0)
                cron_json = None

        if cron_json is not None:
            add_check("cron_command.txt contains valid JSON", True, "Parsed successfully.", weight=0.5)

            # Check job name
            correct_name = cron_json.get("name") == "agents-refresh-daily"
            add_check(
                "cron JSON: name is 'agents-refresh-daily'",
                correct_name,
                f"Got name: {cron_json.get('name')}",
                weight=1.5
            )

            # Check schedule
            schedule = cron_json.get("schedule", {})
            correct_kind = schedule.get("kind") == "cron"
            add_check(
                "cron JSON: schedule.kind is 'cron'",
                correct_kind,
                f"Got schedule.kind: {schedule.get('kind')}",
                weight=1.5
            )

            correct_expr = schedule.get("expr") == "0 6 * * *"
            add_check(
                "cron JSON: schedule.expr is '0 6 * * *'",
                correct_expr,
                f"Got schedule.expr: {schedule.get('expr')}",
                weight=1.5
            )

            correct_tz = schedule.get("tz") == "Asia/Tokyo"
            add_check(
                "cron JSON: schedule.tz is 'Asia/Tokyo'",
                correct_tz,
                f"Got schedule.tz: {schedule.get('tz')}",
                weight=1.5
            )

            # Check payload
            payload = cron_json.get("payload", {})
            correct_payload_kind = payload.get("kind") == "systemEvent"
            add_check(
                "cron JSON: payload.kind is 'systemEvent'",
                correct_payload_kind,
                f"Got payload.kind: {payload.get('kind')}",
                weight=1.5
            )

            has_payload_text = bool(payload.get("text") and len(str(payload.get("text"))) > 20)
            add_check(
                "cron JSON: payload.text is non-empty",
                has_payload_text,
                f"Got payload.text: {str(payload.get('text'))[:80]}",
                weight=1.0
            )

            # Check delivery
            delivery = cron_json.get("delivery", {})
            correct_delivery_mode = delivery.get("mode") == "announce"
            add_check(
                "cron JSON: delivery.mode is 'announce'",
                correct_delivery_mode,
                f"Got delivery.mode: {delivery.get('mode')}",
                weight=1.5
            )

            # Check sessionTarget
            correct_session_target = cron_json.get("sessionTarget") == "main"
            add_check(
                "cron JSON: sessionTarget is 'main'",
                correct_session_target,
                f"Got sessionTarget: {cron_json.get('sessionTarget')}",
                weight=1.5
            )

            # Check task
            correct_task = cron_json.get("task") == "refresh_memory"
            add_check(
                "cron JSON: task is 'refresh_memory'",
                correct_task,
                f"Got task: {cron_json.get('task')}",
                weight=1.5
            )

        elif json_match is None:
            add_check("cron_command.txt contains valid JSON", False, "No JSON object found in file.", weight=3.0)

    # ============================================================
    # FINAL SCORING
    # ============================================================
    final_score = round(score_total / weight_total, 4) if weight_total > 0 else 0.0
    passed = final_score >= 0.70

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))