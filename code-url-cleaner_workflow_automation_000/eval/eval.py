import sys
import json
import re
from pathlib import Path

def load_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return None

def run_eval(workspace):
    checks = []
    
    # ── Expected cleaned content for each file ──────────────────────────────
    # We check specific lines/patterns that demonstrate correct cleaning.
    # The rules: URL spaces collapsed, path spaces collapsed, multi-spaces 
    # in commands collapsed, but natural language and indentation preserved.

    target_files = {
        "deploy/scripts/bootstrap.sh": {
            "must_not_contain": [
                r'https://github\.com/acme-corp\s+/backend-api\.git',
                r'https://github\.com/acme-corp\s+/frontend-app\.git',
                r'/var/log\s+/bootstrap\.log',
                r'/etc/acme\s+/config',
                r'pip3 install\s{2,}-r',
                r'npm install\s{2,}--legacy',
            ],
            "must_contain": [
                r'https://github\.com/acme-corp/backend-api\.git',
                r'https://github\.com/acme-corp/frontend-app\.git',
                r'pip3 install -r requirements\.txt --break-system-packages',
                r'npm install --legacy-peer-deps --prefer-offline',
                r'mkdir -p /etc/acme/config',
            ],
            "preserve_indentation": True,
        },
        "deploy/scripts/deploy_release.sh": {
            "must_not_contain": [
                r'registry\.acme\.io\s+/releases/backend',
                r'localhost:8080\s+/healthz',
                r'systemctl restart\s{2,}acme',
                r'docker run\s{2,}--rm',
            ],
            "must_contain": [
                r'registry\.acme\.io/releases/backend:\$VERSION',
                r'http://localhost:8080/healthz',
                r'systemctl restart acme-backend acme-worker',
                r'docker run --rm --network=host',
            ],
            "preserve_indentation": True,
        },
        "deploy/configs/ci_pipeline.yml": {
            "must_not_contain": [
                r'https://github\.com/acme-corp\s+/backend-api\.git',
                r'registry\.acme\.io\s+/releases/backend',
                r'pip3 install\s{2,}-r',
                r'python -m pytest\s{2,}tests',
                r'npm ci\s{2,}--prefer',
                r'/opt/deploy\s+/scripts',
            ],
            "must_contain": [
                r'https://github\.com/acme-corp/backend-api\.git',
                r'registry\.acme\.io/releases/backend:\$VERSION',
                r'pip3 install -r requirements\.txt -r requirements-dev\.txt',
                r'python -m pytest tests/ --tb=short -q',
                r'/opt/deploy/scripts/run_deploy\.sh',
            ],
            "preserve_indentation": True,
        },
        "pipeline/stages/build/build.sh": {
            "must_not_contain": [
                r'/tmp/deps\s+/build',
                r'https://github\.com/acme-corp\s+/shared-libs\.git',
                r'https://github\.com/acme-corp\s+/proto-defs\.git',
                r'pip3 install\s{2,}protobuf',
                r'python -m grpc_tools\.protoc\s{2,}',
            ],
            "must_contain": [
                r'/tmp/deps/build',
                r'https://github\.com/acme-corp/shared-libs\.git',
                r'https://github\.com/acme-corp/proto-defs\.git',
                r'pip3 install protobuf grpcio-tools --quiet',
            ],
            "preserve_indentation": True,
        },
        "deploy/configs/requirements_matrix.txt": {
            "must_not_contain": [
                r'https://github\.com/acme-corp\s+/shared-libs',
                r'https://mirrors\.acme\.io\s+/pypi',
                r'pip3 install\s{2,}-r',
                r'/opt/acme\s+/packages',
                r'/etc/acme\s+/service',
            ],
            "must_contain": [
                r'https://github\.com/acme-corp/shared-libs',
                r'https://mirrors\.acme\.io/pypi',
                r'/opt/acme/packages/internal',
                r'/etc/acme/service\.conf',
            ],
            "preserve_indentation": True,
        },
    }

    overall_passed = True
    total_score = 0.0
    file_weight = 1.0 / len(target_files)

    for rel_path, rules in target_files.items():
        full_path = Path(workspace) / rel_path
        content = load_file(full_path)
        
        if content is None:
            checks.append({
                "name": f"File exists: {rel_path}",
                "passed": False,
                "detail": f"File not found or unreadable: {full_path}"
            })
            overall_passed = False
            continue
        
        file_pass = True
        
        # Check must_not_contain (spacing defects must be gone)
        for pat in rules.get("must_not_contain", []):
            if re.search(pat, content):
                checks.append({
                    "name": f"[{rel_path}] Spacing defect removed: {pat}",
                    "passed": False,
                    "detail": f"Found forbidden pattern '{pat}' still present in file."
                })
                file_pass = False
                overall_passed = False
            else:
                checks.append({
                    "name": f"[{rel_path}] Spacing defect removed: {pat}",
                    "passed": True,
                    "detail": "Defect pattern not found (correctly cleaned)."
                })
        
        # Check must_contain (correct cleaned forms must be present)
        for pat in rules.get("must_contain", []):
            if re.search(pat, content):
                checks.append({
                    "name": f"[{rel_path}] Cleaned form present: {pat}",
                    "passed": True,
                    "detail": "Expected cleaned pattern found."
                })
            else:
                checks.append({
                    "name": f"[{rel_path}] Cleaned form present: {pat}",
                    "passed": False,
                    "detail": f"Expected pattern '{pat}' NOT found in file."
                })
                file_pass = False
                overall_passed = False
        
        # Check indentation preservation: lines starting with spaces/tabs
        if rules.get("preserve_indentation"):
            indented_lines = [l for l in content.split('\n') if l.startswith(('    ', '\t'))]
            if len(indented_lines) > 0:
                checks.append({
                    "name": f"[{rel_path}] Indentation preserved",
                    "passed": True,
                    "detail": f"Found {len(indented_lines)} indented lines preserved."
                })
            else:
                # Some files may legitimately have no indentation, only flag if original had it
                orig_paths_with_indent = [
                    "pipeline/stages/build/build.sh",
                    "deploy/configs/ci_pipeline.yml"
                ]
                if rel_path in orig_paths_with_indent:
                    checks.append({
                        "name": f"[{rel_path}] Indentation preserved",
                        "passed": False,
                        "detail": "No indented lines found - indentation may have been destroyed."
                    })
                    file_pass = False
                    overall_passed = False
                else:
                    checks.append({
                        "name": f"[{rel_path}] Indentation preserved",
                        "passed": True,
                        "detail": "File does not require indentation check."
                    })
        
        if file_pass:
            total_score += file_weight

    # Check that distractor files were NOT modified
    distractor_checks = {
        "docs/runbooks/disaster_recovery.md": "This document describes the process.",
        "pipeline/stages/test/pytest.ini": "testpaths = tests",
        "infra/ansible/inventory.ini": "[webservers]",
    }
    for rel_path, expected_snippet in distractor_checks.items():
        full_path = Path(workspace) / rel_path
        content = load_file(full_path)
        if content and expected_snippet in content:
            checks.append({
                "name": f"Distractor file untouched: {rel_path}",
                "passed": True,
                "detail": "Distractor file content is intact."
            })
        else:
            checks.append({
                "name": f"Distractor file untouched: {rel_path}",
                "passed": True,  # Don't penalize for this
                "detail": "Distractor file either unchanged or missing (not penalized)."
            })

    # Normalize score
    score = round(min(total_score, 1.0), 3)
    
    # Final pass = all file checks passed
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))