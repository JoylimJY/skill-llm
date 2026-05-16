import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    total_score = 0.0

    # ── Find output file ──────────────────────────────────────────────────────
    candidates = list(Path(workspace).rglob("consolidated_contacts.json"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named 'consolidated_contacts.json'" if file_found else "No file named 'consolidated_contacts.json' found anywhere in workspace"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    output_path = candidates[0]

    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        with open(output_path) as f:
            data = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": f"Valid JSON at {output_path}"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Top-level structure: must have 'contacts' list and 'metadata' dict ───
    has_contacts = isinstance(data.get("contacts"), list)
    has_metadata = isinstance(data.get("metadata"), dict)
    checks.append({
        "name": "top_level_structure",
        "passed": has_contacts and has_metadata,
        "detail": f"contacts: {'list' if has_contacts else 'MISSING/WRONG TYPE'}, metadata: {'dict' if has_metadata else 'MISSING/WRONG TYPE'}"
    })
    if not (has_contacts and has_metadata):
        return {"passed": False, "score": 0.0, "checks": checks}

    contacts = data["contacts"]
    metadata = data["metadata"]

    # ── Expected valid contacts after dedup and validation ───────────────────
    # Valid Turkish phone: matches pattern like "0XXX YYY YY YY" (with spaces, 11 digits, starts with 0)
    # From november_notes.txt:
    #   ayse.kaya@globalcorp.com / 0532 444 55 66 ✓
    #   ali.demir@techsolutions.net / 0545 876 54 32 ✓
    #   +44 20 7946 0958 → INVALID phone
    #   fatma.celik@startupzone.io / 0533-111-22-33 → INVALID phone (dashes)
    #   zeynep.arslan@innovate.biz / 0506 321 98 76 ✓
    # From december_notes.txt:
    #   emre.yildiz@databridge.com / "0 5 5 2   9 9 9   1 1   2 2" → INVALID phone (weird spacing)
    #   selin.ozturk@cloudnine.net / 0541 222 33 44 ✓
    #   ayse.kaya@globalcorp.com → DUPLICATE, skip
    #   @nodomain.com → invalid email
    #   canan.polat@enterprise.org / 0530 555 66 77 ✓
    # From crm_export_q4.csv (via csv_to_dict):
    #   tuncay.berk@logistics.com / 0544 111 22 33 ✓
    #   merve.aksoy@retailpro.net / 0532 999 00 11 ✓
    #   NOT_AN_EMAIL → invalid email
    #   pinar.yurt@mediasphere.com / +90-532-111-2233 → INVALID phone
    #   bulent.erol@fintech.io / 0548 333 44 55 ✓

    expected_emails = {
        "ayse.kaya@globalcorp.com",
        "ali.demir@techsolutions.net",
        "zeynep.arslan@innovate.biz",
        "selin.ozturk@cloudnine.net",
        "canan.polat@enterprise.org",
        "tuncay.berk@logistics.com",
        "merve.aksoy@retailpro.net",
        "bulent.erol@fintech.io",
    }

    found_emails = set()
    for c in contacts:
        if isinstance(c.get("email"), str):
            found_emails.add(c["email"].strip().lower())

    # Check expected contacts are present
    missing = expected_emails - found_emails
    extra_invalid = found_emails - expected_emails
    # Extra contacts that weren't expected (shouldn't include invalid ones)
    invalid_emails_that_should_be_excluded = {
        "not_an_email",
        "@nodomain.com",
        "bad_email_address",
        "old_email@archived.com",
    }
    # Check no clearly invalid emails slipped through
    no_invalid_emails = len(found_emails.intersection(invalid_emails_that_should_be_excluded)) == 0

    contact_count_ok = len(contacts) == len(expected_emails)
    checks.append({
        "name": "correct_contact_count_and_dedup",
        "passed": contact_count_ok,
        "detail": f"Expected {len(expected_emails)} unique valid contacts, got {len(contacts)}. Missing: {missing}. Unexpected: {extra_invalid - invalid_emails_that_should_be_excluded}"
    })

    checks.append({
        "name": "no_invalid_emails_in_output",
        "passed": no_invalid_emails,
        "detail": f"Output must not contain known-invalid emails. Found: {found_emails.intersection(invalid_emails_that_should_be_excluded)}"
    })

    # ── Validate Turkish phone rejection ─────────────────────────────────────
    # No contact should have an international phone like +44... or +90-...
    invalid_phone_patterns = ["+44", "+90-", "0533-111", "0 5 5 2"]
    bad_phones = []
    for c in contacts:
        phone = str(c.get("phone", ""))
        for pat in invalid_phone_patterns:
            if pat in phone:
                bad_phones.append(phone)
    phone_filter_ok = len(bad_phones) == 0
    checks.append({
        "name": "turkish_phone_format_enforced",
        "passed": phone_filter_ok,
        "detail": f"No invalid phone formats should appear in output. Found bad phones: {bad_phones}"
    })

    # ── Each contact must have a non-empty 'id' field ─────────────────────────
    all_have_ids = all(
        isinstance(c.get("id"), str) and len(c.get("id", "")) > 0
        for c in contacts
    )
    checks.append({
        "name": "contacts_have_ids",
        "passed": all_have_ids,
        "detail": f"Every contact must have a non-empty 'id' string field. Passed: {all_have_ids}"
    })

    # IDs must be unique
    ids = [c.get("id") for c in contacts if c.get("id")]
    ids_unique = len(ids) == len(set(ids))
    checks.append({
        "name": "ids_are_unique",
        "passed": ids_unique,
        "detail": f"All contact IDs must be unique. Got {len(ids)} ids, {len(set(ids))} unique."
    })

    # IDs look like hex hashes (8 chars from UtilityTools.generate_id)
    ids_look_like_hashes = all(
        len(i) == 8 and all(c in "0123456789abcdef" for c in i)
        for i in ids
    )
    checks.append({
        "name": "ids_are_library_generated_hashes",
        "passed": ids_look_like_hashes,
        "detail": f"IDs must be 8-char hex strings as produced by UtilityTools.generate_id. Sample IDs: {ids[:3]}"
    })

    # ── Each contact must have a 'timestamp' field ────────────────────────────
    all_have_timestamps = all(
        isinstance(c.get("timestamp"), str) and len(c.get("timestamp", "")) > 0
        for c in contacts
    )
    checks.append({
        "name": "contacts_have_timestamps",
        "passed": all_have_timestamps,
        "detail": f"Every contact must have a 'timestamp' string. Passed: {all_have_timestamps}"
    })

    # ── Metadata must have 'total_contacts' and 'processed_at' ───────────────
    meta_total = metadata.get("total_contacts")
    meta_time = metadata.get("processed_at")
    meta_total_ok = meta_total == len(expected_emails)
    meta_time_ok = isinstance(meta_time, str) and len(meta_time) > 0
    checks.append({
        "name": "metadata_total_contacts",
        "passed": meta_total_ok,
        "detail": f"metadata.total_contacts should be {len(expected_emails)}, got {meta_total}"
    })
    checks.append({
        "name": "metadata_processed_at",
        "passed": meta_time_ok,
        "detail": f"metadata.processed_at must be a non-empty string timestamp. Got: {meta_time}"
    })

    # ── MemoryTools usage: check memory-derived metadata is consistent ────────
    # The agent should have used MemoryTools to store and retrieve total_contacts
    # We can only verify the final output reflects it correctly (already checked above)

    # ── Score calculation ─────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)

    # Must pass critical checks to pass overall
    critical = ["output_file_exists", "valid_json", "correct_contact_count_and_dedup",
                "turkish_phone_format_enforced", "ids_are_library_generated_hashes"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

    return {
        "passed": critical_passed and score >= 0.8,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))