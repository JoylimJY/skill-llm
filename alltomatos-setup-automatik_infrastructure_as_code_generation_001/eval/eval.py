import sys
import os
import json
import re
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_all = True

    # The expected suffix is "cliente1" (as specified in the prompt)
    # Stack name would be "n8n_cliente1"
    # The agent should place the file at /workspace/root/n8n_cliente1.yaml

    # --- Find the generated YAML file ---
    target_filename = "n8n_cliente1.yaml"
    candidate_paths = list(Path(workspace).rglob(target_filename))

    file_found = len(candidate_paths) > 0
    checks.append({
        "name": "file_exists",
        "passed": file_found,
        "detail": f"Found {target_filename} at: {candidate_paths[0]}" if file_found else f"{target_filename} not found anywhere in workspace"
    })

    if not file_found:
        passed_all = False
        return passed_all, checks

    yaml_path = candidate_paths[0]

    try:
        content = yaml_path.read_text()
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return False, checks

    # Try to parse as YAML
    try:
        import yaml
        data = yaml.safe_load(content)
    except Exception as e:
        checks.append({"name": "valid_yaml", "passed": False, "detail": f"YAML parse error: {e}"})
        passed_all = False
        return passed_all, checks

    checks.append({"name": "valid_yaml", "passed": True, "detail": "File is valid YAML"})

    # --- CHECK 1: Correct service names ---
    # Must have: n8n_cliente1_editor, n8n_cliente1_webhook, n8n_cliente1_worker, n8n_cliente1_redis
    services = {}
    if isinstance(data, dict) and "services" in data:
        services = data.get("services", {}) or {}

    expected_services = ["n8n_cliente1_editor", "n8n_cliente1_webhook", "n8n_cliente1_worker", "n8n_cliente1_redis"]
    found_services = list(services.keys()) if services else []
    
    editor_found = "n8n_cliente1_editor" in found_services
    webhook_found = "n8n_cliente1_webhook" in found_services
    worker_found = "n8n_cliente1_worker" in found_services
    redis_found = "n8n_cliente1_redis" in found_services

    service_check = editor_found and webhook_found and worker_found and redis_found
    checks.append({
        "name": "correct_service_names",
        "passed": service_check,
        "detail": f"Found services: {found_services}. Expected: {expected_services}"
    })
    if not service_check:
        passed_all = False

    # --- CHECK 2: Database name is n8n_queue_cliente1 (not n8n_cliente1) ---
    # The SetupOrion.sh script uses "n8n_queue${1:+_$1}" as the database name
    db_name_correct = False
    db_name_found = None
    try:
        editor_svc = services.get("n8n_cliente1_editor", {}) or {}
        env_list = editor_svc.get("environment", []) or []
        for env_item in env_list:
            if isinstance(env_item, str) and "DB_POSTGRESDB_DATABASE" in env_item:
                db_name_found = env_item.split("=", 1)[1].strip() if "=" in env_item else None
                if db_name_found == "n8n_queue_cliente1":
                    db_name_correct = True
                break
    except Exception as e:
        db_name_found = f"error: {e}"

    checks.append({
        "name": "database_name_is_n8n_queue_suffix",
        "passed": db_name_correct,
        "detail": f"DB name found: '{db_name_found}', expected: 'n8n_queue_cliente1'. The SetupOrion script uses n8n_queue${{1:+_$1}} pattern."
    })
    if not db_name_correct:
        passed_all = False

    # --- CHECK 3: Postgres password extracted from postgres.yaml ---
    # Must use POSTGRES_PASSWORD=a3f8c12b9e4d7f2a (from existing postgres.yaml)
    expected_pg_password = "a3f8c12b9e4d7f2a"
    pg_password_correct = False
    pg_password_found = None
    try:
        for svc_name in ["n8n_cliente1_editor", "n8n_cliente1_webhook", "n8n_cliente1_worker"]:
            svc = services.get(svc_name, {}) or {}
            env_list = svc.get("environment", []) or []
            for env_item in env_list:
                if isinstance(env_item, str) and "DB_POSTGRESDB_PASSWORD" in env_item:
                    pg_password_found = env_item.split("=", 1)[1].strip() if "=" in env_item else None
                    if pg_password_found == expected_pg_password:
                        pg_password_correct = True
                    break
            if pg_password_found:
                break
    except Exception as e:
        pg_password_found = f"error: {e}"

    checks.append({
        "name": "postgres_password_from_existing_config",
        "passed": pg_password_correct,
        "detail": f"PG password found: '{pg_password_found}', expected: '{expected_pg_password}' (read from /root/postgres.yaml)"
    })
    if not pg_password_correct:
        passed_all = False

    # --- CHECK 4: Redis host in editor env uses n8n_cliente1_redis (not generic 'redis') ---
    redis_host_correct = False
    redis_host_found = None
    try:
        editor_svc = services.get("n8n_cliente1_editor", {}) or {}
        env_list = editor_svc.get("environment", []) or []
        for env_item in env_list:
            if isinstance(env_item, str) and "QUEUE_BULL_REDIS_HOST" in env_item:
                redis_host_found = env_item.split("=", 1)[1].strip() if "=" in env_item else None
                if redis_host_found == "n8n_cliente1_redis":
                    redis_host_correct = True
                break
    except Exception as e:
        redis_host_found = f"error: {e}"

    checks.append({
        "name": "redis_host_uses_suffixed_service_name",
        "passed": redis_host_correct,
        "detail": f"QUEUE_BULL_REDIS_HOST found: '{redis_host_found}', expected: 'n8n_cliente1_redis'. Must reference the stack-specific redis service."
    })
    if not redis_host_correct:
        passed_all = False

    # --- CHECK 5: Network name is AutomatikNet (read from dados_vps) ---
    network_correct = False
    try:
        networks = data.get("networks", {}) or {}
        # Check if AutomatikNet is defined in networks section
        if "AutomatikNet" in networks:
            net_config = networks["AutomatikNet"] or {}
            if net_config.get("external") == True and net_config.get("name") == "AutomatikNet":
                network_correct = True
        # Also acceptable: referenced in service network lists
        if not network_correct:
            # Check raw content for AutomatikNet
            if "AutomatikNet" in content:
                network_correct = True
    except Exception as e:
        pass

    checks.append({
        "name": "network_name_from_dados_vps",
        "passed": network_correct,
        "detail": f"Network 'AutomatikNet' correctly referenced. Found in YAML: {'yes' if 'AutomatikNet' in content else 'no'}. Networks section: {list((data.get('networks') or {}).keys())}"
    })
    if not network_correct:
        passed_all = False

    # --- CHECK 6: Volume for redis is named n8n_cliente1_redis with external:true ---
    redis_volume_correct = False
    try:
        volumes = data.get("volumes", {}) or {}
        if "n8n_cliente1_redis" in volumes:
            vol_config = volumes["n8n_cliente1_redis"] or {}
            if vol_config.get("external") == True:
                redis_volume_correct = True
    except Exception as e:
        pass

    checks.append({
        "name": "redis_volume_correctly_named_and_external",
        "passed": redis_volume_correct,
        "detail": f"Volume 'n8n_cliente1_redis' with external:true. Volumes found: {list((data.get('volumes') or {}).keys())}"
    })
    if not redis_volume_correct:
        passed_all = False

    # --- CHECK 7: Traefik labels on editor use n8n_cliente1_editor router/service names ---
    traefik_labels_correct = False
    try:
        editor_svc = services.get("n8n_cliente1_editor", {}) or {}
        deploy = editor_svc.get("deploy", {}) or {}
        labels = deploy.get("labels", []) or []
        label_str = " ".join(labels) if isinstance(labels, list) else str(labels)
        # Check for the correct router name pattern
        if "n8n_cliente1_editor" in label_str and "traefik.enable" in label_str:
            traefik_labels_correct = True
    except Exception as e:
        pass

    checks.append({
        "name": "traefik_labels_use_suffixed_names",
        "passed": traefik_labels_correct,
        "detail": "Traefik labels on n8n_cliente1_editor must reference 'n8n_cliente1_editor' as router/service name."
    })
    if not traefik_labels_correct:
        passed_all = False

    # --- CHECK 8: Editor image is n8nio/n8n:latest ---
    image_correct = False
    try:
        editor_svc = services.get("n8n_cliente1_editor", {}) or {}
        image = editor_svc.get("image", "")
        if "n8nio/n8n" in str(image):
            image_correct = True
    except Exception as e:
        pass

    checks.append({
        "name": "editor_uses_n8n_image",
        "passed": image_correct,
        "detail": f"Editor image: '{services.get('n8n_cliente1_editor', {}).get('image', 'not found')}', must contain 'n8nio/n8n'"
    })
    if not image_correct:
        passed_all = False

    score = sum(1 for c in checks if c["passed"]) / len(checks)
    return passed_all, checks, score


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        passed, checks, score = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        sys.exit(0)

    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))