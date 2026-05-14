import sys
import json
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name, passed, detail=""):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── 1. Locate plan directory ──────────────────────────────────────────────
    plan_root = None
    spec_file = None
    plan_file = None

    try:
        docs_plan = workspace / "docs" / "plan"
        if docs_plan.exists():
            subdirs = [d for d in docs_plan.iterdir() if d.is_dir()]
            if subdirs:
                # Should have exactly one track dir
                # Find the one that has spec.md and plan.md
                for sd in subdirs:
                    if (sd / "spec.md").exists() or (sd / "plan.md").exists():
                        plan_root = sd
                        spec_file = sd / "spec.md"
                        plan_file = sd / "plan.md"
                        break
    except Exception as e:
        add_check("plan_directory_found", False, f"Exception scanning plan dir: {e}")

    dir_found = plan_root is not None
    add_check(
        "plan_directory_in_docs_plan",
        dir_found,
        f"Found: {plan_root}" if dir_found else "No plan directory found under docs/plan/"
    )

    # ── 2. Track ID format: {shortname}_{YYYYMMDD} ───────────────────────────
    track_id_valid = False
    track_id_str = ""
    if plan_root:
        try:
            dir_name = plan_root.name
            track_id_str = dir_name
            # Pattern: kebab-words_YYYYMMDD
            pattern = r'^[a-z][a-z0-9-]+_\d{8}$'
            if re.match(pattern, dir_name):
                date_part = dir_name.split("_")[-1]
                year = int(date_part[:4])
                month = int(date_part[4:6])
                day = int(date_part[6:8])
                # date should be plausible (2024-2026)
                if 2024 <= year <= 2026 and 1 <= month <= 12 and 1 <= day <= 31:
                    track_id_valid = True
        except Exception as e:
            track_id_valid = False
    add_check(
        "track_id_format_correct",
        track_id_valid,
        f"Track dir name: '{track_id_str}'. Expected pattern: shortname_YYYYMMDD"
    )

    # ── 3. spec.md exists and has required sections ───────────────────────────
    spec_exists = spec_file is not None and spec_file.exists()
    add_check("spec_md_exists", spec_exists, str(spec_file) if spec_file else "spec.md not found")

    spec_content = ""
    if spec_exists:
        try:
            spec_content = spec_file.read_text()
        except Exception as e:
            add_check("spec_md_readable", False, str(e))

    if spec_content:
        required_spec_sections = [
            ("## Summary", r'##\s+Summary'),
            ("## Acceptance Criteria", r'##\s+Acceptance Criteria'),
            ("## Dependencies", r'##\s+Dependencies'),
            ("## Out of Scope", r'##\s+Out of Scope'),
            ("## Technical Notes", r'##\s+Technical Notes'),
        ]
        for section_name, pattern in required_spec_sections:
            found = bool(re.search(pattern, spec_content, re.IGNORECASE))
            add_check(f"spec_has_{section_name.replace('## ', '').replace(' ', '_').lower()}", found,
                      f"Section '{section_name}' {'found' if found else 'MISSING'} in spec.md")

        # Acceptance criteria: 3-8 items with [ ] checkboxes
        ac_items = re.findall(r'-\s*\[\s*\]', spec_content)
        ac_section = re.search(r'##\s+Acceptance Criteria(.*?)(?=^##|\Z)', spec_content, re.DOTALL | re.MULTILINE)
        ac_count = 0
        if ac_section:
            ac_count = len(re.findall(r'-\s*\[\s*\]', ac_section.group(1)))
        ac_valid = 3 <= ac_count <= 8
        add_check("spec_acceptance_criteria_count_3_to_8", ac_valid,
                  f"Found {ac_count} acceptance criteria items (need 3-8)")

        # spec must have Track ID and Type fields
        has_trackid = bool(re.search(r'\*\*Track ID\*\*', spec_content))
        has_type = bool(re.search(r'\*\*Type\*\*', spec_content))
        add_check("spec_has_track_id_field", has_trackid, "**Track ID** field in spec.md")
        add_check("spec_has_type_field", has_type, "**Type** field in spec.md")

        # Track type should be "Refactor" (task desc has "reorganize/refactor/cleanup" keywords)
        type_is_refactor = bool(re.search(r'\*\*Type\*\*[:\s]+Refactor', spec_content, re.IGNORECASE))
        add_check("spec_type_classified_as_refactor", type_is_refactor,
                  "Type should be 'Refactor' based on task keywords. " + 
                  (f"Found: {re.search(r'\\*\\*Type\\*\\*.*', spec_content).group()}" if re.search(r'\*\*Type\*\*.*', spec_content) else "Type field not found"))

    # ── 4. plan.md exists ─────────────────────────────────────────────────────
    plan_exists = plan_file is not None and plan_file.exists()
    add_check("plan_md_exists", plan_exists, str(plan_file) if plan_file else "plan.md not found")

    plan_content = ""
    if plan_exists:
        try:
            plan_content = plan_file.read_text()
        except Exception as e:
            add_check("plan_md_readable", False, str(e))

    if plan_content:
        # Phase headers format: ## Phase N: Name
        phase_headers = re.findall(r'^##\s+Phase\s+\d+:', plan_content, re.MULTILINE)
        phase_count = len(phase_headers)
        phase_count_valid = 2 <= phase_count <= 4
        add_check("plan_phase_count_2_to_4", phase_count_valid,
                  f"Found {phase_count} phase headers (need 2-4). Headers: {phase_headers}")

        # Task format: - [ ] Task N.Y: Description
        task_items = re.findall(r'-\s*\[\s*[\s~x]\s*\]\s*Task\s+\d+\.\d+:', plan_content)
        task_count = len(task_items)
        task_count_valid = 5 <= task_count <= 15
        add_check("plan_task_count_5_to_15", task_count_valid,
                  f"Found {task_count} tasks matching 'Task N.Y:' format (need 5-15)")

        # All tasks use [ ] (unchecked initially)
        unchecked = re.findall(r'-\s*\[\s*\]\s*Task\s+\d+\.\d+:', plan_content)
        in_progress = re.findall(r'-\s*\[~\]\s*Task\s+\d+\.\d+:', plan_content)
        done = re.findall(r'-\s*\[x\]\s*Task\s+\d+\.\d+:', plan_content)
        all_unchecked = len(unchecked) == task_count and task_count > 0
        add_check("plan_all_tasks_unchecked", all_unchecked,
                  f"All {task_count} tasks should be [ ] unchecked. Found {len(in_progress)} [~] and {len(done)} [x]")

        # Last phase must be "Docs & Cleanup"
        last_phase_match = None
        all_phase_matches = list(re.finditer(r'^##\s+Phase\s+(\d+):\s*(.+)$', plan_content, re.MULTILINE))
        if all_phase_matches:
            last_phase_match = all_phase_matches[-1]
            last_phase_name = last_phase_match.group(2).strip()
            last_phase_is_docs = bool(re.search(r'docs?\s*[&and]+\s*cleanup', last_phase_name, re.IGNORECASE))
            add_check("plan_last_phase_is_docs_and_cleanup", last_phase_is_docs,
                      f"Last phase name: '{last_phase_name}'. Must be 'Docs & Cleanup'.")
        else:
            add_check("plan_last_phase_is_docs_and_cleanup", False, "No phase headers found")

        # Deploy phase must be present (Dockerfile + deploy.sh exist in workspace)
        has_deploy_phase = bool(re.search(r'##\s+Phase\s+\d+[^#]*Deploy', plan_content, re.IGNORECASE))
        add_check("plan_has_deploy_phase", has_deploy_phase,
                  "A Deploy phase is required because Dockerfile and scripts/deploy.sh exist in the project. " +
                  ("Deploy phase found." if has_deploy_phase else "Deploy phase MISSING."))

        # Plan must have Final Verification section
        has_final_verification = bool(re.search(r'##\s+Final Verification', plan_content, re.IGNORECASE))
        add_check("plan_has_final_verification", has_final_verification,
                  "'## Final Verification' section " + ("found" if has_final_verification else "MISSING"))

        # plan.md must reference spec.md
        has_spec_ref = bool(re.search(r'spec\.md', plan_content))
        add_check("plan_references_spec_md", has_spec_ref,
                  "plan.md should reference spec.md. " + ("Found." if has_spec_ref else "Not found."))

        # plan.md must have Track ID
        has_plan_trackid = bool(re.search(r'\*\*Track ID\*\*', plan_content))
        add_check("plan_has_track_id_field", has_plan_trackid, "**Track ID** in plan.md")

        # Tasks mention file paths (at least some should have src/ or tests/ paths)
        has_file_paths = bool(re.search(r'src/|tests/|docs/', plan_content))
        add_check("plan_tasks_mention_file_paths", has_file_paths,
                  "Tasks should reference concrete file paths from research. " +
                  ("File paths found." if has_file_paths else "No file paths detected."))

        # Verification sections per phase
        verification_sections = re.findall(r'^###\s+Verification', plan_content, re.MULTILINE)
        verif_count = len(verification_sections)
        verif_ok = verif_count >= 2
        add_check("plan_has_verification_sections", verif_ok,
                  f"Found {verif_count} '### Verification' sections (need at least 2, one per phase)")

        # Plan Overview section
        has_overview = bool(re.search(r'##\s+Overview', plan_content, re.IGNORECASE))
        add_check("plan_has_overview_section", has_overview,
                  "'## Overview' section " + ("found" if has_overview else "MISSING"))

    # ── 5. Context detection: must use docs/plan/{trackId}/ (project context) ─
    # (Already validated above by checking docs/plan/ path)
    # Additional: should NOT have used KB path (docs/plan/{shortname-without-date}/)
    if plan_root:
        dir_name = plan_root.name
        has_date_suffix = bool(re.match(r'.+_\d{8}$', dir_name))
        add_check("project_context_used_not_kb_context", has_date_suffix,
                  f"Project context requires date suffix in dir name. Dir: '{dir_name}'. " +
                  ("Date suffix found — project context correctly used." if has_date_suffix else
                   "No date suffix — may have used KB context path instead of project context."))

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall_passed = score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))