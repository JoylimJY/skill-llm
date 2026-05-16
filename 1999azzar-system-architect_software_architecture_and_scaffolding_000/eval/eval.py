#!/usr/bin/env python3
"""
Evaluation script for the ClarityHealth monorepo scaffold task.
Usage: python eval_script.py <workspace_dir>
"""
import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
total_weight = 0
passed_weight = 0


def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_weight, passed_weight
    total_weight += weight
    if passed:
        passed_weight += weight


# ─── Helper: find a file anywhere under a subtree ───────────────────────────

def find_file(subtree: Path, filename: str) -> Path | None:
    matches = list(subtree.rglob(filename))
    return matches[0] if matches else None


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return ""


# ════════════════════════════════════════════════════════════════════
# CHECK GROUP 1 — Monorepo top-level structure
# Must use Option B: apps/backend/ and apps/frontend/ + packages/
# ════════════════════════════════════════════════════════════════════

apps_backend = workspace / "apps" / "backend"
apps_frontend = workspace / "apps" / "frontend"
packages_dir = workspace / "packages"

add_check(
    "monorepo/apps_backend_exists",
    apps_backend.is_dir(),
    f"apps/backend/ dir exists: {apps_backend.is_dir()}",
    weight=2.0,
)
add_check(
    "monorepo/apps_frontend_exists",
    apps_frontend.is_dir(),
    f"apps/frontend/ dir exists: {apps_frontend.is_dir()}",
    weight=2.0,
)
add_check(
    "monorepo/packages_exists",
    packages_dir.is_dir(),
    f"packages/ dir exists (monorepo shared code): {packages_dir.is_dir()}",
    weight=1.0,
)

# ════════════════════════════════════════════════════════════════════
# CHECK GROUP 2 — Python backend: src/ layout (NOT flat app/)
# Must have apps/backend/src/<package>/  AND apps/backend/tests/
# ════════════════════════════════════════════════════════════════════

backend_src = apps_backend / "src"
backend_tests = apps_backend / "tests"

add_check(
    "backend/src_layout_exists",
    backend_src.is_dir(),
    f"apps/backend/src/ exists (required src-layout): {backend_src.is_dir()}",
    weight=2.0,
)

# src must have at least one subdirectory (the package)
src_subdirs = [d for d in backend_src.iterdir() if d.is_dir()] if backend_src.is_dir() else []
add_check(
    "backend/src_has_package",
    len(src_subdirs) > 0,
    f"apps/backend/src/ contains a package directory: {[d.name for d in src_subdirs]}",
    weight=1.5,
)

# package must have __init__.py
has_init = any((pkg / "__init__.py").exists() for pkg in src_subdirs) if src_subdirs else False
add_check(
    "backend/package_has_init",
    has_init,
    f"Package inside src/ has __init__.py: {has_init}",
    weight=1.0,
)

add_check(
    "backend/tests_dir_exists",
    backend_tests.is_dir(),
    f"apps/backend/tests/ exists: {backend_tests.is_dir()}",
    weight=1.0,
)

# pyproject.toml (modern packaging)
backend_pyproject = apps_backend / "pyproject.toml"
add_check(
    "backend/pyproject_toml_exists",
    backend_pyproject.exists(),
    f"apps/backend/pyproject.toml exists: {backend_pyproject.exists()}",
    weight=1.5,
)

# .env.example
backend_env_example = apps_backend / ".env.example"
add_check(
    "backend/env_example_exists",
    backend_env_example.exists(),
    f"apps/backend/.env.example exists: {backend_env_example.exists()}",
    weight=0.5,
)

# ════════════════════════════════════════════════════════════════════
# CHECK GROUP 3 — TypeScript frontend: src/ + public/ + tsconfig.json
# ════════════════════════════════════════════════════════════════════

frontend_src = apps_frontend / "src"
frontend_public = apps_frontend / "public"
frontend_tsconfig = apps_frontend / "tsconfig.json"
frontend_pkg_json = apps_frontend / "package.json"

