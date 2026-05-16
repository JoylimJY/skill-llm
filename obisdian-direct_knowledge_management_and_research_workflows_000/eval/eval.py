#!/usr/bin/env python3
"""
Evaluation script for the Obsidian knowledge base task.

Expected agent behavior:
1. Search for EGFR-related notes using obsidian_search.py
2. Read relevant notes (EGFR Structure and Function, EGFR Binding Assay Notes)
3. Create a new note "EGFR Research Summary" with:
   - Appropriate tags (research, EGFR, summary, etc.)
   - Content synthesizing both source notes
   - Wikilinks to source notes ([[EGFR Structure and Function]], [[EGFR Binding Assay Notes]])
   - Auto-folder or suggest-folder placing it in Research or Research/Proteins
4. Edit "EGFR Inhibitor Project" note using replace-section to add/update a "Related Research" section
   that includes a wikilink to the new [[EGFR Research Summary]] note
"""
import sys
import json
import re
from pathlib import Path

def run_checks(workspace_dir: str):
    checks = []
    vault = Path("/home/ruslan/webdav/data/ruslain")
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # -----------------------------------------------------------------------
    # CHECK 1: New summary note was created
    # -----------------------------------------------------------------------
    summary_note = None
    try:
        candidates = list(vault.rglob("EGFR Research Summary.md"))
        # also accept minor name variations
        if not candidates:
            candidates = list(vault.rglob("*EGFR*Summary*.md"))
        if not candidates:
            candidates = list(vault.rglob("*EGFR*Research*Summary*.md"))
        
        if candidates:
            summary_note = candidates[0]
            add_check(
                "summary_note_created",
                True,
                f"Found summary note at: {summary_note.relative_to(vault)}"
            )
        else:
            add_check(
                "summary_note_created",
                False,
                "No EGFR Research Summary note found in vault"
            )
    except Exception as e:
        add_check("summary_note_created", False, f"Exception: {e}")

    # -----------------------------------------------------------------------
    # CHECK 2: Summary note has valid frontmatter with tags
    # -----------------------------------------------------------------------
    summary_content = ""
    summary_has_frontmatter = False
    summary_tags = []
    try:
        if summary_note:
            summary_content = summary_note.read_text(encoding='utf-8')
            if summary_content.startswith('---'):
                end = summary_content.find('\n---', 3)
                if end != -1:
                    fm_text = summary_content[4:end]
                    # Extract tags
                    tag_match = re.search(r'tags:\s*\n((?:\s+-\s+.+\n)*)', fm_text)
                    if tag_match:
                        raw_tags = tag_match.group(1)
                        summary_tags = [t.strip().lstrip('- ') for t in raw_tags.strip().split('\n') if t.strip()]
                    summary_has_frontmatter = len(summary_tags) > 0
            
            has_egfr_tag = any('egfr' in t.lower() for t in summary_tags)
            add_check(
                "summary_has_frontmatter_with_tags",
                summary_has_frontmatter and has_egfr_tag,
                f"Frontmatter present: {summary_has_frontmatter}, Tags: {summary_tags}, Has EGFR tag: {has_egfr_tag}"
            )
        else:
            add_check("summary_has_frontmatter_with_tags", False, "No summary note to check")
    except Exception as e:
        add_check("summary_has_frontmatter_with_tags", False, f"Exception: {e}")

    # -----------------------------------------------------------------------
    # CHECK 3: Summary note placed in Research folder (not root)
    # -----------------------------------------------------------------------
    try:
        if summary_note:
            rel_path = summary_note.relative_to(vault)
            parts = rel_path.parts
            in_research = len(parts) > 1 and 'research' in parts[0].lower()
            add_check(
                "summary_in_research_folder",
                in_research,
                f"Note path: {rel_path}, in Research folder: {in_research}"
            )
        else:
            add_check("summary_in_research_folder", False, "No summary note to check")
    except Exception as e:
        add_check("summary_in_research_folder", False, f"Exception: {e}")

    # -----------------------------------------------------------------------
    # CHECK 4: Summary note contains wikilinks to source notes
    # -----------------------------------------------------------------------
    try:
        if summary_content:
            wikilinks = re.findall(r'\[\[([^\]|#]+)(?:[|#][^\]]*)?]]', summary_content)
            wikilinks_lower = [w.lower() for w in wikilinks]
            
            has_structure_link = any('egfr structure' in w or 'egfr structure and function' in w 
                                     for w in wikilinks_lower)
            has_assay_link = any('egfr binding' in w or 'egfr binding assay' in w 
                                 for w in wikilinks_lower)
            
            add_check(
                "summary_has_wikilinks_to_sources",
                has_structure_link and has_assay_link,
                f"Wikilinks found: {wikilinks}, Has structure link: {has_structure_link}, Has assay link: {has_assay_link}"
            )
        else:
            add_check("summary_has_wikilinks_to_sources", False, "No summary content to check")
    except Exception as e:
        add_check("summary_has_wikilinks_to_sources", False, f"Exception: {e}")

    # -----------------------------------------------------------------------
    # CHECK 5: EGFR Inhibitor Project note was edited (has Related Research section)
    # -----------------------------------------------------------------------
    project_note_path = vault / "Projects" / "EGFR Inhibitor Project.md"
    project_content = ""
    try:
        if project_note_path.exists():
            project_content = project_note_path.read_text(encoding='utf-8')
            has_related_section = bool(re.search(
                r'#{1,6}\s+Related Research', project_content, re.IGNORECASE
            ))
            add_check(
                "project_note_has_related_research_section",
                has_related_section,
                f"'Related Research' section present in EGFR Inhibitor Project: {has_related_section}"
            )
        else:
            add_check(
                "project_note_has_related_research_section",
                False,
                "EGFR Inhibitor Project.md not found at expected path"
            )
    except Exception as e:
        add_check("project_note_has_related_research_section", False, f"Exception: {e}")

    # -----------------------------------------------------------------------
    # CHECK 6: Related Research section in project note links to new summary
    # -----------------------------------------------------------------------
    try:
        if project_content:
            # Find the Related Research section content
            section_match = re.search(
                r'#{1,6}\s+Related Research\s*\n(.*?)(?=^#{1,6}\s|\Z)',
                project_content,
                re.MULTILINE | re.DOTALL | re.IGNORECASE
            )
            if section_match:
                section_body = section_match.group(1)
                wikilinks_in_section = re.findall(r'\[\[([^\]|#]+)(?:[|#][^\]]*)?]]', section_body)
                links_lower = [l.lower() for l in wikilinks_in_section]
                
                # Check for link to EGFR Research Summary
                has_summary_link = any(
                    'egfr research summary' in l or 'egfr' in l and 'summary' in l
                    for l in links_lower
                )
                add_check(
                    "project_related_research_links_to_summary",
                    has_summary_link,
                    f"Wikilinks in Related Research section: {wikilinks_in_section}, Links to summary: {has_summary_link}"
                )
            else:
                add_check(
                    "project_related_research_links_to_summary",
                    False,
                    "No 'Related Research' section found to check for links"
                )
        else:
            add_check("project_related_research_links_to_summary", False, "Project note content empty")
    except Exception as e:
        add_check("project_related_research_links_to_summary", False, f"Exception: {e}")

    # -----------------------------------------------------------------------
    # CHECK 7: Project note's modified timestamp was updated (frontmatter check)
    # -----------------------------------------------------------------------
    try:
        if project_content and project_content.startswith('---'):
            end = project_content.find('\n---', 3)
            if end != -1:
                fm_text = project_content[4:end]
                modified_match = re.search(r'modified:\s*(\S+)', fm_text)
                if modified_match:
                    modified_val = modified_match.group(1)
                    # Should be newer than 2024-03-18 (original)
                    original_modified = "2024-03-18T09:00:00"
                    was_updated = modified_val > original_modified
                    add_check(
                        "project_note_modified_timestamp_updated",
                        was_updated,
                        f"Modified field: {modified_val}, Original: {original_modified}, Updated: {was_updated}"
                    )
                else:
                    add_check("project_note_modified_timestamp_updated", False, "No 'modified' field in frontmatter")
            else:
                add_check("project_note_modified_timestamp_updated", False, "Could not parse frontmatter")
        else:
            add_check("project_note_modified_timestamp_updated", False, "No frontmatter in project note")
    except Exception as e:
        add_check("project_note_modified_timestamp_updated", False, f"Exception: {e}")

    # -----------------------------------------------------------------------
    # CHECK 8: Summary note body has substantive content (>200 chars non-frontmatter)
    # -----------------------------------------------------------------------
    try:
        if summary_content:
            # Strip frontmatter
            if summary_content.startswith('---'):
                end_fm = summary_content.find('\n---', 3)
                body = summary_content[end_fm+4:] if end_fm != -1 else summary_content
            else:
                body = summary_content
            
            body_len = len(body.strip())
            has_substance = body_len > 200
            add_check(
                "summary_note_has_substantive_content",
                has_substance,
                f"Summary note body length: {body_len} chars (need >200)"
            )
        else:
            add_check("summary_note_has_substantive_content", False, "No summary content")
    except Exception as e:
        add_check("summary_note_has_substantive_content", False, f"Exception: {e}")

    # -----------------------------------------------------------------------
    # Compute final score
    # -----------------------------------------------------------------------
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    overall_passed = passed_count >= 6  # Need at least 6/8 to pass

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))