import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "travel_requests/2026/Q2",
    "travel_requests/2026/Q1",
    "finance/budgets/team_travel",
    "finance/receipts/2025",
    "hr/training/overseas",
    "hr/policies",
    "ops/infra/monitoring",
    "ops/infra/deployments",
    "marketing/campaigns/asia_pacific",
    "legal/contracts/vendors",
    "product/roadmap/2026",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "travel_requests/2026/Q1/beijing_chengdu_feb.md": "# Beijing to Chengdu Feb 2026\nApproved budget: ¥2000\nTravel date: 2026-02-14\nStatus: Completed",
    "travel_requests/2026/Q2/notes.txt": "Team training trip to Tokyo confirmed for May 2026.\nDeparture: Shanghai\nReturn: May 7th\nBudget per person: ¥3000 total round trip",
    "finance/budgets/team_travel/2026_q2_budget.json": json.dumps({"team": "engineering", "q2_travel_budget": 50000, "approved": True, "currency": "CNY"}),
    "finance/receipts/2025/oct_osaka_trip.txt": "Receipt: Shanghai->Osaka Oct 2025\nFlight: ¥1800 (one way)\nHotel: ¥2400 (3 nights)",
    "hr/training/overseas/tokyo_training_agenda.md": "# Tokyo Training Agenda May 2026\n- Day 1: Arrival\n- Day 2-4: Workshop\n- Day 5: Cultural visit\n- Day 6: Departure",
    "hr/policies/travel_policy_v3.pdf.txt": "Travel Policy v3.0\n- Economy class only for domestic\n- Economy class preferred for international\n- Budget limit: ¥3000 per person for short haul",
    "ops/infra/monitoring/alert_rules.yaml": "alerts:\n  - name: high_latency\n    threshold: 500ms\n  - name: error_rate\n    threshold: 5%",
    "ops/infra/deployments/prod_deploy_log.txt": "2026-04-01 Deploy v2.3.1 to prod\n2026-03-28 Rollback v2.3.0\n2026-03-25 Deploy v2.3.0",
    "marketing/campaigns/asia_pacific/q2_plan.md": "# Asia Pacific Q2 Campaign\nTarget: Tokyo, Seoul, Singapore\nBudget: ¥500,000\nTimeline: May-June 2026",
    "legal/contracts/vendors/flight_vendor_agreement_2025.txt": "Vendor: CheapFlights Corp\nContract Period: 2025-01-01 to 2025-12-31\nDiscount: 5% on group bookings",
    "product/roadmap/2026/h1_features.md": "# H1 2026 Features\n- Feature A: AI search\n- Feature B: Price comparison\n- Feature C: Auto-booking",
    "travel_requests/2026/Q2/previous_search_attempt.json": json.dumps({
        "note": "Previous manual search - DO NOT USE",
        "origin": "上海",
        "destination": "东京",
        "results": [
            {"airline": "China Eastern", "price": 3200, "url": "http://old-url.example.com"},
        ],
        "status": "outdated"
    }),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create a SKILL.md reference directory structure (as would exist in a real env)
os.makedirs(os.path.join(workspace, "references"), exist_ok=True)

# Create the mock flyai CLI data that the mock server will serve
# This is the raw flight data that should be returned by the mock
mock_data_dir = os.path.join(workspace, ".mock_data")
os.makedirs(mock_data_dir, exist_ok=True)

# Round-trip bundled search data (18 results - triggers Case 2 >15)
bundled_results = []
airlines_data = [
    ("中国东方航空", "MU", "东方"),
    ("中国国际航空", "CA", "国航"),
    ("中国南方航空", "CZ", "南航"),
    ("日本航空", "JL", "日航"),
    ("全日空", "NH", "全日空"),
    ("春秋航空", "9C", "春秋"),
    ("吉祥航空", "HO", "吉祥"),
    ("厦门航空", "MF", "厦航"),
    ("上海航空", "FM", "上航"),
]

for i in range(18):
    airline_info = airlines_data[i % len(airlines_data)]
    flight_num = f"{airline_info[1]}{100 + i * 13}"
    is_direct = (i % 3 != 1)
    base_price = 1800 + (i * 87) + random.randint(0, 50)
    dep_hour = 6 + (i * 2) % 18
    dep_time = f"{dep_hour:02d}:00"
    arr_time = f"{(dep_hour + 4 + (0 if is_direct else 3)):02d}:30"
    duration = "4h30m" if is_direct else "7h30m"
    transfer_info = "上海浦东 → 东京成田 via 北京(等待2h30m)" if not is_direct else None
    
    result = {
        "rank": i + 1,
        "airline": airline_info[0],
        "flightNo": flight_num,
        "depTime": dep_time,
        "arrTime": arr_time,
        "duration": duration,
        "direct": is_direct,
        "transferCity": "北京" if not is_direct else None,
        "waitTime": "2h30m" if not is_direct else None,
        "price": base_price,
        "currency": "CNY",
        "detailUrl": f"https://www.fliggy.com/detail/{flight_num}?type=roundtrip",
        "jumpUrl": f"https://deprecated.fliggy.com/jump/{flight_num}",
    }
    bundled_results.append(result)

