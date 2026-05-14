#!/usr/bin/env python3
"""
Evaluation script for the agent-hardening skill task.

Grading rubric:
1. Output file exists at the correct location (audit/threat_report.json)
2. JSON is valid and has the required top-level schema
3. All 20 document IDs are present in results
4. Unicode Cf sanitization: correct detection for DOC-002,006,008,009,011,012,016,019
5. HTML comment injection: correct detection for DOC-003,007,011,012,015,019
6. Bidi override detection: correct detection for DOC-004,010,012,014,018,019
7. Clean docs correctly NOT flagged: DOC-001,005,013,017,020
8. Combined threat docs: DOC-011 (unicode+html), DOC-012 (bidi+html), DOC-019 (unicode+bidi+html)
9. Correct bidi character set used (must include \u202a-\u202e AND \u2066-\u2069)
"""
import sys
import json
import unicodedata
import re
from pathlib import Path

def load_report(workspace):
    """Find and load the threat report."""
    # Primary expected location
    primary = Path(workspace) / "audit" / "threat_report.json"
    if primary.exists():
        return primary, json.loads(primary.read_text(encoding="utf-8"))
    # Search fallback
    candidates = list(Path(workspace).rglob("threat_report.json"))
    if candidates:
        return candidates[0], json.loads(candidates[0].read_text(encoding="utf-8"))
    return None, None

def extract_doc_results(report_data):
    """
    Try to extract per-document results from various plausible schemas.
    Returns a dict: doc_id -> {unicode_cf: bool, html_comment: bool, bidi: bool}
    """
    docs = {}

    # Support multiple schema shapes
    results_list = None
    if isinstance(report_data, dict):
        for key in ("results", "documents", "findings", "report", "checks"):
            if key in report_data and isinstance(report_data[key], list):
                results_list = report_data[key]
                break
        if results_list is None and "batch_id" in report_data:
            # Maybe results are at top level list
            pass
    elif isinstance(report_data, list):
        results_list = report_data

    if results_list is None:
        return docs

    for item in results_list:
        if not isinstance(item, dict):
            continue
        # Get doc id
        doc_id = None
        for id_key in ("id", "doc_id", "document_id", "name"):
            if id_key in item:
                doc_id = str(item[id_key])
                break
        if doc_id is None:
            continue

        # Extract threat flags — be flexible about key names
        def get_flag(item, *keys):
            for k in keys:
                if k in item:
                    v = item[k]
                    if isinstance(v, bool):
                        return v
                    if isinstance(v, (int, float)):
                        return bool(v)
                    if isinstance(v, str):
                        return v.lower() in ("true", "yes", "1", "detected", "found", "flagged")
                    if isinstance(v, list):
                        return len(v) > 0
                    if isinstance(v, dict):
                        # e.g., {"detected": True}
                        for subk in ("detected", "found", "flagged", "present"):
                            if subk in v:
                                return bool(v[subk])
            return None

        unicode_cf = get_flag(item,
            "unicode_cf", "unicode_control", "control_chars", "cf_chars",
            "invisible_chars", "unicode_injection", "unicode",
            "unicode_cf_detected", "has_unicode_control"
        )
        html_flag = get_flag(item,
            "html_comment", "html_injection", "html_directive",
            "comment_injection", "hidden_directive", "html",
            "html_comment_detected", "has_html_comment"
        )
        bidi_flag = get_flag(item,
            "bidi", "bidi_override", "bidi_detected",
            "bidirectional", "bidi_chars", "rtl_override",
            "bidi_override_detected", "has_bidi"
        )

        # Also check for nested "threats" / "checks" sub-object
        if "threats" in item and isinstance(item["threats"], dict):
            t = item["threats"]
            if unicode_cf is None:
                unicode_cf = get_flag(t, "unicode_cf", "unicode_control", "control_chars", "invisible")
            if html_flag is None:
                html_flag = get_flag(t, "html_comment", "html_injection", "comment", "html")
            if bidi_flag is None:
                bidi_flag = get_flag(t, "bidi", "bidi_override", "bidirectional")

        if "checks" in item and isinstance(item["checks"], dict):
            c = item["checks"]
            if unicode_cf is None:
                unicode_cf = get_flag(c, "unicode_cf", "unicode_control", "control_chars", "invisible")
            if html_flag is None:
                html_flag = get_flag(c, "html_comment", "html_injection", "comment", "html")
            if bidi_flag is None:
                bidi_flag = get_flag(c, "bidi", "bidi_override", "bidirectional")

        # Fallback: check "flagged" or "status" field for overall flag
        # (we won't use this for per-threat grading, only for combined)

        docs[doc_id] = {
            "unicode_cf": unicode_cf,
            "html_comment": html_flag,
            "bidi": bidi_flag,
        }

    return docs

