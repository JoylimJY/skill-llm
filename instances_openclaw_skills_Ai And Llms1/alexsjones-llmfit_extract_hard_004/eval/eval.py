import json
import os
from pathlib import Path


def normalize_text(s):
    try:
        import re
        s = s.lower()
        s = re.sub(r"[^a-z0-9]+", "", s)
        return s
    except Exception:
        return ""


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None, str(e)


checks = []
workspace = Path(os.sys.argv[1]) if len(os.sys.argv) > 1 else Path.cwd()

# Check 1: output files exist
for filename in ["system.json", "recommendations.json"]:
    try:
        exists = (workspace / filename).exists()
        checks.append({
            "name": f"{filename} exists",
            "passed": bool(exists),
            "detail": "found" if exists else f"missing: {filename}",
        })
    except Exception as e:
        checks.append({
            "name": f"{filename} exists",
            "passed": False,
            "detail": f"error checking existence: {e}",
        })

# Check 2: system.json structure
try:
    p = workspace / "system.json"
    if not p.exists():
        checks.append({"name": "system.json valid JSON", "passed": False, "detail": "missing file"})
    else:
        try:
            data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            system = data.get("system", {}) if isinstance(data, dict) else {}
            has_cpu = bool(system.get("cpu_name"))
            has_ram = isinstance(system.get("total_ram_gb"), (int, float)) or isinstance(system.get("total_ram_gb"), str)
            checks.append({
                "name": "system.json valid JSON",
                "passed": bool(isinstance(data, dict) and isinstance(system, dict) and has_cpu and has_ram),
                "detail": "contains system summary" if has_cpu else "missing expected system fields",
            })
        except Exception as e:
            checks.append({"name": "system.json valid JSON", "passed": False, "detail": f"parse error: {e}"})
except Exception as e:
    checks.append({"name": "system.json valid JSON", "passed": False, "detail": f"unexpected error: {e}"})

# Check 3: recommendations.json structure
try:
    p = workspace / "recommendations.json"
    if not p.exists():
        checks.append({"name": "recommendations.json valid JSON", "passed": False, "detail": "missing file"})
    else:
        try:
            data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            models = data.get("models", []) if isinstance(data, dict) else []
            ok = isinstance(models, list) and len(models) > 0
            checks.append({
                "name": "recommendations.json valid JSON",
                "passed": bool(ok),
                "detail": f"models_count={len(models) if isinstance(models, list) else 'n/a'}",
            })
        except Exception as e:
            checks.append({"name": "recommendations.json valid JSON", "passed": False, "detail": f"parse error: {e}"})
except Exception as e:
    checks.append({"name": "recommendations.json valid JSON", "passed": False, "detail": f"unexpected error: {e}"})

# Check 4: coding use-case present in recommendations (fuzzy)
try:
    p = workspace / "recommendations.json"
    if not p.exists():
        checks.append({"name": "coding use-case recommendations", "passed": False, "detail": "missing file"})
    else:
        try:
            data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            models = data.get("models", []) if isinstance(data, dict) else []
            found = False
            detail = "no models"
            if isinstance(models, list):
                for m in models:
                    if isinstance(m, dict):
                        use_case = normalize_text(str(m.get("use_case", "")))
                        name = normalize_text(str(m.get("name", "")))
                        if "coding" in use_case or "coder" in name:
                            found = True
                            detail = f"matched model {m.get('name', 'unknown')}"
                            break
            checks.append({"name": "coding use-case recommendations", "passed": found, "detail": detail})
        except Exception as e:
            checks.append({"name": "coding use-case recommendations", "passed": False, "detail": f"parse error: {e}"})
except Exception as e:
    checks.append({"name": "coding use-case recommendations", "passed": False, "detail": f"unexpected error: {e}"})

passed_count = sum(1 for c in checks if c.get("passed"))
score = passed_count / len(checks) if checks else 0.0
result = {
    "passed": passed_count == len(checks) and len(checks) > 0,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, indent=2))
