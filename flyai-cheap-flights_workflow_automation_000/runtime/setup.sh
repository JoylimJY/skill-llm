#!/bin/bash
set -e

# Create the mock flyai CLI server
cat > /tmp/mock_flyai_server.py << 'PYEOF'
#!/usr/bin/env python3
"""Mock flyai CLI REST server - simulates flyai search-flight responses"""
import json
import sys
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
MOCK_DATA_DIR = "/workspace/.mock_data"

@app.route('/search-flight', methods=['GET', 'POST'])
def search_flight():
    params = request.args.to_dict() if request.method == 'GET' else request.json or {}
    
    origin = params.get('origin', '')
    destination = params.get('destination', '')
    back_date = params.get('back_date', params.get('backDate', ''))
    max_price = params.get('max_price', params.get('maxPrice', None))
    dep_date = params.get('dep_date', params.get('depDate', ''))
    sort_type = params.get('sort_type', params.get('sortType', '1'))
    dep_date_start = params.get('dep_date_start', '')
    dep_date_end = params.get('dep_date_end', '')
    dep_hour_start = params.get('dep_hour_start', None)
    
    sha_origins = ['上海', 'shanghai', 'pvg', 'sha', 'SHA', 'PVG', 'Shanghai']
    tyo_dests = ['东京', 'tokyo', 'nrt', 'tyo', 'NRT', 'TYO', 'Tokyo']
    tyo_origins = ['东京', 'tokyo', 'nrt', 'tyo', 'NRT', 'TYO', 'Tokyo']
    sha_dests = ['上海', 'shanghai', 'pvg', 'sha', 'SHA', 'PVG', 'Shanghai']
    
    is_sha_to_tyo = any(o in origin for o in sha_origins) and any(d in destination for d in tyo_dests)
    is_tyo_to_sha = any(o in origin for o in tyo_origins) and any(d in destination for d in sha_dests)
    is_roundtrip = bool(back_date)
    
    if is_sha_to_tyo and is_roundtrip:
        if max_price:
            data_file = os.path.join(MOCK_DATA_DIR, "roundtrip_budget_2800.json")
        else:
            data_file = os.path.join(MOCK_DATA_DIR, "roundtrip_bundled.json")
    elif is_sha_to_tyo:
        data_file = os.path.join(MOCK_DATA_DIR, "outbound_sha_tyo.json")
    elif is_tyo_to_sha:
        data_file = os.path.join(MOCK_DATA_DIR, "return_tyo_sha.json")
    else:
        return jsonify({"total": 0, "flights": [], "error": "Route not found"})
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    flights = data['flights']
    
    # Apply dep_hour_start filter
    if dep_hour_start:
        try:
            hour_start = int(dep_hour_start)
            flights = [f for f in flights if int(f['depTime'].split(':')[0]) >= hour_start]
        except (ValueError, KeyError):
            pass
    
    # Apply max_price filter
    if max_price:
        try:
            mp = float(max_price)
            flights = [f for f in flights if f['price'] <= mp]
        except (ValueError, TypeError):
            pass
    
    # Sort by price if sort_type == 3
    if str(sort_type) == '3':
        flights = sorted(flights, key=lambda x: x['price'])
    
    # Re-rank
    for i, f in enumerate(flights):
        f['rank'] = i + 1
    
    return jsonify({"total": len(flights), "flights": flights})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "mock-flyai-server"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7788, debug=False)
PYEOF

python3 /tmp/mock_flyai_server.py &
SERVER_PID=$!
echo $SERVER_PID > /tmp/mock_server.pid

# Wait for server to start
sleep 2

# Create the flyai CLI wrapper that hits the mock server
cat > /usr/local/bin/flyai << 'BASHEOF'
#!/bin/bash
# Mock flyai CLI - translates CLI args to HTTP calls to mock server

SUBCOMMAND="$1"
shift

if [ "$SUBCOMMAND" = "search-flight" ]; then
    ORIGIN=""
    DESTINATION=""
    DEP_DATE=""
    BACK_DATE=""
    SORT_TYPE="1"
    MAX_PRICE=""
    JOURNEY_TYPE=""
    DEP_DATE_START=""
    DEP_DATE_END=""
    DEP_HOUR_START=""
    DEP_HOUR_END=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --origin) ORIGIN="$2"; shift 2;;
            --destination) DESTINATION="$2"; shift 2;;
            --dep-date) DEP_DATE="$2"; shift 2;;
            --back-date) BACK_DATE="$2"; shift 2;;
            --sort-type) SORT_TYPE="$2"; shift 2;;
            --max-price) MAX_PRICE="$2"; shift 2;;
            --journey-type) JOURNEY_TYPE="$2"; shift 2;;
            --dep-date-start) DEP_DATE_START="$2"; shift 2;;
            --dep-date-end) DEP_DATE_END="$2"; shift 2;;
            --dep-hour-start) DEP_HOUR_START="$2"; shift 2;;
            --dep-hour-end) DEP_HOUR_END="$2"; shift 2;;
            *) shift;;
        esac
    done

    URL="http://localhost:7788/search-flight?origin=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$ORIGIN'))")&destination=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$DESTINATION'))")&sort_type=$SORT_TYPE"
    
    [ -n "$DEP_DATE" ] && URL="${URL}&dep_date=${DEP_DATE}"
    [ -n "$BACK_DATE" ] && URL="${URL}&back_date=${BACK_DATE}"
    [ -n "$MAX_PRICE" ] && URL="${URL}&max_price=${MAX_PRICE}"
    [ -n "$JOURNEY_TYPE" ] && URL="${URL}&journey_type=${JOURNEY_TYPE}"
    [ -n "$DEP_DATE_START" ] && URL="${URL}&dep_date_start=${DEP_DATE_START}"
    [ -n "$DEP_DATE_END" ] && URL="${URL}&dep_date_end=${DEP_DATE_END}"
    [ -n "$DEP_HOUR_START" ] && URL="${URL}&dep_hour_start=${DEP_HOUR_START}"
    [ -n "$DEP_HOUR_END" ] && URL="${URL}&dep_hour_end=${DEP_HOUR_END}"

    curl -s "$URL"
else
    echo '{"error": "Unknown subcommand"}'
fi
BASHEOF

chmod +x /usr/local/bin/flyai

# Verify mock server is running
sleep 1
curl -s http://localhost:7788/health && echo "Mock server running OK" || echo "WARNING: Mock server may not be running"

echo "Setup complete. flyai CLI mock is ready."