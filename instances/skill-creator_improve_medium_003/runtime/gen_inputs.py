#!/usr/bin/env python3
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

# Create skill directory structure
skill_dir = Path('analytics-helper')
skill_dir.mkdir(exist_ok=True)

# Create a deliberately suboptimal skill
skill_md = '''---
name: analytics-helper
description: Analyze CSV data and create visualizations. Use when users want data analysis, charts, or statistical summaries.
---

# Analytics Helper

This skill helps analyze CSV files and create visualizations.

## Process

1. Load the CSV file using pandas
2. Perform basic analysis
3. Create charts as requested
4. Save results

## Instructions

Read the CSV file and analyze it. Create charts if requested. Always save output to a file.

Make sure to handle missing data appropriately.

'''

with open(skill_dir / 'SKILL.md', 'w') as f:
    f.write(skill_md)

# Create evals directory and test data
evals_dir = skill_dir / 'evals'
evals_dir.mkdir(exist_ok=True)

# Generate test CSV files with marker content
sales_data = pd.DataFrame({
    'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    'revenue': [15000, 18000, 22000, 19000, 25000, 28000],
    'customers': [150, 180, 220, 190, 250, 280],
    'region': ['North', 'South', 'North', 'West', 'East', 'South']
})
sales_data.to_csv(evals_dir / 'sales_data.csv', index=False)

# Generate performance data with some missing values
performance_data = pd.DataFrame({
    'employee_id': [1001, 1002, 1003, 1004, 1005],
    'department': ['Engineering', 'Sales', 'Marketing', 'Engineering', 'Sales'], 
    'score': [85.5, np.nan, 92.3, 78.9, 88.1],
    'projects_completed': [12, 8, 15, 10, 11],
    'marker_field': ['TEST_MARKER_ENG', 'TEST_MARKER_SALES', 'TEST_MARKER_MKT', 'TEST_MARKER_ENG2', 'TEST_MARKER_SALES2']
})
performance_data.to_csv(evals_dir / 'performance.csv', index=False)

# Create evals.json
evals_config = {
    'skill_name': 'analytics-helper',
    'evals': [
        {
            'id': 1,
            'prompt': 'Analyze the sales_data.csv file and create a bar chart showing revenue by month. Save the chart as sales_chart.png',
            'expected_output': 'Bar chart showing monthly revenue with proper labels',
            'files': ['evals/sales_data.csv'],
            'expectations': [
                'Chart file sales_chart.png is created',
                'Chart shows revenue data for all 6 months',
                'Chart has proper axis labels',
                'Data values are correctly plotted'
            ]
        },
        {
            'id': 2, 
            'prompt': 'Load performance.csv and calculate summary statistics. Handle any missing data appropriately and save results to summary.json',
            'expected_output': 'JSON file with statistical summary handling NaN values',
            'files': ['evals/performance.csv'],
            'expectations': [
                'Summary file summary.json is created',
                'Missing values are handled correctly',
                'Statistics include mean, std, count for numeric columns',
                'Department breakdown is included'
            ]
        },
        {
            'id': 3,
            'prompt': 'Create a scatter plot from performance.csv showing relationship between score and projects_completed. Save as scatter.png and ignore any missing data points.',
            'expected_output': 'Scatter plot with proper correlation analysis',
            'files': ['evals/performance.csv'],
            'expectations': [
                'Scatter plot file scatter.png is created',
                'Missing values are excluded from plot',
                'Both axes are properly labeled',
                'Plot shows clear data points'
            ]
        }
    ]
}

with open(skill_dir / 'evals' / 'evals.json', 'w') as f:
    json.dump(evals_config, f, indent=2)

print('Generated analytics-helper skill with test data')