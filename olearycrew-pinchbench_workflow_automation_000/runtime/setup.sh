#!/usr/bin/env bash
set -e

SKILL_DIR="/workspace/pinchbench_skill"

# Create the mock benchmark.py that validates flags and produces realistic JSON output
cat > "$SKILL_DIR/benchmark.py" << 'PYEOF'
#!/usr/bin/env python3
"""
Mock PinchBench benchmark runner for testing purposes.
Simulates the real benchmark.py behavior including all CLI flags.
"""
import argparse
import json
import os
import sys
import re
import time
import random
from pathlib import Path
from datetime import datetime, timezone

# Realistic scores per task (deterministic seed)
TASK_SCORES = {
    "task_00_sanity":                {"mean": 1.0,  "cat": "Basic"},
    "task_01_calendar":              {"mean": 0.72, "cat": "Productivity"},
    "task_02_stock":                 {"mean": 0.85, "cat": "Research"},
    "task_03_blog":                  {"mean": 0.61, "cat": "Writing"},
    "task_04_weather":               {"mean": 0.78, "cat": "Coding"},
    "task_05_summary":               {"mean": 0.43, "cat": "Analysis"},
    "task_06_events":                {"mean": 0.55, "cat": "Research"},
    "task_07_email":                 {"mean": 0.88, "cat": "Writing"},
    "task_08_memory":                {"mean": 0.34, "cat": "Memory"},
    "task_09_files":                 {"mean": 0.91, "cat": "Files"},
    "task_10_workflow":              {"mean": 0.47, "cat": "Integration"},
    "task_11_clawdhub":              {"mean": 0.62, "cat": "Skills"},
    "task_12_skill_search":          {"mean": 0.70, "cat": "Skills"},
    "task_13_image_gen":             {"mean": 0.38, "cat": "Creative"},
    "task_14_humanizer":             {"mean": 0.59, "cat": "Writing"},
    "task_15_daily_summary":         {"mean": 0.80, "cat": "Productivity"},
    "task_16_email_triage":          {"mean": 0.45, "cat": "Email"},
    "task_17_email_search":          {"mean": 0.67, "cat": "Email"},
    "task_18_market_research":       {"mean": 0.52, "cat": "Research"},
    "task_19_spreadsheet_summary":   {"mean": 0.76, "cat": "Analysis"},
    "task_20_eli5_pdf_summary":      {"mean": 0.41, "cat": "Analysis"},
    "task_21_openclaw_comprehension":{"mean": 0.83, "cat": "Knowledge"},
    "task_22_second_brain":          {"mean": 0.37, "cat": "Memory"},
}

AUTOMATED_TASKS = [
    "task_00_sanity", "task_02_stock", "task_04_weather", "task_05_summary",
    "task_08_memory", "task_09_files", "task_12_skill_search", "task_17_email_search",
    "task_19_spreadsheet_summary", "task_20_eli5_pdf_summary", "task_21_openclaw_comprehension",
]

def parse_args():
    parser = argparse.ArgumentParser(description="PinchBench Benchmark Runner")
    parser.add_argument("--model", required=False, help="Model identifier")
    parser.add_argument("--suite", default="all", help="Suite: all, automated-only, or comma-separated task IDs")
    parser.add_argument("--output-dir", default="results/", help="Results directory")
    parser.add_argument("--timeout-multiplier", type=float, default=1.0, help="Scale task timeouts")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs per task")
    parser.add_argument("--no-upload", action="store_true", help="Skip uploading to leaderboard")
    parser.add_argument("--register", action="store_true", help="Register for API token")
    parser.add_argument("--upload", metavar="FILE", help="Upload previous results JSON")
    return parser.parse_args()

def get_tasks_for_suite(suite):
    if suite == "all":
        return list(TASK_SCORES.keys())
    elif suite == "automated-only":
        return AUTOMATED_TASKS
    else:
        # Comma-separated task IDs - THIS IS THE KEY PROPRIETARY BEHAVIOR
        task_ids = [t.strip() for t in suite.split(",")]
        valid = []
        invalid = []
        for tid in task_ids:
            if tid in TASK_SCORES:
                valid.append(tid)
            else:
                invalid.append(tid)
        if invalid:
            print(f"WARNING: Unknown task IDs: {invalid}", file=sys.stderr)
        if not valid:
            print("ERROR: No valid task IDs specified.", file=sys.stderr)
            sys.exit(1)
        return valid

