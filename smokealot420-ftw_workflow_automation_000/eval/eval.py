#!/usr/bin/env python3
import sys
import os
import json
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    ws = Path(workspace)
    checks = []

    # ── Check 1: PIV directory structure exists ──
    def check_piv_dirs():
        required = [
            ws / "PRDs",
            ws / "PRPs" / "templates",
            ws / "PRPs" / "planning",
        ]
        missing = [str(d) for d in required if not d.is_dir()]
        if missing:
            return False, f"Missing directories: {missing}"
        return True, "All PIV directories present: PRDs/, PRPs/templates/, PRPs/planning/"

    checks.append(run_check("PIV directory structure created", check_piv_dirs))

    # ── Check 2: prp_base.md copied to PRPs/templates/ ──
    def check_prp_template():
        template_path = ws / "PRPs" / "templates" / "prp_base.md"
        if not template_path.exists():
            return False, f"prp_base.md not found at {template_path}"
        content = template_path.read_text()
        # Should contain PRP template markers from the asset
        if "## Overview" not in content and "Overview" not in content:
            return False, "prp_base.md exists but lacks expected template content (## Overview section)"
        return True, f"prp_base.md correctly present at PRPs/templates/prp_base.md with template content"

    checks.append(run_check("prp_base.md copied to PRPs/templates/", check_prp_template))

    # ── Check 3: WORKFLOW.md exists at project root ──
    def check_workflow_md():
        workflow_path = ws / "WORKFLOW.md"
        if not workflow_path.exists():
            return False, "WORKFLOW.md not found at project root"
        content = workflow_path.read_text()
        # Should have some workflow content from template
        if len(content.strip()) < 50:
            return False, "WORKFLOW.md exists but is nearly empty (< 50 chars)"
        return True, f"WORKFLOW.md exists at project root with {len(content)} chars"

    checks.append(run_check("WORKFLOW.md created at project root", check_workflow_md))

    # ── Check 4: PRD file exists with correct naming convention ──
    def check_prd_file():
        prd_dir = ws / "PRDs"
        if not prd_dir.is_dir():
            return False, "PRDs/ directory does not exist"
        prd_files = list(prd_dir.glob("PRD-*.md"))
        if not prd_files:
            # Also check for any .md file in PRDs/
            any_md = list(prd_dir.glob("*.md"))
            if not any_md:
                return False, "No PRD file found in PRDs/ directory"
            return False, f"Found .md files in PRDs/ but none follow naming convention PRD-{{name}}.md: {[f.name for f in any_md]}"
        # Check content has key sections
        prd_file = prd_files[0]
        content = prd_file.read_text()
        missing_sections = []
        for section in ["Phase", "phase"]:
            if section in content:
                break
        else:
            missing_sections.append("phase information")
        if len(content) < 200:
            return False, f"PRD file {prd_file.name} exists but is too short ({len(content)} chars) — likely a placeholder"
        return True, f"PRD file found: {prd_file.name} ({len(content)} chars)"

    checks.append(run_check("PRD file created with correct naming (PRD-*.md)", check_prd_file))

    # ── Check 5: PRD content quality — must describe the patient scheduler project ──
    def check_prd_content():
        prd_dir = ws / "PRDs"
        prd_files = list(prd_dir.glob("PRD-*.md"))
        if not prd_files:
            return False, "No PRD file to check content"
        content = prd_files[0].read_text().lower()
        # Must mention appointment/scheduling domain
        domain_keywords = ["appointment", "patient", "schedule", "scheduler", "booking"]
        found = [k for k in domain_keywords if k in content]
        if not found:
            return False, f"PRD content doesn't mention project domain (appointment/patient/scheduler). Content preview: {content[:300]}"
        # Must have multiple phases
        phase_count = content.count("phase ")
        if phase_count < 2:
            return False, f"PRD must define multiple phases; found {phase_count} phase mentions"
        return True, f"PRD content valid: domain keywords found {found}, phase mentions: {phase_count}"

    checks.append(run_check("PRD content covers patient scheduler domain with phases", check_prd_content))

    # ── Check 6: Codebase analysis file exists ──
    def check_analysis_file():
        planning_dir = ws / "PRPs" / "planning"
        if not planning_dir.is_dir():
            return False, "PRPs/planning/ directory does not exist"
        analysis_files = list(planning_dir.glob("*phase*analysis*")) + list(planning_dir.glob("*analysis*phase*")) + list(planning_dir.glob("*-phase-1-analysis.md")) + list(planning_dir.glob("*phase-1*.md"))
        # More permissive: any .md file in planning dir
        any_md = list(planning_dir.glob("*.md"))
        if not any_md:
            return False, "No analysis file found in PRPs/planning/"
        analysis_file = any_md[0]
        content = analysis_file.read_text()
        if len(content) < 100:
            return False, f"Analysis file {analysis_file.name} is too short ({len(content)} chars)"
        return True, f"Analysis file found: {analysis_file.name} ({len(content)} chars)"

    checks.append(run_check("Codebase analysis file in PRPs/planning/", check_analysis_file))

    # ── Check 7: PRP file exists with correct naming convention ──
    def check_prp_file():
        prp_dir = ws / "PRPs"
        if not prp_dir.is_dir():
            return False, "PRPs/ directory does not exist"
        # Look for PRP-*-phase-1.md or PRP-*phase*.md
        prp_files = list(prp_dir.glob("PRP-*phase*.md")) + list(prp_dir.glob("PRP-*-phase-*.md"))
        # Also check direct children
        all_prp = [f for f in prp_dir.iterdir() if f.is_file() and f.name.startswith("PRP-") and f.suffix == ".md"]
        if not all_prp:
            return False, "No PRP file found in PRPs/ (expected PRP-{PRD_NAME}-phase-1.md)"
        prp_file = all_prp[0]
        content = prp_file.read_text()
        if len(content) < 150:
            return False, f"PRP file {prp_file.name} exists but too short ({len(content)} chars)"
        return True, f"PRP file found: {prp_file.name} ({len(content)} chars)"

    checks.append(run_check("PRP file created with correct naming (PRP-*.md)", check_prp_file))

    # ── Check 8: PRP content has required sections from prp_base template ──
    def check_prp_content():
        prp_dir = ws / "PRPs"
        all_prp = [f for f in prp_dir.iterdir() if f.is_file() and f.name.startswith("PRP-") and f.suffix == ".md"]
        if not all_prp:
            return False, "No PRP file found"
        content = all_prp[0].read_text()
        required_sections = ["Overview", "Implementation", "Validation"]
        found = [s for s in required_sections if s in content]
        missing = [s for s in required_sections if s not in content]
        if len(found) < 2:
            return False, f"PRP missing required sections: {missing}. Found: {found}"
        return True, f"PRP has required template sections: {found}"

    checks.append(run_check("PRP content has required sections from template", check_prp_content))

    # ── Check 9: Git commit with PIV signature string ──
    def check_git_commit():
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--all"],
                cwd=workspace,
                capture_output=True, text=True, timeout=10
            )
            log = result.stdout
            if not log:
                return False, "No git commits found"
            # Check for the specific FTW commit message
            result_full = subprocess.run(
                ["git", "log", "--format=%s %b"],
                cwd=workspace,
                capture_output=True, text=True, timeout=10
            )
            full_log = result_full.stdout
            ftw_string = "Built with FTW (First Try Works)"
            ftw_url = "https://github.com/SmokeAlot420/ftw"
            has_ftw_string = ftw_string in full_log
            has_ftw_url = ftw_url in full_log
            if has_ftw_string and has_ftw_url:
                return True, f"Git commit found with correct FTW signature"
            elif has_ftw_string:
                return False, f"Commit has FTW string but missing URL: {ftw_url}"
            else:
                commits_preview = full_log[:400]
                return False, f"No commit with 'Built with FTW (First Try Works)' found. Commits: {commits_preview}"
        except Exception as e:
            return False, f"Git log failed: {e}"

    checks.append(run_check("Git commit with PIV FTW signature string", check_git_commit))

    # ── Check 10: PRD_NAME consistency (PRP filename references PRD name) ──
    def check_naming_consistency():
        prd_dir = ws / "PRDs"
        prp_dir = ws / "PRPs"
        prd_files = list(prd_dir.glob("PRD-*.md"))
        prp_files = [f for f in prp_dir.iterdir() if f.is_file() and f.name.startswith("PRP-") and f.suffix == ".md"]
        if not prd_files or not prp_files:
            return False, f"Missing PRD or PRP files for consistency check. PRDs: {[f.name for f in prd_files]}, PRPs: {[f.name for f in prp_files]}"
        prd_name = prd_files[0].stem  # e.g., PRD-patient-scheduler
        prp_name = prp_files[0].name  # e.g., PRP-PRD-patient-scheduler-phase-1.md
        # PRP should contain the PRD basename
        # According to skill: PRP-{PRD_NAME}-phase-{N}.md where PRD_NAME includes "PRD-" prefix
        if prd_name in prp_name:
            return True, f"PRP filename correctly references PRD name: PRD='{prd_name}', PRP='{prp_name}'"
        # Also accept if the project name part (without "PRD-" prefix) is in PRP name
        project_part = prd_name.replace("PRD-", "")
        if project_part in prp_name:
            return True, f"PRP filename references project name '{project_part}' from PRD '{prd_name}'"
        return False, f"PRP filename '{prp_name}' does not reference PRD name '{prd_name}'. Expected pattern: PRP-{prd_name}-phase-N.md"

    checks.append(run_check("PRP filename is consistent with PRD name", check_naming_consistency))

    # ── Scoring ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    # Task passes if at least 7/10 checks pass (core structural + naming + content)
    # But require the critical checks to pass
    critical_checks = [
        "PIV directory structure created",
        "PRD file created with correct naming (PRD-*.md)",
        "PRP file created with correct naming (PRP-*.md)",
        "Git commit with PIV FTW signature string",
    ]
    critical_results = {c["name"]: c["passed"] for c in checks}
    critical_passed = all(critical_results.get(name, False) for name in critical_checks)
    overall_pass = critical_passed and passed_count >= 7

    result = {
        "passed": overall_pass,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()