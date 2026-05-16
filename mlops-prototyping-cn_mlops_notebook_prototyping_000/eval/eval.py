import sys
import json
import re
import subprocess
from pathlib import Path

def load_notebook(path: Path):
    with open(path) as f:
        return json.load(f)

def all_sources(nb) -> str:
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in nb.get("cells", [])
    )

def run_check_script(nb_path: Path, workspace: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["./scripts/check-notebook.sh", str(nb_path)],
            capture_output=True, text=True,
            cwd=str(workspace), timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def main():
    workspace = Path(sys.argv[1])
    checks = []
    total_score = 0.0
    weight_each = 1.0 / 8  # 8 checks

    # ── Locate the target notebook ────────────────────────────────────────────
    candidates = list(workspace.rglob("fraud_detection_prototype.ipynb"))
    nb_found = len(candidates) > 0
    checks.append({
        "name": "notebook_file_exists",
        "passed": nb_found,
        "detail": f"Found: {candidates[0]}" if nb_found else "fraud_detection_prototype.ipynb not found anywhere in workspace"
    })
    if not nb_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    nb_path = candidates[0]

    # ── Load notebook ─────────────────────────────────────────────────────────
    try:
        nb = load_notebook(nb_path)
        src = all_sources(nb)
    except Exception as e:
        checks.append({"name": "notebook_parseable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "notebook_parseable", "passed": True, "detail": "Valid JSON / nbformat"})

    # ── Run proprietary check-notebook.sh ────────────────────────────────────
    script_ok, script_output = run_check_script(nb_path, workspace)
    checks.append({
        "name": "check_script_passes",
        "passed": script_ok,
        "detail": script_output.strip()[:800]
    })

    # ── H1 title in a markdown cell ──────────────────────────────────────────
    h1_ok = any(
        cell.get("cell_type") == "markdown" and
        re.search(r"^#\s+\S", "".join(cell.get("source", [])), re.MULTILINE)
        for cell in nb.get("cells", [])
    )
    checks.append({
        "name": "h1_title_in_markdown_cell",
        "passed": h1_ok,
        "detail": "H1 title found in a markdown cell" if h1_ok else "No markdown cell with H1 title (# Title) found"
    })

    # ── Config / Constants section with RANDOM_STATE ─────────────────────────
    config_section_ok = bool(re.search(r"##\s+Config", src, re.IGNORECASE))
    random_state_ok = bool(re.search(r"RANDOM_STATE\s*=\s*\d+", src))
    checks.append({
        "name": "config_section_with_random_state",
        "passed": config_section_ok and random_state_ok,
        "detail": f"Config section: {config_section_ok}, RANDOM_STATE constant: {random_state_ok}"
    })

    # ── sklearn Pipeline used (not just imported) ─────────────────────────────
    pipeline_usage_ok = bool(re.search(r"Pipeline\s*\(", src))
    checks.append({
        "name": "sklearn_pipeline_instantiated",
        "passed": pipeline_usage_ok,
        "detail": "Pipeline(...) found in notebook" if pipeline_usage_ok else "No Pipeline(...) instantiation found"
    })

    # ── Data split BEFORE any fit call ────────────────────────────────────────
    # Heuristic: train_test_split must appear before .fit( in the concatenated source
    tts_match = re.search(r"train_test_split", src)
    fit_match  = re.search(r"\.fit\s*\(", src)
    split_before_fit = (
        tts_match is not None and fit_match is not None and
        tts_match.start() < fit_match.start()
    )
    checks.append({
        "name": "split_before_fit_no_leakage",
        "passed": split_before_fit,
        "detail": (
            f"train_test_split at pos {tts_match.start() if tts_match else 'N/A'}, "
            f".fit( at pos {fit_match.start() if fit_match else 'N/A'}"
        )
    })

    # ── No bare magic numbers in code cells (test_size must use a named constant) ─
    code_src = "\n".join(
        "".join(cell.get("source", []))
        for cell in nb.get("cells", [])
        if cell.get("cell_type") == "code"
    )
    # Detect test_size=<literal float> without a variable reference
    magic_test_size = bool(re.search(r"test_size\s*=\s*0\.\d+", code_src))
    # Detect random_state=<literal int> in non-config code cells
    # Allow RANDOM_STATE constant usage; flag inline literals like random_state=42
    magic_random_state = bool(re.search(r"random_state\s*=\s*\d+", code_src))
    no_magic_numbers = (not magic_test_size) and (not magic_random_state)
    checks.append({
        "name": "no_magic_numbers_in_code",
        "passed": no_magic_numbers,
        "detail": (
            f"magic test_size literal: {magic_test_size}, "
            f"magic random_state literal: {magic_random_state}. "
            "All numeric params must use named Config constants."
        )
    })

    # ── Compute score ─────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)
    overall_passed = all(c["passed"] for c in checks)

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()