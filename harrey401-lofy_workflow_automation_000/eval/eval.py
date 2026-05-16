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

    # ── CHECK 1: Core configuration files exist at workspace root ─────────────
    core_files = ["AGENTS.md", "SOUL.md", "IDENTITY.md", "HEARTBEAT.md", "MEMORY_SYSTEM.md"]
    missing_core = []
    for f in core_files:
        if not (workspace / f).exists():
            missing_core.append(f)
    score = add_check(
        "core_config_files_at_root",
        len(missing_core) == 0,
        f"Missing core files: {missing_core}" if missing_core else f"All core files present: {core_files}",
        weight=1.0
    )
    total_score += score

    # ── CHECK 2: USER.md exists at root (may already exist, just verify it's there) ─
    user_md = workspace / "USER.md"
    score = add_check(
        "user_md_exists",
        user_md.exists(),
        "USER.md present at workspace root" if user_md.exists() else "USER.md missing at workspace root",
        weight=0.5
    )
    total_score += score

    # ── CHECK 3: data/ directory with all 5 required JSON files ───────────────
    data_dir = workspace / "data"
    required_data_files = ["goals.json", "fitness.json", "applications.json", "projects.json", "home-config.json"]
    missing_data = []
    malformed_data = []
    for f in required_data_files:
        fpath = data_dir / f
        if not fpath.exists():
            missing_data.append(f)
        else:
            try:
                content = json.loads(fpath.read_text())
                # Must be valid JSON and not contain the template marker as the only content
                # (agent should have initialized it, not just left template as-is without any real keys)
                if not isinstance(content, dict):
                    malformed_data.append(f"{f}: not a JSON object")
            except json.JSONDecodeError as e:
                malformed_data.append(f"{f}: invalid JSON ({e})")

    data_ok = len(missing_data) == 0 and len(malformed_data) == 0
    score = add_check(
        "data_directory_with_json_files",
        data_ok,
        f"Missing: {missing_data}; Malformed: {malformed_data}" if not data_ok
        else "All 5 data JSON files present and valid",
        weight=1.5
    )
    total_score += score

    # ── CHECK 4: memory/ directory exists and uses YYYY-MM-DD.md naming ───────
    memory_dir = workspace / "memory"
    memory_dir_exists = memory_dir.exists() and memory_dir.is_dir()
    score = add_check(
        "memory_directory_exists",
        memory_dir_exists,
        "memory/ directory exists" if memory_dir_exists else "memory/ directory missing — required for daily logs (memory/YYYY-MM-DD.md lifecycle)",
        weight=1.0
    )
    total_score += score

    # Check if there's at least one daily log file with correct naming pattern OR
    # the directory is initialized (existence is sufficient; logs are created dynamically)
    if memory_dir_exists:
        daily_logs = list(memory_dir.glob("*.md"))
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\.md$')
        valid_logs = [f for f in daily_logs if date_pattern.match(f.name)]
        # Either no logs yet (fresh init) or any existing logs follow the pattern
        invalid_logs = [f.name for f in daily_logs if not date_pattern.match(f.name)]
        score = add_check(
            "memory_daily_log_naming_convention",
            len(invalid_logs) == 0,
            f"Invalid log filenames (must be YYYY-MM-DD.md): {invalid_logs}" if invalid_logs
            else f"Naming convention correct. Valid dated logs: {[f.name for f in valid_logs]}",
            weight=0.5
        )
        total_score += score

    # ── CHECK 5: MEMORY.md exists and respects 100-line max limit ─────────────
    memory_md = workspace / "MEMORY.md"
    if memory_md.exists():
        try:
            lines = memory_md.read_text().splitlines()
            # Remove trailing empty lines for fair count
            non_empty_lines = [l for l in lines if l.strip()]
            within_limit = len(non_empty_lines) <= 100
            score = add_check(
                "memory_md_100_line_limit",
                within_limit,
                f"MEMORY.md has {len(non_empty_lines)} non-empty lines (limit: 100)" +
                (" ✓" if within_limit else " ✗ EXCEEDS LIMIT"),
                weight=1.5
            )
            total_score += score

            # Check for [PINNED] tag support awareness (at least mention in MEMORY_SYSTEM.md)
            mem_sys = workspace / "MEMORY_SYSTEM.md"
            if mem_sys.exists():
                mem_sys_content = mem_sys.read_text()
                has_pinned = "[PINNED]" in mem_sys_content or "PINNED" in mem_sys_content
                score = add_check(
                    "memory_system_pinned_tag_documented",
                    has_pinned,
                    "MEMORY_SYSTEM.md documents [PINNED] tag" if has_pinned
                    else "MEMORY_SYSTEM.md missing [PINNED] tag documentation — required for permanent memories",
                    weight=1.0
                )
                total_score += score
        except Exception as e:
            score = add_check("memory_md_100_line_limit", False, f"Could not read MEMORY.md: {e}", weight=1.5)
            total_score += score
    else:
        # MEMORY.md is optional at init but MEMORY_SYSTEM.md must describe it
        mem_sys = workspace / "MEMORY_SYSTEM.md"
        if mem_sys.exists():
            try:
                mem_sys_content = mem_sys.read_text()
                has_100_line_rule = "100" in mem_sys_content
                has_pinned = "[PINNED]" in mem_sys_content or "PINNED" in mem_sys_content
                has_lifecycle = "14" in mem_sys_content or "fourteen" in mem_sys_content.lower()
                score = add_check(
                    "memory_system_100_line_rule_documented",
                    has_100_line_rule,
                    "MEMORY_SYSTEM.md documents 100-line limit" if has_100_line_rule
                    else "MEMORY_SYSTEM.md missing 100-line max limit for MEMORY.md",
                    weight=1.5
                )
                total_score += score
                score = add_check(
                    "memory_system_pinned_tag_documented",
                    has_pinned,
                    "MEMORY_SYSTEM.md documents [PINNED] tag" if has_pinned
                    else "MEMORY_SYSTEM.md missing [PINNED] tag documentation",
                    weight=1.0
                )
                total_score += score
                score = add_check(
                    "memory_system_14day_lifecycle_documented",
                    has_lifecycle,
                    "MEMORY_SYSTEM.md documents 14-day lifecycle" if has_lifecycle
                    else "MEMORY_SYSTEM.md missing 14-day lifecycle rule for daily logs",
                    weight=0.5
                )
                total_score += score
            except Exception as e:
                add_check("memory_system_content_check", False, f"Error reading MEMORY_SYSTEM.md: {e}", weight=1.0)

    # ── CHECK 6: MEMORY_SYSTEM.md describes 5-layer architecture ──────────────
    mem_sys = workspace / "MEMORY_SYSTEM.md"
    if mem_sys.exists():
        try:
            content = mem_sys.read_text()
            # Must mention all 5 layers
            layers = {
                "Working Memory": any(t in content for t in ["Working Memory", "working memory"]),
                "Short-Term": any(t in content for t in ["Short-Term", "Short Term", "short-term"]),
                "Long-Term Declarative": any(t in content for t in ["Declarative", "declarative"]),
                "Long-Term Procedural": any(t in content for t in ["Procedural", "procedural"]),
                "Salience": any(t in content for t in ["Salience", "salience", "Salient"]),
            }
            missing_layers = [k for k, v in layers.items() if not v]
            score = add_check(
                "memory_system_5_layers_documented",
                len(missing_layers) == 0,
                f"Missing layers: {missing_layers}" if missing_layers
                else "All 5 memory layers documented in MEMORY_SYSTEM.md",
                weight=1.5
            )
            total_score += score

            # Must mention group/shared context security rule
            has_security_rule = any(t in content for t in [
                "group", "shared", "never loads", "security", "private"
            ])
            score = add_check(
                "memory_system_group_context_security",
                has_security_rule,
                "MEMORY_SYSTEM.md documents group context security rule" if has_security_rule
                else "MEMORY_SYSTEM.md missing: MEMORY.md must never load in shared/group contexts",
                weight=1.0
            )
            total_score += score
        except Exception as e:
            add_check("memory_system_5_layers_documented", False, f"Error: {e}", weight=1.5)

    # ── CHECK 7: HEARTBEAT.md configures 30-min polling with 4 check types ────
    heartbeat_md = workspace / "HEARTBEAT.md"
    if heartbeat_md.exists():
        try:
            content = heartbeat_md.read_text()
            has_30min = any(t in content for t in ["30", "thirty", "30 min", "30-min"])
            check_types = {
                "unread_emails": any(t in content.lower() for t in ["email", "unread", "inbox"]),
                "calendar_events": any(t in content.lower() for t in ["calendar", "event", "upcoming"]),
                "overdue_followups": any(t in content.lower() for t in ["overdue", "follow-up", "followup", "follow up"]),
                "approaching_deadlines": any(t in content.lower() for t in ["deadline", "approaching", "due"]),
            }
            missing_checks = [k for k, v in check_types.items() if not v]

            score = add_check(
                "heartbeat_30min_polling",
                has_30min,
                "HEARTBEAT.md configures 30-minute polling interval" if has_30min
                else "HEARTBEAT.md missing 30-minute polling interval specification",
                weight=1.5
            )
            total_score += score

            score = add_check(
                "heartbeat_4_check_types",
                len(missing_checks) == 0,
                f"Missing check types: {missing_checks}" if missing_checks
                else "All 4 proactive check types configured in HEARTBEAT.md",
                weight=1.5
            )
            total_score += score
        except Exception as e:
            add_check("heartbeat_content_check", False, f"Error reading HEARTBEAT.md: {e}", weight=1.5)
    else:
        add_check("heartbeat_content_check", False, "HEARTBEAT.md missing from workspace root", weight=1.5)

    # ── CHECK 8: profile/ directory with all 4 required files ─────────────────
    profile_dir = workspace / "profile"
    required_profile_files = ["career.md", "projects.md", "body.md", "personality.md"]
    missing_profile = []
    for f in required_profile_files:
        if not (profile_dir / f).exists():
            missing_profile.append(f)
    score = add_check(
        "profile_directory_with_4_files",
        len(missing_profile) == 0,
        f"Missing profile files: {missing_profile}" if missing_profile
        else f"All 4 profile files present in profile/: {required_profile_files}",
        weight=1.5
    )
    total_score += score

    # ── CHECK 9: AGENTS.md mentions memory protocol and privacy rule ───────────
    agents_md = workspace / "AGENTS.md"
    if agents_md.exists():
        try:
            content = agents_md.read_text()
            has_memory_protocol = any(t in content.lower() for t in [
                "memory protocol", "memory", "MEMORY.md", "daily log"
            ])
            has_privacy_rule = any(t in content.lower() for t in [
                "group", "personal data", "private", "shared", "privacy", "security"
            ])
            score = add_check(
                "agents_md_memory_protocol",
                has_memory_protocol,
                "AGENTS.md includes memory protocol guidance" if has_memory_protocol
                else "AGENTS.md missing memory protocol section",
                weight=0.5
            )
            total_score += score
            score = add_check(
                "agents_md_privacy_rule",
                has_privacy_rule,
                "AGENTS.md includes privacy/group context rule" if has_privacy_rule
                else "AGENTS.md missing privacy rule for group contexts",
                weight=0.5
            )
            total_score += score
        except Exception as e:
            add_check("agents_md_content_check", False, f"Error reading AGENTS.md: {e}", weight=0.5)

    # ── CHECK 10: No legacy/wrong files pollute root (old_attempt trap) ────────
    # The agent should NOT have just copied lofy_old/MEMORY.md (149 lines > 100 limit)
    if memory_md.exists():
        try:
            lines = [l for l in memory_md.read_text().splitlines() if l.strip()]
            copied_bad = len(lines) > 100
            score = add_check(
                "memory_md_not_copied_from_bad_template",
                not copied_bad,
                f"MEMORY.md correctly within 100 lines ({len(lines)} lines)" if not copied_bad
                else f"MEMORY.md has {len(lines)} lines — appears copied from distractor with 149 lines, violating 100-line max",
                weight=1.0
            )
            total_score += score
        except Exception:
            pass

    # ── Normalize score ────────────────────────────────────────────────────────
    max_score = 18.0  # sum of all weights
    normalized = min(1.0, total_score / max_score)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed and normalized >= 0.75,
        "score": round(normalized, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)