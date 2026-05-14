import sys
import json
import math
from pathlib import Path

def compute_blended_score(real, bench, sentiment, cost):
    """Exact SKILL.md weights: Real=45%, Bench=30%, Sentiment=20%, Cost=5%"""
    return round(real * 0.45 + bench * 0.30 + sentiment * 0.20 + cost * 0.05, 2)

ANTHROPIC_MODELS = {"claude_sonnet_4", "claude", "anthropic", "claude-sonnet"}

def is_anthropic(model_name: str) -> bool:
    return any(a in model_name.lower() for a in ["claude", "anthropic"])

# Ground truth: compute expected values from the raw eval data
RAW_DATA_PATH = Path("/workspace/data/raw_evals/daily_eval_dump_2025-07-08.json")

def load_expected():
    with open(RAW_DATA_PATH) as f:
        data = json.load(f)
    
    results = {}
    for cat in data["categories"]:
        cname = cat["category_name"]
        models = cat["models_evaluated"]
        
        # Compute blended scores for all models
        scored = []
        for m in models:
            s = compute_blended_score(
                m["real_task_score"],
                m["benchmark_score"],
                m["sentiment_score"],
                m["cost_score"]
            )
            scored.append((m["model"], s))
        
        scored.sort(key=lambda x: -x[1])
        
        # Raw #1 (including Anthropic)
        raw_1_model = scored[0][0]
        raw_1_score = scored[0][1]
        
        # Policy: Anthropic excluded → auto-promote #2
        non_anthropic = [(m, s) for m, s in scored if not is_anthropic(m)]
        effective_1_model = non_anthropic[0][0] if non_anthropic else scored[0][0]
        effective_1_score = non_anthropic[0][1] if non_anthropic else scored[0][1]
        
        # Confidence: based on delta between effective #1 and effective #2
        if len(non_anthropic) >= 2:
            delta = non_anthropic[0][1] - non_anthropic[1][1]
            if delta >= 5:
                confidence = "High"
            elif delta >= 2:
                confidence = "Medium"
            else:
                confidence = "Low"
        else:
            confidence = "High"
        
        # For the scorecard row: use the effective_1 model's component scores
        # (i.e., the scores of the model that is Effective #1)
        eff_model_data = next((m for m in models if m["model"] == effective_1_model), None)
        
        results[cname] = {
            "raw_score": effective_1_score,  # the effective #1's blended score
            "raw_score_of_raw1": raw_1_score,
            "raw_1": raw_1_model,
            "effective_1": effective_1_model,
            "confidence": confidence,
            "real_eval": eff_model_data["real_task_score"] if eff_model_data else None,
            "bench": eff_model_data["benchmark_score"] if eff_model_data else None,
            "sentiment": eff_model_data["sentiment_score"] if eff_model_data else None,
            "cost": eff_model_data["cost_score"] if eff_model_data else None,
        }
    return results

def find_scorecard(workspace):
    # Look for the daily scorecard file
    workspace_path = Path(workspace)
    candidates = list(workspace_path.rglob("daily_scorecard*.md")) + \
                 list(workspace_path.rglob("scorecard*.md")) + \
                 list(workspace_path.rglob("*scorecard*2025*.md"))
    # Filter out archived/old files
    candidates = [c for c in candidates if "archive" not in str(c) and "may" not in str(c).lower() and "jun" not in str(c).lower()]
    return candidates

def parse_markdown_table(content):
    """Parse a markdown table into list of dicts."""
    rows = []
    lines = content.split("\n")
    header = None
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not cells:
            continue
        if header is None:
            header = cells
        elif all(set(c.replace("-","").replace(":","").replace(" ","")) <= set() or c.replace("-","").replace(":","").strip() == "" for c in cells):
            # separator row
            continue
        else:
            if len(cells) == len(header):
                rows.append(dict(zip(header, cells)))
    return rows