def simulate_run(task_id, runs, timeout_multiplier):
    """Simulate multiple runs with slight variance."""
    rng = random.Random(hash(task_id) & 0xFFFFFFFF)
    base_mean = TASK_SCORES[task_id]["mean"]
    run_scores = []
    for _ in range(runs):
        noise = rng.uniform(-0.05, 0.05) * timeout_multiplier
        score = max(0.0, min(1.0, base_mean + noise))
        run_scores.append(round(score, 4))
    
    mean_score = round(sum(run_scores) / len(run_scores), 4)
    return {
        "mean": mean_score,
        "runs": run_scores,
        "std": round((sum((s - mean_score)**2 for s in run_scores) / max(len(run_scores),1))**0.5, 4) if runs > 1 else 0.0,
    }

def main():
    args = parse_args()
    
    if args.register:
        print("Requesting API token...")
        print("Token: pb_mock_token_abc123xyz")
        print("Save this token securely. Use it for leaderboard submissions.")
        sys.exit(0)
    
    if args.upload:
        print(f"Uploading results from {args.upload} to leaderboard...")
        print("Upload successful. View at https://pinchbench.com/leaderboard")
        sys.exit(0)
    
    if not args.model:
        print("ERROR: --model is required", file=sys.stderr)
        sys.exit(1)
    
    tasks = get_tasks_for_suite(args.suite)
    
    # Simulate benchmark execution
    print(f"PinchBench v1.0.0")
    print(f"Model: {args.model}")
    print(f"Suite: {args.suite}")
    print(f"Tasks: {len(tasks)}")
    print(f"Runs per task: {args.runs}")
    print(f"Timeout multiplier: {args.timeout_multiplier}x")
    print(f"Upload: {'disabled' if args.no_upload else 'enabled'}")
    print("-" * 60)
    
    task_results = []
    for task_id in tasks:
        cat = TASK_SCORES[task_id]["cat"]
        grading = simulate_run(task_id, args.runs, args.timeout_multiplier)
        status = "PASS" if grading["mean"] >= 0.5 else "FAIL"
        print(f"  [{status}] {task_id:<35} score={grading['mean']:.4f}")
        task_results.append({
            "task_id": task_id,
            "category": cat,
            "grading": grading,
            "status": status,
        })
        time.sleep(0.05)  # Simulate work
    
    overall = round(sum(t["grading"]["mean"] for t in task_results) / len(task_results), 4)
    
    print("-" * 60)
    print(f"Overall average: {overall:.4f}")
    
    # Save results
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename: NNNN_model-slug.json
    existing = list(output_dir.glob("*.json"))
    run_num = len(existing) + 1
    model_slug = re.sub(r'[^a-zA-Z0-9_-]', '-', args.model)
    output_file = output_dir / f"{run_num:04d}_{model_slug}.json"
    
    results = {
        "model": args.model,
        "suite": args.suite,
        "runs_per_task": args.runs,
        "timeout_multiplier": args.timeout_multiplier,
        "overall_mean": overall,
        "tasks": task_results,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pinchbench_version": "1.0.0",
            "uploaded": not args.no_upload,
        }
    }
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved: {output_file}")
    
    if not args.no_upload:
        print("Uploading results to leaderboard...")
        print("Upload successful. View at https://pinchbench.com/leaderboard")
    else:
        print("Upload skipped (--no-upload).")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
PYEOF

chmod +x "$SKILL_DIR/benchmark.py"

# Ensure uv is available in PATH
export PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Initialize the uv project so `uv run` works
cd "$SKILL_DIR"
uv init --no-readme --no-workspace 2>/dev/null || true
# Make sure uv can run the script
uv python pin 3.11 2>/dev/null || true

echo "Setup complete. Mock benchmark.py installed at $SKILL_DIR/benchmark.py"
echo "uv available: $(which uv 2>/dev/null || echo 'not found')"