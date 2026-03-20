import json
import random
import os
from datetime import datetime, timedelta

# Set seed for reproducibility
random.seed(42)

# Create the main Flask application with performance issues
app_code = '''import json
import time
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from collections import defaultdict

app = Flask(__name__)

# Simulate a database with inefficient queries
class MockDatabase:
    def __init__(self):
        self.data = self._generate_data()
    
    def _generate_data(self):
        data = []
        for i in range(10000):  # Large dataset
            data.append({
                'user_id': random.randint(1, 1000),
                'metric_type': random.choice(['revenue', 'users', 'sessions', 'conversion']),
                'value': random.uniform(10, 1000),
                'timestamp': datetime.now() - timedelta(days=random.randint(0, 30)),
                'region': random.choice(['US', 'EU', 'ASIA', 'OTHER'])
            })
        return data
    
    def get_metrics(self, filters=None):
        # Inefficient: always processes full dataset
        time.sleep(0.01)  # Simulate network delay
        result = self.data.copy()
        
        if filters:
            # Inefficient filtering
            filtered = []
            for item in result:
                matches = True
                for key, value in filters.items():
                    if key in item and item[key] != value:
                        matches = False
                        break
                if matches:
                    filtered.append(item)
            result = filtered
        
        return result

db = MockDatabase()

@app.route('/api/metrics', methods=['GET'])
def get_aggregated_metrics():
    # MARKER: PERFORMANCE_ENDPOINT_START
    start_time = time.time()
    
    # Get query parameters
    metric_type = request.args.get('type')
    region = request.args.get('region')
    
    filters = {}
    if metric_type:
        filters['metric_type'] = metric_type
    if region:
        filters['region'] = region
    
    # Inefficient database query
    raw_data = db.get_metrics(filters)
    
    # Inefficient aggregation using pandas (overkill for simple aggregation)
    df = pd.DataFrame(raw_data)
    
    if df.empty:
        return jsonify({'error': 'No data found'})
    
    # Multiple inefficient operations
    results = {}
    
    # Inefficient grouping and aggregation
    for metric_type in df['metric_type'].unique():
        type_data = df[df['metric_type'] == metric_type]
        
        # Inefficient nested loops
        regional_stats = {}
        for region in type_data['region'].unique():
            region_data = type_data[type_data['region'] == region]
            
            # Inefficient calculations
            values = region_data['value'].tolist()
            regional_stats[region] = {
                'count': len(values),
                'sum': sum(values),
                'avg': sum(values) / len(values) if values else 0,
                'min': min(values) if values else 0,
                'max': max(values) if values else 0
            }
        
        results[metric_type] = regional_stats
    
    # Artificial delay to simulate complex calculations
    time.sleep(0.05)
    
    processing_time = time.time() - start_time
    # MARKER: PERFORMANCE_ENDPOINT_END
    
    return jsonify({
        'data': results,
        'processing_time': processing_time,
        'total_records': len(raw_data),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
'''

with open('app.py', 'w') as f:
    f.write(app_code)

# Create requirements.txt
requirements = '''flask==2.3.3
pandas==2.1.1
numpy==1.24.3
psutil==5.9.5
requests==2.31.0
gunicorn==21.2.0
'''

with open('requirements.txt', 'w') as f:
    f.write(requirements)

# Create a sample load test script for reference
load_test_script = '''import requests
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

def make_request(url, params=None):
    start = time.time()
    try:
        response = requests.get(url, params=params, timeout=5)
        end = time.time()
        return {
            'status_code': response.status_code,
            'response_time': end - start,
            'success': response.status_code == 200
        }
    except Exception as e:
        end = time.time()
        return {
            'status_code': 0,
            'response_time': end - start,
            'success': False,
            'error': str(e)
        }

def run_load_test(base_url, num_requests=100, concurrency=10):
    url = f"{base_url}/api/metrics"
    
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        
        for i in range(num_requests):
            params = {}
            if i % 3 == 0:
                params['type'] = 'revenue'
            if i % 4 == 0:
                params['region'] = 'US'
            
            future = executor.submit(make_request, url, params)
            futures.append(future)
        
        for future in as_completed(futures):
            results.append(future.result())
    
    return results

if __name__ == '__main__':
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5000'
    
    print(f"Running load test against {base_url}")
    results = run_load_test(base_url, num_requests=50, concurrency=5)
    
    response_times = [r['response_time'] for r in results if r['success']]
    success_rate = sum(1 for r in results if r['success']) / len(results)
    
    if response_times:
        print(f"Success Rate: {success_rate:.2%}")
        print(f"Avg Response Time: {statistics.mean(response_times):.3f}s")
        print(f"95th Percentile: {statistics.quantiles(response_times, n=20)[18]:.3f}s")
    else:
        print("All requests failed")
'''

with open('load_test.py', 'w') as f:
    f.write(load_test_script)

# Create a simple Dockerfile for the app
app_dockerfile = '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
'''

with open('Dockerfile.app', 'w') as f:
    f.write(app_dockerfile)

print("Generated Flask application with performance bottlenecks")
print("Files created: app.py, requirements.txt, load_test.py, Dockerfile.app")