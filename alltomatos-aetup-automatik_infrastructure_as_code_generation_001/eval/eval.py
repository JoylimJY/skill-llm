import sys
import json
import os
import re
from pathlib import Path

def find_yaml_file(workspace):
    """Find the generated n8n stack YAML file."""
    # Look for any yaml file that could be the n8n_prod stack
    candidates = []
    for p in Path(workspace).rglob("*.yaml"):
        # Skip distractor files we know about
        name = p.name.lower()
        if "n8n" in name and "old" not in name and "template" not in name:
            candidates.append(p)
    for p in Path(workspace).rglob("*.yml"):
        name = p.name.lower()
        if "n8n" in name and "old" not in name and "template" not in name:
            candidates.append(p)
    return candidates

def load_yaml_safe(path):
    """Load YAML safely, returning None on failure."""
    try:
        import yaml
        with open(path, "r") as f:
            content = f.read()
        return yaml.safe_load(content), content
    except Exception as e:
        return None, str(e)

def run_checks(workspace):
    checks = []
    
    # --- Check 1: File exists ---
    yaml_files = find_yaml_file(workspace)
    
    # Filter out distractor files
    distractor_names = {"n8n_old.yaml", "stack_template.yaml"}
    yaml_files = [p for p in yaml_files if p.name not in distractor_names]
    
    file_found = len(yaml_files) > 0
    chosen_file = yaml_files[0] if file_found else None
    
    checks.append({
        "name": "stack_yaml_file_created",
        "passed": file_found,
        "detail": f"Found N8N stack YAML at: {chosen_file}" if file_found else "No N8N stack YAML file found (excluding known distractor files)"
    })
    
    if not file_found:
        return checks, 0.0
    
    data, raw_content = load_yaml_safe(chosen_file)
    
    checks.append({
        "name": "yaml_is_valid",
        "passed": data is not None,
        "detail": f"YAML parsed successfully from {chosen_file}" if data is not None else f"YAML parse error: {raw_content}"
    })
    
    if data is None:
        return checks, 0.0
    
    services = data.get("services", {})
    
    # --- Check 2: Four required services ---
    # The installer creates: editor, webhook, worker, redis (all prefixed n8n_prod_)
    # Accept both with and without the suffix for flexibility, but check service COUNT
    service_names = list(services.keys()) if services else []
    
    has_editor = any("editor" in s for s in service_names)
    has_webhook = any("webhook" in s for s in service_names)
    has_worker = any("worker" in s for s in service_names)
    has_redis = any("redis" in s for s in service_names)
    
    four_services = has_editor and has_webhook and has_worker and has_redis
    checks.append({
        "name": "four_services_present",
        "passed": four_services,
        "detail": f"Services found: {service_names}. Need editor+webhook+worker+redis. editor={has_editor}, webhook={has_webhook}, worker={has_worker}, redis={has_redis}"
    })
    
    # --- Check 3: Database name uses n8n_queue pattern ---
    # The script uses: n8n_queue${1:+_$1} -> n8n_queue_prod
    db_name_correct = False
    db_name_found = ""
    try:
        for svc_name, svc_config in services.items():
            if "editor" in svc_name or "worker" in svc_name or "webhook" in svc_name:
                env = svc_config.get("environment", [])
                if isinstance(env, list):
                    for e in env:
                        if "DB_POSTGRESDB_DATABASE" in str(e):
                            db_name_found = str(e)
                            # Must contain "n8n_queue" pattern
                            if "n8n_queue" in str(e):
                                db_name_correct = True
                elif isinstance(env, dict):
                    val = env.get("DB_POSTGRESDB_DATABASE", "")
                    db_name_found = val
                    if "n8n_queue" in str(val):
                        db_name_correct = True
    except Exception as ex:
        db_name_found = f"Error: {ex}"
    
    checks.append({
        "name": "database_name_uses_n8n_queue_pattern",
        "passed": db_name_correct,
        "detail": f"DB name must contain 'n8n_queue' (script uses n8n_queue_<suffix>). Found: '{db_name_found}'"
    })
    
    # --- Check 4: EXECUTIONS_MODE=queue ---
    queue_mode_found = False
    try:
        for svc_name, svc_config in services.items():
            if "editor" in svc_name:
                env = svc_config.get("environment", [])
                env_str = json.dumps(env)
                if "EXECUTIONS_MODE" in env_str and "queue" in env_str.lower():
                    queue_mode_found = True
    except Exception:
        pass
    
    checks.append({
        "name": "executions_mode_queue",
        "passed": queue_mode_found,
        "detail": "Editor service must have EXECUTIONS_MODE=queue (required by installer script for queue-based execution)"
    })
    
    # --- Check 5: Webhook Traefik routing rule uses PathPrefix /webhook ---
    webhook_path_rule = False
    try:
        for svc_name, svc_config in services.items():
            if "webhook" in svc_name:
                deploy = svc_config.get("deploy", {})
                labels = deploy.get("labels", [])
                labels_str = json.dumps(labels)
                # Must have PathPrefix(`/webhook`) in the routing rule
                if "PathPrefix" in labels_str and "/webhook" in labels_str:
                    webhook_path_rule = True
    except Exception:
        pass
    
    checks.append({
        "name": "webhook_traefik_uses_pathprefix",
        "passed": webhook_path_rule,
        "detail": "Webhook service Traefik rule must include PathPrefix(`/webhook`) - this is the proprietary routing pattern from the installer"
    })
    
    # --- Check 6: Internal Redis service with correct naming ---
    # The installer creates its own redis for n8n named n8n_<suffix>_redis
    # And the queue config points to it: QUEUE_BULL_REDIS_HOST=n8n_prod_redis
    internal_redis_host_correct = False
    try:
        for svc_name, svc_config in services.items():
            if "editor" in svc_name or "worker" in svc_name or "webhook" in svc_name:
                env = svc_config.get("environment", [])
                env_str = json.dumps(env)
                # Check that QUEUE_BULL_REDIS_HOST points to an n8n-internal redis
                if "QUEUE_BULL_REDIS_HOST" in env_str:
                    # Should NOT be just "redis" (shared) but should reference the n8n-specific redis
                    # The script uses: n8n${1:+_$1}_redis
                    if "n8n" in env_str and "redis" in env_str:
                        # Find the actual value
                        match = re.search(r'QUEUE_BULL_REDIS_HOST[=:]([^\s,"\'\\]+)', env_str)
                        if match:
                            host_val = match.group(1).strip('"\'')
                            if "n8n" in host_val and "redis" in host_val:
                                internal_redis_host_correct = True
    except Exception as ex:
        pass
    
    checks.append({
        "name": "queue_redis_host_points_to_internal_n8n_redis",
        "passed": internal_redis_host_correct,
        "detail": "QUEUE_BULL_REDIS_HOST must point to the n8n-specific redis service (e.g., n8n_prod_redis), not a shared 'redis' service"
    })
    
    # --- Check 7: Volume for redis is external with n8n naming ---
    redis_volume_correct = False
    try:
        volumes = data.get("volumes", {})
        for vol_name in volumes.keys():
            if "n8n" in str(vol_name) and "redis" in str(vol_name):
                vol_def = volumes[vol_name]
                if isinstance(vol_def, dict) and vol_def.get("external") == True:
                    redis_volume_correct = True
    except Exception:
        pass
    
    checks.append({
        "name": "n8n_redis_volume_is_external",
        "passed": redis_volume_correct,
        "detail": "The n8n redis volume must be defined as 'external: true' with an n8n-specific name (e.g., n8n_prod_redis)"
    })
    
    # --- Check 8: Network matches dados_vps ---
    # dados_vps says internal network is "GrowthNet"
    network_correct = False
    try:
        networks = data.get("networks", {})
        if "GrowthNet" in networks:
            net_def = networks["GrowthNet"]
            if isinstance(net_def, dict) and net_def.get("external") == True:
                network_correct = True
        # Also check services reference GrowthNet
        for svc_name, svc_config in services.items():
            svc_nets = svc_config.get("networks", [])
            if "GrowthNet" in str(svc_nets):
                network_correct = True
                break
    except Exception:
        pass
    
    checks.append({
        "name": "network_matches_dados_vps",
        "passed": network_correct,
        "detail": "Network must be 'GrowthNet' as defined in dados_vps/dados_vps (Rede interna: GrowthNet)"
    })
    
    # --- Check 9: Image is n8nio/n8n:latest ---
    correct_image = False
    try:
        for svc_name, svc_config in services.items():
            if "editor" in svc_name:
                image = svc_config.get("image", "")
                if "n8nio/n8n" in image:
                    correct_image = True
    except Exception:
        pass
    
    checks.append({
        "name": "uses_n8nio_n8n_image",
        "passed": correct_image,
        "detail": f"Editor service must use n8nio/n8n image. Services: {list(services.keys())}"
    })
    
    # --- Check 10: Version 3.7 ---
    version_ok = str(data.get("version", "")).strip('"') in ["3.7", "3", "3.8", "3.9"]
    checks.append({
        "name": "compose_version_correct",
        "passed": version_ok,
        "detail": f"Compose version should be 3.7 (or compatible). Found: {data.get('version', 'missing')}"
    })
    
    # Calculate score
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / len(checks)
    
    return checks, score

def main():
    if len(sys.argv) < 2:
        workspace = "/workspace"
    else:
        workspace = sys.argv[1]
    
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_runtime_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        return
    
    # Pass threshold: must pass at least 7/10 checks including the critical ones
    critical_checks = [
        "stack_yaml_file_created",
        "yaml_is_valid",
        "four_services_present",
        "database_name_uses_n8n_queue_pattern",
        "webhook_traefik_uses_pathprefix",
    ]
    
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.7
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()