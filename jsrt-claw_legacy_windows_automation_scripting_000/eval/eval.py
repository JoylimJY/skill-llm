import sys
import os
import json
import re
from pathlib import Path

def find_target_file(workspace):
    """Find fetch_and_report.js anywhere in workspace."""
    candidates = list(Path(workspace).rglob("fetch_and_report.js"))
    return candidates[0] if candidates else None

def load_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def run_checks(workspace):
    checks = []
    score = 0.0

    # --- CHECK 1: File exists ---
    target = find_target_file(workspace)
    file_exists = target is not None
    checks.append({
        "name": "fetch_and_report.js exists",
        "passed": file_exists,
        "detail": str(target) if file_exists else "File not found anywhere in workspace"
    })
    if not file_exists:
        return checks, 0.0

    try:
        content = load_file(target)
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        return checks, 0.0

    checks.append({"name": "File readable", "passed": True, "detail": f"Read {len(content)} chars"})

    # --- CHECK 2: CreateObject guard pattern ---
    # Must have: if (typeof CreateObject === "undefined") { var CreateObject = function(...
    has_guard = bool(re.search(
        r'if\s*\(\s*typeof\s+CreateObject\s*===?\s*["\']undefined["\']\s*\)',
        content
    ))
    checks.append({
        "name": "CreateObject undefined-guard present",
        "passed": has_guard,
        "detail": "Found required 'if (typeof CreateObject === undefined)' guard" if has_guard else "Missing required CreateObject guard pattern from SKILL.md"
    })

    # --- CHECK 3: CreateObject.make sub-method defined ---
    has_make = bool(re.search(r'CreateObject\.make\s*=\s*function', content))
    checks.append({
        "name": "CreateObject.make sub-method defined",
        "passed": has_make,
        "detail": "Found CreateObject.make = function" if has_make else "Missing CreateObject.make sub-method (required by SKILL.md loader spec)"
    })

    # --- CHECK 4: WScript.CreateObject branch in .make ---
    has_wscript_branch = bool(re.search(r'WScript\.CreateObject\s*\(', content))
    checks.append({
        "name": "WScript.CreateObject branch in loader",
        "passed": has_wscript_branch,
        "detail": "Found WScript.CreateObject path" if has_wscript_branch else "Missing WScript.CreateObject branch in CreateObject.make"
    })

    # --- CHECK 5: ActiveXObject fallback in .make ---
    has_activex = bool(re.search(r'new\s+ActiveXObject\s*\(', content))
    checks.append({
        "name": "ActiveXObject fallback in loader",
        "passed": has_activex,
        "detail": "Found new ActiveXObject(...) fallback" if has_activex else "Missing ActiveXObject fallback in loader"
    })

    # --- CHECK 6: XMLHTTP fallback array with correct order ---
    # Must include at minimum Msxml2.XMLHTTP.6.0 before Msxml2.XMLHTTP.3.0, with Microsoft.XMLHTTP or WinHttp somewhere
    xmlhttp_progids = [
        r'Msxml2\.XMLHTTP\.6\.0',
        r'Msxml2\.XMLHTTP\.3\.0',
        r'Msxml2\.XMLHTTP',
        r'Microsoft\.XMLHTTP',
        r'WinHttp\.WinHttpRequest\.5\.1'
    ]
    found_progids = []
    for pid in xmlhttp_progids:
        if re.search(pid, content):
            found_progids.append(pid.replace('\\', ''))
    
    # Must have at least 3 XMLHTTP ProgIDs in a fallback array
    has_fallback_array = bool(re.search(
        r'\[\s*["\']Msxml2\.XMLHTTP',
        content
    ))
    has_enough_progids = len(found_progids) >= 3
    
    checks.append({
        "name": "XMLHTTP fallback array with multiple ProgIDs",
        "passed": has_fallback_array and has_enough_progids,
        "detail": f"Found fallback array: {has_fallback_array}, ProgIDs present: {found_progids}"
    })

    # --- CHECK 7: Msxml2.XMLHTTP.6.0 appears BEFORE Msxml2.XMLHTTP.3.0 (correct order) ---
    pos_6 = content.find("Msxml2.XMLHTTP.6.0")
    pos_3 = content.find("Msxml2.XMLHTTP.3.0")
    correct_order = (pos_6 != -1 and pos_3 != -1 and pos_6 < pos_3)
    checks.append({
        "name": "XMLHTTP ProgID order: 6.0 before 3.0",
        "passed": correct_order,
        "detail": f"6.0 at pos {pos_6}, 3.0 at pos {pos_3} — {'correct order' if correct_order else 'wrong order or missing'}"
    })

    # --- CHECK 8: getProcessVersion function present ---
    has_version_fn = bool(re.search(r'function\s+getProcessVersion\s*\(', content))
    checks.append({
        "name": "getProcessVersion function defined",
        "passed": has_version_fn,
        "detail": "Found getProcessVersion() function" if has_version_fn else "Missing getProcessVersion() function"
    })

    # --- CHECK 9: WScript.Version in version detection ---
    has_wscript_version = bool(re.search(r'WScript\.Version', content))
    checks.append({
        "name": "WScript.Version used in version detection",
        "passed": has_wscript_version,
        "detail": "Found WScript.Version reference" if has_wscript_version else "Missing WScript.Version in version detection"
    })

    # --- CHECK 10: Polyfill URL with correct version 4.8.0 ---
    has_polyfill_version = bool(re.search(r'4\.8\.0', content))
    checks.append({
        "name": "Polyfill version 4.8.0 in URL",
        "passed": has_polyfill_version,
        "detail": "Found version=4.8.0" if has_polyfill_version else "Missing polyfill version 4.8.0"
    })

    # --- CHECK 11: Polyfill URL with URL-encoded features parameter ---
    # Must use %2C between features (URL-encoded comma), not raw commas
    # features=default%2Ces2015%2Ces6 (order may vary but must be URL-encoded)
    has_url_encoded_features = bool(re.search(
        r'features=[^\s"\']*default[^\s"\']*%2C[^\s"\']*es2015|features=[^\s"\']*es2015[^\s"\']*%2C[^\s"\']*default',
        content, re.IGNORECASE
    ))
    # Also check that raw comma is NOT used between features in the URL
    has_raw_comma_in_features = bool(re.search(
        r'features=[^\s"\'&]*default,[^\s"\'&]*es2015|features=[^\s"\'&]*es2015,[^\s"\']*default',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "Polyfill features URL-encoded with %2C (not raw comma)",
        "passed": has_url_encoded_features and not has_raw_comma_in_features,
        "detail": (
            f"URL-encoded %2C found: {has_url_encoded_features}, "
            f"raw comma used (bad): {has_raw_comma_in_features}"
        )
    })

    # --- CHECK 12: All three features present (default, es2015, es6) ---
    features_content = content.lower()
    has_default = "default" in features_content and "features" in features_content
    has_es2015 = "es2015" in features_content
    has_es6 = "es6" in features_content
    all_features = has_default and has_es2015 and has_es6
    checks.append({
        "name": "All three polyfill features present (default, es2015, es6)",
        "passed": all_features,
        "detail": f"default: {has_default}, es2015: {has_es2015}, es6: {has_es6}"
    })

    # --- CHECK 13: IE 8.0 User-Agent string ---
    # Must match: Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)
    has_ie8_ua = bool(re.search(
        r'Mozilla/4\.0.*compatible.*MSIE\s*8\.0.*Windows NT 6\.1.*Trident/4\.0',
        content
    ))
    checks.append({
        "name": "IE 8.0 User-Agent string (JScript 5.8 compatible)",
        "passed": has_ie8_ua,
        "detail": "Found correct IE8 UA: Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)" if has_ie8_ua else "Missing or incorrect IE8 User-Agent (must match JScript 5.8 / IE 8.0 exactly)"
    })

    # --- CHECK 14: polyfill CDN domain present ---
    has_cdn = bool(re.search(r'cdnjs\.cloudflare\.com/polyfill', content))
    checks.append({
        "name": "Polyfill CDN URL (cdnjs.cloudflare.com/polyfill)",
        "passed": has_cdn,
        "detail": "Found correct CDN domain" if has_cdn else "Missing polyfill CDN URL"
    })

    # --- CHECK 15: Scripting.FileSystemObject used for file writing ---
    has_fso = bool(re.search(r'Scripting\.FileSystemObject', content))
    checks.append({
        "name": "Scripting.FileSystemObject used for file I/O",
        "passed": has_fso,
        "detail": "Found Scripting.FileSystemObject" if has_fso else "Missing Scripting.FileSystemObject for disk output"
    })

    # --- CHECK 16: Output path C:\automation\status_report.json referenced ---
    has_output_path = bool(re.search(
        r'C:\\\\automation\\\\status_report\.json|C:\\automation\\status_report\.json',
        content
    )) or ("status_report.json" in content and ("automation" in content or "C:\\" in content))
    checks.append({
        "name": "Output path references status_report.json",
        "passed": has_output_path,
        "detail": "Found status_report.json path reference" if has_output_path else "Missing output path C:\\automation\\status_report.json"
    })

    # --- CHECK 17: CreateObject used (not raw new ActiveXObject) for COM instantiation in main logic ---
    # The main COM object creations (not inside .make) should use CreateObject(...)
    # Count uses of CreateObject([...]) array pattern
    has_createobject_array_call = bool(re.search(
        r'CreateObject\s*\(\s*\[',
        content
    ))
    checks.append({
        "name": "CreateObject([...]) array call used for COM instantiation",
        "passed": has_createobject_array_call,
        "detail": "Found CreateObject([...]) fallback-array call" if has_createobject_array_call else "Missing CreateObject([...]) call — agent should use the fallback loader, not raw new ActiveXObject"
    })

    # --- Scoring ---
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 4)

    return checks, score

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "Evaluation runner", "passed": False, "detail": f"Unexpected error: {e}"}]
        }
        print(json.dumps(result))
        return

    passed_checks = sum(1 for c in checks if c["passed"])
    total = len(checks)
    overall_passed = score >= 0.75 and checks[0]["passed"]  # Must at least find file and pass 75%

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()