add_check(
    "frontend/src_exists",
    frontend_src.is_dir(),
    f"apps/frontend/src/ exists: {frontend_src.is_dir()}",
    weight=2.0,
)
add_check(
    "frontend/public_exists",
    frontend_public.is_dir(),
    f"apps/frontend/public/ exists (SPA): {frontend_public.is_dir()}",
    weight=1.0,
)
add_check(
    "frontend/tsconfig_exists",
    frontend_tsconfig.exists(),
    f"apps/frontend/tsconfig.json exists: {frontend_tsconfig.exists()}",
    weight=1.5,
)

# tsconfig.json must have "strict": true
tsconfig_content = read(frontend_tsconfig)
tsconfig_strict = '"strict": true' in tsconfig_content or '"strict":true' in tsconfig_content
add_check(
    "frontend/tsconfig_strict_true",
    tsconfig_strict,
    f"tsconfig.json contains strict:true: {tsconfig_strict}",
    weight=2.0,
)

add_check(
    "frontend/package_json_exists",
    frontend_pkg_json.exists(),
    f"apps/frontend/package.json exists: {frontend_pkg_json.exists()}",
    weight=1.0,
)

# ════════════════════════════════════════════════════════════════════
# CHECK GROUP 4 — Config files: .pylintrc, .editorconfig, .eslintrc.json
# Agent must place them correctly (either at monorepo root or inside each app)
# and they must have correct proprietary values.
# ════════════════════════════════════════════════════════════════════

# .pylintrc — must have max-line-length=88 (NOT 79, NOT 120)
pylintrc_candidates = list(workspace.rglob(".pylintrc"))
# exclude source/template files
pylintrc_files = [p for p in pylintrc_candidates if "assets/templates" not in str(p)]

pylintrc_found = len(pylintrc_files) > 0
add_check(
    "config/pylintrc_exists",
    pylintrc_found,
    f".pylintrc found (outside templates): {[str(p.relative_to(workspace)) for p in pylintrc_files]}",
    weight=2.0,
)

pylintrc_correct_linelen = False
if pylintrc_found:
    for pf in pylintrc_files:
        content = read(pf)
        if "max-line-length=88" in content:
            pylintrc_correct_linelen = True
            break
add_check(
    "config/pylintrc_max_line_88",
    pylintrc_correct_linelen,
    f".pylintrc has max-line-length=88 (Black standard, NOT 79 or 120): {pylintrc_correct_linelen}",
    weight=3.0,
)

# .editorconfig — must have indent_size=4 for Python and 2 for JS/TS
editorconfig_candidates = list(workspace.rglob(".editorconfig"))
editorconfig_files = [p for p in editorconfig_candidates if "assets/templates" not in str(p)]

editorconfig_found = len(editorconfig_files) > 0
add_check(
    "config/editorconfig_exists",
    editorconfig_found,
    f".editorconfig found (outside templates): {[str(p.relative_to(workspace)) for p in editorconfig_files]}",
    weight=1.5,
)

editorconfig_py_indent4 = False
editorconfig_js_indent2 = False
if editorconfig_found:
    for ef in editorconfig_files:
        content = read(ef)
        # Check for Python 4-space indent
        if re.search(r'\[.*\.py.*\]', content) and "indent_size = 4" in content:
            editorconfig_py_indent4 = True
        # Check for JS/TS 2-space indent
        if re.search(r'\[.*\.(js|ts|json).*\]', content) and "indent_size = 2" in content:
            editorconfig_js_indent2 = True

add_check(
    "config/editorconfig_py_indent_4",
    editorconfig_py_indent4,
    f".editorconfig has indent_size=4 for Python: {editorconfig_py_indent4}",
    weight=1.5,
)
add_check(
    "config/editorconfig_js_indent_2",
    editorconfig_js_indent2,
    f".editorconfig has indent_size=2 for JS/TS: {editorconfig_js_indent2}",
    weight=1.5,
)

# .eslintrc.json — must ban 'any' and use typescript plugin
eslintrc_candidates = list(workspace.rglob(".eslintrc.json"))
eslintrc_files = [p for p in eslintrc_candidates if "assets/templates" not in str(p)]

