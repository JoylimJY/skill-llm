import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ──────────────────────────────────────────────────────────────────────────
    # FIND THE BRIEF FILE
    # ──────────────────────────────────────────────────────────────────────────
    brief_files = list(workspace.rglob("payments_handoff_brief.md"))
    # Also check home directory
    home = Path.home()
    brief_files += list(home.rglob("payments_handoff_brief.md"))
    brief_files = list(set(brief_files))

    brief_content = ""
    brief_found = len(brief_files) > 0

    checks.append({
        "name": "brief_file_exists",
        "passed": brief_found,
        "detail": f"Found payments_handoff_brief.md at: {[str(f) for f in brief_files]}" if brief_found else "payments_handoff_brief.md not found anywhere in workspace or home."
    })

    if brief_found:
        try:
            brief_content = brief_files[0].read_text(encoding="utf-8")
        except Exception as e:
            checks.append({"name": "brief_file_readable", "passed": False, "detail": str(e)})
            brief_content = ""

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 1: Header line format  📋 [BRIEF TYPE] — [SUBJECT]
    # Must contain the 📋 emoji, the word "Handoff" (correct type), and an em-dash —
    # ──────────────────────────────────────────────────────────────────────────
    header_pattern = re.compile(r"📋\s+Handoff\s*[—–-]\s+\S", re.IGNORECASE)
    header_ok = bool(header_pattern.search(brief_content))
    checks.append({
        "name": "brief_header_format_with_emoji",
        "passed": header_ok,
        "detail": f"Brief must start with '📋 Handoff — [Subject]'. Found: {brief_content[:120]!r}" if not header_ok else "Header format correct with 📋 emoji and Handoff type."
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 2: ⚡ BOTTOM LINE section present
    # ──────────────────────────────────────────────────────────────────────────
    bottom_line_ok = "⚡" in brief_content and "BOTTOM LINE" in brief_content.upper()
    checks.append({
        "name": "bottom_line_section_with_emoji",
        "passed": bottom_line_ok,
        "detail": "Must have '⚡ BOTTOM LINE' section with the ⚡ emoji." if not bottom_line_ok else "⚡ BOTTOM LINE section found."
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 3: 📊 KEY POINTS section present
    # ──────────────────────────────────────────────────────────────────────────
    key_points_ok = "📊" in brief_content and "KEY POINTS" in brief_content.upper()
    checks.append({
        "name": "key_points_section_with_emoji",
        "passed": key_points_ok,
        "detail": "Must have '📊 KEY POINTS' section with the 📊 emoji." if not key_points_ok else "📊 KEY POINTS section found."
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 4: 🎯 ACTION NEEDED section present
    # ──────────────────────────────────────────────────────────────────────────
    action_needed_ok = "🎯" in brief_content and "ACTION NEEDED" in brief_content.upper()
    checks.append({
        "name": "action_needed_section_with_emoji",
        "passed": action_needed_ok,
        "detail": "Must have '🎯 ACTION NEEDED' section with the 🎯 emoji." if not action_needed_ok else "🎯 ACTION NEEDED section found."
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 5: Handoff-type key elements present — Current state, gotchas, priorities
    # The Handoff type specifically requires: Current state, gotchas, priorities
    # Check that these themes are represented in the brief content
    # ──────────────────────────────────────────────────────────────────────────
    content_lower = brief_content.lower()
    has_current_state = any(term in content_lower for term in ["current state", "running", "live", "transaction", "production", "k8s", "kubernetes"])
    has_gotchas = any(term in content_lower for term in ["gotcha", "warning", "caution", "off-by-one", "retry", "pay-441", "bug", "silent", "vault token", "manual"])
    has_priorities = any(term in content_lower for term in ["priorit", "p0", "p1", "next 30", "fix", "rotate", "audit"])

    handoff_elements_ok = has_current_state and has_gotchas and has_priorities
    checks.append({
        "name": "handoff_type_elements_present",
        "passed": handoff_elements_ok,
        "detail": (
            f"Handoff brief must cover: current state ({has_current_state}), "
            f"gotchas ({has_gotchas}), priorities ({has_priorities}). "
            "All three must be present from raw_notes.txt."
        ) if not handoff_elements_ok else "Handoff elements (current state, gotchas, priorities) all present."
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 6: Key factual content from source notes (PAY-441, Vault rotation, staging/prod)
    # ──────────────────────────────────────────────────────────────────────────
    has_pay441 = "pay-441" in content_lower or "pay441" in content_lower or "retry" in content_lower
    has_vault = "vault" in content_lower
    has_staging_prod = ("staging" in content_lower and "prod" in content_lower) or "pay-388" in content_lower or "tokenization" in content_lower
    source_content_ok = has_pay441 and has_vault and has_staging_prod
    checks.append({
        "name": "key_source_content_included",
        "passed": source_content_ok,
        "detail": (
            f"Must include key content from raw_notes.txt: "
            f"PAY-441/retry bug ({has_pay441}), Vault token rotation ({has_vault}), "
            f"staging/prod credential issue ({has_staging_prod})."
        ) if not source_content_ok else "Key factual content from source notes is present."
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 7: preferences.md exists at ~/brief/preferences.md
    # ──────────────────────────────────────────────────────────────────────────
    prefs_path = Path.home() / "brief" / "preferences.md"
    prefs_exist = prefs_path.exists()
    checks.append({
        "name": "preferences_file_exists_at_correct_path",
        "passed": prefs_exist,
        "detail": f"~/brief/preferences.md {'found' if prefs_exist else 'NOT found'}. Path checked: {prefs_path}"
    })

    prefs_content = ""
    if prefs_exist:
        try:
            prefs_content = prefs_path.read_text(encoding="utf-8")
        except Exception as e:
            checks.append({"name": "preferences_file_readable", "passed": False, "detail": str(e)})

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 8: preferences.md uses correct ONE-LINE-PER-PREFERENCE format
    # Each line must start with "- " and be a single-line preference (not a paragraph)
    # Must NOT store brief content — only format preferences
    # ──────────────────────────────────────────────────────────────────────────
    pref_lines = [line.strip() for line in prefs_content.splitlines() if line.strip()]
    # Filter out empty lines and check each non-empty line starts with "- "
    valid_format_lines = [l for l in pref_lines if l.startswith("- ")]
    # No lines should be longer than ~200 chars (no paragraphs)
    no_paragraphs = all(len(l) < 200 for l in pref_lines)
    format_ok = len(valid_format_lines) >= 2 and no_paragraphs and len(valid_format_lines) == len(pref_lines)
    checks.append({
        "name": "preferences_correct_format",
        "passed": format_ok,
        "detail": (
            f"Each preference must be on its own line starting with '- '. "
            f"Found {len(valid_format_lines)} valid lines out of {len(pref_lines)} total. "
            f"No paragraphs: {no_paragraphs}. Sample: {pref_lines[:3]}"
        ) if not format_ok else f"Correct format: {len(valid_format_lines)} preference lines."
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 9: Preferences reflect the 3 stated user preferences from task.md
    # 1. metrics when available  2. concise/no paragraphs  3. critical risk/action first
    # ──────────────────────────────────────────────────────────────────────────
    prefs_lower = prefs_content.lower()
    has_metrics_pref = any(term in prefs_lower for term in ["metric", "data", "number", "quantitative"])
    has_concise_pref = any(term in prefs_lower for term in ["concise", "brief", "short", "bullet", "no paragraph", "point"])
    has_priority_pref = any(term in prefs_lower for term in ["critical", "risk", "priority", "first", "top", "important"])
    pref_content_ok = has_metrics_pref and has_concise_pref and has_priority_pref
    checks.append({
        "name": "preferences_reflect_user_feedback",
        "passed": pref_content_ok,
        "detail": (
            f"Preferences must encode: metrics ({has_metrics_pref}), "
            f"concise/bullets ({has_concise_pref}), critical-first ({has_priority_pref})."
        ) if not pref_content_ok else "All 3 stated user preferences are recorded."
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 10: ~/brief/templates directory was created (first-use setup)
    # ──────────────────────────────────────────────────────────────────────────
    templates_dir = Path.home() / "brief" / "templates"
    templates_dir_ok = templates_dir.exists() and templates_dir.is_dir()
    checks.append({
        "name": "brief_templates_directory_created",
        "passed": templates_dir_ok,
        "detail": f"~/brief/templates/ {'exists' if templates_dir_ok else 'was NOT created'}. SKILL.md requires: mkdir -p ~/brief/templates on first use."
    })

    # ──────────────────────────────────────────────────────────────────────────
    # SCORING
    # ──────────────────────────────────────────────────────────────────────────
    weights = {
        "brief_file_exists": 1.0,
        "brief_header_format_with_emoji": 1.5,
        "bottom_line_section_with_emoji": 1.5,
        "key_points_section_with_emoji": 1.5,
        "action_needed_section_with_emoji": 1.5,
        "handoff_type_elements_present": 1.5,
        "key_source_content_included": 1.0,
        "preferences_file_exists_at_correct_path": 1.0,
        "preferences_correct_format": 1.5,
        "preferences_reflect_user_feedback": 1.0,
        "brief_templates_directory_created": 0.5,
    }

    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 1.0) for c in checks if c["passed"])
    score = round(earned / total_weight, 4)
    passed = score >= 0.75 and checks[0]["passed"]  # must at least have the file

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))