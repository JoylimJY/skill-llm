import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    
    # --- Locate the output file ---
    output_files = list(Path(workspace_dir).rglob("contradiction_analysis.json"))
    
    if not output_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{
                "name": "output_file_exists",
                "passed": False,
                "detail": "contradiction_analysis.json not found anywhere in workspace"
            }]
        }
    
    # Use the most recently modified if multiple found
    output_file = sorted(output_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found at: {output_file}"
    })
    total_score += 0.05
    
    # --- Parse JSON ---
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.05,
            "checks": checks + [{
                "name": "json_parseable",
                "passed": False,
                "detail": f"JSON parse error: {e}"
            }]
        }
    
    checks.append({
        "name": "json_parseable",
        "passed": True,
        "detail": "File is valid JSON"
    })
    total_score += 0.05

    # ============================================================
    # CHECK 1: Step 1 - All contradictions listed (at least 3 pairs)
    # ============================================================
    try:
        step1_keys = ["step1", "contradictions", "all_contradictions", "identified_contradictions", "矛盾识别", "第一步"]
        step1 = None
        for k in step1_keys:
            if k in data:
                step1 = data[k]
                break
        
        # Also search nested
        if step1 is None:
            for v in data.values():
                if isinstance(v, dict):
                    for k in step1_keys:
                        if k in v:
                            step1 = v[k]
                            break
        
        contradictions_list = []
        if step1 is not None:
            if isinstance(step1, list):
                contradictions_list = step1
            elif isinstance(step1, dict):
                for k in ["items", "list", "contradictions", "pairs"]:
                    if k in step1 and isinstance(step1[k], list):
                        contradictions_list = step1[k]
                        break
                if not contradictions_list:
                    contradictions_list = [step1]
        
        has_enough_contradictions = len(contradictions_list) >= 3
        
        # Also check the raw text for contradiction patterns even if not in step1
        raw_text = json.dumps(data, ensure_ascii=False).lower()
        contradiction_keywords = [
            "tech debt", "technical debt", "feature", "reliability", "compliance",
            "velocity", "stability", "capacity", "churn", "revenue", "morale",
            "技术债", "功能", "稳定", "合规", "速度"
        ]
        keyword_hits = sum(1 for kw in contradiction_keywords if kw in raw_text)
        
        check_passed = has_enough_contradictions or (keyword_hits >= 4 and len(raw_text) > 500)
        
        checks.append({
            "name": "step1_identifies_multiple_contradictions",
            "passed": check_passed,
            "detail": f"Found {len(contradictions_list)} contradiction entries in step1 field; keyword hits in full doc: {keyword_hits}"
        })
        if check_passed:
            total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "step1_identifies_multiple_contradictions",
            "passed": False,
            "detail": f"Error checking step1: {e}"
        })

    # ============================================================
    # CHECK 2: Step 2 - Principal contradiction identified
    # Must identify something related to: stability/reliability vs. feature delivery
    # OR tech debt vs. business velocity (both acceptable as principal contradiction)
    # ============================================================
    try:
        principal_keys = ["step2", "principal_contradiction", "main_contradiction", "主要矛盾", "第二步"]
        principal_text = ""
        
        for k in principal_keys:
            if k in data:
                val = data[k]
                principal_text = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
                break
        
        if not principal_text:
            # Search nested
            for v in data.values():
                if isinstance(v, dict):
                    for k in principal_keys:
                        if k in v:
                            val = v[k]
                            principal_text = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
                            break
        
        # Principal contradiction should be about the core tension:
        # reliability/stability vs. feature/velocity (most defensible choice)
        # OR capacity/resource vs. demand (also valid)
        principal_indicators = [
            "tech debt", "technical debt", "reliability", "stability", "feature", "velocity",
            "performance", "outage", "capacity", "churn", "foundation", "technical foundation",
            "技术债", "稳定性", "功能交付", "可靠性"
        ]
        
        hits = sum(1 for ind in principal_indicators if ind in principal_text)
        
        # Must also have a justification (non-trivial length)
        has_justification = len(principal_text) > 80
        
        check_passed = hits >= 2 and has_justification
        
        checks.append({
            "name": "step2_principal_contradiction_identified",
            "passed": check_passed,
            "detail": f"Principal contradiction text length: {len(principal_text)}; indicator hits: {hits}"
        })
        if check_passed:
            total_score += 0.15
    except Exception as e:
        checks.append({
            "name": "step2_principal_contradiction_identified",
            "passed": False,
            "detail": f"Error checking step2: {e}"
        })

    # ============================================================
    # CHECK 3: Step 3 - Dominant aspect (主要方面) of principal contradiction
    # Must identify WHICH SIDE is currently dominant
    # ============================================================
    try:
        step3_keys = ["step3", "dominant_aspect", "主要方面", "第三步", "principal_aspect"]
        step3_text = ""
        
        for k in step3_keys:
            if k in data:
                val = data[k]
                step3_text = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
                break
        
        if not step3_text:
            for v in data.values():
                if isinstance(v, dict):
                    for k in step3_keys:
                        if k in v:
                            val = v[k]
                            step3_text = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
                            break
        
        # Must specify a dominant side - either business pressure OR technical debt side
        # and must have the concept of "which side is winning/dominant"
        dominant_indicators = [
            "dominant", "主导", "支配", "主要方面", "currently", "presently",
            "business pressure", "technical debt", "winning", "controls", "determines",
            "drives", "leading", "主要的一方", "占支配"
        ]
        
        hits = sum(1 for ind in dominant_indicators if ind in step3_text)
        has_content = len(step3_text) > 60
        
        check_passed = hits >= 1 and has_content
        
        checks.append({
            "name": "step3_dominant_aspect_identified",
            "passed": check_passed,
            "detail": f"Step3 text length: {len(step3_text)}; dominant aspect indicator hits: {hits}"
        })
        if check_passed:
            total_score += 0.12
    except Exception as e:
        checks.append({
            "name": "step3_dominant_aspect_identified",
            "passed": False,
            "detail": f"Error checking step3: {e}"
        })

    # ============================================================
    # CHECK 4: Step 4 - Contradiction nature classified
    # The internal engineering vs PM / product vs stability conflict is NON-ANTAGONISTIC
    # (shared goal of company survival), NOT antagonistic
    # This is the key proprietary trap - must use the specific classification
    # ============================================================
    try:
        step4_keys = ["step4", "contradiction_nature", "nature", "矛盾性质", "第四步", "antagonistic"]
        step4_text = ""
        
        for k in step4_keys:
            if k in data:
                val = data[k]
                step4_text = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
                break
        
        if not step4_text:
            for v in data.values():
                if isinstance(v, dict):
                    for k in step4_keys:
                        if k in v:
                            val = v[k]
                            step4_text = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
                            break
        
        # Must use the specific antagonistic/non-antagonistic classification vocabulary
        classification_terms = [
            "antagonistic", "non-antagonistic", "非对抗", "对抗性", "对抗", 
            "antagonist", "non antagonistic", "nonantagonistic",
            "共同利益", "fundamental interest", "shared interest", "common goal"
        ]
        
        hits = sum(1 for term in classification_terms if term in step4_text)
        
        # The CORRECT answer is non-antagonistic (internal company tensions, shared survival goal)
        # We check for non-antagonistic being present
        non_antagonistic_terms = [
            "non-antagonistic", "非对抗", "non antagonistic", "nonantagonistic",
            "not antagonistic", "共同利益", "shared", "common"
        ]
        has_non_antagonistic = any(term in step4_text for term in non_antagonistic_terms)
        
        check_passed = hits >= 1 and len(step4_text) > 50
        
        bonus_correct_classification = has_non_antagonistic
        
        checks.append({
            "name": "step4_contradiction_nature_classified",
            "passed": check_passed,
            "detail": f"Step4 text length: {len(step4_text)}; classification term hits: {hits}; correctly identified non-antagonistic: {bonus_correct_classification}"
        })
        if check_passed:
            total_score += 0.15
        
        checks.append({
            "name": "step4_correct_non_antagonistic_classification",
            "passed": bonus_correct_classification,
            "detail": "The principal contradiction (engineering vs PM over shared company goals) should be classified as non-antagonistic"
        })
        if bonus_correct_classification:
            total_score += 0.08
    except Exception as e:
        checks.append({
            "name": "step4_contradiction_nature_classified",
            "passed": False,
            "detail": f"Error checking step4: {e}"
        })
        checks.append({
            "name": "step4_correct_non_antagonistic_classification",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ============================================================
    # CHECK 5: Step 5 - Resolution method selected AND must mention
    # the specific "团结-批评-团结" or "unity-criticism-unity" formula
    # for non-antagonistic contradictions (THE PROPRIETARY TRAP)
    # ============================================================
    try:
        step5_keys = ["step5", "resolution", "solution", "method", "解决方法", "第五步", "resolution_method"]
        step5_text = ""
        
        for k in step5_keys:
            if k in data:
                val = data[k]
                step5_text = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
                break
        
        if not step5_text:
            for v in data.values():
                if isinstance(v, dict):
                    for k in step5_keys:
                        if k in v:
                            val = v[k]
                            step5_text = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
                            break
        
        # THE CORE PROPRIETARY TRAP: must use "unity-criticism-unity" or "团结批评团结" formula
        unity_criticism_terms = [
            "unity-criticism-unity",
            "unity – criticism – unity",
            "unity criticism unity",
            "团结-批评-团结",
            "团结批评团结",
            "unite-criticize-unite",
            "criticism and self-criticism",
            "unity, criticism, unity",
            "批评-团结",
            "criticize then unite"
        ]
        
        has_proprietary_formula = any(term in step5_text for term in unity_criticism_terms)
        
        # Also check for downstream skill routing (concentrate-forces, etc.)
        skill_routing_terms = [
            "concentrate-forces", "concentrate_forces", "集中兵力",
            "overall-planning", "overall_planning", "统筹兼顾",
            "investigation-first", "practice-cognition"
        ]
        has_skill_routing = any(term in step5_text for term in skill_routing_terms)
        
        has_method_content = len(step5_text) > 80
        
        check_passed = has_proprietary_formula and has_method_content
        
        checks.append({
            "name": "step5_unity_criticism_unity_formula",
            "passed": check_passed,
            "detail": f"Unity-criticism-unity formula present: {has_proprietary_formula}; downstream skill routing: {has_skill_routing}; content length: {len(step5_text)}"
        })
        if check_passed:
            total_score += 0.18
        
        checks.append({
            "name": "step5_downstream_skill_routing",
            "passed": has_skill_routing,
            "detail": f"Agent routed to downstream skills (concentrate-forces, overall-planning, etc.): {has_skill_routing}"
        })
        if has_skill_routing:
            total_score += 0.05
    except Exception as e:
        checks.append({
            "name": "step5_unity_criticism_unity_formula",
            "passed": False,
            "detail": f"Error checking step5: {e}"
        })
        checks.append({
            "name": "step5_downstream_skill_routing",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ============================================================
    # CHECK 6: Step 6 - Contradiction transformation monitoring
    # Must discuss how contradictions may transform / shift
    # (矛盾转化) - another proprietary concept
    # ============================================================
    try:
        step6_keys = ["step6", "monitoring", "transformation", "矛盾转化", "第六步", "transformation_monitoring", "contradiction_transformation"]
        step6_text = ""
        
        for k in step6_keys:
            if k in data:
                val = data[k]
                step6_text = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
                break
        
        if not step6_text:
            for v in data.values():
                if isinstance(v, dict):
                    for k in step6_keys:
                        if k in v:
                            val = v[k]
                            step6_text = json.dumps(val, ensure_ascii=False).lower() if not isinstance(val, str) else val.lower()
                            break
        
        transformation_terms = [
            "transform", "transformation", "shift", "转化", "矛盾转化",
            "principal contradiction may change", "secondary contradiction",
            "escalate", "non-antagonistic to antagonistic",
            "次要矛盾", "上升为主要矛盾", "monitor", "watch"
        ]
        
        hits = sum(1 for term in transformation_terms if term in step6_text)
        has_content = len(step6_text) > 80
        
        # Specifically check for the risk of non-antagonistic becoming antagonistic
        escalation_risk_terms = [
            "antagonistic", "escalat", "non-antagonistic to antagonistic",
            "对抗性矛盾", "激化", "become antagonistic"
        ]
        has_escalation_risk = any(term in step6_text for term in escalation_risk_terms)
        
        check_passed = hits >= 2 and has_content
        
        checks.append({
            "name": "step6_transformation_monitoring",
            "passed": check_passed,
            "detail": f"Step6 transformation content length: {len(step6_text)}; transformation term hits: {hits}; escalation risk discussed: {has_escalation_risk}"
        })
        if check_passed:
            total_score += 0.12
        
        checks.append({
            "name": "step6_escalation_risk_discussed",
            "passed": has_escalation_risk,
            "detail": "Agent should warn that mishandled non-antagonistic contradictions can become antagonistic"
        })
        if has_escalation_risk:
            total_score += 0.05
    except Exception as e:
        checks.append({
            "name": "step6_transformation_monitoring",
            "passed": False,
            "detail": f"Error checking step6: {e}"
        })
        checks.append({
            "name": "step6_escalation_risk_discussed",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ============================================================
    # CHECK 7: Overall document quality - all 6 steps must be present
    # ============================================================
    try:
        raw = json.dumps(data, ensure_ascii=False).lower()
        
        step_indicators = {
            "step1_present": any(k in raw for k in ["step1", "step 1", "第一步", "contradictions", "identified"]),
            "step2_present": any(k in raw for k in ["step2", "step 2", "第二步", "principal", "主要矛盾"]),
            "step3_present": any(k in raw for k in ["step3", "step 3", "第三步", "dominant", "主要方面"]),
            "step4_present": any(k in raw for k in ["step4", "step 4", "第四步", "nature", "antagoni", "矛盾性质"]),
            "step5_present": any(k in raw for k in ["step5", "step 5", "第五步", "resolution", "method", "解决"]),
            "step6_present": any(k in raw for k in ["step6", "step 6", "第六步", "monitor", "transform", "转化"]),
        }
        
        steps_present = sum(1 for v in step_indicators.values() if v)
        all_six_steps = steps_present >= 6
        
        checks.append({
            "name": "all_six_steps_present",
            "passed": all_six_steps,
            "detail": f"Steps present: {steps_present}/6. Breakdown: {step_indicators}"
        })
        if all_six_steps:
            total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "all_six_steps_present",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # Cap score at 1.0
    total_score = min(round(total_score, 3), 1.0)
    
    # Overall pass threshold: must score >= 0.55 AND have the proprietary formula
    proprietary_formula_check = next(
        (c for c in checks if c["name"] == "step5_unity_criticism_unity_formula"),
        {"passed": False}
    )
    
    passed = total_score >= 0.55 and proprietary_formula_check["passed"]
    
    return {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))