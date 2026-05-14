import sys
import json
import subprocess
import sqlite3
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0
total_weight = 0.0


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score, total_weight
    total_weight += weight
    if passed:
        score += weight


# ---- Check 1: Journal was initialized (DB exists) ----
db_path = Path.home() / ".openclaw" / "workspace" / "ops-journal" / "journal.db"
try:
    exists = db_path.exists()
    add_check(
        "journal_db_initialized",
        exists,
        f"journal.db {'found' if exists else 'NOT found'} at {db_path}",
        weight=1.0,
    )
except Exception as e:
    add_check("journal_db_initialized", False, f"Exception: {e}", weight=1.0)


# ---- Check 2: At least 5 journal entries exist across multiple categories ----
try:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    entries = conn.execute("SELECT * FROM entries").fetchall()
    cats = set(e["category"] for e in entries)
    count = len(entries)
    multi_cat = len(cats) >= 3
    detail = f"{count} entries found across categories: {cats}"
    add_check(
        "multiple_entries_multiple_categories",
        count >= 5 and multi_cat,
        detail,
        weight=1.5,
    )
except Exception as e:
    add_check("multiple_entries_multiple_categories", False, f"Exception: {e}", weight=1.5)


# ---- Check 3: At least one incident was opened with severity=high or critical ----
try:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    incidents = conn.execute("SELECT * FROM incidents").fetchall()
    severe_inc = [i for i in incidents if i["severity"] in ("high", "critical")]
    has_severe = len(severe_inc) >= 1
    detail = f"{len(incidents)} incidents total, {len(severe_inc)} with high/critical severity"
    add_check(
        "incident_opened_with_high_severity",
        has_severe,
        detail,
        weight=1.5,
    )
except Exception as e:
    add_check("incident_opened_with_high_severity", False, f"Exception: {e}", weight=1.5)


# ---- Check 4: At least one incident is resolved with a resolution string ----
try:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    resolved = conn.execute(
        "SELECT * FROM incidents WHERE status='resolved' AND resolution IS NOT NULL AND resolution != ''"
    ).fetchall()
    has_resolved = len(resolved) >= 1
    detail = f"{len(resolved)} resolved incidents with resolution text found"
    add_check(
        "incident_resolved_with_resolution",
        has_resolved,
        detail,
        weight=1.5,
    )
except Exception as e:
    add_check("incident_resolved_with_resolution", False, f"Exception: {e}", weight=1.5)


# ---- Check 5: An incident markdown file exists in incidents/ dir ----
try:
    inc_dir = Path.home() / ".openclaw" / "workspace" / "ops-journal" / "incidents"
    inc_files = list(inc_dir.glob("INC-*.md")) if inc_dir.exists() else []
    has_inc_file = len(inc_files) >= 1
    detail = f"Incident markdown files: {[f.name for f in inc_files]}"
    add_check(
        "incident_markdown_file_exists",
        has_inc_file,
        detail,
        weight=1.0,
    )
except Exception as e:
    add_check("incident_markdown_file_exists", False, f"Exception: {e}", weight=1.0)


# ---- Check 6: timeline --format json works and contains required fields ----
try:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    first_inc = conn.execute("SELECT id FROM incidents ORDER BY opened_at ASC LIMIT 1").fetchone()
    conn.close()
    if first_inc:
        inc_id = first_inc["id"]
        result = run(f"cd {workspace} && python3 scripts/journal.py timeline {inc_id} --format json")
        try:
            data = json.loads(result.stdout)
            required_keys = {"incident_id", "description", "severity", "status", "opened_at", "timeline"}
            missing = required_keys - set(data.keys())
            has_timeline_entries = isinstance(data.get("timeline"), list) and len(data["timeline"]) >= 1
            passed = len(missing) == 0 and has_timeline_entries
            detail = f"Keys present: {set(data.keys())}. Missing: {missing}. Timeline entries: {len(data.get('timeline', []))}"
        except json.JSONDecodeError as je:
            passed = False
            detail = f"timeline --format json output not valid JSON: {je}. stdout={result.stdout[:300]}"
    else:
        passed = False
        detail = "No incidents in DB to test timeline against."
    add_check("timeline_json_format_correct", passed, detail, weight=2.0)
