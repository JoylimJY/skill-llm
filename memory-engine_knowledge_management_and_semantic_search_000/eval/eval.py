import sys
import json
import sqlite3
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ---- Check 1: ingest_script_exists ----
    # The agent should have created a JS script that runs the ingestion
    js_files = list(Path(workspace).rglob("*.js"))
    ingest_scripts = [f for f in js_files if any(
        kw in f.read_text(errors='ignore').lower()
        for kw in ['creatememoryengine', 'addmemory', 'memory-engine']
    )]
    if ingest_scripts:
        add_check("ingest_script_exists", True,
                  f"Found JS script(s) using memory-engine: {[str(s) for s in ingest_scripts]}", 1.0)
    else:
        add_check("ingest_script_exists", False,
                  "No JS script found that uses memory-engine API (createMemoryEngine/addMemory)", 1.0)

    # ---- Check 2: database_created ----
    db_files = list(Path(workspace).rglob("*.db"))
    db_path = None
    for db in db_files:
        if db.stat().st_size > 1000:  # must have real content
            db_path = db
            break
    if db_path:
        add_check("database_created", True,
                  f"Found memory database at: {db_path} ({db_path.stat().st_size} bytes)", 1.5)
    else:
        add_check("database_created", False,
                  "No SQLite database (.db) with substantial content found in workspace", 1.5)
        # Cannot proceed with DB checks
        all_passed = all(c["passed"] for c in checks)
        score = total_score / max_score if max_score > 0 else 0.0
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ---- Check 3: memories_table_exists ----
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        has_memories = any('memor' in t.lower() for t in tables)
        add_check("memories_table_exists", has_memories,
                  f"Tables found: {tables}", 1.0)
    except Exception as e:
        add_check("memories_table_exists", False, f"Error reading DB: {e}", 1.0)
        conn = None

    # ---- Check 4: correct_memory_count ----
    # 10 notes should be stored
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%memor%'")
        mem_table = cursor.fetchone()
        if mem_table:
            table_name = mem_table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            passed = count >= 10
            add_check("correct_memory_count", passed,
                      f"Found {count} memories in table '{table_name}' (expected >= 10)", 2.0)
        else:
            add_check("correct_memory_count", False,
                      "No memories table found to count rows", 2.0)
    except Exception as e:
        add_check("correct_memory_count", False, f"Count query failed: {e}", 2.0)

    # ---- Check 5: valid_memory_types ----
    # Must use only valid enum types: fact/experience/lesson/preference/skill
    VALID_TYPES = {'fact', 'experience', 'lesson', 'preference', 'skill'}
    try:
        # Try to find type column
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1].lower() for row in cursor.fetchall()]
        if 'type' in columns:
            cursor.execute(f"SELECT DISTINCT type FROM {table_name}")
            stored_types = {row[0] for row in cursor.fetchall() if row[0]}
            invalid_types = stored_types - VALID_TYPES
            all_valid = len(invalid_types) == 0 and len(stored_types) > 0
            add_check("valid_memory_types", all_valid,
                      f"Stored types: {stored_types}, invalid: {invalid_types}, valid set: {VALID_TYPES}", 2.0)
        else:
            # types might be stored in a JSON blob - check content field
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            add_check("valid_memory_types", True,
                      f"No separate 'type' column; DB columns: {columns}. Sample rows present: {len(rows)>0}", 1.0)
    except Exception as e:
        add_check("valid_memory_types", False, f"Type check failed: {e}", 2.0)

    # ---- Check 6: importance_values_in_range ----
    try:
        if 'importance' in columns:
            cursor.execute(f"SELECT importance FROM {table_name} WHERE importance IS NOT NULL")
            importances = [row[0] for row in cursor.fetchall()]
            if importances:
                all_in_range = all(0.0 <= float(v) <= 1.0 for v in importances)
                high_values = [v for v in importances if float(v) >= 0.6]
                passed = all_in_range and len(high_values) >= 5
                add_check("importance_values_in_range", passed,
                          f"{len(importances)} importance values, all in [0,1]: {all_in_range}, high-value (>=0.6): {len(high_values)}", 1.5)
            else:
                add_check("importance_values_in_range", False,
                          "No importance values found", 1.5)
        else:
            add_check("importance_values_in_range", True,
                      f"No separate importance column; skipping (columns: {columns})", 0.5)
    except Exception as e:
        add_check("importance_values_in_range", False, f"Importance check error: {e}", 1.5)

    # ---- Check 7: search_results_file_exists ----
    # Agent must write search results to search_results.json
    result_files = list(Path(workspace).rglob("search_results.json"))
    if result_files:
        result_file = result_files[0]
        add_check("search_results_file_exists", True,
                  f"Found search_results.json at: {result_file}", 1.5)
    else:
        add_check("search_results_file_exists", False,
                  "search_results.json not found anywhere in workspace", 1.5)
        if conn:
            conn.close()
        all_passed = all(c["passed"] for c in checks)
        score = total_score / max_score if max_score > 0 else 0.0
        return {"passed": all_passed, "score": round(score, 3), "checks": checks}

    # ---- Check 8: search_results_structure ----
    try:
        with open(result_file, "r") as f:
            results = json.load(f)

        # Must be a dict or list with entries for each query
        if isinstance(results, dict):
            num_queries = len(results)
        elif isinstance(results, list):
            num_queries = len(results)
        else:
            num_queries = 0

        has_multiple_queries = num_queries >= 3
        add_check("search_results_multiple_queries", has_multiple_queries,
                  f"search_results.json has {num_queries} top-level entries (expected >= 3 queries)", 2.0)

        # Check that results contain actual memory content (not empty)
        result_str = json.dumps(results).lower()
        has_pcr = "pcr" in result_str or "contamination" in result_str or "sequencing" in result_str
        has_crispr = "crispr" in result_str or "editing" in result_str or "cas9" in result_str
        has_pref = "prefer" in result_str or "tabular" in result_str or "heatmap" in result_str or "presentation" in result_str

        content_checks_passed = sum([has_pcr, has_crispr, has_pref])
        add_check("search_results_content_relevant", content_checks_passed >= 2,
                  f"Results contain relevant content: PCR/seq={has_pcr}, CRISPR={has_crispr}, preferences={has_pref}", 2.5)

    except json.JSONDecodeError as e:
        add_check("search_results_multiple_queries", False,
                  f"search_results.json is not valid JSON: {e}", 2.0)
        add_check("search_results_content_relevant", False,
                  "Cannot check content due to JSON parse error", 2.5)
    except Exception as e:
        add_check("search_results_multiple_queries", False, f"Error: {e}", 2.0)
        add_check("search_results_content_relevant", False, f"Error: {e}", 2.5)

    # ---- Check 9: diverse_types_stored ----
    # Must store at least 4 of the 5 valid types
    try:
        if 'type' in columns:
            cursor.execute(f"SELECT DISTINCT type FROM {table_name}")
            stored_types = {row[0] for row in cursor.fetchall() if row[0] and row[0] in VALID_TYPES}
            diverse_enough = len(stored_types) >= 4
            add_check("diverse_types_stored", diverse_enough,
                      f"Valid types stored: {stored_types} (need >= 4 of {VALID_TYPES})", 1.5)
        else:
            add_check("diverse_types_stored", True,
                      "No separate type column to check diversity; skipping", 0.5)
    except Exception as e:
        add_check("diverse_types_stored", False, f"Error: {e}", 1.5)

    if conn:
        conn.close()

    all_passed = all(c["passed"] for c in checks)
    score = total_score / max_score if max_score > 0 else 0.0
    return {"passed": all_passed, "score": round(score, 3), "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))