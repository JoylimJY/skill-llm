import sys
import json
import re
from pathlib import Path

def find_content_ideas_file(workspace):
    candidates = list(Path(workspace).rglob("content_ideas.md"))
    if not candidates:
        return None
    return candidates[0]

def parse_table_rows(section_text):
    """Extract non-header, non-separator rows from a markdown table."""
    rows = []
    for line in section_text.splitlines():
        line = line.strip()
        if line.startswith("|") and not re.match(r"^\|[-| ]+\|$", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cells)
    # Remove header row (first row)
    if rows:
        rows = rows[1:]
    return rows

def run_checks(workspace):
    checks = []
    score = 0.0

    # --- Find the file ---
    fpath = find_content_ideas_file(workspace)
    if fpath is None:
        checks.append({"name": "file_exists", "passed": False, "detail": "content_ideas.md not found anywhere in workspace"})
        return False, 0.0, checks

    try:
        content = fpath.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"})
        return False, 0.0, checks

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {fpath}"})

    # -----------------------------------------------------------------------
    # CHECK 1: {AGENT_NAME} replaced with "Hana" throughout
    # -----------------------------------------------------------------------
    agent_placeholder_remaining = "{AGENT_NAME}" in content
    hana_present = "Hana" in content
    c1_passed = not agent_placeholder_remaining and hana_present
    checks.append({
        "name": "agent_name_substitution",
        "passed": c1_passed,
        "detail": (
            "PASS: {AGENT_NAME} replaced with Hana" if c1_passed
            else f"FAIL: placeholder_remaining={agent_placeholder_remaining}, hana_present={hana_present}"
        )
    })
    if c1_passed:
        score += 0.15

    # -----------------------------------------------------------------------
    # CHECK 2: すぐ使えるアイデア section has at least 3 original + ≥2 new rows
    # The new rows must have IDs continuing from 003 (i.e., 004, 005, ...)
    # They must use ⭐ notation for priority (not plain text like "high")
    # -----------------------------------------------------------------------
    try:
        ready_match = re.search(
            r"### すぐ使えるアイデア\n(.*?)(?=\n###|\Z)",
            content, re.DOTALL
        )
        if ready_match:
            ready_text = ready_match.group(1)
            ready_rows = parse_table_rows(ready_text)
            # Filter out placeholder rows (all dashes)
            real_rows = [r for r in ready_rows if not all(c == "-" for c in r)]
            
            c2a_passed = len(real_rows) >= 5  # original 3 + at least 2 new
            checks.append({
                "name": "ready_ideas_count",
                "passed": c2a_passed,
                "detail": f"Found {len(real_rows)} real rows in すぐ使えるアイデア (need ≥5)"
            })
            if c2a_passed:
                score += 0.10

            # IDs must be sequential numbers continuing from 003
            id_vals = []
            for row in real_rows:
                if row and re.match(r"^\d{3}$", row[0]):
                    id_vals.append(int(row[0]))
            new_ids = [i for i in id_vals if i > 3]
            c2b_passed = len(new_ids) >= 2 and all(isinstance(i, int) for i in new_ids)
            checks.append({
                "name": "ready_ideas_new_ids_sequential",
                "passed": c2b_passed,
                "detail": f"New IDs (>003) found: {new_ids}"
            })
            if c2b_passed:
                score += 0.10

            # Priority must use ⭐ stars
            star_count = sum(1 for row in real_rows if len(row) >= 5 and "⭐" in row[4])
            c2c_passed = star_count == len(real_rows)
            checks.append({
                "name": "priority_star_notation",
                "passed": c2c_passed,
                "detail": f"{star_count}/{len(real_rows)} rows use ⭐ star notation in priority column"
            })
            if c2c_passed:
                score += 0.10
        else:
            checks.append({"name": "ready_ideas_section_found", "passed": False, "detail": "すぐ使えるアイデア section not found"})
    except Exception as e:
        checks.append({"name": "ready_ideas_parse_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 3: 検討中のアイデア section has at least 1 real entry
    # Must follow schema: ID | カテゴリ | アイデア | メモ (4 columns)
    # -----------------------------------------------------------------------
    try:
        pending_match = re.search(
            r"### 検討中のアイデア\n(.*?)(?=\n###|\Z)",
            content, re.DOTALL
        )
        if pending_match:
            pending_text = pending_match.group(1)
            pending_rows = parse_table_rows(pending_text)
            real_pending = [r for r in pending_rows if not all(c == "-" for c in r)]
            
            c3a_passed = len(real_pending) >= 1
            checks.append({
                "name": "pending_ideas_has_entries",
                "passed": c3a_passed,
                "detail": f"Found {len(real_pending)} real pending idea rows (need ≥1)"
            })
            if c3a_passed:
                score += 0.10

            # Schema check: must have 4 columns
            correct_schema = all(len(row) == 4 for row in real_pending)
            checks.append({
                "name": "pending_ideas_4col_schema",
                "passed": correct_schema,
                "detail": f"Column counts: {[len(r) for r in real_pending]} (all must be 4)"
            })
            if correct_schema:
                score += 0.05
        else:
            checks.append({"name": "pending_section_found", "passed": False, "detail": "検討中のアイデア section not found"})
    except Exception as e:
        checks.append({"name": "pending_parse_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 4: 完了済み section has at least 1 real entry
    # Schema: ID | 投稿日 | 内容 | 反応 (4 columns)
    # Based on published_log.csv data: posts from 2/14, 2/22, 3/3 should be logged
    # -----------------------------------------------------------------------
    try:
        done_match = re.search(
            r"### 完了済み\n(.*?)(?=\n---|\Z)",
            content, re.DOTALL
        )
        if done_match:
            done_text = done_match.group(1)
            done_rows = parse_table_rows(done_text)
            real_done = [r for r in done_rows if not all(c == "-" for c in r)]

            c4a_passed = len(real_done) >= 1
            checks.append({
                "name": "completed_ideas_has_entries",
                "passed": c4a_passed,
                "detail": f"Found {len(real_done)} real completed rows (need ≥1)"
            })
            if c4a_passed:
                score += 0.10

            # Schema check: must have 4 columns
            correct_done_schema = all(len(row) == 4 for row in real_done)
            checks.append({
                "name": "completed_ideas_4col_schema",
                "passed": correct_done_schema,
                "detail": f"Column counts: {[len(r) for r in real_done]} (all must be 4)"
            })
            if correct_done_schema:
                score += 0.05
        else:
            checks.append({"name": "completed_section_found", "passed": False, "detail": "完了済み section not found"})
    except Exception as e:
        checks.append({"name": "completed_parse_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 5: 季節・イベントカレンダー still intact (all 3 months present)
    # -----------------------------------------------------------------------
    try:
        has_feb = "### 2月" in content
        has_mar = "### 3月" in content
        has_apr = "### 4月" in content
        c5_passed = has_feb and has_mar and has_apr
        checks.append({
            "name": "seasonal_calendar_intact",
            "passed": c5_passed,
            "detail": f"2月={has_feb}, 3月={has_mar}, 4月={has_apr}"
        })
        if c5_passed:
            score += 0.05
    except Exception as e:
        checks.append({"name": "seasonal_calendar_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 6: トレンド活用テンプレート still present with correct format
    # -----------------------------------------------------------------------
    try:
        trend_template_present = (
            "[トレンドワード]について、AIの視点から考えてみた" in content
            and "#[トレンドワード] #AI視点" in content
        )
        checks.append({
            "name": "trend_template_intact",
            "passed": trend_template_present,
            "detail": "Trend template with correct format preserved" if trend_template_present else "Trend template missing or malformed"
        })
        if trend_template_present:
            score += 0.05
    except Exception as e:
        checks.append({"name": "trend_template_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 7: 更新履歴 updated with a new entry beyond [2026-02-01]
    # -----------------------------------------------------------------------
    try:
        history_match = re.search(r"## 更新履歴.*?```(.*?)```", content, re.DOTALL)
        new_history_entries = []
        if history_match:
            history_text = history_match.group(1)
            entries = re.findall(r"\[(\d{4}-\d{2}-\d{2})\]", history_text)
            new_history_entries = [e for e in entries if e > "2026-02-01"]
        c7_passed = len(new_history_entries) >= 1
        checks.append({
            "name": "update_history_new_entry",
            "passed": c7_passed,
            "detail": f"New history entries after 2026-02-01: {new_history_entries}"
        })
        if c7_passed:
            score += 0.05
    except Exception as e:
        checks.append({"name": "update_history_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 8: New ideas use categories from the defined taxonomy
    # (AI体験, 日常・雑談, ノウハウ・Tips, 交流, or Note categories)
    # -----------------------------------------------------------------------
    valid_categories = ["AI体験", "自己紹介", "成長記録", "日常・雑談", "ノウハウ・Tips", "交流", "長文記事", "シリーズ"]
    try:
        ready_match2 = re.search(
            r"### すぐ使えるアイデア\n(.*?)(?=\n###|\Z)",
            content, re.DOTALL
        )
        if ready_match2:
            ready_rows2 = parse_table_rows(ready_match2.group(1))
            real_rows2 = [r for r in ready_rows2 if not all(c == "-" for c in r)]
            new_rows = [r for r in real_rows2 if r and re.match(r"^\d{3}$", r[0]) and int(r[0]) > 3]
            valid_cat_count = sum(1 for row in new_rows if len(row) >= 2 and row[1] in valid_categories)
            c8_passed = len(new_rows) == 0 or valid_cat_count >= max(1, len(new_rows) - 1)
            checks.append({
                "name": "new_ideas_use_valid_categories",
                "passed": c8_passed,
                "detail": f"{valid_cat_count}/{len(new_rows)} new ideas use valid taxonomy categories"
            })
            if c8_passed:
                score += 0.10
        else:
            checks.append({"name": "categories_check_skipped", "passed": False, "detail": "Could not find すぐ使えるアイデア for category check"})
    except Exception as e:
        checks.append({"name": "categories_check_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 9: Platform column uses valid values (X, Threads, Note, X/Threads, etc.)
    # -----------------------------------------------------------------------
    valid_platforms_patterns = [r"X$", r"Threads$", r"Note$", r"X/Threads", r"X/Note", r"Threads/Note", r"X/Threads/Note"]
    try:
        ready_match3 = re.search(
            r"### すぐ使えるアイデア\n(.*?)(?=\n###|\Z)",
            content, re.DOTALL
        )
        if ready_match3:
            ready_rows3 = parse_table_rows(ready_match3.group(1))
            real_rows3 = [r for r in ready_rows3 if not all(c == "-" for c in r)]
            platform_valid = []
            for row in real_rows3:
                if len(row) >= 4:
                    plat = row[3]
                    is_valid = any(re.search(p, plat) for p in valid_platforms_patterns)
                    platform_valid.append(is_valid)
            c9_passed = all(platform_valid) if platform_valid else False
            checks.append({
                "name": "platform_values_valid",
                "passed": c9_passed,
                "detail": f"{sum(platform_valid)}/{len(platform_valid)} rows have valid platform values"
            })
            if c9_passed:
                score += 0.05
        else:
            checks.append({"name": "platform_check_skipped", "passed": False, "detail": "Could not find section"})
    except Exception as e:
        checks.append({"name": "platform_check_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 10: 5W1H or 組み合わせ brainstorming method evidence
    # At least one idea should reflect the seasonal calendar (桜, エイプリル, 新年度, etc.)
    # or a combination method (AI × something)
    # -----------------------------------------------------------------------
    try:
        seasonal_keywords = ["桜", "エイプリル", "新年度", "新生活", "ひな祭り", "ホワイトデー", "春分", "年度末"]
        combination_pattern = r"AI[×x×]|[×x×]AI"
        
        full_ideabank_match = re.search(
            r"## アイデアバンク(.*?)(?=\n## )",
            content, re.DOTALL
        )
        bank_text = full_ideabank_match.group(1) if full_ideabank_match else content
        
        has_seasonal = any(kw in bank_text for kw in seasonal_keywords)
        has_combination = bool(re.search(combination_pattern, bank_text))
        c10_passed = has_seasonal or has_combination
        checks.append({
            "name": "brainstorm_method_applied",
            "passed": c10_passed,
            "detail": f"seasonal_content={has_seasonal}, combination_method={has_combination}"
        })
        if c10_passed:
            score += 0.10
    except Exception as e:
        checks.append({"name": "brainstorm_method_error", "passed": False, "detail": str(e)})

    passed = score >= 0.55
    return passed, round(score, 3), checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        passed, score, checks = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()