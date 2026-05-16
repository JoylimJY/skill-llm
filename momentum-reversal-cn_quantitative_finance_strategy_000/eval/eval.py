import sys
import json
import math
import numpy as np
import pandas as pd
from pathlib import Path

def load_and_clean_returns(workspace):
    """Replicate the expected data cleaning pipeline."""
    csv_path = Path(workspace) / "data" / "raw" / "a_share_monthly_returns.csv"
    df = pd.read_csv(csv_path, dtype=str)

    def parse_return(val):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return np.nan
        if isinstance(val, str):
            val = val.strip()
            if val == '' or val.lower() == 'nan' or val.lower() == 'none':
                return np.nan
            if val.endswith('%'):
                return float(val[:-1]) / 100.0
            return float(val)
        return float(val)

    for col in ['return_2024_01', 'return_2024_02', 'return_2024_03']:
        df[col] = df[col].apply(parse_return)

    # Drop stocks with any NaN in their monthly returns
    df_clean = df.dropna(subset=['return_2024_01', 'return_2024_02', 'return_2024_03']).copy()
    df_clean = df_clean.reset_index(drop=True)
    return df_clean

def compute_cumulative_return(row):
    """3-month cumulative return via compounding (not geometric mean across stocks)."""
    r1 = row['return_2024_01']
    r2 = row['return_2024_02']
    r3 = row['return_2024_03']
    return (1 + r1) * (1 + r2) * (1 + r3) - 1

def geometric_mean_of_group(returns):
    """Geometric mean return across stocks in a group: (Π(1+ri))^(1/n) - 1"""
    n = len(returns)
    product = 1.0
    for r in returns:
        product *= (1 + r)
    return product ** (1.0 / n) - 1

