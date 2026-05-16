import os
import stat
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractor_tree = {
    "docs/architecture/overview.md": "# Architecture\nTBD",
    "docs/architecture/decisions/001-use-rest.md": "# ADR-001\nWe chose REST.",
    "docs/onboarding/setup_guide.txt": "Ask DevOps for help.",
    "infra/terraform/main.tf": 'provider "aws" { region = "us-east-1" }',
    "infra/terraform/variables.tf": 'variable "env" { default = "dev" }',
    "infra/docker/Dockerfile.prod": "FROM python:3.11\nCMD gunicorn",
    "infra/docker/docker-compose.yml": "version: '3'\nservices:\n  db:\n    image: postgres",
    "scripts/legacy/old_setup.sh": "#!/bin/bash\necho 'deprecated'",
    "scripts/legacy/migrate_v1.py": "# old migration helper - do not use",
    "scripts/utils/check_health.sh": "#!/bin/bash\ncurl -s http://localhost:8000/health/",
    "notes/sprint_planning.txt": "Sprint 12 goals: finish patient API",
    "notes/tech_debt.txt": "Refactor auth module by Q3",
    ".gitignore": "*.pyc\n__pycache__/\n.env\nvenv/\n*.log",
    "CHANGELOG.md": "## v0.1.0\n- Initial commit",
}

for rel_path, content in distractor_tree.items():
    full = WORKSPACE / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)

# ── The bootstrapping tool ────────────────────────────────────────────────────
# Simulate a realistic "team provisioner" tool already present on the server.
# The tool lives at /workspace/provisioner/ and exposes a CLI: provision.sh

provisioner_dir = WORKSPACE / "provisioner"
provisioner_dir.mkdir(exist_ok=True)

