import sys
import os
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

workspace = sys.argv[1]
ws = Path(workspace)

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    global total_score, max_score
    checks.append({"name": name, "passed": passed, "detail": detail})
    max_score += weight
    if passed:
        total_score += weight

# ── Helper ────────────────────────────────────────────────────────────────────
def read_json(path):
    with open(path) as f:
        return json.load(f)

def read_yaml(path):
    with open(path) as f:
        if yaml:
            return yaml.safe_load(f)
        # Fallback: crude parse
        content = f.read()
        return content

# ════════════════════════════════════════════════════════════════════════════════
# CHECK 1: pnpm-workspace.yaml exists and has correct package globs
# ════════════════════════════════════════════════════════════════════════════════
try:
    pw_path = ws / "pnpm-workspace.yaml"
    if not pw_path.exists():
        add_check("pnpm-workspace.yaml exists", False, "File not found at root", weight=2.0)
    else:
        content = pw_path.read_text()
        has_apps = "apps/*" in content
        has_packages = "packages/*" in content
        passed = has_apps and has_packages
        add_check(
            "pnpm-workspace.yaml has correct globs",
            passed,
            f"apps/*: {has_apps}, packages/*: {has_packages}. Content:\n{content}",
            weight=2.0
        )
except Exception as e:
    add_check("pnpm-workspace.yaml exists", False, f"Exception: {e}", weight=2.0)

# ════════════════════════════════════════════════════════════════════════════════
# CHECK 2: Root package.json has workspaces or turbo devDep + correct name
# ════════════════════════════════════════════════════════════════════════════════
try:
    root_pkg_path = ws / "package.json"
    root_pkg = read_json(root_pkg_path)
    
    name_ok = root_pkg.get("name") == "medplatform"
    private_ok = root_pkg.get("private") == True
    
    # turbo should be in devDependencies
    dev_deps = root_pkg.get("devDependencies", {})
    turbo_present = "turbo" in dev_deps
    
    # Should have build/lint/test scripts using turbo
    scripts = root_pkg.get("scripts", {})
    has_build_script = "build" in scripts
    build_uses_turbo = "turbo" in scripts.get("build", "")
    
    passed = name_ok and private_ok and turbo_present
    add_check(
        "Root package.json: name=medplatform, private=true, turbo devDep",
        passed,
        f"name={root_pkg.get('name')}, private={root_pkg.get('private')}, turbo_devDep={turbo_present}",
        weight=2.0
    )
    add_check(
        "Root package.json: build script uses turbo",
        has_build_script and build_uses_turbo,
        f"scripts.build = '{scripts.get('build', '')}'",
        weight=1.0
    )
except Exception as e:
    add_check("Root package.json valid", False, f"Exception: {e}", weight=3.0)

# ════════════════════════════════════════════════════════════════════════════════
# CHECK 3: turbo.json exists at root and uses 'tasks' key (NOT 'pipeline')
# ════════════════════════════════════════════════════════════════════════════════
try:
    turbo_path = ws / "turbo.json"
    if not turbo_path.exists():
        add_check("turbo.json exists", False, "turbo.json not found at root", weight=3.0)
    else:
        turbo = read_json(turbo_path)
        
        # Must use 'tasks' not 'pipeline' (Turborepo v2)
        uses_tasks_key = "tasks" in turbo
        uses_pipeline_key = "pipeline" in turbo
        add_check(
            "turbo.json uses 'tasks' key (not deprecated 'pipeline')",
            uses_tasks_key and not uses_pipeline_key,
            f"Has 'tasks': {uses_tasks_key}, Has 'pipeline': {uses_pipeline_key}",
            weight=2.0
        )
        
        tasks = turbo.get("tasks", turbo.get("pipeline", {}))
        
        # Build task: dependsOn ^build, outputs dist/** and .next/**
        build_task = tasks.get("build", {})
        build_depends = build_task.get("dependsOn", [])
        build_outputs = build_task.get("outputs", [])
        build_dep_ok = "^build" in build_depends
        has_dist = any("dist" in o for o in build_outputs)
        has_next = any(".next" in o for o in build_outputs)
        
        add_check(
            "turbo.json build task: dependsOn ['^build']",
            build_dep_ok,
            f"build.dependsOn = {build_depends}",
            weight=2.0
        )
        add_check(
            "turbo.json build task: outputs include dist/** and .next/**",
            has_dist and has_next,
            f"build.outputs = {build_outputs}",
            weight=2.0
        )
        
        # Lint task: must have dependsOn ^build (non-obvious from skill)
        lint_task = tasks.get("lint", {})
        lint_depends = lint_task.get("dependsOn", [])
        lint_dep_ok = "^build" in lint_depends
        add_check(
            "turbo.json lint task: dependsOn ['^build']",
            lint_dep_ok,
            f"lint.dependsOn = {lint_depends}",
            weight=2.0
        )
        
        # Test task: must have dependsOn ^build
        test_task = tasks.get("test", {})
        test_depends = test_task.get("dependsOn", [])
        test_dep_ok = "^build" in test_depends
        add_check(
            "turbo.json test task: dependsOn ['^build']",
            test_dep_ok,
            f"test.dependsOn = {test_depends}",
            weight=2.0
        )

