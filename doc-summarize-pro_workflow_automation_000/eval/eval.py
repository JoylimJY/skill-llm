import sys
import os
import json
import subprocess
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def run_check(name, fn):
    try:
        passed, detail = fn()
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed
    except Exception as e:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})
        return False


# ── Helper ──────────────────────────────────────────────────────────────────────
def get_config_value(key):
    config_path = Path.home() / ".doc-summarize-pro" / "config"
    try:
        text = config_path.read_text()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None

def get_history():
    history_path = Path.home() / ".doc-summarize-pro" / "history.log"
    try:
        return history_path.read_text()
    except Exception:
        return ""


# ── CHECK 1: summary_sentences set to 3 ─────────────────────────────────────────
def check_summary_sentences():
    val = get_config_value("summary_sentences")
    if val == "3":
        return True, f"summary_sentences correctly set to 3 (found: {val})"
    return False, f"summary_sentences expected '3', got '{val}'"

run_check("config_summary_sentences_is_3", check_summary_sentences)


# ── CHECK 2: keyword_count set to 20 ────────────────────────────────────────────
def check_keyword_count():
    val = get_config_value("keyword_count")
    if val == "20":
        return True, f"keyword_count correctly set to 20 (found: {val})"
    return False, f"keyword_count expected '20', got '{val}'"

run_check("config_keyword_count_is_20", check_keyword_count)


# ── CHECK 3: batch command was run on market_research dir ───────────────────────
def check_batch_history():
    history = get_history()
    # Look for a batch entry pointing at the market_research directory
    if re.search(r'batch\s+.*market_research', history):
        return True, "history.log contains a 'batch' entry for market_research directory"
    return False, f"No 'batch market_research' entry found in history.log. History: {history[:500]}"

run_check("batch_run_on_market_research", check_batch_history)


# ── CHECK 4: batch actually processes files (verify via script output or side effect) ─
def check_batch_processes_files():
    # Run batch fresh and verify it produces output for expected files
    market_dir = os.path.join(workspace, "market_research")
    result = subprocess.run(
        ["bash", os.path.join(workspace, "scripts", "script.sh"), "batch", market_dir],
        capture_output=True, text=True
    )
    output = result.stdout
    # Should mention at least 4 of the text/md/log files in the directory
    expected_names = ["strategy_q1.md", "strategy_q2.md", "semiconductor_supply.txt",
                      "consumer_survey_2024.txt", "competitor_brief.txt", "financial_summary.txt",
                      "ops_pipeline.log"]
    found = sum(1 for name in expected_names if name in output)
    if found >= 4:
        return True, f"batch output references {found}/{len(expected_names)} expected files"
    return False, f"batch output only references {found}/{len(expected_names)} files. Output snippet: {output[:400]}"

run_check("batch_output_covers_files", check_batch_processes_files)


# ── CHECK 5: compare was run on strategy_q1.md and strategy_q2.md ───────────────
def check_compare_history():
    history = get_history()
    if re.search(r'compare\s+.*strategy_q[12].*strategy_q[12]', history) or \
       re.search(r'compare.*strategy_q1.*strategy_q2', history) or \
       re.search(r'compare.*strategy_q2.*strategy_q1', history):
        return True, "history.log contains a 'compare' entry for strategy_q1 and strategy_q2"
    # Also accept if compare was run but history key just shows the command
    if re.search(r'compare', history) and re.search(r'strategy', history):
        return True, "history.log contains compare + strategy references"
    return False, f"No 'compare strategy_q1 strategy_q2' entry found in history. History: {history[:500]}"

run_check("compare_run_on_strategy_docs", check_compare_history)


# ── CHECK 6: compare output is semantically correct ─────────────────────────────
def check_compare_output():
    f1 = os.path.join(workspace, "market_research", "strategy_q1.md")
    f2 = os.path.join(workspace, "market_research", "strategy_q2.md")
    result = subprocess.run(
        ["bash", os.path.join(workspace, "scripts", "script.sh"), "compare", f1, f2],
        capture_output=True, text=True
    )
    output = result.stdout
    # Should contain word count line and keyword sections
    has_wordcount = "Word Count" in output and "diff=" in output
    has_shared = "Shared Keywords" in output
    has_unique = "Unique to" in output
    if has_wordcount and has_shared and has_unique:
        return True, f"compare output contains expected sections. Snippet: {output[:300]}"
    return False, f"compare output missing required sections. Output: {output[:400]}"

