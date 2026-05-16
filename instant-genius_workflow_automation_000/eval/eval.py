import sys
import os
import json
from pathlib import Path

def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    home = os.path.expanduser("~")
    openclaw_dir = os.path.join(home, ".openclaw", "workspace")
    self_improving_dir = os.path.join(home, "self-improving")

    checks = []
    total_score = 0.0
    max_checks = 0

    # ── CHECK 1: AGENTS.md exists and was modified (has original + appended content) ──
    max_checks += 1
    agents_path = os.path.join(openclaw_dir, "AGENTS.md")
    try:
        agents_content = Path(agents_path).read_text(encoding="utf-8")
        # Must retain original content
        has_original = "Core Identity" in agents_content or "OpenClaw" in agents_content
        # Must have appended content from agents-additions.md
        has_appended = "Self-Learning System" in agents_content or "Correction Detection" in agents_content
        passed = has_original and has_appended
        checks.append(check(
            "AGENTS.md has original content preserved AND genius additions appended",
            passed,
            f"has_original={has_original}, has_appended={has_appended}. "
            f"First 300 chars: {agents_content[:300]!r}"
        ))
        if passed:
            total_score += 1
    except Exception as e:
        checks.append(check("AGENTS.md has original content preserved AND genius additions appended",
                            False, f"Exception reading AGENTS.md: {e}"))

    # ── CHECK 2: AGENTS.md contains memory promotion rules ──
    max_checks += 1
    try:
        agents_content = Path(agents_path).read_text(encoding="utf-8")
        has_promotion = ("Hot" in agents_content and "Warm" in agents_content) or \
                        ("promotion" in agents_content.lower()) or \
                        ("corrections.md" in agents_content)
        checks.append(check(
            "AGENTS.md contains memory/correction rules from template",
            has_promotion,
            f"Found Hot/Warm/corrections references: {has_promotion}"
        ))
        if has_promotion:
            total_score += 1
    except Exception as e:
        checks.append(check("AGENTS.md contains memory/correction rules from template",
                            False, f"Exception: {e}"))

    # ── CHECK 3: SOUL.md exists and contains proactive behavior content ──
    max_checks += 1
    soul_path = os.path.join(openclaw_dir, "SOUL.md")
    try:
        soul_content = Path(soul_path).read_text(encoding="utf-8")
        has_proactive = ("Proactive" in soul_content or "proactive" in soul_content or
                         "Reverse Prompting" in soul_content or "Anticipatory" in soul_content or
                         "instant-genius" in soul_content)
        checks.append(check(
            "SOUL.md exists and contains proactive behavior engine content",
            has_proactive,
            f"has_proactive={has_proactive}. Content snippet: {soul_content[:200]!r}"
        ))
        if has_proactive:
            total_score += 1
    except Exception as e:
        checks.append(check("SOUL.md exists and contains proactive behavior engine content",
                            False, f"Exception reading SOUL.md: {e}"))

    # ── CHECK 4: HEARTBEAT.md exists and contains smart heartbeat content ──
    max_checks += 1
    heartbeat_path = os.path.join(openclaw_dir, "HEARTBEAT.md")
    try:
        hb_content = Path(heartbeat_path).read_text(encoding="utf-8")
        has_heartbeat = ("HEARTBEAT_OK" in hb_content or "heartbeat" in hb_content.lower() or
                         "Smart Heartbeat" in hb_content or "memory_promoted" in hb_content or
                         "instant-genius" in hb_content)
        checks.append(check(
            "HEARTBEAT.md exists and contains smart heartbeat protocol",
            has_heartbeat,
            f"has_heartbeat={has_heartbeat}. Content snippet: {hb_content[:200]!r}"
        ))
        if has_heartbeat:
            total_score += 1
    except Exception as e:
        checks.append(check("HEARTBEAT.md exists and contains smart heartbeat protocol",
                            False, f"Exception reading HEARTBEAT.md: {e}"))

    # ── CHECK 5: self-improving/ directory exists ──
    max_checks += 1
    try:
        si_exists = os.path.isdir(self_improving_dir)
        checks.append(check(
            "~/self-improving/ directory exists",
            si_exists,
            f"Path: {self_improving_dir}, exists={si_exists}"
        ))
        if si_exists:
            total_score += 1
    except Exception as e:
        checks.append(check("~/self-improving/ directory exists",
                            False, f"Exception: {e}"))

    # ── CHECK 6: self-improving subdirectories (memory, projects, domains, archive) ──
    max_checks += 1
    required_subdirs = ["memory", "projects", "domains", "archive"]
    try:
        missing = []
        for sub in required_subdirs:
            subpath = os.path.join(self_improving_dir, sub)
            if not os.path.isdir(subpath):
                missing.append(sub)
        passed = len(missing) == 0
        checks.append(check(
            "~/self-improving/ has all 4 required subdirectories (memory/projects/domains/archive)",
            passed,
            f"Missing subdirs: {missing}" if missing else "All 4 subdirectories present"
        ))
        if passed:
            total_score += 1
    except Exception as e:
        checks.append(check("~/self-improving/ has all 4 required subdirectories",
                            False, f"Exception: {e}"))

    # ── CHECK 7: corrections.md exists inside self-improving/ ──
    max_checks += 1
    corrections_path = os.path.join(self_improving_dir, "corrections.md")
    try:
        corr_exists = os.path.isfile(corrections_path)
        if corr_exists:
            corr_content = Path(corrections_path).read_text(encoding="utf-8")
            has_format_hint = "Corrections" in corr_content or "correction" in corr_content.lower()
        else:
            has_format_hint = False
        passed = corr_exists and has_format_hint
        checks.append(check(
            "~/self-improving/corrections.md exists with content",
            passed,
            f"exists={corr_exists}, has_content={has_format_hint}"
        ))
        if passed:
            total_score += 1
    except Exception as e:
        checks.append(check("~/self-improving/corrections.md exists with content",
                            False, f"Exception: {e}"))

    # ── CHECK 8: Hot/Warm/Cold three-tier memory structure in memory/MEMORY.md ──
    max_checks += 1
    memory_md_path = os.path.join(self_improving_dir, "memory", "MEMORY.md")
    # Also accept the structure being documented elsewhere in the config files
    try:
        found_tiers = False
        # Primary: MEMORY.md
        if os.path.isfile(memory_md_path):
            mem_content = Path(memory_md_path).read_text(encoding="utf-8")
            if ("Hot" in mem_content and "Warm" in mem_content and "Cold" in mem_content):
                found_tiers = True

        # Fallback: check AGENTS.md or HEARTBEAT.md for tier mentions
        if not found_tiers:
            for fpath in [agents_path, heartbeat_path]:
                try:
                    fc = Path(fpath).read_text(encoding="utf-8")
                    if ("Hot" in fc and "Warm" in fc and "Cold" in fc):
                        found_tiers = True
                        break
                except Exception:
                    pass

        checks.append(check(
            "Hot/Warm/Cold three-tier memory structure is defined (in MEMORY.md or config files)",
            found_tiers,
            f"MEMORY.md path={memory_md_path}, exists={os.path.isfile(memory_md_path)}, tiers_found={found_tiers}"
        ))
        if found_tiers:
            total_score += 1
    except Exception as e:
        checks.append(check("Hot/Warm/Cold three-tier memory structure is defined",
                            False, f"Exception: {e}"))

    # ── FINAL SCORE ───────────────────────────────────────────────────────────
    score = round(total_score / max_checks, 4)
    passed_overall = total_score >= (max_checks * 0.75)  # 75% threshold to pass

    result = {
        "passed": passed_overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()