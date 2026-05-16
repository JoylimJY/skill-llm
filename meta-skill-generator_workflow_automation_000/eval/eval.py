#!/usr/bin/env python3
"""
Evaluation script for meta-skill-generator audit task.
Checks that the agent performed the full pipeline:
1. Scanned skills-library and updated skills_db.json
2. Ran sandbox tests and evaluated skills using the correct formula
3. Identified underperforming skills (score < 0.7) and optimized them
4. Created the audit_report.json with correct structure and data
"""
import json
import sys
import os
from pathlib import Path

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    base = os.path.join(workspace, "meta-skill-generator")
    
    checks = []
    total_score = 0.0
    max_score = 7.0  # 7 checks
    
    # ------------------------------------------------------------------
    # CHECK 1: skills_db.json was updated with the 5 skills from skills-library
    # ------------------------------------------------------------------
    try:
        sdb_path = os.path.join(base, "skills_db.json")
        with open(sdb_path, 'r') as f:
            skills_db = json.load(f)
        
        expected_names = {"data-validator", "code-reviewer", "report-builder", "log-analyzer", "api-tester"}
        found_names = set()
        if isinstance(skills_db, list):
            found_names = {s.get('name', '') for s in skills_db}
        elif isinstance(skills_db, dict):
            found_names = set(skills_db.keys())
        
        missing = expected_names - found_names
        if len(missing) == 0:
            checks.append({"name": "skills_db_updated", "passed": True, "detail": f"All 5 skills found in skills_db.json. Total entries: {len(skills_db) if isinstance(skills_db, list) else len(skills_db)}"})
            total_score += 1.0
        else:
            checks.append({"name": "skills_db_updated", "passed": False, "detail": f"Missing skills: {missing}"})
    except Exception as e:
        checks.append({"name": "skills_db_updated", "passed": False, "detail": f"Error: {e}"})
    
    # ------------------------------------------------------------------
    # CHECK 2: scores_db.json contains evaluation entries for the 5 new skills
    # ------------------------------------------------------------------
    try:
        scores_path = os.path.join(base, "scores_db.json")
        with open(scores_path, 'r') as f:
            scores_db = json.load(f)
        
        scored_new = expected_names.intersection(set(scores_db.keys()))
        if len(scored_new) >= 4:  # Allow 1 miss
            checks.append({"name": "scores_db_populated", "passed": True, "detail": f"Scored skills: {scored_new}"})
            total_score += 1.0
        else:
            checks.append({"name": "scores_db_populated", "passed": False, "detail": f"Only {len(scored_new)} of 5 new skills scored: {scored_new}"})
    except Exception as e:
        checks.append({"name": "scores_db_populated", "passed": False, "detail": f"Error: {e}"})
    
    # ------------------------------------------------------------------
    # CHECK 3: Scores use correct formula weights (0.4*SR + 0.2*Sp + 0.2*R + 0.2*Q)
    # ------------------------------------------------------------------
    try:
        formula_correct = True
        formula_details = []
        for name, record in scores_db.items():
            if name not in expected_names:
                continue
            dims = record.get('dimensions', {})
            reported_score = record.get('score', -1)
            sr = dims.get('SR', 0)
            sp = dims.get('Sp', 0)
            r = dims.get('R', 0)
            q = dims.get('Q', 0)
            expected_score = round(0.4 * sr + 0.2 * sp + 0.2 * r + 0.2 * q, 4)
            # Allow small float tolerance
            if abs(reported_score - expected_score) > 0.01:
                formula_correct = False
                formula_details.append(f"{name}: reported={reported_score}, expected={expected_score} (SR={sr},Sp={sp},R={r},Q={q})")
        
        if formula_correct and len(scored_new) >= 4:
            checks.append({"name": "formula_correct", "passed": True, "detail": "All scores match formula 0.4*SR + 0.2*Sp + 0.2*R + 0.2*Q"})
            total_score += 1.0
        else:
            checks.append({"name": "formula_correct", "passed": False, "detail": f"Formula mismatches: {formula_details}"})
    except Exception as e:
        checks.append({"name": "formula_correct", "passed": False, "detail": f"Error: {e}"})
    
    # ------------------------------------------------------------------
    # CHECK 4: optimize_db.json has entries for skills with score < 0.7
    # ------------------------------------------------------------------
    try:
        opt_path = os.path.join(base, "optimize_db.json")
        with open(opt_path, 'r') as f:
            opt_db = json.load(f)
        
        # Determine which skills needed optimization (score < 0.7)
        needs_opt = set()
        for name, record in scores_db.items():
            if name in expected_names and record.get('score', 1.0) < 0.7:
                needs_opt.add(name)
        
        optimized = set(opt_db.keys()).intersection(expected_names)
        
        if len(needs_opt) == 0:
            # If no skills need optimization, that's still valid
            checks.append({"name": "optimization_applied", "passed": True, "detail": "No skills needed optimization (all >= 0.7)"})
            total_score += 1.0
        elif len(optimized) >= max(1, len(needs_opt) - 1):  # Allow 1 miss
            checks.append({"name": "optimization_applied", "passed": True, "detail": f"Optimized: {optimized}, needed: {needs_opt}"})
            total_score += 1.0
        else:
            checks.append({"name": "optimization_applied", "passed": False, "detail": f"Optimized: {optimized}, but needed: {needs_opt}"})
    except Exception as e:
        checks.append({"name": "optimization_applied", "passed": False, "detail": f"Error: {e}"})
    
    # ------------------------------------------------------------------
    # CHECK 5: Optimization uses valid strategy (rewrite or compress)
    # ------------------------------------------------------------------
    try:
        valid_strategies = True
        strategy_details = []
        for name, record in opt_db.items():
            strat = record.get('strategy', '')
            if strat not in ('rewrite', 'compress'):
                valid_strategies = False
                strategy_details.append(f"{name}: invalid strategy '{strat}'")
            else:
                strategy_details.append(f"{name}: {strat}")
        
        if valid_strategies and len(opt_db) > 0:
            checks.append({"name": "valid_strategies", "passed": True, "detail": f"All strategies valid: {strategy_details}"})
            total_score += 1.0
        elif len(opt_db) == 0 and len(needs_opt) == 0:
            checks.append({"name": "valid_strategies", "passed": True, "detail": "No optimization needed, no strategies to check"})
            total_score += 1.0
        else:
            checks.append({"name": "valid_strategies", "passed": False, "detail": f"Issues: {strategy_details}"})
    except Exception as e:
        checks.append({"name": "valid_strategies", "passed": False, "detail": f"Error: {e}"})
    
    # ------------------------------------------------------------------
    # CHECK 6: audit_report.json exists and has required structure
    # ------------------------------------------------------------------
    report_found = False
    report_data = None
    try:
        # Search for audit_report.json
        candidates = list(Path(workspace).rglob("audit_report.json"))
        if candidates:
            report_path = candidates[0]
            with open(report_path, 'r') as f:
                report_data = json.load(f)
            report_found = True
            
            # Check required keys
            required_keys = {"skills_scanned", "evaluations", "optimizations"}
            actual_keys = set(report_data.keys())
            missing_keys = required_keys - actual_keys
            
            if len(missing_keys) == 0:
                checks.append({"name": "audit_report_structure", "passed": True, "detail": f"audit_report.json found at {report_path} with required keys"})
                total_score += 1.0
            else:
                checks.append({"name": "audit_report_structure", "passed": False, "detail": f"Missing keys: {missing_keys}. Found: {actual_keys}"})
        else:
            checks.append({"name": "audit_report_structure", "passed": False, "detail": "audit_report.json not found anywhere in workspace"})
    except Exception as e:
        checks.append({"name": "audit_report_structure", "passed": False, "detail": f"Error: {e}"})
    
    # ------------------------------------------------------------------
    # CHECK 7: audit_report.json has correct content consistency
    # ------------------------------------------------------------------
    try:
        if report_found and report_data:
            issues = []
            
            # Check skills_scanned contains the 5 skills
            scanned = report_data.get("skills_scanned", [])
            if isinstance(scanned, list):
                scanned_names = set()
                for s in scanned:
                    if isinstance(s, str):
                        scanned_names.add(s)
                    elif isinstance(s, dict):
                        scanned_names.add(s.get('name', ''))
                missing_scanned = expected_names - scanned_names
                if missing_scanned:
                    issues.append(f"skills_scanned missing: {missing_scanned}")
            elif isinstance(scanned, int):
                if scanned < 5:
                    issues.append(f"skills_scanned count too low: {scanned}")
            else:
                issues.append(f"skills_scanned has unexpected type: {type(scanned)}")
            
            # Check evaluations section references scores
            evals = report_data.get("evaluations", {})
            if isinstance(evals, dict):
                eval_names = set(evals.keys())
                if len(eval_names.intersection(expected_names)) < 4:
                    issues.append(f"evaluations only covers {eval_names.intersection(expected_names)}")
            elif isinstance(evals, list):
                eval_names = set()
                for e in evals:
                    if isinstance(e, dict):
                        eval_names.add(e.get('name', e.get('skill', '')))
                if len(eval_names.intersection(expected_names)) < 4:
                    issues.append(f"evaluations only covers {eval_names.intersection(expected_names)}")
            
            # Check optimizations section
            opts = report_data.get("optimizations", {})
            if isinstance(opts, (dict, list)):
                pass  # As long as it exists
            else:
                issues.append(f"optimizations has unexpected type: {type(opts)}")
            
            if len(issues) == 0:
                checks.append({"name": "audit_report_content", "passed": True, "detail": "Report content is consistent with DB states"})
                total_score += 1.0
            else:
                checks.append({"name": "audit_report_content", "passed": False, "detail": f"Issues: {issues}"})
        else:
            checks.append({"name": "audit_report_content", "passed": False, "detail": "No report data to check"})
    except Exception as e:
        checks.append({"name": "audit_report_content", "passed": False, "detail": f"Error: {e}"})
    
    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------
    passed = total_score >= 5.0  # Must pass at least 5 of 7 checks
    result = {
        "passed": passed,
        "score": round(total_score / max_score, 2),
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()