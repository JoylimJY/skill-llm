#!/bin/bash
set -e

WORKSPACE=/workspace

# ── 1. Write the mock API server ────────────────────────────────────────────
cat > /tmp/mock_api_server.py << 'MOCK_SERVER_EOF'
#!/usr/bin/env python3
"""
Mock server simulating sunrise-sunset.org API for the Ramadan times skill.
Returns deterministic, fixed sunrise/sunset times for testing.
"""
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Fixed sunrise/sunset data for 2026-03-15 (deterministic for testing)
CITY_DATA = {
    "london": {
        "lat": 51.5074, "lon": -0.1278,
        "sunrise": "05:48",   # UTC
        "sunset": "17:52",    # UTC
        # Local times (GMT on 2026-03-15, before DST)
        "sahur_local": "05:33",
        "iftar_local": "18:07",
        "timezone": "Europe/London"
    },
    "cairo": {
        "lat": 30.0444, "lon": 31.2357,
        "sunrise": "05:57",
        "sunset": "17:59",
        # Local times (Cairo is UTC+2)
        "sahur_local": "04:42",
        "iftar_local": "18:14",
        "timezone": "Africa/Cairo"
    },
    "istanbul": {
        "lat": 41.0082, "lon": 28.9784,
        "sunrise": "06:18",
        "sunset": "18:22",
        "sahur_local": "05:03",
        "iftar_local": "18:37",
        "timezone": "Europe/Istanbul"
    },
    "default": {
        "sahur_local": "04:30",
        "iftar_local": "18:47",
        "timezone": "UTC"
    }
}

@app.route('/api/sunrise-sunset', methods=['GET'])
def sunrise_sunset():
    lat = request.args.get('lat', '41.0')
    lng = request.args.get('lng', '28.9')
    date = request.args.get('date', '2026-03-15')
    city = request.args.get('city', 'default').lower()
    
    data = CITY_DATA.get(city, CITY_DATA['default'])
    
    return jsonify({
        "results": {
            "sunrise": data.get('sahur_local', '04:30'),
            "sunset": data.get('iftar_local', '18:47'),
            "date": date,
            "city": city
        },
        "status": "OK"
    })

@app.route('/api/prayer-times', methods=['GET'])
def prayer_times():
    city = request.args.get('city', 'default').lower()
    date = request.args.get('date', '2026-03-15')
    
    data = CITY_DATA.get(city, CITY_DATA['default'])
    
    return jsonify({
        "city": city,
        "date": date,
        "times": {
            "sahur": data.get('sahur_local', '04:30'),
            "iftar": data.get('iftar_local', '18:47')
        },
        "status": "OK"
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "mock-ramadan-api"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5722, debug=False)
MOCK_SERVER_EOF

chmod +x /tmp/mock_api_server.py

# ── 2. Start the mock API server in background ───────────────────────────────
python3 /tmp/mock_api_server.py &
MOCK_PID=$!
echo "Mock API server started with PID $MOCK_PID on port 5722"

# Wait for server to be ready
sleep 2
for i in {1..15}; do
    if curl -sf http://localhost:5722/health > /dev/null 2>&1; then
        echo "Mock API server is ready."
        break
    fi
    echo "Waiting for mock API... attempt $i"
    sleep 1
done

# ── 3. Write the main skill script ──────────────────────────────────────────
cat > $WORKSPACE/skill/ramadan-times.sh << 'SKILL_EOF'
#!/bin/bash
# =============================================================================
# Ramadan Times Skill
# Fetches accurate Iftar/Sahur times for a given city and outputs them
# in the correct language format.
#
# Usage:
#   ./ramadan-times.sh [OPTIONS]
#
# Options:
#   --city CITY       City name (default: auto-detect from timezone)
#   --lang LANG       Language code: tr|en|ar|de|fr|es|ru (default: auto-detect)
#   --date DATE       Date in YYYY-MM-DD format (default: today)
#   --output FILE     Write output to FILE instead of stdout
#   --api-base URL    Override API base URL (default: from config.json)
#
# Examples:
#   ./ramadan-times.sh --city London --lang en --date 2026-03-15
#   ./ramadan-times.sh --city Cairo --lang ar --date 2026-03-15
#   ./ramadan-times.sh --city Istanbul --lang tr
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.json"

# ── Parse arguments ──────────────────────────────────────────────────────────
CITY=""
LANG=""
DATE_ARG=""
OUTPUT_FILE=""
API_BASE_OVERRIDE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --city) CITY="$2"; shift 2 ;;
        --lang) LANG="$2"; shift 2 ;;
        --date) DATE_ARG="$2"; shift 2 ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        --api-base) API_BASE_OVERRIDE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# ── Load config ──────────────────────────────────────────────────────────────
if [[ -f "$CONFIG_FILE" ]]; then
    API_BASE=$(python3 -c "import json; d=json.load(open('$CONFIG_FILE')); print(d['api']['primary'])" 2>/dev/null || echo "http://localhost:5722/api/sunrise-sunset")
else
    API_BASE="http://localhost:5722/api/sunrise-sunset"
fi

