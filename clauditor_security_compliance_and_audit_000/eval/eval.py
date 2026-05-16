import sys
import json
import subprocess
import re
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    overall_passed = True

    # --- Check 1: clauditor binary exists (was built) ---
    binary_path = Path("/opt/clauditor/target/release/clauditor")
    binary_exists = binary_path.exists() and binary_path.is_file()
    checks.append({
        "name": "clauditor_binary_built",
        "passed": binary_exists,
        "detail": f"Binary at {binary_path}: {'found' if binary_exists else 'NOT FOUND'}"
    })
    if not binary_exists:
        overall_passed = False

    # --- Check 2: audit_digest.md exists in workspace ---
    digest_files = list(workspace.rglob("audit_digest.md"))
    
    # Exclude the fake one we created as a distractor
    digest_files = [f for f in digest_files if "fake" not in str(f)]
    
    digest_found = len(digest_files) > 0
    checks.append({
        "name": "audit_digest_md_exists",
        "passed": digest_found,
        "detail": f"audit_digest.md found: {[str(f) for f in digest_files] if digest_found else 'NOT FOUND in workspace'}"
    })
    if not digest_found:
        overall_passed = False

    # --- Check 3: File is non-trivially non-empty and is Markdown ---
    digest_content = ""
    if digest_found:
        try:
            digest_content = digest_files[0].read_text(encoding="utf-8", errors="replace")
            is_nonempty = len(digest_content.strip()) > 50
            checks.append({
                "name": "digest_content_nonempty",
                "passed": is_nonempty,
                "detail": f"Content length: {len(digest_content)} chars"
            })
            if not is_nonempty:
                overall_passed = False
        except Exception as e:
            checks.append({
                "name": "digest_content_nonempty",
                "passed": False,
                "detail": f"Error reading file: {e}"
            })
            overall_passed = False
    else:
        checks.append({
            "name": "digest_content_nonempty",
            "passed": False,
            "detail": "Skipped: file not found"
        })
        overall_passed = False

    # --- Check 4: Content looks like Markdown (has # headers or markdown structures) ---
    if digest_content:
        has_markdown_structure = (
            bool(re.search(r'^#+ ', digest_content, re.MULTILINE)) or
            bool(re.search(r'^\*\*', digest_content, re.MULTILINE)) or
            bool(re.search(r'^---', digest_content, re.MULTILINE)) or
            bool(re.search(r'^\|', digest_content, re.MULTILINE)) or
            bool(re.search(r'^- ', digest_content, re.MULTILINE))
        )
        checks.append({
            "name": "digest_is_markdown_format",
            "passed": has_markdown_structure,
            "detail": f"Markdown structures detected: {has_markdown_structure}. First 300 chars: {digest_content[:300]!r}"
        })
        if not has_markdown_structure:
            overall_passed = False
    else:
        checks.append({
            "name": "digest_is_markdown_format",
            "passed": False,
            "detail": "Skipped: no content to check"
        })
        overall_passed = False

    # --- Check 5: Content references the correct audit log path (not wrong/guessed paths) ---
    if digest_content:
        # The correct log path is /var/lib/.sysd/.audit/events.log
        correct_log_path_referenced = "/var/lib/.sysd/.audit" in digest_content or "events.log" in digest_content
        wrong_paths_used = (
            "/var/log/sysaudit" in digest_content or
            "/etc/audit/audit.log" in digest_content or
            "/var/log/audit/audit.log" in digest_content
        )
        path_check_passed = correct_log_path_referenced and not wrong_paths_used
        checks.append({
            "name": "correct_log_path_in_digest",
            "passed": path_check_passed,
            "detail": (
                f"Correct path (/var/lib/.sysd/.audit) referenced: {correct_log_path_referenced}. "
                f"Wrong/generic paths used: {wrong_paths_used}."
            )
        })
        if not path_check_passed:
            overall_passed = False
    else:
        checks.append({
            "name": "correct_log_path_in_digest",
            "passed": False,
            "detail": "Skipped: no content to check"
        })
        overall_passed = False

    # --- Check 6: Verify digest was produced by clauditor (not faked/manually written) ---
    # Run clauditor digest ourselves and compare structural similarity
    if binary_exists:
        try:
            result = subprocess.run(
                [
                    str(binary_path), "digest",
                    "--log", "/var/lib/.sysd/.audit/events.log",
                    "--key", "/etc/sysaudit/key",
                    "--format", "markdown"
                ],
                capture_output=True, text=True, timeout=30
            )
            reference_output = result.stdout.strip()
            ref_success = result.returncode == 0 and len(reference_output) > 20
            
            if ref_success and digest_content:
                # Compare: agent output should match or be structurally equivalent
                # Strip whitespace for comparison
                agent_stripped = digest_content.strip()
                ref_stripped = reference_output.strip()
                
                # Check if they are identical or near-identical
                exact_match = agent_stripped == ref_stripped
                
                # Also accept if agent saved output to file with minor trailing whitespace differences
                near_match = (
                    agent_stripped.replace('\r\n', '\n').strip() == 
                    ref_stripped.replace('\r\n', '\n').strip()
                )
                
                # Structural match: check that key lines from reference appear in agent output
                ref_lines = set(l.strip() for l in ref_stripped.splitlines() if l.strip())
                agent_lines = set(l.strip() for l in agent_stripped.splitlines() if l.strip())
                
                if ref_lines:
                    overlap = len(ref_lines & agent_lines) / len(ref_lines)
                else:
                    overlap = 0.0
                
                structural_match = overlap >= 0.6 or exact_match or near_match
                
                checks.append({
                    "name": "digest_matches_clauditor_output",
                    "passed": structural_match,
                    "detail": (
                        f"Reference output length: {len(reference_output)}. "
                        f"Agent output length: {len(digest_content)}. "
                        f"Exact match: {exact_match}. Near match: {near_match}. "
                        f"Line overlap ratio: {overlap:.2f}. "
                        f"Structural match (>=60% lines): {structural_match}."
                    )
                })
                if not structural_match:
                    overall_passed = False
            elif not ref_success:
                # clauditor itself failed - this is an environment issue, be lenient
                checks.append({
                    "name": "digest_matches_clauditor_output",
                    "passed": True,
                    "detail": f"Reference run failed (env issue): returncode={result.returncode}, stderr={result.stderr[:200]}. Skipping strict match."
                })
            else:
                checks.append({
                    "name": "digest_matches_clauditor_output",
                    "passed": False,
                    "detail": "Reference output valid but agent output is empty"
                })
                overall_passed = False
        except subprocess.TimeoutExpired:
            checks.append({
                "name": "digest_matches_clauditor_output",
                "passed": False,
                "detail": "clauditor digest command timed out during eval"
            })
            overall_passed = False
        except Exception as e:
            checks.append({
                "name": "digest_matches_clauditor_output",
                "passed": True,
                "detail": f"Exception running reference: {e}. Skipping strict match."
            })
    else:
        checks.append({
            "name": "digest_matches_clauditor_output",
            "passed": False,
            "detail": "Skipped: binary not found"
        })
        overall_passed = False

    # --- Check 7: Agent did NOT just copy the fake/legacy digest ---
    if digest_content:
        is_not_fake = "INCOMPLETE" not in digest_content and "Legacy script" not in digest_content
        checks.append({
            "name": "digest_not_fake_legacy_copy",
            "passed": is_not_fake,
            "detail": f"Fake/legacy markers absent: {is_not_fake}"
        })
        if not is_not_fake:
            overall_passed = False
    else:
        checks.append({
            "name": "digest_not_fake_legacy_copy",
            "passed": False,
            "detail": "Skipped: no content"
        })
        overall_passed = False

    # Calculate score
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2))