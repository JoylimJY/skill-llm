import os
import json
import random
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")
random.seed(42)

# ── 1. Distractor directory structure ────────────────────────────────────────
dirs = [
    "experiments/run_001/raw",
    "experiments/run_001/processed",
    "experiments/run_002/raw",
    "experiments/run_002/processed",
    "configs/legacy",
    "configs/active",
    "notebooks",
    "scripts/preprocessing",
    "scripts/analysis",
    "docs",
    "tmp",
    "archive/2023",
    "archive/2024",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── 2. Distractor files ───────────────────────────────────────────────────────

# Old broken config
(WORKSPACE / "configs/legacy/decoder_config.json").write_text(json.dumps({
    "neurons": 32,
    "model": "old_linear",
    "dt": 0.05,
    "NOTE": "DEPRECATED - do not use, causes drift artifact"
}, indent=2))

# Active but wrong config (trap: wrong neuron count)
(WORKSPACE / "configs/active/decoder_config.json").write_text(json.dumps({
    "neurons": 128,
    "model": "cosine_tuning_v2",
    "dt": 0.02,
    "NOTE": "Pending validation - neuron count not yet verified"
}, indent=2))

# Fake old trajectory output (CSV with wrong format)
(WORKSPACE / "experiments/run_001/processed/traj_old.csv").write_text(
    "t,cursor_x,cursor_y\n0,0.1,0.2\n1,0.3,0.4\n2,0.5,0.1\n"
)

# Broken spike data
(WORKSPACE / "experiments/run_002/raw/spikes_corrupt.bin").write_bytes(
    bytes([random.randint(0, 255) for _ in range(512)])
)

# Notebook placeholder
(WORKSPACE / "notebooks/analysis_scratch.py").write_text(
    "# TODO: import trajectory_data.csv and run PCA\n# This is a placeholder\nimport pandas as pd\n# df = pd.read_csv('../trajectory_data.csv')\n"
)

# Preprocessing script (distractor)
(WORKSPACE / "scripts/preprocessing/normalize_spikes.py").write_text(textwrap.dedent("""\
    import numpy as np
    import sys

    def normalize(data):
        return (data - data.mean()) / (data.std() + 1e-8)

    if __name__ == "__main__":
        print("Usage: normalize_spikes.py <input.npy>")
"""))

# Analysis script (distractor)
(WORKSPACE / "scripts/analysis/plot_velocity.py").write_text(textwrap.dedent("""\
    # Requires trajectory_data.csv to exist
    import csv
    import sys

    def load_trajectory(path):
        rows = []
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows

    if __name__ == "__main__":
        data = load_trajectory(sys.argv[1])
        print(f"Loaded {len(data)} timesteps")
"""))

# Docs with vague references
(WORKSPACE / "docs/bci_pipeline_overview.txt").write_text(textwrap.dedent("""\
    BCI Data Pipeline Overview
    ==========================
    Step 1: Neural signal acquisition (hardware layer)
    Step 2: Spike sorting and rate estimation
    Step 3: Velocity decoding via motor cortex model
    Step 4: Export decoded trajectory for ML team

    The decoding step uses a 64-channel array.
    Output must be consumable by the ML pipeline.
    See: neuralink-decoder skill documentation for decode command details.
"""))

# Fake requirements file (distractor with wrong deps)
(WORKSPACE / "scripts/requirements_old.txt").write_text(
    "numpy==1.21.0\nscipy==1.7.0\nmatplotlib==3.4.0\npandas==1.3.0\n"
)

# Archive files
(WORKSPACE / "archive/2023/experiment_log.txt").write_text(
    "2023-11-01: Initial 32-neuron array test. Decoder unstable.\n"
    "2023-12-15: Upgraded to 64-neuron array. Cosine tuning model applied.\n"
)
(WORKSPACE / "archive/2024/notes.txt").write_text(
    "2024-03-10: neuralink-decoder skill installed. decode command tested manually.\n"
    "2024-06-22: ML team requests CSV export of vx, vy trajectory.\n"
)

# Tmp file (red herring)
(WORKSPACE / "tmp/scratch_decode_attempt.sh").write_text(
    "#!/bin/bash\n# INCOMPLETE - do not run\n# neuralink-decoder decode --neurons 32 # wrong count?\n"
)

# ── 3. Create the neuralink-decoder skill as a local pip package ──────────────
pkg_root = WORKSPACE / "neuralink_decoder_pkg"
pkg_root.mkdir(exist_ok=True)

# Package source
pkg_src = pkg_root / "neuralink_decoder"
pkg_src.mkdir(exist_ok=True)

(pkg_src / "__init__.py").write_text('__version__ = "0.1.0"\n')

# The core simulator + decoder + CLI
(pkg_src / "simulator.py").write_text(textwrap.dedent("""\
    import numpy as np

    N_NEURONS = 64
    DT = 0.05  # seconds per timestep
    T_TOTAL = 5.0  # seconds
    N_STEPS = int(T_TOTAL / DT)

    def generate_spike_trains(rng=None):
        \"\"\"
        Cosine tuning model: each neuron has a preferred direction.
        Firing rate = baseline + gain * cos(theta - preferred_theta)
        Returns spike_rates: (N_STEPS, N_NEURONS)
        \"\"\"
        if rng is None:
            rng = np.random.default_rng(seed=7)

        preferred_dirs = rng.uniform(0, 2 * np.pi, N_NEURONS)
        baseline_rate = 5.0   # Hz
        gain = 20.0            # Hz

        # Simulate a smooth circular movement trajectory
        t = np.linspace(0, T_TOTAL, N_STEPS)
        true_angle = 2 * np.pi * t / T_TOTAL  # one full circle

        spike_rates = np.zeros((N_STEPS, N_NEURONS))
        for i, theta in enumerate(true_angle):
            tuning = baseline_rate + gain * np.cos(theta - preferred_dirs)
            tuning = np.clip(tuning, 0, None)
            # Poisson spike count converted to rate
            counts = rng.poisson(tuning * DT)
            spike_rates[i] = counts / DT

        return spike_rates, preferred_dirs

    def decode_velocity(spike_rates, preferred_dirs):
        \"\"\"
        Linear decoder: population vector algorithm.
        vx = sum_i(r_i * cos(theta_i)) / N
        vy = sum_i(r_i * sin(theta_i)) / N
        Returns: (N_STEPS, 2) array of [vx, vy]
        \"\"\"
        cos_dirs = np.cos(preferred_dirs)
        sin_dirs = np.sin(preferred_dirs)

        vx = spike_rates @ cos_dirs / N_NEURONS
        vy = spike_rates @ sin_dirs / N_NEURONS

        return np.column_stack([vx, vy])
"""))

(pkg_src / "cli.py").write_text(textwrap.dedent("""\
    import sys
    import numpy as np
    from .simulator import generate_spike_trains, decode_velocity, N_STEPS, DT

    def run_decode():
        \"\"\"Entry point for the 'decode' subcommand.\"\"\"
        rng = np.random.default_rng(seed=7)
        spike_rates, preferred_dirs = generate_spike_trains(rng=rng)
        velocity = decode_velocity(spike_rates, preferred_dirs)

        print("=== Neuralink Decoder: Decoded Trajectory ===")
        print(f"Timesteps: {N_STEPS}  |  Neurons: 64  |  dt: {DT}s")
        print(f"{'timestep':>10}  {'vx':>12}  {'vy':>12}")
        print("-" * 40)
        for i, (vx, vy) in enumerate(velocity):
            print(f"{i:>10}  {vx:>12.6f}  {vy:>12.6f}")
        print("=== End of Trajectory ===")

    def main():
        if len(sys.argv) < 2 or sys.argv[1] != "decode":
            print("Usage: neuralink-decoder decode", file=sys.stderr)
            print("Commands:", file=sys.stderr)
            print("  decode    Run the simulation and decoding loop", file=sys.stderr)
            sys.exit(1)
        run_decode()

    if __name__ == "__main__":
        main()
"""))

# pyproject.toml
(pkg_root / "pyproject.toml").write_text(textwrap.dedent("""\
    [build-system]
    requires = ["setuptools>=61.0"]
    build-backend = "setuptools.backends.legacy:build"

    [project]
    name = "neuralink-decoder"
    version = "0.1.0"
    description = "Simulates and decodes neural spike activity into cursor movement (BCI)."
    requires-python = ">=3.9"
    dependencies = ["numpy"]

    [project.scripts]
    neuralink-decoder = "neuralink_decoder.cli:main"
"""))

# setup.cfg fallback
(pkg_root / "setup.cfg").write_text(textwrap.dedent("""\
    [metadata]
    name = neuralink-decoder
    version = 0.1.0

    [options]
    packages = neuralink_decoder
    install_requires = numpy

    [options.entry_points]
    console_scripts =
        neuralink-decoder = neuralink_decoder.cli:main
"""))

# setup.py fallback
(pkg_root / "setup.py").write_text(textwrap.dedent("""\
    from setuptools import setup, find_packages
    setup(
        name="neuralink-decoder",
        version="0.1.0",
        packages=find_packages(),
        entry_points={
            "console_scripts": [
                "neuralink-decoder=neuralink_decoder.cli:main",
            ],
        },
        install_requires=["numpy"],
    )
"""))

# SKILL.md inside the package (matches the provided one)
(pkg_root / "SKILL.md").write_text(textwrap.dedent("""\
    ---
    name: neuralink-decoder
    description: Simulates and decodes neural spike activity into cursor movement (BCI).
    author: tempguest
    version: 0.1.0
    license: MIT
    ---

    # Neuralink Decoder Skill

    This skill simulates a Brain-Computer Interface (BCI).
    It generates synthetic neural spiking data based on cosine tuning (motor cortex model) and uses a linear decoder to reconstruct cursor velocity.

    ## Features
    - **Neural Simulator**: Generates realistic spike trains for 64 neurons.
    - **Decoder**: Maps spike rates to 2D velocity ($v_x, v_y$).
    - **Visualization**: Prints the decoded trajectory.

    ## Commands

    - `decode`: Run the simulation and decoding loop.
"""))

print("Workspace generated successfully.")
print(f"Package location: {pkg_root}")
print(f"Total files created: {len(list(WORKSPACE.rglob('*')))}")