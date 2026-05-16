#!/usr/bin/env python3
"""
Evaluation script for career-spotlight-finder task.
Checks:
1. ~/.career-spotlight/ directory structure initialized
2. Per-project analyses exist in analyses/ with required sections and front-matter
3. Old report.md was archived to history/ with correct timestamp format
4. New report.md exists and has required structural sections
5. Old copies/ files were archived to history/ with timestamp suffixes
6. All 4 required copy files exist in copies/ with required content
7. The stale analysis was regenerated (has newer analyzed_at than the old one)
"""

import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime

checks = []
total_score = 0.0
max_score = 0.0

def check(name: str, passed: bool, detail: str, weight: float = 1.0):
    global total_score, max_score
    checks.append({"name": name, "passed": passed, "detail": detail})
    max_score += weight
    if passed:
        total_score += weight

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
home = Path.home()
career = home / ".career-spotlight"
analyses_dir = career / "analyses"
copies_dir = career / "copies"
history_dir = career / "history"
report_path = career / "report.md"

# ─────────────────────────────────────────────
# CHECK 1: Directory structure initialized
# ─────────────────────────────────────────────
try:
    dirs_ok = all([
        career.is_dir(),
        analyses_dir.is_dir(),
        copies_dir.is_dir(),
        history_dir.is_dir(),
    ])
    check(
        "directory_structure_initialized",
        dirs_ok,
        f"~/.career-spotlight dirs: career={career.is_dir()}, "
        f"analyses={analyses_dir.is_dir()}, copies={copies_dir.is_dir()}, history={history_dir.is_dir()}"
    )