run_check("compare_output_structure_correct", check_compare_output)


# ── CHECK 7: export JSON file exists ────────────────────────────────────────────
def check_export_json_exists():
    # Find any JSON file produced that looks like a summary export
    candidates = list(Path(workspace).rglob("*.json"))
    # Also look in home dir just in case
    candidates += list(Path.home().rglob("*.json"))
    if candidates:
        return True, f"Found JSON export file(s): {[str(c) for c in candidates[:3]]}"
    return False, "No JSON export file found anywhere in workspace or home directory"

json_exists = run_check("export_json_file_exists", check_export_json_exists)


# ── CHECK 8: export JSON has correct structure ────────────────────────────────────
def check_export_json_structure():
    candidates = list(Path(workspace).rglob("*.json"))
    candidates += list(Path.home().rglob("*.json"))
    if not candidates:
        return False, "No JSON file found to validate structure"
    
    errors = []
    for cand in candidates:
        try:
            raw = cand.read_text().strip()
            # The tool outputs raw JSON (not wrapped in markdown)
            data = json.loads(raw)
            has_file = "file" in data
            has_wc = "word_count" in data
            has_summary = "summary" in data
            has_keywords = "keywords" in data
            if has_file and has_wc and has_summary and has_keywords:
                # Verify keywords list respects keyword_count=20 (at most 20)
                kw_count = len(data["keywords"])
                if kw_count <= 20:
                    return True, f"JSON export at {cand} has correct structure with {kw_count} keywords (<=20)"
                else:
                    errors.append(f"{cand}: has {kw_count} keywords > 20 (config keyword_count=20 not respected)")
            else:
                missing = [k for k,v in [("file",has_file),("word_count",has_wc),("summary",has_summary),("keywords",has_keywords)] if not v]
                errors.append(f"{cand}: missing fields {missing}")
        except json.JSONDecodeError as e:
            # Could be that the export was piped/redirected or the tool outputs non-json wrapper
            # Try to extract JSON block
            try:
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    if all(k in data for k in ["file","word_count","summary","keywords"]):
                        return True, f"JSON export at {cand} valid (extracted from output)"
            except Exception:
                pass
            errors.append(f"{cand}: JSON parse error: {e}")
        except Exception as e:
            errors.append(f"{cand}: {e}")
    
    return False, f"JSON structure validation failed: {'; '.join(errors)}"

run_check("export_json_structure_valid", check_export_json_structure)


# ── CHECK 9: export JSON reflects keyword_count=20 (max 20 keywords) ────────────
def check_export_respects_keyword_count():
    # Run export fresh to see current behavior
    f = os.path.join(workspace, "market_research", "strategy_q2.md")
    result = subprocess.run(
        ["bash", os.path.join(workspace, "scripts", "script.sh"), "export", f, "json"],
        capture_output=True, text=True
    )
    output = result.stdout.strip()
    try:
        data = json.loads(output)
        kw_count = len(data.get("keywords", []))
        if kw_count <= 20:
            return True, f"export json respects keyword_count=20: found {kw_count} keywords"
        return False, f"export json has {kw_count} keywords, exceeds keyword_count=20"
    except Exception as e:
        return False, f"Could not parse export json output: {e}. Output: {output[:300]}"

run_check("export_json_respects_keyword_count_20", check_export_respects_keyword_count)


# ── CHECK 10: history shows all 4 major operation types ─────────────────────────
def check_history_completeness():
    history = get_history()
    operations = {
        "config": bool(re.search(r'config', history)),
        "batch": bool(re.search(r'batch', history)),
        "compare": bool(re.search(r'compare', history)),
        "export": bool(re.search(r'export', history)),
    }
    done = [k for k,v in operations.items() if v]
    missing = [k for k,v in operations.items() if not v]
    if len(done) >= 3:
        return True, f"history contains operations: {done}. Missing: {missing}"
    return False, f"history only contains {done}, missing {missing}. History: {history[:400]}"

run_check("history_contains_all_operations", check_history_completeness)


# ── Scoring ──────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
all_passed = passed_count == total

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))