[[ -n "$API_BASE_OVERRIDE" ]] && API_BASE="$API_BASE_OVERRIDE"

# ── Defaults ──────────────────────────────────────────────────────────────────
[[ -z "$CITY" ]] && CITY="Istanbul"
[[ -z "$LANG" ]] && LANG="en"
[[ -z "$DATE_ARG" ]] && DATE_ARG=$(date +%Y-%m-%d)

CITY_LOWER=$(echo "$CITY" | tr '[:upper:]' '[:lower:]')

# ── Fetch times from API ──────────────────────────────────────────────────────
API_RESPONSE=$(curl -sf "${API_BASE}?city=${CITY_LOWER}&date=${DATE_ARG}" 2>/dev/null)

if [[ -z "$API_RESPONSE" ]]; then
    # Fallback
    SAHUR="04:30"
    IFTAR="18:47"
else
    SAHUR=$(echo "$API_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['results']['sunrise'])" 2>/dev/null || echo "04:30")
    IFTAR=$(echo "$API_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['results']['sunset'])" 2>/dev/null || echo "18:47")
fi

# ── Calculate countdown to iftar ─────────────────────────────────────────────
CURRENT_TIME=$(date +%H:%M)
CURRENT_H=$(date +%H | sed 's/^0//')
CURRENT_M=$(date +%M | sed 's/^0//')
IFTAR_H=$(echo $IFTAR | cut -d: -f1 | sed 's/^0//')
IFTAR_M=$(echo $IFTAR | cut -d: -f2 | sed 's/^0//')

CURRENT_TOTAL=$((CURRENT_H * 60 + CURRENT_M))
IFTAR_TOTAL=$((IFTAR_H * 60 + IFTAR_M))
DIFF=$((IFTAR_TOTAL - CURRENT_TOTAL))

if [[ $DIFF -lt 0 ]]; then
    DIFF=$((DIFF + 1440))
fi

COUNTDOWN_H=$((DIFF / 60))
COUNTDOWN_M=$((DIFF % 60))

# ── Format date per language ──────────────────────────────────────────────────
# Get day of week and month components
DOW_EN=$(date -d "$DATE_ARG" +%A 2>/dev/null || date +%A)
DAY_NUM=$(date -d "$DATE_ARG" +%d 2>/dev/null || date +%d)
MONTH_NUM=$(date -d "$DATE_ARG" +%m 2>/dev/null || date +%m)
YEAR=$(date -d "$DATE_ARG" +%Y 2>/dev/null || date +%Y)

# Month names
declare -A MONTHS_EN=([01]="January" [02]="February" [03]="March" [04]="April" [05]="May" [06]="June" [07]="July" [08]="August" [09]="September" [10]="October" [11]="November" [12]="December")
declare -A MONTHS_TR=([01]="Ocak" [02]="Şubat" [03]="Mart" [04]="Nisan" [05]="Mayıs" [06]="Haziran" [07]="Temmuz" [08]="Ağustos" [09]="Eylül" [10]="Ekim" [11]="Kasım" [12]="Aralık")
declare -A MONTHS_AR=([01]="يناير" [02]="فبراير" [03]="مارس" [04]="أبريل" [05]="مايو" [06]="يونيو" [07]="يوليو" [08]="أغسطس" [09]="سبتمبر" [10]="أكتوبر" [11]="نوفمبر" [12]="ديسمبر")
declare -A MONTHS_DE=([01]="Januar" [02]="Februar" [03]="März" [04]="April" [05]="Mai" [06]="Juni" [07]="Juli" [08]="August" [09]="September" [10]="Oktober" [11]="November" [12]="Dezember")
declare -A MONTHS_FR=([01]="janvier" [02]="février" [03]="mars" [04]="avril" [05]="mai" [06]="juin" [07]="juillet" [08]="août" [09]="septembre" [10]="octobre" [11]="novembre" [12]="décembre")

declare -A DAYS_TR=([Monday]="Pazartesi" [Tuesday]="Salı" [Wednesday]="Çarşamba" [Thursday]="Perşembe" [Friday]="Cuma" [Saturday]="Cumartesi" [Sunday]="Pazar")
declare -A DAYS_AR=([Monday]="الاثنين" [Tuesday]="الثلاثاء" [Wednesday]="الأربعاء" [Thursday]="الخميس" [Friday]="الجمعة" [Saturday]="السبت" [Sunday]="الأحد")
declare -A DAYS_DE=([Monday]="Montag" [Tuesday]="Dienstag" [Wednesday]="Mittwoch" [Thursday]="Donnerstag" [Friday]="Freitag" [Saturday]="Samstag" [Sunday]="Sonntag")
declare -A DAYS_FR=([Monday]="lundi" [Tuesday]="mardi" [Wednesday]="mercredi" [Thursday]="jeudi" [Friday]="vendredi" [Saturday]="samedi" [Sunday]="dimanche")

# Capitalize city
CITY_DISPLAY=$(echo "$CITY" | python3 -c "import sys; print(sys.stdin.read().strip().title())")

