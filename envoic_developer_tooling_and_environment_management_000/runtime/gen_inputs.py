#!/usr/bin/env python3
"""
Generates a realistic, messy data science workspace simulating disk bloat
from abandoned ML experiments, stale venvs, and forgotten frontend prototypes.
"""

import os
import json
import random
import struct
import stat
from pathlib import Path

WORKSPACE = Path("/workspace")
random.seed(42)

def make_fake_binary(path: Path, size_kb: int):
    """Create a fake binary file of approximate size."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        chunk = b'\x00' * 1024
        for _ in range(size_kb):
            f.write(chunk)

def make_broken_venv(venv_path: Path):
    """Create a venv directory missing pyvenv.cfg (broken)."""
    venv_path.mkdir(parents=True, exist_ok=True)
    (venv_path / "bin").mkdir(exist_ok=True)
    (venv_path / "lib").mkdir(exist_ok=True)
    (venv_path / "lib" / "python3.11").mkdir(parents=True, exist_ok=True)
    (venv_path / "lib" / "python3.11" / "site-packages").mkdir(exist_ok=True)
    # NO pyvenv.cfg => broken venv
    make_fake_binary(venv_path / "lib" / "python3.11" / "site-packages" / "numpy" / "core" / "_multiarray_umath.so", 8192)
    make_fake_binary(venv_path / "lib" / "python3.11" / "site-packages" / "torch" / "lib" / "libtorch.so", 16384)

def make_valid_venv(venv_path: Path, python_version="3.10"):
    """Create a valid-looking venv with pyvenv.cfg."""
    venv_path.mkdir(parents=True, exist_ok=True)
    (venv_path / "bin").mkdir(exist_ok=True)
    (venv_path / "lib").mkdir(exist_ok=True)
    (venv_path / "lib" / f"python{python_version}").mkdir(parents=True, exist_ok=True)
    (venv_path / "lib" / f"python{python_version}" / "site-packages").mkdir(exist_ok=True)
    cfg_content = f"""home = /usr/bin
