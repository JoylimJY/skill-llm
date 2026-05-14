import sys
import json
import csv
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Check 1: trajectory_data.csv exists anywhere in the workspace ─────────
    found_files = list(workspace_path.rglob("trajectory_data.csv"))
    csv_found = len(found_files) > 0
    checks.append({
        "name": "trajectory_data.csv exists",
        "passed": csv_found,
        "detail": f"Found at: {found_files[0]}" if csv_found else "File 'trajectory_data.csv' not found anywhere in the workspace."
    })

    if not csv_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    csv_path = found_files[0]

    # ── Check 2: CSV has correct headers (timestep, vx, vy) ─────────────────
    try:
        with open(csv_path, newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
        # Normalize: strip whitespace, lowercase
        normalized_header = [h.strip().lower() for h in header]
        expected_headers = ["timestep", "vx", "vy"]
        headers_correct = normalized_header == expected_headers
        checks.append({
            "name": "CSV has correct headers: timestep, vx, vy",
            "passed": headers_correct,
            "detail": f"Found headers: {header}" if not headers_correct else f"Headers are correct: {header}"
        })
    except Exception as e:
        checks.append({
            "name": "CSV has correct headers: timestep, vx, vy",
            "passed": False,
            "detail": f"Error reading CSV headers: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 3: CSV has correct number of rows (100 timesteps from N_STEPS=int(5.0/0.05)) ─
    try:
        with open(csv_path, newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
        # rows[0] is header; data rows are rows[1:]
        data_rows = rows[1:]
        n_rows = len(data_rows)
        # Expected: T_TOTAL=5.0, DT=0.05 => N_STEPS=100
        expected_steps = 100
        rows_correct = n_rows == expected_steps
        checks.append({
            "name": f"CSV has exactly {expected_steps} data rows (timesteps)",
            "passed": rows_correct,
            "detail": f"Found {n_rows} data rows; expected {expected_steps}."
        })
    except Exception as e:
        checks.append({
            "name": f"CSV has exactly 100 data rows (timesteps)",
            "passed": False,
            "detail": f"Error reading CSV rows: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 4: All timestep values are sequential integers 0..99 ───────────
    try:
        timesteps = [int(row[0].strip()) for row in data_rows]
        sequential = timesteps == list(range(expected_steps))
        checks.append({
            "name": "Timestep column contains sequential integers 0 to 99",
            "passed": sequential,
            "detail": f"First 5 timesteps: {timesteps[:5]}, last 5: {timesteps[-5:]}" if not sequential else "All timesteps are sequential."
        })
    except Exception as e:
        checks.append({
            "name": "Timestep column contains sequential integers 0 to 99",
            "passed": False,
            "detail": f"Error parsing timestep column: {e}"
        })

    # ── Check 5: vx and vy are valid floats, non-trivially non-zero ──────────
    try:
        vx_vals = [float(row[1].strip()) for row in data_rows]
        vy_vals = [float(row[2].strip()) for row in data_rows]
        # Check non-trivial: not all zeros, has variance
        vx_nonzero = any(abs(v) > 1e-6 for v in vx_vals)
        vy_nonzero = any(abs(v) > 1e-6 for v in vy_vals)
        floats_valid = vx_nonzero and vy_nonzero
        checks.append({
            "name": "vx and vy columns contain non-trivial float values",
            "passed": floats_valid,
            "detail": (
                f"vx range: [{min(vx_vals):.4f}, {max(vx_vals):.4f}], "
                f"vy range: [{min(vy_vals):.4f}, {max(vy_vals):.4f}]"
            )
        })
    except Exception as e:
        checks.append({
            "name": "vx and vy columns contain non-trivial float values",
            "passed": False,
            "detail": f"Error parsing vx/vy columns: {e}"
        })

    # ── Check 6: Values match the deterministic neuralink-decoder output ─────
    # Re-run the decoder ourselves and compare first 5 and last 5 rows
    try:
        import subprocess
        result = subprocess.run(
            ["neuralink-decoder", "decode"],
            capture_output=True, text=True, timeout=30
        )
        reference_lines = [
            line.strip() for line in result.stdout.splitlines()
            if line.strip() and not line.startswith("=") and not line.startswith("-")
            and not line.strip().startswith("Timesteps") and not line.strip().startswith("timestep")
        ]
        # Parse reference output: each line is "timestep  vx  vy"
        ref_data = []
        for line in reference_lines:
            parts = line.split()
            if len(parts) == 3:
                try:
                    ref_data.append((int(parts[0]), float(parts[1]), float(parts[2])))
                except ValueError:
                    pass

        if len(ref_data) == expected_steps:
            # Compare first 5 rows
            mismatches = 0
            for i in range(min(5, len(ref_data))):
                ref_t, ref_vx, ref_vy = ref_data[i]
                agent_t = int(data_rows[i][0].strip())
                agent_vx = float(data_rows[i][1].strip())
                agent_vy = float(data_rows[i][2].strip())
                if abs(agent_vx - ref_vx) > 1e-3 or abs(agent_vy - ref_vy) > 1e-3:
                    mismatches += 1

            values_match = mismatches == 0
            checks.append({
                "name": "CSV values match deterministic neuralink-decoder output",
                "passed": values_match,
                "detail": (
                    f"First 5 rows matched." if values_match
                    else f"{mismatches}/5 rows had significant numerical differences."
                )
            })
        else:
            checks.append({
                "name": "CSV values match deterministic neuralink-decoder output",
                "passed": False,
                "detail": f"Reference decoder produced {len(ref_data)} rows; could not compare."
            })
    except Exception as e:
        checks.append({
            "name": "CSV values match deterministic neuralink-decoder output",
            "passed": False,
            "detail": f"Could not run reference decoder for comparison: {e}"
        })

    # ── Score aggregation ─────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))