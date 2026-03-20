import os
import random
import json
from datetime import datetime, timedelta

# Set deterministic seed
random.seed(42)

# Create sample expense data
sample_expenses = [
    {"id": 1, "description": "Grocery shopping", "amount": 125.50, "category": "Food", "date": "2024-01-15"},
    {"id": 2, "description": "Gas station", "amount": 45.20, "category": "Transportation", "date": "2024-01-14"},
    {"id": 3, "description": "Netflix subscription", "amount": 15.99, "category": "Entertainment", "date": "2024-01-13"},
    {"id": 4, "description": "Office supplies", "amount": 67.80, "category": "Business", "date": "2024-01-12"},
    {"id": 5, "description": "Restaurant dinner", "amount": 89.25, "category": "Food", "date": "2024-01-11"},
    {"id": 6, "description": "Uber ride", "amount": 23.45, "category": "Transportation", "date": "2024-01-10"}
]

# Create requirements file with marker
with open('requirements.txt', 'w') as f:
    f.write('# EVAL_MARKER_REQUIREMENTS: Expense tracker app requirements\n')
    f.write('- Dashboard with expense categories and chart visualization\n')
    f.write('- Add expense form with category dropdown and date picker\n')
    f.write('- List view with search and filter functionality\n')
    f.write('- Professional modern design avoiding AI design patterns\n')
    f.write('- Sample data for demonstration\n')

# Create sample data file
with open('sample_data.json', 'w') as f:
    json.dump({
        'marker': 'EVAL_MARKER_SAMPLE_DATA',
        'expenses': sample_expenses,
        'categories': ['Food', 'Transportation', 'Entertainment', 'Business', 'Utilities', 'Healthcare']
    }, f, indent=2)

print('Generated input files with expense tracker requirements and sample data')
