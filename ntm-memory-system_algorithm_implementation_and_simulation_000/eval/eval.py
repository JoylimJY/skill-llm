import sys
import json
import math
import numpy as np
from pathlib import Path

def softmax(x):
    x = np.array(x, dtype=float)
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

def cosine_similarity(a, b):
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

def content_addressing(memory, key, beta):
    """Compute content-based addressing weights."""
    memory = np.array(memory, dtype=float)
    key = np.array(key, dtype=float)
    sims = np.array([cosine_similarity(key, memory[i]) for i in range(len(memory))])
    return softmax(sims * beta)

def circular_convolution(weights, shift_weights):
    """Circular convolution for location-based shift."""
    N = len(weights)
    S = len(shift_weights)  # typically 3: [-1, 0, +1]
    result = np.zeros(N)
    half = S // 2
    for i in range(N):
        for j, sw in enumerate(shift_weights):
            idx = (i - (j - half)) % N
            result[i] += weights[idx] * sw
    return result

def sharpen(weights, gamma):
    """Sharpening: w^gamma / sum(w^gamma)"""
    w = np.array(weights, dtype=float)
    powered = np.power(np.abs(w), gamma)
    s = powered.sum()
    if s == 0:
        return w
    return powered / s

def hybrid_addressing(memory, key, beta, prev_weights, gate, shift_weights, gamma):
    """Full hybrid addressing pipeline from SKILL.md."""
    # 1. Content addressing
    content_w = content_addressing(memory, key, beta)
    # 2. Interpolation gate
    prev = np.array(prev_weights, dtype=float)
    interpolated = gate * content_w + (1 - gate) * prev
    # 3. Circular convolution (location shift)
    shifted = circular_convolution(interpolated, shift_weights)
    # 4. Sharpening
    final_w = sharpen(shifted, gamma)
    return final_w

def ntm_read(memory, weights):
    """Weighted sum read."""
    memory = np.array(memory, dtype=float)
    weights = np.array(weights, dtype=float)
    return weights @ memory  # shape (M,)

def ntm_write(memory, weights, erase, add):
    """NTM write: m_t(i) = m_{t-1}(i) * (1 - w(i)*e(j)) + w(i)*a(j)"""
    memory = np.array(memory, dtype=float)
    weights = np.array(weights, dtype=float)
    erase = np.array(erase, dtype=float)
    add = np.array(add, dtype=float)
    N, M = memory.shape
    new_memory = np.zeros_like(memory)
    for i in range(N):
        for j in range(M):
            new_memory[i, j] = memory[i, j] * (1 - weights[i] * erase[j]) + weights[i] * add[j]
    return new_memory

def compute_reference(task_spec):
    """Compute the ground-truth reference output."""
    memory = np.array(task_spec["initial_memory"], dtype=float)
    results = {}

    op1 = task_spec["operations"][0]
    ap1 = op1["addressing_params"]
    w1 = hybrid_addressing(
        memory,
        ap1["key"],
        ap1["beta"],
        ap1["prev_weights"],
        ap1["interpolation_gate"],
        ap1["shift_weights"],
        ap1["gamma"]
    )
    results["op1_weights"] = w1.tolist()

    # Write
    wp = op1["write_params"]
    memory_after_write = ntm_write(memory, w1, wp["erase"], wp["add"])
    results["memory_after_op1"] = memory_after_write.tolist()

    # Read after write
    read1 = ntm_read(memory_after_write, w1)
    results["op1_read_vector"] = read1.tolist()

    # Operation 2: read only on updated memory
    op2 = task_spec["operations"][1]
    ap2 = op2["addressing_params"]
    w2 = hybrid_addressing(
        memory_after_write,
        ap2["key"],
        ap2["beta"],
        ap2["prev_weights"],
        ap2["interpolation_gate"],
        ap2["shift_weights"],
        ap2["gamma"]
    )
    results["op2_weights"] = w2.tolist()
    read2 = ntm_read(memory_after_write, w2)
    results["op2_read_vector"] = read2.tolist()

    return results

def allclose(a, b, atol=1e-4):
    try:
        return np.allclose(np.array(a, dtype=float), np.array(b, dtype=float), atol=atol)
    except Exception:
        return False

