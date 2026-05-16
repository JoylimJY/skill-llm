import sys
import json
import ast
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── 1. Package must be created via the script → src/ layout ──
src_pkg = workspace / "src" / "churn_predictor"
has_src_layout = src_pkg.is_dir()
check(
    "src_layout_exists",
    has_src_layout,
    f"Expected src/churn_predictor/ directory. Found: {has_src_layout}"
)

# ── 2. All required subdirectories exist ──
for subdir in ["io", "domain", "application"]:
    d = src_pkg / subdir
    check(
        f"subdir_{subdir}_exists",
        d.is_dir(),
        f"src/churn_predictor/{subdir}/ {'exists' if d.is_dir() else 'MISSING'}"
    )

# ── 3. __init__.py files exist in package root and all subdirs ──
for init_path in [
    src_pkg / "__init__.py",
    src_pkg / "io" / "__init__.py",
    src_pkg / "domain" / "__init__.py",
    src_pkg / "application" / "__init__.py",
]:
    exists = init_path.is_file()
    check(
        f"init_py_{init_path.parent.name}",
        exists,
        f"{init_path.relative_to(workspace)} {'exists' if exists else 'MISSING'}"
    )

# ── 4. domain/features.py: must contain no I/O calls (pure functions only) ──
domain_features = src_pkg / "domain" / "features.py"
try:
    domain_src = domain_features.read_text()
    # Check it has some real content (not just a comment stub)
    has_function = bool(re.search(r'def\s+\w+', domain_src))
    # Must NOT import open/os/pandas read_csv/pickle etc.
    has_io = bool(re.search(r'\b(open\s*\(|os\.path|pd\.read_csv|pickle|joblib\.dump|joblib\.load|\.to_csv|\.to_parquet|requests\.)\b', domain_src))
    check(
        "domain_has_function",
        has_function,
        f"domain/features.py has at least one function def: {has_function}. Content snippet: {domain_src[:200]}"
    )
    check(
        "domain_is_pure_no_io",
        not has_io,
        f"domain/features.py must be pure (no I/O). IO found: {has_io}. Content: {domain_src[:300]}"
    )
except Exception as e:
    check("domain_features_readable", False, f"Could not read domain/features.py: {e}")

# ── 5. io/data.py: must contain I/O related functionality ──
io_data = src_pkg / "io" / "data.py"
try:
    io_src = io_data.read_text()
    has_real_io = bool(re.search(
        r'\b(open\s*\(|pd\.read_csv|pd\.read_parquet|pickle|joblib|csv|os\.path|pathlib|load|save|read|write)\b',
        io_src
    ))
    has_function_or_class = bool(re.search(r'(def\s+\w+|class\s+\w+)', io_src))
    check(
        "io_data_has_function_or_class",
        has_function_or_class,
        f"io/data.py has function or class: {has_function_or_class}. Content: {io_src[:200]}"
    )
    check(
        "io_data_has_io_operations",
        has_real_io,
        f"io/data.py should contain I/O operations. Found I/O: {has_real_io}. Content: {io_src[:300]}"
    )
except Exception as e:
    check("io_data_readable", False, f"Could not read io/data.py: {e}")

# ── 6. application/train.py: must have a main() function ──
app_train = src_pkg / "application" / "train.py"
try:
    app_src = app_train.read_text()
    has_main = bool(re.search(r'def\s+main\s*\(', app_src))
    check(
        "application_train_has_main",
        has_main,
        f"application/train.py must define main(). Found: {has_main}. Content: {app_src[:300]}"
    )
    # Application should reference/import from both domain and io layers
    references_domain = bool(re.search(r'(from\s+.*domain|import\s+.*domain|from\s+.*features|import\s+.*features)', app_src))
    references_io = bool(re.search(r'(from\s+.*io|import\s+.*io|from\s+.*data|import\s+.*data)', app_src))
    check(
        "application_wires_domain_and_io",
        references_domain and references_io,
        f"application/train.py should import from both domain and io. domain_ref={references_domain}, io_ref={references_io}"
    )
except Exception as e:
    check("application_train_readable", False, f"Could not read application/train.py: {e}")

# ── 7. pyproject.toml: must have [project.scripts] with correct entrypoint ──
pyproject_path = workspace / "pyproject.toml"
try:
    import toml
    pyproject = toml.loads(pyproject_path.read_text())
    scripts = pyproject.get("project", {}).get("scripts", {})
    
    # Check 'train' key exists
    has_train_key = "train" in scripts
    check(
        "pyproject_has_train_script_key",
        has_train_key,
        f"pyproject.toml [project.scripts] must have 'train' key. Found keys: {list(scripts.keys())}"
    )
    
    if has_train_key:
        entrypoint = scripts["train"]
        # Must be: "churn_predictor.application.train:main"
        correct_module = "churn_predictor.application.train" in entrypoint
        correct_callable = entrypoint.endswith(":main")
        check(
            "pyproject_train_entrypoint_module_path",
            correct_module,
            f"Entrypoint module path must contain 'churn_predictor.application.train'. Got: '{entrypoint}'"
        )
        check(
            "pyproject_train_entrypoint_callable",
            correct_callable,
            f"Entrypoint must end with ':main'. Got: '{entrypoint}'"
        )
    else:
        check("pyproject_train_entrypoint_module_path", False, "train key missing, cannot check entrypoint")
        check("pyproject_train_entrypoint_callable", False, "train key missing, cannot check callable")

except ImportError:
    check("pyproject_toml_parsed", False, "toml module not available")
except Exception as e:
    check("pyproject_toml_parsed", False, f"Failed to parse pyproject.toml: {e}")

# ── 8. Flat layout must NOT be used (no churn_predictor/ at root) ──
flat_pkg = workspace / "churn_predictor"
no_flat_layout = not flat_pkg.is_dir()
check(
    "no_flat_layout_at_root",
    no_flat_layout,
    f"Package must use src/ layout, not flat layout. Flat dir at root exists: {not no_flat_layout}"
)

# ── Final scoring ──
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
overall = passed_count == total

result = {
    "passed": overall,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))