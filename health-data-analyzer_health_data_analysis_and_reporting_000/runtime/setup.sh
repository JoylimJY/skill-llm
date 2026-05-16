#!/bin/bash
set -e

# ─── Build the mock healthdata MCP Flask server ───────────────────────────────
cat > /tmp/healthdata_server.py << 'PYEOF'
from flask import Flask, request, jsonify
import json, datetime

app = Flask(__name__)

# ── Fake data store ──────────────────────────────────────────────────────────

TABLES = [
    "users", "user_data_sources",
    "health_data_numeric", "fusion_health_data_numeric", "health_data_workout",
    "sleep_segments", "training_segments", "metrics_segments",
    "sleep_calculations", "strain_calculations", "recovery_calculations"
]

SCHEMAS = {
    "sleep_segments": {
        "columns": ["user_id","user_data_sources_id","type","sleep_date",
                    "asleep_duration_minutes","deep_duration_minutes","light_duration_minutes",
                    "rem_duration_minutes","awake_duration_minutes","in_bed_duration_minutes",
                    "in_bed_start_ts","in_bed_end_ts","asleep_start_ts","asleep_end_ts",
                    "avg_hr","avg_hrv","avg_spo2","avg_rr","avg_temp","data_quality_flag"]
    },
    "sleep_calculations": {
        "columns": ["calculation_id","user_id","user_data_sources_id","utc_ts",
                    "overall_score","sleep_vs_need_score","sleep_efficiency_score",
                    "sleep_consistency_score","restorative_sleep_score","rem_sleep_score",
                    "deep_sleep_score","sleep_debt","current_sleep_needed_minutes",
                    "next_sleep_needed_minutes","personalized_baseline","time_asleep_baseline"]
    },
    "recovery_calculations": {
        "columns": ["calculation_id","user_id","user_data_sources_id","utc_ts",
                    "overall_recovery","overall_z_score","metrics_count","interpretation","warning",
                    "optimal_range_min","optimal_range_max",
                    "hrv","hrv_score","hrv_level","hrv_baseline","hrv_baseline_variance",
                    "hrv_optimal_range_min","hrv_optimal_range_max",
                    "rhr","rhr_score","rhr_level","rhr_baseline","rhr_baseline_variance",
                    "spo2","spo2_score","spo2_level","spo2_baseline",
                    "temp","temp_score","temp_level","temp_baseline"]
    },
    "metrics_segments": {
        "columns": ["user_id","user_data_sources_id","type","value","unit",
                    "target_date","date_from","date_to"]
    },
    "training_segments": {
        "columns": ["user_id","user_data_sources_id","workout_id","calculation_id",
                    "workout_activity_type","date_from","date_to","duration",
                    "avg_hr","max_hr","min_hr","user_max_hr","rest_hr","hr_zone",
                    "total_energy_burned","total_distance","total_steps","event_load"]
    },
    "strain_calculations": {
        "columns": ["user_id","user_data_sources_id","utc_ts",
                    "overall_strain","daily_load","acute_load","chronic_load","acwr",
                    "strain_zone","activity_score","workout_count","steps_count","calories_count"]
    },
    "users": {
        "columns": ["id","external_id","email","username","age","gender","height","weight","is_deleted"]
    },
    "user_data_sources": {
        "columns": ["id","user_id","source_platform","source_name","source_device_id"]
    },
}

# ── Fake query results ────────────────────────────────────────────────────────

