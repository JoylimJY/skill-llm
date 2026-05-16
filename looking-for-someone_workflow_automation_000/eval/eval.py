import sys
import json
import os
import re
from pathlib import Path

def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_cases_dir():
    """Find the data directory where cases are stored."""
    candidates = [
        Path.home() / ".openclaw" / "skills-data" / "looking-for-someone",
        Path("/root/.openclaw/skills-data/looking-for-someone"),
        Path("/home") / os.environ.get("USER", "root") / ".openclaw" / "skills-data" / "looking-for-someone",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def run_checks(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # ── Check 1: Data directory exists ────────────────────────────────────────
    cases_dir = find_cases_dir()
    check1_passed = cases_dir is not None and cases_dir.exists()
    checks.append({
        "name": "data_directory_exists",
        "passed": check1_passed,
        "detail": f"Cases data dir found at: {cases_dir}" if check1_passed else "Could not find ~/.openclaw/skills-data/looking-for-someone/"
    })
    if not check1_passed:
        # Can't do further file-based checks
        for name in ["case_created_with_correct_fields", "case_contains_person_name", 
                     "case_contains_last_seen_date", "case_has_clue_recorded",
                     "wechat_notice_generated"]:
            checks.append({"name": name, "passed": False, "detail": "Data directory not found"})
        total = sum(1 for c in checks if c["passed"])
        return {"passed": False, "score": total / len(checks), "checks": checks}

    # ── Collect all case JSON files (excluding the stale archive) ─────────────
    case_files = [
        f for f in cases_dir.glob("*.json")
        if f.name != "ARCHIVE_2023.json"
    ]
    # Also check for subdirectory structures some implementations use
    case_files += [
        f for f in cases_dir.rglob("*.json")
        if f.name != "ARCHIVE_2023.json" and f.parent != cases_dir
    ]

    # ── Check 2: At least one new case was created ─────────────────────────────
    # Filter to only cases that look like newly created ones (not the stale one)
    new_cases = []
    for f in case_files:
        try:
            data = load_json_file(f)
            # It might be a list of cases or a single case object
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("id") != "STALE-0001":
                        new_cases.append(item)
            elif isinstance(data, dict):
                if data.get("id") != "STALE-0001":
                    new_cases.append(data)
        except Exception as e:
            pass

    check2_passed = len(new_cases) >= 1
    checks.append({
        "name": "case_created_with_correct_fields",
        "passed": check2_passed,
        "detail": f"Found {len(new_cases)} new case(s) in data directory" if check2_passed else "No new cases found in data directory"
    })

    if not check2_passed:
        for name in ["case_contains_person_name", "case_contains_last_seen_date",
                     "case_has_clue_recorded", "wechat_notice_generated"]:
            checks.append({"name": name, "passed": False, "detail": "No new case found"})
        total = sum(1 for c in checks if c["passed"])
        return {"passed": False, "score": total / len(checks), "checks": checks}

    # Pick the most relevant case (newest or the one with Wang Jianguo)
    target_case = None
    for case in new_cases:
        name_val = case.get("name", "")
        if "Wang" in str(name_val) or "王" in str(name_val) or "Jianguo" in str(name_val) or "建国" in str(name_val):
            target_case = case
            break
    if target_case is None:
        target_case = new_cases[-1]  # fallback: last case

    # ── Check 3: Case contains the person's name ───────────────────────────────
    name_val = str(target_case.get("name", ""))
    check3_passed = bool(name_val) and name_val not in ("", "undefined", "null")
    checks.append({
        "name": "case_contains_person_name",
        "passed": check3_passed,
        "detail": f"name field value: '{name_val}'"
    })

    # ── Check 4: Case contains lastSeenDate (the proprietary camelCase field) ──
    # The skill uses camelCase: lastSeenDate, lastSeenLocation (NOT last_seen, date_last_seen)
    last_seen_date = target_case.get("lastSeenDate", "") or target_case.get("last_seen_date", "")
    last_seen_loc = target_case.get("lastSeenLocation", "") or target_case.get("last_seen_location", "")
    check4_passed = bool(last_seen_date) and bool(last_seen_loc)
    checks.append({
        "name": "case_contains_last_seen_date_and_location",
        "passed": check4_passed,
        "detail": f"lastSeenDate='{last_seen_date}', lastSeenLocation='{last_seen_loc}'"
    })

    # ── Check 5: A clue has been recorded for this case ────────────────────────
    case_id = target_case.get("id", "")
    clues = target_case.get("clues", [])
    
    # Some implementations store clues inline; others write separate files
    clue_found_inline = isinstance(clues, list) and len(clues) >= 1
    
    # Check for separate clue files referencing the case ID
    clue_found_external = False
    if case_id:
        for f in cases_dir.rglob("*"):
            if f.is_file() and case_id in f.name and "clue" in f.name.lower():
                clue_found_external = True
                break
            try:
                if f.is_file() and f.suffix == ".json" and f != Path(cases_dir / f"{case_id}.json"):
                    d = load_json_file(f)
                    if isinstance(d, dict) and d.get("caseId") == case_id:
                        clue_found_external = True
                        break
                    if isinstance(d, list):
                        for item in d:
                            if isinstance(item, dict) and item.get("caseId") == case_id:
                                clue_found_external = True
                                break
            except Exception:
                pass

    check5_passed = clue_found_inline or clue_found_external
    clue_detail = f"Inline clues count: {len(clues)}"
    if clue_found_external:
        clue_detail += "; external clue file found"
    checks.append({
        "name": "case_has_clue_recorded",
        "passed": check5_passed,
        "detail": clue_detail
    })

    # ── Check 6: A WeChat-platform notice was generated ────────────────────────
    # The agent must have run: node scripts/cli.js 启事 <id> wechat
    # Evidence: a notice file saved somewhere, OR stdout captured to a file
    # We search for any file containing WeChat-specific markers
    wechat_notice_found = False
    wechat_notice_detail = "No WeChat notice output file found"

    notice_search_dirs = [
        workspace,
        cases_dir,
        Path("/tmp"),
        Path("/root"),
    ]

    wechat_keywords = ["微信", "wechat", "朋友圈", "转发", "寻人"]
    notice_candidate_files = []
    for search_dir in notice_search_dirs:
        if search_dir.exists():
            for f in search_dir.rglob("*"):
                if f.is_file() and f.suffix in (".txt", ".json", ".md", ".out", ".log", ""):
                    if any(kw in f.name.lower() for kw in ["notice", "启事", "wechat", "output", "result"]):
                        notice_candidate_files.append(f)

    # Also check if the case record itself has a notices field
    notices_in_case = target_case.get("notices", []) or target_case.get("notice", "")
    if notices_in_case:
        content = json.dumps(notices_in_case, ensure_ascii=False)
        if any(kw in content.lower() for kw in ["wechat", "微信", "朋友圈"]):
            wechat_notice_found = True
            wechat_notice_detail = "WeChat notice found inside case record"

    if not wechat_notice_found:
        for nf in notice_candidate_files:
            try:
                content = nf.read_text(encoding='utf-8', errors='ignore')
                if any(kw in content for kw in wechat_keywords):
                    wechat_notice_found = True
                    wechat_notice_detail = f"WeChat notice content found in: {nf}"
                    break
            except Exception:
                pass

    # Broader search: any recently written file anywhere in workspace or home
    if not wechat_notice_found:
        for search_dir in [workspace, cases_dir, Path("/root"), Path("/tmp")]:
            if not search_dir.exists():
                continue
            for f in search_dir.rglob("*"):
                if f.is_file() and f.suffix in (".txt", ".json", ".md"):
                    try:
                        content = f.read_text(encoding='utf-8', errors='ignore')
                        if any(kw in content for kw in wechat_keywords) and ("王" in content or "Wang" in content or "建国" in content or "Jianguo" in content):
                            wechat_notice_found = True
                            wechat_notice_detail = f"WeChat notice with person info found in: {f}"
                            break
                    except Exception:
                        pass
            if wechat_notice_found:
                break

    checks.append({
        "name": "wechat_notice_generated",
        "passed": wechat_notice_found,
        "detail": wechat_notice_detail
    })

    # ── Final scoring ──────────────────────────────────────────────────────────
    num_passed = sum(1 for c in checks if c["passed"])
    score = num_passed / len(checks)
    overall_passed = num_passed >= 5  # must pass at least 5 of 6

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace/looking-for-someone"
    try:
        result = run_checks(workspace_dir)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))