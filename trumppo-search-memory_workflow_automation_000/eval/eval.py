#!/usr/bin/env python3
"""
Evaluation script for the legal-research memory indexing task.
Checks:
  1. Index cache exists at memory/cache/index.json and is valid JSON.
  2. Index covers MEMORY.md (root-level file).
  3. Index covers at least 10 memory/**/*.md files (all deeply nested ones).
  4. search_results.txt exists anywhere in the workspace.
  5. search_results.txt has exactly 3 ranked results (--top 3).
  6. Results use the proprietary score format: "N. [X.XX] path".
  7. The most-recently-dated patent-related file surfaces in the top result
     (recency boost must have fired: research/ip/patent_strategy_notes.md is 20 days old
      with strong "patent" keyword frequency → should be #1 for a "patent" query).
  8. Distractor files (archive/, .txt, .csv) are NOT in the index.
"""

import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
passed_all = True

def add_check(name, passed, detail):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# ── Check 1: Cache index exists and is valid JSON ───────────────────────────
cache_path = workspace / "memory" / "cache" / "index.json"
cache = None
try:
    with open(cache_path) as f:
        cache = json.load(f)
    add_check(
        "cache_index_exists_and_valid",
        True,
        f"Found valid JSON cache at {cache_path} with {len(cache)} entries."
    )
except FileNotFoundError:
    add_check("cache_index_exists_and_valid", False,
              f"Cache file not found at {cache_path}. Did agent run the indexer?")
except json.JSONDecodeError as e:
    add_check("cache_index_exists_and_valid", False,
              f"Cache file exists but is not valid JSON: {e}")

# ── Check 2: Root MEMORY.md is indexed ──────────────────────────────────────
if cache is not None:
    root_mem_indexed = any("MEMORY.md" in k and "/" not in k.replace("MEMORY.md", "") 
                           for k in cache.keys())
    # More precisely: key should be exactly "MEMORY.md"
    root_mem_indexed = "MEMORY.md" in cache
    add_check(
        "root_MEMORY_md_indexed",
        root_mem_indexed,
        "MEMORY.md (root-level) found in cache." if root_mem_indexed
        else f"MEMORY.md NOT found in cache keys: {list(cache.keys())[:5]}"
    )
else:
    add_check("root_MEMORY_md_indexed", False, "Cache not loaded, skipping.")

# ── Check 3: At least 10 memory/**/*.md files indexed ───────────────────────
if cache is not None:
    nested_keys = [k for k in cache.keys() if k.startswith("memory/") and k.endswith(".md")
                   and "cache" not in k]
    enough = len(nested_keys) >= 10
    add_check(
        "nested_memory_files_indexed",
        enough,
        f"Found {len(nested_keys)} memory/**/*.md entries in cache (need ≥10): {nested_keys}"
    )
else:
    add_check("nested_memory_files_indexed", False, "Cache not loaded, skipping.")

# ── Check 4: search_results.txt exists ──────────────────────────────────────
results_files = list(workspace.rglob("search_results.txt"))
found_results = len(results_files) > 0
results_path = results_files[0] if found_results else None
add_check(
    "search_results_file_exists",
    found_results,
    f"Found search_results.txt at {results_path}" if found_results
    else "search_results.txt not found anywhere in workspace."
)

# ── Check 5: Exactly 3 results (--top 3) ────────────────────────────────────
results_content = ""
if results_path:
    try:
        results_content = results_path.read_text(errors="replace").strip()
        lines = [l.strip() for l in results_content.splitlines() if l.strip()]
        # Count lines that match the result pattern
        result_lines = [l for l in lines if re.match(r"^\d+\.\s+\[[\d.]+\]", l)]
        exactly_three = len(result_lines) == 3
        add_check(
            "exactly_three_results",
            exactly_three,
            f"Found {len(result_lines)} ranked result lines (need exactly 3): {result_lines}"
        )
    except Exception as e:
        add_check("exactly_three_results", False, f"Error reading search_results.txt: {e}")
else:
    add_check("exactly_three_results", False, "search_results.txt not found, skipping.")

# ── Check 6: Results use proprietary format "N. [X.XX] path" ───────────────
if results_content:
    lines = [l.strip() for l in results_content.splitlines() if l.strip()]
    result_lines = [l for l in lines if re.match(r"^\d+\.\s+\[[\d.]+\]", l)]
    if result_lines:
        all_valid_format = all(
            re.match(r"^\d+\.\s+\[[\d.]+\]\s+\S+", l) for l in result_lines
        )
        add_check(
            "result_format_correct",
            all_valid_format,
            f"All result lines match 'N. [score] path' format." if all_valid_format
            else f"Some lines don't match format: {result_lines}"
        )
    else:
        add_check("result_format_correct", False,
                  "No valid result lines found to check format.")
else:
    add_check("result_format_correct", False, "No results content to check.")

# ── Check 7: Recency boost fires – patent_strategy_notes.md or globex_pharma.md
#    appears in top results for a patent-related query ────────────────────────
if results_content:
    lines = [l.strip() for l in results_content.splitlines() if l.strip()]
    result_lines = [l for l in lines if re.match(r"^\d+\.\s+\[[\d.]+\]", l)]
    # The recent files with patent keywords that should surface in top 3:
    recent_patent_files = [
        "research/ip/patent_strategy_notes.md",
        "clients/globex_pharma.md",
        "admin/court_deadlines_2024.md",
    ]
    found_recent = any(
        any(rp in line for rp in recent_patent_files)
        for line in result_lines
    )
    # Also check that old (age>90d) files are NOT exclusively dominating
    old_files = [
        "cases/patent/biolab_v_genex.md",   # 350 days old
        "research/contracts/force_majeure_analysis.md",  # 400 days old
        "cases/employment/doe_v_bankgroup.md",  # 500 days old
    ]
    top1 = result_lines[0] if result_lines else ""
    top1_is_old_only = all(old_f in top1 for old_f in old_files)  # won't fire meaningfully
    # The real check: at least one recent-boosted patent file is in top results
    add_check(
        "recency_boost_applied",
        found_recent,
        f"Recent patent-relevant file found in top results: {result_lines}" if found_recent
        else f"No recent patent files found in results. Got: {result_lines}. "
             f"Expected one of: {recent_patent_files}"
    )
else:
    add_check("recency_boost_applied", False, "No results content to check.")

# ── Check 8: Distractor files NOT in index ──────────────────────────────────
if cache is not None:
    distractor_patterns = ["archive/", ".txt", ".csv", "notes.txt", "clients_export"]
    leaked_distractors = [
        k for k in cache.keys()
        if any(pat in k for pat in distractor_patterns)
    ]
    no_distractors = len(leaked_distractors) == 0
    add_check(
        "distractors_excluded_from_index",
        no_distractors,
        "No distractor files in index." if no_distractors
        else f"Distractor files found in index (should not be there): {leaked_distractors}"
    )
else:
    add_check("distractors_excluded_from_index", False, "Cache not loaded, skipping.")

# ── Final score ──────────────────────────────────────────────────────────────
score = sum(1 for c in checks if c["passed"]) / len(checks)

result = {
    "passed": passed_all,
    "score": round(score, 3),
    "checks": checks
}
print(json.dumps(result, indent=2))