eslintrc_found = len(eslintrc_files) > 0
add_check(
    "config/eslintrc_exists",
    eslintrc_found,
    f".eslintrc.json found (outside templates): {[str(p.relative_to(workspace)) for p in eslintrc_files]}",
    weight=2.0,
)

eslintrc_no_any = False
eslintrc_ts_plugin = False
if eslintrc_found:
    for ef in eslintrc_files:
        content = read(ef)
        if "no-explicit-any" in content or "no_explicit_any" in content:
            eslintrc_no_any = True
        if "typescript-eslint" in content or "@typescript-eslint" in content:
            eslintrc_ts_plugin = True

add_check(
    "config/eslintrc_bans_any",
    eslintrc_no_any,
    f".eslintrc.json bans explicit any: {eslintrc_no_any}",
    weight=2.0,
)
add_check(
    "config/eslintrc_ts_plugin",
    eslintrc_ts_plugin,
    f".eslintrc.json uses @typescript-eslint plugin: {eslintrc_ts_plugin}",
    weight=1.0,
)

# ════════════════════════════════════════════════════════════════════
# CHECK GROUP 5 — README.md: must follow the template structure
# Must have Quick Start (both Node AND Python sections), Architecture section
# ════════════════════════════════════════════════════════════════════

readme_candidates = list(workspace.rglob("README.md"))
# exclude old_attempt and template files
readme_files = [
    p for p in readme_candidates
    if "assets/templates" not in str(p) and "old_attempt" not in str(p)
]

readme_found = len(readme_files) > 0
add_check(
    "docs/readme_exists",
    readme_found,
    f"README.md found (outside templates/old_attempt): {[str(p.relative_to(workspace)) for p in readme_files]}",
    weight=1.5,
)

readme_has_quickstart = False
readme_has_node_section = False
readme_has_python_section = False
readme_has_architecture_section = False
readme_has_project_name = False

if readme_found:
    for rf in readme_files:
        content = read(rf)
        if "Quick Start" in content or "quick start" in content.lower():
            readme_has_quickstart = True
        if "npm" in content or "Node" in content or "TypeScript" in content:
            readme_has_node_section = True
        if "python" in content.lower() or "pip" in content or "pytest" in content:
            readme_has_python_section = True
        if "Architecture" in content or "ARCHITECTURE" in content:
            readme_has_architecture_section = True
        # Must not still say "Project:" placeholder — must have actual name
        if "ClarityHealth" in content or "clarity" in content.lower() or "clarity-health" in content.lower():
            readme_has_project_name = True

add_check("docs/readme_has_quickstart", readme_has_quickstart, f"README has Quick Start section: {readme_has_quickstart}", weight=1.0)
add_check("docs/readme_has_node_section", readme_has_node_section, f"README has Node/TS section: {readme_has_node_section}", weight=0.5)
add_check("docs/readme_has_python_section", readme_has_python_section, f"README has Python section: {readme_has_python_section}", weight=0.5)
add_check("docs/readme_has_architecture_ref", readme_has_architecture_section, f"README references Architecture: {readme_has_architecture_section}", weight=1.0)
add_check("docs/readme_has_project_name", readme_has_project_name, f"README references project name (ClarityHealth): {readme_has_project_name}", weight=1.0)

# ════════════════════════════════════════════════════════════════════
# CHECK GROUP 6 — ARCHITECTURE.md: must have all required sections
# Components table, Data Flow, Deployment, Decisions (ADR-001), Diagrams (Mermaid)
# ════════════════════════════════════════════════════════════════════

arch_candidates = list(workspace.rglob("ARCHITECTURE.md"))
arch_files = [
    p for p in arch_candidates
    if "assets/templates" not in str(p) and "old_attempt" not in str(p)
]

arch_found = len(arch_files) > 0
add_check(
    "docs/architecture_md_exists",
    arch_found,
    f"ARCHITECTURE.md found (outside templates): {[str(p.relative_to(workspace)) for p in arch_files]}",
    weight=2.0,
)