def make_sleep_segments(start_date, end_date):
    import datetime
    rows = []
    base = datetime.date(2026, 3, 1)
    end  = datetime.date(2026, 3, 7)
    # Parse actual dates for filtering
    try:
        base = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end  = datetime.datetime.strptime(end_date,   "%Y-%m-%d").date()
    except:
        pass
    data = [
        # (sleep_date, asleep_min, deep_min, light_min, rem_min, awake_min, avg_hrv, avg_spo2, quality)
        ("2026-03-01", 412, 78, 198, 104, 18, 45.2, 97.1, "normal"),
        ("2026-03-02", 385, 65, 195,  92, 22, 41.8, 96.8, "normal"),
        ("2026-03-03", 430, 85, 205, 112, 14, 48.3, 97.4, "normal"),
        ("2026-03-04", 358, 55, 190,  85, 30, 38.9, 96.5, "normal"),
        ("2026-03-05", 401, 72, 200, 100, 20, 43.1, 97.0, "normal"),
        ("2026-03-06", 445, 90, 210, 118, 12, 50.7, 97.6, "normal"),
        ("2026-03-07", 395, 68, 198,  98, 18, 42.5, 96.9, "normal"),
    ]
    for d in data:
        sleep_d = datetime.datetime.strptime(d[0], "%Y-%m-%d").date()
        if base <= sleep_d <= end:
            # in_bed_end_ts is what filters sleep_segments
            in_bed_end = int(datetime.datetime(2026, sleep_d.month, sleep_d.day, 7, 30).timestamp())
            rows.append({
                "user_id": 1001,
                "user_data_sources_id": 42,
                "type": "PRIMARY",
                "sleep_date": d[0],
                "asleep_duration_minutes": d[1],
                "deep_duration_minutes": d[2],
                "light_duration_minutes": d[3],
                "rem_duration_minutes": d[4],
                "awake_duration_minutes": d[5],
                "in_bed_duration_minutes": d[1] + d[5],
                "in_bed_start_ts": in_bed_end - (d[1]+d[5])*60,
                "in_bed_end_ts": in_bed_end,
                "asleep_start_ts": in_bed_end - d[1]*60,
                "asleep_end_ts": in_bed_end,
                "avg_hr": 55.0,
                "avg_hrv": d[6],
                "avg_spo2": d[7],
                "avg_rr": 14.5,
                "avg_temp": 36.6,
                "data_quality_flag": d[8]
            })
    return rows

def make_sleep_calculations(start_date, end_date):
    import datetime
    rows = []
    data = [
        ("2026-03-01", 72.5, -25,  68),
        ("2026-03-02", 68.1, -45,  64),
        ("2026-03-03", 78.3,  10,  75),
        ("2026-03-04", 62.4, -60,  58),
        ("2026-03-05", 74.0,  -5,  70),
        ("2026-03-06", 80.2,  30,  78),
        ("2026-03-07", 75.1,   5,  72),
    ]
    try:
        s = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        e = datetime.datetime.strptime(end_date,   "%Y-%m-%d").date()
    except:
        s = datetime.date(2026,3,1); e = datetime.date(2026,3,7)
    for i, d in enumerate(data):
        utc_dt = datetime.datetime(2026, 3, i+1, 8, 0, 0)
        if s <= utc_dt.date() <= e:
            rows.append({
                "calculation_id": 5000+i,
                "user_id": 1001,
                "user_data_sources_id": 42,
                "utc_ts": utc_dt.isoformat(),
                "overall_score": d[1],
                "sleep_vs_need_score": d[3],
                "sleep_efficiency_score": d[1] + 3,
                "sleep_consistency_score": d[1] - 5,
                "restorative_sleep_score": d[1] + 1,
                "rem_sleep_score": d[1] - 2,
                "deep_sleep_score": d[1] + 2,
                "sleep_debt": d[2],
                "current_sleep_needed_minutes": 450,
                "next_sleep_needed_minutes": 460 if d[2] < 0 else 440,
                "personalized_baseline": 73.0,
                "time_asleep_baseline": 420
            })
    return rows

