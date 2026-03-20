import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import random
import json

# Set deterministic seed
np.random.seed(42)
random.seed(42)

# Generate sales data with known markers
base_date = datetime(2024, 1, 1)
dates = [base_date + timedelta(days=i*7) for i in range(52)]

# Q1 data with marker product
q1_data = {
    'date': dates[:13],
    'product': ['Widget_MARKER_Q1'] * 5 + ['Gadget'] * 4 + ['Tool'] * 4,
    'sales': [1000, 1200, 1100, 1300, 1250, 800, 900, 850, 950, 920, 600, 650, 700],
    'region': ['North', 'South', 'East', 'West', 'North'] * 2 + ['South', 'East', 'West']
}
pd.DataFrame(q1_data).to_csv('sales_q1_2024.csv', index=False)

# Q2 data with marker product  
q2_data = {
    'date': dates[13:26],
    'product': ['Widget_MARKER_Q1'] * 6 + ['Gadget'] * 4 + ['SuperTool_MARKER_Q2'] * 3,
    'sales': [1400, 1500, 1350, 1600, 1550, 1480, 950, 1000, 980, 1020, 750, 800, 820],
    'region': ['North', 'South', 'East', 'West'] * 3 + ['North']
}
pd.DataFrame(q2_data).to_csv('sales_q2_2024.csv', index=False)

# Q3 data with intentional missing values
q3_data = {
    'date': dates[26:39],
    'product': ['Widget_MARKER_Q1'] * 4 + [None] * 2 + ['Gadget'] * 4 + ['SuperTool_MARKER_Q2'] * 3,
    'sales': [1200, 1350, None, 1400, 1300, 1250, 1100, 1150, 1080, 1200, 900, 950, None],
    'region': ['North', 'South', 'East', 'West'] * 3 + ['North']
}
pd.DataFrame(q3_data).to_csv('sales_q3_2024.csv', index=False)

# Generate customer feedback with known sentiment markers
feedback_data = [
    {
        'feedback_id': 'FB_POSITIVE_MARKER_001',
        'text': 'Absolutely love the new Widget_MARKER_Q1! Best purchase ever made. Quality is outstanding and customer service was exceptional.',
        'rating': 5,
        'product': 'Widget_MARKER_Q1',
        'sentiment_expected': 'positive'
    },
    {
        'feedback_id': 'FB_NEGATIVE_MARKER_002', 
        'text': 'Very disappointed with SuperTool_MARKER_Q2. Poor quality, breaks easily, terrible experience overall.',
        'rating': 1,
        'product': 'SuperTool_MARKER_Q2',
        'sentiment_expected': 'negative'
    },
    {
        'feedback_id': 'FB_NEUTRAL_MARKER_003',
        'text': 'The Gadget is okay, nothing special but does what it says. Average product for the price.',
        'rating': 3,
        'product': 'Gadget', 
        'sentiment_expected': 'neutral'
    }
]

# Write feedback files
for i, feedback in enumerate(feedback_data):
    with open(f'customer_feedback_{i+1}.txt', 'w') as f:
        f.write(f"ID: {feedback['feedback_id']}\n")
        f.write(f"Product: {feedback['product']}\n")
        f.write(f"Rating: {feedback['rating']}/5\n")
        f.write(f"Feedback: {feedback['text']}\n")

# Create metadata file for validation
metadata = {
    'expected_products': ['Widget_MARKER_Q1', 'SuperTool_MARKER_Q2', 'Gadget', 'Tool'],
    'expected_quarters': ['Q1', 'Q2', 'Q3'],
    'marker_feedbacks': {
        'FB_POSITIVE_MARKER_001': 'positive',
        'FB_NEGATIVE_MARKER_002': 'negative', 
        'FB_NEUTRAL_MARKER_003': 'neutral'
    },
    'total_sales_q1_widget': 6350,  # Sum of Widget sales in Q1
    'total_sales_q2_supertool': 2370,  # Sum of SuperTool sales in Q2
    'missing_data_files': ['sales_q3_2024.csv']
}

with open('.test_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print('Generated input files with validation markers')