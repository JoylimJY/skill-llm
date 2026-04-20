import json
import os
import re
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        # Check benchmark_task.json exists (case-insensitive)
        benchmark_path = ws / 'benchmark_task.json'
        add_check('file_exists_benchmark_task_json', benchmark_path.exists(), 
                  f"benchmark_task.json {'found' if benchmark_path.exists() else 'missing'}")

        if not benchmark_path.exists():
            result = {
                'passed': False,
                'score': 0.0,
                'checks': checks,
            }
            print(json.dumps(result, ensure_ascii=False))
            return

        # Load and validate JSON (with error recovery)
        try:
            content = benchmark_path.read_text(encoding='utf-8', errors='replace')
            # Try to extract JSON if there's extra text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                task_data = json.loads(json_match.group())
            else:
                task_data = json.loads(content)
            add_check('valid_json', True, 'benchmark_task.json is valid JSON')
        except json.JSONDecodeError as e:
            add_check('valid_json', False, f'Invalid JSON: {e}')
            result = {
                'passed': False,
                'score': 0.0,
                'checks': checks,
            }
            print(json.dumps(result, ensure_ascii=False))
            return

        # Check required top-level fields (case-insensitive matching)
        required_fields = [
            'task_id', 'task_name', 'description', 'difficulty', 'category',
            'input_generation', 'prompt_template', 'ground_truth', 'grader',
            'adversarial_aspects'
        ]
        for field in required_fields:
            # Case-insensitive field matching
            found = any(field.lower() == k.lower() for k in task_data.keys())
            add_check(f'has_field_{field}', found, 
                      f"Field '{field}' {'present' if found else 'missing'}")

        # Check difficulty is 'hard' (case-insensitive)
        difficulty = task_data.get('difficulty', '').lower()
        add_check('difficulty_hard', difficulty == 'hard',
                  f"Difficulty is '{task_data.get('difficulty')}' (expected 'hard')")

        # Check category is 'adversarial-prompting' (case-insensitive)
        category = task_data.get('category', '').lower()
        add_check('category_adversarial', 'adversarial' in category,
                  f"Category is '{task_data.get('category')}' (expected 'adversarial-prompting')")

        # Check input_generation has required structure
        input_gen = task_data.get('input_generation', {})
        if isinstance(input_gen, dict):
            add_check('input_gen_has_script', 'script' in input_gen,
                      f"input_generation has 'script' field: {'yes' if 'script' in input_gen else 'no'}")
            # Check for deterministic flag (flexible naming)
            has_deterministic = any('determin' in k.lower() for k in input_gen.keys())
            add_check('input_gen_deterministic', has_deterministic,
                      f"input_generation has deterministic flag: {'yes' if has_deterministic else 'no'}")
        else:
            add_check('input_gen_has_script', False, "input_generation is not a dict")
            add_check('input_gen_deterministic', False, "input_generation is not a dict")

        # Check prompt_template has system and user (flexible)
        prompt_template = task_data.get('prompt_template', {})
        if isinstance(prompt_template, dict):
            has_system = any('system' in k.lower() for k in prompt_template.keys())
            has_user = any('user' in k.lower() for k in prompt_template.keys())
            add_check('prompt_has_system', has_system,
                      f"prompt_template has 'system': {'yes' if has_system else 'no'}")
            add_check('prompt_has_user', has_user,
                      f"prompt_template has 'user': {'yes' if has_user else 'no'}")
        else:
            add_check('prompt_has_system', False, "prompt_template is not a dict")
            add_check('prompt_has_user', False, "prompt_template is not a dict")

        # Check grader has scoring_criteria (flexible)
        grader = task_data.get('grader', {})
        if isinstance(grader, dict):
            has_criteria = any('criteria' in k.lower() or 'scoring' in k.lower() for k in grader.keys())
            add_check('grader_has_criteria', has_criteria,
                      f"grader has scoring criteria: {'yes' if has_criteria else 'no'}")
        else:
            add_check('grader_has_criteria', False, "grader is not a dict")

        # Check adversarial_aspects exists and has content
        adv_aspects = task_data.get('adversarial_aspects', [])
        if isinstance(adv_aspects, list):
            add_check('has_adversarial_aspects', len(adv_aspects) >= 2,
                      f"Has {len(adv_aspects)} adversarial aspects (expected >= 2)")
        else:
            add_check('has_adversarial_aspects', False, "adversarial_aspects is not a list")

        # Check ground_truth exists
        ground_truth = task_data.get('ground_truth', {})
        if isinstance(ground_truth, dict):
            add_check('has_ground_truth', len(ground_truth) > 0,
                      f"ground_truth has {len(ground_truth)} fields")
        else:
            add_check('has_ground_truth', False, "ground_truth is not a dict")

    except Exception as e:
        add_check('unexpected_error', False, f'Unexpected evaluator error: {e}')

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks) if checks else 1
    result = {
        'passed': passed_count == total,
        'score': passed_count / total,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    main(workspace)