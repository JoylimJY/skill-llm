import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    
    # --- Find the output file ---
    report_path = None
    candidates = list(Path(workspace_dir).rglob("market_insights_report.json"))
    if candidates:
        report_path = candidates[0]
    
    # CHECK 0: File exists
    file_exists = report_path is not None and report_path.exists()
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found at {report_path}" if file_exists else "market_insights_report.json not found anywhere in workspace"
    })
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # --- Parse JSON ---
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        report = json.loads(content)
        json_valid = True
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "json_parseable", "passed": True, "detail": "Valid JSON"})
    
    # ==========================================
    # CHECK 1: Market Segmentation Matrix (Step 1)
    # Must have 3-5 segments with required fields
    # ==========================================
    try:
        segments = None
        # flexible key search
        for key in ["市场细分矩阵", "market_segmentation", "segmentation_matrix", "segments", "market_segments"]:
            if key in report:
                segments = report[key]
                break
        # also search nested
        if segments is None:
            for v in report.values():
                if isinstance(v, list) and len(v) >= 3:
                    # check if items look like segments
                    if isinstance(v[0], dict):
                        segments = v
                        break
        
        seg_count_ok = segments is not None and 3 <= len(segments) <= 5
        checks.append({
            "name": "segmentation_matrix_3_to_5_segments",
            "passed": seg_count_ok,
            "detail": f"Found {len(segments) if segments else 0} segments (need 3-5)"
        })
        
        if seg_count_ok:
            total_score += 0.10
            # Check for required fields in segments
            required_seg_fields_keywords = [
                ["size", "规模", "market_size", "规模估算"],
                ["growth", "增长", "trend", "增长趋势"],
                ["competition", "竞争", "competitive"],
                ["barrier", "壁垒", "entry_barrier", "进入壁垒"]
            ]
            fields_found = 0
            for seg in segments[:3]:  # check first 3
                seg_str = json.dumps(seg, ensure_ascii=False).lower()
                for field_group in required_seg_fields_keywords:
                    if any(kw.lower() in seg_str for kw in field_group):
                        fields_found += 1
                        break
            seg_fields_ok = fields_found >= 3
            checks.append({
                "name": "segmentation_includes_required_fields",
                "passed": seg_fields_ok,
                "detail": f"Segments contain {fields_found}/4 required field categories (size, growth, competition, barrier)"
            })
            if seg_fields_ok:
                total_score += 0.05
        else:
            checks.append({
                "name": "segmentation_includes_required_fields",
                "passed": False,
                "detail": "Skipped - insufficient segments"
            })
    except Exception as e:
        checks.append({"name": "segmentation_matrix_3_to_5_segments", "passed": False, "detail": str(e)})
        checks.append({"name": "segmentation_includes_required_fields", "passed": False, "detail": str(e)})
    
    # ==========================================
    # CHECK 2: Beachhead Selection (Step 2)
    # Must select ONE market AND apply the 5-dimension framework
    # ==========================================
    report_str = json.dumps(report, ensure_ascii=False).lower()
    
    try:
        beachhead = None
        for key in ["滩头阵地", "beachhead", "beachhead_market", "target_market", "selected_market", "beachhead_selection"]:
            if key in report:
                beachhead = report[key]
                break
        
        # also try nested search
        if beachhead is None:
            for v in report.values():
                if isinstance(v, dict):
                    v_str = json.dumps(v, ensure_ascii=False).lower()
                    if any(k in v_str for k in ["beachhead", "滩头", "target", "selected"]):
                        beachhead = v
                        break
        
        beachhead_exists = beachhead is not None
        checks.append({
            "name": "beachhead_selection_present",
            "passed": beachhead_exists,
            "detail": f"Beachhead section found: {bool(beachhead)}"
        })
        if beachhead_exists:
            total_score += 0.10
        
        # Check 5-dimension evaluation criteria (proprietary trap)
        # Must contain references to all 5 dimensions:
        # 1. 痛点强度 (pain point intensity)
        # 2. 付费意愿与能力 (willingness/ability to pay)
        # 3. 渠道可达性 (channel accessibility)
        # 4. 竞争空白点 (competitive gap)
        # 5. 战略一致性 (strategic alignment)
        
        five_dim_keywords = [
            ["痛点", "pain", "urgency", "紧迫"],
            ["付费", "payment", "willingness", "ability to pay", "budget", "购买能力"],
            ["渠道", "channel", "reachable", "reach", "触达", "accessible"],
            ["竞争", "competition", "competitive gap", "空白", "weak competition"],
            ["战略", "strategic", "vision", "alignment", "一致性", "long.term"]
        ]
        
        bh_str = json.dumps(beachhead if beachhead else report, ensure_ascii=False).lower()
        dims_found = 0
        dim_details = []
        for dim_group in five_dim_keywords:
            found = any(kw.lower() in bh_str for kw in dim_group)
            if found:
                dims_found += 1
            dim_details.append(f"{'✓' if found else '✗'} {dim_group[0]}")
        
        five_dim_ok = dims_found >= 4  # allow 4/5 minimum
        checks.append({
            "name": "beachhead_five_dimension_evaluation",
            "passed": five_dim_ok,
            "detail": f"Found {dims_found}/5 required dimensions: {', '.join(dim_details)}"
        })
        if five_dim_ok:
            total_score += 0.15
        
        # Check that mid-size specialty farms (segment 2) is chosen as beachhead
        # (this is strongly supported by the data provided)
        midsize_chosen = any(kw in bh_str for kw in [
            "mid-size", "midsize", "mid size", "specialty", "vegetable", 
            "200", "2000", "特种", "蔬菜", "中型", "segment 2", "段2"
        ])
        checks.append({
            "name": "beachhead_correct_segment_selected",
            "passed": midsize_chosen,
            "detail": "Mid-size specialty crop farms (200-2000 acres) selected as beachhead based on provided data"
        })
        if midsize_chosen:
            total_score += 0.05
            
    except Exception as e:
        checks.append({"name": "beachhead_selection_present", "passed": False, "detail": str(e)})
        checks.append({"name": "beachhead_five_dimension_evaluation", "passed": False, "detail": str(e)})
        checks.append({"name": "beachhead_correct_segment_selected", "passed": False, "detail": str(e)})
    
    # ==========================================
    # CHECK 3: User Persona (Step 3)
    # Must have 1-2 detailed personas with all 4 dimension categories
    # ==========================================
    try:
        persona = None
        for key in ["终端用户画像", "persona", "personas", "user_persona", "customer_profile", "用户画像"]:
            if key in report:
                persona = report[key]
                break
        
        persona_exists = persona is not None
        checks.append({
            "name": "user_persona_present",
            "passed": persona_exists,
            "detail": f"Persona section found: {bool(persona)}"
        })
        if persona_exists:
            total_score += 0.05
        
        # Check persona has all 4 dimension categories:
        # demographic, psychographic, behavioral, pain_points
        persona_str = json.dumps(persona if persona else {}, ensure_ascii=False).lower()
        persona_dim_keywords = [
            ["age", "年龄", "gender", "income", "education", "demographic", "人口"],
            ["value", "lifestyle", "attitude", "心理", "psycho", "兴趣", "interest"],
            ["behavior", "habit", "purchase", "行为", "usage", "场景"],
            ["pain", "痛点", "need", "需求", "problem", "challenge", "goal"]
        ]
        persona_dims_found = sum(
            1 for dim_group in persona_dim_keywords
            if any(kw.lower() in persona_str for kw in dim_group)
        )
        persona_dims_ok = persona_dims_found >= 3
        checks.append({
            "name": "persona_four_dimensions",
            "passed": persona_dims_ok,
            "detail": f"Found {persona_dims_found}/4 persona dimension categories (demographic, psychographic, behavioral, pain_points)"
        })
        if persona_dims_ok:
            total_score += 0.10
            
        # Check persona references real interview data (Carlos or Priya)
        persona_real = any(name in persona_str for name in ["carlos", "priya", "mendoza", "shah", "fresno", "homestead"])
        checks.append({
            "name": "persona_based_on_interview_data",
            "passed": persona_real,
            "detail": "Persona references actual interview subjects (Carlos Mendoza or Priya Shah)"
        })
        if persona_real:
            total_score += 0.05
            
    except Exception as e:
        checks.append({"name": "user_persona_present", "passed": False, "detail": str(e)})
        checks.append({"name": "persona_four_dimensions", "passed": False, "detail": str(e)})
        checks.append({"name": "persona_based_on_interview_data", "passed": False, "detail": str(e)})
    
    # ==========================================
    # CHECK 4: TAM/SAM/SOM (Step 4)
    # Must have all three tiers with bottom-up methodology
    # ==========================================
    try:
        tam_section = None
        for key in ["tam_sam_som", "market_size", "市场规模", "TAM", "tam"]:
            if key in report:
                tam_section = report[key]
                break
        
        tam_exists = tam_section is not None or all(
            kw in report_str for kw in ["tam", "sam", "som"]
        )
        checks.append({
            "name": "tam_sam_som_present",
            "passed": tam_exists,
            "detail": f"TAM/SAM/SOM section found"
        })
        if tam_exists:
            total_score += 0.05
        
        # Check all three tiers present
        tam_str = json.dumps(tam_section if tam_section else report, ensure_ascii=False).lower()
        three_tiers_ok = all(kw in tam_str for kw in ["tam", "sam", "som"])
        checks.append({
            "name": "tam_sam_som_three_tiers",
            "passed": three_tiers_ok,
            "detail": f"All three tiers (TAM/SAM/SOM) present in report"
        })
        if three_tiers_ok:
            total_score += 0.05
        
        # Check bottom-up calculation methodology (proprietary constraint)
        # Must reference: customer count × unit price
        bottom_up_keywords = [
            "bottom.up", "自下而上", "customer.*price", "price.*customer",
            "unit price", "单价", "客单价", "number of customers", "客户数",
            "×", "x ", "* ", "multiply", "per customer", "per farm",
            "11,500", "11500", "9,600", "9600", "800/mo", "$800"
        ]
        bottom_up_found = any(kw.lower() in report_str for kw in bottom_up_keywords)
        checks.append({
            "name": "tam_sam_som_bottom_up_method",
            "passed": bottom_up_found,
            "detail": "Bottom-up calculation method used (customer count × unit price), as required"
        })
        if bottom_up_found:
            total_score += 0.10
        
        # Check assumptions/sources labeled
        assumption_keywords = ["assumption", "假设", "source", "来源", "based on", "据", "note", "calculation"]
        assumptions_labeled = any(kw.lower() in tam_str for kw in assumption_keywords)
        checks.append({
            "name": "tam_sam_som_labeled_assumptions",
            "passed": assumptions_labeled,
            "detail": "Data sources and calculation assumptions are labeled"
        })
        if assumptions_labeled:
            total_score += 0.05
        
        # Check SOM is numerically smallest (sanity check)
        # Extract numbers - at minimum check they discuss realistic SOM
        som_realistic = any(kw in report_str for kw in [
            "35", "40", "year 1", "first year", "第一年", "initial", "short.term", "近期"
        ])
        checks.append({
            "name": "som_realistic_year1_estimate",
            "passed": som_realistic,
            "detail": "SOM includes realistic Year 1 estimate (35-40 customers based on data)"
        })
        if som_realistic:
            total_score += 0.05
            
    except Exception as e:
        for check_name in ["tam_sam_som_present", "tam_sam_som_three_tiers", 
                           "tam_sam_som_bottom_up_method", "tam_sam_som_labeled_assumptions",
                           "som_realistic_year1_estimate"]:
            checks.append({"name": check_name, "passed": False, "detail": str(e)})
    
    # ==========================================
    # CHECK 5: Customer Decision Process (Step 5)
    # Must have all 5 sub-dimensions
    # ==========================================
    try:
        decision = None
        for key in ["客户决策", "decision_process", "customer_decision", "decision_journey", 
                    "purchase_decision", "decision_map", "决策旅程"]:
            if key in report:
                decision = report[key]
                break
        
        decision_exists = decision is not None or any(
            kw in report_str for kw in ["decision", "决策", "purchase process", "buyer journey"]
        )
        checks.append({
            "name": "decision_process_present",
            "passed": decision_exists,
            "detail": "Customer decision process section found"
        })
        if decision_exists:
            total_score += 0.05
        
        decision_str = json.dumps(decision if decision else report, ensure_ascii=False).lower()
        
        # Check all 5 sub-dimensions of decision process (proprietary)
        decision_subdims = [
            # 1. Decision participants
            (["decision maker", "使用者", "决策者", "影响者", "审批者", "stakeholder", "user", "buyer", "influencer", "approver"], "decision_participants"),
            # 2. Decision criteria
            (["criteria", "标准", "value", "price", "brand", "service", "决策标准", "feature", "priority", "most important"], "decision_criteria"),
            # 3. Decision process (awareness->interest->evaluation->purchase->use)
            (["awareness", "认知", "interest", "兴趣", "evaluation", "评估", "purchase", "购买", "journey", "path", "funnel"], "decision_journey_path"),
            # 4. Purchase barriers
            (["barrier", "障碍", "obstacle", "concern", "hesitation", "risk", "阻碍", "trust", "budget constraint"], "purchase_barriers"),
            # 5. Information sources
            (["information source", "信息来源", "where.*learn", "expo", "conference", "social media", "referral", "word of mouth", "newsletter", "farm bureau"], "information_sources")
        ]
        
        subdims_passed = 0
        for kw_list, dim_name in decision_subdims:
            found = any(kw.lower() in decision_str for kw in kw_list)
            if found:
                subdims_passed += 1
            checks.append({
                "name": f"decision_subdim_{dim_name}",
                "passed": found,
                "detail": f"Decision sub-dimension '{dim_name}' addressed"
            })
            if found:
                total_score += 0.04
        
        # Bonus: references actual interview data for decision process
        decision_interview_ref = any(kw in decision_str for kw in [
            "father", "accountant", "quickbooks", "raj", "30-day", "trial", 
            "priya", "carlos", "farm bureau", "world ag expo", "whatsapp"
        ])
        checks.append({
            "name": "decision_process_references_interview_data",
            "passed": decision_interview_ref,
            "detail": "Decision process incorporates real insights from customer interviews"
        })
        if decision_interview_ref:
            total_score += 0.05
            
    except Exception as e:
        checks.append({"name": "decision_process_present", "passed": False, "detail": str(e)})
        for dim_name in ["participants", "criteria", "journey_path", "barriers", "sources"]:
            checks.append({"name": f"decision_subdim_{dim_name}", "passed": False, "detail": str(e)})
    
    # ==========================================
    # CHECK 6: Report Structure Completeness (Output Format)
    # Must have all 5 sections of the 《市场细分与客户洞察报告》
    # ==========================================
    try:
        required_sections = [
            (["segmentation", "市场细分", "segments", "segment_matrix"], "section_1_market_segmentation"),
            (["beachhead", "滩头", "target_market", "selected"], "section_2_beachhead"),
            (["persona", "画像", "customer_profile", "user_profile"], "section_3_persona"),
            (["tam", "sam", "som", "market_size", "市场规模"], "section_4_market_size"),
            (["decision", "决策", "journey", "purchase_process"], "section_5_decision_journey"),
        ]
        
        sections_found = 0
        for kw_list, sec_name in required_sections:
            found = any(kw.lower() in report_str for kw in kw_list)
            if found:
                sections_found += 1
        
        all_5_sections = sections_found == 5
        checks.append({
            "name": "report_has_all_5_required_sections",
            "passed": all_5_sections,
            "detail": f"Report contains {sections_found}/5 required sections"
        })
        if all_5_sections:
            total_score += 0.05
            
    except Exception as e:
        checks.append({"name": "report_has_all_5_required_sections", "passed": False, "detail": str(e)})
    
    # --- Final scoring ---
    total_score = min(total_score, 1.0)
    passed = total_score >= 0.60  # 60% threshold
    
    return {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))