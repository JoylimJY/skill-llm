import sys
import os
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []
    workspace = Path(workspace)

    # ── CHECK 1: buffer-optimizer SKILL.md was extracted ─────────────────────
    try:
        optimizer_skill = workspace / "skills" / "buffer-optimizer" / "SKILL.md"
        exists = optimizer_skill.exists()
        if exists:
            content = optimizer_skill.read_text(encoding="utf-8")
            has_name = "buffer-optimizer" in content
            has_audit = "Audit" in content
            has_setup = "Setup" in content
            passed = has_name and has_audit and has_setup
            detail = f"Found {optimizer_skill}. name_ok={has_name}, audit_ok={has_audit}, setup_ok={has_setup}"
        else:
            passed = False
            detail = f"skills/buffer-optimizer/SKILL.md does not exist"
        checks.append(check("buffer_optimizer_skill_extracted", passed, detail))
    except Exception as e:
        checks.append(check("buffer_optimizer_skill_extracted", False, str(e)))

    # ── CHECK 2: measure-boot.sh was created and is executable ───────────────
    try:
        script_path = workspace / "skills" / "buffer-optimizer" / "scripts" / "measure-boot.sh"
        exists = script_path.exists()
        if exists:
            content = script_path.read_text(encoding="utf-8")
            is_bash = content.strip().startswith("#!/bin/bash")
            has_threshold = "THRESHOLDS" in content or "check" in content
            has_workspace_var = "OPENCLAW_WORKSPACE" in content
            executable = os.access(str(script_path), os.X_OK)
            passed = is_bash and has_threshold and has_workspace_var
            detail = f"exists={exists}, bash={is_bash}, has_thresholds={has_threshold}, workspace_var={has_workspace_var}, executable={executable}"
        else:
            passed = False
            detail = f"measure-boot.sh not found at skills/buffer-optimizer/scripts/measure-boot.sh"
        checks.append(check("measure_boot_sh_created", passed, detail))
    except Exception as e:
        checks.append(check("measure_boot_sh_created", False, str(e)))

    # ── CHECK 3: audit-agents-md.sh was created ───────────────────────────────
    try:
        audit_script = workspace / "skills" / "buffer-optimizer" / "scripts" / "audit-agents-md.sh"
        exists = audit_script.exists()
        if exists:
            content = audit_script.read_text(encoding="utf-8")
            is_bash = content.strip().startswith("#!/bin/bash")
            checks_pre_response = "pre-response" in content.lower() or "before every response" in content.lower() or "checkpoint" in content.lower()
            checks_negative = "negative" in content.lower() or "reinvent" in content.lower()
            passed = is_bash and (checks_pre_response or checks_negative)
            detail = f"exists={exists}, is_bash={is_bash}, checks_structure={checks_pre_response or checks_negative}"
        else:
            passed = False
            detail = "audit-agents-md.sh not found"
        checks.append(check("audit_agents_md_sh_created", passed, detail))
    except Exception as e:
        checks.append(check("audit_agents_md_sh_created", False, str(e)))

    # ── CHECK 4: HANDOFF.md exists and has correct structure ──────────────────
    try:
        handoff_path = workspace / "HANDOFF.md"
        if not handoff_path.exists():
            checks.append(check("handoff_md_exists_and_structured", False, "HANDOFF.md does not exist"))
        else:
            content = handoff_path.read_text(encoding="utf-8")
            # Must have all 5 required sections
            required_sections = [
                "## Current Work",
                "## Stopping Point",
                "## Key Outcomes",
                "## Open Questions",
                "## Next Steps",
            ]
            missing = [s for s in required_sections if s not in content]
            size_bytes = len(content.encode("utf-8"))
            size_ok = size_bytes <= 2048
            sections_ok = len(missing) == 0

            # Check ordering of sections
            order_ok = True
            if sections_ok:
                positions = [content.index(s) for s in required_sections]
                order_ok = positions == sorted(positions)

            passed = sections_ok and size_ok and order_ok
            detail = (
                f"size={size_bytes}B (limit=2048), "
                f"missing_sections={missing}, "
                f"order_correct={order_ok}"
            )
            checks.append(check("handoff_md_exists_and_structured", passed, detail))
    except Exception as e:
        checks.append(check("handoff_md_exists_and_structured", False, str(e)))

    # ── CHECK 5: HANDOFF.md size ≤ 2KB ───────────────────────────────────────
    try:
        handoff_path = workspace / "HANDOFF.md"
        if not handoff_path.exists():
            checks.append(check("handoff_md_under_2kb", False, "HANDOFF.md does not exist"))
        else:
            size = len(handoff_path.read_bytes())
            passed = size <= 2048
            checks.append(check("handoff_md_under_2kb", passed, f"size={size}B, limit=2048B"))
    except Exception as e:
        checks.append(check("handoff_md_under_2kb", False, str(e)))

    # ── CHECK 6: HANDOFF.md Key Outcomes are conclusions, not activities ──────
    try:
        handoff_path = workspace / "HANDOFF.md"
        if not handoff_path.exists():
            checks.append(check("handoff_outcomes_are_conclusions", False, "HANDOFF.md does not exist"))
        else:
            content = handoff_path.read_text(encoding="utf-8")
            # Extract Key Outcomes section
            outcome_match = re.search(r"## Key Outcomes\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
            if not outcome_match:
                checks.append(check("handoff_outcomes_are_conclusions", False, "Key Outcomes section not found"))
            else:
                outcomes_text = outcome_match.group(1)
                # Activity anti-patterns: "tested X", "ran X", "reviewed X", "checked X", "read X"
                # Must have at least one outcome that looks like a conclusion ("X works because Y", "X is fixed", etc.)
                activity_patterns = [
                    r"\btested\b", r"\bran\b", r"\breviewed\b", r"\bchecked\b",
                    r"\bread\b", r"\blocated\b", r"\bfound and\b",
                ]
                activity_hits = [p for p in activity_patterns if re.search(p, outcomes_text, re.IGNORECASE)]

                # Must be non-empty and have bullet points
                has_content = bool(re.search(r"-\s+\S", outcomes_text))
                # Penalize if all lines are pure activities
                mostly_activity = len(activity_hits) >= 3 and not re.search(
                    r"(works because|is fixed|confirmed|resolved|complete|approved|ready|pass)", outcomes_text, re.IGNORECASE
                )
                passed = has_content and not mostly_activity
                detail = f"has_content={has_content}, activity_patterns_hit={activity_hits}, mostly_activity={mostly_activity}"
                checks.append(check("handoff_outcomes_are_conclusions", passed, detail))
    except Exception as e:
        checks.append(check("handoff_outcomes_are_conclusions", False, str(e)))

    # ── CHECK 7: MEMORY.md reduced to ≤ 1.5KB ────────────────────────────────
    try:
        memory_path = workspace / "MEMORY.md"
        if not memory_path.exists():
            checks.append(check("memory_md_under_1500b", False, "MEMORY.md does not exist"))
        else:
            size = len(memory_path.read_bytes())
            passed = size <= 1536
            checks.append(check("memory_md_under_1500b", passed, f"size={size}B, limit=1536B"))
    except Exception as e:
        checks.append(check("memory_md_under_1500b", False, str(e)))

    # ── CHECK 8: MEMORY.md still has core sections (not gutted) ──────────────
    try:
        memory_path = workspace / "MEMORY.md"
        if not memory_path.exists():
            checks.append(check("memory_md_has_required_sections", False, "MEMORY.md does not exist"))
        else:
            content = memory_path.read_text(encoding="utf-8")
            # Must retain: priorities, projects/project states, people
            has_priorities = bool(re.search(r"priorit", content, re.IGNORECASE))
            has_projects = bool(re.search(r"project", content, re.IGNORECASE))
            has_people = bool(re.search(r"people|person|priya|dev|marcus|sarah", content, re.IGNORECASE))
            has_this_week = bool(re.search(r"this week|week", content, re.IGNORECASE))
            # Must NOT contain architecture docs or URLs (those should be trimmed)
            has_urls = bool(re.search(r"https?://", content))
            has_architecture_bloc = bool(re.search(r"## Architecture Notes", content))
            has_historical = bool(re.search(r"## Historical Context", content))
            has_retrospective = bool(re.search(r"Retrospective", content, re.IGNORECASE))
            trimmed_ok = not has_architecture_bloc and not has_historical
            passed = has_priorities and has_projects and has_people and has_this_week and trimmed_ok
            detail = (
                f"priorities={has_priorities}, projects={has_projects}, people={has_people}, "
                f"this_week={has_this_week}, has_architecture_block={has_architecture_bloc}, "
                f"has_historical_context={has_historical}, trimmed_ok={trimmed_ok}"
            )
            checks.append(check("memory_md_has_required_sections", passed, detail))
    except Exception as e:
        checks.append(check("memory_md_has_required_sections", False, str(e)))

    # ── CHECK 9: AGENTS.md has "Before Every Response" as the FIRST ## section ─
    try:
        agents_path = workspace / "AGENTS.md"
        if not agents_path.exists():
            checks.append(check("agents_md_pre_response_first", False, "AGENTS.md does not exist"))
        else:
            content = agents_path.read_text(encoding="utf-8")
            h2_sections = re.findall(r"^## (.+)$", content, re.MULTILINE)
            if not h2_sections:
                checks.append(check("agents_md_pre_response_first", False, "No ## sections found in AGENTS.md"))
            else:
                first = h2_sections[0].lower()
                is_checkpoint_first = any(kw in first for kw in ["before every", "pre-response", "checkpoint", "response"])
                passed = is_checkpoint_first
                detail = f"First ## section: '{h2_sections[0]}', is_checkpoint={is_checkpoint_first}"
                checks.append(check("agents_md_pre_response_first", passed, detail))
    except Exception as e:
        checks.append(check("agents_md_pre_response_first", False, str(e)))

    # ── CHECK 10: AGENTS.md has "Don't Reinvent Skills" / negative triggers ───
    try:
        agents_path = workspace / "AGENTS.md"
        if not agents_path.exists():
            checks.append(check("agents_md_has_negative_triggers", False, "AGENTS.md does not exist"))
        else:
            content = agents_path.read_text(encoding="utf-8")
            has_negative = bool(re.search(
                r"don.t reinvent|don.t bypass|never manually|negative trigger",
                content, re.IGNORECASE
            ))
            passed = has_negative
            detail = f"has_negative_triggers={has_negative}"
            checks.append(check("agents_md_has_negative_triggers", passed, detail))
    except Exception as e:
        checks.append(check("agents_md_has_negative_triggers", False, str(e)))

    # ── CHECK 11: AGENTS.md has no weak patterns ──────────────────────────────
    try:
        agents_path = workspace / "AGENTS.md"
        if not agents_path.exists():
            checks.append(check("agents_md_no_weak_patterns", False, "AGENTS.md does not exist"))
        else:
            content = agents_path.read_text(encoding="utf-8")
            weak_patterns = [
                r"you have access",
                r"you might want",
                r"\bconsider\b",
                r"\btry to\b",
                r"if appropriate",
                r"you could",
                r"feel free",
                r"it.s recommended",
            ]
            hits = [p for p in weak_patterns if re.search(p, content, re.IGNORECASE)]
            passed = len(hits) == 0
            detail = f"weak_patterns_found={hits}"
            checks.append(check("agents_md_no_weak_patterns", passed, detail))
    except Exception as e:
        checks.append(check("agents_md_no_weak_patterns", False, str(e)))

    # ── CHECK 12: AGENTS.md size ≤ 4KB ───────────────────────────────────────
    try:
        agents_path = workspace / "AGENTS.md"
        if not agents_path.exists():
            checks.append(check("agents_md_under_4kb", False, "AGENTS.md does not exist"))
        else:
            size = len(agents_path.read_bytes())
            passed = size <= 4096
            detail = f"size={size}B, limit=4096B"
            checks.append(check("agents_md_under_4kb", passed, detail))
    except Exception as e:
        checks.append(check("agents_md_under_4kb", False, str(e)))

    # ── CHECK 13: HANDOFF.md contains Meridian/auth content (not empty stub) ──
    try:
        handoff_path = workspace / "HANDOFF.md"
        if not handoff_path.exists():
            checks.append(check("handoff_md_has_session_content", False, "HANDOFF.md does not exist"))
        else:
            content = handoff_path.read_text(encoding="utf-8").lower()
            # Must reference at least some session outcomes
            has_meridian = "meridian" in content or "etl" in content or "pipeline" in content
            has_next_steps = bool(re.search(r"next steps.*\n.*\S", content, re.DOTALL | re.IGNORECASE))
            # Has at least one open question
            has_open_q = bool(re.search(r"open questions.*\n.*\S", content, re.DOTALL | re.IGNORECASE))
            passed = has_meridian and has_next_steps
            detail = f"has_meridian_ref={has_meridian}, has_next_steps={has_next_steps}, has_open_questions={has_open_q}"
            checks.append(check("handoff_md_has_session_content", passed, detail))
    except Exception as e:
        checks.append(check("handoff_md_has_session_content", False, str(e)))

    # ── Compute score ─────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = passed_count >= 10  # need at least 10/13 to pass

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))