# ── Build output based on language ────────────────────────────────────────────
case "$LANG" in
    tr)
        DOW_LOCAL="${DAYS_TR[$DOW_EN]:-$DOW_EN}"
        MONTH_LOCAL="${MONTHS_TR[$MONTH_NUM]:-$MONTH_NUM}"
        DATE_FMT="${DAY_NUM} ${MONTH_LOCAL} ${YEAR}, ${DOW_LOCAL}"
        OUTPUT=$(printf "🌙 RAMAZAN - %s\n\n📅 %s\n\n🌅 Sahur: %s\n🌅 İftar: %s\n\n⏰ İftara: %s saat %s dakika" \
            "$CITY_DISPLAY" "$DATE_FMT" "$SAHUR" "$IFTAR" "$COUNTDOWN_H" "$COUNTDOWN_M")
        ;;
    en)
        DATE_FMT="${DOW_EN}, ${MONTHS_EN[$MONTH_NUM]:-Month} ${DAY_NUM}, ${YEAR}"
        OUTPUT=$(printf "🌙 RAMADAN - %s\n\n📅 %s\n\n🌅 Sahur: %s\n🌅 Iftar: %s\n\n⏰ Time until iftar: %s hours %s minutes" \
            "$CITY_DISPLAY" "$DATE_FMT" "$SAHUR" "$IFTAR" "$COUNTDOWN_H" "$COUNTDOWN_M")
        ;;
    ar)
        DOW_LOCAL="${DAYS_AR[$DOW_EN]:-$DOW_EN}"
        MONTH_LOCAL="${MONTHS_AR[$MONTH_NUM]:-$MONTH_NUM}"
        DATE_FMT="${DAY_NUM} ${MONTH_LOCAL} ${YEAR}, ${DOW_LOCAL}"
        OUTPUT=$(printf "🌙 رمضان - %s\n\n📅 %s\n\n🌅 السحور: %s\n🌅 الإفطار: %s\n\n⏰ الوقت حتى الإفطار: %s ساعة %s دقيقة" \
            "$CITY_DISPLAY" "$DATE_FMT" "$SAHUR" "$IFTAR" "$COUNTDOWN_H" "$COUNTDOWN_M")
        ;;
    de)
        DOW_LOCAL="${DAYS_DE[$DOW_EN]:-$DOW_EN}"
        MONTH_LOCAL="${MONTHS_DE[$MONTH_NUM]:-$MONTH_NUM}"
        DATE_FMT="${DOW_LOCAL}, ${DAY_NUM}. ${MONTH_LOCAL} ${YEAR}"
        OUTPUT=$(printf "🌙 RAMADAN - %s\n\n📅 %s\n\n🌅 Sahur: %s\n🌅 Iftar: %s\n\n⏰ Zeit bis Iftar: %s Stunden %s Minuten" \
            "$CITY_DISPLAY" "$DATE_FMT" "$SAHUR" "$IFTAR" "$COUNTDOWN_H" "$COUNTDOWN_M")
        ;;
    fr)
        DOW_LOCAL="${DAYS_FR[$DOW_EN]:-$DOW_EN}"
        MONTH_LOCAL="${MONTHS_FR[$MONTH_NUM]:-$MONTH_NUM}"
        DATE_FMT="${DOW_LOCAL} ${DAY_NUM} ${MONTH_LOCAL} ${YEAR}"
        OUTPUT=$(printf "🌙 RAMADAN - %s\n\n📅 %s\n\n🌅 Sahur : %s\n🌅 Iftar : %s\n\n⏰ Temps avant l'iftar : %s heures %s minutes" \
            "$CITY_DISPLAY" "$DATE_FMT" "$SAHUR" "$IFTAR" "$COUNTDOWN_H" "$COUNTDOWN_M")
        ;;
    *)
        # Default English
        DATE_FMT="${DOW_EN}, ${MONTHS_EN[$MONTH_NUM]:-Month} ${DAY_NUM}, ${YEAR}"
        OUTPUT=$(printf "🌙 RAMADAN - %s\n\n📅 %s\n\n🌅 Sahur: %s\n🌅 Iftar: %s\n\n⏰ Time until iftar: %s hours %s minutes" \
            "$CITY_DISPLAY" "$DATE_FMT" "$SAHUR" "$IFTAR" "$COUNTDOWN_H" "$COUNTDOWN_M")
        ;;
esac

# ── Write output ──────────────────────────────────────────────────────────────
if [[ -n "$OUTPUT_FILE" ]]; then
    echo "$OUTPUT" > "$OUTPUT_FILE"
    echo "Output written to: $OUTPUT_FILE"
else
    echo "$OUTPUT"
fi
SKILL_EOF

chmod +x $WORKSPACE/skill/ramadan-times.sh

# ── 4. Verify mock server is responding ──────────────────────────────────────
echo "Verifying mock API..."
TEST_RESP=$(curl -sf "http://localhost:5722/api/sunrise-sunset?city=london&date=2026-03-15" 2>/dev/null)
echo "Test API response: $TEST_RESP"

echo "Setup complete. Skill available at: $WORKSPACE/skill/ramadan-times.sh"
echo "Mock API available at: http://localhost:5722"