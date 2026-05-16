import sys
import json
import math
from pathlib import Path

def load_jsonl(path):
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    agent_id = "financebot"
    optimizer_base = workspace / "workspace" / "subagents" / agent_id / "optimizer"
    
    # ==== CHECK 1: optimizer directory structure exists ====
    try:
        dir_exists = optimizer_base.is_dir()
        prompts_dir = (optimizer_base / "prompts").is_dir()
        checks.append({
            "name": "optimizer_directory_structure",
            "passed": dir_exists and prompts_dir,
            "detail": f"optimizer dir: {dir_exists}, prompts subdir: {prompts_dir}"
        })
    except Exception as e:
        checks.append({"name": "optimizer_directory_structure", "passed": False, "detail": str(e)})

    # ==== CHECK 2: config.json has required fields ====
    try:
        config_path = optimizer_base / "config.json"
        config = json.loads(config_path.read_text(encoding='utf-8'))
        
        required_fields = ["agent_id", "optimization_target", "metrics", "ab_test", "prompt_versions", "current_version", "optimization_interval"]
        missing = [f for f in required_fields if f not in config]
        
        agent_id_ok = config.get("agent_id") == "financebot"
        ab_test_ok = config.get("ab_test") == True
        current_version_ok = config.get("current_version") == "v2.0"
        opt_interval_ok = config.get("optimization_interval") == 100
        metrics_ok = isinstance(config.get("metrics"), list) and len(config.get("metrics", [])) > 0
        prompt_versions_ok = isinstance(config.get("prompt_versions"), list) and "v2.0" in config.get("prompt_versions", [])
        
        all_ok = (not missing) and agent_id_ok and ab_test_ok and current_version_ok and opt_interval_ok and metrics_ok and prompt_versions_ok
        checks.append({
            "name": "config_json_correct_fields",
            "passed": all_ok,
            "detail": f"missing={missing}, agent_id_ok={agent_id_ok}, ab_test_ok={ab_test_ok}, current_version_ok={current_version_ok}, interval_ok={opt_interval_ok}, metrics_ok={metrics_ok}, prompt_versions_ok={prompt_versions_ok}"
        })
    except Exception as e:
        checks.append({"name": "config_json_correct_fields", "passed": False, "detail": str(e)})

    # ==== CHECK 3: Prompt version files exist ====
    try:
        prompts_dir = optimizer_base / "prompts"
        v10 = (prompts_dir / "v1.0.txt").is_file()
        v11 = (prompts_dir / "v1.1.txt").is_file()
        v20 = (prompts_dir / "v2.0.txt").is_file()
        
        # v2.0.txt must have non-trivial content
        v20_content = ""
        if v20:
            v20_content = (prompts_dir / "v2.0.txt").read_text(encoding='utf-8').strip()
        
        v20_has_content = len(v20_content) > 20
        
        all_ok = v10 and v11 and v20 and v20_has_content
        checks.append({
            "name": "prompt_version_files_exist",
            "passed": all_ok,
            "detail": f"v1.0={v10}, v1.1={v11}, v2.0={v20}, v2.0_has_content={v20_has_content} (len={len(v20_content)})"
        })
    except Exception as e:
        checks.append({"name": "prompt_version_files_exist", "passed": False, "detail": str(e)})

    # ==== CHECK 4: trajectories.jsonl has correct schema and 4 records ====
    try:
        traj_path = optimizer_base / "trajectories.jsonl"
        trajectories = load_jsonl(traj_path)
        
        count_ok = len(trajectories) == 4
        
        required_traj_fields = ["agent_id", "timestamp", "task", "output", "metrics", "prompt_version"]
        schema_errors = []
        for i, t in enumerate(trajectories):
            missing = [f for f in required_traj_fields if f not in t]
            if missing:
                schema_errors.append(f"record {i}: missing {missing}")
            if t.get("agent_id") != "financebot":
                schema_errors.append(f"record {i}: wrong agent_id '{t.get('agent_id')}'")
            # output must contain predicted_roi and confidence
            output = t.get("output", {})
            if not isinstance(output, dict):
                schema_errors.append(f"record {i}: output is not dict")
            elif "predicted_roi" not in output:
                schema_errors.append(f"record {i}: output missing predicted_roi")
            # metrics must be present as dict
            metrics = t.get("metrics", {})
            if not isinstance(metrics, dict):
                schema_errors.append(f"record {i}: metrics is not dict")
        
        schema_ok = len(schema_errors) == 0
        checks.append({
            "name": "trajectories_jsonl_schema",
            "passed": count_ok and schema_ok,
            "detail": f"count={len(trajectories)} (expected 4), schema_errors={schema_errors[:3]}"
        })
    except Exception as e:
        checks.append({"name": "trajectories_jsonl_schema", "passed": False, "detail": str(e)})
        trajectories = []

    # ==== CHECK 5: rewards.jsonl has correct schema and 4 records ====
    try:
        rewards_path = optimizer_base / "rewards.jsonl"
        rewards = load_jsonl(rewards_path)
        
        count_ok = len(rewards) == 4
        
        required_reward_fields = ["agent_id", "trajectory_id", "timestamp", "reward_value", "reward_type"]
        schema_errors = []
        for i, r in enumerate(rewards):
            missing = [f for f in required_reward_fields if f not in r]
            if missing:
                schema_errors.append(f"record {i}: missing {missing}")
            if r.get("agent_id") != "financebot":
                schema_errors.append(f"record {i}: wrong agent_id")
            if r.get("reward_type") != "prediction_accuracy":
                schema_errors.append(f"record {i}: wrong reward_type '{r.get('reward_type')}'")
            rv = r.get("reward_value")
            if not isinstance(rv, (int, float)) or rv < 0 or rv > 1:
                schema_errors.append(f"record {i}: reward_value {rv} not in [0,1]")
        
        schema_ok = len(schema_errors) == 0
        checks.append({
            "name": "rewards_jsonl_schema",
            "passed": count_ok and schema_ok,
            "detail": f"count={len(rewards)} (expected 4), schema_errors={schema_errors[:3]}"
        })
    except Exception as e:
        checks.append({"name": "rewards_jsonl_schema", "passed": False, "detail": str(e)})
        rewards = []

    # ==== CHECK 6: reward values use the correct formula: 1.0 / (1.0 + |predicted - actual|) ====
    try:
        expected_data = [
            ("预测任务 ROI", 2.5, 2.3),
            ("预测任务 ROI", 3.1, 3.8),
            ("预测任务 ROI", 1.8, 1.9),
            ("预测任务 ROI", 4.0, 2.5),
        ]
        expected_rewards = [1.0 / (1.0 + abs(pred - actual)) for (_, pred, actual) in expected_data]
        
        rewards_path = optimizer_base / "rewards.jsonl"
        rewards = load_jsonl(rewards_path)
        
        actual_reward_values = sorted([r["reward_value"] for r in rewards])
        expected_sorted = sorted(expected_rewards)
        
        TOLERANCE = 0.001
        formula_ok = all(
            abs(a - e) < TOLERANCE
            for a, e in zip(actual_reward_values, expected_sorted)
        )
        
        checks.append({
            "name": "reward_formula_correct",
            "passed": formula_ok,
            "detail": f"expected (sorted)={[round(v,4) for v in expected_sorted]}, actual (sorted)={[round(v,4) for v in actual_reward_values]}"
        })
    except Exception as e:
        checks.append({"name": "reward_formula_correct", "passed": False, "detail": str(e)})

    # ==== CHECK 7: trajectory_id in rewards equals the task field of corresponding trajectory ====
    try:
        rewards_path = optimizer_base / "rewards.jsonl"
        traj_path = optimizer_base / "trajectories.jsonl"
        rewards = load_jsonl(rewards_path)
        trajectories = load_jsonl(traj_path)
        
        # Get all task values from trajectories
        task_values = {t.get("task") for t in trajectories}
        # All reward trajectory_ids must match a task value
        traj_id_ok = all(r.get("trajectory_id") in task_values for r in rewards)
        
        checks.append({
            "name": "trajectory_id_matches_task_field",
            "passed": traj_id_ok,
            "detail": f"task_values={task_values}, reward_traj_ids={[r.get('trajectory_id') for r in rewards]}"
        })
    except Exception as e:
        checks.append({"name": "trajectory_id_matches_task_field", "passed": False, "detail": str(e)})

    # ==== CHECK 8: optimization_report.json has required fields and correct avg_reward ====
    try:
        report_path = optimizer_base / "optimization_report.json"
        report = json.loads(report_path.read_text(encoding='utf-8'))
        
        required_report_fields = ["agent_id", "total_trajectories", "total_rewards", "average_reward", 
                                   "high_reward_patterns", "low_reward_patterns", "suggestions"]
        missing = [f for f in required_report_fields if f not in report]
        
        agent_id_ok = report.get("agent_id") == "financebot"
        total_traj_ok = report.get("total_trajectories") == 4
        total_rewards_ok = report.get("total_rewards") == 4
        
        # Verify average_reward matches the formula-derived rewards
        expected_data = [
            (2.5, 2.3), (3.1, 3.8), (1.8, 1.9), (4.0, 2.5)
        ]
        expected_rewards_vals = [1.0 / (1.0 + abs(pred - actual)) for (pred, actual) in expected_data]
        expected_avg = sum(expected_rewards_vals) / len(expected_rewards_vals)
        
        actual_avg = report.get("average_reward", -1)
        avg_ok = abs(actual_avg - expected_avg) < 0.01
        
        schema_ok = not missing
        all_ok = schema_ok and agent_id_ok and total_traj_ok and total_rewards_ok and avg_ok
        
        checks.append({
            "name": "optimization_report_correct",
            "passed": all_ok,
            "detail": f"missing={missing}, agent_id_ok={agent_id_ok}, total_traj={total_traj_ok}, total_rewards={total_rewards_ok}, avg_ok={avg_ok} (expected={round(expected_avg,4)}, got={round(actual_avg,4) if isinstance(actual_avg, float) else actual_avg})"
        })
    except Exception as e:
        checks.append({"name": "optimization_report_correct", "passed": False, "detail": str(e)})

    # ==== SCORING ====
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)
    
    result = {
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)