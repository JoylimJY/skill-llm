#!/usr/bin/env python3
"""
Evaluation script for the A-share portfolio management task.
Checks:
1. Portfolio file exists at the correct hidden path (~/.clawdbot/skills/a-stock-analysis/portfolio.json)
2. Portfolio contains exactly the correct holdings (600789, 002446, 002342, 300750) with correct data
3. Portfolio does NOT contain 000858 (should have been removed)
4. 600789 cost is updated to 10.250 (not the original 10.416)
5. stock_analysis_report.json exists somewhere in the workspace and is valid JSON
6. stock_analysis_report.json contains data for 600789, 002446, 002342
"""
import sys
import json
import os
from pathlib import Path

def run_eval(workspace_dir):
    checks = []
    total_score = 0.0
    
    workspace = Path(workspace_dir)
    
    # =========================================================
    # CHECK 1: Portfolio file at the correct hidden path
    # =========================================================
    portfolio_path = Path.home() / ".clawdbot" / "skills" / "a-stock-analysis" / "portfolio.json"
    portfolio_data = None
    
    try:
        if not portfolio_path.exists():
            checks.append({
                "name": "portfolio_file_at_correct_path",
                "passed": False,
                "detail": f"Portfolio file not found at required path: {portfolio_path}. Agent must use the portfolio.py tool which stores data at ~/.clawdbot/skills/a-stock-analysis/portfolio.json"
            })
        else:
            with open(portfolio_path) as f:
                portfolio_data = json.load(f)
            checks.append({
                "name": "portfolio_file_at_correct_path",
                "passed": True,
                "detail": f"Portfolio file found at {portfolio_path} with {len(portfolio_data)} entries"
            })
            total_score += 0.15
    except Exception as e:
        checks.append({
            "name": "portfolio_file_at_correct_path",
            "passed": False,
            "detail": f"Error reading portfolio file: {e}"
        })

    # =========================================================
    # CHECK 2: Correct holdings present (600789, 002446, 002342, 300750)
    # =========================================================
    required_codes = {"600789", "002446", "002342", "300750"}
    try:
        if portfolio_data is None:
            checks.append({
                "name": "required_holdings_present",
                "passed": False,
                "detail": "Portfolio data not loaded, cannot check required holdings"
            })
        else:
            present = set(portfolio_data.keys())
            missing = required_codes - present
            if missing:
                checks.append({
                    "name": "required_holdings_present",
                    "passed": False,
                    "detail": f"Missing required holdings: {missing}. Present: {present}"
                })
            else:
                checks.append({
                    "name": "required_holdings_present",
                    "passed": True,
                    "detail": f"All required holdings present: {required_codes}"
                })
                total_score += 0.15
    except Exception as e:
        checks.append({
            "name": "required_holdings_present",
            "passed": False,
            "detail": f"Error checking holdings: {e}"
        })

    # =========================================================
    # CHECK 3: 000858 (五粮液) should NOT be in portfolio
    # =========================================================
    try:
        if portfolio_data is None:
            checks.append({
                "name": "000858_removed",
                "passed": False,
                "detail": "Portfolio data not loaded"
            })
        elif "000858" in portfolio_data:
            checks.append({
                "name": "000858_removed",
                "passed": False,
                "detail": "000858 (五粮液) is still in the portfolio but should have been removed"
            })
        else:
            checks.append({
                "name": "000858_removed",
                "passed": True,
                "detail": "000858 (五粮液) correctly removed from portfolio"
            })
            total_score += 0.15
    except Exception as e:
        checks.append({
            "name": "000858_removed",
            "passed": False,
            "detail": f"Error checking 000858 removal: {e}"
        })

    # =========================================================
    # CHECK 4: 600789 cost updated to 10.250
    # =========================================================
    try:
        if portfolio_data is None:
            checks.append({
                "name": "600789_cost_updated",
                "passed": False,
                "detail": "Portfolio data not loaded"
            })
        elif "600789" not in portfolio_data:
            checks.append({
                "name": "600789_cost_updated",
                "passed": False,
                "detail": "600789 not in portfolio, cannot check cost update"
            })
        else:
            actual_cost = portfolio_data["600789"].get("cost", None)
            if actual_cost is None:
                checks.append({
                    "name": "600789_cost_updated",
                    "passed": False,
                    "detail": "600789 entry has no 'cost' field"
                })
            elif abs(float(actual_cost) - 10.250) < 0.001:
                checks.append({
                    "name": "600789_cost_updated",
                    "passed": True,
                    "detail": f"600789 cost correctly updated to {actual_cost} (expected 10.250)"
                })
                total_score += 0.15
            elif abs(float(actual_cost) - 10.416) < 0.001:
                checks.append({
                    "name": "600789_cost_updated",
                    "passed": False,
                    "detail": f"600789 cost is still the original value 10.416, not updated to 10.250"
                })
            else:
                checks.append({
                    "name": "600789_cost_updated",
                    "passed": False,
                    "detail": f"600789 cost is {actual_cost}, expected 10.250"
                })
    except Exception as e:
        checks.append({
            "name": "600789_cost_updated",
            "passed": False,
            "detail": f"Error checking cost update: {e}"
        })

    # =========================================================
    # CHECK 5: 600789 quantity is correct (3400)
    # =========================================================
    try:
        if portfolio_data and "600789" in portfolio_data:
            actual_qty = portfolio_data["600789"].get("qty", None)
            if actual_qty is not None and int(actual_qty) == 3400:
                checks.append({
                    "name": "600789_quantity_correct",
                    "passed": True,
                    "detail": f"600789 quantity correctly set to {actual_qty}"
                })
                total_score += 0.05
            else:
                checks.append({
                    "name": "600789_quantity_correct",
                    "passed": False,
                    "detail": f"600789 quantity is {actual_qty}, expected 3400"
                })
        else:
            checks.append({
                "name": "600789_quantity_correct",
                "passed": False,
                "detail": "600789 not in portfolio or portfolio not loaded"
            })
    except Exception as e:
        checks.append({
            "name": "600789_quantity_correct",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # =========================================================
    # CHECK 6: Other holdings have correct initial costs
    # =========================================================
    cost_checks = [
        ("002446", 8.320),
        ("002342", 14.750),
        ("300750", 185.600),
    ]
    all_costs_correct = True
    cost_details = []
    try:
        if portfolio_data:
            for code, expected_cost in cost_checks:
                if code not in portfolio_data:
                    all_costs_correct = False
                    cost_details.append(f"{code} missing")
                    continue
                actual = float(portfolio_data[code].get("cost", 0))
                if abs(actual - expected_cost) < 0.001:
                    cost_details.append(f"{code}: {actual} ✓")
                else:
                    all_costs_correct = False
                    cost_details.append(f"{code}: got {actual}, expected {expected_cost} ✗")
        else:
            all_costs_correct = False
            cost_details.append("Portfolio not loaded")
        
        checks.append({
            "name": "other_holdings_costs_correct",
            "passed": all_costs_correct,
            "detail": "; ".join(cost_details)
        })
        if all_costs_correct:
            total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "other_holdings_costs_correct",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # =========================================================
    # CHECK 7: stock_analysis_report.json exists in workspace
    # =========================================================
    report_file = None
    try:
        found_files = list(workspace.rglob("stock_analysis_report.json"))
        if not found_files:
            checks.append({
                "name": "analysis_report_file_exists",
                "passed": False,
                "detail": "stock_analysis_report.json not found anywhere in workspace"
            })
        else:
            report_file = found_files[0]
            checks.append({
                "name": "analysis_report_file_exists",
                "passed": True,
                "detail": f"Found at: {report_file}"
            })
            total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "analysis_report_file_exists",
            "passed": False,
            "detail": f"Error searching for report: {e}"
        })

    # =========================================================
    # CHECK 8: stock_analysis_report.json is valid JSON with correct structure
    # =========================================================
    report_data = None
    try:
        if report_file is None:
            checks.append({
                "name": "analysis_report_valid_json",
                "passed": False,
                "detail": "Report file not found, cannot validate"
            })
        else:
            with open(report_file) as f:
                content = f.read().strip()
            
            # The output from analyze.py --json is a JSON array
            report_data = json.loads(content)
            
            if not isinstance(report_data, list):
                checks.append({
                    "name": "analysis_report_valid_json",
                    "passed": False,
                    "detail": f"Expected JSON array from analyze.py --json, got {type(report_data).__name__}"
                })
            else:
                checks.append({
                    "name": "analysis_report_valid_json",
                    "passed": True,
                    "detail": f"Valid JSON array with {len(report_data)} entries"
                })
                total_score += 0.05
    except json.JSONDecodeError as e:
        checks.append({
            "name": "analysis_report_valid_json",
            "passed": False,
            "detail": f"Invalid JSON in report file: {e}"
        })
    except Exception as e:
        checks.append({
            "name": "analysis_report_valid_json",
            "passed": False,
            "detail": f"Error reading report: {e}"
        })

    # =========================================================
    # CHECK 9: Report contains data for all 3 required stocks
    # =========================================================
    required_report_codes = {"600789", "002446", "002342"}
    try:
        if report_data is None:
            checks.append({
                "name": "analysis_report_contains_required_stocks",
                "passed": False,
                "detail": "Report data not loaded"
            })
        elif not isinstance(report_data, list):
            checks.append({
                "name": "analysis_report_contains_required_stocks",
                "passed": False,
                "detail": "Report is not a list"
            })
        else:
            found_codes = set()
            for entry in report_data:
                if isinstance(entry, dict) and "code" in entry:
                    found_codes.add(entry["code"])
            
            missing = required_report_codes - found_codes
            extra_ok = found_codes >= required_report_codes
            
            if not missing:
                checks.append({
                    "name": "analysis_report_contains_required_stocks",
                    "passed": True,
                    "detail": f"Report contains all required stocks: {found_codes}"
                })
                total_score += 0.10
            else:
                checks.append({
                    "name": "analysis_report_contains_required_stocks",
                    "passed": False,
                    "detail": f"Missing stocks in report: {missing}. Found: {found_codes}"
                })
    except Exception as e:
        checks.append({
            "name": "analysis_report_contains_required_stocks",
            "passed": False,
            "detail": f"Error checking report contents: {e}"
        })

    # Final score
    passed_count = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    
    # Normalize score to 0-1
    final_score = min(1.0, total_score)
    overall_passed = final_score >= 0.70  # Need at least 70% to pass
    
    result = {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks,
        "summary": f"{passed_count}/{total_checks} checks passed, score: {final_score:.3f}"
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)