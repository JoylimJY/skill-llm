import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # =========================================================
    # CHECK GROUP 1: notes/ideas.md - Hackathon Ideation Output
    # =========================================================
    ideas_path = workspace_path / "notes" / "ideas.md"

    # Check 1.1: File exists and was modified (has content beyond original)
    try:
        ideas_content = ideas_path.read_text(encoding="utf-8")
        original_marker = "AI Quiz Generator"
        has_original = original_marker in ideas_content
        # The file should be longer than the original (~900 chars)
        is_extended = len(ideas_content) > 1200
        checks.append({
            "name": "ideas_md_exists_and_extended",
            "passed": has_original and is_extended,
            "detail": f"File exists: True, has original content: {has_original}, extended with new content: {is_extended} (len={len(ideas_content)})"
        })
    except Exception as e:
        checks.append({
            "name": "ideas_md_exists_and_extended",
            "passed": False,
            "detail": f"Could not read notes/ideas.md: {e}"
        })
        ideas_content = ""

    # Check 1.2: SCAMPER header for AI Quiz Generator present
    try:
        # Must have a SCAMPER section header referencing the subject
        scamper_header_pattern = r"###\s+SCAMPER:\s+.*(Quiz|quiz|AI Quiz|ai quiz)"
        has_scamper_header = bool(re.search(scamper_header_pattern, ideas_content))
        checks.append({
            "name": "ideas_md_scamper_header",
            "passed": has_scamper_header,
            "detail": f"SCAMPER header (### SCAMPER: [Subject]) found: {has_scamper_header}"
        })
    except Exception as e:
        checks.append({
            "name": "ideas_md_scamper_header",
            "passed": False,
            "detail": f"Error checking SCAMPER header: {e}"
        })

    # Check 1.3: All 7 lenses present in the appended section (Full SCAMPER)
    try:
        # Find the SCAMPER section in ideas.md (after the AI Quiz Generator entry)
        quiz_pos = ideas_content.find("AI Quiz Generator")
        scamper_section = ideas_content[quiz_pos:] if quiz_pos != -1 else ideas_content

        required_lenses = [
            r"\*\*Substitute:\*\*",
            r"\*\*Combine:\*\*",
            r"\*\*Adapt:\*\*",
            r"\*\*Modify:\*\*",
            r"\*\*Put to other uses:\*\*",
            r"\*\*Eliminate:\*\*",
            r"\*\*Reverse:\*\*",
        ]
        missing_lenses = []
        for lens_pattern in required_lenses:
            if not re.search(lens_pattern, scamper_section):
                missing_lenses.append(lens_pattern)

        all_lenses_present = len(missing_lenses) == 0
        checks.append({
            "name": "ideas_md_all_7_lenses_present",
            "passed": all_lenses_present,
            "detail": f"All 7 bold lens labels present: {all_lenses_present}. Missing: {missing_lenses}"
        })
    except Exception as e:
        checks.append({
            "name": "ideas_md_all_7_lenses_present",
            "passed": False,
            "detail": f"Error checking lenses: {e}"
        })

    # Check 1.4: Strongest angle footer present
    try:
        quiz_pos = ideas_content.find("AI Quiz Generator")
        scamper_section = ideas_content[quiz_pos:] if quiz_pos != -1 else ideas_content
        strongest_angle_pattern = r"💡\s*\*\*Strongest angle:\*\*"
        has_strongest = bool(re.search(strongest_angle_pattern, scamper_section))
        checks.append({
            "name": "ideas_md_strongest_angle_footer",
            "passed": has_strongest,
            "detail": f"'💡 **Strongest angle:**' footer found in SCAMPER section: {has_strongest}"
        })
    except Exception as e:
        checks.append({
            "name": "ideas_md_strongest_angle_footer",
            "passed": False,
            "detail": f"Error checking strongest angle footer: {e}"
        })

    # Check 1.5: Exactly 3 hackathon concepts identified/listed
    try:
        quiz_pos = ideas_content.find("AI Quiz Generator")
        scamper_section = ideas_content[quiz_pos:] if quiz_pos != -1 else ideas_content

        # Look for numbered list items or explicit "Top 3" / concept markers
        # Accept numbered list 1. 2. 3. or explicit headers with "Concept 1/2/3" or "top 3"
        # Strategy: count distinct concept headers or numbered items after a filtering/top-concepts marker
        top3_section_patterns = [
            r"top\s*3",
            r"Top\s*3",
            r"top three",
            r"hackathon concept",
            r"Hackathon Concept",
            r"24h",
            r"24-hour",
            r"demo"
        ]
        has_top3_marker = any(re.search(p, scamper_section) for p in top3_section_patterns)

        # Count numbered items (1. ... 2. ... 3. ...) or bold concept headers
        numbered_items = re.findall(r"^\s*[1-3]\.\s+\S", scamper_section, re.MULTILINE)
        bold_concepts = re.findall(r"\*\*Concept\s+[123]", scamper_section)
        concept_headers = re.findall(r"#{1,4}\s+Concept\s+[123]", scamper_section)

        total_concept_markers = len(numbered_items) + len(bold_concepts) + len(concept_headers)
        # We expect at least 3 numbered/labeled concepts and a top-3 marker
        has_3_concepts = has_top3_marker and (total_concept_markers >= 3)

        checks.append({
            "name": "ideas_md_top3_hackathon_concepts",
            "passed": has_3_concepts,
            "detail": (
                f"Top-3 marker found: {has_top3_marker}, "
                f"numbered items: {len(numbered_items)}, "
                f"bold concepts: {len(bold_concepts)}, "
                f"concept headers: {len(concept_headers)}, "
                f"total concept markers: {total_concept_markers}"
            )
        })
    except Exception as e:
        checks.append({
            "name": "ideas_md_top3_hackathon_concepts",
            "passed": False,
            "detail": f"Error checking hackathon concepts: {e}"
        })

    # =========================================================
    # CHECK GROUP 2: framework_scamper.md - Framework Adaptation
    # =========================================================
    # Search for the file anywhere in the workspace
    try:
        found_files = list(workspace_path.rglob("framework_scamper.md"))
        fw_file_found = len(found_files) > 0
        fw_path = found_files[0] if fw_file_found else None
        checks.append({
            "name": "framework_scamper_md_exists",
            "passed": fw_file_found,
            "detail": f"framework_scamper.md found: {fw_file_found}. Path(s): {[str(p) for p in found_files]}"
        })
    except Exception as e:
        checks.append({
            "name": "framework_scamper_md_exists",
            "passed": False,
            "detail": f"Error searching for framework_scamper.md: {e}"
        })
        fw_path = None

    # Check 2.2: SCAMPER header for spaced repetition / framework
    try:
        if fw_path:
            fw_content = fw_path.read_text(encoding="utf-8")
            fw_header_pattern = r"###\s+SCAMPER:\s+.{3,}"
            has_fw_header = bool(re.search(fw_header_pattern, fw_content))
            checks.append({
                "name": "framework_scamper_header",
                "passed": has_fw_header,
                "detail": f"SCAMPER header present in framework_scamper.md: {has_fw_header}"
            })
        else:
            checks.append({
                "name": "framework_scamper_header",
                "passed": False,
                "detail": "framework_scamper.md not found, cannot check header."
            })
            fw_content = ""
    except Exception as e:
        checks.append({
            "name": "framework_scamper_header",
            "passed": False,
            "detail": f"Error reading framework_scamper.md: {e}"
        })
        fw_content = ""

    # Check 2.3: Framework Adaptation uses only Substitute, Combine, Adapt lenses (not all 7)
    try:
        if fw_content:
            # Must have Substitute, Combine, Adapt
            required_fw_lenses = [r"\*\*Substitute:\*\*", r"\*\*Combine:\*\*", r"\*\*Adapt:\*\*"]
            has_required = all(re.search(p, fw_content) for p in required_fw_lenses)

            # Should NOT have Modify, Put to other uses, Eliminate, Reverse
            # (Framework adaptation only uses S, C, A)
            forbidden_fw_lenses = [r"\*\*Modify:\*\*", r"\*\*Put to other uses:\*\*", r"\*\*Eliminate:\*\*", r"\*\*Reverse:\*\*"]
            has_forbidden = any(re.search(p, fw_content) for p in forbidden_fw_lenses)

            fw_lenses_correct = has_required and not has_forbidden
            checks.append({
                "name": "framework_scamper_correct_lenses",
                "passed": fw_lenses_correct,
                "detail": (
                    f"Has required S/C/A lenses: {has_required}, "
                    f"Has forbidden M/P/E/R lenses: {has_forbidden}. "
                    f"Framework Adaptation should only use Substitute, Combine, Adapt."
                )
            })
        else:
            checks.append({
                "name": "framework_scamper_correct_lenses",
                "passed": False,
                "detail": "framework_scamper.md not found or empty."
            })
    except Exception as e:
        checks.append({
            "name": "framework_scamper_correct_lenses",
            "passed": False,
            "detail": f"Error checking framework lenses: {e}"
        })

    # Check 2.4: Framework SCAMPER addresses the specific framework-adaptation sub-prompts
    try:
        if fw_content:
            # The Framework Adaptation sub-prompts are very specific:
            # Substitute: "What would you swap for your industry/role?"
            # Combine: "What other framework could this merge with?"
            # Adapt: "Who does something similar you could borrow from?"
            # Agent should address these angles in some form
            fw_lower = fw_content.lower()
            substitute_signals = ["industry", "role", "swap", "replace", "instead of"]
            combine_signals = ["framework", "merge", "blend", "combine", "integrate"]
            adapt_signals = ["borrow", "similar", "like this", "elsewhere", "copy", "who does"]

            sub_hit = any(s in fw_lower for s in substitute_signals)
            comb_hit = any(s in fw_lower for s in combine_signals)
            adapt_hit = any(s in fw_lower for s in adapt_signals)

            all_subprompts_addressed = sub_hit and comb_hit and adapt_hit
            checks.append({
                "name": "framework_scamper_sub_prompts_addressed",
                "passed": all_subprompts_addressed,
                "detail": (
                    f"Substitute sub-prompt signals present: {sub_hit}, "
                    f"Combine sub-prompt signals present: {comb_hit}, "
                    f"Adapt sub-prompt signals present: {adapt_hit}"
                )
            })
        else:
            checks.append({
                "name": "framework_scamper_sub_prompts_addressed",
                "passed": False,
                "detail": "framework_scamper.md not found or empty."
            })
    except Exception as e:
        checks.append({
            "name": "framework_scamper_sub_prompts_addressed",
            "passed": False,
            "detail": f"Error checking sub-prompts: {e}"
        })

    # Check 2.5: framework_scamper.md references spaced repetition / the source framework
    try:
        if fw_content:
            spaced_rep_signals = ["spaced repetition", "spaced_repetition", "spacing", "interval", "retention"]
            fw_lower = fw_content.lower()
            references_source = any(s in fw_lower for s in spaced_rep_signals)
            checks.append({
                "name": "framework_scamper_references_source_framework",
                "passed": references_source,
                "detail": f"framework_scamper.md references the source framework (spaced repetition): {references_source}"
            })
        else:
            checks.append({
                "name": "framework_scamper_references_source_framework",
                "passed": False,
                "detail": "framework_scamper.md not found or empty."
            })
    except Exception as e:
        checks.append({
            "name": "framework_scamper_references_source_framework",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # =========================================================
    # Final Score
    # =========================================================
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = round(passed_count / total_count, 4) if total_count > 0 else 0.0
    overall_passed = passed_count == total_count

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation_error", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))