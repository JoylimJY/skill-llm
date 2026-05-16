#!/bin/bash
set -e

# Make deploy script executable (distractor)
chmod +x /workspace/scripts/deploy.sh

# Create permission-check module stubs so imports don't fail
mkdir -p /workspace/nova-permission-system/permission-check
touch /workspace/nova-permission-system/permission-check/__init__.py

cat > /workspace/nova-permission-system/permission-check/main.py << 'PYEOF'
"""
Nova Permission System - Permission Check Main Module
Authenticates users based on their platform identity and required permission level.
"""
import json
import os
from pathlib import Path


def authenticate(request: dict) -> dict:
    """
    Authenticate a user request.
    
    Args:
        request: dict with keys:
            - open_id: str, the platform user identifier
            - platform: str, the platform name (e.g., "feishu", "wechat")
            - permission: str, required permission ("read", "write", "admin", "execute")
    
    Returns:
        dict with keys:
            - allowed: bool
            - reason: str
            - role: str (if found)
    """
    data_dir = Path(os.environ.get("NOVA_DATA_DIR", "/workspace/data"))
    
    try:
        with open(data_dir / "permissions.json", "r", encoding="utf-8") as f:
            perms_config = json.load(f)
    except FileNotFoundError:
        return {"allowed": False, "reason": "permissions.json not found", "role": "unknown"}
    
    try:
        with open(data_dir / "accounts.json", "r", encoding="utf-8") as f:
            accounts = json.load(f)
    except FileNotFoundError:
        return {"allowed": False, "reason": "accounts.json not found", "role": "unknown"}
    
    try:
        with open(data_dir / "users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except FileNotFoundError:
        return {"allowed": False, "reason": "users.json not found", "role": "unknown"}
    
    open_id = request.get("open_id")
    platform = request.get("platform")
    permission = request.get("permission")
    
    # Test mode check
    test_mode = perms_config.get("test_mode", False)
    whitelist = perms_config.get("whitelist", [])
    
    if test_mode and open_id in whitelist:
        return {"allowed": True, "reason": "test_mode whitelist", "role": "whitelisted"}
    
    # Find account
    user_id = None
    if isinstance(accounts, list):
        for account in accounts:
            if account.get("open_id") == open_id and account.get("platform") == platform:
                user_id = account.get("user_id")
                break
    
    if not user_id:
        return {"allowed": False, "reason": "account not found", "role": "stranger"}
    
    # Find user role
    role = None
    for user in users:
        if user.get("user_id") == user_id:
            role = user.get("role")
            break
    
    if not role:
        return {"allowed": False, "reason": "user not found", "role": "unknown"}
    
    # Check permission
    roles_config = perms_config.get("roles", {})
    role_perms = roles_config.get(role, {})
    
    allowed = role_perms.get(permission, False)
    
    return {
        "allowed": allowed,
        "reason": f"role={role}, permission={permission}, allowed={allowed}",
        "role": role
    }
PYEOF

cat > /workspace/nova-permission-system/permission-check/audit.py << 'PYEOF'
"""Audit logging for Nova Permission System."""
import json
import datetime
from pathlib import Path
import os


def log_action(action: str, user_id: str, result: dict, data_dir: str = None):
    if data_dir is None:
        data_dir = os.environ.get("NOVA_DATA_DIR", "/workspace/data")
    log_path = Path(data_dir) / "audit.log"
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "action": action,
        "user_id": user_id,
        "result": result
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
PYEOF

cat > /workspace/nova-permission-system/permission-check/middleware.py << 'PYEOF'
"""Permission middleware for Nova Permission System."""
from .main import authenticate


class PermissionMiddleware:
    def __init__(self, data_dir):
        import os
        os.environ["NOVA_DATA_DIR"] = str(data_dir)
        self.data_dir = data_dir

    def check(self, open_id: str, platform: str, permission: str) -> dict:
        return authenticate({
            "open_id": open_id,
            "platform": platform,
            "permission": permission
        })
PYEOF

mkdir -p /workspace/nova-permission-system/permission-gate
touch /workspace/nova-permission-system/permission-gate/__init__.py

mkdir -p /workspace/nova-permission-system/identity-management
touch /workspace/nova-permission-system/identity-management/__init__.py

# Make sure data dir exists
mkdir -p /workspace/data

echo "Setup complete."