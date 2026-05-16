import sys
import json
import re
import os
from pathlib import Path

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    
    # ─── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ─── CHECK 1: Report file exists in report/ directory ────────────────────
    report_files = list((workspace / "report").glob("ds_*.md"))
    # Exclude the pre-existing old report
    report_files = [f for f in report_files if f.name != "old_report_nev_2023.md"]
    
    if not report_files:
        score = add_check(
            "report_file_exists",
            False,
            "No report file starting with 'ds_' found in report/ directory."
        )
        total_score += score
    else:
        score = add_check(
            "report_file_exists",
            True,
            f"Found report file(s): {[f.name for f in report_files]}"
        )
        total_score += score

    # ─── CHECK 2: Report filename follows ds_{snake_case}_{timestamp}.md format ─
    report_file = None
    if report_files:
        report_file = report_files[0]  # Use first valid one
        fname = report_file.name
        # Pattern: ds_ + snake_case_words + _ + timestamp (digits and underscores)
        # Timestamp can be YYYYMMDD_HHMMSS or just digits
        pattern = r'^ds_[a-z][a-z0-9_]+_\d{8,}.*\.md$'
        fname_valid = bool(re.match(pattern, fname))
        
        # More lenient check - just ensure it starts with ds_ and has something numeric
        lenient_pattern = r'^ds_.+_\d+.*\.md$'
        fname_lenient = bool(re.match(lenient_pattern, fname))
        
        score = add_check(
            "report_filename_format",
            fname_lenient,
            f"Filename '{fname}' {'matches' if fname_lenient else 'does NOT match'} "
            f"required pattern ds_{{snake_case}}_{{timestamp}}.md"
        )
        total_score += score
    else:
        score = add_check(
            "report_filename_format",
            False,
            "Cannot check filename: no report file found."
        )
        total_score += score

    # ─── CHECK 3: Report content - read it ───────────────────────────────────
    report_content = ""
    if report_file and report_file.exists():
        try:
            report_content = report_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            score = add_check(
                "report_readable",
                False,
                f"Could not read report file: {e}"
            )
            total_score += score
            report_content = ""
    
    if report_content:
        score = add_check(
            "report_readable",
            True,
            f"Report file is readable, length: {len(report_content)} chars"
        )
        total_score += score
    elif report_files:
        score = add_check(
            "report_readable",
            False,
            "Report file exists but could not be read."
        )
        total_score += score

    # ─── CHECK 4: Report is in English ───────────────────────────────────────
    if report_content:
        # Count Chinese characters
        chinese_chars = sum(1 for c in report_content if '\u4e00' <= c <= '\u9fff')
        total_chars = len(report_content)
        chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
        
        # Report should be primarily in English (< 20% Chinese characters)
        is_english = chinese_ratio < 0.20
        score = add_check(
            "report_written_in_english",
            is_english,
            f"Chinese character ratio: {chinese_ratio:.1%} "
            f"({'acceptable' if is_english else 'TOO HIGH - report should be in English'})"
        )
        total_score += score
    else:
        score = add_check("report_written_in_english", False, "No report content to check.")
        total_score += score

    # ─── CHECK 5: Required sections present ──────────────────────────────────
    if report_content:
        required_sections = [
            "Executive Summary",
            "Market Overview",
            "Technology",
            "Policy",
            "International",
            "Conclusion"
        ]
        found_sections = []
        missing_sections = []
        content_upper = report_content
        
        for section in required_sections:
            # Case-insensitive check for section headings
            if re.search(re.escape(section), content_upper, re.IGNORECASE):
                found_sections.append(section)
            else:
                missing_sections.append(section)
        
        sections_ok = len(found_sections) >= 4  # At least 4 of 6 required sections
        score = add_check(
            "required_sections_present",
            sections_ok,
            f"Found sections: {found_sections}. Missing: {missing_sections}. "
            f"Need at least 4/6 required sections."
        )
        total_score += score
    else:
        score = add_check("required_sections_present", False, "No report content to check.")
        total_score += score

    # ─── CHECK 6: Citations in [^N] footnote format ───────────────────────────
    if report_content:
        citation_pattern = r'\[\^(\d+)\]'
        citations = re.findall(citation_pattern, report_content)
        unique_citations = set(citations)
        
        # Need at least 8 citation references (min_sources is 12 but some flexibility)
        has_citations = len(unique_citations) >= 8
        score = add_check(
            "footnote_citations_present",
            has_citations,
            f"Found {len(unique_citations)} unique citation references [^N]. "
            f"Need at least 8 (target: 12+)."
        )
        total_score += score
    else:
        score = add_check("footnote_citations_present", False, "No report content to check.")
        total_score += score

    # ─── CHECK 7: Minimum sources (12) cited ─────────────────────────────────
    if report_content:
        citation_pattern = r'\[\^(\d+)\]'
        citations = re.findall(citation_pattern, report_content)
        unique_citations = set(citations)
        max_citation_num = max((int(c) for c in unique_citations), default=0)
        
        # Check citation count via highest citation number OR count of unique refs
        sources_ok = len(unique_citations) >= 12 or max_citation_num >= 12
        score = add_check(
            "minimum_12_sources",
            sources_ok,
            f"Unique citation count: {len(unique_citations)}, max citation number: {max_citation_num}. "
            f"Need at least 12 sources referenced."
        )
        total_score += score
    else:
        score = add_check("minimum_12_sources", False, "No report content to check.")
        total_score += score

    # ─── CHECK 8: Research questions addressed (NEV market topics) ────────────
    if report_content:
        content_lower = report_content.lower()
        key_topics = {
            "BYD or market share data": bool(re.search(r'byd|比亚迪|market share', content_lower)),
            "Battery technology (LFP/NMC/solid-state)": bool(re.search(r'lfp|nmc|lithium|battery|blade battery|solid.state', content_lower)),
            "Government policy": bool(re.search(r'policy|subsidy|subsidi|dual.credit|purchase tax|government', content_lower)),
            "Export/international expansion": bool(re.search(r'export|overseas|europe|global|international|hungary|thailand', content_lower)),
            "Competitive landscape": bool(re.search(r'tesla|nio|xpeng|li auto|huawei|competi', content_lower)),
        }
        
        covered_topics = [t for t, found in key_topics.items() if found]
        topics_ok = len(covered_topics) >= 4
        score = add_check(
            "research_questions_addressed",
            topics_ok,
            f"Topics covered: {covered_topics}. "
            f"Missing: {[t for t, f in key_topics.items() if not f]}. "
            f"Need at least 4/5 key topics."
        )
        total_score += score
    else:
        score = add_check("research_questions_addressed", False, "No report content to check.")
        total_score += score

    # ─── CHECK 9: index.md updated with new entry ─────────────────────────────
    index_path = workspace / "index.md"
    index_ok = False
    index_detail = ""
    
    try:
        if index_path.exists():
            index_content = index_path.read_text(encoding="utf-8", errors="replace")
            
            # Check that original entries still exist (not overwritten)
            has_original = "Global Semiconductor Supply Chain Analysis" in index_content
            
            # Check for new entry in correct format: - [title](path)
            # The new entry should link to the new report
            entry_pattern = r'- \[.+\]\(report/ds_.+\.md\)'
            new_entries = re.findall(entry_pattern, index_content)
            
            if not has_original:
                index_detail = "ERROR: Original index entries were deleted/overwritten. Must APPEND only."
                index_ok = False
            elif not new_entries:
                index_detail = (
                    f"No new entry found in index.md matching format '- [title](report/ds_*.md)'. "
                    f"Index content preview: {index_content[:300]}"
                )
                index_ok = False
            else:
                # Check if the entry actually points to the created report
                if report_file:
                    report_rel_path = f"report/{report_file.name}"
                    entry_matches_report = any(report_file.name in e for e in new_entries)
                    index_ok = entry_matches_report
                    index_detail = (
                        f"Found {len(new_entries)} new entry/entries. "
                        f"Entry matches created report: {entry_matches_report}. "
                        f"Entries: {new_entries}"
                    )
                else:
                    index_ok = bool(new_entries)
                    index_detail = f"Found new entries: {new_entries}"
        else:
            index_detail = "index.md file not found."
    except Exception as e:
        index_detail = f"Error reading index.md: {e}"
    
    score = add_check("index_md_updated", index_ok, index_detail)
    total_score += score

    # ─── CHECK 10: Evidence of bilingual search (Chinese content in report or 
    #               evidence of Chinese queries being used based on source diversity) ─
    if report_content:
        # Look for evidence that Chinese sources were consulted:
        # Either Chinese terms appear in the report or specific Chinese-source data appears
        chinese_source_indicators = [
            # Chinese-specific data points that would only come from Chinese sources
            r'caam|china automobile|工信部|miit\.gov|乘联会|盖世',
            r'dual.credit|双积分',
            r'blade battery|刀片电池',
            r'dm.?5|fifth.generation dm|第五代',
            r'baas|battery.as.a.service',
            r'aito|wenjie|问界',
        ]
        
        chinese_evidence = []
        for pattern in chinese_source_indicators:
            if re.search(pattern, report_content, re.IGNORECASE):
                chinese_evidence.append(pattern)
        
        bilingual_ok = len(chinese_evidence) >= 2
        score = add_check(
            "bilingual_search_evidence",
            bilingual_ok,
            f"Evidence of Chinese source consultation: {len(chinese_evidence)} indicators found "
            f"({chinese_evidence[:3]}). Need at least 2 China-specific data points "
            f"that would require Chinese-language sources."
        )
        total_score += score
    else:
        score = add_check("bilingual_search_evidence", False, "No report content to check.")
        total_score += score

    # ─── Compute final score ──────────────────────────────────────────────────
    num_checks = len(checks)
    final_score = total_score / num_checks if num_checks > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)
    
    return {
        "passed": all_passed,
        "score": round(final_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))