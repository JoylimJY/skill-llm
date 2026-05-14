import json
import sys
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # Find the output file
    output_file = None
    candidates = list(Path(workspace).rglob("structure.json"))
    if candidates:
        output_file = candidates[0]

    # CHECK 1: File exists
    file_exists = output_file is not None and output_file.exists()
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found structure.json at {output_file}" if file_exists else "structure.json not found anywhere in workspace"
    })
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}

    # CHECK 2: Valid JSON
    try:
        with open(output_file, "r") as f:
            data = json.load(f)
        valid_json = True
        checks.append({"name": "valid_json", "passed": True, "detail": "File contains valid JSON"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # CHECK 3: Root node schema — must have name, type, children (from skill's JSON schema)
    try:
        has_name = "name" in data
        has_type = "type" in data and data["type"] == "directory"
        has_children = "children" in data and isinstance(data["children"], list)
        schema_ok = has_name and has_type and has_children
        checks.append({
            "name": "root_node_schema",
            "passed": schema_ok,
            "detail": f"Root has name={has_name}, type=directory={has_type}, children={has_children}. Actual keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}"
        })
    except Exception as e:
        checks.append({"name": "root_node_schema", "passed": False, "detail": f"Schema check error: {e}"})
        schema_ok = False

    # CHECK 4: Root name corresponds to the target directory (legacy-payments-module)
    try:
        root_name = data.get("name", "")
        # Accept either the basename or the full path ending with the module name
        is_correct_target = "legacy-payments-module" in root_name
        checks.append({
            "name": "correct_target_directory",
            "passed": is_correct_target,
            "detail": f"Root node name is '{root_name}', expected to contain 'legacy-payments-module'"
        })
    except Exception as e:
        checks.append({"name": "correct_target_directory", "passed": False, "detail": f"Error: {e}"})
        is_correct_target = False

    # CHECK 5: Depth is limited to 2 levels
    # At depth=2: root (depth 0) -> L1 dirs (depth 1) -> L2 dirs/files (depth 2) -> children of L2 should be empty []
    # Verify that L2 subdirectories have empty children (depth cut-off)
    try:
        depth_correctly_limited = True
        detail_msgs = []

        def check_depth(node, current_depth, max_allowed_depth):
            nonlocal depth_correctly_limited
            if not isinstance(node, dict):
                return
            if node.get("type") == "directory":
                children = node.get("children", [])
                if current_depth >= max_allowed_depth:
                    # At max depth, children should be empty (no further expansion)
                    if len(children) > 0:
                        depth_correctly_limited = False
                        detail_msgs.append(f"Node '{node.get('name')}' at depth {current_depth} has {len(children)} children but should have none (depth limit exceeded)")
                else:
                    for child in children:
                        check_depth(child, current_depth + 1, max_allowed_depth)

        # Root is depth 0, max_allowed_depth=2 means children at depth 2 should be empty
        check_depth(data, 0, 2)

        checks.append({
            "name": "depth_limited_to_2",
            "passed": depth_correctly_limited,
            "detail": "Depth correctly limited to 2" if depth_correctly_limited else f"Depth not correctly limited: {'; '.join(detail_msgs[:3])}"
        })
    except Exception as e:
        checks.append({"name": "depth_limited_to_2", "passed": False, "detail": f"Depth check error: {e}"})
        depth_correctly_limited = False

    # CHECK 6: Expected L1 directories are present as children
    try:
        expected_l1 = {"src", "config", "tests", "docs", "scripts", "vendor"}
        l1_names = set()
        for child in data.get("children", []):
            if isinstance(child, dict):
                l1_names.add(child.get("name", ""))
        found_l1 = expected_l1.intersection(l1_names)
        l1_ok = len(found_l1) >= 5  # at least 5 of 6 expected
        checks.append({
            "name": "l1_directories_present",
            "passed": l1_ok,
            "detail": f"Found L1 dirs: {sorted(found_l1)} (expected {sorted(expected_l1)})"
        })
    except Exception as e:
        checks.append({"name": "l1_directories_present", "passed": False, "detail": f"Error: {e}"})
        l1_ok = False

    # CHECK 7: L2 directories appear as children of L1 (not cut off too early)
    try:
        l2_found = False
        for child in data.get("children", []):
            if isinstance(child, dict) and child.get("name") == "src":
                src_children = child.get("children", [])
                src_names = {c.get("name") for c in src_children if isinstance(c, dict)}
                if {"handlers", "models", "utils"}.issubset(src_names):
                    l2_found = True
                    break
        checks.append({
            "name": "l2_directories_present",
            "passed": l2_found,
            "detail": "L2 directories (handlers, models, utils under src) found" if l2_found else "L2 directories not found — depth may be too shallow or target is wrong"
        })
    except Exception as e:
        checks.append({"name": "l2_directories_present", "passed": False, "detail": f"Error: {e}"})
        l2_found = False

    # CHECK 8: L3 directories/files are NOT present (depth=2 cuts them off)
    try:
        l3_not_present = True
        detail_l3 = []
        for child in data.get("children", []):
            if isinstance(child, dict) and child.get("name") == "src":
                for l2_child in child.get("children", []):
                    if isinstance(l2_child, dict) and l2_child.get("name") == "handlers":
                        # At depth=2, handlers' children should be empty
                        handlers_children = l2_child.get("children", [])
                        if len(handlers_children) > 0:
                            l3_not_present = False
                            detail_l3.append(f"handlers has {len(handlers_children)} children at depth 2 (should be 0)")
        checks.append({
            "name": "l3_content_excluded",
            "passed": l3_not_present,
            "detail": "L3 content correctly excluded" if l3_not_present else f"L3 content present: {detail_l3}"
        })
    except Exception as e:
        checks.append({"name": "l3_content_excluded", "passed": False, "detail": f"Error: {e}"})
        l3_not_present = True  # can't verify, don't penalize

    # CHECK 9: child nodes have correct schema (name + type fields)
    try:
        schema_correct = True
        def check_schema(node):
            nonlocal schema_correct
            if not isinstance(node, dict):
                schema_correct = False
                return
            if "name" not in node or "type" not in node:
                schema_correct = False
                return
            if node.get("type") not in ("file", "directory"):
                schema_correct = False
                return
            for child in node.get("children", []):
                check_schema(child)
        check_schema(data)
        checks.append({
            "name": "child_node_schema_correct",
            "passed": schema_correct,
            "detail": "All nodes have correct name/type schema" if schema_correct else "Some nodes missing name or type fields"
        })
    except Exception as e:
        checks.append({"name": "child_node_schema_correct", "passed": False, "detail": f"Error: {e}"})
        schema_correct = False

    # Compute score
    scored_checks = [
        "output_file_exists",
        "valid_json",
        "root_node_schema",
        "correct_target_directory",
        "depth_limited_to_2",
        "l1_directories_present",
        "l2_directories_present",
        "l3_content_excluded",
        "child_node_schema_correct",
    ]
    weights = {
        "output_file_exists": 0.10,
        "valid_json": 0.10,
        "root_node_schema": 0.15,
        "correct_target_directory": 0.15,
        "depth_limited_to_2": 0.15,
        "l1_directories_present": 0.10,
        "l2_directories_present": 0.10,
        "l3_content_excluded": 0.10,
        "child_node_schema_correct": 0.05,
    }
    score = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)

    all_critical = all(
        c["passed"] for c in checks
        if c["name"] in {"output_file_exists", "valid_json", "correct_target_directory", "depth_limited_to_2", "root_node_schema"}
    )

    return {
        "passed": all_critical and score >= 0.75,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))