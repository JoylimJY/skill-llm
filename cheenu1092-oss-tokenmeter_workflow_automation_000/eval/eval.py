import sys
import json
import sqlite3
import os
from pathlib import Path

def find_output_file(workspace: Path) -> Path | None:
    """Search for the cost_audit_feb2026.json file anywhere in workspace."""
    candidates = list(workspace.rglob("cost_audit_feb2026.json"))
    if candidates:
        return candidates[0]
    return None

def get_db_path() -> Path:
    return Path.home() / ".tokenmeter" / "usage.db"

def get_db_records():
    """Query the tokenmeter SQLite database for all records."""
    db_path = get_db_path()
    if not db_path.exists():
        return None, "Database not found at ~/.tokenmeter/usage.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        
        # Try to get all usage records
        usage_data = []
        for table in tables:
            try:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                for row in rows:
                    usage_data.append(dict(zip(cols, row)))
            except Exception as e:
                pass
        conn.close()
        return usage_data, None
    except Exception as e:
        return None, str(e)

# Pricing table from SKILL.md
PRICING = {
    "claude-opus-4":    {"input": 15.0,  "output": 75.0, "cache_write": 18.75, "cache_read": 1.50},
    "claude-sonnet-4":  {"input": 3.0,   "output": 15.0, "cache_write": 3.75,  "cache_read": 0.30},
    "claude-3.5-haiku": {"input": 0.80,  "output": 4.0,  "cache_write": 1.00,  "cache_read": 0.08},
}

# Pre-computed expected values (from gen_inputs_script calculations)
SESSIONS = [
    # legalbot
    {"model": "claude-opus-4",    "input": 2500,  "output": 1200, "cache_write": 45000, "cache_read": 0},
    {"model": "claude-opus-4",    "input": 800,   "output": 2100, "cache_write": 0,     "cache_read": 42000},
    {"model": "claude-sonnet-4",  "input": 3200,  "output": 1800, "cache_write": 28000, "cache_read": 0},
    {"model": "claude-opus-4",    "input": 1100,  "output": 3400, "cache_write": 0,     "cache_read": 89000},
    {"model": "claude-sonnet-4",  "input": 4500,  "output": 900,  "cache_write": 62000, "cache_read": 155000},
    {"model": "claude-3.5-haiku", "input": 12000, "output": 4500, "cache_write": 8000,  "cache_read": 35000},
    # researchbot
    {"model": "claude-sonnet-4",  "input": 5600,  "output": 7200, "cache_write": 95000, "cache_read": 0},
    {"model": "claude-sonnet-4",  "input": 2200,  "output": 8900, "cache_write": 0,     "cache_read": 91000},
    {"model": "claude-opus-4",    "input": 3800,  "output": 5500, "cache_write": 72000, "cache_read": 215000},
    {"model": "claude-3.5-haiku", "input": 18000, "output": 12000,"cache_write": 25000, "cache_read": 180000},
    {"model": "claude-sonnet-4",  "input": 6700,  "output": 9300, "cache_write": 88000, "cache_read": 302000},
]

def calc_cost(model, input_t, output_t, cache_w, cache_r):
    p = PRICING[model]
    return (input_t * p["input"] + output_t * p["output"] +
            cache_w * p["cache_write"] + cache_r * p["cache_read"]) / 1_000_000

# Compute ground truth
expected_total = sum(calc_cost(s["model"], s["input"], s["output"], s["cache_write"], s["cache_read"]) for s in SESSIONS)
expected_by_model = {}
for s in SESSIONS:
    m = s["model"]
    c = calc_cost(s["model"], s["input"], s["output"], s["cache_write"], s["cache_read"])
    expected_by_model[m] = expected_by_model.get(m, 0.0) + c

MAX_PLAN = 100.0
expected_savings = expected_total - MAX_PLAN
TOLERANCE = 0.05  # 5% tolerance to allow for minor rounding differences

def within_tolerance(actual, expected, tol=TOLERANCE):
    if expected == 0:
        return abs(actual) < 0.01
    return abs(actual - expected) / abs(expected) <= tol