# ── provision.sh  (the main entrypoint the agent must discover & invoke) ──────
provision_sh = provisioner_dir / "provision.sh"
provision_sh.write_text(textwrap.dedent(r"""
#!/usr/bin/env bash
# =============================================================================
# provision.sh  –  Automated Django / DRF project bootstrapper
# Usage:
#   ./provision.sh --framework <django|drf> --project-name <name> [--output-dir <dir>]
#
# Options:
#   --framework     django   : plain Django project
#                   drf      : Django REST Framework project (default REST setup)
#   --project-name  <name>   : Python-identifier used as the Django project package name
#   --output-dir    <dir>    : destination directory (default: current working dir)
#
# What it does:
#   1. Creates a virtualenv at <output-dir>/.venv
#   2. Installs dependencies (framework-specific requirements)
#   3. Runs django-admin startproject
#   4. Overlays the standard settings split (base / development / production)
#   5. Writes requirements/ directory with base.txt, dev.txt, prod.txt
#   6. Creates a .env.example with mandatory variables
#   7. Writes a provisioner_manifest.json recording what was built
# =============================================================================
set -euo pipefail

FRAMEWORK=""
PROJECT_NAME=""
OUTPUT_DIR="$(pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --framework)     FRAMEWORK="$2";     shift 2 ;;
    --project-name)  PROJECT_NAME="$2";  shift 2 ;;
    --output-dir)    OUTPUT_DIR="$2";    shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$FRAMEWORK" || -z "$PROJECT_NAME" ]]; then
  echo "ERROR: --framework and --project-name are required."
  exit 1
fi

if [[ "$FRAMEWORK" != "django" && "$FRAMEWORK" != "drf" ]]; then
  echo "ERROR: --framework must be 'django' or 'drf'."
  exit 1
fi

# Validate project name (must be a valid Python identifier)
if ! python3 -c "import keyword,sys; n='$PROJECT_NAME'; sys.exit(0 if (n.isidentifier() and not keyword.iskeyword(n)) else 1)"; then
  echo "ERROR: --project-name '$PROJECT_NAME' is not a valid Python identifier."
  exit 1
fi

PROJECT_DIR="$OUTPUT_DIR/$PROJECT_NAME"
mkdir -p "$PROJECT_DIR"

echo "[provisioner] Creating virtualenv..."
python3 -m venv "$PROJECT_DIR/.venv"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
VENV_PIP="$PROJECT_DIR/.venv/bin/pip"

"$VENV_PIP" install --quiet --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "[provisioner] Installing base dependencies..."
"$VENV_PIP" install --quiet django python-decouple django-environ \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

if [[ "$FRAMEWORK" == "drf" ]]; then
  echo "[provisioner] Installing DRF dependencies..."
  "$VENV_PIP" install --quiet djangorestframework django-cors-headers \
      -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

echo "[provisioner] Scaffolding Django project..."
"$VENV_PY" -m django startproject "$PROJECT_NAME" "$PROJECT_DIR"

# ── Settings split ────────────────────────────────────────────────────────────
SETTINGS_DIR="$PROJECT_DIR/$PROJECT_NAME/settings"
mkdir -p "$SETTINGS_DIR"

# Move original settings.py -> settings/base.py  then delete it
mv "$PROJECT_DIR/$PROJECT_NAME/settings.py" "$SETTINGS_DIR/base.py"

# Patch base.py: replace the hard-coded SECRET_KEY with decouple
python3 - <<PYEOF
import re, pathlib
p = pathlib.Path("$SETTINGS_DIR/base.py")
txt = p.read_text()
# inject decouple import after first import line
txt = "from decouple import config\n" + txt
# replace SECRET_KEY line
txt = re.sub(r"SECRET_KEY\s*=\s*'[^']*'", "SECRET_KEY = config('SECRET_KEY')", txt)
# replace DEBUG line
txt = re.sub(r"DEBUG\s*=\s*True", "DEBUG = config('DEBUG', default=False, cast=bool)", txt)
p.write_text(txt)
PYEOF

# ── settings/development.py ───────────────────────────────────────────────────
cat > "$SETTINGS_DIR/development.py" <<'DEVEOF'
from .base import *  # noqa

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_dev.sqlite3",
    }
}
DEVEOF

# ── settings/production.py ───────────────────────────────────────────────────
cat > "$SETTINGS_DIR/production.py" <<'PRODEOF'
from .base import *  # noqa

DEBUG = False

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "proddb",
        "USER": "produser",
        "PASSWORD": "changeme",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
PRODEOF

# ── settings/__init__.py  (empty – user chooses env) ─────────────────────────
touch "$SETTINGS_DIR/__init__.py"

# ── DRF-specific: add to INSTALLED_APPS in base.py ───────────────────────────
if [[ "$FRAMEWORK" == "drf" ]]; then
python3 - <<PYEOF
import pathlib
p = pathlib.Path("$SETTINGS_DIR/base.py")
txt = p.read_text()
txt = txt.replace(
    "INSTALLED_APPS = [",
    "INSTALLED_APPS = [\n    'rest_framework',\n    'corsheaders',"
)
p.write_text(txt)
PYEOF
fi

# ── requirements/ ─────────────────────────────────────────────────────────────
REQ_DIR="$PROJECT_DIR/requirements"
mkdir -p "$REQ_DIR"

cat > "$REQ_DIR/base.txt" <<BASEEOF
Django>=4.2,<5.0
python-decouple>=3.8
django-environ>=0.11
BASEEOF

if [[ "$FRAMEWORK" == "drf" ]]; then
  cat >> "$REQ_DIR/base.txt" <<DRFEOF
djangorestframework>=3.14
django-cors-headers>=4.0
DRFEOF
fi

cat > "$REQ_DIR/dev.txt" <<DEVREQEOF
-r base.txt
pytest>=7.0
pytest-django>=4.5
DEVREQEOF

cat > "$REQ_DIR/prod.txt" <<PRODREQEOF
-r base.txt
gunicorn>=21.0
whitenoise>=6.0
psycopg2-binary>=2.9
PRODREQEOF

# ── .env.example ─────────────────────────────────────────────────────────────
cat > "$PROJECT_DIR/.env.example" <<ENVEOF
SECRET_KEY=replace-me-with-a-real-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db_dev.sqlite3
ENVEOF

# ── provisioner_manifest.json ────────────────────────────────────────────────
python3 - <<PYEOF
import json, pathlib, datetime
manifest = {
    "provisioned_at": datetime.datetime.utcnow().isoformat() + "Z",
    "framework": "$FRAMEWORK",
    "project_name": "$PROJECT_NAME",
    "settings_split": ["base", "development", "production"],
    "requirements_files": ["base.txt", "dev.txt", "prod.txt"],
    "venv_path": ".venv"
}
pathlib.Path("$PROJECT_DIR/provisioner_manifest.json").write_text(
    json.dumps(manifest, indent=2)
)
PYEOF

echo "[provisioner] Done. Project provisioned at: $PROJECT_DIR"
""").lstrip())

provision_sh.chmod(provision_sh.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Minimal README for the provisioner tool (technical, not a hint) ───────────
(provisioner_dir / "README.txt").write_text(textwrap.dedent("""
    Provisioner Tool
    ================
    Run ./provision.sh --help or inspect the script header for usage.
    Supported frameworks: django, drf
    Required flags: --framework, --project-name
    Optional flags: --output-dir
""").lstrip())

# ── A stale, broken attempt by a previous dev (distractor) ───────────────────
broken_attempt = WORKSPACE / "scratch" / "broken_init"
broken_attempt.mkdir(parents=True, exist_ok=True)
(broken_attempt / "manage.py").write_text("# this was manually created and is incomplete")
(broken_attempt / "settings.py").write_text(
    "SECRET_KEY = 'hardcoded-bad'\nDEBUG = True\nINSTALLED_APPS = []"
)
(broken_attempt / "requirements.txt").write_text("django\n# missing drf")

print("Workspace generated successfully.")
print("Distractor files:", len(distractor_tree))
print("Provisioner tool:", str(provision_sh))