def make_recovery_calculations(start_date, end_date):
    import datetime
    rows = []
    data = [
        # (date, overall_recovery, hrv, hrv_score, hrv_level, hrv_baseline, rhr, rhr_score, spo2, spo2_score, temp, interpretation)
        ("2026-03-01", 65.2, 45.2, 63.1, "normal", 44.0, 58.0, 62.0, 97.1, 88.0, 36.6, "moderate"),
        ("2026-03-02", 58.7, 41.8, 55.4, "low",    44.0, 61.0, 55.0, 96.8, 82.0, 36.7, "low"),
        ("2026-03-03", 72.1, 48.3, 72.8, "normal", 44.0, 56.0, 70.0, 97.4, 92.0, 36.5, "good"),
        ("2026-03-04", 51.3, 38.9, 47.2, "low",    44.0, 64.0, 44.0, 96.5, 78.0, 36.8, "low"),
        ("2026-03-05", 68.4, 43.1, 66.5, "normal", 44.0, 59.0, 64.0, 97.0, 86.0, 36.6, "moderate"),
        ("2026-03-06", 76.3, 50.7, 79.3, "high",   44.0, 55.0, 76.0, 97.6, 94.0, 36.4, "good"),
        ("2026-03-07", 70.5, 42.5, 68.1, "normal", 44.0, 57.0, 67.0, 96.9, 89.0, 36.5, "moderate"),
    ]
    try:
        s = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        e = datetime.datetime.strptime(end_date,   "%Y-%m-%d").date()
    except:
        s = datetime.date(2026,3,1); e = datetime.date(2026,3,7)
    for i, d in enumerate(data):
        utc_dt = datetime.datetime(2026, 3, i+1, 9, 0, 0)
        if s <= utc_dt.date() <= e:
            rows.append({
                "calculation_id": 6000+i,
                "user_id": 1001,
                "user_data_sources_id": 42,
                "utc_ts": utc_dt.isoformat(),
                "overall_recovery": d[1],
                "overall_z_score": (d[1]-65)/10.0,
                "metrics_count": 5,
                "interpretation": d[11],
                "warning": "" if d[1] >= 60 else "recovery_below_threshold",
                "optimal_range_min": 60.0,
                "optimal_range_max": 85.0,
                "hrv": d[2],
                "hrv_score": d[3],
                "hrv_level": d[4],
                "hrv_baseline": d[5],
                "hrv_baseline_variance": 4.5,
                "hrv_optimal_range_min": 38.0,
                "hrv_optimal_range_max": 55.0,
                "rhr": d[6],
                "rhr_score": d[7],
                "rhr_level": "normal" if d[6] < 62 else "elevated",
                "rhr_baseline": 57.0,
                "rhr_baseline_variance": 3.0,
                "spo2": d[8],
                "spo2_score": d[9],
                "spo2_level": "normal",
                "spo2_baseline": 97.0,
                "temp": d[10],
                "temp_score": 80.0,
                "temp_level": "normal",
                "temp_baseline": 36.6
            })
    return rows

def make_metrics_segments(start_date, end_date):
    import datetime
    rows = []
    try:
        s = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        e = datetime.datetime.strptime(end_date,   "%Y-%m-%d").date()
    except:
        s = datetime.date(2026,3,1); e = datetime.date(2026,3,7)
    types_vals = [
        ("RESTING_HEART_RATE", [58,61,56,64,59,55,57], "bpm"),
        ("HEART_RATE_VARIABILITY_SDNN", [45.2,41.8,48.3,38.9,43.1,50.7,42.5], "ms"),
        ("BLOOD_OXYGEN", [97.1,96.8,97.4,96.5,97.0,97.6,96.9], "%"),
        ("RESPIRATORY_RATE", [14.5,15.1,14.2,15.8,14.6,13.9,14.4], "breaths/min"),
        ("BODY_TEMPERATURE", [36.6,36.7,36.5,36.8,36.6,36.4,36.5], "°C"),
    ]
    cur = s
    idx = 0
    while cur <= e:
        for typ, vals, unit in types_vals:
            rows.append({
                "user_id": 1001,
                "user_data_sources_id": 42,
                "type": typ,
                "value": vals[idx % 7],
                "unit": unit,
                "target_date": cur.isoformat(),
                "date_from": int(datetime.datetime(cur.year, cur.month, cur.day, 6, 0).timestamp()),
                "date_to":   int(datetime.datetime(cur.year, cur.month, cur.day, 8, 0).timestamp()),
            })
        cur += datetime.timedelta(days=1)
        idx += 1
    return rows

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/tool/list_available_tables", methods=["POST","GET"])
def list_tables():
    return jsonify({"tables": TABLES})

