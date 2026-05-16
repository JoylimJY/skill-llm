#!/usr/bin/env python3
"""
Evaluation script for the Obsidian biomedical research task.

Task requirements:
1. Search for protein purification notes -> find "Protein Purification Protocol"
2. Edit "Protein Purification Protocol" by replacing the "Results Log" section with 
   updated content (must include the new yield and optimization note from the user request)
3. Create a new note "Compound NSC-12345 Synthesis Report" in the Research folder
   with appropriate tags including 'oncology' or 'drug-screening', and wikilinks 
   to [[Drug Screening Results]] and [[BRCA1 Mutation Review]]
"""

import sys
import json
import re
from pathlib import Path
import yaml

def parse_frontmatter(content):
    """Parse YAML frontmatter."""
    if content.startswith('---'):
        end = content.find('\n---', 3)
        if end != -1:
            fm_text = content[3:end].strip()
            try:
                fm = yaml.safe_load(fm_text)
                body = content[end+4:].strip()
                return fm or {}, body
            except Exception as e:
                return {}, content
    return {}, content

def run_checks(workspace_dir):
    checks = []
    vault_path = Path("/home/ruslan/webdav/data/ruslain")

    # ===== CHECK 1: Protein Purification Protocol was edited (Results Log section updated) =====
    check1_name = "protein_purification_results_log_updated"
    try:
        prot_note = vault_path / "Research" / "Protocols" / "Protein Purification Protocol.md"
        if not prot_note.exists():
            # Try finding it anywhere
            candidates = list(vault_path.rglob("Protein Purification Protocol.md"))
            if candidates:
                prot_note = candidates[0]
            else:
                raise FileNotFoundError("Protein Purification Protocol.md not found")
        
        content = prot_note.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(content)
        
        # Check that Results Log section exists and has been modified
        has_results_section = bool(re.search(r'##\s+Results\s+Log', body, re.IGNORECASE))
        
        # The original had "Attempt 1: 0.2mg/mL" and "Needs optimization"
        # The agent should have updated this section with new content
        original_text_preserved_unchanged = (
            "Attempt 1: 0.2mg/mL final yield (low)" in body and
            "Needs optimization" in body and
            not re.search(r'(attempt\s*2|optimized|improved|1\.[0-9]mg|mg/mL|yield.*increas|increas.*yield|mg.*mL|mL.*mg)', body, re.IGNORECASE)
        )
        
        # Modified: must have something beyond just the original two lines
        results_section_match = re.search(
            r'##\s+Results\s+Log\s*\n(.*?)(?=\n##\s|\Z)', 
            body, 
            re.DOTALL | re.IGNORECASE
        )
        
        section_content = results_section_match.group(1).strip() if results_section_match else ""
        
        # Count non-empty lines in Results Log
        result_lines = [l for l in section_content.split('\n') if l.strip()]
        was_edited = len(result_lines) >= 2 and not original_text_preserved_unchanged
        
        # Also check modified timestamp changed
        modified_ts = fm.get('modified', '')
        
        checks.append({
            "name": check1_name,
            "passed": has_results_section and was_edited,
            "detail": (
                f"Results Log section found={has_results_section}, "
                f"section was updated={was_edited}, "
                f"lines_in_section={len(result_lines)}, "
                f"modified_ts={modified_ts}, "
                f"section_content_preview={section_content[:200]!r}"
            )
        })
    except Exception as e:
        checks.append({"name": check1_name, "passed": False, "detail": f"Exception: {e}"})

    # ===== CHECK 2: New note "Compound NSC-12345 Synthesis Report" exists =====
    check2_name = "synthesis_report_note_created"
    synthesis_note = None
    try:
        candidates = list(vault_path.rglob("Compound NSC-12345 Synthesis Report.md"))
        if not candidates:
            # Fuzzy: try partial name match
            candidates = list(vault_path.rglob("*NSC-12345*.md"))
        
        if not candidates:
            raise FileNotFoundError("Compound NSC-12345 Synthesis Report.md not found")
        
        synthesis_note = candidates[0]
        checks.append({
            "name": check2_name,
            "passed": True,
            "detail": f"Found at: {synthesis_note.relative_to(vault_path)}"
        })
    except Exception as e:
        checks.append({"name": check2_name, "passed": False, "detail": f"Exception: {e}"})

    # ===== CHECK 3: New note has proper frontmatter (tags, created, modified) =====
    check3_name = "synthesis_report_has_frontmatter"
    try:
        if synthesis_note is None:
            raise ValueError("Note not found from previous check")
        
        content = synthesis_note.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(content)
        
        has_created = 'created' in fm and fm['created']
        has_modified = 'modified' in fm and fm['modified']
        
        tags = fm.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        tags_lower = [str(t).lower() for t in tags]
        
        has_relevant_tag = any(
            t in tags_lower for t in ['oncology', 'drug-screening', 'drug_screening', 
                                       'compound', 'nsc-12345', 'research', 'cancer',
                                       'screening']
        )
        
        checks.append({
            "name": check3_name,
            "passed": has_created and has_modified and has_relevant_tag,
            "detail": (
                f"has_created={has_created}, has_modified={has_modified}, "
                f"tags={tags}, has_relevant_tag={has_relevant_tag}"
            )
        })
    except Exception as e:
        checks.append({"name": check3_name, "passed": False, "detail": f"Exception: {e}"})

    # ===== CHECK 4: New note contains wikilinks to Drug Screening Results and BRCA1 Mutation Review =====
    check4_name = "synthesis_report_has_wikilinks"
    try:
        if synthesis_note is None:
            raise ValueError("Note not found from previous check")
        
        content = synthesis_note.read_text(encoding='utf-8')
        
        # Check for wikilinks to both required notes
        has_drug_screening_link = bool(re.search(r'\[\[Drug Screening Results', content))
        has_brca1_link = bool(re.search(r'\[\[BRCA1 Mutation Review', content))
        
        checks.append({
            "name": check4_name,
            "passed": has_drug_screening_link and has_brca1_link,
            "detail": (
                f"has_drug_screening_wikilink={has_drug_screening_link}, "
                f"has_brca1_mutation_review_wikilink={has_brca1_link}"
            )
        })
    except Exception as e:
        checks.append({"name": check4_name, "passed": False, "detail": f"Exception: {e}"})

    # ===== CHECK 5: New note is placed in Research folder (auto-folder or explicit) =====
    check5_name = "synthesis_report_in_research_folder"
    try:
        if synthesis_note is None:
            raise ValueError("Note not found from previous check")
        
        rel_path = synthesis_note.relative_to(vault_path)
        parts = rel_path.parts
        # Should be under Research/ or Research/Experiments or Research/Literature or similar
        in_research = len(parts) > 1 and parts[0].lower() == 'research'
        
        checks.append({
            "name": check5_name,
            "passed": in_research,
            "detail": f"Note path relative to vault: {rel_path}, parts={parts}"
        })
    except Exception as e:
        checks.append({"name": check5_name, "passed": False, "detail": f"Exception: {e}"})

    # ===== CHECK 6: Synthesis note has meaningful content (not empty) =====
    check6_name = "synthesis_report_has_content"
    try:
        if synthesis_note is None:
            raise ValueError("Note not found from previous check")
        
        content = synthesis_note.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(content)
        
        # Check body has substantive content: at least a title heading + some text
        has_title = bool(re.search(r'^#\s+', body, re.MULTILINE))
        body_words = len(body.split())
        has_content = body_words >= 30  # at least 30 words of content
        
        # Should mention NSC-12345 or the compound name
        mentions_compound = 'NSC-12345' in body or 'NSC12345' in body.replace('-', '')
        
        checks.append({
            "name": check6_name,
            "passed": has_title and has_content and mentions_compound,
            "detail": (
                f"has_title={has_title}, body_words={body_words}, "
                f"mentions_compound={mentions_compound}"
            )
        })
    except Exception as e:
        checks.append({"name": check6_name, "passed": False, "detail": f"Exception: {e}"})

    # ===== CHECK 7: Protein Purification Protocol frontmatter modified timestamp updated =====
    check7_name = "protein_purification_modified_ts_updated"
    try:
        prot_note = None
        candidates = list(vault_path.rglob("Protein Purification Protocol.md"))
        if candidates:
            prot_note = candidates[0]
        
        if prot_note is None:
            raise FileNotFoundError("Protein Purification Protocol.md not found")
        
        content = prot_note.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(content)
        
        created_ts = str(fm.get('created', ''))
        modified_ts = str(fm.get('modified', ''))
        
        # modified should differ from created (note was created 20 days ago, edited now)
        timestamps_differ = modified_ts != created_ts and modified_ts != ''
        
        checks.append({
            "name": check7_name,
            "passed": timestamps_differ,
            "detail": f"created={created_ts}, modified={modified_ts}, differ={timestamps_differ}"
        })
    except Exception as e:
        checks.append({"name": check7_name, "passed": False, "detail": f"Exception: {e}"})

    # Calculate overall pass/fail and score
    passed_checks = [c for c in checks if c['passed']]
    score = len(passed_checks) / len(checks) if checks else 0.0
    
    # Must pass critical checks: note created (2), wikilinks (4), protocol edited (1)
    critical = {checks[i]['name']: checks[i]['passed'] for i in range(len(checks))}
    overall_passed = (
        critical.get("protein_purification_results_log_updated", False) and
        critical.get("synthesis_report_note_created", False) and
        critical.get("synthesis_report_has_wikilinks", False)
    )
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))