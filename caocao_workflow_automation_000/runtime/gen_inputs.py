import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Distractor directory structure ---
dirs = [
    "company/hr/policies",
    "company/finance/q1_reports",
    "company/finance/q2_reports",
    "company/it/infrastructure",
    "company/travel/requests/pending",
    "company/travel/requests/approved",
    "company/travel/vendors",
    "company/legal/contracts",
    "company/ops/fleet",
    "company/admin/misc",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = [
    ("company/hr/policies/travel_policy_v2.txt", "Employee travel must use approved vendors. Receipts required for expenses over 50 CNY."),
    ("company/hr/policies/reimbursement_form.txt", "Fill in date, amount, purpose, and attach invoice."),
    ("company/finance/q1_reports/summary.txt", "Q1 travel spend: CNY 128,400. Taxi: 45%, Train: 35%, Flight: 20%."),
    ("company/finance/q2_reports/draft_notes.txt", "Q2 projections pending vendor quotes. Ride-hailing costs increased 12% YoY."),
    ("company/it/infrastructure/server_list.csv", "host,ip,role\napp01,10.0.0.1,web\ndb01,10.0.0.2,database"),
    ("company/travel/requests/pending/emp_zhang_20260601.txt", "Employee: Zhang Wei\nDestination: Shanghai\nDate: 2026-06-01\nPurpose: Client meeting"),
    ("company/travel/requests/pending/emp_li_20260602.txt", "Employee: Li Na\nDestination: Chengdu\nDate: 2026-06-02\nPurpose: Internal training"),
    ("company/travel/requests/approved/emp_wang_20260530.txt", "Employee: Wang Fang\nApproved amount: CNY 200\nVendor: TBD"),
    ("company/travel/vendors/current_vendors.txt", "Vendor 1: XX Taxi Corp - Basic service\nVendor 2: YY Car Rental - For long trips"),
    ("company/legal/contracts/nda_template.txt", "This Non-Disclosure Agreement is entered into by..."),
    ("company/ops/fleet/company_cars.csv", "plate,model,available\nSH-A1234,Buick GL8,yes\nSH-B5678,Toyota Camry,no"),
    ("company/admin/misc/office_supplies_q2.txt", "Pens: 50 boxes, Paper: 20 reams, Printer ink: 10 cartridges"),
]
for rel_path, content in distractors:
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- The actual problem input ---
# A messy, realistic set of employee trip scenarios that the agent must analyze
trip_scenarios_raw = {
    "company": "新星科技有限公司",
    "analysis_request_date": "2026-06-10",
    "request_from": "行政总监 陈梅",
    "context": (
        "我司正在评估是否开通曹操出行企业账户。请根据以下员工用车场景，"
        "为每个场景分析推荐的服务类型、预估费用，并说明企业账户与个人付款的区别。"
        "同时请提供平台客服热线和安全功能摘要。"
    ),
    "scenarios": [
        {
            "id": "S001",
            "employee": "张伟",
            "purpose": "普通上下班通勤，每天早上8点出发",
            "distance_km": 8,
            "duration_min": 25,
            "city": "杭州",
            "notes": "预算有限，希望最省钱的新能源方案"
        },
        {
            "id": "S002",
            "employee": "王芳",
            "purpose": "接待重要外国客户，从公司到五星级酒店",
            "distance_km": 12,
            "duration_min": 30,
            "city": "上海",
            "notes": "需要高标准服务，司机着装规范，车内整洁"
        },
        {
            "id": "S003",
            "employee": "李娜",
            "purpose": "深夜加班打车回家（凌晨1点出发）",
            "distance_km": 15,
            "duration_min": 35,
            "city": "北京",
            "notes": "公司应报销，需要安全功能提醒"
        },
        {
            "id": "S004",
            "employee": "赵明",
            "purpose": "杭州到苏州城际出行，不赶时间",
            "distance_km": 170,
            "duration_min": 130,
            "city": "杭州",
            "notes": "尽量省钱，接受等待"
        }
    ]
}

problem_input_path = os.path.join(workspace, "company/travel/vendors/caocao_analysis_request.json")
with open(problem_input_path, "w", encoding="utf-8") as f:
    json.dump(trip_scenarios_raw, f, ensure_ascii=False, indent=2)

# Also drop a confusing decoy file with wrong pricing (from a different platform)
decoy_pricing = {
    "note": "这是旧版出租车计价参考（非曹操出行官方）",
    "base_fare": 14,
    "per_km": 2.0,
    "per_min": 0.4,
    "night_hours": "22:00-05:00"
}
decoy_path = os.path.join(workspace, "company/travel/vendors/old_taxi_pricing_reference.json")
with open(decoy_path, "w", encoding="utf-8") as f:
    json.dump(decoy_pricing, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print(f"Problem input: {problem_input_path}")