except Exception as e:
    check("directory_structure_initialized", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 2: config.json exists (init step)
# ─────────────────────────────────────────────
try:
    config_path = career / "config.json"
    if config_path.exists():
        import json as _json
        cfg = _json.loads(config_path.read_text())
        config_ok = cfg.get("initialized") == True
        check("config_json_initialized", config_ok, f"config.json: {cfg}")
    else:
        check("config_json_initialized", False, "config.json not found")
except Exception as e:
    check("config_json_initialized", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 3: Per-project analyses exist
# ─────────────────────────────────────────────
EXPECTED_PROJECTS = {
    "variant-calling-pipeline": ["Variant Calling", "variant", "GATK", "Snakemake", "somatic"],
    "crispr": ["CRISPR", "crispr", "off-target", "gRNA", "graph"],
    "protein": ["protein", "AlphaFold", "folding", "LoRA", "rare disease"],
}

try:
    analysis_files = list(analyses_dir.glob("*.md"))
    check(
        "analyses_directory_has_files",
        len(analysis_files) >= 2,
        f"Found {len(analysis_files)} analysis files: {[f.name for f in analysis_files]}"
    )
except Exception as e:
    check("analyses_directory_has_files", False, f"Exception: {e}")

# Check each expected project has an analysis
for proj_key, keywords in EXPECTED_PROJECTS.items():
    try:
        # Find any analysis file that might correspond to this project
        matching = []
        for af in analyses_dir.glob("*.md"):
            content = af.read_text(errors="replace").lower()
            if any(kw.lower() in content for kw in keywords):
                matching.append(af.name)
        
        found = len(matching) > 0
        check(
            f"analysis_exists_{proj_key}",
            found,
            f"Analysis for '{proj_key}' (keywords: {keywords[:3]}): "
            f"{'found in ' + str(matching) if found else 'NOT FOUND'}"
        )
    except Exception as e:
        check(f"analysis_exists_{proj_key}", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 4: Analysis front-matter has required fields
# ─────────────────────────────────────────────
try:
    analysis_files = list(analyses_dir.glob("*.md"))
    front_matter_ok_count = 0
    front_matter_details = []
    
    required_fields = ["project:", "slug:", "priority:", "analyzed_at:", "source_path:"]
    required_sections = ["## Project Overview", "## Technical Contributions", 
                         "## Hidden Strengths", "## Industry Buzzwords",
                         "## Impact Signals", "## Career Narrative Hook"]
    
    for af in analysis_files:
        content = af.read_text(errors="replace")
        fields_present = all(f in content for f in required_fields)
        sections_present = sum(1 for s in required_sections if s in content)
        if fields_present and sections_present >= 4:
            front_matter_ok_count += 1
            front_matter_details.append(f"{af.name}: OK (sections={sections_present})")
        else:
            front_matter_details.append(
                f"{af.name}: PARTIAL (fields={fields_present}, sections={sections_present}/6)"
            )
    
    check(
        "analysis_front_matter_and_sections",
        front_matter_ok_count >= 2,
        f"{front_matter_ok_count}/{len(analysis_files)} analyses have correct structure. "
        f"Details: {front_matter_details}"
    )
except Exception as e:
    check("analysis_front_matter_and_sections", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 5: Priority labels used (highlight / supporting)
# ─────────────────────────────────────────────
try:
    analysis_files = list(analyses_dir.glob("*.md"))
    priorities_found = {"highlight": 0, "supporting": 0}
    for af in analysis_files:
        content = af.read_text(errors="replace").lower()
        if "priority: highlight" in content:
            priorities_found["highlight"] += 1
        elif "priority: supporting" in content:
            priorities_found["supporting"] += 1
    
    has_priorities = sum(priorities_found.values()) >= 2
    check(
        "analysis_priority_labels_assigned",
        has_priorities,
        f"Priority counts: {priorities_found}"
    )
except Exception as e:
    check("analysis_priority_labels_assigned", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 6: Old report.md archived to history/ with correct timestamp format
# ─────────────────────────────────────────────
try:
    history_reports = list(history_dir.glob("report-*.md"))
    
    # Check timestamp format: report-YYYY-MM-DDTHH-MM-SS.md
    timestamp_pattern = re.compile(
        r"report-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.md$"
    )
    
    valid_archives = [f for f in history_reports if timestamp_pattern.match(f.name)]
    
    archive_ok = len(valid_archives) >= 1
    check(
        "old_report_archived_correct_format",
        archive_ok,
        f"History reports: {[f.name for f in history_reports]}. "
        f"Valid timestamp format (report-YYYY-MM-DDTHH-MM-SS.md): {[f.name for f in valid_archives]}"
    )
    
    # Also verify the archived file contains the old content
    if valid_archives:
        archived_content = valid_archives[0].read_text(errors="replace")
        contains_old = "OUTDATED" in archived_content or "2024-01-01" in archived_content or "old" in archived_content.lower()
        check(
            "archived_report_contains_old_content",
            contains_old,
            f"Archived report '{valid_archives[0].name}' contains old content markers: {contains_old}"
        )
    else:
        check("archived_report_contains_old_content", False, "No valid archived report found to check content")

except Exception as e:
    check("old_report_archived_correct_format", False, f"Exception: {e}")
    check("archived_report_contains_old_content", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 7: New report.md exists with required structure
# ─────────────────────────────────────────────
try:
    if report_path.exists():
        report_content = report_path.read_text(errors="replace")
        
        required_report_sections = [
            "## Distinctiveness Thesis",
            "## Meta-Themes",
            "## Top 3 Hidden Capabilities",
            "## Core Keywords",
            "## Career Arc Narrative",
        ]
        
        sections_found = [s for s in required_report_sections if s in report_content]
        has_positioning = "Positioning" in report_content or "positioning" in report_content
        is_not_old = "OUTDATED" not in report_content and len(report_content) > 500
        structure_ok = len(sections_found) >= 4 and has_positioning and is_not_old
        
        check(
            "new_report_md_structure",
            structure_ok,
            f"report.md: length={len(report_content)}, sections_found={sections_found}, "
            f"has_positioning={has_positioning}, is_not_old={is_not_old}"
        )
        
        # Check report references both highlight and supporting projects
        has_project_refs = any(
            kw in report_content.lower() 
            for kw in ["variant", "crispr", "protein", "alphafold", "gatk", "folding"]
        )
        check(
            "report_references_projects",
            has_project_refs,
            f"report.md references actual project content: {has_project_refs}"
        )
    else:
        check("new_report_md_structure", False, "report.md does not exist")
        check("report_references_projects", False, "report.md does not exist")

except Exception as e:
    check("new_report_md_structure", False, f"Exception: {e}")
    check("report_references_projects", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 8: Old copies archived with timestamp suffix
# ─────────────────────────────────────────────
try:
    # Old copies should be in history/ with some timestamp suffix
    history_files = list(history_dir.glob("*"))
    copy_archive_pattern = re.compile(
        r"(resume-bullets|elevator-pitch|linkedin-summary|casual-intro).*\d{4}.*\.md$"
    )
    archived_copies = [f for f in history_files if copy_archive_pattern.match(f.name)]
    
    # Also accept if they are in a subdirectory
    all_history = list(history_dir.rglob("*.md"))
    copy_names_found_in_history = sum(
        1 for f in all_history
        if any(cn in f.name for cn in ["resume-bullets", "elevator-pitch", "linkedin-summary", "casual-intro"])
        and any(c.isdigit() for c in f.name)
    )
    
    copies_archived = len(archived_copies) >= 3 or copy_names_found_in_history >= 3
    check(
        "old_copies_archived_to_history",
        copies_archived,
        f"Archived copy files in history/: {[f.name for f in archived_copies]}. "
        f"Copy names with timestamp: {copy_names_found_in_history}"
    )
except Exception as e:
    check("old_copies_archived_to_history", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 9: All 4 required copy files exist in copies/
# ─────────────────────────────────────────────
REQUIRED_COPIES = ["resume-bullets.md", "elevator-pitch.md", "linkedin-summary.md", "casual-intro.md"]

for copy_name in REQUIRED_COPIES:
    try:
        copy_path = copies_dir / copy_name
        if copy_path.exists():
            content = copy_path.read_text(errors="replace")
            is_not_old = "(OLD)" not in content and len(content) > 100
            check(
                f"copy_file_{copy_name.replace('.md','').replace('-','_')}",
                is_not_old,
                f"{copy_name}: exists=True, length={len(content)}, not_old={is_not_old}"
            )
        else:
            check(
                f"copy_file_{copy_name.replace('.md','').replace('-','_')}",
                False,
                f"{copy_name}: NOT FOUND in {copies_dir}"
            )
    except Exception as e:
        check(
            f"copy_file_{copy_name.replace('.md','').replace('-','_')}",
            False,
            f"Exception: {e}"
        )

# ─────────────────────────────────────────────
# CHECK 10: Copy content quality — references projects and uses action verbs
# ─────────────────────────────────────────────
try:
    resume_path = copies_dir / "resume-bullets.md"
    if resume_path.exists():
        rb_content = resume_path.read_text(errors="replace")
        
        # Should have bullet points
        has_bullets = rb_content.count("- ") >= 4 or rb_content.count("* ") >= 4
        
        # Should reference at least one real project keyword
        project_keywords = ["variant", "CRISPR", "crispr", "protein", "AlphaFold", 
                           "genomic", "genomics", "GATK", "pipeline", "off-target", "folding"]
        has_project_ref = any(kw in rb_content for kw in project_keywords)
        
        check(
            "resume_bullets_quality",
            has_bullets and has_project_ref,
            f"resume-bullets.md: has_bullets={has_bullets}, "
            f"has_project_ref={has_project_ref}, length={len(rb_content)}"
        )
    else:
        check("resume_bullets_quality", False, "resume-bullets.md not found")
except Exception as e:
    check("resume_bullets_quality", False, f"Exception: {e}")

try:
    elevator_path = copies_dir / "elevator-pitch.md"
    if elevator_path.exists():
        ep_content = elevator_path.read_text(errors="replace")
        has_content = len(ep_content.strip()) > 150
        check(
            "elevator_pitch_quality",
            has_content,
            f"elevator-pitch.md: length={len(ep_content)}"
        )
    else:
        check("elevator_pitch_quality", False, "elevator-pitch.md not found")
except Exception as e:
    check("elevator_pitch_quality", False, f"Exception: {e}")

try:
    linkedin_path = copies_dir / "linkedin-summary.md"
    if linkedin_path.exists():
        li_content = linkedin_path.read_text(errors="replace")
        # Should be 150-300 words approximately
        word_count = len(li_content.split())
        has_content = word_count >= 100  # being generous with 100 min
        check(
            "linkedin_summary_quality",
            has_content,
            f"linkedin-summary.md: word_count={word_count}"
        )
    else:
        check("linkedin_summary_quality", False, "linkedin-summary.md not found")
except Exception as e:
    check("linkedin_summary_quality", False, f"Exception: {e}")

try:
    casual_path = copies_dir / "casual-intro.md"
    if casual_path.exists():
        ci_content = casual_path.read_text(errors="replace")
        has_content = len(ci_content.strip()) > 80
        check(
            "casual_intro_quality",
            has_content,
            f"casual-intro.md: length={len(ci_content)}"
        )
    else:
        check("casual_intro_quality", False, "casual-intro.md not found")
except Exception as e:
    check("casual_intro_quality", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 11: Stale analysis was regenerated
# (the variant-calling-pipeline analysis should have a newer analyzed_at)
# ─────────────────────────────────────────────
try:
    OLD_TS_STR = "2024"  # The stale analysis was from ~90 days ago, in 2024 area
    stale_regen = False
    stale_detail = "No analysis found for variant-calling-pipeline"
    
    for af in analyses_dir.glob("*.md"):
        content = af.read_text(errors="replace")
        if "variant" in content.lower() and "calling" in content.lower():
            # Check if analyzed_at is recent (not the old stale timestamp)
            ts_match = re.search(r"analyzed_at:\s*(\S+)", content)
            if ts_match:
                ts_str = ts_match.group(1).strip()
                # Old was 90 days ago; if it was regenerated, it should have a recent timestamp
                try:
                    # Parse the timestamp
                    ts_clean = ts_str.replace('"', '').replace("'", "")
                    # Try multiple formats
                    for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                        try:
                            ts_dt = datetime.strptime(ts_clean[:len(fmt.replace('%Y','2024').replace('%m','01').replace('%d','01').replace('%H','00').replace('%M','00').replace('%S','00').replace('%f','000000'))], fmt)
                            break
                        except:
                            ts_dt = None
                    
                    if ts_dt:
                        age_days = (datetime.now() - ts_dt).days
                        stale_regen = age_days < 30  # regenerated within last 30 days
                        stale_detail = f"analyzed_at={ts_str}, age_days={age_days}"
                    else:
                        # If we can't parse, check if it's clearly newer (contains current year)
                        current_year = str(datetime.now().year)
                        stale_regen = current_year in ts_str
                        stale_detail = f"analyzed_at={ts_str}, contains_current_year={stale_regen}"
                except Exception as parse_e:
                    stale_detail = f"analyzed_at={ts_str}, parse_error={parse_e}"
            break
    
    check(
        "stale_analysis_regenerated",
        stale_regen,
        stale_detail
    )
except Exception as e:
    check("stale_analysis_regenerated", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 12: Docx was processed (protein-folding project appears in analyses)
# Pandoc must have been used to convert the .docx
# ─────────────────────────────────────────────
try:
    protein_keywords = ["protein", "alphafold", "lora", "folding", "rare disease", "evoformer", "kubernetes"]
    protein_found = False
    protein_detail = "No protein/AlphaFold analysis found"
    
    for af in analyses_dir.glob("*.md"):
        content = af.read_text(errors="replace").lower()
        kw_matches = [kw for kw in protein_keywords if kw in content]
        if len(kw_matches) >= 2:
            protein_found = True
            protein_detail = f"Found in {af.name}: matched keywords {kw_matches}"
            break
    
    check(
        "docx_processed_via_pandoc",
        protein_found,
        protein_detail
    )
except Exception as e:
    check("docx_processed_via_pandoc", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# Final scoring
# ─────────────────────────────────────────────
all_passed = all(c["passed"] for c in checks)
score = round(total_score / max_score, 4) if max_score > 0 else 0.0

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))
sys.exit(0 if all_passed else 1)