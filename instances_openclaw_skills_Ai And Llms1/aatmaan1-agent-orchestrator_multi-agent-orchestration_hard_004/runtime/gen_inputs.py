import json
import os
import random

random.seed(42)

os.makedirs('input_data', exist_ok=True)

market_data = {
    'report_id': 'MKT-2024-Q1',
    'sector': 'Electric Vehicles',
    'marker': 'BENCHMARK_MARKER_EV_2024',
    'companies': [
        {'name': 'TeslaMotors', 'market_share': 0.38, 'revenue_bn': 96.8, 'yoy_growth': 0.19},
        {'name': 'BYDGroup', 'market_share': 0.22, 'revenue_bn': 84.9, 'yoy_growth': 0.42},
        {'name': 'RivianAuto', 'market_share': 0.05, 'revenue_bn': 4.4, 'yoy_growth': 0.167},
        {'name': 'LucidMotors', 'market_share': 0.02, 'revenue_bn': 0.6, 'yoy_growth': -0.12}
    ],
    'total_market_size_bn': 388.1,
    'projected_cagr': 0.237,
    'key_trends': [
        'battery_cost_reduction',
        'charging_infrastructure_expansion',
        'government_incentive_programs',
        'autonomous_driving_integration'
    ],
    'risks': [
        'supply_chain_lithium_shortage',
        'regulatory_uncertainty',
        'consumer_adoption_rate'
    ]
}

with open('input_data/raw_market_data.json', 'w') as f:
    json.dump(market_data, f, indent=2)

print('Generated input_data/raw_market_data.json')
