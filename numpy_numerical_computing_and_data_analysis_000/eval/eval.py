import sys
import json
import traceback
from pathlib import Path

def fail(checks, name, detail):
    checks.append({"name": name, "passed": False, "detail": detail})

def succeed(checks, name, detail):
    checks.append({"name": name, "passed": True, "detail": detail})

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # ── 1. Locate the distance matrix file ──────────────────────────────────
    dist_files = list(workspace.rglob("distance_matrix.npy"))
    if not dist_files:
        fail(checks, "distance_matrix_exists", "No file named 'distance_matrix.npy' found anywhere in workspace.")
        return checks
    dist_path = dist_files[0]
    succeed(checks, "distance_matrix_exists", f"Found at {dist_path}")

    # ── 2. Load and validate distance matrix shape ───────────────────────────
    try:
        import numpy as np
        dist_mat = np.load(str(dist_path))
    except Exception as e:
        fail(checks, "distance_matrix_loadable", f"Could not load distance_matrix.npy: {e}")
        return checks
    succeed(checks, "distance_matrix_loadable", "Loaded successfully.")

    if dist_mat.shape != (8, 6):
        fail(checks, "distance_matrix_shape",
             f"Expected shape (8, 6) [8 sensors A × 6 sensors B], got {dist_mat.shape}")
    else:
        succeed(checks, "distance_matrix_shape", f"Shape is correct: (8, 6)")

    # ── 3. Validate distance matrix values (Euclidean distances) ─────────────
    # Recompute reference using vectorized broadcasting (ground truth)
    try:
        import csv
        def load_sensor_csv(path):
            rows = []
            with open(path) as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                for row in reader:
                    rows.append([float(x) for x in row[1:]])
            return np.array(rows, dtype=np.float64)

        a_data = load_sensor_csv(str(workspace / "plant_data/line_A/raw/sensor_group_A.csv"))
        b_data = load_sensor_csv(str(workspace / "plant_data/line_B/raw/sensor_group_B.csv"))

        # Reference: Euclidean distance between each pair of sensor time-series
        # a_data shape: (8, 120), b_data shape: (6, 120)
        # Expected: dist[i,j] = ||a[i] - b[j]||_2
        ref_dist = np.sqrt(np.sum((a_data[:, np.newaxis, :] - b_data[np.newaxis, :, :]) ** 2, axis=2))
        # ref_dist shape: (8, 6)

        if dist_mat.shape == (8, 6):
            max_err = np.max(np.abs(dist_mat.astype(np.float64) - ref_dist))
            if max_err < 0.5:  # allow float32 rounding
                succeed(checks, "distance_matrix_values",
                        f"Values match expected Euclidean distances (max error={max_err:.6f})")
            else:
                fail(checks, "distance_matrix_values",
                     f"Values deviate from expected Euclidean distances (max error={max_err:.4f}). "
                     f"Sample agent[0,0]={dist_mat[0,0]:.4f} vs ref={ref_dist[0,0]:.4f}")
        else:
            fail(checks, "distance_matrix_values", "Skipped due to wrong shape.")
    except Exception as e:
        fail(checks, "distance_matrix_values", f"Error during reference computation: {e}\n{traceback.format_exc()}")

    # ── 4. Locate eigenvalues file ───────────────────────────────────────────
    eig_files = list(workspace.rglob("dominant_eigenvalues.npy"))
    if not eig_files:
        fail(checks, "eigenvalues_exists", "No file named 'dominant_eigenvalues.npy' found anywhere in workspace.")
        return checks
    eig_path = eig_files[0]
    succeed(checks, "eigenvalues_exists", f"Found at {eig_path}")

    # ── 5. Load eigenvalues ──────────────────────────────────────────────────
    try:
        eig_vals = np.load(str(eig_path))
    except Exception as e:
        fail(checks, "eigenvalues_loadable", f"Could not load dominant_eigenvalues.npy: {e}")
        return checks
    succeed(checks, "eigenvalues_loadable", "Loaded successfully.")

    # ── 6. dtype must be float32 ─────────────────────────────────────────────
    if eig_vals.dtype == np.float32:
        succeed(checks, "eigenvalues_dtype_float32", f"dtype is float32 as required.")
    else:
        fail(checks, "eigenvalues_dtype_float32",
             f"Expected dtype=float32 (compact storage), got dtype={eig_vals.dtype}. "
             f"The SKILL.md requires choosing the smallest appropriate dtype.")

    # ── 7. Values must all be positive reals ────────────────────────────────
    if np.all(eig_vals > 0):
        succeed(checks, "eigenvalues_positive", "All stored eigenvalues are positive (correct filtering).")
    else:
        fail(checks, "eigenvalues_positive",
             f"Some eigenvalues are non-positive: {eig_vals[eig_vals <= 0]}. "
             f"Only positive real eigenvalues should be retained.")

    if not np.any(np.iscomplex(eig_vals)):
        succeed(checks, "eigenvalues_real", "Eigenvalues are real-valued (complex part correctly discarded).")
    else:
        fail(checks, "eigenvalues_real", "Eigenvalues contain complex entries; .real must be extracted first.")

    # ── 8. Validate eigenvalue computation ───────────────────────────────────
    # The covariance-like matrix should be built from the distance matrix:
    # C = dist_mat.T @ dist_mat  (shape 6×6) OR dist_mat @ dist_mat.T (shape 8×8)
    # Either is acceptable; we check that the positive real eigs are a subset of
    # np.linalg.eig of either product matrix.
    try:
        if dist_mat.shape == (8, 6):
            ref_dm = ref_dist  # use our trusted reference
            # Try both: (6×6) and (8×8) covariance products
            candidates = []
            for cov in [ref_dm.T @ ref_dm, ref_dm @ ref_dm.T]:
                raw_eigs = np.linalg.eig(cov)[0]
                pos_real = np.sort(raw_eigs.real[raw_eigs.real > 0])[::-1]
                candidates.append(pos_real)

            agent_sorted = np.sort(eig_vals.astype(np.float64))[::-1]
            matched = False
            for ref_eigs in candidates:
                min_len = min(len(agent_sorted), len(ref_eigs))
                if min_len == 0:
                    continue
                err = np.max(np.abs(agent_sorted[:min_len] - ref_eigs[:min_len]))
                if err < 1.0 and len(agent_sorted) == len(ref_eigs):
                    matched = True
                    break
                elif err < 1.0 and len(agent_sorted) <= len(ref_eigs):
                    # agent may have filtered more aggressively — still acceptable
                    matched = True
                    break
            if matched:
                succeed(checks, "eigenvalues_correct_computation",
                        "Eigenvalue values are consistent with np.linalg.eig of a valid covariance product matrix.")
            else:
                detail_parts = []
                for i, c in enumerate(candidates):
                    detail_parts.append(f"candidate_{i}={c[:4]}")
                fail(checks, "eigenvalues_correct_computation",
                     f"Eigenvalues don't match expected positive-real eigs from covariance product. "
                     f"Agent values (sorted desc): {agent_sorted[:6]}. "
                     f"References: {'; '.join(detail_parts)}")
        else:
            fail(checks, "eigenvalues_correct_computation",
                 "Skipped because distance_matrix shape was wrong.")
    except Exception as e:
        fail(checks, "eigenvalues_correct_computation",
             f"Error during eigenvalue reference check: {e}\n{traceback.format_exc()}")

    # ── 9. No-loop bonus check (inspect Python source if agent saved it) ─────
    # Look for any .py file the agent may have written and check for for-loops
    py_files = list(workspace.rglob("*.py"))
    loop_found = False
    loop_detail = "No Python source files found to inspect."
    for pf in py_files:
        try:
            src = pf.read_text(errors="replace")
            # Check for naked for-loops iterating over sensor data
            import re
            # Heuristic: "for" followed by variable in data-ish context
            if re.search(r'\bfor\b\s+\w+\s+in\b', src):
                # Check if it's array-level (not just enumerate/zip in setup)
                suspicious = re.findall(r'for\s+\w+\s+in\s+(?!zip|enumerate|range|open|csv|os|glob|Path)\w+', src)
                if suspicious:
                    loop_found = True
                    loop_detail = f"Suspicious loops in {pf.name}: {suspicious[:3]}"
                    break
        except Exception:
            pass
    if not loop_found:
        succeed(checks, "vectorized_no_array_loops",
                "No suspicious array-level Python loops detected in agent's source code.")
    else:
        fail(checks, "vectorized_no_array_loops",
             f"Vectorization rule violated — Python loops found for array operations. {loop_detail}")

    return checks


def main():
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks = evaluate(workspace_dir)
    except Exception as e:
        checks = [{"name": "eval_crashed", "passed": False, "detail": str(e)}]

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    overall = score >= 0.8  # need ≥80% checks to pass

    result = {
        "passed": overall,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()