def run_eval(workspace):
    checks = []
    score = 0.0

    try:
        expected = load_expected()
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "load_expected_data", "passed": False, "detail": f"Could not load/compute expected: {e}"}]
        }

    # --- Check 1: Scorecard file exists ---
    candidates = find_scorecard(workspace)
    if not candidates:
        checks.append({"name": "scorecard_file_exists", "passed": False, "detail": "No scorecard markdown file found in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    scorecard_path = candidates[0]
    checks.append({"name": "scorecard_file_exists", "passed": True, "detail": f"Found: {scorecard_path}"})
    score += 5.0

    try:
        content = scorecard_path.read_text()
    except Exception as e:
        checks.append({"name": "scorecard_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": score, "checks": checks}

    # --- Check 2: All 7 required categories present ---
    required_categories = [
        "Research", "Planning", "Coding (complex)", "Coding (routine)",
        "Creative Writing", "Enterprise Discussion", "Citizen Sentiment (X)"
    ]
    missing_cats = [c for c in required_categories if c not in content]
    if not missing_cats:
        checks.append({"name": "all_categories_present", "passed": True, "detail": "All 7 categories found in scorecard."})
        score += 10.0
    else:
        checks.append({"name": "all_categories_present", "passed": False, "detail": f"Missing categories: {missing_cats}"})

    # --- Check 3: Table has required columns ---
    required_cols_substrings = ["Real Eval", "Bench", "Sentiment", "Cost", "Raw Score", "Raw #1", "Effective #1", "Confidence"]
    missing_cols = [c for c in required_cols_substrings if c not in content]
    if not missing_cols:
        checks.append({"name": "required_columns_present", "passed": True, "detail": "All required columns present."})
        score += 10.0
    else:
        checks.append({"name": "required_columns_present", "passed": False, "detail": f"Missing columns: {missing_cols}"})

    # --- Parse the table ---
    rows = parse_markdown_table(content)

    # --- Check 4: Weighted score calculation correctness ---
    # For each category, check that the blended score is computed with correct weights (45/30/20/5)
    weight_correct = 0
    weight_total = 0
    weight_details = []
    for row in rows:
        cat = row.get("Category", "").strip()
        if cat not in expected:
            continue
        exp = expected[cat]
        
        # Try to find the raw score in the row (look for "Raw Score" column variant)
        raw_score_key = next((k for k in row if "Raw" in k and "Score" in k), None)
        if raw_score_key is None:
            raw_score_key = next((k for k in row if "Score" in k), None)
        
        if raw_score_key and row[raw_score_key].strip():
            try:
                agent_score = float(row[raw_score_key].replace("/100", "").strip())
                exp_score = exp["raw_score"]
                tolerance = 1.5  # allow small rounding
                if abs(agent_score - exp_score) <= tolerance:
                    weight_correct += 1
                    weight_details.append(f"{cat}: OK (agent={agent_score}, expected≈{exp_score})")
                else:
                    weight_details.append(f"{cat}: WRONG (agent={agent_score}, expected≈{exp_score})")
                weight_total += 1
            except:
                weight_details.append(f"{cat}: could not parse score '{row.get(raw_score_key)}'")
                weight_total += 1

    if weight_total > 0 and weight_correct >= math.ceil(weight_total * 0.7):
        checks.append({"name": "blended_score_weights_correct", "passed": True, "detail": f"{weight_correct}/{weight_total} correct. " + "; ".join(weight_details)})
        score += 20.0
    else:
        checks.append({"name": "blended_score_weights_correct", "passed": False, "detail": f"{weight_correct}/{weight_total} correct. " + "; ".join(weight_details)})

    # --- Check 5: Anthropic exclusion policy applied (auto-promote #2) ---
    # For categories where claude_sonnet_4 is Raw #1, Effective #1 must be different (promoted #2)
    anthropic_policy_correct = 0
    anthropic_policy_total = 0
    policy_details = []
    
    for row in rows:
        cat = row.get("Category", "").strip()
        if cat not in expected:
            continue
        exp = expected[cat]
        
        # Only check categories where Anthropic was raw #1
        if not is_anthropic(exp["raw_1"]):
            continue
        
        anthropic_policy_total += 1
        
        eff1_key = next((k for k in row if "Effective" in k), None)
        raw1_key = next((k for k in row if "Raw" in k and "#1" in k and "Score" not in k), None)
        
        eff1_val = row.get(eff1_key, "").strip().lower() if eff1_key else ""
        raw1_val = row.get(raw1_key, "").strip().lower() if raw1_key else ""
        
        # Raw #1 should be claude/anthropic
        raw1_ok = "claude" in raw1_val or "anthropic" in raw1_val or "sonnet" in raw1_val
        # Effective #1 must NOT be claude/anthropic
        eff1_ok = eff1_val and not ("claude" in eff1_val or "anthropic" in eff1_val or "sonnet" in eff1_val)
        
        if raw1_ok and eff1_ok:
            anthropic_policy_correct += 1
            policy_details.append(f"{cat}: PASS (raw1={raw1_val}, eff1={eff1_val})")
        else:
            policy_details.append(f"{cat}: FAIL (raw1_ok={raw1_ok}, eff1_ok={eff1_ok}, raw1='{raw1_val}', eff1='{eff1_val}')")

    if anthropic_policy_total == 0:
        checks.append({"name": "anthropic_exclusion_policy", "passed": False, "detail": "Could not identify any categories with Anthropic as Raw #1, or table not parseable."})
    elif anthropic_policy_correct >= math.ceil(anthropic_policy_total * 0.7):
        checks.append({"name": "anthropic_exclusion_policy", "passed": True, "detail": f"{anthropic_policy_correct}/{anthropic_policy_total} correct. " + "; ".join(policy_details)})
        score += 25.0
    else:
        checks.append({"name": "anthropic_exclusion_policy", "passed": False, "detail": f"{anthropic_policy_correct}/{anthropic_policy_total} correct. " + "; ".join(policy_details)})

    # --- Check 6: Effective routing matches SKILL.md prescribed routes ---
    # SKILL.md defines: Research/Planning → Gemini 3.1 Pro; Complex Coding/Enterprise → GPT-5.3 Codex;
    # Routine Coding → GPT-5-mini; Citizen Sentiment (X) → Grok
    prescribed_routes = {
        "Research": ["gemini"],
        "Planning": ["gemini"],
        "Coding (complex)": ["gpt5_codex", "gpt-5", "codex", "gpt5.3"],
        "Coding (routine)": ["gpt5_mini", "gpt-5-mini", "mini"],
        "Enterprise Discussion": ["gpt5_codex", "gpt-5", "codex", "gpt5.3"],
        "Citizen Sentiment (X)": ["grok"],
    }
    route_correct = 0
    route_total = 0
    route_details = []
    
    for row in rows:
        cat = row.get("Category", "").strip()
        if cat not in prescribed_routes:
            continue
        route_total += 1
        eff1_key = next((k for k in row if "Effective" in k), None)
        eff1_val = row.get(eff1_key, "").strip().lower() if eff1_key else ""
        
        expected_keywords = prescribed_routes[cat]
        if any(kw in eff1_val for kw in expected_keywords):
            route_correct += 1
            route_details.append(f"{cat}: OK (eff1='{eff1_val}')")
        else:
            route_details.append(f"{cat}: WRONG (eff1='{eff1_val}', expected one of {expected_keywords})")
    
    if route_total > 0 and route_correct >= math.ceil(route_total * 0.7):
        checks.append({"name": "effective_routing_matches_policy", "passed": True, "detail": f"{route_correct}/{route_total} correct. " + "; ".join(route_details)})
        score += 20.0
    else:
        checks.append({"name": "effective_routing_matches_policy", "passed": False, "detail": f"{route_correct}/{route_total} correct. " + "; ".join(route_details)})

    # --- Check 7: Confidence column populated ---
    confidence_populated = 0
    conf_total = 0
    for row in rows:
        cat = row.get("Category", "").strip()
        if cat not in required_categories:
            continue
        conf_total += 1
        conf_key = next((k for k in row if "Confidence" in k), None)
        conf_val = row.get(conf_key, "").strip() if conf_key else ""
        if conf_val and conf_val not in ("", "-", "N/A"):
            confidence_populated += 1
    
    if conf_total > 0 and confidence_populated >= math.ceil(conf_total * 0.7):
        checks.append({"name": "confidence_column_populated", "passed": True, "detail": f"{confidence_populated}/{conf_total} rows have confidence values."})
        score += 10.0
    else:
        checks.append({"name": "confidence_column_populated", "passed": False, "detail": f"{confidence_populated}/{conf_total} rows have confidence values."})

    # --- Final verdict ---
    # Must pass: file exists, all categories, columns, anthropic policy, routing
    critical_checks = ["scorecard_file_exists", "all_categories_present", "anthropic_exclusion_policy", "effective_routing_matches_policy", "blended_score_weights_correct"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    passed = critical_passed and score >= 60.0
    
    return {
        "passed": passed,
        "score": round(score, 2),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))