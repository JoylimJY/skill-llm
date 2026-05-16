import os
import json
import random

random.seed(42)

BASE = "/workspace"

# --- Create deeply nested distractor directory structure ---
dirs = [
    "projects/crash_analysis/v1/meshes",
    "projects/crash_analysis/v1/results",
    "projects/crash_analysis/v2/meshes",
    "projects/nvh_study/baseline/inputs",
    "projects/nvh_study/optimized/outputs",
    "solvers/old_versions/abaqus_6.14",
    "solvers/old_versions/ansys_17",
    "solvers/third_party/hypermesh",
    "configs/backup",
    "configs/archive",
    "logs/2023",
    "logs/2024",
    "scripts/pre_processing",
    "scripts/post_processing",
    "temp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Create distractor files ---
distractor_files = [
    ("projects/crash_analysis/v1/meshes/door_panel.inp", "** Abaqus input file\n*Node\n1, 0.0, 0.0, 0.0\n"),
    ("projects/crash_analysis/v1/results/door_panel.odb", "binary_odb_placeholder"),
    ("projects/crash_analysis/v2/meshes/bumper_v2.inp", "** Abaqus input file v2\n*Node\n1, 1.0, 0.0, 0.0\n"),
    ("projects/nvh_study/baseline/inputs/engine_mount.inp", "** NVH mesh\n*Node\n1, 0.5, 0.5, 0.0\n"),
    ("projects/nvh_study/optimized/outputs/results_summary.txt", "Max displacement: 2.3mm\nMax stress: 450MPa\n"),
    ("solvers/old_versions/abaqus_6.14/README.txt", "Old Abaqus 6.14 installation - DO NOT USE"),
    ("solvers/old_versions/ansys_17/license.dat", "SERVER localhost ANY 1055\n"),
    ("solvers/third_party/hypermesh/hm_config.xml", "<config><version>2021</version></config>"),
    ("logs/2023/run_log_20231101.txt", "Job submitted at 08:00\nCompleted at 10:32\n"),
    ("logs/2024/run_log_20240315.txt", "Job submitted at 09:15\nFailed: license error\n"),
    ("scripts/pre_processing/clean_mesh.py", "# Mesh cleaning script\nimport sys\nprint('cleaning...')\n"),
    ("scripts/post_processing/extract_forces.py", "# Force extraction\nimport json\n"),
    ("temp/scratch/test_run.inp", "** temporary test\n*Node\n"),
    ("configs/backup/config_backup_2023.json", json.dumps({"note": "old backup", "saved_paths": {}})),
    ("configs/archive/config_v1.json", json.dumps({"note": "archive v1"})),
]

for rel_path, content in distractor_files:
    full_path = os.path.join(BASE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the MAIN config.json with predefined common install paths but NO saved paths for abaqus ---
# This simulates a fresh/misconfigured workstation where abaqus is installed in a non-standard location
config = {
    "saved_paths": {
        "ansys": "/apps/ansys/v221/ansys/bin/ansys221",
        "hyperworks": "/apps/altair/2022/hwsolvers/bin/optistruct"
    },
    "common_install_paths": {
        "abaqus": [
            "C:/SIMULIA/Abaqus/2022/Commands/abaqus.bat",
            "C:/SIMULIA/Abaqus/2021/Commands/abaqus.bat",
            "/usr/SIMULIA/Commands/abaqus"
        ],
        "ansys": [
            "C:/Program Files/ANSYS Inc/v221/ansys/bin/ansys221.exe"
        ],
        "ansa": [
            "C:/Program Files/BETA CAE Systems/ANSA/ansa_x64.exe"
        ],
        "hyperworks": [
            "C:/Program Files/Altair/2022/hwsolvers/bin/optistruct.exe"
        ]
    }
}

config_path = os.path.join(BASE, "configs", "cae_config.json")
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

# --- Create skill_runner.py placeholder that will be replaced by setup_script ---
# The actual mock is installed by setup_script
skill_runner_placeholder = os.path.join(BASE, "skill_runner_placeholder.txt")
with open(skill_runner_placeholder, "w") as f:
    f.write("skill_runner.py will be installed by setup script\n")

# --- Create the target simulation file the engineer wants to open ---
target_inp = os.path.join(BASE, "projects", "crash_analysis", "v2", "meshes", "final_crash_model.inp")
with open(target_inp, "w") as f:
    f.write("** Final crash model - Abaqus input\n** Author: J. Smith\n*Node\n1, 0.0, 0.0, 0.0\n2, 100.0, 0.0, 0.0\n*Element, type=C3D8\n1, 1, 2\n*End Step\n")

print("Workspace initialized successfully.")
print(f"Config at: {config_path}")
print(f"Target file: {target_inp}")