import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "src",
    "tests",
    "data/raw",
    "data/processed",
    "config",
    "docs",
    "scripts",
    "logs",
    "archive/2023",
    "archive/2024",
    "notebooks",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────

# 1. Old, broken dosage script (distractor — wrong algorithm)
with open(os.path.join(BASE, "src", "dosage_old.py"), "w") as f:
    f.write("""\
# DEPRECATED — do not use
def compute_dose(weight_kg, concentration_mg_per_ml):
    # BUG: missing body_surface_area factor
    return weight_kg * concentration_mg_per_ml * 0.5
""")

# 2. Partial config file
with open(os.path.join(BASE, "config", "dosage_config.json"), "w") as f:
    json.dump({
        "drug": "Amoxicillin",
        "standard_dose_mg_per_kg": 25,
        "max_dose_mg": 500,
        "concentration_mg_per_ml": 50,
        "route": "oral"
    }, f, indent=2)

# 3. Raw patient data (messy CSV — missing headers, extra whitespace)
with open(os.path.join(BASE, "data", "raw", "patients.csv"), "w") as f:
    f.write(
        "patient_id , weight_kg , age_years\n"
        "P001 , 32.5 , 8\n"
        "P002 , 71.0 , 35\n"
        "P003 , 15.2 , 4\n"
        "P004 , 88.3 , 52\n"
        "P005 , 5.9 , 1\n"
    )

# 4. Notebook stub (distractor)
with open(os.path.join(BASE, "notebooks", "analysis.ipynb"), "w") as f:
    json.dump({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}, f)

# 5. Stale log file
with open(os.path.join(BASE, "logs", "run_20240101.log"), "w") as f:
    f.write("ERROR: dosage_old.py crashed with ZeroDivisionError\n")

# 6. Archive placeholder
with open(os.path.join(BASE, "archive", "2023", "README.txt"), "w") as f:
    f.write("Archived runs — do not modify.\n")

# 7. scripts placeholder
with open(os.path.join(BASE, "scripts", "migrate.sh"), "w") as f:
    f.write("#!/bin/bash\necho 'Migration placeholder'\n")

# 8. docs stub
with open(os.path.join(BASE, "docs", "spec.md"), "w") as f:
    f.write(
        "# Dosage Calculation Spec\n\n"
        "Formula: dose_ml = min(weight_kg * standard_dose_mg_per_kg, max_dose_mg) / concentration_mg_per_ml\n"
        "Output must be a list of dicts with keys: patient_id, dose_ml (rounded to 2 dp)\n"
    )

# 9. data/processed placeholder
with open(os.path.join(BASE, "data", "processed", ".gitkeep"), "w") as f:
    f.write("")

# 10. archive/2024 placeholder
with open(os.path.join(BASE, "archive", "2024", "notes.txt"), "w") as f:
    f.write("Q1 run notes: switched to new concentration formula.\n")

# 11. Broken test file that should NOT be used (distractor in wrong location)
with open(os.path.join(BASE, "scripts", "test_broken.py"), "w") as f:
    f.write("""\
# This file is intentionally broken and in the wrong directory.
def test_always_fails():
    assert False, "This test must never be collected"
""")

# ── tdd.py (the TDD helper — already exists per skill) ───────────────────────
with open(os.path.join(BASE, "tdd.py"), "w") as f:
    f.write("""\
import argparse, subprocess, sys, os

parser = argparse.ArgumentParser()
parser.add_argument('--tests', default='tests', help='Path to tests (dir or file)')
parser.add_argument('--run', required=True, help='Command to run after tests pass')
args = parser.parse_args()

TEST_CMD = os.getenv('TEST_CMD') or f"pytest {args.tests}" if os.path.isdir(args.tests) else f"pytest {args.tests}"

print(f"Running tests: {TEST_CMD}")
res = subprocess.run(TEST_CMD, shell=True)
if res.returncode != 0:
    print("Tests failed or missing. Aborting run.")
    sys.exit(res.returncode or 1)

if os.getenv('WARN_AS_ERROR') == '1':
    lint = os.getenv('LINT_CMD') or "ruff ."
    print(f"Running lint: {lint}")
    lint_res = subprocess.run(lint, shell=True)
    if lint_res.returncode != 0:
        print("Lint/warnings failed. Aborting run.")
        sys.exit(lint_res.returncode or 1)

print("Tests green. Running target...")
run_res = subprocess.run(args.run, shell=True)
sys.exit(run_res.returncode)
""")

print("Workspace generated successfully.")