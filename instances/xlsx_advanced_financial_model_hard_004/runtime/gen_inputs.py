import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
import random

random.seed(12345)
np.random.seed(12345)

# Generate historical financials
historical_data = {
    'Year': [2019, 2020, 2021, 2022, 2023],
    'Revenue': [50000000, 65000000, 85000000, 110000000, 143000000],
    'Gross_Profit': [40000000, 52000000, 68000000, 88000000, 114400000],
    'Operating_Expenses': [35000000, 45000000, 55000000, 70000000, 85000000],
    'EBITDA': [5000000, 7000000, 13000000, 18000000, 29400000],
    'Depreciation': [2000000, 2500000, 3000000, 3500000, 4000000],
    'Interest_Expense': [1000000, 1200000, 1500000, 2000000, 2500000],
    'Tax_Rate': [0.25, 0.25, 0.25, 0.25, 0.25],
    'CapEx': [3000000, 4000000, 5000000, 6000000, 7000000],
    'Working_Capital': [5000000, 6500000, 8500000, 11000000, 14300000],
    'Total_Debt': [20000000, 25000000, 30000000, 35000000, 40000000],
    'Cash': [10000000, 12000000, 15000000, 20000000, 25000000]
}

wb1 = Workbook()
ws1 = wb1.active
ws1.title = 'Historical_Financials'

for i, (key, values) in enumerate(historical_data.items()):
    ws1.cell(row=1, column=i+1).value = key
    ws1.cell(row=1, column=i+1).font = Font(bold=True)
    for j, value in enumerate(values):
        ws1.cell(row=j+2, column=i+1).value = value

# Add marker content
ws1['A10'] = 'MARKER_HISTORICAL_DATA_COMPLETE'
ws1['B10'] = 'DCF_MODEL_SOURCE'

wb1.save('financials_2019_2023.xlsx')

# Generate SaaS metrics
saas_data = {
    'Year': [2019, 2020, 2021, 2022, 2023],
    'Total_Customers': [5000, 6200, 7800, 9500, 11400],
    'ARR': [48000000, 62400000, 81120000, 104832000, 135561600],
    'New_Customers': [1500, 1200, 1600, 1700, 1900],
    'Churned_Customers': [300, 310, 390, 470, 570],
    'Monthly_Churn_Rate': [0.05, 0.042, 0.042, 0.041, 0.042],
    'ARPU': [9600, 10065, 10400, 11035, 11890],
    'Customer_Acquisition_Cost': [2400, 2600, 2800, 3000, 3200],
    'LTV_CAC_Ratio': [4.0, 3.9, 3.7, 3.7, 3.7],
    'Gross_Revenue_Retention': [0.95, 0.958, 0.958, 0.959, 0.958],
    'Net_Revenue_Retention': [1.12, 1.15, 1.18, 1.20, 1.22]
}

wb2 = Workbook()
ws2 = wb2.active
ws2.title = 'SaaS_Metrics'

for i, (key, values) in enumerate(saas_data.items()):
    ws2.cell(row=1, column=i+1).value = key
    ws2.cell(row=1, column=i+1).font = Font(bold=True)
    for j, value in enumerate(values):
        ws2.cell(row=j+2, column=i+1).value = value

# Add marker content
ws2['A10'] = 'MARKER_SAAS_METRICS_COMPLETE'
ws2['B10'] = 'ARR_DRIVEN_MODEL'
ws2['C10'] = 'CHURN_ANALYSIS_DATA'

wb2.save('saas_metrics.xlsx')