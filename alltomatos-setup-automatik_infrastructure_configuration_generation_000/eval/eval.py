import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Find the generated YAML file
    yaml_file = None
    
    # Look for n8n_stack.yaml specifically
    candidates = list(Path(workspace_dir).rglob("n8n_stack.yaml"))
    if not candidates:
        # Also accept n8n_prod.yaml as that's a valid interpretation
        candidates = list(Path(workspace_dir).rglob("n8n_prod.yaml"))
    if not candidates:
        candidates = list(Path(workspace_dir).rglob("n8n_prod*.yaml"))
    if not candidates:
        # Broader search for any n8n yaml that isn't the broken test one
        all_n8n = [f for f in Path(workspace_dir).rglob("*.yaml") 
                   if 'n8n' in f.name.lower() 
                   and 'broken' not in f.name.lower()
                   and 'test' not in str(f).lower()
                   and f.name not in ['n8n_test_broken.yaml']]
        # Filter out distractor files
        candidates = [f for f in all_n8n if 'staging' not in str(f) and 'testing' not in str(f)]
        # Prefer files named n8n_stack or similar in production or root
        prod_candidates = [f for f in candidates if 'production' in str(f) or f.parent == Path(workspace_dir)]
        if prod_candidates:
            candidates = prod_candidates

    if not candidates:
        checks.append({
            "name": "file_found",
            "passed": False,
            "detail": "No n8n stack YAML file found. Expected n8n_stack.yaml or similar in the workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    yaml_file = candidates[0]
    checks.append({
        "name": "file_found",
        "passed": True,
        "detail": f"Found stack YAML at: {yaml_file}"
    })
    
    # Read the file content
    try:
        content = yaml_file.read_text()
    except Exception as e:
        checks.append({
            "name": "file_readable",
            "passed": False,
            "detail": f"Could not read file: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({
        "name": "file_readable",
        "passed": True,
        "detail": "File is readable"
    })
    
    # Parse YAML
    try:
        import yaml
        parsed = yaml.safe_load(content)
    except Exception as e:
        checks.append({
            "name": "valid_yaml",
            "passed": False,
            "detail": f"Invalid YAML syntax: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({
        "name": "valid_yaml",
        "passed": True,
        "detail": "File parses as valid YAML"
    })
    
    services = {}
    try:
        services = parsed.get("services", {})
    except Exception:
        services = {}
    
    # CHECK 1: Must have exactly 4 services: editor, webhook, worker, redis
    # The suffix should be 'prod' based on deployment_params.json
    service_names = list(services.keys())
    
    has_editor = any('editor' in s for s in service_names)
    has_webhook = any('webhook' in s for s in service_names)
    has_worker = any('worker' in s for s in service_names)
    has_redis = any('redis' in s for s in service_names)
    
    four_services = has_editor and has_webhook and has_worker and has_redis
    checks.append({
        "name": "four_services_present",
        "passed": four_services,
        "detail": f"Services found: {service_names}. Need editor, webhook, worker, redis services."
    })
    
    # CHECK 2: Editor service must have correct domain
    editor_service = None
    for name, svc in services.items():
        if 'editor' in name:
            editor_service = svc
            break
    
    editor_domain_ok = False
    if editor_service:
        deploy = editor_service.get("deploy", {})
        labels = deploy.get("labels", [])
        labels_str = str(labels)
        if "n8n.globeshop.io" in labels_str:
            editor_domain_ok = True
    
    checks.append({
        "name": "editor_domain_correct",
        "passed": editor_domain_ok,
        "detail": f"Editor service Traefik labels should reference 'n8n.globeshop.io'. Found: {'yes' if editor_domain_ok else 'no'}"
    })
    
    # CHECK 3: Webhook service must use PathPrefix rule format
    webhook_service = None
    for name, svc in services.items():
        if 'webhook' in name:
            webhook_service = svc
            break
    
    webhook_pathprefix_ok = False
    if webhook_service:
        deploy = webhook_service.get("deploy", {})
        labels = deploy.get("labels", [])
        labels_str = str(labels)
        # The webhook rule must contain PathPrefix(`/webhook`) - this is the proprietary trap
        if "PathPrefix" in labels_str and "/webhook" in labels_str:
            webhook_pathprefix_ok = True
    
    checks.append({
        "name": "webhook_pathprefix_rule",
        "passed": webhook_pathprefix_ok,
        "detail": "Webhook service Traefik rule must use PathPrefix(`/webhook`) pattern (proprietary constraint from SetupOrion.sh)"
    })
    
    # CHECK 4: Webhook domain is webhook.globeshop.io
    webhook_domain_ok = False
    if webhook_service:
        deploy = webhook_service.get("deploy", {})
        labels = deploy.get("labels", [])
        labels_str = str(labels)
        if "webhook.globeshop.io" in labels_str:
            webhook_domain_ok = True
    
    checks.append({
        "name": "webhook_domain_correct",
        "passed": webhook_domain_ok,
        "detail": "Webhook service labels should reference 'webhook.globeshop.io'"
    })
    
    # CHECK 5: EXECUTIONS_MODE=queue in all compute services (not redis)
    queue_mode_ok = True
    queue_mode_detail = []
    for name, svc in services.items():
        if 'redis' in name:
            continue
        env = svc.get("environment", [])
        env_str = str(env)
        if "EXECUTIONS_MODE" in env_str:
            if "queue" not in env_str:
                queue_mode_ok = False
                queue_mode_detail.append(f"{name}: EXECUTIONS_MODE not set to queue")
        else:
            queue_mode_ok = False
            queue_mode_detail.append(f"{name}: EXECUTIONS_MODE missing")
    
    checks.append({
        "name": "executions_mode_queue",
        "passed": queue_mode_ok,
        "detail": f"All compute services must have EXECUTIONS_MODE=queue. Issues: {queue_mode_detail if queue_mode_detail else 'none'}"
    })
    
    # CHECK 6: Redis service references internal redis, not external
    # QUEUE_BULL_REDIS_HOST must point to n8n_<suffix>_redis (internal service)
    redis_host_ok = False
    for name, svc in services.items():
        if 'editor' in name or 'webhook' in name or 'worker' in name:
            env = svc.get("environment", [])
            env_str = str(env)
            if "QUEUE_BULL_REDIS_HOST" in env_str:
                # Must reference the internal redis service, not an external redis
                # Pattern: n8n_<something>_redis
                if re.search(r'n8n[_a-z]*_redis', env_str):
                    redis_host_ok = True
                    break
    
    checks.append({
        "name": "internal_redis_host",
        "passed": redis_host_ok,
        "detail": "QUEUE_BULL_REDIS_HOST must reference the stack's own internal redis service (e.g., n8n_prod_redis), not an external redis"
    })
    
    # CHECK 7: Postgres password from deployment_params must be used
    postgres_password = "P0stgr3s_Gl0be_S3cur3"
    postgres_password_ok = postgres_password in content
    checks.append({
        "name": "postgres_password_used",
        "passed": postgres_password_ok,
        "detail": f"The postgres password from deployment_params.json must appear in the YAML"
    })
    
    # CHECK 8: Internal network is GlobeNet
    network_ok = "GlobeNet" in content
    checks.append({
        "name": "internal_network_globenet",
        "passed": network_ok,
        "detail": "The internal Docker network 'GlobeNet' (from deployment_params.json) must be referenced in the YAML"
    })
    
    # CHECK 9: Database name follows n8n_queue_<suffix> pattern
    db_name_ok = False
    db_name_pattern = re.search(r'n8n_queue[_a-z]*', content)
    if db_name_pattern:
        db_name_ok = True
    checks.append({
        "name": "database_name_pattern",
        "passed": db_name_ok,
        "detail": "Database name must follow n8n_queue_<suffix> pattern (e.g., n8n_queue_prod) as defined in SetupOrion.sh"
    })
    
    # CHECK 10: N8N_ENCRYPTION_KEY is present and appears to be a hex value (32+ chars)
    encryption_ok = False
    enc_match = re.search(r'N8N_ENCRYPTION_KEY[=:\s]+([a-fA-F0-9]{16,})', content)
    if enc_match:
        encryption_ok = True
    checks.append({
        "name": "encryption_key_hex",
        "passed": encryption_ok,
        "detail": "N8N_ENCRYPTION_KEY must be present and be a hex string (openssl rand -hex 16 pattern from SetupOrion.sh)"
    })
    
    # CHECK 11: SMTP configuration uses deployment_params values
    smtp_ok = "smtp.mailgun.org" in content and "ops@globeshop.io" in content
    checks.append({
        "name": "smtp_configuration",
        "passed": smtp_ok,
        "detail": "SMTP host (smtp.mailgun.org) and email (ops@globeshop.io) from deployment_params.json must appear in YAML"
    })
    
    # CHECK 12: Volume definition follows external named volume pattern
    volumes_section = parsed.get("volumes", {})
    volume_external_ok = False
    if volumes_section:
        for vol_name, vol_config in volumes_section.items():
            if isinstance(vol_config, dict) and vol_config.get("external") == True:
                volume_external_ok = True
                break
    checks.append({
        "name": "external_named_volumes",
        "passed": volume_external_ok,
        "detail": "Volumes must use 'external: true' pattern as defined in SetupOrion.sh"
    })
    
    # Calculate score and overall pass
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    # Must pass core structural checks to pass overall
    core_checks = [
        "file_found", "valid_yaml", "four_services_present",
        "webhook_pathprefix_rule", "executions_mode_queue",
        "internal_redis_host"
    ]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)
    
    overall_passed = core_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))