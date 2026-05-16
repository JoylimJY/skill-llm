import sys
import json
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight

    # Find the output file
    matches = list(Path(workspace_dir).rglob("lamborghini_client_brief.json"))
    if not matches:
        add_check("file_exists", False, "lamborghini_client_brief.json not found anywhere in workspace", weight=3.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    filepath = matches[0]
    add_check("file_exists", True, f"Found at {filepath}", weight=1.0)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        add_check("file_parseable", False, f"JSON parse error: {e}", weight=3.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("file_parseable", True, "Valid JSON", weight=1.0)

    # ---- SECTION 1: BRAND_OVERVIEW ----
    try:
        brand = data.get("BRAND_OVERVIEW") or data.get("brand_overview") or {}
        
        # Founded year: 1963
        founded_val = str(brand.get("year_founded", brand.get("founded", brand.get("established", ""))))
        add_check("brand_founded_year", "1963" in founded_val, f"Expected 1963, got: {founded_val}", weight=1.0)
        
        # Founder
        founder_val = str(brand.get("founder", brand.get("founder_name", "")))
        add_check("brand_founder", "兰博基尼" in founder_val or "Ferruccio" in founder_val or "费鲁吉欧" in founder_val,
                  f"Expected Ferruccio/费鲁吉欧·兰博基尼, got: {founder_val}", weight=1.0)
        
        # Parent company + acquisition year
        parent_val = str(brand.get("parent_company", brand.get("parent", "")))
        acq_val = str(brand.get("acquisition_year", brand.get("acquired_year", parent_val)))
        add_check("brand_parent_vw", "大众" in parent_val or "Volkswagen" in parent_val or "VW" in parent_val,
                  f"Expected VW/大众, got: {parent_val}", weight=1.0)
        add_check("brand_acquisition_1998", "1998" in acq_val or "1998" in str(brand),
                  f"Expected acquisition year 1998, got: {acq_val}", weight=1.0)
        
        # 2023 sales: 10112
        sales_val = str(brand.get("sales_2023", brand.get("global_sales_2023", brand.get("2023_sales", ""))))
        add_check("brand_2023_sales", "10112" in sales_val or "10,112" in sales_val,
                  f"Expected 10112, got: {sales_val}", weight=1.0)
        
        # Headquarters
        hq_val = str(brand.get("headquarters", brand.get("hq", brand.get("location", ""))))
        add_check("brand_headquarters", "圣阿加塔" in hq_val or "Sant'Agata" in hq_val or "Sant" in hq_val or "博洛涅塞" in hq_val,
                  f"Expected Sant'Agata Bolognese/圣阿加塔-博洛涅塞, got: {hq_val}", weight=1.0)
    except Exception as e:
        add_check("brand_overview_section", False, f"Error processing BRAND_OVERVIEW: {e}", weight=2.0)

    # ---- SECTION 2: MODEL_COMPARISON ----
    try:
        models = data.get("MODEL_COMPARISON") or data.get("model_comparison") or {}
        
        # Helper: search nested or flat dict for a model
        def find_model(models_dict, *keys):
            for k in keys:
                if k in models_dict:
                    return models_dict[k]
            # Try case-insensitive
            for dk, dv in models_dict.items():
                for k in keys:
                    if k.lower() in dk.lower():
                        return dv
            return {}
        
        # Huracán EVO: 640Ps, 2.9s, 325km/h, 254万
        hevo = find_model(models, "Huracán EVO", "huracan_evo", "Huracan EVO", "HuracanEVO", "huracán_evo", "Huracan_EVO")
        hevo_str = json.dumps(hevo, ensure_ascii=False) if hevo else ""
        add_check("model_huracan_evo_hp", "640" in hevo_str, f"Huracán EVO HP: expected 640, data: {hevo_str[:200]}", weight=1.0)
        add_check("model_huracan_evo_0100", "2.9" in hevo_str, f"Huracán EVO 0-100: expected 2.9, data: {hevo_str[:200]}", weight=1.0)
        add_check("model_huracan_evo_price", "254" in hevo_str, f"Huracán EVO price: expected 254, data: {hevo_str[:200]}", weight=1.0)
        
        # Huracán STO: 640Ps, 3.0s, 310km/h, 334万
        hsto = find_model(models, "Huracán STO", "huracan_sto", "Huracan STO", "HuracanSTO", "huracán_sto")
        hsto_str = json.dumps(hsto, ensure_ascii=False) if hsto else ""
        add_check("model_huracan_sto_price", "334" in hsto_str, f"Huracán STO price: expected 334, data: {hsto_str[:200]}", weight=1.0)
        add_check("model_huracan_sto_topspeed", "310" in hsto_str, f"Huracán STO top speed: expected 310, data: {hsto_str[:200]}", weight=1.0)
        
        # Aventador SVJ: 770Ps, 2.8s, 350km/h, 595万
        asvj = find_model(models, "Aventador SVJ", "aventador_svj", "AventadorSVJ")
        asvj_str = json.dumps(asvj, ensure_ascii=False) if asvj else ""
        add_check("model_aventador_svj_hp", "770" in asvj_str, f"Aventador SVJ HP: expected 770, data: {asvj_str[:200]}", weight=1.0)
        add_check("model_aventador_svj_price", "595" in asvj_str, f"Aventador SVJ price: expected 595, data: {asvj_str[:200]}", weight=1.0)
        
        # Aventador Ultimae: 780Ps, 2.8s, 355km/h, 538万
        ault = find_model(models, "Aventador Ultimae", "aventador_ultimae", "AventadorUltimae")
        ault_str = json.dumps(ault, ensure_ascii=False) if ault else ""
        add_check("model_aventador_ultimae_hp", "780" in ault_str, f"Aventador Ultimae HP: expected 780, data: {ault_str[:200]}", weight=1.0)
        add_check("model_aventador_ultimae_topspeed", "355" in ault_str, f"Aventador Ultimae top speed: expected 355, data: {ault_str[:200]}", weight=1.0)
        
        # Urus S: 666Ps, 3.5s, 305km/h, 294万
        urus_s = find_model(models, "Urus S", "urus_s", "UrusS")
        urus_s_str = json.dumps(urus_s, ensure_ascii=False) if urus_s else ""
        add_check("model_urus_s_hp", "666" in urus_s_str, f"Urus S HP: expected 666, data: {urus_s_str[:200]}", weight=1.0)
        add_check("model_urus_s_0100", "3.5" in urus_s_str, f"Urus S 0-100: expected 3.5, data: {urus_s_str[:200]}", weight=1.0)
        add_check("model_urus_s_price", "294" in urus_s_str, f"Urus S price: expected 294, data: {urus_s_str[:200]}", weight=1.0)
        
        # Urus Performante: 666Ps, 3.3s, 306km/h, 329万
        urus_p = find_model(models, "Urus Performante", "urus_performante", "UrusPerformante")
        urus_p_str = json.dumps(urus_p, ensure_ascii=False) if urus_p else ""
        add_check("model_urus_performante_0100", "3.3" in urus_p_str, f"Urus Performante 0-100: expected 3.3, data: {urus_p_str[:200]}", weight=1.5)
        add_check("model_urus_performante_price", "329" in urus_p_str, f"Urus Performante price: expected 329, data: {urus_p_str[:200]}", weight=1.0)
    except Exception as e:
        add_check("model_comparison_section", False, f"Error processing MODEL_COMPARISON: {e}", weight=3.0)

    # ---- SECTION 3: LIMITED_EDITIONS ----
    try:
        limited = data.get("LIMITED_EDITIONS") or data.get("limited_editions") or {}
        limited_str = json.dumps(limited, ensure_ascii=False)
        
        # Centenario: 40 units, 190万USD
        add_check("limited_centenario_qty", "40" in limited_str, f"Centenario quantity: expected 40, found in: {limited_str[:300]}", weight=1.0)
        add_check("limited_centenario_price", "190" in limited_str, f"Centenario price: expected 190万USD, found in: {limited_str[:300]}", weight=1.0)
        
        # Veneno: 14 units, 450万USD
        add_check("limited_veneno_qty", "14" in limited_str, f"Veneno quantity: expected 14, found in: {limited_str[:300]}", weight=1.0)
        add_check("limited_veneno_price", "450" in limited_str, f"Veneno price: expected 450万USD, found in: {limited_str[:300]}", weight=1.0)
        
        # Sián: 63 units, supercapacitor tech (超级电容 or supercapacitor)
        add_check("limited_sian_qty", "63" in limited_str, f"Sián quantity: expected 63, found in: {limited_str[:300]}", weight=1.0)
        add_check("limited_sian_supercapacitor", "超级电容" in limited_str or "supercapacitor" in limited_str.lower() or "super capacitor" in limited_str.lower(),
                  f"Sián tech: expected supercapacitor/超级电容, found in: {limited_str[:300]}", weight=1.5)
        
        # Countach LPI 800-4: 112 units, 260万USD
        add_check("limited_countach_qty", "112" in limited_str, f"Countach LPI 800-4 quantity: expected 112, found in: {limited_str[:300]}", weight=1.0)
        add_check("limited_countach_price", "260" in limited_str, f"Countach LPI 800-4 price: expected 260万USD, found in: {limited_str[:300]}", weight=1.0)
    except Exception as e:
        add_check("limited_editions_section", False, f"Error processing LIMITED_EDITIONS: {e}", weight=2.0)

    # ---- SECTION 4: PURCHASE_PROCESS ----
    try:
        purchase = data.get("PURCHASE_PROCESS") or data.get("purchase_process") or {}
        purchase_str = json.dumps(purchase, ensure_ascii=False)
        
        # Deposit: 50-100万
        add_check("purchase_deposit_min", "50" in purchase_str, f"Deposit min: expected 50万, found in: {purchase_str[:300]}", weight=1.0)
        add_check("purchase_deposit_max", "100" in purchase_str, f"Deposit max: expected 100万, found in: {purchase_str[:300]}", weight=1.0)
        
        # Production wait: 4-12 months
        add_check("purchase_wait_time", "4" in purchase_str and "12" in purchase_str,
                  f"Wait time: expected 4-12 months, found in: {purchase_str[:300]}", weight=1.0)
        
        # Finance: 30% down, 12-60 months, 4.5%
        add_check("purchase_finance_downpayment", "30" in purchase_str, f"Finance down payment: expected 30%, found in: {purchase_str[:300]}", weight=1.0)
        add_check("purchase_finance_rate", "4.5" in purchase_str, f"Finance rate: expected 4.5%, found in: {purchase_str[:300]}", weight=1.5)
        add_check("purchase_finance_terms", "12" in purchase_str and "60" in purchase_str,
                  f"Finance terms: expected 12-60 months, found in: {purchase_str[:300]}", weight=1.0)
        
        # Customization: 200+ colors, 4-8 months, 10-100万
        add_check("purchase_custom_colors", "200" in purchase_str, f"Custom colors: expected 200+, found in: {purchase_str[:300]}", weight=1.0)
        add_check("purchase_custom_leadtime", ("4" in purchase_str) and ("8" in purchase_str),
                  f"Custom lead time: expected 4-8 months, found in: {purchase_str[:300]}", weight=1.0)
        add_check("purchase_custom_cost", "10" in purchase_str and "100" in purchase_str,
                  f"Custom cost: expected 10-100万, found in: {purchase_str[:300]}", weight=1.0)
    except Exception as e:
        add_check("purchase_process_section", False, f"Error processing PURCHASE_PROCESS: {e}", weight=2.0)

    # ---- SECTION 5: AFTERSALES ----
    try:
        after = data.get("AFTERSALES") or data.get("aftersales") or {}
        after_str = json.dumps(after, ensure_ascii=False)
        
        # Vehicle warranty: 3 years
        # Paint warranty: 3 years
        # Parts warranty: 2 years
        # The key trap: distractor says 2yr vehicle, 2yr paint, 1yr parts — must use SKILL.md values
        
        def check_warranty_years(section_data, field_keys, expected_year, name, detail):
            for key in field_keys:
                val = section_data.get(key, "")
                if str(expected_year) in str(val):
                    return True
            # Also check in full string with context
            return False
        
        # Check vehicle warranty = 3 years  
        veh_warranty = after.get("vehicle_warranty", after.get("warranty_vehicle", after.get("整车保修", "")))
        add_check("aftersales_vehicle_warranty_3yr", "3" in str(veh_warranty) or 
                  ("vehicle" in after_str.lower() and "3" in after_str),
                  f"Vehicle warranty: expected 3 years, got: {str(veh_warranty)}", weight=1.0)
        
        # Parts warranty = 2 years (trap: distractor says 1 year)
        parts_warranty = after.get("parts_warranty", after.get("warranty_parts", after.get("配件保修", "")))
        # Check that 2 appears near parts context
        add_check("aftersales_parts_warranty_2yr", "2" in str(parts_warranty) or
                  ("part" in after_str.lower() and "2" in after_str),
                  f"Parts warranty: expected 2 years, got: {str(parts_warranty)}", weight=1.0)
        
        # Hotline: 400-120-6699 (trap: distractor has wrong number)
        add_check("aftersales_hotline_correct", "400-120-6699" in after_str or "4001206699" in after_str.replace("-",""),
                  f"Hotline: expected 400-120-6699, found in: {after_str[:300]}", weight=1.5)
        
        # Small service: every 1yr/1.5万km, 5000-10000元
        add_check("aftersales_small_service_price", "5000" in after_str and "10000" in after_str,
                  f"Small service price: expected 5000-10000, found in: {after_str[:300]}", weight=1.0)
    except Exception as e:
        add_check("aftersales_section", False, f"Error processing AFTERSALES: {e}", weight=2.0)

    # ---- SECTION 6: BRAND_MILESTONES ----
    try:
        milestones = data.get("BRAND_MILESTONES") or data.get("brand_milestones") or {}
        milestones_str = json.dumps(milestones, ensure_ascii=False)
        
        # 1963: founded
        add_check("milestone_1963", "1963" in milestones_str and ("创立" in milestones_str or "founded" in milestones_str.lower() or "established" in milestones_str.lower()),
                  f"1963 milestone: expected company founding, found: {milestones_str[:300]}", weight=1.0)
        
        # 1966: Miura - mid-engine pioneer
        add_check("milestone_1966", "1966" in milestones_str and "Miura" in milestones_str,
                  f"1966 milestone: expected Miura launch, found: {milestones_str[:300]}", weight=1.0)
        
        # 1990: Diablo - first 320km/h production car
        add_check("milestone_1990", "1990" in milestones_str and "Diablo" in milestones_str,
                  f"1990 milestone: expected Diablo, found: {milestones_str[:300]}", weight=1.0)
        
        # 1998: acquired by VW
        add_check("milestone_1998", "1998" in milestones_str and ("大众" in milestones_str or "VW" in milestones_str or "Volkswagen" in milestones_str or "收购" in milestones_str or "acquired" in milestones_str.lower()),
                  f"1998 milestone: expected VW acquisition, found: {milestones_str[:300]}", weight=1.0)
        
        # 2018: Urus launch
        add_check("milestone_2018", "2018" in milestones_str and "Urus" in milestones_str,
                  f"2018 milestone: expected Urus launch, found: {milestones_str[:300]}", weight=1.0)
    except Exception as e:
        add_check("brand_milestones_section", False, f"Error processing BRAND_MILESTONES: {e}", weight=2.0)

    # ---- SECTION 7: CHINA_DEALERS ----
    try:
        dealers = data.get("CHINA_DEALERS") or data.get("china_dealers") or []
        dealers_str = json.dumps(dealers, ensure_ascii=False)
        
        # All 6 cities present
        cities = ["北京", "上海", "广州", "深圳", "成都", "杭州"]
        for city in cities:
            add_check(f"dealer_city_{city}", city in dealers_str,
                      f"Dealer city {city}: not found in dealers data", weight=0.5)
        
        # Specific dealer names
        add_check("dealer_beijing_name", "英杰宝" in dealers_str, f"Beijing dealer: expected 英杰宝, found: {dealers_str[:400]}", weight=0.5)
        add_check("dealer_shanghai_name", "永达" in dealers_str, f"Shanghai dealer: expected 永达, found: {dealers_str[:400]}", weight=0.5)
        
        # Key addresses
        add_check("dealer_beijing_address", "朝阳" in dealers_str and "金港" in dealers_str,
                  f"Beijing address: expected 朝阳区金港汽车公园, found: {dealers_str[:400]}", weight=0.5)
        
        # Chengdu: 高新区机场路 (trap: old distractor says "location TBD")
        add_check("dealer_chengdu_address", "高新区" in dealers_str and "机场路" in dealers_str,
                  f"Chengdu address: expected 高新区机场路, found: {dealers_str[:400]}", weight=0.5)
        
        # All 6 dealers present check
        dealer_names = ["英杰宝", "永达", "南菱", "中升", "三和", "和诚"]
        all_dealers_present = all(name in dealers_str for name in dealer_names)
        add_check("all_6_dealers_present", all_dealers_present,
                  f"All 6 dealer names present: {[n for n in dealer_names if n not in dealers_str]} missing", weight=1.0)
    except Exception as e:
        add_check("china_dealers_section", False, f"Error processing CHINA_DEALERS: {e}", weight=2.0)

    # Final scoring
    final_score = total_score / max_score if max_score > 0 else 0.0
    final_passed = final_score >= 0.80  # Must get 80%+ to pass

    return {
        "passed": final_passed,
        "score": round(final_score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))