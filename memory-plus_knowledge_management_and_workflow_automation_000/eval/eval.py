import sys
import json
import sqlite3
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)
    skill_dir = Path.home() / ".openclaw" / "workspace" / "skills" / "memory-workflow"
    data_dir = Path.home() / ".openclaw" / "workspace" / "memory-workflow-data"
    memories_dir = data_dir / "memories"
    fts5_db = data_dir / "fts5_index.db"
    kg_db = data_dir / "knowledge-graph" / "kg.db"
    agents_md = Path.home() / ".openclaw" / "workspace" / "AGENTS.md"

    # =========================================================
    # CHECK 1: AGENTS.md has the memory-workflow installation marker
    # =========================================================
    check_name = "agents_md_has_install_marker"
    try:
        content = agents_md.read_text(encoding="utf-8")
        has_marker = "<!-- [memory-workflow] 已安装 -->" in content
        has_section = "## 每次消息时" in content
        passed = has_marker and has_section
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"marker={'found' if has_marker else 'MISSING'}, section={'found' if has_section else 'MISSING'}"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 2: Memory files created in correct location (YYYY-MM-DD.md)
    # =========================================================
    check_name = "memory_files_created"
    try:
        md_files = list(memories_dir.glob("*.md"))
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
        valid_files = [f for f in md_files if date_pattern.match(f.name)]
        passed = len(valid_files) >= 1
        # Count total memory entries
        total_entries = 0
        for f in valid_files:
            content = f.read_text(encoding="utf-8")
            total_entries += content.count("## ")
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Found {len(valid_files)} date-formatted memory files, {total_entries} total entries"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 3: FTS5 index was populated (memories are indexed)
    # =========================================================
    check_name = "fts5_index_populated"
    try:
        conn = sqlite3.connect(str(fts5_db))
        rows = conn.execute("SELECT COUNT(*) FROM memories_fts").fetchone()
        conn.close()
        count = rows[0] if rows else 0
        # Should have at least 4 unique memories stored (8 notes minus ~2 duplicates)
        # but we check for >= 4 to be lenient about exact dedup behavior
        passed = count >= 4
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"FTS5 index has {count} entries (expected >= 4 after dedup)"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 4: Deduplication was performed — near-duplicates removed
    # FTS5 index should NOT have both NOTE 1 and NOTE 3 (near-dups)
    # AND should NOT have both NOTE 2 and NOTE 6 (near-dups)
    # =========================================================
    check_name = "dedup_removed_near_duplicates"
    try:
        conn = sqlite3.connect(str(fts5_db))
        rows = conn.execute("SELECT content FROM memories_fts").fetchall()
        conn.close()
        
        # Extract contents
        contents = [r[0] for r in rows]
        
        # Check for NOTE1/NOTE3 pair: both contain 梯度下降 + 深度学习 + 优化
        gradient_entries = [c for c in contents if "梯度下降" in c and ("深度学习" in c or "深度") and "优化" in c]
        # Check for NOTE2/NOTE6 pair: both contain Adam + 优化器 + 学习率
        adam_entries = [c for c in contents if "Adam" in c and "优化" in c]
        
        # At most 1 entry for each near-duplicate group
        gradient_deduped = len(gradient_entries) <= 1
        adam_deduped = len(adam_entries) <= 1
        
        passed = gradient_deduped and adam_deduped
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": (
                f"Gradient-descent group: {len(gradient_entries)} entries (expected <=1), "
                f"Adam group: {len(adam_entries)} entries (expected <=1)"
            )
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 5: KG database has metadata entries
    # =========================================================
    check_name = "kg_metadata_populated"
    try:
        conn = sqlite3.connect(str(kg_db))
        meta_count = conn.execute("SELECT COUNT(*) FROM memories_meta").fetchone()[0]
        triple_count = conn.execute("SELECT COUNT(*) FROM triples").fetchone()[0]
        conn.close()
        passed = meta_count >= 4 and triple_count >= 1
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"KG has {meta_count} memory records and {triple_count} triples"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 6: search_results.json exists and has correct structure
    # =========================================================
    check_name = "search_results_json_exists"
    result_files = list(Path(workspace_dir).rglob("search_results.json"))
    # Also check home dir and skill dir
    extra_locations = [
        Path.home() / ".openclaw" / "workspace" / "search_results.json",
        skill_dir / "search_results.json",
        Path.home() / "search_results.json",
    ]
    for loc in extra_locations:
        if loc.exists():
            result_files.append(loc)
    
    result_files = list(set(result_files))
    
    try:
        if not result_files:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "search_results.json not found anywhere"
            })
        else:
            fpath = result_files[0]
            data = json.loads(fpath.read_text(encoding="utf-8"))
            has_query = "query" in data
            has_results = "results" in data and isinstance(data["results"], list)
            has_count = "count" in data
            passed = has_query and has_results and has_count
            checks.append({
                "name": check_name,
                "passed": passed,
                "detail": f"Found at {fpath}; keys present: query={has_query}, results={has_results}, count={has_count}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 7: search_results.json contains relevant ML optimization content
    # =========================================================
    check_name = "search_results_content_relevant"
    try:
        if not result_files:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "No search_results.json to check"
            })
        else:
            data = json.loads(result_files[0].read_text(encoding="utf-8"))
            results_list = data.get("results", [])
            
            # Should have results, and they should contain ML optimization content
            has_results = len(results_list) >= 1
            
            # Check that at least one result has ML-related content
            ml_keywords = ["梯度", "优化", "Adam", "学习率", "归一化", "Dropout", "初始化"]
            content_is_relevant = False
            for r in results_list:
                content_str = str(r)
                if any(kw in content_str for kw in ml_keywords):
                    content_is_relevant = True
                    break
            
            passed = has_results and content_is_relevant
            checks.append({
                "name": check_name,
                "passed": passed,
                "detail": f"Results count: {len(results_list)}, ML content present: {content_is_relevant}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 8: search used --limit and --llm-answer flags correctly
    # (Verified by checking count field in search_results.json is <= limit used)
    # Also check that llm_answer field is present and true in results
    # =========================================================
    check_name = "search_used_correct_flags"
    try:
        if not result_files:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "No search_results.json to check"
            })
        else:
            data = json.loads(result_files[0].read_text(encoding="utf-8"))
            count = data.get("count", -1)
            results = data.get("results", [])
            llm_answer = data.get("llm_answer", None)
            
            # count should match len(results)
            count_matches = (count == len(results))
            # llm_answer should be true (agent should have used --llm-answer flag)
            llm_answer_used = llm_answer is True
            # results should be within limit (<=3 based on task prompt)
            within_limit = count <= 3
            
            passed = count_matches and llm_answer_used and within_limit
            checks.append({
                "name": check_name,
                "passed": passed,
                "detail": (
                    f"count_matches_results={count_matches} ({count} vs {len(results)}), "
                    f"llm_answer={llm_answer_used} ({llm_answer}), "
                    f"within_limit_3={within_limit} (count={count})"
                )
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # SCORE CALCULATION
    # =========================================================
    # Weights: checks 1,2,3 are basic (0.5 each), check 4 (dedup) is critical (2.0),
    # checks 5,6,7 (1.0 each), check 8 is advanced (1.5)
    weights = [0.5, 0.5, 0.5, 2.0, 1.0, 1.0, 1.0, 1.5]
    total_weight = sum(weights)
    earned = sum(w for c, w in zip(checks, weights) if c["passed"])
    score = round(earned / total_weight, 3)
    passed_overall = score >= 0.7

    output = {
        "passed": passed_overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/root/.openclaw/workspace"
    evaluate(ws)