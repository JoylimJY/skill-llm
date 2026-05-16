import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail=""):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ════════════════════════════════════════════════════════════════════════
    # PART 1: Evaluate the exported ability package
    # The agent must have produced a file called "ability_package.md"
    # (the task asks to export AgentAlpha's config without MEMORY.md)
    # ════════════════════════════════════════════════════════════════════════
    
    export_candidates = list(workspace.rglob("ability_package.md"))
    # Also accept common alternative names the agent might choose
    if not export_candidates:
        export_candidates = list(workspace.rglob("能力包*.md"))
    if not export_candidates:
        export_candidates = list(workspace.rglob("export*.md"))
    if not export_candidates:
        export_candidates = list(workspace.rglob("agent_alpha_package.md"))

    export_file_found = len(export_candidates) > 0
    add_check(
        "exported_package_file_exists",
        export_file_found,
        f"Found: {[str(p.relative_to(workspace)) for p in export_candidates]}" if export_file_found else "No exported ability package file found."
    )

    export_content = ""
    if export_file_found:
        try:
            export_content = export_candidates[0].read_text(encoding="utf-8")
        except Exception as e:
            add_check("exported_package_readable", False, str(e))
            export_content = ""

    # Check: Package header - must start with "# 能力包：" (proprietary format)
    has_header = bool(re.search(r'^#\s*能力包[：:].+', export_content, re.MULTILINE))
    add_check(
        "export_has_ability_package_header",
        has_header,
        "Header '# 能力包：...' found." if has_header else "Missing required header '# 能力包：{名称}'."
    )

    # Check: Package has version line
    has_version = bool(re.search(r'-\s*版本[：:]\s*1\.0', export_content))
    add_check(
        "export_has_version_line",
        has_version,
        "Version line found." if has_version else "Missing '- 版本：1.0' line in header."
    )

    # Check: Package has export time line
    has_time = bool(re.search(r'-\s*导出时间[：:]', export_content))
    add_check(
        "export_has_export_time",
        has_time,
        "Export time line found." if has_time else "Missing '- 导出时间：...' line."
    )

    # Check: Package has source/来源 line
    has_source = bool(re.search(r'-\s*来源[：:]', export_content))
    add_check(
        "export_has_source_line",
        has_source,
        "Source line found." if has_source else "Missing '- 来源：...' line."
    )

    # Check: Contains AGENTS.md section
    has_agents_section = bool(re.search(r'^##\s*AGENTS\.md', export_content, re.MULTILINE))
    add_check(
        "export_contains_agents_md_section",
        has_agents_section,
        "## AGENTS.md section found." if has_agents_section else "Missing ## AGENTS.md section."
    )

    # Check: Contains SOUL.md section
    has_soul_section = bool(re.search(r'^##\s*SOUL\.md', export_content, re.MULTILINE))
    add_check(
        "export_contains_soul_md_section",
        has_soul_section,
        "## SOUL.md section found." if has_soul_section else "Missing ## SOUL.md section."
    )

    # Check: Contains TOOLS.md section
    has_tools_section = bool(re.search(r'^##\s*TOOLS\.md', export_content, re.MULTILINE))
    add_check(
        "export_contains_tools_md_section",
        has_tools_section,
        "## TOOLS.md section found." if has_tools_section else "Missing ## TOOLS.md section."
    )

    # Check: Contains IDENTITY.md section
    has_identity_section = bool(re.search(r'^##\s*IDENTITY\.md', export_content, re.MULTILINE))
    add_check(
        "export_contains_identity_md_section",
        has_identity_section,
        "## IDENTITY.md section found." if has_identity_section else "Missing ## IDENTITY.md section."
    )

    # Check: DOES NOT contain MEMORY.md section (user requested exclusion)
    has_memory_section = bool(re.search(r'^##\s*MEMORY\.md', export_content, re.MULTILINE))
    memory_excluded = not has_memory_section
    add_check(
        "export_excludes_memory_md",
        memory_excluded,
        "MEMORY.md correctly excluded from export." if memory_excluded else "MEMORY.md section present — it should have been excluded per user request."
    )

    # Check: AGENTS.md content is actually included (spot check for known content)
    agents_content_present = "concise answers" in export_content or "4-space indentation" in export_content
    add_check(
        "export_agents_md_content_present",
        agents_content_present,
        "AGENTS.md content appears in export." if agents_content_present else "AGENTS.md content not found in export."
    )

    # Check: SOUL.md content actually included
    soul_content_present = "calm, methodical" in export_content or "Honesty above all" in export_content
    add_check(
        "export_soul_md_content_present",
        soul_content_present,
        "SOUL.md content appears in export." if soul_content_present else "SOUL.md content not found in export."
    )

    # Check: Section separators present (--- between sections)
    separator_count = len(re.findall(r'^---\s*$', export_content, re.MULTILINE))
    has_separators = separator_count >= 3  # At least between 4 sections
    add_check(
        "export_has_section_separators",
        has_separators,
        f"Found {separator_count} '---' separators." if has_separators else f"Too few section separators (found {separator_count}, expected at least 3)."
    )

    # ════════════════════════════════════════════════════════════════════════
    # PART 2: Evaluate selective import from agent_b_package.md
    # The agent should have imported ONLY SOUL.md and IDENTITY.md from Agent B
    # into the workspace root, overwriting those files.
    # AGENTS.md, TOOLS.md, MEMORY.md should remain as Agent A's originals.
    # ════════════════════════════════════════════════════════════════════════

    # Original Agent A content fingerprints
    original_agents_fingerprint = "concise answers"  # from Agent A's AGENTS.md
    original_tools_fingerprint = "python_repl"       # from Agent A's TOOLS.md
    original_memory_fingerprint = "Zhang Wei"         # from Agent A's MEMORY.md

    # Agent B content fingerprints (should appear after import)
    beta_soul_fingerprint = "enthusiastic, creative"   # from Agent B's SOUL.md
    beta_identity_fingerprint = "AgentBeta"             # from Agent B's IDENTITY.md

    # Check SOUL.md was overwritten with Agent B's content
    soul_path = workspace / "SOUL.md"
    try:
        soul_content = soul_path.read_text(encoding="utf-8")
        soul_updated = beta_soul_fingerprint in soul_content
        add_check(
            "import_soul_md_overwritten_with_beta",
            soul_updated,
            "SOUL.md contains Agent B content." if soul_updated else f"SOUL.md does not contain expected Agent B content ('{beta_soul_fingerprint}')."
        )
    except Exception as e:
        add_check("import_soul_md_overwritten_with_beta", False, f"Cannot read SOUL.md: {e}")

    # Check IDENTITY.md was overwritten with Agent B's content
    identity_path = workspace / "IDENTITY.md"
    try:
        identity_content = identity_path.read_text(encoding="utf-8")
        identity_updated = beta_identity_fingerprint in identity_content
        add_check(
            "import_identity_md_overwritten_with_beta",
            identity_updated,
            "IDENTITY.md contains Agent B content." if identity_updated else f"IDENTITY.md does not contain expected Agent B content ('{beta_identity_fingerprint}')."
        )
    except Exception as e:
        add_check("import_identity_md_overwritten_with_beta", False, f"Cannot read IDENTITY.md: {e}")

    # Check AGENTS.md was NOT overwritten (should still have Agent A content)
    agents_path = workspace / "AGENTS.md"
    try:
        agents_content = agents_path.read_text(encoding="utf-8")
        agents_preserved = original_agents_fingerprint in agents_content
        add_check(
            "import_agents_md_preserved",
            agents_preserved,
            "AGENTS.md correctly preserved with original Agent A content." if agents_preserved else f"AGENTS.md was overwritten — original content '{original_agents_fingerprint}' not found."
        )
    except Exception as e:
        add_check("import_agents_md_preserved", False, f"Cannot read AGENTS.md: {e}")

    # Check TOOLS.md was NOT overwritten (should still have Agent A content)
    tools_path = workspace / "TOOLS.md"
    try:
        tools_content = tools_path.read_text(encoding="utf-8")
        tools_preserved = original_tools_fingerprint in tools_content
        add_check(
            "import_tools_md_preserved",
            tools_preserved,
            "TOOLS.md correctly preserved with original Agent A content." if tools_preserved else f"TOOLS.md was overwritten — original content '{original_tools_fingerprint}' not found."
        )
    except Exception as e:
        add_check("import_tools_md_preserved", False, f"Cannot read TOOLS.md: {e}")

    # Check MEMORY.md was NOT overwritten (should still have Agent A content)
    memory_path = workspace / "MEMORY.md"
    try:
        memory_content = memory_path.read_text(encoding="utf-8")
        memory_preserved = original_memory_fingerprint in memory_content
        add_check(
            "import_memory_md_preserved",
            memory_preserved,
            "MEMORY.md correctly preserved with original Agent A content." if memory_preserved else f"MEMORY.md was overwritten — original content '{original_memory_fingerprint}' not found."
        )
    except Exception as e:
        add_check("import_memory_md_preserved", False, f"Cannot read MEMORY.md: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # Final Score
    # ════════════════════════════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall_passed = score >= 0.80

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))