import json
import os
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def main():
    import sys
    workspace = Path(sys.argv[1])
    checks = []
    total = 0
    passed_count = 0

    def add_check(name, passed, detail):
        nonlocal total, passed_count
        total += 1
        if passed:
            passed_count += 1
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    # Check 1: input marker exists
    try:
        desc_path = workspace / "description.txt"
        if not desc_path.exists():
            add_check("input_marker", False, "description.txt is missing")
        else:
            text = desc_path.read_text(encoding='utf-8', errors='ignore')
            ok = "rocket_task_marker_v1" in text.lower()
            add_check("input_marker", ok, "marker found" if ok else "marker not found in description.txt")
    except Exception as e:
        add_check("input_marker", False, f"error reading description.txt: {e}")

    # Check 2: output STL exists
    try:
        out_dir = workspace / "outputs"
        stls = list(out_dir.glob("*.stl")) if out_dir.exists() else []
        ok = len(stls) >= 1
        add_check("stl_exists", ok, f"found {len(stls)} STL file(s)" if ok else "no STL file found in outputs/")
    except Exception as e:
        add_check("stl_exists", False, f"error checking outputs/: {e}")

    # Check 3: output STL is non-empty and parsable by trimesh
    try:
        import trimesh
        out_dir = workspace / "outputs"
        stls = list(out_dir.glob("*.stl")) if out_dir.exists() else []
        if not stls:
            add_check("stl_valid", False, "cannot validate because no STL file exists")
        else:
            path = stls[0]
            size_ok = path.stat().st_size > 0
            if not size_ok:
                add_check("stl_valid", False, "STL file is empty")
            else:
                try:
                    mesh = trimesh.load(path, force='mesh')
                    ok = mesh is not None and hasattr(mesh, 'faces') and len(mesh.faces) > 0
                    add_check("stl_valid", ok, f"loaded mesh with {len(mesh.faces) if ok else 0} faces" if ok else "failed to load a valid mesh")
                except Exception as e:
                    add_check("stl_valid", False, f"trimesh failed to load STL: {e}")
    except Exception as e:
        add_check("stl_valid", False, f"validation error: {e}")

    # Check 4: output filename should mention rocket (fuzzy)
    try:
        out_dir = workspace / "outputs"
        stls = list(out_dir.glob("*.stl")) if out_dir.exists() else []
        if not stls:
            add_check("filename_fuzzy", False, "no STL file to inspect")
        else:
            name = stls[0].name.lower().replace("-", "_").replace(" ", "_")
            ok = "rocket" in name
            add_check("filename_fuzzy", ok, f"filename={stls[0].name}" if ok else f"filename does not look rocket-related: {stls[0].name}")
    except Exception as e:
        add_check("filename_fuzzy", False, f"error checking filename: {e}")

    result = {
        "passed": passed_count == total and total > 0,
        "score": (passed_count / total) if total else 0.0,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
