import os
import json
import numpy as np

np.random.seed(42)

workspace = "/workspace"

# --- Create distractor directory structure ---
dirs = [
    "experiments/run_001/logs",
    "experiments/run_002/checkpoints",
    "experiments/run_003/outputs",
    "src/models/lstm",
    "src/models/transformer",
    "src/utils",
    "src/data",
    "tests/unit",
    "tests/integration",
    "docs/references",
    "configs/deprecated",
    "memory/snapshots",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "experiments/run_001/logs/training.log": "Epoch 1/100: loss=2.345\nEpoch 2/100: loss=2.102\n",
    "experiments/run_002/checkpoints/model_step_500.txt": "checkpoint data placeholder",
    "experiments/run_003/outputs/results.csv": "step,accuracy\n100,0.45\n200,0.62\n",
    "src/models/lstm/model.py": "class LSTMModel:\n    pass\n",
    "src/models/transformer/attention.py": "def scaled_dot_product(q, k, v):\n    pass\n",
    "src/utils/metrics.py": "def accuracy(pred, label):\n    return (pred == label).mean()\n",
    "src/data/loader.py": "class DataLoader:\n    pass\n",
    "tests/unit/test_attention.py": "def test_softmax():\n    pass\n",
    "tests/integration/test_pipeline.py": "def test_end_to_end():\n    pass\n",
    "docs/references/graves2014.txt": "Neural Turing Machines - Graves et al. 2014\narXiv: 1410.5401\n",
    "configs/deprecated/old_config.json": json.dumps({"memory_size": 64, "word_size": 32, "deprecated": True}),
    "memory/snapshots/snapshot_0.txt": "empty snapshot",
}
for path, content in distractor_files.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# --- Generate the actual NTM task inputs ---
# Parameters for the NTM simulation
N = 4   # memory size (rows)
M = 3   # memory dimension (cols)

# Initial memory matrix (non-trivial values)
initial_memory = np.array([
    [0.5, 0.1, 0.3],
    [0.2, 0.8, 0.1],
    [0.6, 0.4, 0.2],
    [0.1, 0.3, 0.9],
], dtype=float)

# We define a sequence of TWO operations to simulate:
# Operation 1: WRITE then READ
# Operation 2: READ only (using updated memory from op1)

# ---- Operation 1 parameters ----
# Content addressing key and beta (strength)
key_1 = [0.6, 0.4, 0.2]
beta_1 = 2.0

# Previous weights (uniform initialization)
prev_weights_1 = [0.25, 0.25, 0.25, 0.25]

# Interpolation gate
gate_1 = 0.8

# Shift weights for circular convolution (3-element: shift -1, 0, +1)
# shift_weights[0] = weight for shift -1, [1] = 0, [2] = +1
shift_weights_1 = [0.1, 0.7, 0.2]

# Sharpening gamma
gamma_1 = 2.5

# Write erase vector
erase_1 = [0.9, 0.5, 0.3]

# Write add vector
add_1 = [0.4, 0.7, 0.2]

# ---- Operation 2 parameters ----
key_2 = [0.2, 0.8, 0.1]
beta_2 = 3.0
prev_weights_2 = [0.25, 0.25, 0.25, 0.25]  # will be updated after op1
gate_2 = 0.6
shift_weights_2 = [0.05, 0.9, 0.05]
gamma_2 = 1.5

# No write in op2, only read

task_spec = {
    "description": "NTM simulation task: apply two sequential operations on the memory matrix.",
    "memory_config": {
        "N": N,
        "M": M
    },
    "initial_memory": initial_memory.tolist(),
    "operations": [
        {
            "op_id": 1,
            "type": "write_then_read",
            "addressing_params": {
                "key": key_1,
                "beta": beta_1,
                "prev_weights": prev_weights_1,
                "interpolation_gate": gate_1,
                "shift_weights": shift_weights_1,
                "gamma": gamma_1
            },
            "write_params": {
                "erase": erase_1,
                "add": add_1
            }
        },
        {
            "op_id": 2,
            "type": "read_only",
            "addressing_params": {
                "key": key_2,
                "beta": beta_2,
                "prev_weights": prev_weights_2,
                "interpolation_gate": gate_2,
                "shift_weights": shift_weights_2,
                "gamma": gamma_2
            }
        }
    ],
    "output_file": "ntm_simulation_result.json"
}

with open(os.path.join(workspace, "ntm_task_spec.json"), "w") as f:
    json.dump(task_spec, f, indent=2)

# Also write a partial/wrong reference to mislead naive approaches
wrong_ref = {
    "note": "DRAFT - DO NOT USE - incorrect reference implementation",
    "wrong_read_formula": "simple_average_not_weighted_sum",
    "wrong_write": "additive_only_no_erase",
    "wrong_addressing": "softmax_without_beta_scaling"
}
with open(os.path.join(workspace, "src/utils/wrong_ntm_ref.json"), "w") as f:
    json.dump(wrong_ref, f, indent=2)

# Write a misleading config
misleading_config = {
    "ntm_memory": {
        "memory_size": 128,
        "memory_dim": 64,
        "num_read_heads": 1,
        "num_write_heads": 1,
        "addressing": {
            "content": True,
            "location": True,
            "hybrid": False
        },
        "note": "This config is for a DIFFERENT experiment, not the simulation task"
    }
}
with open(os.path.join(workspace, "configs/deprecated/ntm_config_draft.json"), "w") as f:
    json.dump(misleading_config, f, indent=2)

print("Workspace generated successfully.")
print(f"Task spec written to: {workspace}/ntm_task_spec.json")