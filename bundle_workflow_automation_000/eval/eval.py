import sys
import os
import json
import subprocess
import glob
from pathlib import Path

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    store_dir = os.path.expanduser("~/.local/share/bundle")
    script = os.path.join(workspace, "scripts", "script.sh")
    pipeline_dir = os.path.join(workspace, "genomics_pipeline_v2")
    staging_dir = os.path.join(workspace, "staging")

    # ----------------------------------------------------------------
    # CHECK 1: A .bundle.tar.gz file must exist somewhere in workspace
    # ----------------------------------------------------------------
    bundle_files = list(Path(workspace).rglob("*.bundle.tar.gz"))
    if bundle_files:
        bundle_path = str(bundle_files[0])
        checks.append({
            "name": "bundle_file_created",
            "passed": True,
            "detail": f"Bundle file found: {bundle_path}"
        })
    else:
        checks.append({
            "name": "bundle_file_created",
            "passed": False,
            "detail": "No .bundle.tar.gz file found anywhere in workspace"
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ----------------------------------------------------------------
    # CHECK 2: The bundle must be created from the genomics_pipeline_v2 dir
    # and must contain expected files inside it
    # ----------------------------------------------------------------
    try:
        rc, out, err = run(f"tar -tzf '{bundle_path}'")
        expected_paths = [
            "genomics_pipeline_v2/bin/align.sh",
            "genomics_pipeline_v2/config/pipeline.yaml",
            "genomics_pipeline_v2/lib/parsers/vcf_parser.py",
        ]
        all_present = all(any(ep in line for line in out.splitlines()) for ep in expected_paths)
        checks.append({
            "name": "bundle_contains_pipeline_files",
            "passed": all_present,
            "detail": f"Bundle contents listing: {out[:400]}" if all_present else f"Missing expected paths. Found: {out[:400]}"
        })
    except Exception as e:
        checks.append({
            "name": "bundle_contains_pipeline_files",
            "passed": False,
            "detail": f"Exception reading bundle: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 3: A manifest file must exist in ~/.local/share/bundle/
    # ----------------------------------------------------------------
    try:
        manifest_files = list(Path(store_dir).glob("*.manifest"))
        if manifest_files:
            manifest_path = str(manifest_files[0])
            with open(manifest_path) as f:
                manifest_content = f.read()
            # Manifest should have lines of form: "relative/path sha256hash"
            lines = [l for l in manifest_content.splitlines() if l.strip()]
            valid_lines = [l for l in lines if len(l.split()) == 2]
            checks.append({
                "name": "manifest_file_in_store",
                "passed": len(valid_lines) >= 5,
                "detail": f"Manifest at {manifest_path} has {len(valid_lines)} valid entries (need >=5). Sample: {lines[:3]}"
            })
        else:
            checks.append({
                "name": "manifest_file_in_store",
                "passed": False,
                "detail": f"No .manifest file found in {store_dir}"
            })
    except Exception as e:
        checks.append({
            "name": "manifest_file_in_store",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 4: Bundle must pass verify command
    # ----------------------------------------------------------------
    try:
        rc, out, err = run(f"bash '{script}' verify '{bundle_path}'", cwd=workspace)
        verify_ok = rc == 0 and "OK" in out
        checks.append({
            "name": "bundle_verify_passes",
            "passed": verify_ok,
            "detail": f"verify rc={rc}, stdout='{out}', stderr='{err}'"
        })
    except Exception as e:
        checks.append({
            "name": "bundle_verify_passes",
            "passed": False,
            "detail": f"Exception running verify: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 5: Bundle must have been extracted into staging dir
    # ----------------------------------------------------------------
    try:
        extracted_files = list(Path(staging_dir).rglob("*"))
        extracted_regular = [f for f in extracted_files if f.is_file()]
        has_extraction = len(extracted_regular) >= 5
        checks.append({
            "name": "bundle_extracted_to_staging",
            "passed": has_extraction,
            "detail": f"staging/ contains {len(extracted_regular)} files: {[str(f.relative_to(staging_dir)) for f in extracted_regular[:5]]}"
        })
    except Exception as e:
        checks.append({
            "name": "bundle_extracted_to_staging",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 6: A manifest must have been generated for the staging dir
    # (agent must run `manifest` on extracted dir and save output)
    # We check for a saved manifest file in workspace root named staging_manifest.txt
    # ----------------------------------------------------------------
    try:
        manifest_output_candidates = list(Path(workspace).rglob("staging_manifest.txt"))
        if manifest_output_candidates:
            with open(str(manifest_output_candidates[0])) as f:
                content = f.read()
            lines = [l for l in content.splitlines() if l.strip()]
            valid = [l for l in lines if len(l.split()) == 2]
            checks.append({
                "name": "staging_manifest_generated",
                "passed": len(valid) >= 5,
                "detail": f"staging_manifest.txt found with {len(valid)} valid lines. Sample: {lines[:3]}"
            })
        else:
            # Also accept any manifest output file that contains staging paths
            any_manifest = list(Path(workspace).rglob("*manifest*"))
            found_staging_manifest = False
            detail = "No staging_manifest.txt found in workspace."
            for mf in any_manifest:
                if mf.suffix in ('.manifest', '.txt', '.log', '') and mf.is_file():
                    try:
                        content = mf.read_text(errors='replace')
                        if 'genomics_pipeline_v2' in content or 'align.sh' in content:
                            lines = [l for l in content.splitlines() if l.strip()]
                            valid = [l for l in lines if len(l.split()) == 2]
                            if len(valid) >= 5:
                                found_staging_manifest = True
                                detail = f"Manifest-like file found at {mf} with {len(valid)} valid entries"
                                break
                    except Exception:
                        pass
            checks.append({
                "name": "staging_manifest_generated",
                "passed": found_staging_manifest,
                "detail": detail
            })
    except Exception as e:
        checks.append({
            "name": "staging_manifest_generated",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ----------------------------------------------------------------
    # SCORING
    # ----------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 4)

    # Must pass checks 1,2,3,4,5 to be considered overall passing
    critical = ["bundle_file_created", "bundle_contains_pipeline_files",
                "manifest_file_in_store", "bundle_verify_passes",
                "bundle_extracted_to_staging"]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )

    print(json.dumps({
        "passed": critical_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()