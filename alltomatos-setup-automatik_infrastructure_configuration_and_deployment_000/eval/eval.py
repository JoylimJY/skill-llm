import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace):
    checks = []
    
    # ----------------------------------------------------------------
    # CHECK 1: dados_vps file exists at the correct proprietary path
    # ----------------------------------------------------------------
    dados_vps_path = Path(workspace) / "dados_vps" / "dados_vps"
    
    dados_content = ""
    dados_exists = dados_vps_path.exists()
    
    checks.append({
        "name": "dados_vps file exists at correct path (dados_vps/dados_vps)",
        "passed": dados_exists,
        "detail": f"Expected file at {dados_vps_path}. {'Found.' if dados_exists else 'Not found. The Orion Design system requires this exact path.'}"
    })
    
    if dados_exists:
        try:
            dados_content = dados_vps_path.read_text()
        except Exception as e:
            dados_content = ""
            checks.append({
                "name": "dados_vps file readable",
                "passed": False,
                "detail": f"Could not read file: {e}"
            })
    
    # ----------------------------------------------------------------
    # CHECK 2: dados_vps has correct proprietary key format
    # The script uses: grep "Nome do Servidor:" "$dados_vps" | awk -F': ' '{print $2}'
    # ----------------------------------------------------------------
    server_name_check = False
    server_name_detail = "dados_vps file not found or empty"
    
    if dados_content:
        # Must use format "Nome do Servidor: VALUE" (colon-space separator)
        match = re.search(r'Nome do Servidor:\s*(.+)', dados_content)
        if match:
            found_name = match.group(1).strip()
            server_name_check = found_name == "ProdServerAlpha"
            server_name_detail = f"Found 'Nome do Servidor: {found_name}'. Expected 'ProdServerAlpha'."
        else:
            server_name_detail = "Key 'Nome do Servidor:' not found in dados_vps. Must use exact Orion format with colon-space separator."
    
    checks.append({
        "name": "dados_vps contains 'Nome do Servidor' in correct Orion format",
        "passed": server_name_check,
        "detail": server_name_detail
    })
    
    # ----------------------------------------------------------------
    # CHECK 3: dados_vps has 'Rede interna' key
    # ----------------------------------------------------------------
    network_check = False
    network_detail = "dados_vps file not found or empty"
    
    if dados_content:
        match = re.search(r'Rede interna:\s*(.+)', dados_content)
        if match:
            found_network = match.group(1).strip()
            network_check = found_network == "AlphaNet"
            network_detail = f"Found 'Rede interna: {found_network}'. Expected 'AlphaNet'."
        else:
            network_detail = "Key 'Rede interna:' not found. Must match Orion's exact key name."
    
    checks.append({
        "name": "dados_vps contains 'Rede interna' with correct value",
        "passed": network_check,
        "detail": network_detail
    })
    
    # ----------------------------------------------------------------
    # CHECK 4: dados_portainer file exists at correct proprietary path
    # ----------------------------------------------------------------
    dados_portainer_path = Path(workspace) / "dados_vps" / "dados_portainer"
    portainer_content = ""
    portainer_exists = dados_portainer_path.exists()
    
    checks.append({
        "name": "dados_portainer file exists at correct path (dados_vps/dados_portainer)",
        "passed": portainer_exists,
        "detail": f"Expected file at {dados_portainer_path}. {'Found.' if portainer_exists else 'Not found. The Orion stack_editavel function reads credentials from this exact path.'}"
    })
    
    if portainer_exists:
        try:
            portainer_content = dados_portainer_path.read_text()
        except Exception as e:
            portainer_content = ""
    
    # ----------------------------------------------------------------
    # CHECK 5: dados_portainer has 'Dominio do portainer' key (not 'URL' or other variant)
    # ----------------------------------------------------------------
    portainer_domain_check = False
    portainer_domain_detail = "dados_portainer not found or empty"
    
    if portainer_content:
        match = re.search(r'Dominio do portainer:\s*(.+)', portainer_content)
        if match:
            found_domain = match.group(1).strip()
            portainer_domain_check = "portainer.alphacompany.io" in found_domain
            portainer_domain_detail = f"Found 'Dominio do portainer: {found_domain}'."
        else:
            portainer_domain_detail = "Key 'Dominio do portainer:' not found. Must use Orion's exact key name."
    
    checks.append({
        "name": "dados_portainer contains 'Dominio do portainer' key",
        "passed": portainer_domain_check,
        "detail": portainer_domain_detail
    })
    
    # ----------------------------------------------------------------
    # CHECK 6: dados_portainer has Usuario, Senha, Token keys
    # ----------------------------------------------------------------
    portainer_fields_check = False
    portainer_fields_detail = "dados_portainer not found or empty"
    
    if portainer_content:
        has_usuario = bool(re.search(r'Usuario:\s*alpha_admin', portainer_content))
        has_senha = bool(re.search(r'Senha:\s*SecurePass2024@', portainer_content))
        has_token = bool(re.search(r'Token:\s*.+', portainer_content))
        
        portainer_fields_check = has_usuario and has_senha and has_token
        portainer_fields_detail = (
            f"Usuario found: {has_usuario}, Senha found: {has_senha}, Token found: {has_token}. "
            f"The Orion script uses grep pattern 'Usuario: ', 'Senha: ', 'Token: ' to parse these."
        )
    
    checks.append({
        "name": "dados_portainer has correct Usuario, Senha, and Token fields",
        "passed": portainer_fields_check,
        "detail": portainer_fields_detail
    })
    
    # ----------------------------------------------------------------
    # CHECK 7: Uptime Kuma YAML stack file exists
    # ----------------------------------------------------------------
    yaml_files = list(Path(workspace).rglob("uptimekuma*.yaml")) + list(Path(workspace).rglob("uptimekuma*.yml"))
    yaml_exists = len(yaml_files) > 0
    
    yaml_content = ""
    yaml_path = None
    if yaml_files:
        yaml_path = yaml_files[0]
        try:
            yaml_content = yaml_path.read_text()
        except Exception as e:
            yaml_content = ""
    
    checks.append({
        "name": "Uptime Kuma stack YAML file exists",
        "passed": yaml_exists,
        "detail": f"{'Found at: ' + str(yaml_path) if yaml_exists else 'No uptimekuma*.yaml file found in workspace.'}"
    })
    
    # ----------------------------------------------------------------
    # CHECK 8: YAML uses 'louislam/uptime-kuma:latest' image
    # ----------------------------------------------------------------
    correct_image_check = False
    correct_image_detail = "YAML not found"
    
    if yaml_content:
        correct_image_check = "louislam/uptime-kuma" in yaml_content
        correct_image_detail = (
            f"'louislam/uptime-kuma' image {'found' if correct_image_check else 'NOT found'} in YAML. "
            "Orion Design uses this specific image for Uptime Kuma deployments."
        )
    
    checks.append({
        "name": "YAML uses correct 'louislam/uptime-kuma' image",
        "passed": correct_image_check,
        "detail": correct_image_detail
    })
    
    # ----------------------------------------------------------------
    # CHECK 9: YAML has external volume with correct Orion naming pattern
    # The pattern is: name: uptimekuma_{suffix} or uptimekuma (external: true)
    # ----------------------------------------------------------------
    volume_check = False
    volume_detail = "YAML not found"
    
    if yaml_content:
        # Orion pattern: external: true with name: uptimekuma...
        has_external = "external: true" in yaml_content
        has_volume_name = bool(re.search(r'name:\s*uptimekuma', yaml_content))
        volume_check = has_external and has_volume_name
        volume_detail = (
            f"external: true present: {has_external}, "
            f"volume name matches 'uptimekuma*' pattern: {has_volume_name}. "
            "Orion stacks require volumes declared as external with specific naming."
        )
    
    checks.append({
        "name": "YAML has correctly named external volume",
        "passed": volume_check,
        "detail": volume_detail
    })
    
    # ----------------------------------------------------------------
    # CHECK 10: YAML has Traefik labels with correct Orion pattern
    # Orion uses: letsencryptresolver, websecure entrypoint, service labels
    # ----------------------------------------------------------------
    traefik_check = False
    traefik_detail = "YAML not found"
    
    if yaml_content:
        has_traefik_enable = "traefik.enable=true" in yaml_content or "traefik.enable=1" in yaml_content
        has_letsencrypt = "letsencryptresolver" in yaml_content
        has_websecure = "websecure" in yaml_content
        has_domain = "uptime.alphacompany.io" in yaml_content
        
        traefik_check = has_traefik_enable and has_letsencrypt and has_websecure and has_domain
        traefik_detail = (
            f"traefik.enable: {has_traefik_enable}, "
            f"letsencryptresolver: {has_letsencrypt}, "
            f"websecure entrypoint: {has_websecure}, "
            f"correct domain: {has_domain}. "
            "Orion stacks use letsencryptresolver as the cert resolver name."
        )
    
    checks.append({
        "name": "YAML has correct Traefik labels (letsencryptresolver, websecure, correct domain)",
        "passed": traefik_check,
        "detail": traefik_detail
    })
    
    # ----------------------------------------------------------------
    # CHECK 11: YAML references the correct internal network (AlphaNet)
    # ----------------------------------------------------------------
    network_yaml_check = False
    network_yaml_detail = "YAML not found"
    
    if yaml_content:
        network_yaml_check = "AlphaNet" in yaml_content
        network_yaml_detail = (
            f"Network 'AlphaNet' {'found' if network_yaml_check else 'NOT found'} in YAML. "
            "The stack must reference the internal network name from dados_vps."
        )
    
    checks.append({
        "name": "YAML references correct internal network name 'AlphaNet'",
        "passed": network_yaml_check,
        "detail": network_yaml_detail
    })
    
    # ----------------------------------------------------------------
    # CHECK 12: YAML has Orion Design structural comment markers
    # ----------------------------------------------------------------
    orion_comment_check = False
    orion_comment_detail = "YAML not found"
    
    if yaml_content:
        orion_comment_check = "ORION" in yaml_content
        orion_comment_detail = (
            f"Orion Design section markers {'found' if orion_comment_check else 'NOT found'} in YAML. "
            "Orion stacks use '## --------------------------- ORION --------------------------- ##' as section delimiters."
        )
    
    checks.append({
        "name": "YAML contains Orion Design structural markers",
        "passed": orion_comment_check,
        "detail": orion_comment_detail
    })
    
    # ----------------------------------------------------------------
    # Calculate final score
    # ----------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    overall_passed = score >= 0.8  # Must pass at least 80% of checks
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))