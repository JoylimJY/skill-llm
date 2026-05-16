#!/usr/bin/env python3
"""
Evaluation script for the Portfolio Risk Analyzer task.
Checks:
1. Agent correctly normalized the messy portfolio JSON into the proper schema.
2. Agent ran portfolio-risk-analyzer with --benchmark SPY.
3. Agent produced a risk_summary.md (or similarly named summary) synthesizing key findings.
4. The summary contains the critical required sections: VaR, Max Drawdown, Stress Tests, Concentration, Actionable Insights.
5. The normalized portfolio JSON is valid and conforming to the expected schema.
"""

import sys
import json
import os
import re
from pathlib import Path
from datetime import date

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    workspace = Path(workspace)
    
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # -------------------------------------------------------------------------
    # CHECK 1: A valid, normalized portfolio.json was created matching the schema
    # -------------------------------------------------------------------------
    portfolio_file = None
    try:
        # Look for any portfolio JSON that conforms to the expected schema
        # It should NOT be the original messy file
        candidates = list(workspace.rglob("portfolio.json")) + \
                     list(workspace.rglob("portfolio_normalized.json")) + \
                     list(workspace.rglob("portfolio_clean.json")) + \
                     list(workspace.rglob("normalized_portfolio.json")) + \
                     list(workspace.rglob("clean_portfolio.json"))
        
        # Also check if agent modified the original file in place (in any subdir)
        raw_export = workspace / "client_data" / "raw" / "portfolio_export_custody.json"
        
        valid_portfolio = None
        valid_portfolio_path = None
        
        for candidate in candidates:
            try:
                with open(candidate) as f:
                    data = json.load(f)
                if 'positions' in data and isinstance(data['positions'], list):
                    # Verify each position has required fields with correct types
                    all_valid = True
                    for pos in data['positions']:
                        if not all(k in pos for k in ['ticker', 'quantity', 'avg_price']):
                            all_valid = False
                            break
                        try:
                            float(pos['quantity'])
                            float(pos['avg_price'])
                        except (ValueError, TypeError):
                            all_valid = False
                            break
                    if all_valid and 'cash' in data:
                        valid_portfolio = data
                        valid_portfolio_path = candidate
                        break
            except Exception:
                continue
        
        # Also check if original file was fixed
        if valid_portfolio is None:
            try:
                with open(raw_export) as f:
                    data = json.load(f)
                if 'positions' in data and 'cash' in data:
                    all_valid = True
                    for pos in data['positions']:
                        if not all(k in pos for k in ['ticker', 'quantity', 'avg_price']):
                            all_valid = False; break
                        try:
                            float(pos['quantity']); float(pos['avg_price'])
                        except: all_valid = False; break
                    if all_valid:
                        valid_portfolio = data
                        valid_portfolio_path = raw_export
            except Exception:
                pass
        
        if valid_portfolio is None:
            add_check("normalized_portfolio_exists", False, 
                      "Could not find a valid portfolio JSON with required schema (positions[], cash, numeric quantity/avg_price)")
        else:
            add_check("normalized_portfolio_exists", True, 
                      f"Found valid portfolio JSON at: {valid_portfolio_path}")
            portfolio_file = valid_portfolio_path
    except Exception as e:
        add_check("normalized_portfolio_exists", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # CHECK 2: Portfolio has correct schema - 'positions' array with required fields
    # -------------------------------------------------------------------------
    try:
        if valid_portfolio is not None:
            positions = valid_portfolio.get('positions', [])
            cash = valid_portfolio.get('cash', None)
            
            schema_ok = True
            issues = []
            
            if cash is None:
                schema_ok = False
                issues.append("Missing 'cash' field")
            
            tickers = [p['ticker'] for p in positions]
            # Check numeric types
            for pos in positions:
                try:
                    q = float(pos['quantity'])
                    p = float(pos['avg_price'])
                    if q <= 0 or p <= 0:
                        schema_ok = False
                        issues.append(f"Non-positive quantity or price for {pos.get('ticker')}")
                except:
                    schema_ok = False
                    issues.append(f"Non-numeric quantity/avg_price for {pos.get('ticker')}")
            
            if len(positions) < 3:
                schema_ok = False
                issues.append(f"Too few positions ({len(positions)}); expected at least the major tickers")
            
            if schema_ok:
                add_check("portfolio_schema_valid", True, 
                         f"Portfolio schema valid: {len(positions)} positions, cash={cash}, tickers={tickers}")
            else:
                add_check("portfolio_schema_valid", False, f"Schema issues: {'; '.join(issues)}")
        else:
            add_check("portfolio_schema_valid", False, "No valid portfolio file found")
    except Exception as e:
        add_check("portfolio_schema_valid", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # CHECK 3: risk_report JSON file was generated by the CLI
    # -------------------------------------------------------------------------
    risk_json_file = None
    try:
        today = date.today().isoformat()
        # Search for risk_report_*.json
        json_reports = list(workspace.rglob(f"risk_report_{today}.json"))
        # Also check current directory
        cwd_json = Path(f"risk_report_{today}.json")
        if cwd_json.exists():
            json_reports.append(cwd_json)
        
        # Broader search
        if not json_reports:
            json_reports = list(workspace.rglob("risk_report_*.json"))
            if not json_reports:
                # check root
                for p in Path(".").glob("risk_report_*.json"):
                    json_reports.append(p)
        
        if not json_reports:
            # Look in /workspace itself
            for p in Path("/workspace").glob("risk_report_*.json"):
                json_reports.append(p)
        
        if json_reports:
            risk_json_file = json_reports[0]
            with open(risk_json_file) as f:
                risk_json = json.load(f)
            
            required_keys = ['portfolio_beta', 'var', 'max_drawdown_pct', 'stress_tests', 
                           'sector_weights', 'actionable_insights', 'correlation_hotspots']
            missing = [k for k in required_keys if k not in risk_json]
            
            if missing:
                add_check("risk_json_generated", False, f"Missing keys in JSON: {missing}")
            else:
                benchmark = risk_json.get('benchmark', '')
                add_check("risk_json_generated", True, 
                         f"Risk JSON report found at {risk_json_file}, benchmark={benchmark}")
        else:
            add_check("risk_json_generated", False, 
                     "No risk_report_*.json file found. CLI may not have been run.")
    except Exception as e:
        add_check("risk_json_generated", False, f"Exception reading risk JSON: {e}")

    # -------------------------------------------------------------------------
    # CHECK 4: Benchmark is SPY (not QQQ or something else)
    # -------------------------------------------------------------------------
    try:
        if risk_json_file:
            with open(risk_json_file) as f:
                risk_json = json.load(f)
            benchmark = risk_json.get('benchmark', '').upper()
            if benchmark == 'SPY':
                add_check("correct_benchmark_spy", True, "Benchmark correctly set to SPY")
            else:
                add_check("correct_benchmark_spy", False, 
                         f"Wrong benchmark: '{benchmark}'. Expected 'SPY'.")
        else:
            # Try to find benchmark from markdown
            md_reports = list(workspace.rglob("risk_report_*.md"))
            if not md_reports:
                for p in Path("/workspace").glob("risk_report_*.md"):
                    md_reports.append(p)
            if md_reports:
                content = md_reports[0].read_text()
                if 'SPY' in content:
                    add_check("correct_benchmark_spy", True, "SPY found in Markdown report")
                else:
                    add_check("correct_benchmark_spy", False, "SPY not found in report")
            else:
                add_check("correct_benchmark_spy", False, "No report found to verify benchmark")
    except Exception as e:
        add_check("correct_benchmark_spy", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # CHECK 5: A synthesized risk summary file was created by the agent
    # -------------------------------------------------------------------------
    summary_file = None
    try:
        # Search for any markdown file named risk_summary or similar (not the auto-generated report)
        candidates = list(workspace.rglob("risk_summary.md")) + \
                     list(workspace.rglob("risk_summary*.md")) + \
                     list(workspace.rglob("summary_risk*.md")) + \
                     list(workspace.rglob("portfolio_risk_summary*.md")) + \
                     list(workspace.rglob("risk_analysis_summary*.md"))
        
        # Also check /workspace directly
        for p in Path("/workspace").glob("risk_summary*.md"):
            candidates.append(p)
        for p in Path("/workspace").glob("*summary*.md"):
            candidates.append(p)
        
        # Filter out draft/placeholder files and the auto-generated risk_report files
        filtered = []
        for c in candidates:
            if 'risk_report_' in c.name:
                continue
            try:
                content = c.read_text()
                if len(content) > 200 and 'TBD' not in content:
                    filtered.append(c)
            except:
                pass
        
        if filtered:
            summary_file = filtered[0]
            add_check("synthesis_summary_exists", True, f"Synthesized summary found: {summary_file}")
        else:
            add_check("synthesis_summary_exists", False, 
                     "No synthesized risk summary file found. Agent should create risk_summary.md.")
    except Exception as e:
        add_check("synthesis_summary_exists", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # CHECK 6: Summary contains all required sections from SKILL.md Step 4
    # -------------------------------------------------------------------------
    try:
        if summary_file:
            content = summary_file.read_text().lower()
            
            required_topics = {
                "VaR/Value at Risk": any(x in content for x in ['var', 'value at risk', 'value-at-risk']),
                "Max Drawdown": any(x in content for x in ['drawdown', 'max drawdown', 'maximum drawdown']),
                "Stress Test": any(x in content for x in ['stress', '2008', '2020', '2022', 'crisis', 'crash']),
                "Concentration": any(x in content for x in ['concentration', 'sector', 'technology', 'weight']),
                "Actionable Insights/Recommendations": any(x in content for x in ['recommend', 'consider', 'insight', 'suggest', 'action', 'diversif']),
                "Beta": any(x in content for x in ['beta', 'volatility relative']),
            }
            
            missing = [k for k, v in required_topics.items() if not v]
            present = [k for k, v in required_topics.items() if v]
            
            if len(present) >= 4:
                add_check("summary_contains_required_sections", True,
                         f"Summary covers {len(present)}/6 required topics: {present}")
            else:
                add_check("summary_contains_required_sections", False,
                         f"Summary only covers {len(present)}/6 required topics. Missing: {missing}")
        else:
            add_check("summary_contains_required_sections", False, "No summary file to evaluate")
    except Exception as e:
        add_check("summary_contains_required_sections", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # CHECK 7: Summary contains actual numeric values from the generated report
    # -------------------------------------------------------------------------
    try:
        if summary_file and risk_json_file:
            content = summary_file.read_text()
            
            with open(risk_json_file) as f:
                risk_data = json.load(f)
            
            # Check for numeric data presence (beta, drawdown percentage)
            beta = str(risk_data.get('portfolio_beta', ''))
            drawdown = str(risk_data.get('max_drawdown_pct', ''))
            
            numeric_checks = []
            if beta and beta in content:
                numeric_checks.append(f"beta={beta}")
            if drawdown and (drawdown in content or drawdown.lstrip('-') in content):
                numeric_checks.append(f"drawdown={drawdown}%")
            
            # Check that at least some dollar or percentage values appear
            has_dollar = bool(re.search(r'\$[\d,]+', content))
            has_percent = bool(re.search(r'\d+\.?\d*%', content))
            
            if numeric_checks or (has_dollar and has_percent):
                add_check("summary_contains_real_metrics", True,
                         f"Summary includes real metrics: {numeric_checks}, dollar_values={has_dollar}, pct_values={has_percent}")
            else:
                add_check("summary_contains_real_metrics", False,
                         "Summary appears to be generic/template text without actual computed values from the risk report")
        else:
            add_check("summary_contains_real_metrics", False, "Missing summary or risk JSON file")
    except Exception as e:
        add_check("summary_contains_real_metrics", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # CHECK 8: Duplicate AAPL positions were handled (merged or one chosen)
    # -------------------------------------------------------------------------
    try:
        if valid_portfolio is not None:
            positions = valid_portfolio.get('positions', [])
            tickers = [p['ticker'] for p in positions]
            aapl_count = tickers.count('AAPL')
            
            # The original file has AAPL twice; agent should either merge or keep one
            # Both are acceptable; what's NOT acceptable is having AAPL twice in the final schema
            if aapl_count <= 1:
                add_check("duplicate_tickers_handled", True,
                         f"AAPL duplicate handled correctly (appears {aapl_count} time(s) in final portfolio)")
            else:
                add_check("duplicate_tickers_handled", False,
                         f"AAPL still appears {aapl_count} times in the portfolio. Duplicates should be merged.")
        else:
            add_check("duplicate_tickers_handled", False, "No valid portfolio to check")
    except Exception as e:
        add_check("duplicate_tickers_handled", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # Final scoring
    # -------------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall_passed = passed_count >= 6  # At least 6/8 checks must pass

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()