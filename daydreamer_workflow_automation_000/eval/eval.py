import sys
import json
import re
from pathlib import Path

def load_json_safe(path, label):
    try:
        with open(path) as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"{label}: file not found at {path}"
    except json.JSONDecodeError as e:
        return None, f"{label}: JSON parse error — {e}"

def main(workspace):
    ws = Path(workspace)
    skill_dir = ws / ".claude" / "skills" / "daydreamer"
    checks = []
    total_score = 0.0

    # ── CHECK 1: daydreamer-config.json exists and is valid ───────────────────
    config_path = ws / "daydreamer-config.json"
    cfg, err = load_json_safe(config_path, "daydreamer-config.json")
    c1_passed = cfg is not None
    checks.append({
        "name": "config_exists_and_valid_json",
        "passed": c1_passed,
        "detail": err if err else f"Found config at {config_path}"
    })
    if c1_passed:
        total_score += 0.05

    # ── CHECK 2: config has required keys ─────────────────────────────────────
    required_keys = {"frequency", "cycles_per_session", "default_daydream_type", "session_count"}
    if cfg:
        missing = required_keys - set(cfg.keys())
        c2_passed = len(missing) == 0
        checks.append({
            "name": "config_has_required_keys",
            "passed": c2_passed,
            "detail": f"Missing keys: {missing}" if missing else f"All required keys present: {required_keys}"
        })
        if c2_passed:
            total_score += 0.05
    else:
        checks.append({"name": "config_has_required_keys", "passed": False, "detail": "Config file missing"})

    # ── CHECK 3: default_daydream_type is "idea" (as task requires) ───────────
    if cfg:
        ddt = cfg.get("default_daydream_type", "")
        # The task asks for "idea" type daydream, so the agent should have configured "idea"
        c3_passed = ddt == "idea"
        checks.append({
            "name": "config_default_type_is_idea",
            "passed": c3_passed,
            "detail": f"default_daydream_type = '{ddt}' (expected 'idea')"
        })
        if c3_passed:
            total_score += 0.05
    else:
        checks.append({"name": "config_default_type_is_idea", "passed": False, "detail": "Config file missing"})

    # ── CHECK 4: Daydreams.MD exists and has memories ─────────────────────────
    dreams_path = ws / "Daydreams.MD"
    try:
        dreams_content = dreams_path.read_text()
        memory_lines = [l.strip() for l in dreams_content.splitlines() if re.match(r'^\d+\.\s+.+', l.strip())]
        c4_passed = len(memory_lines) >= 10
        checks.append({
            "name": "daydreams_md_has_memories",
            "passed": c4_passed,
            "detail": f"Found {len(memory_lines)} memory entries (need ≥10)"
        })
        if c4_passed:
            total_score += 0.10
    except FileNotFoundError:
        checks.append({"name": "daydreams_md_has_memories", "passed": False, "detail": "Daydreams.MD not found"})
        memory_lines = []

    # ── CHECK 5: memories are properly formatted (WHO WHAT WHY, no timestamps) ─
    if memory_lines:
        good_format = 0
        bad_format = []
        for line in memory_lines[:20]:  # sample first 20
            # Should have a verb-like structure, not just numbers/timestamps
            # Memory format: "N. [WHO] [WHAT]. [WHY if clear]"
            body = re.sub(r'^\d+\.\s+', '', line)
            has_timestamp = bool(re.search(r'\d{4}-\d{2}-\d{2}|\d{2}:\d{2}', body))
            has_content = len(body) > 20
            is_reasonable = not has_timestamp and has_content
            if is_reasonable:
                good_format += 1
            else:
                bad_format.append(body[:60])
        ratio = good_format / min(len(memory_lines), 20)
        c5_passed = ratio >= 0.7
        checks.append({
            "name": "memories_correctly_formatted",
            "passed": c5_passed,
            "detail": f"{good_format}/{min(len(memory_lines),20)} memories pass format check. Bad examples: {bad_format[:3]}"
        })
        if c5_passed:
            total_score += 0.05
    else:
        checks.append({"name": "memories_correctly_formatted", "passed": False, "detail": "No memories to check"})

    # ── CHECK 6: Memories are meaningful (not heartbeats/empty checks) ─────────
    if memory_lines:
        trivial_patterns = [r'heartbeat', r'no work', r'idle', r'status check', r'polling', r'empty']
        trivial_count = 0
        for line in memory_lines:
            body = re.sub(r'^\d+\.\s+', '', line).lower()
            if any(re.search(p, body) for p in trivial_patterns):
                trivial_count += 1
        c6_passed = trivial_count == 0
        checks.append({
            "name": "no_trivial_memories",
            "passed": c6_passed,
            "detail": f"{trivial_count} trivial/heartbeat entries found (should be 0)"
        })
        if c6_passed:
            total_score += 0.05
    else:
        checks.append({"name": "no_trivial_memories", "passed": False, "detail": "No memories to check"})

    # ── CHECK 7: ideas/ directory exists with at least one idea file ──────────
    ideas_dir = ws / "ideas"
    try:
        idea_files = sorted(ideas_dir.glob("*.md"))
        c7_passed = len(idea_files) >= 1
        checks.append({
            "name": "ideas_directory_has_file",
            "passed": c7_passed,
            "detail": f"Found {len(idea_files)} idea file(s): {[f.name for f in idea_files]}"
        })
        if c7_passed:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "ideas_directory_has_file", "passed": False, "detail": str(e)})
        idea_files = []

    # ── CHECK 8: idea file has required structure (synthesis, memory trail) ────
    if idea_files:
        idea_path = idea_files[0]
        try:
            idea_content = idea_path.read_text()
            has_synthesis = "## Synthesis" in idea_content or "synthesis" in idea_content.lower()
            has_memory_trail = "Memory Trail" in idea_content or "Seed" in idea_content or "Cycle" in idea_content
            has_content = len(idea_content.strip()) > 100
            c8_passed = has_synthesis and has_memory_trail and has_content
            checks.append({
                "name": "idea_file_has_required_structure",
                "passed": c8_passed,
                "detail": f"synthesis={has_synthesis}, memory_trail={has_memory_trail}, content_length={len(idea_content)}"
            })
            if c8_passed:
                total_score += 0.10
        except Exception as e:
            checks.append({"name": "idea_file_has_required_structure", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "idea_file_has_required_structure", "passed": False, "detail": "No idea files found"})

    # ── CHECK 9: Daydreamlog.MD exists and has a session entry ────────────────
    log_path = ws / "Daydreamlog.MD"
    try:
        log_content = log_path.read_text()
        has_session = "Session" in log_content and len(log_content.strip()) > 50
        has_synthesis = "Synthesis" in log_content
        c9_passed = has_session and has_synthesis
        checks.append({
            "name": "daydreamlog_has_session_entry",
            "passed": c9_passed,
            "detail": f"Log length: {len(log_content)}, has_session={has_session}, has_synthesis={has_synthesis}"
        })
        if c9_passed:
            total_score += 0.10
    except FileNotFoundError:
        checks.append({"name": "daydreamlog_has_session_entry", "passed": False, "detail": "Daydreamlog.MD not found"})

    # ── CHECK 10: session used --forced (last_daydream_date should be None or unchanged) ─
    # The daydream was forced, so last_daydream_date should NOT be today's date
    # (or may remain None from initial config if no non-forced session ran)
    # We verify: session_count > 0 (a session happened) but forced was respected
    if cfg:
        session_count = cfg.get("session_count", 0)
        c10_passed = session_count >= 1
        checks.append({
            "name": "session_count_incremented",
            "passed": c10_passed,
            "detail": f"session_count = {session_count} (expected ≥1, indicates finalize was called)"
        })
        if c10_passed:
            total_score += 0.10
    else:
        checks.append({"name": "session_count_incremented", "passed": False, "detail": "Config missing"})

    # ── CHECK 11: .daydream-session/ was cleaned up after finalize ────────────
    session_dir = ws / ".daydream-session"
    c11_passed = not session_dir.exists()
    checks.append({
        "name": "session_directory_cleaned_up",
        "passed": c11_passed,
        "detail": f".daydream-session/ {'does not exist (correct)' if c11_passed else 'still exists (finalize should clean it up)'}"
    })
    if c11_passed:
        total_score += 0.10

    # ── CHECK 12: idea file is for "idea" type daydream ───────────────────────
    if idea_files:
        idea_path = idea_files[0]
        try:
            idea_content = idea_path.read_text()
            # Should mention idea type
            c12_passed = "idea" in idea_content.lower()
            checks.append({
                "name": "idea_file_is_type_idea",
                "passed": c12_passed,
                "detail": f"Idea file {'mentions' if c12_passed else 'does not mention'} 'idea' type"
            })
            if c12_passed:
                total_score += 0.05
        except Exception as e:
            checks.append({"name": "idea_file_is_type_idea", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "idea_file_is_type_idea", "passed": False, "detail": "No idea files found"})

    # ── CHECK 13: cycle log entries in idea file use correct format ───────────
    if idea_files:
        idea_path = idea_files[0]
        try:
            idea_content = idea_path.read_text()
            # Look for cycle log entries with mode format: [Cycle N | Mode X] ...
            cycle_entries = re.findall(r'\[Cycle \d+\s*\|\s*Mode \d+\]', idea_content)
            # Also check Daydreamlog.MD
            log_content_str = ""
            try:
                log_content_str = log_path.read_text()
            except Exception:
                pass
            cycle_entries_log = re.findall(r'\[Cycle \d+\s*\|\s*Mode \d+\]', log_content_str)
            total_cycle_entries = len(cycle_entries) + len(cycle_entries_log)
            c13_passed = total_cycle_entries >= 3  # At least 3 cycles logged with proper format
            checks.append({
                "name": "cycle_log_entries_correct_format",
                "passed": c13_passed,
                "detail": f"Found {total_cycle_entries} properly-formatted cycle log entries across idea file and log (need ≥3)"
            })
            if c13_passed:
                total_score += 0.10
        except Exception as e:
            checks.append({"name": "cycle_log_entries_correct_format", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "cycle_log_entries_correct_format", "passed": False, "detail": "No idea files found"})

    # ── CHECK 14: synthesis has "status" field value (Complete or Inconclusive) ─
    if idea_files:
        idea_path = idea_files[0]
        try:
            idea_content = idea_path.read_text()
            has_status = bool(re.search(r'\*\*Status:\*\*\s*(Complete|Inconclusive)', idea_content))
            log_content_str = ""
            try:
                log_content_str = log_path.read_text()
            except Exception:
                pass
            has_status_log = bool(re.search(r'\*\*Status:\*\*\s*(Complete|Inconclusive)', log_content_str))
            c14_passed = has_status or has_status_log
            checks.append({
                "name": "synthesis_status_field_present",
                "passed": c14_passed,
                "detail": f"Status field (Complete/Inconclusive) found: idea_file={has_status}, log={has_status_log}"
            })
            if c14_passed:
                total_score += 0.10
        except Exception as e:
            checks.append({"name": "synthesis_status_field_present", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "synthesis_status_field_present", "passed": False, "detail": "No idea files found"})

    # Final score cap
    total_score = min(total_score, 1.0)
    passed = total_score >= 0.6

    result = {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg_error", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    main(sys.argv[1])