#!/usr/bin/env python3
"""
Evaluation script for article-bookmarker task.
Usage: python3 eval.py <workspace_dir>
"""
import sys
import json
import re
import os
from pathlib import Path

def find_bookmark_dir(workspace: Path) -> Path:
    """Return the expected bookmark directory."""
    return workspace / "bookmarks"

def load_state(bookmark_dir: Path) -> dict:
    state = {}
    state_file = bookmark_dir / ".bookmark_state"
    if state_file.exists():
        for line in state_file.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                state[k.strip()] = v.strip()
    return state

def find_article_files(bookmark_dir: Path):
    """Return all .md files excluding TAG_INDEX.md and README.md"""
    return [
        f for f in bookmark_dir.glob("*.md")
        if f.name not in ("TAG_INDEX.md", "README.md")
    ]

def check_bookmark_file_format(content: str, url_fragment: str) -> dict:
    """Check a bookmark file for required sections and fields."""
    issues = []

    # Must start with # <Title>
    if not re.match(r'^# .+', content.strip()):
        issues.append("Missing H1 title at top")

    # Must have **Source:** field
    if not re.search(r'\*\*Source:\*\*\s*https?://', content):
        issues.append("Missing or malformed **Source:** field")

    # Must have **Bookmarked:** with GMT+8
    if not re.search(r'\*\*Bookmarked:\*\*\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+GMT\+8', content):
        issues.append("Missing or malformed **Bookmarked:** field (must include GMT+8)")

    # Must have **Tags:** field
    if not re.search(r'\*\*Tags:\*\*\s*\S+', content):
        issues.append("Missing **Tags:** field")

    # Must have ## Summary section
    if '## Summary' not in content:
        issues.append("Missing ## Summary section")

    # Must have ## Content section
    if '## Content' not in content:
        issues.append("Missing ## Content section")

    # Summary must come BEFORE Content
    summary_pos = content.find('## Summary')
    content_pos = content.find('## Content')
    if summary_pos != -1 and content_pos != -1 and summary_pos > content_pos:
        issues.append("## Summary must appear before ## Content")

    # Must have ## Original URL section at the bottom
    if '## Original URL' not in content:
        issues.append("Missing ## Original URL section")

    # Summary section must have actual content
    summary_match = re.search(r'## Summary\s+([\s\S]+?)(?=##|\Z)', content)
    if summary_match:
        summary_text = summary_match.group(1).strip()
        if len(summary_text) < 50:
            issues.append(f"Summary section appears empty or too short ({len(summary_text)} chars)")
    else:
        issues.append("Could not parse ## Summary section content")

    return issues

def check_filename_conventions(filename: str) -> list:
    """Check SEO-friendly filename conventions."""
    issues = []
    name = filename.replace(".md", "")
    if name != name.lower():
        issues.append(f"Filename '{filename}' is not all lowercase")
    if re.search(r'[A-Z\s]', name):
        issues.append(f"Filename '{filename}' contains uppercase or spaces")
    if len(name) > 55:
        issues.append(f"Filename '{filename}' exceeds ~50 char limit ({len(name)} chars)")
    return issues

def check_tag_index(tag_index_content: str, article_filenames: list) -> list:
    """Check TAG_INDEX.md for required structure."""
    issues = []

    if '# Article Tag Index' not in tag_index_content:
        issues.append("TAG_INDEX.md missing '# Article Tag Index' header")

    if '## Tags' not in tag_index_content:
        issues.append("TAG_INDEX.md missing '## Tags' section")

    if '## Articles by Tag Count' not in tag_index_content:
        issues.append("TAG_INDEX.md missing '## Articles by Tag Count' section (required by file-structure.md)")

    # Tags section must come before Articles by Tag Count
    tags_pos = tag_index_content.find('## Tags')
    count_pos = tag_index_content.find('## Articles by Tag Count')
    if tags_pos != -1 and count_pos != -1 and tags_pos > count_pos:
        issues.append("'## Tags' must appear before '## Articles by Tag Count'")

    # Each article file should appear in the tag index
    for fname in article_filenames:
        if fname not in tag_index_content:
            issues.append(f"Article '{fname}' not referenced in TAG_INDEX.md")

    # Tags section should have at least one bold tag entry
    tags_section_match = re.search(r'## Tags\s+([\s\S]+?)(?=##|\Z)', tag_index_content)
    if tags_section_match:
        tags_section = tags_section_match.group(1)
        bold_tags = re.findall(r'\*\*([^*]+)\*\*', tags_section)
        if len(bold_tags) == 0:
            issues.append("TAG_INDEX.md ## Tags section has no bold tag entries")
        # Check consistent vocabulary (no "artificial-intelligence" when "AI" should be used)
        for tag in bold_tags:
            if tag.lower() in ("artificial-intelligence", "machine-learning", "deep-learning"):
                issues.append(
                    f"Tag '{tag}' uses hyphenated form; consistent vocabulary prefers short forms like 'AI', 'ML', 'DL'"
                )
    else:
        issues.append("Could not parse ## Tags section from TAG_INDEX.md")

    # Articles by Tag Count section should reference articles with counts
    count_section_match = re.search(r'## Articles by Tag Count\s+([\s\S]+?)(?=##|\Z)', tag_index_content)
    if count_section_match:
        count_section = count_section_match.group(1).strip()
        if len(count_section) < 10:
            issues.append("## Articles by Tag Count section appears empty")
        # Should have entries like "- N tags: [...]"
        if not re.search(r'-\s+\d+\s+tags?:', count_section):
            issues.append("## Articles by Tag Count section missing '- N tags:' entries")
    else:
        issues.append("Could not parse ## Articles by Tag Count section")

    return issues

