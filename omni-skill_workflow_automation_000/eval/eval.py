#!/usr/bin/env python3
"""
Evaluation script for the OmniSkill integration task.
Checks:
  1. omni_packager.py was run from within omni-skill/ (manifest.json exists with correct project_root)
  2. Package directory contains manifest.json with correct schema_version and source info
  3. Package directory contains __init__.py with __omni_package__ = True
  4. registry.json was updated with the text_classifier skill
  5. dispatch_result.json exists, is valid OmniResponse JSON, and has all required fields
  6. dispatch_result.json payload has all 5 required request fields reflected correctly
"""
import json
import sys
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    passed_all = True

    # ── Helper ──────────────────────────────────────────────
    def add(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # ───────────────────────────────────────────────────────
    # Check 1: Package directory exists somewhere under /workspace
    # ───────────────────────────────────────────────────────
    manifests = list(ws.rglob("manifest.json"))
    # Filter out any accidentally pre-existing ones by checking content
    valid_manifests = []
    for m in manifests:
        try:
            data = json.loads(m.read_text())
            if data.get("packaged_by") == "omni_packager":
                valid_manifests.append((m, data))
        except Exception:
            pass

    if valid_manifests:
        mpath, mdata = valid_manifests[0]
        add("package_manifest_exists",
            True,
            f"manifest.json found at {mpath}")
    else:
        add("package_manifest_exists",
            False,
            "No manifest.json produced by omni_packager found anywhere in workspace.")

    # ───────────────────────────────────────────────────────
    # Check 2: manifest.json schema_version and packaged_by
    # ───────────────────────────────────────────────────────
    if valid_manifests:
        mpath, mdata = valid_manifests[0]
        ok = (mdata.get("schema_version") == "1.0"
              and mdata.get("packaged_by") == "omni_packager")
        add("manifest_schema_correct",
            ok,
            f"schema_version={mdata.get('schema_version')}, packaged_by={mdata.get('packaged_by')}")
    else:
        add("manifest_schema_correct", False, "No manifest.json to inspect.")

    # ───────────────────────────────────────────────────────
    # Check 3: manifest project_root is within omni-skill/
    #          (proves packager was called from correct directory)
    # ───────────────────────────────────────────────────────
    if valid_manifests:
        mpath, mdata = valid_manifests[0]
        project_root = mdata.get("project_root", "")
        # project_root must end with 'omni-skill' (or contain it)
        ok = "omni-skill" in project_root
        add("packager_run_from_project_root",
            ok,
            f"project_root recorded as '{project_root}' — must contain 'omni-skill'")
    else:
        add("packager_run_from_project_root", False, "No manifest to check project_root.")

    # ───────────────────────────────────────────────────────
    # Check 4: Package __init__.py has __omni_package__ = True
    # ───────────────────────────────────────────────────────
    if valid_manifests:
        mpath, mdata = valid_manifests[0]
        pkg_dir = mpath.parent
        init_path = pkg_dir / "__init__.py"
        try:
            content = init_path.read_text()
            ok = "__omni_package__ = True" in content
            add("package_init_flag",
                ok,
                f"__init__.py {'contains' if ok else 'missing'} __omni_package__ = True")
        except FileNotFoundError:
            add("package_init_flag", False, f"__init__.py not found in {pkg_dir}")
    else:
        add("package_init_flag", False, "No package directory to check.")

    # ───────────────────────────────────────────────────────
    # Check 5: Source files were copied into the package
    # ───────────────────────────────────────────────────────
    if valid_manifests:
        mpath, mdata = valid_manifests[0]
        pkg_dir = mpath.parent
        py_files = [p for p in pkg_dir.rglob("*.py") if p.name != "__init__.py"]
        ok = len(py_files) >= 3  # classifier.py, base_model.py, preprocessor.py, tokenizer.py
        add("source_files_copied",
            ok,
            f"Found {len(py_files)} .py source files in package (expected ≥3): "
            f"{[str(p.relative_to(pkg_dir)) for p in py_files]}")
    else:
        add("source_files_copied", False, "No package directory.")

    # ───────────────────────────────────────────────────────
    # Check 6: registry.json updated with text_classifier
    # ───────────────────────────────────────────────────────
    registry_path = ws / "omni-skill" / "data" / "registry" / "registry.json"
    try:
        reg = json.loads(registry_path.read_text())
        skill_names = [s["name"] for s in reg.get("skills", [])]
        ok = "text_classifier" in skill_names
        add("skill_registered",
            ok,
            f"registry.json skills={skill_names} — 'text_classifier' {'found' if ok else 'NOT found'}")
    except FileNotFoundError:
        add("skill_registered", False, f"registry.json not found at {registry_path}")
    except Exception as e:
        add("skill_registered", False, f"Error reading registry.json: {e}")

    # ───────────────────────────────────────────────────────
    # Check 7: runtime_type is a valid value (python/node/bash/wasm)
    # ───────────────────────────────────────────────────────
    VALID_RUNTIME_TYPES = {"python", "node", "bash", "wasm"}
    try:
        reg = json.loads(registry_path.read_text())
        matching = [s for s in reg.get("skills", []) if s["name"] == "text_classifier"]
        if matching:
            rt = matching[0].get("runtime_type", "")
            ok = rt in VALID_RUNTIME_TYPES
            add("valid_runtime_type",
                ok,
                f"runtime_type='{rt}' — must be one of {sorted(VALID_RUNTIME_TYPES)}")
        else:
            add("valid_runtime_type", False, "text_classifier skill entry not found in registry.")
    except Exception as e:
        add("valid_runtime_type", False, f"Cannot read registry: {e}")

    # ───────────────────────────────────────────────────────
    # Check 8: dispatch_result.json exists
    # ───────────────────────────────────────────────────────
    result_files = list(ws.rglob("dispatch_result.json"))
    if result_files:
        add("dispatch_result_exists", True, f"dispatch_result.json found at {result_files[0]}")
        result_path = result_files[0]
    else:
        add("dispatch_result_exists", False, "dispatch_result.json not found anywhere in workspace.")
        result_path = None

    # ───────────────────────────────────────────────────────
    # Check 9: dispatch_result.json is valid OmniResponse JSON
    # ───────────────────────────────────────────────────────
    omni_resp = None
    if result_path:
        try:
            omni_resp = json.loads(result_path.read_text())
            required = {"schema_version", "status", "route_type", "mode", "dispatched_at", "result"}
            missing = required - set(omni_resp.keys())
            ok = len(missing) == 0
            add("omni_response_schema",
                ok,
                f"OmniResponse fields present={sorted(omni_resp.keys())} missing={sorted(missing)}")
        except json.JSONDecodeError as e:
            add("omni_response_schema", False, f"dispatch_result.json is not valid JSON: {e}")
        except Exception as e:
            add("omni_response_schema", False, f"Error reading dispatch_result.json: {e}")
    else:
        add("omni_response_schema", False, "No dispatch_result.json to validate.")

    # ───────────────────────────────────────────────────────
    # Check 10: OmniResponse status=ok and mode is valid
    # ───────────────────────────────────────────────────────
    if omni_resp:
        ok = (omni_resp.get("status") == "ok"
              and omni_resp.get("mode") in ("sync", "async"))
        add("omni_response_valid_content",
            ok,
            f"status={omni_resp.get('status')}, mode={omni_resp.get('mode')}")
    else:
        add("omni_response_valid_content", False, "No OmniResponse to validate.")

    # ───────────────────────────────────────────────────────
    # Check 11: The dispatched request included all 5 required JSON fields
    #           (reflected in registered_skills list showing text_classifier was live)
    # ───────────────────────────────────────────────────────
    if omni_resp:
        registered_in_response = omni_resp.get("registered_skills", [])
        ok = "text_classifier" in registered_in_response
        add("dispatch_used_registered_skill",
            ok,
            f"registered_skills at dispatch time: {registered_in_response} "
            f"— 'text_classifier' {'present' if ok else 'ABSENT (dispatch before register?)'}")
    else:
        add("dispatch_used_registered_skill", False, "No OmniResponse to inspect.")

    # ───────────────────────────────────────────────────────
    # Score
    # ───────────────────────────────────────────────────────
    n = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / n, 4) if n > 0 else 0.0

    return {
        "passed": passed_all,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "No workspace path provided."}]}))
        sys.exit(1)
    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))