arch_has_components = False
arch_has_dataflow = False
arch_has_deployment = False
arch_has_decisions_adr = False
arch_has_mermaid = False
arch_has_security_note = False
arch_has_project_name = False

if arch_found:
    for af in arch_files:
        content = read(af)
        if "## Components" in content or "| Component" in content:
            arch_has_components = True
        if "## Data Flow" in content or "Data Flow" in content:
            arch_has_dataflow = True
        if "## Deployment" in content:
            arch_has_deployment = True
        if "ADR-001" in content or ("ADR" in content and "Decision" in content.replace("Decisions", "")):
            arch_has_decisions_adr = True
        if "mermaid" in content.lower() or "```mermaid" in content:
            arch_has_mermaid = True
        # Security: must mention non-root, pinned images, or secrets in env vars
        security_terms = ["non-root", "nonroot", "secrets", ".env", "pinned", "pin base", "never in repo"]
        if any(t in content.lower() for t in security_terms):
            arch_has_security_note = True
        if "ClarityHealth" in content or "clarity" in content.lower():
            arch_has_project_name = True

add_check("docs/architecture_components_table", arch_has_components, f"ARCHITECTURE.md has Components section/table: {arch_has_components}", weight=1.5)
add_check("docs/architecture_dataflow", arch_has_dataflow, f"ARCHITECTURE.md has Data Flow section: {arch_has_dataflow}", weight=1.5)
add_check("docs/architecture_deployment", arch_has_deployment, f"ARCHITECTURE.md has Deployment section: {arch_has_deployment}", weight=1.5)
add_check("docs/architecture_adr001", arch_has_decisions_adr, f"ARCHITECTURE.md has ADR-001 decision entry: {arch_has_decisions_adr}", weight=2.0)
add_check("docs/architecture_mermaid_diagram", arch_has_mermaid, f"ARCHITECTURE.md contains Mermaid diagram: {arch_has_mermaid}", weight=2.0)
add_check("docs/architecture_security_note", arch_has_security_note, f"ARCHITECTURE.md references security constraints (secrets/non-root/pinned): {arch_has_security_note}", weight=1.5)
add_check("docs/architecture_project_name", arch_has_project_name, f"ARCHITECTURE.md references project name (ClarityHealth): {arch_has_project_name}", weight=1.0)

# ════════════════════════════════════════════════════════════════════
# CHECK GROUP 7 — Security: no secrets hardcoded, .gitignore present
# ════════════════════════════════════════════════════════════════════

# Check .gitignore exists somewhere in the monorepo (not old_attempt)
gitignore_candidates = list(workspace.rglob(".gitignore"))
gitignore_files = [p for p in gitignore_candidates if "old_attempt" not in str(p)]
add_check(
    "security/gitignore_exists",
    len(gitignore_files) > 0,
    f".gitignore found: {[str(p.relative_to(workspace)) for p in gitignore_files]}",
    weight=1.0,
)

# No hardcoded secrets in new files (check for password= or secret= patterns outside old_attempt)
suspicious_new_files = []
for f in workspace.rglob("*.py"):
    if "old_attempt" in str(f) or "assets" in str(f):
        continue
    content = read(f)
    if re.search(r'(?i)(password|secret|api_key)\s*=\s*["\'][^"\']{3,}', content):
        suspicious_new_files.append(str(f.relative_to(workspace)))

for f in workspace.rglob("*.ts"):
    content = read(f)
    if re.search(r'(?i)(password|secret|apiKey)\s*=\s*["\'][^"\']{3,}', content):
        suspicious_new_files.append(str(f.relative_to(workspace)))

add_check(
    "security/no_hardcoded_secrets",
    len(suspicious_new_files) == 0,
    f"No hardcoded secrets in new source files. Violations: {suspicious_new_files}",
    weight=1.5,
)

# ════════════════════════════════════════════════════════════════════
# SCORE COMPUTATION
# ════════════════════════════════════════════════════════════════════

score = round(passed_weight / total_weight, 4) if total_weight > 0 else 0.0
overall_passed = score >= 0.75  # Must pass at least 75% of weighted checks

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks,
}

print(json.dumps(result, indent=2))