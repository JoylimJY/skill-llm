import json
import sys
from pathlib import Path
from datetime import date

def evaluate(workspace: str):
    checks = []
    crm_file = Path(workspace) / "StudioBrain/00_SYSTEM/skills/gracie-crm/crm.json"

    # ── Load CRM data ─────────────────────────────────────────────────────────
    try:
        raw = crm_file.read_text()
        data = json.loads(raw)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "crm_json_loadable", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        return

    checks.append({"name": "crm_json_loadable", "passed": True, "detail": f"Loaded {len(data)} leads."})

    # Helper
    def find_lead(name_fragment):
        for l in data:
            if name_fragment.lower() in l.get("name", "").lower():
                return l
        return None

    # ── CHECK 1: All three leads added ────────────────────────────────────────
    protech = find_lead("protech")
    arctic  = find_lead("arctic")
    bayside = find_lead("bayside")

    checks.append({
        "name": "lead_protech_exists",
        "passed": protech is not None,
        "detail": f"ProTech Auto Service found: {protech is not None}"
    })
    checks.append({
        "name": "lead_arctic_exists",
        "passed": arctic is not None,
        "detail": f"Arctic Comfort HVAC found: {arctic is not None}"
    })
    checks.append({
        "name": "lead_bayside_exists",
        "passed": bayside is not None,
        "detail": f"Bayside Family Dental found: {bayside is not None}"
    })

    # ── CHECK 2: Correct categories ───────────────────────────────────────────
    protech_cat_ok = protech is not None and protech.get("category") == "auto"
    arctic_cat_ok  = arctic  is not None and arctic.get("category") == "hvac"
    bayside_cat_ok = bayside is not None and bayside.get("category") == "dental"

    checks.append({
        "name": "protech_category_auto",
        "passed": protech_cat_ok,
        "detail": f"ProTech category: {protech.get('category') if protech else 'N/A'} (expected: auto)"
    })
    checks.append({
        "name": "arctic_category_hvac",
        "passed": arctic_cat_ok,
        "detail": f"Arctic category: {arctic.get('category') if arctic else 'N/A'} (expected: hvac)"
    })
    checks.append({
        "name": "bayside_category_dental",
        "passed": bayside_cat_ok,
        "detail": f"Bayside category: {bayside.get('category') if bayside else 'N/A'} (expected: dental)"
    })

    # ── CHECK 3: Correct phone numbers ────────────────────────────────────────
    protech_phone_ok = protech is not None and "347" in protech.get("phone", "")
    arctic_phone_ok  = arctic  is not None and "646" in arctic.get("phone", "")
    bayside_phone_ok = bayside is not None and "718" in bayside.get("phone", "")

    checks.append({
        "name": "protech_phone",
        "passed": protech_phone_ok,
        "detail": f"ProTech phone: {protech.get('phone') if protech else 'N/A'}"
    })
    checks.append({
        "name": "arctic_phone",
        "passed": arctic_phone_ok,
        "detail": f"Arctic phone: {arctic.get('phone') if arctic else 'N/A'}"
    })
    checks.append({
        "name": "bayside_phone",
        "passed": bayside_phone_ok,
        "detail": f"Bayside phone: {bayside.get('phone') if bayside else 'N/A'}"
    })

    # ── CHECK 4: ProTech status = no_answer (proprietary trap: not "no answer") ─
    protech_status_ok = protech is not None and protech.get("status") == "no_answer"
    checks.append({
        "name": "protech_status_no_answer",
        "passed": protech_status_ok,
        "detail": f"ProTech status: '{protech.get('status') if protech else 'N/A'}' (expected: 'no_answer')"
    })

    # ── CHECK 5: Arctic status = interested ───────────────────────────────────
    arctic_status_ok = arctic is not None and arctic.get("status") == "interested"
    checks.append({
        "name": "arctic_status_interested",
        "passed": arctic_status_ok,
        "detail": f"Arctic status: '{arctic.get('status') if arctic else 'N/A'}' (expected: 'interested')"
    })

    # ── CHECK 6: Bayside status = called or no_answer (receptionist said call back) ─
    bayside_status_ok = bayside is not None and bayside.get("status") in ("called", "no_answer")
    checks.append({
        "name": "bayside_status_called_or_no_answer",
        "passed": bayside_status_ok,
        "detail": f"Bayside status: '{bayside.get('status') if bayside else 'N/A'}' (expected: 'called' or 'no_answer')"
    })

    # ── CHECK 7: Follow-up dates ───────────────────────────────────────────────
    protech_fu = protech is not None and protech.get("followup_date") == "2026-03-15"
    arctic_fu  = arctic  is not None and arctic.get("followup_date") == "2026-03-12"
    bayside_fu = bayside is not None and bayside.get("followup_date") == "2026-03-11"

    checks.append({
        "name": "protech_followup_date",
        "passed": protech_fu,
        "detail": f"ProTech followup: {protech.get('followup_date') if protech else 'N/A'} (expected: 2026-03-15)"
    })
    checks.append({
        "name": "arctic_followup_date",
        "passed": arctic_fu,
        "detail": f"Arctic followup: {arctic.get('followup_date') if arctic else 'N/A'} (expected: 2026-03-12)"
    })
    checks.append({
        "name": "bayside_followup_date",
        "passed": bayside_fu,
        "detail": f"Bayside followup: {bayside.get('followup_date') if bayside else 'N/A'} (expected: 2026-03-11)"
    })

    # ── CHECK 8: Notes on Arctic and Bayside ──────────────────────────────────
    arctic_notes = arctic.get("notes", []) if arctic else []
    arctic_note_ok = any("linda" in n.lower() or "missed calls" in n.lower() or "warm" in n.lower() for n in arctic_notes)
    checks.append({
        "name": "arctic_note_attached",
        "passed": arctic_note_ok,
        "detail": f"Arctic notes: {arctic_notes}"
    })

    bayside_notes = bayside.get("notes", []) if bayside else []
    bayside_note_ok = any("maria" in n.lower() or "10am" in n.lower() or "front desk" in n.lower() for n in bayside_notes)
    checks.append({
        "name": "bayside_note_attached",
        "passed": bayside_note_ok,
        "detail": f"Bayside notes: {bayside_notes}"
    })

    # ── CHECK 9: Call records exist for all three leads ───────────────────────
    protech_calls = protech.get("calls", []) if protech else []
    arctic_calls  = arctic.get("calls", [])  if arctic  else []
    bayside_calls = bayside.get("calls", []) if bayside else []

    checks.append({
        "name": "protech_has_call_record",
        "passed": len(protech_calls) > 0,
        "detail": f"ProTech call count: {len(protech_calls)}"
    })
    checks.append({
        "name": "arctic_has_call_record",
        "passed": len(arctic_calls) > 0,
        "detail": f"Arctic call count: {len(arctic_calls)}"
    })
    checks.append({
        "name": "bayside_has_call_record",
        "passed": len(bayside_calls) > 0,
        "detail": f"Bayside call count: {len(bayside_calls)}"
    })

    # ── CHECK 10: Initial status was "new" (IDs were auto-assigned, not 0) ────
    all_ids_positive = all(l.get("id", 0) >= 1 for l in data)
    checks.append({
        "name": "all_ids_positive",
        "passed": all_ids_positive,
        "detail": f"All lead IDs >= 1: {all_ids_positive}"
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall = passed_count == total

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/root"
    evaluate(workspace)