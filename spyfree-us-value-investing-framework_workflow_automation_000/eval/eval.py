import sys
import json
import os
from pathlib import Path

def check(name, condition, detail):
    return {"name": name, "passed": bool(condition), "detail": detail}

def load_json(path):
    with open(path) as f:
        return json.load(f)

def main():
    workspace = sys.argv[1]
    ws = Path(workspace)
    checks = []

    # ── Expected ground truth ────────────────────────────────────────────────
    expected = {
        "BRND": {
            "rating": "A",
            "passes": 4,
            "rules": {
                "roe": True,
                "leverage": True,
                "cash_conversion": True,
                "moat": True,
            },
        },
        "NETW": {
            "rating": "B",
            "passes": 3,
            "rules": {
                "roe": True,      # max consecutive run = 3 (indices 1-3)
                "leverage": False, # 0.53 >= 0.50
                "cash_conversion": True,  # 850/1000 = 85% > 80%
                "moat": True,
            },
        },
        "COMM": {
            "rating": "C",
            "passes": 2,
            "rules": {
                "roe": False,     # broken run: max consecutive = 2
                "leverage": True,  # 0.44 < 0.50
                "cash_conversion": False,  # 800/1000 = exactly 80%, NOT > 80%
                "moat": True,
            },
        },
    }

    # ── Locate output files for each ticker ──────────────────────────────────
    # Agent may place them at .state/BRND/eval.json, .state/eval_BRND.json, etc.
    # We search broadly but require both a .json and a .md per ticker.

    def find_ticker_files(ticker):
        """Find JSON and MD evaluation output files for a given ticker."""
        json_candidates = list(ws.rglob(f"*{ticker}*.json")) + \
                          list(ws.rglob(f"*{ticker.lower()}*.json"))
        md_candidates   = list(ws.rglob(f"*{ticker}*.md")) + \
                          list(ws.rglob(f"*{ticker.lower()}*.md"))
        # exclude input files
        json_candidates = [p for p in json_candidates
                           if "filings" not in str(p) and "template" not in str(p)
                           and "archive" not in str(p)]
        md_candidates   = [p for p in md_candidates
                           if "archive" not in str(p) and "SKILL" not in str(p)]
        return json_candidates, md_candidates

    all_passed = True

    for ticker, exp in expected.items():
        json_files, md_files = find_ticker_files(ticker)

        # ── JSON output exists? ───────────────────────────────────────────
        json_exists = len(json_files) > 0
        checks.append(check(
            f"{ticker}: JSON output file exists",
            json_exists,
            f"Found: {[str(p) for p in json_files]}" if json_files else "No JSON file found for ticker."
        ))
        if not json_exists:
            all_passed = False
            # Add placeholder failures for downstream checks
            for rule in ["rating", "passes", "roe_rule", "leverage_rule", "cash_rule", "moat_rule"]:
                checks.append(check(f"{ticker}: {rule}", False, "Skipped — JSON file missing."))
            checks.append(check(f"{ticker}: Markdown output file exists", False, "Skipped — no outputs found."))
            checks.append(check(f"{ticker}: Markdown has bilingual content", False, "Skipped."))
            continue

        # ── Parse JSON ───────────────────────────────────────────────────
        try:
            result = load_json(json_files[0])
        except Exception as e:
            checks.append(check(f"{ticker}: JSON is valid", False, str(e)))
            all_passed = False
            continue

        # Rating
        rating_ok = result.get("rating") == exp["rating"]
        checks.append(check(
            f"{ticker}: Rating is {exp['rating']}",
            rating_ok,
            f"Got rating='{result.get('rating')}', expected='{exp['rating']}'"
        ))
        if not rating_ok:
            all_passed = False

        # Passes count
        passes_ok = result.get("passes") == exp["passes"]
        checks.append(check(
            f"{ticker}: Passes count is {exp['passes']}",
            passes_ok,
            f"Got passes={result.get('passes')}, expected={exp['passes']}"
        ))
        if not passes_ok:
            all_passed = False

        # Individual rule results
        rules_data = result.get("rules", {})
        for rule_key, exp_pass in exp["rules"].items():
            rule_result = rules_data.get(rule_key, {})
            got_pass = rule_result.get("pass")
            ok = (got_pass == exp_pass)
            checks.append(check(
                f"{ticker}: Rule '{rule_key}' pass={exp_pass}",
                ok,
                f"Got pass={got_pass}, expected pass={exp_pass}. Detail: {rule_result.get('detail', 'N/A')}"
            ))
            if not ok:
                all_passed = False

        # ── Markdown output exists? ───────────────────────────────────────
        md_exists = len(md_files) > 0
        checks.append(check(
            f"{ticker}: Markdown output file exists",
            md_exists,
            f"Found: {[str(p) for p in md_files]}" if md_files else "No .md file found for ticker."
        ))
        if not md_exists:
            all_passed = False
            checks.append(check(f"{ticker}: Markdown has bilingual content", False, "Skipped — MD file missing."))
            continue

        # ── Bilingual content check ───────────────────────────────────────
        try:
            md_content = md_files[0].read_text(encoding="utf-8")
            # Must contain Chinese characters (中文摘要 section)
            has_chinese = any('\u4e00' <= ch <= '\u9fff' for ch in md_content)
            # Must contain the rating letter
            has_rating = f"**{exp['rating']}**" in md_content or f": {exp['rating']}" in md_content
            bilingual_ok = has_chinese and has_rating
            checks.append(check(
                f"{ticker}: Markdown has bilingual content (EN+中文) and correct rating",
                bilingual_ok,
                f"has_chinese={has_chinese}, has_rating_letter={has_rating}"
            ))
            if not bilingual_ok:
                all_passed = False
        except Exception as e:
            checks.append(check(f"{ticker}: Markdown readable", False, str(e)))
            all_passed = False

    # ── Critical proprietary edge-case spot checks ────────────────────────────

    # COMM: FCF=800, NI=1000 → exactly 80% → must FAIL (strict >)
    comm_json_files, _ = find_ticker_files("COMM")
    if comm_json_files:
        try:
            comm_result = load_json(comm_json_files[0])
            cash_rule_pass = comm_result.get("rules", {}).get("cash_conversion", {}).get("pass", True)
            strict_fcf_ok = (cash_rule_pass == False)
            checks.append(check(
                "COMM: FCF exactly 80% of NI correctly FAILS strict '>' threshold",
                strict_fcf_ok,
                f"cash_conversion.pass={cash_rule_pass}. Must be False because 800/1000=80% is NOT > 80% (strict greater-than required)."
            ))
            if not strict_fcf_ok:
                all_passed = False
        except Exception as e:
            checks.append(check("COMM: FCF strict threshold check", False, str(e)))
            all_passed = False

    # NETW: ROE [0.14, 0.18, 0.19, 0.22] — first year breaks run, but 3 consecutive years exist
    netw_json_files, _ = find_ticker_files("NETW")
    if netw_json_files:
        try:
            netw_result = load_json(netw_json_files[0])
            netw_roe_pass = netw_result.get("rules", {}).get("roe", {}).get("pass", False)
            consecutive_ok = (netw_roe_pass == True)
            checks.append(check(
                "NETW: ROE correctly PASSES despite year-1 dip (3 consecutive years found in years 2-4)",
                consecutive_ok,
                f"roe.pass={netw_roe_pass}. ROE=[0.14,0.18,0.19,0.22]: year1=0.14 fails, but years 2-4 form a 3-year consecutive run."
            ))
            if not consecutive_ok:
                all_passed = False
        except Exception as e:
            checks.append(check("NETW: ROE consecutive run check", False, str(e)))
            all_passed = False

    # COMM: ROE [0.20, 0.12, 0.18, 0.19] — broken by year2=0.12, max run=2 → must FAIL
    if comm_json_files:
        try:
            comm_result2 = load_json(comm_json_files[0])
            comm_roe_pass = comm_result2.get("rules", {}).get("roe", {}).get("pass", True)
            broken_run_ok = (comm_roe_pass == False)
            checks.append(check(
                "COMM: ROE correctly FAILS due to broken consecutive run (year2=0.12 breaks chain)",
                broken_run_ok,
                f"roe.pass={comm_roe_pass}. ROE=[0.20,0.12,0.18,0.19]: year2=0.12<15% breaks the run, max consecutive=2."
            ))
            if not broken_run_ok:
                all_passed = False
        except Exception as e:
            checks.append(check("COMM: ROE broken run check", False, str(e)))
            all_passed = False

    # ── Score ────────────────────────────────────────────────────────────────
    n = len(checks)
    n_passed = sum(1 for c in checks if c["passed"])
    score = round(n_passed / n, 4) if n > 0 else 0.0

    output = {
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()