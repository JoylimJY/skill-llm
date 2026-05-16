import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    
    # Find the verification report
    report_path = None
    candidates = list(Path(workspace).rglob("verification_report.json"))
    if candidates:
        report_path = candidates[0]
    
    if not report_path or not report_path.exists():
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_exists", "passed": False, "detail": "verification_report.json not found anywhere in workspace"}]
        }
    
    checks.append({"name": "report_exists", "passed": True, "detail": f"Found at {report_path}"})
    
    # Load report
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "report_parseable", "passed": False, "detail": f"JSON parse error: {e}"}]
        }
    
    checks.append({"name": "report_parseable", "passed": True, "detail": "JSON parsed successfully"})
    
    # Extract results — support both list and dict formats
    # Agent may produce {"results": [...]} or a list directly or {"evidence_items": [...]}
    results = None
    if isinstance(report, list):
        results = report
    elif isinstance(report, dict):
        for key in ("results", "evidence_items", "items", "verification_results", "report"):
            if key in report and isinstance(report[key], list):
                results = report[key]
                break
        if results is None:
            # Maybe it's a dict keyed by ID
            # Try to find any list value
            for v in report.values():
                if isinstance(v, list) and len(v) > 0:
                    results = v
                    break
    
    if not results:
        checks.append({"name": "report_has_results", "passed": False, "detail": f"Could not find a results list in report. Keys: {list(report.keys()) if isinstance(report, dict) else 'N/A'}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "report_has_results", "passed": True, "detail": f"Found {len(results)} result entries"})
    
    # Build a lookup by evidence ID
    result_by_id = {}
    for item in results:
        if isinstance(item, dict):
            # Try various ID field names
            for id_key in ("id", "evidence_id", "item_id", "ID"):
                if id_key in item:
                    result_by_id[item[id_key]] = item
                    break
    
    def get_validity(item):
        """Extract whether the item is marked valid/invalid."""
        if not item:
            return None
        for key in ("valid", "is_valid", "status", "result", "verified", "passed"):
            if key in item:
                val = item[key]
                if isinstance(val, bool):
                    return val
                if isinstance(val, str):
                    val_lower = val.lower()
                    if val_lower in ("valid", "true", "pass", "passed", "ok", "success", "verified"):
                        return True
                    if val_lower in ("invalid", "false", "fail", "failed", "error", "not_found", 
                                     "missing", "placeholder", "empty", "type_mismatch", "content_mismatch"):
                        return False
        return None
    
    def get_reason(item):
        """Extract reason/detail string."""
        if not item:
            return ""
        for key in ("reason", "detail", "message", "error", "note", "description", "issue"):
            if key in item:
                return str(item[key]).lower()
        return str(item).lower()
    
    # Define expected outcomes per the SKILL.md rules:
    # EV-001: /real-report → 200, text/plain, real content → VALID
    # EV-002: /placeholder-page → 200, but content has "placeholder" → INVALID (placeholder content)
    # EV-003: /missing-resource → 404 → INVALID (not found)
    # EV-004: /pdf-as-text → 200, but content-type is application/pdf, claimed_type=text → INVALID (content type mismatch)
    # EV-005: /valid-json-report → 200, application/json, no placeholders → VALID (json is substantive content)
    # EV-006: /lorem-ipsum-page → 200, but content has "lorem ipsum" → INVALID (placeholder content)
    # EV-007: local valid non-empty file → VALID
    # EV-008: local empty file (0 bytes) → INVALID (empty file)
    # EV-009: local missing file → INVALID (path does not exist)
    # EV-010: local valid non-empty file → VALID
    
    expected = {
        "EV-001": {"valid": True,  "reason_hint": "200 ok real content"},
        "EV-002": {"valid": False, "reason_hint": "placeholder"},
        "EV-003": {"valid": False, "reason_hint": "404 not found"},
        "EV-004": {"valid": False, "reason_hint": "content type mismatch pdf"},
        "EV-005": {"valid": True,  "reason_hint": "200 ok substantive json"},
        "EV-006": {"valid": False, "reason_hint": "lorem ipsum placeholder"},
        "EV-007": {"valid": True,  "reason_hint": "local file exists non-empty"},
        "EV-008": {"valid": False, "reason_hint": "empty file 0 bytes"},
        "EV-009": {"valid": False, "reason_hint": "file not found missing"},
        "EV-010": {"valid": True,  "reason_hint": "local file exists non-empty"},
    }
    
    item_checks = []
    correct_count = 0
    
    for ev_id, exp in expected.items():
        item = result_by_id.get(ev_id)
        validity = get_validity(item)
        reason = get_reason(item)
        
        if item is None:
            item_checks.append({
                "name": f"item_{ev_id}",
                "passed": False,
                "detail": f"{ev_id}: Not found in report. Expected valid={exp['valid']} ({exp['reason_hint']})"
            })
            continue
        
        if validity is None:
            item_checks.append({
                "name": f"item_{ev_id}",
                "passed": False,
                "detail": f"{ev_id}: Could not determine validity from item: {item}. Expected valid={exp['valid']}"
            })
            continue
        
        passed = (validity == exp["valid"])
        if passed:
            correct_count += 1
        
        item_checks.append({
            "name": f"item_{ev_id}",
            "passed": passed,
            "detail": f"{ev_id}: got valid={validity} (reason: '{reason[:80]}'), expected valid={exp['valid']} ({exp['reason_hint']})"
        })
    
    checks.extend(item_checks)
    
    # Specific proprietary trap checks
    # 1. Placeholder detection (EV-002 and EV-006) — both must be flagged invalid
    ev002 = result_by_id.get("EV-002")
    ev006 = result_by_id.get("EV-006")
    placeholder_trap = (get_validity(ev002) == False and get_validity(ev006) == False)
    checks.append({
        "name": "proprietary_placeholder_detection",
        "passed": placeholder_trap,
        "detail": f"Both placeholder-content URLs (EV-002, EV-006) must be flagged invalid. EV-002={get_validity(ev002)}, EV-006={get_validity(ev006)}"
    })
    
    # 2. Empty file check (EV-008) — must be flagged invalid even though file exists
    ev008 = result_by_id.get("EV-008")
    empty_trap = (get_validity(ev008) == False)
    checks.append({
        "name": "proprietary_empty_file_detection",
        "passed": empty_trap,
        "detail": f"Empty local file (EV-008) must be flagged invalid (size=0). Got valid={get_validity(ev008)}"
    })
    
    # 3. Content type mismatch (EV-004) — PDF served as claimed text
    ev004 = result_by_id.get("EV-004")
    type_trap = (get_validity(ev004) == False)
    checks.append({
        "name": "proprietary_content_type_mismatch",
        "passed": type_trap,
        "detail": f"Content-type mismatch (EV-004, PDF claimed as text) must be flagged invalid. Got valid={get_validity(ev004)}"
    })
    
    # Score calculation
    total_items = len(expected)
    base_score = correct_count / total_items
    
    # Bonus for proprietary traps (they're included in correct_count already)
    proprietary_score = sum([placeholder_trap, empty_trap, type_trap]) / 3.0
    
    # Final score: 70% item accuracy + 30% proprietary traps
    final_score = round(0.7 * base_score + 0.3 * proprietary_score, 3)
    
    all_items_passed = correct_count == total_items
    all_proprietary_passed = placeholder_trap and empty_trap and type_trap
    overall_passed = all_items_passed and all_proprietary_passed
    
    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))