include-system-site-packages = false
version = {python_version}.5
virtualenv = 20.24.0
"""
    (venv_path / "pyvenv.cfg").write_text(cfg_content)
    make_fake_binary(venv_path / "lib" / f"python{python_version}" / "site-packages" / "sklearn" / "_lib.so", 4096)
    make_fake_binary(venv_path / "lib" / f"python{python_version}" / "site-packages" / "pandas" / "core.so", 6144)
    (venv_path / "bin" / "python").write_text("#!/bin/sh\nexec python3 \"$@\"")
    (venv_path / "bin" / "activate").write_text(f"# This file must be used with source\nexport VIRTUAL_ENV={venv_path}")

def make_node_modules(nm_path: Path, size_mb_approx: int = 50):
    """Create a fake node_modules directory with typical structure."""
    nm_path.mkdir(parents=True, exist_ok=True)
    packages = ["react", "lodash", "express", "webpack", "babel-core", "eslint", "jest", "typescript"]
    for pkg in packages:
        pkg_dir = nm_path / pkg
        pkg_dir.mkdir(exist_ok=True)
        (pkg_dir / "package.json").write_text(json.dumps({
            "name": pkg,
            "version": f"1.{random.randint(0,9)}.{random.randint(0,20)}",
            "main": "index.js"
        }, indent=2))
        (pkg_dir / "index.js").write_text(f"// {pkg} main module\nmodule.exports = {{}};")
        # Add fake dist/build artifacts
        make_fake_binary(pkg_dir / "dist" / "bundle.js", size_mb_approx * 10 // len(packages))

# ── Project 1: ml-experiment-alpha (abandoned, has broken venv deep inside) ──
proj1 = WORKSPACE / "projects" / "ml-experiment-alpha"
proj1.mkdir(parents=True, exist_ok=True)
(proj1 / "requirements.txt").write_text("torch==2.0.1\nnumpy==1.24.0\nscikit-learn==1.3.0\n")
(proj1 / "train.py").write_text("import torch\nprint('training...')\n")
(proj1 / "config.yaml").write_text("model: transformer\nlr: 0.001\nbatch_size: 32\n")

# Nested broken venv (requires --deep to find)
make_broken_venv(proj1 / "experiments" / "run_001" / ".venv")
make_broken_venv(proj1 / "experiments" / "run_002" / ".venv")

# Stale __pycache__ and build artifacts
(proj1 / "__pycache__").mkdir(exist_ok=True)
(proj1 / "__pycache__" / "train.cpython-311.pyc").write_bytes(b'\x00' * 4096)
(proj1 / ".pytest_cache").mkdir(exist_ok=True)
(proj1 / ".pytest_cache" / "v" / "cache" / "lastfailed").mkdir(parents=True, exist_ok=True)
make_fake_binary(proj1 / "dist" / "model_alpha.pt", 2048)

# ── Project 2: data-pipeline (has a valid but stale venv) ──
proj2 = WORKSPACE / "projects" / "data-pipeline"
proj2.mkdir(parents=True, exist_ok=True)
(proj2 / "requirements.txt").write_text("pandas==1.5.3\nairflow==2.7.0\npsycopg2==2.9.7\n")
(proj2 / "pipeline.py").write_text("import pandas as pd\nprint('pipeline')\n")
make_valid_venv(proj2 / ".venv", "3.10")

# Build artifacts
(proj2 / "build").mkdir(exist_ok=True)
make_fake_binary(proj2 / "build" / "pipeline.egg-info" / "PKG-INFO", 10)
(proj2 / ".eggs").mkdir(exist_ok=True)
make_fake_binary(proj2 / ".eggs" / "airflow-2.7.0-py3.10.egg", 512)

# ── Project 3: frontend-dashboard (stale node_modules, no package-lock.json) ──
proj3 = WORKSPACE / "projects" / "frontend-dashboard"
proj3.mkdir(parents=True, exist_ok=True)
(proj3 / "package.json").write_text(json.dumps({
    "name": "frontend-dashboard",
    "version": "0.3.1",
    "dependencies": {"react": "^18.0.0", "webpack": "^5.0.0"}
}, indent=2))
(proj3 / "src").mkdir(exist_ok=True)
(proj3 / "src" / "index.js").write_text("import React from 'react';\n")
make_node_modules(proj3 / "node_modules", size_mb_approx=40)

# ── Project 4: api-service (deep nested stale venv + node_modules) ──
proj4 = WORKSPACE / "projects" / "api-service"
proj4.mkdir(parents=True, exist_ok=True)
(proj4 / "requirements.txt").write_text("fastapi==0.100.0\nuvicorn==0.23.0\n")
(proj4 / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
# Deep nested venv (requires --deep)
make_valid_venv(proj4 / "services" / "auth" / ".venv", "3.11")
make_broken_venv(proj4 / "services" / "ml" / ".venv")
make_node_modules(proj4 / "services" / "frontend" / "node_modules", size_mb_approx=30)

# ── Project 5: old-prototype (deeply nested, completely abandoned) ──
proj5 = WORKSPACE / "archive" / "old-prototype"
proj5.mkdir(parents=True, exist_ok=True)
(proj5 / "README_DO_NOT_USE.txt").write_text("Deprecated. Do not use this code.\n")
make_broken_venv(proj5 / "backend" / "api" / "v1" / ".venv")
make_node_modules(proj5 / "frontend" / "client" / "node_modules", size_mb_approx=60)
# Also has a dangling symlink
try:
    os.symlink(str(proj5 / "nonexistent_target"), str(proj5 / "backend" / "current_env"))
except FileExistsError:
    pass

# ── Distractor files (normal project files, should NOT be deleted) ──
(WORKSPACE / "projects" / "shared-lib").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "projects" / "shared-lib" / "setup.py").write_text("from setuptools import setup\nsetup(name='shared-lib')\n")
(WORKSPACE / "projects" / "shared-lib" / "requirements.txt").write_text("pytest==7.4.0\n")
(WORKSPACE / "projects" / "shared-lib" / "setup.cfg").write_text("[metadata]\nname = shared-lib\nversion = 0.1.0\n")
(WORKSPACE / "projects" / "shared-lib" / "pyproject.toml").write_text('[build-system]\nrequires = ["setuptools"]\n')

# Conda-style environment marker (distractor but also a target)
conda_env = WORKSPACE / "envs" / "ml-base-env"
conda_env.mkdir(parents=True, exist_ok=True)
(conda_env / "conda-meta").mkdir(exist_ok=True)
(conda_env / "conda-meta" / "history").write_text("# cmd: conda create -n ml-base-env python=3.9\n")
make_fake_binary(conda_env / "lib" / "python3.9" / "site-packages" / "tensorflow" / "libtensorflow.so", 32768)

# Extra distractors: git repos, config files, data files
(WORKSPACE / ".git").mkdir(exist_ok=True)
(WORKSPACE / ".git" / "config").write_text("[core]\nrepositoryformatversion = 0\n")
(WORKSPACE / "docs").mkdir(exist_ok=True)
(WORKSPACE / "docs" / "architecture.md").write_text("# Architecture\nThis workspace hosts multiple ML and data projects.\n")
(WORKSPACE / "Makefile").write_text("clean:\n\trm -rf dist/\n\ntest:\n\tpytest tests/\n")
(WORKSPACE / ".env.example").write_text("DATABASE_URL=postgresql://localhost/mydb\nSECRET_KEY=changeme\n")
(WORKSPACE / "data" / "raw" / "dataset.csv").mkdir(parents=True, exist_ok=True)
# Fix: data/raw/dataset.csv should be a file not dir
import shutil
shutil.rmtree(WORKSPACE / "data" / "raw" / "dataset.csv", ignore_errors=True)
(WORKSPACE / "data" / "raw").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "data" / "raw" / "dataset.csv").write_text("id,feature1,feature2,label\n1,0.5,0.3,1\n2,0.1,0.9,0\n")

# pip cache bloat simulation
pip_cache = WORKSPACE / ".cache" / "pip" / "wheels" / "cp311"
pip_cache.mkdir(parents=True, exist_ok=True)
make_fake_binary(pip_cache / "torch-2.0.1-cp311-cp311-linux_x86_64.whl", 8192)
make_fake_binary(pip_cache / "numpy-1.24.0-cp311-cp311-linux_x86_64.whl", 1024)

# npm cache
npm_cache = WORKSPACE / ".npm" / "_cacache" / "content-v2"
npm_cache.mkdir(parents=True, exist_ok=True)
make_fake_binary(npm_cache / "sha512" / "aa" / "bb" / "react-18.2.0.tgz", 512)

print("Workspace generated successfully.")
print("\nWorkspace structure summary:")
for p in sorted(WORKSPACE.rglob("*"))[:60]:
    if p.is_dir():
        print(f"  [DIR]  {p.relative_to(WORKSPACE)}")
    else:
        print(f"  [FILE] {p.relative_to(WORKSPACE)}")