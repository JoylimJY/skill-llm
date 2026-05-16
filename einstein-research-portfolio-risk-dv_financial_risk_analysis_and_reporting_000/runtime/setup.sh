#!/bin/bash
set -e

# Create the portfolio-risk-analyzer CLI mock as a realistic, self-contained script
cat > /usr/local/bin/portfolio-risk-analyzer << 'PYSCRIPT'
#!/usr/bin/env python3
"""
Mock portfolio-risk-analyzer CLI - generates realistic risk analysis output.
Implements the exact behavior described in the SKILL.md.
"""
import sys
import json
import math
import random
import os
from datetime import date, datetime
from pathlib import Path

def main():
    args = sys.argv[1:]
    
    if not args or args[0] != 'run':
        print("Usage: portfolio-risk-analyzer run --portfolio <path> --benchmark <ticker>")
        sys.exit(1)
    
    # Parse args
    portfolio_path = None
    benchmark = 'SPY'
    i = 1
    while i < len(args):
        if args[i] == '--portfolio' and i+1 < len(args):
            portfolio_path = args[i+1]; i += 2
        elif args[i] == '--benchmark' and i+1 < len(args):
            benchmark = args[i+1]; i += 2
        else:
            i += 1
    
    if not portfolio_path:
        print("ERROR: --portfolio is required")
        sys.exit(1)
    
    # Load portfolio
    with open(portfolio_path) as f:
        data = json.load(f)
    
    positions = data.get('positions', [])
    cash = data.get('cash', 0)
    
    # Validate required fields
    for pos in positions:
        if 'ticker' not in pos or 'quantity' not in pos or 'avg_price' not in pos:
            print(f"ERROR: Position missing required fields (ticker, quantity, avg_price): {pos}")
            sys.exit(1)
    
    # Deterministic seed based on portfolio content
    random.seed(hash(str(sorted([p['ticker'] for p in positions]))) % (2**32))
    
    # Calculate portfolio values
    total_value = cash
    position_values = {}
    for pos in positions:
        val = float(pos['quantity']) * float(pos['avg_price'])
        ticker = pos['ticker']
        position_values[ticker] = position_values.get(ticker, 0) + val
        total_value += val
    
    # Compute weights
    weights = {t: v/total_value for t, v in position_values.items()}
    
    # Synthetic but deterministic risk metrics
    portfolio_beta = round(0.85 + sum(weights.get(t, 0) * random.uniform(0.1, 0.5) for t in weights), 2)
    
    # VaR calculations (as dollar amounts)
    daily_vol = 0.012 + sum(weights.get(t, 0) * random.uniform(0.005, 0.015) for t in weights)
    
    var_95_param = round(total_value * daily_vol * 1.645, 2)
    var_99_param = round(total_value * daily_vol * 2.326, 2)
    var_95_hist = round(var_95_param * random.uniform(0.92, 1.08), 2)
    var_99_hist = round(var_99_param * random.uniform(0.92, 1.08), 2)
    var_95_mc = round(var_95_param * random.uniform(0.95, 1.05), 2)
    var_99_mc = round(var_99_param * random.uniform(0.95, 1.05), 2)
    
    max_drawdown = round(-(18 + sum(weights.get(t, 0) * random.uniform(5, 20) for t in weights)), 1)
    
    # Correlation matrix
    tickers = list(position_values.keys())
    corr_matrix = {}
    for t1 in tickers:
        corr_matrix[t1] = {}
        for t2 in tickers:
            if t1 == t2:
                corr_matrix[t1][t2] = 1.0
            else:
                key = tuple(sorted([t1, t2]))
                random.seed(hash(key) % (2**32))
                corr_matrix[t1][t2] = round(random.uniform(0.3, 0.92), 3)
    
    random.seed(42)
    
    # Sector allocation
    sector_map = {
        'AAPL': 'Technology', 'MSFT': 'Technology', 'NVDA': 'Technology',
        'TSLA': 'Consumer Discretionary', 'SPY': 'Broad Market',
        'JPM': 'Financials', 'GS': 'Financials', 'BAC': 'Financials',
        'JNJ': 'Healthcare', 'XOM': 'Energy'
    }
    sector_weights = {}
    for t, w in weights.items():
        sector = sector_map.get(t, 'Other')
        sector_weights[sector] = sector_weights.get(sector, 0) + w
    
    # Stress tests
    stress_scenarios = {
        '2008 GFC': round(-total_value * (0.35 + sum(weights.get(t,0)*random.uniform(0.05,0.2) for t in weights)), 2),
        '2020 COVID Crash': round(-total_value * (0.25 + sum(weights.get(t,0)*random.uniform(0.03,0.15) for t in weights)), 2),
        '2022 Rate Hike Cycle': round(-total_value * (0.18 + sum(weights.get(t,0)*random.uniform(0.02,0.12) for t in weights)), 2),
    }
    
    # Concentration risk
    top5 = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Find high correlation pairs
    hotspots = []
    for i, t1 in enumerate(tickers):
        for j, t2 in enumerate(tickers):
            if i < j:
                c = corr_matrix[t1].get(t2, 0)
                if c > 0.75:
                    hotspots.append((t1, t2, c))
    hotspots.sort(key=lambda x: x[2], reverse=True)
    
    # Tech concentration insight
    tech_weight = sector_weights.get('Technology', 0)
    insights = []
    if tech_weight > 0.4:
        insights.append(f"Your portfolio is heavily concentrated in Technology ({tech_weight*100:.1f}%). Consider adding exposure to other sectors like Healthcare or Consumer Staples to improve diversification.")
    if hotspots:
        t1, t2, c = hotspots[0]
        insights.append(f"The high correlation between {t1} and {t2} ({c:.2f}) reduces diversification benefits. Consider trimming one or adding an uncorrelated asset.")
    if max_drawdown < -30:
        insights.append("Historical max drawdown exceeds -30%. Consider adding defensive positions or hedging instruments.")
    insights.append(f"Portfolio Beta of {portfolio_beta} vs {benchmark} indicates {'above' if portfolio_beta > 1 else 'below'}-market volatility.")
    
    # --- Build output ---
    today = date.today().isoformat()
    
    # JSON report
    report_json = {
        "report_date": today,
        "benchmark": benchmark,
        "portfolio_total_value": round(total_value, 2),
        "cash": cash,
        "portfolio_beta": portfolio_beta,
        "var": {
            "parametric": {"var_95": var_95_param, "var_99": var_99_param},
            "historical": {"var_95": var_95_hist, "var_99": var_99_hist},
            "monte_carlo": {"var_95": var_95_mc, "var_99": var_99_mc}
        },
        "max_drawdown_pct": max_drawdown,
        "correlation_matrix": corr_matrix,
        "stress_tests": stress_scenarios,
        "sector_weights": {k: round(v*100, 2) for k, v in sector_weights.items()},
        "top_positions_by_weight": [{"ticker": t, "weight_pct": round(w*100, 2)} for t, w in top5],
        "correlation_hotspots": [{"pair": f"{t1}/{t2}", "correlation": c} for t1, t2, c in hotspots],
        "actionable_insights": insights
    }
    
    json_filename = f"risk_report_{today}.json"
    with open(json_filename, 'w') as f:
        json.dump(report_json, f, indent=2)
    
    # Markdown report
    md_lines = []
    md_lines.append(f"# Portfolio Risk Report — {today}")
    md_lines.append("")
    md_lines.append("## Risk Summary")
    md_lines.append("")
    md_lines.append(f"- **Portfolio Beta**: {portfolio_beta} vs. {benchmark}")
    md_lines.append(f"- **99% VaR (1-day, Parametric)**: ${var_99_param:,.2f} (Your portfolio has a 1% chance of losing at least ${var_99_param:,.2f} on any given day)")
    md_lines.append(f"- **99% VaR (1-day, Historical)**: ${var_99_hist:,.2f}")
    md_lines.append(f"- **99% VaR (1-day, Monte Carlo)**: ${var_99_mc:,.2f}")
    md_lines.append(f"- **95% VaR (1-day, Parametric)**: ${var_95_param:,.2f}")
    md_lines.append(f"- **Historical Max Drawdown**: {max_drawdown}%")
    md_lines.append("")
    md_lines.append("## Concentration Analysis")
    md_lines.append("")
    md_lines.append("### Top 5 Positions by Weight")
    md_lines.append("")
    md_lines.append("| Ticker | Weight |")
    md_lines.append("|--------|--------|")
    for t, w in top5:
        md_lines.append(f"| {t} | {w*100:.2f}% |")
    md_lines.append("")
    md_lines.append("### Sector Allocation")
    md_lines.append("")
    md_lines.append("| Sector | Weight |")
    md_lines.append("|--------|--------|")
    for sector, w in sorted(sector_weights.items(), key=lambda x: x[1], reverse=True):
        md_lines.append(f"| {sector} | {w*100:.2f}% |")
    md_lines.append("")
    md_lines.append("## Stress Test Results")
    md_lines.append("")
    md_lines.append("| Scenario | Simulated P&L |")
    md_lines.append("|----------|--------------|")
    for scenario, pnl in stress_scenarios.items():
        md_lines.append(f"| {scenario} | ${pnl:,.2f} |")
    md_lines.append("")
    md_lines.append("## Correlation Hotspots")
    md_lines.append("")
    if hotspots:
        md_lines.append("| Asset Pair | Correlation |")
        md_lines.append("|------------|------------|")
        for t1, t2, c in hotspots:
            md_lines.append(f"| {t1}/{t2} | {c:.3f} |")
    else:
        md_lines.append("No highly correlated pairs detected (threshold: 0.75).")
    md_lines.append("")
    md_lines.append("## Actionable Insights")
    md_lines.append("")
    for insight in insights:
        md_lines.append(f"- {insight}")
    md_lines.append("")
    
    md_filename = f"risk_report_{today}.md"
    with open(md_filename, 'w') as f:
        f.write('\n'.join(md_lines))
    
    print(f"Risk analysis complete.")
    print(f"JSON report: {json_filename}")
    print(f"Markdown report: {md_filename}")
    print(f"Portfolio total value: ${total_value:,.2f}")
    print(f"Portfolio beta vs {benchmark}: {portfolio_beta}")
    print(f"99% VaR (1-day): ${var_99_param:,.2f}")
    print(f"Max Drawdown: {max_drawdown}%")

if __name__ == '__main__':
    main()
PYSCRIPT

chmod +x /usr/local/bin/portfolio-risk-analyzer

echo "portfolio-risk-analyzer CLI installed successfully."
portfolio-risk-analyzer --help 2>/dev/null || true
echo "Setup complete."