@app.route("/tool/get_table_schema", methods=["POST","GET"])
def get_schema():
    raw = request.args.get("table_list") or (request.json or {}).get("table_list","[]")
    try:
        tables = json.loads(raw)
    except:
        tables = []
    result = {t: SCHEMAS.get(t, {"columns": []}) for t in tables}
    return jsonify({"schemas": result})

@app.route("/tool/query_table_data", methods=["POST","GET"])
def query_data():
    args = request.args if request.method == "GET" else (request.json or {})
    table = args.get("table_name","")
    start = args.get("start_date","2026-03-01")
    end   = args.get("end_date","2026-03-07")

    dispatch = {
        "sleep_segments":       lambda: make_sleep_segments(start, end),
        "sleep_calculations":   lambda: make_sleep_calculations(start, end),
        "recovery_calculations":lambda: make_recovery_calculations(start, end),
        "metrics_segments":     lambda: make_metrics_segments(start, end),
        "training_segments":    lambda: [],
        "strain_calculations":  lambda: [],
        "users":                lambda: [{"id":1001,"username":"health_user","age":32,"gender":"M","height":178,"weight":72}],
        "user_data_sources":    lambda: [{"id":42,"user_id":1001,"source_platform":"appleHealth","source_name":"WHOOP","source_device_id":"WHOOP-001"}],
        "health_data_numeric":  lambda: [],
        "fusion_health_data_numeric": lambda: [],
        "health_data_workout":  lambda: [],
    }
    rows = dispatch.get(table, lambda: [])()
    return jsonify({"table": table, "rows": rows, "count": len(rows)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5400, debug=False)
PYEOF

# ─── Build the mcporter CLI wrapper ──────────────────────────────────────────
cat > /usr/local/bin/mcporter << 'SHEOF'
#!/bin/bash
# mcporter - MCP client CLI wrapper
# Usage: mcporter call healthdata.<method> [key=value ...]

if [ "$1" != "call" ] && [ "$1" != "list" ]; then
    echo "Usage: mcporter call <server>.<method> [args...]" >&2
    exit 1
fi

if [ "$1" == "list" ]; then
    echo "Available servers:"
    echo "  healthdata  (running on localhost:5400)"
    exit 0
fi

# Parse: mcporter call healthdata.<method> [key=value ...]
CALL_TARGET="$2"
shift 2

SERVER=$(echo "$CALL_TARGET" | cut -d. -f1)
METHOD=$(echo "$CALL_TARGET" | cut -d. -f2-)

if [ "$SERVER" != "healthdata" ]; then
    echo "Error: Unknown server '$SERVER'" >&2
    exit 1
fi

# Build query string from key=value pairs
QUERY_PARAMS=""
for arg in "$@"; do
    KEY=$(echo "$arg" | cut -d= -f1)
    # Value may contain '=' so use parameter expansion
    VAL="${arg#*=}"
    # URL-encode spaces in value (basic)
    VAL_ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$VAL" 2>/dev/null || echo "$VAL")
    if [ -z "$QUERY_PARAMS" ]; then
        QUERY_PARAMS="?${KEY}=${VAL_ENC}"
    else
        QUERY_PARAMS="${QUERY_PARAMS}&${KEY}=${VAL_ENC}"
    fi
done

URL="http://localhost:5400/tool/${METHOD}${QUERY_PARAMS}"

RESPONSE=$(curl -sf "$URL" 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "Error: Failed to connect to healthdata server. Is it running? Try: mcporter list" >&2
    exit 1
fi

echo "$RESPONSE"
SHEOF

chmod +x /usr/local/bin/mcporter

# ─── Start the Flask server in the background ─────────────────────────────────
nohup python3 /tmp/healthdata_server.py > /tmp/healthdata_server.log 2>&1 &
echo $! > /tmp/healthdata_server.pid

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -sf http://localhost:5400/tool/list_available_tables > /dev/null 2>&1; then
        echo "[setup] healthdata MCP server is ready on port 5400"
        break
    fi
    sleep 1
done

# Verify mcporter works
echo "[setup] Testing mcporter..."
mcporter list
mcporter call healthdata.list_available_tables | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'[setup] Tables available: {len(d[\"tables\"])}')"

echo "[setup] Setup complete."