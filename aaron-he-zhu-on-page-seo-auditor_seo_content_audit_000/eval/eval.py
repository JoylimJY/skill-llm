#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
from datetime import datetime

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    
    # ── 1. Find the saved audit file ─────────────────────────────────────────
    audit_dir = workspace / "memory" / "audits" / "on-page-seo-auditor"
    
    try:
        audit_files = list(audit_dir.rglob("*.md"))
        has_audit_file = len(audit_files) > 0
        checks.append({
            "name": "audit_file_exists_in_correct_directory",
            "passed": has_audit_file,
            "detail": f"Found {len(audit_files)} .md file(s) in memory/audits/on-page-seo-auditor/: {[f.name for f in audit_files]}"
        })
    except Exception as e:
        checks.append({
            "name": "audit_file_exists_in_correct_directory",
            "passed": False,
            "detail": f"Exception reading audit dir: {e}"
        })
        audit_files = []

    # ── 2. Check filename follows YYYY-MM-DD-<topic>.md pattern ──────────────
    correct_filename_pattern = False
    audit_content = ""
    chosen_file = None
    
    try:
        pattern = re.compile(r'^\d{4}-\d{2}-\d{2}-.+\.md$')
        matching = [f for f in audit_files if pattern.match(f.name)]
        correct_filename_pattern = len(matching) > 0
        checks.append({
            "name": "audit_filename_follows_date_topic_convention",
            "passed": correct_filename_pattern,
            "detail": f"Files matching YYYY-MM-DD-<topic>.md: {[f.name for f in matching]}"
        })
        if matching:
            chosen_file = matching[0]
            audit_content = chosen_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "audit_filename_follows_date_topic_convention",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 3. Audit file contains one-line verdict / headline finding ────────────
    try:
        # Look for verdict/headline indicators
        has_verdict = bool(re.search(
            r'(verdict|headline|finding|summary|result|critical|score|overall)',
            audit_content, re.IGNORECASE
        ))
        checks.append({
            "name": "audit_file_contains_verdict_or_headline",
            "passed": has_verdict,
            "detail": "Looked for verdict/headline/finding/score keywords in audit file." + (f" File: {chosen_file}" if chosen_file else " No file found.")
        })
    except Exception as e:
        checks.append({
            "name": "audit_file_contains_verdict_or_headline",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 4. Audit file contains actionable items ───────────────────────────────
    try:
        # Look for numbered or bulleted actionable items
        has_actions = bool(re.search(
            r'(action|fix|recommend|priority|improve|optimiz)',
            audit_content, re.IGNORECASE
        ))
        checks.append({
            "name": "audit_file_contains_actionable_items",
            "passed": has_actions,
            "detail": "Looked for action/fix/recommend/priority keywords."
        })
    except Exception as e:
        checks.append({
            "name": "audit_file_contains_actionable_items",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 5. Find the main audit output (anywhere in workspace) ────────────────
    # The agent may have written the main audit report to a different file
    # We search broadly for the full audit content
    all_md_files = list(workspace.rglob("*.md")) + list(workspace.rglob("*.txt"))
    all_content = ""
    for f in all_md_files:
        try:
            all_content += f.read_text(encoding="utf-8", errors="ignore") + "\n"
        except Exception:
            pass
    # Also check for any .md files at workspace root
    for f in workspace.glob("*"):
        if f.is_file() and f.suffix in (".md", ".txt"):
            try:
                all_content += f.read_text(encoding="utf-8", errors="ignore") + "\n"
            except Exception:
                pass

    # ── 6. Title tag analysis: detected title is too long (78 chars) ─────────
    try:
        # The page title is "The Ultimate Guide to Buying Camping Equipment for Your Next Outdoor Adventure Trip - TrailPeak"
        # Agent should flag it as too long (>60 chars)
        title_length_flagged = bool(re.search(
            r'(title.{0,50}(too long|over|exceed|long|\d{2,3}\s*char)|'
            r'(\d{2,3}\s*char.{0,30}title)|'
            r'length.{0,30}(50|60|55|70|75|78|80))',
            all_content, re.IGNORECASE
        ))
        checks.append({
            "name": "title_length_issue_identified",
            "passed": title_length_flagged,
            "detail": "Agent should flag the title as too long (78 chars, exceeds 50-60 char guideline)."
        })
    except Exception as e:
        checks.append({
            "name": "title_length_issue_identified",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 7. Keyword not at front of title ─────────────────────────────────────
    try:
        keyword_position_flagged = bool(re.search(
            r'(keyword.{0,60}(not at front|not front|end|middle|missing from title|not in title|absent)|'
            r'(front.{0,30}keyword|keyword.{0,30}front).{0,30}(no|not|missing|❌|fail)|'
            r'eco camping gear.{0,80}(not|missing|absent).{0,30}title|'
            r'title.{0,80}(not|missing|absent).{0,30}eco camping gear)',
            all_content, re.IGNORECASE
        ))
        checks.append({
            "name": "keyword_placement_in_title_identified",
            "passed": keyword_position_flagged,
            "detail": "Agent should identify that the target keyword 'eco camping gear' is not at the front of (or present in) the title."
        })
    except Exception as e:
        checks.append({
            "name": "keyword_placement_in_title_identified",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 8. Meta description too short (82 chars, needs 150-160) ──────────────
    try:
        meta_short_flagged = bool(re.search(
            r'(meta.{0,50}(too short|short|under|below|less than|only \d+)|'
            r'description.{0,50}(too short|short|\d{2,3}\s*char)|'
            r'(150|160).{0,30}(meta|description)|'
            r'(meta|description).{0,30}(150|160))',
            all_content, re.IGNORECASE
        ))
        checks.append({
            "name": "meta_description_too_short_identified",
            "passed": meta_short_flagged,
            "detail": "Agent should flag meta description as too short (82 chars vs 150-160 char guideline)."
        })
    except Exception as e:
        checks.append({
            "name": "meta_description_too_short_identified",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 9. Missing H1 tag identified ─────────────────────────────────────────
    try:
        missing_h1_flagged = bool(re.search(
            r'(no h1|missing h1|h1.{0,30}(missing|absent|not found|none|0)|'
            r'(missing|absent|no).{0,20}h1|'
            r'h1.{0,30}❌|'
            r'single h1.{0,30}(❌|fail|no|0\s*h1)|'
            r'found.{0,20}0.{0,10}h1)',
            all_content, re.IGNORECASE
        ))
        checks.append({
            "name": "missing_h1_tag_identified",
            "passed": missing_h1_flagged,
            "detail": "Agent should detect and flag the missing H1 tag — the page has only H2s and H4s."
        })
    except Exception as e:
        checks.append({
            "name": "missing_h1_tag_identified",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 10. Skipped header levels identified (H2→H4, no H3) ─────────────────
    try:
        skipped_levels_flagged = bool(re.search(
            r'(skip.{0,40}(level|h3|header|heading)|'
            r'(h2.{0,20}h4|h2.{0,30}jump|jump.{0,30}h4)|'
            r'(no h3|missing h3|h3.{0,20}missing)|'
            r'(hierarchy|structure).{0,60}(broken|incorrect|skip|jump|wrong|issue)|'
            r'h4.{0,30}(without|no|missing).{0,10}h3)',
            all_content, re.IGNORECASE
        ))
        checks.append({
            "name": "skipped_header_levels_identified",
            "passed": skipped_levels_flagged,
            "detail": "Agent should detect H2→H4 skip (no H3 present), indicating broken header hierarchy."
        })
    except Exception as e:
        checks.append({
            "name": "skipped_header_levels_identified",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 11. Images missing alt text identified ────────────────────────────────
    try:
        images_alt_flagged = bool(re.search(
            r'(alt.{0,40}(missing|absent|empty|no|without|❌|fail)|'
            r'(missing|no|without).{0,20}alt|'
            r'image.{0,40}(alt|optimiz|missing)|'
            r'alt text.{0,30}(missing|not|no|0))',
            all_content, re.IGNORECASE
        ))
        checks.append({
            "name": "images_missing_alt_text_identified",
            "passed": images_alt_flagged,
            "detail": "Agent should flag the 3 images that have no alt text attributes."
        })
    except Exception as e:
        checks.append({
            "name": "images_missing_alt_text_identified",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 12. Poor anchor text identified ("click here") ───────────────────────
    try:
        anchor_text_flagged = bool(re.search(
            r'(click here.{0,60}(anchor|link|poor|bad|generic|improve|fix)|'
            r'(anchor text|link text).{0,60}(poor|generic|click here|non-descriptive|improve)|'
            r'(poor|bad|generic|improve).{0,40}(anchor|link text))',
            all_content, re.IGNORECASE
        ))
        checks.append({
            "name": "poor_anchor_text_identified",
            "passed": anchor_text_flagged,
            "detail": "Agent should flag 'click here' as poor/non-descriptive anchor text for internal links."
        })
    except Exception as e:
        checks.append({
            "name": "poor_anchor_text_identified",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 13. Audit includes a score or scoring indicators ─────────────────────
    try:
        has_score = bool(re.search(
            r'(\d+\s*/\s*10|\d+\s*out of\s*10|score\s*:\s*\d+|overall.{0,30}\d+|'
            r'(title|header|meta|content|image).{0,20}score)',
            all_content, re.IGNORECASE
        ))
        checks.append({
            "name": "audit_includes_scores",
            "passed": has_score,
            "detail": "Audit should include numeric scores (e.g., X/10) per section."
        })
    except Exception as e:
        checks.append({
            "name": "audit_includes_scores",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 14. Status symbols (✅/⚠️/❌) used in tables ─────────────────────────
    try:
        has_status_symbols = bool(re.search(
            r'(✅|⚠️|❌)',
            all_content
        ))
        checks.append({
            "name": "audit_uses_status_symbols",
            "passed": has_status_symbols,
            "detail": "Audit should use ✅/⚠️/❌ status symbols in criterion tables per SKILL.md format."
        })
    except Exception as e:
        checks.append({
            "name": "audit_uses_status_symbols",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── 15. Priority / recommended fixes section present ─────────────────────
    try:
        has_priority_section = bool(re.search(
            r'(critical|high priority|priority.{0,20}(fix|issue|repair)|'
            r'(fix|repair|address).{0,20}(first|immediately|critical)|'
            r'priority.{0,5}(1|2|3|one|two|three))',
            all_content, re.IGNORECASE
        ))
        checks.append({
            "name": "audit_includes_prioritized_fixes",
            "passed": has_priority_section,
            "detail": "Audit should include a prioritized repair plan with critical/important/minor classification."
        })
    except Exception as e:
        checks.append({
            "name": "audit_includes_prioritized_fixes",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── compute final score ───────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    
    # Must pass at least 10 of 15 checks to be considered passing
    overall_passed = passed_count >= 10

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()