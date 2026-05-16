import sys
import json
import os
from pathlib import Path

def load_report(workspace):
    """Find moderation_report.json anywhere in workspace."""
    matches = list(Path(workspace).rglob("moderation_report.json"))
    if not matches:
        return None, "moderation_report.json not found anywhere in workspace"
    # prefer the closest to workspace root
    matches.sort(key=lambda p: len(p.parts))
    return matches[0], None

def run_eval(workspace):
    checks = []
    
    # ── Check 1: File exists ────────────────────────────────────────────────
    report_path, err = load_report(workspace)
    file_found = report_path is not None
    checks.append({
        "name": "moderation_report.json exists",
        "passed": file_found,
        "detail": str(report_path) if file_found else err
    })
    if not file_found:
        return checks

    # ── Load JSON ───────────────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "report is valid JSON", "passed": False, "detail": str(e)})
        return checks

    checks.append({"name": "report is valid JSON", "passed": True, "detail": f"Loaded from {report_path}"})

    # ── Check 2: Only flagged entries returned (ids 6-12, 16-18) ────────────
    # Clean IDs that must NOT appear: 1-5, 13-15, 19-20
    # Flagged IDs that MUST appear (at minimum the obvious ones):
    MUST_FLAG   = {6, 7, 8, 9, 16, 17, 18}   # clear leetspeak/profanity
    MUST_CLEAN  = {1, 2, 3, 4, 5, 13, 14, 15, 19, 20}  # clearly clean

    # The report can be a list or a dict with a list
    entries = report if isinstance(report, list) else report.get("flagged", report.get("results", report.get("comments", [])))

    try:
        reported_ids = set()
        for entry in entries:
            if isinstance(entry, dict):
                # id could be at top level or nested
                eid = entry.get("id") or entry.get("comment", {}).get("id")
                if eid is not None:
                    reported_ids.add(int(eid))
    except Exception as e:
        checks.append({"name": "entries parseable", "passed": False, "detail": str(e)})
        return checks

    checks.append({"name": "entries parseable", "passed": True, "detail": f"Reported IDs: {sorted(reported_ids)}"})

    # All must-flag IDs are present
    missing_flags = MUST_FLAG - reported_ids
    all_flagged_present = len(missing_flags) == 0
    checks.append({
        "name": "all obvious profane comments flagged (ids 6,7,8,9,16,17,18)",
        "passed": all_flagged_present,
        "detail": f"Missing from report: {missing_flags}" if not all_flagged_present else "All present"
    })

    # Clean IDs must NOT appear
    wrongly_flagged = MUST_CLEAN & reported_ids
    no_false_positives = len(wrongly_flagged) == 0
    checks.append({
        "name": "clean comments not wrongly flagged (ids 1-5,13-15,19-20)",
        "passed": no_false_positives,
        "detail": f"Wrongly flagged: {wrongly_flagged}" if not no_false_positives else "No false positives"
    })

    # ── Check 3: Censored text uses preserveFirstLetter format (f***, s***, etc.) ──
    # We look for at least some entries where the censored text starts with
    # the first letter of the profane word followed by asterisks
    first_letter_pattern_found = False
    censored_texts = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        # censored version could be in multiple keys
        for key in ("processedText", "processed_text", "censored", "censoredText", "text"):
            val = entry.get(key, "")
            if val and isinstance(val, str):
                censored_texts.append(val)
        # also check nested result object
        for rkey in ("result", "moderation", "check"):
            sub = entry.get(rkey, {})
            if isinstance(sub, dict):
                for key in ("processedText", "processed_text", "censored"):
                    val = sub.get(key, "")
                    if val and isinstance(val, str):
                        censored_texts.append(val)

    import re
    # Pattern: a letter followed by 2+ asterisks (e.g., f***, s****, b****)
    first_letter_re = re.compile(r'\b[a-zA-Z]\*{2,}')
    for ct in censored_texts:
        if first_letter_re.search(ct):
            first_letter_pattern_found = True
            break

    checks.append({
        "name": "censored text uses preserveFirstLetter format (e.g., f***, s***)",
        "passed": first_letter_pattern_found,
        "detail": f"Sample censored texts: {censored_texts[:4]}" if censored_texts else "No censored text fields found in report"
    })

    # ── Check 4: profaneWords / detected words list present ─────────────────
    has_detected_words = False
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for key in ("profaneWords", "profane_words", "detectedWords", "detected_words", "words"):
            val = entry.get(key)
            if val and isinstance(val, list) and len(val) > 0:
                has_detected_words = True
                break
        for rkey in ("result", "moderation", "check"):
            sub = entry.get(rkey, {})
            if isinstance(sub, dict):
                for key in ("profaneWords", "profane_words", "detectedWords"):
                    val = sub.get(key)
                    if val and isinstance(val, list) and len(val) > 0:
                        has_detected_words = True

    checks.append({
        "name": "detected/profane words list present in flagged entries",
        "passed": has_detected_words,
        "detail": "Found profaneWords arrays in entries" if has_detected_words else "No profaneWords/detectedWords arrays found"
    })

    # ── Check 5: leetspeak entries (8: f4ck, 7: sh1t) actually caught ───────
    # We already checked via MUST_FLAG but let's also verify unicode entry 10 or 11
    unicode_ids = {10, 11}
    unicode_caught = bool(unicode_ids & reported_ids)
    checks.append({
        "name": "Unicode homoglyph evasion comments caught (id 10 or 11)",
        "passed": unicode_caught,
        "detail": f"Unicode IDs in report: {unicode_ids & reported_ids}" if unicode_caught else "Neither Unicode evasion comment (id 10, 11) was caught"
    })

    # ── Check 6: The script used batchCheck or batch approach (not just loop) ──
    # We detect this by looking for a JS or TS file in workspace that imports batchCheck
    # or calls batchCheck — this confirms the agent used the right API
    batch_api_used = False
    batch_detail = "No script found using batchCheck"
    script_files = list(Path(workspace).rglob("*.js")) + list(Path(workspace).rglob("*.ts")) + list(Path(workspace).rglob("*.mjs"))
    # exclude node_modules
    script_files = [f for f in script_files if "node_modules" not in str(f)]
    for sf in script_files:
        try:
            content = sf.read_text(errors="ignore")
            if "batchCheck" in content:
                batch_api_used = True
                batch_detail = f"batchCheck found in {sf}"
                break
        except Exception:
            pass
    checks.append({
        "name": "batchCheck API used in moderation script",
        "passed": batch_api_used,
        "detail": batch_detail
    })

    # ── Check 7: leetspeakLevel aggressive or at least detectLeetspeak used ──
    leet_config_used = False
    leet_detail = "No script found with leetspeak configuration"
    for sf in script_files:
        try:
            content = sf.read_text(errors="ignore")
            if "detectLeetspeak" in content or "detect_leetspeak" in content:
                leet_config_used = True
                if "aggressive" in content:
                    leet_detail = f"detectLeetspeak + aggressive level found in {sf}"
                else:
                    leet_detail = f"detectLeetspeak found in {sf} (aggressive level not confirmed)"
                break
        except Exception:
            pass
    checks.append({
        "name": "leetspeak detection configured in moderation script",
        "passed": leet_config_used,
        "detail": leet_detail
    })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks = run_eval(workspace)
    except Exception as e:
        checks = [{"name": "eval_runner", "passed": False, "detail": f"Unhandled error: {e}"}]

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = (passed_count == total)

    output = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()