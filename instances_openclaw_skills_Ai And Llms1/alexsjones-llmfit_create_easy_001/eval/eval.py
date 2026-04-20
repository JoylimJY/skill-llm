import json
import sys
import re
from pathlib import Path


def normalize(text):
    try:
        return ''.join(ch.lower() for ch in text if ch.isalnum() or ch.isspace())
    except Exception:
        return ''


def safe_read(path):
    """Always returns (text, error) tuple"""
    try:
        content = Path(path).read_text(encoding='utf-8', errors='ignore')
        return content, None
    except Exception as e:
        return None, str(e)


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    # Check 1: task.yaml or task.md exists and has required fields
    task_yaml = workspace / 'task.yaml'
    task_md = workspace / 'task.md'
    task_file = task_yaml if task_yaml.exists() else (task_md if task_md.exists() else None)
    
    try:
        if not task_file:
            checks.append({"name": "task_yaml_exists", "passed": False, "detail": "task.yaml or task.md is missing"})
        else:
            text, err = safe_read(task_file)
            if text is None:
                checks.append({"name": "task_yaml_exists", "passed": False, "detail": f"Could not read task file: {err}"})
            else:
                n = normalize(text)
                has_name = 'name' in n or 'task' in n
                has_description = 'description' in n or 'extract' in n or 'facts' in n
                has_input = 'source.pdf' in text.lower() or 'input' in n
                has_output = 'output' in n or 'facts' in n
                passed = has_name and has_description and has_input and has_output
                checks.append({"name": "task_yaml_exists", "passed": passed, "detail": "task file should have name, description, input and output fields"})
    except Exception as e:
        checks.append({"name": "task_yaml_exists", "passed": False, "detail": f"Unexpected error checking task file: {e}"})

    # Check 2: expected_output.txt exists and has expected content
    expected_out = workspace / 'expected_output.txt'
    try:
        if not expected_out.exists():
            checks.append({"name": "expected_output_exists", "passed": False, "detail": "expected_output.txt is missing"})
        else:
            text, err = safe_read(expected_out)
            if text is None:
                checks.append({"name": "expected_output_exists", "passed": False, "detail": f"Could not read expected_output.txt: {err}"})
            else:
                n = normalize(text)
                has_task = 'task' in n
                has_model = 'qwen' in n
                has_fit = 'good' in n
                has_quant = 'q5' in n
                passed = has_task and has_model and has_fit and has_quant
                checks.append({"name": "expected_output_exists", "passed": passed, "detail": "expected_output.txt should contain task, model, fit level, and quantization"})
    except Exception as e:
        checks.append({"name": "expected_output_exists", "passed": False, "detail": f"Unexpected error checking expected_output.txt: {e}"})

    # Check 3: evaluate.sh exists and is executable
    eval_sh = workspace / 'evaluate.sh'
    try:
        if not eval_sh.exists():
            checks.append({"name": "evaluate_sh_exists", "passed": False, "detail": "evaluate.sh is missing"})
        else:
            text, err = safe_read(eval_sh)
            if text is None:
                checks.append({"name": "evaluate_sh_exists", "passed": False, "detail": f"Could not read evaluate.sh: {err}"})
            else:
                has_shebang = '#!/bin/bash' in text or '#!/bin/sh' in text
                has_check = 'output' in text.lower() or 'facts' in text.lower()
                has_compare = 'diff' in text.lower() or 'compare' in text.lower() or 'match' in text.lower()
                passed = has_shebang and has_check and has_compare
                checks.append({"name": "evaluate_sh_exists", "passed": passed, "detail": "evaluate.sh should check output file and compare with expected"})
    except Exception as e:
        checks.append({"name": "evaluate_sh_exists", "passed": False, "detail": f"Unexpected error checking evaluate.sh: {e}"})

    # Check 4: source.pdf exists (input file)
    pdf = workspace / 'source.pdf'
    try:
        if not pdf.exists():
            checks.append({"name": "input_pdf_exists", "passed": False, "detail": "source.pdf is missing"})
        else:
            checks.append({"name": "input_pdf_exists", "passed": True, "detail": "source.pdf exists"})
    except Exception as e:
        checks.append({"name": "input_pdf_exists", "passed": False, "detail": f"Unexpected error checking source.pdf: {e}"})

    score = 0.0
    try:
        score = sum(1 for c in checks if c.get('passed')) / max(len(checks), 1)
    except Exception:
        score = 0.0
    passed = bool(checks) and all(c.get('passed') for c in checks)
    print(json.dumps({"passed": passed, "score": score, "checks": checks}))


if __name__ == '__main__':
    main()