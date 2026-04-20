import json
import os
import re
from pathlib import Path

workspace = Path(os.sys.argv[1]) if len(os.sys.argv) > 1 else Path('.')
checks = []

try:
    output_dir = workspace / "output"
    hardware_path = workspace / "hardware.json"
    markers_path = workspace / "markers.txt"

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # Find report JSON file (flexible matching)
    report_path = None
    if output_dir.exists():
        for f in output_dir.glob("*.json"):
            fname = f.name.lower()
            if 'report' in fname or 'recommendation' in fname:
                report_path = f
                break

    # Find summary text file (flexible matching)
    summary_path = None
    if output_dir.exists():
        for f in output_dir.glob("*.txt"):
            fname = f.name.lower()
            if 'summary' in fname or 'report' in fname:
                summary_path = f
                break

    # Check 1: required files exist
    try:
        exists = report_path is not None and summary_path is not None
        detail = f"report.json exists={report_path is not None}, summary.txt exists={summary_path is not None}"
        if report_path:
            detail += f" (found: {report_path.name})"
        if summary_path:
            detail += f" (found: {summary_path.name})"
        add_check("output_files_exist", exists, detail)
    except Exception as e:
        add_check("output_files_exist", False, f"error checking files: {e}")

    # Check 2: report JSON structure (flexible)
    report = None
    try:
        if report_path and report_path.exists():
            report = json.loads(report_path.read_text(encoding='utf-8'))
            # Accept various reasonable structures for recommendations
            has_top_models = isinstance(report, dict) and 'top_models' in report
            has_top_recs = isinstance(report, dict) and 'top_recommendations' in report
            has_ranked_recs = isinstance(report, dict) and 'ranked_recommendations' in report
            has_models = isinstance(report, dict) and 'models' in report
            ok = has_top_models or has_top_recs or has_ranked_recs or has_models
            add_check("report_json_structure", ok, f"keys={list(report.keys()) if isinstance(report, dict) else 'n/a'}")
        else:
            add_check("report_json_structure", False, "report.json missing")
    except Exception as e:
        add_check("report_json_structure", False, f"parse error: {e}")

    # Check 3: top model is the expected coding model, fuzzy match
    try:
        if isinstance(report, dict):
            top = {}
            # Try top_models list first
            top_models = report.get('top_models', [])
            if top_models and isinstance(top_models, list):
                top = top_models[0] if top_models else {}
            # Try top_recommendations dict
            elif 'top_recommendations' in report:
                top_recs = report.get('top_recommendations', {})
                top = top_recs.get('coding', {}) or top_recs.get('reasoning', {}) or {}
            # Try ranked_recommendations dict (new)
            elif 'ranked_recommendations' in report:
                ranked = report.get('ranked_recommendations', {})
                top = ranked.get('coding', [{}])[0] if isinstance(ranked.get('coding'), list) else {}
            # Try models list
            elif 'models' in report:
                models = report.get('models', [])
                if models and isinstance(models, list):
                    top = models[0] if models else {}
            
            name = str(top.get('name', '') or top.get('model', '')).lower()
            ok = ('qwen' in name and 'coder' in name and '7b' in name)
            add_check("top_model_is_coding_pick", ok, f"top_model={top.get('name', top.get('model', ''))}")
        else:
            add_check("top_model_is_coding_pick", False, "report unavailable")
    except Exception as e:
        add_check("top_model_is_coding_pick", False, f"error: {e}")

    # Check 4: summary mentions marginal fit note if any marginal model exists in source recommendations
    try:
        has_marginal = False
        if hardware_path.exists():
            rec_path = workspace / 'recommendations.json'
            if rec_path.exists():
                rec = json.loads(rec_path.read_text(encoding='utf-8'))
                for m in rec.get('models', []):
                    fit_level = str(m.get('fit_level', '')).strip().lower()
                    # Check for 'good' with high utilization or 'marginal'
                    if fit_level == 'marginal' or (fit_level == 'good' and m.get('utilization_pct', 0) > 90):
                        has_marginal = True
                        break
        
        summary_text = ""
        if summary_path and summary_path.exists():
            summary_text = summary_path.read_text(encoding='utf-8').lower()
        
        # Check for marginal fit mention in summary
        has_marginal_mention = ('marginal' in summary_text and 'fit' in summary_text) or \
                               ('warning' in summary_text and 'utilization' in summary_text) or \
                               ('92' in summary_text and 'vram' in summary_text)
        
        ok = (not has_marginal) or has_marginal_mention
        add_check("marginal_fit_note", ok, f"has_marginal={has_marginal}, summary_mentions_marginal={has_marginal_mention}")
    except Exception as e:
        add_check("marginal_fit_note", False, f"error: {e}")

    # Check 5: marker file present and preserved
    try:
        marker_text = markers_path.read_text(encoding='utf-8').lower() if markers_path.exists() else ''
        ok = 'llmfit-adv-001' in marker_text and 'recommendation-set-a' in marker_text
        add_check("marker_content_present", ok, f"markers_found={ok}")
    except Exception as e:
        add_check("marker_content_present", False, f"error: {e}")

except Exception as e:
    checks.append({"name": "fatal", "passed": False, "detail": f"unexpected eval error: {e}"})

score = (sum(1 for c in checks if c.get('passed')) / len(checks)) if checks else 0.0
passed = all(c.get('passed') for c in checks) if checks else False
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))