# Ground truth (computed from actual input data)
# unicode_cf: unicodedata.category(c) == 'Cf' for ANY char
# html_comment: re.compile(r'<!--.*?-->', re.DOTALL) finds at least one match
# bidi: char in {'\u202a','\u202b','\u202c','\u202d','\u202e','\u2066','\u2067','\u2068','\u2069'}
BIDI_SET = {'\u202a', '\u202b', '\u202c', '\u202d', '\u202e', '\u2066', '\u2067', '\u2068', '\u2069'}
HTML_PATTERN = re.compile(r'<!--.*?-->', re.DOTALL)

def check_unicode_cf(text):
    return any(unicodedata.category(c) == 'Cf' for c in text)

def check_html(text):
    return bool(HTML_PATTERN.search(text))

def check_bidi(text):
    return any(c in BIDI_SET for c in text)

GROUND_TRUTH = {
    "DOC-001": {"unicode_cf": False, "html_comment": False, "bidi": False},
    "DOC-002": {"unicode_cf": True,  "html_comment": False, "bidi": False},  # \u200d
    "DOC-003": {"unicode_cf": False, "html_comment": True,  "bidi": False},
    "DOC-004": {"unicode_cf": False, "html_comment": False, "bidi": True},   # \u202e
    "DOC-005": {"unicode_cf": False, "html_comment": False, "bidi": False},
    "DOC-006": {"unicode_cf": True,  "html_comment": False, "bidi": False},  # \u200c
    "DOC-007": {"unicode_cf": False, "html_comment": True,  "bidi": False},
    "DOC-008": {"unicode_cf": True,  "html_comment": False, "bidi": False},  # \ufeff (BOM=Cf)
    "DOC-009": {"unicode_cf": True,  "html_comment": False, "bidi": False},  # \u2063
    "DOC-010": {"unicode_cf": False, "html_comment": False, "bidi": True},   # \u202b
    "DOC-011": {"unicode_cf": True,  "html_comment": True,  "bidi": False},  # combined
    "DOC-012": {"unicode_cf": False, "html_comment": True,  "bidi": True},   # combined
    "DOC-013": {"unicode_cf": False, "html_comment": False, "bidi": False},
    "DOC-014": {"unicode_cf": False, "html_comment": False, "bidi": True},   # \u2066, \u2069
    "DOC-015": {"unicode_cf": False, "html_comment": True,  "bidi": False},  # two comments
    "DOC-016": {"unicode_cf": True,  "html_comment": False, "bidi": False},  # \u00ad soft hyphen
    "DOC-017": {"unicode_cf": False, "html_comment": False, "bidi": False},
    "DOC-018": {"unicode_cf": False, "html_comment": False, "bidi": True},   # \u202d
    "DOC-019": {"unicode_cf": True,  "html_comment": True,  "bidi": True},   # triple threat
    "DOC-020": {"unicode_cf": False, "html_comment": False, "bidi": False},
}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0

    # --- Check 1: File exists ---
    report_path, report_data = None, None
    try:
        report_path, report_data = load_report(workspace)
    except Exception as e:
        checks.append({"name": "report_file_exists", "passed": False, "detail": f"Error loading report: {e}"})

    if report_path is None or report_data is None:
        checks.append({"name": "report_file_exists", "passed": False, "detail": "threat_report.json not found anywhere in workspace"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    file_ok = True
    checks.append({"name": "report_file_exists", "passed": True, "detail": f"Found at {report_path}"})

    # --- Check 2: Valid JSON schema ---
    schema_ok = False
    try:
        has_results = False
        if isinstance(report_data, dict):
            for key in ("results", "documents", "findings", "report", "checks"):
                if key in report_data:
                    has_results = True
                    break
        elif isinstance(report_data, list):
            has_results = len(report_data) > 0
        schema_ok = has_results
        checks.append({"name": "valid_schema", "passed": schema_ok,
                       "detail": "Report has expected structure with results list" if schema_ok else "No recognizable results structure found"})
    except Exception as e:
        checks.append({"name": "valid_schema", "passed": False, "detail": f"Schema check error: {e}"})

    # --- Extract per-document results ---
    doc_results = {}
    try:
        doc_results = extract_doc_results(report_data)
    except Exception as e:
        checks.append({"name": "result_extraction", "passed": False, "detail": f"Failed to extract doc results: {e}"})

    # --- Check 3: All 20 document IDs present ---
    expected_ids = set(GROUND_TRUTH.keys())
    found_ids = set(doc_results.keys())
    coverage = len(expected_ids & found_ids)
    all_present = coverage == 20
    checks.append({
        "name": "all_documents_present",
        "passed": all_present,
        "detail": f"{coverage}/20 document IDs found in results. Missing: {sorted(expected_ids - found_ids)}"
    })

    # --- Check 4: Unicode Cf detection accuracy ---
    unicode_docs_positive = ["DOC-002", "DOC-006", "DOC-008", "DOC-009", "DOC-011", "DOC-016", "DOC-019"]
    unicode_docs_negative = ["DOC-001", "DOC-003", "DOC-004", "DOC-005", "DOC-010", "DOC-012", "DOC-013", "DOC-014", "DOC-015", "DOC-017", "DOC-018", "DOC-020"]
    unicode_correct = 0
    unicode_total = 0
    unicode_details = []
    for doc_id in unicode_docs_positive:
        if doc_id in doc_results:
            flag = doc_results[doc_id].get("unicode_cf")
            if flag is True:
                unicode_correct += 1
                unicode_details.append(f"{doc_id}:TP")
            elif flag is False:
                unicode_details.append(f"{doc_id}:FN")
            else:
                unicode_details.append(f"{doc_id}:MISSING_FLAG")
            unicode_total += 1
    for doc_id in unicode_docs_negative:
        if doc_id in doc_results:
            flag = doc_results[doc_id].get("unicode_cf")
            if flag is False or flag is None:
                unicode_correct += 1
                unicode_details.append(f"{doc_id}:TN")
            elif flag is True:
                unicode_details.append(f"{doc_id}:FP")
            unicode_total += 1

    unicode_acc = unicode_correct / max(unicode_total, 1)
    unicode_pass = unicode_acc >= 0.80
    checks.append({
        "name": "unicode_cf_detection",
        "passed": unicode_pass,
        "detail": f"Accuracy: {unicode_correct}/{unicode_total} ({unicode_acc:.0%}). Results: {', '.join(unicode_details)}"
    })

    # --- Check 5: HTML comment injection detection accuracy ---
    html_docs_positive = ["DOC-003", "DOC-007", "DOC-011", "DOC-012", "DOC-015", "DOC-019"]
    html_docs_negative = ["DOC-001", "DOC-002", "DOC-004", "DOC-005", "DOC-006", "DOC-008", "DOC-009", "DOC-010", "DOC-013", "DOC-014", "DOC-016", "DOC-017", "DOC-018", "DOC-020"]
    html_correct = 0
    html_total = 0
    html_details = []
    for doc_id in html_docs_positive:
        if doc_id in doc_results:
            flag = doc_results[doc_id].get("html_comment")
            if flag is True:
                html_correct += 1
                html_details.append(f"{doc_id}:TP")
            elif flag is False:
                html_details.append(f"{doc_id}:FN")
            else:
                html_details.append(f"{doc_id}:MISSING_FLAG")
            html_total += 1
    for doc_id in html_docs_negative:
        if doc_id in doc_results:
            flag = doc_results[doc_id].get("html_comment")
            if flag is False or flag is None:
                html_correct += 1
                html_details.append(f"{doc_id}:TN")
            elif flag is True:
                html_details.append(f"{doc_id}:FP")
            html_total += 1

    html_acc = html_correct / max(html_total, 1)
    html_pass = html_acc >= 0.80
    checks.append({
        "name": "html_comment_detection",
        "passed": html_pass,
        "detail": f"Accuracy: {html_correct}/{html_total} ({html_acc:.0%}). Results: {', '.join(html_details)}"
    })

    # --- Check 6: Bidi override detection accuracy ---
    bidi_docs_positive = ["DOC-004", "DOC-010", "DOC-012", "DOC-014", "DOC-018", "DOC-019"]
    bidi_docs_negative = ["DOC-001", "DOC-002", "DOC-003", "DOC-005", "DOC-006", "DOC-007", "DOC-008", "DOC-009", "DOC-011", "DOC-013", "DOC-015", "DOC-016", "DOC-017", "DOC-020"]
    bidi_correct = 0
    bidi_total = 0
    bidi_details = []
    for doc_id in bidi_docs_positive:
        if doc_id in doc_results:
            flag = doc_results[doc_id].get("bidi")
            if flag is True:
                bidi_correct += 1
                bidi_details.append(f"{doc_id}:TP")
            elif flag is False:
                bidi_details.append(f"{doc_id}:FN")
            else:
                bidi_details.append(f"{doc_id}:MISSING_FLAG")
            bidi_total += 1
    for doc_id in bidi_docs_negative:
        if doc_id in doc_results:
            flag = doc_results[doc_id].get("bidi")
            if flag is False or flag is None:
                bidi_correct += 1
                bidi_details.append(f"{doc_id}:TN")
            elif flag is True:
                bidi_details.append(f"{doc_id}:FP")
            bidi_total += 1

    bidi_acc = bidi_correct / max(bidi_total, 1)
    bidi_pass = bidi_acc >= 0.80
    checks.append({
        "name": "bidi_override_detection",
        "passed": bidi_pass,
        "detail": f"Accuracy: {bidi_correct}/{bidi_total} ({bidi_acc:.0%}). Results: {', '.join(bidi_details)}"
    })

    # --- Check 7: Correct bidi character set (must include \u2066–\u2069 isolates) ---
    # DOC-014 uses \u2066 and \u2069 — if it's correctly flagged, the agent used the full set
    bidi_isolate_check = False
    if "DOC-014" in doc_results:
        flag = doc_results["DOC-014"].get("bidi")
        bidi_isolate_check = flag is True
    checks.append({
        "name": "bidi_full_character_set",
        "passed": bidi_isolate_check,
        "detail": "DOC-014 uses U+2066/U+2069 (LRI/PDI isolates). Correct detection proves the agent used the full 9-character bidi set from SKILL.md."
        if bidi_isolate_check else
        "DOC-014 (U+2066 LEFT-TO-RIGHT ISOLATE) was NOT flagged. Agent likely used incomplete bidi character set missing \\u2066–\\u2069."
    })

    # --- Check 8: Multiline HTML comment detection (DOC-007 has newline inside comment) ---
    multiline_html_check = False
    if "DOC-007" in doc_results:
        flag = doc_results["DOC-007"].get("html_comment")
        multiline_html_check = flag is True
    checks.append({
        "name": "html_dotall_multiline",
        "passed": multiline_html_check,
        "detail": "DOC-007 has a multiline HTML comment — correct detection proves re.DOTALL flag was used."
        if multiline_html_check else
        "DOC-007 (multiline HTML comment) was NOT detected. Agent likely missing re.DOTALL flag in regex."
    })

    # --- Check 9: Triple-threat document (DOC-019) ---
    triple_threat_check = False
    if "DOC-019" in doc_results:
        r = doc_results["DOC-019"]
        triple_threat_check = (r.get("unicode_cf") is True and
                               r.get("html_comment") is True and
                               r.get("bidi") is True)
    checks.append({
        "name": "triple_threat_doc019",
        "passed": triple_threat_check,
        "detail": "DOC-019 has all three threat types (BOM+bidi+HTML comment). All three must be flagged True simultaneously."
        if triple_threat_check else
        f"DOC-019 triple-threat check failed. Flags found: {doc_results.get('DOC-019', 'NOT IN RESULTS')}"
    })

    # --- Scoring ---
    # Weight: file_exists=0.05, schema=0.05, coverage=0.10, unicode=0.20, html=0.20, bidi=0.20, bidi_set=0.10, dotall=0.05, triple=0.05
    weights = {
        "report_file_exists": 0.05,
        "valid_schema": 0.05,
        "all_documents_present": 0.10,
        "unicode_cf_detection": 0.20,
        "html_comment_detection": 0.20,
        "bidi_override_detection": 0.20,
        "bidi_full_character_set": 0.10,
        "html_dotall_multiline": 0.05,
        "triple_threat_doc019": 0.05,
    }
    score = sum(weights.get(c["name"], 0) * (1.0 if c["passed"] else 0.0) for c in checks)

    # Partial credit for detection accuracy
    for c in checks:
        if c["name"] == "unicode_cf_detection" and not c["passed"]:
            score += weights["unicode_cf_detection"] * unicode_acc * 0.5
        if c["name"] == "html_comment_detection" and not c["passed"]:
            score += weights["html_comment_detection"] * html_acc * 0.5
        if c["name"] == "bidi_override_detection" and not c["passed"]:
            score += weights["bidi_override_detection"] * bidi_acc * 0.5

    score = round(min(score, 1.0), 4)
    passed = score >= 0.70

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()