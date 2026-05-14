import sys
import json
import math
import os
from pathlib import Path

def analyze_gpt_content(text, min_confidence=0.7):
    """Reference implementation mirroring the SKILL.md logic exactly."""
    normalized_text = text.lower()

    gpt_phrases = {
        'gpt-4': [
            'delve into', 'landscape of', 'realm of', "it's important to note",
            'multifaceted', 'nuanced', 'comprehensive', 'holistic approach'
        ],
        'gpt-3.5': [
            'as an ai language model', "i don't have personal", 'i apologize for',
            'certainly', 'absolutely', 'furthermore', 'moreover'
        ],
        'common': [
            "it's worth noting", 'keep in mind', 'in conclusion',
            'to summarize', 'in summary', 'navigate the', 'tapestry of'
        ]
    }

    gpt4_score = 0.0
    gpt35_score = 0.0
    common_score = 0.0
    found_phrases = []

    for phrase in gpt_phrases['gpt-4']:
        if phrase in normalized_text:
            gpt4_score += 0.2
            found_phrases.append({'phrase': phrase, 'model': 'gpt-4'})

    for phrase in gpt_phrases['gpt-3.5']:
        if phrase in normalized_text:
            gpt35_score += 0.2
            found_phrases.append({'phrase': phrase, 'model': 'gpt-3.5'})

    for phrase in gpt_phrases['common']:
        if phrase in normalized_text:
            common_score += 0.1
            found_phrases.append({'phrase': phrase, 'model': 'common'})

    # Structure analysis - must match JS regex \n\d+\. and \n[•\-\*]
    import re
    has_numbered_lists = len(re.findall(r'\n\d+\.', text)) >= 3
    has_bullet_points = len(re.findall(r'\n[•\-\*]', text)) >= 3
    structure_score = 0.15 if (has_numbered_lists or has_bullet_points) else 0.0

    # Sentence uniformity
    sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
    if sentences:
        avg_length = sum(len(s) for s in sentences) / len(sentences)
        variance = sum((len(s) - avg_length) ** 2 for s in sentences) / len(sentences)
    else:
        avg_length = 0.0
        variance = 0.0

    uniformity_score = 0.1 if variance < 500 else 0.0

    total_score = gpt4_score + gpt35_score + common_score + structure_score + uniformity_score
    confidence = min(total_score, 1.0)

    if gpt4_score > gpt35_score and gpt4_score > 0:
        detected_model = 'gpt-4'
    elif gpt35_score > gpt4_score and gpt35_score > 0:
        detected_model = 'gpt-3.5'
    elif common_score > 0:
        detected_model = 'gpt-family'
    else:
        detected_model = 'unknown'

    is_gpt = confidence >= min_confidence
    confidence_int = round(confidence * 100)

    if confidence >= 0.85:
        recommendation = 'Very likely GPT'
    elif confidence >= 0.70:
        recommendation = 'Likely GPT'
    elif confidence >= 0.50:
        recommendation = 'Possibly GPT'
    else:
        recommendation = 'Unlikely GPT or human-written'

    return {
        'isGPT': is_gpt,
        'confidence': confidence_int,
        'detectedModel': detected_model if is_gpt else 'not-gpt',
        'scores': {
            'gpt4': round(gpt4_score * 100) / 100,
            'gpt35': round(gpt35_score * 100) / 100,
            'common': round(common_score * 100) / 100,
            'structure': round(structure_score * 100) / 100,
            'uniformity': round(uniformity_score * 100) / 100,
        },
        'indicators': {
            'foundPhrases': len(found_phrases),
            'hasStructure': has_numbered_lists or has_bullet_points,
            'avgSentenceLength': round(avg_length),
            'sentenceVariance': round(variance),
        },
        'recommendation': recommendation,
    }