except Exception as e:
    add_check("timeline_json_format_correct", False, f"Exception: {e}", weight=2.0)


# ---- Check 7: Export to markdown file was created ----
try:
    # Agent should have exported to a file; look for any .md export file in workspace
    export_files = list(Path(workspace).rglob("*.md"))
    # Filter for files that look like exports (contain "Ops Journal Export" header)
    export_candidates = []
    for f in export_files:
        try:
            text = f.read_text()
            if "Ops Journal Export" in text or "ops journal export" in text.lower():
                export_candidates.append(f)
        except Exception:
            pass
    # Also check home dir
    home_exports = list(Path.home().rglob("*.md"))
    for f in home_exports:
        try:
            text = f.read_text()
            if "Ops Journal Export" in text or "ops journal export" in text.lower():
                if f not in export_candidates:
                    export_candidates.append(f)
        except Exception:
            pass

    has_export = len(export_candidates) >= 1
    detail = f"Markdown export files found: {[str(f) for f in export_candidates]}"
    add_check(
        "markdown_export_file_created",
        has_export,
        detail,
        weight=2.0,
    )
    if has_export:
        # Deeper check: file should have multiple entries
        sample = export_candidates[0].read_text()
        has_entries = sample.count("##") >= 3
        add_check(
            "markdown_export_has_multiple_entries",
            has_entries,
            f"Export file has {'enough' if has_entries else 'too few'} section headers (## count={sample.count('##')})",
            weight=1.0,
        )
    else:
        add_check("markdown_export_has_multiple_entries", False, "No export file found to check", weight=1.0)
except Exception as e:
    add_check("markdown_export_file_created", False, f"Exception: {e}", weight=2.0)
    add_check("markdown_export_has_multiple_entries", False, f"Exception: {e}", weight=1.0)


# ---- Check 8: summary --json produces valid JSON with expected structure ----
try:
    result = run(f"cd {workspace} && python3 scripts/journal.py summary --period week --json")
    try:
        data = json.loads(result.stdout)
        required = {"period", "total_entries", "by_category", "by_severity"}
        missing = required - set(data.keys())
        passed = len(missing) == 0 and data.get("total_entries", 0) >= 1
        detail = f"summary JSON keys present: {set(data.keys())}. Missing: {missing}. total_entries={data.get('total_entries')}"
    except json.JSONDecodeError as je:
        passed = False
        detail = f"summary --json output not valid JSON: {je}. stdout={result.stdout[:300]}"
    add_check("summary_json_valid_structure", passed, detail, weight=1.5)
except Exception as e:
    add_check("summary_json_valid_structure", False, f"Exception: {e}", weight=1.5)


# ---- Check 9: Entries include deploy category with correct severity not just default ----
try:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    deploy_entries = conn.execute("SELECT * FROM entries WHERE category='deploy'").fetchall()
    conn.close()
    has_deploy = len(deploy_entries) >= 1
    detail = f"{len(deploy_entries)} deploy entries found"
    add_check("deploy_category_entries_exist", has_deploy, detail, weight=1.0)
except Exception as e:
    add_check("deploy_category_entries_exist", False, f"Exception: {e}", weight=1.0)


# ---- Check 10: search command works and filters correctly ----
try:
    result = run(f"cd {workspace} && python3 scripts/journal.py search --category incident --severity high")
    output = result.stdout + result.stderr
    # Either it found entries or correctly says "No entries found"
    passed = result.returncode == 0
    detail = f"search --category incident --severity high: returncode={result.returncode}, output snippet='{output[:200]}'"
    add_check("search_category_severity_filter_works", passed, detail, weight=1.0)
except Exception as e:
    add_check("search_category_severity_filter_works", False, f"Exception: {e}", weight=1.0)


# ---- Final scoring ----
final_score = round(score / total_weight, 3) if total_weight > 0 else 0.0
passed_overall = final_score >= 0.75 and all(
    c["passed"] for c in checks if c["name"] in [
        "journal_db_initialized",
        "incident_opened_with_high_severity",
        "incident_resolved_with_resolution",
        "timeline_json_format_correct",
        "markdown_export_file_created",
    ]
)

print(json.dumps({
    "passed": passed_overall,
    "score": final_score,
    "checks": checks,
}, indent=2))