# Sort by price
bundled_results.sort(key=lambda x: x["price"])
for i, r in enumerate(bundled_results):
    r["rank"] = i + 1

with open(os.path.join(mock_data_dir, "roundtrip_bundled.json"), "w", encoding="utf-8") as f:
    json.dump({"total": len(bundled_results), "flights": bundled_results}, f, ensure_ascii=False, indent=2)

# One-way outbound search data (Shanghai -> Tokyo, 2026-05-01) - 8 results
outbound_results = []
for i in range(8):
    airline_info = airlines_data[i % len(airlines_data)]
    flight_num = f"{airline_info[1]}{200 + i * 7}"
    is_direct = (i % 4 != 2)
    base_price = 890 + (i * 130) + random.randint(0, 40)
    dep_hour = 7 + (i * 2) % 16
    dep_time = f"{dep_hour:02d}:20"
    arr_time = f"{(dep_hour + 4):02d}:50"
    duration = "4h30m" if is_direct else "7h00m"
    
    result = {
        "rank": i + 1,
        "airline": airline_info[0],
        "flightNo": flight_num,
        "depTime": dep_time,
        "arrTime": arr_time,
        "duration": duration,
        "direct": is_direct,
        "transferCity": "广州" if not is_direct else None,
        "waitTime": "2h30m" if not is_direct else None,
        "price": base_price,
        "currency": "CNY",
        "detailUrl": f"https://www.fliggy.com/detail/{flight_num}?type=oneway",
        "jumpUrl": f"https://deprecated.fliggy.com/jump/{flight_num}",
    }
    outbound_results.append(result)

outbound_results.sort(key=lambda x: x["price"])
for i, r in enumerate(outbound_results):
    r["rank"] = i + 1

with open(os.path.join(mock_data_dir, "outbound_sha_tyo.json"), "w", encoding="utf-8") as f:
    json.dump({"total": len(outbound_results), "flights": outbound_results}, f, ensure_ascii=False, indent=2)

# One-way return search data (Tokyo -> Shanghai, 2026-05-07) - 7 results
return_results = []
for i in range(7):
    airline_info = airlines_data[i % len(airlines_data)]
    flight_num = f"{airline_info[1]}{300 + i * 11}"
    is_direct = (i % 3 != 2)
    base_price = 950 + (i * 110) + random.randint(0, 35)
    dep_hour = 8 + (i * 2) % 14
    dep_time = f"{dep_hour:02d}:15"
    arr_time = f"{(dep_hour + 4):02d}:45"
    duration = "4h30m" if is_direct else "6h45m"
    
    result = {
        "rank": i + 1,
        "airline": airline_info[0],
        "flightNo": flight_num,
        "depTime": dep_time,
        "arrTime": arr_time,
        "duration": duration,
        "direct": is_direct,
        "transferCity": "青岛" if not is_direct else None,
        "waitTime": "1h30m" if not is_direct else None,
        "price": base_price,
        "currency": "CNY",
        "detailUrl": f"https://www.fliggy.com/detail/{flight_num}?type=return",
        "jumpUrl": f"https://deprecated.fliggy.com/jump/{flight_num}",
    }
    return_results.append(result)

return_results.sort(key=lambda x: x["price"])
for i, r in enumerate(return_results):
    r["rank"] = i + 1

with open(os.path.join(mock_data_dir, "return_tyo_sha.json"), "w", encoding="utf-8") as f:
    json.dump({"total": len(return_results), "flights": return_results}, f, ensure_ascii=False, indent=2)

# Budget-filtered results (max-price applied to bundled, keeping under 3000 total)
# Simulating budget filter: max-price per person round trip ~2800
budget_results = [r for r in bundled_results if r["price"] <= 2800]
# Make sure we have at least 3 but fewer edge cases
if len(budget_results) < 3:
    budget_results = bundled_results[:5]

with open(os.path.join(mock_data_dir, "roundtrip_budget_2800.json"), "w", encoding="utf-8") as f:
    json.dump({"total": len(budget_results), "flights": budget_results}, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print(f"Mock data files created in {mock_data_dir}")
print("Distractor files created across directory structure.")