def evaluate(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    
    # ---- CHECK 1: Database exists and has records ----
    db_path = get_db_path()
    db_exists = db_path.exists()
    checks.append({
        "name": "tokenmeter_database_exists",
        "passed": db_exists,
        "detail": f"Database at {db_path}: {'found' if db_exists else 'NOT FOUND'}"
    })
    
    # ---- CHECK 2: Database has at least 11 records (one per session) ----
    db_record_count = 0
    db_check_detail = "N/A (database not found)"
    if db_exists:
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall()]
            for t in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {t}")
                    cnt = cursor.fetchone()[0]
                    db_record_count += cnt
                except:
                    pass
            conn.close()
            db_check_detail = f"Found {db_record_count} total records across tables: {tables}"
        except Exception as e:
            db_check_detail = f"DB query error: {e}"
    
    db_has_records = db_record_count >= 11
    checks.append({
        "name": "database_has_all_session_records",
        "passed": db_has_records,
        "detail": db_check_detail
    })
    
    # ---- CHECK 3: Output JSON file exists ----
    output_file = find_output_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "cost_audit_file_exists",
        "passed": file_exists,
        "detail": f"cost_audit_feb2026.json {'found at ' + str(output_file) if file_exists else 'NOT FOUND anywhere in workspace'}"
    })
    
    if not file_exists:
        # Can't continue without the file
        score = sum(1 for c in checks if c["passed"]) / 7.0
        return {"passed": False, "score": score, "checks": checks}
    
    # ---- Load and parse JSON ----
    try:
        with open(output_file) as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        score = sum(1 for c in checks if c["passed"]) / 7.0
        return {"passed": False, "score": score, "checks": checks}
    
    checks.append({"name": "json_parseable", "passed": True, "detail": "JSON loaded successfully"})
    
    # ---- CHECK 5: Total API-equivalent cost is correct (within tolerance) ----
    # Accept various key names: total_cost, api_cost, api_equivalent_cost, total_api_cost, etc.
    total_cost_val = None
    for key in ["total_cost", "api_equivalent_cost", "total_api_cost", "api_cost", "total"]:
        if key in report:
            total_cost_val = report[key]
            break
    
    # Also check nested structures
    if total_cost_val is None and isinstance(report, dict):
        for v in report.values():
            if isinstance(v, (int, float)) and within_tolerance(float(v), expected_total, 0.10):
                total_cost_val = float(v)
                break
    
    total_cost_correct = False
    total_cost_detail = f"Expected ~${expected_total:.4f}, found: {total_cost_val}"
    if total_cost_val is not None:
        try:
            total_cost_correct = within_tolerance(float(total_cost_val), expected_total)
            total_cost_detail = f"Expected ~${expected_total:.4f}, got ${float(total_cost_val):.4f} ({'PASS' if total_cost_correct else 'FAIL'})"
        except (ValueError, TypeError) as e:
            total_cost_detail = f"Could not parse total cost value: {total_cost_val}, error: {e}"
    
    checks.append({
        "name": "total_api_cost_correct",
        "passed": total_cost_correct,
        "detail": total_cost_detail
    })
    
    # ---- CHECK 6: Per-model breakdown present and approximately correct ----
    model_breakdown_correct = False
    model_detail = ""
    
    # Find model breakdown - could be under "models", "breakdown", "by_model", etc.
    model_data = None
    for key in ["models", "breakdown", "by_model", "model_breakdown", "cost_by_model"]:
        if key in report and isinstance(report[key], dict):
            model_data = report[key]
            break
    
    if model_data:
        # Check that at least the three models are represented and costs are roughly right
        model_checks = []
        for model_short, expected_cost in expected_by_model.items():
            # Try various key formats for model names
            found_val = None
            for key_variant in [model_short, f"claude/{model_short}", 
                                  f"anthropic/{model_short}", f"anthropic/claude-{model_short.replace('claude-', '')}",
                                  model_short.replace("claude-", "")]:
                if key_variant in model_data:
                    found_val = model_data[key_variant]
                    break
                # Also try case-insensitive
                for k, v in model_data.items():
                    if model_short.lower() in k.lower():
                        found_val = v
                        break
                if found_val is not None:
                    break
            
            if found_val is not None:
                # found_val might be a dict with 'cost' key or a float
                cost_val = None
                if isinstance(found_val, dict):
                    for ck in ["cost", "total_cost", "api_cost", "amount"]:
                        if ck in found_val:
                            cost_val = found_val[ck]
                            break
                else:
                    cost_val = found_val
                
                if cost_val is not None:
                    try:
                        ok = within_tolerance(float(cost_val), expected_cost)
                        model_checks.append((model_short, ok, float(cost_val), expected_cost))
                    except (ValueError, TypeError):
                        model_checks.append((model_short, False, None, expected_cost))
                else:
                    model_checks.append((model_short, False, None, expected_cost))
            else:
                model_checks.append((model_short, False, None, expected_cost))
        
        passed_models = sum(1 for _, ok, _, _ in model_checks if ok)
        model_breakdown_correct = passed_models >= 2  # at least 2 of 3 models correct
        model_detail = f"Model checks: {[(m, ok, f'${got:.4f}' if got else 'NOT FOUND', f'${exp:.4f}') for m, ok, got, exp in model_checks]}"
    else:
        model_detail = f"No model breakdown found. Report keys: {list(report.keys()) if isinstance(report, dict) else 'N/A'}"
    
    checks.append({
        "name": "model_breakdown_present_and_correct",
        "passed": model_breakdown_correct,
        "detail": model_detail
    })
    
    # ---- CHECK 7: Savings calculation correct ----
    savings_val = None
    for key in ["savings", "max_plan_savings", "net_savings", "total_savings", "monthly_savings"]:
        if key in report:
            savings_val = report[key]
            break
    
    savings_correct = False
    savings_detail = f"Expected savings ~${expected_savings:.4f} (api_cost - $100 Max plan)"
    
    if savings_val is not None:
        try:
            savings_correct = within_tolerance(float(savings_val), expected_savings, 0.10)
            savings_detail = f"Expected ~${expected_savings:.4f}, got ${float(savings_val):.4f} ({'PASS' if savings_correct else 'FAIL'})"
        except (ValueError, TypeError) as e:
            savings_detail = f"Could not parse savings value: {savings_val}, error: {e}"
    else:
        savings_detail = f"No savings field found in report. Keys: {list(report.keys()) if isinstance(report, dict) else 'N/A'}"
    
    checks.append({
        "name": "max_plan_savings_correct",
        "passed": savings_correct,
        "detail": savings_detail
    })
    
    # Overall pass: need at least 5 of 7 checks to pass, including the critical cost check
    passed_count = sum(1 for c in checks if c["passed"])
    critical_passed = total_cost_correct and file_exists
    overall_passed = critical_passed and passed_count >= 5
    score = passed_count / 7.0
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))