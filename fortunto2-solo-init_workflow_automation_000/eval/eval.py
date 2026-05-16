import sys
import json
import os
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    home = Path.home()

    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ─────────────────────────────────────────────────────────────
    # CHECK 1: ~/.solo-factory/defaults.yaml exists
    # ─────────────────────────────────────────────────────────────
    defaults_path = home / ".solo-factory" / "defaults.yaml"
    if not defaults_path.exists():
        add_check("defaults.yaml exists", False, f"File not found at {defaults_path}", 2.0)
        # Add placeholder failures for sub-checks
        for k in ["org_domain", "apple_dev_team", "github_org", "projects_dir", "knowledge_base_repo"]:
            add_check(f"defaults.yaml key: {k}", False, "Parent file missing", 1.0)
        add_check("defaults.yaml header comment", False, "Parent file missing", 1.0)
    else:
        add_check("defaults.yaml exists", True, str(defaults_path), 2.0)
        try:
            import yaml
            with open(defaults_path) as f:
                raw_content = f.read()
                data = yaml.safe_load(raw_content)

            expected_keys = {
                "org_domain": "pixelcraft.io",
                "apple_dev_team": "T8KQ4XVBN2",
                "github_org": "pixelcraft-labs",
                "projects_dir": "/Users/nova/dev",
                "knowledge_base_repo": "pixelcraft-kb",
            }
            for key, expected_val in expected_keys.items():
                actual = str(data.get(key, "")).strip() if data.get(key) is not None else ""
                passed = actual == expected_val
                add_check(
                    f"defaults.yaml key: {key}",
                    passed,
                    f"Expected '{expected_val}', got '{actual}'",
                    1.0
                )

            # Check header comment
            header_present = (
                "Solo Factory — org defaults" in raw_content and
                "Re-run /init to update these values." in raw_content
            )
            add_check(
                "defaults.yaml header comment",
                header_present,
                "Header comment block must include 'Solo Factory — org defaults' and 'Re-run /init to update these values.'",
                1.0
            )
        except Exception as e:
            add_check("defaults.yaml parseable", False, f"Parse error: {e}", 1.0)

    # ─────────────────────────────────────────────────────────────
    # CHECK 2: .solo/manifest.md
    # ─────────────────────────────────────────────────────────────
    manifest_path = workspace / ".solo" / "manifest.md"
    if not manifest_path.exists():
        add_check("manifest.md exists", False, f"Not found at {manifest_path}", 2.0)
        for s in ["Mission", "Target Customer", "Primary Constraint", "12-Month Vision"]:
            add_check(f"manifest.md section: {s}", False, "Parent file missing", 1.0)
    else:
        add_check("manifest.md exists", True, str(manifest_path), 2.0)
        try:
            content = manifest_path.read_text()
            # Header
            has_header = "# Founder Manifest" in content
            add_check("manifest.md header", has_header, "'# Founder Manifest' heading required", 0.5)

            section_checks = {
                "## Mission": "Build delightful developer tools that make indie founders 10x more productive without burning out.",
                "## Target Customer": "Solo and micro-team SaaS founders who code their own products.",
                "## Primary Constraint": "focus",
                "## 12-Month Vision": "Three products live, each generating $2k MRR, with a growing community of 500 power users.",
            }
            for section_header, expected_content in section_checks.items():
                section_name = section_header.replace("## ", "")
                has_section = section_header in content
                section_has_content = expected_content in content if has_section else False
                add_check(
                    f"manifest.md section: {section_name}",
                    has_section and section_has_content,
                    f"Section '{section_header}' must exist and contain: '{expected_content[:60]}...'",
                    1.0
                )
        except Exception as e:
            add_check("manifest.md readable", False, f"Error: {e}", 1.0)

    # ─────────────────────────────────────────────────────────────
    # CHECK 3: .solo/stream-framework.md
    # ─────────────────────────────────────────────────────────────
    stream_path = workspace / ".solo" / "stream-framework.md"
    if not stream_path.exists():
        add_check("stream-framework.md exists", False, f"Not found at {stream_path}", 2.0)
        for s in ["Decision Style", "Risk Tolerance", "Calibration Notes"]:
            add_check(f"stream-framework.md section: {s}", False, "Parent file missing", 1.0)
    else:
        add_check("stream-framework.md exists", True, str(stream_path), 2.0)
        try:
            content = stream_path.read_text()
            has_header = "# STREAM Framework" in content
            add_check("stream-framework.md header", has_header, "'# STREAM Framework' heading required", 0.5)

            has_decision_section = "## Decision Style" in content
            has_decision_value = "solo-fast" in content
            add_check(
                "stream-framework.md: Decision Style",
                has_decision_section and has_decision_value,
                "Section '## Decision Style' with value 'solo-fast' required",
                1.0
            )

            has_risk_section = "## Risk Tolerance" in content
            has_risk_value = "medium" in content
            add_check(
                "stream-framework.md: Risk Tolerance",
                has_risk_section and has_risk_value,
                "Section '## Risk Tolerance' with value 'medium' required",
                1.0
            )

            # The critical proprietary trap: calibration note for solo-fast + medium
            # Must contain exact sentence from generation-rules.md
            expected_calibration = "Move fast but gut-check against data before shipping."
            has_calibration_section = "## Calibration Notes" in content
            has_calibration_note = expected_calibration in content
            add_check(
                "stream-framework.md: Calibration Notes (proprietary rule)",
                has_calibration_section and has_calibration_note,
                f"Section '## Calibration Notes' must contain exact sentence: '{expected_calibration}'",
                2.0  # High weight — this is the proprietary trap
            )
        except Exception as e:
            add_check("stream-framework.md readable", False, f"Error: {e}", 1.0)

    # ─────────────────────────────────────────────────────────────
    # CHECK 4: .solo/dev-principles.md
    # ─────────────────────────────────────────────────────────────
    devprinciples_path = workspace / ".solo" / "dev-principles.md"
    if not devprinciples_path.exists():
        add_check("dev-principles.md exists", False, f"Not found at {devprinciples_path}", 2.0)
        for s in ["Code Review Style", "Type Preference", "Tech Debt Approach", "Testing Philosophy"]:
            add_check(f"dev-principles.md section: {s}", False, "Parent file missing", 1.0)
    else:
        add_check("dev-principles.md exists", True, str(devprinciples_path), 2.0)
        try:
            content = devprinciples_path.read_text()
            has_header = "# Dev Principles" in content
            add_check("dev-principles.md header", has_header, "'# Dev Principles' heading required", 0.5)

            section_checks = {
                "## Code Review Style": "solo",
                "## Type Preference": "typed",
                "## Tech Debt Approach": "pay-as-you-go",
                "## Testing Philosophy": "tdd",
            }
            for section_header, expected_val in section_checks.items():
                section_name = section_header.replace("## ", "")
                has_section = section_header in content
                has_value = expected_val in content if has_section else False
                add_check(
                    f"dev-principles.md section: {section_name}",
                    has_section and has_value,
                    f"Section '{section_header}' with value '{expected_val}' required",
                    1.0
                )
        except Exception as e:
            add_check("dev-principles.md readable", False, f"Error: {e}", 1.0)

    # ─────────────────────────────────────────────────────────────
    # CHECK 5: .solo/stacks/ — correct stack YAMLs copied
    # ─────────────────────────────────────────────────────────────
    stacks_dir = workspace / ".solo" / "stacks"
    stacks_dir_exists = stacks_dir.exists() and stacks_dir.is_dir()
    add_check("stacks/ directory exists", stacks_dir_exists, f"Expected directory at {stacks_dir}", 1.0)

    if stacks_dir_exists:
        # nextjs-supabase.yaml
        njs_path = stacks_dir / "nextjs-supabase.yaml"
        njs_exists = njs_path.exists()
        if njs_exists:
            try:
                import yaml
                njs_data = yaml.safe_load(njs_path.read_text())
                njs_valid = (
                    njs_data.get("name") == "nextjs-supabase" and
                    njs_data.get("framework") == "Next.js"
                )
            except Exception:
                njs_valid = False
        else:
            njs_valid = False
        add_check(
            "stacks/nextjs-supabase.yaml present and valid",
            njs_exists and njs_valid,
            f"Expected .solo/stacks/nextjs-supabase.yaml with correct content",
            1.5
        )

        # python-api.yaml
        pyapi_path = stacks_dir / "python-api.yaml"
        pyapi_exists = pyapi_path.exists()
        if pyapi_exists:
            try:
                import yaml
                pyapi_data = yaml.safe_load(pyapi_path.read_text())
                pyapi_valid = (
                    pyapi_data.get("name") == "python-api" and
                    pyapi_data.get("language") == "Python"
                )
            except Exception:
                pyapi_valid = False
        else:
            pyapi_valid = False
        add_check(
            "stacks/python-api.yaml present and valid",
            pyapi_exists and pyapi_valid,
            f"Expected .solo/stacks/python-api.yaml with correct content",
            1.5
        )

        # Ensure NO extra stacks were added (only the two selected)
        yaml_files = list(stacks_dir.glob("*.yaml"))
        unexpected = [f.name for f in yaml_files if f.name not in ("nextjs-supabase.yaml", "python-api.yaml")]
        add_check(
            "stacks/ contains only selected stacks",
            len(unexpected) == 0,
            f"Unexpected stack files: {unexpected}" if unexpected else "Only selected stacks present",
            1.0
        )
    else:
        add_check("stacks/nextjs-supabase.yaml present and valid", False, "stacks/ directory missing", 1.5)
        add_check("stacks/python-api.yaml present and valid", False, "stacks/ directory missing", 1.5)
        add_check("stacks/ contains only selected stacks", False, "stacks/ directory missing", 1.0)

    # ─────────────────────────────────────────────────────────────
    # CHECK 6: Two-layer separation — org config is at HOME, not workspace
    # ─────────────────────────────────────────────────────────────
    wrong_location = workspace / ".solo-factory" / "defaults.yaml"
    wrong_location_exists = wrong_location.exists()
    add_check(
        "defaults.yaml is at ~/.solo-factory/ (not in workspace)",
        not wrong_location_exists,
        f"defaults.yaml must be at ~/.solo-factory/defaults.yaml, not inside the project workspace",
        2.0  # High weight — the two-layer architecture is the key proprietary constraint
    )

    # ─────────────────────────────────────────────────────────────
    # Final Score
    # ─────────────────────────────────────────────────────────────
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))