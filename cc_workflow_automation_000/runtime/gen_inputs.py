import os
import random
import stat

random.seed(42)

workspace = "/workspace"

# --- Create realistic project directory structure ---
projects_root = os.path.join(workspace, "dev_projects")
projects = ["ledger-api", "fraud-detector", "payment-gateway", "audit-service", "compliance-bot"]

for proj in projects:
    proj_dir = os.path.join(projects_root, proj)
    os.makedirs(proj_dir, exist_ok=True)
    
    # Add distractor files inside each project
    subdirs = ["src", "tests", "config", "docs", "scripts"]
    for sd in subdirs:
        os.makedirs(os.path.join(proj_dir, sd), exist_ok=True)

    # Distractor files
    distractor_files = {
        "src/main.py": f"# {proj} main module\nimport sys\n\ndef main():\n    print('Starting {proj}')\n\nif __name__ == '__main__':\n    main()\n",
        "src/utils.py": f"# Utility functions for {proj}\n\ndef format_currency(amount):\n    return f'${{amount:.2f}}'\n",
        "tests/test_main.py": f"import pytest\n\ndef test_placeholder():\n    assert True\n",
        "config/settings.yaml": f"project: {proj}\nenv: production\ndebug: false\nlog_level: INFO\n",
        "docs/API.md": f"# {proj} API Documentation\n\n## Endpoints\n\n- GET /health\n- POST /process\n",
        "scripts/deploy.sh": f"#!/bin/bash\necho 'Deploying {proj}...'\n",
        ".gitignore": "__pycache__/\n*.pyc\n.env\n",
        "requirements.txt": "fastapi==0.104.1\nuvicorn==0.24.0\npydantic==2.5.0\n",
    }
    for rel_path, content in distractor_files.items():
        fpath = os.path.join(proj_dir, rel_path)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, "w") as f:
            f.write(content)

# --- Create workspace-level distractors ---
extra_files = {
    "workspace_notes.txt": "TODO: configure relay for payment-gateway project\nMeeting notes: discuss fraud detection improvements\n",
    "env_check.sh": "#!/bin/bash\necho 'Checking environment...'\ntmux -V\nnode --version\n",
    "old_config.json": '{"root": "/old/projects", "deprecated": true}\n',
    ".bashrc_custom": "export PATH=$PATH:/usr/local/bin\nalias ll='ls -la'\n",
    "system_log.txt": "\n".join([f"2024-01-{i:02d} INFO: System check passed" for i in range(1, 20)]) + "\n",
}
for fname, content in extra_files.items():
    with open(os.path.join(workspace, fname), "w") as f:
        f.write(content)

# --- Create scripts directory and cc.sh mock scaffold ---
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

# State file for mock (simulates persistent config)
state_file = os.path.join(scripts_dir, ".cc_state")
with open(state_file, "w") as f:
    f.write("configured=false\nactive_project=\n")

# Create a long output file for the mock to serve (>4000 chars)
long_output_lines = []
long_output_lines.append("Analyzing payment-gateway codebase for PCI-DSS compliance issues...")
long_output_lines.append("")
long_output_lines.append("Found the following components under review:")
long_output_lines.append("")
for i in range(1, 80):
    long_output_lines.append(f"  [{i:03d}] Scanning module: payment_core/transaction_handler_{i:04d}.py ... OK")
long_output_lines.append("")
long_output_lines.append("Compliance scan complete.")
long_output_lines.append("Total files scanned: 79")
long_output_lines.append("Critical issues found: 0")
long_output_lines.append("Warnings: 3")
long_output_lines.append("  - Warning: Deprecated TLS 1.0 reference in legacy/tls_compat.py")
long_output_lines.append("  - Warning: Hardcoded timeout value in config/network.py line 42")
long_output_lines.append("  - Warning: Missing input validation in api/webhook_handler.py")
long_output_lines.append("Recommendation: Address warnings before next audit cycle.")
long_output_lines.append("Session complete. Claude Code is ready for next instruction.")

long_output = "\n".join(long_output_lines)
with open(os.path.join(scripts_dir, ".cc_long_output.txt"), "w") as f:
    f.write(long_output)

print(f"Long output length: {len(long_output)} chars")
assert len(long_output) > 4000, f"Long output must be >4000 chars, got {len(long_output)}"

print("Workspace generated successfully.")
print(f"Projects root: {projects_root}")
print(f"Available projects: {projects}")