import sys
import json
import ast
import os
from pathlib import Path

def load_python_source(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None

def find_integration_root(workspace: str) -> Path | None:
    candidates = list(Path(workspace).rglob("custom_components/nestguard"))
    if candidates:
        return candidates[0]
    return None

def check_ast_valid(src: str, filename: str) -> tuple[bool, str]:
    try:
        ast.parse(src)
        return True, f"{filename} is valid Python"
    except SyntaxError as e:
        return False, f"{filename} has SyntaxError: {e}"

def src_contains(src: str, *fragments: str) -> bool:
    return all(frag in src for frag in fragments)

def check_no_underscore_private_api(src: str) -> tuple[bool, str]:
    """Ensure no hass.data['_xxx'] or hass.data[\"_xxx\"] patterns."""
    import re
    pattern = re.compile(r'hass\.data\s*\[\s*["\']_')
    match = pattern.search(src)
    if match:
        return False, f"Uses private underscore API: {match.group()!r}"
    return True, "No private underscore API usage"

def evaluate(workspace: str):
    checks = []

    # ── Locate integration root ───────────────────────────────────────────────
    root = find_integration_root(workspace)
    checks.append({
        "name": "custom_components/nestguard directory exists",
        "passed": root is not None,
        "detail": str(root) if root else "Directory not found"
    })
    if root is None:
        # Can't proceed
        return finalize(checks)

    # ── manifest.json ─────────────────────────────────────────────────────────
    manifest_path = root / "manifest.json"
    manifest_ok = False
    try:
        manifest_raw = manifest_path.read_text()
        manifest = json.loads(manifest_raw)
        required_keys = {"domain", "name", "codeowners", "config_flow", "dependencies",
                         "requirements", "version"}
        missing = required_keys - manifest.keys()
        domain_ok = manifest.get("domain") == "nestguard"
        config_flow_ok = manifest.get("config_flow") is True
        version_present = bool(manifest.get("version"))
        manifest_ok = not missing and domain_ok and config_flow_ok and version_present
        detail = (
            f"domain={manifest.get('domain')}, config_flow={manifest.get('config_flow')}, "
            f"version={manifest.get('version')}, missing_keys={missing}"
        )
    except Exception as e:
        detail = f"Failed to read/parse manifest.json: {e}"

    checks.append({
        "name": "manifest.json: required fields, domain=nestguard, config_flow=true",
        "passed": manifest_ok,
        "detail": detail
    })

    # ── services.yaml ─────────────────────────────────────────────────────────
    services_path = root / "services.yaml"
    services_ok = False
    try:
        content = services_path.read_text()
        services_ok = "get_zone_config" in content
        detail = "get_zone_config found" if services_ok else "get_zone_config NOT found in services.yaml"
    except Exception as e:
        detail = f"Failed to read services.yaml: {e}"

    checks.append({
        "name": "services.yaml: defines get_zone_config service",
        "passed": services_ok,
        "detail": detail
    })

    # ── __init__.py ───────────────────────────────────────────────────────────
    init_path = root / "__init__.py"
    init_src = load_python_source(init_path)
    init_exists = init_src is not None
    checks.append({
        "name": "__init__.py exists",
        "passed": init_exists,
        "detail": str(init_path) if init_exists else "File not found"
    })

    if init_src:
        # Must be valid Python
        valid, detail = check_ast_valid(init_src, "__init__.py")
        checks.append({"name": "__init__.py: valid Python syntax", "passed": valid, "detail": detail})

        # Must import SupportsResponse from homeassistant.helpers.service
        supports_import = (
            "SupportsResponse" in init_src and
            "homeassistant.helpers.service" in init_src
        )
        checks.append({
            "name": "__init__.py: imports SupportsResponse from homeassistant.helpers.service",
            "passed": supports_import,
            "detail": "SupportsResponse import found" if supports_import else "Missing SupportsResponse import from homeassistant.helpers.service"
        })

        # Must use SupportsResponse.ONLY (not OPTIONAL or nothing)
        supports_only = "SupportsResponse.ONLY" in init_src
        checks.append({
            "name": "__init__.py: uses SupportsResponse.ONLY for get_zone_config service",
            "passed": supports_only,
            "detail": "SupportsResponse.ONLY found" if supports_only else "SupportsResponse.ONLY NOT found — service won't return data"
        })

        # Must register the service
        registers_service = (
            "async_register" in init_src and
            "get_zone_config" in init_src
        )
        checks.append({
            "name": "__init__.py: registers nestguard.get_zone_config service",
            "passed": registers_service,
            "detail": "Service registration found" if registers_service else "Service registration missing"
        })

        # Must register an HTTP view
        registers_view = "register_view" in init_src and "http" in init_src
        checks.append({
            "name": "__init__.py: calls hass.http.register_view(...)",
            "passed": registers_view,
            "detail": "register_view call found" if registers_view else "register_view call NOT found"
        })

        # Must NOT use underscore private APIs
        no_private, detail = check_no_underscore_private_api(init_src)
        checks.append({"name": "__init__.py: no private underscore API usage", "passed": no_private, "detail": detail})

        # Must import or reference HomeAssistantView
        has_view_class = "HomeAssistantView" in init_src or any(
            "HomeAssistantView" in (load_python_source(p) or "")
            for p in root.glob("*.py")
        )
        checks.append({
            "name": "Integration: defines/imports HomeAssistantView subclass",
            "passed": has_view_class,
            "detail": "HomeAssistantView found in integration" if has_view_class else "HomeAssistantView NOT found anywhere in integration"
        })

    # ── HTTP View checks (may be in __init__.py or a separate view file) ───────
    all_py_sources = []
    for py_file in root.glob("*.py"):
        src = load_python_source(py_file)
        if src:
            all_py_sources.append((py_file.name, src))

    combined_src = "\n".join(s for _, s in all_py_sources)

    # url must be /api/nestguard/zones
    correct_url = '"/api/nestguard/zones"' in combined_src or "'/api/nestguard/zones'" in combined_src
    checks.append({
        "name": "HTTP View: url = '/api/nestguard/zones'",
        "passed": correct_url,
        "detail": "Correct URL found" if correct_url else "URL /api/nestguard/zones NOT found in any .py file"
    })

    # requires_auth = True
    requires_auth = "requires_auth" in combined_src and (
        "requires_auth = True" in combined_src or "requires_auth=True" in combined_src
    )
    checks.append({
        "name": "HTTP View: requires_auth = True",
        "passed": requires_auth,
        "detail": "requires_auth = True found" if requires_auth else "requires_auth = True NOT found"
    })

    # request.app["hass"] pattern for hass retrieval inside view
    hass_from_request = 'request.app["hass"]' in combined_src or "request.app['hass']" in combined_src
    checks.append({
        "name": "HTTP View: retrieves hass via request.app[\"hass\"]",
        "passed": hass_from_request,
        "detail": "request.app[\"hass\"] found" if hass_from_request else "request.app[\"hass\"] NOT found — wrong hass access pattern inside view"
    })

    # ── storage_services.py ───────────────────────────────────────────────────
    storage_path = root / "storage_services.py"
    storage_src = load_python_source(storage_path)
    storage_exists = storage_src is not None
    checks.append({
        "name": "storage_services.py exists",
        "passed": storage_exists,
        "detail": str(storage_path) if storage_exists else "File not found"
    })

    if storage_src:
        valid, detail = check_ast_valid(storage_src, "storage_services.py")
        checks.append({"name": "storage_services.py: valid Python syntax", "passed": valid, "detail": detail})

        # Must use homeassistant.helpers.storage.Store
        uses_store = "from homeassistant.helpers.storage import Store" in storage_src or \
                     "homeassistant.helpers.storage" in storage_src
        checks.append({
            "name": "storage_services.py: uses homeassistant.helpers.storage.Store",
            "passed": uses_store,
            "detail": "Store import found" if uses_store else "Store import NOT found — wrong storage pattern"
        })

        # Storage key must be nestguard.zones
        correct_key = "nestguard.zones" in storage_src
        checks.append({
            "name": "storage_services.py: STORAGE_KEY = 'nestguard.zones'",
            "passed": correct_key,
            "detail": "nestguard.zones found" if correct_key else "nestguard.zones NOT found as storage key"
        })

        # Storage version = 1
        version_ok = "STORAGE_VERSION = 1" in storage_src or "STORAGE_VERSION=1" in storage_src or \
                     "Store(hass, 1," in storage_src or "Store(hass,1," in storage_src
        checks.append({
            "name": "storage_services.py: STORAGE_VERSION = 1",
            "passed": version_ok,
            "detail": "Storage version 1 found" if version_ok else "Storage version 1 NOT found"
        })

        # Must use async_save and async_load
        has_save = "async_save" in storage_src
        has_load = "async_load" in storage_src
        storage_ops_ok = has_save and has_load
        checks.append({
            "name": "storage_services.py: uses async_save and async_load",
            "passed": storage_ops_ok,
            "detail": f"async_save={has_save}, async_load={has_load}"
        })

        no_private_s, detail = check_no_underscore_private_api(storage_src)
        checks.append({"name": "storage_services.py: no private underscore API usage", "passed": no_private_s, "detail": detail})

    # ── config_flow.py ────────────────────────────────────────────────────────
    cf_path = root / "config_flow.py"
    cf_src = load_python_source(cf_path)
    cf_exists = cf_src is not None
    checks.append({
        "name": "config_flow.py exists",
        "passed": cf_exists,
        "detail": str(cf_path) if cf_exists else "File not found"
    })

    if cf_src:
        valid, detail = check_ast_valid(cf_src, "config_flow.py")
        checks.append({"name": "config_flow.py: valid Python syntax", "passed": valid, "detail": detail})

        has_flow_class = "ConfigFlow" in cf_src
        checks.append({
            "name": "config_flow.py: defines a ConfigFlow class",
            "passed": has_flow_class,
            "detail": "ConfigFlow found" if has_flow_class else "ConfigFlow class NOT found"
        })

    return finalize(checks)


def finalize(checks):
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = passed_count == total
    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))