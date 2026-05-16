import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    weights = {}

    # --- Find the output file ---
    # Must match: 人月神话_整理.md (or similar with book name + _整理.md)
    candidates = list(workspace.rglob("*_整理.md"))
    # Also look for the specific expected filename
    exact_matches = [f for f in candidates if "人月神话" in f.name or "mythical" in f.name.lower() or "man-month" in f.name.lower()]
    
    if not exact_matches:
        # Broader search: any _整理.md file
        if not candidates:
            checks.append(check("file_exists", False, f"No *_整理.md file found anywhere in workspace. Searched: {workspace}"))
            return {"passed": False, "score": 0.0, "checks": checks}
        target_file = candidates[0]
    else:
        target_file = exact_matches[0]

    checks.append(check("file_exists", True, f"Found output file: {target_file.relative_to(workspace)}"))
    total_score += 0.05

    # Read content
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": total_score, "checks": checks}

    checks.append(check("file_readable", True, f"File read successfully, length={len(content)} chars"))

    # --- Check 1: Filename convention ---
    filename = target_file.name
    has_correct_suffix = filename.endswith("_整理.md")
    has_book_name = "人月神话" in filename or "mythical" in filename.lower()
    filename_ok = has_correct_suffix and has_book_name
    checks.append(check(
        "filename_convention",
        filename_ok,
        f"Filename: '{filename}'. Must contain book name (人月神话) and end with '_整理.md'"
    ))
    if filename_ok:
        total_score += 0.05

    # --- Check 2: Emoji section headers (from template spec) ---
    required_emojis = ["📚", "📖", "🗂️", "💡", "✨", "🎯", "💭", "🧠"]
    found_emojis = [e for e in required_emojis if e in content]
    emoji_ratio = len(found_emojis) / len(required_emojis)
    emoji_ok = emoji_ratio >= 0.75  # at least 6/8
    checks.append(check(
        "emoji_section_headers",
        emoji_ok,
        f"Found {len(found_emojis)}/{len(required_emojis)} required emoji headers: {found_emojis}. Missing: {[e for e in required_emojis if e not in content]}"
    ))
    if emoji_ok:
        total_score += 0.10

    # --- Check 3: Book info table (2-column attribute table) ---
    # Must have | 属性 | 内容 | header or similar book info table
    has_info_table = bool(re.search(r'\|\s*(属性|书名|作者)\s*\|', content))
    # Must have actual book data
    has_author = bool(re.search(r'(弗雷德[里克]*·布鲁克斯|Brooks|Frederick)', content, re.IGNORECASE))
    info_table_ok = has_info_table and has_author
    checks.append(check(
        "book_info_table",
        info_table_ok,
        f"Book info table present: {has_info_table}, Author (Brooks) present: {has_author}"
    ))
    if info_table_ok:
        total_score += 0.10

    # --- Check 4: 6-column concept table (the proprietary trap from references/templates.md) ---
    # The templates.md specifies: | 序号 | 概念 | 英文 | 简明解释 | 章节 | 应用场景 |
    # Basic SKILL.md only has 3 columns: | 概念 | 解释 | 出现在 |
    six_col_pattern = re.search(
        r'\|\s*序号\s*\|\s*概念\s*\|\s*英文\s*\|\s*(简明解释|解释)\s*\|\s*章节\s*\|\s*应用场景\s*\|',
        content
    )
    has_six_col = six_col_pattern is not None
    
    # Also check that there's actual content in the table (not just headers)
    concept_rows = re.findall(r'\|\s*\d+\s*\|[^|\n]+\|[^|\n]+\|[^|\n]+\|[^|\n]+\|[^|\n]+\|', content)
    has_concept_rows = len(concept_rows) >= 2
    
    concept_table_ok = has_six_col and has_concept_rows
    checks.append(check(
        "six_column_concept_table",
        concept_table_ok,
        f"6-column concept table header found: {has_six_col}, Data rows (≥2): {has_concept_rows} (found {len(concept_rows)}). This is the extended template from references/templates.md"
    ))
    if concept_table_ok:
        total_score += 0.20

    # --- Check 5: Mermaid mind map with graph TD ---
    mermaid_block = re.search(r'```mermaid\s*\ngraph TD', content)
    mermaid_has_nodes = re.search(r'```mermaid.*?graph TD.*?-->', content, re.DOTALL)
    mermaid_ok = mermaid_block is not None and mermaid_has_nodes is not None
    checks.append(check(
        "mermaid_mindmap_graph_td",
        mermaid_ok,
        f"Mermaid block with 'graph TD': {mermaid_block is not None}, Has arrow connections (-->): {mermaid_has_nodes is not None}"
    ))
    if mermaid_ok:
        total_score += 0.15

    # --- Check 6: Categorized 金句 (quotes with subsections) ---
    # templates.md specifies subsections like ### 关于人生, ### 关于成长, etc.
    quote_sections = re.findall(r'###\s+关于\S+', content)
    has_quote_categories = len(quote_sections) >= 2
    # Also check blockquote format with attribution
    quote_blocks = re.findall(r'>\s+"[^"]+"\s*\n>\s*——', content)
    has_quote_blocks = len(quote_blocks) >= 1
    quotes_ok = has_quote_categories and has_quote_blocks
    checks.append(check(
        "categorized_quotes_with_attribution",
        quotes_ok,
        f"Quote category subsections (### 关于X): {len(quote_sections)}, Blockquotes with '——' attribution: {len(quote_blocks)}"
    ))
    if quotes_ok:
        total_score += 0.15

    # --- Check 7: 读后感 with star rating ---
    # templates.md requires: ★★★★☆（x/5星）
    star_rating = re.search(r'[★☆]{5}[（(]\d/5星[)）]', content)
    has_star_rating = star_rating is not None
    # Also check for required subsections in 读后感
    has_yijuhua = "一句话总结" in content
    has_suitability = "适合谁读" in content or "适合人群" in content
    duhougan_ok = has_star_rating and has_yijuhua and has_suitability
    checks.append(check(
        "duhougan_with_star_rating",
        duhougan_ok,
        f"Star rating (★/☆ pattern): {has_star_rating}, 一句话总结: {has_yijuhua}, 适合谁读: {has_suitability}"
    ))
    if duhougan_ok:
        total_score += 0.10

    # --- Check 8: Timestamp footer ---
    timestamp_ok = bool(re.search(r'\*整理时间：\d{4}-\d{2}-\d{2}\*', content))
    checks.append(check(
        "timestamp_footer",
        timestamp_ok,
        f"Footer '*整理时间：YYYY-MM-DD*' present: {timestamp_ok}"
    ))
    if timestamp_ok:
        total_score += 0.05

    # --- Check 9: Content quality (Brooks' Law, No Silver Bullet) ---
    has_brooks_law = bool(re.search(r'布鲁克斯(定律|法则)|Brooks.*Law', content, re.IGNORECASE))
    has_no_silver = bool(re.search(r'没有银弹|No Silver Bullet', content, re.IGNORECASE))
    has_chapter_summary = bool(re.search(r'第[一二三四五六七八九十\d]+章', content))
    content_quality_ok = has_brooks_law and has_no_silver and has_chapter_summary
    checks.append(check(
        "content_quality",
        content_quality_ok,
        f"Brooks' Law mentioned: {has_brooks_law}, No Silver Bullet: {has_no_silver}, Chapter summaries: {has_chapter_summary}"
    ))
    if content_quality_ok:
        total_score += 0.05

    # --- Final decision ---
    # Must pass critical checks to pass overall
    critical_checks = [
        "file_exists",
        "six_column_concept_table",
        "mermaid_mindmap_graph_td",
        "categorized_quotes_with_attribution",
        "duhougan_with_star_rating",
    ]
    critical_results = {c["name"]: c["passed"] for c in checks}
    critical_passed_count = sum(1 for c in critical_checks if critical_results.get(c, False))
    
    overall_passed = (
        critical_results.get("file_exists", False) and
        critical_passed_count >= 4 and  # must pass 4/5 critical checks
        total_score >= 0.50
    )

    return {
        "passed": overall_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))