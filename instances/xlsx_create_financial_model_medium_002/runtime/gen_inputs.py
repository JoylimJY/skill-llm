import random
import json

# Set deterministic seed
random.seed(42)

# Create marker file with known content for eval verification
markers = {
    'base_cac': 150,
    'base_churn': 0.025,
    'base_arpu': 89,
    'expected_ltv_month_1': 3560,  # ARPU / churn = 89 / 0.025
    'expected_customers_month_12': 600,  # Starting with 100, adding 50/month minus churn
    'revenue_growth_year_1': 0.15,
    'model_identifier': 'SAAS_MODEL_MARKER_2024'
}

with open('model_markers.json', 'w') as f:
    json.dump(markers, f)

print('Generated marker file with validation data')