import sys
import json
import re
from pathlib import Path

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ─────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 1: user_settings.json exists with correct mode = "passive"
    # The task requires setting mode to passive (被动模式) and
    # frequency to realtime (实时)
    # ══════════════════════════════════════════════════════════════════════
    settings_path = workspace / "skills" / "memory-auto-update" / "data" / "user_settings.json"
    try:
        if not settings_path.exists():
            total_score += add_check(
                "settings_file_exists",
                False,
                f"user_settings.json not found at {settings_path}"
            )
        else:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            total_score += add_check(
                "settings_file_exists",
                True,
                f"user_settings.json found at {settings_path}"
            )

            # Check mode = passive
            mode_ok = settings.get("update_mode") == "passive"
            total_score += add_check(
                "settings_mode_passive",
                mode_ok,
                f"update_mode = '{settings.get('update_mode')}', expected 'passive'"
            )

            # Check frequency = realtime
            freq_ok = settings.get("update_frequency") == "realtime"
            total_score += add_check(
                "settings_frequency_realtime",
                freq_ok,
                f"update_frequency = '{settings.get('update_frequency')}', expected 'realtime'"
            )
    except Exception as e:
        total_score += add_check("settings_file_exists", False, f"Exception reading settings: {e}")
        total_score += add_check("settings_mode_passive", False, "Could not read settings file")
        total_score += add_check("settings_frequency_realtime", False, "Could not read settings file")

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 2: Intermediate extracted JSON exists somewhere in workspace
    # ══════════════════════════════════════════════════════════════════════
    try:
        extracted_files = list(workspace.rglob("*.json"))
        # Look for a JSON file that contains extracted categories
        found_extracted = False
        extracted_data = {}
        for f in extracted_files:
            if f.name in ("user_settings.json", "default_settings.json", "_meta.json", "scratch.json"):
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                # A valid extracted file should have at least one category key
                valid_cats = {"decision", "todo", "appointment", "fact", "preference", "project"}
                if isinstance(data, dict) and any(k in valid_cats for k in data.keys()):
                    found_extracted = True
                    extracted_data = data
                    break
            except Exception:
                continue
        total_score += add_check(
            "extracted_json_exists",
            found_extracted,
            "Found intermediate extracted JSON with valid categories" if found_extracted
            else "No intermediate extracted JSON with memory categories found"
        )
    except Exception as e:
        total_score += add_check("extracted_json_exists", False, f"Exception: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 3: Memory file written to memory/2024-03-15.md
    # ══════════════════════════════════════════════════════════════════════
    memory_file = workspace / "memory" / "2024-03-15.md"
    memory_content = ""
    try:
        if not memory_file.exists():
            # Also search broadly
            candidates = list(workspace.rglob("2024-03-15.md"))
            if candidates:
                memory_file = candidates[0]
                memory_content = memory_file.read_text(encoding="utf-8")
                total_score += add_check(
                    "memory_file_exists",
                    True,
                    f"Memory file found at {memory_file} (not in expected memory/ dir)"
                )
            else:
                total_score += add_check(
                    "memory_file_exists",
                    False,
                    "Memory file 2024-03-15.md not found anywhere in workspace"
                )
        else:
            memory_content = memory_file.read_text(encoding="utf-8")
            total_score += add_check(
                "memory_file_exists",
                True,
                f"Memory file found at expected path {memory_file}"
            )
    except Exception as e:
        total_score += add_check("memory_file_exists", False, f"Exception: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 4: Memory file has correct H1 header format "# 2024-03-15 记忆"
    # ══════════════════════════════════════════════════════════════════════
    try:
        if memory_content:
            has_h1 = bool(re.search(r'^#\s+2024-03-15\s+记忆', memory_content, re.MULTILINE))
            total_score += add_check(
                "memory_h1_header",
                has_h1,
                f"H1 header '# 2024-03-15 记忆' {'found' if has_h1 else 'NOT found'} in memory file"
            )
        else:
            total_score += add_check("memory_h1_header", False, "Memory file is empty or missing")
    except Exception as e:
        total_score += add_check("memory_h1_header", False, f"Exception: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 5: Memory file has "## 今日事项" section
    # ══════════════════════════════════════════════════════════════════════
    try:
        if memory_content:
            has_section = bool(re.search(r'^##\s+今日事项', memory_content, re.MULTILINE))
            total_score += add_check(
                "memory_section_header",
                has_section,
                f"Section '## 今日事项' {'found' if has_section else 'NOT found'}"
            )
        else:
            total_score += add_check("memory_section_header", False, "Memory file empty or missing")
    except Exception as e:
        total_score += add_check("memory_section_header", False, f"Exception: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 6: Memory file has at least one "### " subsection
    # ══════════════════════════════════════════════════════════════════════
    try:
        if memory_content:
            has_subsection = bool(re.search(r'^###\s+\S+', memory_content, re.MULTILINE))
            total_score += add_check(
                "memory_subsection",
                has_subsection,
                f"At least one '### ' subsection {'found' if has_subsection else 'NOT found'}"
            )
        else:
            total_score += add_check("memory_subsection", False, "Memory file empty or missing")
    except Exception as e:
        total_score += add_check("memory_subsection", False, f"Exception: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 7: Memory file uses bold-field format "**决策：**" or "**待办：**" etc.
    # Must have at least 2 bold field entries of the proprietary format
    # ══════════════════════════════════════════════════════════════════════
    try:
        if memory_content:
            bold_fields = re.findall(r'\*\*(决策|待办|约定|事实|偏好|项目|事件)：\*\*', memory_content)
            has_bold_fields = len(bold_fields) >= 2
            total_score += add_check(
                "memory_bold_field_format",
                has_bold_fields,
                f"Found {len(bold_fields)} bold field entries (need ≥2): {bold_fields[:5]}"
            )
        else:
            total_score += add_check("memory_bold_field_format", False, "Memory file empty or missing")
    except Exception as e:
        total_score += add_check("memory_bold_field_format", False, f"Exception: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 8: Memory file contains key decision content (方案B)
    # ══════════════════════════════════════════════════════════════════════
    try:
        if memory_content:
            has_decision = bool(re.search(r'方案B|方案 B|采用方案', memory_content))
            total_score += add_check(
                "memory_contains_decision",
                has_decision,
                f"Key decision content (方案B) {'found' if has_decision else 'NOT found'} in memory"
            )
        else:
            total_score += add_check("memory_contains_decision", False, "Memory file empty or missing")
    except Exception as e:
        total_score += add_check("memory_contains_decision", False, f"Exception: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 9: Memory file contains todo item with [ ] checkbox format
    # ══════════════════════════════════════════════════════════════════════
    try:
        if memory_content:
            has_todo_checkbox = bool(re.search(r'\*\*待办：\*\*\s*\[\s*\]', memory_content))
            total_score += add_check(
                "memory_todo_checkbox_format",
                has_todo_checkbox,
                f"Todo checkbox format '**待办：** [ ]' {'found' if has_todo_checkbox else 'NOT found'}"
            )
        else:
            total_score += add_check("memory_todo_checkbox_format", False, "Memory file empty or missing")
    except Exception as e:
        total_score += add_check("memory_todo_checkbox_format", False, f"Exception: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 10: Memory file contains factual data (预算 50万 or 留存率 62%)
    # ══════════════════════════════════════════════════════════════════════
    try:
        if memory_content:
            has_fact = bool(re.search(r'50万|50 万|62%|留存率|预算', memory_content))
            total_score += add_check(
                "memory_contains_fact",
                has_fact,
                f"Factual data (budget/retention rate) {'found' if has_fact else 'NOT found'} in memory"
            )
        else:
            total_score += add_check("memory_contains_fact", False, "Memory file empty or missing")
    except Exception as e:
        total_score += add_check("memory_contains_fact", False, f"Exception: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # FINAL SCORE
    # ══════════════════════════════════════════════════════════════════════
    num_checks = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / num_checks if num_checks > 0 else 0.0
    overall_passed = score >= 0.75  # Need at least 75% to pass

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))