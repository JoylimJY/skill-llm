#!/usr/bin/env bash
set -e

# ── Create the mock flyai CLI ─────────────────────────────────────────────────
# This mock simulates the real flyai-cli, logs all calls, and returns
# structured JSON responses. Critically, it implements the Case 2 fallback
# trigger: search-hotels for 京都 WITH date filters returns only 1 result.

mkdir -p /usr/local/lib/flyai-mock

cat > /usr/local/lib/flyai-mock/flyai_mock.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock flyai CLI for evaluation purposes.
Logs every invocation to /tmp/flyai_calls.log
"""
import sys
import json
import os
import datetime
import hashlib

LOG_FILE = "/tmp/flyai_calls.log"

def log_call(args):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        entry = {
            "ts": datetime.datetime.utcnow().isoformat(),
            "args": args
        }
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))

def handle_version():
    print("flyai-cli v1.2.3")

def handle_fliggy_fast_search(args):
    query = ""
    for i, a in enumerate(args):
        if a == "--query" and i+1 < len(args):
            query = args[i+1]
    result = {
        "status": "success",
        "query": query,
        "results": [
            {
                "title": "日本旅游签证办理指南",
                "summary": "中国大陆公民赴日需提前申请签证。可申请单次、三年或五年多次往返签证。材料：护照、照片、在职证明、银行流水。办理周期约5-7个工作日。",
                "url": "https://fliggy.com/visa/japan/guide",
                "type": "visa_info"
            },
            {
                "title": "日本签证费用",
                "summary": "签证费约165元人民币，通过旅行社代办约300-500元含服务费。",
                "url": "https://fliggy.com/visa/japan/cost",
                "type": "visa_info"
            }
        ]
    }
    print_json(result)

def handle_search_flight(args):
    origin = ""
    destination = ""
    dep_date = ""
    sort_type = "3"
    dep_date_start = ""
    dep_date_end = ""
    i = 0
    while i < len(args):
        if args[i] == "--origin" and i+1 < len(args):
            origin = args[i+1]; i += 2
        elif args[i] == "--destination" and i+1 < len(args):
            destination = args[i+1]; i += 2
        elif args[i] == "--dep-date" and i+1 < len(args):
            dep_date = args[i+1]; i += 2
        elif args[i] == "--sort-type" and i+1 < len(args):
            sort_type = args[i+1]; i += 2
        elif args[i] == "--dep-date-start" and i+1 < len(args):
            dep_date_start = args[i+1]; i += 2
        elif args[i] == "--dep-date-end" and i+1 < len(args):
            dep_date_end = args[i+1]; i += 2
        else:
            i += 1

    # Return flight: origin=大阪 or osaka
    if "阪" in origin or origin.lower() in ["osaka", "大阪"]:
        flights = [
            {"flight_no": "MU557", "airline": "中国东方航空", "origin": origin, "destination": destination,
             "dep_time": "18:30", "arr_time": "21:45", "price": 2180, "currency": "CNY",
             "url": "https://fliggy.com/flight/MU557", "seats_left": 4},
            {"flight_no": "CA831", "airline": "中国国际航空", "origin": origin, "destination": destination,
             "dep_time": "20:00", "arr_time": "23:10", "price": 2350, "currency": "CNY",
             "url": "https://fliggy.com/flight/CA831", "seats_left": 7}
        ]
    else:
        flights = [
            {"flight_no": "MU291", "airline": "中国东方航空", "origin": origin, "destination": destination,
             "dep_time": "09:00", "arr_time": "13:30", "price": 2560, "currency": "CNY",
             "url": "https://fliggy.com/flight/MU291", "seats_left": 3},
            {"flight_no": "NH922", "airline": "全日空", "origin": origin, "destination": destination,
             "dep_time": "11:25", "arr_time": "15:55", "price": 2890, "currency": "CNY",
             "url": "https://fliggy.com/flight/NH922", "seats_left": 9},
            {"flight_no": "JL881", "airline": "日本航空", "origin": origin, "destination": destination,
             "dep_time": "14:00", "arr_time": "18:20", "price": 3100, "currency": "CNY",
             "url": "https://fliggy.com/flight/JL881", "seats_left": 2}
        ]

    print_json({"status": "success", "flights": flights, "lowest_price": flights[0]["price"]})

def handle_search_hotels(args):
    dest = ""
    check_in = ""
    check_out = ""
    sort = "rate_desc"
    key_words = ""
    max_price = None
    i = 0
    while i < len(args):
        if args[i] == "--dest-name" and i+1 < len(args):
            dest = args[i+1]; i += 2
        elif args[i] == "--check-in-date" and i+1 < len(args):
            check_in = args[i+1]; i += 2
        elif args[i] == "--check-out-date" and i+1 < len(args):
            check_out = args[i+1]; i += 2
        elif args[i] == "--sort" and i+1 < len(args):
            sort = args[i+1]; i += 2
        elif args[i] == "--key-words" and i+1 < len(args):
            key_words = args[i+1]; i += 2
        elif args[i] == "--max-price" and i+1 < len(args):
            max_price = args[i+1]; i += 2
        else:
            i += 1

    dest_lower = dest.lower()

    # CRITICAL: 京都 WITH date filters → only 1 result (triggers Case 2 fallback)
    kyoto_names = ["京都", "kyoto"]
    is_kyoto = any(k in dest for k in kyoto_names) or dest_lower == "kyoto"

    if is_kyoto and (check_in or check_out):
        # Sparse result — should trigger fallback
        hotels = [
            {"name": "京都格兰维亚酒店", "stars": 5, "price_per_night": 1280,
             "rating": 4.8, "url": "https://fliggy.com/hotel/kyoto/granvia",
             "address": "京都站内", "available_rooms": 1}
        ]
    elif is_kyoto:
        # After fallback (no date filters) → 3 results
        hotels = [
            {"name": "京都格兰维亚酒店", "stars": 5, "price_per_night": 1280,
             "rating": 4.8, "url": "https://fliggy.com/hotel/kyoto/granvia", "address": "京都站内"},
            {"name": "The Thousand Kyoto", "stars": 5, "price_per_night": 980,
             "rating": 4.7, "url": "https://fliggy.com/hotel/kyoto/thousand", "address": "京都站徒步5分钟"},
            {"name": "京都东方快车酒店", "stars": 4, "price_per_night": 650,
             "rating": 4.5, "url": "https://fliggy.com/hotel/kyoto/orient", "address": "四条烏丸"}
        ]
    elif "东京" in dest or dest_lower in ["tokyo", "东京"]:
        hotels = [
            {"name": "东京帝国酒店", "stars": 5, "price_per_night": 1580,
             "rating": 4.9, "url": "https://fliggy.com/hotel/tokyo/imperial", "address": "日比谷"},
            {"name": "东京新宿王子大饭店", "stars": 4, "price_per_night": 720,
             "rating": 4.6, "url": "https://fliggy.com/hotel/tokyo/prince", "address": "新宿"},
            {"name": "东京涉谷 Excel 东急", "stars": 4, "price_per_night": 680,
             "rating": 4.5, "url": "https://fliggy.com/hotel/tokyo/excel", "address": "涉谷"},
            {"name": "Dormy Inn 浅草", "stars": 3, "price_per_night": 420,
             "rating": 4.4, "url": "https://fliggy.com/hotel/tokyo/dormy", "address": "浅草"},
            {"name": "东横 INN 东京站", "stars": 3, "price_per_night": 380,
             "rating": 4.2, "url": "https://fliggy.com/hotel/tokyo/toyoko", "address": "东京站"}
        ]
    elif "大阪" in dest or dest_lower in ["osaka", "大阪"]:
        hotels = [
            {"name": "大阪洲际酒店", "stars": 5, "price_per_night": 1200,
             "rating": 4.8, "url": "https://fliggy.com/hotel/osaka/intercontinental", "address": "中之岛"},
            {"name": "大阪克罗斯酒店", "stars": 4, "price_per_night": 650,
             "rating": 4.6, "url": "https://fliggy.com/hotel/osaka/cross", "address": "难波"},
            {"name": "Dormy Inn 心斋桥", "stars": 3, "price_per_night": 480,
             "rating": 4.4, "url": "https://fliggy.com/hotel/osaka/dormy", "address": "心斋桥"},
            {"name": "大阪 APA 酒店", "stars": 3, "price_per_night": 350,
             "rating": 4.1, "url": "https://fliggy.com/hotel/osaka/apa", "address": "难波"}
        ]
    else:
        hotels = []

    print_json({"status": "success", "dest": dest, "hotels": hotels, "count": len(hotels)})

def handle_search_poi(args):
    city = ""
    category = ""
    poi_level = ""
    keyword = ""
    i = 0
    while i < len(args):
        if args[i] == "--city-name" and i+1 < len(args):
            city = args[i+1]; i += 2
        elif args[i] == "--category" and i+1 < len(args):
            category = args[i+1]; i += 2
        elif args[i] == "--poi-level" and i+1 < len(args):
            poi_level = args[i+1]; i += 2
        elif args[i] == "--keyword" and i+1 < len(args):
            keyword = args[i+1]; i += 2
        else:
            i += 1

    city_lower = city.lower()
    pois = []

    if "东京" in city or city_lower == "tokyo":
        pois = [
            {"name": "浅草寺", "category": "宗教场所", "level": 5, "rating": 4.9,
             "url": "https://fliggy.com/poi/tokyo/sensoji", "tip": "早晨7点前人少"},
            {"name": "东京晴空塔", "category": "地标建筑", "level": 5, "rating": 4.7,
             "url": "https://fliggy.com/poi/tokyo/skytree", "tip": "网上提前购票"},
            {"name": "涉谷十字路口", "category": "地标", "level": 5, "rating": 4.8,
             "url": "https://fliggy.com/poi/tokyo/shibuya", "tip": "傍晚人流最旺"},
            {"name": "新宿御苑", "category": "公园", "level": 5, "rating": 4.6,
             "url": "https://fliggy.com/poi/tokyo/shinjukugyoen", "tip": "樱花季必去"},
            {"name": "秋叶原电器街", "category": "购物", "level": 4, "rating": 4.5,
             "url": "https://fliggy.com/poi/tokyo/akihabara", "tip": "动漫周边集中地"}
        ]
    elif "京都" in city or city_lower == "kyoto":
        pois = [
            {"name": "伏见稻荷大社", "category": "宗教场所", "level": 5, "rating": 4.9,
             "url": "https://fliggy.com/poi/kyoto/fushimiinari", "tip": "千本鸟居日出最美"},
            {"name": "清水寺", "category": "宗教场所", "level": 5, "rating": 4.8,
             "url": "https://fliggy.com/poi/kyoto/kiyomizudera", "tip": "夜间特别开放"},
            {"name": "金阁寺", "category": "宗教场所", "level": 5, "rating": 4.7,
             "url": "https://fliggy.com/poi/kyoto/kinkakuji", "tip": "雪天最美"},
            {"name": "嵯峨野竹林", "category": "自然景观", "level": 4, "rating": 4.6,
             "url": "https://fliggy.com/poi/kyoto/arashiyama", "tip": "早晨人少"}
        ]
    elif "大阪" in city or city_lower == "osaka":
        pois = [
            {"name": "黑门市场", "category": "市集", "level": 4, "rating": 4.6,
             "url": "https://fliggy.com/poi/osaka/kuromon", "tip": "海鲜和小吃集中地"},
            {"name": "大阪城公园", "category": "历史遗迹", "level": 5, "rating": 4.7,
             "url": "https://fliggy.com/poi/osaka/castle", "tip": "秋叶季极美"},
            {"name": "道顿堀", "category": "市集", "level": 5, "rating": 4.8,
             "url": "https://fliggy.com/poi/osaka/dotonbori", "tip": "章鱼小丸子发源地"},
            {"name": "环球影城 USJ", "category": "主题乐园", "level": 5, "rating": 4.9,
             "url": "https://fliggy.com/poi/osaka/usj", "tip": "提前3个月购票"}
        ]

    print_json({"status": "success", "city": city, "pois": pois, "count": len(pois)})

def main():
    args = sys.argv[1:]
    log_call(args)

    if not args:
        print("flyai-cli v1.2.3")
        return

    if args[0] == "--version":
        handle_version()
        return

    # args[0] is subcommand
    cmd = args[0]
    rest = args[1:]

    if cmd == "fliggy-fast-search":
        handle_fliggy_fast_search(rest)
    elif cmd == "search-flight":
        handle_search_flight(rest)
    elif cmd == "search-hotels":
        handle_search_hotels(rest)
    elif cmd == "search-poi":
        handle_search_poi(rest)
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
PYEOF

chmod +x /usr/local/lib/flyai-mock/flyai_mock.py

# Create the `flyai` wrapper in PATH
cat > /usr/local/bin/flyai << 'SHEOF'
#!/usr/bin/env bash
exec python3 /usr/local/lib/flyai-mock/flyai_mock.py "$@"
SHEOF

chmod +x /usr/local/bin/flyai

# Initialize the call log file
touch /tmp/flyai_calls.log
chmod 666 /tmp/flyai_calls.log

echo "Mock flyai CLI installed at /usr/local/bin/flyai"
flyai --version