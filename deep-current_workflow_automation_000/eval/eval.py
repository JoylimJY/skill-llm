import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

workspace = Path(sys.argv[1])

checks = []
score_parts = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

def run_cli(*args):
    result = subprocess.run(
        ["python3", str(workspace / "scripts" / "deep-current.py")] + list(args),
        capture_output=True, text=True, cwd=str(workspace)
    )
    return result.stdout + result.stderr

# ── Load currents.json ────────────────────────────────────────────────────
try:
    currents_path = workspace / "deep-current" / "currents.json"
    currents_raw = currents_path.read_text()
    currents = json.loads(currents_raw)
    threads = currents.get("threads", [])
    check("currents_json_readable", True, "currents.json is valid JSON")
except Exception as e:
    check("currents_json_readable", False, f"Could not read currents.json: {e}")
    threads = []

# Helper: find thread by id prefix
def find_thread(partial_id):
    for t in threads:
        if t.get("id", "").startswith(partial_id):
            return t
    return None

# ── CHECK 1: PROTAC thread was pruned by decay ────────────────────────────
# protac-degrader-landscape: created 95 days ago, no notes => should be removed
protac = find_thread("protac-degrader-landscape")
c1 = check(
    "stale_protac_thread_decayed",
    protac is None,
    f"protac-degrader-landscape (>90d inactive, no notes) {'correctly removed' if protac is None else 'still present — decay not applied'}"
)

# ── CHECK 2: kras-g12d-inhibitors thread still exists (has notes, active) ─
kras = find_thread("kras-g12d-inhibitors")
c2 = check(
    "kras_thread_preserved",
    kras is not None,
    f"kras-g12d-inhibitors {'present' if kras else 'missing'} — should survive decay (has notes)"
)

# ── CHECK 3: New thread "Antibody-Drug Conjugate Safety Signals" added ────
# The task asks agent to add a new PROTAC-replacement thread on a new topic
# We look for any new thread the agent created (not in the original 5)
original_ids = {
    "protac-degrader-landscape",
    "kras-g12d-inhibitors",
    "adc-manufacturing-bottlenecks",
    "ai-drug-discovery-partnerships",
    "donanemab-alzheimers-launch"
}
new_threads = [t for t in threads if t.get("id") not in original_ids]
c3 = check(
    "new_thread_created",
    len(new_threads) >= 1,
    f"New thread(s) found: {[t.get('id') for t in new_threads]}" if new_threads else "No new thread detected"
)

# ── CHECK 4: New thread has at least one note, one source, one finding ────
if new_threads:
    nt = new_threads[0]
    has_note    = len(nt.get("notes", [])) >= 1
    has_source  = len(nt.get("sources", [])) >= 1
    has_finding = len(nt.get("findings", [])) >= 1
    c4 = check(
        "new_thread_populated",
        has_note and has_source and has_finding,
        f"New thread '{nt.get('id')}': notes={len(nt.get('notes',[]))}, "
        f"sources={len(nt.get('sources',[]))}, findings={len(nt.get('findings',[]))}"
    )
else:
    c4 = check("new_thread_populated", False, "No new thread to inspect")

# ── CHECK 5: adc-manufacturing-bottlenecks marked as resolved ─────────────
adc = find_thread("adc-manufacturing-bottlenecks")
if adc:
    c5 = check(
        "adc_thread_resolved",
        adc.get("status") == "resolved",
        f"adc-manufacturing-bottlenecks status = '{adc.get('status')}' (expected 'resolved')"
    )
else:
    c5 = check("adc_thread_resolved", False, "adc-manufacturing-bottlenecks thread missing")

# ── CHECK 6: Today's report file exists with correct filename format ───────
today_str = datetime.utcnow().strftime("%Y-%m-%d")
report_dir = workspace / "deep-current-reports"
report_file = report_dir / f"{today_str}.md"
c6 = check(
    "todays_report_file_exists",
    report_file.exists(),
    f"Expected report at deep-current-reports/{today_str}.md — {'FOUND' if report_file.exists() else 'NOT FOUND'}"
)

# ── CHECK 7: Report has date header and at least 2 sections ──────────────
if report_file.exists():
    try:
        report_content = report_file.read_text()
        has_header = bool(re.search(r"#\s*Deep Current", report_content, re.IGNORECASE))
        section_count = len(re.findall(r"^##\s+.+", report_content, re.MULTILINE))
        has_links = bool(re.search(r"\[.+?\]\(https?://.+?\)", report_content))
        c7 = check(
            "report_format_correct",
            has_header and section_count >= 2 and has_links,
            f"header={has_header}, sections={section_count}, has_inline_links={has_links}"
        )
    except Exception as e:
        c7 = check("report_format_correct", False, f"Error reading report: {e}")
else:
    c7 = check("report_format_correct", False, "Report file not found, skipping content check")

# ── CHECK 8: covered command lists URLs from existing reports ─────────────
try:
    covered_output = run_cli("covered", "14")
    # The recent report has specific known URLs — check at least one appears
    known_url_fragments = ["lilly", "statnews", "reuters", "isomorphic", "biospace", "nejm", "fiercepharma"]
    found_any = any(frag in covered_output.lower() for frag in known_url_fragments)
    c8 = check(
        "covered_command_works",
        found_any and len(covered_output.strip()) > 20,
        f"'covered' output length={len(covered_output)}, known URL found={found_any}"
    )
except Exception as e:
    c8 = check("covered_command_works", False, f"Error running covered: {e}")

# ── CHECK 9: ai-drug-discovery-partnerships remains paused (not wrongly touched)
ai_thread = find_thread("ai-drug-discovery-partnerships")
if ai_thread:
    c9 = check(
        "paused_thread_untouched",
        ai_thread.get("status") == "paused",
        f"ai-drug-discovery-partnerships status = '{ai_thread.get('status')}' (should remain 'paused')"
    )
else:
    # if it was decayed - check if it qualifies: 80 days, no notes => borderline
    # 80 days < 90 threshold => should NOT be decayed
    c9 = check(
        "paused_thread_untouched",
        False,
        "ai-drug-discovery-partnerships is missing — it was 80 days old (< 90d threshold) and should NOT be decayed"
    )

# ── CHECK 10: donanemab thread has at least one finding recorded ──────────
dona = find_thread("donanemab-alzheimers-launch")
if dona:
    dona_findings = len(dona.get("findings", []))
    c10 = check(
        "donanemab_finding_recorded",
        dona_findings >= 1,
        f"donanemab-alzheimers-launch findings count = {dona_findings}"
    )
else:
    c10 = check("donanemab_finding_recorded", False, "donanemab-alzheimers-launch thread missing")

# ── Scoring ───────────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
total = len(checks)
passed = len(passed_checks)
score = round(passed / total, 3)

all_passed = passed == total

print(json.dumps({
    "passed": all_passed,
    "score": score,
    "checks": checks
}, indent=2))