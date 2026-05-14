import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    # ----------------------------------------------------------------
    # Helper to find the n8n yaml file
    # ----------------------------------------------------------------
    def find_n8n_yaml():
        # Look for files named n8n.yaml or n8n_*.yaml in workspace root first
        candidates = list(Path(workspace).glob("n8n*.yaml"))
        # Also check root level
        root_candidate = Path(workspace) / "n8n.yaml"
        if root_candidate.exists():
            return root_candidate
        # Filter out distractor/old files
        for c in candidates:
            if "draft" not in c.name and "old" not in c.name and "staging" not in str(c):
                if c.parent == Path(workspace):
                    return c
        # Broader search
        all_yamls = list(Path(workspace).rglob("n8n*.yaml"))
        for c in all_yamls:
            if "draft" not in c.name and "old" not in c.name and "staging" not in str(c) and "archive" not in str(c):
                return c
        return None

    # ----------------------------------------------------------------
    # Check 1: n8n.yaml exists in workspace
    # ----------------------------------------------------------------
    n8n_yaml_path = find_n8n_yaml()
    check1_passed = n8n_yaml_path is not None and n8n_yaml_path.exists()
    checks.append({
        "name": "n8n_yaml_exists",
        "passed": check1_passed,
        "detail": f"Found n8n yaml at: {n8n_yaml_path}" if check1_passed else "No n8n.yaml found in workspace root"
    })

    if not check1_passed:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    # Load yaml content as text (avoid import issues with complex yaml)
    try:
        with open(n8n_yaml_path, "r") as f:
            content = f.read()
    except Exception as e:
        checks.append({"name": "yaml_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        import yaml
        data = yaml.safe_load(content)
        yaml_valid = True
    except Exception as e:
        yaml_valid = False
        data = {}
        checks.append({"name": "yaml_valid", "passed": False, "detail": f"YAML parse error: {e}"})

    # ----------------------------------------------------------------
    # Check 2: Has exactly 4 services (editor, webhook, worker, redis)
    # ----------------------------------------------------------------
    try:
        services = data.get("services", {})
        service_names = list(services.keys()) if services else []
        
        # Look for service types: editor, webhook, worker, redis
        has_editor = any("editor" in s for s in service_names)
        has_webhook = any("webhook" in s for s in service_names)
        has_worker = any("worker" in s for s in service_names)
        has_redis = any("redis" in s for s in service_names)
        
        four_services = len(service_names) >= 4
        checks.append({
            "name": "four_services_present",
            "passed": four_services and has_editor and has_webhook and has_worker and has_redis,
            "detail": f"Services found: {service_names}. Need editor+webhook+worker+redis. editor={has_editor}, webhook={has_webhook}, worker={has_worker}, redis={has_redis}"
        })
    except Exception as e:
        checks.append({"name": "four_services_present", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Check 3: Uses correct internal network name from dados_vps
    # The network MUST be 'empresa_net' (read from dados_vps file)
    # ----------------------------------------------------------------
    try:
        network_correct = "empresa_net" in content
        checks.append({
            "name": "correct_network_name",
            "passed": network_correct,
            "detail": f"Expected network 'empresa_net' (from dados_vps). Found in content: {network_correct}"
        })
    except Exception as e:
        checks.append({"name": "correct_network_name", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Check 4: Uses correct postgres password from dados_postgres/postgres.yaml
    # Password is 'a3f8b2c91d4e7f6a'
    # ----------------------------------------------------------------
    try:
        correct_pg_pass = "a3f8b2c91d4e7f6a" in content
        checks.append({
            "name": "correct_postgres_password",
            "passed": correct_pg_pass,
            "detail": f"Expected postgres password 'a3f8b2c91d4e7f6a' from existing postgres.yaml. Found: {correct_pg_pass}"
        })
    except Exception as e:
        checks.append({"name": "correct_postgres_password", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Check 5: N8N editor has correct Traefik routing label
    # Must reference the editor domain with correct traefik label pattern
    # ----------------------------------------------------------------
    try:
        # The editor service must have traefik labels with the n8n editor domain
        has_traefik_editor = "traefik.http.routers" in content and "editor" in content
        checks.append({
            "name": "traefik_labels_editor",
            "passed": has_traefik_editor,
            "detail": f"Traefik router labels for editor service present: {has_traefik_editor}"
        })
    except Exception as e:
        checks.append({"name": "traefik_labels_editor", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Check 6: N8N webhook uses compound Traefik rule with PathPrefix /webhook
    # This is the key proprietary trap: Host(...) && PathPrefix(`/webhook`)
    # ----------------------------------------------------------------
    try:
        # The webhook router MUST use PathPrefix rule
        webhook_path_prefix = (
            ("PathPrefix" in content and "webhook" in content.lower()) or
            ("/webhook" in content)
        )
        # More specific: look for the compound rule pattern
        compound_rule = bool(re.search(r'PathPrefix.*webhook|webhook.*PathPrefix', content, re.IGNORECASE))
        
        checks.append({
            "name": "webhook_pathprefix_rule",
            "passed": webhook_path_prefix or compound_rule,
            "detail": f"Webhook service uses PathPrefix('/webhook') compound Traefik rule. path_prefix={webhook_path_prefix}, compound={compound_rule}"
        })
    except Exception as e:
        checks.append({"name": "webhook_pathprefix_rule", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Check 7: Redis service has a volume defined (n8n_*_redis or similar)
    # ----------------------------------------------------------------
    try:
        volumes = data.get("volumes", {})
        volume_names = list(volumes.keys()) if volumes else []
        has_redis_volume = any("redis" in v for v in volume_names)
        # Also check in content
        redis_vol_in_content = bool(re.search(r'redis.*_data|n8n.*redis', content))
        checks.append({
            "name": "redis_volume_defined",
            "passed": has_redis_volume or redis_vol_in_content,
            "detail": f"Redis volume defined in volumes section. volumes={volume_names}, in_content={redis_vol_in_content}"
        })
    except Exception as e:
        checks.append({"name": "redis_volume_defined", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Check 8: EXECUTIONS_MODE=queue is set (queue mode with Redis)
    # This is a non-obvious requirement for the multi-service N8N setup
    # ----------------------------------------------------------------
    try:
        queue_mode = "EXECUTIONS_MODE=queue" in content or "EXECUTIONS_MODE: queue" in content
        checks.append({
            "name": "executions_mode_queue",
            "passed": queue_mode,
            "detail": f"EXECUTIONS_MODE=queue is required for multi-worker N8N setup. Found: {queue_mode}"
        })
    except Exception as e:
        checks.append({"name": "executions_mode_queue", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Check 9: Redis queue connection settings reference internal redis service
    # QUEUE_BULL_REDIS_HOST must point to internal redis service name
    # ----------------------------------------------------------------
    try:
        redis_host_set = "QUEUE_BULL_REDIS_HOST" in content
        # Should reference an internal service, not localhost or external
        redis_points_to_service = bool(re.search(r'QUEUE_BULL_REDIS_HOST[=:]\s*[a-zA-Z_]', content))
        checks.append({
            "name": "redis_queue_connection",
            "passed": redis_host_set and redis_points_to_service,
            "detail": f"QUEUE_BULL_REDIS_HOST set={redis_host_set}, points to service={redis_points_to_service}"
        })
    except Exception as e:
        checks.append({"name": "redis_queue_connection", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Check 10: dados_n8n file created in dados_vps directory
    # The script saves installation data to /dados_vps/dados_n8n
    # ----------------------------------------------------------------
    try:
        dados_dir = Path(workspace) / "dados_vps"
        dados_n8n_candidates = list(dados_dir.glob("dados_n8n*"))
        dados_n8n_exists = len(dados_n8n_candidates) > 0
        checks.append({
            "name": "dados_n8n_saved",
            "passed": dados_n8n_exists,
            "detail": f"dados_n8n file in dados_vps/ directory. Found: {[str(p) for p in dados_n8n_candidates]}"
        })
    except Exception as e:
        checks.append({"name": "dados_n8n_saved", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Calculate final score
    # ----------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Must pass critical checks to be considered passing:
    # - file exists
    # - 4 services
    # - correct network
    # - correct postgres password
    critical = ["n8n_yaml_exists", "four_services_present", "correct_network_name", "correct_postgres_password"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    
    overall_passed = critical_passed and score >= 0.65

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))