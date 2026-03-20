import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

# Historical financials CSV with messy data
historical_data = {
    'Year': ['2021', '2022', '2023'],
    'Revenue': [500000, 850000, 1200000],
    'COGS': [200000, 340000, 480000],
    'Sales & Marketing': [150000, 255000, 360000],
    'R&D': [100000, 170000, 240000],
    'General & Admin': [80000, 136000, 192000],
    'Other Expenses': [20000, 34000, 48000],
    'Employees': [12, 18, 24],
    'ARR': [450000, 765000, 1080000]
}
df_hist = pd.DataFrame(historical_data)
df_hist.to_csv('historical_financials.csv', index=False)

# Funding rounds Excel with formatting issues
funding_data = {
    'Round': ['Seed', 'Series A', 'Series B'],
    'Date': ['2021-03-15', '2022-08-20', '2024-01-10'],
    'Amount_Raised': [1000000, 5000000, 15000000],
    'Pre_Money_Valuation': [4000000, 20000000, 60000000],
    'Lead_Investor': ['Angel Fund', 'VC Partners', 'Growth Capital'],
    'Shares_Issued': [200000, 200000, 187500],
    'Share_Price': [5.00, 25.00, 80.00],
    'Notes': ['Initial funding', 'Market expansion', 'International growth']
}
df_funding = pd.DataFrame(funding_data)
with pd.ExcelWriter('funding_rounds.xlsx') as writer:
    df_funding.to_excel(writer, sheet_name='Funding_Data', index=False)

# Market projections TSV
market_data = {
    'Metric': ['Market_Size_Growth', 'Customer_Acquisition_Rate', 'Churn_Rate', 'Price_Increase', 'Employee_Growth'],
    '2024': [0.25, 0.30, 0.08, 0.05, 0.35],
    '2025': [0.23, 0.28, 0.07, 0.04, 0.30],
    '2026': [0.20, 0.25, 0.06, 0.03, 0.25],
    '2027': [0.18, 0.22, 0.05, 0.03, 0.20],
    '2028': [0.15, 0.20, 0.05, 0.02, 0.15],
    'Source': ['Industry Report 2024', 'Historical Analysis', 'Cohort Study', 'Pricing Strategy', 'Headcount Plan']
}
df_market = pd.DataFrame(market_data)
df_market.to_csv('market_projections.tsv', sep='\t', index=False)

print('Generated input files: historical_financials.csv, funding_rounds.xlsx, market_projections.tsv')