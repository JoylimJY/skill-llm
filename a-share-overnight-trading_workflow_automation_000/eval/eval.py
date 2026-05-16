import sys
import json
import csv
import os
from pathlib import Path

def load_candidate_stocks(workspace):
    """Load the original candidate stocks to verify agent's filtering logic."""
    csv_path = os.path.join(workspace, "data/raw/candidate_stocks_today.csv")
    stocks = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stocks.append(row)
    return stocks

def find_recommendation_file(workspace):
    """Find the recommendation JSON file."""
    candidates = list(Path(workspace).rglob("recommendation.json"))
    if not candidates:
        return None
    # Prefer files not in raw data directory
    return str(candidates[0])

def evaluate(workspace):
    checks = []
    
    # ===== Load recommendation file =====
    rec_path = find_recommendation_file(workspace)
    
    if rec_path is None:
        checks.append({"name": "recommendation_file_exists", "passed": False, "detail": "recommendation.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "recommendation_file_exists", "passed": True, "detail": f"Found at {rec_path}"})
    
    try:
        with open(rec_path, "r", encoding="utf-8") as f:
            rec = json.load(f)
    except Exception as e:
        checks.append({"name": "recommendation_file_valid_json", "passed": False, "detail": f"Invalid JSON: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "recommendation_file_valid_json", "passed": True, "detail": "File is valid JSON"})
    
    # ===== Check: Only ONE stock selected =====
    selected_code = None
    
    # Try to extract the selected stock code
    if "selected_stock" in rec:
        selected_code = str(rec["selected_stock"].get("code", "")).strip()
    elif "code" in rec:
        selected_code = str(rec["code"]).strip()
    elif "recommendation" in rec:
        r = rec["recommendation"]
        if isinstance(r, dict):
            selected_code = str(r.get("code", "")).strip()
    
    if not selected_code:
        checks.append({"name": "single_stock_selected", "passed": False, "detail": f"Could not find selected stock code in recommendation. Keys found: {list(rec.keys())}"})
    else:
        checks.append({"name": "single_stock_selected", "passed": True, "detail": f"Selected stock code: {selected_code}"})
    
    # ===== Determine VALID candidates per SKILL.md rules =====
    # Rules:
    # 1. Code prefix: must start with 60 or 00
    # 2. Not ST (is_st == False or 'False')
    # 3. gain_pct: 1.0 <= gain_pct <= 5.0
    # 4. volume_cny_100m > 1.0 (>1亿)
    # 5. float_mktcap_cny_100m: 50 <= mktcap <= 500
    # 6. turnover_rate_pct: 3.0 <= rate <= 10.0
    # 7. price > 5
    # 8. volume_ratio: 0.8 <= vr <= 2.0
    # 9. sector_category NOT IN ["房地产", "教育"] and not "高负债国企" and not "强周期股"
    #    (From SKILL.md: avoid 房地产, 教育, 高负债国企, 强周期股)
    
    EXCLUDED_SECTOR_CATEGORIES = {"房地产", "教育"}
    PRIORITY_ORDER = ["券商/金融", "科技/半导体", "新能源", "医药"]
    
    try:
        stocks = load_candidate_stocks(workspace)
    except Exception as e:
        checks.append({"name": "can_load_input_data", "passed": False, "detail": f"Cannot load input CSV: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    valid_stocks = []
    for s in stocks:
        code = s["code"].strip()
        is_st = s["is_st"].strip().lower() in ("true", "1", "yes")
        
        try:
            gain = float(s["gain_pct"])
            volume = float(s["volume_cny_100m"])
            mktcap = float(s["float_mktcap_cny_100m"])
            turnover = float(s["turnover_rate_pct"])
            price = float(s["price"])
            vol_ratio = float(s["volume_ratio"])
        except ValueError:
            continue
        
        sector_cat = s["sector_category"].strip()
        
        # Code prefix check
        if not (code.startswith("60") or code.startswith("00")):
            continue
        # ST check
        if is_st:
            continue
        # Gain range
        if not (1.0 <= gain <= 5.0):
            continue
        # Volume
        if volume <= 1.0:
            continue
        # Market cap
        if not (50 <= mktcap <= 500):
            continue
        # Turnover rate
        if not (3.0 <= turnover <= 10.0):
            continue
        # Price
        if price <= 5.0:
            continue
        # Volume ratio
        if not (0.8 <= vol_ratio <= 2.0):
            continue
        # Excluded sectors
        if sector_cat in EXCLUDED_SECTOR_CATEGORIES:
            continue
        
        valid_stocks.append(s)
    
    valid_codes = [s["code"] for s in valid_stocks]
    
    checks.append({
        "name": "valid_pool_identified",
        "passed": len(valid_stocks) > 0,
        "detail": f"Valid stock pool after all filters: {valid_codes}"
    })
    
    # ===== Check: Selected stock must be in valid pool =====
    if selected_code:
        in_valid_pool = selected_code in valid_codes
        checks.append({
            "name": "selected_stock_passes_all_filters",
            "passed": in_valid_pool,
            "detail": f"Code {selected_code} {'is' if in_valid_pool else 'is NOT'} in valid pool {valid_codes}"
        })
    else:
        checks.append({
            "name": "selected_stock_passes_all_filters",
            "passed": False,
            "detail": "No selected code to verify"
        })
        in_valid_pool = False
    
    # ===== Check: Must NOT have selected an excluded code-type stock =====
    excluded_by_code = ["300750", "300059", "688981", "688599"]  # ChiNext and STAR market
    excluded_by_st = ["600013", "000609"]
    excluded_by_sector = ["000002", "600048"]  # 房地产
    
    incorrectly_selected = (
        selected_code in excluded_by_code or
        selected_code in excluded_by_st or
        selected_code in excluded_by_sector
    )
    checks.append({
        "name": "excluded_stocks_not_selected",
        "passed": not incorrectly_selected,
        "detail": f"Code {selected_code} is {'INCORRECTLY' if incorrectly_selected else 'correctly'} not from excluded groups"
    })
    
    # ===== Check: Priority sector logic =====
    # The highest-priority sector category with valid stocks determines the selection
    # Priority: 券商/金融 > 科技/半导体 > 新能源 > 医药
    # Valid stocks in priority sectors:
    priority_valid = {}
    for s in valid_stocks:
        cat = s["sector_category"].strip()
        if cat in PRIORITY_ORDER:
            if cat not in priority_valid:
                priority_valid[cat] = []
            priority_valid[cat].append(s["code"])
    
    # Determine the highest priority sector with valid stocks
    highest_priority_sector = None
    for sector in PRIORITY_ORDER:
        if sector in priority_valid and priority_valid[sector]:
            highest_priority_sector = sector
            break
    
    if highest_priority_sector and selected_code:
        selected_stock_data = next((s for s in valid_stocks if s["code"] == selected_code), None)
        if selected_stock_data:
            selected_sector = selected_stock_data["sector_category"].strip()
            sector_priority_respected = (selected_sector == highest_priority_sector)
            checks.append({
                "name": "sector_priority_respected",
                "passed": sector_priority_respected,
                "detail": f"Highest priority sector with valid stocks: '{highest_priority_sector}'. Selected stock sector: '{selected_sector}'. Codes in highest priority sector: {priority_valid.get(highest_priority_sector, [])}"
            })
        else:
            checks.append({
                "name": "sector_priority_respected",
                "passed": False,
                "detail": f"Selected stock {selected_code} not found in valid pool, cannot verify sector priority"
            })
    else:
        checks.append({
            "name": "sector_priority_respected",
            "passed": False,
            "detail": f"Cannot verify sector priority. Highest priority sector: {highest_priority_sector}, selected_code: {selected_code}"
        })
    
    # ===== Check: Among 券商/金融 stocks, liquidity is king =====
    # Within the top priority sector, the stock with highest volume (liquidity first) should be selected
    # OR at least the selected stock must be from 券商/金融
    if highest_priority_sector == "券商/金融" and selected_code:
        zq_stocks = priority_valid.get("券商/金融", [])
        # Find the one with highest volume_cny_100m (liquidity priority)
        zq_stock_data = [s for s in valid_stocks if s["code"] in zq_stocks]
        if zq_stock_data:
            try:
                most_liquid = max(zq_stock_data, key=lambda x: float(x["volume_cny_100m"]))
                most_liquid_code = most_liquid["code"]
                liquidity_check_passed = (selected_code == most_liquid_code)
                checks.append({
                    "name": "liquidity_priority_within_sector",
                    "passed": liquidity_check_passed,
                    "detail": f"Most liquid 券商/金融 stock: {most_liquid_code} (vol={most_liquid['volume_cny_100m']}亿). Selected: {selected_code}. Liquidity is highest priority per SKILL.md."
                })
            except Exception as e:
                checks.append({
                    "name": "liquidity_priority_within_sector",
                    "passed": False,
                    "detail": f"Error comparing liquidity: {e}"
                })
        else:
            checks.append({
                "name": "liquidity_priority_within_sector",
                "passed": True,
                "detail": "No multiple stocks to compare in same sector"
            })
    else:
        checks.append({
            "name": "liquidity_priority_within_sector",
            "passed": True,
            "detail": f"Not applicable or no valid 券商/金融 stocks to compare"
        })
    
    # ===== Check: Recommendation has reasoning =====
    has_reasoning = False
    for key in ["reasoning", "reason", "analysis", "rationale", "explanation", "理由", "分析"]:
        if key in rec and rec[key]:
            has_reasoning = True
            break
    if not has_reasoning and "selected_stock" in rec:
        inner = rec["selected_stock"]
        if isinstance(inner, dict):
            for key in ["reasoning", "reason", "analysis", "rationale", "explanation"]:
                if key in inner and inner[key]:
                    has_reasoning = True
                    break
    
    checks.append({
        "name": "recommendation_includes_reasoning",
        "passed": has_reasoning,
        "detail": "Recommendation should include a reasoning/reason field explaining the selection"
    })
    
    # ===== Compute final score =====
    critical_checks = [
        "recommendation_file_exists",
        "single_stock_selected",
        "selected_stock_passes_all_filters",
        "excluded_stocks_not_selected",
        "sector_priority_respected",
        "liquidity_priority_within_sector",
    ]
    optional_checks = [
        "recommendation_includes_reasoning",
    ]
    
    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    critical_total = len(critical_checks)
    optional_passed = sum(1 for c in checks if c["name"] in optional_checks and c["passed"])
    
    score = (critical_passed / critical_total) * 0.9 + (optional_passed / len(optional_checks)) * 0.1
    
    all_critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    return {
        "passed": all_critical_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))