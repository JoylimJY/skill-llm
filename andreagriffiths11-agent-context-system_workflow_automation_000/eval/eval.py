import sys
import os
import json
import re
import subprocess

def run_checks(workspace):
    checks = []
    passed_count = 0

    def add_check(name, passed, detail):
        nonlocal passed_count
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            passed_count += 1

    # ---- CHECK 1: AGENTS.md exists ----
    agents_md_path = os.path.join(workspace, "AGENTS.md")
    try:
        with open(agents_md_path, "r") as f:
            agents_content = f.read()
        agents_lines = agents_content.splitlines()
        add_check("AGENTS.md exists", True, f"Found AGENTS.md with {len(agents_lines)} lines")
    except FileNotFoundError:
        add_check("AGENTS.md exists", False, "AGENTS.md not found in workspace root")
        agents_content = ""
        agents_lines = []

    # ---- CHECK 2: AGENTS.md under 120 lines ----
    line_count = len(agents_lines)
    passed = line_count > 0 and line_count <= 120
    add_check(
        "AGENTS.md under 120 lines",
        passed,
        f"Line count: {line_count} (must be 1-120)"
    )

    # ---- CHECK 3: AGENTS.md has pipe-delimited Patterns section ----
    try:
        # Look for at least 2 pipe-delimited entries in a Patterns section
        patterns_section = re.search(
            r'###\s*Patterns.*?(?=###|\Z)',
            agents_content,
            re.DOTALL | re.IGNORECASE
        )
        if patterns_section:
            section_text = patterns_section.group(0)
            pipe_lines = [l for l in section_text.splitlines() if '|' in l and not l.strip().startswith('#') and not l.strip().startswith('<!--')]
            passed = len(pipe_lines) >= 2
            add_check(
                "AGENTS.md Patterns section has pipe-delimited entries",
                passed,
                f"Found {len(pipe_lines)} pipe-delimited pattern lines: {pipe_lines[:3]}"
            )
        else:
            add_check(
                "AGENTS.md Patterns section has pipe-delimited entries",
                False,
                "No '### Patterns' section found in AGENTS.md"
            )
    except Exception as e:
        add_check("AGENTS.md Patterns section has pipe-delimited entries", False, str(e))

    # ---- CHECK 4: AGENTS.md has pipe-delimited Boundaries section ----
    try:
        boundaries_section = re.search(
            r'###\s*Boundaries.*?(?=###|\Z)',
            agents_content,
            re.DOTALL | re.IGNORECASE
        )
        if boundaries_section:
            section_text = boundaries_section.group(0)
            pipe_lines = [l for l in section_text.splitlines() if '|' in l and not l.strip().startswith('#') and not l.strip().startswith('<!--')]
            passed = len(pipe_lines) >= 2
            add_check(
                "AGENTS.md Boundaries section has pipe-delimited entries",
                passed,
                f"Found {len(pipe_lines)} pipe-delimited boundary lines: {pipe_lines[:3]}"
            )
        else:
            add_check(
                "AGENTS.md Boundaries section has pipe-delimited entries",
                False,
                "No '### Boundaries' section found in AGENTS.md"
            )
    except Exception as e:
        add_check("AGENTS.md Boundaries section has pipe-delimited entries", False, str(e))

    # ---- CHECK 5: AGENTS.md has pipe-delimited Gotchas section ----
    try:
        gotchas_section = re.search(
            r'###\s*Gotchas.*?(?=###|\Z)',
            agents_content,
            re.DOTALL | re.IGNORECASE
        )
        if gotchas_section:
            section_text = gotchas_section.group(0)
            pipe_lines = [l for l in section_text.splitlines() if '|' in l and not l.strip().startswith('#') and not l.strip().startswith('<!--')]
            passed = len(pipe_lines) >= 1
            add_check(
                "AGENTS.md Gotchas section has pipe-delimited entries",
                passed,
                f"Found {len(pipe_lines)} pipe-delimited gotcha lines: {pipe_lines[:3]}"
            )
        else:
            add_check(
                "AGENTS.md Gotchas section has pipe-delimited entries",
                False,
                "No '### Gotchas' section found in AGENTS.md"
            )
    except Exception as e:
        add_check("AGENTS.md Gotchas section has pipe-delimited entries", False, str(e))

    # ---- CHECK 6: AGENTS.md contains project-specific content (genomics) ----
    try:
        genomics_keywords = ['genomic', 'vcf', 'pipeline', 'variant', 'normalize', 'chrom', 'fastq', 'sequenc', 'bio']
        content_lower = agents_content.lower()
        found = [kw for kw in genomics_keywords if kw in content_lower]
        passed = len(found) >= 2
        add_check(
            "AGENTS.md contains project-specific genomics content",
            passed,
            f"Found genomics keywords: {found}"
        )
    except Exception as e:
        add_check("AGENTS.md contains project-specific genomics content", False, str(e))

    # ---- CHECK 7: .agents.local.md exists ----
    local_md_path = os.path.join(workspace, ".agents.local.md")
    try:
        with open(local_md_path, "r") as f:
            local_content = f.read()
        local_lines = local_content.splitlines()
        add_check(".agents.local.md exists", True, f"Found .agents.local.md with {len(local_lines)} lines")
    except FileNotFoundError:
        add_check(".agents.local.md exists", False, ".agents.local.md not found in workspace root")
        local_content = ""
        local_lines = []

    # ---- CHECK 8: .agents.local.md has Session Log section with at least one entry ----
    try:
        session_log_section = re.search(
            r'##\s*Session\s*Log.*',
            local_content,
            re.DOTALL | re.IGNORECASE
        )
        if session_log_section:
            section_text = session_log_section.group(0)
            # Check for date-like patterns or substantive content beyond just the header
            has_content = len([l for l in section_text.splitlines()[1:] if l.strip()]) >= 3
            add_check(
                ".agents.local.md has Session Log with entries",
                has_content,
                f"Session Log section found with {'sufficient' if has_content else 'insufficient'} content"
            )
        else:
            add_check(
                ".agents.local.md has Session Log with entries",
                False,
                "No '## Session Log' section found in .agents.local.md"
            )
    except Exception as e:
        add_check(".agents.local.md has Session Log with entries", False, str(e))

    # ---- CHECK 9: .agents.local.md has Ready to Promote section ----
    try:
        promote_section = re.search(
            r'##\s*Ready\s*to\s*Promote.*?(?=##|\Z)',
            local_content,
            re.DOTALL | re.IGNORECASE
        )
        if promote_section:
            section_text = promote_section.group(0)
            add_check(
                ".agents.local.md has '## Ready to Promote' section",
                True,
                "Section found"
            )
        else:
            add_check(
                ".agents.local.md has '## Ready to Promote' section",
                False,
                "No '## Ready to Promote' section found"
            )
    except Exception as e:
        add_check(".agents.local.md has '## Ready to Promote' section", False, str(e))

    # ---- CHECK 10: Ready to Promote has pipe-delimited entries (normalize_chrom pattern - 3+ sessions) ----
    try:
        promote_section = re.search(
            r'##\s*Ready\s*to\s*Promote.*?(?=##|\Z)',
            local_content,
            re.DOTALL | re.IGNORECASE
        )
        if promote_section:
            section_text = promote_section.group(0)
            pipe_lines = [l for l in section_text.splitlines() if '|' in l and l.strip() and not l.strip().startswith('#') and not l.strip().startswith('<!--')]
            # Must have at least one pipe-delimited entry
            has_pipe_entries = len(pipe_lines) >= 1
            # Check for normalize_chrom or related chromosome normalization pattern
            all_section_lower = section_text.lower()
            has_normalize = any(kw in all_section_lower for kw in ['normalize', 'chrom', 'chr'])
            add_check(
                "Ready to Promote has pipe-delimited entries for recurring pattern (normalize_chrom/chrom)",
                has_pipe_entries and has_normalize,
                f"Pipe entries: {pipe_lines[:3]}, has_normalize_keyword: {has_normalize}"
            )
        else:
            add_check(
                "Ready to Promote has pipe-delimited entries for recurring pattern (normalize_chrom/chrom)",
                False,
                "No '## Ready to Promote' section found"
            )
    except Exception as e:
        add_check("Ready to Promote has pipe-delimited entries for recurring pattern (normalize_chrom/chrom)", False, str(e))

    # ---- CHECK 11: .agents.local.md is gitignored ----
    try:
        gitignore_path = os.path.join(workspace, ".gitignore")
        with open(gitignore_path, "r") as f:
            gitignore_content = f.read()
        # Check if .agents.local.md is in .gitignore
        is_gitignored = ".agents.local.md" in gitignore_content
        add_check(
            ".agents.local.md is listed in .gitignore",
            is_gitignored,
            f".gitignore {'contains' if is_gitignored else 'does NOT contain'} .agents.local.md"
        )
    except FileNotFoundError:
        add_check(".agents.local.md is listed in .gitignore", False, ".gitignore not found")
    except Exception as e:
        add_check(".agents.local.md is listed in .gitignore", False, str(e))

    # ---- CHECK 12: Verify .agents.local.md is actually ignored by git ----
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-v", ".agents.local.md"],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        is_ignored_by_git = result.returncode == 0
        add_check(
            ".agents.local.md is ignored by git (git check-ignore)",
            is_ignored_by_git,
            f"git check-ignore exit code: {result.returncode}, output: {result.stdout.strip()}"
        )
    except Exception as e:
        add_check(".agents.local.md is ignored by git (git check-ignore)", False, str(e))

    # ---- CHECK 13: CLAUDE.md exists as a symlink pointing to AGENTS.md ----
    claude_md_path = os.path.join(workspace, "CLAUDE.md")
    try:
        is_symlink = os.path.islink(claude_md_path)
        if is_symlink:
            link_target = os.readlink(claude_md_path)
            # Should point to AGENTS.md (relative or absolute)
            points_to_agents = "AGENTS.md" in link_target
            add_check(
                "CLAUDE.md is a symlink pointing to AGENTS.md",
                points_to_agents,
                f"CLAUDE.md is symlink: {is_symlink}, target: '{link_target}'"
            )
        else:
            # Maybe CLAUDE.md exists but is not a symlink - check if it's a copy
            if os.path.exists(claude_md_path):
                add_check(
                    "CLAUDE.md is a symlink pointing to AGENTS.md",
                    False,
                    f"CLAUDE.md exists but is NOT a symlink (it's a regular file)"
                )
            else:
                add_check(
                    "CLAUDE.md is a symlink pointing to AGENTS.md",
                    False,
                    "CLAUDE.md does not exist"
                )
    except Exception as e:
        add_check("CLAUDE.md is a symlink pointing to AGENTS.md", False, str(e))

    # ---- CHECK 14: .agents.local.md has the required structural sections ----
    try:
        required_sections = ['## Preferences', '## Patterns', '## Gotchas', '## Dead Ends', '## Session Log']
        found_sections = []
        missing_sections = []
        for section in required_sections:
            # Case-insensitive check
            if re.search(re.escape(section), local_content, re.IGNORECASE):
                found_sections.append(section)
            else:
                missing_sections.append(section)
        passed = len(missing_sections) == 0
        add_check(
            ".agents.local.md has all required structural sections",
            passed,
            f"Found: {found_sections}, Missing: {missing_sections}"
        )
    except Exception as e:
        add_check(".agents.local.md has all required structural sections", False, str(e))

    # ---- CHECK 15: AGENTS.md contains Rules section with numbered rules ----
    try:
        rules_section = re.search(
            r'##\s*Rules.*?(?=##|\Z)',
            agents_content,
            re.DOTALL | re.IGNORECASE
        )
        if rules_section:
            section_text = rules_section.group(0)
            # Look for numbered rules
            numbered_rules = re.findall(r'^\s*\d+\.', section_text, re.MULTILINE)
            passed = len(numbered_rules) >= 3
            add_check(
                "AGENTS.md contains Rules section with numbered rules",
                passed,
                f"Found {len(numbered_rules)} numbered rules"
            )
        else:
            add_check(
                "AGENTS.md contains Rules section with numbered rules",
                False,
                "No '## Rules' section found in AGENTS.md"
            )
    except Exception as e:
        add_check("AGENTS.md contains Rules section with numbered rules", False, str(e))

    # ---- Compute final score ----
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    overall_passed = passed_count >= 11  # Must pass at least 11/15 checks

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))