def run_evaluation(workspace):
    checks = []
    
    # --- Find strategy_report.json ---
    report_files = list(Path(workspace).rglob("strategy_report.json"))
    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "strategy_report.json not found anywhere in workspace"}]
        }
    
    report_path = report_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {report_path}"})

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_parseable", "passed": False, "detail": f"JSON parse error: {e}"}]
        }
    checks.append({"name": "file_parseable", "passed": True, "detail": "Valid JSON"})

    # --- Compute expected values ---
    try:
        df_clean = load_and_clean_returns(workspace)
        df_clean['cum_return_3m'] = df_clean.apply(compute_cumulative_return, axis=1)
        n_valid = len(df_clean)
        
        # Sort and assign quintile groups (5 groups), Q1=losers, Q5=winners
        df_clean_sorted = df_clean.sort_values('cum_return_3m').reset_index(drop=True)
        df_clean_sorted['quintile'] = pd.qcut(df_clean_sorted['cum_return_3m'], q=5, labels=[1, 2, 3, 4, 5])
        df_clean_sorted['quintile'] = df_clean_sorted['quintile'].astype(int)
        
        q1_returns = df_clean_sorted[df_clean_sorted['quintile'] == 1]['cum_return_3m'].tolist()
        q5_returns = df_clean_sorted[df_clean_sorted['quintile'] == 5]['cum_return_3m'].tolist()
        
        expected_q1_geo = geometric_mean_of_group(q1_returns)
        expected_q5_geo = geometric_mean_of_group(q5_returns)
        expected_ls_return = expected_q1_geo - expected_q5_geo  # reversal: long losers, short winners
        
        # Also compute arithmetic means to check agent didn't use wrong method
        expected_q1_arith = np.mean(q1_returns)
        expected_q5_arith = np.mean(q5_returns)
        
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "expected_computation", "passed": False, "detail": f"Error computing expected: {e}"}]
        }

    TOLERANCE = 0.001  # 0.1% absolute tolerance

    # Check 1: Number of groups = 5
    try:
        groups_data = report.get("groups", report.get("quintile_groups", report.get("quintiles", None)))
        num_groups_check = False
        num_groups_detail = "No groups/quintile_groups/quintiles key found"
        if groups_data is not None:
            if isinstance(groups_data, dict):
                num_groups_check = len(groups_data) == 5
                num_groups_detail = f"Found {len(groups_data)} groups (expected 5)"
            elif isinstance(groups_data, list):
                num_groups_check = len(groups_data) == 5
                num_groups_detail = f"Found {len(groups_data)} group entries (expected 5)"
        checks.append({"name": "num_groups_equals_5", "passed": num_groups_check, "detail": num_groups_detail})
    except Exception as e:
        checks.append({"name": "num_groups_equals_5", "passed": False, "detail": f"Error: {e}"})

    # Check 2: Strategy type is reversal (not momentum)
    try:
        strategy = str(report.get("strategy", report.get("strategy_type", ""))).lower()
        reversal_keywords = ["reversal", "反转", "contrarian", "mean_reversion", "mean-reversion"]
        is_reversal = any(kw in strategy for kw in reversal_keywords)
        checks.append({
            "name": "strategy_is_reversal",
            "passed": is_reversal,
            "detail": f"Strategy field value: '{strategy}'. Expected reversal-type keyword."
        })
    except Exception as e:
        checks.append({"name": "strategy_is_reversal", "passed": False, "detail": f"Error: {e}"})

    # Check 3: Observation period = 3 months
    try:
        obs_period = report.get("observation_period", report.get("observation_months", report.get("lookback_months", None)))
        obs_correct = False
        obs_detail = f"observation_period/observation_months not found"
        if obs_period is not None:
            obs_val = str(obs_period).replace("month", "").replace("months", "").replace("m", "").strip()
            try:
                obs_correct = int(float(obs_val)) == 3
                obs_detail = f"Observation period: {obs_period} (expected 3)"
            except:
                obs_detail = f"Could not parse observation period: {obs_period}"
        checks.append({"name": "observation_period_3m", "passed": obs_correct, "detail": obs_detail})
    except Exception as e:
        checks.append({"name": "observation_period_3m", "passed": False, "detail": f"Error: {e}"})

    # Check 4: Q1 (losers) geometric mean return is correct
    try:
        q1_val = None
        # Try various possible key names
        for key_path in [
            ["q1_return"], ["Q1_return"], ["loser_return"], ["q1_geo_mean"],
            ["losers_geo_mean"], ["group_1_return"], ["quintile_1_return"]
        ]:
            val = report
            for k in key_path:
                if isinstance(val, dict) and k in val:
                    val = val[k]
                else:
                    val = None
                    break
            if val is not None:
                q1_val = float(val)
                break
        # Also try nested structures
        if q1_val is None and groups_data is not None:
            if isinstance(groups_data, dict):
                for k in ["1", "Q1", "q1", "group_1", "loser", "losers"]:
                    if k in groups_data:
                        g = groups_data[k]
                        if isinstance(g, dict):
                            for rk in ["return", "geo_mean", "geometric_mean", "mean_return", "portfolio_return"]:
                                if rk in g:
                                    q1_val = float(g[rk])
                                    break
                        else:
                            try:
                                q1_val = float(g)
                            except:
                                pass
                        if q1_val is not None:
                            break

        if q1_val is None:
            checks.append({"name": "q1_geometric_mean_correct", "passed": False,
                          "detail": f"Could not find Q1/loser return in report. Expected ~{expected_q1_geo:.6f}"})
        else:
            diff = abs(q1_val - expected_q1_geo)
            passed = diff <= TOLERANCE
            # Also check it's not arithmetic mean (wrong method)
            arith_diff = abs(q1_val - expected_q1_arith)
            method_note = ""
            if not passed and arith_diff <= TOLERANCE:
                method_note = " (Looks like arithmetic mean was used instead of geometric mean)"
            checks.append({
                "name": "q1_geometric_mean_correct",
                "passed": passed,
                "detail": f"Q1 geo mean: {q1_val:.6f}, expected: {expected_q1_geo:.6f}, diff: {diff:.6f}{method_note}"
            })
    except Exception as e:
        checks.append({"name": "q1_geometric_mean_correct", "passed": False, "detail": f"Error: {e}"})

    # Check 5: Q5 (winners) geometric mean return is correct
    try:
        q5_val = None
        for key_path in [
            ["q5_return"], ["Q5_return"], ["winner_return"], ["q5_geo_mean"],
            ["winners_geo_mean"], ["group_5_return"], ["quintile_5_return"]
        ]:
            val = report
            for k in key_path:
                if isinstance(val, dict) and k in val:
                    val = val[k]
                else:
                    val = None
                    break
            if val is not None:
                q5_val = float(val)
                break
        if q5_val is None and groups_data is not None:
            if isinstance(groups_data, dict):
                for k in ["5", "Q5", "q5", "group_5", "winner", "winners"]:
                    if k in groups_data:
                        g = groups_data[k]
                        if isinstance(g, dict):
                            for rk in ["return", "geo_mean", "geometric_mean", "mean_return", "portfolio_return"]:
                                if rk in g:
                                    q5_val = float(g[rk])
                                    break
                        else:
                            try:
                                q5_val = float(g)
                            except:
                                pass
                        if q5_val is not None:
                            break

        if q5_val is None:
            checks.append({"name": "q5_geometric_mean_correct", "passed": False,
                          "detail": f"Could not find Q5/winner return in report. Expected ~{expected_q5_geo:.6f}"})
        else:
            diff = abs(q5_val - expected_q5_geo)
            passed = diff <= TOLERANCE
            arith_diff = abs(q5_val - expected_q5_arith)
            method_note = ""
            if not passed and arith_diff <= TOLERANCE:
                method_note = " (Looks like arithmetic mean was used instead of geometric mean)"
            checks.append({
                "name": "q5_geometric_mean_correct",
                "passed": passed,
                "detail": f"Q5 geo mean: {q5_val:.6f}, expected: {expected_q5_geo:.6f}, diff: {diff:.6f}{method_note}"
            })
    except Exception as e:
        checks.append({"name": "q5_geometric_mean_correct", "passed": False, "detail": f"Error: {e}"})

    # Check 6: Long-short portfolio return (reversal: long Q1 losers, short Q5 winners)
    try:
        ls_val = None
        for key in ["long_short_return", "ls_return", "reversal_return", "net_return",
                    "portfolio_return", "strategy_return", "long_short", "net_portfolio_return"]:
            if key in report:
                ls_val = float(report[key])
                break

        if ls_val is None:
            checks.append({"name": "long_short_return_correct", "passed": False,
                          "detail": f"long_short_return or similar key not found. Expected ~{expected_ls_return:.6f}"})
        else:
            diff = abs(ls_val - expected_ls_return)
            passed = diff <= TOLERANCE
            # Check: did agent do momentum instead (Q5 - Q1)?
            momentum_val = expected_q5_geo - expected_q1_geo
            momentum_diff = abs(ls_val - momentum_val)
            method_note = ""
            if not passed and momentum_diff <= TOLERANCE:
                method_note = " (Agent applied momentum: long winners - short losers, but reversal requires long losers - short winners)"
            checks.append({
                "name": "long_short_return_correct",
                "passed": passed,
                "detail": f"L/S return: {ls_val:.6f}, expected (Q1-Q5 reversal): {expected_ls_return:.6f}, diff: {diff:.6f}{method_note}"
            })
    except Exception as e:
        checks.append({"name": "long_short_return_correct", "passed": False, "detail": f"Error: {e}"})

    # Check 7: Valid stocks count (must have dropped NaN rows)
    try:
        n_stocks_val = report.get("num_stocks", report.get("n_stocks", report.get("stock_count", None)))
        expected_n = len(df_clean)
        n_correct = False
        n_detail = f"num_stocks not found in report, expected {expected_n}"
        if n_stocks_val is not None:
            n_correct = int(n_stocks_val) == expected_n
            n_detail = f"num_stocks: {n_stocks_val}, expected: {expected_n}"
        checks.append({"name": "correct_stock_count_after_cleaning", "passed": n_correct, "detail": n_detail})
    except Exception as e:
        checks.append({"name": "correct_stock_count_after_cleaning", "passed": False, "detail": f"Error: {e}"})

    # Score: weighted
    weight_map = {
        "file_exists": 0.05,
        "file_parseable": 0.05,
        "num_groups_equals_5": 0.15,
        "strategy_is_reversal": 0.15,
        "observation_period_3m": 0.10,
        "q1_geometric_mean_correct": 0.20,
        "q5_geometric_mean_correct": 0.15,
        "long_short_return_correct": 0.10,
        "correct_stock_count_after_cleaning": 0.05,
    }

    score = 0.0
    for chk in checks:
        if chk["passed"]:
            score += weight_map.get(chk["name"], 0.0)

    passed_overall = score >= 0.70

    return {
        "passed": passed_overall,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_evaluation(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))