def run_eval(workspace_dir):
    checks = []

    # 1. Find analysis_report.json
    report_path = None
    candidates = list(Path(workspace_dir).rglob('analysis_report.json'))
    if candidates:
        report_path = candidates[0]

    if not report_path or not report_path.exists():
        checks.append({"name": "report_exists", "passed": False, "detail": "analysis_report.json not found anywhere in workspace"})
        return checks, 0.0

    checks.append({"name": "report_exists", "passed": True, "detail": f"Found at {report_path}"})

    # 2. Parse JSON
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "report_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return checks, 0.0

    checks.append({"name": "report_parseable", "passed": True, "detail": "Valid JSON"})

    # 3. Check all 5 submissions are present
    submission_names = ['submission_A.txt', 'submission_B.txt', 'submission_C.txt', 'submission_D.txt', 'submission_E.txt']
    
    # The report could be a dict keyed by filename, or a list
    if isinstance(report, dict):
        # keyed by submission name or stem
        def get_entry(name):
            if name in report:
                return report[name]
            stem = name.replace('.txt', '')
            if stem in report:
                return report[stem]
            # try keys that contain the stem
            for k in report:
                if stem in k or name in k:
                    return report[k]
            return None
    elif isinstance(report, list):
        def get_entry(name):
            stem = name.replace('.txt', '')
            for item in report:
                if isinstance(item, dict):
                    for k in ['submission', 'file', 'name', 'id', 'filename']:
                        if k in item and (name in str(item[k]) or stem in str(item[k])):
                            return item
            return None
    else:
        checks.append({"name": "report_structure", "passed": False, "detail": f"Report is neither dict nor list: {type(report)}"})
        return checks, 0.0

    all_present = True
    for name in submission_names:
        entry = get_entry(name)
        if entry is None:
            all_present = False
            checks.append({"name": f"submission_{name}_present", "passed": False, "detail": f"No entry found for {name}"})
        else:
            checks.append({"name": f"submission_{name}_present", "passed": True, "detail": "Found"})

    if not all_present:
        return checks, 0.0

    # 4. Load actual submission texts and compute expected values
    submissions_dir = Path(workspace_dir) / "platform/ingestion/raw/submissions"
    
    field_checks_passed = 0
    field_checks_total = 0

    for name in submission_names:
        txt_path = submissions_dir / name
        try:
            with open(txt_path, 'r') as f:
                text = f.read()
        except Exception as e:
            checks.append({"name": f"{name}_read", "passed": False, "detail": str(e)})
            continue

        expected = analyze_gpt_content(text)
        entry = get_entry(name)

        # If entry has a nested 'result' or 'analysis' key, drill in
        if isinstance(entry, dict):
            for nested_key in ['result', 'analysis', 'output']:
                if nested_key in entry and isinstance(entry[nested_key], dict):
                    entry = entry[nested_key]
                    break

        def check_field(field_path, exp_val, actual_obj):
            """Navigate dot-separated path."""
            parts = field_path.split('.')
            cur = actual_obj
            try:
                for p in parts:
                    cur = cur[p]
            except (KeyError, TypeError):
                return None
            return cur

        # Critical fields to check
        critical_checks = [
            ('isGPT', expected['isGPT']),
            ('confidence', expected['confidence']),
            ('detectedModel', expected['detectedModel']),
            ('recommendation', expected['recommendation']),
            ('scores.gpt4', expected['scores']['gpt4']),
            ('scores.gpt35', expected['scores']['gpt35']),
            ('scores.common', expected['scores']['common']),
            ('scores.structure', expected['scores']['structure']),
            ('scores.uniformity', expected['scores']['uniformity']),
            ('indicators.foundPhrases', expected['indicators']['foundPhrases']),
            ('indicators.hasStructure', expected['indicators']['hasStructure']),
        ]

        for field_path, exp_val in critical_checks:
            field_checks_total += 1
            actual_val = check_field(field_path, exp_val, entry)
            passed = actual_val == exp_val
            checks.append({
                "name": f"{name}::{field_path}",
                "passed": passed,
                "detail": f"expected={exp_val!r}, got={actual_val!r}"
            })
            if passed:
                field_checks_passed += 1

    # Score: file existence (20%) + field accuracy (80%)
    if field_checks_total > 0:
        field_accuracy = field_checks_passed / field_checks_total
    else:
        field_accuracy = 0.0

    base_score = 0.2  # for having valid parseable report with all submissions
    field_score = 0.8 * field_accuracy
    total_score = base_score + field_score

    return checks, total_score


def main():
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_eval(workspace_dir)
    except Exception as e:
        checks = [{"name": "eval_crashed", "passed": False, "detail": str(e)}]
        score = 0.0

    passed = score >= 0.7

    result = {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()