import sys
import os
import json
import re
from pathlib import Path

def find_scorecards(workspace):
    """Find all markdown scorecard files in the workspace."""
    md_files = list(Path(workspace).rglob("*.md"))
    return md_files

def extract_weighted_total(content):
    """Extract the weighted total from a scorecard markdown table."""
    # Look for TOTAL row with a score like **X.XX/5.0** or X.XX/5.0
    patterns = [
        r'\*\*TOTAL\*\*.*?\*\*([\d.]+)/5\.0\*\*',
        r'TOTAL.*?([\d.]+)/5\.0',
        r'\*\*([\d.]+)/5\.0\*\*',
        r'([\d.]+)/5\.0',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                continue
    return None

def extract_recommendation(content):
    """Extract HIRE / NO HIRE / MAYBE recommendation."""
    patterns = [
        r'Recommendation:\s*(HIRE|NO HIRE|MAYBE)',
        r'Recommendation\s*[:\-]\s*(HIRE|NO HIRE|MAYBE)',
        r'\b(NO HIRE|HIRE|MAYBE)\b',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            return m.group(1).upper().strip()
    return None

def check_criteria_weights(content):
    """Check that the 6 default criteria with correct weights appear in the scorecard."""
    required = [
        ("Technical Skills", "25%"),
        ("Relevant Experience", "20%"),
        ("Culture Fit", "15%"),
        ("Communication", "15%"),
        ("Problem Solving", "15%"),
        ("Growth Potential", "10%"),
    ]
    found = []
    for criterion, weight in required:
        # Allow for some flexibility in formatting
        pattern = rf'{re.escape(criterion)}.*?{re.escape(weight)}'
        if re.search(pattern, content, re.IGNORECASE):
            found.append(True)
        else:
            found.append(False)
    return found, required

def compute_expected_weighted_total(scores):
    """Compute expected weighted total from scores dict."""
    weights = {
        "technical_skills": 0.25,
        "relevant_experience": 0.20,
        "culture_fit": 0.15,
        "communication": 0.15,
        "problem_solving": 0.15,
        "growth_potential": 0.10,
    }
    total = sum(weights[k] * v for k, v in scores.items())
    return round(total, 2)

# Expected scores from the interview notes
CANDIDATE_DATA = {
    "miriam": {
        "scores": {
            "technical_skills": 5,
            "relevant_experience": 4,
            "culture_fit": 2,
            "communication": 4,
            "problem_solving": 3,
            "growth_potential": 2,
        },
        "recommendation": "MAYBE",
        "name_variants": ["miriam", "osei", "osei-bonsu"],
    },
    "tariq": {
        "scores": {
            "technical_skills": 3,
            "relevant_experience": 5,
            "culture_fit": 5,
            "communication": 3,
            "problem_solving": 4,
            "growth_potential": 5,
        },
        "recommendation": "HIRE",
        "name_variants": ["tariq", "abubakar", "hassan"],
    },
    "svetlana": {
        "scores": {
            "technical_skills": 5,
            "relevant_experience": 4,
            "culture_fit": 2,
            "communication": 4,
            "problem_solving": 3,
            "growth_potential": 3,
        },
        "recommendation": "MAYBE",
        "name_variants": ["svetlana", "volkov", "petrov"],
    },
}

# Precompute expected totals
for cand_key, data in CANDIDATE_DATA.items():
    data["expected_total"] = compute_expected_weighted_total(data["scores"])

# Miriam: 5*0.25 + 4*0.20 + 2*0.15 + 4*0.15 + 3*0.15 + 2*0.10 = 1.25+0.80+0.30+0.60+0.45+0.20 = 3.60
# Tariq:  3*0.25 + 5*0.20 + 5*0.15 + 3*0.15 + 4*0.15 + 5*0.10 = 0.75+1.00+0.75+0.45+0.60+0.50 = 4.05
# Svetlana: 5*0.25 + 4*0.20 + 2*0.15 + 4*0.15 + 3*0.15 + 3*0.10 = 1.25+0.80+0.30+0.60+0.45+0.30 = 3.70

def run_eval(workspace):
    checks = []
    
    # --- Check 1: Find at least 3 scorecard markdown files ---
    all_md = find_scorecards(workspace)
    scorecard_files = [f for f in all_md if f.stat().st_size > 200]
    
    checks.append({
        "name": "At least 3 candidate scorecard markdown files exist",
        "passed": len(scorecard_files) >= 3,
        "detail": f"Found {len(scorecard_files)} markdown files: {[str(f) for f in scorecard_files]}"
    })
    
    if len(scorecard_files) < 3:
        # Try to find any text files
        all_txt = list(Path(workspace).rglob("*.txt"))
        checks[-1]["detail"] += f" | TXT files: {[str(f) for f in all_txt if 'scorecard' in str(f).lower() or 'score' in str(f).lower()]}"
    
    # --- Check 2-10: Per-candidate checks ---
    candidate_results = {}
    
    for cand_key, data in CANDIDATE_DATA.items():
        found_file = None
        found_content = None
        
        for md_file in scorecard_files:
            try:
                content = md_file.read_text(encoding='utf-8', errors='replace').lower()
                for variant in data["name_variants"]:
                    if variant.lower() in content:
                        found_file = md_file
                        found_content = md_file.read_text(encoding='utf-8', errors='replace')
                        break
                if found_file:
                    break
            except Exception as e:
                continue
        
        candidate_results[cand_key] = {
            "file": found_file,
            "content": found_content,
        }
        
        checks.append({
            "name": f"Scorecard found for {cand_key.capitalize()}",
            "passed": found_file is not None,
            "detail": f"File: {str(found_file) if found_file else 'NOT FOUND'}"
        })
        
        if found_content is None:
            # Add placeholder checks
            checks.append({
                "name": f"{cand_key.capitalize()}: Correct 6 criteria with proper weights present",
                "passed": False,
                "detail": "No scorecard file found"
            })
            checks.append({
                "name": f"{cand_key.capitalize()}: Weighted total correct (expected {data['expected_total']:.2f}/5.0)",
                "passed": False,
                "detail": "No scorecard file found"
            })
            checks.append({
                "name": f"{cand_key.capitalize()}: Recommendation is {data['recommendation']}",
                "passed": False,
                "detail": "No scorecard file found"
            })
            continue
        
        # Check criteria and weights
        weight_results, required = check_criteria_weights(found_content)
        all_weights_ok = all(weight_results)
        missing = [required[i][0] for i, ok in enumerate(weight_results) if not ok]
        checks.append({
            "name": f"{cand_key.capitalize()}: All 6 default criteria with correct weights present",
            "passed": all_weights_ok,
            "detail": f"Missing/incorrect: {missing}" if missing else "All 6 criteria with weights found"
        })
        
        # Check weighted total
        actual_total = extract_weighted_total(found_content)
        expected_total = data["expected_total"]
        total_ok = actual_total is not None and abs(actual_total - expected_total) <= 0.1
        checks.append({
            "name": f"{cand_key.capitalize()}: Weighted total correct (expected ~{expected_total:.2f}/5.0)",
            "passed": total_ok,
            "detail": f"Found total: {actual_total}, Expected: {expected_total:.2f}"
        })
        
        # Check recommendation
        rec = extract_recommendation(found_content)
        rec_ok = rec == data["recommendation"]
        checks.append({
            "name": f"{cand_key.capitalize()}: Recommendation is '{data['recommendation']}'",
            "passed": rec_ok,
            "detail": f"Found recommendation: '{rec}', Expected: '{data['recommendation']}'"
        })
    
    # --- Check: Comparison/ranking document exists ---
    comparison_found = False
    comparison_content = ""
    all_files = list(Path(workspace).rglob("*"))
    for f in all_files:
        if f.is_file() and f.stat().st_size > 100:
            try:
                content = f.read_text(encoding='utf-8', errors='replace').lower()
                # Look for a file that mentions all three candidates and ranking/comparison
                has_all_candidates = all(
                    any(v in content for v in data["name_variants"])
                    for data in CANDIDATE_DATA.values()
                )
                has_comparison_keywords = any(kw in content for kw in [
                    "rank", "comparison", "compare", "summary", "hire recommendation",
                    "hiring summary", "side-by-side", "ranked"
                ])
                if has_all_candidates and has_comparison_keywords:
                    comparison_found = True
                    comparison_content = f.read_text(encoding='utf-8', errors='replace')
                    break
            except:
                continue
    
    checks.append({
        "name": "Comparison/ranking summary document exists mentioning all 3 candidates",
        "passed": comparison_found,
        "detail": f"Found comparison doc" if comparison_found else "No comparison document found with all 3 candidates and ranking/summary language"
    })
    
    # --- Check: Tariq ranked highest in comparison (score 4.05 > Svetlana 3.70 > Miriam 3.60) ---
    if comparison_found and comparison_content:
        content_lower = comparison_content.lower()
        # Check that Tariq appears before others in ranking context
        tariq_pos = min([content_lower.find(v) for v in ["tariq", "abubakar"] if content_lower.find(v) != -1] or [9999])
        svetlana_pos = min([content_lower.find(v) for v in ["svetlana", "volkov"] if content_lower.find(v) != -1] or [9999])
        miriam_pos = min([content_lower.find(v) for v in ["miriam", "osei"] if content_lower.find(v) != -1] or [9999])
        
        # Tariq should appear first in ranking (rank 1)
        rank1_patterns = [
            r'1[.\)]\s*tariq', r'rank\s*1.*tariq', r'tariq.*rank\s*1',
            r'#1.*tariq', r'tariq.*#1', r'first.*tariq', r'tariq.*first',
            r'top.*tariq', r'tariq.*4\.[0-9]',
        ]
        tariq_ranked_first = any(re.search(p, content_lower) for p in rank1_patterns)
        
        # Also check if Tariq's score 4.05 appears near the top
        tariq_score_present = bool(re.search(r'4\.0[0-9]', comparison_content))
        
        checks.append({
            "name": "Comparison ranks Tariq first (highest weighted total ~4.05/5.0)",
            "passed": tariq_ranked_first or tariq_score_present,
            "detail": f"Tariq ranked first: {tariq_ranked_first}, Tariq's score present: {tariq_score_present}"
        })
        
        # HIRE recommendation for Tariq appears in comparison
        hire_tariq = bool(re.search(r'tariq.*hire|hire.*tariq', content_lower))
        checks.append({
            "name": "Comparison summary shows HIRE recommendation for Tariq",
            "passed": hire_tariq,
            "detail": f"HIRE+Tariq pattern found: {hire_tariq}"
        })
    else:
        checks.append({
            "name": "Comparison ranks Tariq first (highest weighted total ~4.05/5.0)",
            "passed": False,
            "detail": "No comparison document to evaluate"
        })
        checks.append({
            "name": "Comparison summary shows HIRE recommendation for Tariq",
            "passed": False,
            "detail": "No comparison document to evaluate"
        })
    
    # --- Check: Scorecards use /5.0 scale (not /100 or /10) ---
    scale_correct = True
    for cand_key, res in candidate_results.items():
        if res["content"]:
            # Should NOT have /100 or /10 as the total scale
            if re.search(r'\b\d+\.?\d*/100\b', res["content"]) or re.search(r'\bTOTAL.*?/10\b', res["content"]):
                scale_correct = False
                break
    checks.append({
        "name": "Scorecards use correct /5.0 scale (not /100 or /10)",
        "passed": scale_correct,
        "detail": "All scorecards appear to use /5.0 scale" if scale_correct else "Found incorrect scale (/100 or /10)"
    })
    
    # --- Compute final score ---
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    all_passed = passed_checks == total_checks
    
    return {
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "Eval script crashed", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, indent=2))