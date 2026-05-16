import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── 1. Create a realistic, deeply nested distractor structure ─────────────────

distractor_dirs = [
    "src/core/handlers",
    "src/core/validators",
    "src/api/v1/routes",
    "src/api/v2/routes",
    "src/utils/crypto",
    "src/utils/logging",
    "tests/unit/core",
    "tests/integration",
    "docs/internal",
    "scripts/migration",
    ".cache/tmp",
    "config_backup",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "src/core/handlers/request_handler.py": """\
# Request handler stub
class RequestHandler:
    def handle(self, request):
        pass
""",
    "src/core/handlers/response_handler.py": """\
# Response handler stub
class ResponseHandler:
    def format(self, data):
        return json.dumps(data)
""",
    "src/core/validators/input_validator.py": """\
# Input validator
def validate(payload):
    return bool(payload)
""",
    "src/api/v1/routes/user_routes.py": """\
# User routes v1
ROUTES = ['/users', '/users/<id>']
""",
    "src/api/v2/routes/skill_routes.py": """\
# Skill routes v2
ROUTES = ['/skills', '/skills/<id>/install', '/skills/<id>/uninstall']
""",
    "src/utils/crypto/hash_util.py": """\
import hashlib
def hash_user_id(uid):
    return hashlib.sha256(uid.encode()).hexdigest()
""",
    "src/utils/logging/logger.py": """\
import logging
logger = logging.getLogger('app')
""",
    "tests/unit/core/test_handler.py": """\
def test_handler():
    assert True
""",
    "tests/integration/test_api.py": """\
def test_api_smoke():
    assert True
""",
    "docs/internal/permission_notes.txt": """\
Permission system notes - DRAFT
================================
Various thoughts on access control.
Level A: super user
Level B: normal user
(These levels are NOT the real implementation - see actual config)
""",
    "scripts/migration/migrate_v1_to_v2.py": """\
# Migration script - do not run in production
print('migrating...')
""",
    "config_backup/old_permissions.json": """\
{
  "users": {
    "admin": "all",
    "user": "read"
  }
}
""",
    ".cache/tmp/session_abc123.tmp": "session data placeholder\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── 2. Create an INCOMPLETE / BROKEN config at the WRONG location ──────────────
# The agent must put it at the correct proprietary path; this wrong-path file
# acts as a red herring.

wrong_config_dir = os.path.join(workspace, "config_backup")
os.makedirs(wrong_config_dir, exist_ok=True)
wrong_config = {
    "permissions": {
        "admin": 99,
        "guest": 1
    }
}
with open(os.path.join(wrong_config_dir, "config.json"), "w") as f:
    json.dump(wrong_config, f, indent=2)

# ── 3. Create a partial, malformed spec file the agent will read ───────────────
# This simulates a "ticket" or "request spec" that the agent must fulfil.

spec = {
    "task": "Set up the huo15-permission access control system for the platform.",
    "required_users": {
        "ZhaoBo": "administrator",
        "Xun": "regular_user",
        "HuangShuo": "regular_user",
        "LiuYang": "regular_user"
    },
    "test_cases": [
        {
            "id": "tc001",
            "userid": "ZhaoBo",
            "action": "安装技能",
            "expected_allowed": True
        },
        {
            "id": "tc002",
            "userid": "Xun",
            "action": "安装技能",
            "expected_allowed": False
        },
        {
            "id": "tc003",
            "userid": "HuangShuo",
            "action": "卸载技能",
            "expected_allowed": False
        },
        {
            "id": "tc004",
            "userid": "LiuYang",
            "action": "删除技能",
            "expected_allowed": False
        },
        {
            "id": "tc005",
            "userid": "Xun",
            "action": "新增",
            "expected_allowed": True
        },
        {
            "id": "tc006",
            "userid": "HuangShuo",
            "action": "修改",
            "expected_allowed": True
        },
        {
            "id": "tc007",
            "userid": "LiuYang",
            "action": "删除",
            "expected_allowed": True
        },
        {
            "id": "tc008",
            "userid": "ZhaoBo",
            "action": "卸载技能",
            "expected_allowed": True
        },
        {
            "id": "tc009",
            "userid": "Xun",
            "action": "remove skill",
            "expected_allowed": False
        },
        {
            "id": "tc010",
            "userid": "HuangShuo",
            "action": "创建",
            "expected_allowed": True
        }
    ],
    "output_file": "permission_check_results.json"
}

with open(os.path.join(workspace, "task_spec.json"), "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2, ensure_ascii=False)

print("Workspace generated successfully.")
print(f"Workspace root: {workspace}")
print("Files created:")
for root, dirs, files in os.walk(workspace):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")