def check_script_invocations(state: dict) -> list:
    """Check that bookmark.sh was called correctly (init + save)."""
    issues = []
    if state.get("init_called") != "true":
        issues.append("scripts/bookmark.sh init was never called (or called without ARTICLE_BOOKMARK_DIR env var)")
    if state.get("save_called") != "true":
        issues.append("scripts/bookmark.sh save was never called")
    if state.get("save_msg"):
        msg = state["save_msg"]
        if "add" not in msg.lower() and "article" not in msg.lower():
            issues.append(f"Save commit message '{msg}' doesn't describe adding articles")
    return issues

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    bookmark_dir = find_bookmark_dir(workspace)

    checks = []
    total_score = 0.0

    # ── CHECK 1: Bookmark directory exists ─────────────────────────────────
    try:
        dir_exists = bookmark_dir.exists() and bookmark_dir.is_dir()
        checks.append({
            "name": "bookmark_directory_created",
            "passed": dir_exists,
            "detail": f"Bookmark directory {bookmark_dir} {'exists' if dir_exists else 'does NOT exist'}"
        })
        if dir_exists:
            total_score += 5
    except Exception as e:
        checks.append({"name": "bookmark_directory_created", "passed": False, "detail": str(e)})

    # ── CHECK 2: script invocations ─────────────────────────────────────────
    try:
        state = load_state(bookmark_dir) if bookmark_dir.exists() else {}
        script_issues = check_script_invocations(state)
        script_passed = len(script_issues) == 0
        checks.append({
            "name": "script_bookmark_sh_called_correctly",
            "passed": script_passed,
            "detail": "; ".join(script_issues) if script_issues else
                      f"bookmark.sh init and save called correctly (save_msg='{state.get('save_msg', '')}')"
        })
        if script_passed:
            total_score += 15
    except Exception as e:
        checks.append({"name": "script_bookmark_sh_called_correctly", "passed": False, "detail": str(e)})

    # ── CHECK 3: Two bookmark files exist ───────────────────────────────────
    try:
        if not bookmark_dir.exists():
            article_files = []
        else:
            article_files = find_article_files(bookmark_dir)

        two_articles = len(article_files) >= 2
        checks.append({
            "name": "two_bookmark_files_created",
            "passed": two_articles,
            "detail": f"Found {len(article_files)} bookmark file(s): {[f.name for f in article_files]}"
        })
        if two_articles:
            total_score += 10
    except Exception as e:
        checks.append({"name": "two_bookmark_files_created", "passed": False, "detail": str(e)})
        article_files = []

    # ── CHECK 4: Filename conventions for both articles ─────────────────────
    try:
        filename_issues_all = []
        for f in article_files:
            issues = check_filename_conventions(f.name)
            filename_issues_all.extend([f"{f.name}: {i}" for i in issues])
        filename_ok = len(filename_issues_all) == 0
        checks.append({
            "name": "seo_filename_conventions",
            "passed": filename_ok,
            "detail": "; ".join(filename_issues_all) if filename_issues_all else
                      "All bookmark filenames follow SEO conventions"
        })
        if filename_ok:
            total_score += 10
    except Exception as e:
        checks.append({"name": "seo_filename_conventions", "passed": False, "detail": str(e)})

    # ── CHECK 5: Bookmark file format for article 1 (transformer) ───────────
    transformer_file = None
    try:
        for f in article_files:
            content = f.read_text(encoding="utf-8")
            if "transformer" in content.lower() or "clinical decision" in content.lower():
                transformer_file = f
                break

        if transformer_file is None:
            checks.append({
                "name": "article1_transformer_format",
                "passed": False,
                "detail": "Could not find transformer/clinical-decision bookmark file"
            })
        else:
            content = transformer_file.read_text(encoding="utf-8")
            issues = check_bookmark_file_format(content, "pubmed.example.org")
            passed = len(issues) == 0
            checks.append({
                "name": "article1_transformer_format",
                "passed": passed,
                "detail": "; ".join(issues) if issues else
                          f"Transformer article bookmark ({transformer_file.name}) is correctly formatted"
            })
            if passed:
                total_score += 15
    except Exception as e:
        checks.append({"name": "article1_transformer_format", "passed": False, "detail": str(e)})

    # ── CHECK 6: Bookmark file format for article 2 (federated learning) ────
    federated_file = None
    try:
        for f in article_files:
            content = f.read_text(encoding="utf-8")
            if "federated" in content.lower() or "medical image" in content.lower():
                federated_file = f
                break

        if federated_file is None:
            checks.append({
                "name": "article2_federated_format",
                "passed": False,
                "detail": "Could not find federated-learning bookmark file"
            })
        else:
            content = federated_file.read_text(encoding="utf-8")
            issues = check_bookmark_file_format(content, "npjdigitalmed.example.org")
            passed = len(issues) == 0
            checks.append({
                "name": "article2_federated_format",
                "passed": passed,
                "detail": "; ".join(issues) if issues else
                          f"Federated learning article bookmark ({federated_file.name}) is correctly formatted"
            })
            if passed:
                total_score += 15
    except Exception as e:
        checks.append({"name": "article2_federated_format", "passed": False, "detail": str(e)})

    # ── CHECK 7: Summaries are substantive (150+ words) ─────────────────────
    try:
        short_summaries = []
        for f in article_files:
            content = f.read_text(encoding="utf-8")
            summary_match = re.search(r'## Summary\s+([\s\S]+?)(?=##|\Z)', content)
            if summary_match:
                summary_text = summary_match.group(1).strip()
                word_count = len(summary_text.split())
                if word_count < 80:
                    short_summaries.append(f"{f.name}: {word_count} words (expected 150-300)")
        summary_ok = len(short_summaries) == 0
        checks.append({
            "name": "summaries_substantive",
            "passed": summary_ok,
            "detail": "; ".join(short_summaries) if short_summaries else
                      "Both summaries have sufficient length"
        })
        if summary_ok:
            total_score += 10
    except Exception as e:
        checks.append({"name": "summaries_substantive", "passed": False, "detail": str(e)})

    # ── CHECK 8: TAG_INDEX.md exists ─────────────────────────────────────────
    tag_index_content = None
    try:
        tag_index_path = bookmark_dir / "TAG_INDEX.md"
        tag_index_exists = tag_index_path.exists()
        if tag_index_exists:
            tag_index_content = tag_index_path.read_text(encoding="utf-8")
        checks.append({
            "name": "tag_index_exists",
            "passed": tag_index_exists,
            "detail": f"TAG_INDEX.md {'exists' if tag_index_exists else 'does NOT exist'} at {tag_index_path}"
        })
        if tag_index_exists:
            total_score += 5
    except Exception as e:
        checks.append({"name": "tag_index_exists", "passed": False, "detail": str(e)})

    # ── CHECK 9: TAG_INDEX.md structure (the proprietary trap) ───────────────
    try:
        if tag_index_content is None:
            checks.append({
                "name": "tag_index_structure",
                "passed": False,
                "detail": "TAG_INDEX.md is missing; cannot check structure"
            })
        else:
            article_filenames = [f.name for f in article_files]
            issues = check_tag_index(tag_index_content, article_filenames)
            passed = len(issues) == 0
            checks.append({
                "name": "tag_index_structure",
                "passed": passed,
                "detail": "; ".join(issues) if issues else
                          "TAG_INDEX.md has correct structure with both '## Tags' and '## Articles by Tag Count' sections"
            })
            if passed:
                total_score += 15
    except Exception as e:
        checks.append({"name": "tag_index_structure", "passed": False, "detail": str(e)})

    # ── CHECK 10: GMT+8 timestamp in both bookmarks ──────────────────────────
    try:
        gmt8_issues = []
        for f in article_files:
            content = f.read_text(encoding="utf-8")
            if not re.search(r'\*\*Bookmarked:\*\*\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+GMT\+8', content):
                gmt8_issues.append(f"{f.name}: missing GMT+8 in **Bookmarked:** field")
        gmt8_ok = len(gmt8_issues) == 0
        checks.append({
            "name": "gmt8_timestamp_format",
            "passed": gmt8_ok,
            "detail": "; ".join(gmt8_issues) if gmt8_issues else
                      "Both bookmarks have correct GMT+8 timestamp format"
        })
        if gmt8_ok:
            total_score += 10
    except Exception as e:
        checks.append({"name": "gmt8_timestamp_format", "passed": False, "detail": str(e)})

    # ── Final scoring ────────────────────────────────────────────────────────
    max_score = 110.0  # slightly over 100 to allow partial credit
    normalized_score = min(1.0, total_score / 100.0)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())