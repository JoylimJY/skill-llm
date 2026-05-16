import sys
import json
import os
from pathlib import Path

def run_checks(workspace_root: str):
    ws = Path(workspace_root)
    checks = []
    total_score = 0.0
    weights = {}

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        weights[name] = weight
        return passed

    # ── Locate provisioner_manifest.json ─────────────────────────────────────
    manifests = list(ws.rglob("provisioner_manifest.json"))
    manifest_found = add_check(
        "manifest_exists",
        len(manifests) >= 1,
        f"Found {len(manifests)} provisioner_manifest.json file(s): {[str(m) for m in manifests]}",
        weight=1.0,
    )

    manifest_data = {}
    if manifest_found:
        try:
            manifest_data = json.loads(manifests[0].read_text())
        except Exception as e:
            add_check("manifest_parseable", False, f"Could not parse manifest: {e}", weight=1.0)
            manifest_data = {}
    else:
        add_check("manifest_parseable", False, "No manifest to parse.", weight=1.0)

    # ── Framework must be 'drf' ───────────────────────────────────────────────
    framework_ok = add_check(
        "framework_is_drf",
        manifest_data.get("framework") == "drf",
        f"manifest.framework = {manifest_data.get('framework')!r} (expected 'drf')",
        weight=1.5,
    )

    # ── Project name is a valid Python identifier (non-empty) ─────────────────
    project_name = manifest_data.get("project_name", "")
    pname_ok = add_check(
        "project_name_valid",
        bool(project_name) and project_name.isidentifier(),
        f"project_name = {project_name!r}",
        weight=0.5,
    )

    # ── settings split: base / development / production ───────────────────────
    settings_split = manifest_data.get("settings_split", [])
    split_ok = add_check(
        "settings_split_recorded",
        set(settings_split) == {"base", "development", "production"},
        f"settings_split = {settings_split}",
        weight=1.0,
    )

    # ── Actual settings files exist on disk ───────────────────────────────────
    settings_dirs = list(ws.rglob("settings")) if project_name else []
    # Find the settings directory that is a package (has __init__.py)
    valid_settings_dir = None
    for sd in settings_dirs:
        if sd.is_dir() and (sd / "__init__.py").exists():
            valid_settings_dir = sd
            break

    settings_files_ok = False
    settings_detail = "No valid settings/ package directory found."
    if valid_settings_dir:
        has_base = (valid_settings_dir / "base.py").exists()
        has_dev = (valid_settings_dir / "development.py").exists()
        has_prod = (valid_settings_dir / "production.py").exists()
        settings_files_ok = has_base and has_dev and has_prod
        settings_detail = (
            f"In {valid_settings_dir}: base={has_base}, development={has_dev}, production={has_prod}"
        )
    add_check("settings_files_on_disk", settings_files_ok, settings_detail, weight=1.5)

    # ── base.py uses decouple for SECRET_KEY (not hardcoded) ─────────────────
    base_py_ok = False
    base_py_detail = "base.py not found or not readable."
    if valid_settings_dir and (valid_settings_dir / "base.py").exists():
        try:
            base_txt = (valid_settings_dir / "base.py").read_text()
            uses_decouple = "decouple" in base_txt
            no_hardcoded = "SECRET_KEY = '" not in base_txt and 'SECRET_KEY = "' not in base_txt
            base_py_ok = uses_decouple and no_hardcoded
            base_py_detail = f"uses_decouple={uses_decouple}, no_hardcoded_secret={no_hardcoded}"
        except Exception as e:
            base_py_detail = f"Error reading base.py: {e}"
    add_check("base_settings_uses_decouple", base_py_ok, base_py_detail, weight=1.5)

    # ── DRF installed in base.py INSTALLED_APPS ───────────────────────────────
    drf_in_apps = False
    drf_detail = "base.py not found."
    if valid_settings_dir and (valid_settings_dir / "base.py").exists():
        try:
            base_txt = (valid_settings_dir / "base.py").read_text()
            drf_in_apps = "'rest_framework'" in base_txt or '"rest_framework"' in base_txt
            drf_detail = f"'rest_framework' in INSTALLED_APPS section: {drf_in_apps}"
        except Exception as e:
            drf_detail = f"Error: {e}"
    add_check("drf_in_installed_apps", drf_in_apps, drf_detail, weight=2.0)

    # ── requirements/ directory with base.txt, dev.txt, prod.txt ─────────────
    req_dirs = list(ws.rglob("requirements")) if project_name else []
    req_dir_valid = None
    for rd in req_dirs:
        if rd.is_dir():
            req_dir_valid = rd
            break

    req_ok = False
    req_detail = "No requirements/ directory found."
    if req_dir_valid:
        has_base_req = (req_dir_valid / "base.txt").exists()
        has_dev_req = (req_dir_valid / "dev.txt").exists()
        has_prod_req = (req_dir_valid / "prod.txt").exists()
        req_ok = has_base_req and has_dev_req and has_prod_req
        req_detail = (
            f"In {req_dir_valid}: base.txt={has_base_req}, dev.txt={has_dev_req}, prod.txt={has_prod_req}"
        )
    add_check("requirements_split_exists", req_ok, req_detail, weight=1.0)

    # ── base.txt includes djangorestframework (DRF project) ──────────────────
    drf_in_req = False
    drf_req_detail = "base.txt not found."
    if req_dir_valid and (req_dir_valid / "base.txt").exists():
        try:
            base_req_txt = (req_dir_valid / "base.txt").read_text().lower()
            drf_in_req = "djangorestframework" in base_req_txt
            drf_req_detail = f"djangorestframework in base.txt: {drf_in_req}"
        except Exception as e:
            drf_req_detail = f"Error: {e}"
    add_check("drf_in_requirements", drf_in_req, drf_req_detail, weight=1.5)

    # ── .env.example exists ───────────────────────────────────────────────────
    env_examples = list(ws.rglob(".env.example"))
    env_ok = len(env_examples) >= 1
    add_check(
        "env_example_exists",
        env_ok,
        f"Found {len(env_examples)} .env.example file(s).",
        weight=0.5,
    )

    # ── virtualenv was created (.venv directory) ──────────────────────────────
    venvs = list(ws.rglob(".venv"))
    venv_ok = any(v.is_dir() for v in venvs)
    add_check(
        "venv_created",
        venv_ok,
        f"Found .venv dirs: {[str(v) for v in venvs if v.is_dir()]}",
        weight=1.0,
    )

    # ── Not using the broken scratch attempt as the real project ─────────────
    scratch_not_used = add_check(
        "scratch_not_used_as_project",
        not (ws / "scratch" / "broken_init" / "provisioner_manifest.json").exists(),
        "Confirmed: scratch/broken_init was not the provisioned output.",
        weight=0.5,
    )

    # ── Score calculation ─────────────────────────────────────────────────────
    total_weight = sum(weights[c["name"]] for c in checks)
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"])
    score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0

    # Overall pass: must score >= 0.80 AND critical checks must pass
    critical = ["framework_is_drf", "settings_files_on_disk", "drf_in_installed_apps",
                "base_settings_uses_decouple", "drf_in_requirements"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    passed = score >= 0.80 and critical_passed

    return {
        "passed": passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [],
                          "error": "No workspace path provided."}))
        sys.exit(1)
    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))