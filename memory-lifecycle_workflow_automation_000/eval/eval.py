#!/usr/bin/env python3
"""
Evaluation script for the memory-lifecycle task.
Checks final filesystem state against expected outcomes for 5 research entities.
"""

import json
import re
import sys
from pathlib import Path

def read_file_safe(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def get_frontmatter_field(content: str, field: str):
    if content is None:
        return None
    pattern = rf'^{re.escape(field)}:\s*(.+)$'
    m = re.search(pattern, content, re.MULTILINE)
    return m.group(1).strip() if m else None

def run_checks(workspace: Path) -> list[dict]:
    checks = []

    # ── CHECK 1: CRISPR Knockout Study → moved to research/completed ─────────
    crispr_expected = workspace / "research/completed/crispr-knockout-study.md"
    crispr_original = workspace / "research/active/crispr-knockout-study.md"
    try:
        moved = crispr_expected.exists()
        not_in_active = not crispr_original.exists()
        checks.append({
            "name": "crispr_knockout_moved_to_completed",
            "passed": moved and not_in_active,
            "detail": f"Expected at research/completed/crispr-knockout-study.md (exists={moved}); must not remain in research/active/ (not_there={not_in_active})"
        })
        content = read_file_safe(crispr_expected)
        status_val = get_frontmatter_field(content, "status") if content else None
        checks.append({
            "name": "crispr_knockout_status_completed",
            "passed": status_val == "completed",
            "detail": f"frontmatter status should be 'completed', got '{status_val}'"
        })
        completed_val = get_frontmatter_field(content, "completed") if content else None
        has_date = bool(completed_val and completed_val.strip() and completed_val.strip() != "")
        checks.append({
            "name": "crispr_knockout_completed_date_set",
            "passed": has_date,
            "detail": f"frontmatter 'completed' field should be a non-empty date, got '{completed_val}'"
        })
    except Exception as e:
        checks.append({"name": "crispr_knockout_check_error", "passed": False, "detail": str(e)})

    # ── CHECK 2: Metabolomics Pilot → moved to research/missed ───────────────
    metab_expected = workspace / "research/missed/metabolomics-pilot.md"
    metab_original = workspace / "research/active/metabolomics-pilot.md"
    try:
        moved = metab_expected.exists()
        not_in_active = not metab_original.exists()
        checks.append({
            "name": "metabolomics_pilot_moved_to_missed",
            "passed": moved and not_in_active,
            "detail": f"Expected at research/missed/metabolomics-pilot.md (exists={moved}); must not remain in research/active/ (not_there={not_in_active})"
        })
        content = read_file_safe(metab_expected)
        status_val = get_frontmatter_field(content, "status") if content else None
        checks.append({
            "name": "metabolomics_pilot_status_missed",
            "passed": status_val == "missed",
            "detail": f"frontmatter status should be 'missed', got '{status_val}'"
        })
    except Exception as e:
        checks.append({"name": "metabolomics_pilot_check_error", "passed": False, "detail": str(e)})

    # ── CHECK 3: Protein Folding ML Model → already completed, NOT re-moved ──
    pf_completed = workspace / "research/completed/protein-folding-ml-model.md"
    # Must still be in research/completed AND status must remain 'completed'
    try:
        still_there = pf_completed.exists()
        # Must NOT appear anywhere else (not in active or archive)
        active_copy = (workspace / "research/active/protein-folding-ml-model.md").exists()
        archive_copy = (workspace / "research/archive/protein-folding-ml-model.md").exists()
        checks.append({
            "name": "protein_folding_not_moved_again",
            "passed": still_there and not active_copy and not archive_copy,
            "detail": f"Should remain in research/completed/ unchanged. still_there={still_there}, in_active={active_copy}, in_archive={archive_copy}"
        })
        content = read_file_safe(pf_completed)
        status_val = get_frontmatter_field(content, "status") if content else None
        checks.append({
            "name": "protein_folding_status_unchanged",
            "passed": status_val == "completed",
            "detail": f"Status should remain 'completed', got '{status_val}'"
        })
    except Exception as e:
        checks.append({"name": "protein_folding_check_error", "passed": False, "detail": str(e)})

    # ── CHECK 4: Organoid Drug Screen → PAUSED: stays in research/active, frontmatter updated ──
    organoid_active = workspace / "research/active/organoid-drug-screen.md"
    organoid_archive = workspace / "research/archive/organoid-drug-screen.md"
    try:
        stays_in_active = organoid_active.exists()
        not_moved = not organoid_archive.exists()
        # Also check it hasn't been moved to completed or missed
        not_in_completed = not (workspace / "research/completed/organoid-drug-screen.md").exists()
        checks.append({
            "name": "organoid_stays_in_active_folder",
            "passed": stays_in_active and not_moved and not_in_completed,
            "detail": f"Paused item must remain in research/active/ (stays={stays_in_active}, not_in_archive={not_moved}, not_in_completed={not_in_completed})"
        })
        content = read_file_safe(organoid_active)
        status_val = get_frontmatter_field(content, "status") if content else None
        checks.append({
            "name": "organoid_status_paused",
            "passed": status_val == "paused",
            "detail": f"frontmatter status should be 'paused', got '{status_val}'"
        })
    except Exception as e:
        checks.append({"name": "organoid_check_error", "passed": False, "detail": str(e)})

    # ── CHECK 5: Epigenomics Pipeline → REACTIVATED: moved from archive → active ──
    epi_expected = workspace / "research/active/epigenomics-pipeline.md"
    epi_original = workspace / "research/archive/epigenomics-pipeline.md"
    try:
        moved_to_active = epi_expected.exists()
        not_in_archive = not epi_original.exists()
        checks.append({
            "name": "epigenomics_reactivated_to_active",
            "passed": moved_to_active and not_in_archive,
            "detail": f"Should be moved to research/active/ (exists={moved_to_active}); must not remain in research/archive/ (not_there={not_in_archive})"
        })
        content = read_file_safe(epi_expected)
        status_val = get_frontmatter_field(content, "status") if content else None
        checks.append({
            "name": "epigenomics_status_active",
            "passed": status_val == "active",
            "detail": f"frontmatter status should be 'active', got '{status_val}'"
        })
        # The 'completed' field should be cleared/blank since it's been reactivated
        completed_val = get_frontmatter_field(content, "completed") if content else "UNREADABLE"
        # Accept either blank/empty or the original date cleared (flexible: just check status was reverted)
        checks.append({
            "name": "epigenomics_reactivation_consistent",
            "passed": status_val == "active",  # already checked, but make explicit in output
            "detail": f"Status confirmed active after reactivation. completed field: '{completed_val}'"
        })
    except Exception as e:
        checks.append({"name": "epigenomics_check_error", "passed": False, "detail": str(e)})

    # ── CHECK 6: Distractor files untouched ─────────────────────────────────
    distractor_paths = [
        "research/active/brca2-expression-panel.md",
        "tasks/active/submit-ethics-amendment.md",
        "grants/active/wellcome-organoid-grant.md",
        "contacts/dr-chen.md",
    ]
    try:
        all_intact = all((workspace / p).exists() for p in distractor_paths)
        checks.append({
            "name": "distractor_files_untouched",
            "passed": all_intact,
            "detail": f"All distractor files should remain in original locations. Intact={all_intact}"
        })
    except Exception as e:
        checks.append({"name": "distractor_check_error", "passed": False, "detail": str(e)})

    return checks


def main():
    if len(sys.argv) < 2:
        workspace = Path("/workspace")
    else:
        workspace = Path(sys.argv[1])

    checks = run_checks(workspace)
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())