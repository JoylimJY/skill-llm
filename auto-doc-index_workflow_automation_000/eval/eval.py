#!/usr/bin/env python3
"""
Evaluation script for the RFC doc-index task.

Checks:
1. doc/rfc/README.md exists and has INDEX:START / INDEX:END markers
2. The README.md index table between markers contains all 3 RFC entries
3. Each RFC entry has the correct title (verbatim from file H1)
4. Each RFC entry has the correct status (verbatim from file, no normalization)
5. Each RFC entry has the correct date
6. Each RFC entry has the correct proposer
7. Entries are sorted numerically (001, 002, 003)
8. The generator script handles 'rfc' mode (or 'all' covers rfc)
9. Content outside markers is preserved (intro text untouched)
10. Column structure is correct (5 columns: RFC/ID, Title, Status, Date, Proposer)
"""

import sys
import re
import json
import subprocess
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
passed_all = True


def check(name: str, passed: bool, detail: str):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def read_file(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None


# ---------------------------------------------------------------------------
# 1. doc/rfc/README.md exists
# ---------------------------------------------------------------------------

rfc_readme_path = os.path.join(workspace, "doc", "rfc", "README.md")
rfc_readme = read_file(rfc_readme_path)

check(
    "rfc_readme_exists",
    rfc_readme is not None,
    f"doc/rfc/README.md {'found' if rfc_readme is not None else 'NOT FOUND'}",
)

# ---------------------------------------------------------------------------
# 2. Markers present in README.md
# ---------------------------------------------------------------------------

START_MARKER = "<!-- INDEX:START -->"
END_MARKER = "<!-- INDEX:END -->"

has_markers = (
    rfc_readme is not None
    and START_MARKER in rfc_readme
    and END_MARKER in rfc_readme
)
check(
    "markers_present",
    has_markers,
    f"INDEX:START and INDEX:END markers {'found' if has_markers else 'NOT FOUND'} in doc/rfc/README.md",
)

# ---------------------------------------------------------------------------
# 3. Extract content between markers
# ---------------------------------------------------------------------------

index_content = ""
if has_markers:
    try:
        start_idx = rfc_readme.index(START_MARKER) + len(START_MARKER)
        end_idx = rfc_readme.index(END_MARKER)
        index_content = rfc_readme[start_idx:end_idx]
    except Exception as e:
        check("extract_index_content", False, f"Error extracting index content: {e}")
        index_content = ""

check(
    "index_content_nonempty",
    bool(index_content.strip()),
    f"Index content between markers is {'non-empty' if index_content.strip() else 'EMPTY — generator may not have been run'}",
)

# ---------------------------------------------------------------------------
# 4. Table header has correct columns (5 columns including Proposer)
# ---------------------------------------------------------------------------

# Expected columns: some variant of RFC/ID, Title, Status, Date, Proposer
header_line = ""
for line in index_content.splitlines():
    line = line.strip()
    if line.startswith("|") and "Title" in line:
        header_line = line
        break

columns = [c.strip() for c in header_line.split("|") if c.strip()] if header_line else []
has_five_cols = len(columns) == 5
has_proposer = any("proposer" in c.lower() for c in columns)
has_status = any("status" in c.lower() for c in columns)
has_date = any("date" in c.lower() for c in columns)
has_title = any("title" in c.lower() for c in columns)

check(
    "table_has_five_columns",
    has_five_cols,
    f"Table header has {len(columns)} columns (expected 5). Header: '{header_line}'",
)
check(
    "table_has_proposer_column",
    has_proposer,
    f"Table header {'has' if has_proposer else 'MISSING'} Proposer column. Columns: {columns}",
)
check(
    "table_has_required_columns",
    has_status and has_date and has_title,
    f"Status={has_status}, Date={has_date}, Title={has_title} in header: {columns}",
)

# ---------------------------------------------------------------------------
# 5. All 3 RFCs appear in the index
# ---------------------------------------------------------------------------

# Expected values (verbatim from the source files)
expected_rfcs = [
    {
        "id_hint": "001",
        "title": "Standardise webhook payload envelope for all outbound events",
        "status": "accepted",   # verbatim — must NOT be normalized to "Accepted"
        "date": "2026-03-01",
        "proposer": "alice@fincore.io",
    },
    {
        "id_hint": "002",
        "title": "Deprecate v1 settlement API by end of Q3 2026",
        "status": "under review",  # verbatim — multi-word
        "date": "2026-03-15",
        "proposer": "bob@fincore.io",
    },
    {
        "id_hint": "003",
        "title": "Introduce rate limiting on public-facing ledger query endpoints",
        "status": "draft",  # verbatim
        "date": "2026-04-02",
        "proposer": "carol@fincore.io",
    },
]

# Parse data rows from index content
data_rows = []
for line in index_content.splitlines():
    line = line.strip()
    if line.startswith("|") and not re.match(r'^\|\s*[-:]+', line):
        cols = [c.strip() for c in line.split("|") if c.strip()]
        if cols and len(cols) >= 3 and "Title" not in line and "---" not in line:
            data_rows.append(cols)

check(
    "three_rfc_rows_present",
    len(data_rows) == 3,
    f"Expected 3 data rows in index, found {len(data_rows)}. Rows: {data_rows}",
)

# ---------------------------------------------------------------------------
# 6. Verbatim title check (no truncation)
# ---------------------------------------------------------------------------

index_text = index_content

for rfc in expected_rfcs:
    title_found = rfc["title"] in index_text
    check(
        f"title_verbatim_{rfc['id_hint']}",
        title_found,
        f"RFC-{rfc['id_hint']} title {'found verbatim' if title_found else 'NOT FOUND or TRUNCATED'} in index. Expected: \"{rfc['title']}\"",
    )

# ---------------------------------------------------------------------------
# 7. Verbatim status check (no case normalization)
# ---------------------------------------------------------------------------

for rfc in expected_rfcs:
    status_found = rfc["status"] in index_text
    check(
        f"status_verbatim_{rfc['id_hint']}",
        status_found,
        f"RFC-{rfc['id_hint']} status {'found verbatim' if status_found else 'NOT FOUND or NORMALIZED'} in index. Expected: \"{rfc['status']}\"",
    )

# ---------------------------------------------------------------------------
# 8. Date check
# ---------------------------------------------------------------------------

for rfc in expected_rfcs:
    date_found = rfc["date"] in index_text
    check(
        f"date_present_{rfc['id_hint']}",
        date_found,
        f"RFC-{rfc['id_hint']} date {'found' if date_found else 'NOT FOUND'} in index. Expected: \"{rfc['date']}\"",
    )

# ---------------------------------------------------------------------------
# 9. Proposer check
# ---------------------------------------------------------------------------

for rfc in expected_rfcs:
    proposer_found = rfc["proposer"] in index_text
    check(
        f"proposer_present_{rfc['id_hint']}",
        proposer_found,
        f"RFC-{rfc['id_hint']} proposer {'found' if proposer_found else 'NOT FOUND'} in index. Expected: \"{rfc['proposer']}\"",
    )

# ---------------------------------------------------------------------------
# 10. Entries sorted by RFC number (001, 002, 003 in order)
# ---------------------------------------------------------------------------

if len(data_rows) == 3:
    # Each row's first cell should contain the RFC number in order
    row_texts = [" ".join(row) for row in data_rows]
    order_001_before_002 = any("001" in r for r in row_texts) and any("002" in r for r in row_texts)
    idx_001 = next((i for i, r in enumerate(row_texts) if "001" in r), -1)
    idx_002 = next((i for i, r in enumerate(row_texts) if "002" in r), -1)
    idx_003 = next((i for i, r in enumerate(row_texts) if "003" in r), -1)
    sorted_correctly = idx_001 < idx_002 < idx_003 if all(x >= 0 for x in [idx_001, idx_002, idx_003]) else False
    check(
        "entries_sorted_by_id",
        sorted_correctly,
        f"Entries order: 001@{idx_001}, 002@{idx_002}, 003@{idx_003}. Sorted={'yes' if sorted_correctly else 'NO'}",
    )
else:
    check("entries_sorted_by_id", False, "Cannot check sort order — wrong number of rows")

# ---------------------------------------------------------------------------
# 11. Content outside markers is preserved (README has intro text)
# ---------------------------------------------------------------------------

if rfc_readme is not None:
    before_markers = rfc_readme[:rfc_readme.index(START_MARKER)] if START_MARKER in rfc_readme else rfc_readme
    has_intro = len(before_markers.strip()) > 20  # some meaningful content before markers
    check(
        "content_outside_markers_preserved",
        has_intro,
        f"Content before INDEX:START marker: {len(before_markers.strip())} chars. {'OK' if has_intro else 'README appears to be ONLY the index table — intro text missing'}",
    )
else:
    check("content_outside_markers_preserved", False, "README not found")

# ---------------------------------------------------------------------------
# 12. Generator script handles 'rfc' mode
# ---------------------------------------------------------------------------

gen_script_path = os.path.join(workspace, "scripts", "generate-doc-index.ts")
gen_script = read_file(gen_script_path)

if gen_script is not None:
    has_rfc_mode = "rfc" in gen_script and ("processRfc" in gen_script or "process_rfc" in gen_script or "rfc" in gen_script.lower())
    # More specifically: does it have a function that processes RFC and is it wired into main?
    has_process_rfc_fn = bool(re.search(r'function\s+processRfc\b', gen_script) or 
                               re.search(r'processRfc\s*\(\)', gen_script))
    check(
        "generator_has_rfc_support",
        has_process_rfc_fn,
        f"Generator script {'has' if has_process_rfc_fn else 'MISSING'} processRfc function",
    )
    # Check it's wired into the mode dispatcher
    rfc_dispatched = bool(re.search(r"mode\s*===?\s*['\"]rfc['\"]", gen_script) or
                          re.search(r"['\"]rfc['\"].*processRfc", gen_script) or
                          re.search(r"processRfc.*['\"]rfc['\"]", gen_script))
    check(
        "generator_rfc_mode_dispatched",
        rfc_dispatched,
        f"Generator script RFC mode {'is dispatched in main()' if rfc_dispatched else 'NOT wired into mode dispatcher'}",
    )
    # Check it also responds to 'all' mode
    all_includes_rfc = bool(re.search(r"mode\s*===?\s*['\"]all['\"].*processRfc|processRfc.*mode\s*===?\s*['\"]all['\"]", gen_script, re.DOTALL) or
                            (re.search(r"['\"]all['\"]", gen_script) and "processRfc" in gen_script))
    check(
        "generator_all_mode_includes_rfc",
        all_includes_rfc,
        f"Generator 'all' mode {'includes RFC processing' if all_includes_rfc else 'does NOT process RFCs'}",
    )
else:
    check("generator_has_rfc_support", False, "Generator script not found")
    check("generator_rfc_mode_dispatched", False, "Generator script not found")
    check("generator_all_mode_includes_rfc", False, "Generator script not found")

# ---------------------------------------------------------------------------
# 13. Idempotency — running the generator again should not double-append rows
# ---------------------------------------------------------------------------

# Try running the generator to verify it works (and to test idempotency)
try:
    result = subprocess.run(
        ["npx", "tsx", "scripts/generate-doc-index.ts", "rfc"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30,
    )
    generator_ran = result.returncode == 0
    check(
        "generator_runs_without_error",
        generator_ran,
        f"Generator exit code: {result.returncode}. stdout: {result.stdout[:200]}. stderr: {result.stderr[:200]}",
    )
    if generator_ran:
        # Re-read and check still 3 rows (idempotency)
        rfc_readme_after = read_file(rfc_readme_path) or ""
        if START_MARKER in rfc_readme_after and END_MARKER in rfc_readme_after:
            start_idx2 = rfc_readme_after.index(START_MARKER) + len(START_MARKER)
            end_idx2 = rfc_readme_after.index(END_MARKER)
            index_content2 = rfc_readme_after[start_idx2:end_idx2]
            data_rows2 = []
            for line in index_content2.splitlines():
                line2 = line.strip()
                if line2.startswith("|") and not re.match(r'^\|\s*[-:]+', line2):
                    cols2 = [c.strip() for c in line2.split("|") if c.strip()]
                    if cols2 and len(cols2) >= 3 and "Title" not in line2 and "---" not in line2:
                        data_rows2.append(cols2)
            check(
                "idempotent_still_three_rows",
                len(data_rows2) == 3,
                f"After re-run, index has {len(data_rows2)} data rows (expected 3 — idempotency test)",
            )
        else:
            check("idempotent_still_three_rows", False, "Markers missing after re-run")
except subprocess.TimeoutExpired:
    check("generator_runs_without_error", False, "Generator script timed out")
    check("idempotent_still_three_rows", False, "Generator timed out")
except Exception as e:
    check("generator_runs_without_error", False, f"Exception running generator: {e}")
    check("idempotent_still_three_rows", False, f"Generator failed: {e}")

# ---------------------------------------------------------------------------
# Score
# ---------------------------------------------------------------------------

total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
final_passed = all(c["passed"] for c in checks)

output = {
    "passed": final_passed,
    "score": score,
    "checks": checks,
}

print(json.dumps(output, indent=2))