import sys
import os
import json
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def find_project_root(workspace: Path, project_name: str) -> Path | None:
    candidate = workspace / project_name
    if candidate.is_dir():
        return candidate
    # Search one level deep
    for d in workspace.iterdir():
        if d.is_dir() and d.name == project_name:
            return d
    return None

def main():
    workspace = Path(sys.argv[1]).resolve()
    PROJECT_NAME = "drug-discovery-model"
    # Also accept underscore variant (uv may normalize)
    PROJECT_NAME_UNDER = PROJECT_NAME.replace("-", "_")

    checks = []

    # ── Locate the project directory ─────────────────────────────────────────
    project_dir = find_project_root(workspace, PROJECT_NAME)
    if project_dir is None:
        # Try underscore
        project_dir = find_project_root(workspace, PROJECT_NAME_UNDER)

    def check_project_dir_exists():
        if project_dir and project_dir.is_dir():
            return True, f"Project directory found at: {project_dir}"
        return False, f"Project directory '{PROJECT_NAME}' not found under {workspace}"

    checks.append(run_check("project_directory_exists", check_project_dir_exists))

    # If project dir missing, remaining checks will fail gracefully
    proj = project_dir if project_dir else workspace / PROJECT_NAME

    # ── src/ layout ──────────────────────────────────────────────────────────
    def check_src_layout():
        src_dir = proj / "src"
        if not src_dir.is_dir():
            return False, f"src/ directory not found inside {proj}"
        # There should be at least one Python package inside src/
        packages = [d for d in src_dir.iterdir() if d.is_dir()]
        if not packages:
            return False, "src/ exists but contains no package subdirectory"
        return True, f"src/ layout present with packages: {[p.name for p in packages]}"

    checks.append(run_check("src_layout_present", check_src_layout))

    # ── pyproject.toml exists ────────────────────────────────────────────────
    def check_pyproject_exists():
        ppt = proj / "pyproject.toml"
        if ppt.is_file():
            return True, "pyproject.toml found"
        return False, "pyproject.toml not found in project root"

    checks.append(run_check("pyproject_toml_exists", check_pyproject_exists))

    # ── pyproject.toml contains required dependencies ────────────────────────
    def check_dependencies():
        try:
            import toml
        except ImportError:
            # Fallback to raw text search
            toml = None

        ppt = proj / "pyproject.toml"
        if not ppt.is_file():
            return False, "pyproject.toml missing, cannot check dependencies"

        content = ppt.read_text()
        required = ["pandas", "numpy", "scikit-learn"]
        missing = []
        for dep in required:
            # Accept both 'dep' and 'dep>=version' forms
            if dep not in content:
                missing.append(dep)

        if missing:
            return False, f"Missing dependencies in pyproject.toml: {missing}"
        return True, f"All required dependencies found: {required}"

    checks.append(run_check("required_dependencies_in_pyproject", check_dependencies))

    # ── uv.lock exists (locked environment) ──────────────────────────────────
    def check_uv_lock():
        lock = proj / "uv.lock"
        if lock.is_file() and lock.stat().st_size > 100:
            return True, f"uv.lock found ({lock.stat().st_size} bytes)"
        if lock.is_file():
            return False, f"uv.lock exists but appears empty ({lock.stat().st_size} bytes)"
        return False, "uv.lock not found — environment was never synced/locked"

    checks.append(run_check("uv_lock_exists", check_uv_lock))

    # ── .gitignore exists ─────────────────────────────────────────────────────
    def check_gitignore():
        gi = proj / ".gitignore"
        if not gi.is_file():
            return False, ".gitignore not found"
        content = gi.read_text()
        # Should have common Python/MLOps patterns
        markers = ["__pycache__", ".venv", "*.log"]
        found = [m for m in markers if m in content]
        if len(found) >= 2:
            return True, f".gitignore present with patterns: {found}"
        return False, f".gitignore present but missing expected patterns (found only: {found})"

    checks.append(run_check("gitignore_present", check_gitignore))

    # ── .vscode/settings.json exists ─────────────────────────────────────────
    def check_vscode_settings():
        vs = proj / ".vscode" / "settings.json"
        if not vs.is_file():
            return False, ".vscode/settings.json not found"
        try:
            data = json.loads(vs.read_text())
        except json.JSONDecodeError as e:
            return False, f".vscode/settings.json is invalid JSON: {e}"
        # Must contain at least formatOnSave or python linting config (from reference)
        has_format = "editor.formatOnSave" in data or "editor.defaultFormatter" in data
        has_python = any("python" in k.lower() for k in data.keys())
        if has_format and has_python:
            return True, ".vscode/settings.json valid with formatting and Python config"
        return False, f".vscode/settings.json missing expected keys (formatOnSave={has_format}, python={has_python})"

    checks.append(run_check("vscode_settings_present", check_vscode_settings))

    # ── Git repository initialized ───────────────────────────────────────────
    def check_git_repo():
        git_dir = proj / ".git"
        if git_dir.is_dir():
            return True, ".git directory found — repository initialized"
        return False, ".git directory not found — git was not initialized"

    checks.append(run_check("git_repository_initialized", check_git_repo))

    # ── uv run python works (environment is usable) ───────────────────────────
    def check_uv_run_python():
        env = os.environ.copy()
        env["PATH"] = "/root/.local/bin:/root/.cargo/bin:" + env.get("PATH", "")
        result = subprocess.run(
            ["uv", "run", "python", "-c",
             "import pandas; import numpy; import sklearn; print('OK')"],
            cwd=str(proj),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        if result.returncode == 0 and "OK" in result.stdout:
            return True, "uv run python can import pandas, numpy, sklearn successfully"
        return False, (
            f"uv run python failed (rc={result.returncode}). "
            f"stdout: {result.stdout[:300]} stderr: {result.stderr[:300]}"
        )

    checks.append(run_check("uv_run_python_imports_work", check_uv_run_python))

    # ── Final scoring ─────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())