def run_eval(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # Load task spec
    task_spec_path = workspace / "ntm_task_spec.json"
    try:
        with open(task_spec_path) as f:
            task_spec = json.load(f)
    except Exception as e:
        checks.append({"name": "load_task_spec", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "load_task_spec", "passed": True, "detail": "Task spec loaded."})

    # Compute reference
    ref = compute_reference(task_spec)

    # Find agent output file
    output_files = list(workspace.rglob("ntm_simulation_result.json"))
    if not output_files:
        checks.append({"name": "find_output_file", "passed": False, "detail": "ntm_simulation_result.json not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    output_path = output_files[0]
    checks.append({"name": "find_output_file", "passed": True, "detail": f"Found at {output_path}"})

    try:
        with open(output_path) as f:
            agent_output = json.load(f)
    except Exception as e:
        checks.append({"name": "parse_output_file", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "parse_output_file", "passed": True, "detail": "JSON parsed."})

    # Check 1: op1 addressing weights
    try:
        agent_w1 = agent_output.get("op1_weights") or agent_output.get("operations", [{}])[0].get("weights")
        passed = allclose(agent_w1, ref["op1_weights"])
        checks.append({
            "name": "op1_addressing_weights",
            "passed": passed,
            "detail": f"Expected ~{[round(x,5) for x in ref['op1_weights']]}, got {agent_w1}"
        })
    except Exception as e:
        checks.append({"name": "op1_addressing_weights", "passed": False, "detail": str(e)})

    # Check 2: memory after write (op1)
    try:
        agent_mem = agent_output.get("memory_after_op1") or agent_output.get("operations", [{}])[0].get("memory_after_write")
        passed = allclose(agent_mem, ref["memory_after_op1"])
        ref_flat = [round(x, 5) for row in ref["memory_after_op1"] for x in row]
        checks.append({
            "name": "memory_after_op1_write",
            "passed": passed,
            "detail": f"Expected flat ~{ref_flat[:6]}..., got {str(agent_mem)[:120]}"
        })
    except Exception as e:
        checks.append({"name": "memory_after_op1_write", "passed": False, "detail": str(e)})

    # Check 3: op1 read vector
    try:
        agent_r1 = agent_output.get("op1_read_vector") or agent_output.get("operations", [{}])[0].get("read_vector")
        passed = allclose(agent_r1, ref["op1_read_vector"])
        checks.append({
            "name": "op1_read_vector",
            "passed": passed,
            "detail": f"Expected ~{[round(x,5) for x in ref['op1_read_vector']]}, got {agent_r1}"
        })
    except Exception as e:
        checks.append({"name": "op1_read_vector", "passed": False, "detail": str(e)})

    # Check 4: op2 addressing weights
    try:
        agent_w2 = agent_output.get("op2_weights") or agent_output.get("operations", [{}, {}])[1].get("weights")
        passed = allclose(agent_w2, ref["op2_weights"])
        checks.append({
            "name": "op2_addressing_weights",
            "passed": passed,
            "detail": f"Expected ~{[round(x,5) for x in ref['op2_weights']]}, got {agent_w2}"
        })
    except Exception as e:
        checks.append({"name": "op2_addressing_weights", "passed": False, "detail": str(e)})

    # Check 5: op2 read vector
    try:
        agent_r2 = agent_output.get("op2_read_vector") or agent_output.get("operations", [{}, {}])[1].get("read_vector")
        passed = allclose(agent_r2, ref["op2_read_vector"])
        checks.append({
            "name": "op2_read_vector",
            "passed": passed,
            "detail": f"Expected ~{[round(x,5) for x in ref['op2_read_vector']]}, got {agent_r2}"
        })
    except Exception as e:
        checks.append({"name": "op2_read_vector", "passed": False, "detail": str(e)})

    # Score
    core_checks = [c for c in checks if c["name"] not in ("load_task_spec", "find_output_file", "parse_output_file")]
    passed_count = sum(1 for c in core_checks if c["passed"])
    score = passed_count / max(len(core_checks), 1)
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))