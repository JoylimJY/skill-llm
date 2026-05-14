import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # Locate the output file
    report_files = list(Path(workspace).rglob("migration_assessment_report.json"))
    if not report_files:
        checks.append({"name": "file_exists", "passed": False, "detail": "migration_assessment_report.json not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {report_path}"})
    total_score += 0.05

    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"Could not parse JSON: {e}"})
        return {"passed": False, "score": total_score, "checks": checks}

    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON."})
    total_score += 0.05

    # Check top-level structure: must have a list of migration assessments
    # Accept various key names: migrations, assessments, migration_assessments, results
    migration_list = None
    for key in ["migrations", "assessments", "migration_assessments", "results", "items"]:
        if key in report and isinstance(report[key], list):
            migration_list = report[key]
            break

    if migration_list is None:
        # Try if report itself is a list
        if isinstance(report, list):
            migration_list = report
        else:
            checks.append({"name": "has_migration_list", "passed": False, "detail": "No list of migration assessments found. Expected a key like 'migrations', 'assessments', or a top-level array."})
            return {"passed": False, "score": total_score, "checks": checks}

    checks.append({"name": "has_migration_list", "passed": True, "detail": f"Found migration list with {len(migration_list)} entries."})
    total_score += 0.05

    if len(migration_list) < 7:
        checks.append({"name": "all_seven_migrations", "passed": False, "detail": f"Expected 7 migration entries, found {len(migration_list)}."})
    else:
        checks.append({"name": "all_seven_migrations", "passed": True, "detail": "All 7 migration entries present."})
        total_score += 0.05

    # Helper: find entry by migration id or staff name
    def find_entry(mig_id, staff_name):
        for entry in migration_list:
            if not isinstance(entry, dict):
                continue
            # Check by ID
            for id_key in ["id", "migration_id", "mig_id"]:
                if entry.get(id_key, "").upper() == mig_id.upper():
                    return entry
            # Check by staff name (partial match)
            for name_key in ["staff_name", "name", "employee", "employee_name"]:
                if staff_name.lower() in str(entry.get(name_key, "")).lower():
                    return entry
        return None

    def get_field(entry, *keys):
        """Get field from entry trying multiple possible key names."""
        for k in keys:
            if k in entry:
                return entry[k]
        return None

    def field_contains(value, *keywords):
        """Check if a field value contains any of the keywords (case-insensitive)."""
        if value is None:
            return False
        val_str = str(value).lower()
        return any(kw.lower() in val_str for kw in keywords)

    # ===== CHECK 1: MIG-001 Alice Chen - Yahoo Mail → Gmail =====
    # Expected: Method = "IMAP → Gmail Import", Complexity = "Easy"
    # Risk: Must use app passwords, free account has folder limits
    entry_001 = find_entry("MIG-001", "Alice Chen")
    if entry_001 is None:
        checks.append({"name": "mig001_found", "passed": False, "detail": "MIG-001 (Alice Chen / Yahoo Mail) entry not found."})
    else:
        checks.append({"name": "mig001_found", "passed": True, "detail": "MIG-001 entry found."})
        total_score += 0.03

        # Complexity: Easy
        complexity = get_field(entry_001, "complexity", "difficulty", "migration_complexity")
        c_pass = field_contains(complexity, "easy")
        checks.append({"name": "mig001_complexity_easy", "passed": c_pass,
                        "detail": f"Yahoo→Gmail complexity should be 'Easy'. Got: {complexity}"})
        if c_pass: total_score += 0.05

        # Method: IMAP → Gmail Import
        method = get_field(entry_001, "method", "migration_method", "approach", "recommended_method")
        m_pass = field_contains(method, "imap", "gmail import", "import")
        checks.append({"name": "mig001_method_imap_gmail", "passed": m_pass,
                        "detail": f"Yahoo→Gmail method should reference IMAP/Gmail Import. Got: {method}"})
        if m_pass: total_score += 0.05

        # Risk/challenge: app password AND folder limits (free account)
        risks_text = json.dumps(entry_001).lower()
        app_pass_mentioned = "app password" in risks_text or "app-password" in risks_text or "application password" in risks_text
        folder_limit_mentioned = "folder limit" in risks_text or "folder limit" in risks_text or "free account" in risks_text or "limited folder" in risks_text or "folder" in risks_text
        checks.append({"name": "mig001_app_password_risk", "passed": app_pass_mentioned,
                        "detail": f"MIG-001 should mention app password requirement for Yahoo. Found in entry: {app_pass_mentioned}"})
        if app_pass_mentioned: total_score += 0.04

        checks.append({"name": "mig001_folder_limit_risk", "passed": folder_limit_mentioned,
                        "detail": f"MIG-001 (Yahoo free account) should flag folder limits. Found: {folder_limit_mentioned}"})
        if folder_limit_mentioned: total_score += 0.03

    # ===== CHECK 2: MIG-002 Bob Patel - Zoho Mail → Gmail =====
    # Expected: Method = "IMAP → Gmail Import", Complexity = "Easy"
    entry_002 = find_entry("MIG-002", "Bob Patel")
    if entry_002 is None:
        checks.append({"name": "mig002_found", "passed": False, "detail": "MIG-002 (Bob Patel / Zoho Mail) entry not found."})
    else:
        checks.append({"name": "mig002_found", "passed": True, "detail": "MIG-002 entry found."})
        total_score += 0.03

        complexity = get_field(entry_002, "complexity", "difficulty", "migration_complexity")
        c_pass = field_contains(complexity, "easy")
        checks.append({"name": "mig002_complexity_easy", "passed": c_pass,
                        "detail": f"Zoho→Gmail complexity should be 'Easy'. Got: {complexity}"})
        if c_pass: total_score += 0.04

        method = get_field(entry_002, "method", "migration_method", "approach", "recommended_method")
        m_pass = field_contains(method, "imap", "gmail import", "import")
        checks.append({"name": "mig002_method_imap_gmail", "passed": m_pass,
                        "detail": f"Zoho→Gmail method should reference IMAP/Gmail Import. Got: {method}"})
        if m_pass: total_score += 0.04

    # ===== CHECK 3: MIG-003 Carol Russo - ProtonMail (FREE) → Gmail =====
    # CRITICAL PROPRIETARY TRAP:
    # - Method: "Export → Import" (NOT IMAP bridging - ProtonMail has NO IMAP)
    # - Complexity: "Hard"
    # - Free account: ProtonMail Bridge is ONLY for paid plans
    # - Workaround: Export to Thunderbird first, then migrate from Thunderbird
    # - "No bulk export due to encryption"
    entry_003 = find_entry("MIG-003", "Carol Russo")
    if entry_003 is None:
        checks.append({"name": "mig003_found", "passed": False, "detail": "MIG-003 (Carol Russo / ProtonMail free) entry not found."})
    else:
        checks.append({"name": "mig003_found", "passed": True, "detail": "MIG-003 entry found."})
        total_score += 0.03

        complexity = get_field(entry_003, "complexity", "difficulty", "migration_complexity")
        c_pass = field_contains(complexity, "hard")
        checks.append({"name": "mig003_complexity_hard", "passed": c_pass,
                        "detail": f"ProtonMail→Gmail complexity should be 'Hard'. Got: {complexity}"})
        if c_pass: total_score += 0.06

        method = get_field(entry_003, "method", "migration_method", "approach", "recommended_method")
        # Should NOT say IMAP (ProtonMail has no IMAP)
        entry_text = json.dumps(entry_003).lower()
        no_imap_direct = not ("imap" in str(method).lower() and "direct" in str(method).lower())
        # Should mention export/import approach
        export_mentioned = field_contains(method, "export", "import", "thunderbird", "eml")
        checks.append({"name": "mig003_method_export_not_imap", "passed": export_mentioned,
                        "detail": f"ProtonMail→Gmail should use Export→Import (not direct IMAP). Got: {method}"})
        if export_mentioned: total_score += 0.06

        # Must flag: no IMAP access / encryption limitation
        no_imap_flag = "no imap" in entry_text or "no bulk" in entry_text or "encryption" in entry_text or "limited export" in entry_text or "imap access" in entry_text
        checks.append({"name": "mig003_no_imap_flagged", "passed": no_imap_flag,
                        "detail": f"MIG-003 must flag ProtonMail has no IMAP access due to encryption. Found: {no_imap_flag}"})
        if no_imap_flag: total_score += 0.06

        # Free account: ProtonMail Bridge NOT available (paid only)
        # The workaround must mention export to Thunderbird or individual EML export
        bridge_caveat = "paid" in entry_text or "bridge" in entry_text or "thunderbird" in entry_text or "individual" in entry_text or "eml" in entry_text
        checks.append({"name": "mig003_free_account_limitation", "passed": bridge_caveat,
                        "detail": f"MIG-003 (free ProtonMail) should flag Bridge is only for paid plans or recommend Thunderbird workaround. Found: {bridge_caveat}"})
        if bridge_caveat: total_score += 0.05

    # ===== CHECK 4: MIG-004 Dan Whitmore - iCloud Mail → Gmail =====
    # Expected: Method = "IMAP → Gmail Import", Complexity = "Easy"
    # iCloud quirks: some folders may not sync, slow IMAP response
    entry_004 = find_entry("MIG-004", "Dan Whitmore")
    if entry_004 is None:
        checks.append({"name": "mig004_found", "passed": False, "detail": "MIG-004 (Dan Whitmore / iCloud) entry not found."})
    else:
        checks.append({"name": "mig004_found", "passed": True, "detail": "MIG-004 entry found."})
        total_score += 0.03

        complexity = get_field(entry_004, "complexity", "difficulty", "migration_complexity")
        c_pass = field_contains(complexity, "easy")
        checks.append({"name": "mig004_complexity_easy", "passed": c_pass,
                        "detail": f"iCloud→Gmail complexity should be 'Easy'. Got: {complexity}"})
        if c_pass: total_score += 0.04

        method = get_field(entry_004, "method", "migration_method", "approach", "recommended_method")
        m_pass = field_contains(method, "imap", "gmail import", "import")
        checks.append({"name": "mig004_method_imap_gmail", "passed": m_pass,
                        "detail": f"iCloud→Gmail method should reference IMAP/Gmail Import. Got: {method}"})
        if m_pass: total_score += 0.04

        # iCloud-specific quirks
        entry_text = json.dumps(entry_004).lower()
        icloud_quirk = ("folder" in entry_text and ("sync" in entry_text or "quirk" in entry_text)) or \
                       "slow" in entry_text or "app password" in entry_text or \
                       "imap quirk" in entry_text or "not sync" in entry_text or \
                       "performance" in entry_text
        checks.append({"name": "mig004_icloud_quirks_flagged", "passed": icloud_quirk,
                        "detail": f"MIG-004 should note iCloud IMAP quirks (slow response, folder sync issues, app password). Found: {icloud_quirk}"})
        if icloud_quirk: total_score += 0.04

    # ===== CHECK 5: MIG-005 Eve Tanaka - Zoho Mail (large 18GB) → Gmail =====
    # Expected: Complexity "Easy", Method "IMAP → Gmail Import"
    # BUT: Large mailbox → must flag size/batch challenge
    entry_005 = find_entry("MIG-005", "Eve Tanaka")
    if entry_005 is None:
        checks.append({"name": "mig005_found", "passed": False, "detail": "MIG-005 (Eve Tanaka / Zoho large) entry not found."})
    else:
        checks.append({"name": "mig005_found", "passed": True, "detail": "MIG-005 entry found."})
        total_score += 0.03

        # Large mailbox risk
        entry_text = json.dumps(entry_005).lower()
        size_risk = "batch" in entry_text or "large" in entry_text or "18" in entry_text or \
                    "size" in entry_text or "storage" in entry_text or "quota" in entry_text or \
                    "split" in entry_text
        checks.append({"name": "mig005_large_mailbox_risk", "passed": size_risk,
                        "detail": f"MIG-005 (18GB mailbox) should flag size/batch/storage challenge. Found: {size_risk}"})
        if size_risk: total_score += 0.05

    # ===== CHECK 6: MIG-006 Frank O'Brien - Yahoo Mail (free, many subfolders) → Gmail =====
    # Same as MIG-001 but emphasize folder mapping challenge
    entry_006 = find_entry("MIG-006", "Frank O'Brien")
    if entry_006 is None:
        checks.append({"name": "mig006_found", "passed": False, "detail": "MIG-006 (Frank O'Brien / Yahoo) entry not found."})
    else:
        checks.append({"name": "mig006_found", "passed": True, "detail": "MIG-006 entry found."})
        total_score += 0.03

        entry_text = json.dumps(entry_006).lower()
        folder_mapping = "folder" in entry_text and ("mapping" in entry_text or "map" in entry_text or "structure" in entry_text or "limit" in entry_text or "subfolder" in entry_text)
        checks.append({"name": "mig006_folder_mapping_risk", "passed": folder_mapping,
                        "detail": f"MIG-006 (Yahoo free with subfolders) should flag folder mapping/limit issues. Found: {folder_mapping}"})
        if folder_mapping: total_score += 0.05

    # ===== CHECK 7: MIG-007 Gina Marsh - ProtonMail (PAID) → Gmail =====
    # CRITICAL DISTINCTION from MIG-003:
    # - Paid plan → ProtonMail Bridge IS available as workaround
    # - But: method is still "Export → Import" (Hard complexity per decision matrix)
    # - Bridge mention should appear for paid plan
    entry_007 = find_entry("MIG-007", "Gina Marsh")
    if entry_007 is None:
        checks.append({"name": "mig007_found", "passed": False, "detail": "MIG-007 (Gina Marsh / ProtonMail paid) entry not found."})
    else:
        checks.append({"name": "mig007_found", "passed": True, "detail": "MIG-007 entry found."})
        total_score += 0.03

        complexity = get_field(entry_007, "complexity", "difficulty", "migration_complexity")
        c_pass = field_contains(complexity, "hard")
        checks.append({"name": "mig007_complexity_hard", "passed": c_pass,
                        "detail": f"ProtonMail→Gmail complexity should be 'Hard'. Got: {complexity}"})
        if c_pass: total_score += 0.05

        # Paid plan: Bridge should be mentioned as available option
        entry_text = json.dumps(entry_007).lower()
        bridge_available = "bridge" in entry_text or "paid" in entry_text
        checks.append({"name": "mig007_paid_bridge_option", "passed": bridge_available,
                        "detail": f"MIG-007 (paid ProtonMail) should note Bridge is available for paid plans. Found: {bridge_available}"})
        if bridge_available: total_score += 0.06

        # Must still flag no-IMAP constraint
        no_imap_flag = "no imap" in entry_text or "encryption" in entry_text or "limited" in entry_text or \
                       "export" in entry_text or "no bulk" in entry_text
        checks.append({"name": "mig007_no_imap_still_flagged", "passed": no_imap_flag,
                        "detail": f"MIG-007 should still note ProtonMail's encryption/no-IMAP constraint. Found: {no_imap_flag}"})
        if no_imap_flag: total_score += 0.04

    # ===== CHECK 8: Global best practices =====
    report_text = json.dumps(report).lower()

    # Planning best practices: pilot users mentioned
    pilot_mentioned = "pilot" in report_text
    checks.append({"name": "global_pilot_testing_mentioned", "passed": pilot_mentioned,
                    "detail": f"Report should mention pilot testing best practice. Found: {pilot_mentioned}"})
    if pilot_mentioned: total_score += 0.03

    # Rollback plan mentioned
    rollback_mentioned = "rollback" in report_text or "roll back" in report_text or "revert" in report_text
    checks.append({"name": "global_rollback_plan_mentioned", "passed": rollback_mentioned,
                    "detail": f"Report should mention rollback plan. Found: {rollback_mentioned}"})
    if rollback_mentioned: total_score += 0.03

    # Validation steps mentioned
    validation_mentioned = "validat" in report_text or "count" in report_text or "verify" in report_text or "integrity" in report_text
    checks.append({"name": "global_validation_mentioned", "passed": validation_mentioned,
                    "detail": f"Report should mention validation/verification steps. Found: {validation_mentioned}"})
    if validation_mentioned: total_score += 0.03

    # Cap score at 1.0
    total_score = min(round(total_score, 4), 1.0)

    # Determine overall pass: need at least 0.65 AND critical ProtonMail checks passed
    proton_checks_passed = all(
        c["passed"] for c in checks
        if c["name"] in ["mig003_complexity_hard", "mig003_no_imap_flagged", "mig007_complexity_hard"]
    )
    passed = total_score >= 0.65 and proton_checks_passed

    return {"passed": passed, "score": total_score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))