except Exception as e:
    add_check("turbo.json valid", False, f"Exception: {e}", weight=11.0)

# ════════════════════════════════════════════════════════════════════════════════
# CHECK 4: Correct package structure - apps/web and apps/admin
# ════════════════════════════════════════════════════════════════════════════════
for app_name, pkg_name in [("web", "@medplatform/web"), ("admin", "@medplatform/admin")]:
    try:
        pkg_path = ws / "apps" / app_name / "package.json"
        if not pkg_path.exists():
            add_check(f"apps/{app_name}/package.json exists", False, f"Missing: {pkg_path}", weight=1.5)
            continue
        pkg = read_json(pkg_path)
        name_ok = pkg.get("name") == pkg_name
        add_check(
            f"apps/{app_name} package name is '{pkg_name}'",
            name_ok,
            f"name = '{pkg.get('name')}'",
            weight=1.5
        )
    except Exception as e:
        add_check(f"apps/{app_name} package.json", False, f"Exception: {e}", weight=1.5)

# ════════════════════════════════════════════════════════════════════════════════
# CHECK 5: Correct package structure - packages/ui, utils, config-eslint, config-typescript
# ════════════════════════════════════════════════════════════════════════════════
expected_packages = {
    "ui": "@medplatform/ui",
    "utils": "@medplatform/utils",
    "config-eslint": "@medplatform/config-eslint",
    "config-typescript": "@medplatform/config-typescript",
}
for dir_name, expected_pkg_name in expected_packages.items():
    try:
        pkg_path = ws / "packages" / dir_name / "package.json"
        if not pkg_path.exists():
            add_check(f"packages/{dir_name}/package.json exists", False, f"Missing: {pkg_path}", weight=1.5)
            continue
        pkg = read_json(pkg_path)
        name_ok = pkg.get("name") == expected_pkg_name
        add_check(
            f"packages/{dir_name} package name is '{expected_pkg_name}'",
            name_ok,
            f"name = '{pkg.get('name')}'",
            weight=1.5
        )
    except Exception as e:
        add_check(f"packages/{dir_name} package.json", False, f"Exception: {e}", weight=1.5)

# ════════════════════════════════════════════════════════════════════════════════
# CHECK 6: Internal deps use workspace:* (the proprietary protocol)
# ════════════════════════════════════════════════════════════════════════════════

# apps/web and apps/admin must depend on @medplatform/ui and @medplatform/utils via workspace:*
for app_name in ["web", "admin"]:
    try:
        pkg_path = ws / "apps" / app_name / "package.json"
        pkg = read_json(pkg_path)
        all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        
        ui_dep = all_deps.get("@medplatform/ui", "")
        utils_dep = all_deps.get("@medplatform/utils", "")
        
        ui_ok = ui_dep == "workspace:*"
        utils_ok = utils_dep == "workspace:*"
        
        add_check(
            f"apps/{app_name}: @medplatform/ui uses 'workspace:*'",
            ui_ok,
            f"@medplatform/ui = '{ui_dep}' (expected 'workspace:*')",
            weight=2.0
        )
        add_check(
            f"apps/{app_name}: @medplatform/utils uses 'workspace:*'",
            utils_ok,
            f"@medplatform/utils = '{utils_dep}' (expected 'workspace:*')",
            weight=2.0
        )
    except Exception as e:
        add_check(f"apps/{app_name} workspace:* deps", False, f"Exception: {e}", weight=4.0)

# packages/ui and packages/utils must reference config packages via workspace:*
for pkg_dir, config_deps in [
    ("ui", ["@medplatform/config-eslint", "@medplatform/config-typescript"]),
    ("utils", ["@medplatform/config-eslint", "@medplatform/config-typescript"]),
]:
    try:
        pkg_path = ws / "packages" / pkg_dir / "package.json"
        pkg = read_json(pkg_path)
        all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        
        for config_dep in config_deps:
            dep_val = all_deps.get(config_dep, "")
            dep_ok = dep_val == "workspace:*"
            add_check(
                f"packages/{pkg_dir}: {config_dep} uses 'workspace:*'",
                dep_ok,
                f"{config_dep} = '{dep_val}' (expected 'workspace:*')",
                weight=1.5
            )
    except Exception as e:
        add_check(f"packages/{pkg_dir} config workspace:* deps", False, f"Exception: {e}", weight=3.0)

# ════════════════════════════════════════════════════════════════════════════════
# FINAL SCORING
# ════════════════════════════════════════════════════════════════════════════════
score = round(total_score / max_score, 4) if max_score > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))